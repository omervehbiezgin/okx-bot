"""
Günlük trend stratejisi: portföy ve bütçe kuralları testi (100 USDT başlangıç, bileşik). Mesaj göndermez.
Çıktı: trend_portfoy.md

Sabit kurgu: günlük kapanışla kırılım (EMA50), 08:00 TR'de sabah fiyatına limit emir (48 saat), stop kırılan seviye
− 0,5 günlük ATR, TP 5R. Komisyon, long funding ve stop çıkışlarında %0,05 kayma dahil.
Denenen kurallar: aynı anda en fazla N pozisyon, aynı yönde en fazla M pozisyon, yer azken öncelik (24s hacim /
kırılım hacmi gücü), işlem başı risk. Seçim sadece eğitim dönemine (ilk 240 gün) göre; son 125 gün doğrulama.
"""
import sys
import time
import random
from collections import defaultdict
from datetime import datetime

import numpy as np

import pa_trend_bt as T
import pa_trend_ema as E

OUT = "trend_portfoy.md"
SLIP = 0.05
START = 100.0
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


class NoBtc:
    def dir_at(self, t):
        return 0


def build_trades():
    data, created = T.load()
    t_start = created - T.DAYS * 86400
    t_split = created - T.TEST_DAYS * 86400
    coins = {k: T.Coin(k, v) for k, v in data.items()}
    daily = E.load_daily(list(coins))
    trades = []
    for k, c in coins.items():
        if k not in daily:
            continue
        m = E.ema_map(daily[k], 50)
        vq = np.array(c.s1["v"])
        for ev in T.events(c, "1D", NoBtc(), ema_n=50, ema_map=m):
            if ev["t"] < t_start:
                continue
            f = T.fill(ev, c, "lim_s0", 0.5)
            if isinstance(f, str):
                continue
            r = T.simulate(ev, c, f, "tp5")
            if not r:
                continue
            legs = 0 if r["sonuc"] == "TP" else 1
            r["net"] -= SLIP * legs / r["sp"]
            j = int(np.searchsorted(c.t, ev["t"]))
            r["vol24"] = float(vq[max(0, j - 24):j].sum())
            r["volr"] = ev["volr"] or 0.0
            r["t_sig"] = ev["t"] + 5 * 3600
            trades.append(r)
    trades.sort(key=lambda r: (r["t_sig"], -r["vol24"]))
    return trades, t_split, created


def simulate(trades, maxn, maxdir, risk, prio, risk_cap=None, start=START, t_split=None):
    """Zaman çizelgesi: sinyal anında yer varsa pozisyon açılır (o anki bakiyeye göre), çıkışta kâr/zarar yazılır."""
    groups = defaultdict(list)
    for r in trades:
        groups[r["t_sig"]].append(r)
    times = sorted(groups)
    bal, peak, mdd, low = start, start, 0.0, start
    acik = []                       # (t_out, r, risk_usdt)
    alinan, atlanan = [], 0
    bal_split = None
    eq_curve = []
    seri = mxseri = 0
    max_open_risk = 0.0

    def close_until(t):
        nonlocal bal, peak, mdd, low, seri, mxseri, bal_split
        acik.sort(key=lambda x: x[0])
        while acik and acik[0][0] <= t:
            t_out, r, ru = acik.pop(0)
            if t_split and bal_split is None and t_out >= t_split:
                bal_split = bal
            bal += ru * r["net"]
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
            seri = seri + 1 if r["net"] <= 0 else 0
            mxseri = max(mxseri, seri)
            eq_curve.append((t_out, bal))

    for t in times:
        close_until(t)
        if t_split and bal_split is None and t >= t_split:
            bal_split = bal
        cand = groups[t]
        if prio == "hacim":
            cand = sorted(cand, key=lambda r: -r["vol24"])
        elif prio == "kirilim":
            cand = sorted(cand, key=lambda r: -r["volr"])
        for r in cand:
            if len(acik) >= maxn or any(x[1]["inst"] == r["inst"] for x in acik):
                atlanan += 1
                continue
            if maxdir and sum(1 for x in acik if x[1]["dir"] == r["dir"]) >= maxdir:
                atlanan += 1
                continue
            ru = bal * risk / 100
            if risk_cap and (sum(x[2] for x in acik) + ru) > bal * risk_cap / 100:
                atlanan += 1
                continue
            acik.append((r["t_out"], r, ru))
            alinan.append(r)
            max_open_risk = max(max_open_risk, sum(x[2] for x in acik) / bal * 100)
    close_until(float("inf"))
    if bal_split is None:
        bal_split = bal
    return dict(son=bal, mdd=mdd, low=low, n=len(alinan), atlanan=atlanan, seri=mxseri,
                egit=(bal_split / start - 1) * 100, dogr=(bal / bal_split - 1) * 100,
                curve=eq_curve, alinan=alinan, max_open_risk=max_open_risk)


def monte_carlo(rs, risk, n=2000, seed=1):
    """Bootstrap: aynı sayıda işlem, gerçek işlemlerden rastgele (yerine koyarak) seçilip sırayla bileşik uygulanır.
    Hem işlem sırasının hem de hangi işlemlerin geldiğinin şansa bağlı etkisini gösterir."""
    rnd = random.Random(seed)
    sons, mdds, lows = [], [], []
    for _ in range(n):
        seq = [rnd.choice(rs) for _ in rs]      # yerine koyarak örnekleme (bootstrap)
        bal = peak = START
        mdd = 0.0
        low = START
        for x in seq:
            bal *= 1 + risk / 100 * x
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
        sons.append(bal)
        mdds.append(mdd)
        lows.append(low)
    q = lambda a, p: sorted(a)[int(p * (len(a) - 1))]
    return dict(son5=q(sons, 0.05), son50=q(sons, 0.5), son95=q(sons, 0.95), mdd50=q(mdds, 0.5),
                mdd95=q(mdds, 0.95), low5=q(lows, 0.05), kayip=sum(1 for s in sons if s < START) / n * 100)


def main():
    T0 = time.time()
    trades, t_split, created = build_trades()
    tr_days = T.DAYS - T.TEST_DAYS
    out("# Portföy ve bütçe kuralları testi — günlük trend stratejisi")
    out(f"{len(trades)} sinyal (dolan limit emirler), son {T.DAYS} gün. 100 USDT başlangıç, bileşik: her işlemin riski o anki "
        f"bakiyeye göre. Eğitim ilk {tr_days} gün, doğrulama son {T.TEST_DAYS} gün. Kurgu: günlük kırılım (EMA50), sabah fiyatına "
        "limit, stop seviye − 0,5 ATR, TP 5R. Komisyon, long funding ve stoplarda %0,05 kayma dahil. "
        "\"Düşüş\": bakiyenin zirveden en fazla geri çekilmesi (kapanan işlemlere göre).")
    out()
    rows = []
    for risk in (1.0, 2.0):
        for maxn in (3, 5, 8):
            for maxdir in (None, 3):
                if maxdir and maxdir >= maxn:
                    continue
                for prio in ("hacim", "kirilim"):
                    for cap in (None, 8.0):
                        if cap and cap >= maxn * risk:
                            continue
                        s = simulate(trades, maxn, maxdir, risk, prio, cap, t_split=t_split)
                        rows.append(((risk, maxn, maxdir, prio, cap), s))

    def ad(k):
        risk, maxn, maxdir, prio, cap = k
        return (f"%{risk:g} risk · en fazla {maxn} pozisyon · " + (f"aynı yönde en fazla {maxdir} · " if maxdir else "") +
                ("öncelik: 24s hacim" if prio == "hacim" else "öncelik: kırılım hacmi") +
                (f" · toplam açık risk ≤ %{cap:g}" if cap else ""))

    head = ("| Kurallar | Yıl sonu bakiye | Eğitim dönemi getiri | Doğrulama dönemi getiri | En büyük düşüş | "
            "En düşük bakiye | İşlem / atlanan | En uzun kayıp serisi | Aynı anda en fazla açık risk |\n"
            "|---|---|---|---|---|---|---|---|---|")
    for risk in (1.0, 2.0):
        out(f"## %{risk:g} risk")
        out(head)
        for k, s in sorted([x for x in rows if x[0][0] == risk], key=lambda x: -x[1]["son"]):
            out(f"| {ad(k)} | {s['son']:.0f} USDT | %{s['egit']:+.0f} | %{s['dogr']:+.0f} | %{s['mdd']:.0f} | "
                f"{s['low']:.0f} USDT | {s['n']} / {s['atlanan']} | {s['seri']} | %{s['max_open_risk']:.0f} |")
        out()

    # Seçim: eğitim getirisi / en büyük düşüş (yalnızca eğitim dönemine bakarak), %2 risk içinden
    def egitim_skor(k):
        risk, maxn, maxdir, prio, cap = k
        s = simulate([r for r in trades if r["t_sig"] < t_split], maxn, maxdir, risk, prio, cap)
        return (s["son"] / START - 1) * 100 / max(s["mdd"], 1.0), s
    adaylar = [(egitim_skor(k), k, s) for k, s in rows if k[0] == 2.0]
    adaylar.sort(key=lambda x: -x[0][0])
    (_, es), k, s = adaylar[0]
    out("## Seçilen kurgu (eğitim döneminde getiri / düşüş oranı en iyi, %2 risk)")
    out(f"**{ad(k)}**")
    out(f"- Eğitim döneminde (tek başına, 100 USDT'den): %{(es['son'] / START - 1) * 100:+.0f} getiri, en büyük düşüş %{es['mdd']:.0f}")
    out(f"- Tüm yıl: 100 → **{s['son']:.0f} USDT**, eğitim %{s['egit']:+.0f}, doğrulama %{s['dogr']:+.0f}, "
        f"en büyük düşüş %{s['mdd']:.0f}, en düşük bakiye {s['low']:.0f} USDT, {s['n']} işlem "
        f"(haftada ~{s['n'] / T.DAYS * 7:.1f}), en uzun kayıp serisi {s['seri']}")
    ay = defaultdict(lambda: [None, None])
    for t, b in s["curve"]:
        key = datetime.fromtimestamp(t, T.TR).strftime("%Y-%m")
        if ay[key][0] is None:
            ay[key][0] = b
        ay[key][1] = b
    prev = START
    parts = []
    for key in sorted(ay):
        son = ay[key][1]
        parts.append(f"{key} %{(son / prev - 1) * 100:+.0f}")
        prev = son
    out("- Aylık getiri: " + " · ".join(parts))
    out(f"- Artı kapanan ay: {sum(1 for p_ in parts if p_.split('%')[1].startswith('+'))}/{len(parts)}")
    mc = monte_carlo([r["net"] for r in s["alinan"]], k[0])
    out(f"- **Kötü şans simülasyonu** (gerçek işlemlerden rastgele seçilmiş 2.000 farklı yıl): yıl sonu bakiye en kötü %5'te "
        f"{mc['son5']:.0f} USDT, ortada {mc['son50']:.0f}, en iyi %5'te {mc['son95']:.0f}. En büyük düşüş ortada "
        f"%{mc['mdd50']:.0f}, en kötü %5'te %{mc['mdd95']:.0f}. Bakiyenin yıl içinde inebileceği en düşük seviye "
        f"(en kötü %5): {mc['low5']:.0f} USDT. Yılı zararla kapatma ihtimali: %{mc['kayip']:.0f}")
    out()
    out("İlk 5 aday (eğitim skoruna göre):")
    for (sk, es_), kk, ss in adaylar[:5]:
        out(f"- {ad(kk)}: eğitim skoru {sk:.2f} · yıl sonu {ss['son']:.0f} USDT · doğrulama %{ss['dogr']:+.0f} · düşüş %{ss['mdd']:.0f}")
    out()
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        with open(OUT, "w") as f:
            f.write("\n".join(lines) + "\n")
