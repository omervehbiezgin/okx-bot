# Limit giriş ve bütçe planı testi — günlük trend stratejisi
64 coin, son 365 gün (eğitim ilk 240 / doğrulama son 125 gün). Kurgu: günlük kapanışla kırılım, EMA50, stop kırılan seviye − 0,5 günlük ATR, TP 5R. Komisyon, long funding ve piyasa emirlerinde %0.05 kayma dahil. Portföy: coin başına 1, aynı anda en fazla 5.

## 1) Giriş türleri
| Giriş | Sinyal / dolan / dolmayan | Kazanan | Tüm işlemler net R | Eğitim / doğrulama net R | Portföy 5 net R (eğitim / doğrulama) | Portföy en büyük düşüş R | Ort. stop % |
|---|---|---|---|---|---|---|---|
| sabah 08:00 piyasa | 1340 / 1193 / 0 | %26 | +256.3 | +253.6 / +2.7 | +33.9 (+19.9 / +13.9) | 13.0 | 6.2 |
| limit @sabah fiyatı | 1340 / 1189 / 0 | %26 | +277.1 | +266.5 / +10.5 | +36.3 (+21.5 / +14.8) | 12.8 | 6.2 |
| limit @sabah fiyatı ∓ 0,25 ATR | 1340 / 862 / 333 | %23 | +132.1 | +157.1 / -25.0 | +24.9 (+15.1 / +9.8) | 26.3 | 4.9 |
| limit @sabah fiyatı ∓ 0,5 ATR | 1340 / 556 / 604 | %20 | +14.0 | +30.8 / -16.8 | +36.9 (+31.1 / +5.8) | 26.7 | 4.3 |
| limit @kırılan seviye | 1340 / 1171 / 159 | %21 | +81.8 | +140.4 / -58.6 | +70.0 (+23.4 / +46.6) | 22.8 | 5.2 |

## 2) Bütçe planları (100 USDT başlangıç, bileşik, portföy en fazla 5)
| Giriş | Plan | Son bakiye | En düşük bakiye | En büyük düşüş % | Tek işlemde en büyük kayıp % | Aynı anda en büyük pozisyon / bakiye |
|---|---|---|---|---|---|---|
| sabah 08:00 piyasa | %10 teminat × 10x (pozisyon = bakiye) | 292 USDT | 50 USDT | %52 | %-17.0 | 14.3x |
| sabah 08:00 piyasa | %1 risk | 132 USDT | 92 USDT | %13 | %-1.5 | 3.6x |
| sabah 08:00 piyasa | %2 risk | 158 USDT | 84 USDT | %24 | %-3.2 | 7.2x |
| limit @sabah fiyatı | %10 teminat × 10x (pozisyon = bakiye) | 281 USDT | 51 USDT | %51 | %-16.9 | 10.3x |
| limit @sabah fiyatı | %1 risk | 135 USDT | 93 USDT | %12 | %-1.5 | 2.8x |
| limit @sabah fiyatı | %2 risk | 165 USDT | 85 USDT | %24 | %-3.1 | 5.6x |
| limit @sabah fiyatı ∓ 0,25 ATR | %10 teminat × 10x (pozisyon = bakiye) | 218 USDT | 19 USDT | %81 | %-28.9 | 11.0x |
| limit @sabah fiyatı ∓ 0,25 ATR | %1 risk | 120 USDT | 79 USDT | %24 | %-1.4 | 4.3x |
| limit @sabah fiyatı ∓ 0,25 ATR | %2 risk | 131 USDT | 59 USDT | %44 | %-3.2 | 8.7x |
| limit @sabah fiyatı ∓ 0,5 ATR | %10 teminat × 10x (pozisyon = bakiye) | 41 USDT | 16 USDT | %89 | %-26.7 | 8.6x |
| limit @sabah fiyatı ∓ 0,5 ATR | %1 risk | 130 USDT | 96 USDT | %24 | %-1.5 | 5.9x |
| limit @sabah fiyatı ∓ 0,5 ATR | %2 risk | 143 USDT | 83 USDT | %45 | %-3.1 | 11.7x |
| limit @kırılan seviye | %10 teminat × 10x (pozisyon = bakiye) | 280 USDT | 23 USDT | %80 | %-17.0 | 11.8x |
| limit @kırılan seviye | %1 risk | 181 USDT | 83 USDT | %21 | %-1.5 | 2.4x |
| limit @kırılan seviye | %2 risk | 275 USDT | 68 USDT | %38 | %-3.1 | 4.8x |

- Limit @sabah fiyatı, portföy: en uzun kayıp serisi 12 işlem; stop mesafesi ortanca %5.5, en büyük %15.0. Pozisyon = bakiye iken her stop bakiyenin stop mesafesi kadarını kaybettirir.
Süre: 0 dk
