# Günlük trend stratejisi — kapsamlı final testi (2 yıl)
64 coin. Dönem 18.10.2024 – bugün: **eğitim 18.10.2024 – 15.02.2026 (485 gün)**, **doğrulama son 245 gün**. Her aşamada seçim sadece eğitime göre yapıldı. Maliyetler: maker %0.02, taker %0.05 + %0.05 kayma (stoplar), long funding 8 saatte %0.01. Portföy: 100 USDT başlangıç, bileşik, coin başına 1 pozisyon, sinyal fazlaysa 24s hacmi yüksek olan önce. Not: coinler bugünün hacim listesinden seçildi (o dönemde listede olup sonra düşen coinler yok); bu sonuçları bir miktar iyimser gösterebilir.

## A) Giriş saati (BTC filtresi yok)
| Ayar | Tüm işlemler: sayı / kazanan / net R | Eğitim / doğrulama net R | R/işlem | Portföy (%2 × 3): son bakiye | Eğitim / doğrulama getiri | En büyük düşüş |
|---|---|---|---|---|---|---|
| kapanışta 03:00 (Tokyo açılışı) · TP 5R | 2223 / %23 / +346.1 | +340.7 / +5.4 | +0.16 | 129 USDT | %+24 / %+4 | %37 |
| kapanışta 03:00 (Tokyo açılışı) · günlük stop 10 gün dibi | 2223 / %26 / +635.1 | +524.2 / +110.9 | +0.29 | 82 USDT | %-6 / %-12 | %54 |
| +1 saat (04:00) · TP 5R | 2207 / %22 / +244.7 | +226.4 / +18.3 | +0.11 | 122 USDT | %+21 / %+1 | %46 |
| +1 saat (04:00) · günlük stop 10 gün dibi | 2207 / %25 / +736.8 | +629.6 / +107.2 | +0.33 | 69 USDT | %-14 / %-20 | %58 |
| +2 saat 05:00 (Hong Kong/Şangay) · TP 5R | 2204 / %22 / +268.3 | +270.7 / -2.5 | +0.12 | 87 USDT | %-25 / %+17 | %48 |
| +2 saat 05:00 (Hong Kong/Şangay) · günlük stop 10 gün dibi | 2204 / %25 / +666.1 | +567.2 / +98.9 | +0.30 | 93 USDT | %-3 / %-4 | %49 |
| +5 saat (08:00) · TP 5R | 2157 / %22 / +244.6 | +238.9 / +5.7 | +0.11 | 156 USDT | %+10 / %+41 | %43 |
| +5 saat (08:00) · günlük stop 10 gün dibi | 2157 / %25 / +537.6 | +503.0 / +34.6 | +0.25 | 112 USDT | %+0 / %+12 | %53 |
| +7 saat 10:00 (Londra, yaz saati) · TP 5R | 2104 / %21 / +125.4 | +145.3 / -19.9 | +0.06 | 134 USDT | %+13 / %+18 | %46 |
| +7 saat 10:00 (Londra, yaz saati) · günlük stop 10 gün dibi | 2104 / %24 / +392.9 | +351.6 / +41.3 | +0.19 | 102 USDT | %-3 / %+5 | %54 |
| +8 saat 11:00 (Londra, kış saati) · TP 5R | 2088 / %21 / +138.2 | +173.5 / -35.3 | +0.07 | 213 USDT | %+36 / %+56 | %25 |
| +8 saat 11:00 (Londra, kış saati) · günlük stop 10 gün dibi | 2088 / %24 / +354.8 | +316.3 / +38.5 | +0.17 | 81 USDT | %-5 / %-14 | %64 |
| +9 saat (12:00) · TP 5R | 2078 / %21 / +86.7 | +155.3 / -68.6 | +0.04 | 117 USDT | %+6 / %+10 | %41 |
| +9 saat (12:00) · günlük stop 10 gün dibi | 2078 / %24 / +268.2 | +303.2 / -35.0 | +0.13 | 57 USDT | %-22 / %-27 | %59 |
| +13 saat 16:00 (New York öncesi, yaz) · TP 5R | 2058 / %21 / +103.9 | +175.9 / -72.0 | +0.05 | 110 USDT | %-16 / %+30 | %41 |
| +13 saat 16:00 (New York öncesi, yaz) · günlük stop 10 gün dibi | 2058 / %24 / +225.7 | +256.3 / -30.6 | +0.11 | 57 USDT | %-23 / %-27 | %56 |
| +14 saat 17:00 (New York, kış/yaz sonrası) · TP 5R | 2017 / %21 / -7.2 | +32.0 / -39.1 | -0.00 | 95 USDT | %-25 / %+27 | %54 |
| +14 saat 17:00 (New York, kış/yaz sonrası) · günlük stop 10 gün dibi | 2017 / %24 / +254.5 | +269.9 / -15.4 | +0.13 | 97 USDT | %+1 / %-4 | %51 |
| kademeli 03:00 / 08:00 / 13:00 · TP 5R | 1997 / %26 / +239.3 | +247.9 / -8.6 | +0.12 | 84 USDT | %-35 / %+28 | %43 |
| kademeli 03:00 / 08:00 / 13:00 · günlük stop 10 gün dibi | 1997 / %25 / +494.2 | +442.2 / +52.1 | +0.25 | 94 USDT | %-15 / %+11 | %49 |
| kademeli oturumlar: Asya 03:00 / Avrupa 11:00 / ABD 17:00 · TP 5R | 1903 / %26 / +178.3 | +193.4 / -15.1 | +0.09 | 97 USDT | %-35 / %+48 | %42 |
| kademeli oturumlar: Asya 03:00 / Avrupa 11:00 / ABD 17:00 · günlük stop 10 gün dibi | 1903 / %26 / +447.2 | +390.7 / +56.5 | +0.24 | 85 USDT | %-1 / %-15 | %54 |

Eğitimde en iyi: kapanışta 03:00 (Tokyo açılışı) (+864.9R), kapanışta giriş +864.9R. Fark küçük → seçilen giriş: **kapanışta 03:00 (Tokyo açılışı)**

## B) Çıkış türü × BTC filtresi (giriş: kapanışta 03:00 (Tokyo açılışı))
| Ayar | Tüm işlemler: sayı / kazanan / net R | Eğitim / doğrulama net R | R/işlem | Portföy (%2 × 3): son bakiye | Eğitim / doğrulama getiri | En büyük düşüş |
|---|---|---|---|---|---|---|
| TP 5R · BTC filtresiz | 2223 / %23 / +346.1 | +340.7 / +5.4 | +0.16 | 129 USDT | %+24 / %+4 | %37 |
| TP 5R · BTC filtreli | 1633 / %22 / +211.1 | +204.3 / +6.7 | +0.13 | 145 USDT | %+10 / %+31 | %47 |
| TP 5R + 2R'de stop girişe · BTC filtresiz | 2223 / %18 / +307.7 | +301.5 / +6.2 | +0.14 | 143 USDT | %+46 / %-2 | %29 |
| TP 5R + 2R'de stop girişe · BTC filtreli | 1633 / %17 / +191.2 | +177.4 / +13.9 | +0.12 | 146 USDT | %-10 / %+62 | %46 |
| günlük stop 10 gün dibi · BTC filtresiz | 2223 / %26 / +635.1 | +524.2 / +110.9 | +0.29 | 82 USDT | %-6 / %-12 | %54 |
| günlük stop 10 gün dibi · BTC filtreli | 1633 / %25 / +566.5 | +458.4 / +108.1 | +0.35 | 115 USDT | %+49 / %-23 | %39 |
| günlük stop 10 gün + 2R'de stop girişe · BTC filtresiz | 2223 / %23 / +582.4 | +515.9 / +66.5 | +0.26 | 96 USDT | %+1 / %-5 | %43 |
| günlük stop 10 gün + 2R'de stop girişe · BTC filtreli | 1633 / %23 / +518.4 | +441.9 / +76.6 | +0.32 | 134 USDT | %+57 / %-15 | %33 |
| günlük stop 20 gün dibi · BTC filtresiz | 2223 / %22 / +511.8 | +453.5 / +58.3 | +0.23 | 84 USDT | %-26 / %+14 | %36 |
| günlük stop 20 gün dibi · BTC filtreli | 1633 / %21 / +372.6 | +313.6 / +59.0 | +0.23 | 89 USDT | %-18 / %+8 | %35 |
| yarısı 3R + kalanı günlük stop 10 gün · BTC filtresiz | 2223 / %29 / +436.0 | +382.9 / +53.1 | +0.20 | 120 USDT | %-12 / %+36 | %28 |
| yarısı 3R + kalanı günlük stop 10 gün · BTC filtreli | 1633 / %29 / +336.1 | +290.6 / +45.5 | +0.21 | 149 USDT | %+14 / %+32 | %26 |
| OKX iz süren stop 2×ATR · BTC filtresiz | 2223 / %32 / +146.9 | +124.8 / +22.1 | +0.07 | 91 USDT | %+39 / %-35 | %43 |
| OKX iz süren stop 2×ATR · BTC filtreli | 1633 / %32 / +28.7 | +12.2 / +16.5 | +0.02 | 90 USDT | %-8 / %-3 | %39 |
| OKX iz süren stop 3×ATR · BTC filtresiz | 2223 / %26 / +172.8 | +201.6 / -28.8 | +0.08 | 81 USDT | %-5 / %-15 | %51 |
| OKX iz süren stop 3×ATR · BTC filtreli | 1633 / %25 / +14.8 | +49.6 / -34.9 | +0.01 | 104 USDT | %-14 / %+20 | %39 |
| OKX iz süren stop 3×ATR (1R kârda başlar) · BTC filtresiz | 2223 / %26 / +179.0 | +207.8 / -28.7 | +0.08 | 81 USDT | %-5 / %-15 | %51 |
| OKX iz süren stop 3×ATR (1R kârda başlar) · BTC filtreli | 1633 / %26 / +20.6 | +55.8 / -35.2 | +0.01 | 104 USDT | %-14 / %+20 | %39 |

Seçilen (eğitimde tüm işlemler net R en iyi): **günlük stop 10 gün dibi · BTC filtresiz**

## C) Portföy ve risk kuralları
| Risk × en fazla pozisyon | Düşüşte risk yarıya | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | En düşük bakiye | İşlem | En uzun kayıp serisi | Acil fren çalıştı mı | Eğitim skoru (getiri/düşüş) |
|---|---|---|---|---|---|---|---|---|---|
| %2 × 3 | hayır | 82 USDT | %-6 / %-12 | %54 | 66 USDT | 210 | 25 | hayır | 0.02 |
| %2 × 3 | evet | 93 USDT | %-3 / %-4 | %37 | 77 USDT | 210 | 25 | hayır | 0.03 |
| %1.5 × 4 | hayır | 125 USDT | %+6 / %+18 | %43 | 77 USDT | 271 | 19 | hayır | 0.38 |
| %1.5 × 4 | evet | 111 USDT | %+2 / %+9 | %31 | 83 USDT | 271 | 19 | hayır | 0.24 |
| %1.25 × 5 | hayır | 178 USDT | %+17 / %+52 | %41 | 72 USDT | 328 | 20 | hayır | 0.65 |
| %1.25 × 5 | evet | 142 USDT | %+6 / %+34 | %29 | 74 USDT | 328 | 20 | hayır | 0.34 |
| %1 × 6 | hayır | 186 USDT | %+26 / %+47 | %34 | 81 USDT | 394 | 21 | hayır | 1.16 |
| %1 × 6 | evet | 146 USDT | %+14 / %+28 | %25 | 85 USDT | 394 | 21 | hayır | 0.81 |
| %1 × 8 | hayır | 186 USDT | %+32 / %+41 | %39 | 73 USDT | 511 | 26 | hayır | 1.19 |
| %1 × 8 | evet | 130 USDT | %+13 / %+15 | %28 | 74 USDT | 511 | 26 | hayır | 0.68 |

Seçilen: **%1 risk × en fazla 8 pozisyon, düşüşte risk yarıya: hayır**

## D) Günlük mumun kapanış saati (sağlamlık)
| Kapanış saati (TR) | Tüm işlemler: sayı / net R | Eğitim / doğrulama net R | Portföy son bakiye | Eğitim / doğrulama getiri | En büyük düşüş |
|---|---|---|---|---|---|
| 03:00 | 2223 / +635.1 | +524.2 / +110.9 | 186 USDT | %+32 / %+41 | %39 |
| 09:00 | 2137 / +492.8 | +458.6 / +34.2 | 145 USDT | %-4 / %+52 | %60 |
| 15:00 | 2171 / +480.0 | +456.0 / +24.0 | 86 USDT | %-27 / %+17 | %50 |
| 21:00 | 2254 / +295.9 | +196.2 / +99.7 | 135 USDT | %+4 / %+30 | %47 |
| **dördü birlikte** | 8785 / +1903.8 | +1635.0 / +268.8 | 124 USDT | %+10 / %+12 | %52 |

Eğitim skoru: tek saat 1.19, dördü birlikte 0.46 → seçilen: **sadece 03:00 kapanışı**

## E) Şans seviyesi (mumları karıştırılmış veri, 03:00 kapanışı, aynı ayar)
- Gerçek veri: tüm işlemler net **+635.1R** (2223 işlem). Karışık veri (3 deneme): -385.5R, +30.5R, -161.5R

## Seçilen son kurgu
- Giriş: kapanışta 03:00 (Tokyo açılışı) limit · Çıkış: günlük stop 10 gün dibi · BTC filtresiz · %1 risk × en fazla 8 pozisyon · düşüşte risk yarıya: hayır · 03:00 kapanışı
- 2 yıl: 100 → **186 USDT**, eğitim %+32, doğrulama %+41, en büyük düşüş %39, en düşük bakiye 73 USDT, 511 işlem (haftada ~4.9), en uzun kayıp serisi 26, acil fren: çalışmadı
- Long 244 işlem (+58.4R) · Short 267 işlem (+55.3R) · kazanan oranı %27
- Aylık: 2024-10 %-15 · 2024-11 %-8 · 2024-12 %+21 · 2025-01 %-23 · 2025-02 %+7 · 2025-03 %+44 · 2025-04 %+9 · 2025-05 %+2 · 2025-06 %+12 · 2025-07 %+11 · 2025-08 %-16 · 2025-09 %-6 · 2025-10 %-8 · 2025-11 %-7 · 2025-12 %+15 · 2026-01 %-12 · 2026-02 %+23 · 2026-03 %-10 · 2026-04 %-8 · 2026-05 %-6 · 2026-06 %+15 · 2026-07 %+0 · 2026-08 %-5 · 2026-09 %+60 · 2026-10 %+5
- Artı kapanan ay: 13/25
- **Bootstrap (2.000 farklı 2 yıl):** son bakiye en kötü %5'te 102, ortada 262, en iyi %5'te 733 USDT. En büyük düşüş ortada %29, en kötü %5'te %48. En düşük bakiye (en kötü %5) 65 USDT. Dönemi zararla kapatma ihtimali %4.

Süre: 28 dk
