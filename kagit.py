"""
Kâğıt üzerinde işlem (sanal) - okx_scan_once.py içinden çağrılır. OKX'e emir GÖNDERMEZ.

Geçmiş testte seçilen kurulum (3x, en fazla 3 açık işlem, işlem başına 1 $ risk, 100 $ sanal bakiye):
  EMA21 haftalık : kesişimde en yakın günlük FVG sınırına emir (long: destek FVG üstü), stop FVG'nin öbür ucu
                   (+0.1 x günlük ATR), kâr al fiyatın %10'u, emir 2 hafta bekler; haftalık kapanış EMA21'in
                   öbür tarafına dönerse iptal.
  FVG'den dönüş  : EMA filtresi (long: fiyat günlük EMA200 VEYA haftalık EMA21 üstünde), FVG ortasına emir,
                   stop FVG'nin öbür ucu (+0.1 x günlük ATR), kâr al 2R, emir 3 gün bekler; 4H kapanış bölgenin
                   öbür tarafındaysa iptal.
  4H kırılım     : sadece 3 yıldız, ⚠️ notlu değil, EMA filtresi; bant ortasına emir, stop bandın öbür ucu
                   (+ bant genişliğinin %10'u), kâr al %33, emir 4 gün bekler; 4H kapanış bandın öbür ucunu
                   geçerse iptal.
Kurallar: fiyat emre gelince ilk gelen alınır (en fazla 3 açık, coin başına 1); yer ya da teminat yoksa o emir
atlanır. Giriş gerçekte piyasa emriyle yapılacağı için giriş ücreti %0.05 + %0.03 kayma; stop %0.05 + %0.03 kayma,
kâr al %0.02. Fonlama ücreti OKX'in gerçekleşen oranlarıyla düşülür. Mesajlar EMA botuna, başında 📝 ile gider.
"""
import json
import time

B = None                      # okx_scan_once modülü (okx_scan_once tarafından atanır)

BAKIYE0, RISK, KALDIRAC, MAX_ACIK = 100.0, 1.0, 3, 3
LIKIT = 0.30                  # 3x'te stop mesafesi bundan büyükse işlem açılmaz
UCRET_GIRIS, UCRET_STOP, UCRET_TP = 0.0005 + 0.0003, 0.0005 + 0.0003, 0.0002
KANAL = "ema"
DAY, H4 = 86400, 14400
STR_AD = {"EMA21": "📈 EMA21 haftalık", "FVG": "🟩🟥 FVG dönüşü", "K4H": "📦 4H kırılım ⭐⭐⭐"}


def _st(state):
    k = state.setdefault("KAGIT", {})
    k.setdefault("bakiye", BAKIYE0)
    k.setdefault("emirler", [])
    k.setdefault("acik", [])
    k.setdefault("kapanan", [])          # son işlemler (özet için, en fazla 300)
    k.setdefault("sayac", dict(atlanan=0, iptal=0, suresi_dolan=0))
    k.setdefault("baslangic", int(time.time()))
    k.setdefault("son_ozet", (int(time.time()) - 6 * 3600) // DAY)   # ilk özet bir sonraki 09:00'da
    k.setdefault("son_ozet2", (int(time.time()) - 6 * 3600) // (DAY // 2))
    return k


def _fmt(x):
    return f"{x:.6g}"


def _ema_izin(inst, t, fiyat, yon):
    """Long: fiyat günlük EMA200 VEYA haftalık EMA21 üstünde; short tersi (son kapanmış mumlara göre)."""
    try:
        d = B.daily(inst)
        di = B.day_at(d, t)
        e200 = B.ema_series(d["c"][:di + 1], 200)[-1] if di + 1 >= 200 else None
        w = B.candles(inst, "1Wutc", 60)
        wc = [float(r[4]) for r in w if int(r[0]) // 1000 + 7 * DAY <= t]
        e21 = B.ema_series(wc, 21)[-1] if len(wc) >= 21 else None
    except Exception as e:
        print(f"Kâğıt: {inst} EMA filtresi hesaplanamadı: {e}")
        return False
    ok = lambda e: e is not None and ((yon == 1 and fiyat > e) or (yon == -1 and fiyat < e))
    return ok(e200) or ok(e21)


def _emir_ekle(k, emir):
    if any(e["id"] == emir["id"] for e in k["emirler"]):
        return False
    if (emir["giris"] - emir["stop"]) * emir["yon"] <= 0:
        return False
    k["emirler"].append(emir)
    return True


def sinyal_ekle(state, kind, name, hits, candle_open, sec):
    """Tarama sonuçlarından sanal emir kurar (mesaj göndermez)."""
    k = _st(state)
    t = candle_open + sec
    once = len(k["emirler"])
    for h in hits:
        inst = h["inst"]
        try:
            if kind == "brk" and name == "4H":
                if h.get("stars") != 3 or h.get("uyari"):
                    continue
                yon = h["kind"]
                if not _ema_izin(inst, t, h["price"], yon):
                    continue
                hi, lo = h["hi"], h["lo"]
                w = hi - lo
                dip = lo if yon == 1 else hi
                giris = (hi + lo) / 2
                _emir_ekle(k, dict(id=f"K4H|{inst}|{t}", s="K4H", inst=inst, yon=yon, giris=giris,
                                   stop=dip - 0.10 * w * yon,
                                   tp=giris * 1.33 if yon == 1 else giris / 1.33, t=t, bitis=t + 24 * H4,
                                   iptal=dict(tur="4h_kapanis", seviye=dip), son_kontrol=t))
            elif kind == "fvg":
                yon = 1 if h["kind"] == "SUPPORT" else -1
                if not _ema_izin(inst, t, h["price"], yon):
                    continue
                alt, ust = h["bot"], h["top"]
                giris = (alt + ust) / 2
                stop = (alt if yon == 1 else ust) - h.get("pay", 0.0) * yon
                _emir_ekle(k, dict(id=f"FVG|{inst}|{t}", s="FVG", inst=inst, yon=yon, giris=giris, stop=stop,
                                   tp=giris + 2 * abs(giris - stop) * yon, t=t, bitis=t + 3 * DAY,
                                   iptal=dict(tur="4h_kapanis", seviye=alt if yon == 1 else ust), son_kontrol=t))
            elif kind == "ema" and name == "EMA21_1W":
                yon = 1 if h["kind"] == "UP" else -1
                d = B.daily(inst)
                fiyat = h["price"]
                di = B.day_at(d, t)
                pay = 0.1 * d["atr"][di] if di >= 0 and d["atr"][di] else 0.0
                aday = None
                for z in B.open_fvgs(d, t):
                    if yon == 1 and z["tur"] == 1 and z["ust"] < fiyat and (1 - z["ust"] / fiyat) * 100 <= 15:
                        if aday is None or z["ust"] > aday["ust"]:
                            aday = z
                    if yon == -1 and z["tur"] == -1 and z["alt"] > fiyat and (z["alt"] / fiyat - 1) * 100 <= 15:
                        if aday is None or z["alt"] < aday["alt"]:
                            aday = z
                if aday is None:
                    continue
                giris = aday["ust"] if yon == 1 else aday["alt"]
                stop = (aday["alt"] if yon == 1 else aday["ust"]) - pay * yon
                _emir_ekle(k, dict(id=f"EMA21|{inst}|{t}", s="EMA21", inst=inst, yon=yon, giris=giris, stop=stop,
                                   tp=giris * 1.10 if yon == 1 else giris / 1.10, t=t, bitis=t + 14 * DAY,
                                   iptal=dict(tur="hafta_ema"), son_kontrol=t))
        except Exception as e:
            print(f"Kâğıt: {inst} sinyali eklenemedi: {e}")
    yeni = k["emirler"][once:]
    if yeni:                                          # yeni kurulan sanal emirler: tek mesaj
        sure = {"EMA21": "2 hafta", "FVG": "3 gün", "K4H": "4 gün"}
        satir = [f"📝 Kâğıt: {len(yeni)} yeni emir kuruldu (fiyat gelirse açılır)"]
        for e in yeni:
            satir.append(f"  {STR_AD[e['s']]} {B.link(e['inst'], 'EMA21_1W' if e['s'] == 'EMA21' else '4H')} "
                         f"{'long' if e['yon'] == 1 else 'short'}  |  giriş {_fmt(e['giris'])}  |  stop {_fmt(e['stop'])}  |  "
                         f"kâr al {_fmt(e['tp'])}  |  {sure[e['s']]} geçerli")
        satir.append(f"Bekleyen emir: {len(k['emirler'])}  |  açık işlem: {len(k['acik'])}/{MAX_ACIK}")
        B.send("\n".join(satir), KANAL)


def _r_hesap(p, cikis, ucret_cikis):
    """1 $ riske göre sonuç (ücretler ve fonlama dahil)."""
    notional = p["notional"]
    brut = (cikis - p["giris_px"]) / p["giris_px"] * notional * p["yon"]
    ucret = notional * UCRET_GIRIS + notional * (cikis / p["giris_px"]) * ucret_cikis
    return brut - ucret - p.get("fonlama", 0.0)


def _kapat(k, p, cikis, neden, ucret, mesajlar):
    sonuc = _r_hesap(p, cikis, ucret)
    k["bakiye"] += sonuc
    k["acik"] = [x for x in k["acik"] if x["id"] != p["id"]]
    kayit = dict(s=p["s"], inst=p["inst"], yon=p["yon"], sonuc=sonuc, neden=neden, giris_t=p["giris_t"],
                 cikis_t=int(time.time()))
    k["kapanan"] = (k["kapanan"] + [kayit])[-300:]
    sure = (time.time() - p["giris_t"]) / 3600
    sure_txt = f"{sure:.0f} saat" if sure < 48 else f"{sure / 24:.1f} gün"
    isaret = "✅" if sonuc > 0 else "❌"
    mesajlar.append(f"📝 Kâğıt: {isaret} {STR_AD[p['s']]} {B.link(p['inst'], 'EMA21_1W' if p['s'] == 'EMA21' else '4H')} "
                    f"{'long' if p['yon'] == 1 else 'short'} kapandı ({neden}): {_fmt(p['giris_px'])} → {_fmt(cikis)}  |  "
                    f"{sonuc:+.2f} $  |  {sure_txt}  |  bakiye {k['bakiye']:.2f} $")


def _ac(k, e, px, mesajlar):
    risk_pct = abs(px - e["stop"]) / px
    if risk_pct <= 0 or (e["stop"] - px) * e["yon"] >= 0:
        return "geçersiz"
    if risk_pct >= LIKIT:
        return "likidasyon"
    notional = RISK / risk_pct
    teminat = notional / KALDIRAC
    kullanilan = sum(p["teminat"] for p in k["acik"])
    if len(k["acik"]) >= MAX_ACIK or any(p["inst"] == e["inst"] for p in k["acik"]):
        return "yer yok"
    if teminat > k["bakiye"] - kullanilan:
        return "teminat yok"
    p = dict(e, giris_px=px, giris_t=int(time.time()), notional=notional, teminat=teminat, risk_pct=risk_pct,
             fonlama=0.0, fon_t=int(time.time()))
    k["acik"].append(p)
    mesajlar.append(f"📝 Kâğıt: 🔔 {STR_AD[e['s']]} {B.link(e['inst'], 'EMA21_1W' if e['s'] == 'EMA21' else '4H')} "
                    f"{'long' if e['yon'] == 1 else 'short'} açıldı: giriş {_fmt(px)}  |  stop {_fmt(e['stop'])} "
                    f"(%{risk_pct * 100:.1f})  |  kâr al {_fmt(e['tp'])}  |  pozisyon {notional:.0f} $, teminat {teminat:.1f} $ (3x)  |  "
                    f"açık {len(k['acik'])}/{MAX_ACIK}")
    return "açıldı"


def _fiyatlar():
    son = {}
    for t in B.api("/api/v5/market/tickers", {"instType": "SWAP"}):
        try:
            son[t["instId"]] = float(t["last"])
        except (ValueError, KeyError):
            pass
    return son


def kontrol(state, fitil=False):
    """Açık pozisyonları ve bekleyen emirleri fiyatla karşılaştırır. fitil=True: son 15m mumlarına da bakar."""
    k = _st(state)
    if not k["emirler"] and not k["acik"]:
        return
    now = time.time()
    mesajlar = []
    try:
        son = _fiyatlar()
    except Exception as e:
        print("Kâğıt: fiyatlar alınamadı:", e)
        return
    veri = {}                                         # inst -> [(başlangıç, en düşük, en yüksek)]
    insts = {e["inst"] for e in k["emirler"]} | {p["inst"] for p in k["acik"]}
    for inst in insts:
        if inst in son:
            veri.setdefault(inst, []).append((now, son[inst], son[inst]))
    if fitil:
        for inst in insts:
            try:
                for r in B.candles(inst, "15m", 3):
                    veri.setdefault(inst, []).append((int(r[0]) // 1000, float(r[3]), float(r[2])))
                time.sleep(B.REQUEST_PAUSE)
            except Exception as e:
                print(f"Kâğıt: {inst} mumları alınamadı: {e}")

    def aralik(inst, since):
        """'since' anından sonra açılan mumlar ve anlık fiyat: (en düşük, en yüksek) ya da None."""
        v = [(lo_, hi_) for t0, lo_, hi_ in veri.get(inst, []) if t0 >= since]
        if not v:
            return None
        return min(x[0] for x in v), max(x[1] for x in v)

    # 1) açık pozisyonlar: önce stop, sonra kâr al
    for p in list(k["acik"]):
        a = aralik(p["inst"], p["giris_t"])
        if a is None:
            continue
        lo_, hi_ = a
        if (p["yon"] == 1 and lo_ <= p["stop"]) or (p["yon"] == -1 and hi_ >= p["stop"]):
            _kapat(k, p, p["stop"], "stop", UCRET_STOP, mesajlar)
        elif (p["yon"] == 1 and hi_ >= p["tp"]) or (p["yon"] == -1 and lo_ <= p["tp"]):
            _kapat(k, p, p["tp"], "kâr al", UCRET_TP, mesajlar)

    # 2) bekleyen emirler: süresi dolan çıkar, fiyat gelen dolar (ilk gelen alınır)
    kalan = []
    for e in sorted(k["emirler"], key=lambda e: e["t"]):
        if now > e["bitis"]:
            k["sayac"]["suresi_dolan"] += 1
            continue
        a = aralik(e["inst"], e["t"])
        if a and ((e["yon"] == 1 and a[0] <= e["giris"]) or (e["yon"] == -1 and a[1] >= e["giris"])):
            px = e["giris"] * (1 + 0.0003 * e["yon"])            # emir gerçekte piyasa emriyle verilir
            durum = _ac(k, e, px, mesajlar)
            if durum == "açıldı":
                lo_, hi_ = a                                    # aynı aralıkta stop da görüldüyse (temkinli)
                if (e["yon"] == 1 and lo_ <= e["stop"]) or (e["yon"] == -1 and hi_ >= e["stop"]):
                    p = [x for x in k["acik"] if x["id"] == e["id"]][0]
                    _kapat(k, p, e["stop"], "stop, aynı mumda", UCRET_STOP, mesajlar)
            else:
                k["sayac"]["atlanan"] += 1
                print(f"Kâğıt: {e['id']} atlandı ({durum})")
            continue
        kalan.append(e)
    k["emirler"] = kalan
    if mesajlar:
        B.send("\n".join(mesajlar), KANAL)


def bakim(state):
    """15 dakikada bir: emir iptal kuralları, fonlama ücreti, günlük özet."""
    k = _st(state)
    now = int(time.time())
    # iptal: 4H kapanış seviyenin öbür tarafında / haftalık kapanış EMA21'in öbür tarafında
    son4h = (now // H4) * H4
    kalan = []
    for e in k["emirler"]:
        ip = e.get("iptal", {})
        try:
            if ip.get("tur") == "4h_kapanis" and e.get("son_kontrol", 0) < son4h:
                rows = B.candles(e["inst"], "4H", 3)
                kapanislar = [float(r[4]) for r in rows if e["t"] <= int(r[0]) // 1000 and int(r[0]) // 1000 + H4 <= now]
                e["son_kontrol"] = son4h
                if any((e["yon"] == 1 and c < ip["seviye"]) or (e["yon"] == -1 and c > ip["seviye"]) for c in kapanislar):
                    k["sayac"]["iptal"] += 1
                    continue
            elif ip.get("tur") == "hafta_ema":
                hafta = ((now - 345600) // (7 * DAY)) * 7 * DAY + 345600      # bu haftanın başı (Pzt 00:00 UTC)
                if e.get("son_kontrol", 0) < hafta and hafta > e["t"]:
                    rows = B.candles(e["inst"], "1Wutc", 60)
                    c = [float(r[4]) for r in rows if int(r[0]) // 1000 + 7 * DAY <= now]
                    e["son_kontrol"] = hafta
                    if len(c) >= 21:
                        em = B.ema_series(c, 21)[-1]
                        if (e["yon"] == 1 and c[-1] < em) or (e["yon"] == -1 and c[-1] > em):
                            k["sayac"]["iptal"] += 1
                            continue
        except Exception as ex:
            print(f"Kâğıt: {e['id']} iptal kontrolü yapılamadı: {ex}")
        kalan.append(e)
    k["emirler"] = kalan

    # fonlama: 00:00, 08:00, 16:00 UTC; gerçekleşen oran, long pozitif oranda öder
    for p in k["acik"]:
        son_fon = (now // 28800) * 28800
        if p["fon_t"] < son_fon:
            try:
                r = B.api("/api/v5/public/funding-rate-history", {"instId": p["inst"], "limit": "1"})
                oran = float(r[0].get("realizedRate") or r[0].get("fundingRate") or 0) if r else 0.0
                p["fonlama"] = p.get("fonlama", 0.0) + oran * p["notional"] * p["yon"]
            except Exception as ex:
                print(f"Kâğıt: {p['inst']} fonlama alınamadı: {ex}")
            p["fon_t"] = son_fon

    # özet: günde iki kez, 06:00 ve 18:00 UTC (09:00 ve 21:00 TR) sonrası ilk çalışma
    yarim = (now - 6 * 3600) // (DAY // 2)
    fiyat = {}
    try:
        if k["acik"]:
            fiyat = _fiyatlar()
    except Exception as ex:
        print("Kâğıt: fiyatlar alınamadı:", ex)
    if k.get("son_ozet2") != yarim:
        k["son_ozet2"] = yarim
        ozet(k, fiyat)
    durum_yaz(k, fiyat)


def _acik_satirlari(k, fiyat):
    satir, toplam = [], 0.0
    for p in k["acik"]:
        px = fiyat.get(p["inst"])
        ek = ""
        if px:
            anlik = _r_hesap(p, px, UCRET_STOP)
            toplam += anlik
            ek = f", şu an {_fmt(px)} → {anlik:+.2f} $"
        sure = (time.time() - p["giris_t"]) / 3600
        satir.append(f"  {STR_AD[p['s']]} {B.short(p['inst'])} {'long' if p['yon'] == 1 else 'short'}: giriş {_fmt(p['giris_px'])}, "
                     f"stop {_fmt(p['stop'])}, kâr al {_fmt(p['tp'])}{ek} ({sure:.0f} saattir açık)")
    return satir, toplam


def durum_yaz(k, fiyat):
    """Anlık durumu kagit_durum.json'a yazar (tarama döngüsü bunu 'kagit-durum' dalına gönderir)."""
    try:
        acik = []
        for p in k["acik"]:
            px = fiyat.get(p["inst"])
            acik.append(dict(strateji=p["s"], coin=B.short(p["inst"]), yon="long" if p["yon"] == 1 else "short",
                             giris=p["giris_px"], stop=p["stop"], kar_al=p["tp"], anlik_fiyat=px,
                             anlik_sonuc=round(_r_hesap(p, px, UCRET_STOP), 3) if px else None,
                             teminat=round(p["teminat"], 2), acilis=time.strftime("%Y-%m-%d %H:%M", time.gmtime(p["giris_t"] + 10800))))
        bekleyen = [dict(strateji=e["s"], coin=B.short(e["inst"]), yon="long" if e["yon"] == 1 else "short",
                         giris=e["giris"], stop=e["stop"], kar_al=e["tp"],
                         bitis=time.strftime("%Y-%m-%d %H:%M", time.gmtime(e["bitis"] + 10800))) for e in k["emirler"]]
        son = [dict(x, cikis=time.strftime("%Y-%m-%d %H:%M", time.gmtime(x["cikis_t"] + 10800))) for x in k["kapanan"][-20:]]
        with open("kagit_durum.json", "w") as f:
            json.dump(dict(zaman_tr=time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 10800)),
                           bakiye=round(k["bakiye"], 2), acik=acik, bekleyen=bekleyen, son_kapananlar=son,
                           sayac=k["sayac"], toplam_islem=len(k["kapanan"])), f, ensure_ascii=False, indent=1)
    except Exception as ex:
        print("Kâğıt: durum yazılamadı:", ex)


def ozet(k, fiyat=None):
    fiyat = fiyat or {}
    now = time.time()
    son24 = [x for x in k["kapanan"] if x["cikis_t"] >= now - DAY]
    tum = k["kapanan"]
    gun = max((now - k["baslangic"]) / DAY, 0.01)
    satir = [f"📝 Kâğıt işlem — özet ({gun:.0f}. gün, {'sabah' if time.gmtime(now).tm_hour < 18 else 'akşam'})",
             f"Sanal bakiye: {k['bakiye']:.2f} $ (başlangıç {BAKIYE0:.0f} $, {k['bakiye'] - BAKIYE0:+.2f} $)",
             f"Son 24 saat: {len(son24)} işlem kapandı, {sum(x['sonuc'] for x in son24):+.2f} $",
             f"Toplam: {len(tum)} işlem, kazanan %{(sum(x['sonuc'] > 0 for x in tum) / len(tum) * 100) if tum else 0:.0f}"]
    for s in ("EMA21", "FVG", "K4H"):
        v = [x for x in tum if x["s"] == s]
        if v:
            satir.append(f"  {STR_AD[s]}: {len(v)} işlem, {sum(x['sonuc'] for x in v):+.2f} $")
    acik_s, anlik = _acik_satirlari(k, fiyat)
    satir.append(f"Açık işlem: {len(k['acik'])}/{MAX_ACIK}" + (f" (şu an toplam {anlik:+.2f} $)" if k["acik"] and fiyat else ""))
    satir += acik_s
    bek = {}
    for e in k["emirler"]:
        bek[e["s"]] = bek.get(e["s"], 0) + 1
    satir.append("Bekleyen emir: " + (", ".join(f"{STR_AD[s]} {n}" for s, n in bek.items()) if bek else "yok"))
    sy = k["sayac"]
    satir.append(f"Atlanan (yer/teminat yok): {sy['atlanan']}  |  iptal: {sy['iptal']}  |  süresi dolan: {sy['suresi_dolan']}")
    satir.append(f"Test beklentisi: 180 günde yaklaşık +89 $ (günde ~+0,5 $); kötü dönemde 18 $'a kadar geri gidiş olabilir.")
    B.send("\n".join(satir), KANAL)
