"""
Günlük trend stratejisi — kapsamlı final testi (2 yıl). Mesaj göndermez, canlı bota dokunmaz. Çıktı: final_sonuc.md

Strateji çekirdeği (sabit): günlük kapanış son onaylı tepenin üstünde (long) / dibin altında (short), kapanış EMA50'nin
doğru tarafında. Stop: kırılan seviye ∓ 0,5 günlük ATR. Giriş: limit emir (o anki fiyata). Bot otomatik çalışır.

Aşamalar (her aşamada seçim SADECE eğitim dönemine göre; son TEST_DAYS gün doğrulama):
  A) Giriş saati: kapanışta (03:00 TR, Tokyo açılışı), +1, +2 (Hong Kong/Şangay), +5, +7/+8 (Londra yaz/kış),
     +9, +13/+14 (New York), kademeli 03/08/13 ve oturumlara göre kademeli (Asya/Avrupa/ABD)
  B) Çıkış × BTC filtresi: TP 5R | TP 5R + 2R'de stop girişe | günlük stop 10/20 gün dibi | günlük stop + 2R'de
     stop girişe | yarısı 3R + kalanı günlük stop | OKX iz süren stop 2/3 × ATR (sürekli). BTC filtresi açık/kapalı.
  C) Portföy ve risk: (risk, en fazla pozisyon) × düşüşte riski yarıya indirme (zirveden %15+). Acil fren: bakiye
     60 USDT altına inerse yeni işlem açılmaz.
  D) Günlük mumun kapanış saati: 03:00 / 09:00 / 15:00 / 21:00 TR ve dördü birlikte.
  E) Şans seviyesi: mumları karıştırılmış verilerle aynı ayar.
  F) Bootstrap: aynı işlemlerden rastgele kurulmuş 2.000 farklı dönem.
Maliyetler: maker %0,02 (limit giriş, TP), taker %0,05 + %0,05 kayma (stop / süre çıkışı), long funding 8 saatte %0,01.
"""
import sys
import time
import random
import bisect
from collections import defaultdict
from datetime import datetime

import numpy as np

import pa_trend_bt as T

p = T.p
T.DAYS, T.WARM, T.CACHE = 730, 70, "final_cache.json.gz"
DAYS, TEST_DAYS = 730, 245
OUT = "final_sonuc.md"
MAKER, TAKER, SLIP, FUND = 0.02, 0.05, 0.05, 0.01
K, SK = 3, 0.5
MAXH = 60 * 24
START = 100.0
KILL = 60.0
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


def first_true(b):
    if b.size == 0:
        return None
    i = int(np.argmax(b))
    return i if b[i] else None


def agg(s, sec, off):
    """1H mumlardan, 'off' saniye kaydırılmış sınırlarla büyük mum (yalnızca tam dolanlar)."""
    t = np.array(s["t"], dtype=np.int64)
    key = (t - off) // sec
    outd = dict(t=[], o=[], h=[], l=[], c=[], v=[], sec=sec)
    need = sec // 3600
    i, n = 0, len(t)
    while i < n:
        j = i
        while j < n and key[j] == key[i]:
            j += 1
        if j - i == need:
            outd["t"].append(int(key[i] * sec + off))
            outd["o"].append(s["o"][i])
            outd["h"].append(max(s["h"][i:j]))
            outd["l"].append(min(s["l"][i:j]))
            outd["c"].append(s["c"][j - 1])
            outd["v"].append(sum(s["v"][i:j]))
        i = j
    return outd


class Coin:
    def __init__(self, inst, s1, off=0):
        self.inst, self.off = inst, off
        self.t = np.array(s1["t"], dtype=np.int64)
        self.o, self.h = np.array(s1["o"]), np.array(s1["h"])
        self.l, self.c = np.array(s1["l"]), np.array(s1["c"])
        v = np.array(s1["v"])
        cs = np.concatenate(([0.0], np.cumsum(v)))
        self.cs = cs
        self.D = agg(s1, 86400, off)
        self.atr = p.atr_arr(self.D)
        self.e50 = T.ema(self.D["c"], 50)
        dt = np.array(self.D["t"], dtype=np.int64)
        di = np.searchsorted(dt, self.t - 86400, side="right") - 1
        dl, dh = np.array(self.D["l"]), np.array(self.D["h"])
        self.don = {}
        for N in (10, 20):
            mn = np.full(len(dl), np.nan)
            mx = np.full(len(dh), np.nan)
            for k in range(N - 1, len(dl)):
                mn[k] = dl[k - N + 1:k + 1].min()
                mx[k] = dh[k - N + 1:k + 1].max()
            lo = np.full(len(self.t), np.nan)
            hi = np.full(len(self.t), np.nan)
            ok = di >= 0
            lo[ok], hi[ok] = mn[di[ok]], mx[di[ok]]
            self.don[N] = (lo, hi)

    def vol24(self, t):
        j = int(np.searchsorted(self.t, t))
        return float(self.cs[j] - self.cs[max(0, j - 24)])


class Btc:
    def __init__(self, coin):
        self.t, self.c, self.e = coin.D["t"], coin.D["c"], coin.e50

    def dir_at(self, t):
        i = bisect.bisect_right(self.t, t - 86400) - 1
        if i < 0 or self.e[i] is None:
            return 0
        return 1 if self.c[i] > self.e[i] else -1


def events(coin, btc):
    S = coin.D
    n = len(S["t"])
    if n < 60:
        return []
    h, l, c = S["h"], S["l"], S["c"]
    ph, pl = p.pivots(h, l, 0, n - 1, K)
    evs = []
    for d, piv in ((1, ph), (-1, pl)):
        pi, cur = 0, None
        for i in range(K + 1, n):
            while pi < len(piv) and piv[pi][0] <= i - K:
                cur = [piv[pi][0], piv[pi][1], False]
                pi += 1
            if cur is None or cur[2] or coin.atr[i] is None or coin.e50[i] is None:
                continue
            lvl = cur[1]
            if (c[i] - lvl) * d <= 0:
                continue
            cur[2] = True
            if (c[i] - coin.e50[i]) * d <= 0:
                continue
            tc = S["t"][i] + 86400
            evs.append(dict(inst=coin.inst, dir=d, lvl=lvl, t=tc, atr=coin.atr[i], btc=btc.dir_at(tc),
                            vol24=coin.vol24(tc), off=coin.off))
    return evs


def fill(ev, coin, delay):
    d = ev["dir"]
    stop = ev["lvl"] - d * SK * ev["atr"]
    j0 = int(np.searchsorted(coin.t, ev["t"] + delay * 3600))
    if j0 >= len(coin.t):
        return None
    e = float(coin.o[j0])
    if (e - stop) * d <= 0:
        return None
    sp = abs(e - stop) / e * 100
    if sp < T.MIN_SP or sp > T.MAX_SP:
        return None
    bad = coin.l[j0] <= stop if d == 1 else coin.h[j0] >= stop
    return dict(e=e, stop=stop, jf=j0, sp=sp, bad=bad)


def leg(coin, d, e, stop, sp, jf, a, b, eff, tp):
    H, L, O, C = coin.h[a:b], coin.l[a:b], coin.o[a:b], coin.c[a:b]
    adv, fav = (L, H) if d == 1 else (H, L)
    ks = first_true(adv <= eff) if d == 1 else first_true(adv >= eff)
    kt = None
    if tp is not None:
        kt = first_true(fav >= tp) if d == 1 else first_true(fav <= tp)
    R = abs(e - stop)
    if ks is not None and (kt is None or ks <= kt):
        px = min(O[ks], eff[ks]) if d == 1 else max(O[ks], eff[ks])
        g, fo, sl, k = (px - e) * d / R, TAKER, SLIP, ks
        son = "stop" if g <= 0 else "izsüren"
    elif kt is not None:
        g, fo, sl, k, son = abs(tp - e) / R, MAKER, 0.0, kt, "TP"
    else:
        k = b - a - 1
        g, fo, sl, son = (C[-1] - e) * d / R, TAKER, SLIP, "süre"
    hours = (a + k) - jf + 1
    fund = FUND * hours / 8 if d == 1 else 0.0
    return g - (MAKER + fo + sl + fund) / sp, g, son, int(coin.t[a + k])


def sim(ev, coin, f, ex):
    d, e, stop, sp, jf = ev["dir"], f["e"], f["stop"], f["sp"], f["jf"]
    R = abs(e - stop)
    if f["bad"]:
        g = -1.0
        return g - (MAKER + TAKER + SLIP) / sp, g, "stop", int(coin.t[jf])
    a = jf + 1
    b = min(len(coin.t), a + MAXH)
    if a >= b:
        return None
    eff = np.full(b - a, stop, dtype=float)
    if "don" in ex:
        N = 20 if "don20" in ex else 10
        lo, hi = coin.don[N]
        if d == 1:
            eff = np.maximum.accumulate(np.maximum(stop, np.nan_to_num(lo[a:b], nan=-np.inf)))
        else:
            eff = np.minimum.accumulate(np.minimum(stop, np.nan_to_num(hi[a:b], nan=np.inf)))
    if ex.startswith("tr"):                 # OKX iz süren stop: zirveden (dipten) m × günlük ATR geri çekilince kapanır
        m = float(ex[2])
        cb = m * ev["atr"]
        if d == 1:
            peak = np.maximum.accumulate(np.concatenate(([e], coin.h[a:b])))[:-1]
            tr = peak - cb
            if ex.endswith("a"):
                tr = np.where(peak >= e + R, tr, -np.inf)
            eff = np.maximum(eff, tr)
        else:
            peak = np.minimum.accumulate(np.concatenate(([e], coin.l[a:b])))[:-1]
            tr = peak + cb
            if ex.endswith("a"):
                tr = np.where(peak <= e - R, tr, np.inf)
            eff = np.minimum(eff, tr)
    if "be" in ex:
        fav = coin.h[a:b] if d == 1 else coin.l[a:b]
        kb = first_true(fav >= e + 2 * R) if d == 1 else first_true(fav <= e - 2 * R)
        if kb is not None and kb + 1 < len(eff):
            eff = eff.copy()
            eff[kb + 1:] = np.maximum(eff[kb + 1:], e) if d == 1 else np.minimum(eff[kb + 1:], e)
    if ex.startswith("tp5"):
        return leg(coin, d, e, stop, sp, jf, a, b, eff, e + d * 5 * R)
    if ex.startswith("hyb"):
        n1, g1, s1, t1 = leg(coin, d, e, stop, sp, jf, a, b, eff, e + d * 3 * R)
        n2, g2, s2, t2 = leg(coin, d, e, stop, sp, jf, a, b, eff, None)
        return (n1 + n2) / 2, (g1 + g2) / 2, s2 if s1 != "stop" else "stop", max(t1, t2)
    return leg(coin, d, e, stop, sp, jf, a, b, eff, None)


def trades_for(coins, evs, entry, ex, use_btc):
    res = []
    for ev in evs:
        if use_btc and ev["btc"] != ev["dir"]:
            continue
        c = coins[(ev["inst"], ev["off"])]
        delays = KAD.get(entry, (entry,))
        parts = []
        for dl in delays:
            f = fill(ev, c, dl)
            if f is None:
                continue
            r = sim(ev, c, f, ex)
            if r:
                parts.append((r, int(c.t[f["jf"]])))
        if not parts or (entry in KAD and len(parts) < len(KAD[entry])):
            continue
        net = sum(x[0][0] for x in parts) / len(parts)
        gross = sum(x[0][1] for x in parts) / len(parts)
        res.append(dict(inst=ev["inst"], dir=ev["dir"], t_sig=ev["t"] + (0 if entry in KAD else entry * 3600),
                        t_in=min(x[1] for x in parts), t_out=max(x[0][3] for x in parts), net=net, gross=gross,
                        sonuc=parts[0][0][2], vol24=ev["vol24"]))
    res.sort(key=lambda r: (r["t_sig"], -r["vol24"]))
    return res


def all_stats(rs, t0, t_split):
    rs = [r for r in rs if r["t_sig"] >= t0]
    n = len(rs)
    tr = sum(r["net"] for r in rs if r["t_sig"] < t_split)
    te = sum(r["net"] for r in rs if r["t_sig"] >= t_split)
    win = sum(1 for r in rs if r["gross"] > 0) / n * 100 if n else 0
    return dict(n=n, win=win, tr=tr, te=te, tot=tr + te, per=(tr + te) / n if n else 0)


def portfolio(rs, risk, maxn, t0, t_split, ddcut=False, kill=True):
    rs = [r for r in rs if r["t_sig"] >= t0]
    groups = defaultdict(list)
    for r in rs:
        groups[r["t_sig"]].append(r)
    bal = peak = low = START
    mdd = 0.0
    acik, alinan = [], []
    bal_split, killed = None, False
    seri = mx = 0
    curve = []

    def close_until(t):
        nonlocal bal, peak, low, mdd, seri, mx, bal_split
        acik.sort(key=lambda x: x[0])
        while acik and acik[0][0] <= t:
            t_out, r, ru = acik.pop(0)
            if bal_split is None and t_out >= t_split:
                bal_split = bal
            bal += ru * r["net"]
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
            seri = seri + 1 if r["net"] <= 0 else 0
            mx = max(mx, seri)
            curve.append((t_out, bal))

    for t in sorted(groups):
        close_until(t)
        if bal_split is None and t >= t_split:
            bal_split = bal
        if kill and bal < KILL:
            killed = True
            continue
        for r in sorted(groups[t], key=lambda r: -r["vol24"]):
            if len(acik) >= maxn or any(x[1]["inst"] == r["inst"] for x in acik):
                continue
            rk = risk / 2 if ddcut and (peak - bal) / peak > 0.15 else risk
            acik.append((r["t_out"], r, bal * rk / 100))
            alinan.append(r)
    close_until(float("inf"))
    if bal_split is None:
        bal_split = bal
    return dict(son=bal, mdd=mdd, low=low, n=len(alinan), seri=mx, killed=killed, alinan=alinan, curve=curve,
                egit=(bal_split / START - 1) * 100, dogr=(bal / bal_split - 1) * 100,
                egit_skor=(bal_split / START - 1) * 100 / max(mdd, 1.0))


def portfolio_train(rs, risk, maxn, t0, t_split, ddcut=False):
    """Seçim için: sadece eğitim dönemi işlemleriyle portföy (getiri / düşüş)."""
    s = portfolio([r for r in rs if r["t_sig"] < t_split], risk, maxn, t0, t_split + 10 ** 10, ddcut)
    return (s["son"] / START - 1) * 100 / max(s["mdd"], 1.0), s


def bootstrap(rs, risk, n=2000, seed=1):
    rnd = random.Random(seed)
    sons, mdds, lows = [], [], []
    for _ in range(n):
        bal = peak = low = START
        mdd = 0.0
        for _ in rs:
            x = rnd.choice(rs)
            bal *= 1 + risk / 100 * x
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
        sons.append(bal)
        mdds.append(mdd)
        lows.append(low)
    q = lambda a, pp: sorted(a)[int(pp * (len(a) - 1))]
    return dict(s5=q(sons, .05), s50=q(sons, .5), s95=q(sons, .95), m50=q(mdds, .5), m95=q(mdds, .95),
                l5=q(lows, .05), kayip=sum(1 for s in sons if s < START) / n * 100)


KAD = {"kad": (0, 5, 10), "kads": (0, 8, 14)}
ENTRY_AD = {0: "kapanışta 03:00 (Tokyo açılışı)", 1: "+1 saat (04:00)", 2: "+2 saat 05:00 (Hong Kong/Şangay)",
            5: "+5 saat (08:00)", 7: "+7 saat 10:00 (Londra, yaz saati)", 8: "+8 saat 11:00 (Londra, kış saati)",
            9: "+9 saat (12:00)", 13: "+13 saat 16:00 (New York öncesi, yaz)", 14: "+14 saat 17:00 (New York, kış/yaz sonrası)",
            "kad": "kademeli 03:00 / 08:00 / 13:00", "kads": "kademeli oturumlar: Asya 03:00 / Avrupa 11:00 / ABD 17:00"}
ENTRIES = [0, 1, 2, 5, 7, 8, 9, 13, 14, "kad", "kads"]
EXIT_AD = {"tp5": "TP 5R", "tp5_be": "TP 5R + 2R'de stop girişe", "don10": "günlük stop 10 gün dibi",
           "don10_be": "günlük stop 10 gün + 2R'de stop girişe", "don20": "günlük stop 20 gün dibi",
           "hyb10": "yarısı 3R + kalanı günlük stop 10 gün", "tr2": "OKX iz süren stop 2×ATR",
           "tr3": "OKX iz süren stop 3×ATR", "tr3a": "OKX iz süren stop 3×ATR (1R kârda başlar)"}
OFF_AD = {0: "03:00", 6 * 3600: "09:00", 12 * 3600: "15:00", 18 * 3600: "21:00"}


def main():
    T0 = time.time()
    data, created = T.load()
    t0 = created - DAYS * 86400
    t_split = created - TEST_DAYS * 86400
    tr_days = DAYS - TEST_DAYS
    coins = {(k, 0): Coin(k, v, 0) for k, v in data.items()}
    btc = Btc(coins[("BTC-USDT-SWAP", 0)])
    evs = []
    for c in coins.values():
        evs += events(c, btc)
    print(f"Hazırlık {time.time() - T0:.0f} sn, {len(evs)} kurulum", flush=True)
    sp_from = datetime.fromtimestamp(t0, T.TR).strftime("%d.%m.%Y")
    sp_mid = datetime.fromtimestamp(t_split, T.TR).strftime("%d.%m.%Y")

    out("# Günlük trend stratejisi — kapsamlı final testi (2 yıl)")
    out(f"{len(data)} coin. Dönem {sp_from} – bugün: **eğitim {sp_from} – {sp_mid} ({tr_days} gün)**, "
        f"**doğrulama son {TEST_DAYS} gün**. Her aşamada seçim sadece eğitime göre yapıldı. Maliyetler: maker %{MAKER}, "
        f"taker %{TAKER} + %{SLIP} kayma (stoplar), long funding 8 saatte %{FUND}. Portföy: 100 USDT başlangıç, bileşik, "
        f"coin başına 1 pozisyon, sinyal fazlaysa 24s hacmi yüksek olan önce. Not: coinler bugünün hacim listesinden "
        f"seçildi (o dönemde listede olup sonra düşen coinler yok); bu sonuçları bir miktar iyimser gösterebilir.")
    out()

    PHEAD = ("| Ayar | Tüm işlemler: sayı / kazanan / net R | Eğitim / doğrulama net R | R/işlem | "
             "Portföy (%2 × 3): son bakiye | Eğitim / doğrulama getiri | En büyük düşüş |\n|---|---|---|---|---|---|---|")

    def prow(ad, rs):
        a = all_stats(rs, t0, t_split)
        s = portfolio(rs, 2.0, 3, t0, t_split)
        return (f"| {ad} | {a['n']} / %{a['win']:.0f} / {a['tot']:+.1f} | {a['tr']:+.1f} / {a['te']:+.1f} | "
                f"{a['per']:+.2f} | {s['son']:.0f} USDT | %{s['egit']:+.0f} / %{s['dogr']:+.0f} | %{s['mdd']:.0f} |"), a

    # A) Giriş saati
    out("## A) Giriş saati (BTC filtresi yok)")
    out(PHEAD)
    sc = {}
    for entry in ENTRIES:
        tot = 0.0
        for ex in ("tp5", "don10"):
            line, a = prow(f"{ENTRY_AD[entry]} · {EXIT_AD[ex]}", trades_for(coins, evs, entry, ex, False))
            out(line)
            tot += a["tr"]
        sc[entry] = tot
        save()
    best_e = max(sc, key=lambda k: sc[k])
    # Çok seçenek denendiği için: en iyi ile "kapanışta" arasındaki fark küçükse sade seçenek (kapanışta) tercih edilir
    fark = sc[best_e] - sc[0]
    esik = 0.1 * abs(sc[0]) + 20
    entry = best_e if fark > esik else 0
    out(f"\nEğitimde en iyi: {ENTRY_AD[best_e]} ({sc[best_e]:+.1f}R), kapanışta giriş {sc[0]:+.1f}R. "
        f"Fark {'belirgin' if fark > esik else 'küçük'} → seçilen giriş: **{ENTRY_AD[entry]}**\n")

    # B) Çıkış × BTC
    out(f"## B) Çıkış türü × BTC filtresi (giriş: {ENTRY_AD[entry]})")
    out(PHEAD)
    best = None
    cache = {}
    for ex in EXIT_AD:
        for ub in (False, True):
            rs = trades_for(coins, evs, entry, ex, ub)
            cache[(ex, ub)] = rs
            line, a = prow(f"{EXIT_AD[ex]} · {'BTC filtreli' if ub else 'BTC filtresiz'}", rs)
            out(line)
            if best is None or a["tr"] > best[0]:
                best = (a["tr"], ex, ub)
        save()
    _, ex, ub = best
    rs = cache[(ex, ub)]
    out(f"\nSeçilen (eğitimde tüm işlemler net R en iyi): **{EXIT_AD[ex]} · {'BTC filtreli' if ub else 'BTC filtresiz'}**\n")

    # C) Portföy ve risk
    out("## C) Portföy ve risk kuralları")
    out("| Risk × en fazla pozisyon | Düşüşte risk yarıya | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | "
        "En düşük bakiye | İşlem | En uzun kayıp serisi | Acil fren çalıştı mı | Eğitim skoru (getiri/düşüş) |")
    out("|---|---|---|---|---|---|---|---|---|---|")
    bestp = None
    for risk, maxn in ((2.0, 3), (1.5, 4), (1.25, 5), (1.0, 6), (1.0, 8)):
        for ddcut in (False, True):
            s = portfolio(rs, risk, maxn, t0, t_split, ddcut)
            skor, _ = portfolio_train(rs, risk, maxn, t0, t_split, ddcut)
            out(f"| %{risk:g} × {maxn} | {'evet' if ddcut else 'hayır'} | {s['son']:.0f} USDT | %{s['egit']:+.0f} / "
                f"%{s['dogr']:+.0f} | %{s['mdd']:.0f} | {s['low']:.0f} USDT | {s['n']} | {s['seri']} | "
                f"{'EVET' if s['killed'] else 'hayır'} | {skor:.2f} |")
            if bestp is None or skor > bestp[0]:
                bestp = (skor, risk, maxn, ddcut)
    save()
    _, risk, maxn, ddcut = bestp
    out(f"\nSeçilen: **%{risk:g} risk × en fazla {maxn} pozisyon, düşüşte risk yarıya: {'evet' if ddcut else 'hayır'}**\n")

    # D) Günlük mum kapanış saati
    out("## D) Günlük mumun kapanış saati (sağlamlık)")
    out("| Kapanış saati (TR) | Tüm işlemler: sayı / net R | Eğitim / doğrulama net R | Portföy son bakiye | "
        "Eğitim / doğrulama getiri | En büyük düşüş |")
    out("|---|---|---|---|---|---|")
    hepsi = []
    allcoins = dict(coins)
    for off in (0, 6 * 3600, 12 * 3600, 18 * 3600):
        if off:
            for k, v in data.items():
                allcoins[(k, off)] = Coin(k, v, off)
            b_off = Btc(allcoins[("BTC-USDT-SWAP", off)])
            ev_off = []
            for k in data:
                ev_off += events(allcoins[(k, off)], b_off)
        else:
            ev_off = evs
        # giriş saati kapanışa göre aynı gecikme
        r_off = trades_for(allcoins, ev_off, entry, ex, ub)
        hepsi += r_off
        a = all_stats(r_off, t0, t_split)
        s = portfolio(r_off, risk, maxn, t0, t_split, ddcut)
        out(f"| {OFF_AD[off]} | {a['n']} / {a['tot']:+.1f} | {a['tr']:+.1f} / {a['te']:+.1f} | {s['son']:.0f} USDT | "
            f"%{s['egit']:+.0f} / %{s['dogr']:+.0f} | %{s['mdd']:.0f} |")
        save()
    hepsi.sort(key=lambda r: (r["t_sig"], -r["vol24"]))
    s4 = portfolio(hepsi, risk, maxn, t0, t_split, ddcut)
    a4 = all_stats(hepsi, t0, t_split)
    out(f"| **dördü birlikte** | {a4['n']} / {a4['tot']:+.1f} | {a4['tr']:+.1f} / {a4['te']:+.1f} | {s4['son']:.0f} USDT | "
        f"%{s4['egit']:+.0f} / %{s4['dogr']:+.0f} | %{s4['mdd']:.0f} |")
    s1 = portfolio(rs, risk, maxn, t0, t_split, ddcut)
    sk1, _ = portfolio_train(rs, risk, maxn, t0, t_split, ddcut)
    sk4, _ = portfolio_train(hepsi, risk, maxn, t0, t_split, ddcut)
    use_all = sk4 > sk1
    out(f"\nEğitim skoru: tek saat {sk1:.2f}, dördü birlikte {sk4:.2f} → seçilen: "
        f"**{'dört kapanış saati birlikte' if use_all else 'sadece 03:00 kapanışı'}**\n")
    final_rs = hepsi if use_all else rs
    fs = s4 if use_all else s1
    save()

    # E) Şans seviyesi
    out("## E) Şans seviyesi (mumları karıştırılmış veri, 03:00 kapanışı, aynı ayar)")
    gercek = all_stats(rs, t0, t_split)
    sans = []
    for seed in (7, 11, 23):
        sh = T.shuffled(data, seed)
        shc = {(k, 0): Coin(k, v, 0) for k, v in sh.items()}
        shb = Btc(shc[("BTC-USDT-SWAP", 0)])
        sev = []
        for c in shc.values():
            sev += events(c, shb)
        sans.append(all_stats(trades_for(shc, sev, entry, ex, ub), t0, t_split)["tot"])
    out(f"- Gerçek veri: tüm işlemler net **{gercek['tot']:+.1f}R** ({gercek['n']} işlem). Karışık veri (3 deneme): "
        + ", ".join(f"{x:+.1f}R" for x in sans))
    out()
    save()

    # F) Son kurgu ayrıntısı
    out("## Seçilen son kurgu")
    out(f"- Giriş: {ENTRY_AD[entry]} limit · Çıkış: {EXIT_AD[ex]} · {'BTC filtreli' if ub else 'BTC filtresiz'} · "
        f"%{risk:g} risk × en fazla {maxn} pozisyon · düşüşte risk yarıya: {'evet' if ddcut else 'hayır'} · "
        f"{'dört kapanış saati' if use_all else '03:00 kapanışı'}")
    out(f"- 2 yıl: 100 → **{fs['son']:.0f} USDT**, eğitim %{fs['egit']:+.0f}, doğrulama %{fs['dogr']:+.0f}, "
        f"en büyük düşüş %{fs['mdd']:.0f}, en düşük bakiye {fs['low']:.0f} USDT, {fs['n']} işlem "
        f"(haftada ~{fs['n'] / DAYS * 7:.1f}), en uzun kayıp serisi {fs['seri']}, acil fren: {'çalıştı' if fs['killed'] else 'çalışmadı'}")
    L = [r for r in fs["alinan"] if r["dir"] == 1]
    S = [r for r in fs["alinan"] if r["dir"] == -1]
    out(f"- Long {len(L)} işlem ({sum(r['net'] for r in L):+.1f}R) · Short {len(S)} işlem ({sum(r['net'] for r in S):+.1f}R) · "
        f"kazanan oranı %{sum(1 for r in fs['alinan'] if r['gross'] > 0) / max(1, fs['n']) * 100:.0f}")
    ay = {}
    for t, b in fs["curve"]:
        ay[datetime.fromtimestamp(t, T.TR).strftime("%Y-%m")] = b
    prev, parts = START, []
    for k in sorted(ay):
        parts.append((k, (ay[k] / prev - 1) * 100))
        prev = ay[k]
    out("- Aylık: " + " · ".join(f"{k} %{v:+.0f}" for k, v in parts))
    out(f"- Artı kapanan ay: {sum(1 for _, v in parts if v > 0)}/{len(parts)}")
    bs = bootstrap([r["net"] for r in fs["alinan"]], risk)
    out(f"- **Bootstrap (2.000 farklı 2 yıl):** son bakiye en kötü %5'te {bs['s5']:.0f}, ortada {bs['s50']:.0f}, "
        f"en iyi %5'te {bs['s95']:.0f} USDT. En büyük düşüş ortada %{bs['m50']:.0f}, en kötü %5'te %{bs['m95']:.0f}. "
        f"En düşük bakiye (en kötü %5) {bs['l5']:.0f} USDT. Dönemi zararla kapatma ihtimali %{bs['kayip']:.0f}.")
    out()
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")
    save()
    print(f"::notice::Final: {ENTRY_AD[entry]} · {EXIT_AD[ex]} · BTC {ub} · %{risk} × {maxn} · ddcut {ddcut} · "
          f"hepsi {use_all} → {fs['son']:.0f} USDT")


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
