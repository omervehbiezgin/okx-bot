"""
PA kırılım-retest stratejisi: kapsamlı geçmiş test.
Telegram'a MESAJ GÖNDERMEZ, canlı botun durum dosyasına dokunmaz. Sonuçlar bt_sonuc.md dosyasına yazılır.

Yöntem
- Veri: hacimde ilk ~80 kripto USDT perpetual, son 120 gün (+35 gün ısınma). 15m ve günlük mumlar
  bir kez çekilir (bt_cache2.json.gz); 30m/1H/4H/6H/8H mumlar 15m'den üretilir. İşlemler 15m ile izlenir.
- Komisyon (OKX standart): maker %0,02 (limit giriş, TP), taker %0,05 (piyasa giriş, stop, başabaş).
  Funding hesaba katılmaz.
- Ezber riskine karşı: EĞİTİM = ilk 80 gün, DOĞRULAMA = son 40 gün. Her aşamada seçim SADECE
  eğitim net R'ına göre yapılır; doğrulama tarafsız kontrol olarak raporlanır.
- Önce her zaman dilimi için tüm red olayları (kurulum başına tüm red mumları) çıkarılır;
  filtreler/giriş/stop/TP seçenekleri bu olaylar üzerinde hızlıca denenir.

Aşamalar
  0) Seviye tanımı: önceki tepe/dip | son tepeyi oluşturan dip | birleşik
  1) TP × stop tablosu (13 TP × 7 stop)
  2) Giriş türü × BTC filtresi × hacim filtresi
  3) Teyit filtreleri (güçlü kırılım, RSI uyumsuzluğu, likidite süpürmesi, retestte düşük hacim, ilk test)
  4) Tüm zaman dilimleri: son ayarla ve karşılaştırma için başlangıç ayarıyla
"""
import os
import sys
import gzip
import json
import time
import bisect
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import pa_scan_once as p

MAKER, TAKER = 0.02, 0.05
CACHE = "bt_cache2.json.gz"
OUT = "bt_sonuc.md"
WARMUP_DAYS = 35
DEV_TFS = [("1D", "1H"), ("8H", "30m"), ("4H", "30m")]     # ayar seçiminde kullanılan zaman dilimleri
GRID = [("1D", "4H"), ("1D", "1H"), ("1D", "30m"), ("1D", "15m"),
        ("8H", "1H"), ("8H", "30m"), ("8H", "15m"),
        ("6H", "1H"), ("6H", "30m"), ("6H", "15m"),
        ("4H", "1H"), ("4H", "30m"), ("4H", "15m")]

LEVELS = {"onceki_tepe": "önceki tepe/dip (8→10 ise 8)", "son_dip": "son tepeyi oluşturan dip (7)",
          "birlesik": "birleşik (8, ama 7 de kırılmış)"}
ENTRIES = {"piyasa": "piyasa (red kapanışı)", "limit_kapanis": "limit @kapanış",
           "limit_yari": "limit @fitil ortası", "limit_seviye": "limit @kırılan seviye"}
STOPS = {"fitil": "red fitili ötesi", "seviye_atr": "seviye + 0,5 ATR", "kirilim": "kırılım mumu ucu",
         "son_tepe": "son tepe/dip ötesi", "y2": "sabit %2", "y3": "sabit %3", "y5": "sabit %5"}
TPS = {"r1_seviye": "kısmi: 1R + sıradaki seviye (≥2R)", "yapi": "kısmi: ilk dip + ikinci dip",
       "sabit_r": "kısmi: 1R + 3R", "t_ilk": "tek: ilk dip", "t_ikinci": "tek: ikinci dip",
       "t_1.5R": "tek: 1,5R", "t_2R": "tek: 2R", "t_3R": "tek: 3R",
       "t_y5": "tek: %5", "t_y10": "tek: %10", "t_y15": "tek: %15",
       "t_a2": "tek: 2× günlük ATR", "t_a3": "tek: 3× günlük ATR"}
CONFS = {"guclu": "güçlü kırılım mumu", "rsi": "son tepede RSI uyumsuzluğu", "supurme": "likidite süpürmesi",
         "hacim_retest": "retestte düşük hacim", "ilk_test": "sadece ilk test"}
BASE = dict(entry="piyasa", stop="fitil", tp="r1_seviye", btc=False, vol=0.0, conf=())

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
        print("Coin listesi alınamadı, önbellekle devam:", e, flush=True)
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


# ---------------- Olay çıkarma ----------------
class Bench:
    def __init__(self, data):
        self.raw = data
        self.series, self.atr, self.piv, self.dmap, self.setups = {}, {}, {}, {}, {}
        self.np15 = {}
        self.events = {}
        self.btc = BtcTrend(data["BTC-USDT-SWAP"]["s15"]) if "BTC-USDT-SWAP" in data else None
        self.datr1 = {}

    def ser(self, inst, tf):
        key = (inst, tf)
        if key not in self.series:
            r = self.raw[inst]
            s = r["d1"] if tf == "1D" else (r["s15"] if tf == "15m" else p.aggregate(r["s15"], p.TF[tf][1]))
            self.series[key] = s
            self.atr[key] = p.atr_arr(s)
        return self.series[key], self.atr[key]

    def arr(self, inst):
        if inst not in self.np15:
            s = self.raw[inst]["s15"]
            self.np15[inst] = (s["t"], np.array(s["h"]), np.array(s["l"]), np.array(s["c"]))
        return self.np15[inst]

    def daily_atr(self, inst, t):
        if inst not in self.datr1:
            d1, a1 = self.ser(inst, "1D")
            self.datr1[inst] = (d1, a1)
        d1, a1 = self.datr1[inst]
        i = p.last_day_before(d1, t)
        return a1[i] if i >= 0 else None

    def gen(self, stf, rej, level):
        """Bu zaman dilimi ve seviye tanımı için tüm red olayları (kurulum başına tüm red mumları)."""
        key = (stf, rej, level)
        if key in self.events:
            return self.events[key]
        t0 = time.time()
        p.STRUCT_TF, p.LEVEL_MODE = stf, level
        p.MIN_STOP_PCT, p.MAX_STOP_PCT, p.MIN_RR = 0.0, 1e9, 0.0
        cfg = p.STRUCT[stf]
        m = max(1, p.TF[stf][1] // p.TF[rej][1])
        evs = []
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
            sc = self.setups.setdefault((inst, stf, level), {})
            xv = x.get("v") or [0.0] * len(x["t"])
            touched = set()
            for j in range(len(x["t"])):
                D = dm[j]
                if D < 0:
                    continue
                if D not in sc:
                    sc[D] = p.setups_at(d, D, datr, self.piv[pk])
                sts, highs, lows = sc[D]
                for st in sts:
                    L, a, dr = st["level"], st["atr"], st["dir"]
                    touch = (x["h"][j] >= L - p.TOUCH_TOL * a) if dr == -1 else (x["l"][j] <= L + p.TOUCH_TOL * a)
                    g = p.check_reject(x, j, xatr, st, highs, lows)
                    if g:
                        g["inst"] = inst
                        g["first"] = st["key"] not in touched
                        g["E"], g["brk_ext"], g["ax"] = st["E"], st["brk_ext"], xatr[j]
                        g["satr"] = a
                        yaklasma = sum(xv[max(0, j - m + 1):j + 1])
                        g["retest_dusuk"] = st.get("brk_vol") is not None and yaklasma < st["brk_vol"]
                        g["btc"] = self.btc.dir_at(g["t"]) if self.btc else 0
                        g["datr"] = self.daily_atr(inst, g["t"])
                        g["rej_sec"] = p.TF[rej][1]
                        evs.append(g)
                    if touch:
                        touched.add(st["key"])
        evs.sort(key=lambda g: g["t"])
        self.events[key] = evs
        print(f"  olaylar {stf}→{rej} [{level}]: {len(evs)} ({time.time() - t0:.0f} sn)", flush=True)
        return evs


# ---------------- Simülasyon ----------------
def first_true(b):
    if b.size == 0:
        return None
    i = int(np.argmax(b))
    return i if b[i] else None


def plan(g, cfg, e):
    """Stop ve hedefler. (sl, tp_a, tp_b veya None, kısmi mi) ya da None (bu ayarla işlem yok)."""
    d, ax = g["dir"], g["ax"] or 0
    st = cfg["stop"]
    if st == "fitil":
        sl = g["sl"]
    elif st == "seviye_atr":
        sl = g["level"] - d * 0.5 * g["satr"]
    elif st == "kirilim":
        sl = g["brk_ext"] - d * 0.1 * ax
    elif st == "son_tepe":
        sl = g["E"] - d * 0.1 * ax
    else:
        sl = e * (1 - d * {"y2": 2, "y3": 3, "y5": 5}[st] / 100)
    if sl is None or (e - sl) * d <= 0:
        return None
    R = abs(e - sl)
    sp = R / e * 100
    if sp < 0.3 or sp > (8.0 if st == "fitil" else 20.0):
        return None
    tg = [q for q in g["targets"] if (q - e) * d > 0]
    tp = cfg["tp"]
    if tp == "r1_seviye":
        b = next((q for q in tg if abs(q - e) > 0.2 * R), e + d * 2 * R)
        if abs(b - e) < 2 * R:
            return None
        return sl, e + d * R, b, True
    if tp == "yapi":
        if not tg or abs(tg[0] - e) < R:
            return None
        b = tg[1] if len(tg) > 1 else tg[0] + (tg[0] - e)
        return sl, tg[0], b, True
    if tp == "sabit_r":
        return sl, e + d * R, e + d * 3 * R, True
    if tp == "t_ilk":
        return (sl, tg[0], None, False) if tg and abs(tg[0] - e) >= R else None
    if tp == "t_ikinci":
        return (sl, tg[1], None, False) if len(tg) > 1 and abs(tg[1] - e) >= R else None
    if tp in ("t_1.5R", "t_2R", "t_3R"):
        return sl, e + d * float(tp[2:-1]) * R, None, False
    if tp in ("t_y5", "t_y10", "t_y15"):
        return sl, e * (1 + d * int(tp[3:]) / 100), None, False
    if tp in ("t_a2", "t_a3"):
        if not g["datr"]:
            return None
        return sl, e + d * int(tp[3:]) * g["datr"], None, False
    return None


def simulate(g, cfg, arrs):
    """(net R, brüt R, sonuç) | "dolmadi" | "elendi"."""
    t, H, Lw, C = arrs
    d, mode = g["dir"], cfg["entry"]
    e = {"piyasa": g["entry"], "limit_kapanis": g["entry"], "limit_yari": (g["entry"] + g["ext"]) / 2,
         "limit_seviye": g["level"]}[mode]
    pl = plan(g, cfg, e)
    if pl is None:
        return "elendi"
    sl, a, b, kismi = pl
    R = abs(e - sl)
    sp = R / e * 100
    fee_in = TAKER if mode == "piyasa" else MAKER
    j = bisect.bisect_left(t, g["t"])
    n = len(t)

    def res(gross, fee, sonuc):
        return gross - fee / sp, gross, sonuc

    if mode != "piyasa":
        son = g["t"] + p.FILL_BARS * g["rej_sec"]
        dolu = False
        while j < n and t[j] < son:
            hi, lo = H[j], Lw[j]
            fill = (hi >= e) if d == -1 else (lo <= e)
            if not fill and ((lo <= a) if d == -1 else (hi >= a)):
                return "dolmadi"
            if fill:
                dolu = True
                if (hi >= sl) if d == -1 else (lo <= sl):
                    return res(-1.0, fee_in + TAKER, "stop")
                j += 1
                break
            j += 1
        if not dolu:
            return "dolmadi"
    if j >= n:
        return res(0.0, fee_in + TAKER, "açık")
    hs, ls = H[j:], Lw[j:]
    adv, fav = (hs, ls) if d == -1 else (ls, hs)

    def hit_adv(level):
        return (adv >= level) if d == -1 else (adv <= level)

    def hit_fav(level):
        return (fav <= level) if d == -1 else (fav >= level)

    i_s = first_true(hit_adv(sl))
    i_a = first_true(hit_fav(a))
    ra = abs(a - e) / R
    if not kismi:
        if i_s is not None and (i_a is None or i_s <= i_a):
            return res(-1.0, fee_in + TAKER, "stop")
        if i_a is not None:
            return res(ra, fee_in + MAKER, "TP")
        return res((C[-1] - e) * d / R, fee_in + TAKER, "açık")
    rb = abs(b - e) / R
    if i_s is not None and (i_a is None or i_s <= i_a):
        return res(-1.0, fee_in + TAKER, "stop")
    if i_a is None:
        return res((C[-1] - e) * d / R, fee_in + TAKER, "açık")
    if hit_fav(b)[i_a]:
        return res(0.5 * ra + 0.5 * rb, fee_in + MAKER, "TP2")
    hs2 = slice(i_a + 1, None)
    i_be = first_true(hit_adv(e)[hs2])
    i_b = first_true(hit_fav(b)[hs2])
    if i_be is not None and (i_b is None or i_be <= i_b):
        return res(0.5 * ra, fee_in + 0.5 * MAKER + 0.5 * TAKER, "TP1+başabaş")
    if i_b is not None:
        return res(0.5 * ra + 0.5 * rb, fee_in + MAKER, "TP2")
    return res(0.5 * ra + 0.5 * (C[-1] - e) * d / R, fee_in + 0.5 * MAKER + 0.5 * TAKER, "açık")


def passes(g, cfg):
    if cfg["btc"] and g["btc"] != g["dir"]:
        return False
    if cfg["vol"] and g.get("volr") is not None and g["volr"] < cfg["vol"]:
        return False
    for c in cfg["conf"]:
        if c == "ilk_test":
            if not g["first"]:
                return False
        elif c == "hacim_retest":
            if not g["retest_dusuk"]:
                return False
        elif not g["flags"].get(c):
            return False
    return True


def evaluate(b, evs, cfg, t_start, t_split, t_end):
    """Kurulum başına filtrelerden geçen ilk red olayı işleme alınır."""
    used = set()
    tr, te, unf, el = [], [], 0, 0
    for g in evs:
        if g["t"] < t_start or g["t"] >= t_end:
            continue
        k = (g["inst"], g["key"])
        if k in used or not passes(g, cfg):
            continue
        used.add(k)
        r = simulate(g, cfg, b.arr(g["inst"]))
        if r == "dolmadi":
            unf += 1
            continue
        if r == "elendi":
            el += 1
            continue
        rec = dict(net=r[0], gross=r[1], sonuc=r[2], sp=abs(g["entry"] - g["sl"]) / g["entry"] * 100)
        (tr if g["t"] < t_split else te).append(rec)
    return tr, te, unf, el


def st(recs, days):
    n = len(recs)
    kap = [r for r in recs if r["sonuc"] != "açık"]
    kaz = sum(1 for r in kap if r["sonuc"] != "stop")
    seri = mx = 0
    for r in recs:
        seri = seri + 1 if r["sonuc"] == "stop" else 0
        mx = max(mx, seri)
    net = sum(r["net"] for r in recs)
    return dict(n=n, win=kaz / len(kap) * 100 if kap else 0, net=net, per=net / n if n else 0,
                ay=n / days * 30, gross=sum(r["gross"] for r in recs), seri=mx)


HEAD = ("| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | "
        "Toplam işlem | Dolmayan / elenen | Kazanan | Net R | R/işlem | En uzun stop serisi |\n"
        "|---|---|---|---|---|---|---|---|---|")


class Ctx:
    def __init__(self, b, t_start, t_split, t_end, tr_days, te_days):
        self.b, self.ts, self.tsp, self.te = b, t_start, t_split, t_end
        self.trd, self.ted = tr_days, te_days

    def score(self, tfs, level, cfg):
        """Birden fazla zaman diliminde toplam sonuç."""
        TR, TE, U, E = [], [], 0, 0
        for stf, rej in tfs:
            tr, te, u, e = evaluate(self.b, self.b.gen(stf, rej, level), cfg, self.ts, self.tsp, self.te)
            TR += tr
            TE += te
            U += u
            E += e
        return st(TR, self.trd), st(TE, self.ted), st(TR + TE, self.trd + self.ted), U, E

    def row(self, ad, sc):
        tr, te, al, u, e = sc
        return (f"| {ad} | {tr['n']} / %{tr['win']:.0f} / {tr['net']:+.1f} | {te['n']} / %{te['win']:.0f} / "
                f"{te['net']:+.1f} | {al['n']} (~{al['ay']:.0f}/ay) | {u} / {e} | %{al['win']:.0f} | "
                f"**{al['net']:+.1f}** | {al['per']:+.2f} | {al['seri']} |")


def cfg_ad(cfg):
    parts = [ENTRIES[cfg["entry"]], STOPS[cfg["stop"]], TPS[cfg["tp"]]]
    if cfg["btc"]:
        parts.append("BTC filtresi")
    if cfg["vol"]:
        parts.append("hacim ≥1x")
    parts += [CONFS[c] for c in cfg["conf"]]
    return " · ".join(parts)


def main():
    days = max(30, min(int(os.getenv("PA_BACKTEST", "120") or 120), 150))
    test_days = max(10, min(int(os.getenv("PA_TEST_DAYS", "40") or 40), days - 20))
    data, created = load_data(days)
    t_start, t_split, t_end = created - days * 86400, created - test_days * 86400, created + 86400
    b = Bench(data)
    x = Ctx(b, t_start, t_split, t_end, days - test_days, test_days)
    T0 = time.time()

    out(f"# PA kırılım-retest kapsamlı geçmiş test")
    out(f"Tarih: {time.strftime('%d.%m.%Y %H:%M', time.gmtime(created + 3 * 3600))} (TR). "
        f"{len(data)} coin, son {days} gün: **eğitim ilk {days - test_days} gün**, **doğrulama son {test_days} gün**. "
        f"Seçimler sadece eğitim sonucuna göre yapıldı. Komisyon: maker %{MAKER}, taker %{TAKER}; funding dahil değil. "
        f"\"Kazanan\": stop olmadan kârla kapanan işlem oranı. Limit emir en fazla {p.FILL_BARS} red mumu bekler.")
    out()

    # 0) Seviye tanımı
    out("## 0) Seviye tanımı")
    out(f"Başlangıç ayarı: {cfg_ad(BASE)}. Zaman dilimleri toplamı: {', '.join(f'{a}→{c}' for a, c in DEV_TFS)}")
    out(HEAD)
    best_lv, best_v = None, None
    for lv, ad in LEVELS.items():
        sc = x.score(DEV_TFS, lv, BASE)
        out(x.row(ad, sc))
        save_out()
        if best_v is None or sc[0]["net"] > best_v:
            best_lv, best_v = lv, sc[0]["net"]
    level = best_lv
    out(f"\nSeçilen: **{LEVELS[level]}**\n")

    # 1) TP × stop
    out("## 1) TP × stop (piyasa girişi, filtresiz)")
    rows = []
    for tp in TPS:
        for sp in STOPS:
            cfg = dict(BASE, tp=tp, stop=sp)
            rows.append((tp, sp, x.score(DEV_TFS, level, cfg)))
    rows.sort(key=lambda r: r[2][0]["net"], reverse=True)
    out("Eğitim net R'ına göre sıralı, ilk 25 (tamamı en altta):")
    out(HEAD)
    for tp, sp, sc in rows[:25]:
        out(x.row(f"TP {TPS[tp]} · stop {STOPS[sp]}", sc))
    tp_best, sp_best = rows[0][0], rows[0][1]
    out(f"\nSeçilen: **TP {TPS[tp_best]} · stop {STOPS[sp_best]}**\n")
    out("%10 hedef satırları:")
    out(HEAD)
    for tp, sp, sc in rows:
        if tp == "t_y10":
            out(x.row(f"TP {TPS[tp]} · stop {STOPS[sp]}", sc))
    out()
    save_out()
    cur = dict(BASE, tp=tp_best, stop=sp_best)

    # 2) Giriş × BTC × hacim
    out("## 2) Giriş türü, BTC filtresi, hacim filtresi")
    out(HEAD)
    best = None
    for en in ENTRIES:
        for btc in (False, True):
            for vol in (0.0, 1.0):
                cfg = dict(cur, entry=en, btc=btc, vol=vol)
                sc = x.score(DEV_TFS, level, cfg)
                out(x.row(cfg_ad(cfg), sc))
                if best is None or sc[0]["net"] > best[0]:
                    best = (sc[0]["net"], cfg)
        save_out()
    cur = best[1]
    out(f"\nSeçilen: **{cfg_ad(cur)}**\n")

    # 3) Teyit filtreleri
    out("## 3) Teyit filtreleri")
    out(HEAD)
    base_sc = x.score(DEV_TFS, level, cur)
    out(x.row("teyit yok", base_sc))
    iyi = []
    for c, ad in CONFS.items():
        cfg = dict(cur, conf=(c,))
        sc = x.score(DEV_TFS, level, cfg)
        out(x.row(f"+ {ad}", sc))
        if sc[0]["net"] > base_sc[0]["net"] and sc[0]["n"] >= 30:
            iyi.append((sc[0]["net"], c))
    save_out()
    iyi.sort(reverse=True)
    adaylar = [("teyit yok", ())]
    if iyi:
        adaylar.append((f"en iyi tek: {CONFS[iyi[0][1]]}", (iyi[0][1],)))
    if len(iyi) >= 2:
        adaylar.append(("en iyi iki", tuple(c for _, c in iyi[:2])))
    if len(iyi) >= 3:
        adaylar.append(("eğitimde iyileştiren hepsi", tuple(c for _, c in iyi)))
    best = (base_sc[0]["net"], ())
    for ad, cs in adaylar[1:]:
        sc = x.score(DEV_TFS, level, dict(cur, conf=cs))
        out(x.row(f"{ad} ({', '.join(CONFS[c] for c in cs)})", sc))
        if sc[0]["n"] >= 30 and sc[0]["net"] > best[0]:
            best = (sc[0]["net"], cs)
    cur = dict(cur, conf=best[1])
    out(f"\nSeçilen son ayar: **{cfg_ad(cur)}**\n")
    save_out()

    # 4) Tüm zaman dilimleri
    out(f"## 4) Tüm zaman dilimleri — son ayar ({LEVELS[level]} · {cfg_ad(cur)})")
    out(HEAD)
    for stf, rej in GRID:
        out(x.row(f"{stf}→{rej}", x.score([(stf, rej)], level, cur)))
        save_out()
    out()
    out(f"## 5) Tüm zaman dilimleri — karşılaştırma: başlangıç ayarı ({LEVELS[level]} · {cfg_ad(BASE)})")
    out(HEAD)
    for stf, rej in GRID:
        out(x.row(f"{stf}→{rej}", x.score([(stf, rej)], level, BASE)))
        save_out()
    out()
    out("## Ek: TP × stop tablosunun tamamı")
    out(HEAD)
    for tp, sp, sc in rows:
        out(x.row(f"TP {TPS[tp]} · stop {STOPS[sp]}", sc))
    out()
    out(f"Seçilen ayar (JSON): `{json.dumps(dict(level=level, **{k: (list(v) if isinstance(v, tuple) else v) for k, v in cur.items()}))}`")
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")
    print(f"::notice::Bitti. Seviye: {LEVELS[level]} | {cfg_ad(cur)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        save_out()
