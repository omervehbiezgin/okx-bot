"""
OKX perpetual PUMP / DUMP tarayıcı - GitHub Actions için tek seferlik sürüm (v2)

Alarm için ÜÇ şart birden gerekir:
  1) Hacim normalin çok üstünde (ratio ve robust z-score)
  2) Mumdaki fiyat değişimi yeterince büyük (pump veya dump)
  3) Mumun gerçek USDT hacmi yeterince büyük (küçük/ölü mumlar elenir)

Her zaman dilimi için TEK mesaj gönderilir, en güçlü hareketler üstte sıralanır.

Ortam değişkenleri: TG_TOKEN, TG_CHAT_ID
"""
import os
import sys
import json
import time
import statistics
import requests

BASE = "https://www.okx.com"
STATE_FILE = "state.json"

# ---------------- AYARLAR ----------------
TIMEFRAMES = {
    # OKX bar adı: ayarlar
    #   lookback : normal hacmi hesaplamak için geriye bakılan mum sayısı
    #   ratio    : hacim, normalin en az kaç katı olmalı
    #   z        : robust z-score eşiği
    #   change   : mumda en az % kaç fiyat değişimi (açılış -> kapanış)
    #   min_usdt : mumun en az kaç USDT hacmi olmalı
    #   sec      : mum süresi (saniye)
    "15m":   dict(lookback=96, ratio=5.0, z=6.0, change=2.0, min_usdt=500_000,    sec=900),
    "1H":    dict(lookback=72, ratio=4.0, z=5.0, change=3.0, min_usdt=1_500_000,  sec=3600),
    "4H":    dict(lookback=60, ratio=3.5, z=5.0, change=5.0, min_usdt=4_000_000,  sec=14400),
    "1Dutc": dict(lookback=30, ratio=3.0, z=4.0, change=8.0, min_usdt=15_000_000, sec=86400),
}
TOP_N = 100                      # hacme göre ilk N USDT perpetual
MIN_QUOTE_VOLUME = 10_000_000    # 24s USDT hacmi altı coinler elenir
MAX_ALERTS_PER_SCAN = 8          # bir taramada en fazla kaç hareket bildirilsin
REQUEST_PAUSE = 0.06
# -----------------------------------------

session = requests.Session()


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


def analyze(inst, bar, cfg):
    lookback = cfg["lookback"]
    data = api("/api/v5/market/candles",
               {"instId": inst, "bar": bar, "limit": str(lookback + 2)})
    rows = [r for r in reversed(data) if r[8] == "1"]   # sadece kapanmış mumlar
    if len(rows) < lookback // 2:
        return None
    last = rows[-1]
    o, c = float(last[1]), float(last[4])
    vol = float(last[7])                                # USDT cinsinden hacim
    if o <= 0 or vol < cfg["min_usdt"]:
        return None

    change = (c / o - 1) * 100
    if abs(change) < cfg["change"]:                     # fiyat hareketi yetersizse çık
        return None

    hist = [float(r[7]) for r in rows[:-1]]
    median = statistics.median(hist)
    mad = statistics.median([abs(v - median) for v in hist])
    if median <= 0 or mad <= 0:
        return None

    ratio = vol / median
    z = 0.6745 * (vol - median) / mad
    if ratio >= cfg["ratio"] and z >= cfg["z"]:
        return {"inst": inst, "ratio": ratio, "z": z,
                "change": change, "price": c, "vol": vol}
    return None


def send(msg):
    print(msg + "\n", flush=True)
    token, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID")
    if token and chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": msg}, timeout=10,
            )
        except Exception as e:
            print("Telegram hatası:", e)


def fmt_usdt(v):
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    return f"{v / 1_000:.0f}K"


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    state = load_state()
    now = int(time.time())
    manual = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"

    due = []
    for bar, cfg in TIMEFRAMES.items():
        sec = cfg["sec"]
        last_closed_open = (now // sec) * sec - sec     # son kapanan mumun açılış zamanı
        if state.get(bar) != last_closed_open:
            due.append((bar, last_closed_open))

    if manual:
        send("✅ Test: OKX pump/dump botu GitHub Actions üzerinde çalışıyor.")
    if not due:
        print("Taranacak yeni mum yok.")
        return

    symbols = get_symbols()
    print(f"{len(symbols)} sembol, taranacak: {[b for b, _ in due]}")

    for bar, candle_open in due:
        cfg = TIMEFRAMES[bar]
        wait = candle_open + cfg["sec"] + 5 - time.time()   # OKX mumu onaylasın
        if wait > 0:
            time.sleep(wait)

        hits = []
        for inst in symbols:
            try:
                r = analyze(inst, bar, cfg)
            except Exception as e:
                print(f"{inst} {bar} hata: {e}")
                time.sleep(1)
                continue
            time.sleep(REQUEST_PAUSE)
            if r:
                hits.append(r)

        state[bar] = candle_open
        print(f"{bar} tarandı, {len(hits)} hareket.")
        if not hits:
            continue

        hits.sort(key=lambda x: x["ratio"], reverse=True)   # en güçlü hacim üstte
        label = bar.replace("utc", "")
        lines = [f"🚨 [{label}] {len(hits)} güçlü hareket"]
        for r in hits[:MAX_ALERTS_PER_SCAN]:
            kind = "🟢 PUMP" if r["change"] > 0 else "🔴 DUMP"
            name = r["inst"].replace("-USDT-SWAP", "")
            lines.append(
                f"{kind} {name}  {r['change']:+.1f}%  |  hacim {r['ratio']:.1f}x "
                f"({fmt_usdt(r['vol'])} USDT)  |  fiyat {r['price']}"
            )
        if len(hits) > MAX_ALERTS_PER_SCAN:
            lines.append(f"... ve {len(hits) - MAX_ALERTS_PER_SCAN} hareket daha")
        send("\n".join(lines))

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
