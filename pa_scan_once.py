"""
OKX PA tarayıcı: GÜNLÜK YAPI KIRILIMI + RETEST + RED (GitHub Actions için tek seferlik sürüm)

Mevcut okx_scan_once.py'den TAMAMEN BAĞIMSIZDIR: onu içe aktarmaz, onun durum dosyasını
(state.json) kullanmaz. Sadece aynı Telegram botuna (TG_TOKEN, TG_CHAT_ID) mesaj gönderir.

Strateji (sadece kripto USDT perpetual):
  SHORT
    1) Yükselen yapı: son tepe bir öncekinden yüksek (ör. tepeler 8 -> 10).
    2) Bir önceki tepe (8, seviye) KAPANIŞLA aşağı kırılır.
    3) Fiyat seviyeden uzaklaşır (en az yarım günlük ort. mum boyu), sonra seviyeye geri gelir.
    4) Red mumu (REJECT_TF): seviyeye değer, seviyenin altında, mumun alt yarısında kapanır,
       belirgin üst fitil bırakır. Giriş bu mumun kapanışı.
    Kurulum iptal: kırılımdan sonra günlük kapanış seviyenin üstünde olursa ya da
    RETEST_DAYS gün içinde retest gelmezse.
  LONG: tam tersi (dipler 7 -> 5 ise 7 kapanışla yukarı kırılır, 7'ye retest, red).

  Stop: red mumunun fitili ötesi. TP1 = 1R. TP2 = sıradaki günlük yapı seviyesi (en az 2R).
  Her kurulum için sadece ilk red sinyali gönderilir.

Ortam değişkenleri:
  TG_TOKEN, TG_CHAT_ID : Telegram (mevcut botla aynı)
  TEST_RUN             : "true" ise elle çalıştırmada test mesajı gönderir
  Geçmişe dönük test için pa_backtest.py kullanılır (mesaj göndermez).
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
STATE_FILE = "pa_state.json"          # mevcut botun state.json dosyasından ayrı

# ---------------- AYARLAR ----------------
STRUCT_TF = "1D"           # yapı ve kırılım zaman dilimi: "1D" veya "4H"
REJECT_TF = "1H"           # red mumunun zaman dilimi: "1H", "4H" veya "1D"
MIN_24H_USDT = 5_000_000   # 24s hacmi bunun altındaki coinler taranmaz
MAX_SYMBOLS = 80           # hacme göre en fazla kaç coin taransın
DAILY_K = 3                # günlük tepe/dip: sağında ve solunda en az kaç gün daha düşük/yüksek
STRUCT_DAYS = 150          # yapı için bakılan gün sayısı
TOP_MAX_AGE = 60           # kırılan yapının son tepesi/dibi en fazla kaç günlük olabilir
RETEST_DAYS = 20           # kırılımdan sonra retest için beklenecek en fazla gün
MIN_AWAY = 0.5             # retestten önce seviyeden en az (günlük ort. mum boyu x bu) uzaklaşma
TOUCH_TOL = 0.15           # seviyeye "değme" toleransı: günlük ort. mum boyu x bu
MAX_PIERCE = 0.5           # red mumu seviyeyi en fazla (günlük ort. mum boyu x bu) aşabilir
WICK_MIN = 0.3             # red mumunda ret yönündeki fitil, mum boyunun en az bu oranı
CLOSE_HALF = 0.5           # kapanış mumun alt (long'da üst) yarısında
MIN_RANGE = 0.5            # red mumu en az (kendi zaman diliminin ort. mum boyu x bu) boyunda
SL_BUFFER = 0.1            # stop tamponu: red zaman diliminin ort. mum boyu x bu
MIN_STOP_PCT = 0.3
MAX_STOP_PCT = 8.0
VOL_MULT = 0.0             # >0 ise kırılım mumu hacmi, önceki 20 mumun ortancasının en az bu katı
BTC_FILTER = False         # True ise long sadece BTC 4H EMA50 üstündeyken, short sadece altındayken
LEVEL_MODE = "onceki_tepe" # "onceki_tepe" (8->10 ise 8) | "son_dip" (10'u oluşturan dip) | "birlesik"
ENTRY_MODE = "piyasa"      # "piyasa": red mumu kapanışı | "limit_kapanis" | "limit_yari": fitil ortası | "limit_seviye"
FILL_BARS = 4              # limit emir en fazla kaç red mumu bekler (dolmazsa iptal)
MIN_RR = 2.0               # TP2 en az kaç R
FUNDING_WARN = 0.0005      # |funding| bu değerin üstündeyse uyarı (%0,05)
RISK_PCT = 1.0             # mesajdaki pozisyon büyüklüğü önerisi için işlem başı risk %
REQUEST_PAUSE = 0.1
# -----------------------------------------

TF = {"15m": ("15m", 900), "30m": ("30m", 1800), "1H": ("1H", 3600), "4H": ("4H", 14400),
      "6H": ("6Hutc", 21600), "8H": (None, 28800), "1D": ("1Dutc", 86400)}   # 8H OKX'te yok, 1H'den üretilir
# Yapı zaman dilimine göre ayarlar (mum sayısı olarak):
#   k: tepe/dip onayı, look: bakılan mum, top_age: kırılan yapı en fazla kaç mum önce, retest: kırılımdan sonra bekleme
STRUCT = {
    "1D": dict(k=DAILY_K, look=STRUCT_DAYS, top_age=TOP_MAX_AGE, retest=RETEST_DAYS, ad="günlük"),
    "8H": dict(k=3, look=180, top_age=45, retest=15, ad="8H"),
    "6H": dict(k=3, look=180, top_age=60, retest=20, ad="6H"),
    "4H": dict(k=3, look=180, top_age=90, retest=30, ad="4H"),
}
DAY = 86400
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
                c=[float(r[4]) for r in rows], v=[float(r[7]) for r in rows], sec=sec)


def fetch(inst, bar, sec, n):
    """En az n kapanmış mum (eskiden yeniye)."""
    data = api("/api/v5/market/candles", {"instId": inst, "bar": bar, "limit": str(min(max(n, 20), 300))})
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


def aggregate(s, sec):
    """Küçük zaman dilimi mumlarından büyük mum (sadece tam dolanlar)."""
    out = dict(t=[], o=[], h=[], l=[], c=[], v=[], sec=sec)
    hv = "v" in s
    need = sec // s["sec"]
    i, n = 0, len(s["t"])
    while i < n:
        b = s["t"][i] // sec * sec
        j = i
        while j < n and s["t"][j] // sec * sec == b:
            j += 1
        if j - i == need:
            out["t"].append(b)
            out["o"].append(s["o"][i])
            out["h"].append(max(s["h"][i:j]))
            out["l"].append(min(s["l"][i:j]))
            out["c"].append(s["c"][j - 1])
            out["v"].append(sum(s["v"][i:j]) if hv else 0.0)
        i = j
    return out


# ---------------- Yardımcılar ----------------
def atr_arr(s, n=14):
    h, l, c = s["h"], s["l"], s["c"]
    out = [None] * len(c)
    tr = [h[0] - l[0] if c else 0] + [max(h[j] - l[j], abs(h[j] - c[j - 1]), abs(l[j] - c[j - 1]))
                                      for j in range(1, len(c))]
    run = 0.0
    for j in range(len(c)):
        run += tr[j]
        if j >= n:
            run -= tr[j - n]
        if j >= n:
            out[j] = run / n
    return out


def pivots(h, l, a, b, k):
    """[a, b] aralığında onaylanmış tepe ve dipler (b dahil veriyle): [(indeks, fiyat)]"""
    ph, pl = [], []
    for i in range(a + k, b - k + 1):
        if h[i] == max(h[i - k:i + k + 1]) and h[i] > max(h[i - k:i]):
            ph.append((i, h[i]))
        if l[i] == min(l[i - k:i + k + 1]) and l[i] < min(l[i - k:i]):
            pl.append((i, l[i]))
    return ph, pl


def rsi_arr(c, n=14):
    """Wilder RSI."""
    out = [None] * len(c)
    if len(c) <= n:
        return out
    g = [max(c[i] - c[i - 1], 0) for i in range(1, len(c))]
    ls = [max(c[i - 1] - c[i], 0) for i in range(1, len(c))]
    ag, al = sum(g[:n]) / n, sum(ls[:n]) / n
    for i in range(n, len(c)):
        if i > n:
            ag = (ag * (n - 1) + g[i - 1]) / n
            al = (al * (n - 1) + ls[i - 1]) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def vol_ratio(d, b):
    """Kırılım mumu hacmi / önceki 20 mumun ortancası (hesaplanamazsa None)."""
    if not d.get("v"):
        return None
    prev = d["v"][max(0, b - 20):b]
    if len(prev) < 5:
        return None
    med = statistics.median(prev)
    return d["v"][b] / med if med > 0 else None


def vol_ok(d, b):
    """Kırılım mumu hacmi, önceki 20 mumun ortancasının en az VOL_MULT katı mı?"""
    if VOL_MULT <= 0:
        return True
    r = vol_ratio(d, b)
    return r is None or r >= VOL_MULT


def setups_at(d, D, datr, piv=None):
    """D mumuna kadar (D dahil) kapanmış yapı verisiyle aktif kurulumlar.
    piv: tüm seri için önceden hesaplanmış pivots(h, l, 0, len-1, k) (geçmiş testte hız için)."""
    cfg = STRUCT[STRUCT_TF]
    if D < 40 or datr[D] is None:
        return [], [], []
    h, l, c, t = d["h"], d["l"], d["c"], d["t"]
    a = datr[D]
    start = max(0, D - cfg["look"])
    if piv is None:
        ph, pl = pivots(h, l, start, D, cfg["k"])
    else:
        lo_i, hi_i = start + cfg["k"], D - cfg["k"]
        ph = [p for p in piv[0] if lo_i <= p[0] <= hi_i]
        pl = [p for p in piv[1] if lo_i <= p[0] <= hi_i]
    out = []

    rsi = d.get("_rsi")
    if rsi is None or len(rsi) != len(c):
        rsi = rsi_arr(c)
        d["_rsi"] = rsi
    o = d["o"]
    v = d.get("v") or []

    # Seviye tanımı (LEVEL_MODE), short için (long tam tersi):
    #   "onceki_tepe": bir önceki tepe (tepeler 8 -> 10 ise 8) kapanışla kırılır
    #   "son_dip"    : son tepeyi oluşturan dip (6 -> 8 -> 7 -> 10 ise 7) kapanışla kırılır
    #   "birlesik"   : seviye önceki tepe (8), ama 7 de kapanışla kırılmış olmalı (trend dönüşü teyidi)
    for d_ in (-1, 1):
        tops = ph if d_ == -1 else pl          # short: tepeler, long: dipler
        bots = pl if d_ == -1 else ph
        for x, (ie, E) in enumerate(tops):
            if D - ie > cfg["top_age"] or x == 0:
                continue
            i0, E0 = tops[x - 1]
            if not (E - E0) * -d_ > 0:         # short: E > E0 (yükselen tepe), long: E < E0 (alçalan dip)
                continue
            ara = [q for q in bots if i0 < q[0] < ie]
            if LEVEL_MODE == "son_dip":
                once = [q for q in bots if q[0] < ie]
                if len(once) < 2 or once[-1][0] < i0:
                    continue
                (iv, lvl), (_, B0) = once[-1], once[-2]
                if not (lvl - B0) * -d_ > 0:
                    continue
            else:
                iv, lvl = i0, E0
            b = None
            for jj in range(ie + 1, D + 1):
                if (c[jj] - lvl) * d_ > 0:      # short: kapanış seviyenin altında
                    b = jj
                    break
                if (h[jj] if d_ == -1 else l[jj]) * -d_ > E * -d_:   # önce yeni tepe/dip gelirse geçersiz
                    break
            if b is None:
                continue
            kb = b                              # retest süresi bu mumdan itibaren sayılır
            if LEVEL_MODE == "birlesik":
                Bv = ara[-1][1] if ara else (min(l[i0:ie + 1]) if d_ == -1 else max(h[i0:ie + 1]))
                kb = next((jj for jj in range(ie + 1, D + 1) if (c[jj] - Bv) * d_ > 0), None)
                if kb is None:
                    continue
                kb = max(kb, b)
            if D - kb > cfg["retest"]:
                continue
            if any((c[jj] - lvl) * d_ < 0 for jj in range(b + 1, D + 1)):
                continue
            uz = min(l[b:D + 1]) if d_ == -1 else max(h[b:D + 1])
            if (lvl - uz) * -d_ < MIN_AWAY * a:
                continue
            if not vol_ok(d, b):
                continue
            # Teyit bilgileri (geçmiş testte filtre olarak denenir)
            rngb = h[b] - l[b]
            ab = datr[b] or a
            guclu = (rngb > 0 and abs(c[b] - o[b]) >= ab and
                     ((c[b] - l[b]) if d_ == -1 else (h[b] - c[b])) <= 0.3 * rngb and (c[b] - o[b]) * d_ > 0)
            rsi_div = (rsi[ie] is not None and rsi[i0] is not None and (rsi[ie] - rsi[i0]) * d_ > 0)
            onceki = [q for q in tops if q[0] < ie and (E - q[1]) * -d_ > 0 and ie - q[0] <= cfg["look"]]
            supurme = any((c[ie] - q[1]) * d_ > 0 for q in onceki)
            out.append(dict(dir=d_, level=lvl, key=f"{d_}|{t[iv]}|{t[ie]}", brk=t[b], atr=a,
                            E=E, brk_ext=(h[b] if d_ == -1 else l[b]),
                            volr=vol_ratio(d, b), brk_vol=(v[b] if v else None),
                            flags=dict(guclu=guclu, rsi=rsi_div, supurme=supurme)))

    return out, [p for _, p in ph], [p for _, p in pl]


def check_reject(x, j, xatr, st, highs, lows):
    """x serisinin j mumu, kurulum st için red mumu mu? Sinyal sözlüğü veya None."""
    o, h, l, c = x["o"][j], x["h"][j], x["l"][j], x["c"][j]
    rng = h - l
    ax = xatr[j]
    if not ax or rng <= 0 or rng < MIN_RANGE * ax:
        return None
    L, a, d = st["level"], st["atr"], st["dir"]
    if d == -1:
        ok = (h >= L - TOUCH_TOL * a and h <= L + MAX_PIERCE * a and c < L and
              h - max(o, c) >= WICK_MIN * rng and (c - l) <= CLOSE_HALF * rng)
        sl = h + SL_BUFFER * ax
    else:
        ok = (l <= L + TOUCH_TOL * a and l >= L - MAX_PIERCE * a and c > L and
              min(o, c) - l >= WICK_MIN * rng and (h - c) <= CLOSE_HALF * rng)
        sl = l - SL_BUFFER * ax
    if not ok:
        return None
    R = (c - sl) * d
    if R <= 0:
        return None
    stop_pct = R / c * 100
    if stop_pct < MIN_STOP_PCT or stop_pct > MAX_STOP_PCT:
        return None
    if d == 1:
        ileri = sorted(p for p in highs if p > c + 0.2 * R)
    else:
        ileri = sorted((p for p in lows if p < c - 0.2 * R), reverse=True)
    if ileri:
        tp2, tp2_not = ileri[0], "sıradaki yapı seviyesi"
    else:
        tp2, tp2_not = c + d * MIN_RR * R, "seviye yok, 2R"
    rr2 = abs(tp2 - c) / R
    if rr2 < MIN_RR:
        return None
    if d == 1:
        hedefler = sorted(p for p in highs if p > c)
    else:
        hedefler = sorted((p for p in lows if p < c), reverse=True)
    return dict(dir=d, level=L, brk=st["brk"], key=st["key"], entry=c, ext=(h if d == -1 else l),
                volr=st.get("volr"), brk_vol=st.get("brk_vol"), flags=st.get("flags", {}), targets=hedefler, sl=sl, tp1=c + d * R,
                tp2=tp2, rr2=rr2, tp2_not=tp2_not, stop_pct=stop_pct, t=x["t"][j] + x["sec"])


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
    kir = datetime.fromtimestamp(g["brk"], TR).strftime("%d.%m")
    lines = [
        f"{'🟢 LONG' if up else '🔴 SHORT'} {short(g['inst'])}  {STRUCT[STRUCT_TF]['ad']} yapı {'yukarı' if up else 'aşağı'} "
        f"kırıldı ({kir}), seviye {fp(g['level'])} retestten {REJECT_TF} red",
        f"   Giriş {fp(g['entry'])} | SL {fp(g['sl'])} ({'-' if up else '+'}{g['stop_pct']:.2f}%) | "
        f"TP1 {fp(g['tp1'])} (1R) | TP2 {fp(g['tp2'])} ({g['rr2']:.1f}R, {g['tp2_not']})",
        f"   %{RISK_PCT:g} risk → pozisyon ≈ bakiye × {RISK_PCT / g['stop_pct']:.2f}",
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


def last_day_before(d, t_open):
    """t_open anına kadar kapanmış son yapı mumunun indeksi."""
    return bisect.bisect_right(d["t"], t_open - d["sec"]) - 1


# ---------------- Canlı tarama ----------------
def live():
    state = load_state()
    now = int(time.time())
    manual = (os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
              and os.getenv("TEST_RUN", "false").lower() == "true")
    if manual:
        send("✅ Test: OKX kırılım-retest (PA) botu GitHub Actions üzerinde çalışıyor.")

    bar, sec = TF[REJECT_TF]
    co = (now // sec) * sec - sec          # son kapanmış red mumunun açılışı (UTC hizalı)
    tc = co + sec
    if state.get("last") == co:
        print(f"Taranacak yeni {REJECT_TF} mum yok.")
        return
    if now - tc > max(1800, sec // 2):
        print("Mum çok eski, taranmadan geçildi.")
        state["last"] = co
        save_state(state)
        return
    wait = tc + 10 - time.time()
    if wait > 0:
        time.sleep(wait)

    sent = {k: v for k, v in state.get("sent", {}).items() if now - v < 45 * DAY}
    symbols = get_symbols()
    print(f"{len(symbols)} sembol taranıyor ({REJECT_TF} red).")
    hits, stale = [], 0
    for inst in symbols:
        try:
            d = fetch(inst, TF[STRUCT_TF][0], TF[STRUCT_TF][1], 300)
            time.sleep(REQUEST_PAUSE)
            datr = atr_arr(d)
            D = last_day_before(d, co)
            sts, highs, lows = setups_at(d, D, datr)
            sts = [s for s in sts if f"{inst}|{s['key']}" not in sent]
            if not sts:
                continue
            x = d if REJECT_TF == STRUCT_TF else fetch(inst, bar, sec, 40)
            if REJECT_TF != STRUCT_TF:
                time.sleep(REQUEST_PAUSE)
            if not x["t"] or x["t"][-1] != co:
                stale += 1
                continue
            xatr = atr_arr(x)
            for st in sts:
                g = check_reject(x, len(x["t"]) - 1, xatr, st, highs, lows)
                if g:
                    g["inst"] = inst
                    g["funding"] = funding(inst)
                    hits.append(g)
                    break
        except Exception as e:
            print(f"{inst} hata: {e}")
            time.sleep(1)

    if stale and stale > len(symbols) * 0.3:
        print(f"OKX mumu henüz onaylamamış ({stale}), sonraki çalışmada tekrar denenecek.")
        return

    ok = True
    if hits:
        a = datetime.fromtimestamp(co, TR)
        b = datetime.fromtimestamp(tc, TR)
        msg = [f"🎯 [Kırılım-Retest {STRUCT_TF}→{REJECT_TF}] {len(hits)} sinyal",
               f"🕒 Mum (TR saati): {a:%d.%m.%Y %H:%M} → {b:%d.%m %H:%M}"]
        msg += [fmt_signal(g) for g in hits]
        msg.append("ℹ️ Otomatik sinyal, yatırım tavsiyesi değildir.")
        ok = send("\n".join(msg))
        if ok:
            for g in hits:
                sent[f"{g['inst']}|{g['key']}"] = now
    print(f"Tarandı, {len(hits)} sinyal.")
    if ok:
        state["last"] = co
        state["sent"] = sent
        save_state(state)


if __name__ == "__main__":
    try:
        live()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
