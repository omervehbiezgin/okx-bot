# okx-bot

## PA stratejisi (ayrı sistem)

`pa_scan_once.py` + `.github/workflows/pa_scan.yml`. Mevcut hacim tarayıcısından tamamen bağımsızdır
(ayrı dosya, ayrı `pa_state.json`, ayrı cache ve concurrency grubu); sadece aynı Telegram botuna yazar.

- 4H: tepe/dip yapısı (HH-HL / LH-LL) + EMA50 ile yön
- 1H: talep/arz bölgesi veya kırılan seviye
- 15m: bölgeye temasta engulfing veya pin bar
- Mesajda giriş, stop, TP1 (1R), TP2 (sıradaki seviye, en az 2R) ve %1 risk için pozisyon büyüklüğü

Geçmiş test: Actions → "PA Gecmis Test" → Run workflow (mesaj göndermez).
