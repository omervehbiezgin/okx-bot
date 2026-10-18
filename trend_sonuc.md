# Trend takip PA stratejisi — 365 günlük test
Tarih: 18.10.2026 09:32 (TR). 64 coin. **Eğitim ilk 240 gün, doğrulama son 125 gün.** Seçimler sadece eğitime göre. Komisyon maker %0.02 / taker %0.05; long için funding 8 saatte %0.01. "Kazanan": kârla kapanan işlem oranı. Portföy sütunu: coin başına 1, aynı anda en fazla 5 pozisyon. Toplam 600 ayar denendi: en iyisi şans eseri iyi görünebilir, asıl ölçü doğrulama sütunudur. Veri: 64 coin; alınamayan 0, 90 günden kısa geçmişli 5.

## 1) Eğitim dönemine göre en iyi 25 ayar
| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |
|---|---|---|---|---|---|---|---|---|---|
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc | 3069 / %29 / +355.5 | 1408 / %23 / -136.0 | 4477 (~368/ay) | %27 | **+219.5** | +0.05 | 68 | 2.0 g | +75.1 / 47.2 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 3R · btc | 3061 / %28 / +329.5 | 1411 / %24 / -93.9 | 4472 (~368/ay) | %27 | **+235.5** | +0.05 | 80 | 4.1 g | +85.3 / 34.4 |
| 4H · piyasa · stop 1.0 ATR · sabit TP 3R · btc | 3248 / %28 / +295.5 | 1515 / %26 / -3.8 | 4763 (~391/ay) | %28 | **+291.7** | +0.06 | 60 | 3.2 g | +43.6 / 48.0 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 2R · btc | 3061 / %37 / +291.0 | 1411 / %31 / -109.7 | 4472 (~368/ay) | %35 | **+181.3** | +0.04 | 55 | 2.7 g | +72.6 / 38.7 |
| 4H · limit @seviye · stop 0.5 ATR · sabit TP 5R · btc | 3046 / %19 / +287.5 | 1390 / %17 / -51.1 | 4436 (~365/ay) | %18 | **+236.4** | +0.05 | 71 | 1.1 g | +70.9 / 106.4 |
| 4H · piyasa · stop 1.0 ATR · sabit TP 2R · btc | 3248 / %37 / +282.6 | 1515 / %33 / -60.0 | 4763 (~391/ay) | %36 | **+222.5** | +0.05 | 49 | 2.1 g | +85.0 / 43.3 |
| 1D · piyasa · stop 0.5 ATR · sabit TP 5R · BTC filtresiz | 800 / %27 / +280.1 | 427 / %22 / +17.9 | 1227 (~101/ay) | %25 | **+298.0** | +0.24 | 49 | 10.9 g | +49.6 / 20.4 |
| 4H · piyasa · stop 1.5 ATR · sabit TP 2R · btc | 3214 / %37 / +269.6 | 1504 / %33 / -69.7 | 4718 (~388/ay) | %36 | **+199.9** | +0.04 | 55 | 3.7 g | +22.2 / 36.3 |
| 4H · piyasa · stop 1.5 ATR · sabit TP 3R · btc | 3214 / %28 / +252.8 | 1504 / %26 / -14.9 | 4718 (~388/ay) | %27 | **+237.9** | +0.05 | 68 | 5.8 g | +74.4 / 26.6 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 2R · btc | 3069 / %37 / +245.1 | 1408 / %32 / -85.4 | 4477 (~368/ay) | %35 | **+159.7** | +0.04 | 50 | 1.3 g | +12.4 / 68.7 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 5R · btc | 3069 / %19 / +238.8 | 1408 / %16 / -147.3 | 4477 (~368/ay) | %18 | **+91.5** | +0.02 | 132 | 3.5 g | +83.9 / 48.4 |
| 4H · piyasa · stop 0.5 ATR · sabit TP 5R · btc | 3245 / %19 / +232.4 | 1508 / %19 / +112.2 | 4753 (~391/ay) | %19 | **+344.6** | +0.07 | 71 | 2.7 g | +68.3 / 63.3 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 800 / %36 / +228.8 | 427 / %33 / +25.1 | 1227 (~101/ay) | %35 | **+253.8** | +0.21 | 30 | 7.5 g | +33.6 / 24.9 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 3R · btc+hacim | 2423 / %28 / +226.8 | 1145 / %25 / -9.5 | 3568 (~293/ay) | %27 | **+217.3** | +0.06 | 67 | 4.1 g | +101.1 / 31.6 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 800 / %35 / +223.6 | 427 / %32 / +26.0 | 1227 (~101/ay) | %34 | **+249.6** | +0.20 | 30 | 7.3 g | +19.5 / 21.2 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren stop 3×ATR · BTC filtresiz | 800 / %29 / +222.0 | 427 / %26 / +9.2 | 1227 (~101/ay) | %28 | **+231.2** | +0.19 | 47 | 11.4 g | +36.1 / 17.6 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren 3×ATR (1R'de başlar) · BTC filtresiz | 800 / %29 / +220.8 | 427 / %26 / +10.3 | 1227 (~101/ay) | %28 | **+231.1** | +0.19 | 47 | 11.4 g | +36.1 / 17.6 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 5R · btc | 3061 / %19 / +203.6 | 1411 / %16 / -196.4 | 4472 (~368/ay) | %18 | **+7.2** | +0.00 | 179 | 7.1 g | +71.0 / 35.2 |
| 1D · piyasa · stop 1.0 ATR · sabit TP 5R · BTC filtresiz | 684 / %31 / +203.6 | 390 / %25 / +46.7 | 1074 (~88/ay) | %29 | **+250.3** | +0.23 | 39 | 18.6 g | +6.9 / 22.6 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc+hacim | 2426 / %28 / +201.0 | 1143 / %24 / -67.0 | 3569 (~293/ay) | %27 | **+134.0** | +0.04 | 67 | 1.9 g | +112.5 / 38.8 |
| 4H · piyasa · stop 1.5 ATR · sabit TP 5R · btc | 3214 / %21 / +192.3 | 1504 / %18 / -33.2 | 4718 (~388/ay) | %20 | **+159.1** | +0.03 | 176 | 9.1 g | +66.0 / 24.3 |
| 4H · limit @seviye · stop 0.5 ATR · sabit TP 3R · btc | 3046 / %28 / +190.1 | 1390 / %25 / -55.2 | 4436 (~365/ay) | %27 | **+134.9** | +0.03 | 65 | 0.6 g | -11.2 / 118.8 |
| 1D · piyasa · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 684 / %47 / +189.9 | 390 / %37 / -6.1 | 1074 (~88/ay) | %43 | **+183.8** | +0.17 | 35 | 9.7 g | -2.3 / 20.4 |
| 1D · piyasa · stop 1.0 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 684 / %44 / +185.9 | 390 / %36 / +5.7 | 1074 (~88/ay) | %41 | **+191.7** | +0.18 | 35 | 9.0 g | +4.9 / 18.7 |
| 4H · piyasa · stop 0.5 ATR · sabit TP 3R · btc | 3245 / %28 / +185.0 | 1508 / %27 / +31.3 | 4753 (~391/ay) | %27 | **+216.3** | +0.05 | 63 | 1.4 g | +14.8 / 74.6 |

## 2) Her çıkış türünün en iyi ayarı (eğitime göre)
| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |
|---|---|---|---|---|---|---|---|---|---|
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 2R · btc | 3061 / %37 / +291.0 | 1411 / %31 / -109.7 | 4472 (~368/ay) | %35 | **+181.3** | +0.04 | 55 | 2.7 g | +72.6 / 38.7 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc | 3069 / %29 / +355.5 | 1408 / %23 / -136.0 | 4477 (~368/ay) | %27 | **+219.5** | +0.05 | 68 | 2.0 g | +75.1 / 47.2 |
| 4H · limit @seviye · stop 0.5 ATR · sabit TP 5R · btc | 3046 / %19 / +287.5 | 1390 / %17 / -51.1 | 4436 (~365/ay) | %18 | **+236.4** | +0.05 | 71 | 1.1 g | +70.9 / 106.4 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 800 / %35 / +223.6 | 427 / %32 / +26.0 | 1227 (~101/ay) | %34 | **+249.6** | +0.20 | 30 | 7.3 g | +19.5 / 21.2 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren stop 3×ATR · BTC filtresiz | 800 / %29 / +222.0 | 427 / %26 / +9.2 | 1227 (~101/ay) | %28 | **+231.2** | +0.19 | 47 | 11.4 g | +36.1 / 17.6 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 800 / %36 / +228.8 | 427 / %33 / +25.1 | 1227 (~101/ay) | %35 | **+253.8** | +0.21 | 30 | 7.5 g | +33.6 / 24.9 |
| 1D · piyasa · stop 0.5 ATR · OKX iz süren 3×ATR (1R'de başlar) · BTC filtresiz | 800 / %29 / +220.8 | 427 / %26 / +10.3 | 1227 (~101/ay) | %28 | **+231.1** | +0.19 | 47 | 11.4 g | +36.1 / 17.6 |
| 1D · piyasa · stop 0.5 ATR · yarısı 2R + kalanı iz süren 3×ATR · BTC filtresiz | 800 / %39 / +170.9 | 427 / %37 / +7.1 | 1227 (~101/ay) | %38 | **+178.0** | +0.15 | 26 | 11.4 g | +15.7 / 13.8 |
| 1D · piyasa · stop 0.5 ATR · günlük stop: 10 gün dibi · BTC filtresiz | 800 / %32 / +159.9 | 427 / %26 / +193.9 | 1227 (~101/ay) | %30 | **+353.7** | +0.29 | 36 | 10.1 g | +26.9 / 34.6 |
| 1D · piyasa · stop 1.0 ATR · günlük stop: 20 gün dibi · BTC filtresiz | 684 / %33 / +104.5 | 390 / %28 / +153.5 | 1074 (~88/ay) | %31 | **+258.0** | +0.24 | 49 | 18.8 g | +27.9 / 14.1 |

## 3) Zaman dilimi × giriş türü: en iyi ayar (eğitime göre)
| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |
|---|---|---|---|---|---|---|---|---|---|
| 1D · limit @seviye · stop 1.0 ATR · sabit TP 5R · BTC filtresiz | 710 / %27 / +164.5 | 387 / %22 / -5.5 | 1097 (~90/ay) | %25 | **+159.0** | +0.14 | 47 | 15.9 g | +6.5 / 28.8 |
| 1D · piyasa · stop 0.5 ATR · sabit TP 5R · BTC filtresiz | 800 / %27 / +280.1 | 427 / %22 / +17.9 | 1227 (~101/ay) | %25 | **+298.0** | +0.24 | 49 | 10.9 g | +49.6 / 20.4 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc | 3069 / %29 / +355.5 | 1408 / %23 / -136.0 | 4477 (~368/ay) | %27 | **+219.5** | +0.05 | 68 | 2.0 g | +75.1 / 47.2 |
| 4H · piyasa · stop 1.0 ATR · sabit TP 3R · btc | 3248 / %28 / +295.5 | 1515 / %26 / -3.8 | 4763 (~391/ay) | %28 | **+291.7** | +0.06 | 60 | 3.2 g | +43.6 / 48.0 |

## 4) Filtrelerin etkisi (her filtre için en iyi ayar, eğitime göre)
| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |
|---|---|---|---|---|---|---|---|---|---|
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc | 3069 / %29 / +355.5 | 1408 / %23 / -136.0 | 4477 (~368/ay) | %27 | **+219.5** | +0.05 | 68 | 2.0 g | +75.1 / 47.2 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 3R · btc+hacim | 2423 / %28 / +226.8 | 1145 / %25 / -9.5 | 3568 (~293/ay) | %27 | **+217.3** | +0.06 | 67 | 4.1 g | +101.1 / 31.6 |
| 4H · limit @seviye · stop 1.5 ATR · sabit TP 5R · btc+sadece long | 731 / %18 / +23.8 | 718 / %24 / +251.0 | 1449 (~119/ay) | %21 | **+274.8** | +0.19 | 45 | 4.0 g | +68.3 / 28.0 |
| 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc+hacim+sadece long | 665 / %27 / +14.5 | 639 / %28 / +55.1 | 1304 (~107/ay) | %27 | **+69.7** | +0.05 | 42 | 1.3 g | +71.5 / 30.4 |
| 1D · piyasa · stop 0.5 ATR · sabit TP 5R · BTC filtresiz | 800 / %27 / +280.1 | 427 / %22 / +17.9 | 1227 (~101/ay) | %25 | **+298.0** | +0.24 | 49 | 10.9 g | +49.6 / 20.4 |

## 5) Seçilen ayarın ayrıntısı: 4H · limit @seviye · stop 1.0 ATR · sabit TP 3R · btc
- Long: 1446 işlem, +57.3R · Short: 3031 işlem, +162.3R
- En iyi 3 gün: 01.12.2025 (+166.2R), 21.11.2025 (+114.6R), 31.01.2026 (+109.5R) → bu 3 gün olmadan **-170.8R**
- Aylık: 2025-10: 130 işlem -20.6R · 2025-11: 416 işlem +197.8R · 2025-12: 459 işlem +94.8R · 2026-01: 284 işlem +104.7R · 2026-02: 379 işlem +29.8R · 2026-03: 407 işlem -102.0R · 2026-04: 408 işlem -84.5R · 2026-05: 367 işlem +102.2R · 2026-06: 424 işlem +48.0R · 2026-07: 327 işlem -128.3R · 2026-08: 336 işlem -72.8R · 2026-09: 392 işlem +115.1R · 2026-10: 148 işlem -64.7R
- Portföy, aynı anda en fazla 3: 534 işlem, net +24.6R (eğitim -14.5 / doğrulama +39.1), en büyük düşüş 46.1R, haftada ~10.2 yeni işlem
- Portföy, aynı anda en fazla 5: 812 işlem, net +75.1R (eğitim +10.3 / doğrulama +64.8), en büyük düşüş 47.2R, haftada ~15.6 yeni işlem
- Portföy, aynı anda en fazla 10: 1453 işlem, net +136.9R (eğitim +63.9 / doğrulama +73.1), en büyük düşüş 76.6R, haftada ~27.9 yeni işlem
- Çıkış türleri: stop 3267, TP 1204, süre/açık 6

## 6) Şans seviyesi kontrolü
Aynı 600 ayar, her coinin mumları rastgele karıştırılmış veriyle (oynaklık aynı, trend yok) denendi. Gerçek veride sonuç bunun belirgin şekilde üstünde değilse şans eseri sayılmalı.
| Ayar | Eğitim: işlem / kazanan / net R | Doğrulama: işlem / kazanan / net R | Toplam işlem | Kazanan | Net R | R/işlem | En uzun kayıp serisi | Ort. tutma | Portföy (en fazla 5 açık): net R / en büyük düşüş |
|---|---|---|---|---|---|---|---|---|---|
| [karışık veri, eğitimde en iyi] 4H · limit @seviye · stop 1.0 ATR · sabit TP 5R · btc | 2508 / %18 / +168.1 | 1428 / %15 / -261.0 | 3936 (~324/ay) | %17 | **-92.8** | -0.02 | 37 | 3.0 g | -10.9 / 73.3 |
- gerçek veri: eğitimde en iyi 25 ayarın doğrulama ortalaması -34.2R, tüm ayarların doğrulama ortalaması +135.6R
- karışık veri: eğitimde en iyi 25 ayarın doğrulama ortalaması -216.9R, tüm ayarların doğrulama ortalaması -102.4R

Süre: 18 dk
