"""Teşhis: botun mantığını Telegram'a mesaj atmadan, durum dosyasına dokunmadan çalıştırır.
Son kapanan mumlar için her taramada kaç coin bulunduğunu ve hataları GitHub notu (annotation) olarak yazar."""
import time, collections
import okx_scan_once as b

def note(t):
    print("::notice::" + t.replace("\n", " | "), flush=True)

now = int(time.time())
try:
    syms = b.get_symbols()
except Exception as e:
    note(f"SEMBOL LİSTESİ ALINAMADI: {e}")
    raise SystemExit(0)
note(f"Taranan sembol sayısı: {len(syms)} (ilk 5: {', '.join(s.replace('-USDT-SWAP','') for s in syms[:5])})")

ozet, hatalar = [], collections.Counter()
for bar, cfg in b.BREAKOUT.items():
    co = b.last_closed_open(now, cfg["sec"])
    hit = stale = err = 0
    for s in syms:
        try:
            if b.analyze_breakout(s, bar, cfg, co): hit += 1
        except b.StaleCandle: stale += 1
        except Exception as e:
            err += 1; hatalar[str(e)[:80]] += 1
        time.sleep(0.08)
    ozet.append(f"{bar}: {hit} kırılım, {stale} bayat, {err} hata")
co = b.last_closed_open(now, b.FVG_SEC); hit = err = stale = 0
for s in syms:
    try:
        if b.analyze_fvg(s, co): hit += 1
    except b.StaleCandle: stale += 1
    except Exception as e:
        err += 1; hatalar[str(e)[:80]] += 1
    time.sleep(0.08)
ozet.append(f"FVG 4H: {hit} dönüş, {stale} bayat, {err} hata")
note("Son kapanan mumlar → " + " ; ".join(ozet))
note("En sık hatalar: " + (" ; ".join(f"{k} ({v})" for k, v in hatalar.most_common(4)) or "yok"))
