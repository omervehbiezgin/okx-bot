# Günlük trend ayarları — gerçekçi sağlamlık analizi
64 coin, 365 gün (eğitim ilk 240 gün, doğrulama son 125 gün). "sabah": günlük kapanış 03:00 TR, giriş ve günlük stop güncellemesi 08:00 TR. Şans seviyesi: aynı sabit ayar, mumları karıştırılmış 3 farklı veri setinde (ortalama). Portföy: coin başına 1, aynı anda en fazla 5 pozisyon (işlem başı %1 riskte 1R ≈ bakiyenin %1'i).

| Ayar | Tüm işlemler: sayı / kazanan / net R | Eğitim net R | Doğrulama net R | Şans seviyesi net R | Portföy 5: net R (eğitim / doğrulama) | Portföy 5: en büyük düşüş R | Haftada işlem | Ort. tutma |
|---|---|---|---|---|---|---|---|---|
| piyasa · stop 0.5 ATR · günlük stop: 10 gün dibi · BTC filtresiz | 1227 / %30 / +353.7 | +159.9 | +193.9 | -193.0 | +26.9 (+18.4 / +8.5) | 34.6 | 3.3 | 10.1 g |
| piyasa · stop 0.5 ATR · günlük stop: 10 gün dibi · btc | 966 / %30 / +246.0 | +21.7 | +224.4 | -67.1 | +69.8 (+26.8 / +43.0) | 23.3 | 2.7 | 10.2 g |
| piyasa · stop 0.5 ATR · günlük stop: 10 gün dibi · btc+sadece long | 308 / %26 / +242.7 | -59.3 | +302.0 | -68.3 | +81.1 (-3.6 / +84.7) | 19.0 | 1.3 | 9.2 g |
| piyasa · stop 0.5 ATR · günlük stop: 20 gün dibi · BTC filtresiz | 1227 / %25 / +273.1 | +93.9 | +179.2 | -266.9 | +83.4 (+51.8 / +31.5) | 10.6 | 2.1 | 14.2 g |
| piyasa · stop 0.5 ATR · günlük stop: 20 gün dibi · btc | 966 / %24 / +163.3 | -43.6 | +206.9 | -85.5 | +52.2 (+29.7 / +22.5) | 12.5 | 1.9 | 14.3 g |
| piyasa · stop 0.5 ATR · günlük stop: 20 gün dibi · btc+sadece long | 308 / %20 / +205.9 | -93.5 | +299.5 | -79.9 | +43.0 (-6.2 / +49.2) | 20.4 | 1.1 | 12.0 g |
| piyasa · stop 0.5 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 1227 / %34 / +249.6 | +223.6 | +26.0 | -109.8 | +19.5 (+27.0 / -7.5) | 21.2 | 4.2 | 7.3 g |
| piyasa · stop 0.5 ATR · OKX iz süren stop 2×ATR · btc | 966 / %34 / +110.5 | +43.7 | +66.8 | -46.9 | +27.8 (+20.7 / +7.1) | 22.0 | 3.7 | 7.2 g |
| piyasa · stop 0.5 ATR · OKX iz süren stop 2×ATR · btc+sadece long | 308 / %38 / +123.0 | -20.7 | +143.7 | -39.2 | +29.9 (-9.2 / +39.1) | 27.6 | 2.2 | 3.0 g |
| piyasa · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 1227 / %35 / +253.8 | +228.8 | +25.1 | -113.6 | +33.6 (+32.5 / +1.0) | 24.9 | 3.9 | 7.5 g |
| piyasa · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc | 966 / %34 / +113.2 | +52.0 | +61.2 | -45.9 | +21.0 (+18.1 / +2.9) | 22.3 | 3.7 | 7.5 g |
| piyasa · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc+sadece long | 308 / %39 / +116.0 | -23.4 | +139.4 | -39.3 | +27.0 (-7.8 / +34.8) | 25.9 | 2.2 | 3.3 g |
| piyasa · stop 0.5 ATR · sabit TP 5R · BTC filtresiz | 1227 / %25 / +298.0 | +280.1 | +17.9 | -124.3 | +49.6 (+48.1 / +1.4) | 20.4 | 2.7 | 10.9 g |
| piyasa · stop 0.5 ATR · sabit TP 5R · btc | 966 / %24 / +200.8 | +152.1 | +48.6 | -33.7 | +76.9 (+64.3 / +12.5) | 13.1 | 2.2 | 11.6 g |
| piyasa · stop 0.5 ATR · sabit TP 5R · btc+sadece long | 308 / %27 / +142.5 | -25.3 | +167.9 | -59.5 | +44.4 (+2.5 / +41.8) | 18.9 | 1.5 | 6.9 g |
| piyasa · stop 1.0 ATR · günlük stop: 10 gün dibi · BTC filtresiz | 1074 / %37 / +290.4 | +154.5 | +135.9 | -114.6 | +51.7 (+30.7 / +21.0) | 9.1 | 2.2 | 13.0 g |
| piyasa · stop 1.0 ATR · günlük stop: 10 gün dibi · btc | 844 / %38 / +225.9 | +53.7 | +172.2 | -37.9 | +32.5 (+18.1 / +14.4) | 11.7 | 2.2 | 13.1 g |
| piyasa · stop 1.0 ATR · günlük stop: 10 gün dibi · btc+sadece long | 285 / %32 / +189.2 | -39.3 | +228.5 | -57.0 | +34.3 (+0.3 / +33.9) | 15.8 | 1.2 | 11.9 g |
| piyasa · stop 1.0 ATR · günlük stop: 20 gün dibi · BTC filtresiz | 1074 / %31 / +258.0 | +104.5 | +153.5 | -180.9 | +27.9 (+32.0 / -4.1) | 14.1 | 1.8 | 18.8 g |
| piyasa · stop 1.0 ATR · günlük stop: 20 gün dibi · btc | 844 / %30 / +175.6 | -5.8 | +181.4 | -57.9 | +22.8 (+12.3 / +10.6) | 18.0 | 1.7 | 18.9 g |
| piyasa · stop 1.0 ATR · günlük stop: 20 gün dibi · btc+sadece long | 285 / %28 / +188.8 | -64.6 | +253.4 | -72.8 | +32.1 (+2.2 / +29.8) | 16.0 | 1.0 | 16.5 g |
| piyasa · stop 1.0 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 1074 / %41 / +191.7 | +185.9 | +5.7 | -63.6 | +4.9 (+19.2 / -14.3) | 18.7 | 3.3 | 9.0 g |
| piyasa · stop 1.0 ATR · OKX iz süren stop 2×ATR · btc | 844 / %41 / +120.6 | +74.9 | +45.7 | -24.7 | +20.7 (+15.2 / +5.5) | 16.9 | 3.0 | 8.8 g |
| piyasa · stop 1.0 ATR · OKX iz süren stop 2×ATR · btc+sadece long | 285 / %44 / +77.7 | -15.3 | +93.1 | -31.6 | +19.7 (-5.8 / +25.5) | 16.8 | 1.8 | 3.9 g |
| piyasa · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 1074 / %43 / +183.8 | +189.9 | -6.1 | -75.2 | -2.3 (+18.3 / -20.6) | 20.4 | 3.1 | 9.7 g |
| piyasa · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc | 844 / %44 / +113.8 | +81.5 | +32.3 | -27.3 | +24.7 (+26.9 / -2.2) | 14.8 | 2.8 | 9.5 g |
| piyasa · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc+sadece long | 285 / %47 / +75.3 | -12.4 | +87.8 | -34.1 | +17.1 (-6.5 / +23.6) | 15.9 | 1.7 | 5.0 g |
| piyasa · stop 1.0 ATR · sabit TP 5R · BTC filtresiz | 1074 / %29 / +250.3 | +203.6 | +46.7 | -104.6 | +6.9 (+32.2 / -25.3) | 22.6 | 1.8 | 18.6 g |
| piyasa · stop 1.0 ATR · sabit TP 5R · btc | 844 / %27 / +147.6 | +75.8 | +71.8 | -27.3 | +40.9 (+44.9 / -4.0) | 16.2 | 1.9 | 19.2 g |
| piyasa · stop 1.0 ATR · sabit TP 5R · btc+sadece long | 285 / %29 / +137.6 | -49.4 | +187.0 | -71.2 | +13.4 (-10.9 / +24.3) | 20.3 | 1.2 | 11.8 g |
| sabah · stop 0.5 ATR · günlük stop: 10 gün dibi (sabah güncelle) · BTC filtresiz | 1190 / %30 / +285.3 | +174.8 | +110.5 | -179.9 | +76.4 (+13.5 / +63.0) | 33.2 | 3.2 | 10.1 g |
| sabah · stop 0.5 ATR · günlük stop: 10 gün dibi (sabah güncelle) · btc | 943 / %29 / +231.7 | +79.9 | +151.8 | -69.8 | +68.0 (+33.1 / +34.9) | 21.9 | 2.6 | 10.1 g |
| sabah · stop 0.5 ATR · günlük stop: 10 gün dibi (sabah güncelle) · btc+sadece long | 290 / %26 / +182.3 | -49.5 | +231.9 | -67.9 | +44.0 (-6.7 / +50.7) | 18.1 | 1.2 | 9.2 g |
| sabah · stop 0.5 ATR · günlük stop: 20 gün dibi (sabah güncelle) · BTC filtresiz | 1190 / %25 / +201.2 | +86.7 | +114.5 | -239.9 | +54.7 (+44.6 / +10.1) | 11.6 | 2.2 | 14.3 g |
| sabah · stop 0.5 ATR · günlük stop: 20 gün dibi (sabah güncelle) · btc | 943 / %24 / +147.5 | -7.2 | +154.7 | -80.4 | +38.7 (+33.5 / +5.3) | 18.0 | 2.0 | 14.5 g |
| sabah · stop 0.5 ATR · günlük stop: 20 gün dibi (sabah güncelle) · btc+sadece long | 290 / %20 / +167.4 | -83.2 | +250.6 | -82.7 | +32.3 (-9.6 / +41.9) | 20.2 | 1.1 | 12.3 g |
| sabah · stop 0.5 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 1190 / %33 / +203.9 | +220.3 | -16.4 | -122.5 | -2.2 (+0.8 / -3.0) | 31.9 | 4.4 | 7.2 g |
| sabah · stop 0.5 ATR · OKX iz süren stop 2×ATR · btc | 943 / %33 / +133.5 | +98.8 | +34.7 | -47.3 | -10.2 (-12.3 / +2.1) | 37.6 | 3.9 | 7.2 g |
| sabah · stop 0.5 ATR · OKX iz süren stop 2×ATR · btc+sadece long | 290 / %38 / +122.9 | +8.1 | +114.8 | -42.2 | +11.2 (-12.7 / +23.9) | 27.7 | 2.1 | 3.0 g |
| sabah · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 1190 / %35 / +211.5 | +227.6 | -16.0 | -129.7 | -5.7 (-3.2 / -2.5) | 32.4 | 4.2 | 7.5 g |
| sabah · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc | 943 / %34 / +145.7 | +109.9 | +35.9 | -48.2 | -10.8 (-10.8 / +0.0) | 37.1 | 3.9 | 7.5 g |
| sabah · stop 0.5 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc+sadece long | 290 / %41 / +128.2 | +10.9 | +117.3 | -42.3 | +15.3 (-7.0 / +22.4) | 21.9 | 2.1 | 3.5 g |
| sabah · stop 0.5 ATR · sabit TP 5R · BTC filtresiz | 1190 / %26 / +285.4 | +273.3 | +12.1 | -126.1 | +55.3 (+37.7 / +17.6) | 11.7 | 2.6 | 11.7 g |
| sabah · stop 0.5 ATR · sabit TP 5R · btc | 943 / %25 / +209.8 | +166.5 | +43.3 | -51.1 | +19.6 (+21.5 / -1.8) | 24.3 | 2.6 | 12.0 g |
| sabah · stop 0.5 ATR · sabit TP 5R · btc+sadece long | 290 / %28 / +135.5 | -14.2 | +149.7 | -60.5 | +12.8 (-8.3 / +21.1) | 18.8 | 1.4 | 8.2 g |
| sabah · stop 1.0 ATR · günlük stop: 10 gün dibi (sabah güncelle) · BTC filtresiz | 1058 / %38 / +283.4 | +165.0 | +118.4 | -115.4 | +39.1 (+15.3 / +23.7) | 16.0 | 2.5 | 12.8 g |
| sabah · stop 1.0 ATR · günlük stop: 10 gün dibi (sabah güncelle) · btc | 836 / %38 / +253.0 | +89.2 | +163.8 | -41.7 | +28.0 (+15.4 / +12.7) | 15.3 | 2.1 | 13.0 g |
| sabah · stop 1.0 ATR · günlük stop: 10 gün dibi (sabah güncelle) · btc+sadece long | 268 / %32 / +178.2 | -44.7 | +222.9 | -55.0 | +28.3 (-7.4 / +35.7) | 18.5 | 1.1 | 11.8 g |
| sabah · stop 1.0 ATR · günlük stop: 20 gün dibi (sabah güncelle) · BTC filtresiz | 1058 / %31 / +241.1 | +109.8 | +131.2 | -163.2 | +3.5 (+13.6 / -10.1) | 13.4 | 1.9 | 18.6 g |
| sabah · stop 1.0 ATR · günlük stop: 20 gün dibi (sabah güncelle) · btc | 836 / %31 / +187.2 | +18.5 | +168.8 | -55.3 | +22.7 (+16.7 / +6.0) | 18.9 | 1.7 | 18.9 g |
| sabah · stop 1.0 ATR · günlük stop: 20 gün dibi (sabah güncelle) · btc+sadece long | 268 / %27 / +168.9 | -76.2 | +245.2 | -69.1 | +22.4 (-10.1 / +32.5) | 20.3 | 0.9 | 16.2 g |
| sabah · stop 1.0 ATR · OKX iz süren stop 2×ATR · BTC filtresiz | 1058 / %40 / +184.5 | +198.8 | -14.3 | -68.7 | +0.1 (+9.5 / -9.4) | 19.7 | 3.7 | 8.9 g |
| sabah · stop 1.0 ATR · OKX iz süren stop 2×ATR · btc | 836 / %40 / +145.9 | +112.3 | +33.5 | -24.7 | +12.1 (+10.1 / +2.0) | 21.2 | 3.2 | 8.8 g |
| sabah · stop 1.0 ATR · OKX iz süren stop 2×ATR · btc+sadece long | 268 / %43 / +74.1 | -10.4 | +84.4 | -30.5 | +16.5 (-3.8 / +20.3) | 16.6 | 1.9 | 3.9 g |
| sabah · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · BTC filtresiz | 1058 / %43 / +189.6 | +207.2 | -17.6 | -78.8 | -4.7 (+6.4 / -11.1) | 25.0 | 3.4 | 9.7 g |
| sabah · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc | 836 / %43 / +150.5 | +125.1 | +25.4 | -26.2 | +20.7 (+19.0 / +1.6) | 19.0 | 3.0 | 9.6 g |
| sabah · stop 1.0 ATR · OKX iz süren 2×ATR (1R'de başlar) · btc+sadece long | 268 / %47 / +82.3 | -5.3 | +87.5 | -33.8 | +21.0 (-1.4 / +22.4) | 16.8 | 1.8 | 5.1 g |
| sabah · stop 1.0 ATR · sabit TP 5R · BTC filtresiz | 1058 / %29 / +237.1 | +196.8 | +40.3 | -118.9 | +7.0 (+27.0 / -20.0) | 16.6 | 2.0 | 18.1 g |
| sabah · stop 1.0 ATR · sabit TP 5R · btc | 836 / %28 / +177.9 | +105.1 | +72.9 | -36.7 | +18.1 (+25.0 / -6.9) | 17.1 | 1.9 | 18.6 g |
| sabah · stop 1.0 ATR · sabit TP 5R · btc+sadece long | 268 / %29 / +138.2 | -47.6 | +185.8 | -64.7 | +20.4 (-12.2 / +32.6) | 21.6 | 1.2 | 11.7 g |

## Sabah girişli en iyi 3 ayarın ayrıntısı (portföy 5)
### sabah · stop 0.5 ATR · günlük stop: 10 gün dibi (sabah güncelle) · BTC filtresiz
- Portföy: 167 işlem, net +76.4R, en büyük düşüş 33.2R. Long 76 işlem +45.5R · Short 91 işlem +30.9R
- Kazanan işlem oranı %33, en iyi işlem +26.6R
- Aylık: 2025-10 +9.0R · 2025-11 +2.2R · 2025-12 -1.4R · 2026-01 +9.5R · 2026-02 -5.5R · 2026-03 -14.1R · 2026-04 -6.7R · 2026-05 +21.4R · 2026-06 -5.7R · 2026-07 +5.9R · 2026-08 +26.4R · 2026-09 +35.9R · 2026-10 -0.6R
- Artı kapanan ay: 7/13
- En iyi 5 işlem olmadan: -23.7R

### sabah · stop 0.5 ATR · günlük stop: 10 gün dibi (sabah güncelle) · btc
- Portföy: 134 işlem, net +68.0R, en büyük düşüş 21.9R. Long 54 işlem +41.1R · Short 80 işlem +26.9R
- Kazanan işlem oranı %31, en iyi işlem +26.6R
- Aylık: 2025-10 +9.0R · 2025-11 +8.2R · 2025-12 +0.2R · 2026-01 +17.9R · 2026-02 -2.6R · 2026-03 -10.6R · 2026-04 +7.8R · 2026-05 +6.0R · 2026-06 -6.2R · 2026-07 -8.1R · 2026-08 +18.6R · 2026-09 +37.6R · 2026-10 -9.8R
- Artı kapanan ay: 8/13
- En iyi 5 işlem olmadan: -19.0R

### sabah · stop 0.5 ATR · sabit TP 5R · BTC filtresiz
- Portföy: 135 işlem, net +55.3R, en büyük düşüş 11.7R. Long 56 işlem +24.7R · Short 79 işlem +30.7R
- Kazanan işlem oranı %33, en iyi işlem +5.0R
- Aylık: 2025-10 -0.4R · 2025-11 +16.7R · 2025-12 -0.1R · 2026-01 +7.9R · 2026-02 -3.7R · 2026-03 -6.3R · 2026-04 +3.2R · 2026-05 +22.7R · 2026-06 +5.7R · 2026-07 +0.5R · 2026-08 +0.5R · 2026-09 +6.5R · 2026-10 +2.2R
- Artı kapanan ay: 9/13
- En iyi 5 işlem olmadan: +30.4R

Süre: 0 dk
