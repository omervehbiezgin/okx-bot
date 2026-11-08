"""
Trend stratejisi geliştirme testi (botun mevcut kuralları üzerinde, sadece portföy kuralları değişir).
Mesaj göndermez, emir vermez. Çıktı: gelistir_sonuc.md

Sorular:
 1) 8 yer dolduğunda öncelik: 24s hacim (bugünkü bot) / kırılım hacmi oranı / kırılım mumu boyu / ikisinin birleşimi /
    rastgele (karşılaştırma için)
 2) Yer sayısı × işlem başı risk: 6×%1,33 · 8×%1 · 10×%0,8 · 12×%0,67 · 16×%0,5 (toplam risk ~%8) ve 12×%1 (daha agresif)
 3) Aynı yöne en fazla N pozisyon: sınırsız / 6 / 5 / 4 (8 yerle)
Seçim sadece eğitim döneminde (getiri / en büyük düşüş); doğrulama son 245 gün. 100 USDT, bileşik, acil fren 60 USDT.
Sinyal ve çıkış kuralları botla aynı: kapanışta giriş, stop seviye ∓ 0,5 ATR, günlük stop 10 gün dibi/tepesi, 60 gün.
"""
import sys
import time
import random
from collections import defaultdict
from datetime import datetime

import numpy as np

import pa_final as F
import pa_kayip as KY

OUT = "gelistir_sonuc.md"
START, KILL = 100.0, 60.0
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


def run(rs, t0, t_split, risk, maxn, key, dir_cap=None, rnd=None, until=None):
    """Portföy simülasyonu (pa_final.portfolio ile aynı mantık + öncelik anahtarı + yön sınırı)."""
    rs = [r for r in rs if r["t_sig"] >= t0 and (until is None or r["t_sig"] < until)]
    groups = defaultdict(list)
    for r in rs:
        groups[r["t_sig"]].append(r)
    bal = peak = START
    mdd = 0.0
    acik = []
    bal_split = None
    alinan = atlanan = 0

    def close_until(t):
        nonlocal bal, peak, mdd, bal_split
        acik.sort(key=lambda x: x[0])
        while acik and acik[0][0] <= t:
            t_out, r, ru = acik.pop(0)
            if bal_split is None and t_out >= t_split:
                bal_split = bal
            bal += ru * r["net"]
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)

    for t in sorted(groups):
        close_until(t)
        if bal_split is None and t >= t_split:
            bal_split = bal
        if bal < KILL:
            continue
        g = groups[t]
        if rnd is not None:
            g = g[:]
            rnd.shuffle(g)
        else:
            g = sorted(g, key=key)
        for r in g:
            if any(x[1]["inst"] == r["inst"] for x in acik):
                continue
            if len(acik) >= maxn:
                atlanan += 1
                continue
            if dir_cap is not None and sum(1 for x in acik if x[1]["dir"] == r["dir"]) >= dir_cap:
                atlanan += 1
                continue
            acik.append((r["t_out"], r, bal * risk / 100))
            alinan += 1
    close_until(float("inf"))
    bal_split = bal_split or bal
    return dict(son=bal, mdd=mdd, egit=(bal_split / START - 1) * 100, dogr=(bal / bal_split - 1) * 100,
                alinan=alinan, atlanan=atlanan)


def train_score(rs, t0, t_split, **kw):
    s = run(rs, t0, t_split, until=t_split, **kw)
    return (s["son"] / START - 1) * 100 / max(s["mdd"], 1.0)


def main():
    T0 = time.time()
    data, created = F.T.load()
    t0 = created - F.DAYS * 86400
    t_split = created - F.TEST_DAYS * 86400
    coins = {(k, 0): F.Coin(k, v, 0) for k, v in data.items()}
    btc = F.Btc(coins[("BTC-USDT-SWAP", 0)])
    evs = []
    for c in coins.values():
        evs += F.events(c, btc)
    rs = F.trades_for(coins, evs, 0, "don10", False)
    feat = {}
    for ev in evs:
        fz = KY.features(coins[(ev["inst"], 0)], ev, btc)
        if fz:
            feat[(ev["inst"], ev["t"])] = fz
    for r in rs:
        fz = feat.get((r["inst"], r["t_sig"]), {})
        r["hacim"] = fz.get("hacim", np.nan)
        r["mum"] = fz.get("mum_boyu", np.nan)
    # birleşik sıra: her gün içindeki sıra yerine tüm eğitim dağılımına göre yüzdelik (geleceğe bakmadan: eğitim eşikleri)
    tr_h = np.array([r["hacim"] for r in rs if r["t_sig"] < t_split and np.isfinite(r["hacim"])])
    tr_m = np.array([r["mum"] for r in rs if r["t_sig"] < t_split and np.isfinite(r["mum"])])
    for r in rs:
        ph = (tr_h < r["hacim"]).mean() if np.isfinite(r["hacim"]) else 0
        pm = (tr_m < r["mum"]).mean() if np.isfinite(r["mum"]) else 0
        r["birlesik"] = ph + pm

    sp0 = datetime.fromtimestamp(t0).strftime("%d.%m.%Y")
    sp1 = datetime.fromtimestamp(t_split).strftime("%d.%m.%Y")
    out("# Trend stratejisi — geliştirme testi")
    out(f"{len(data)} coin, {len(rs)} işlem. Eğitim {sp0} – {sp1}, doğrulama son {F.TEST_DAYS} gün (veri "
        f"{datetime.fromtimestamp(created).strftime('%d.%m.%Y')} tarihine kadar). Seçim sadece eğitime göre "
        f"(getiri ÷ en büyük düşüş). 100 USDT başlangıç, bileşik, acil fren 60 USDT. Kurallar botla aynı.")
    out()

    def nan_last(v):
        return -v if np.isfinite(v) else 1e9

    KEYS = {
        "24s hacim (bugünkü bot)": lambda r: -r["vol24"],
        "kırılım hacmi oranı": lambda r: nan_last(r["hacim"]),
        "kırılım mumu boyu": lambda r: nan_last(r["mum"]),
        "hacim oranı + mum boyu": lambda r: -r["birlesik"],
    }
    HEAD = ("| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |\n"
            "|---|---|---|---|---|---|")

    def row(ad, **kw):
        sc = train_score(rs, t0, t_split, **kw)
        s = run(rs, t0, t_split, **kw)
        out(f"| {ad} | {sc:.2f} | {s['son']:.0f} | {s['egit']:+.0f}% / {s['dogr']:+.0f}% | %{s['mdd']:.0f} | "
            f"{s['alinan']} / {s['atlanan']} |")
        return sc, s

    # 1) Öncelik
    out("## 1) 8 yer dolunca öncelik (8 yer × %1)")
    out(HEAD)
    sc1 = {}
    for ad, k in KEYS.items():
        sc1[ad], _ = row(ad, risk=1.0, maxn=8, key=k)
    rr = [run(rs, t0, t_split, 1.0, 8, None, rnd=random.Random(i)) for i in range(30)]
    rtr = [train_score(rs, t0, t_split, risk=1.0, maxn=8, key=None, rnd=random.Random(i)) for i in range(30)]
    out(f"| rastgele sıra (30 deneme ortalaması) | {np.mean(rtr):.2f} | {np.mean([x['son'] for x in rr]):.0f} "
        f"(en kötü {min(x['son'] for x in rr):.0f}, en iyi {max(x['son'] for x in rr):.0f}) | "
        f"{np.mean([x['egit'] for x in rr]):+.0f}% / {np.mean([x['dogr'] for x in rr]):+.0f}% | "
        f"%{np.mean([x['mdd'] for x in rr]):.0f} | - |")
    best_k = max(sc1, key=sc1.get)
    out(f"\nEğitimde en iyi öncelik: **{best_k}**. Rastgele sıranın eğitim skoru {np.mean(rtr):.2f} "
        f"(30 denemede {min(rtr):.2f}–{max(rtr):.2f}).")
    out()
    save()

    # 2) Yer × risk
    out("## 2) Yer sayısı × işlem başı risk")
    for kad in ("24s hacim (bugünkü bot)", best_k) if best_k != "24s hacim (bugünkü bot)" else ("24s hacim (bugünkü bot)",):
        out(f"### Öncelik: {kad}")
        out(HEAD)
        for n_, rk in ((6, 1.33), (8, 1.0), (10, 0.8), (12, 0.67), (16, 0.5), (12, 1.0)):
            row(f"{n_} yer × %{rk}", risk=rk, maxn=n_, key=KEYS[kad])
        out()
    save()

    # 3) Yön sınırı
    out("## 3) Aynı yöne en fazla N pozisyon (8 yer × %1)")
    out(HEAD)
    for kad in dict.fromkeys(("24s hacim (bugünkü bot)", best_k)):
        for cap in (None, 6, 5, 4):
            row(f"{kad} · yön sınırı {'yok' if cap is None else cap}", risk=1.0, maxn=8, key=KEYS[kad], dir_cap=cap)
    out()

    # 4) Eğitimde en iyi birleşim
    out("## 4) Eğitime göre en iyi birleşim (tüm ızgara)")
    grid = []
    for kad, k in KEYS.items():
        for n_, rk in ((6, 1.33), (8, 1.0), (10, 0.8), (12, 0.67), (16, 0.5)):
            for cap in (None, n_ - 2, n_ - 3):
                sc = train_score(rs, t0, t_split, risk=rk, maxn=n_, key=k, dir_cap=cap)
                grid.append((sc, kad, n_, rk, cap))
    grid.sort(key=lambda x: -x[0])
    out(HEAD)
    base = None
    for sc, kad, n_, rk, cap in grid[:8]:
        row(f"{kad} · {n_}×%{rk} · yön sınırı {cap or 'yok'}", risk=rk, maxn=n_, key=KEYS[kad], dir_cap=cap)
    out("\n**Bugünkü bot (karşılaştırma):**")
    out(HEAD)
    row("24s hacim · 8×%1 · yön sınırı yok", risk=1.0, maxn=8, key=KEYS["24s hacim (bugünkü bot)"])
    out()
    # 5) Sağlamlık: sonuç hangi sinyalin yer bulduğuna çok duyarlı; yön sınırının etkisini 30 rastgele sırada ölç
    out("## 5) Sağlamlık kontrolü: yön sınırı, 30 rastgele sinyal sırasında (8 yer × %1)")
    out("| Yön sınırı | Ortalama son bakiye | Ortalama en büyük düşüş | Ortalama eğitim / doğrulama getiri | "
        "Sınırsıza göre düşüşü azalttığı deneme |")
    out("|---|---|---|---|---|")
    ref = [run(rs, t0, t_split, 1.0, 8, None, rnd=random.Random(100 + i)) for i in range(30)]
    for cap in (None, 6, 5, 4):
        xs = [run(rs, t0, t_split, 1.0, 8, None, dir_cap=cap, rnd=random.Random(100 + i)) for i in range(30)]
        better = sum(1 for a, b in zip(xs, ref) if a["mdd"] < b["mdd"] - 0.5)
        out(f"| {'yok' if cap is None else cap} | {np.mean([x['son'] for x in xs]):.0f} | "
            f"%{np.mean([x['mdd'] for x in xs]):.0f} | {np.mean([x['egit'] for x in xs]):+.0f}% / "
            f"{np.mean([x['dogr'] for x in xs]):+.0f}% | {'-' if cap is None else f'{better}/30'} |")
    out()
    out("Not: Fonlama oranına göre filtre test edilemedi; OKX 2 yıllık fonlama geçmişi vermiyor (yaklaşık 3 ay). "
        "Testte longlara sabit fonlama maliyeti eklenmişti.")
    out(f"\nSüre: {(time.time() - T0) / 60:.0f} dk")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        save()
