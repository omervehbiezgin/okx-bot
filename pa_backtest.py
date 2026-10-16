"""
PA kırılım-retest stratejisi için geçmişe dönük test ve ayar araması.
Telegram'a MESAJ GÖNDERMEZ, canlı botun durum dosyasına dokunmaz.

- 15 dakikalık veri bir kez çekilir (bt_cache.json.gz) ve sonraki çalışmalarda yeniden kullanılır;
  30m, 1H ve 4H mumlar bundan üretilir. İşlemler 15 dakikalık mumlarla takip edilir.
- Komisyon: giriş+çıkış toplamı FEE_PCT (%) her işlemden düşülür (net R).
- Ezber riskine karşı: ayarlar EĞİTİM döneminde (ilk kısım) aranır, sonuç hiç görülmemiş
  DOĞRULAMA döneminde (son TEST_DAYS gün) ölçülür.

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

FEE_PCT = 0.10                 # giriş + çıkış toplam komisyon (%), piyasa emri varsayımı
CACHE = "bt_cache.json.gz"
WARMUP_DAYS = 35
MIN_SIGNALS_TRAIN = 40         # aramada en az bu kadar eğitim sinyali olan ayarlar kabul edilir

REJ_PARAMS = ["TOUCH_TOL", "MIN_AWAY", "WICK_MIN", "CLOSE_HALF", "MAX_PIERCE", "MIN_RR", "MIN_STOP_PCT"]
SEARCH = [
    ("TOUCH_TOL", [0.1, 0.15, 0.25, 0.35]),
    ("MIN_AWAY", [0.3, 0.5, 1.0, 1.5]),
    ("WICK_MIN", [0.2, 0.3, 0.5]),
    ("CLOSE_HALF", [0.35, 0.5]),
    ("MAX_PIERCE", [0.25, 0.5, 1.0]),
    ("MIN_RR", [1.5, 2.0, 2.5, 3.0]),
    ("MIN_STOP_PCT", [0.3, 0.5, 0.8]),
    ("S.k", [2, 3, 5]),
    ("S.retest", [12, 30, 60]),
    ("S.top_age", [45, 90, 150]),
]


def note(t):
    print("::notice::" + t, flush=True)


# ---------------- Veri ----------------
def fetch_retry(inst, bar, sec, n):
    for deneme in range(5):
        try:
            return p.fetch(inst, bar, sec, n)
        except Exception as e:
            print(f"{inst} deneme {deneme + 1}: {e}", flush=True)
            time.sleep(2 + deneme * 2)
    return None


def load_data(days):
    try:
        with gzip.open(CACHE, "rt") as f:
            c = json.load(f)
        if c.get("days") == days and time.time() - c["created"] < 2 * 86400 and c["data"]:
            print(f"Önbellekteki veri kullanılıyor ({len(c['data'])} coin).", flush=True)
            return c["data"], c["created"]
    except Exception:
        pass
    symbols = p.get_symbols()
    n = (days + WARMUP_DAYS) * 96
    print(f"{len(symbols)} coin için 15m veri çekiliyor ({n} mum)...", flush=True)

    def one(inst):
        s = fetch_retry(inst, "15m", 900, n)
        time.sleep(0.2)
        return inst, s

    data = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        for inst, s in ex.map(one, symbols):
            if s and len(s["t"]) > 96 * (WARMUP_DAYS + 7):
                data[inst] = s
    created = time.time()
    with gzip.open(CACHE, "wt") as f:
        json.dump({"days": days, "created": created, "data": data}, f)
    return data, created


# ---------------- Değerlendirme ----------------
class Bench:
    def __init__(self, data):
        self.s15 = data
        self.series = {}     # (inst, tf) -> seri
        self.atr = {}        # (inst, tf) -> atr dizisi
        self.piv = {}        # (inst, k) -> 4H pivotlar
        self.dmap = {}       # (inst, tf) -> her red mumu için son kapanmış 4H indeksi
        self.setups = {}     # (inst, yapı ayarları) -> {D: kurulumlar}

    def ser(self, inst, tf):
        key = (inst, tf)
        if key not in self.series:
            s = self.s15[inst]
            self.series[key] = s if tf == "15m" else p.aggregate(s, p.TF[tf][1])
            self.atr[key] = p.atr_arr(self.series[key])
        return self.series[key], self.atr[key]

    def run(self, rej, t0, t1):
        cfg = p.STRUCT[p.STRUCT_TF]
        skey = (cfg["k"], cfg["look"], cfg["top_age"], cfg["retest"], p.MIN_AWAY)
        sigs = []
        for inst in self.s15:
            d, datr = self.ser(inst, p.STRUCT_TF)
            x, xatr = self.ser(inst, rej)
            pk = (inst, cfg["k"])
            if pk not in self.piv:
                self.piv[pk] = p.pivots(d["h"], d["l"], 0, len(d["t"]) - 1, cfg["k"])
            mk = (inst, rej)
            if mk not in self.dmap:
                self.dmap[mk] = [p.last_day_before(d, t) for t in x["t"]]
            dm = self.dmap[mk]
            sc = self.setups.setdefault((inst,) + skey, {})
            j0 = bisect.bisect_left(x["t"], t0)
            j1 = bisect.bisect_left(x["t"], t1)
            used = set()
            for j in range(j0, j1):
                D = dm[j]
                if D not in sc:
                    sc[D] = p.setups_at(d, D, datr, self.piv[pk])
                sts, highs, lows = sc[D]
                for st in sts:
                    if st["key"] in used:
                        continue
                    g = p.check_reject(x, j, xatr, st, highs, lows)
                    if g:
                        used.add(st["key"])
                        g["inst"] = inst
                        g["R"], g["sonuc"] = simulate(g, self.s15[inst])
                        g["net"] = g["R"] - FEE_PCT / g["stop_pct"]
                        sigs.append(g)
        return sigs


def simulate(g, s):
    """TP1'de yarısı kapanır ve stop girişe çekilir. Sonuç R cinsinden (komisyonsuz)."""
    d, e, sl, tp1, tp2 = g["dir"], g["entry"], g["sl"], g["tp1"], g["tp2"]
    R = abs(e - sl)
    half = False
    for j in range(bisect.bisect_left(s["t"], g["t"]), len(s["t"])):
        adv = s["l"][j] if d == 1 else s["h"][j]
        fav = s["h"][j] if d == 1 else s["l"][j]
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
    acik = (s["c"][-1] - e) * d / R
    return (0.5 + 0.5 * acik if half else acik), "açık"


def stats(sigs, days):
    n = len(sigs)
    kap = [g for g in sigs if g["sonuc"] != "açık"]
    stop = sum(1 for g in kap if g["sonuc"] == "stop")
    gross = sum(g["R"] for g in sigs)
    net = sum(g["net"] for g in sigs)
    return dict(n=n, tp1=(len(kap) - stop) / len(kap) * 100 if kap else 0, gross=gross, net=net,
                per=net / n if n else 0, ay=n / days * 30,
                stop=sum(g["stop_pct"] for g in sigs) / n if n else 0)


def fmt(s):
    return (f"{s['n']} sinyal (~{s['ay']:.0f}/ay), TP1+ %{s['tp1']:.0f}, brüt {s['gross']:+.1f}R, "
            f"net {s['net']:+.1f}R ({s['per']:+.2f}R/işlem), ort. stop %{s['stop']:.2f}")


def get_param(k):
    return p.STRUCT[p.STRUCT_TF][k[2:]] if k.startswith("S.") else getattr(p, k)


def set_param(k, v):
    if k.startswith("S."):
        p.STRUCT[p.STRUCT_TF][k[2:]] = v
    else:
        setattr(p, k, v)


def snapshot():
    return {k: get_param(k) for k, _ in SEARCH}


def restore(sn):
    for k, v in sn.items():
        set_param(k, v)


def search(bench, rej, t0, t1, days):
    """Koordinat araması: her ayarı sırayla dener, eğitim net R'ını en çok artıranı tutar (2 tur)."""
    best = stats(bench.run(rej, t0, t1), days)["net"]
    for tur in range(2):
        degisti = False
        for k, vals in SEARCH:
            cur = get_param(k)
            for v in vals:
                if v == cur:
                    continue
                set_param(k, v)
                st = stats(bench.run(rej, t0, t1), days)
                if st["n"] >= MIN_SIGNALS_TRAIN and st["net"] > best + 0.5:
                    best, cur, degisti = st["net"], v, True
                set_param(k, cur)
            print(f"  {rej} tur {tur + 1}: {k} = {cur} (eğitim net {best:+.1f}R)", flush=True)
        if not degisti:
            break
    return snapshot()


def main():
    days = max(30, min(int(os.getenv("PA_BACKTEST", "120") or 120), 150))
    test_days = max(10, min(int(os.getenv("PA_TEST_DAYS", "40") or 40), days - 20))
    data, created = load_data(days)
    now = created
    t_start, t_split, t_end = now - days * 86400, now - test_days * 86400, now + 86400
    tr_days, te_days = days - test_days, test_days
    note(f"Veri: {len(data)} coin, son {days} gün (eğitim {tr_days} gün + doğrulama {te_days} gün), "
         f"komisyon %{FEE_PCT} giriş+çıkış")

    p.STRUCT_TF = "4H"
    base = snapshot()
    base_rej = {k: getattr(p, k) for k in REJ_PARAMS}
    bench = Bench(data)

    for rej in ("15m", "30m", "1H"):
        tr = stats(bench.run(rej, t_start, t_split), tr_days)
        te = stats(bench.run(rej, t_split, t_end), te_days)
        note(f"4H→{rej} MEVCUT AYAR | eğitim: {fmt(tr)} || doğrulama: {fmt(te)}")

    for rej in ("30m", "15m"):
        restore(base)
        for k, v in base_rej.items():
            setattr(p, k, v)
        print(f"\n=== 4H→{rej} ayar araması ===", flush=True)
        opt = search(bench, rej, t_start, t_split, tr_days)
        tr = stats(bench.run(rej, t_start, t_split), tr_days)
        te = stats(bench.run(rej, t_split, t_end), te_days)
        degisen = {k: v for k, v in opt.items() if v != base[k]}
        note(f"4H→{rej} OPTİMİZE {json.dumps(degisen)} | eğitim: {fmt(tr)} || doğrulama: {fmt(te)}")
        allp = stats(bench.run(rej, t_start, t_end), days)
        note(f"4H→{rej} OPTİMİZE tüm {days} gün: {fmt(allp)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("HATA:", e)
        sys.exit(1)
