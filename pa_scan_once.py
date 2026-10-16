"""
OKX PA (price action) tarayıcı - GitHub Actions için tek seferlik sürüm

Mevcut okx_scan_once.py'den TAMAMEN BAĞIMSIZDIR: onu içe aktarmaz, onun durum dosyasını
(state.json) kullanmaz. Sadece aynı Telegram botuna (TG_TOKEN, TG_CHAT_ID) mesaj gönderir.

Strateji (sadece kripto USDT perpetual, long ve short):
  1) 4H yapı  : son iki tepe ve iki dip yükseliyorsa (HH-HL) sadece LONG,
                alçalıyorsa (LH-LL) sadece SHORT. Belirsizse işlem yok.
  2) 1H bölge : LONG için talep bölgesi (güçlü yükselişin başladığı dip) veya kırılan eski direnç;
                SHORT için arz bölgesi (güçlü düşüşün başladığı tepe) veya kırılan eski destek.
                Bölge oluştuktan sonra 1H kapanışla bozulmamış olmalı.
  3) 15m tetik: bölgeye temas eden mumda engulfing veya pin bar.
  4) Giriş tetik mumu kapanışı, stop bölgenin/fitilin ötesi, TP1 = 1R,
     TP2 = sıradaki 1H/4H seviye. TP2 en az 2R değilse sinyal verilmez.

Ortam değişkenleri:
  TG_TOKEN, TG_CHAT_ID : Telegram (mevcut botla aynı)
  TEST_RUN             : "true" ise elle çalıştırmada test mesajı gönderir
  PA_BACKTEST          : sayı verilirse son o kadar günü geçmişe dönük test eder,
                         MESAJ GÖNDERMEZ ve durum dosyasına yazmaz.
"""
import os
import sys
import json
import time
import statistics
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://www.okx.com"
STATE_FILE = "pa_state.json"          # mevcut botun state.json dosyasından ayrı

# ---------------- AYARLAR ----------------
MIN_24H_USDT = 5_000_000   # 24s hacmi bunun altındaki coinler taranmaz
MAX_SYMBOLS = 80           # hacme göre en fazla kaç coin taransın
PIVOT_K = 3                # tepe/dip: sağında ve solunda en az kaç mum daha düşük/yüksek olmalı
TREND_BARS = 120           # 4H yapıya bakılan mum sayısı (~20 gün)
ZONE_BARS = 200            # 1H bölge aranan mum sayısı (~8 gün)
ZONE_MIN_W = 0.25          # bölge en az (1H ort. mum boyu x bu) kalınlıkta
ZONE_MAX_W = 1.0           # bölge en fazla (1H ort. mum boyu x bu) kalınlıkta
IMPULSE_ATR = 1.5          # talep/arz bölgesinden sonra en az bu kadar 1H ort. mum boyu hareket
IMPULSE_BARS = 10          # bu hareket kaç 1H mum içinde olmalı
TRIG_MIN_RANGE = 0.6       # tetik mumu en az (15m ort. mum boyu x bu) boyunda
PIN_WICK = 2.0             # pin bar: fitil gövdenin en az bu katı
PIN_WICK_RANGE = 0.55      # pin bar: fitil mum boyunun en az bu oranı
PIN_CLOSE_POS = 0.6        # pin bar: kapanış mumun üst (short'ta alt) %40'ında
SL_BUFFER = 0.1            # stop tamponu: 1H ort. mum boyu x bu
MIN_STOP_PCT = 0.3         # stop mesafesi % en az (çok dar stop gürültüde patlar)
MAX_STOP_PCT = 5.0         # stop mesafesi % en fazla (3x-5x kaldıraçla anlamlı kalsın)
MIN_RR = 2.0               # TP2 en az kaç R olmalı
FUNDING_WARN = 0.0005      # |funding| bu değerin üstündeyse uyarı (%0,05)
RESEND_HOURS = 12          # aynı coin+yön+bölge için tekrar sinyal en erken kaç saat sonra
RISK_PCT = 1.0             # mesajdaki pozisyon büyüklüğü önerisi için işlem başı risk %
REQUEST_PAUSE = 0.1
SEC15 = 900
# -----------------------------------------

session = requests.Session()
TR = timezone(timedelta(hours=3))


# ---------------- OKX ----------------
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
    """Kripto USDT perpetual'lar (hisse/emtia/döviz TradFi kontratları hariç), hacme göre sıralı."""
    kripto = None
    try:
        data = api("/api/v5/public/instruments", {"instType": "SWAP"})
        kat = {d["instId"]: str(d.get("instCategory", "")) for d in data}
        if any(kat.values()):
            kripto = {k for k, v in kat.items() if v in ("", "1")}   # 1 = kripto
    except Exception as e:
        print("UYARI: kontrat kategorileri alınamadı:", e)
    rows = []
    for t in api("/api/v5/market/tickers", {"instType": "SWAP"}):
        inst = t["instId"]
        if not inst.endswith("-USDT-SWAP") or (kripto is not None and inst not in kripto):
            continue
        try:
            qv = float(t["volCcy24h"]) * float(t["last"])
        except (ValueError, KeyError):
            continue
        if qv >= MIN_24H_USDT:
            rows.append((inst, qv))
    rows.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in rows[:MAX_SYMBOLS]]


def to_series(rows, sec):
    return dict(t=[int(r[0]) // 1000 for r in rows], o=[float(r[1]) for r in rows],
                h=[float(r[2]) for r in rows], l=[float(r[3]) for r in rows],
                c=[float(r[4]) for r in rows], sec=sec)


def fetch(inst, bar, sec, n):
    """En az n kapanmış mum (eskiden yeniye)."""
    data = api("/api/v5/market/candles", {"instId": inst, "bar": bar, "limit": "300"})
    rows = [r for r in reversed(data) if r[8] == "1"]
    while len(rows) < n and rows:
        time.sleep(0.12)
        data = api("/api/v5/market/history-candles",
                   {"instId": inst, "bar": bar, "limit": "100", "after": rows[0][0]})
        older = [r for r in reversed(data) if r[8] == "1"]
        if not older:
            break
        rows = older + rows
    return to_series(rows, sec)


def upto(s, t_close, n):
    """t_close anına kadar kapanmış son n mum (dilim)."""
    j = len(s["t"])
    while j > 0 and s["t"][j - 1] + s["sec"] > t_close:
        j -= 1
    i = max(0, j - n)
    return {k: (v[i:j] if isinstance(v, list) else v) for k, v in s.items()}


# ---------------- Yardımcılar ----------------
def atr(s, n=14):
    h, l, c = s["h"], s["l"], s["c"]
    if len(c) < n + 1:
        return None
    tr = [max(h[j] - l[j], abs(h[j] - c[j - 1]), abs(l[j] - c[j - 1])) for j in range(len(c) - n, len(c))]
    return sum(tr) / n


def pivots(s, k=PIVOT_K):
    """Onaylanmış tepe ve dipler: [(indeks, fiyat)]"""
    h, l = s["h"], s["l"]
    ph, pl = [], []
    for i in range(k, len(h) - k):
        if h[i] == max(h[i - k:i + k + 1]) and h[i] > max(h[i - k:i]):
            ph.append((i, h[i]))
        if l[i] == min(l[i - k:i + k + 1]) and l[i] < min(l[i - k:i]):
            pl.append((i, l[i]))
    return ph, pl


def trend_4h(s):
    """1 = yükselen yapı, -1 = alçalan yapı, 0 = belirsiz."""
    ph, pl = pivots(s)
    if len(ph) < 2 or len(pl) < 2:
        return 0
    (_, h1), (_, h2) = ph[-2], ph[-1]
    (_, l1), (_, l2) = pl[-2], pl[-1]
    c = s["c"][-1]
    if h2 > h1 and l2 > l1 and c > l2:
        return 1
    if h2 < h1 and l2 < l1 and c < h2:
        return -1
    return 0


def zones_1h(s, d):
    """d=1: talep bölgeleri (long), d=-1: arz bölgeleri (short). [(alt, ust, ad, anahtar)]"""
    a = atr(s)
    if not a:
        return []
    o, h, l, c, t = s["o"], s["h"], s["l"], s["c"], s["t"]
    n = len(c)
    ph, pl = pivots(s)
    out = []

    def clamp(lo, hi, anchor_low):
        if anchor_low:   # alt sabit, üst ayarlanır
            hi = min(max(hi, lo + ZONE_MIN_W * a), lo + ZONE_MAX_W * a)
        else:            # üst sabit, alt ayarlanır
            lo = max(min(lo, hi - ZONE_MIN_W * a), hi - ZONE_MAX_W * a)
        return lo, hi

    if d == 1:
        # Talep: dip mumu, ardından güçlü yükseliş, sonra hiçbir 1H kapanış bölge altına inmemiş
        for i, p in pl:
            lo, hi = clamp(l[i], min(o[i], c[i]), True)
            if max(h[i + 1:i + 1 + IMPULSE_BARS]) < hi + IMPULSE_ATR * a:
                continue
            if any(c[j] < lo for j in range(i + 1, n)):
                continue
            out.append((lo, hi, "talep bölgesi", f"D{t[i]}"))
        # Kırılan direnç -> destek
        for i, p in ph:
            br = next((j for j in range(i + 1, n) if c[j] > p), None)
            if br is None:
                continue
            lo, hi = clamp(max(o[i], c[i]), p, False)
            if any(c[j] < lo for j in range(br + 1, n)):
                continue
            out.append((lo, hi, "kırılan direnç", f"F{t[i]}"))
    else:
        for i, p in ph:
            lo, hi = clamp(max(o[i], c[i]), h[i], False)
            if min(l[i + 1:i + 1 + IMPULSE_BARS]) > lo - IMPULSE_ATR * a:
                continue
            if any(c[j] > hi for j in range(i + 1, n)):
                continue
            out.append((lo, hi, "arz bölgesi", f"S{t[i]}"))
        for i, p in pl:
            br = next((j for j in range(i + 1, n) if c[j] < p), None)
            if br is None:
                continue
            lo, hi = clamp(p, min(o[i], c[i]), True)
            if any(c[j] > hi for j in range(br + 1, n)):
                continue
            out.append((lo, hi, "kırılan destek", f"F{t[i]}"))
    return out


def trigger_15m(s):
    """Son kapanmış 15m mumda tetik: (yön, ad, mum altı, mum üstü) veya None."""
    if len(s["c"]) < 20:
        return None
    o, h, l, c = s["o"], s["h"], s["l"], s["c"]
    L = len(c) - 1
    a = atr(s)
    rng = h[L] - l[L]
    if not a or rng <= 0 or rng < TRIG_MIN_RANGE * a:
        return None
    body = abs(c[L] - o[L])
    pbody = abs(c[L - 1] - o[L - 1])
    lo2, hi2 = min(l[L], l[L - 1]), max(h[L], h[L - 1])

    if (c[L] > o[L] and c[L - 1] < o[L - 1] and c[L] >= o[L - 1] and o[L] <= c[L - 1]
            and body >= pbody and body >= 0.5 * rng):
        return (1, "bullish engulfing", lo2, hi2)
    if (c[L] < o[L] and c[L - 1] > o[L - 1] and c[L] <= o[L - 1] and o[L] >= c[L - 1]
            and body >= pbody and body >= 0.5 * rng):
        return (-1, "bearish engulfing", lo2, hi2)
    alt_fitil = min(o[L], c[L]) - l[L]
    ust_fitil = h[L] - max(o[L], c[L])
    if (alt_fitil >= PIN_WICK * body and alt_fitil >= PIN_WICK_RANGE * rng
            and (c[L] - l[L]) >= PIN_CLOSE_POS * rng):
        return (1, "pin bar (alt fitil)", l[L], h[L])
    if (ust_fitil >= PIN_WICK * body and ust_fitil >= PIN_WICK_RANGE * rng
            and (h[L] - c[L]) >= PIN_CLOSE_POS * rng):
        return (-1, "pin bar (üst fitil)", l[L], h[L])
    return None


# ---------------- Strateji ----------------
def analyze(inst, s4, s1, s15, t_close):
    """t_close anında kapanan 15m mum için sinyal (yoksa None). Sadece o ana kadar kapanmış veriyi kullanır."""
    m15 = upto(s15, t_close, 40)
    if not m15["t"] or m15["t"][-1] + SEC15 != t_close:
        return None
    trg = trigger_15m(m15)
    if not trg:
        return None
    d, pat, plo, phi = trg

    h4 = upto(s4, t_close, TREND_BARS)
    if trend_4h(h4) != d:
        return None

    h1 = upto(s1, t_close, ZONE_BARS)
    a1 = atr(h1)
    if not a1:
        return None
    entry = m15["c"][-1]

    # Tetik mumunun dokunduğu, kapanışın bölgenin doğru tarafında kaldığı bölgeler
    cands = []
    for lo, hi, ad, key in zones_1h(h1, d):
        if d == 1 and plo <= hi and entry > lo:
            cands.append((lo, hi, ad, key))
        if d == -1 and phi >= lo and entry < hi:
            cands.append((lo, hi, ad, key))
    if not cands:
        return None
    # Fiyata en yakın bölge
    lo, hi, ad, key = (max(cands, key=lambda z: z[1]) if d == 1 else min(cands, key=lambda z: z[0]))

    if d == 1:
        sl = min(lo, plo) - SL_BUFFER * a1
        R = entry - sl
    else:
        sl = max(hi, phi) + SL_BUFFER * a1
        R = sl - entry
    if R <= 0:
        return None
    stop_pct = R / entry * 100
    if stop_pct < MIN_STOP_PCT or stop_pct > MAX_STOP_PCT:
        return None

    # TP2: sıradaki karşı seviye (1H ve 4H tepe/dipler)
    seviyeler = []
    for s in (h1, h4):
        ph, pl = pivots(s)
        seviyeler += [p for _, p in (ph if d == 1 else pl)]
    if d == 1:
        ileri = sorted(p for p in seviyeler if p > entry + 0.2 * R)
    else:
        ileri = sorted((p for p in seviyeler if p < entry - 0.2 * R), reverse=True)
    if ileri:
        tp2 = ileri[0]
        tp2_not = "sıradaki seviye"
    else:
        tp2 = entry + d * MIN_RR * R
        tp2_not = "seviye yok, 2R"
    rr2 = abs(tp2 - entry) / R
    if rr2 < MIN_RR:
        return None

    return dict(inst=inst, dir=d, pattern=pat, zone=(lo, hi), zone_name=ad, key=f"{inst}|{d}|{key}",
                entry=entry, sl=sl, tp1=entry + d * R, tp2=tp2, rr2=rr2, tp2_not=tp2_not,
                stop_pct=stop_pct, t=t_close)


# ---------------- Telegram / mesaj ----------------
def send(msg):
    print(msg + "\n", flush=True)
    token, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID")
    if not (token and chat):
        print("UYARI: TG_TOKEN veya TG_CHAT_ID tanımlı değil, Telegram'a mesaj gönderilmedi!")
        return False
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
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              data={"chat_id": chat, "text": ch}, timeout=10)
            if r.status_code != 200:
                print("Telegram hata:", r.status_code, r.text[:200])
                ok = False
        except Exception as e:
            print("Telegram hatası:", e)
            ok = False
    return ok


def fp(x):
    return f"{x:.6g}"


def short(inst):
    return inst.replace("-USDT-SWAP", "")


def fmt_signal(g):
    up = g["dir"] == 1
    lines = [
        f"{'🟢 LONG' if up else '🔴 SHORT'} {short(g['inst'])}  ({g['pattern']}, 1H {g['zone_name']} "
        f"{fp(g['zone'][0])}–{fp(g['zone'][1])})",
        f"   Giriş {fp(g['entry'])} | SL {fp(g['sl'])} ({'-' if up else '+'}{g['stop_pct']:.2f}%) | "
        f"TP1 {fp(g['tp1'])} (1R) | TP2 {fp(g['tp2'])} ({g['rr2']:.1f}R, {g['tp2_not']})",
        f"   4H trend {'yukarı' if up else 'aşağı'} | %{RISK_PCT:g} risk → pozisyon ≈ bakiye × "
        f"{RISK_PCT / g['stop_pct']:.2f}",
    ]
    fr = g.get("funding")
    if fr is not None and ((up and fr > FUNDING_WARN) or (not up and fr < -FUNDING_WARN)):
        lines.append(f"   ⚠️ funding {fr * 100:+.3f}% (bu yön kalabalık, temkinli ol)")
    return "\n".join(lines)


def funding(inst):
    try:
        return float(api("/api/v5/public/funding-rate", {"instId": inst})[0]["fundingRate"])
    except Exception:
        return None


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ---------------- Canlı tarama ----------------
def live():
    state = load_state()
    now = int(time.time())
    manual = (os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
              and os.getenv("TEST_RUN", "false").lower() == "true")
    if manual:
        send("✅ Test: OKX PA stratejisi botu GitHub Actions üzerinde çalışıyor.")

    candle_open = (now // SEC15) * SEC15 - SEC15
    t_close = candle_open + SEC15
    if state.get("last") == candle_open:
        print("Taranacak yeni 15m mum yok.")
        return
    if now - t_close > 1800:   # çok gecikmiş mum için sinyal verme
        print("Mum 30 dk'dan eski, taranmadan geçildi.")
        state["last"] = candle_open
        save_state(state)
        return
    wait = t_close + 10 - time.time()
    if wait > 0:
        time.sleep(wait)

    sent = {k: v for k, v in state.get("sent", {}).items() if now - v < 3 * 86400}
    symbols = get_symbols()
    print(f"{len(symbols)} sembol taranıyor.")
    hits, stale = [], 0
    for inst in symbols:
        try:
            s15 = fetch(inst, "15m", SEC15, 40)
            time.sleep(REQUEST_PAUSE)
            if not s15["t"] or s15["t"][-1] != candle_open:
                stale += 1
                continue
            if not trigger_15m(upto(s15, t_close, 40)):   # tetik yoksa diğer veriyi hiç çekme
                continue
            s4 = fetch(inst, "4H", 14400, TREND_BARS)
            time.sleep(REQUEST_PAUSE)
            s1 = fetch(inst, "1H", 3600, ZONE_BARS)
            time.sleep(REQUEST_PAUSE)
            g = analyze(inst, s4, s1, s15, t_close)
        except Exception as e:
            print(f"{inst} hata: {e}")
            time.sleep(1)
            continue
        if g and now - sent.get(g["key"], 0) >= RESEND_HOURS * 3600:
            g["funding"] = funding(inst)
            hits.append(g)

    if stale > len(symbols) * 0.3:
        print(f"OKX mumu henüz onaylamamış ({stale}/{len(symbols)}), sonraki çalışmada tekrar denenecek.")
        return

    ok = True
    if hits:
        a = datetime.fromtimestamp(candle_open, TR)
        b = datetime.fromtimestamp(t_close, TR)
        msg = [f"🎯 [PA 15m] {len(hits)} sinyal", f"🕒 Mum (TR saati): {a:%d.%m.%Y %H:%M} → {b:%H:%M}"]
        msg += [fmt_signal(g) for g in hits]
        msg.append("ℹ️ Otomatik sinyal, yatırım tavsiyesi değildir.")
        ok = send("\n".join(msg))
        if ok:
            for g in hits:
                sent[g["key"]] = now
    print(f"Tarandı, {len(hits)} sinyal.")
    if ok:
        state["last"] = candle_open
        state["sent"] = sent
        save_state(state)


# ---------------- Geçmişe dönük test (mesaj göndermez) ----------------
def simulate(g, s15):
    """TP1'de yarısı kapanır ve stop girişe çekilir. Sonuç R cinsinden."""
    d, e, sl, tp1, tp2 = g["dir"], g["entry"], g["sl"], g["tp1"], g["tp2"]
    R = abs(e - sl)
    half = False
    start = s15["t"].index(g["t"] - SEC15) + 1 if (g["t"] - SEC15) in s15["t"] else len(s15["t"])
    for j in range(start, len(s15["t"])):
        lo, hi = s15["l"][j], s15["h"][j]
        adv = lo if d == 1 else hi       # aleyhe uç
        fav = hi if d == 1 else lo       # lehe uç
        if not half:
            if (adv - sl) * d <= 0:
                return -1.0, "stop"
            if (fav - tp1) * d >= 0:
                half = True
                if (fav - tp2) * d >= 0:
                    return 0.5 + 0.5 * g["rr2"], "TP2"
                continue
        else:
            if (adv - e) * d <= 0:
                return 0.5, "TP1 + başabaş"
            if (fav - tp2) * d >= 0:
                return 0.5 + 0.5 * g["rr2"], "TP2"
    last = s15["c"][-1]
    acik = (last - e) * d / R
    return (0.5 + 0.5 * acik if half else acik), "açık"


def backtest(days):
    days = max(1, min(days, 6))
    now = int(time.time())
    end_open = (now // SEC15) * SEC15 - SEC15
    n15 = days * 96
    symbols = get_symbols()
    print(f"Geçmiş test: son {days} gün, {len(symbols)} sembol. (Mesaj gönderilmez.)", flush=True)
    sigs = []
    for inst in symbols:
        try:
            s15 = fetch(inst, "15m", SEC15, n15 + 60)
            s4 = fetch(inst, "4H", 14400, TREND_BARS + days * 6 + 10)
            s1 = fetch(inst, "1H", 3600, ZONE_BARS + days * 24 + 10)
        except Exception as e:
            print(f"{inst} hata: {e}")
            continue
        last_sent = {}
        for co in range(end_open - (n15 - 1) * SEC15, end_open + 1, SEC15):
            t_close = co + SEC15
            try:
                g = analyze(inst, s4, s1, s15, t_close)
            except Exception as e:
                print(f"{inst} analiz hatası: {e}")
                break
            if g and t_close - last_sent.get(g["key"], 0) >= RESEND_HOURS * 3600:
                last_sent[g["key"]] = t_close
                g["R"], g["sonuc"] = simulate(g, s15)
                sigs.append(g)
        time.sleep(REQUEST_PAUSE)

    sigs.sort(key=lambda g: g["t"])
    for g in sigs:
        ts = datetime.fromtimestamp(g["t"], TR)
        print(f"{ts:%d.%m %H:%M}  {'LONG ' if g['dir'] == 1 else 'SHORT'} {short(g['inst']):<10} "
              f"{g['pattern']:<20} {g['zone_name']:<15} stop %{g['stop_pct']:.2f}  TP2 {g['rr2']:.1f}R  "
              f"-> {g['sonuc']:<14} {g['R']:+.2f}R")
    kapali = [g for g in sigs if g["sonuc"] != "açık"]
    toplam = sum(g["R"] for g in sigs)
    stop = sum(1 for g in kapali if g["sonuc"] == "stop")
    ozet = (f"PA geçmiş test ({days} gün, {len(symbols)} coin): {len(sigs)} sinyal "
            f"(long {sum(1 for g in sigs if g['dir'] == 1)}, short {sum(1 for g in sigs if g['dir'] == -1)}), "
            f"kapanan {len(kapali)}: stop {stop}, TP1+ {len(kapali) - stop}; "
            f"toplam {toplam:+.1f}R, sinyal başı {toplam / len(sigs) if sigs else 0:+.2f}R")
    print("::notice::" + ozet)
    print(ozet)


if __name__ == "__main__":
    try:
        bt = os.getenv("PA_BACKTEST", "").strip()
        if bt:
            backtest(int(bt))
        else:
            live()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
