"""
Efloud "Mixed Price Action" (MPA) kurgusunun kural tabanlı geçmiş testi (2 yıl, 15m veri). Mesaj göndermez.
Çıktı: mpa_sonuc.md

Kurallar (videolardan derlendi; takdire bağlı kısımlar için birden çok seçenek denenir):
  Yön (günlük)  : son günlük dip bir öncekinden yüksek ve kapanış onun üstünde → long (short tersi). Kapatılabilir.
  Bölge         : (1) günlük eski tepe/dip (destek-direnç dönüşümü), (2) günlük/4H açık FVG, (3) haftalık açılış,
                  önceki haftalık açılış, aylık açılış, (4) son günlük salınımın OTE'si (0,618–0,786).
                  Süpürülen dip en az 'need' farklı unsurun bölgesinde olmalı (1 veya 2).
  Onay (15m/1H) : son onaylı küçük dip süpürülür → sonra son onaylı küçük tepenin üstünde kapanış (yapı değişimi).
  Giriş         : e1 kırılım mumu kapanışı | e2 kırılan tepeye (breaker) limit | e3 OTE 0,705'e limit | e4 yarısı e1
                  yarısı e2. Limitler 6 saat geçerli.
  Stop          : süpürülen dibin altı (küçük zaman dilimi ATR'sinin 0,1'i kadar tampon). Stop %0,3–%8.
  Hedef         : TP1 = küçük zaman dilimindeki karşı likidite (en yakın onaylı tepe, en az 1R). TP1 1,5R'den
                  yakınsa işlem yok (kötü R:R). TP2 = sonraki büyük seviye (günlük tepe / haftalık-aylık açılış).
  Yönetim       : m1 %50 TP1 + stop girişe, %25 TP2, %25 kalan | m2 %90 TP1, %10 kalan (stop girişe) |
                  m3 tek hedef TP1 | m4 %50 TP1 + stop girişe, %50 TP2. En uzun 10 gün.
  Filtreler     : BTC günlük yönü, seans (07:00 TR sonrası, manipülasyon sonrası), hafta sonu hariç.
Maliyet: maker %0,02 (limit, TP), taker %0,05 + %0,05 kayma (piyasa giriş, stop), long funding 8 saatte %0,01.
Eğitim: ilk 485 gün, doğrulama: son 245 gün. Seçim sadece eğitime göre.
"""
import os
import sys
import time
import bisect
import random
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import pa_scan_once as p

DAYS, WARM, TEST_DAYS = 730, 75, 245
CACHE = "mpa_cache.npz"
OUT = "mpa_sonuc.md"
MAX_COINS = 50
MAKER, TAKER, SLIP, FUND = 0.02, 0.05, 0.05, 0.01
K_LTF, K_D = 3, 3
TR = timezone(timedelta(hours=3))
START = 100.0
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


def first_true(b):
    if b.size == 0:
        return None
    i = int(np.argmax(b))
    return i if b[i] else None


# ---------------- Veri ----------------
def fetch_retry(inst, n):
    for d in range(8):
        try:
            return p.fetch(inst, "15m", 900, n)
        except Exception as e:
            print(f"{inst} deneme {d + 1}: {e}", flush=True)
            time.sleep(3 + 4 * d)
    return None


def load():
    if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 3 * 86400:
        z = np.load(CACHE, allow_pickle=False)
        insts = [str(x) for x in z["insts"]]
        data = {k: {f: z[f"{i}_{f}"] for f in ("t", "o", "h", "l", "c", "v")} for i, k in enumerate(insts)}
        print(f"Önbellekte {len(data)} coin.", flush=True)
        return data, float(z["created"])
    syms = p.get_symbols()[:MAX_COINS]
    if "BTC-USDT-SWAP" not in syms:
        syms.insert(0, "BTC-USDT-SWAP")
    n = (DAYS + WARM) * 96
    created = time.time()
    print(f"{len(syms)} coin için {n} adet 15m mum çekiliyor...", flush=True)

    def one(inst):
        s = fetch_retry(inst, n)
        time.sleep(0.2)
        if not s or len(s["t"]) < 96 * 120:
            return inst, None
        j = bisect.bisect_right(s["t"], created)
        return inst, {f: np.array(s[f][:j], dtype=np.int64 if f == "t" else np.float64)
                      for f in ("t", "o", "h", "l", "c", "v")}

    data = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        for k, (inst, s) in enumerate(ex.map(one, syms)):
            if s is not None:
                data[inst] = s
            print(f"  {k + 1}/{len(syms)} {inst} ({time.time() - t0:.0f} sn)", flush=True)
    arrs = {"insts": np.array(list(data)), "created": np.array(created)}
    for i, (k, s) in enumerate(data.items()):
        for f, a in s.items():
            arrs[f"{i}_{f}"] = a
    np.savez_compressed(CACHE, **arrs)
    return data, created


def agg(s, sec, off=0):
    t = s["t"]
    key = (t - off) // sec
    idx = np.flatnonzero(np.diff(key)) + 1
    starts = np.concatenate(([0], idx))
    ends = np.concatenate((idx, [len(t)]))
    need = sec // 900
    full = (ends - starts) == need
    st, en = starts[full], ends[full]
    return dict(t=key[st] * sec + off, o=s["o"][st], h=np.maximum.reduceat(s["h"], starts)[full],
                l=np.minimum.reduceat(s["l"], starts)[full], c=s["c"][en - 1],
                v=np.add.reduceat(s["v"], starts)[full], sec=sec)


def atr(h, l, c, n=14):
    pc = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out_ = np.full(len(c), np.nan)
    if len(c) > n:
        cs = np.cumsum(tr)
        out_[n:] = (cs[n:] - cs[:-n]) / n
    return out_


def pivots(h, l, k):
    n = len(h)
    ph, pl = np.zeros(n, bool), np.zeros(n, bool)
    for i in range(k, n - k):
        w = h[i - k:i + k + 1]
        if h[i] == w.max() and h[i] > h[i - k:i].max():
            ph[i] = True
        w = l[i - k:i + k + 1]
        if l[i] == w.min() and l[i] < l[i - k:i].min():
            pl[i] = True
    return ph, pl


# ---------------- Coin hazırlığı (yön işaretiyle: short için fiyatlar −1 ile çarpılır) ----------------
class Side:
    def __init__(self, raw, sgn, btc_bias_day=None):
        self.sgn = sgn
        s = dict(raw)
        if sgn == 1:
            o, h, l, c = raw["o"], raw["h"], raw["l"], raw["c"]
        else:
            o, h, l, c = -raw["o"], -raw["l"], -raw["h"], -raw["c"]
        self.t = raw["t"]
        self.o, self.h, self.l, self.c = o, h, l, c
        s15 = dict(t=raw["t"], o=o, h=h, l=l, c=c, v=raw["v"])
        self.cs_v = np.concatenate(([0.0], np.cumsum(raw["v"])))
        self.D = agg(s15, 86400)
        self.H4 = agg(s15, 14400)
        self.H1 = agg(s15, 3600)
        D = self.D
        self.datr = atr(D["h"], D["l"], D["c"])  # işaretli seride de aralık aynı
        self.ltf_ph = {}
        self.Dt_close = D["t"] + 86400
        # günlük pivotlar (destek-direnç ve yön)
        dph, dpl = pivots(D["h"], D["l"], K_D)
        self.d_piv = []                     # (onay zamanı, fiyat)
        for i in np.flatnonzero(dph | dpl):
            if i + K_D < len(D["t"]):
                tc = int(D["t"][i + K_D] + 86400)
                if dph[i]:
                    self.d_piv.append((tc, float(D["h"][i]), "H", i))
                if dpl[i]:
                    self.d_piv.append((tc, float(D["l"][i]), "L", i))
        self.d_piv.sort()
        self.dp_t = np.array([x[0] for x in self.d_piv], dtype=np.int64)
        self.dp_p = np.array([x[1] for x in self.d_piv])
        self.dp_k = np.array([x[2] for x in self.d_piv])
        # günlük yön (bias): her gün kapanışında
        nD = len(D["t"])
        bias = np.zeros(nD, int)
        lows, highs = [], []
        pi = 0
        for d in range(nD):
            tc = D["t"][d] + 86400
            while pi < len(self.d_piv) and self.d_piv[pi][0] <= tc:
                (lows if self.d_piv[pi][2] == "L" else highs).append(self.d_piv[pi][1])
                pi += 1
            if len(lows) >= 2 and lows[-1] > lows[-2] and D["c"][d] > lows[-1]:
                bias[d] = 1
            elif len(highs) >= 2 and highs[-1] < highs[-2] and D["c"][d] < highs[-1]:
                bias[d] = -1
        self.bias = bias
        # FVG'ler (işaretli seride "yukarı" boşluklar): günlük ve 4H
        self.fvg = []                       # (onay zamanı, alt, üst, dolma zamanı, max yaş sn)
        for S, maxage in ((D, 60 * 86400), (self.H4, 20 * 86400)):
            hh, ll, tt, sec = S["h"], S["l"], S["t"], S["sec"]
            for i in range(2, len(tt)):
                if ll[i] > hh[i - 2]:
                    lo, hi = hh[i - 2], ll[i]
                    tc = int(tt[i] + sec)
                    later = ll[i + 1:]
                    k = first_true(later <= lo)
                    tf = int(tt[i + 1 + k]) if k is not None else 2 ** 62
                    self.fvg.append((tc, lo, hi, tf, maxage))
        self.fvg.sort()
        self.fv = np.array(self.fvg) if self.fvg else np.zeros((0, 5))
        # haftalık / aylık açılışlar
        W = agg(s15, 604800, 345600)
        self.W_t, self.W_o = W["t"], W["o"]
        mkeys = np.array([datetime.fromtimestamp(int(x), timezone.utc).year * 12 +
                          datetime.fromtimestamp(int(x), timezone.utc).month for x in D["t"]])
        firsts = np.flatnonzero(np.concatenate(([True], np.diff(mkeys) != 0)))
        self.M_t, self.M_o = D["t"][firsts], D["o"][firsts]

    def day_idx(self, t):
        return int(np.searchsorted(self.Dt_close, t, side="right")) - 1

    def datr_at(self, t):
        d = self.day_idx(t)
        return self.datr[d] if d >= 0 else np.nan

    def bias_at(self, t):
        d = self.day_idx(t)
        return self.bias[d] if d >= 0 else 0

    def confluence(self, P, t):
        """Fiyat P, t anında kaç farklı unsurun bölgesinde?"""
        a = self.datr_at(t)
        if not np.isfinite(a):
            return 0
        n = 0
        # 1) günlük eski tepe/dip
        j = int(np.searchsorted(self.dp_t, t, side="right"))
        if j:
            tt, pp = self.dp_t[:j], self.dp_p[:j]
            m = (t - tt <= 180 * 86400) & (np.abs(pp - P) <= 0.25 * a)
            n += int(m.any())
        # 2) açık FVG
        if len(self.fv):
            f = self.fv
            m = (f[:, 0] <= t) & (f[:, 3] > t) & (t - f[:, 0] <= f[:, 4]) & (P >= f[:, 1] - 0.1 * a) & (P <= f[:, 2])
            n += int(m.any())
        # 3) haftalık / önceki haftalık / aylık açılış
        w = int(np.searchsorted(self.W_t, t, side="right")) - 1
        lv = []
        if w >= 0:
            lv.append(self.W_o[w])
        if w >= 1:
            lv.append(self.W_o[w - 1])
        mi = int(np.searchsorted(self.M_t, t, side="right")) - 1
        if mi >= 0:
            lv.append(self.M_o[mi])
        n += int(any(abs(x - P) <= 0.15 * a for x in lv))
        # 4) OTE: son onaylı günlük dipten sonraki en yüksek tepeye göre 0,618–0,786
        d = self.day_idx(t)
        if j and d >= 0:
            ks = self.dp_k[:j]
            Ls = np.flatnonzero(ks == "L")
            if len(Ls):
                L = self.dp_p[Ls[-1]]
                i0 = self.d_piv[Ls[-1]][3]
                if i0 <= d:
                    H = self.D["h"][i0:d + 1].max()
                    if H - L >= 2 * a:
                        lo, hi = H - 0.786 * (H - L), H - 0.618 * (H - L)
                        n += int(lo <= P <= hi)
        return n

    def htf_targets(self, t, above):
        """t anında 'above' üstündeki büyük seviyeler (günlük pivotlar + açılışlar), artan sırada."""
        j = int(np.searchsorted(self.dp_t, t, side="right"))
        lv = list(self.dp_p[:j][(t - self.dp_t[:j] <= 365 * 86400)])
        w = int(np.searchsorted(self.W_t, t, side="right")) - 1
        if w >= 0:
            lv.append(self.W_o[w])
        if w >= 1:
            lv.append(self.W_o[w - 1])
        mi = int(np.searchsorted(self.M_t, t, side="right")) - 1
        if mi >= 0:
            lv.append(self.M_o[mi])
        return sorted(x for x in lv if x > above)


# ---------------- Kurulum tespiti (küçük zaman dilimi) ----------------
def setups(side, ltf):
    """İşaretli seride long kurulumları: süpürme → yapı değişimi."""
    S = {"15m": dict(t=side.t, o=side.o, h=side.h, l=side.l, c=side.c, sec=900), "1H": side.H1}[ltf]
    t, h, l, c = S["t"], S["h"], S["l"], S["c"]
    sec = S["sec"]
    n = len(t)
    if n < 200:
        return []
    a_ltf = atr(h, l, c)
    ph, pl = pivots(h, l, K_LTF)
    idx = np.flatnonzero(ph)
    side.ltf_ph[ltf] = (idx, h[idx], t + sec)
    maxw = 48 if ltf == "15m" else 24
    res = []
    lastPL = lastPH = None          # (indeks, fiyat)
    armed = None                    # dict(sweep_low, start, conf)
    for j in range(K_LTF + 1, n):
        i = j - K_LTF
        if pl[i]:
            lastPL = (i, l[i])
        if ph[i]:
            lastPH = (i, h[i])
        tj = int(t[j] + sec)
        if armed is not None:
            if j - armed["start"] > maxw:
                armed = None
            else:
                if l[j] < armed["low"]:
                    armed["low"] = l[j]
                    armed["lowj"] = j
                if lastPH is not None and lastPH[0] < j and c[j] > lastPH[1] and c[j - 1] <= lastPH[1] \
                        and lastPH[0] >= armed["start"] - 60:
                    hi = h[armed["lowj"]:j + 1].max()
                    res.append(dict(t=tj, j=j, low=armed["low"], close=c[j], brk=lastPH[1], hi=hi,
                                    atr=a_ltf[j] if np.isfinite(a_ltf[j]) else (h[j] - l[j]), conf=armed["conf"],
                                    ltf=ltf))
                    armed = None
                    continue
        if armed is None and lastPL is not None and l[j] < lastPL[1] and lastPL[0] < j:
            conf = side.confluence(l[j], tj)
            if conf >= 1:
                armed = dict(low=l[j], lowj=j, start=j, conf=conf)
            lastPL = None           # bu dip süpürüldü
    return res


def ltf_targets(side, ltf, t, above, R):
    """Küçük zaman dilimindeki karşı likidite: t anında onaylı, son 400 (15m) / 200 (1H) mumdaki,
    girişin en az 1R üstündeki en yakın tepe."""
    idx, val, tclose = side.ltf_ph[ltf]
    j = int(np.searchsorted(tclose, t, side="right"))      # t anına kadar kapanmış mum sayısı
    look = 400 if ltf == "15m" else 200
    m = (idx + K_LTF < j) & (idx >= j - look) & (val >= above + R)
    return float(val[m].min()) if m.any() else None


# ---------------- İşlem simülasyonu (15m mumlarla) ----------------
def sim_trade(side, su, entry, mgmt):
    t15, o, h, l, c = side.t, side.o, side.h, side.l, side.c
    n = len(t15)
    j0 = int(np.searchsorted(t15, su["t"]))
    if j0 >= n:
        return None
    stop = su["low"] - 0.1 * su["atr"]
    legs = []
    if entry in ("e1", "e4"):
        legs.append(("mkt", su["close"], j0, 0.5 if entry == "e4" else 1.0))
    if entry in ("e2", "e3", "e4"):
        lvl = su["brk"] if entry in ("e2", "e4") else su["hi"] - 0.705 * (su["hi"] - su["low"])
        if lvl <= stop:
            return None
        end = min(n, j0 + 24)
        k = first_true(l[j0:end] <= lvl)
        if k is not None:
            legs.append(("lim", lvl, j0 + k, 0.5 if entry == "e4" else 1.0))
        elif entry != "e4":
            return "dolmadi"
    if not legs:
        return None
    res_net, res_gross, t_out, kaz = 0.0, 0.0, 0, False
    base_R = None
    for kind, e, jf, w in legs:
        R = e - stop
        if R <= 0:
            return None
        sp = R / abs(e) * 100
        if sp < 0.3 or sp > 8:
            return None
        if base_R is None:
            base_R = (e, R)
        tp1 = ltf_targets(side, su["ltf"], su["t"], e, R)
        if tp1 is None:
            tl = side.htf_targets(su["t"], e + R)
            tp1 = tl[0] if tl else None
        if tp1 is None or tp1 - e < 1.5 * R:
            return None
        tl = side.htf_targets(su["t"], tp1 + 0.5 * R)
        tp2 = tl[0] if tl else tp1 + (tp1 - e)
        tp3 = tp2 + (tp2 - e)
        a = jf + (1 if kind == "lim" else 0)
        b = min(n, a + 960)
        if a >= b:
            return None
        H, L, O, C = h[a:b], l[a:b], o[a:b], c[a:b]
        fee_in = TAKER + SLIP if kind == "mkt" else MAKER
        if kind == "lim" and l[jf] <= stop:
            g, fo, k_end = -1.0, TAKER + SLIP, jf - a
            nets = [(1.0, g, fo, max(k_end, 0))]
        else:
            ks = first_true(L <= stop)
            k1 = first_true(H >= tp1)

            def after(k_from, lvl_stop, tp):
                """k_from sonrasında: stop lvl_stop mu, hedef tp mi önce?"""
                if k_from is None:
                    return None
                Hs, Ls = H[k_from + 1:], L[k_from + 1:]
                kb = first_true(Ls <= lvl_stop)
                kt = first_true(Hs >= tp) if tp is not None else None
                if kb is not None and (kt is None or kb <= kt):
                    px = min(O[k_from + 1 + kb], lvl_stop)
                    return ((px - e) / R, TAKER + SLIP, k_from + 1 + kb)
                if kt is not None:
                    return ((tp - e) / R, MAKER, k_from + 1 + kt)
                return ((C[-1] - e) / R, TAKER + SLIP, len(C) - 1)

            if ks is not None and (k1 is None or ks <= k1):
                px = min(O[ks], stop)
                nets = [(1.0, (px - e) / R, TAKER + SLIP, ks)]
            elif k1 is None:
                nets = [(1.0, (C[-1] - e) / R, TAKER + SLIP, len(C) - 1)]
            else:
                r1 = (tp1 - e) / R
                if mgmt == "m3":
                    nets = [(1.0, r1, MAKER, k1)]
                elif mgmt == "m4":
                    g2 = after(k1, e, tp2)
                    nets = [(0.5, r1, MAKER, k1), (0.5,) + g2]
                elif mgmt == "m2":
                    g2 = after(k1, e, tp2)
                    nets = [(0.9, r1, MAKER, k1), (0.1,) + g2]
                else:  # m1
                    g2 = after(k1, e, tp2)
                    nets = [(0.5, r1, MAKER, k1), (0.25,) + g2]
                    if g2[1] == MAKER:                  # TP2 alındıysa kalan: stop TP1'e, hedef TP3
                        g3 = after(g2[2], tp1, tp3)
                        nets.append((0.25,) + g3)
                    else:
                        nets.append((0.25,) + g2)
        for frac, g, fo, k in nets:
            hours = (a + k - jf + 1) / 4
            fund = FUND * hours / 8 if side.sgn == 1 else 0.0
            res_net += w * frac * (g - (fee_in + fo + fund) / sp)
            res_gross += w * frac * g
            t_out = max(t_out, int(t15[min(a + k, n - 1)]))
    return dict(net=res_net, gross=res_gross, t_out=t_out)


# ---------------- Değerlendirme ----------------
def build(coins, btc_bias, ltf_list=("15m", "1H")):
    """Tüm kurulumlar: {(ltf): [(coin, side, setup)]}"""
    S = {lt: [] for lt in ltf_list}
    for inst, raw in coins.items():
        for sgn in (1, -1):
            side = Side(raw, sgn)
            for lt in ltf_list:
                for su in setups(side, lt):
                    su["inst"], su["dir"] = inst, sgn
                    su["bias"] = side.bias_at(su["t"])
                    su["btc"] = btc_bias(su["t"]) * sgn
                    su["vol24"] = float(side.cs_v[int(np.searchsorted(side.t, su["t"]))] -
                                        side.cs_v[max(0, int(np.searchsorted(side.t, su["t"])) - 96)])
                    S[lt].append((side, su))
        print(f"  kurulumlar: {inst} ({sum(len(v) for v in S.values())})", flush=True)
    return S


def trades(S, ltf, entry, mgmt, need, use_bias, t0, cache):
    key = (ltf, entry, mgmt)
    if key not in cache:
        rs = []
        unf = 0
        for side, su in S[ltf]:
            if su["t"] < t0:
                continue
            r = sim_trade(side, su, entry, mgmt)
            if r == "dolmadi":
                unf += 1
                continue
            if r:
                r.update(inst=su["inst"], dir=su["dir"], t_sig=su["t"], vol24=su["vol24"], conf=su["conf"],
                         bias=su["bias"], btc=su["btc"])
                rs.append(r)
        rs.sort(key=lambda r: (r["t_sig"], -r["vol24"]))
        cache[key] = (rs, unf)
    rs, unf = cache[key]
    return [r for r in rs if r["conf"] >= need and (not use_bias or r["bias"] == 1)], unf


def flt(rs, btc=False, seans=False, hsonu=False):
    outl = []
    for r in rs:
        if btc and r["btc"] != 1:
            continue
        dt = datetime.fromtimestamp(r["t_sig"], TR)
        if seans and dt.hour < 7:
            continue
        if hsonu and dt.weekday() >= 5:
            continue
        outl.append(r)
    return outl


def st(rs, t_split):
    n = len(rs)
    tr = sum(r["net"] for r in rs if r["t_sig"] < t_split)
    te = sum(r["net"] for r in rs if r["t_sig"] >= t_split)
    ntr = sum(1 for r in rs if r["t_sig"] < t_split)
    win = sum(1 for r in rs if r["gross"] > 0.001) / n * 100 if n else 0
    return dict(n=n, ntr=ntr, win=win, tr=tr, te=te, tot=tr + te, per=(tr + te) / n if n else 0)


def portfolio(rs, risk, maxn, t0, t_split):
    groups = defaultdict(list)
    for r in rs:
        groups[r["t_sig"]].append(r)
    bal = peak = low = START
    mdd = 0.0
    acik, alinan = [], []
    bal_split = None
    curve = []

    def close_until(tm):
        nonlocal bal, peak, low, mdd, bal_split
        acik.sort(key=lambda x: x[0])
        while acik and acik[0][0] <= tm:
            to, r, ru = acik.pop(0)
            if bal_split is None and to >= t_split:
                bal_split = bal
            bal += ru * r["net"]
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
            low = min(low, bal)
            curve.append((to, bal))

    for tm in sorted(groups):
        close_until(tm)
        if bal_split is None and tm >= t_split:
            bal_split = bal
        if bal < 60:
            continue
        for r in sorted(groups[tm], key=lambda r: -r["vol24"]):
            if len(acik) >= maxn or any(x[1]["inst"] == r["inst"] for x in acik):
                continue
            acik.append((r["t_out"], r, bal * risk / 100))
            alinan.append(r)
    close_until(float("inf"))
    if bal_split is None:
        bal_split = bal
    return dict(son=bal, mdd=mdd, low=low, n=len(alinan), egit=(bal_split / START - 1) * 100,
                dogr=(bal / bal_split - 1) * 100, curve=curve, alinan=alinan)


def shuffle_data(coins, seed):
    rng = np.random.default_rng(seed)
    outd = {}
    for k, s in coins.items():
        c = s["c"]
        prev = np.concatenate(([s["o"][0]], c[:-1]))
        r = np.stack([s["o"] / prev, s["h"] / prev, s["l"] / prev, c / prev], 1)
        idx = rng.permutation(len(c))
        r = r[idx]
        pc = s["o"][0] * np.cumprod(r[:, 3])
        pp = np.concatenate(([s["o"][0]], pc[:-1]))
        outd[k] = dict(t=s["t"], o=pp * r[:, 0], h=pp * r[:, 1], l=pp * r[:, 2], c=pc, v=s["v"][idx])
    return outd


ENT = {"e1": "kırılım kapanışı", "e2": "breaker'a limit", "e3": "OTE 0,705'e limit", "e4": "yarısı kırılım + yarısı breaker"}
MGT = {"m1": "%50 TP1 + BE, %25 TP2, %25 kalan", "m2": "%90 TP1, %10 kalan (BE)", "m3": "tek hedef TP1",
       "m4": "%50 TP1 + BE, %50 TP2"}


def main():
    T0 = time.time()
    data, created = load()
    t0 = created - DAYS * 86400
    t_split = created - TEST_DAYS * 86400
    btc_side = Side(data["BTC-USDT-SWAP"], 1)
    btc_bias = lambda tm: btc_side.bias_at(tm)
    S = build(data, btc_bias)
    print(f"Hazırlık {time.time() - T0:.0f} sn", flush=True)
    out("# Efloud MPA kurgusu — kural tabanlı 2 yıllık test")
    out(f"{len(data)} coin, 15m veri. Eğitim {datetime.fromtimestamp(t0, TR):%d.%m.%Y} – "
        f"{datetime.fromtimestamp(t_split, TR):%d.%m.%Y}, doğrulama son {TEST_DAYS} gün. Seçimler sadece eğitime göre. "
        "\"Kazanan\": kârla kapanan işlem oranı (kısmi kâr + başa baş dahil, brüt > 0). Komisyon, kayma ve funding dahil.")
    out()
    HEAD = ("| Ayar | İşlem | Kazanan | Tüm işlemler net R | Eğitim / doğrulama net R | R/işlem | "
            "Portföy %2 × 4: son / en büyük düşüş |\n|---|---|---|---|---|---|---|")
    cache = {}
    rows = []
    for ltf in ("15m", "1H"):
        for entry in ENT:
            for mgmt in MGT:
                for need in (1, 2):
                    for ub in (False, True):
                        rs, unf = trades(S, ltf, entry, mgmt, need, ub, t0, cache)
                        s = st(rs, t_split)
                        rows.append(((ltf, entry, mgmt, need, ub), s, rs))
        print(f"{ltf} bitti ({time.time() - T0:.0f} sn)", flush=True)

    def ad(k):
        ltf, entry, mgmt, need, ub = k
        return f"{ltf} onay · {ENT[entry]} · {MGT[mgmt]} · bölge ≥{need} unsur · {'günlük yön filtreli' if ub else 'yön filtresiz'}"

    def row(k, s, rs):
        pf = portfolio(rs, 2.0, 4, t0, t_split)
        return (f"| {ad(k)} | {s['n']} | %{s['win']:.0f} | {s['tot']:+.1f} | {s['tr']:+.1f} / {s['te']:+.1f} | "
                f"{s['per']:+.2f} | {pf['son']:.0f} USDT / %{pf['mdd']:.0f} |")

    el = sorted([x for x in rows if x[1]["ntr"] >= 50], key=lambda x: -x[1]["tr"])
    out("## 1) Eğitim dönemine göre en iyi 20 ayar (128 ayar denendi)")
    out(HEAD)
    for k, s, rs in el[:20]:
        out(row(k, s, rs))
    save()
    out()
    out("## 2) Her boyutun etkisi (o seçeneği içeren en iyi ayar, eğitime göre)")
    out(HEAD)
    for idx, opts in ((0, ("15m", "1H")), (1, tuple(ENT)), (2, tuple(MGT)), (3, (1, 2)), (4, (False, True))):
        for op in opts:
            c = [x for x in el if x[0][idx] == op]
            if c:
                out(row(*c[0]))
    out()
    hw = sorted(rows, key=lambda x: -x[1]["win"])[:5]
    out("## 3) Kazanan oranı en yüksek 5 ayar (%70 iddiasını kontrol)")
    out(HEAD)
    for k, s, rs in hw:
        out(row(k, s, rs))
    save()

    if not el:
        out("Yeterli işlem yok.")
        return
    bk, bs, brs = el[0]
    # 4) Filtreler
    out()
    out(f"## 4) Filtreler — seçilen ayar: {ad(bk)}")
    out(HEAD.replace("Ayar", "Filtreler"))
    best_f = None
    for btc in (False, True):
        for seans in (False, True):
            for hs in (False, True):
                rs = flt(brs, btc, seans, hs)
                s = st(rs, t_split)
                nm = ", ".join(x for x, y in (("BTC yönü", btc), ("07:00 sonrası", seans), ("hafta sonu yok", hs)) if y) or "filtre yok"
                pf = portfolio(rs, 2.0, 4, t0, t_split)
                out(f"| {nm} | {s['n']} | %{s['win']:.0f} | {s['tot']:+.1f} | {s['tr']:+.1f} / {s['te']:+.1f} | "
                    f"{s['per']:+.2f} | {pf['son']:.0f} USDT / %{pf['mdd']:.0f} |")
                if s["ntr"] >= 50 and (best_f is None or s["tr"] > best_f[0]):
                    best_f = (s["tr"], (btc, seans, hs), rs, nm)
    _, fset, frs, fnm = best_f
    out(f"\nSeçilen filtre: **{fnm}**\n")
    save()

    # 5) Portföy / risk
    out("## 5) Portföy ve risk (100 USDT, bileşik)")
    out("| Risk × en fazla pozisyon | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | En düşük bakiye | İşlem |")
    out("|---|---|---|---|---|---|")
    pfs = {}
    for risk, maxn in ((2.0, 4), (2.0, 6), (1.0, 8), (1.0, 6)):
        pf = portfolio(frs, risk, maxn, t0, t_split)
        pfs[(risk, maxn)] = pf
        out(f"| %{risk:g} × {maxn} | {pf['son']:.0f} USDT | %{pf['egit']:+.0f} / %{pf['dogr']:+.0f} | %{pf['mdd']:.0f} | "
            f"{pf['low']:.0f} USDT | {pf['n']} |")
    save()

    # 6) Şans seviyesi
    out()
    out("## 6) Şans seviyesi (mumları karıştırılmış 15m veri, aynı ayar ve filtre)")
    sk = []
    for seed in (7, 11):
        sh = shuffle_data(data, seed)
        bs_side = Side(sh["BTC-USDT-SWAP"], 1)
        S2 = build(sh, lambda tm: bs_side.bias_at(tm), (bk[0],))
        rs2, _ = trades(S2, bk[0], bk[1], bk[2], bk[3], bk[4], t0, {})
        sk.append(st(flt(rs2, *fset), t_split)["tot"])
    gs = st(frs, t_split)
    out(f"- Gerçek veri: {gs['n']} işlem, net **{gs['tot']:+.1f}R**, kazanan %{gs['win']:.0f}. Karışık veri: " +
        ", ".join(f"{x:+.1f}R" for x in sk))
    save()

    # 7) Trend stratejisiyle birlikte
    out()
    out("## 7) Trend stratejisiyle birlikte (her biri ayrı 50 USDT, %1 × 8)")
    try:
        import pa_final as F
        fdata, fcreated = F.T.load()
        fcoins = {(k, 0): F.Coin(k, v, 0) for k, v in fdata.items()}
        fbtc = F.Btc(fcoins[("BTC-USDT-SWAP", 0)])
        fev = []
        for cc in fcoins.values():
            fev += F.events(cc, fbtc)
        trs = F.trades_for(fcoins, fev, 0, "don10", False)
        p_tr = F.portfolio(trs, 1.0, 8, t0, t_split)
        p_mp = portfolio(frs, 1.0, 8, t0, t_split)

        def eq_at(curve, tm):
            b = START
            for to, bb in curve:
                if to > tm:
                    break
                b = bb
            return b

        days = np.arange(t0, created, 86400)
        e1 = np.array([eq_at(p_tr["curve"], d) for d in days])
        e2 = np.array([eq_at(p_mp["curve"], d) for d in days])
        comb = 0.5 * e1 + 0.5 * e2
        pk = np.maximum.accumulate(comb)
        mdd = ((pk - comb) / pk).max() * 100
        m1 = e1[::30]
        m2 = e2[::30]
        r1, r2 = np.diff(m1) / m1[:-1], np.diff(m2) / m2[:-1]
        cor = float(np.corrcoef(r1, r2)[0, 1]) if len(r1) > 3 else float("nan")
        out(f"- Trend tek başına: 100 → {p_tr['son']:.0f} USDT, düşüş %{p_tr['mdd']:.0f}")
        out(f"- MPA tek başına (%1 × 8): 100 → {p_mp['son']:.0f} USDT, düşüş %{p_mp['mdd']:.0f}")
        out(f"- **Birlikte (50 + 50):** 100 → {comb[-1]:.0f} USDT, en büyük düşüş %{mdd:.0f}. Aylık getirilerin korelasyonu "
            f"{cor:+.2f} (0'a yakın = farklı zamanlarda kazanıyorlar)")
    except Exception as e:
        out(f"- Birlikte hesap yapılamadı: {e}")
    out()
    out(f"Süre: {(time.time() - T0) / 60:.0f} dk")
    save()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        save()
