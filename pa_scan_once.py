"""
OKX PA tarayıcı: GÜNLÜK YAPI KIRILIMI + RETEST + RED (GitHub Actions için tek seferlik sürüm)

Mevcut okx_scan_once.py'den TAMAMEN BAĞIMSIZDIR: onu içe aktarmaz, onun durum dosyasını
(state.json) kullanmaz. Sadece aynı Telegram botuna (TG_TOKEN, TG_CHAT_ID) mesaj gönderir.

Strateji (sadece kripto USDT perpetual):
  SHORT
    1) Günlükte yükselen yapı: son tepe bir öncekinden yüksek, o tepeyi oluşturan dip de
       bir önceki dipten yüksek (HH-HL).
    2) Son tepeyi oluşturan dip (seviye), günlük KAPANIŞLA aşağı kırılır.
    3) Fiyat seviyeden uzaklaşır (en az yarım günlük ort. mum boyu), sonra seviyeye geri gelir.
    4) Red mumu (REJECT_TF): seviyeye değer, seviyenin altında, mumun alt yarısında kapanır,
       belirgin üst fitil bırakır. Giriş bu mumun kapanışı.
    Kurulum iptal: kırılımdan sonra günlük kapanış seviyenin üstünde olursa ya da
    RETEST_DAYS gün içinde retest gelmezse.
  LONG: tam tersi (düşen yapı, son dibi oluşturan tepe kapanışla yukarı kırılır, retest, red).

  Stop: red mumunun fitili ötesi. TP1 = 1R. TP2 = sıradaki günlük yapı seviyesi (en az 2R).
  Her kurulum için sadece ilk red sinyali gönderilir.

Ortam değişkenleri:
  TG_TOKEN, TG_CHAT_ID : Telegram (mevcut botla aynı)
  TEST_RUN             : "true" ise elle çalıştırmada test mesajı gönderir
  PA_BACKTEST          : gün sayısı verilirse geçmişe dönük test yapar; MESAJ GÖNDERMEZ,
                         durum dosyasına yazmaz.
"""
import os
import sys
import json
import time
import bisect
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://www.okx.com"
STATE_FILE = "pa_state.json"          # mevcut botun state.json dosyasından ayrı

# ---------------- AYARLAR ----------------
REJECT_TF = "4H"           # red mumunun zaman dilimi: "1H", "4H" veya "1D"
MIN_24H_USDT = 5_000_000   # 24s hacmi bunun altındaki coinler taranmaz
MAX_SYMBOLS = 80           # hacme göre en fazla kaç coin taransın
DAILY_K = 3                # günlük tepe/dip: sağında ve solunda en az kaç gün daha düşük/yüksek
STRUCT_DAYS = 150          # yapı için bakılan gün sayısı
TOP_MAX_AGE = 60           # kırılan yapının son tepesi/dibi en fazla kaç günlük olabilir
RETEST_DAYS = 20           # kırılımdan sonra retest için beklenecek en fazla gün
MIN_AWAY = 0.5             # retestten önce seviyeden en az (günlük ort. mum boyu x bu) uzaklaşma
TOUCH_TOL = 0.25           # seviyeye "değme" toleransı: günlük ort. mum boyu x bu
MAX_PIERCE = 0.5           # red mumu seviyeyi en fazla (günlük ort. mum boyu x bu) aşabilir
WICK_MIN = 0.3             # red mumunda ret yönündeki fitil, mum boyunun en az bu oranı
CLOSE_HALF = 0.5           # kapanış mumun alt (long'da üst) yarısında
MIN_RANGE = 0.5            # red mumu en az (kendi zaman diliminin ort. mum boyu x bu) boyunda
SL_BUFFER = 0.1            # stop tamponu: red zaman diliminin ort. mum boyu x bu
MIN_STOP_PCT = 0.3
MAX_STOP_PCT = 8.0
MIN_RR = 2.0               # TP2 en az kaç R
FUNDING_WARN = 0.0005      # |funding| bu değerin üstündeyse uyarı (%0,05)
RISK_PCT = 1.0             # mesajdaki pozisyon büyüklüğü önerisi için işlem başı risk %
REQUEST_PAUSE = 0.1
# -----------------------------------------

TF = {"1H": ("1H", 3600), "4H": ("4H", 14400), "1D": ("1Dutc", 86400)}
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
                c=[float(r[4]) for r in rows], sec=sec)


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
    out = dict(t=[], o=[], h=[], l=[], c=[], sec=sec)
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


def setups_at(d, D, datr):
    """D gününe kadar (D dahil) kapanmış günlük veriyle aktif kurulumlar."""
    if D < 40 or datr[D] is None:
        return [], [], []
    h, l, c, t = d["h"], d["l"], d["c"], d["t"]
    a = datr[D]
    start = max(0, D - STRUCT_DAYS)
    ph, pl = pivots(h, l, start, D, DAILY_K)
    out = []

    # SHORT: yükselen yapıda son tepeyi oluşturan dip kapanışla kırıldı
    for x, (ih, H) in enumerate(ph):
        if D - ih > TOP_MAX_AGE or x == 0:
            continue
        H0 = ph[x - 1][1]
        lows = [p for p in pl if p[0] < ih]
        if len(lows) < 2 or lows[-1][0] < ph[x - 1][0]:
            continue
        (iv, Lv), (_, L0) = lows[-1], lows[-2]
        if not (H > H0 and Lv > L0):
            continue
        b = None
        for j in range(ih + 1, D + 1):
            if c[j] < Lv:
                b = j
                break
            if h[j] > H:
                break
        if b is None or D - b > RETEST_DAYS:
            continue
        if any(c[j] > Lv for j in range(b + 1, D + 1)):
            continue
        if min(l[b:D + 1]) > Lv - MIN_AWAY * a:
            continue
        out.append(dict(dir=-1, level=Lv, key=f"-1|{t[iv]}", brk=t[b], atr=a))

    # LONG: düşen yapıda son dibi oluşturan tepe kapanışla kırıldı
    for x, (il, Lo) in enumerate(pl):
        if D - il > TOP_MAX_AGE or x == 0:
            continue
        L0 = pl[x - 1][1]
        highs = [p for p in ph if p[0] < il]
        if len(highs) < 2 or highs[-1][0] < pl[x - 1][0]:
            continue
        (iv, Hv), (_, H0) = highs[-1], highs[-2]
        if not (Lo < L0 and Hv < H0):
            continue
        b = None
        for j in range(il + 1, D + 1):
            if c[j] > Hv:
                b = j
                break
            if l[j] < Lo:
                break
        if b is None or D - b > RETEST_DAYS:
            continue
        if any(c[j] < Hv for j in range(b + 1, D + 1)):
            continue
        if max(h[b:D + 1]) < Hv + MIN_AWAY * a:
            continue
        out.append(dict(dir=1, level=Hv, key=f"1|{t[iv]}", brk=t[b], atr=a))

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
        tp2, tp2_not = ileri[0], "sıradaki günlük seviye"
    else:
        tp2, tp2_not = c + d * MIN_RR * R, "seviye yok, 2R"
    rr2 = abs(tp2 - c) / R
    if rr2 < MIN_RR:
        return None
    return dict(dir=d, level=L, brk=st["brk"], key=st["key"], entry=c, sl=sl, tp1=c + d * R,
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
        f"{'🟢 LONG' if up else '🔴 SHORT'} {short(g['inst'])}  günlük yapı {'yukarı' if up else 'aşağı'} "
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
    """t_open anına kadar kapanmış son günün indeksi."""
    return bisect.bisect_right(d["t"], t_open - DAY) - 1


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
            d = fetch(inst, "1Dutc", DAY, 300)
            time.sleep(REQUEST_PAUSE)
            datr = atr_arr(d)
            D = last_day_before(d, co)
            sts, highs, lows = setups_at(d, D, datr)
            sts = [s for s in sts if f"{inst}|{s['key']}" not in sent]
            if not sts:
                continue
            x = d if REJECT_TF == "1D" else fetch(inst, bar, sec, 40)
            if REJECT_TF != "1D":
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
        msg = [f"🎯 [Kırılım-Retest {REJECT_TF}] {len(hits)} sinyal",
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


# ---------------- Geçmişe dönük test (mesaj göndermez) ----------------
def simulate(g, s1h):
    """1H mumlarla: TP1'de yarısı kapanır ve stop girişe çekilir. Sonuç R cinsinden."""
    d, e, sl, tp1, tp2 = g["dir"], g["entry"], g["sl"], g["tp1"], g["tp2"]
    R = abs(e - sl)
    half = False
    start = bisect.bisect_left(s1h["t"], g["t"])
    for j in range(start, len(s1h["t"])):
        adv = s1h["l"][j] if d == 1 else s1h["h"][j]
        fav = s1h["h"][j] if d == 1 else s1h["l"][j]
        if not half:
            if (adv - sl) * d <= 0:
                return -1.0, "stop"
            if (fav - tp1) * d >= 0:
                half = True
                if (fav - tp2) * d >= 0:
                    return 0.5 + 0.5 * g["rr2"], "TP2"
        else:
            if (adv - e) * d <= 0:
                return 0.5, "TP1 + başabaş"
            if (fav - tp2) * d >= 0:
                return 0.5 + 0.5 * g["rr2"], "TP2"
    acik = (s1h["c"][-1] - e) * d / R if s1h["c"] else 0
    return (0.5 + 0.5 * acik if half else acik), "açık"


def run_bt(data, tf, t_from):
    sec = TF[tf][1]
    sigs = []
    for inst, (d, s1h) in data.items():
        datr = atr_arr(d)
        x = d if tf == "1D" else (s1h if tf == "1H" else aggregate(s1h, 14400))
        xatr = atr_arr(x)
        used, cache = set(), {}
        for j in range(len(x["t"])):
            if x["t"][j] < t_from:
                continue
            D = last_day_before(d, x["t"][j])
            if D not in cache:
                cache[D] = setups_at(d, D, datr)
            sts, highs, lows = cache[D]
            for st in sts:
                if st["key"] in used:
                    continue
                g = check_reject(x, j, xatr, st, highs, lows)
                if g:
                    used.add(st["key"])
                    g["inst"] = inst
                    g["R"], g["sonuc"] = simulate(g, s1h)
                    sigs.append(g)
    sigs.sort(key=lambda g: g["t"])
    return sigs


def ozet(sigs):
    kapali = [g for g in sigs if g["sonuc"] != "açık"]
    stop = sum(1 for g in kapali if g["sonuc"] == "stop")
    toplam = sum(g["R"] for g in sigs)
    oran = (len(kapali) - stop) / len(kapali) * 100 if kapali else 0
    ort_stop = sum(g["stop_pct"] for g in sigs) / len(sigs) if sigs else 0
    return (f"{len(sigs)} sinyal (L{sum(1 for g in sigs if g['dir'] == 1)}/S{sum(1 for g in sigs if g['dir'] == -1)}), "
            f"TP1+ oranı %{oran:.0f}, toplam {toplam:+.1f}R, sinyal başı "
            f"{toplam / len(sigs) if sigs else 0:+.2f}R, ort. stop %{ort_stop:.1f}")


def backtest(days):
    days = max(7, min(days, 150))
    now = int(time.time())
    t_from = now - days * DAY
    symbols = get_symbols()
    print(f"Geçmiş test: son {days} gün, {len(symbols)} sembol. (Mesaj gönderilmez.)", flush=True)
    data = {}
    for inst in symbols:
        try:
            data[inst] = (fetch(inst, "1Dutc", DAY, days + STRUCT_DAYS + 20),
                          fetch(inst, "1H", 3600, days * 24 + 48))
        except Exception as e:
            print(f"{inst} hata: {e}")
        time.sleep(REQUEST_PAUSE)

    for tf in ("1H", "4H", "1D"):
        sigs = run_bt(data, tf, t_from)
        print(f"\n===== red {tf} =====")
        for g in sigs:
            ts = datetime.fromtimestamp(g["t"], TR)
            print(f"{ts:%d.%m.%y %H:%M}  {'LONG ' if g['dir'] == 1 else 'SHORT'} {short(g['inst']):<10} "
                  f"seviye {fp(g['level']):<10} stop %{g['stop_pct']:.2f}  TP2 {g['rr2']:.1f}R  "
                  f"-> {g['sonuc']:<14} {g['R']:+.2f}R")
        print(f"::notice::[{days} gün, {len(data)} coin] red {tf}: {ozet(sigs)}")


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
