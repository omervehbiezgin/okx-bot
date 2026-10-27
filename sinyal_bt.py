"""
Tarama botu sinyallerinin geçmişe dönük testi (sinyal_bt.py)

Botun (okx_scan_once.py) kurallarıyla geçmiş mumlarda sinyal arar ve her sinyalde kullanıcının
stratejisine göre işlem simülasyonu yapar. Telegram'a mesaj göndermez, botun durum dosyasına dokunmaz.

Stratejiler (long örneği; short'ta tersi):
  1) KIRILIM (15m, 1H, 4H) - ilk 100 coin, son 120 gün
     Giriş : kırılan çizgi (bant üstü) | bant ortası | bant dibi | kademeli (üçe bölünmüş)
     Stop  : çizgi girişinde çizginin %10 bant altı, diğerlerinde bant dibinin %10 bant altı
     Bekleme: 24 / 48 / 96 mum; bant dibinin altında kapanış emri iptal eder
     İz süren stop: 1R'de başa baş + k x ATR (k = 1.5, 2, 3) | hemen 2 x ATR | son 3 mum dibi
  2) FVG'DEN DÖNÜŞ (günlük bölge, 4H tepki) - bütün coinler, son 180 gün
     Giriş : sinyal kapanışında | FVG üst çizgisine limit (1 / 3 / 7 gün)
     Stop  : tepki fitilinin altı | FVG alt çizgisinin altı (pay: 0.1 x günlük ATR)
     İz süren stop: 1R'de başa baş + k x 4H ATR (k = 1.5, 2, 3)
  3) EMA21 HAFTALIK - bütün coinler, bütün geçmiş
     Giriş : EMA21 çizgisine limit | en yakın günlük destek FVG'si | hangisi önce gelirse
     Stop  : EMA girişinde kesişim mumunun dibi, FVG girişinde FVG alt çizgisi (pay: 0.1 x günlük ATR)
     Bekleme: 2 / 4 / 8 hafta, haftalık kapanış EMA'nın altına dönerse iptal
     İz süren stop: 1R geriden (hemen | 1R kârdan sonra), kâr al: yok | 2R | fiyatın 2 katı
  4) RSI DÖNÜŞÜ + RSI'ın SMA14'ünü kesmesi (4H, 1D, 1W)
     Giriş : 30'dan dönüş (kapanış/fitil) ve RSI'ın SMA'sını yukarı kesmesi; ikisi tamamlanınca kapanışta
     Stop  : dönüş sırasındaki en düşük fiyatın altı (pay: 0.1 x ATR)
     Çıkış : RSI 70 (kapanışla | fitille) ya da iz süren stop (1R geriden | 1R'de başa baş + 2 x ATR)

Ortak: OKX ücretleri (limit 0.02%, piyasa/stop 0.05% + 0.03% kayma), aynı mumda hem stop hem
hedef olursa stop sayılır, aynı coinde aynı anda tek işlem, son dönem ayrı (doğrulama).
Sonuç "sinyal-test-sonuclari" dalına sinyal_sonuc.md ve sinyal_sonuc.json olarak yazılır.
"""
import os
import sys
import gzip
import json
import time
import bisect
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

import okx_scan_once as b

CACHE = "sinyal_cache.json.gz"
OUT_MD, OUT_JSON = "sinyal_sonuc.md", "sinyal_sonuc.json"
DAY = 86400

# Kapsam
TOP_N = int(os.getenv("BT_TOP", "100"))          # kırılım için hacme göre ilk N coin
KIR_GUN = int(os.getenv("BT_KIR_GUN", "120"))    # kırılım testi kaç gün
FVG_GUN = int(os.getenv("BT_FVG_GUN", "180"))
RSI4_GUN = int(os.getenv("BT_RSI4_GUN", "730"))
MAX_COIN = int(os.getenv("BT_MAX_COIN", "0"))    # 0 = hepsi (deneme için sınırlanabilir)
# Doğrulama (son dönem) gün sayıları
DOG = {"KIR": 30, "FVG": 45, "RSI": 180, "EMA": 180}

FEE_MAKER, FEE_TAKER, KAYMA = 0.0002, 0.0005, 0.0003
TF_SEC = {"15m": 900, "1H": 3600, "4H": 14400, "1D": 86400, "1W": 604800}


# ======================= VERİ =======================
_kilit = threading.Lock()
_son_istek = [0.0]


def api(path, params):
    """OKX isteği; saniyede ~8 istek, hata ve hız sınırında tekrar dener."""
    for deneme in range(6):
        with _kilit:
            bekle = _son_istek[0] + 0.125 - time.time()
            if bekle > 0:
                time.sleep(bekle)
            _son_istek[0] = time.time()
        try:
            return b.api(path, params)
        except Exception as e:
            print(f"  istek hatası ({deneme + 1}): {e}", flush=True)
            time.sleep(1 + 2 * deneme)
    return None


def fetch(inst, bar, since):
    """'since' (sn) anından bugüne kadar kapanmış mumlar: {t,o,h,l,c,q} listeleri (eskiden yeniye)."""
    rows, after = [], None
    while True:
        p = {"instId": inst, "bar": bar, "limit": "100"}
        if after:
            p["after"] = after
        data = api("/api/v5/market/history-candles", p)
        if not data:
            break
        rows.extend(data)
        after = data[-1][0]
        if int(after) // 1000 <= since or len(data) < 100:
            break
    rows = [r for r in reversed(rows) if r[8] == "1" and int(r[0]) // 1000 >= since]
    seen, out = set(), {k: [] for k in "tohlcq"}
    for r in rows:
        t = int(r[0]) // 1000
        if t in seen:
            continue
        seen.add(t)
        out["t"].append(t)
        for k, j in zip("ohlc", (1, 2, 3, 4)):
            out[k].append(float(r[j]))
        out["q"].append(float(r[7]))
    return out


def load_data():
    now = int(time.time())
    data = {}
    try:
        with gzip.open(CACHE, "rt") as f:
            c = json.load(f)
        if now - c["created"] < 3 * DAY:
            data = c["data"]
            now = c["created"]
            print(f"Önbellekte {len(data)} coin var.", flush=True)
    except Exception:
        pass
    symbols = b.get_symbols()                       # hacme göre sıralı, kripto, >= 1M USDT
    if MAX_COIN:
        symbols = symbols[:MAX_COIN]
    top = set(symbols[:TOP_N])
    eksik = [s for s in symbols if s not in data or (s in top and "15m" not in data[s])]
    print(f"{len(symbols)} coin, veri çekilecek: {len(eksik)}", flush=True)

    def one(inst):
        d = {"1D": fetch(inst, "1Dutc", 0)}
        d["4H"] = fetch(inst, "4H", now - (RSI4_GUN + 60) * DAY)
        if inst in top:
            d["1H"] = fetch(inst, "1H", now - (KIR_GUN + 10) * DAY)
            d["15m"] = fetch(inst, "15m", now - (KIR_GUN + 5) * DAY)
        return inst, d

    tamam = 0
    with ThreadPoolExecutor(max_workers=2) as ex:
        for inst, d in ex.map(one, eksik):
            if len(d["1D"]["t"]) >= 30:
                data[inst] = d
            tamam += 1
            if tamam % 20 == 0:
                print(f"  {tamam}/{len(eksik)} coin indirildi", flush=True)
            if tamam % 60 == 0:                         # iş yarıda kesilirse indirilen veri kaybolmasın
                with gzip.open(CACHE, "wt") as f:
                    json.dump({"created": now, "data": data}, f)
    with gzip.open(CACHE, "wt") as f:
        json.dump({"created": now, "data": data}, f)
    return data, symbols, top, now


def weekly_from_daily(d):
    """Günlük (UTC) mumlardan haftalık (Pazartesi 00:00 UTC) mumlar; sadece tamamlanmış haftalar."""
    w = {k: [] for k in "tohlcq"}
    for i, t in enumerate(d["t"]):
        hs = t - ((t // DAY + 3) % 7) * DAY          # 1970-01-01 Perşembe -> Pazartesi başlangıcı
        if not w["t"] or w["t"][-1] != hs:
            for k, v in zip("tohlcq", (hs, d["o"][i], d["h"][i], d["l"][i], d["c"][i], d["q"][i])):
                w[k].append(v)
        else:
            w["h"][-1] = max(w["h"][-1], d["h"][i])
            w["l"][-1] = min(w["l"][-1], d["l"][i])
            w["c"][-1] = d["c"][i]
            w["q"][-1] += d["q"][i]
    if w["t"] and d["t"] and d["t"][-1] < w["t"][-1] + 6 * DAY:   # son hafta tamamlanmadı
        for k in w:
            w[k].pop()
    return w


def arr(s):
    return {k: np.asarray(v, dtype=float) for k, v in s.items()}


def atr(h, l, c, n=14):
    """Gerçek aralığın n mumluk basit ortalaması (botla aynı); i. değer i. mum dahil."""
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return pd.Series(tr).rolling(n).mean().to_numpy(), tr


def ema(vals, n):
    out = np.full(len(vals), np.nan)
    if len(vals) < n:
        return out
    out[n - 1] = np.mean(vals[:n])
    k = 2 / (n + 1)
    for i in range(n, len(vals)):
        out[i] = vals[i] * k + out[i - 1] * (1 - k)
    return out


def rsi_wilder(c, n=14):
    """TradingView ta.rsi ile aynı; (rsi, ort_kazanç, ort_kayıp) dizileri."""
    m = len(c)
    r, g, lo = np.full(m, np.nan), np.full(m, np.nan), np.full(m, np.nan)
    if m <= n:
        return r, g, lo
    ch = np.diff(c)
    gg, ll = np.mean(np.maximum(ch[:n], 0)), np.mean(np.maximum(-ch[:n], 0))
    g[n], lo[n] = gg, ll
    for i in range(n + 1, m):
        d = ch[i - 1]
        gg = (gg * (n - 1) + max(d, 0)) / n
        ll = (ll * (n - 1) + max(-d, 0)) / n
        g[i], lo[i] = gg, ll
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(lo == 0, 100.0, 100 - 100 / (1 + g / lo))
    r[:n] = np.nan
    return r, g, lo


def rsi_if(price, prev_c, g0, l0, n=14):
    d = price - prev_c
    g = (g0 * (n - 1) + max(d, 0)) / n
    ls = (l0 * (n - 1) + max(-d, 0)) / n
    return 100.0 if ls == 0 else 100 - 100 / (1 + g / ls)


def rsi_price(target, prev_c, g0, l0, n=14):
    """RSI'ı 'target' yapan kapanış fiyatı (kapalı form)."""
    # Yukarı: g = (g0(n-1)+d)/n, l = l0(n-1)/n ; RSI = 100 - 100/(1+g/l)
    rs = target / (100 - target)
    if target >= 50:
        l = l0 * (n - 1) / n
        d = rs * l * n - g0 * (n - 1)
        return prev_c + max(d, 0)
    g = g0 * (n - 1) / n
    if rs == 0:
        return None
    lneed = g / rs
    d = lneed * n - l0 * (n - 1)
    return prev_c - max(d, 0)


# ---------------- Günlük FVG'ler (botla aynı kural) ----------------
def daily_fvg(d):
    """Günlük FVG'ler: dict(tur, alt, ust, f, formed, uc) ve her gün sonunda açık olanlar (kapanış kuralı)."""
    h, l, c = d["h"], d["l"], d["c"]
    a, _ = atr(h, l, c, b.ATR_DAYS)
    zones = []
    for f in range(2, len(h)):
        i = f - 2
        if np.isnan(a[f]):
            continue
        if h[i] < l[f] and l[f] - h[i] >= b.FVG_MIN_GAP_ATR * a[f]:
            zones.append(dict(tur=1, alt=h[i], ust=l[f], f=f, t0=d["t"][i], formed=d["t"][f] + DAY, uc=h[f]))
        elif l[i] > h[f] and l[i] - h[f] >= b.FVG_MIN_GAP_ATR * a[f]:
            zones.append(dict(tur=-1, alt=h[f], ust=l[i], f=f, t0=d["t"][i], formed=d["t"][f] + DAY, uc=l[f]))
    # açık listeler: open_by_day[f] = f günü kapanınca açık olan bölgeler (en fazla NOTE_MAX_ZONES)
    by_f = {}
    for z in zones:
        by_f.setdefault(z["f"], []).append(z)
    acik, open_by_day = [], []
    for f in range(len(h)):
        acik = [z for z in acik if not ((z["tur"] == 1 and c[f] < z["alt"]) or (z["tur"] == -1 and c[f] > z["ust"]))]
        for z in by_f.get(f, []):
            acik.append(z)
            if len(acik) > b.NOTE_MAX_ZONES:
                acik.pop(0)
        open_by_day.append(list(acik))
    return zones, open_by_day, a


def day_index(d, t):
    """t anında kapanmış son günün indeksi."""
    return bisect.bisect_right(d["t"], t - DAY) - 1


# ======================= SİNYALLER =======================
KIR_CFG = {"15m": dict(lb=96, base=32, k=3.5, htf="1H"), "1H": dict(lb=72, base=24, k=3.0, htf="4H"),
           "4H": dict(lb=60, base=20, k=3.0, htf="1D")}


def kirilim_sinyalleri(s, tf, htf_s, htf_sec, d, fvg_open, t_bas):
    cfg = KIR_CFG[tf]
    lb, base = cfg["lb"], cfg["base"]
    o, h, l, c, q, t = s["o"], s["h"], s["l"], s["c"], s["q"], s["t"]
    n = len(c)
    if n < lb + 2 * base + 5:
        return []
    sec = TF_SEC[tf]
    hs, ls = pd.Series(h), pd.Series(l)
    hi = hs.rolling(base).max().shift(1).to_numpy()
    lo = ls.rolling(base).min().shift(1).to_numpy()
    _, tr = atr(h, l, c)
    trm = pd.Series(tr).rolling(lb).mean().shift(base + 1).to_numpy()   # tr[L-base-lb : L-base]
    qmed = pd.Series(q).rolling(lb).median().shift(1).to_numpy()
    canli = pd.Series((q > 0).astype(float)).rolling(base).sum().shift(1).to_numpy()
    rng_ort = pd.Series(h - l).rolling(base).mean().shift(1).to_numpy()
    # üst zaman dilimi EMA21 (kapanmış mumlara göre)
    he = ema(htf_s["c"], 21) if htf_s is not None and len(htf_s["c"]) >= 21 else None
    out = []
    for L in range(2 * base + 2, n):
        if t[L] < t_bas:
            continue
        w = hi[L] - lo[L]
        boy = h[L] - l[L]
        if not (w > 0 and boy > 0 and lo[L] > 0 and o[L] > 0) or np.isnan(trm[L]):
            continue
        if w > cfg["k"] * trm[L]:
            continue
        up = (c[L] > hi[L] + b.BRK_CLOSE_OUT * w and c[L] > o[L] and c[L] - o[L] >= b.BRK_BODY * boy
              and c[L] - l[L] >= b.BRK_CLOSE_POS * boy)
        dn = (c[L] < lo[L] - b.BRK_CLOSE_OUT * w and c[L] < o[L] and o[L] - c[L] >= b.BRK_BODY * boy
              and h[L] - c[L] >= b.BRK_CLOSE_POS * boy)
        if not (up or dn):
            continue
        kind = 1 if up else -1
        band = slice(L - base, L)
        if (np.sum(h[band] >= hi[L] - b.BRK_TOUCH_ZONE * w) < b.BRK_MIN_TOUCH or
                np.sum(l[band] <= lo[L] + b.BRK_TOUCH_ZONE * w) < b.BRK_MIN_TOUCH):
            continue
        if canli[L] * 100 < b.BRK_LIVE_PCT * base:
            continue
        ratio = q[L] / qmed[L] if qmed[L] > 0 else None
        if ratio is None or ratio < b.BRK_MIN_VOL_RATIO:
            continue
        stars = int(ratio >= b.BRK_STAR_VOL) + int(boy >= b.BRK_STAR_SIZE * rng_ort[L])
        close_time = t[L] + sec
        if he is not None:
            j = bisect.bisect_right(htf_s["t"], close_time - htf_sec) - 1
            if j >= 20 and not np.isnan(he[j]):
                stars += int((kind == 1 and c[L] > he[j]) or (kind == -1 and c[L] < he[j]))
        rev = False
        bc = c[L - 2 * base]
        if bc > 0:
            pt = (c[L - base] / bc - 1) * 100
            if abs(pt) >= (hi[L] / lo[L] - 1) * 100:
                rev = (1 if pt > 0 else -1) != kind
        iyi = uyari = False
        di = day_index(d, close_time)
        if di >= 0:
            cc = c[L]
            for z in fvg_open[di]:
                if z["tur"] == kind and z["alt"] <= hi[L] and z["ust"] >= lo[L]:
                    iyi = True
                if kind == 1:
                    ters = z["tur"] == -1 and ((z["alt"] <= cc <= z["ust"]) or
                                               (z["alt"] > cc and (z["alt"] / cc - 1) * 100 <= b.NOTE_NEAR_PCT))
                else:
                    ters = z["tur"] == 1 and ((z["alt"] <= cc <= z["ust"]) or
                                              (z["ust"] < cc and (1 - z["ust"] / cc) * 100 <= b.NOTE_NEAR_PCT))
                uyari = uyari or ters
        out.append(dict(i=L, t=close_time, yon=kind, hi=hi[L], lo=lo[L], stars=stars, rev=rev, iyi=iyi,
                        uyari=uyari))
    return out


def fvg_sinyalleri(s4, d, zones, datr, t_bas):
    """analyze_fvg ile aynı izleme: bölgeye ilk temas, pencere içinde dışarıda kapanış, puan."""
    t4, op, hi, lo, cl, qv = s4["t"], s4["o"], s4["h"], s4["l"], s4["c"], s4["q"]
    n = len(t4)
    if n < 40:
        return []
    zs = [dict(z, tem=0, po=None, pl=None, ph=None, pv=0.0, dead=False, uc=z["uc"]) for z in zones
          if z["formed"] >= t4[0]]
    qmed = pd.Series(qv).rolling(30).median().shift(1).to_numpy()
    out = []
    zi = 0
    aktif = []
    for k in range(n):
        while zi < len(zs) and zs[zi]["formed"] <= t4[k]:
            aktif.append(zs[zi])
            zi += 1
        ct = t4[k] + 14400
        di = day_index(d, ct)
        da = datr[di] if di >= 0 else np.nan
        dc1 = d["c"][di] if di >= 0 else None
        vr = qv[k] / qmed[k] if k >= 30 and qmed[k] > 0 else 0.0
        en_iyi = None
        for z in aktif:
            if z["dead"]:
                continue
            tur, alt, ust = z["tur"], z["alt"], z["ust"]
            yas = (t4[k] - z["formed"]) / DAY
            pay = b.FVG_NEAR_TOUCH * da if not np.isnan(da) else 0.0
            temas = lo[k] <= ust + pay if tur == 1 else hi[k] >= alt - pay
            if z["tem"] == 0 and temas and yas <= b.FVG_MAX_AGE_DAYS:
                z.update(tem=1, po=op[k], pl=lo[k], ph=hi[k], pv=vr)
            elif z["tem"] > 0:
                z.update(tem=z["tem"] + 1, pl=min(z["pl"], lo[k]), ph=max(z["ph"], hi[k]), pv=max(z["pv"], vr))
            if z["tem"] > 0:
                crng = z["ph"] - z["pl"]
                bozuldu = cl[k] < alt if tur == 1 else cl[k] > ust
                cikti = cl[k] > ust if tur == 1 else cl[k] < alt
                if bozuldu:
                    z["dead"] = True
                elif cikti:
                    z["dead"] = True
                    yakin = dc1 is not None and (dc1 <= ust * (1 + b.FVG_NEAR_PCT / 100) if tur == 1
                                                 else dc1 >= alt * (1 - b.FVG_NEAR_PCT / 100))
                    if crng <= 0 or not yakin or np.isnan(da) or ct < t_bas:
                        continue
                    if tur == 1:
                        fit = (min(z["po"], cl[k]) - z["pl"]) / crng
                        yon = cl[k] > z["po"]
                        geri = z["uc"] - ust
                        mes = z["pl"] > ust
                    else:
                        fit = (z["ph"] - max(z["po"], cl[k])) / crng
                        yon = cl[k] < z["po"]
                        geri = alt - z["uc"]
                        mes = z["ph"] < alt
                    score = int(fit >= b.FVG_WICK) + int(yon) + int(z["pv"] >= b.FVG_VOL)
                    if geri < b.FVG_MIN_PULLBACK * da or score < b.FVG_MIN_SCORE:
                        continue
                    sig = dict(i=k, t=ct, yon=tur, alt=alt, ust=ust, pl=z["pl"], ph=z["ph"], pay=b.FVG_NEAR_TOUCH * da,
                               score=score, yakin=mes, _f=z["formed"])
                    if en_iyi is None or (score, z["formed"]) > (en_iyi["score"], en_iyi["_f"]):
                        en_iyi = sig
                elif z["tem"] >= b.FVG_WINDOW:
                    z["dead"] = True
            else:
                z["uc"] = max(z["uc"], hi[k]) if tur == 1 else min(z["uc"], lo[k])
                if yas > b.FVG_MAX_AGE_DAYS:
                    z["dead"] = True
        aktif = [z for z in aktif if not z["dead"]]
        if en_iyi:
            out.append(en_iyi)
    return out


def ema21w_sinyalleri(w, t_bas):
    e = ema(w["c"], 21)
    out = []
    for i in range(21, len(w["c"])):
        if np.isnan(e[i]) or w["t"][i] + 7 * DAY < t_bas:
            continue
        o, c = w["o"][i], w["c"][i]
        if (o - e[i]) * (c - e[i]) >= 0:
            continue
        out.append(dict(i=i, t=w["t"][i] + 7 * DAY, yon=1 if c > e[i] else -1, e=e[i], h=w["h"][i], l=w["l"][i]))
    return out, e


def rsi_sinyalleri(s, t_bas, sec, pencere_once):
    """RSI 30/70 dönüşü (kapanış/fitil) + RSI'ın SMA14'ünü kesmesi; giriş ikisi tamamlanınca."""
    c, h, l = s["c"], s["h"], s["l"]
    r, g, lo = rsi_wilder(c)
    sma = pd.Series(r).rolling(14).mean().to_numpy()
    n = len(c)
    # dönüşler
    donus = []
    for i in range(16, n):
        if np.isnan(r[i - 1]) or np.isnan(r[i]):
            continue
        onceki, simdi = r[i - 1], r[i]
        if onceki < 30 <= simdi:
            donus.append((i, 1, "kapanış"))
        elif onceki > 70 >= simdi:
            donus.append((i, -1, "kapanış"))
        else:
            ud = rsi_if(l[i], c[i - 1], g[i - 1], lo[i - 1])
            uy = rsi_if(h[i], c[i - 1], g[i - 1], lo[i - 1])
            if onceki >= 30 and ud <= 30 < simdi:
                donus.append((i, 1, "fitil"))
            elif onceki <= 70 and uy >= 70 > simdi:
                donus.append((i, -1, "fitil"))
    kes_up = np.zeros(n, bool)
    kes_dn = np.zeros(n, bool)
    for i in range(1, n):
        if np.isnan(sma[i]) or np.isnan(sma[i - 1]):
            continue
        kes_up[i] = r[i] > sma[i] and r[i - 1] <= sma[i - 1]
        kes_dn[i] = r[i] < sma[i] and r[i - 1] >= sma[i - 1]
    out = []
    for i, yon, tip in donus:
        kes = kes_up if yon == 1 else kes_dn
        giris = None
        for j in range(i - pencere_once, i + 6):
            if 0 <= j < n and kes[j]:
                giris = max(i, j)
                break
        if giris is None or giris >= n or s["t"][giris] + sec < t_bas:
            continue
        # dönüş dönemindeki uç: RSI'ın bölge dışına çıktığı son andan girişe kadar (en fazla 20 mum)
        bas = giris
        while bas > max(giris - 20, 0) and ((yon == 1 and r[bas - 1] <= 32) or (yon == -1 and r[bas - 1] >= 68)
                                              or bas > i - 1):
            bas -= 1
        uc = np.min(l[bas:giris + 1]) if yon == 1 else np.max(h[bas:giris + 1])
        out.append(dict(i=giris, t=s["t"][giris] + sec, yon=yon, tip=tip, uc=uc, donus=i))
    return out, r, g, lo


# ======================= İŞLEM SİMÜLASYONU =======================
def simulate(s, a, i0, yon, emirler, stop0, iz, tp=None, bekle=None, iptal=None, rsi_cik=None, max_bar=None,
             piyasa=None):
    """
    s: mum dizileri (o,h,l,c,t), a: ATR dizisi, i0: sinyalden sonraki ilk mum indeksi
    emirler: [(fiyat, ağırlık, stop)] limit emirler (ağırlıklar toplamı 1); piyasa: sinyal kapanış fiyatı (piyasa emri)
    iz: ("be", k) 1R'de başa baş + k x ATR | ("atr", k) hemen k x ATR | ("swing", 3) | ("r1", 0) 1R geriden hemen
        | ("r1be", 0) 1R kârdan sonra 1R geriden
    tp: hedef fiyat (limit) | bekle: dolmayan emirlerin iptal edileceği mum sayısı
    iptal(j): j. mum kapanışında dolmamış emirleri iptal et mi | rsi_cik(j) -> çıkış fiyatı ya da None
    Dönüş: dict(R, pct, giris_t, cikis_t, dolan) ya da None (hiç dolmadı)
    """
    o, h, l, c = s["o"], s["h"], s["l"], s["c"]
    n = len(c)
    bekleyen = list(emirler)
    dolan = []                                         # (fiyat, ağırlık, ücret)
    stop = None
    if piyasa is not None:
        dolan.append((piyasa, 1.0, FEE_TAKER))
        stop = stop0
    en_iyi = None
    ilk_dolum = i0 if piyasa is not None else None
    son = n - 1 if max_bar is None else min(n - 1, i0 + max_bar)
    cikis = None
    j = i0
    while j <= son:
        # 1) bekleyen limit emirler
        if bekleyen:
            if bekle is not None and j - i0 >= bekle:      # bekleme süresi doldu: dolmayan emirler iptal
                bekleyen = []
                if not dolan:
                    return None
            kalan = []
            for fiyat, w, st in bekleyen:
                if (yon == 1 and l[j] <= fiyat) or (yon == -1 and h[j] >= fiyat):
                    px = min(o[j], fiyat) if yon == 1 else max(o[j], fiyat)
                    dolan.append((px, w, FEE_MAKER))
                    stop = st if stop is None else (min(stop, st) if yon == 1 else max(stop, st))
                    if ilk_dolum is None:
                        ilk_dolum = j
                else:
                    kalan.append((fiyat, w, st))
            bekleyen = kalan
        if not dolan:
            if iptal is not None and iptal(j):
                return None
            j += 1
            continue
        wsum = sum(w for _, w, _ in dolan)
        ort = sum(p * w for p, w, _ in dolan) / wsum
        R = abs(ort - stop0 if stop0 is not None else ort - stop)
        if R <= 0:
            return None
        # 2) stop (aynı mumda hedef de olsa önce stop)
        if (yon == 1 and l[j] <= stop) or (yon == -1 and h[j] >= stop):
            px = min(o[j], stop) if yon == 1 else max(o[j], stop)
            cikis = (px * (1 - KAYMA * yon), FEE_TAKER, j)
            break
        # 3) hedef
        if tp is not None and ((yon == 1 and h[j] >= tp) or (yon == -1 and l[j] <= tp)):
            cikis = (tp, FEE_MAKER, j)
            break
        # 4) RSI çıkışı (kapanış ya da fitil fiyatı)
        if rsi_cik is not None:
            px = rsi_cik(j)
            if px is not None:
                cikis = (px, FEE_TAKER, j)
                break
        # 5) iz süren stop (mum kapandıktan sonra güncellenir, sonraki mumdan geçerli)
        en_iyi = (h[j] if en_iyi is None else max(en_iyi, h[j])) if yon == 1 else \
            (l[j] if en_iyi is None else min(en_iyi, l[j]))
        tur, k = iz
        aj = a[j] if not np.isnan(a[j]) else 0.0
        kar = (en_iyi - ort) * yon
        yeni = None
        if tur == "be":
            if kar >= R:
                yeni = max(ort, en_iyi - k * aj) if yon == 1 else min(ort, en_iyi + k * aj)
        elif tur == "atr":
            yeni = en_iyi - k * aj * yon
        elif tur == "swing":
            if j - 2 >= 0:
                yeni = np.min(l[j - 2:j + 1]) if yon == 1 else np.max(h[j - 2:j + 1])
        elif tur == "r1":
            yeni = en_iyi - R * yon
        elif tur == "r1be":
            if kar >= R:
                yeni = en_iyi - R * yon
        if yeni is not None:
            stop = max(stop, yeni) if yon == 1 else min(stop, yeni)
        # bekleyen kademeli emirler tamamen dolmadan stop girişin üstüne çıkarsa kalanları iptal et
        if bekleyen and ((yon == 1 and stop >= min(p for p, _, _ in bekleyen)) or
                         (yon == -1 and stop <= max(p for p, _, _ in bekleyen))):
            bekleyen = []
        j += 1
    if not dolan:                                      # veri bitti, emir hiç dolmadı
        return None
    if cikis is None:                                  # veri bitti / süre doldu: son kapanıştan kapat
        cikis = (c[son], FEE_TAKER, son)
    px, fee_out, jc = cikis
    wsum = sum(w for _, w, _ in dolan)
    ort = sum(p * w for p, w, _ in dolan) / wsum
    risk = sum(w * abs(p - stop0) for p, w, _ in dolan) if stop0 is not None else 0
    pnl = sum(w * (px - p) * yon for p, w, _ in dolan)
    ucret = sum(w * (p * f + px * fee_out) for p, w, f in dolan)
    if risk <= 0:
        return None
    return dict(R=(pnl - ucret) / risk, pct=(pnl - ucret) / (ort * wsum) * 100, giris_t=s["t"][ilk_dolum],
                cikis_t=s["t"][jc], dolan=wsum, acik=jc == son and cikis[0] == c[son])


def calistir(sinyaller, fn):
    """Aynı coinde aynı anda tek işlem: sinyaller sırayla; önceki işlem/emir bitmeden gelen atlanır."""
    sonuc, mesgul = [], -1
    for sg in sinyaller:
        if sg["t"] < mesgul:
            continue
        r = fn(sg)
        if r is None:
            mesgul = sg.get("emir_bitis", sg["t"])
            continue
        r.update({k: v for k, v in sg.items() if k in ("yon", "stars", "iyi", "uyari", "rev", "score", "yakin", "tip", "t")})
        sonuc.append(r)
        mesgul = r["cikis_t"]
    return sonuc


# ======================= DEĞERLENDİRME =======================
def ozet(islemler, sinyal_sayisi):
    if not islemler:
        return dict(n=0, sinyal=sinyal_sayisi)
    R = np.array([x["R"] for x in islemler])
    pct = np.array([x["pct"] for x in islemler])
    sira = sorted(islemler, key=lambda x: x["cikis_t"])
    eq = np.cumsum([x["R"] for x in sira])
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], eq])) - np.concatenate([[0], eq])))
    seri = en_seri = 0
    for x in sira:
        seri = seri + 1 if x["R"] <= 0 else 0
        en_seri = max(en_seri, seri)
    kazanc, kayip = R[R > 0].sum(), -R[R <= 0].sum()
    gunler = {}
    for x in islemler:
        gunler.setdefault(int(x["giris_t"] // DAY), []).append(x["R"])
    gun_ort = float(np.mean([np.mean(v) for v in gunler.values()]))
    sure = np.mean([(x["cikis_t"] - x["giris_t"]) / 3600 for x in islemler])
    return dict(n=len(islemler), sinyal=sinyal_sayisi, dolma=len(islemler) / max(sinyal_sayisi, 1),
                kazanan=float(np.mean(R > 0)), ortR=float(R.mean()), medR=float(np.median(R)), topR=float(R.sum()),
                pf=float(kazanc / kayip) if kayip > 0 else None, dd=dd, seri=en_seri, ort_pct=float(pct.mean()),
                gun=len(gunler), gun_ortR=gun_ort, sure_saat=float(sure), buyuk3=float(np.mean(R >= 3)))


def bol(islemler, t_split):
    return [x for x in islemler if x["t"] < t_split], [x for x in islemler if x["t"] >= t_split]


lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def tablo(baslik, satirlar, n_min=30):
    out(f"\n#### {baslik}\n")
    out("| Ayar | Sinyal | İşlem | Kazanan | Ort. R | Medyan R | Toplam R | PF | En kötü seri | Maks. düşüş R | Ort. % | ≥3R | Gün başı ort. R |")
    out("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for ad, z in satirlar:
        if z.get("n", 0) == 0:
            out(f"| {ad} | {z.get('sinyal', 0)} | 0 | | | | | | | | | | |")
            continue
        az = " ⚠️az" if z["n"] < n_min else ""
        out(f"| {ad}{az} | {z['sinyal']} | {z['n']} | %{z['kazanan'] * 100:.0f} | {z['ortR']:+.2f} | {z['medR']:+.2f} | "
            f"{z['topR']:+.0f} | {z['pf'] if z['pf'] is None else round(z['pf'], 2)} | {z['seri']} | {z['dd']:.0f} | "
            f"{z['ort_pct']:+.2f} | %{z['buyuk3'] * 100:.0f} | {z['gun_ortR']:+.2f} |")


# ======================= ANA AKIŞ =======================
def main():
    t0 = time.time()
    data, symbols, top, now = load_data()
    print(f"Veri hazır ({(time.time() - t0) / 60:.0f} dk). Simülasyon başlıyor.", flush=True)
    sonuc = {}
    out(f"# Sinyal geçmiş testi\n\nVeri: {len(data)} coin (kırılım: hacme göre ilk {len(top)}), "
        f"test tarihi {time.strftime('%Y-%m-%d', time.gmtime(now))}. Ücret: limit %0.02, piyasa/stop %0.05 + %0.03 kayma. "
        f"R = başlangıç riskine göre sonuç. 'Eğitim' dönemi ayarları seçmek, 'doğrulama' (son dönem) sınamak içindir.\n")

    # ---------- coin başına hazırlık ----------
    hazir = {}
    for inst, dd in data.items():
        d = arr(dd["1D"])
        if len(d["c"]) < 30:
            continue
        zones, fvg_open, datr = daily_fvg(d)
        hazir[inst] = dict(d=d, zones=zones, fvg_open=fvg_open, datr=datr)

    # ===== 1) KIRILIM =====
    t_kir = now - KIR_GUN * DAY
    t_kir_split = now - DOG["KIR"] * DAY
    kir_var = []
    girisler = ["cizgi", "orta", "dip", "kademe"]
    izler = [("be", 1.5), ("be", 2.0), ("be", 3.0), ("atr", 2.0), ("swing", 3)]
    bekler = [24, 48, 96]
    kir_isl = {}
    kir_sinyal = {}
    for inst in top:
        if inst not in data or inst not in hazir:
            continue
        dd = data[inst]
        H = hazir[inst]
        seriler = {tf: arr(dd[tf]) for tf in ("15m", "1H", "4H") if tf in dd}
        for tf in ("15m", "1H", "4H"):
            s = seriler.get(tf)
            if s is None or len(s["c"]) < 300:
                continue
            htf = KIR_CFG[tf]["htf"]
            htf_s = seriler.get(htf) if htf != "1D" else H["d"]
            sigs = kirilim_sinyalleri(s, tf, htf_s, TF_SEC[htf], H["d"], H["fvg_open"], t_kir)
            kir_sinyal[tf] = kir_sinyal.get(tf, 0) + len(sigs)
            a, _ = atr(s["h"], s["l"], s["c"])
            sec = TF_SEC[tf]
            max_bar = {"15m": 7 * 96, "1H": 21 * 24, "4H": 60 * 6}[tf]
            for g in girisler:
                for bk in bekler:
                    for iz in izler:
                        def fn(sg, g=g, bk=bk, iz=iz):
                            yon, hi, lo = sg["yon"], sg["hi"], sg["lo"]
                            w = hi - lo
                            pay = 0.10 * w
                            cizgi, orta, dip = (hi, (hi + lo) / 2, lo) if yon == 1 else (lo, (hi + lo) / 2, hi)
                            stop_dip = dip - pay * yon
                            if g == "cizgi":
                                emir, st = [(cizgi, 1.0, cizgi - pay * yon)], cizgi - pay * yon
                            elif g == "orta":
                                emir, st = [(orta, 1.0, stop_dip)], stop_dip
                            elif g == "dip":
                                emir, st = [(dip, 1.0, stop_dip)], stop_dip
                            else:
                                emir, st = [(cizgi, 1 / 3, stop_dip), (orta, 1 / 3, stop_dip), (dip, 1 / 3, stop_dip)], stop_dip
                            i0 = sg["i"] + 1
                            sg["emir_bitis"] = sg["t"] + bk * sec
                            c = s["c"]
                            return simulate(s, a, i0, yon, emir, st, iz, bekle=bk,
                                            iptal=lambda j: (yon == 1 and c[j] < dip) or (yon == -1 and c[j] > dip),
                                            max_bar=max_bar)
                        key = (tf, g, bk, iz)
                        kir_isl.setdefault(key, []).extend(calistir([dict(x) for x in sigs], fn))
        print(f"  kırılım: {inst} bitti", flush=True)
    out("\n## 1) Kırılım\n")
    out("Giriş: cizgi = kırılan bant çizgisi, orta = bant ortası, dip = bandın öbür ucu, kademe = üçüne eşit bölünmüş. "
        "Bekleme mum sayısı (15m'de 24 mum = 6 saat). İz: be k = 1R'de başa baş sonra k x ATR, atr 2 = hemen 2 x ATR, swing = son 3 mum dibi.\n")
    kir_ozet = {}
    for tf in ("15m", "1H", "4H"):
        satir = []
        for g in girisler:
            for bk in bekler:
                for iz in izler:
                    isl = kir_isl.get((tf, g, bk, iz), [])
                    egit, dog = bol(isl, t_kir_split)
                    ze = ozet(egit, kir_sinyal.get(tf, 0))
                    zd = ozet(dog, kir_sinyal.get(tf, 0))
                    ad = f"{g} / {bk} mum / {iz[0]} {iz[1]}"
                    satir.append((ad, ze, zd, (tf, g, bk, iz)))
                    kir_ozet[f"{tf}|{ad}"] = dict(egitim=ze, dogrulama=zd)
        satir.sort(key=lambda x: (x[1].get("n", 0) >= 30, x[1].get("ortR", -99)), reverse=True)
        out(f"\n### Kırılım {tf} — toplam {kir_sinyal.get(tf, 0)} sinyal")
        tablo(f"{tf} eğitim dönemi, en iyi 15 ayar", [(x[0], x[1]) for x in satir[:15]])
        tablo(f"{tf} aynı ayarların doğrulama dönemi (son {DOG['KIR']} gün)", [(x[0], x[2]) for x in satir[:15]])
        tablo(f"{tf} eğitim dönemi, en kötü 5 ayar", [(x[0], x[1]) for x in satir[-5:]])
        # en iyi ayarın kırılımları
        if satir and satir[0][1].get("n", 0):
            key = satir[0][3]
            isl = kir_isl[key]
            parca = []
            for ad, f in [("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1),
                          ("0 yıldız", lambda x: x["stars"] == 0), ("1 yıldız", lambda x: x["stars"] == 1),
                          ("2 yıldız", lambda x: x["stars"] == 2), ("3 yıldız", lambda x: x["stars"] == 3),
                          ("✅ var", lambda x: x["iyi"]), ("✅ yok", lambda x: not x["iyi"]),
                          ("⚠️ var", lambda x: x["uyari"]), ("⚠️ yok", lambda x: not x["uyari"]),
                          ("🔄 dönüş", lambda x: x["rev"]), ("🔄 değil", lambda x: not x["rev"])]:
                alt = [x for x in isl if f(x)]
                parca.append((ad, ozet(alt, len(alt))))
            tablo(f"{tf} en iyi ayar ({satir[0][0]}) — tüm dönem, sinyal özelliklerine göre", parca)
    sonuc["kirilim"] = kir_ozet

    # ===== 2) FVG'DEN DÖNÜŞ =====
    t_fvg = now - FVG_GUN * DAY
    t_fvg_split = now - DOG["FVG"] * DAY
    fvg_isl, fvg_n = {}, 0
    for inst, H in hazir.items():
        s4 = arr(data[inst]["4H"])
        if len(s4["c"]) < 60:
            continue
        sigs = fvg_sinyalleri(s4, H["d"], H["zones"], H["datr"], t_fvg)
        fvg_n += len(sigs)
        a4, _ = atr(s4["h"], s4["l"], s4["c"])
        c4 = s4["c"]
        for giris in ("hemen", "limit 1g", "limit 3g", "limit 7g"):
            for stp in ("fitil", "bölge"):
                for k in (1.5, 2.0, 3.0):
                    def fn(sg, giris=giris, stp=stp, k=k):
                        yon = sg["yon"]
                        if stp == "fitil":
                            st = (sg["pl"] if yon == 1 else sg["ph"]) - sg["pay"] * yon
                        else:
                            st = (sg["alt"] if yon == 1 else sg["ust"]) - sg["pay"] * yon
                        i0 = sg["i"] + 1
                        if giris == "hemen":
                            px = c4[sg["i"]]
                            if (px - st) * yon <= 0:
                                return None
                            return simulate(s4, a4, i0, yon, [], st, ("be", k), piyasa=px, max_bar=60 * 6)
                        gun = int(giris.split()[1][:-1])
                        seviye = sg["ust"] if yon == 1 else sg["alt"]
                        sg["emir_bitis"] = sg["t"] + gun * DAY
                        alt, ust = sg["alt"], sg["ust"]
                        return simulate(s4, a4, i0, yon, [(seviye, 1.0, st)], st, ("be", k), bekle=gun * 6,
                                        iptal=lambda j: (yon == 1 and c4[j] < alt) or (yon == -1 and c4[j] > ust),
                                        max_bar=60 * 6)
                    fvg_isl.setdefault((giris, stp, k), []).extend(calistir([dict(x) for x in sigs], fn))
    out(f"\n## 2) FVG'den dönüş — toplam {fvg_n} sinyal (son {FVG_GUN} gün, {len(hazir)} coin)\n")
    satir, fvg_ozet = [], {}
    for key, isl in fvg_isl.items():
        egit, dog = bol(isl, t_fvg_split)
        ad = f"{key[0]} / stop {key[1]} / be {key[2]}"
        ze, zd = ozet(egit, fvg_n), ozet(dog, fvg_n)
        satir.append((ad, ze, zd, key))
        fvg_ozet[ad] = dict(egitim=ze, dogrulama=zd)
    satir.sort(key=lambda x: (x[1].get("n", 0) >= 30, x[1].get("ortR", -99)), reverse=True)
    tablo("Eğitim dönemi, bütün ayarlar", [(x[0], x[1]) for x in satir])
    tablo(f"Doğrulama dönemi (son {DOG['FVG']} gün)", [(x[0], x[2]) for x in satir])
    if satir and satir[0][1].get("n", 0):
        isl = fvg_isl[satir[0][3]]
        parca = []
        for ad, f in [("Long (🟩)", lambda x: x["yon"] == 1), ("Short (🟥)", lambda x: x["yon"] == -1),
                      ("⭐⭐", lambda x: x["score"] == 2), ("⭐⭐⭐", lambda x: x["score"] == 3),
                      ("yakın temas", lambda x: x["yakin"]), ("gerçek temas", lambda x: not x["yakin"])]:
            alt = [x for x in isl if f(x)]
            parca.append((ad, ozet(alt, len(alt))))
        tablo(f"En iyi ayar ({satir[0][0]}) — tüm dönem, sinyal özelliklerine göre", parca)
    sonuc["fvg"] = fvg_ozet

    # ===== 3) EMA21 HAFTALIK =====
    t_ema_split = now - DOG["EMA"] * DAY
    ema_isl, ema_n = {}, 0
    for inst, H in hazir.items():
        d = H["d"]
        w = arr(weekly_from_daily(data[inst]["1D"]))
        if len(w["c"]) < 30:
            continue
        sigs, we = ema21w_sinyalleri(w, 0)
        ema_n += len(sigs)
        ad_, _ = atr(d["h"], d["l"], d["c"])
        cd = d["c"]
        for giris in ("ema", "fvg", "ilk"):
            for hafta in (2, 4, 8):
                for iz in ("r1", "r1be"):
                    for tp in ("yok", "2R", "2x"):
                        def fn(sg, giris=giris, hafta=hafta, iz=iz, tp=tp):
                            yon = sg["yon"]
                            i0 = bisect.bisect_left(d["t"], sg["t"])          # haftadan sonraki ilk gün
                            if i0 >= len(cd):
                                return None
                            di = i0 - 1
                            pay = 0.1 * H["datr"][di] if di >= 0 and not np.isnan(H["datr"][di]) else 0
                            px_son = cd[di]
                            emirler = []
                            if giris in ("ema", "ilk"):
                                st = (sg["l"] if yon == 1 else sg["h"]) - pay * yon
                                if (sg["e"] - st) * yon > 0:
                                    emirler.append((sg["e"], 1.0, st, "ema"))
                            if giris in ("fvg", "ilk"):
                                aday = None
                                for z in H["fvg_open"][di] if di >= 0 else []:
                                    if yon == 1 and z["tur"] == 1 and z["ust"] < px_son and (1 - z["ust"] / px_son) * 100 <= 15:
                                        if aday is None or z["ust"] > aday["ust"]:
                                            aday = z
                                    if yon == -1 and z["tur"] == -1 and z["alt"] > px_son and (z["alt"] / px_son - 1) * 100 <= 15:
                                        if aday is None or z["alt"] < aday["alt"]:
                                            aday = z
                                if aday:
                                    sev = aday["ust"] if yon == 1 else aday["alt"]
                                    st = (aday["alt"] if yon == 1 else aday["ust"]) - pay * yon
                                    emirler.append((sev, 1.0, st, "fvg"))
                            if not emirler:
                                return None
                            # hangisi önce dolarsa: ilk dolan emri bul, onunla simüle et
                            bitis = min(len(cd) - 1, i0 + hafta * 7)
                            sec = None
                            for j in range(i0, bitis + 1):
                                wk = bisect.bisect_right(w["t"], d["t"][j]) - 1
                                for e in emirler:
                                    sev = e[0]
                                    if e[3] == "ema":       # EMA emri her hafta son kapanmış haftanın EMA21'ine taşınır
                                        wc = wk - 1 if (wk >= 0 and d["t"][j] < w["t"][wk] + 7 * DAY) else wk
                                        if wc >= sg["i"] and not np.isnan(we[wc]):
                                            sev = we[wc]
                                        if (sev - e[2]) * yon <= 0:
                                            continue
                                    if (yon == 1 and d["l"][j] <= sev) or (yon == -1 and d["h"][j] >= sev):
                                        cand = (sev, e[1], e[2], e[3])
                                        sec = cand if sec is None or (cand[0] - sec[0]) * yon > 0 else sec
                                if sec:
                                    break
                                # haftalık kapanış EMA'nın öbür tarafında: iptal
                                if d["t"][j] + DAY == w["t"][wk] + 7 * DAY and wk >= 0 and not np.isnan(we[wk]):
                                    if (yon == 1 and w["c"][wk] < we[wk]) or (yon == -1 and w["c"][wk] > we[wk]):
                                        return None
                            if sec is None:
                                sg["emir_bitis"] = sg["t"] + hafta * 7 * DAY
                                return None
                            giris_px, st = sec[0], sec[2]
                            R = abs(giris_px - st)
                            hedef = None
                            if tp == "2R":
                                hedef = giris_px + 2 * R * yon
                            elif tp == "2x":
                                hedef = giris_px * 2 if yon == 1 else giris_px * 0.5
                            r = simulate(d, ad_, j, yon, [(giris_px, 1.0, st)], st, (iz, 0), tp=hedef, bekle=1)
                            if r:
                                r["giris_tur"] = sec[3]
                            return r
                        ema_isl.setdefault((giris, hafta, iz, tp), []).extend(calistir([dict(x) for x in sigs], fn))
    out(f"\n## 3) EMA21 haftalık — toplam {ema_n} kesişim (bütün geçmiş, {len(hazir)} coin)\n")
    out("Giriş: ema = EMA21 çizgisine limit, fvg = en yakın günlük FVG sınırına limit, ilk = hangisi önce dolarsa. "
        "İz: r1 = hemen 1R geriden, r1be = 1R kârdan sonra 1R geriden. Kâr al: yok / 2R / 2x (fiyatın 2 katı; short'ta yarısı).\n")
    satir, ema_ozet = [], {}
    for key, isl in ema_isl.items():
        egit, dog = bol(isl, t_ema_split)
        ad = f"{key[0]} / {key[1]} hafta / {key[2]} / tp {key[3]}"
        ze, zd = ozet(egit, ema_n), ozet(dog, ema_n)
        satir.append((ad, ze, zd, key))
        ema_ozet[ad] = dict(egitim=ze, dogrulama=zd)
    satir.sort(key=lambda x: (x[1].get("n", 0) >= 30, x[1].get("ortR", -99)), reverse=True)
    tablo("Eğitim dönemi, en iyi 20 ayar", [(x[0], x[1]) for x in satir[:20]])
    tablo(f"Aynı ayarların doğrulama dönemi (son {DOG['EMA']} gün)", [(x[0], x[2]) for x in satir[:20]])
    tablo("Eğitim dönemi, en kötü 5 ayar", [(x[0], x[1]) for x in satir[-5:]])
    if satir and satir[0][1].get("n", 0):
        isl = ema_isl[satir[0][3]]
        parca = [(ad, ozet([x for x in isl if f(x)], len([x for x in isl if f(x)]))) for ad, f in
                 [("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1),
                  ("EMA'dan giriş", lambda x: x.get("giris_tur") == "ema"),
                  ("FVG'den giriş", lambda x: x.get("giris_tur") == "fvg")]]
        tablo(f"En iyi ayar ({satir[0][0]}) — tüm dönem", parca)
    sonuc["ema21w"] = ema_ozet

    # ===== 4) RSI =====
    rsi_ozet = {}
    for tf in ("4H", "1D", "1W"):
        t_bas = now - RSI4_GUN * DAY if tf == "4H" else 0
        t_split = now - DOG["RSI"] * DAY
        isl_all, n_sig = {}, 0
        for inst, H in hazir.items():
            if tf == "4H":
                s = arr(data[inst]["4H"])
            elif tf == "1D":
                s = H["d"]
            else:
                s = arr(weekly_from_daily(data[inst]["1D"]))
            if len(s["c"]) < 40:
                continue
            sec = TF_SEC[tf]
            a, _ = atr(s["h"], s["l"], s["c"])
            for pen in (0, 2):
                sigs, r, g, lo = rsi_sinyalleri(s, t_bas, sec, pen)
                if pen == 2:
                    n_sig += len(sigs)
                for iz in (("r1", 0), ("be", 2.0)):
                    for cik in ("kapanış", "fitil"):
                        def fn(sg, iz=iz, cik=cik, s=s, a=a, r=r, g=g, lo=lo):
                            yon = sg["yon"]
                            i = sg["i"]
                            pay = 0.1 * a[i] if not np.isnan(a[i]) else 0
                            st = sg["uc"] - pay * yon
                            px = s["c"][i]
                            if (px - st) * yon <= 0:
                                return None
                            hedef_rsi = 70 if yon == 1 else 30

                            def rsi_cik(j):
                                if np.isnan(r[j]):
                                    return None
                                if cik == "kapanış":
                                    if (yon == 1 and r[j] >= hedef_rsi) or (yon == -1 and r[j] <= hedef_rsi):
                                        return s["c"][j]
                                    return None
                                p = rsi_price(hedef_rsi, s["c"][j - 1], g[j - 1], lo[j - 1])
                                if p is None:
                                    return None
                                if yon == 1 and s["h"][j] >= p:
                                    return max(p, s["o"][j])
                                if yon == -1 and s["l"][j] <= p:
                                    return min(p, s["o"][j])
                                return None
                            return simulate(s, a, i + 1, yon, [], st, iz, piyasa=px, rsi_cik=rsi_cik)
                        isl_all.setdefault((pen, iz, cik), []).extend(calistir([dict(x) for x in sigs], fn))
        out(f"\n## 4) RSI {tf} — dönüş + SMA kesişimi, {n_sig} sinyal\n")
        out("Pencere: kesişim dönüşten en fazla 5 mum sonra (0) ya da 2 mum önce ile 5 mum sonra arası (2). "
            "İz: r1 = 1R geriden, be 2 = 1R'de başa baş sonra 2 x ATR. Çıkış: RSI 70 kapanışla ya da fitille.\n")
        satir = []
        for key, isl in isl_all.items():
            egit, dog = bol(isl, t_split)
            ad = f"pencere {key[0]} / {key[1][0]} {key[1][1]} / RSI 70 {key[2]}"
            ze, zd = ozet(egit, n_sig), ozet(dog, n_sig)
            satir.append((ad, ze, zd, key))
            rsi_ozet[f"{tf}|{ad}"] = dict(egitim=ze, dogrulama=zd)
        satir.sort(key=lambda x: (x[1].get("n", 0) >= 30, x[1].get("ortR", -99)), reverse=True)
        tablo(f"RSI {tf} eğitim dönemi", [(x[0], x[1]) for x in satir])
        tablo(f"RSI {tf} doğrulama dönemi (son {DOG['RSI']} gün)", [(x[0], x[2]) for x in satir])
        if satir and satir[0][1].get("n", 0):
            isl = isl_all[satir[0][3]]
            parca = [(ad, ozet([x for x in isl if f(x)], len([x for x in isl if f(x)]))) for ad, f in
                     [("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1),
                      ("Kapanışla dönüş", lambda x: x["tip"] == "kapanış"), ("Fitille dönüş", lambda x: x["tip"] == "fitil")]]
            tablo(f"RSI {tf} en iyi ayar ({satir[0][0]}) — tüm dönem", parca)
    sonuc["rsi"] = rsi_ozet

    out(f"\nToplam süre: {(time.time() - t0) / 60:.0f} dk")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(OUT_JSON, "w") as f:
        json.dump(sonuc, f)


if __name__ == "__main__":
    try:
        main()
    except Exception:                                   # hata da sonuç dalına yazılsın (kayıtlar buradan okunamıyor)
        import traceback
        lines.append("\n## HATA\n\n```\n" + traceback.format_exc() + "```")
        with open(OUT_MD, "w") as f:
            f.write("\n".join(lines) + "\n")
        raise
