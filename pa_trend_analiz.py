"""
Trend testinde öne çıkan günlük (1D) ayarların gerçekçi koşullarla sağlamlık analizi. Mesaj göndermez.
- "sabah": günlük kapanış TR 03:00'te; giriş 08:00'de piyasa emriyle, günlük stop güncellemesi de 08:00'de.
- Sabit ayarlar (seçim yok) gerçek veri ve karıştırılmış (şans seviyesi) veriyle karşılaştırılır.
Çıktı: trend_analiz.md
"""
import sys
import time
from collections import defaultdict
from datetime import datetime

import pa_trend_bt as T

OUT = "trend_analiz.md"
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


CFGS = []
for entry in ("piyasa", "sabah"):
    for sk in (0.5, 1.0):
        for ex in ("don10", "don20", "tr2", "tr2a", "tp5"):
            exx = ex + "g" if (entry == "sabah" and ex.startswith("don")) else ex
            for fad in ("BTC filtresiz", "btc", "btc+sadece long"):
                CFGS.append((entry, sk, exx, fad))
EXIT_AD = dict(T.EXIT_AD, don10g="günlük stop: 10 gün dibi (sabah güncelle)",
               don20g="günlük stop: 20 gün dibi (sabah güncelle)")


def run(coins, btc, t_start):
    evs = []
    for c in coins.values():
        evs += [e for e in T.events(c, "1D", btc) if e["t"] >= t_start]
    res = {}
    fills = {}
    for entry, sk, ex, fad in CFGS:
        k = (entry, sk)
        if k not in fills:
            ff = [(ev, T.fill(ev, coins[ev["inst"]], entry, sk)) for ev in evs]
            fills[k] = [(ev, f) for ev, f in ff if not isinstance(f, str)]
        rs = []
        for ev, f in fills[k]:
            if not T.passes(ev, T.FILTERS[fad]):
                continue
            r = T.simulate(ev, coins[ev["inst"]], f, ex)
            if r:
                rs.append(r)
        res[(entry, sk, ex, fad)] = rs
    return res


def main():
    T0 = time.time()
    data, created = T.load()
    t_start = created - T.DAYS * 86400
    t_split = created - T.TEST_DAYS * 86400
    coins = {k: T.Coin(k, v) for k, v in data.items()}
    real = run(coins, T.Btc(coins["BTC-USDT-SWAP"]), t_start)
    shs = []
    for seed in (7, 11, 23):
        sh = {k: T.Coin(k, v) for k, v in T.shuffled(data, seed).items()}
        shs.append(run(sh, T.Btc(sh["BTC-USDT-SWAP"]), t_start))
    tr_d, te_d = T.DAYS - T.TEST_DAYS, T.TEST_DAYS

    out("# Günlük trend ayarları — gerçekçi sağlamlık analizi")
    out(f"{len(coins)} coin, 365 gün (eğitim ilk {tr_d} gün, doğrulama son {te_d} gün). "
        "\"sabah\": günlük kapanış 03:00 TR, giriş ve günlük stop güncellemesi 08:00 TR. "
        "Şans seviyesi: aynı sabit ayar, mumları karıştırılmış 3 farklı veri setinde (ortalama). "
        "Portföy: coin başına 1, aynı anda en fazla 5 pozisyon (işlem başı %1 riskte 1R ≈ bakiyenin %1'i).")
    out()
    out("| Ayar | Tüm işlemler: sayı / kazanan / net R | Eğitim net R | Doğrulama net R | Şans seviyesi net R | "
        "Portföy 5: net R (eğitim / doğrulama) | Portföy 5: en büyük düşüş R | Haftada işlem | Ort. tutma |")
    out("|---|---|---|---|---|---|---|---|---|")
    summ = []
    for key, rs in real.items():
        entry, sk, ex, fad = key
        al = T.stats(rs, T.DAYS)
        tr = sum(r["net"] for r in rs if r["t_in"] < t_split)
        te = sum(r["net"] for r in rs if r["t_in"] >= t_split)
        sans = sum(sum(r["net"] for r in s[key]) for s in shs) / len(shs)
        pf, dd = T.portfolio(rs, 5)
        pt = sum(r["net"] for r in pf if r["t_in"] < t_split)
        pv = sum(r["net"] for r in pf if r["t_in"] >= t_split)
        ad = f"{entry} · stop {sk} ATR · {EXIT_AD[ex]} · {fad}"
        summ.append((pt + pv, ad, key, rs, pf, dd))
        out(f"| {ad} | {al['n']} / %{al['win']:.0f} / {al['net']:+.1f} | {tr:+.1f} | {te:+.1f} | {sans:+.1f} | "
            f"{pt + pv:+.1f} ({pt:+.1f} / {pv:+.1f}) | {dd:.1f} | {len(pf) / T.DAYS * 7:.1f} | {al['hold']:.1f} g |")
    out()
    sabah = [x for x in summ if x[2][0] == "sabah"]
    sabah.sort(key=lambda x: x[0], reverse=True)
    out("## Sabah girişli en iyi 3 ayarın ayrıntısı (portföy 5)")
    for tot, ad, key, rs, pf, dd in sabah[:3]:
        out(f"### {ad}")
        L = [r for r in pf if r["dir"] == 1]
        S = [r for r in pf if r["dir"] == -1]
        out(f"- Portföy: {len(pf)} işlem, net {tot:+.1f}R, en büyük düşüş {dd:.1f}R. "
            f"Long {len(L)} işlem {sum(r['net'] for r in L):+.1f}R · Short {len(S)} işlem {sum(r['net'] for r in S):+.1f}R")
        kaz = sum(1 for r in pf if r["gross"] > 0)
        out(f"- Kazanan işlem oranı %{kaz / len(pf) * 100:.0f}, en iyi işlem {max(r['net'] for r in pf):+.1f}R")
        ay = defaultdict(float)
        for r in pf:
            ay[datetime.fromtimestamp(r["t_in"], T.TR).strftime("%Y-%m")] += r["net"]
        out("- Aylık: " + " · ".join(f"{k} {v:+.1f}R" for k, v in sorted(ay.items())))
        artı = sum(1 for v in ay.values() if v > 0)
        out(f"- Artı kapanan ay: {artı}/{len(ay)}")
        en = sorted(pf, key=lambda r: r["net"], reverse=True)[:5]
        out(f"- En iyi 5 işlem olmadan: {tot - sum(r['net'] for r in en):+.1f}R")
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
