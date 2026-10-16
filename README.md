# okx-bot

## PA stratejisi: günlük kırılım + retest + red (ayrı sistem)

`pa_scan_once.py` + `.github/workflows/pa_scan.yml`. Mevcut hacim tarayıcısından tamamen bağımsızdır
(ayrı dosya, ayrı `pa_state.json`, ayrı cache ve concurrency grubu); sadece aynı Telegram botuna yazar.

- Short: günlükte yükselen yapı (HH-HL), son tepeyi oluşturan dip günlük KAPANIŞLA kırılır,
  fiyat uzaklaşıp seviyeye geri gelir, 1H mumda red (üst fitil, seviyenin altında kapanış).
- Long: tam tersi.
- Stop red mumunun fitili ötesi, TP1 = 1R, TP2 = sıradaki günlük yapı seviyesi (en az 2R).
- Her kurulum için sadece ilk red sinyali gönderilir.

TradingView: `pa_kirilim_retest.pine` aynı kuralları grafikte gösterir (1 saatlik grafikte),
sinyalde Alış/Satış Pozisyonu benzeri kutu ve giriş/SL/TP etiketleri çizer, alarm kurulabilir.

Geçmiş test: Actions → "PA Gecmis Test" → Run workflow (mesaj göndermez).
