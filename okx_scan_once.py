"""
OKX hacim anomali tarayıcı - GitHub Actions için TEK SEFERLİK sürüm.
Her çalıştırmada, kapanmış ama henüz taranmamış mumları tarar ve çıkar.
Hangi mumun taranmadığını state.json dosyasından bilir.

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
    # OKX bar adı: (lookback mum, min ratio, min robust z, periyot saniye)
    "15m":   (96, 3.5, 4.5, 900),
    "1H":    (72, 3.0, 4.0, 3600),
    "4H":    (60, 2.5, 4.0, 14400),
    "1Dutc": (30, 2.0, 3.5, 86400),
}
TOP_N = 80
MIN_QUOTE_VOLUME = 5_000_000
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


def analyze(inst, bar, lookback, min_ratio, min_z):
    data = api("/api/v5/market/candles",
               {"instId": inst, "bar": bar, "limit": str(lookback + 2)})
    rows = [r for r in reversed(data) if r[8] == "1"]   # sadece kapanmış mumlar
    if len(rows) < lookback // 2:
        return None
    last = rows[-1]
    hist = [float(r[7]) for r in rows[:-1]]
    vol = float(last[7])

    median = statistics.median(hist)
    mad = statistics.median([abs(v - median) for v in hist])
    if median <= 0 or mad <= 0:
        return None

    ratio = vol / median
    z = 0.6745 * (vol - median) / mad
    if ratio >= min_ratio and z >= min_z:
        o, c = float(last[1]), float(last[4])
        return {"ratio": ratio, "z": z, "change": (c / o - 1) * 100, "price": c}
    return None


def notify(msg):
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
    for bar, (_, _, _, sec) in TIMEFRAMES.items():
        last_closed_open = (now // sec) * sec - sec   # son kapanan mumun açılış zamanı
        if state.get(bar) != last_closed_open:
            due.append((bar, last_closed_open))

    if manual:
        notify("✅ Test: OKX hacim botu GitHub Actions üzerinde çalışıyor.")
    if not due:
        print("Taranacak yeni mum yok.")
        return

    symbols = get_symbols()
    print(f"{len(symbols)} sembol, taranacak: {[b for b, _ in due]}")

    for bar, candle_open in due:
        # mum kapanışından sonra OKX'in onaylaması için kısa bekleme
        wait = candle_open + TIMEFRAMES[bar][3] + 5 - time.time()
        if wait > 0:
            time.sleep(wait)
        lookback, min_ratio, min_z, _ = TIMEFRAMES[bar]
        found = 0
        for inst in symbols:
            try:
                r = analyze(inst, bar, lookback, min_ratio, min_z)
            except Exception as e:
                print(f"{inst} {bar} hata: {e}")
                time.sleep(1)
                continue
            time.sleep(REQUEST_PAUSE)
            if r:
                found += 1
                arrow = "🟢" if r["change"] >= 0 else "🔴"
                notify(
                    f"{arrow} HACİM ANOMALİSİ {inst.replace('-SWAP', '')} "
                    f"[{bar.replace('utc', '')}]\n"
                    f"Hacim normalin {r['ratio']:.1f}x katı (z={r['z']:.1f})\n"
                    f"Mum değişimi: {r['change']:+.2f}%  |  Fiyat: {r['price']}"
                )
        state[bar] = candle_open
        print(f"{bar} tarandı, {found} alarm.")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("HATA:", e)
        sys.exit(1)
