# okx-bot

## Trend botu (ayrı sistem)

`pa_bot.py` + `.github/workflows/pa_bot.yml`. Mevcut hacim tarayıcısından tamamen bağımsızdır (ayrı dosya,
ayrı `bot_state.json`, ayrı cache ve concurrency grubu); sadece aynı Telegram botuna yazar.

**Strateji (günlük trend takibi):**
- Coinler: OKX kripto USDT perpetual, 24s hacmi ≥ 5M USDT, hacimde ilk 80.
- Long: günlük mum (03:00 TR) son onaylı tepenin (önceki ve sonraki 3 günden yüksek) üstünde, tepe onaylandıktan
  sonraki ilk kez kapanır ve kapanış EMA50 üstündedir. Short tam tersi.
- Giriş: kapanıştan hemen sonra limit emir (1 saatte dolmazsa iptal). Stop: kırılan seviye ∓ 0,5 günlük ATR,
  emirle birlikte borsaya konur.
- Çıkış: her gün stop son 10 günün dibine/tepesine çekilir (sadece kâr yönünde). Sabit hedef yok, 60 gün sınırı.
- Risk: işlem başı bakiyenin %1'i, en fazla 8 pozisyon, coin başına 1, izole marjin, kaldıraç stop mesafesine göre
  (en fazla 10x). Bakiye başlangıcın %60'ının altına inerse yeni işlem açılmaz.

**Modlar:** OKX anahtarı yoksa kuru çalışma (sanal 100 USDT), anahtar varsa gözlem (emir yok), repo değişkeni
`PA_LIVE=1` ise canlı. Kurulum: Settings → Secrets → `OKX_API_KEY`, `OKX_API_SECRET`, `OKX_API_PASSPHRASE`
(alt hesap, sadece Okuma + İşlem izni, çekim izni KAPALI).

**Testler:** `pa_final.py` (2 yıllık kapsamlı test), `pa_final_risk.py`, `pa_trend_*.py`, `pa_mpa.py`; sonuç tabloları
`pa-test-sonuclari` dalında. Testler mesaj göndermez ve sadece elle çalıştırılır.
