"""
Sinyal geçmiş testi 2 (sinyal_bt2.py) - kullanıcının işlem kurallarıyla, 100 $ bakiye simülasyonu.

Veri ve sinyal kuralları sinyal_bt.py ile ortak (botla birebir aynı). Telegram'a mesaj göndermez.

KIRILIM (15m, 1H: hacme göre ilk 100 coin, 120 gün | 4H, 1D: bütün coinler, 2 yıl)
  Yön filtresi: long ancak kapanış günlük EMA200 VEYA haftalık EMA21 üstündeyse; short tersi
  Giriş: A) kırılan bant çizgisine limit  B) bant ortasına limit
  Stop : bandın öbür ucu + bant genişliğinin %10'u
  Gruplar: ana (⚠️ hariç) | ana, sadece 2-3 yıldız | 0-1 yıldız (⚠️ hariç) | ⚠️ (ana stratejiye katılmaz)
FVG'DEN DÖNÜŞ (bütün coinler, 2 yıl)
  Giriş: A) tepki çizgisi (destekte üst, dirençte alt çizgi) B) FVG ortası; EMA filtresi var / yok
  Stop : FVG'nin öbür ucu + 0.1 x günlük ATR
EMA21 HAFTALIK (bütün coinler, bütün geçmiş)
  Giriş: A) en yakın günlük FVG sınırı B) EMA21 çizgisi (her hafta güncellenir)
  Stop : kesişim mumunun dibi / tepesi VEYA FVG'nin öbür ucu (+ 0.1 x günlük ATR)
RSI (günlük, haftalık; bütün coinler, bütün geçmiş)
  Giriş: A) RSI 30 üstünde (short: 70 altında) kapanınca B) + RSI'ın SMA14'ünü kesmesi (-2..+5 mum)
  Stop : dönüş sırasındaki en uç fiyat + 0.1 x ATR
Hepsinde: iz süren stop yok | 1R'de başa baş + 1.5/2/3 x ATR | 1R geriden (EMA21: yok | 1R kârdan sonra 1R geriden)
          kâr al 2R | fiyat %10 lehe (10x kaldıraçta teminatın iki katı); emir bekleme süreleri karşılaştırılır.
Bakiye: 100 $, her işlemde risk 1 $, kaldıraç 10x; teminat (pozisyon / 10) yetmezse işlem atlanır,
        stop mesafesi %9'dan büyükse (likidasyon stoptan önce gelir) işlem açılmaz.
"""
import os
import time
import bisect
import json

import numpy as np

import sinyal_bt as S
from sinyal_bt import DAY, TF_SEC, arr, atr, ema, simulate, ozet, out, lines

# Mod: 10x / 5x / 3x (vadeli, kaldıraç) ya da spot (sadece long, kaldıraçsız, spot ücretleri)
MOD = os.getenv("BT_MOD", "10x")
SPOT = MOD == "spot"
OUT_MD, OUT_JSON = f"sinyal_sonuc_{MOD}.md", f"sinyal_sonuc_{MOD}.json"
if SPOT:                                      # OKX spot normal seviye: maker %0.08, taker %0.10
    S.FEE_MAKER, S.FEE_TAKER = 0.0008, 0.0010
GUN2 = 730
DOG = {"15m": 30, "1H": 30, "4H": 180, "1D": 180, "FVG": 180, "EMA": 180, "RSI": 180}
BAKIYE, RISK = 100.0, 1.0
KALDIRAC = 1 if SPOT else int(MOD.rstrip("x"))
LIKIT = 10.0 if SPOT else 0.9 / KALDIRAC      # stop mesafesi bundan büyükse likidasyon stoptan önce gelir
SECILEN = {}                                  # bölüm -> (en iyi ayarın işlemleri, eğitim özeti, ayar adı)

IZLER = [("yok", 0), ("be", 1.5), ("be", 2.0), ("be", 3.0), ("r1", 0)]
TPLER = os.getenv("BT_TPLER", "2R %10").split()       # ör. "%10 %20 %33 2R 3R yok"
TUM = {}                                              # bölüm -> bütün ayarların işlemleri


def hedef(tp, giris, stop, yon):
    if tp == "yok":
        return None
    if tp.endswith("R"):
        return giris + float(tp[:-1]) * abs(giris - stop) * yon
    pct = float(tp.lstrip("%")) / 100
    return giris * (1 + pct * yon) if yon == 1 else giris / (1 + pct)   # short: %100 = fiyatın yarısı


def calistir(sinyaller, fn):
    """Aynı coinde aynı anda tek işlem; stop mesafesi %9'dan büyük işlemler açılmaz (likidasyon)."""
    sonuc, mesgul = [], -1
    for sg in sinyaller:
        if sg["t"] < mesgul or (SPOT and sg["yon"] == -1):     # spotta short yok
            continue
        r = fn(sg)
        if r is None:
            mesgul = sg.get("emir_bitis", sg["t"])
            if "emir_bitis" in sg:                      # dolmayan emir: tek işlem testinde emir süresi boyunca yer tutar
                sonuc.append(dict(bos=True, t=sg["t"], bitis=sg["emir_bitis"], inst=sg.get("inst"), yon=sg["yon"]))
            continue
        if r["risk_pct"] >= LIKIT:
            mesgul = r["cikis_t"]
            continue
        for k, v in sg.items():
            if k not in r and not isinstance(v, (list, dict, np.ndarray)):
                r[k] = v
        sonuc.append(r)
        mesgul = r["cikis_t"]
    return sonuc


def bakiye_sim(islemler, t_bas=None):
    """100 $ bakiye, işlem başına 1 $ risk, 10x; teminat yetmezse işlem atlanır."""
    isl = sorted([x for x in islemler if t_bas is None or x["giris_t"] >= t_bas], key=lambda x: x["giris_t"])
    bakiye, acik, alinan, atlanan, en_cok = BAKIYE, [], 0, 0, 0
    tepe, dd, en_dusuk = BAKIYE, 0.0, BAKIYE
    for x in isl:
        kapanan = [a for a in acik if a[0] <= x["giris_t"]]
        for a in sorted(kapanan):
            bakiye += a[2]
            tepe = max(tepe, bakiye)
            dd = max(dd, tepe - bakiye)
            en_dusuk = min(en_dusuk, bakiye)
        acik = [a for a in acik if a[0] > x["giris_t"]]
        if bakiye <= 0:
            break
        teminat = RISK / x["risk_pct"] / KALDIRAC
        if teminat > bakiye - sum(a[1] for a in acik):
            atlanan += 1
            continue
        acik.append((x["cikis_t"], teminat, x["R"] * RISK))
        alinan += 1
        en_cok = max(en_cok, len(acik))
    for a in sorted(acik):
        bakiye += a[2]
        tepe = max(tepe, bakiye)
        dd = max(dd, tepe - bakiye)
        en_dusuk = min(en_dusuk, bakiye)
    return dict(son=bakiye, alinan=alinan, atlanan=atlanan, dd=dd, en_dusuk=en_dusuk, en_cok=en_cok)


def tablo(baslik, satirlar):
    out(f"\n#### {baslik}\n")
    out("| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | "
        "Son dönem kazanan | Son dönem PF | En kötü seri |")
    out("|---|---|---|---|---|---|---|---|---|---|")
    for ad, ze, zd in satirlar:
        def f(z, k, fmt):
            return fmt.format(z[k]) if z.get("n") and z.get(k) is not None else "-"
        out(f"| {ad}{' ⚠️az' if ze.get('n', 0) < 30 else ''} | {ze.get('n', 0)} | {f(ze, 'ortR', '{:+.2f}')} | "
            f"{f(ze, 'kazanan', '{:.0%}')} | {f(ze, 'pf', '{:.2f}')} | {zd.get('n', 0)} | "
            f"{f(zd, 'ortR', '{:+.2f}')} | {f(zd, 'kazanan', '{:.0%}')} | {f(zd, 'pf', '{:.2f}')} | {ze.get('seri', '-')} |")


def bakiye_satiri(ad, b):
    out(f"| {ad} | {b['alinan']} | {b['atlanan']} | {b['son']:.1f} $ | {b['son'] - BAKIYE:+.1f} $ | "
        f"{b['dd']:.1f} $ | {b['en_dusuk']:.1f} $ | {b['en_cok']} |")


def bolum(baslik, varyantlar, t_split, gruplar=None, ozellikler=None, sonuc=None):
    """varyantlar: {ad: işlemler}. En iyi 12 ayarı ve en iyisinin bakiye simülasyonunu yazar."""
    tum_varyant = varyantlar
    varyantlar = {ad: [x for x in isl if not x.get("bos")] for ad, isl in varyantlar.items()}
    satir = []
    for ad, isl in varyantlar.items():
        egit = [x for x in isl if x["t"] < t_split]
        dog = [x for x in isl if x["t"] >= t_split]
        satir.append((ad, ozet(egit, len(egit)), ozet(dog, len(dog))))
    satir.sort(key=lambda x: (x[1].get("n", 0) >= 30, x[1].get("ortR", -99)), reverse=True)
    tablo(f"{baslik}: eğitim dönemine göre en iyi 12 ayar", satir[:12])
    if sonuc is not None:
        sonuc[baslik] = {ad: dict(egitim=ze, dogrulama=zd) for ad, ze, zd in satir}
    if not satir or not satir[0][1].get("n"):
        return None
    en_iyi = satir[0][0]
    isl = varyantlar[en_iyi]
    SECILEN[baslik] = (isl, satir[0][1], en_iyi, tum_varyant[en_iyi])
    TUM[baslik] = tum_varyant
    out(f"\n**{baslik} — en iyi ayar: {en_iyi}**\n")
    out("| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |")
    out("|---|---|---|---|---|---|---|---|")
    bakiye_satiri("Tüm dönem (100 $ ile başlayarak)", bakiye_sim(isl))
    bakiye_satiri("Sadece son dönem (100 $ ile başlayarak)", bakiye_sim(isl, t_split))
    if ozellikler:
        parca = []
        for ad, f in ozellikler:
            alt = [x for x in isl if f(x)]
            parca.append((ad, ozet([x for x in alt if x["t"] < t_split], 0), ozet([x for x in alt if x["t"] >= t_split], 0)))
        tablo(f"{baslik} — en iyi ayar, sinyal özelliklerine göre", parca)
    return en_iyi


def tek_sim(kayitlar, max_acik, mod, t_bas=None):
    """Aynı anda en fazla max_acik işlem.
    mod 'a': bekleyen emirler serbest, ilk dolan alınır (doluşta yer yoksa atlanır).
    mod 'b': emir verildiği andan (sinyal) işlem kapanana / emir iptal olana kadar yer tutar; yer yoksa sinyal atlanır."""
    if t_bas is not None:
        kayitlar = [x for x in kayitlar if x["t"] >= t_bas]
    bakiye, acik, alinan, atlanan, tepe, dd, en_dusuk = BAKIYE, [], 0, 0, BAKIYE, 0.0, BAKIYE
    if mod == "a":
        olaylar = sorted([x for x in kayitlar if not x.get("bos")], key=lambda x: x["giris_t"])
        an = lambda x: x["giris_t"]
    else:
        olaylar = sorted(kayitlar, key=lambda x: x["t"])
        an = lambda x: x["t"]
    for x in olaylar:
        simdi = an(x)
        for a in sorted([a for a in acik if a[0] <= simdi]):
            bakiye += a[2]
            tepe = max(tepe, bakiye)
            dd = max(dd, tepe - bakiye)
            en_dusuk = min(en_dusuk, bakiye)
        acik = [a for a in acik if a[0] > simdi]
        if len(acik) >= max_acik or any(a[3] == x.get("inst") for a in acik):
            if not x.get("bos"):
                atlanan += 1
            continue
        if x.get("bos"):                                  # mod b: dolmayan emir, süresi boyunca yer tutar
            acik.append((x["bitis"], 0.0, 0.0, x.get("inst")))
            continue
        teminat = RISK / x["risk_pct"] / KALDIRAC
        if teminat > bakiye - sum(a[1] for a in acik):
            atlanan += 1
            continue
        acik.append((x["cikis_t"], teminat, x["R"] * RISK, x.get("inst")))
        alinan += 1
    for a in sorted(acik):
        bakiye += a[2]
        tepe = max(tepe, bakiye)
        dd = max(dd, tepe - bakiye)
        en_dusuk = min(en_dusuk, bakiye)
    return dict(son=bakiye, alinan=alinan, atlanan=atlanan, dd=dd, en_dusuk=en_dusuk)


def tek_islem_bolumu(adaylar, now):
    t_bas2, t_split2 = now - GUN2 * DAY, now - 180 * DAY
    out("\n## 6) Aynı anda sınırlı işlem (tek işlem / en fazla 3 işlem)\n\n"
        "a = bekleyen limit emirler serbest, ilk dolan alınır, yer yoksa dolan emir iptal sayılır. "
        "b = emir verildiği andan işlem kapanana (ya da emir iptal olana) kadar yer tutar, o sırada gelen sinyaller atlanır. "
        "Atlanan = yer olmadığı için alınmayan işlem. Hepsi 100 $ ile başlar, işlem başına 1 $ risk.\n")
    gruplar = [(b_, [x for x in SECILEN[b_][3] if x["t"] >= t_bas2]) for b_ in adaylar if b_ in SECILEN]
    birlikte = []
    for b_, k in gruplar:
        birlikte += k
    gruplar.append(("HEPSİ BİRLİKTE", birlikte))
    ikili = [x for b_, k in gruplar if b_ in ("EMA21 haftalık", "FVG — EMA filtreli") for x in k]
    if ikili:
        gruplar.append(("EMA21 haftalık + FVG", ikili))
    adlar = dict(gruplar)
    for ek in ("Kırılım 4H — ana 3 yıldız", "Kırılım 4H — ⚠️ notlu", "Kırılım 1D — ana"):
        if ikili and ek in adlar:
            gruplar.append((f"EMA21 + FVG + {ek}", ikili + adlar[ek]))
    out("| Strateji | En fazla açık | Emir kuralı | Son 2 yıl: işlem / atlanan | Son 2 yıl bakiye | En büyük düşüş | "
        "Son 180 gün: işlem | Son 180 gün bakiye |")
    out("|---|---|---|---|---|---|---|---|")
    for b_, k in gruplar:
        for mx in (1, 2, 3):
            for mod in ("a", "b"):
                z = tek_sim(k, mx, mod)
                zs = tek_sim(k, mx, mod, t_split2)
                out(f"| {b_} | {mx} | {mod} | {z['alinan']} / {z['atlanan']} | {z['son']:.1f} $ | {z['dd']:.1f} $ | "
                    f"{zs['alinan']} | {zs['son']:.1f} $ |")


def tp_bolumu(now):
    """Seçilen üç stratejide giriş/stop/bekleme sabit, sadece kâr al seviyesi değişir."""
    t_bas2, t_split2 = now - GUN2 * DAY, now - 180 * DAY
    ucu = ["EMA21 haftalık", "FVG — EMA filtreli", "Kırılım 4H — ana 3 yıldız"]
    out("\n## 8) Kâr al seviyesi karşılaştırması (giriş, stop ve bekleme en iyi ayardaki gibi sabit)\n\n"
        "%N = fiyat N% lehe gidince kâr al (short'ta fiyat 1/(1+N%) oranına inince; %100 = yarısı). "
        "Teminat karşılığı: 10x'te %10, 5x'te %20, 3x'te %33, spotta %100 = teminatın iki katı. "
        "yok = kâr al yok, işlem stopla ya da süre dolunca kapanır. 'Tek başına 5 işlem' = strateji tek başına, en fazla 5 açık işlem.\n")
    secilen_tp = {}
    for b_ in ucu:
        if b_ not in SECILEN:
            continue
        en_iyi = SECILEN[b_][2]
        govde = en_iyi.rsplit(" / tp ", 1)[0]
        out(f"\n#### {b_} — {govde}\n")
        out("| Kâr al | Eğitim işlem | Eğitim ort. R | Son dönem işlem | Son dönem ort. R | Kazanan | Ort. süre (gün) | "
            "Tek başına 5 işlem: 2 yıl | düşüş | son 180 gün |")
        out("|---|---|---|---|---|---|---|---|---|---|")
        en, en_puan = None, -9
        for tp in TPLER:
            ad = f"{govde} / tp {tp}"
            if ad not in TUM[b_]:
                continue
            k = TUM[b_][ad]
            dolu = [x for x in k if not x.get("bos")]
            t_split = t_split2 if not b_.startswith("Kırılım 4H") else now - DOG["4H"] * DAY
            ze = ozet([x for x in dolu if x["t"] < t_split], 0)
            zd = ozet([x for x in dolu if x["t"] >= t_split], 0)
            k2 = [x for x in k if x["t"] >= t_bas2]
            z5 = tek_sim(k2, 5, "a")
            z5s = tek_sim(k2, 5, "a", t_split2)
            sure = np.mean([(x["cikis_t"] - x["giris_t"]) / DAY for x in dolu]) if dolu else 0
            out(f"| {tp} | {ze.get('n', 0)} | {ze.get('ortR', 0):+.2f} | {zd.get('n', 0)} | {zd.get('ortR', 0):+.2f} | "
                f"{(ze.get('kazanan', 0)):.0%} | {sure:.1f} | {z5['son']:.0f} $ | {z5['dd']:.0f} $ | {z5s['son']:.0f} $ |")
            if ze.get("n", 0) >= 30 and ze["ortR"] > en_puan:
                en, en_puan = tp, ze["ortR"]
        zorla = dict(x.split("=") for x in os.getenv("BT_TP_SECIM", "").split(";") if "=" in x)
        if zorla.get(KISA.get(b_, b_)) and f"{govde} / tp {zorla[KISA.get(b_, b_)]}" in TUM[b_]:
            en = zorla[KISA.get(b_, b_)]                  # elle seçilen kâr al (BT_TP_SECIM="EMA21=%10;FVG=2R;K4H★3=%33")
        if en:
            secilen_tp[b_] = TUM[b_][f"{govde} / tp {en}"]
            out(f"\nEğitime göre en iyi kâr al: **{en}**")
    if len(secilen_tp) == 3:
        k = [x for b_ in secilen_tp for x in secilen_tp[b_] if x["t"] >= t_bas2]
        out(f"\n#### Üçü birlikte ({', '.join(f'{KISA.get(b_, b_)}' for b_ in secilen_tp)}; kâr al: {os.getenv('BT_TP_SECIM') or 'eğitimde en iyi'})\n")
        out("| En fazla açık | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Son 180 gün bakiye |")
        out("|---|---|---|---|---|")
        for mx in (3, 5, 10):
            z = tek_sim(k, mx, "a")
            zs = tek_sim(k, mx, "a", t_split2)
            out(f"| {mx} | {z['alinan']} | {z['son']:.0f} $ | {z['dd']:.0f} $ | {zs['son']:.0f} $ |")


SECIM_FINAL = {"EMA21 haftalık": "giriş fvg / stop fvg / 2 hafta / yok / tp %10",
               "FVG — EMA filtreli": "orta / 3 gün / yok / tp 2R",
               "Kırılım 4H — ana 3 yıldız": "orta / 24 mum / yok / tp %33"}


def tani_bolumu(now):
    """Önerilen kurulumun ayrıntılı incelemesi: dönemler, yön, fonlama, bekleyen emirler, komşu ayarlar."""
    t_bas2, t_split2 = now - GUN2 * DAY, now - 180 * DAY
    out(f"\n## 9) Önerilen kurulumun incelemesi ({MOD}, dolum payı %{S.DOLUM_PAY * 100:.2f})\n")
    kay = {}
    for b_, ad in SECIM_FINAL.items():
        if b_ in TUM and ad in TUM[b_]:
            kay[b_] = [dict(x, strateji=b_) for x in TUM[b_][ad] if x["t"] >= t_bas2]
        else:
            out(f"- {b_}: '{ad}' bulunamadı")
    hepsi = [x for v in kay.values() for x in v]
    dolu = [x for x in hepsi if not x.get("bos")]
    # 1) en fazla 3 ve 5 işlem
    out("| En fazla açık | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Son 180 gün bakiye |")
    out("|---|---|---|---|---|")
    for mx in (3, 5):
        z, zs = tek_sim(hepsi, mx, "a"), tek_sim(hepsi, mx, "a", t_split2)
        out(f"| {mx} | {z['alinan']} | {z['son']:.0f} $ | {z['dd']:.0f} $ | {zs['son']:.0f} $ |")
    # 2) alınan işlemleri yeniden üret (en fazla 3) ve dönemlere böl
    secilen = []
    acik = []
    for x in sorted(dolu, key=lambda x: x["giris_t"]):
        acik = [a for a in acik if a[0] > x["giris_t"]]
        if len(acik) >= 3 or any(a[1] == x.get("inst") for a in acik):
            continue
        acik.append((x["cikis_t"], x.get("inst")))
        secilen.append(x)
    out("\n**En fazla 3 işlemde alınan işlemler — çeyreklere göre**\n")
    out("| Çeyrek | İşlem | Kazanan | Toplam $ | EMA21 $ | FVG $ | Kırılım $ |")
    out("|---|---|---|---|---|---|---|")
    ceyrek = {}
    for x in secilen:
        tm = time.gmtime(x["giris_t"])
        ceyrek.setdefault(f"{tm.tm_year}-Ç{(tm.tm_mon - 1) // 3 + 1}", []).append(x)
    for c in sorted(ceyrek):
        v = ceyrek[c]
        st = {b_: sum(y["R"] for y in v if y["strateji"] == b_) for b_ in SECIM_FINAL}
        out(f"| {c} | {len(v)} | {np.mean([y['R'] > 0 for y in v]):.0%} | {sum(y['R'] for y in v):+.1f} | "
            f"{st['EMA21 haftalık']:+.1f} | {st['FVG — EMA filtreli']:+.1f} | {st['Kırılım 4H — ana 3 yıldız']:+.1f} |")
    # 3) yön ve strateji
    out("\n| Grup | İşlem | Ort. R | Toplam $ | Ort. süre (gün) | Ort. stop mesafesi |")
    out("|---|---|---|---|---|---|")
    for ad, f in [("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1)] + \
                 [(KISA[b_], (lambda b_: lambda x: x["strateji"] == b_)(b_)) for b_ in SECIM_FINAL]:
        v = [x for x in secilen if f(x)]
        if v:
            out(f"| {ad} | {len(v)} | {np.mean([y['R'] for y in v]):+.2f} | {sum(y['R'] for y in v):+.1f} $ | "
                f"{np.mean([(y['cikis_t'] - y['giris_t']) / DAY for y in v]):.1f} | %{np.mean([y['risk_pct'] for y in v]) * 100:.1f} |")
    # 4) fonlama ücreti tahmini (her 8 saatte pozisyonun %0.01'i, hep aleyhe varsayımıyla)
    fon = sum(0.0001 * ((y["cikis_t"] - y["giris_t"]) / 28800) / y["risk_pct"] for y in secilen)
    out(f"\n**Fonlama ücreti tahmini:** 8 saatte %0.01 ve hep aleyhe varsayılırsa en fazla 3 işlemde 2 yılda yaklaşık "
        f"{fon:.1f} $ (işlem başına {fon / max(len(secilen), 1):.3f} $).")
    # 5) bekleyen emir sayısı (a kuralı): sinyal anından dolum/iptal anına kadar
    olay = []
    for x in hepsi:
        bas, bit = x["t"], (x["giris_t"] if not x.get("bos") else x["bitis"])
        if bit > bas:
            olay += [(bas, 1), (bit, -1)]
    olay.sort()
    n = en = 0
    toplam = 0.0
    for i, (t, d) in enumerate(olay):
        n += d
        en = max(en, n)
        if i + 1 < len(olay):
            toplam += n * (olay[i + 1][0] - t)
    sure = (olay[-1][0] - olay[0][0]) if olay else 1
    out(f"\n**Bekleyen limit emirler (ilk dolan alınır kuralı):** aynı anda en çok {en}, ortalama {toplam / max(sure, 1):.1f} emir. "
        "OKX'te her bekleyen emir teminat ayırır; 100 $'lık hesapta bu sayı önemli.")
    # 6) komşu ayarlar: aynı kâr alla bekleme süresi / giriş değişirse (tek başına en fazla 5 işlem)
    out("\n**Komşu ayarlar (tek başına, en fazla 5 işlem, son 2 yıl / son 180 gün)**\n")
    for b_, ad in SECIM_FINAL.items():
        if b_ not in TUM:
            continue
        tp = ad.rsplit(" / tp ", 1)[1]
        satir = []
        for ad2, k in TUM[b_].items():
            if ad2.endswith(f"/ tp {tp}"):
                k2 = [x for x in k if x["t"] >= t_bas2]
                z, zs = tek_sim(k2, 5, "a"), tek_sim(k2, 5, "a", t_split2)
                satir.append((z["son"], f"| {ad2}{' ⬅ seçilen' if ad2 == ad else ''} | {z['son']:.0f} $ | {z['dd']:.0f} $ | {zs['son']:.0f} $ |"))
        out(f"\n{b_} — en iyi 8 ve seçilen\n")
        out("| Ayar | 2 yıl | Düşüş | Son 180 gün |")
        out("|---|---|---|---|")
        satir.sort(reverse=True)
        gosterilen = satir[:8] + [s_ for s_ in satir[8:] if "seçilen" in s_[1]]
        for _, ss in gosterilen:
            out(ss)


KISA = {"EMA21 haftalık": "EMA21", "FVG — EMA filtreli": "FVG", "Kırılım 4H — ana 3 yıldız": "K4H★3",
        "Kırılım 4H — ⚠️ notlu": "K4H⚠️", "Kırılım 1D — ana": "K1D", "RSI 1W": "RSI-W"}


def kombinasyon_bolumu(adlar, now):
    from itertools import combinations
    t_bas2, t_split2 = now - GUN2 * DAY, now - 180 * DAY
    kay = {b_: [x for x in SECILEN[b_][3] if x["t"] >= t_bas2] for b_ in adlar if b_ in SECILEN}
    adlar = list(kay)
    out(f"\n## 7) Bütün kombinasyonlar — {MOD}, ilk dolan alınır (a)\n\n"
        f"Stratejiler: {', '.join(f'{KISA.get(b_, b_)} = {b_} ({SECILEN[b_][2]})' for b_ in adlar)}. "
        "Oran = 2 yıllık kâr / en büyük düşüş (yüksek = az dalgalanmayla çok kazanç). Hepsi 100 $ ile başlar, işlem başına 1 $ risk.\n")
    sonuclar = []
    for n in range(1, len(adlar) + 1):
        for kombi in combinations(adlar, n):
            k = [x for b_ in kombi for x in kay[b_]]
            for mx in (1, 2, 3, 5, 10, 10 ** 6):
                z = tek_sim(k, mx, "a")
                zs = tek_sim(k, mx, "a", t_split2)
                oran = (z["son"] - BAKIYE) / z["dd"] if z["dd"] > 0 else 0
                sonuclar.append(dict(ad=" + ".join(KISA.get(b_, b_) for b_ in kombi), mx=mx, son=z["son"], dd=z["dd"],
                                     islem=z["alinan"], son180=zs["son"], dd180=zs["dd"], oran=oran))
    for mx in (1, 2, 3, 5, 10, 10 ** 6):
        grup = [r for r in sonuclar if r["mx"] == mx]
        ad_mx = "sınırsız" if mx > 1000 else f"en fazla {mx}"
        for baslik, anahtar in (("son 180 günün kârına göre", "son180"), ("kâr / düşüş oranına göre", "oran")):
            out(f"\n#### Açık işlem {ad_mx} — {baslik} en iyi 5\n")
            out("| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |")
            out("|---|---|---|---|---|---|---|")
            for r in sorted(grup, key=lambda r: r[anahtar], reverse=True)[:5]:
                out(f"| {r['ad']} | {r['islem']} | {r['son']:.0f} $ | {r['dd']:.0f} $ | {r['oran']:.1f} | "
                    f"{r['son180']:.0f} $ | {r['dd180']:.0f} $ |")
    with open(f"sinyal_kombi_{MOD}.json", "w") as f:
        json.dump(sonuclar, f)


def main():
    t0 = time.time()
    data, symbols, top, now = S.load_data()
    sonuc = {}
    out(f"# Sinyal geçmiş testi 2 — sizin kurallarınızla\n\n{len(data)} coin, test tarihi "
        f"{time.strftime('%Y-%m-%d', time.gmtime(now))}. R = 1 $ risk; ortalama +0.20R = işlem başına +0,20 $. "
        f"Ücret: limit %0.02, piyasa/stop %0.05 + %0.03 kayma. Bakiye: 100 $, işlem başına 1 $ risk, 10x kaldıraç. "
        f"'Eğitim' dönemi ayar seçmek, 'son dönem' sınamak içindir.\n\n"
        f"**Mod: {'SPOT — sadece long, kaldıraçsız (pozisyon kadar nakit gerekir), ücret limit %0.08 / piyasa %0.10' if SPOT else f'vadeli {KALDIRAC}x — stop mesafesi %{LIKIT * 100:.0f} üstündeki işlemler likidasyon riski yüzünden açılmaz'}**\n")

    hazir = {}
    for inst, dd in data.items():
        d = arr(dd["1D"])
        if len(d["c"]) < 30:
            continue
        zones, fvg_open, datr = S.daily_fvg(d)
        w = arr(S.weekly_from_daily(dd["1D"]))
        hazir[inst] = dict(d=d, w=w, zones=zones, fvg_open=fvg_open, datr=datr,
                           e200=ema(d["c"], 200), e21w=ema(w["c"], 21) if len(w["c"]) >= 21 else np.full(len(w["c"]), np.nan))

    def ema_izin(H, T, fiyat, yon):
        di = S.day_index(H["d"], T)
        wi = bisect.bisect_right(H["w"]["t"], T - 7 * DAY) - 1
        e1 = H["e200"][di] if di >= 0 else np.nan
        e2 = H["e21w"][wi] if wi >= 0 else np.nan
        if yon == 1:
            return (not np.isnan(e1) and fiyat > e1) or (not np.isnan(e2) and fiyat > e2)
        return (not np.isnan(e1) and fiyat < e1) or (not np.isnan(e2) and fiyat < e2)

    # ===================== 1) KIRILIM =====================
    out("\n## 1) Kırılım\n\nYön filtresi her zaman açık (long: günlük EMA200 veya haftalık EMA21 üstü; short: tersi). "
        "Ana strateji ⚠️ notluları içermez. Giriş: cizgi = kırılan bant çizgisi, orta = bant ortası. "
        "İz: yok / be k = 1R'de başa baş sonra k x ATR / r1 = 1R geriden. Bekleme mum sayısıdır.\n")
    bekle_tf = {"15m": (24, 48, 96), "1H": (24, 48, 96), "4H": (24, 48, 96), "1D": (3, 5, 10)}
    tut_tf = {"15m": 7 * 96, "1H": 21 * 24, "4H": 60 * 6, "1D": 180}
    for tf in ("15m", "1H", "4H", "1D"):
        t_bas = now - (120 if tf in ("15m", "1H") else GUN2) * DAY
        t_split = now - DOG[tf] * DAY
        gruplar = {"ana": {}, "ana 2-3 yıldız": {}, "ana 3 yıldız": {}, "0-1 yıldız": {}, "⚠️ notlu": {}}
        n_sig = 0
        coinler = top if tf in ("15m", "1H") else list(hazir)
        for inst in coinler:
            if inst not in hazir or inst not in data:
                continue
            H = hazir[inst]
            if tf == "1D":
                s, htf_s, htf_sec = H["d"], H["w"], 7 * DAY
            elif tf == "4H":
                s, htf_s, htf_sec = arr(data[inst]["4H"]), H["d"], DAY
            else:
                if tf not in data[inst]:
                    continue
                s = arr(data[inst][tf])
                htf = "1H" if tf == "15m" else "4H"
                htf_s, htf_sec = arr(data[inst][htf]), TF_SEC[htf]
            if len(s["c"]) < 120:
                continue
            sigs = S.kirilim_sinyalleri(s, tf, htf_s, htf_sec, H["d"], H["fvg_open"], t_bas)
            sigs = [x for x in sigs if ema_izin(H, x["t"], x["c"], x["yon"])]
            n_sig += len(sigs)
            a, _ = atr(s["h"], s["l"], s["c"])
            c = s["c"]
            sec = TF_SEC[tf]
            secim = {"ana": [x for x in sigs if not x["uyari"]],
                     "ana 2-3 yıldız": [x for x in sigs if not x["uyari"] and x["stars"] >= 2],
                     "ana 3 yıldız": [x for x in sigs if not x["uyari"] and x["stars"] == 3],
                     "0-1 yıldız": [x for x in sigs if not x["uyari"] and x["stars"] <= 1],
                     "⚠️ notlu": [x for x in sigs if x["uyari"]]}
            for g in ("cizgi", "orta"):
                for bk in bekle_tf[tf]:
                    for iz in IZLER:
                        for tp in TPLER:
                            def fn(sg, g=g, bk=bk, iz=iz, tp=tp):
                                yon, hi, lo = sg["yon"], sg["hi"], sg["lo"]
                                w_ = hi - lo
                                cizgi, orta, dip = (hi, (hi + lo) / 2, lo) if yon == 1 else (lo, (hi + lo) / 2, hi)
                                st = dip - 0.10 * w_ * yon
                                giris = cizgi if g == "cizgi" else orta
                                sg["emir_bitis"] = sg["t"] + bk * sec
                                return simulate(s, a, sg["i"] + 1, yon, [(giris, 1.0, st)], st, iz,
                                                tp=hedef(tp, giris, st, yon), bekle=bk,
                                                iptal=lambda j: (yon == 1 and c[j] < dip) or (yon == -1 and c[j] > dip),
                                                max_bar=tut_tf[tf])
                            ad = f"{g} / {bk} mum / {iz[0]} {iz[1] or ''} / tp {tp}".replace("  ", " ")
                            for gr, liste in secim.items():
                                gruplar[gr].setdefault(ad, []).extend(calistir([dict(x, inst=inst) for x in liste], fn))
        out(f"\n### Kırılım {tf} — EMA filtresinden geçen {n_sig} sinyal "
            f"({'ilk 100 coin, 120 gün' if tf in ('15m', '1H') else 'bütün coinler, 2 yıl'}; son dönem = son {DOG[tf]} gün)")
        oz = [("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1),
              ("✅ var", lambda x: x["iyi"]), ("✅ yok", lambda x: not x["iyi"]),
              ("2 yıldız", lambda x: x["stars"] == 2), ("3 yıldız", lambda x: x["stars"] == 3)]
        for gr in ("ana", "ana 2-3 yıldız", "ana 3 yıldız", "0-1 yıldız", "⚠️ notlu"):
            if gr in ("ana 2-3 yıldız", "0-1 yıldız") and tf not in ("15m", "1H"):
                continue
            if gr == "ana 3 yıldız" and tf not in ("4H", "1D"):
                continue
            bolum(f"Kırılım {tf} — {gr}", gruplar[gr], t_split, ozellikler=oz if gr == "ana" else None, sonuc=sonuc)
        print(f"Kırılım {tf} bitti ({(time.time() - t0) / 60:.0f} dk)", flush=True)

    # ===================== 2) FVG'DEN DÖNÜŞ =====================
    t_bas = now - GUN2 * DAY
    t_split = now - DOG["FVG"] * DAY
    fvg_var = {"filtresiz": {}, "EMA filtreli": {}}
    n_sig = 0
    for inst, H in hazir.items():
        s4 = arr(data[inst]["4H"])
        if len(s4["c"]) < 60:
            continue
        sigs = S.fvg_sinyalleri(s4, H["d"], H["zones"], H["datr"], t_bas)
        n_sig += len(sigs)
        a4, _ = atr(s4["h"], s4["l"], s4["c"])
        c4 = s4["c"]
        filtreli = [x for x in sigs if ema_izin(H, x["t"], c4[x["i"]], x["yon"])]
        for g in ("cizgi", "orta"):
            for gun in (1, 3, 7):
                for iz in IZLER:
                    for tp in TPLER:
                        def fn(sg, g=g, gun=gun, iz=iz, tp=tp):
                            yon, alt, ust = sg["yon"], sg["alt"], sg["ust"]
                            st = (alt if yon == 1 else ust) - sg["pay"] * yon
                            giris = (ust if yon == 1 else alt) if g == "cizgi" else (alt + ust) / 2
                            sg["emir_bitis"] = sg["t"] + gun * DAY
                            return simulate(s4, a4, sg["i"] + 1, yon, [(giris, 1.0, st)], st, iz,
                                            tp=hedef(tp, giris, st, yon), bekle=gun * 6,
                                            iptal=lambda j: (yon == 1 and c4[j] < alt) or (yon == -1 and c4[j] > ust),
                                            max_bar=60 * 6)
                        ad = f"{g} / {gun} gün / {iz[0]} {iz[1] or ''} / tp {tp}".replace("  ", " ")
                        fvg_var["filtresiz"].setdefault(ad, []).extend(calistir([dict(x, inst=inst) for x in sigs], fn))
                        fvg_var["EMA filtreli"].setdefault(ad, []).extend(calistir([dict(x, inst=inst) for x in filtreli], fn))
    out(f"\n## 2) FVG'den dönüş — {n_sig} sinyal (bütün coinler, 2 yıl; son dönem = son {DOG['FVG']} gün)\n\n"
        "Giriş: cizgi = tepki çizgisi (destekte üst, dirençte alt), orta = FVG ortası. Stop: FVG'nin öbür ucu + 0.1 x günlük ATR.\n")
    oz = [("Long (🟩)", lambda x: x["yon"] == 1), ("Short (🟥)", lambda x: x["yon"] == -1),
          ("⭐⭐", lambda x: x["score"] == 2), ("⭐⭐⭐", lambda x: x["score"] == 3),
          ("yakın temas", lambda x: x["yakin"]), ("gerçek temas", lambda x: not x["yakin"])]
    for gr in ("filtresiz", "EMA filtreli"):
        bolum(f"FVG — {gr}", fvg_var[gr], t_split, ozellikler=oz, sonuc=sonuc)
    print(f"FVG bitti ({(time.time() - t0) / 60:.0f} dk)", flush=True)

    # ===================== 3) EMA21 HAFTALIK =====================
    t_split = now - DOG["EMA"] * DAY
    ema_var = {}
    n_sig = 0
    for inst, H in hazir.items():
        d, w = H["d"], H["w"]
        if len(w["c"]) < 30:
            continue
        sigs, we = S.ema21w_sinyalleri(w, 0)
        n_sig += len(sigs)
        ad_, _ = atr(d["h"], d["l"], d["c"])
        cd = d["c"]
        for g in ("fvg", "ema"):
            for stp in ("mum", "fvg"):
                for hafta in (2, 4, 8):
                    for iz in (("yok", 0), ("r1be", 0)):
                        for tp in TPLER:
                            def fn(sg, g=g, stp=stp, hafta=hafta, iz=iz, tp=tp):
                                yon = sg["yon"]
                                i0 = bisect.bisect_left(d["t"], sg["t"])
                                if i0 >= len(cd):
                                    return None
                                di = i0 - 1
                                pay = 0.1 * H["datr"][di] if di >= 0 and not np.isnan(H["datr"][di]) else 0
                                px_son = cd[di]
                                fvg = None
                                for z in H["fvg_open"][di] if di >= 0 else []:
                                    if yon == 1 and z["tur"] == 1 and z["ust"] < px_son and (1 - z["ust"] / px_son) * 100 <= 15:
                                        if fvg is None or z["ust"] > fvg["ust"]:
                                            fvg = z
                                    if yon == -1 and z["tur"] == -1 and z["alt"] > px_son and (z["alt"] / px_son - 1) * 100 <= 15:
                                        if fvg is None or z["alt"] < fvg["alt"]:
                                            fvg = z
                                if stp == "mum":
                                    st = (sg["l"] if yon == 1 else sg["h"]) - pay * yon
                                elif fvg is not None:
                                    st = (fvg["alt"] if yon == 1 else fvg["ust"]) - pay * yon
                                else:
                                    return None
                                if g == "fvg" and fvg is None:
                                    return None
                                sg["emir_bitis"] = sg["t"] + hafta * 7 * DAY
                                bitis = min(len(cd) - 1, i0 + hafta * 7)
                                for j in range(i0, bitis + 1):
                                    wk = bisect.bisect_right(w["t"], d["t"][j]) - 1
                                    if g == "fvg":
                                        sev = fvg["ust"] if yon == 1 else fvg["alt"]
                                    else:
                                        wc = wk - 1 if (wk >= 0 and d["t"][j] < w["t"][wk] + 7 * DAY) else wk
                                        sev = we[wc] if wc >= sg["i"] and not np.isnan(we[wc]) else sg["e"]
                                    if (sev - st) * yon <= 0:
                                        return None
                                    if (yon == 1 and d["l"][j] <= sev * (1 - S.DOLUM_PAY)) or (yon == -1 and d["h"][j] >= sev * (1 + S.DOLUM_PAY)):
                                        return simulate(d, ad_, j, yon, [(sev, 1.0, st)], st, iz,
                                                        tp=hedef(tp, sev, st, yon), bekle=1)
                                    if wk >= 0 and d["t"][j] + DAY == w["t"][wk] + 7 * DAY and not np.isnan(we[wk]):
                                        if (yon == 1 and w["c"][wk] < we[wk]) or (yon == -1 and w["c"][wk] > we[wk]):
                                            return None
                                return None
                            ad = f"giriş {g} / stop {stp} / {hafta} hafta / {iz[0]} / tp {tp}"
                            ema_var.setdefault(ad, []).extend(calistir([dict(x, inst=inst) for x in sigs], fn))
    out(f"\n## 3) EMA21 haftalık — {n_sig} kesişim (bütün coinler, bütün geçmiş; son dönem = son {DOG['EMA']} gün)\n\n"
        "Giriş: fvg = en yakın günlük FVG sınırı (%15 içinde), ema = EMA21 çizgisi. Stop: mum = kesişim mumunun dibi/tepesi, "
        "fvg = FVG'nin öbür ucu. İz: yok / r1be = 1R kârdan sonra 1R geriden.\n")
    bolum("EMA21 haftalık", ema_var, t_split,
          ozellikler=[("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1)], sonuc=sonuc)
    print(f"EMA bitti ({(time.time() - t0) / 60:.0f} dk)", flush=True)

    # ===================== 4) RSI =====================
    for tf in ("1D", "1W"):
        t_split = now - DOG["RSI"] * DAY
        rsi_var = {}
        n_a = n_b = 0
        for inst, H in hazir.items():
            s = H["d"] if tf == "1D" else H["w"]
            if len(s["c"]) < 40:
                continue
            a, _ = atr(s["h"], s["l"], s["c"])
            sigs_b, r, g_, lo_ = S.rsi_sinyalleri(s, 0, TF_SEC[tf], 2)
            # A: dönüş mumunun kapanışında giriş (SMA şartı yok)
            sigs_a = []
            c, h, l = s["c"], s["h"], s["l"]
            for i in range(16, len(c)):
                if np.isnan(r[i - 1]) or np.isnan(r[i]):
                    continue
                yon = tip = None
                if r[i - 1] < 30 <= r[i]:
                    yon, tip = 1, "kapanış"
                elif r[i - 1] > 70 >= r[i]:
                    yon, tip = -1, "kapanış"
                else:
                    ud = S.rsi_if(l[i], c[i - 1], g_[i - 1], lo_[i - 1])
                    uy = S.rsi_if(h[i], c[i - 1], g_[i - 1], lo_[i - 1])
                    if r[i - 1] >= 30 and ud <= 30 < r[i]:
                        yon, tip = 1, "fitil"
                    elif r[i - 1] <= 70 and uy >= 70 > r[i]:
                        yon, tip = -1, "fitil"
                if yon is None:
                    continue
                bas = i
                while bas > max(i - 20, 0) and ((yon == 1 and r[bas - 1] <= 32) or (yon == -1 and r[bas - 1] >= 68)):
                    bas -= 1
                uc = np.min(l[bas:i + 1]) if yon == 1 else np.max(h[bas:i + 1])
                sigs_a.append(dict(i=i, t=s["t"][i] + TF_SEC[tf], yon=yon, tip=tip, uc=uc))
            n_a += len(sigs_a)
            n_b += len(sigs_b)
            for giris, sigs in (("A dönüş", sigs_a), ("B dönüş + SMA kesişimi", sigs_b)):
                for iz in IZLER:
                    for tp in TPLER:
                        def fn(sg, iz=iz, tp=tp, s=s, a=a):
                            yon, i = sg["yon"], sg["i"]
                            pay = 0.1 * a[i] if not np.isnan(a[i]) else 0
                            st = sg["uc"] - pay * yon
                            px = s["c"][i]
                            if (px - st) * yon <= 0:
                                return None
                            return simulate(s, a, i + 1, yon, [], st, iz, piyasa=px, tp=hedef(tp, px, st, yon),
                                            max_bar=365 if tf == "1D" else 104)
                        ad = f"{giris} / {iz[0]} {iz[1] or ''} / tp {tp}".replace("  ", " ")
                        rsi_var.setdefault(ad, []).extend(calistir([dict(x, inst=inst) for x in sigs], fn))
        out(f"\n## 4) RSI {tf} — A: {n_a} dönüş, B: {n_b} dönüş + SMA kesişimi (bütün coinler, bütün geçmiş; son dönem = son {DOG['RSI']} gün)\n")
        bolum(f"RSI {tf}", rsi_var, t_split,
              ozellikler=[("Long", lambda x: x["yon"] == 1), ("Short", lambda x: x["yon"] == -1),
                          ("Kapanışla dönüş", lambda x: x["tip"] == "kapanış"), ("Fitille dönüş", lambda x: x["tip"] == "fitil")],
              sonuc=sonuc)
        print(f"RSI {tf} bitti ({(time.time() - t0) / 60:.0f} dk)", flush=True)

    # ===================== 5) STRATEJİLER BİRLİKTE, TEK BAKİYE =====================
    adaylar = ["EMA21 haftalık", "FVG — EMA filtreli", "Kırılım 4H — ana 3 yıldız", "Kırılım 4H — ⚠️ notlu",
               "Kırılım 1D — ana", "RSI 1W"]
    secim = [(b, SECILEN[b][:3]) for b in adaylar
             if b in SECILEN and SECILEN[b][1].get("n", 0) >= 30 and SECILEN[b][1].get("ortR", 0) > 0]
    t_bas2, t_split2 = now - GUN2 * DAY, now - 180 * DAY
    out("\n## 5) Stratejiler birlikte — tek 100 $ bakiye (son 2 yıl)\n\n"
        "Eğitimde ortalaması artı ve en az 30 işlemi olan stratejilerin en iyi ayarları aynı bakiyede birlikte çalışır. "
        "Aynı coinde aynı anda tek pozisyon (önce gelen alınır); teminat yetmezse işlem atlanır.\n")
    for b_, (_, ze, ad) in secim:
        out(f"- {b_}: {ad} (eğitim {ze['n']} işlem, ort. {ze['ortR']:+.2f}R)")
    birlesik = []
    for b_, (isl, _, _) in secim:
        birlesik += [dict(x, strateji=b_) for x in isl if x["giris_t"] >= t_bas2]
    birlesik.sort(key=lambda x: x["giris_t"])
    filtreli, acik_coin = [], {}
    for x in birlesik:                                  # aynı coinde tek pozisyon
        if acik_coin.get(x["inst"], 0) > x["giris_t"]:
            continue
        filtreli.append(x)
        acik_coin[x["inst"]] = x["cikis_t"]
    out("\n| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |")
    out("|---|---|---|---|---|---|---|---|")
    bakiye_satiri("Son 2 yıl (100 $ ile başlayarak)", bakiye_sim(filtreli))
    bakiye_satiri("Son 180 gün (100 $ ile başlayarak)", bakiye_sim(filtreli, t_split2))
    out("\n| Strateji | İşlem | Ort. R | Toplam $ |")
    out("|---|---|---|---|")
    for b_, _ in secim:
        alt = [x for x in filtreli if x["strateji"] == b_]
        if alt:
            out(f"| {b_} | {len(alt)} | {np.mean([x['R'] for x in alt]):+.2f} | {sum(x['R'] for x in alt) * RISK:+.1f} $ |")

    if os.getenv("BT_TEK") == "1":
        tek_islem_bolumu([b_ for b_, _ in secim], now)      # 5. bölümde seçilen stratejiler
    if os.getenv("BT_TANI") == "1":
        tani_bolumu(now)
    if os.getenv("BT_TPTEST") == "1":
        tp_bolumu(now)
    if os.getenv("BT_KOMBI") == "1":
        kombinasyon_bolumu([b_ for b_, _ in secim], now)

    out(f"\nToplam süre: {(time.time() - t0) / 60:.0f} dk")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(OUT_JSON, "w") as f:
        json.dump(sonuc, f)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        lines.append("\n## HATA\n\n```\n" + traceback.format_exc() + "```")
        with open(OUT_MD, "w") as f:
            f.write("\n".join(lines) + "\n")
        raise
