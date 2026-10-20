"""
EMA ile kısa vadeli (15m / 30m / 1H) hızlı işlem testi, sabit TP hedefli. 2 yıl, 50 coin. Mesaj göndermez, emir vermez.
Çıktı: ema_sonuc.md

Sinyaller (giriş zaman diliminde, mum kapanışında):
  cross    : hızlı EMA yavaş EMA'yı keser (yukarı → long, aşağı → short)
  pullback : trend (hızlı > yavaş) varken mum hızlı EMA'ya değer ve onun üstünde, yeşil kapanır (short tersi);
             aynı coinde 3 mum içinde tekrar sinyal yok
EMA çiftleri: 9/21, 20/50
Yön filtresi: yok | 1H kapanış EMA50'nin doğru tarafında | 4H kapanış EMA50'nin doğru tarafında
Stop: ema = yavaş EMA ∓ 0,3 ATR | swing = son 5 mumun dibi/tepesi ∓ 0,2 ATR | atr = giriş ∓ 1 ATR (stop %0,3–%5)
Hedef: TP 1R / 1,5R / 2R / 3R / yok (sadece stop veya süre). En uzun 48 mum (giriş zaman diliminde).
Giriş: kapanıştan sonraki 15m mumun açılışında piyasa emri (hızlı giriş).
Maliyet: giriş taker %0,05 + %0,02 kayma | TP maker %0,02 | stop taker %0,05 + %0,05 kayma | süre çıkışı %0,05 + %0,02.
Aynı 15m mumda hem TP hem stop görülürse stop sayılır (ihtiyatlı).
Seçim sadece eğitim döneminde (ilk 485 gün); doğrulama son 245 gün. Şans kontrolü: aynı giriş anları, rastgele yön.
Portföy: 1000 USDT, işlem başı %1 risk, en fazla 8 açık pozisyon, coin başına 1 pozisyon, bileşik.
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

import pa_mpa as M

OUT = "ema_sonuc.md"
DAYS, TEST_DAYS = 730, 245
TAKER, MAKER, SLIP_IN, SLIP_SL = 0.05, 0.02, 0.02, 0.05
TPS = [1.0, 1.5, 2.0, 3.0, None]
TFS = {900: "15m", 1800: "30m", 3600: "1H"}
PAIRS = [(9, 21), (20, 50)]
FILTERS = ["yok", "1H", "4H"]
STOPS = ["ema", "swing", "atr"]
SIGS = ["cross", "pullback"]
MAXH = 48
MIN_SP, MAX_SP = 0.3, 5.0
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def save():
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")


def ema(c, n):
    o = np.empty(len(c))
    k = 2 / (n + 1)
    e = c[0]
    for i, x in enumerate(c):
        e = x * k + e * (1 - k)
        o[i] = e
    o[:n] = np.nan
    return o


class Coin:
    def __init__(self, inst, s):
        self.inst = inst
        self.b = s                                        # 15m taban mumlar
        self.tf = {}
        for sec in TFS:
            S = s if sec == 900 else M.agg(s, sec)
            S = {k: np.asarray(v) for k, v in S.items() if k != "sec"}
            S["atr"] = M.atr(S["h"], S["l"], S["c"])
            S["ema"] = {n: ema(S["c"], n) for n in (9, 20, 21, 50)}
            self.tf[sec] = S
        self.htf = {}
        for sec in (3600, 14400):
            H = M.agg(s, sec)
            self.htf[sec] = (np.asarray(H["t"]) + sec, np.asarray(H["c"]), ema(np.asarray(H["c"]), 50))

    def htf_dir(self, sec, t_end):
        te, c, e = self.htf[sec]
        j = np.searchsorted(te, t_end, side="right") - 1
        out_ = np.zeros(len(t_end))
        ok = j >= 0
        jj = j[ok]
        v = np.where(np.isnan(e[jj]), 0, np.sign(c[jj] - e[jj]))
        out_[ok] = v
        return out_


def signals(cn, sec, sig, pair):
    S = cn.tf[sec]
    f, s_ = S["ema"][pair[0]], S["ema"][pair[1]]
    c, o, h, l = S["c"], S["o"], S["h"], S["l"]
    n = len(c)
    d = np.zeros(n, dtype=np.int8)
    if sig == "cross":
        up = (f > s_) & (np.roll(f, 1) <= np.roll(s_, 1))
        dn = (f < s_) & (np.roll(f, 1) >= np.roll(s_, 1))
        d[up] = 1
        d[dn] = -1
    else:
        up = (f > s_) & (l <= f) & (c > f) & (c > o)
        dn = (f < s_) & (h >= f) & (c < f) & (c < o)
        d[up] = 1
        d[dn] = -1
        last = -10
        for i in np.flatnonzero(d):
            if i - last <= 3:
                d[i] = 0
            else:
                last = i
    d[:60] = 0
    d[np.isnan(S["atr"]) | np.isnan(s_)] = 0
    return np.flatnonzero(d), d


def trades_for(cn, sec, sig, pair, filt, stop_kind, t0, rnd=None):
    """Her sinyal için giriş, stop ve her TP seviyesinin sonucu (net R)."""
    S, B = cn.tf[sec], cn.b
    idx, darr = signals(cn, sec, sig, pair)
    if len(idx) == 0:
        return []
    t_end = S["t"][idx] + sec
    keep = t_end >= t0
    idx, t_end = idx[keep], t_end[keep]
    if filt != "yok":
        hd = cn.htf_dir(3600 if filt == "1H" else 14400, t_end)
        keep = hd == darr[idx]
        idx, t_end = idx[keep], t_end[keep]
    bt = B["t"]
    j0s = np.searchsorted(bt, t_end)
    W = MAXH * (sec // 900)
    res = []
    for i, j0 in zip(idx, j0s):
        if j0 >= len(bt) - 2:
            continue
        d = int(darr[i])
        e = float(B["o"][j0])
        a = float(S["atr"][i])
        if stop_kind == "ema":
            stop = S["ema"][pair[1]][i] - d * 0.3 * a
        elif stop_kind == "swing":
            stop = (S["l"][max(0, i - 4):i + 1].min() - 0.2 * a) if d == 1 else (S["h"][max(0, i - 4):i + 1].max() + 0.2 * a)
        else:
            stop = e - d * a
        if (e - stop) * d <= 0:
            continue
        risk = abs(e - stop)
        sp = risk / e * 100
        if sp < MIN_SP or sp > MAX_SP:
            continue
        if rnd is not None:                       # şans kontrolü: aynı an, aynı mesafe, rastgele yön
            d = rnd.choice((1, -1))
            stop = e - d * risk
        H, L, C = B["h"][j0:j0 + W], B["l"][j0:j0 + W], B["c"][j0:j0 + W]
        if len(H) == 0:
            continue
        hit_s = (L <= stop) if d == 1 else (H >= stop)
        js = int(np.argmax(hit_s)) if hit_s.any() else None
        c_in = (TAKER + SLIP_IN) / sp
        outs = {}
        for m in TPS:
            if m is None:
                jt = None
            else:
                tp = e + d * m * risk
                hit_t = (H >= tp) if d == 1 else (L <= tp)
                jt = int(np.argmax(hit_t)) if hit_t.any() else None
            if jt is not None and (js is None or jt < js):
                net, j = m - c_in - MAKER / sp, jt
            elif js is not None:
                net, j = -1 - c_in - (TAKER + SLIP_SL) / sp, js
            else:
                j = len(C) - 1
                net = (C[j] - e) * d / risk - c_in - (TAKER + SLIP_IN) / sp
            outs[m] = (net, int(bt[j0 + j]) + 900)
        res.append(dict(inst=cn.inst, t_in=int(bt[j0]), d=d, sp=sp, outs=outs))
    return res


def stats(rs, m, t_split):
    tr = [r["outs"][m][0] for r in rs if r["t_in"] < t_split]
    te = [r["outs"][m][0] for r in rs if r["t_in"] >= t_split]
    al = tr + te
    win = np.mean([x > 0 for x in al]) * 100 if al else 0
    return dict(n=len(al), ntr=len(tr), nte=len(te), win=win, tr=sum(tr), te=sum(te),
                per_tr=np.mean(tr) if tr else 0, per_te=np.mean(te) if te else 0)


def portfolio(rs, m, t_split, start=1000.0, risk=1.0, maxn=8):
    rows = sorted(rs, key=lambda r: r["t_in"])
    bal = peak = start
    mdd = 0.0
    acik = []
    bal_split = None
    for r in rows:
        acik.sort(key=lambda x: x[0])
        while acik and acik[0][0] <= r["t_in"]:
            t_out, net, ru, _ = acik.pop(0)
            if bal_split is None and t_out >= t_split:
                bal_split = bal
            bal += ru * net
            peak = max(peak, bal)
            mdd = max(mdd, (peak - bal) / peak * 100)
        if bal_split is None and r["t_in"] >= t_split:
            bal_split = bal
        if bal <= start * 0.3:
            break
        if len(acik) >= maxn or any(x[3] == r["inst"] for x in acik):
            continue
        net, t_out = r["outs"][m]
        acik.append((t_out, net, bal * risk / 100, r["inst"]))
    for t_out, net, ru, _ in sorted(acik):
        bal += ru * net
        peak = max(peak, bal)
        mdd = max(mdd, (peak - bal) / peak * 100)
    bal_split = bal_split or bal
    return dict(son=bal, mdd=mdd, egit=(bal_split / start - 1) * 100, dogr=(bal / bal_split - 1) * 100)


def main():
    T0 = time.time()
    if os.path.exists(M.CACHE):                 # önbellekteki 2 yıllık veri yaşına bakılmadan kullanılır
        os.utime(M.CACHE, None)
    data, created = M.load()
    t0 = created - DAYS * 86400
    t_split = created - TEST_DAYS * 86400
    coins = [Coin(k, v) for k, v in data.items()]
    out("# EMA ile hızlı işlem testi (15m / 30m / 1H, sabit TP)")
    out(f"{len(coins)} coin, 2 yıl. Eğitim ilk {DAYS - TEST_DAYS} gün, doğrulama son {TEST_DAYS} gün; seçim sadece eğitime "
        f"göre. Giriş kapanıştan sonra piyasa emriyle. Maliyet: giriş %{TAKER}+%{SLIP_IN}, TP %{MAKER}, stop "
        f"%{TAKER}+%{SLIP_SL}. Aynı mumda TP ve stop görülürse stop sayıldı. Hazırlık {time.time() - T0:.0f} sn.")
    out()
    allres = {}
    rows = []
    for sec in TFS:
        for sig in SIGS:
            for pair in PAIRS:
                for filt in FILTERS:
                    for sk in STOPS:
                        rs = []
                        for cn in coins:
                            rs += trades_for(cn, sec, sig, pair, filt, sk, t0)
                        key = (sec, sig, pair, filt, sk)
                        allres[key] = rs
                        for m in TPS:
                            s = stats(rs, m, t_split)
                            rows.append((key, m, s))
                        print(f"{TFS[sec]} {sig} {pair} {filt} {sk}: {len(rs)} işlem ({time.time() - T0:.0f} sn)", flush=True)

    def lab(key, m):
        sec, sig, pair, filt, sk = key
        return (f"{TFS[sec]} · {sig} {pair[0]}/{pair[1]} · filtre {filt} · stop {sk} · "
                f"{'TP ' + str(m) + 'R' if m else 'TP yok'}")

    def row(key, m, s):
        return (f"| {lab(key, m)} | {s['n']} / %{s['win']:.0f} | {s['per_tr']:+.3f} | {s['per_te']:+.3f} | "
                f"{s['tr']:+.0f} / {s['te']:+.0f} |")

    head = ("| Ayar | İşlem / kazanan | Eğitim R/işlem | Doğrulama R/işlem | Eğitim / doğrulama toplam R |\n"
            "|---|---|---|---|---|")
    elig = [x for x in rows if x[2]["ntr"] >= 300]
    pos_tr = sum(1 for x in elig if x[2]["per_tr"] > 0)
    pos_both = sum(1 for x in elig if x[2]["per_tr"] > 0 and x[2]["per_te"] > 0)
    out(f"Toplam {len(rows)} ayar denendi; eğitimde en az 300 işlemi olan {len(elig)} ayarın {pos_tr} tanesi eğitimde, "
        f"{pos_both} tanesi hem eğitimde hem doğrulamada artıda.")
    out()
    out("## Zaman dilimine göre ortalama (tüm ayarlar)")
    out("| Zaman dilimi | Ayar sayısı | Ortalama eğitim R/işlem | Ortalama doğrulama R/işlem | Ortalama kazanan % |")
    out("|---|---|---|---|---|")
    for sec in TFS:
        xs = [x for x in elig if x[0][0] == sec]
        if xs:
            out(f"| {TFS[sec]} | {len(xs)} | {np.mean([x[2]['per_tr'] for x in xs]):+.3f} | "
                f"{np.mean([x[2]['per_te'] for x in xs]):+.3f} | %{np.mean([x[2]['win'] for x in xs]):.0f} |")
    out()
    out("## TP seviyesine göre ortalama (tüm ayarlar)")
    out("| Hedef | Ortalama eğitim R/işlem | Ortalama doğrulama R/işlem | Ortalama kazanan % |")
    out("|---|---|---|---|")
    for m in TPS:
        xs = [x for x in elig if x[1] == m]
        if xs:
            out(f"| {'TP ' + str(m) + 'R' if m else 'TP yok'} | {np.mean([x[2]['per_tr'] for x in xs]):+.3f} | "
                f"{np.mean([x[2]['per_te'] for x in xs]):+.3f} | %{np.mean([x[2]['win'] for x in xs]):.0f} |")
    out()
    best = sorted(elig, key=lambda x: -x[2]["per_tr"] * np.sqrt(x[2]["ntr"]))[:15]
    out("## Eğitime göre en iyi 15 ayar ve doğrulamadaki sonuçları")
    out(head)
    for key, m, s in best:
        out(row(key, m, s))
    out()
    for sec in TFS:
        xs = sorted([x for x in elig if x[0][0] == sec], key=lambda x: -x[2]["per_tr"] * np.sqrt(x[2]["ntr"]))[:3]
        out(f"### {TFS[sec]} için eğitimde en iyi 3")
        out(head)
        for key, m, s in xs:
            out(row(key, m, s))
        out()
    out("## Portföy (1000 USDT, %1 risk, en fazla 8 pozisyon) ve şans kontrolü — eğitime göre en iyi 5 ayar")
    out("| Ayar | Son bakiye | En büyük düşüş | Eğitim / doğrulama getiri | Rastgele yön R/işlem (5 deneme) | "
        "Gerçek R/işlem |")
    out("|---|---|---|---|---|---|")
    for key, m, s in best[:5]:
        pf = portfolio(allres[key], m, t_split)
        rr = []
        for seed in range(5):
            rnd = random.Random(seed)
            rs = []
            for cn in coins:
                rs += trades_for(cn, *key, t0, rnd=rnd)
            rr.append(np.mean([r["outs"][m][0] for r in rs]) if rs else 0)
        real = np.mean([r["outs"][m][0] for r in allres[key]])
        out(f"| {lab(key, m)} | {pf['son']:.0f} | %{pf['mdd']:.0f} | {pf['egit']:+.0f}% / {pf['dogr']:+.0f}% | "
            f"{np.mean(rr):+.3f} (en iyi {max(rr):+.3f}) | {real:+.3f} |")
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
        save()
