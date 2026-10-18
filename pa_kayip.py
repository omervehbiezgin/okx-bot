"""
Trend stratejisi kayıp analizi: kaybeden ve kazanan işlemleri giriş anındaki özelliklere göre karşılaştırır,
basit filtre adaylarını eğitim döneminde arar, doğrulama döneminde kontrol eder. Mesaj göndermez. Çıktı: kayip_sonuc.md
Kurgu: pa_final ile aynı (03:00 kapanışında giriş, stop seviye − 0,5 ATR, günlük stop 10 gün dibi, BTC filtresiz).
"""
import sys
import time
import bisect
from datetime import datetime

import numpy as np

import pa_final as F

OUT = "kayip_sonuc.md"
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def features(coin, ev, btc):
    D = coin.D
    i = bisect.bisect_left(D["t"], ev["t"] - 86400)
    if i >= len(D["t"]) or D["t"][i] != ev["t"] - 86400 or i < 60:
        return None
    o, h, l, c, v = D["o"][i], D["h"][i], D["l"][i], D["c"][i], D["v"][i]
    a = coin.atr[i]
    d = ev["dir"]
    rng = h - l
    prev_v = D["v"][max(0, i - 20):i]
    e = coin.e50
    f = dict(
        stop_pct=abs((c - (ev["lvl"] - d * 0.5 * a)) / c) * 100,
        mum_boyu=rng / a if a else np.nan,
        govde=abs(c - o) / rng if rng > 0 else 0,
        kirilim_gucu=(c - ev["lvl"]) * d / a,
        hacim=v / np.median(prev_v) if len(prev_v) >= 5 and np.median(prev_v) > 0 else np.nan,
        ema_uzaklik=(c - e[i]) * d / a,
        ema_egim=(e[i] - e[i - 5]) * d / a if e[i - 5] is not None else np.nan,
        getiri20=(c / D["c"][i - 20] - 1) * 100 * d,
        oynaklik=a / c * 100,
        btc_ayni_yon=1.0 if btc.dir_at(ev["t"]) == d else 0.0,
        hafta_sonu=1.0 if datetime.utcfromtimestamp(D["t"][i]).weekday() >= 5 else 0.0,
    )
    return f


AD = {"stop_pct": "stop mesafesi %", "mum_boyu": "kırılım mumu boyu (ATR)", "govde": "kırılım mumu gövde oranı",
      "kirilim_gucu": "kapanışın seviyeyi geçme payı (ATR)", "hacim": "kırılım hacmi / 20 gün ortancası",
      "ema_uzaklik": "EMA50'den uzaklık (ATR)", "ema_egim": "EMA50 eğimi (5 gün, ATR)",
      "getiri20": "son 20 gün getiri % (işlem yönünde)", "oynaklik": "günlük oynaklık (ATR %)",
      "btc_ayni_yon": "BTC aynı yönde (1) / değil (0)", "hafta_sonu": "kırılım hafta sonu (1) / değil (0)"}


def main():
    T0 = time.time()
    data, created = F.T.load()
    t0 = created - F.DAYS * 86400
    t_split = created - F.TEST_DAYS * 86400
    coins = {(k, 0): F.Coin(k, v, 0) for k, v in data.items()}
    btc = F.Btc(coins[("BTC-USDT-SWAP", 0)])
    rows = []
    for c in coins.values():
        for ev in F.events(c, btc):
            if ev["t"] < t0:
                continue
            fz = features(c, ev, btc)
            if fz is None:
                continue
            fl = F.fill(ev, c, 0)
            if fl is None:
                continue
            r = F.sim(ev, c, fl, "don10")
            if not r:
                continue
            rows.append(dict(t=ev["t"], inst=ev["inst"], dir=ev["dir"], net=r[0], gross=r[1], t_out=r[3],
                             vol24=ev["vol24"], **fz))
    rows.sort(key=lambda r: r["t"])
    tr = [r for r in rows if r["t"] < t_split]
    te = [r for r in rows if r["t"] >= t_split]
    out("# Trend stratejisi — kayıp analizi")
    out(f"{len(rows)} işlem (eğitim {len(tr)}, doğrulama {len(te)}). Kurgu: 03:00 girişi, günlük stop 10 gün dibi. "
        "Her özellik eğitim verisinin üçte birlik dilimlerine bölündü; tablo her dilimin işlem başı net R'ını gösterir. "
        "Bir dilim **hem eğitimde hem doğrulamada** belirgin şekilde kötüyse filtre adayıdır.")
    out()
    base_tr = np.mean([r["net"] for r in tr])
    base_te = np.mean([r["net"] for r in te])
    out(f"Ortalama: eğitim {base_tr:+.3f} R/işlem, doğrulama {base_te:+.3f} R/işlem")
    out()
    out("| Özellik | Dilim (eğitim sınırları) | Eğitim: işlem / R/işlem / kazanan | Doğrulama: işlem / R/işlem / kazanan |")
    out("|---|---|---|---|")
    adaylar = []
    for k, ad in AD.items():
        vals = np.array([r[k] for r in tr if np.isfinite(r[k])])
        if len(vals) < 60:
            continue
        if set(np.unique(vals)) <= {0.0, 1.0}:
            cuts = [0.5]
        else:
            cuts = list(np.quantile(vals, [1 / 3, 2 / 3]))
        bounds = [-np.inf] + cuts + [np.inf]
        for b in range(len(bounds) - 1):
            lo, hi = bounds[b], bounds[b + 1]
            g_tr = [r for r in tr if np.isfinite(r[k]) and lo <= r[k] < hi]
            g_te = [r for r in te if np.isfinite(r[k]) and lo <= r[k] < hi]
            if not g_tr:
                continue
            m_tr = np.mean([r["net"] for r in g_tr])
            m_te = np.mean([r["net"] for r in g_te]) if g_te else float("nan")
            w_tr = np.mean([r["gross"] > 0 for r in g_tr]) * 100
            w_te = np.mean([r["gross"] > 0 for r in g_te]) * 100 if g_te else 0
            lab = f"{lo:.2f} – {hi:.2f}".replace("-inf", "…").replace("inf", "…")
            out(f"| {ad} | {lab} | {len(g_tr)} / {m_tr:+.3f} / %{w_tr:.0f} | {len(g_te)} / {m_te:+.3f} / %{w_te:.0f} |")
            if m_tr < base_tr - 0.15 and len(g_tr) >= 80:
                adaylar.append((k, ad, lo, hi, m_tr, m_te))
    out()
    out("## Filtre adayları (eğitimde ortalamanın belirgin altında kalan dilimi çıkarmak)")
    out("| Çıkarılan dilim | Eğitimde o dilim | Doğrulamada o dilim | Filtre sonrası tüm işlemler: eğitim / doğrulama net R | "
        "Portföy %1 × 8: son bakiye / düşüş (filtresiz: aşağıda) |")
    out("|---|---|---|---|---|")
    base_pf = F.portfolio([dict(r, t_sig=r["t"]) for r in rows], 1.0, 8, t0, t_split)
    for k, ad, lo, hi, m_tr, m_te in adaylar:
        kalan = [r for r in rows if not (np.isfinite(r[k]) and lo <= r[k] < hi)]
        s_tr = sum(r["net"] for r in kalan if r["t"] < t_split)
        s_te = sum(r["net"] for r in kalan if r["t"] >= t_split)
        pf = F.portfolio([dict(r, t_sig=r["t"]) for r in kalan], 1.0, 8, t0, t_split)
        tut = "✅ doğrulamada da kötü" if m_te < base_te - 0.1 else "❌ doğrulamada tutmadı"
        out(f"| {ad}: {lo:.2f} – {hi:.2f} | {m_tr:+.3f} R/işlem | {m_te:+.3f} R/işlem ({tut}) | "
            f"{s_tr:+.1f} / {s_te:+.1f} | {pf['son']:.0f} USDT / %{pf['mdd']:.0f} |")
    out(f"\nFiltresiz: tüm işlemler eğitim {sum(r['net'] for r in tr):+.1f} / doğrulama {sum(r['net'] for r in te):+.1f} R · "
        f"portföy {base_pf['son']:.0f} USDT / düşüş %{base_pf['mdd']:.0f}")
    out()
    # Kayıpların yapısı
    los = [r for r in rows if r["gross"] <= 0]
    hold = np.array([(r["t_out"] - r["t"]) / 86400 for r in los])
    out("## Kayıpların yapısı")
    out(f"- Kaybeden işlem: {len(los)} / {len(rows)} (%{len(los) / len(rows) * 100:.0f}). Ortalama kayıp "
        f"{np.mean([r['net'] for r in los]):+.2f}R")
    out(f"- Kaybedenlerin %{np.mean(hold <= 2) * 100:.0f}'ı 2 gün içinde, %{np.mean(hold <= 5) * 100:.0f}'ı 5 gün içinde stop oldu")
    big = sorted(rows, key=lambda r: -r["net"])[:20]
    out(f"- En iyi 20 işlem toplamı {sum(r['net'] for r in big):+.1f}R (tüm işlemler {sum(r['net'] for r in rows):+.1f}R)")
    out(f"\nSüre: {(time.time() - T0) / 60:.0f} dk")


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
