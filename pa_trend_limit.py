"""
Günlük trend stratejisi: limit giriş türleri ve bütçe (pozisyon büyüklüğü) planları. Mesaj göndermez.
Çıktı: trend_limit.md
- Kurgu: günlük kırılım (EMA50, 700 günlük geçmişten), stop kırılan seviye − 0,5 günlük ATR, TP 5R, BTC filtresi yok.
- Giriş: sabah piyasa | sabah fiyatına limit | sabah fiyatı ∓ 0,25 / 0,5 günlük ATR limit (48 saat geçerli) |
  kırılan seviyeye limit (10 gün geçerli). Piyasa emirlerine %0,05 kayma eklenir.
- Bütçe: 100 USDT başlangıç, bileşik. Planlar: (a) bakiyenin %10'u × 10 kaldıraç (pozisyon = bakiye),
  (b) işlem başı %1 risk, (c) %2 risk. Aynı anda en fazla 5 pozisyon, coin başına 1.
"""
import sys
import time
from collections import defaultdict
from datetime import datetime

import pa_trend_bt as T
import pa_trend_ema as E

OUT = "trend_limit.md"
SLIP = 0.05
ENTRIES = [("sabah", "sabah 08:00 piyasa"), ("lim_s0", "limit @sabah fiyatı"),
           ("lim_s0.25", "limit @sabah fiyatı ∓ 0,25 ATR"), ("lim_s0.5", "limit @sabah fiyatı ∓ 0,5 ATR"),
           ("limit", "limit @kırılan seviye")]
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def net_slip(r, entry):
    if entry == "x":                      # zaten kaymalı
        return r["net"]
    legs = (1 if entry == "sabah" else 0) + (0 if r["sonuc"] == "TP" else 1)
    return r["net"] - SLIP * legs / r["sp"]


def compound(pf, entry, plan, start=100.0):
    """Bileşik bakiye simülasyonu. Pozisyon girişte o anki (gerçekleşmiş) bakiyeye göre boyutlanır."""
    evs = []
    for i, r in enumerate(pf):
        evs.append((r["t_in"], 0, i))
        evs.append((r["t_out"], 1, i))
    evs.sort()
    bal, peak, mdd, low = start, start, 0.0, start
    size, worst, maxnot = {}, 0.0, 0.0
    acik = set()
    for t, kind, i in evs:
        r = pf[i]
        if kind == 0:
            if plan == "kaldirac":
                notional = bal * 0.10 * 10
            else:
                notional = bal * plan / r["sp"]
            size[i] = notional
            acik.add(i)
            maxnot = max(maxnot, sum(size[j] for j in acik) / bal if bal > 0 else 0)
        else:
            acik.discard(i)
            pnl = size[i] * net_slip(r, entry) * r["sp"] / 100
            worst = min(worst, pnl / max(bal, 1e-9) * 100)
            bal += pnl
            if bal <= 0:
                return dict(son=0.0, mdd=100.0, low=0.0, worst=worst, maxnot=maxnot, batti=True)
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
    return dict(son=bal, mdd=mdd, low=low, worst=worst, maxnot=maxnot, batti=False)


class NoBtc:
    def dir_at(self, t):
        return 0


def main():
    T0 = time.time()
    data, created = T.load()
    t_start = created - T.DAYS * 86400
    t_split = created - T.TEST_DAYS * 86400
    coins = {k: T.Coin(k, v) for k, v in data.items()}
    daily = E.load_daily(list(coins))
    evs = []
    for k, c in coins.items():
        if k not in daily:
            continue
        m = E.ema_map(daily[k], 50)
        evs += [e for e in T.events(c, "1D", NoBtc(), ema_n=50, ema_map=m) if e["t"] >= t_start]
    out("# Limit giriş ve bütçe planı testi — günlük trend stratejisi")
    out(f"{len(coins)} coin, son {T.DAYS} gün (eğitim ilk {T.DAYS - T.TEST_DAYS} / doğrulama son {T.TEST_DAYS} gün). "
        "Kurgu: günlük kapanışla kırılım, EMA50, stop kırılan seviye − 0,5 günlük ATR, TP 5R. "
        f"Komisyon, long funding ve piyasa emirlerinde %{SLIP} kayma dahil. Portföy: coin başına 1, aynı anda en fazla 5.")
    out()
    out("## 1) Giriş türleri")
    out("| Giriş | Sinyal / dolan / dolmayan | Kazanan | Tüm işlemler net R | Eğitim / doğrulama net R | "
        "Portföy 5 net R (eğitim / doğrulama) | Portföy en büyük düşüş R | Ort. stop % |")
    out("|---|---|---|---|---|---|---|---|")
    pfs = {}
    for entry, ad in ENTRIES:
        rs, dolmadi = [], 0
        for ev in evs:
            f = T.fill(ev, coins[ev["inst"]], entry, 0.5)
            if f == "dolmadi":
                dolmadi += 1
                continue
            if isinstance(f, str):
                continue
            r = T.simulate(ev, coins[ev["inst"]], f, "tp5")
            if r:
                r["net"] = net_slip(r, entry)
                rs.append(r)
        al = T.stats(rs, T.DAYS)
        tr = sum(r["net"] for r in rs if r["t_in"] < t_split)
        te = sum(r["net"] for r in rs if r["t_in"] >= t_split)
        pf, dd = T.portfolio(rs, 5)
        pt = sum(r["net"] for r in pf if r["t_in"] < t_split)
        pv = sum(r["net"] for r in pf if r["t_in"] >= t_split)
        sp = sum(r["sp"] for r in rs) / len(rs) if rs else 0
        pfs[entry] = pf
        out(f"| {ad} | {len(evs)} / {len(rs)} / {dolmadi} | %{al['win']:.0f} | {al['net']:+.1f} | {tr:+.1f} / {te:+.1f} | "
            f"{pt + pv:+.1f} ({pt:+.1f} / {pv:+.1f}) | {dd:.1f} | {sp:.1f} |")
    out()
    out("## 2) Bütçe planları (100 USDT başlangıç, bileşik, portföy en fazla 5)")
    out("| Giriş | Plan | Son bakiye | En düşük bakiye | En büyük düşüş % | Tek işlemde en büyük kayıp % | "
        "Aynı anda en büyük pozisyon / bakiye |")
    out("|---|---|---|---|---|---|---|")
    for entry, ad in ENTRIES:
        pf = sorted(pfs[entry], key=lambda r: r["t_in"])
        for plan, pad in (("kaldirac", "%10 teminat × 10x (pozisyon = bakiye)"), (1.0, "%1 risk"), (2.0, "%2 risk")):
            c = compound(pf, "x", plan)        # net zaten kaymalı
            son = "BATTI" if c["batti"] else f"{c['son']:.0f} USDT"
            out(f"| {ad} | {pad} | {son} | "
                f"{c['low']:.0f} USDT | %{c['mdd']:.0f} | %{c['worst']:.1f} | {c['maxnot']:.1f}x |")
    out()
    # Kayıp serisi örneği
    pf = sorted(pfs["lim_s0"], key=lambda r: r["t_out"])
    seri = mx = 0
    for r in pf:
        seri = seri + 1 if r["net"] <= 0 else 0
        mx = max(mx, seri)
    sps = sorted(r["sp"] for r in pf)
    out(f"- Limit @sabah fiyatı, portföy: en uzun kayıp serisi {mx} işlem; stop mesafesi ortanca %{sps[len(sps) // 2]:.1f}, "
        f"en büyük %{sps[-1]:.1f}. Pozisyon = bakiye iken her stop bakiyenin stop mesafesi kadarını kaybettirir.")
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
