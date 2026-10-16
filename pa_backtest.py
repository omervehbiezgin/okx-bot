"""
PA kırılım-retest stratejisi için geçmişe dönük test.
Telegram'a MESAJ GÖNDERMEZ, canlı botun durum dosyasına dokunmaz.

- 15 dakikalık veri (155 gün) ve günlük veri bir kez çekilir, bt_cache2.json.gz dosyasında saklanır.
  30m, 1H, 4H, 6H, 8H mumlar 15m'den üretilir; işlemler 15m mumlarla takip edilir.
- Komisyon (OKX standart): limit (maker) %0,02, piyasa/stop (taker) %0,05.
  Giriş: piyasa modunda taker, limit modlarında maker. TP çıkışları maker, stop çıkışları taker.
- Ezber riskine karşı: dönem EĞİTİM (ilk kısım) ve DOĞRULAMA (son TEST_DAYS gün) olarak ayrı raporlanır;
  seçimler yalnızca eğitim sonucuna göre yapılır.
- Sonuçlar bt_sonuc.md dosyasına yazılır.

Ortam değişkenleri: PA_BACKTEST (toplam gün, varsayılan 120), PA_TEST_DAYS (doğrulama günü, varsayılan 40)
"""
import os
import sys
import gzip
import json
import time
import bisect
from concurrent.futures import ThreadPoolExecutor

import pa_scan_once as p

MAKER, TAKER = 0.02, 0.05
CACHE = "bt_cache2.json.gz"
OUT = "bt_sonuc.md"
WARMUP_DAYS = 35
ENTRY_MODES = ["piyasa", "limit_kapanis", "limit_yari", "limit_seviye"]
ENTRY_AD = {"piyasa": "piyasa (kapanış)", "limit_kapanis": "limit @kapanış",
            "limit_yari": "limit @fitil ortası", "limit_seviye": "limit @kırılan seviye"}
GRID = [("1D", "4H"), ("1D", "1H"), ("1D", "30m"), ("1D", "15m"),
        ("8H", "1H"), ("8H", "30m"), ("8H", "15m"),
        ("6H", "1H"), ("6H", "30m"), ("6H", "15m"),
        ("4H", "1H"), ("4H", "30m"), ("4H", "15m")]

lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save_out():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------- Veri ----------------
def fetch_retry(inst, bar, sec, n):
    for deneme in range(5):
        try:
            return p.fetch(inst, bar, sec, n)
        except Exception as e:
            print(f"{inst} {bar} deneme {deneme + 1}: {e}", flush=True)
            time.sleep(2 + deneme * 2)
    return None


def cut(s, t_end):
    j = bisect.bisect_right(s["t"], t_end)
    return {k: (v[:j] if isinstance(v, list) else v) for k, v in s.items()}


def load_data(days):
    data, created = {}, time.time()
    try:
        with gzip.open(CACHE, "rt") as f:
            c = json.load(f)
        if c.get("days") == days and time.time() - c["created"] < 2 * 86400:
            data, created = c["data"], c["created"]
            print(f"Önbellekte {len(data)} coin var.", flush=True)
    except Exception:
        pass
    try:
        symbols = [s for s in p.get_symbols() if s not in data]
    except Exception as e:
        if not data:
            raise
        print("Coin listesi alınamadı, önbellekteki veriyle devam:", e, flush=True)
        symbols = []
    if "BTC-USDT-SWAP" not in data and "BTC-USDT-SWAP" not in symbols:
        symbols.insert(0, "BTC-USDT-SWAP")
    n = (days + WARMUP_DAYS) * 96
    if symbols:
        print(f"{len(symbols)} coin için veri çekiliyor ({n} adet 15m mum + günlük)...", flush=True)

        def one(inst):
            s15 = fetch_retry(inst, "15m", 900, n)
            d1 = fetch_retry(inst, "1Dutc", 86400, 300)
            time.sleep(0.5)
            return inst, s15, d1

        kisa = 0
        with ThreadPoolExecutor(max_workers=2) as ex:
            for inst, s15, d1 in ex.map(one, symbols):
                if s15 and d1 and len(s15["t"]) > 96 * (WARMUP_DAYS + 7):
                    data[inst] = {"s15": cut(s15, created), "d1": cut(d1, created - 86400)}
                else:
                    kisa += 1
        print(f"Veri hazır: {len(data)} coin, {kisa} coin verisi yetersiz/alınamadı.", flush=True)
        with gzip.open(CACHE, "wt") as f:
            json.dump({"days": days, "created": created, "data": data}, f)
    return data, created


# ---------------- BTC yönü ----------------
class BtcTrend:
    """BTC 4H kapanışı EMA50'nin üstünde mi (sadece kapanmış mumlar)."""

    def __init__(self, s15):
        b4 = p.aggregate(s15, 14400)
        c = b4["c"]
        k = 2 / 51
        ema = [None] * len(c)
        if len(c) >= 50:
            e = sum(c[:50]) / 50
            ema[49] = e
            for i in range(50, len(c)):
                e = c[i] * k + e * (1 - k)
                ema[i] = e
        self.t, self.c, self.ema = b4["t"], c, ema

    def dir_at(self, t):
        i = bisect.bisect_right(self.t, t - 14400) - 1
        if i < 0 or self.ema[i] is None:
            return 0
        return 1 if self.c[i] > self.ema[i] else -1


# ---------------- İşlem simülasyonu ----------------
def simulate(g, s, mode, rej_sec):
    """Sonuç: (net R, brüt R, sonuç) veya dolmayan limit emir için None."""
    d, close, sl, tp2 = g["dir"], g["entry"], g["sl"], g["tp2"]
    if mode == "piyasa":
        e = close
    elif mode == "limit_kapanis":
        e = close
    elif mode == "limit_yari":
        e = (close + g["ext"]) / 2
    else:
        e = g["level"]
    if (e - sl) * d <= 0 or (tp2 - e) * d <= 0:
        return None
    R = abs(e - sl)
    tp1 = e + d * R
    rr2 = (tp2 - e) * d / R
    fee_in = TAKER if mode == "piyasa" else MAKER

    j = bisect.bisect_left(s["t"], g["t"])
    n = len(s["t"])
    if mode != "piyasa":
        son = g["t"] + p.FILL_BARS * rej_sec
        dolu = False
        while j < n and s["t"][j] < son:
            hi, lo = s["h"][j], s["l"][j]
            if (tp1 - (lo if d == 1 else hi)) * d <= 0 and not ((hi >= e) if d == -1 else (lo <= e)):
                return None                                   # fiyat dolmadan hedefe kaçtı
            if (hi >= e) if d == -1 else (lo <= e):
                dolu = True
                if (hi >= sl) if d == -1 else (lo <= sl):     # aynı mumda stop: temkinli varsay
                    return _res(-1.0, fee_in + TAKER, R, e, "stop")
                j += 1
                break
            j += 1
        if not dolu:
            return None

    half = False
    for j in range(j, n):
        adv = s["l"][j] if d == 1 else s["h"][j]
        fav = s["h"][j] if d == 1 else s["l"][j]
        if not half:
            if (adv - sl) * d <= 0:
                return _res(-1.0, fee_in + TAKER, R, e, "stop")
            if (fav - tp1) * d >= 0:
                half = True
                if (fav - tp2) * d >= 0:
                    return _res(0.5 + 0.5 * rr2, fee_in + MAKER, R, e, "TP2")
        else:
            if (adv - e) * d <= 0:
                return _res(0.5, fee_in + 0.5 * MAKER + 0.5 * TAKER, R, e, "TP1+başabaş")
            if (fav - tp2) * d >= 0:
                return _res(0.5 + 0.5 * rr2, fee_in + MAKER, R, e, "TP2")
    acik = (s["c"][-1] - e) * d / R
    return _res(0.5 + 0.5 * acik if half else acik, fee_in + TAKER, R, e, "açık")


def _res(gross, fee_pct, R, e, sonuc):
    stop_pct = R / e * 100
    return gross - fee_pct / stop_pct, gross, sonuc


# ---------------- Değerlendirme ----------------
class Bench:
    def __init__(self, data):
        self.raw = data
        self.series, self.atr, self.piv, self.dmap, self.setups = {}, {}, {}, {}, {}
        self.btc = BtcTrend(data["BTC-USDT-SWAP"]["s15"]) if "BTC-USDT-SWAP" in data else None

    def ser(self, inst, tf):
        key = (inst, tf)
        if key not in self.series:
            r = self.raw[inst]
            if tf == "1D":
                s = r["d1"]
            elif tf == "15m":
                s = r["s15"]
            else:
                s = p.aggregate(r["s15"], p.TF[tf][1])
            self.series[key] = s
            self.atr[key] = p.atr_arr(s)
        return self.series[key], self.atr[key]

    def run(self, stf, rej, t0, t1, mode="piyasa", btc=False, volm=0.0):
        p.STRUCT_TF = stf
        cfg = p.STRUCT[stf]
        skey = (stf, cfg["k"], cfg["look"], cfg["top_age"], cfg["retest"], p.MIN_AWAY, p.LEVEL_MODE)
        rej_sec = p.TF[rej][1]
        sigs, unfilled = [], 0
        for inst in self.raw:
            d, datr = self.ser(inst, stf)
            x, xatr = self.ser(inst, rej)
            if len(d["t"]) < 50:
                continue
            pk = (inst, stf, cfg["k"])
            if pk not in self.piv:
                self.piv[pk] = p.pivots(d["h"], d["l"], 0, len(d["t"]) - 1, cfg["k"])
            mk = (inst, stf, rej)
            if mk not in self.dmap:
                self.dmap[mk] = [p.last_day_before(d, t) for t in x["t"]]
            dm = self.dmap[mk]
            sc = self.setups.setdefault((inst,) + skey, {})
            j0, j1 = bisect.bisect_left(x["t"], t0), bisect.bisect_left(x["t"], t1)
            used = set()
            s15 = self.raw[inst]["s15"]
            for j in range(j0, j1):
                D = dm[j]
                if D < 0:
                    continue
                if D not in sc:
                    sc[D] = p.setups_at(d, D, datr, self.piv[pk])
                sts, highs, lows = sc[D]
                for st in sts:
                    if st["key"] in used:
                        continue
                    if volm > 0 and st.get("volr") is not None and st["volr"] < volm:
                        continue
                    g = p.check_reject(x, j, xatr, st, highs, lows)
                    if not g:
                        continue
                    if btc and self.btc and self.btc.dir_at(g["t"]) != g["dir"]:
                        continue
                    used.add(st["key"])
                    r = simulate(g, s15, mode, rej_sec)
                    if r is None:
                        unfilled += 1
                        continue
                    g["net"], g["R"], g["sonuc"] = r
                    g["inst"] = inst
                    sigs.append(g)
        return sigs, unfilled


def stats(res, days):
    sigs, unf = res
    n = len(sigs)
    kap = [g for g in sigs if g["sonuc"] != "açık"]
    stop = sum(1 for g in kap if g["sonuc"] == "stop")
    net = sum(g["net"] for g in sigs)
    return dict(n=n, unf=unf, tp1=(len(kap) - stop) / len(kap) * 100 if kap else 0,
                gross=sum(g["R"] for g in sigs), net=net, per=net / n if n else 0, ay=n / days * 30)


def row(ad, tr, te, al):
    return (f"| {ad} | {tr['n']} | %{tr['tp1']:.0f} | {tr['net']:+.1f} | {te['n']} | %{te['tp1']:.0f} | "
            f"{te['net']:+.1f} | {al['n']} (~{al['ay']:.0f}/ay) | {al['unf']} | %{al['tp1']:.0f} | "
            f"{al['gross']:+.1f} | **{al['net']:+.1f}** | {al['per']:+.2f} |")


HEAD = ("| Ayar | Eğt. işlem | Eğt. TP1+ | Eğt. net R | Doğr. işlem | Doğr. TP1+ | Doğr. net R | "
        "Toplam işlem | Dolmayan | TP1+ | Brüt R | Net R | R/işlem |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")


def main():
    days = max(30, min(int(os.getenv("PA_BACKTEST", "120") or 120), 150))
    test_days = max(10, min(int(os.getenv("PA_TEST_DAYS", "40") or 40), days - 20))
    data, created = load_data(days)
    t_start, t_split, t_end = created - days * 86400, created - test_days * 86400, created + 86400
    tr_days = days - test_days
    b = Bench(data)

    def three(stf, rej, **kw):
        tr = stats(b.run(stf, rej, t_start, t_split, **kw), tr_days)
        te = stats(b.run(stf, rej, t_split, t_end, **kw), test_days)
        al = stats(b.run(stf, rej, t_start, t_end, **kw), days)
        return tr, te, al

    out(f"# PA kırılım-retest geçmiş test ({time.strftime('%d.%m.%Y %H:%M', time.gmtime(created + 3 * 3600))} TR)")
    out(f"{len(data)} coin, son {days} gün: eğitim ilk {tr_days} gün, doğrulama son {test_days} gün. "
        f"Komisyon: maker %{MAKER}, taker %{TAKER}. Limit emir en fazla {p.FILL_BARS} red mumu bekler. "
        f"BTC filtresi: BTC 4H kapanış EMA50 yönü.")
    out()

    # 0) Seviye tanımı karşılaştırması (piyasa girişi, filtresiz)
    out("## 0) Seviye tanımı: önceki tepe/dip (senin tanımın) vs son tepeyi oluşturan dip (eski)")
    out(HEAD)
    for lm, ad in (("onceki_tepe", "önceki tepe/dip"), ("son_dip", "son tepeyi oluşturan dip")):
        p.LEVEL_MODE = lm
        for stf, rej in (("1D", "1H"), ("4H", "30m")):
            tr, te, al = three(stf, rej)
            out(row(f"{ad}, {stf}→{rej}", tr, te, al))
            save_out()
    p.LEVEL_MODE = "onceki_tepe"
    out()

    # A) 4H→30m üzerinde giriş türü ve filtreler
    out("## A) 4H→30m: giriş yeri ve filtreler")
    out(HEAD)
    res = {}
    for mode in ENTRY_MODES:
        for btc in (False, True):
            for volm in (0.0, 1.0):
                ad = f"{ENTRY_AD[mode]}{' + BTC' if btc else ''}{' + hacim≥1x' if volm else ''}"
                tr, te, al = three("4H", "30m", mode=mode, btc=btc, volm=volm)
                res[(mode, btc, volm)] = tr["net"]
                out(row(ad, tr, te, al))
                save_out()
    best = max(res, key=lambda k: res[k])
    mode, btc, volm = best
    secim = f"{ENTRY_AD[mode]}{' + BTC' if btc else ''}{' + hacim≥1x' if volm else ''}"
    out()
    out(f"Eğitim döneminde en iyi: **{secim}** (seçim sadece eğitim sonucuna göre).")
    out()

    # B) Zaman dilimi tablosu: seçilen ayar ve karşılaştırma için piyasa girişi
    out(f"## B) Zaman dilimleri — seçilen ayar: {secim}")
    out(HEAD)
    for stf, rej in GRID:
        tr, te, al = three(stf, rej, mode=mode, btc=btc, volm=volm)
        out(row(f"{stf}→{rej}", tr, te, al))
        save_out()
    out()
    out("## C) Zaman dilimleri — karşılaştırma: piyasa girişi, filtresiz")
    out(HEAD)
    for stf, rej in GRID:
        tr, te, al = three(stf, rej)
        out(row(f"{stf}→{rej}", tr, te, al))
        save_out()
    print(f"::notice::Bitti. Seçilen giriş/filtre: {secim}. Ayrıntı: {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        save_out()
        sys.exit(1)
    finally:
        save_out()
