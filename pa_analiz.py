"""
Kapsamlı testin sağlamlık analizi (pa_backtest.py'nin önbelleğe aldığı veriyle). Mesaj göndermez.
Sorular: Kazanç tek bir piyasa olayına mı dayanıyor? Long/short dağılımı? Aylara göre tutarlı mı?
Gerçekçi pozisyon sınırıyla (coin başına 1, aynı anda en fazla N işlem) sonuç ne olur?
Çıktı: analiz.md
"""
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pa_scan_once as p
import pa_backtest as bt

TR = timezone(timedelta(hours=3))
OUT = "analiz.md"
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def trades(b, evs, cfg, t0, t1):
    used, res = set(), []
    for g in evs:
        if g["t"] < t0 or g["t"] >= t1:
            continue
        k = (g["inst"], g["key"])
        if k in used or not bt.passes(g, cfg):
            continue
        used.add(k)
        r = bt.simulate(g, cfg, b.arr(g["inst"]))
        if r in ("dolmadi", "elendi"):
            continue
        res.append(dict(t=g["t"], x=r[3], dir=g["dir"], inst=g["inst"], net=r[0], sonuc=r[2]))
    res.sort(key=lambda r: r["t"])
    return res


def portfoy(tr, maxn):
    """Coin başına tek pozisyon, aynı anda en fazla maxn pozisyon; sırayla gelen sinyaller."""
    acik, alinan = [], []
    for r in tr:
        acik = [a for a in acik if a["x"] > r["t"]]
        if len(acik) >= maxn or any(a["inst"] == r["inst"] for a in acik):
            continue
        acik.append(r)
        alinan.append(r)
    eq = mx = dd = 0.0
    for r in sorted(alinan, key=lambda r: r["x"]):
        eq += r["net"]
        mx = max(mx, eq)
        dd = max(dd, mx - eq)
    return alinan, dd


def max_concurrent(tr):
    ev = sorted([(r["t"], 1) for r in tr] + [(r["x"], -1) for r in tr])
    c = m = 0
    for _, s in ev:
        c += s
        m = max(m, c)
    return m


def report(ad, tr, split):
    n = len(tr)
    if not n:
        out(f"### {ad}\nİşlem yok.\n")
        return
    net = sum(r["net"] for r in tr)
    L = [r for r in tr if r["dir"] == 1]
    S = [r for r in tr if r["dir"] == -1]
    gun = defaultdict(float)
    ay = defaultdict(lambda: [0, 0.0])
    for r in tr:
        dt = datetime.fromtimestamp(r["t"], TR)
        gun[dt.strftime("%d.%m.%Y")] += r["net"]
        ay[dt.strftime("%Y-%m")][0] += 1
        ay[dt.strftime("%Y-%m")][1] += r["net"]
    eniyi = sorted(gun.items(), key=lambda kv: kv[1], reverse=True)
    top3 = sum(v for _, v in eniyi[:3])
    out(f"### {ad}")
    out(f"- Toplam: {n} işlem, net **{net:+.1f}R** (eğitim {sum(r['net'] for r in tr if r['t'] < split):+.1f}R, "
        f"doğrulama {sum(r['net'] for r in tr if r['t'] >= split):+.1f}R)")
    out(f"- Long: {len(L)} işlem, {sum(r['net'] for r in L):+.1f}R · Short: {len(S)} işlem, {sum(r['net'] for r in S):+.1f}R")
    out(f"- En iyi 3 gün: " + ", ".join(f"{k} ({v:+.1f}R)" for k, v in eniyi[:3]) +
        f" → toplam {top3:+.1f}R. **Bu 3 gün olmadan: {net - top3:+.1f}R**")
    out(f"- Aynı anda açık en fazla işlem: {max_concurrent(tr)}")
    out("- Aylık: " + " · ".join(f"{k}: {v[0]} işlem {v[1]:+.1f}R" for k, v in sorted(ay.items())))
    for mn in (3, 5, 10):
        al, dd = portfoy(tr, mn)
        out(f"- Gerçekçi portföy (coin başına 1, aynı anda en fazla {mn}): {len(al)} işlem, "
            f"net **{sum(r['net'] for r in al):+.1f}R**, en büyük düşüş {dd:.1f}R "
            f"(eğitim {sum(r['net'] for r in al if r['t'] < split):+.1f}R / doğrulama "
            f"{sum(r['net'] for r in al if r['t'] >= split):+.1f}R)")
    out()


def main():
    days = int(os.getenv("PA_BACKTEST", "120") or 120)
    test_days = int(os.getenv("PA_TEST_DAYS", "40") or 40)
    data, created = bt.load_data(days)
    t0, split, t1 = created - days * 86400, created - test_days * 86400, created + 86400
    b = bt.Bench(data)
    son = dict(entry="limit_kapanis", stop="fitil", tp="t_y15", btc=False, vol=0.0, conf=())
    cfgs = [
        ("Son ayar: limit @kapanış · fitil stop · tek TP %15", son),
        ("Son ayar + hacim ≥1x", dict(son, vol=1.0)),
        ("Son ayar + sadece ilk test", dict(son, conf=("ilk_test",))),
        ("Son ayar + hacim ≥1x + sadece ilk test", dict(son, vol=1.0, conf=("ilk_test",))),
        ("Tek TP %10 (diğerleri aynı)", dict(son, tp="t_y10")),
        ("Tek TP %15 · stop son tepe ötesi", dict(son, stop="son_tepe")),
        ("Başlangıç: piyasa · fitil · kısmi 1R + seviye", dict(bt.BASE)),
    ]
    out("# Sağlamlık analizi")
    out(f"{len(data)} coin, son {days} gün; doğrulama son {test_days} gün. Seviye: önceki tepe/dip. "
        f"Portföy satırları: aynı coinde açık işlem varken yeni sinyal alınmaz, toplam açık işlem sınırı uygulanır.")
    out()
    for stf, rej in (("4H", "30m"), ("4H", "1H"), ("1D", "1H")):
        evs = b.gen(stf, rej, "onceki_tepe")
        out(f"## {stf}→{rej}")
        for ad, cfg in cfgs:
            report(ad, trades(b, evs, cfg, t0, t1), split)
            with open(OUT, "w") as f:
                f.write("\n".join(lines) + "\n")


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
