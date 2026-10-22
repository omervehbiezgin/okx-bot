"""
OKX perpetual tarayıcı - GitHub Actions için tek seferlik sürüm (v5)

TradingView göstergesi "OKX Tarayıcı Sinyalleri" ile AYNI kurallar ve varsayılan ayarlar.
OKX'teki TÜM USDT perpetual (futures) coinleri tarar. Dört tarama türü:

  1) YATAY KIRILIM (15m, 1H, 4H, 1D)
     Zorunlu şartlar:
       - Bant: son 'base' mumun aralığı, banttan önceki 'lookback' mumun ortalama mum boyunun
         (gerçek aralık ortalaması) en fazla 'k' katı genişliğinde (her coin kendi oynaklığına göre)
       - Bant gerçek olmalı: üst ve alt sınıra (bant genişliğinin %15'i içine) en az 2'şer mum yaklaşmış
       - Kapanış, bandın dışında en az bant genişliğinin %20'si kadar
       - Gövde mum boyunun en az %60'ı, kapanış mumun üst (aşağı kırılımda alt) çeyreğinde
     Yıldızlar: hacim >= 1,5x | mum boyu >= bant ortalamasının 2 katı | üst zaman dilimi EMA21 uyumu
     Notlar: ✅ bant günlük FVG içinde oluştu | ⚠️ kırılım ters yöndeki günlük FVG'ye doğru (%2)
  2) EMA21 1W : Haftalık mum gövdesi EMA21'i kesip kapattı (fitil sayılmaz)
  3) EMA200 1D: Günlük mum gövdesi EMA200'ü kesip kapattı
  4) FVG'DEN DÖNÜŞ: Günlük FVG'ye 4H mumlarla ilk temas (yakın temas payı dahil), 3 mumluk pencere
     içinde bölgenin dışında kapanış, geri çekilme ve puan şartları.

Ortam değişkenleri: TG_TOKEN, TG_CHAT_ID
"""
import os
import sys
import json
import time
import bisect
import statistics
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://www.okx.com"
STATE_FILE = "state.json"

# ---------------- AYARLAR (göstergenin varsayılanlarıyla aynı) ----------------
# Yatay kırılım
#   lookback : ortalama mum boyu ve hacim için bakılan mum sayısı (bant öncesi)
#   base     : bant olarak incelenen mum sayısı (son mum hariç)
#   k        : bant genişliği, ortalama mum boyunun en fazla kaç katı olabilir
#   htf      : yıldız için EMA21'ine bakılan bir üst zaman dilimi
BREAKOUT = {
    "15m":   dict(lookback=96, base=32, k=3.5, sec=900,   htf="1H",    htf_sec=3600),
    "1H":    dict(lookback=72, base=24, k=3.0, sec=3600,  htf="4H",    htf_sec=14400),
    "4H":    dict(lookback=60, base=20, k=3.0, sec=14400, htf="1Dutc", htf_sec=86400),
    "1Dutc": dict(lookback=40, base=14, k=2.5, sec=86400, htf="1Wutc", htf_sec=604800),
}
BRK_CLOSE_OUT = 0.20     # kapanış, bandın dışında en az bant genişliği x bu oran
BRK_BODY = 0.60          # gövde / mum boyu
BRK_CLOSE_POS = 0.75     # kapanış mumun üst (alt) çeyreğinde
BRK_TOUCH_ZONE = 0.15    # sınıra "yaklaşma" bölgesi: bant genişliği x bu oran
BRK_MIN_TOUCH = 2        # üst ve alt sınıra en az kaç mum yaklaşmalı
BRK_LIVE_PCT = 80        # bant içindeki mumların en az % kaçında işlem olmuş olmalı (boş mumlu sahte bantları eler)
BRK_MIN_VOL_RATIO = 1.2  # kırılım mumu hacmi, önceki 'lookback' mumun ortanca hacminin en az bu katı (göstergeyle aynı)
MIN_24H_USDT = 1_000_000 # son 24 saat USDT hacmi bunun altındaki coinler hiç taranmaz (hacimsiz coin elemesi)
BRK_STAR_VOL = 1.5       # ⭐ hacim normalin en az kaç katı
BRK_STAR_SIZE = 2.0      # ⭐ mum boyu bant ortalamasının en az kaç katı
NOTE_NEAR_PCT = 2.0      # ⚠️ notu: kırılım ters FVG'ye en fazla % kaç uzakta
NOTE_MAX_ZONES = 60      # kırılım notları için tutulan en fazla açık günlük FVG

# Günlük FVG ve 4H tepki (FVG'den dönüş)
ATR_DAYS = 14            # günlük ortalama mum boyu kaç günden hesaplanır
FVG_MIN_GAP_ATR = 0.25   # FVG en az (günlük ort. mum boyu x bu) genişlikte
FVG_MAX_AGE_DAYS = 45    # bölgeye ilk giriş en fazla kaç günlük FVG'de sayılır
FVG_NEAR_PCT = 15.0      # son günlük kapanış bölgeden en fazla % kaç uzakta olabilir
FVG_NEAR_TOUCH = 0.10    # yakın temas payı (günlük ort. mum boyu x bu); 0 = sadece gerçek temas
FVG_MIN_PULLBACK = 0.5   # bölgeye gelmeden önce en az (günlük ort. mum boyu x bu) geri çekilme
FVG_WINDOW = 3           # ilk girişten sonra tepki için beklenecek 4H mum (giren mum dahil)
FVG_WICK = 0.40          # ⭐ fitil, birleşik mum boyunun en az bu oranı
FVG_VOL = 1.2            # ⭐ hacim, son 30 adet 4H mumun ortancasının en az bu katı
FVG_MIN_SCORE = 2        # 3 puandan en az kaçı
FVG_SEC = 14400

# EMA kesişim ayarları (off: mum hizalama ofseti; OKX 1Wutc haftası Pazartesi 00:00 UTC açılır)
EMA_TASKS = {
    "EMA21_1W":   dict(bar="1Wutc", period=21,  bars=80,  sec=604800, off=345600),
    "EMA200_1D":  dict(bar="1Dutc", period=200, bars=420, sec=86400,  off=0),
}

# RSI(14) dönüşleri (günlük ve haftalık kapanışta)
#   Kapanış dönüşü: önceki mum RSI 30 altında / 70 üstünde kapanmış, son mum tekrar 30 üstünde / 70 altında kapanmış
#   Fitil dönüşü  : son mumun fitili (en düşük / en yüksek fiyat) RSI'ı 30 ve altına / 70 ve üstüne taşımış,
#                   ama mum 30 üstünde / 70 altında kapanmış (önceki mum bölgenin dışındaysa)
RSI_PERIOD = 14
RSI_LOW, RSI_HIGH = 30, 70
RSI_TASKS = {
    "RSI_1D": dict(bar="1Dutc", sec=86400,  off=0),
    "RSI_1W": dict(bar="1Wutc", sec=604800, off=345600),
}

MAX_ALERTS_PER_SCAN = 50         # bir kırılım mesajında en fazla kaç coin listelensin
REQUEST_PAUSE = 0.1
# Bir görev state'te İLK KEZ görülüyorsa ve mum bu süreden (saniye) önce kapanmışsa taranmaz.
LATE_LIMIT = {900: 3600, 3600: 10800, 14400: 21600, 86400: 21600, 604800: 43200}
# -----------------------------------------------------------------------------

session = requests.Session()
TR = timezone(timedelta(hours=3))                       # Türkiye saati
_daily_cache = {}


class StaleCandle(Exception):
    """OKX beklenen mumu henüz "kapandı" olarak sunmadı."""


def expect_candle(ts_ms, candle_open):
    if int(ts_ms) < candle_open * 1000:
        raise StaleCandle()


def candle_stamp(candle_open, sec, late=0):
    a = datetime.fromtimestamp(candle_open, TR)
    b = datetime.fromtimestamp(candle_open + sec, TR)
    txt = f"🕒 Mum (TR saati): {a:%d.%m.%Y %H:%M} → {b:%d.%m.%Y %H:%M}"
    if late > 1800:
        txt += f"\n⚠️ Bildirim {late // 3600} sa {late % 3600 // 60} dk gecikmeli (GitHub tetikleme gecikmesi)"
    return txt


def api(path, params):
    r = session.get(BASE + path, params=params, timeout=15)
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError(f"OKX geçersiz yanıt (HTTP {r.status_code}): {r.text[:200]}")
    if j.get("code") != "0":
        raise RuntimeError(f"OKX hata: {j.get('code')} {j.get('msg')}")
    return j["data"]


def crypto_only():
    """Sadece KRİPTO perpetual'ları döndürür (hisse, emtia, döviz vb. TradFi kontratları hariç).
    OKX 'instCategory': 1 = kripto, 3 = hisse, 4 = emtia, 5 = döviz, 6 = tahvil.
    Kategori bilgisi alınamazsa None döner ve filtre uygulanmaz."""
    try:
        data = api("/api/v5/public/instruments", {"instType": "SWAP"})
    except Exception as e:
        print("UYARI: kontrat kategorileri alınamadı, TradFi filtresi uygulanmadı:", e)
        return None
    kategori = {d["instId"]: str(d.get("instCategory", "")) for d in data}
    if not any(kategori.values()):
        print("UYARI: OKX kategori bilgisi vermedi, TradFi filtresi uygulanmadı.")
        return None
    tradfi = sorted(k.replace("-USDT-SWAP", "") for k, v in kategori.items()
                    if v and v != "1" and k.endswith("-USDT-SWAP"))
    if tradfi:
        print(f"Kripto dışı {len(tradfi)} kontrat taranmıyor: {', '.join(tradfi)}")
    return {k for k, v in kategori.items() if v in ("", "1")}


def get_symbols():
    """OKX'teki kripto USDT perpetual (futures) sözleşmeleri, hacme göre sıralı.
    Hisse/emtia gibi TradFi kontratları ve 24s hacmi düşük coinler hariç."""
    kripto = crypto_only()
    data = api("/api/v5/market/tickers", {"instType": "SWAP"})
    rows = []
    for t in data:
        inst = t["instId"]
        if not inst.endswith("-USDT-SWAP"):
            continue
        if kripto is not None and inst not in kripto:
            continue
        try:
            qv = float(t["volCcy24h"]) * float(t["last"])
        except (ValueError, KeyError):
            qv = 0.0
        if qv >= MIN_24H_USDT:
            rows.append((inst, qv))
    rows.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in rows]


# ---------------- Mum verisi ----------------
def candles(inst, bar, limit):
    """Son kapanmış mumlar (eskiden yeniye). limit en fazla 300."""
    data = api("/api/v5/market/candles", {"instId": inst, "bar": bar, "limit": str(min(limit, 300))})
    return [r for r in reversed(data) if r[8] == "1"]


def candles_more(inst, bar, n):
    """En az n kapanmış mum: önce son 300, gerekirse history-candles ile geriye devam."""
    rows = candles(inst, bar, 300)
    while len(rows) < n and rows:
        time.sleep(0.15)
        data = api("/api/v5/market/history-candles",
                   {"instId": inst, "bar": bar, "limit": "100", "after": rows[0][0]})
        older = [r for r in reversed(data) if r[8] == "1"]
        if not older:
            break
        rows = older + rows
    return rows


def fetch_closed(inst, bar, n):
    """Son n kapanmış mumu (eskiden yeniye) history-candles ile getirir (EMA taraması için)."""
    out, after = [], None
    while len(out) < n:
        params = {"instId": inst, "bar": bar, "limit": "100"}
        if after:
            params["after"] = after
        data = api("/api/v5/market/history-candles", params)
        if not data:
            break
        out.extend(data)
        after = data[-1][0]
        if len(data) < 100:
            break
        time.sleep(0.15)
    return [r for r in reversed(out) if r[8] == "1"]


def true_ranges(h, l, c):
    tr = []
    for j in range(len(h)):
        if j == 0:
            tr.append(h[j] - l[j])
        else:
            tr.append(max(h[j] - l[j], abs(h[j] - c[j - 1]), abs(l[j] - c[j - 1])))
    return tr


def ema_series(vals, n):
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n                               # SMA ile başlat
    res = [None] * (n - 1) + [e]
    for v in vals[n:]:
        e = v * k + e * (1 - k)
        res.append(e)
    return res


# ---------------- Günlük veri, ortalama mum boyu ve FVG'ler ----------------
def daily(inst):
    """Kapanmış günlük mumlar (bir çalışma boyunca önbellekte tutulur)."""
    if inst not in _daily_cache:
        rows = candles(inst, "1Dutc", 300)
        ts = [int(r[0]) // 1000 for r in rows]
        h = [float(r[2]) for r in rows]
        l = [float(r[3]) for r in rows]
        c = [float(r[4]) for r in rows]
        tr = true_ranges(h, l, c)
        atr = [None] * len(rows)
        for j in range(ATR_DAYS - 1, len(rows)):
            atr[j] = sum(tr[j - ATR_DAYS + 1:j + 1]) / ATR_DAYS
        _daily_cache[inst] = dict(ts=ts, h=h, l=l, c=c, atr=atr, close=[t + 86400 for t in ts])
        time.sleep(REQUEST_PAUSE)
    return _daily_cache[inst]


def day_at(d, t):
    """t anında kapanmış son günün indeksi (yoksa -1)."""
    return bisect.bisect_right(d["close"], t) - 1


def daily_zones(d, upto):
    """Kapanışı 'upto' anına kadar gerçekleşmiş günlerden oluşan günlük FVG'ler (oluşum sırasıyla)."""
    zones = []
    last = day_at(d, upto)
    for f in range(2, last + 1):
        i = f - 2
        a = d["atr"][f]
        if a is None:
            continue
        if d["h"][i] < d["l"][f] and d["l"][f] - d["h"][i] >= FVG_MIN_GAP_ATR * a:
            zones.append(dict(tur=1, alt=d["h"][i], ust=d["l"][f], formed=d["close"][f], f=f, uc=d["h"][f]))
        elif d["l"][i] > d["h"][f] and d["l"][i] - d["h"][f] >= FVG_MIN_GAP_ATR * a:
            zones.append(dict(tur=-1, alt=d["h"][f], ust=d["l"][i], formed=d["close"][f], f=f, uc=d["l"][f]))
    return zones


def open_fvgs(d, upto):
    """Kırılım notları için: 'upto' anında henüz tamamen dolmamış günlük FVG'ler."""
    by_f = {z["f"]: z for z in daily_zones(d, upto)}
    acik = []
    last = day_at(d, upto)
    for f in range(2, last + 1):
        # f günü kapanınca önce bu günle tamamen dolanlar çıkar, sonra yeni FVG eklenir
        acik = [z for z in acik if not ((z["tur"] == 1 and d["l"][f] <= z["alt"]) or
                                         (z["tur"] == -1 and d["h"][f] >= z["ust"]))]
        if f in by_f:
            acik.append(by_f[f])
            if len(acik) > NOTE_MAX_ZONES:
                acik.pop(0)
    return acik


# ---------------- 1) YATAY KIRILIM ----------------
def analyze_breakout(inst, bar, cfg, candle_open):
    lb, base = cfg["lookback"], cfg["base"]
    rows = candles(inst, bar, lb + base + 6)
    if len(rows) < lb + base + 3 or len(rows) < 2 * base + 3:
        return None
    L = len(rows) - 1
    expect_candle(rows[L][0], candle_open)

    o = [float(r[1]) for r in rows]
    h = [float(r[2]) for r in rows]
    l = [float(r[3]) for r in rows]
    c = [float(r[4]) for r in rows]
    qv = [float(r[7]) for r in rows]

    band = range(L - base, L)
    hi = max(h[j] for j in band)
    lo = min(l[j] for j in band)
    w = hi - lo
    boy = h[L] - l[L]
    if lo <= 0 or w <= 0 or boy <= 0 or o[L] <= 0:
        return None

    # Bant genişliği <= k x (banttan önceki 'lookback' mumun ortalama mum boyu)
    tr = true_ranges(h, l, c)
    ort_once = sum(tr[L - base - lb:L - base]) / lb
    if w > cfg["k"] * ort_once:
        return None

    up_ok = (c[L] > hi + BRK_CLOSE_OUT * w and c[L] > o[L] and
             c[L] - o[L] >= BRK_BODY * boy and c[L] - l[L] >= BRK_CLOSE_POS * boy)
    dn_ok = (c[L] < lo - BRK_CLOSE_OUT * w and c[L] < o[L] and
             o[L] - c[L] >= BRK_BODY * boy and h[L] - c[L] >= BRK_CLOSE_POS * boy)
    if up_ok:
        kind = 1
    elif dn_ok:
        kind = -1
    else:
        return None

    # Gerçek bant: üst ve alt sınıra en az 2'şer mum yaklaşmış olmalı
    ust_temas = sum(1 for j in band if h[j] >= hi - BRK_TOUCH_ZONE * w)
    alt_temas = sum(1 for j in band if l[j] <= lo + BRK_TOUCH_ZONE * w)
    if ust_temas < BRK_MIN_TOUCH or alt_temas < BRK_MIN_TOUCH:
        return None

    # Likidite: kırılım mumu hacmi normalin en az 1,2 katı ve bantta işlem görmüş mum oranı
    canli = sum(1 for j in band if qv[j] > 0)
    if canli * 100 < BRK_LIVE_PCT * base:
        return None
    med = statistics.median(qv[L - lb:L])
    ratio = qv[L] / med if med > 0 else None
    if ratio is None or ratio < BRK_MIN_VOL_RATIO:
        return None

    # Yıldızlar
    ort_boy = sum(h[j] - l[j] for j in band) / base
    stars = int(ratio is not None and ratio >= BRK_STAR_VOL) + int(boy >= BRK_STAR_SIZE * ort_boy)

    close_time = candle_open + cfg["sec"]
    try:
        hrows = candles(inst, cfg["htf"], 100)
        hcl = [float(r[4]) for r in hrows if int(r[0]) // 1000 + cfg["htf_sec"] <= close_time]
        if len(hcl) >= 21:
            e = ema_series(hcl, 21)[-1]
            stars += int((kind == 1 and c[L] > e) or (kind == -1 and c[L] < e))
        time.sleep(REQUEST_PAUSE)
    except Exception as ex:
        print(f"{inst} üst zaman dilimi EMA alınamadı: {ex}")

    # Önceki trend (dönüş mü devam mı)
    rng = (hi / lo - 1) * 100
    rev = False
    if c[L - 2 * base] > 0:
        pt = (c[L - base] / c[L - 2 * base] - 1) * 100
        if abs(pt) >= rng:
            rev = (1 if pt > 0 else -1) != kind

    # Günlük FVG notları
    iyi = uyari = None
    try:
        d = daily(inst)
        cc = c[L]
        best_i = best_u = None
        for z in open_fvgs(d, close_time):
            dist = abs((z["alt"] + z["ust"]) / 2 - cc)
            if z["tur"] == kind and z["alt"] <= hi and z["ust"] >= lo:
                if best_i is None or dist < best_i:
                    best_i, iyi = dist, z
            if kind == 1:
                ters = z["tur"] == -1 and ((z["alt"] <= cc <= z["ust"]) or
                                           (z["alt"] > cc and (z["alt"] / cc - 1) * 100 <= NOTE_NEAR_PCT))
            else:
                ters = z["tur"] == 1 and ((z["alt"] <= cc <= z["ust"]) or
                                          (z["ust"] < cc and (1 - z["ust"] / cc) * 100 <= NOTE_NEAR_PCT))
            if ters and (best_u is None or dist < best_u):
                best_u, uyari = dist, z
    except Exception as ex:
        print(f"{inst} günlük FVG notu alınamadı: {ex}")

    return {"inst": inst, "kind": kind, "change": (c[L] / o[L] - 1) * 100, "ratio": ratio,
            "vol": qv[L], "price": c[L], "range": rng, "base": base, "stars": stars,
            "reversal": rev, "iyi": iyi, "uyari": uyari}


# ---------------- 2) EMA KESİŞİMİ ----------------
def analyze_ema(inst, cfg, candle_open):
    rows = fetch_closed(inst, cfg["bar"], cfg["bars"])
    n = cfg["period"]
    if len(rows) < n + 2:
        return None
    last = rows[-1]
    expect_candle(last[0], candle_open)

    closes = [float(r[4]) for r in rows]
    e = ema_series(closes, n)[-1]
    o, c = float(last[1]), float(last[4])
    if (o - e) * (c - e) >= 0:                          # sadece gövde kesişimi
        return None
    kind = "UP" if c > e else "DOWN"
    return {"inst": inst, "kind": kind, "price": c, "ema": e, "dist": (c / e - 1) * 100}


# ---------------- RSI DÖNÜŞÜ ----------------
def rsi_state(closes, n=RSI_PERIOD):
    """TradingView ta.rsi ile aynı (Wilder, ilk değer SMA). Her mum için (rsi, ort_kazanç, ort_kayıp) döner."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    ch = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    g = sum(max(c, 0) for c in ch[:n]) / n
    l = sum(max(-c, 0) for c in ch[:n]) / n
    def val(g, l):
        return 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    out[n] = (val(g, l), g, l)
    for i in range(n + 1, len(closes)):
        c = ch[i - 1]
        g = (g * (n - 1) + max(c, 0)) / n
        l = (l * (n - 1) + max(-c, 0)) / n
        out[i] = (val(g, l), g, l)
    return out


def analyze_rsi(inst, cfg, candle_open):
    rows = candles(inst, cfg["bar"], 300)
    if len(rows) < 50:
        return None
    expect_candle(rows[-1][0], candle_open)
    h = [float(r[2]) for r in rows]
    l = [float(r[3]) for r in rows]
    c = [float(r[4]) for r in rows]
    st = rsi_state(c)
    if st[-2] is None:
        return None
    n = RSI_PERIOD
    onceki, (simdi, _, _) = st[-2][0], st[-1]
    _, g0, l0 = st[-2]

    def rsi_if(price):                                   # son mum bu fiyatta kapansaydı RSI ne olurdu
        d = price - c[-2]
        g = (g0 * (n - 1) + max(d, 0)) / n
        ls = (l0 * (n - 1) + max(-d, 0)) / n
        return 100.0 if ls == 0 else 100 - 100 / (1 + g / ls)

    if onceki < RSI_LOW <= simdi:
        return dict(inst=inst, kind="UP", tip="kapanış", onceki=onceki, simdi=simdi, uc=None, price=c[-1])
    if onceki > RSI_HIGH >= simdi:
        return dict(inst=inst, kind="DOWN", tip="kapanış", onceki=onceki, simdi=simdi, uc=None, price=c[-1])
    uc_dusuk, uc_yuksek = rsi_if(l[-1]), rsi_if(h[-1])
    if onceki >= RSI_LOW and uc_dusuk <= RSI_LOW < simdi:
        return dict(inst=inst, kind="UP", tip="fitil", onceki=onceki, simdi=simdi, uc=uc_dusuk, price=c[-1])
    if onceki <= RSI_HIGH and uc_yuksek >= RSI_HIGH > simdi:
        return dict(inst=inst, kind="DOWN", tip="fitil", onceki=onceki, simdi=simdi, uc=uc_yuksek, price=c[-1])
    return None


# ---------------- 3) FVG'DEN DÖNÜŞ (bölge günlük, tepki 4H) ----------------
def analyze_fvg(inst, candle_open):
    d = daily(inst)
    if len(d["ts"]) < ATR_DAYS + 3:
        return None
    last_t = candle_open + FVG_SEC                       # taranan 4H mumun kapanışı
    dc_now = d["c"][day_at(d, last_t)]
    zones = [z for z in daily_zones(d, last_t)
             if (last_t - z["formed"]) / 86400 <= FVG_MAX_AGE_DAYS + 1
             and ((z["tur"] == 1 and dc_now <= z["ust"] * (1 + FVG_NEAR_PCT / 100)) or
                  (z["tur"] == -1 and dc_now >= z["alt"] * (1 - FVG_NEAR_PCT / 100)))]
    if not zones:                                       # yakında uygun bölge yok: 4H çekmeye gerek yok
        return None

    first = min(z["formed"] for z in zones)
    need = int((candle_open - first) / FVG_SEC) + 35
    rows = candles_more(inst, "4H", need)
    if len(rows) < 40:
        return None
    expect_candle(rows[-1][0], candle_open)
    t4 = [int(r[0]) // 1000 for r in rows]
    op = [float(r[1]) for r in rows]
    hi = [float(r[2]) for r in rows]
    lo = [float(r[3]) for r in rows]
    cl = [float(r[4]) for r in rows]
    qv = [float(r[7]) for r in rows]
    L = len(rows) - 1

    # Sadece 4H verisinin kapsadığı bölgeler, oluşumdan itibaren mum mum izlenir (göstergeyle aynı)
    for z in zones:
        z.update(tem=0, po=None, pl=None, ph=None, pv=0.0, dead=False)
    zones = [z for z in zones if z["formed"] >= t4[0]]
    best = None
    for k in range(L + 1):
        ct = t4[k] + FVG_SEC
        di = day_at(d, ct)
        datr = d["atr"][di] if di >= 0 else None
        dc1 = d["c"][di] if di >= 0 else None
        med = statistics.median(qv[k - 30:k]) if k >= 30 else 0
        vr = qv[k] / med if med > 0 else 0.0
        for z in zones:
            if z["dead"] or t4[k] < z["formed"]:
                continue
            tur, alt, ust = z["tur"], z["alt"], z["ust"]
            yas = (t4[k] - z["formed"]) / 86400
            pay = FVG_NEAR_TOUCH * datr if datr else 0.0
            temas = lo[k] <= ust + pay if tur == 1 else hi[k] >= alt - pay
            if z["tem"] == 0 and temas and yas <= FVG_MAX_AGE_DAYS:
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
                    if k != L:
                        continue
                    yakin = dc1 is not None and (dc1 <= ust * (1 + FVG_NEAR_PCT / 100) if tur == 1
                                                 else dc1 >= alt * (1 - FVG_NEAR_PCT / 100))
                    if crng <= 0 or not yakin or not datr:
                        continue
                    if tur == 1:
                        fit = (min(z["po"], cl[k]) - z["pl"]) / crng
                        yon = cl[k] > z["po"]
                        geri = z["uc"] - ust
                        har = (z["uc"] / ust - 1) * 100
                        mes = (z["pl"] / ust - 1) * 100 if z["pl"] > ust else None
                    else:
                        fit = (z["ph"] - max(z["po"], cl[k])) / crng
                        yon = cl[k] < z["po"]
                        geri = alt - z["uc"]
                        har = (alt / z["uc"] - 1) * 100
                        mes = (1 - z["ph"] / alt) * 100 if z["ph"] < alt else None
                    score = int(fit >= FVG_WICK) + int(yon) + int(z["pv"] >= FVG_VOL)
                    if geri < FVG_MIN_PULLBACK * datr or score < FVG_MIN_SCORE:
                        continue
                    if best is None or (score, z["formed"]) > (best["score"], best["_formed"]):
                        best = dict(kind="SUPPORT" if tur == 1 else "RESIST", bot=alt, top=ust,
                                    age=int(yas), wick=fit, vol_ratio=z["pv"], move=har, score=score,
                                    mum=z["tem"], mesafe=mes, _formed=z["formed"])
                elif z["tem"] >= FVG_WINDOW:
                    z["dead"] = True
            else:
                z["uc"] = max(z["uc"], hi[k]) if tur == 1 else min(z["uc"], lo[k])
                if yas > FVG_MAX_AGE_DAYS:
                    z["dead"] = True

    if not best:
        return None
    best.pop("_formed")
    best.update(inst=inst, price=cl[L])
    return best


# ---------------- Telegram / yardımcılar ----------------
def send(msg):
    """Uzun mesajı 4000 karakterde böler. Hepsi gittiyse True döner."""
    print(plain(msg) + "\n", flush=True)
    token, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID")
    if not (token and chat):
        print("UYARI: TG_TOKEN veya TG_CHAT_ID tanımlı değil, Telegram'a mesaj gönderilmedi!")
        return False

    chunks, cur = [], ""
    for line in msg.split("\n"):
        if len(cur) + len(line) + 1 > 3500:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        chunks.append(cur)

    ok = True
    for ch in chunks:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": to_html(ch), "parse_mode": "HTML",
                      "disable_web_page_preview": "true"}, timeout=10,
            )
            if r.status_code == 400:                    # HTML işlenemezse bağlantısız düz metin gönder
                print("Telegram HTML hatası, düz metinle gönderiliyor:", r.text[:200])
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat, "text": plain(ch)},
                    timeout=10,
                )
            if r.status_code != 200:
                print("Telegram hata:", r.status_code, r.text[:200])
                ok = False
        except Exception as e:
            print("Telegram hatası:", e)
            ok = False
    return ok


def fmt_usdt(v):
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    return f"{v / 1_000:.0f}K"


# TradingView'de açılacak zaman dilimi (bildirimin zaman dilimi)
TV_INTERVAL = {"15m": "15", "1H": "60", "4H": "240", "1Dutc": "D", "RSI_1D": "D", "RSI_1W": "W",
               "EMA21_1W": "W", "EMA200_1D": "D", "FVG": "240"}
LINK_ON, LINK_OFF = "\x01", "\x02"


def link(inst, tf):
    """Coin adını TradingView bağlantısı olacak şekilde işaretler (send() içinde HTML'e çevrilir)."""
    return f"{LINK_ON}{inst}|{TV_INTERVAL.get(tf, '15')}{LINK_OFF}"


def to_html(text):
    """Metni Telegram HTML'ine çevirir; işaretli coin adlarını tıklanabilir TradingView bağlantısı yapar."""
    import html, re
    text = html.escape(text, quote=False)

    def repl(m):
        inst, iv = m.group(1), m.group(2)
        sym = inst.replace("-USDT-SWAP", "")
        app = f"https://tr.tradingview.com/symbols/{sym}USDT.P/?exchange=OKX"                    # 📱 telefonda uygulamayı açar
        pc = f"https://tr.tradingview.com/chart/?symbol=OKX%3A{sym}USDT.P&amp;interval={iv}"     # 💻 bilgisayarda grafiği açar
        return f'{sym} <a href="{app}">📱</a> <a href="{pc}">💻</a>'
    return re.sub(re.escape(LINK_ON) + r"([^|]+)\|([^" + re.escape(LINK_OFF) + r"]+)" + re.escape(LINK_OFF), repl, text)


def plain(text):
    """Bağlantı işaretlerini kaldırıp sadece coin adını bırakır."""
    import re
    return re.sub(re.escape(LINK_ON) + r"([^|]+)\|[^" + re.escape(LINK_OFF) + r"]+" + re.escape(LINK_OFF),
                  lambda m: short(m.group(1)), text)


def short(inst):
    return inst.replace("-USDT-SWAP", "")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------------- Mesaj biçimleri ----------------
def msg_breakout(bar, hits):
    label = bar.replace("utc", "")
    hits.sort(key=lambda x: (x["stars"], x["reversal"], x["ratio"] or 0), reverse=True)
    lines = [f"📦➡️🚀 [{label}] Yatay kırılım: {len(hits)} coin"]
    for r in hits[:MAX_ALERTS_PER_SCAN]:
        up = r["kind"] == 1
        kind = "🟢 YUKARI" if up else "🔴 AŞAĞI"
        stars = " " + "⭐" * r["stars"] if r["stars"] else ""
        tag = " 🔄dönüş" if r["reversal"] else ""
        hacim = f"hacim {r['ratio']:.1f}x ({fmt_usdt(r['vol'])})" if r["ratio"] else f"hacim {fmt_usdt(r['vol'])}"
        lines.append(
            f"{kind} {link(r['inst'], bar)}{stars}{tag}  {r['change']:+.1f}%  |  {hacim}  |  "
            f"bant {r['base']} mum, %{r['range']:.1f}  |  {r['price']}"
        )
        if r["iyi"]:
            z = r["iyi"]
            lines.append(f"    ✅ {'destek' if up else 'direnç'} FVG'sinden kırılım ({z['alt']:.6g}–{z['ust']:.6g})")
        if r["uyari"]:
            z = r["uyari"]
            lines.append(f"    ⚠️ günlük {'direnç' if up else 'destek'} FVG'sine doğru ({z['alt']:.6g}–{z['ust']:.6g})")
    if len(hits) > MAX_ALERTS_PER_SCAN:
        lines.append(f"... ve {len(hits) - MAX_ALERTS_PER_SCAN} coin daha")
    return "\n".join(lines)


def msg_ema(name, cfg, hits):
    up = [h for h in hits if h["kind"] == "UP"]
    down = [h for h in hits if h["kind"] == "DOWN"]
    tf = cfg["bar"].replace("utc", "")
    lines = [f"📈 [{tf}] EMA{cfg['period']} gövde kesişimi: {len(hits)} coin"]

    def row(h):
        return (f"  {link(h['inst'], name)}  kapanış {h['price']}  |  EMA {h['ema']:.6g}  "
                f"({h['dist']:+.1f}%)")

    if up:
        lines.append("🟢 EMA'yı YUKARI kesip kapatanlar:")
        for h in sorted(up, key=lambda x: x["dist"], reverse=True):
            lines.append(row(h))
    if down:
        lines.append("🔴 EMA'yı AŞAĞI kesip kapatanlar:")
        for h in sorted(down, key=lambda x: x["dist"]):
            lines.append(row(h))
    return "\n".join(lines)


def msg_rsi(name, cfg, hits):
    tf = cfg["bar"].replace("utc", "")
    lines = [f"📊 [{tf}] RSI({RSI_PERIOD}) dönüşü: {len(hits)} coin"]

    def row(h):
        if h["tip"] == "kapanış":
            return f"  {link(h['inst'], name)}  kapanışla  |  RSI {h['onceki']:.1f} → {h['simdi']:.1f}  |  {h['price']}"
        return (f"  {link(h['inst'], name)}  fitille  |  fitilde RSI {h['uc']:.1f}, kapanış {h['simdi']:.1f}  "
                f"|  {h['price']}")

    up = [h for h in hits if h["kind"] == "UP"]
    down = [h for h in hits if h["kind"] == "DOWN"]
    if up:
        lines.append(f"🟢 {RSI_LOW} altına inip tekrar üstünde kapatanlar:")
        lines += [row(h) for h in sorted(up, key=lambda x: x["tip"])]
    if down:
        lines.append(f"🔴 {RSI_HIGH} üstüne çıkıp tekrar altında kapatanlar:")
        lines += [row(h) for h in sorted(down, key=lambda x: x["tip"])]
    return "\n".join(lines)


def msg_fvg(hits):
    sup = [h for h in hits if h["kind"] == "SUPPORT"]
    res = [h for h in hits if h["kind"] == "RESIST"]
    lines = [f"🧲 FVG'den dönüş (günlük bölge, 4H tepki): {len(hits)} coin"]

    def row(h, alt_ust, hareket):
        yakin = f" (yakın temas %{h['mesafe']:.2f})" if h["mesafe"] is not None else ""
        return (f"  {link(h['inst'], 'FVG')} {'⭐' * h['score']}{yakin}  FVG {h['bot']:.6g}–{h['top']:.6g} "
                f"({h['age']} gün önce)  |  4H kapanış {h['price']}  |  girişten sonraki {h['mum']}. mum  |  "
                f"{alt_ust} fitil %{h['wick'] * 100:.0f}  |  hacim {h['vol_ratio']:.1f}x  |  {hareket} %{h['move']:.1f}")

    if sup:
        lines.append("🔵 YUKARI dönüş (günlük destek FVG'si):")
        for h in sorted(sup, key=lambda x: (x["score"], -x["age"]), reverse=True):
            lines.append(row(h, "alt", "zirveden geri çekilme"))
    if res:
        lines.append("🟠 AŞAĞI dönüş (günlük direnç FVG'si):")
        for h in sorted(res, key=lambda x: (x["score"], -x["age"]), reverse=True):
            lines.append(row(h, "üst", "dipten yükseliş"))
    return "\n".join(lines)


# ---------------- Ana akış ----------------
def last_closed_open(now, sec, off=0):
    return ((now - off) // sec) * sec + off - sec


def main():
    state = load_state()
    now = int(time.time())
    manual = (os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
              and os.getenv("TEST_RUN", "true").lower() != "false")

    tasks = []   # (state_key, tür, ad, cfg, mum açılışı)
    for bar, cfg in BREAKOUT.items():
        tasks.append((f"BRK_{bar}", "brk", bar, cfg, last_closed_open(now, cfg["sec"])))
    for name, cfg in EMA_TASKS.items():
        tasks.append((name, "ema", name, cfg, last_closed_open(now, cfg["sec"], cfg["off"])))
    tasks.append(("FVG_1Dutc>4H", "fvg", "1Dutc>4H", {"sec": FVG_SEC}, last_closed_open(now, FVG_SEC)))
    for name, cfg in RSI_TASKS.items():
        tasks.append((name, "rsi", name, cfg, last_closed_open(now, cfg["sec"], cfg["off"])))

    due = [t for t in tasks if state.get(t[0]) != t[4]]

    if manual:
        send("✅ Test: OKX tarayıcı botu GitHub Actions üzerinde çalışıyor.")
    if not due:
        print("Taranacak yeni mum yok.")
        return

    symbols = get_symbols()
    print(f"{len(symbols)} sembol, taranacak: {[t[0] for t in due]}")

    for key, kind, name, cfg, candle_open in due:
        late = now - (candle_open + cfg["sec"])
        limit = LATE_LIMIT.get(cfg["sec"], cfg["sec"] * 3)
        if not manual and key not in state and late > limit:
            print(f"{key}: ilk kez görülen görev, mum {late // 60} dk önce kapanmış "
                  f"(sınır {limit // 60} dk), taranmadan geçildi.")
            state[key] = candle_open
            save_state(state)
            continue

        wait = candle_open + cfg["sec"] + 10 - time.time()  # OKX mumu onaylasın
        if wait > 0:
            time.sleep(wait)

        hits = []
        stale = 0
        for inst in symbols:
            try:
                if kind == "brk":
                    r = analyze_breakout(inst, name, cfg, candle_open)
                elif kind == "fvg":
                    r = analyze_fvg(inst, candle_open)
                elif kind == "rsi":
                    r = analyze_rsi(inst, cfg, candle_open)
                else:
                    r = analyze_ema(inst, cfg, candle_open)
            except StaleCandle:
                stale += 1
                continue
            except Exception as e:
                print(f"{inst} {key} hata: {e}")
                time.sleep(1)
                continue
            time.sleep(REQUEST_PAUSE)
            if r:
                hits.append(r)

        if stale > len(symbols) * 0.3:
            print(f"{key}: OKX mumu henüz onaylamamış ({stale}/{len(symbols)}), sonraki çalışmada tekrar denenecek.")
            continue

        print(f"{key} tarandı, {len(hits)} sonuç.")
        sent_ok = True
        if hits:
            if kind == "brk":
                text = msg_breakout(name, hits)
            elif kind == "fvg":
                text = msg_fvg(hits)
            elif kind == "rsi":
                text = msg_rsi(name, cfg, hits)
            else:
                text = msg_ema(name, cfg, hits)
            head, _, rest = text.partition("\n")
            text = head + "\n" + candle_stamp(candle_open, cfg["sec"], late) + ("\n" + rest if rest else "")
            sent_ok = send(text)

        if sent_ok:
            state[key] = candle_open
            save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
