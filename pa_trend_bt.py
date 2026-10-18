"""
Trend takip PA stratejisi: geçmiş test (mesaj göndermez, canlı bota dokunmaz). Sonuç: trend_sonuc.md

Strateji (az zaman isteyen, "kur ve unut" kurgu):
  Ortam : BTC günlük kapanışı EMA50 üstündeyse long, altındaysa short aranır (BTC filtresi kapatılabilir).
          Coin de yapı zaman diliminde EMA50'nin aynı tarafında kapanmış olmalı.
  Kurulum: Yapı zaman diliminde (1D veya 4H) son onaylı tepe (long) / dip (short) KAPANIŞLA kırılır.
  Giriş : "limit": kırılan seviyeye bekleyen limit emir (seviye + 0,25 ATR), en fazla N mum geçerli.
          "piyasa": kırılım mumunun kapanışında giriş (karşılaştırma için).
  Stop  : seviye ∓ sk × ATR (emirle birlikte konur).
  Çıkış (hepsi ekran takibi gerektirmez):
    tpX       : sabit hedef X·R (TP+SL birlikte konur)
    trC / trCa: OKX iz süren stop, geri çekilme = C × günlük ATR ("a": 1R kâra geçince devreye girer)
    yari      : yarısı 2R'de TP, kalanı OKX iz süren stop (3 × günlük ATR)
    donN      : günde bir kez (günlük kapanışta) stop son N günün dibine/tepesine çekilir
  En uzun tutma 60 gün (sonra kapatılır).

Maliyetler: maker %0,02 (limit giriş, TP), taker %0,05 (piyasa giriş, stop, iz süren stop).
Funding: long pozisyon 8 saatte %0,01 öder (kripto ortalamasına yakın), short için gelir sayılmaz (temkinli).
Veri: hacimde ilk ~80 kripto USDT perpetual, son 365 gün 1H mum (+60 gün ısınma). İşlemler 1H mumlarla izlenir;
aynı mumda hem stop hem hedef varsa stop varsayılır.
Değerlendirme: EĞİTİM ilk 240 gün, DOĞRULAMA son 125 gün. Seçim sadece eğitime göre.
"""
import os
import sys
import gzip
import json
import time
import bisect
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import numpy as np

import pa_scan_once as p

MAKER, TAKER = 0.02, 0.05
FUND_8H = 0.01                 # long için 8 saatlik funding maliyeti (%)
CACHE = "trend_cache.json.gz"
OUT = "trend_sonuc.md"
DAYS, WARM = 365, 60
TEST_DAYS = 125
K = 3                          # tepe/dip onayı (mum)
TOL = 0.25                     # limit emir seviyenin bu kadar ATR önüne konur
EXPIRY = {"1D": 10, "4H": 30}  # limit emir geçerlilik (yapı mumu)
MAXH = 60 * 24                 # en uzun tutma (1H mum)
LIMIT_HOURS = 48               # sabah limit emri en fazla kaç saat bekler
MIN_SP, MAX_SP = 0.5, 15.0     # stop mesafesi % aralığı
TR = timezone(timedelta(hours=3))

STFS = {"1D": 86400, "4H": 14400}
ENTRIES = ["limit", "piyasa"]
SKS = [0.5, 1.0, 1.5]
EXITS = ["tp2", "tp3", "tp5", "tr2", "tr3", "tr2a", "tr3a", "yari", "don10", "don20"]
EXIT_AD = {"tp2": "sabit TP 2R", "tp3": "sabit TP 3R", "tp5": "sabit TP 5R",
           "tr2": "OKX iz süren stop 2×ATR", "tr3": "OKX iz süren stop 3×ATR",
           "tr2a": "OKX iz süren 2×ATR (1R'de başlar)", "tr3a": "OKX iz süren 3×ATR (1R'de başlar)",
           "yari": "yarısı 2R + kalanı iz süren 3×ATR", "don10": "günlük stop: 10 gün dibi",
           "don20": "günlük stop: 20 gün dibi"}
FILTERS = {"btc": dict(btc=True, vol=False, long=False), "btc+hacim": dict(btc=True, vol=True, long=False),
           "btc+sadece long": dict(btc=True, vol=False, long=True),
           "btc+hacim+sadece long": dict(btc=True, vol=True, long=True),
           "BTC filtresiz": dict(btc=False, vol=False, long=False)}

lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------- Veri ----------------
def fetch_retry(inst, n):
    for d in range(8):
        try:
            return p.fetch(inst, "1H", 3600, n)
        except Exception as e:
            print(f"{inst} deneme {d + 1}: {e}", flush=True)
            time.sleep(3 + 4 * d)
    return None


FETCH_NOTE = []


def load():
    data, created = {}, time.time()
    try:
        with gzip.open(CACHE, "rt") as f:
            c = json.load(f)
        if time.time() - c["created"] < 3 * 86400:
            data, created = c["data"], c["created"]
            print(f"Önbellekte {len(data)} coin.", flush=True)
    except Exception:
        pass
    try:
        syms = p.get_symbols()
    except Exception as e:
        if len(data) > 20 and "BTC-USDT-SWAP" in data:
            print("Coin listesi alınamadı, önbellekle devam:", e, flush=True)
            return data, created
        raise
    if "BTC-USDT-SWAP" not in syms:
        syms.insert(0, "BTC-USDT-SWAP")
    eksik = [s_ for s_ in syms if s_ not in data]
    n = (DAYS + WARM) * 24
    if eksik:
        print(f"{len(eksik)} coin için {n} adet 1H mum çekiliyor...", flush=True)

        def one(inst):
            s_ = fetch_retry(inst, n)
            time.sleep(0.5)
            return inst, s_

        alinamayan, kisa = [], []
        with ThreadPoolExecutor(max_workers=2) as ex:
            for inst, s_ in ex.map(one, eksik):
                if s_ is None:
                    alinamayan.append(inst)
                elif len(s_["t"]) <= 24 * 90:
                    kisa.append(inst)
                else:
                    j_ = bisect.bisect_right(s_["t"], created)
                    data[inst] = {k: (v[:j_] if isinstance(v, list) else v) for k, v in s_.items()}
        FETCH_NOTE.append(f"Veri: {len(data)} coin; alınamayan {len(alinamayan)}, 90 günden kısa geçmişli {len(kisa)}.")
        print(FETCH_NOTE[-1], flush=True)
        with gzip.open(CACHE, "wt") as f:
            json.dump({"created": created, "data": data}, f)
    if "BTC-USDT-SWAP" not in data:
        raise RuntimeError("BTC verisi alınamadı (OKX istek sınırı olabilir); tekrar çalıştırın.")
    return data, created


# ---------------- Yardımcılar ----------------
def ema(c, n):
    out_ = [None] * len(c)
    if len(c) < n:
        return out_
    e = sum(c[:n]) / n
    out_[n - 1] = e
    k = 2 / (n + 1)
    for i in range(n, len(c)):
        e = c[i] * k + e * (1 - k)
        out_[i] = e
    return out_


def first_true(b):
    if b.size == 0:
        return None
    i = int(np.argmax(b))
    return i if b[i] else None


class Coin:
    def __init__(self, inst, s1):
        self.inst = inst
        self.s1 = s1
        self.t = np.array(s1["t"], dtype=np.int64)
        self.o, self.h = np.array(s1["o"]), np.array(s1["h"])
        self.l, self.c = np.array(s1["l"]), np.array(s1["c"])
        self.D = p.aggregate(s1, 86400)
        self.datr = p.atr_arr(self.D)
        dt = np.array(self.D["t"], dtype=np.int64)
        # her 1H mum için son kapanmış günün indeksi
        self.di = np.searchsorted(dt, self.t - 86400, side="right") - 1
        dl, dh = np.array(self.D["l"]), np.array(self.D["h"])
        self.don = {}
        for N in (10, 20):
            mn = np.full(len(dl), np.nan)
            mx = np.full(len(dh), np.nan)
            for k in range(N - 1, len(dl)):
                mn[k] = dl[k - N + 1:k + 1].min()
                mx[k] = dh[k - N + 1:k + 1].max()
            ok = self.di >= 0
            lo = np.full(len(self.t), np.nan)
            hi = np.full(len(self.t), np.nan)
            lo[ok], hi[ok] = mn[self.di[ok]], mx[self.di[ok]]
            self.don[N] = (lo, hi)
            # sabah güncelleme: günlük kapanıştan 5 saat sonra geçerli olur
            lo5 = np.concatenate((np.full(5, np.nan), lo[:-5]))
            hi5 = np.concatenate((np.full(5, np.nan), hi[:-5]))
            self.don[f"{N}g"] = (lo5, hi5)

    def datr_at(self, t):
        i = bisect.bisect_right(self.D["t"], t - 86400) - 1
        return self.datr[i] if i >= 0 else None


class Btc:
    def __init__(self, coin):
        D = coin.D
        self.t, self.c, self.e = D["t"], D["c"], ema(D["c"], 50)

    def dir_at(self, t):
        i = bisect.bisect_right(self.t, t - 86400) - 1
        if i < 0 or self.e[i] is None:
            return 0
        return 1 if self.c[i] > self.e[i] else -1


# ---------------- Kurulumlar ----------------
def events(coin, stf, btc, ema_n=50, ema_map=None):
    sec = STFS[stf]
    S = coin.D if stf == "1D" else p.aggregate(coin.s1, sec)
    n = len(S["t"])
    if n < 80:
        return []
    h, l, c, v = S["h"], S["l"], S["c"], S["v"]
    atr = p.atr_arr(S)
    if ema_map is not None:                 # uzun günlük geçmişten hesaplanmış EMA (zaman damgasına göre)
        e50 = [ema_map.get(t) for t in S["t"]]
    elif ema_n:
        e50 = ema(c, ema_n)
    else:
        e50 = list(c)                       # EMA filtresi yok: (c - e) * d > 0 kontrolü atlanır
    ph, pl = p.pivots(h, l, 0, n - 1, K)
    evs = []
    for d, piv in ((1, ph), (-1, pl)):
        pi = 0
        cur = None            # (pivot indeksi, değer, kullanıldı mı)
        for i in range(K + 1, n):
            while pi < len(piv) and piv[pi][0] <= i - K:
                cur = [piv[pi][0], piv[pi][1], False]
                pi += 1
            if cur is None or cur[2] or atr[i] is None or (ema_n and e50[i] is None):
                continue
            lvl = cur[1]
            if (c[i] - lvl) * d <= 0:
                continue
            cur[2] = True                                   # her seviye bir kez
            if ema_n and (c[i] - e50[i]) * d <= 0:
                continue
            prev = v[max(0, i - 20):i]
            volr = v[i] / statistics.median(prev) if len(prev) >= 5 and statistics.median(prev) > 0 else None
            tc = S["t"][i] + sec
            evs.append(dict(inst=coin.inst, dir=d, lvl=lvl, t=tc, atr=atr[i], close=c[i], volr=volr,
                            btc=btc.dir_at(tc), datr=coin.datr_at(tc), stf=stf, sec=sec))
    evs.sort(key=lambda e: e["t"])
    return evs


# ---------------- Simülasyon ----------------
def fill(ev, coin, entry, sk):
    """(giriş fiyatı, stop, giriş mum indeksi, ilk izleme indeksi, giriş komisyonu) | 'dolmadi' | 'elendi' | ('stop', ...)"""
    d = ev["dir"]
    stop = ev["lvl"] - d * sk * ev["atr"]
    j0 = int(np.searchsorted(coin.t, ev["t"]))
    n = len(coin.t)
    if j0 >= n:
        return "elendi"
    if entry == "piyasa":
        e = ev["close"]
        jf, start, fee = j0, j0, TAKER
    elif entry.startswith("lim_s"):                          # 08:00 TR'de limit emir: sabah fiyatı ∓ k × günlük ATR
        k = float(entry[5:])
        j0 = int(np.searchsorted(coin.t, ev["t"] + 5 * 3600))
        if j0 >= n or not ev["datr"]:
            return "elendi"
        e = float(coin.o[j0]) - d * k * ev["datr"]
        end = min(n, j0 + LIMIT_HOURS)
        seg = coin.l[j0:end] if d == 1 else coin.h[j0:end]
        kk = first_true(seg <= e) if d == 1 else first_true(seg >= e)
        if kk is None:
            return "dolmadi"
        jf = j0 + kk
        start, fee = jf + 1, MAKER
        if (e - stop) * d <= 0:
            return "elendi"
        R_ = abs(e - stop)
        sp_ = R_ / e * 100
        if sp_ < MIN_SP or sp_ > MAX_SP:
            return "elendi"
        bad = coin.l[jf] <= stop if d == 1 else coin.h[jf] >= stop
        if bad:
            return ("stop", e, stop, jf, fee)
        return (e, stop, jf, start, fee)
    elif entry == "sabah":                                   # mum kapanışından 5 saat sonra (03:00 → 08:00 TR) piyasa
        j0 = int(np.searchsorted(coin.t, ev["t"] + 5 * 3600))
        if j0 >= n:
            return "elendi"
        e = float(coin.o[j0])
        jf, start, fee = j0, j0, TAKER
    else:
        e = ev["lvl"] + d * TOL * ev["atr"]
        if (ev["close"] - e) * d <= 0:                      # kapanış zaten limit fiyatının ötesinde değil
            e = ev["close"]
        end = min(n, j0 + EXPIRY[ev["stf"]] * ev["sec"] // 3600)
        seg = coin.l[j0:end] if d == 1 else coin.h[j0:end]
        k = first_true(seg <= e) if d == 1 else first_true(seg >= e)
        if k is None:
            return "dolmadi"
        jf = j0 + k
        start, fee = jf + 1, MAKER
    R = abs(e - stop)
    if (e - stop) * d <= 0:
        return "elendi"
    sp = R / e * 100
    if sp < MIN_SP or sp > MAX_SP:
        return "elendi"
    if entry == "limit":
        bad = coin.l[jf] <= stop if d == 1 else coin.h[jf] >= stop
        if bad:
            return ("stop", e, stop, jf, fee)
    return (e, stop, jf, start, fee)


def trail_exit(coin, d, e, stop, cb, act_R, a, b):
    """İz süren stop: tetiklenme indeksi (göreli) ve çıkış fiyatı."""
    H, L, O = coin.h[a:b], coin.l[a:b], coin.o[a:b]
    if d == 1:
        peak = np.maximum.accumulate(np.concatenate(([e], H)))[:-1]
        tr = peak - cb
        if act_R is not None:
            tr = np.where(peak >= e + act_R, tr, -np.inf)
        eff = np.maximum(stop, tr)
        k = first_true(L <= eff)
        return (k, min(O[k], eff[k])) if k is not None else (None, None)
    peak = np.minimum.accumulate(np.concatenate(([e], L)))[:-1]
    tr = peak + cb
    if act_R is not None:
        tr = np.where(peak <= e - act_R, tr, np.inf)
    eff = np.minimum(stop, tr)
    k = first_true(H >= eff)
    return (k, max(O[k], eff[k])) if k is not None else (None, None)


def simulate(ev, coin, f, ex):
    """Sonuç sözlüğü (net R, brüt R, sonuç, giriş/çıkış zamanı)."""
    d = ev["dir"]
    if f[0] == "stop":
        _, e, stop, jf, fee = f
        R = abs(e - stop)
        sp = R / e * 100
        g = -1.0
        return dict(net=g - (fee + TAKER) / sp, gross=g, sonuc="stop", t_in=int(coin.t[jf]), t_out=int(coin.t[jf]),
                    dir=d, inst=ev["inst"], sp=sp)
    e, stop, jf, a, fee = f
    n = len(coin.t)
    b = min(n, a + MAXH)
    R = abs(e - stop)
    sp = R / e * 100
    if a >= b:
        return None
    H, L, O, C = coin.h[a:b], coin.l[a:b], coin.o[a:b], coin.c[a:b]
    adv = L if d == 1 else H
    fav = H if d == 1 else L

    def done(gross, fee_out, k, sonuc):
        k = min(k, b - a - 1)
        hours = (a + k) - jf + 1
        fund = FUND_8H * hours / 8 if d == 1 else 0.0
        return dict(net=gross - (fee + fee_out + fund) / sp, gross=gross, sonuc=sonuc,
                    t_in=int(coin.t[jf]), t_out=int(coin.t[a + k]), dir=d, inst=ev["inst"], sp=sp)

    def stop_idx():
        return first_true(adv <= stop) if d == 1 else first_true(adv >= stop)

    if ex.startswith("tp"):
        m = float(ex[2:])
        tp = e + d * m * R
        ks = stop_idx()
        kt = first_true(fav >= tp) if d == 1 else first_true(fav <= tp)
        if ks is not None and (kt is None or ks <= kt):
            px = min(O[ks], stop) if d == 1 else max(O[ks], stop)
            return done((px - e) * d / R, TAKER, ks, "stop")
        if kt is not None:
            return done(m, MAKER, kt, "TP")
        return done((C[-1] - e) * d / R, TAKER, b - a - 1, "süre/açık")

    if ex.startswith("tr") or ex == "yari":
        mult = 3.0 if ex == "yari" else float(ex[2])
        act = R if ex.endswith("a") else None
        if not ev["datr"]:
            return None
        k, px = trail_exit(coin, d, e, stop, mult * ev["datr"], act, a, b)
        if ex != "yari":
            if k is None:
                return done((C[-1] - e) * d / R, TAKER, b - a - 1, "süre/açık")
            g = (px - e) * d / R
            return done(g, TAKER, k, "stop" if g < 0 else "iz süren")
        tp = e + d * 2 * R
        kt = first_true(fav >= tp) if d == 1 else first_true(fav <= tp)
        if k is not None and (kt is None or k <= kt):
            g = (px - e) * d / R
            return done(g, TAKER, k, "stop" if g < 0 else "iz süren")
        if kt is None:
            return done((C[-1] - e) * d / R, TAKER, b - a - 1, "süre/açık")
        if k is None:
            return done(0.5 * 2 + 0.5 * (C[-1] - e) * d / R, 0.5 * MAKER + 0.5 * TAKER, b - a - 1, "süre/açık")
        return done(0.5 * 2 + 0.5 * (px - e) * d / R, 0.5 * MAKER + 0.5 * TAKER, k, "TP + iz süren")

    if ex.startswith("don"):
        N = ex[3:]
        lo, hi = coin.don[int(N) if N.isdigit() else N]
        if d == 1:
            lv = np.nan_to_num(lo[a:b], nan=-np.inf)
            eff = np.maximum.accumulate(np.maximum(stop, lv))
            k = first_true(L <= eff)
            px = min(O[k], eff[k]) if k is not None else None
        else:
            hv = np.nan_to_num(hi[a:b], nan=np.inf)
            eff = np.minimum.accumulate(np.minimum(stop, hv))
            k = first_true(H >= eff)
            px = max(O[k], eff[k]) if k is not None else None
        if k is None:
            return done((C[-1] - e) * d / R, TAKER, b - a - 1, "süre/açık")
        g = (px - e) * d / R
        return done(g, TAKER, k, "stop" if g < 0 else "günlük stop")
    return None


# ---------------- Değerlendirme ----------------
def passes(ev, flt):
    if flt["btc"] and ev["btc"] != ev["dir"]:
        return False
    if flt["vol"] and ev["volr"] is not None and ev["volr"] < 1.0:
        return False
    if flt["long"] and ev["dir"] != 1:
        return False
    return True


def stats(rs, days):
    n = len(rs)
    if not n:
        return dict(n=0, win=0, net=0, per=0, ay=0, seri=0, hold=0)
    kaz = sum(1 for r in rs if r["gross"] > 0)
    seri = mx = 0
    for r in sorted(rs, key=lambda r: r["t_in"]):
        seri = seri + 1 if r["gross"] <= 0 else 0
        mx = max(mx, seri)
    net = sum(r["net"] for r in rs)
    return dict(n=n, win=kaz / n * 100, net=net, per=net / n, ay=n / days * 30, seri=mx,
                hold=sum(r["t_out"] - r["t_in"] for r in rs) / n / 86400)


def portfolio(rs, maxn=5):
    acik, al = [], []
    for r in sorted(rs, key=lambda r: r["t_in"]):
        acik = [x for x in acik if x["t_out"] > r["t_in"]]
        if len(acik) >= maxn or any(x["inst"] == r["inst"] for x in acik):
            continue
        acik.append(r)
        al.append(r)
    eq = pk = dd = 0.0
    for r in sorted(al, key=lambda r: r["t_out"]):
        eq += r["net"]
        pk = max(pk, eq)
        dd = max(dd, pk - eq)
    return al, dd


def fmt_row(ad, tr, te, al, pf, dd):
    return (f"| {ad} | {tr['n']} / %{tr['win']:.0f} / {tr['net']:+.1f} | {te['n']} / %{te['win']:.0f} / {te['net']:+.1f} | "
            f"{al['n']} (~{al['ay']:.0f}/ay) | %{al['win']:.0f} | **{al['net']:+.1f}** | {al['per']:+.2f} | "
            f"{al['seri']} | {al['hold']:.1f} g | {sum(r['net'] for r in pf):+.1f} / {dd:.1f} |")


HEAD = ("| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | "
        "Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |\n"
        "|---|---|---|---|---|---|---|---|---|---|")


def run_grid(coins, btc, t_start, t_split, etiket=""):
    """Tüm ayarlar: [(anahtar, filtre, eğitim, doğrulama, toplam, işlemler)]"""
    T0 = time.time()
    R = {}
    for stf in STFS:
        evs = []
        for c in coins.values():
            evs += [e for e in events(c, stf, btc) if e["t"] >= t_start]
        print(f"{etiket}{stf}: {len(evs)} kurulum", flush=True)
        for entry in ENTRIES:
            for sk in SKS:
                fills = [(ev, fill(ev, coins[ev["inst"]], entry, sk)) for ev in evs]
                fills = [(ev, f) for ev, f in fills if not isinstance(f, str)]
                for ex in EXITS:
                    res = []
                    for ev, f in fills:
                        r = simulate(ev, coins[ev["inst"]], f, ex)
                        if r:
                            res.append((ev, r))
                    R[(stf, entry, sk, ex)] = res
        print(f"{etiket}{stf} simülasyon bitti ({time.time() - T0:.0f} sn)", flush=True)
    tr_days, te_days = DAYS - TEST_DAYS, TEST_DAYS
    rows = []
    for key, res in R.items():
        for fad, flt in FILTERS.items():
            rs = [r for ev, r in res if passes(ev, flt)]
            tr = [r for r in rs if r["t_in"] < t_split]
            te = [r for r in rs if r["t_in"] >= t_split]
            rows.append((key, fad, stats(tr, tr_days), stats(te, te_days), stats(rs, DAYS), rs))
    return rows


def shuffled(data, seed=7):
    """Her coinin 1H mumlarını (önceki kapanışa göre oranlarıyla) karıştırır: oynaklık aynı kalır,
    trend ve ardışıklık yok olur. Şans seviyesini ölçmek için."""
    rng = np.random.default_rng(seed)
    outd = {}
    for k, s in data.items():
        c = np.array(s["c"])
        prev = np.concatenate(([s["o"][0]], c[:-1]))
        ro, rh = np.array(s["o"]) / prev, np.array(s["h"]) / prev
        rl, rc = np.array(s["l"]) / prev, c / prev
        idx = rng.permutation(len(c))
        ro, rh, rl, rc = ro[idx], rh[idx], rl[idx], rc[idx]
        pc = s["o"][0] * np.cumprod(rc)
        pprev = np.concatenate(([s["o"][0]], pc[:-1]))
        outd[k] = dict(t=s["t"], o=list(pprev * ro), h=list(pprev * rh), l=list(pprev * rl), c=list(pc),
                       v=list(np.array(s["v"])[idx]), sec=s["sec"])
    return outd


def main():
    T0 = time.time()
    data, created = load()
    t_start = created - DAYS * 86400
    t_split = created - TEST_DAYS * 86400
    coins = {k: Coin(k, v) for k, v in data.items()}
    btc = Btc(coins["BTC-USDT-SWAP"])
    print(f"Hazırlık {time.time() - T0:.0f} sn", flush=True)

    rows = run_grid(coins, btc, t_start, t_split)
    tr_days, te_days = DAYS - TEST_DAYS, TEST_DAYS

    def ad(key, fad):
        stf, entry, sk, ex = key
        return f"{stf} · {'limit @seviye' if entry == 'limit' else 'piyasa'} · stop {sk} ATR · {EXIT_AD[ex]} · {fad}"

    def line(r):
        key, fad, tr, te, al, rs = r
        pf, dd = portfolio(rs)
        return fmt_row(ad(key, fad), tr, te, al, pf, dd)

    out("# Trend takip PA stratejisi — 365 günlük test")
    out(f"Tarih: {datetime.fromtimestamp(created, TR):%d.%m.%Y %H:%M} (TR). {len(coins)} coin. "
        f"**Eğitim ilk {tr_days} gün, doğrulama son {te_days} gün.** Seçimler sadece eğitime göre. "
        f"Komisyon maker %{MAKER} / taker %{TAKER}; long için funding 8 saatte %{FUND_8H}. "
        f"\"Kazanan\": kârla kapanan işlem oranı. Portföy sütunu: coin başına 1, aynı anda en fazla 5 pozisyon. "
        f"Toplam {len(STFS) * len(ENTRIES) * len(SKS) * len(EXITS) * len(FILTERS)} ayar denendi: en iyisi şans eseri iyi "
        f"görünebilir, asıl ölçü doğrulama sütunudur. " + " ".join(FETCH_NOTE))
    out()
    elig = [r for r in rows if r[2]["n"] >= 40]
    elig.sort(key=lambda r: r[2]["net"], reverse=True)
    out("## 1) Eğitim dönemine göre en iyi 25 ayar")
    out(HEAD)
    for r in elig[:25]:
        out(line(r))
    save()

    best = elig[0] if elig else None
    out()
    out("## 2) Her çıkış türünün en iyi ayarı (eğitime göre)")
    out(HEAD)
    for ex in EXITS:
        cand = [r for r in elig if r[0][3] == ex]
        if cand:
            out(line(cand[0]))
    out()
    out("## 3) Zaman dilimi × giriş türü: en iyi ayar (eğitime göre)")
    out(HEAD)
    for stf in STFS:
        for entry in ENTRIES:
            cand = [r for r in elig if r[0][0] == stf and r[0][1] == entry]
            if cand:
                out(line(cand[0]))
    out()
    out("## 4) Filtrelerin etkisi (her filtre için en iyi ayar, eğitime göre)")
    out(HEAD)
    for fad in FILTERS:
        cand = [r for r in elig if r[1] == fad]
        if cand:
            out(line(cand[0]))
    save()

    if best:
        key, fad, tr, te, al, rs = best
        out()
        out(f"## 5) Seçilen ayarın ayrıntısı: {ad(key, fad)}")
        L = [r for r in rs if r["dir"] == 1]
        S = [r for r in rs if r["dir"] == -1]
        out(f"- Long: {len(L)} işlem, {sum(r['net'] for r in L):+.1f}R · Short: {len(S)} işlem, {sum(r['net'] for r in S):+.1f}R")
        gun = defaultdict(float)
        ay = defaultdict(lambda: [0, 0.0])
        for r in rs:
            gun[datetime.fromtimestamp(r["t_out"], TR).strftime("%d.%m.%Y")] += r["net"]
            k = datetime.fromtimestamp(r["t_in"], TR).strftime("%Y-%m")
            ay[k][0] += 1
            ay[k][1] += r["net"]
        top = sorted(gun.items(), key=lambda kv: kv[1], reverse=True)[:3]
        out(f"- En iyi 3 gün: " + ", ".join(f"{k} ({v:+.1f}R)" for k, v in top) +
            f" → bu 3 gün olmadan **{al['net'] - sum(v for _, v in top):+.1f}R**")
        out("- Aylık: " + " · ".join(f"{k}: {v[0]} işlem {v[1]:+.1f}R" for k, v in sorted(ay.items())))
        for mn in (3, 5, 10):
            pf, dd = portfolio(rs, mn)
            pt = sum(r["net"] for r in pf if r["t_in"] < t_split)
            pv = sum(r["net"] for r in pf if r["t_in"] >= t_split)
            out(f"- Portföy, aynı anda en fazla {mn}: {len(pf)} işlem, net {sum(r['net'] for r in pf):+.1f}R "
                f"(eğitim {pt:+.1f} / doğrulama {pv:+.1f}), en büyük düşüş {dd:.1f}R, "
                f"haftada ~{len(pf) / DAYS * 7:.1f} yeni işlem")
        sonuc = defaultdict(int)
        for r in rs:
            sonuc[r["sonuc"]] += 1
        out("- Çıkış türleri: " + ", ".join(f"{k} {v}" for k, v in sonuc.items()))
    save()

    # Şans seviyesi: aynı test, mumları karıştırılmış (trendi bozulmuş) veriyle
    sh = {k: Coin(k, v) for k, v in shuffled(data).items()}
    rows2 = run_grid(sh, Btc(sh["BTC-USDT-SWAP"]), t_start, t_split, "[karışık] ")
    el2 = sorted([r for r in rows2 if r[2]["n"] >= 40], key=lambda r: r[2]["net"], reverse=True)
    out()
    out("## 6) Şans seviyesi kontrolü")
    out("Aynı 600 ayar, her coinin mumları rastgele karıştırılmış veriyle (oynaklık aynı, trend yok) denendi. "
        "Gerçek veride sonuç bunun belirgin şekilde üstünde değilse şans eseri sayılmalı.")
    out(HEAD)
    if el2:
        out(line(el2[0]).replace("| ", "| [karışık veri, eğitimde en iyi] ", 1))
    for nm, rr in (("gerçek veri", elig), ("karışık veri", el2)):
        if rr:
            top = rr[:25]
            out(f"- {nm}: eğitimde en iyi 25 ayarın doğrulama ortalaması "
                f"{sum(r[3]['net'] for r in top) / len(top):+.1f}R, tüm ayarların doğrulama ortalaması "
                f"{sum(r[3]['net'] for r in rr) / len(rr):+.1f}R")
    out()
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")
    save()
    if best:
        print(f"::notice::En iyi (eğitim): {ad(best[0], best[1])} | eğitim {best[2]['net']:+.1f}R, "
              f"doğrulama {best[3]['net']:+.1f}R")


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
