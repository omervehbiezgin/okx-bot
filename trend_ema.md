# EMA periyodu ve kayma (slippage) testi — günlük trend stratejisi
64 coin, son 365 gün (eğitim ilk 240 / doğrulama son 125 gün). Kurgu: günlük kapanışla kırılım, sabah 08:00 TR piyasa girişi, stop kırılan seviye − 0,5 günlük ATR, BTC filtresi yok. Komisyon ve long funding dahil. Portföy: coin başına 1, aynı anda en fazla 5. Kayma: piyasa emriyle yapılan giriş ve stop/süre çıkışlarında, her işlemde fiyat aleyhe bu kadar kayar.

## Çıkış: sabit TP 5R (kur-unut)
| EMA | Tüm işlemler: sayı / kazanan / net R (kayma %0) | Eğitim / doğrulama net R | Şans seviyesi net R | Portföy 5 net R — kayma %0 · %0,05 · %0,1 · %0,25 · %0,5 | Portföy 5 en büyük düşüş (kayma %0,1) | Haftada işlem | Ort. stop % |
|---|---|---|---|---|---|---|---|
| yok | 1457 / %24 / +169.2 | +194.2 / -24.9 | -128.7 | +45.8 · +42.4 · +39.0 · +29.0 · +12.1 | 24.8 | 2.8 | 6.1 |
| 21 | 1422 / %24 / +188.6 | +215.5 / -26.9 | -122.9 | +44.8 · +41.4 · +38.0 · +27.7 · +10.7 | 24.8 | 2.8 | 6.1 |
| 50 | 1193 / %26 / +282.3 | +270.2 / +12.1 | -126.1 | +37.0 · +33.9 · +30.7 · +21.2 · +5.3 | 13.4 | 2.8 | 6.2 |
| 100 | 1009 / %26 / +244.6 | +296.8 / -52.1 | -100.8 | +43.7 · +40.8 · +38.0 · +29.5 · +15.3 | 19.0 | 2.4 | 6.3 |
| 200 | 882 / %26 / +178.5 | +294.8 / -116.3 | -76.6 | +29.6 · +26.7 · +23.8 · +15.0 · +0.4 | 14.9 | 2.5 | 6.1 |

## Çıkış: günlük stop 10 gün dibi (sabah güncelle)
| EMA | Tüm işlemler: sayı / kazanan / net R (kayma %0) | Eğitim / doğrulama net R | Şans seviyesi net R | Portföy 5 net R — kayma %0 · %0,05 · %0,1 · %0,25 · %0,5 | Portföy 5 en büyük düşüş (kayma %0,1) | Haftada işlem | Ort. stop % |
|---|---|---|---|---|---|---|---|
| yok | 1457 / %28 / +180.5 | +85.6 / +94.9 | -202.3 | +56.2 · +51.4 · +46.7 · +32.5 · +8.9 | 31.8 | 3.5 | 6.1 |
| 21 | 1422 / %28 / +209.6 | +109.9 / +99.7 | -195.1 | +81.5 · +77.4 · +73.2 · +60.8 · +40.1 | 22.7 | 3.2 | 6.1 |
| 50 | 1193 / %30 / +282.2 | +171.7 / +110.5 | -179.9 | +74.3 · +70.1 · +65.8 · +53.1 · +32.0 | 35.9 | 3.2 | 6.2 |
| 100 | 1009 / %31 / +306.1 | +237.5 / +68.5 | -160.8 | +70.9 · +66.8 · +62.7 · +50.4 · +30.0 | 35.3 | 3.2 | 6.3 |
| 200 | 882 / %30 / +159.9 | +248.3 / -88.5 | -106.0 | +32.2 · +27.9 · +23.6 · +10.8 · -10.6 | 34.0 | 3.1 | 6.1 |

Süre: 1 dk
