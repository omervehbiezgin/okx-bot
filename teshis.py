"""Teşhis: son N mumda kaç kırılım çıkardı, hangi filtre ne kadar eledi (mesaj göndermez, durumu değiştirmez)."""
import time, collections
import okx_scan_once as b

def note(t):
    print("::notice::" + t, flush=True)

syms = b.get_symbols()
gercek_candles = b.candles
cache = {}
def candles_kes(inst, bar, limit):
    key = (inst, bar)
    if key not in cache:
        cache[key] = gercek_candles(inst, bar, 300); time.sleep(0.07)
    rows = cache[key]
    upto = globals()["KES"].get(bar)
    if upto is not None:
        rows = [r for r in rows if int(r[0]) // 1000 <= upto]
    return rows[-limit:]
b.candles = candles_kes
b.time.sleep = lambda s: None
KES = {}

now = int(time.time())
GERI = {"15m": 32, "1H": 12}          # 15m: son 8 saat, 1H: son 12 saat
for bar, n in GERI.items():
    cfg = b.BREAKOUT[bar]
    sonuc = {}
    for ad, ayar in [("mevcut", {}), ("hacim oranı kapalı", {"BRK_MIN_VOL_RATIO": 0}),
                     ("%80 kapalı", {"BRK_LIVE_PCT": 0}), ("ikisi de kapalı", {"BRK_MIN_VOL_RATIO": 0, "BRK_LIVE_PCT": 0})]:
        eski = {k: getattr(b, k) for k in ayar}
        for k, v in ayar.items(): setattr(b, k, v)
        toplam, coinler = 0, set()
        for i in range(n):
            co = b.last_closed_open(now, cfg["sec"]) - i * cfg["sec"]
            KES = {bar: co}
            for s in syms:
                try:
                    if b.analyze_breakout(s, bar, cfg, co):
                        toplam += 1; coinler.add(s.replace("-USDT-SWAP", ""))
                except Exception:
                    pass
        KES = {}
        for k, v in eski.items(): setattr(b, k, v)
        sonuc[ad] = f"{toplam} ({', '.join(sorted(coinler)[:6])})"
    note(f"{bar} son {n} mum: " + " ; ".join(f"{k}: {v}" for k, v in sonuc.items()))
