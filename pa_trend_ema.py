"""
Günlük trend stratejisi: EMA periyodu ve kayma (slippage) duyarlılığı. Mesaj göndermez. Çıktı: trend_ema.md
- Sabit kurgu: günlük kırılım, sabah 08:00 TR piyasa girişi, stop seviye − 0,5 günlük ATR.
- Çıkışlar: sabit TP 5R (kur-unut) ve karşılaştırma için günlük stop 10 gün dibi (sabah güncelle).
- EMA: yok, 21, 50, 100, 200. EMA'lar 700 günlük günlük mum geçmişinden hesaplanır (tüm periyotlar
  aynı 365 günde adil karşılaştırılır).
- Kayma: piyasa emirleri (giriş, stop, süre sonu) için %0 / 0,05 / 0,1 / 0,25 / 0,5. Limit TP'de kayma yok.
- Şans seviyesi: aynı ayar, mumları karıştırılmış 3 veri setinde (bu kısımda EMA kendi verisinden hesaplanır).
"""
import sys
import gzip
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pa_trend_bt as T

OUT = "trend_ema.md"
DCACHE = "trend_daily.json.gz"
EMAS = [0, 21, 50, 100, 200]
EXITS = ["tp5", "don10g"]
SLIPS = [0.0, 0.05, 0.10, 0.25, 0.50]
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def load_daily(insts):
    try:
        with gzip.open(DCACHE, "rt") as f:
            c = json.load(f)
        if time.time() - c["created"] < 3 * 86400 and all(i in c["data"] for i in insts):
            return c["data"]
    except Exception:
        pass

    def one(inst):
        for d in range(8):
            try:
                s = T.p.fetch(inst, "1Dutc", 86400, 700)
                time.sleep(0.3)
                return inst, {"t": s["t"], "c": s["c"]}
            except Exception as e:
                print(f"{inst} günlük deneme {d + 1}: {e}", flush=True)
                time.sleep(3 + 4 * d)
        return inst, None

    data = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        for inst, s in ex.map(one, insts):
            if s:
                data[inst] = s
    with gzip.open(DCACHE, "wt") as f:
        json.dump({"created": time.time(), "data": data}, f)
    return data


def ema_map(daily, n):
    e = T.ema(daily["c"], n)
    return {t: v for t, v in zip(daily["t"], e) if v is not None}


def apply_slip(r, slip):
    """Kayma maliyeti R cinsinden: piyasa girişi + (TP dışındaki) piyasa çıkışı."""
    legs = 1 + (0 if r["sonuc"] == "TP" else 1)
    return r["net"] - slip * legs / r["sp"]


def run(coins, t_start, maps=None):
    res = {}
    for n in EMAS:
        evs = []
        for k, c in coins.items():
            m = None
            if maps is not None and n:
                m = maps.get(k, {}).get(n)
                if m is None:
                    continue
            evs += [e for e in T.events(c, "1D", None, ema_n=n, ema_map=m) if e["t"] >= t_start]
        ff = [(ev, T.fill(ev, coins[ev["inst"]], "sabah", 0.5)) for ev in evs]
        ff = [(ev, f) for ev, f in ff if not isinstance(f, str)]
        for ex in EXITS:
            rs = []
            for ev, f in ff:
                r = T.simulate(ev, coins[ev["inst"]], f, ex)
                if r:
                    rs.append(r)
            res[(n, ex)] = rs
    return res


class NoBtc:
    def dir_at(self, t):
        return 0


def main():
    T0 = time.time()
    data, created = T.load()
    t_start = created - T.DAYS * 86400
    t_split = created - T.TEST_DAYS * 86400
    coins = {k: T.Coin(k, v) for k, v in data.items()}
    daily = load_daily(list(coins))
    maps = {k: {n: ema_map(d, n) for n in EMAS if n} for k, d in daily.items()}
    T_events = T.events
    T.events = lambda c, stf, btc, ema_n=50, ema_map=None: T_events(c, stf, NoBtc(), ema_n, ema_map)
    real = run(coins, t_start, maps)
    shs = []
    for seed in (7, 11, 23):
        sh = {k: T.Coin(k, v) for k, v in T.shuffled(data, seed).items()}
        shs.append(run(sh, t_start))

    out("# EMA periyodu ve kayma (slippage) testi — günlük trend stratejisi")
    out(f"{len(coins)} coin, son {T.DAYS} gün (eğitim ilk {T.DAYS - T.TEST_DAYS} / doğrulama son {T.TEST_DAYS} gün). "
        "Kurgu: günlük kapanışla kırılım, sabah 08:00 TR piyasa girişi, stop kırılan seviye − 0,5 günlük ATR, "
        "BTC filtresi yok. Komisyon ve long funding dahil. Portföy: coin başına 1, aynı anda en fazla 5. "
        "Kayma: piyasa emriyle yapılan giriş ve stop/süre çıkışlarında, her işlemde fiyat aleyhe bu kadar kayar.")
    out()
    for ex in EXITS:
        out(f"## Çıkış: {'sabit TP 5R (kur-unut)' if ex == 'tp5' else 'günlük stop 10 gün dibi (sabah güncelle)'}")
        out("| EMA | Tüm işlemler: sayı / kazanan / net R (kayma %0) | Eğitim / doğrulama net R | Şans seviyesi net R | "
            "Portföy 5 net R — kayma %0 · %0,05 · %0,1 · %0,25 · %0,5 | Portföy 5 en büyük düşüş (kayma %0,1) | "
            "Haftada işlem | Ort. stop % |")
        out("|---|---|---|---|---|---|---|---|")
        for n in EMAS:
            rs = real[(n, ex)]
            al = T.stats(rs, T.DAYS)
            tr = sum(r["net"] for r in rs if r["t_in"] < t_split)
            te = sum(r["net"] for r in rs if r["t_in"] >= t_split)
            sans = sum(sum(r["net"] for r in s[(n, ex)]) for s in shs) / len(shs)
            pf, _ = T.portfolio(rs, 5)
            pfs = " · ".join(f"{sum(apply_slip(r, sl) for r in pf):+.1f}" for sl in SLIPS)
            eq = pk = dd = 0.0
            for r in sorted(pf, key=lambda r: r["t_out"]):
                eq += apply_slip(r, 0.10)
                pk = max(pk, eq)
                dd = max(dd, pk - eq)
            sp = sum(r["sp"] for r in rs) / len(rs) if rs else 0
            out(f"| {'yok' if n == 0 else n} | {al['n']} / %{al['win']:.0f} / {al['net']:+.1f} | {tr:+.1f} / {te:+.1f} | "
                f"{sans:+.1f} | {pfs} | {dd:.1f} | {len(pf) / T.DAYS * 7:.1f} | {sp:.1f} |")
        out()
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        with open(OUT, "w") as f:
            f.write("\n".join(lines) + "\n")
