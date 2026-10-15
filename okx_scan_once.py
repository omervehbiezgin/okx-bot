"""
OKX perpetual tarayıcı - GitHub Actions için tek seferlik sürüm (v3)

Üç tarama türü:
  1) BREAKOUT : Yatay (dar aralıklı) hareketi ilk kıran mum + hacim onayı.
                Zaten pump/dump yapmış coinler, aralık geniş olduğu için elenir.
  2) EMA21 1W : Haftalık mum gövdesi EMA21'i kesip kapandıysa bildirir (açılış EMA'nın
                bir tarafında, kapanış diğer tarafında; fitil dokunuşu sayılmaz).
  3) EMA200 1D: Aynı mantık, günlük mum ve EMA200 için.
  4) FVG      : Günlük grafikteki FVG bölgesine 4H mumla ilk kez gelip tepki alan coinler
                (yükseliş FVG'si = destek tepkisi, düşüş FVG'si = direnç reddi).

Ortam değişkenleri: TG_TOKEN, TG_CHAT_ID
"""
import os
import sys
import json
import time
import statistics
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://www.okx.com"
STATE_FILE = "state.json"

# ---------------- AYARLAR ----------------
# Yatay kırılım ayarları
#   lookback : hacim için normal değeri hesaplamak üzere bakılan mum sayısı
#   base     : "yatay bölge" olarak incelenen mum sayısı (son mum hariç)
#   range    : bu bölgenin (en yüksek / en düşük - 1) * 100 değeri en fazla % kaç olabilir
#   change   : kırılım mumunun gövdesi (açılış->kapanış) en az % kaç olmalı
#   ratio, z : hacim, normalin kaç katı / robust z-score
#   min_usdt : kırılım mumunun en az USDT hacmi
#   sec      : mum süresi (sn)
BREAKOUT = {
    "15m":   dict(lookback=96, base=32, range=2.5,  change=1.0, ratio=2.5, z=3.5, min_usdt=300_000,    sec=900),
    "1H":    dict(lookback=72, base=24, range=4.0,  change=1.5, ratio=2.5, z=3.5, min_usdt=1_000_000,  sec=3600),
    "4H":    dict(lookback=60, base=20, range=7.0,  change=2.5, ratio=2.5, z=3.0, min_usdt=3_000_000,  sec=14400),
    "1Dutc": dict(lookback=40, base=14, range=12.0, change=4.0, ratio=2.0, z=3.0, min_usdt=10_000_000, sec=86400),
}

# EMA kesişim ayarları (off: mum hizalama ofseti; OKX 1Wutc haftası Pazartesi 00:00 UTC açılır)
EMA_TASKS = {
    "EMA21_1W":   dict(bar="1Wutc", period=21,  bars=80,  sec=604800, off=345600),
    "EMA200_1D":  dict(bar="1Dutc", period=200, bars=420, sec=86400,  off=0),
}

# FVG (Fair Value Gap) ayarları: bölge GÜNLÜK grafikten bulunur, tepki 4H mumla ölçülür
#   zone_bar/zone_lookback : bölgenin bulunacağı mum türü ve kaç mum geriye bakılacağı
#   react_bar/react_limit  : tepkinin ölçüleceği mum türü ve çekilecek mum sayısı (4H için 300 = ~50 gün)
#   max_age_days     : FVG en fazla kaç gün önce oluşmuş olabilir (react_limit kapsamını aşmasın)
#   near_pct         : son günlük kapanış bölgeden en fazla % kaç uzakta olabilir (gereksiz istek elemesi)
#   min_gap          : FVG boşluğu en az % kaç olmalı
#   min_move         : bölgeye gelmeden önceki hareket en az % (destek: zirveden geri çekilme, direnç: dipten yükseliş)
#   wick             : 4H tepki fitili, mum aralığının en az bu oranı olmalı (puan şartı)
#   vol_ratio        : 4H hacim, son 30 mumun medyanının en az kaç katı (puan şartı)
#   min_score        : 3 puandan (fitil, mum yönü, hacim) en az kaçı gerekli
#   max_prev_touches : oluşumdan beri bölgeye kaç 4H mum girmiş olabilir (0 = sadece ilk test)
FVG = {
    "1Dutc>4H": dict(zone_bar="1Dutc", zone_sec=86400, zone_lookback=60,
                     react_bar="4H", react_limit=300, sec=14400,
                     max_age_days=45, near_pct=15.0, min_gap=1.0, min_move=4.0,
                     wick=0.40, vol_ratio=1.2, min_score=2, max_prev_touches=0),
}

TOP_N = 100                      # hacme göre ilk N USDT perpetual
MIN_QUOTE_VOLUME = 10_000_000    # 24s USDT hacmi altı coinler elenir
MAX_ALERTS_PER_SCAN = 10         # bir mesajda en fazla kaç coin listelensin
REQUEST_PAUSE = 0.1
# Bir görev state'te İLK KEZ görülüyorsa (yeni özellik eklendi veya önbellek silindi) ve mum bu
# süreden (saniye) önce kapanmışsa taranmaz; böylece eski mumlar için geç bildirim gelmez.
# State'te kaydı olan görevlerde uygulanmaz (GitHub tetiklemesi gecikse bile sinyal kaçmaz).
# Elle (Run workflow) çalıştırmada da uygulanmaz.
LATE_LIMIT = {900: 3600, 3600: 10800, 14400: 21600, 86400: 21600, 604800: 43200}
# -----------------------------------------

session = requests.Session()
TR = timezone(timedelta(hours=3))                       # Türkiye saati


class StaleCandle(Exception):
    """OKX beklenen mumu henüz "kapandı" olarak sunmadı."""


def expect_candle(ts_ms, candle_open):
    if int(ts_ms) < candle_open * 1000:
        raise StaleCandle()


def candle_stamp(candle_open, sec, late=0):
    a = datetime.fromtimestamp(candle_open, TR)
    b = datetime.fromtimestamp(candle_open + sec, TR)
    txt = f"🕒 Mum (TR saati): {a:%d.%m.%Y %H:%M} → {b:%d.%m.%Y %H:%M}"
    if late > 1800:                                         # tarama 30 dk'dan fazla gecikmişse belirt
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


def get_symbols():
    data = api("/api/v5/market/tickers", {"instType": "SWAP"})
    rows = []
    for t in data:
        inst = t["instId"]
        if not inst.endswith("-USDT-SWAP"):
            continue
        try:
            qv = float(t["volCcy24h"]) * float(t["last"])
        except (ValueError, KeyError):
            continue
        if qv >= MIN_QUOTE_VOLUME:
            rows.append((inst, qv))
    rows.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in rows[:TOP_N]]


def fetch_closed(inst, bar, n):
    """Son n kapanmış mumu (eskiden yeniye) getirir. 100'lük sayfalarla geriye gider."""
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
        time.sleep(0.15)                                # history-candles: 20 istek / 2 sn sınırı
    return [r for r in reversed(out) if r[8] == "1"]


# ---------------- 1) YATAY KIRILIM ----------------
def analyze_breakout(inst, bar, cfg, candle_open):
    data = api("/api/v5/market/candles",
               {"instId": inst, "bar": bar, "limit": str(cfg["lookback"] + 2)})
    rows = [r for r in reversed(data) if r[8] == "1"]
    base = cfg["base"]
    if len(rows) < base + 5:
        return None

    last = rows[-1]
    expect_candle(last[0], candle_open)

    o, c = float(last[1]), float(last[4])
    vol = float(last[7])
    if o <= 0 or vol < cfg["min_usdt"]:
        return None

    # Yatay bölge: son mumdan önceki 'base' mum
    base_rows = rows[-1 - base:-1]
    hi = max(float(r[2]) for r in base_rows)
    lo = min(float(r[3]) for r in base_rows)
    if lo <= 0:
        return None
    rng = (hi / lo - 1) * 100
    if rng > cfg["range"]:                              # zaten hareketli / geniş aralık -> ele
        return None

    change = (c / o - 1) * 100
    if c > hi and change >= cfg["change"]:
        kind = "UP"
    elif c < lo and change <= -cfg["change"]:
        kind = "DOWN"
    else:
        return None

    # Hacim onayı
    hist = [float(r[7]) for r in rows[:-1]]
    median = statistics.median(hist)
    mad = statistics.median([abs(v - median) for v in hist])
    if median <= 0 or mad <= 0:
        return None
    ratio = vol / median
    z = 0.6745 * (vol - median) / mad
    if ratio < cfg["ratio"] or z < cfg["z"]:
        return None

    # Bilgi amaçlı: yataydan önceki trend (dönüş mü devam mı)
    prev_trend = None
    if len(rows) >= 2 * base + 2:
        start_close = float(rows[-1 - base][4])
        before_close = float(rows[-1 - 2 * base][4])
        if before_close > 0:
            pt = (start_close / before_close - 1) * 100
            if abs(pt) >= rng:                          # yataydan belirgin bir trendle gelmiş
                prev_trend = "UP" if pt > 0 else "DOWN"

    return {"inst": inst, "kind": kind, "change": change, "ratio": ratio,
            "vol": vol, "price": c, "range": rng, "base": base,
            "reversal": prev_trend is not None and prev_trend != kind,
            "prev_trend": prev_trend}


# ---------------- 2) EMA KESİŞİMİ ----------------
def ema_series(vals, n):
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n                               # SMA ile başlat
    res = [None] * (n - 1) + [e]
    for v in vals[n:]:
        e = v * k + e * (1 - k)
        res.append(e)
    return res


def analyze_ema(inst, cfg, candle_open):
    rows = fetch_closed(inst, cfg["bar"], cfg["bars"])
    n = cfg["period"]
    if len(rows) < n + 2:                               # yeterli geçmişi olmayan coin
        return None
    last = rows[-1]
    expect_candle(last[0], candle_open)

    closes = [float(r[4]) for r in rows]
    e = ema_series(closes, n)[-1]
    o, h, l, c = float(last[1]), float(last[2]), float(last[3]), float(last[4])

    # Sadece gövde kesişimi: açılış EMA'nın bir tarafında, kapanış diğer tarafında.
    # (Fitil dokunuşu sayılmaz.)
    if (o - e) * (c - e) >= 0:
        return None

    kind = "UP" if c > e else "DOWN"                    # yukarı kesip kapattı / aşağı kesip kapattı
    return {"inst": inst, "kind": kind, "price": c, "ema": e,
            "dist": (c / e - 1) * 100}


# ---------------- 3) FVG TEPKİSİ (bölge günlük, tepki 4H) ----------------
def analyze_fvg(inst, cfg, candle_open):
    """
    1) Günlük mumlardan FVG bölgeleri bulunur:
         Yükseliş FVG : gün[i].high < gün[i+2].low   -> bölge [gün[i].high, gün[i+2].low]  (destek)
         Düşüş FVG    : gün[i].low  > gün[i+2].high  -> bölge [gün[i+2].high, gün[i].low]  (direnç)
       Bölge, FVG'yi tamamlayan günün kapanışından itibaren geçerlidir.
    2) Tepki, az önce kapanan 4H mumla ölçülür:
         destek : 4H mum bölgeye girdi (low <= üst sınır) ve kapanış bölgenin ÜSTÜNDE
         direnç : 4H mum bölgeye girdi (high >= alt sınır) ve kapanış bölgenin ALTINDA
       Oluşumdan bu yana hiçbir 4H mum bölgeye girmemiş olmalı (ilk test) ve hiçbir 4H mum
       bölgeyi tersine kapanışla bozmamış olmalı.
    """
    zsec = cfg["zone_sec"]
    d = api("/api/v5/market/candles",
            {"instId": inst, "bar": cfg["zone_bar"], "limit": str(cfg["zone_lookback"] + 2)})
    drows = [r for r in reversed(d) if r[8] == "1"]
    if len(drows) < 10:
        return None
    dts = [int(r[0]) // 1000 for r in drows]
    dhi = [float(r[2]) for r in drows]
    dlo = [float(r[3]) for r in drows]
    dcl = [float(r[4]) for r in drows]

    # ---- günlük FVG bölgeleri ----
    zones = []
    for i in range(len(drows) - 2):
        f = i + 2
        formed = dts[f] + zsec                          # bölge, f gününün kapanışında oluşur
        age_days = (candle_open - formed) / 86400
        if age_days < 0 or age_days > cfg["max_age_days"]:
            continue
        if dhi[i] < dlo[f]:
            bot, top, kind = dhi[i], dlo[f], "SUPPORT"
            swing0 = dhi[f]
        elif dlo[i] > dhi[f]:
            bot, top, kind = dhi[f], dlo[i], "RESIST"
            swing0 = dlo[f]
        else:
            continue
        if bot <= 0 or (top / bot - 1) * 100 < cfg["min_gap"]:
            continue
        near = cfg["near_pct"] / 100                    # fiyat bölgeden çok uzaktaysa 4H çekme
        if kind == "SUPPORT" and dcl[-1] > top * (1 + near):
            continue
        if kind == "RESIST" and dcl[-1] < bot * (1 - near):
            continue
        zones.append((kind, bot, top, formed, age_days, swing0))
    if not zones:
        return None

    # ---- 4H mumlar ----
    r4 = api("/api/v5/market/candles",
             {"instId": inst, "bar": cfg["react_bar"], "limit": str(cfg["react_limit"])})
    rows = [r for r in reversed(r4) if r[8] == "1"]
    if len(rows) < 40:
        return None
    expect_candle(rows[-1][0], candle_open)
    t4 = [int(r[0]) // 1000 for r in rows]
    op = [float(r[1]) for r in rows]
    hi = [float(r[2]) for r in rows]
    lo = [float(r[3]) for r in rows]
    cl = [float(r[4]) for r in rows]
    vo = [float(r[7]) for r in rows]

    L = len(rows) - 1
    o, h, l, c = op[L], hi[L], lo[L], cl[L]
    rng = h - l
    if rng <= 0:
        return None
    med_vol = statistics.median(vo[-31:-1])
    vol_ratio = vo[L] / med_vol if med_vol > 0 else 0.0

    best = None
    for kind, bot, top, formed, age_days, swing0 in zones:
        if t4[L] < formed:
            continue
        prev = [j for j in range(L) if t4[j] >= formed]  # oluşum ile sinyal mumu arası 4H mumlar

        if kind == "SUPPORT":
            if sum(1 for j in prev if lo[j] <= top) > cfg["max_prev_touches"]:
                continue
            if any(cl[j] < bot for j in prev):          # bölge aşağı kapanışla bozulmuş
                continue
            if not (l <= top and c > top):
                continue
            move = (max([swing0] + [hi[j] for j in prev]) / top - 1) * 100
            if move < cfg["min_move"]:
                continue
            wick = (min(o, c) - l) / rng
            score = int(wick >= cfg["wick"]) + int(c > o) + int(vol_ratio >= cfg["vol_ratio"])
        else:
            if sum(1 for j in prev if hi[j] >= bot) > cfg["max_prev_touches"]:
                continue
            if any(cl[j] > top for j in prev):          # bölge yukarı kapanışla bozulmuş
                continue
            if not (h >= bot and c < bot):
                continue
            move = (bot / min([swing0] + [lo[j] for j in prev]) - 1) * 100
            if move < cfg["min_move"]:
                continue
            wick = (h - max(o, c)) / rng
            score = int(wick >= cfg["wick"]) + int(c < o) + int(vol_ratio >= cfg["vol_ratio"])

        if score < cfg["min_score"]:
            continue
        if best is None or (score, formed) > (best["score"], best["_formed"]):
            best = dict(kind=kind, bot=bot, top=top, age=int(age_days), wick=wick,
                        move=move, score=score, _formed=formed)

    if not best:
        return None
    best.pop("_formed")
    best.update(inst=inst, price=c, vol_ratio=vol_ratio)
    return best


# ---------------- Telegram / yardımcılar ----------------
def send(msg):
    """Uzun mesajı 4000 karakterde böler. Hepsi gittiyse True döner."""
    print(msg + "\n", flush=True)
    token, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID")
    if not (token and chat):
        return True

    chunks, cur = [], ""
    for line in msg.split("\n"):
        if len(cur) + len(line) + 1 > 4000:
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
                data={"chat_id": chat, "text": ch}, timeout=10,
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
    # Önce dönüşler, sonra hacim oranı
    hits.sort(key=lambda x: (x["reversal"], x["ratio"]), reverse=True)
    lines = [f"📦➡️🚀 [{label}] Yatay kırılım: {len(hits)} coin"]
    for r in hits[:MAX_ALERTS_PER_SCAN]:
        kind = "🟢 YUKARI" if r["kind"] == "UP" else "🔴 AŞAĞI"
        tag = " 🔄dönüş" if r["reversal"] else ""
        lines.append(
            f"{kind} {short(r['inst'])}{tag}  {r['change']:+.1f}%  |  hacim {r['ratio']:.1f}x "
            f"({fmt_usdt(r['vol'])})  |  yatay {r['base']} mum, %{r['range']:.1f} aralık  |  {r['price']}"
        )
    if len(hits) > MAX_ALERTS_PER_SCAN:
        lines.append(f"... ve {len(hits) - MAX_ALERTS_PER_SCAN} coin daha")
    return "\n".join(lines)


def msg_ema(name, cfg, hits):
    up = [h for h in hits if h["kind"] == "UP"]
    down = [h for h in hits if h["kind"] == "DOWN"]
    tf = cfg["bar"].replace("utc", "")
    lines = [f"📈 [{tf}] EMA{cfg['period']} gövde kesişimi: {len(hits)} coin"]

    def row(h):
        return (f"  {short(h['inst'])}  kapanış {h['price']}  |  EMA {h['ema']:.6g}  "
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


def msg_fvg(bar, hits):
    label = bar.replace("utc", "")
    sup = [h for h in hits if h["kind"] == "SUPPORT"]
    res = [h for h in hits if h["kind"] == "RESIST"]
    lines = [f"🧲 FVG tepkisi (günlük bölge, 4H tepki): {len(hits)} coin"]
    if sup:
        lines.append("🟢 DESTEK tepkisi (yükseliş FVG'sinden dönüş ihtimali):")
        for h in sorted(sup, key=lambda x: (x["score"], -x["age"]), reverse=True):
            lines.append(
                f"  {short(h['inst'])} {'⭐' * h['score']}  FVG {h['bot']:.6g}–{h['top']:.6g} "
                f"({h['age']} gün önce)  |  4H kapanış {h['price']}  |  alt fitil %{h['wick'] * 100:.0f}  |  "
                f"hacim {h['vol_ratio']:.1f}x  |  zirveden geri çekilme %{h['move']:.0f}"
            )
    if res:
        lines.append("🔴 DİRENÇ reddi (düşüş FVG'sinden aşağı dönüş ihtimali):")
        for h in sorted(res, key=lambda x: (x["score"], -x["age"]), reverse=True):
            lines.append(
                f"  {short(h['inst'])} {'⭐' * h['score']}  FVG {h['bot']:.6g}–{h['top']:.6g} "
                f"({h['age']} gün önce)  |  4H kapanış {h['price']}  |  üst fitil %{h['wick'] * 100:.0f}  |  "
                f"hacim {h['vol_ratio']:.1f}x  |  dipten yükseliş %{h['move']:.0f}"
            )
    return "\n".join(lines)


# ---------------- Ana akış ----------------
def last_closed_open(now, sec, off=0):
    return ((now - off) // sec) * sec + off - sec


def main():
    state = load_state()
    now = int(time.time())
    # Elle test: sadece "Run workflow" ile ve test kutusu işaretliyse. Dışarıdan (API ile) tetiklemede
    # workflow dosyası TEST_RUN=false gönderir, bot normal çalışır. TEST_RUN tanımlı değilse eski davranış.
    manual = (os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
              and os.getenv("TEST_RUN", "true").lower() != "false")

    tasks = []   # (state_key, tür, ad, cfg, mum açılışı)
    for bar, cfg in BREAKOUT.items():
        co = last_closed_open(now, cfg["sec"])
        tasks.append((f"BRK_{bar}", "brk", bar, cfg, co))
    for name, cfg in EMA_TASKS.items():
        co = last_closed_open(now, cfg["sec"], cfg["off"])
        tasks.append((name, "ema", name, cfg, co))
    for bar, cfg in FVG.items():
        co = last_closed_open(now, cfg["sec"])
        tasks.append((f"FVG_{bar}", "fvg", bar, cfg, co))

    due = [t for t in tasks if state.get(t[0]) != t[4]]

    if manual:
        send("✅ Test: OKX tarayıcı botu GitHub Actions üzerinde çalışıyor.")
    if not due:
        print("Taranacak yeni mum yok.")
        return

    symbols = get_symbols()
    print(f"{len(symbols)} sembol, taranacak: {[t[0] for t in due]}")

    for key, kind, name, cfg, candle_open in due:
        late = now - (candle_open + cfg["sec"])             # mum kaç saniye önce kapandı
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
                    r = analyze_fvg(inst, cfg, candle_open)
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

        if stale > len(symbols) * 0.3:                      # OKX mumu henüz onaylamamış: kaydetme, tekrar dene
            print(f"{key}: OKX mumu henüz onaylamamış ({stale}/{len(symbols)}), sonraki çalışmada tekrar denenecek.")
            continue

        print(f"{key} tarandı, {len(hits)} sonuç.")
        sent_ok = True
        if hits:
            if kind == "brk":
                text = msg_breakout(name, hits)
            elif kind == "fvg":
                text = msg_fvg(name, hits)
            else:
                text = msg_ema(name, cfg, hits)
            head, _, rest = text.partition("\n")             # 2. satıra mum tarih/saat bilgisi ekle
            text = head + "\n" + candle_stamp(candle_open, cfg["sec"], late) + ("\n" + rest if rest else "")
            sent_ok = send(text)

        if sent_ok:                                      # mesaj gitmediyse bir sonraki çalışmada tekrar denenir
            state[key] = candle_open
            save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
