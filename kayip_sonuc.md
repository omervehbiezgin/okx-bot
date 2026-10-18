# Trend stratejisi — kayıp analizi
2333 işlem (eğitim 1470, doğrulama 863). Kurgu: 03:00 girişi, günlük stop 10 gün dibi. Her özellik eğitim verisinin üçte birlik dilimlerine bölündü; tablo her dilimin işlem başı net R'ını gösterir. Bir dilim **hem eğitimde hem doğrulamada** belirgin şekilde kötüyse filtre adayıdır.

Ortalama: eğitim +0.351 R/işlem, doğrulama +0.139 R/işlem

| Özellik | Dilim (eğitim sınırları) | Eğitim: işlem / R/işlem / kazanan | Doğrulama: işlem / R/işlem / kazanan |
|---|---|---|---|
| stop mesafesi % | … – 5.32 | 490 / +0.820 / %25 | 437 / +0.058 / %20 |
| stop mesafesi % | 5.32 – 7.92 | 490 / +0.428 / %28 | 227 / +0.334 / %30 |
| stop mesafesi % | 7.92 – … | 490 / -0.194 / %25 | 199 / +0.093 / %30 |
| kırılım mumu boyu (ATR) | … – 1.12 | 490 / +0.165 / %26 | 294 / -0.084 / %20 |
| kırılım mumu boyu (ATR) | 1.12 – 1.59 | 490 / +0.164 / %28 | 239 / -0.181 / %21 |
| kırılım mumu boyu (ATR) | 1.59 – … | 490 / +0.725 / %23 | 330 / +0.568 / %32 |
| kırılım mumu gövde oranı | … – 0.56 | 490 / -0.057 / %21 | 295 / +0.175 / %23 |
| kırılım mumu gövde oranı | 0.56 – 0.74 | 490 / +0.658 / %26 | 276 / -0.002 / %22 |
| kırılım mumu gövde oranı | 0.74 – … | 490 / +0.453 / %31 | 292 / +0.235 / %29 |
| kapanışın seviyeyi geçme payı (ATR) | … – 0.19 | 490 / +0.621 / %24 | 279 / +0.125 / %18 |
| kapanışın seviyeyi geçme payı (ATR) | 0.19 – 0.44 | 490 / +0.134 / %27 | 271 / +0.020 / %25 |
| kapanışın seviyeyi geçme payı (ATR) | 0.44 – … | 490 / +0.299 / %27 | 313 / +0.253 / %30 |
| kırılım hacmi / 20 gün ortancası | … – 1.06 | 490 / +0.079 / %27 | 293 / -0.249 / %22 |
| kırılım hacmi / 20 gün ortancası | 1.06 – 1.59 | 490 / +0.197 / %29 | 223 / -0.082 / %22 |
| kırılım hacmi / 20 gün ortancası | 1.59 – … | 490 / +0.778 / %22 | 347 / +0.608 / %30 |
| EMA50'den uzaklık (ATR) | … – 1.46 | 490 / +0.889 / %20 | 296 / +0.383 / %30 |
| EMA50'den uzaklık (ATR) | 1.46 – 2.77 | 490 / +0.079 / %26 | 307 / +0.204 / %23 |
| EMA50'den uzaklık (ATR) | 2.77 – … | 490 / +0.086 / %31 | 260 / -0.216 / %21 |
| EMA50 eğimi (5 gün, ATR) | … – 0.10 | 490 / +0.946 / %22 | 292 / +0.414 / %30 |
| EMA50 eğimi (5 gün, ATR) | 0.10 – 0.40 | 490 / +0.030 / %25 | 335 / +0.289 / %27 |
| EMA50 eğimi (5 gün, ATR) | 0.40 – … | 490 / +0.078 / %31 | 236 / -0.417 / %15 |
| son 20 gün getiri % (işlem yönünde) | … – 9.15 | 490 / +1.238 / %27 | 306 / +0.278 / %25 |
| son 20 gün getiri % (işlem yönünde) | 9.15 – 21.19 | 490 / -0.044 / %26 | 335 / +0.057 / %27 |
| son 20 gün getiri % (işlem yönünde) | 21.19 – … | 490 / -0.140 / %25 | 222 / +0.068 / %21 |
| günlük oynaklık (ATR %) | … – 6.69 | 490 / +1.046 / %28 | 508 / +0.325 / %26 |
| günlük oynaklık (ATR %) | 6.69 – 9.10 | 490 / +0.024 / %24 | 238 / -0.044 / %24 |
| günlük oynaklık (ATR %) | 9.10 – … | 490 / -0.017 / %25 | 117 / -0.298 / %23 |
| BTC aynı yönde (1) / değil (0) | … – 0.50 | 402 / +0.122 / %26 | 213 / +0.013 / %26 |
| BTC aynı yönde (1) / değil (0) | 0.50 – … | 1068 / +0.438 / %26 | 650 / +0.180 / %24 |
| kırılım hafta sonu (1) / değil (0) | … – 0.50 | 1112 / +0.407 / %25 | 672 / +0.114 / %27 |
| kırılım hafta sonu (1) / değil (0) | 0.50 – … | 358 / +0.178 / %28 | 191 / +0.225 / %19 |

## Filtre adayları (eğitimde ortalamanın belirgin altında kalan dilimi çıkarmak)
| Çıkarılan dilim | Eğitimde o dilim | Doğrulamada o dilim | Filtre sonrası tüm işlemler: eğitim / doğrulama net R | Portföy %1 × 8: son bakiye / düşüş (filtresiz: aşağıda) |
|---|---|---|---|---|
| stop mesafesi %: 7.92 – inf | -0.194 R/işlem | +0.093 R/işlem (❌ doğrulamada tutmadı) | +611.3 / +101.1 | 447 USDT / %48 |
| kırılım mumu boyu (ATR): -inf – 1.12 | +0.165 R/işlem | -0.084 R/işlem (✅ doğrulamada da kötü) | +435.5 / +144.1 | 126 USDT / %50 |
| kırılım mumu boyu (ATR): 1.12 – 1.59 | +0.164 R/işlem | -0.181 R/işlem (✅ doğrulamada da kötü) | +436.2 / +162.8 | 139 USDT / %41 |
| kırılım mumu gövde oranı: -inf – 0.56 | -0.057 R/işlem | +0.175 R/işlem (❌ doğrulamada tutmadı) | +544.4 / +67.9 | 206 USDT / %54 |
| kapanışın seviyeyi geçme payı (ATR): 0.19 – 0.44 | +0.134 R/işlem | +0.020 R/işlem (✅ doğrulamada da kötü) | +450.7 / +114.1 | 59 USDT / %48 |
| kırılım hacmi / 20 gün ortancası: -inf – 1.06 | +0.079 R/işlem | -0.249 R/işlem (✅ doğrulamada da kötü) | +477.6 / +192.5 | 60 USDT / %44 |
| kırılım hacmi / 20 gün ortancası: 1.06 – 1.59 | +0.197 R/işlem | -0.082 R/işlem (✅ doğrulamada da kötü) | +419.9 / +137.8 | 65 USDT / %47 |
| EMA50'den uzaklık (ATR): 1.46 – 2.77 | +0.079 R/işlem | +0.204 R/işlem (❌ doğrulamada tutmadı) | +477.7 / +56.9 | 328 USDT / %42 |
| EMA50'den uzaklık (ATR): 2.77 – inf | +0.086 R/işlem | -0.216 R/işlem (✅ doğrulamada da kötü) | +474.2 / +175.8 | 260 USDT / %56 |
| EMA50 eğimi (5 gün, ATR): 0.10 – 0.40 | +0.030 R/işlem | +0.289 R/işlem (❌ doğrulamada tutmadı) | +501.7 / +22.6 | 259 USDT / %56 |
| EMA50 eğimi (5 gün, ATR): 0.40 – inf | +0.078 R/işlem | -0.417 R/işlem (✅ doğrulamada da kötü) | +478.3 / +217.9 | 143 USDT / %53 |
| son 20 gün getiri % (işlem yönünde): 9.15 – 21.19 | -0.044 R/işlem | +0.057 R/işlem (❌ doğrulamada tutmadı) | +538.1 / +100.4 | 306 USDT / %53 |
| son 20 gün getiri % (işlem yönünde): 21.19 – inf | -0.140 R/işlem | +0.068 R/işlem (❌ doğrulamada tutmadı) | +585.0 / +104.4 | 259 USDT / %37 |
| günlük oynaklık (ATR %): 6.69 – 9.10 | +0.024 R/işlem | -0.044 R/işlem (✅ doğrulamada da kötü) | +504.5 / +130.1 | 257 USDT / %55 |
| günlük oynaklık (ATR %): 9.10 – inf | -0.017 R/işlem | -0.298 R/işlem (✅ doğrulamada da kötü) | +524.6 / +154.4 | 105 USDT / %42 |
| BTC aynı yönde (1) / değil (0): -inf – 0.50 | +0.122 R/işlem | +0.013 R/işlem (✅ doğrulamada da kötü) | +467.4 / +116.7 | 143 USDT / %52 |
| kırılım hafta sonu (1) / değil (0): 0.50 – inf | +0.178 R/işlem | +0.225 R/işlem (❌ doğrulamada tutmadı) | +452.6 / +76.6 | 257 USDT / %41 |

Filtresiz: tüm işlemler eğitim +516.4 / doğrulama +119.5 R · portföy 157 USDT / düşüş %45

## Kayıpların yapısı
- Kaybeden işlem: 1737 / 2333 (%74). Ortalama kayıp -0.95R
- Kaybedenlerin %45'ı 2 gün içinde, %69'ı 5 gün içinde stop oldu
- En iyi 20 işlem toplamı +808.2R (tüm işlemler +635.9R)

Süre: 2 dk
