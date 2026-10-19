"""
OKX günlük trend botu (PA trend stratejisi). Mevcut hacim tarayıcısından tamamen bağımsızdır;
sadece aynı Telegram botuna yazar.

Strateji (2 yıllık testte seçilen kurgu):
  - Coinler : OKX kripto USDT perpetual, 24s hacmi >= 5M USDT, hacimde ilk 80.
  - Sinyal  : günlük mum (UTC 00:00 = TR 03:00) son onaylı tepenin üstünde kapanır (tepe: önceki ve sonraki 3 günden
              yüksek), tepe onaylandıktan sonraki ilk kapanış, ve kapanış günlük EMA50'nin üstünde → LONG.
              Short tam tersi (son onaylı dibin altında kapanış, EMA50 altında).
  - Giriş   : kapanıştan hemen sonra o anki fiyata limit emir (1 saat içinde dolmazsa iptal).
  - Stop    : kırılan seviye ∓ 0,5 günlük ATR(14); emirle birlikte borsaya konur.
  - Çıkış   : her gün stop son 10 günün dibine (short: tepesine) çekilir, sadece kâr yönünde. Sabit hedef yok.
              60 günü dolduran pozisyon kapatılır.
  - Risk    : işlem başı bakiyenin PA_RISK yüzdesi (varsayılan %1), en fazla PA_MAX_POS (8) pozisyon, coin başına 1,
              sinyal fazlaysa 24s hacmi yüksek olan önce. İzole marjin, kaldıraç stop mesafesine göre (en fazla 10x).
  - Fren    : bakiye başlangıcın %60'ının altına inerse yeni işlem açılmaz.

Çalışma modları:
  - API anahtarı yoksa       : KURU ÇALIŞMA (kâğıt üstünde, 100 USDT varsayımı, sanal pozisyonlar izlenir).
  - Anahtar var, PA_LIVE!=1  : GÖZLEM (gerçek bakiye/pozisyon okunur, emir GÖNDERİLMEZ, "yapacaktım" bildirilir).
  - Anahtar var, PA_LIVE=1   : CANLI (emirler gönderilir).
Ortam değişkenleri: OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE, PA_LIVE, PA_DEMO (1 = OKX demo hesabı),
PA_RISK, PA_MAX_POS, PA_START_BALANCE, PA_DRY_BALANCE, TG_TOKEN, TG_CHAT_ID, BOT_MODE (daily/hourly/test/auto).
"""
import os
import sys
import json
import time
import hmac
import base64
import hashlib
import traceback
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta

import requests

import pa_scan_once as p

# ---------------- AYARLAR ----------------
RISK = float(os.getenv("PA_RISK") or 1.0)          # işlem başı risk, bakiyenin yüzdesi
MAX_POS = int(os.getenv("PA_MAX_POS") or 8)
LIVE = os.getenv("PA_LIVE", "") == "1"
DEMO = os.getenv("PA_DEMO", "") == "1"
DRY_BALANCE = float(os.getenv("PA_DRY_BALANCE") or 100)
START_BALANCE = float(os.getenv("PA_START_BALANCE") or 0)
# Sanal sermaye: >0 ise bot hesabın tamamı yerine bu tutarla başlamış gibi davranır (örn. 5000 USDT demo hesapta 100 USDT).
# Bakiye = sermaye + (hesabın şimdiki değeri − bot başladığındaki değeri); kâr/zarar bu tutara eklenir.
CAPITAL = float(os.getenv("PA_CAPITAL") or 0)
K = 3                       # tepe/dip onayı (gün)
EMA_N = 50
SK = 0.5                    # stop: seviye ∓ SK × ATR
DON_N = 10                  # günlük iz süren stop: son N günün dibi/tepesi
MAX_HOLD_DAYS = 60
MIN_SP, MAX_SP = 0.5, 15.0  # stop mesafesi % sınırları
ENTRY_SLIP = 0.001          # limit fiyatı: son fiyattan %0,1 aleyhe (hemen dolması için)
ENTRY_TIMEOUT = 3600        # dolmayan giriş emri bu kadar saniye sonra iptal
MAX_NOTIONAL_X = 2.0        # tek pozisyon büyüklüğü en fazla bakiyenin bu katı
MAX_MARGIN_USE = 0.8        # toplam teminat en fazla bakiyenin bu oranı
KILL_FRAC = 0.6             # bakiye başlangıcın bu oranının altına inerse yeni işlem yok
STATE_FILE = "bot_state.json"
TAG = "patb"                # bot emirlerinin clOrdId öneki
BASE = "https://www.okx.com"
TR = timezone(timedelta(hours=3))
DAY = 86400
# -----------------------------------------

session = requests.Session()
msgs = []


def log(t):
    print(t, flush=True)


def note(t):
    """Telegram özetine eklenecek satır."""
    log(t)
    msgs.append(t)


def fp(x):
    return f"{x:.6g}"


def short(inst):
    return inst.replace("-USDT-SWAP", "")


# ---------------- Strateji hesapları (testle birebir aynı) ----------------
def ema(c, n):
    out = [None] * len(c)
    if len(c) < n:
        return out
    e = sum(c[:n]) / n
    out[n - 1] = e
    k = 2 / (n + 1)
    for i in range(n, len(c)):
        e = c[i] * k + e * (1 - k)
        out[i] = e
    return out


def signal_at(s, i):
    """s: günlük seri (t,o,h,l,c), i: değerlendirilen kapanmış mumun indeksi. Sinyaller listesi."""
    h, l, c = s["h"], s["l"], s["c"]
    n = len(c)
    if i < EMA_N - 1 or i >= n:
        return []
    atr = p.atr_arr(s)
    e50 = ema(c, EMA_N)
    if atr[i] is None or e50[i] is None:
        return []
    ph, pl = p.pivots(h, l, 0, i, K)          # sadece i'ye kadarki veri (i dahil)
    res = []
    for d, piv in ((1, ph), (-1, pl)):
        conf = [x for x in piv if x[0] <= i - K]
        if not conf:
            continue
        idx, lvl = conf[-1]
        if (c[i] - lvl) * d <= 0:
            continue
        if any((c[j] - lvl) * d > 0 for j in range(idx + K, i)):
            continue                           # bu seviye daha önce kırılmış (kullanılmış)
        if (c[i] - e50[i]) * d <= 0:
            continue
        res.append(dict(dir=d, lvl=lvl, atr=atr[i], close=c[i], ema=e50[i], t=s["t"][i]))
    return res


def donchian(s, i, d):
    """i dahil son DON_N kapanmış günün dibi (long) / tepesi (short)."""
    lo = max(0, i - DON_N + 1)
    return min(s["l"][lo:i + 1]) if d == 1 else max(s["h"][lo:i + 1])


def leverage_for(sp):
    """Tasfiye fiyatı stopun belirgin şekilde ötesinde kalsın: 1/kaldıraç ≥ 1,5 × stop% + %0,5."""
    lev = int(1 / (1.5 * sp / 100 + 0.005))
    return max(1, min(10, lev))


def round_step(x, step, up):
    q = Decimal(str(step))
    v = (Decimal(str(x)) / q).to_integral_value(rounding=ROUND_UP if up else ROUND_DOWN) * q
    return float(v)


# ---------------- OKX ----------------
class OkxError(Exception):
    pass


class Okx:
    def __init__(self):
        self.key = os.getenv("OKX_API_KEY", "")
        self.secret = os.getenv("OKX_API_SECRET", "")
        self.passphrase = os.getenv("OKX_API_PASSPHRASE", "")
        self.has_keys = bool(self.key and self.secret and self.passphrase)
        self._inst = None
        self.pos_mode = "net_mode"

    def req(self, method, path, query=None, body=None):
        qs = ("?" + urlencode(query)) if query else ""
        body_s = json.dumps(body) if body is not None else ""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
            f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
        msg = ts + method + path + qs + body_s
        sign = base64.b64encode(hmac.new(self.secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
        hd = {"OK-ACCESS-KEY": self.key, "OK-ACCESS-SIGN": sign, "OK-ACCESS-TIMESTAMP": ts,
              "OK-ACCESS-PASSPHRASE": self.passphrase, "Content-Type": "application/json"}
        if DEMO:
            hd["x-simulated-trading"] = "1"
        for deneme in range(3):
            try:
                r = session.request(method, BASE + path + qs, data=body_s or None, headers=hd, timeout=15)
                j = r.json()
                break
            except Exception as e:
                if deneme == 2:
                    raise OkxError(f"{path}: bağlantı hatası {e}")
                time.sleep(2)
        if j.get("code") != "0":
            det = ""
            if j.get("data"):
                det = " | " + "; ".join(f"{x.get('sCode')} {x.get('sMsg')}" for x in j["data"] if isinstance(x, dict))
            raise OkxError(f"{path}: {j.get('code')} {j.get('msg')}{det}")
        return j["data"]

    # --- genel ---
    def instruments(self):
        if self._inst is None:
            data = p.api("/api/v5/public/instruments", {"instType": "SWAP"})
            self._inst = {d["instId"]: d for d in data}
        return self._inst

    def tradable(self):
        """Bu hesapta (demo ise demo hesapta) işlem görebilen canlı SWAP kontratları; anahtar yoksa None."""
        if not self.has_keys:
            return None
        data = self.req("GET", "/api/v5/public/instruments", {"instType": "SWAP"})
        return {d["instId"] for d in data if d.get("state", "live") == "live"}

    def last_price(self, inst):
        return float(p.api("/api/v5/market/ticker", {"instId": inst})[0]["last"])

    # --- hesap ---
    def load_config(self):
        cfg = self.req("GET", "/api/v5/account/config")[0]
        self.pos_mode = cfg.get("posMode", "net_mode")
        return cfg

    def balance(self):
        d = self.req("GET", "/api/v5/account/balance", {"ccy": "USDT"})[0]
        det = next((x for x in d.get("details", []) if x.get("ccy") == "USDT"), {})
        eq = float(det.get("eq") or d.get("totalEq") or 0)
        avail = float(det.get("availEq") or det.get("availBal") or eq)
        return eq, avail

    def positions(self):
        out = []
        for x in self.req("GET", "/api/v5/account/positions", {"instType": "SWAP"}):
            pos = float(x.get("pos") or 0)
            if pos == 0:
                continue
            side = x.get("posSide", "net")
            d = (1 if pos > 0 else -1) if side == "net" else (1 if side == "long" else -1)
            out.append(dict(inst=x["instId"], dir=d, sz=abs(pos), avg=float(x.get("avgPx") or 0),
                            ctime=int(x.get("cTime") or 0) // 1000, posSide=side, upl=float(x.get("upl") or 0),
                            mgnMode=x.get("mgnMode")))
        return out

    def pending_orders(self):
        return self.req("GET", "/api/v5/trade/orders-pending", {"instType": "SWAP"})

    def stop_orders(self):
        res = []
        for ot in ("conditional", "oco"):
            try:
                res += self.req("GET", "/api/v5/trade/orders-algo-pending", {"ordType": ot, "instType": "SWAP"})
            except OkxError as e:
                log(f"algo listesi ({ot}) alınamadı: {e}")
        return [x for x in res if x.get("slTriggerPx")]

    def positions_history(self, inst):
        return self.req("GET", "/api/v5/account/positions-history", {"instType": "SWAP", "instId": inst, "limit": "5"})

    # --- işlem ---
    def pos_side(self, d):
        return ("long" if d == 1 else "short") if self.pos_mode == "long_short_mode" else None

    def set_leverage(self, inst, lev, d):
        body = {"instId": inst, "lever": str(lev), "mgnMode": "isolated"}
        ps = self.pos_side(d)
        if ps:
            body["posSide"] = ps
        return self.req("POST", "/api/v5/account/set-leverage", body=body)

    def place_entry(self, inst, d, px, sz, stop, clid):
        body = {"instId": inst, "tdMode": "isolated", "side": "buy" if d == 1 else "sell", "ordType": "limit",
                "px": str(px), "sz": str(sz), "clOrdId": clid,
                "attachAlgoOrds": [{"slTriggerPx": str(stop), "slOrdPx": "-1", "slTriggerPxType": "last"}]}
        ps = self.pos_side(d)
        if ps:
            body["posSide"] = ps
        return self.req("POST", "/api/v5/trade/order", body=body)[0]

    def cancel_order(self, inst, ord_id):
        return self.req("POST", "/api/v5/trade/cancel-order", body={"instId": inst, "ordId": ord_id})

    def place_stop(self, inst, d, sz, stop):
        body = {"instId": inst, "tdMode": "isolated", "side": "sell" if d == 1 else "buy", "ordType": "conditional",
                "sz": str(sz), "slTriggerPx": str(stop), "slOrdPx": "-1", "slTriggerPxType": "last"}
        ps = self.pos_side(d)
        if ps:
            body["posSide"] = ps
        else:
            body["reduceOnly"] = True
        return self.req("POST", "/api/v5/trade/order-algo", body=body)[0]

    def amend_stop(self, inst, algo_id, stop):
        return self.req("POST", "/api/v5/trade/amend-algos",
                        body={"instId": inst, "algoId": algo_id, "newSlTriggerPx": str(stop)})

    def cancel_algos(self, items):
        return self.req("POST", "/api/v5/trade/cancel-algos", body=[{"instId": i, "algoId": a} for i, a in items])

    def close_position(self, inst, d):
        body = {"instId": inst, "mgnMode": "isolated"}
        ps = self.pos_side(d)
        if ps:
            body["posSide"] = ps
        return self.req("POST", "/api/v5/trade/close-position", body=body)


# ---------------- Durum ----------------
def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=1)


def daily_series(inst, n=300):
    s = p.fetch(inst, "1Dutc", DAY, n)
    return s


def last_closed_day_open(now):
    return (now // DAY) * DAY - DAY


# ---------------- Kâğıt (kuru çalışma) pozisyonları ----------------
def paper_check(st, now):
    """Sanal pozisyonların stoplarını 1H mumlarla kontrol eder (kuru çalışma)."""
    pp = st.setdefault("paper", {"bal": DRY_BALANCE, "pos": {}, "closed": []})
    for inst, ps in list(pp["pos"].items()):
        try:
            s = p.fetch(inst, "1H", 3600, 200)
        except Exception as e:
            log(f"{inst} 1H alınamadı: {e}")
            continue
        d = ps["dir"]
        for t, hi, lo in zip(s["t"], s["h"], s["l"]):
            if t < ps.get("checked", ps["t_in"]):
                continue
            hit = lo <= ps["stop"] if d == 1 else hi >= ps["stop"]
            if hit:
                pnl = (ps["stop"] - ps["entry"]) * d * ps["qty"]
                fee = (ps["entry"] + ps["stop"]) * ps["qty"] * 0.0005
                pp["bal"] += pnl - fee
                R = pnl / ps["risk"] if ps["risk"] else 0
                pp["closed"].append(dict(inst=inst, dir=d, pnl=pnl - fee, R=R, t=t))
                note(f"📕 [KAĞIT] {short(inst)} {'LONG' if d == 1 else 'SHORT'} kapandı (stop {fp(ps['stop'])}): "
                     f"{pnl - fee:+.2f} USDT ({R:+.1f}R) · sanal bakiye {pp['bal']:.2f}")
                del pp["pos"][inst]
                break
            ps["checked"] = t + 3600


# OKX'te kripto kategorisinde listelenen ama altına bağlı tokenler (hisse ve emtia kontratları zaten kategoriyle elenir)
NON_CRYPTO = {"PAXG", "XAUT", "XAU", "XAG", "KAU", "KAG", "DGX", "CGO"}


def universe(ok):
    """Hacme göre en büyük 80 kripto USDT perpetual; anahtar varsa sadece bu hesapta işlem görebilenler arasından."""
    n = p.MAX_SYMBOLS
    try:
        ok_set = ok.tradable()
    except OkxError as e:
        log(f"hesaptaki kontrat listesi alınamadı, filtresiz taranıyor: {e}")
        ok_set = None
    if ok_set is None:
        out = [x for x in p.get_symbols() if x.split("-")[0] not in NON_CRYPTO][:n]
        log("Taranan: " + " ".join(short(x) for x in out))
        return out
    p.MAX_SYMBOLS = 10 ** 6
    try:
        allsyms = p.get_symbols()
    finally:
        p.MAX_SYMBOLS = n
    out = [x for x in allsyms if x in ok_set and x.split("-")[0] not in NON_CRYPTO]
    if len(out) < len(allsyms):
        log(f"{len(allsyms) - len(out)} coin bu hesapta işlem görmediği için taranmadı")
    log("Taranan: " + " ".join(short(x) for x in out[:n]))
    return out[:n]


def virtual_balance(st, eq, avail):
    base = st.setdefault("real_start", eq)
    v = CAPITAL + (eq - base)
    return v, v - max(0.0, eq - avail)


# ---------------- Günlük rutin ----------------
def daily(ok, st, now):
    mode = "CANLI" if (ok.has_keys and LIVE) else ("GÖZLEM" if ok.has_keys else "KAĞIT İŞLEM (gerçek piyasa, emir yok)")
    if DEMO and ok.has_keys:
        mode = "DEMO " + mode
    day_open = last_closed_day_open(now)
    day_s = datetime.fromtimestamp(day_open, TR).strftime("%d.%m.%Y")
    note(f"🌅 Trend botu — günlük çalışma ({mode}) · {day_s} günlük mumu")

    inst_info = ok.instruments()
    positions, pend, stops = [], [], []
    if ok.has_keys:
        ok.load_config()
        eq, avail = ok.balance()
        if CAPITAL > 0:
            eq, avail = virtual_balance(st, eq, avail)
        positions = ok.positions()
        pend = [o for o in ok.pending_orders() if o.get("clOrdId", "").startswith(TAG)]
        stops = ok.stop_orders()
    else:
        paper_check(st, now)
        eq = st["paper"]["bal"]
        avail = eq
    start = START_BALANCE or st.setdefault("start_balance", eq)
    note(f"💰 Bakiye: {eq:.2f} USDT (başlangıç {start:.2f})")

    # 1) Açık pozisyonların stoplarını güncelle (son 10 gün dibi/tepesi), 60 gün kontrolü
    open_list = positions if ok.has_keys else [
        dict(inst=k, dir=v["dir"], sz=v["qty"], avg=v["entry"], ctime=v["t_in"]) for k, v in st["paper"]["pos"].items()]
    for ps in open_list:
        inst, d = ps["inst"], ps["dir"]
        try:
            s = daily_series(inst, 60)
            i = len(s["t"]) - 1
            if s["t"][i] != day_open:
                note(f"⚠️ {short(inst)}: günlük mum henüz kapanmamış görünüyor, stop güncellenmedi")
                continue
            don = donchian(s, i, d)
            last = ok.last_price(inst)
            if ok.has_keys:
                my = [x for x in stops if x["instId"] == inst]
                cur = None
                if my:
                    vals = [float(x["slTriggerPx"]) for x in my]
                    cur = max(vals) if d == 1 else min(vals)
            else:
                cur = st["paper"]["pos"][inst]["stop"]
            tick = float(inst_info[inst]["tickSz"])
            new = round_step(don, tick, up=(d == -1))
            if now - ps["ctime"] > MAX_HOLD_DAYS * DAY:
                if ok.has_keys and LIVE:
                    ok.close_position(inst, d)
                note(f"⏱ {short(inst)}: {MAX_HOLD_DAYS} gün doldu → pozisyon {'kapatıldı' if LIVE else 'kapatılacaktı'}")
                continue
            better = cur is None or (new - cur) * d > abs(cur) * 0.001
            valid = (last - new) * d > 0
            if better and valid:
                if ok.has_keys:
                    if LIVE:
                        if my:
                            try:
                                ok.amend_stop(inst, my[0]["algoId"], new)
                                if len(my) > 1:
                                    ok.cancel_algos([(inst, x["algoId"]) for x in my[1:]])
                            except OkxError as e:
                                log(f"{inst} stop değiştirilemedi ({e}), yeni stop konup eskisi iptal ediliyor")
                                ok.place_stop(inst, d, ps["sz"], new)
                                ok.cancel_algos([(inst, x["algoId"]) for x in my])
                        else:
                            ok.place_stop(inst, d, ps["sz"], new)
                    note(f"🔒 {short(inst)} {'LONG' if d == 1 else 'SHORT'}: stop {fp(cur) if cur else 'yok'} → {fp(new)}"
                         f"{'' if LIVE else ' (yapılacaktı)'}")
                else:
                    st["paper"]["pos"][inst]["stop"] = new
                    note(f"🔒 [KAĞIT] {short(inst)}: stop {fp(cur)} → {fp(new)}")
        except Exception as e:
            note(f"⚠️ {short(inst)} stop güncellemesinde hata: {e}")

    # 2) Dolmamış eski giriş emirlerini iptal et
    for o in pend:
        age = now - int(o.get("cTime", "0")) // 1000
        if age > ENTRY_TIMEOUT and LIVE:
            try:
                ok.cancel_order(o["instId"], o["ordId"])
                note(f"🗑 {short(o['instId'])}: dolmayan giriş emri iptal edildi")
            except OkxError as e:
                log(f"iptal hatası: {e}")

    # 3) Acil fren
    if eq < start * KILL_FRAC:
        note(f"🛑 ACİL FREN: bakiye {eq:.2f} < başlangıcın %{KILL_FRAC * 100:.0f}'ı ({start * KILL_FRAC:.2f}). "
             "Yeni işlem açılmıyor; mevcut stoplar çalışmaya devam ediyor.")
        return

    # 4) Yeni sinyaller
    held = {x["inst"] for x in open_list} | {o["instId"] for o in pend}
    slots = MAX_POS - len(held)
    syms = universe(ok)
    found = []
    for inst in syms:
        try:
            s = daily_series(inst)
            time.sleep(0.1)
        except Exception as e:
            log(f"{inst} veri hatası: {e}")
            continue
        i = len(s["t"]) - 1
        if i < 0 or s["t"][i] != day_open:
            continue
        for sg in signal_at(s, i):
            sg["inst"] = inst
            found.append(sg)
    note(f"🔎 {len(syms)} coin tarandı, {len(found)} sinyal. Açık/bekleyen: {len(held)}/{MAX_POS}")

    used_margin = 0.0
    if ok.has_keys:
        used_margin = max(0.0, eq - avail)
    acilan = 0
    for sg in found:                      # get_symbols hacme göre sıralı → öncelik hacim
        inst, d = sg["inst"], sg["dir"]
        yon = "🟢 LONG" if d == 1 else "🔴 SHORT"
        if inst in held:
            note(f"• {yon} {short(inst)}: zaten pozisyon/emir var, atlandı")
            continue
        if acilan >= slots:
            note(f"• {yon} {short(inst)}: yer yok ({MAX_POS} pozisyon dolu), atlandı")
            continue
        info = inst_info.get(inst)
        if not info:
            continue
        tick, lot, minsz = float(info["tickSz"]), float(info["lotSz"]), float(info["minSz"])
        ctval = float(info["ctVal"])
        last = ok.last_price(inst)
        px = round_step(last * (1 + d * ENTRY_SLIP), tick, up=(d == 1))
        stop = round_step(sg["lvl"] - d * SK * sg["atr"], tick, up=(d == -1))
        R = (px - stop) * d
        if R <= 0:
            note(f"• {yon} {short(inst)}: fiyat stopun ötesine geçmiş, atlandı")
            continue
        sp = R / px * 100
        if sp < MIN_SP or sp > MAX_SP:
            note(f"• {yon} {short(inst)}: stop mesafesi %{sp:.2f} sınır dışında, atlandı")
            continue
        risk_usd = eq * RISK / 100
        contracts = round_step(risk_usd / R / ctval, lot, up=False)
        notional = contracts * ctval * px
        if notional > MAX_NOTIONAL_X * eq:
            contracts = round_step(MAX_NOTIONAL_X * eq / (ctval * px), lot, up=False)
            notional = contracts * ctval * px
        if contracts < minsz:
            note(f"• {yon} {short(inst)}: hesaplanan miktar borsa minimumunun altında "
                 f"(min {minsz} kontrat = {minsz * ctval * px:.2f} USDT), atlandı")
            continue
        lev = min(leverage_for(sp), int(float(info.get("lever") or 10)))
        margin = notional / lev
        if used_margin + margin > MAX_MARGIN_USE * eq:
            note(f"• {yon} {short(inst)}: teminat sınırı (%{MAX_MARGIN_USE * 100:.0f}) aşılacaktı, atlandı")
            continue
        real_risk = contracts * ctval * R
        line = (f"{yon} {short(inst)} · seviye {fp(sg['lvl'])} kırıldı · giriş {fp(px)} · stop {fp(stop)} (%{sp:.2f}) · "
                f"{contracts:g} kontrat ≈ {notional:.2f} USDT · {lev}x → teminat {margin:.2f} USDT · "
                f"risk {real_risk:.2f} USDT")
        if ok.has_keys and LIVE:
            try:
                ok.set_leverage(inst, lev, d)
                clid = f"{TAG}{int(now)}{acilan}"
                r = ok.place_entry(inst, d, px, contracts, stop, clid)
                st.setdefault("entries", {})[inst] = dict(dir=d, stop=stop, lvl=sg["lvl"], t=int(now),
                                                           ordId=r.get("ordId"), risk=real_risk)
                note("✅ " + line)
            except OkxError as e:
                if "51001" in str(e):
                    note(f"• {yon} {short(inst)}: bu coin {'demo ' if DEMO else ''}hesapta işlem görmüyor, atlandı")
                else:
                    note(f"❌ {short(inst)} emir hatası: {e}")
                continue
        elif ok.has_keys:
            note("📝 (yapılacaktı) " + line)
        else:
            qty = contracts * ctval
            st["paper"]["pos"][inst] = dict(dir=d, entry=px, stop=stop, qty=qty, risk=real_risk, t_in=int(now),
                                             checked=int(now))
            note("📝 [KAĞIT] " + line)
        used_margin += margin
        acilan += 1
        held.add(inst)
    if not found:
        note("Bugün sinyal yok.")
    if not ok.has_keys:
        pp = st["paper"]
        acik = ", ".join(f"{short(k)} {'L' if v['dir'] == 1 else 'S'} (stop {fp(v['stop'])})" for k, v in pp["pos"].items())
        kap = pp["closed"]
        note(f"📊 [KAĞIT] sanal bakiye {pp['bal']:.2f} USDT · açık: {acik or 'yok'} · kapanan işlem: {len(kap)}"
             + (f" (toplam {sum(x['pnl'] for x in kap):+.2f} USDT)" if kap else ""))
    st["last_daily"] = day_open


# ---------------- Saatlik bakım ----------------
def hourly(ok, st, now):
    if not ok.has_keys:
        before = len(st.get("paper", {}).get("closed", []))
        if st.get("paper", {}).get("pos"):
            paper_check(st, now)
        return len(st.get("paper", {}).get("closed", [])) != before
    ok.load_config()
    inst_info = ok.instruments()
    positions = ok.positions()
    stops = ok.stop_orders()
    pend = [o for o in ok.pending_orders() if o.get("clOrdId", "").startswith(TAG)]
    known = st.setdefault("known", {})
    cur = {x["inst"]: x for x in positions}
    changed = False
    # yeni açılan pozisyonlar
    for inst, ps in cur.items():
        if inst not in known:
            e = st.get("entries", {}).get(inst, {})
            note(f"📗 Pozisyon açıldı: {'🟢 LONG' if ps['dir'] == 1 else '🔴 SHORT'} {short(inst)} · "
                 f"ortalama {fp(ps['avg'])} · {ps['sz']:g} kontrat" + (f" · stop {fp(e['stop'])}" if e.get("stop") else ""))
            known[inst] = dict(dir=ps["dir"], avg=ps["avg"], t=ps["ctime"], risk=e.get("risk"))
            changed = True
    # kapanan pozisyonlar
    for inst in list(known):
        if inst not in cur:
            k = known.pop(inst)
            pnl_s = ""
            try:
                h = ok.positions_history(inst)
                if h:
                    pnl = float(h[0].get("realizedPnl") or h[0].get("pnl") or 0)
                    R = pnl / k["risk"] if k.get("risk") else None
                    pnl_s = f" · sonuç {pnl:+.2f} USDT" + (f" ({R:+.1f}R)" if R is not None else "")
            except OkxError as e:
                log(f"geçmiş alınamadı: {e}")
            note(f"📕 Pozisyon kapandı: {'LONG' if k['dir'] == 1 else 'SHORT'} {short(inst)}{pnl_s}")
            st.get("entries", {}).pop(inst, None)
            changed = True
    # stopsuz pozisyon kontrolü
    for inst, ps in cur.items():
        if not any(x["instId"] == inst for x in stops):
            e = st.get("entries", {}).get(inst)
            d = ps["dir"]
            tick = float(inst_info[inst]["tickSz"])
            stop = e["stop"] if e else round_step(ps["avg"] * (1 - d * 0.08), tick, up=(d == -1))
            if LIVE:
                try:
                    ok.place_stop(inst, d, ps["sz"], stop)
                    note(f"🛡 {short(inst)}: stop bulunamadı, stop konuldu ({fp(stop)})")
                except OkxError as ex:
                    note(f"❌ {short(inst)}: STOP KONULAMADI! {ex} — lütfen elle kontrol edin")
            else:
                note(f"🛡 {short(inst)}: stop yok, {fp(stop)} konulacaktı")
            changed = True
    # dolmamış eski giriş emirleri
    for o in pend:
        age = now - int(o.get("cTime", "0")) // 1000
        if age > ENTRY_TIMEOUT and LIVE:
            try:
                ok.cancel_order(o["instId"], o["ordId"])
                note(f"🗑 {short(o['instId'])}: 1 saatte dolmayan giriş emri iptal edildi")
                changed = True
            except OkxError as e:
                log(f"iptal hatası: {e}")
    return changed


# ---------------- Ana akış ----------------
def connection_report(ok, st):
    msg = "✅ Trend botu bağlantı testi. "
    if not ok.has_keys:
        return msg + "OKX anahtarı tanımlı değil (kuru çalışma)."
    cfg = ok.load_config()
    eq, avail = ok.balance()
    lv = str(cfg.get("acctLv", ""))
    lv_ad = {"1": "Spot (vadeli işlem YAPILAMAZ)", "2": "Vadeli (Futures)", "3": "Çoklu para birimi marjin",
             "4": "Portföy marjin"}.get(lv, lv)
    if CAPITAL > 0:
        msg += f"Sanal sermaye {CAPITAL:.0f} USDT (hesabın tamamı {eq:.2f} USDT, işlemler {CAPITAL:.0f} USDT'ye göre). "
        eq, avail = virtual_balance(st, eq, avail)
    msg += (f"OKX bağlantısı tamam · bakiye {eq:.2f} USDT · hesap modu: {lv_ad} · pozisyon modu {ok.pos_mode} · "
            f"emir: {'EVET' if LIVE else 'hayır (gözlem)'} · demo: {'evet' if DEMO else 'hayır (GERÇEK hesap)'}")
    if lv == "1":
        msg += ("\n⚠️ Hesap Spot modunda. OKX → işlem ekranı ayarları → Hesap modu → 'Vadeli' (Futures) seçilmeli, "
                "yoksa bot işlem açamaz.")
    if eq <= 0:
        msg += "\n⚠️ Bakiye 0 görünüyor: USDT'nin işlem (trading) hesabında olduğundan emin olun."
    else:
        msg += "\nBot bundan sonra her gün 03:04'te tarama yapıp sinyal varsa emir verecek."
    return msg


def main():
    st = load_state()
    ok = Okx()
    now = int(time.time())
    mode = os.getenv("BOT_MODE", "auto") or "auto"
    if mode == "auto":
        hour = datetime.fromtimestamp(now, timezone.utc).hour
        mode = "daily" if (st.get("last_daily") != last_closed_day_open(now) and hour < 2) else "hourly"
    log(f"Mod: {mode} · anahtar: {'var' if ok.has_keys else 'yok'} · canlı: {LIVE} · demo: {DEMO}")
    try:
        # Hesap bağlamı değişirse (kuru çalışma → demo → gerçek) eski durum taşınmaz: başlangıç bakiyesi, acil fren ve
        # pozisyon takibi yeni hesaba göre baştan kurulur.
        ctx = f"{'anahtar' if ok.has_keys else 'kuru'}-{'demo' if DEMO else 'gercek'}"
        if st.get("ctx") != ctx:
            if st.get("ctx") or st:
                log(f"Hesap bağlamı değişti ({st.get('ctx')} → {ctx}): durum sıfırlandı")
            st.clear()
            st["ctx"] = ctx
        if mode == "test" or (ok.has_keys and not st.get("baglanti_raporu")):
            p.send(connection_report(ok, st))
            if ok.has_keys:
                st["baglanti_raporu"] = int(now)
            if mode == "test":
                return
        if mode == "closeall":
            # Elle tetiklenen temizlik: hesaptaki tüm SWAP pozisyonlarını kapatır, bekleyen bot emirlerini ve stopları siler
            if not ok.has_keys or not LIVE:
                p.send("Kapatma: OKX anahtarı yok veya emir kapalı, bir şey yapılmadı.")
                return
            ok.load_config()
            sat = []
            for o in ok.pending_orders():
                if o.get("clOrdId", "").startswith(TAG):
                    try:
                        ok.cancel_order(o["instId"], o["ordId"])
                    except OkxError as e:
                        log(f"emir iptal edilemedi {o['instId']}: {e}")
            for x in ok.positions():
                try:
                    ok.close_position(x["inst"], x["dir"])
                    sat.append(f"{'LONG' if x['dir'] == 1 else 'SHORT'} {short(x['inst'])} (k/z {x['upl']:+.2f} USDT)")
                except OkxError as e:
                    sat.append(f"{short(x['inst'])}: kapatılamadı ({e})")
            items = [(a["instId"], a["algoId"]) for a in ok.stop_orders()]
            for i in range(0, len(items), 10):
                try:
                    ok.cancel_algos(items[i:i + 10])
                except OkxError as e:
                    log(f"stop iptal: {e}")
            # Temizlikten sonra istatistik sıfırdan başlar: sanal sermayenin ve acil frenin başlangıç noktası yeniden alınır
            for k in ("entries", "known", "real_start", "start_balance"):
                st.pop(k, None)
            p.send("🧹 Trend botu: tüm pozisyonlar kapatıldı" + (DEMO and " (DEMO)" or "") + "\n" +
                   ("\n".join("• " + x for x in sat) if sat else "Açık pozisyon yoktu."))
            return
        if mode == "daily":
            daily(ok, st, now)
            p.send("\n".join(msgs) + "\nℹ️ Otomatik işlem botu, yatırım tavsiyesi değildir.")
        else:
            if hourly(ok, st, now) and msgs:
                p.send("\n".join(msgs))
    except Exception as e:
        traceback.print_exc()
        p.send(f"❌ Trend botu hatası ({mode}): {e}")
        raise
    finally:
        save_state(st)


if __name__ == "__main__":
    main()
