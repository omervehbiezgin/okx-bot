# Sinyal geçmiş testi 2 — sizin kurallarınızla

188 coin, test tarihi 2026-10-27. R = 1 $ risk; ortalama +0.20R = işlem başına +0,20 $. Ücret: limit %0.02, piyasa/stop %0.05 + %0.03 kayma. Bakiye: 100 $, işlem başına 1 $ risk, 10x kaldıraç. 'Eğitim' dönemi ayar seçmek, 'son dönem' sınamak içindir.

**Mod: vadeli 3x — stop mesafesi %30 üstündeki işlemler likidasyon riski yüzünden açılmaz**


## 1) Kırılım

Yön filtresi her zaman açık (long: günlük EMA200 veya haftalık EMA21 üstü; short: tersi). Ana strateji ⚠️ notluları içermez. Giriş: cizgi = kırılan bant çizgisi, orta = bant ortası. İz: yok / be k = 1R'de başa baş sonra k x ATR / r1 = 1R geriden. Bekleme mum sayısıdır.


### Kırılım 15m — EMA filtresinden geçen 730 sinyal (ilk 100 coin, 120 gün; son dönem = son 30 gün)

#### Kırılım 15m — ana: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 96 mum / yok / tp %33 | 211 | +0.34 | 11% | 1.34 | 102 | -0.90 | 5% | 0.14 | 23 |
| orta / 48 mum / yok / tp %33 | 181 | +0.27 | 10% | 1.28 | 85 | -0.97 | 4% | 0.08 | 34 |
| cizgi / 24 mum / yok / tp %33 | 228 | -0.02 | 14% | 0.98 | 106 | -0.54 | 8% | 0.43 | 42 |
| orta / 96 mum / yok / tp %10 | 213 | -0.02 | 13% | 0.98 | 102 | -0.28 | 13% | 0.71 | 35 |
| orta / 24 mum / yok / tp %33 | 118 | -0.06 | 8% | 0.94 | 68 | -1.02 | 1% | 0.05 | 33 |
| orta / 48 mum / yok / tp %10 | 183 | -0.09 | 13% | 0.91 | 85 | -0.34 | 12% | 0.65 | 32 |
| cizgi / 96 mum / yok / tp %33 | 259 | -0.10 | 14% | 0.89 | 127 | -0.44 | 9% | 0.53 | 29 |
| cizgi / 24 mum / yok / tp %10 | 230 | -0.11 | 20% | 0.88 | 109 | -0.26 | 17% | 0.70 | 31 |
| cizgi / 48 mum / yok / tp %33 | 248 | -0.12 | 13% | 0.87 | 118 | -0.57 | 8% | 0.40 | 48 |
| cizgi / 24 mum / be 1.5 / tp %33 | 234 | -0.13 | 46% | 0.78 | 115 | -0.29 | 40% | 0.54 | 8 |
| cizgi / 24 mum / be 3.0 / tp %33 | 234 | -0.13 | 44% | 0.78 | 114 | -0.24 | 36% | 0.61 | 8 |
| cizgi / 96 mum / be 1.5 / tp %33 | 268 | -0.14 | 45% | 0.76 | 138 | -0.23 | 42% | 0.61 | 7 |

**Kırılım 15m — ana — en iyi ayar: orta / 96 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 228 | 85 | 89.1 $ | -10.9 $ | 67.4 $ | 80.3 $ | 7 |
| Sadece son dönem (100 $ ile başlayarak) | 63 | 40 | 41.1 $ | -58.9 $ | 59.9 $ | 40.1 $ | 4 |

#### Kırılım 15m — ana — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 88 | +1.01 | 12% | 2.07 | 67 | -0.98 | 3% | 0.06 | 25 |
| Short | 123 | -0.14 | 10% | 0.86 | 35 | -0.74 | 9% | 0.29 | 19 |
| ✅ var ⚠️az | 23 | +0.18 | 9% | 1.18 | 16 | -0.97 | 6% | 0.03 | 15 |
| ✅ yok | 188 | +0.36 | 11% | 1.37 | 86 | -0.88 | 5% | 0.16 | 38 |
| 2 yıldız | 59 | -0.35 | 8% | 0.66 | 26 | -0.90 | 8% | 0.12 | 19 |
| 3 yıldız | 143 | +0.53 | 12% | 1.55 | 69 | -0.88 | 4% | 0.16 | 17 |

#### Kırılım 15m — ana 2-3 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 96 mum / yok / tp %33 | 202 | +0.28 | 11% | 1.28 | 95 | -0.88 | 5% | 0.15 | 22 |
| orta / 48 mum / yok / tp %33 | 174 | +0.18 | 10% | 1.19 | 79 | -0.97 | 4% | 0.08 | 30 |
| orta / 24 mum / yok / tp %33 | 115 | -0.03 | 9% | 0.97 | 65 | -1.02 | 2% | 0.05 | 32 |
| cizgi / 24 mum / yok / tp %33 | 215 | -0.04 | 14% | 0.96 | 100 | -0.56 | 8% | 0.41 | 38 |
| orta / 96 mum / yok / tp %10 | 204 | -0.08 | 13% | 0.92 | 95 | -0.22 | 14% | 0.77 | 31 |
| cizgi / 96 mum / yok / tp %33 | 244 | -0.12 | 14% | 0.87 | 119 | -0.44 | 9% | 0.53 | 26 |
| cizgi / 48 mum / yok / tp %33 | 233 | -0.14 | 13% | 0.85 | 110 | -0.59 | 8% | 0.39 | 43 |
| cizgi / 24 mum / be 1.5 / tp %33 | 221 | -0.14 | 45% | 0.76 | 108 | -0.25 | 42% | 0.58 | 8 |
| cizgi / 24 mum / be 3.0 / tp %33 | 221 | -0.14 | 43% | 0.75 | 107 | -0.21 | 37% | 0.66 | 8 |
| cizgi / 96 mum / be 1.5 / tp %33 | 253 | -0.14 | 45% | 0.75 | 129 | -0.20 | 43% | 0.65 | 7 |
| cizgi / 96 mum / be 3.0 / tp %33 | 252 | -0.14 | 43% | 0.75 | 128 | -0.16 | 39% | 0.71 | 9 |
| orta / 96 mum / be 3.0 / tp %10 | 208 | -0.15 | 29% | 0.77 | 97 | -0.39 | 25% | 0.37 | 16 |

**Kırılım 15m — ana 2-3 yıldız — en iyi ayar: orta / 96 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 218 | 79 | 99.8 $ | -0.2 $ | 63.3 $ | 80.4 $ | 7 |
| Sadece son dönem (100 $ ile başlayarak) | 54 | 42 | 52.8 $ | -47.2 $ | 50.3 $ | 49.7 $ | 4 |

#### Kırılım 15m — 0-1 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 48 mum / yok / tp %33 ⚠️az | 7 | +2.47 | 14% | 3.70 | 6 | -1.08 | 0% | 0.00 | 4 |
| orta / 48 mum / yok / tp %10 ⚠️az | 7 | +2.00 | 14% | 3.19 | 6 | -1.08 | 0% | 0.00 | 4 |
| orta / 96 mum / yok / tp %33 ⚠️az | 9 | +1.68 | 11% | 2.75 | 7 | -1.07 | 0% | 0.00 | 6 |
| orta / 96 mum / yok / tp %10 ⚠️az | 9 | +1.31 | 11% | 2.37 | 7 | -1.07 | 0% | 0.00 | 6 |
| cizgi / 24 mum / yok / tp %10 ⚠️az | 13 | +0.85 | 23% | 2.05 | 7 | -0.49 | 14% | 0.44 | 5 |
| cizgi / 48 mum / yok / tp %10 ⚠️az | 15 | +0.59 | 20% | 1.71 | 9 | -0.62 | 11% | 0.33 | 6 |
| cizgi / 96 mum / yok / tp %10 ⚠️az | 15 | +0.59 | 20% | 1.71 | 9 | -0.62 | 11% | 0.33 | 6 |
| cizgi / 24 mum / yok / tp %33 ⚠️az | 13 | +0.33 | 15% | 1.37 | 7 | -0.32 | 14% | 0.64 | 6 |
| cizgi / 24 mum / r1 / tp 2R ⚠️az | 13 | +0.31 | 54% | 2.30 | 7 | -0.48 | 14% | 0.16 | 3 |
| cizgi / 24 mum / be 2.0 / tp 2R ⚠️az | 13 | +0.28 | 62% | 1.71 | 7 | -0.79 | 14% | 0.12 | 3 |
| cizgi / 24 mum / be 3.0 / tp 2R ⚠️az | 13 | +0.25 | 62% | 1.64 | 7 | -0.74 | 14% | 0.17 | 3 |
| cizgi / 48 mum / r1 / tp 2R ⚠️az | 15 | +0.20 | 47% | 1.72 | 9 | -0.20 | 22% | 0.59 | 5 |

**Kırılım 15m — 0-1 yıldız — en iyi ayar: orta / 48 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 13 | 0 | 110.8 $ | +10.8 $ | 10.7 $ | 97.8 $ | 2 |
| Sadece son dönem (100 $ ile başlayarak) | 6 | 0 | 93.5 $ | -6.5 $ | 6.5 $ | 93.5 $ | 1 |

#### Kırılım 15m — ⚠️ notlu: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 24 mum / yok / tp %33 | 82 | +0.24 | 9% | 1.24 | 15 | -1.10 | 0% | 0.00 | 25 |
| orta / 24 mum / be 3.0 / tp %33 | 83 | +0.07 | 30% | 1.15 | 15 | -0.63 | 20% | 0.16 | 8 |
| orta / 24 mum / be 1.5 / tp %33 | 83 | +0.06 | 48% | 1.12 | 15 | -0.45 | 33% | 0.38 | 5 |
| orta / 24 mum / be 1.5 / tp 2R | 83 | +0.05 | 49% | 1.10 | 15 | -0.37 | 33% | 0.49 | 5 |
| orta / 24 mum / be 2.0 / tp %33 | 83 | +0.04 | 42% | 1.09 | 15 | -0.52 | 27% | 0.30 | 5 |
| orta / 48 mum / yok / tp %33 | 102 | +0.04 | 8% | 1.04 | 30 | -0.92 | 3% | 0.12 | 33 |
| orta / 96 mum / yok / tp %33 | 114 | +0.04 | 8% | 1.04 | 38 | -0.66 | 8% | 0.34 | 35 |
| orta / 24 mum / be 2.0 / tp 2R | 83 | +0.03 | 43% | 1.07 | 15 | -0.41 | 27% | 0.45 | 5 |
| orta / 24 mum / be 3.0 / tp 2R | 83 | +0.03 | 33% | 1.07 | 15 | -0.44 | 20% | 0.41 | 7 |
| orta / 96 mum / be 1.5 / tp 2R | 115 | +0.03 | 51% | 1.06 | 39 | -0.12 | 49% | 0.79 | 6 |
| orta / 24 mum / be 3.0 / tp %10 | 83 | +0.02 | 30% | 1.04 | 15 | -0.63 | 20% | 0.16 | 8 |
| orta / 24 mum / be 1.5 / tp %10 | 83 | +0.02 | 48% | 1.04 | 15 | -0.45 | 33% | 0.38 | 5 |

**Kırılım 15m — ⚠️ notlu — en iyi ayar: orta / 24 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 71 | 26 | 63.2 $ | -36.8 $ | 45.2 $ | 54.8 $ | 4 |
| Sadece son dönem (100 $ ile başlayarak) | 12 | 3 | 86.9 $ | -13.1 $ | 13.1 $ | 86.9 $ | 2 |

### Kırılım 1H — EMA filtresinden geçen 304 sinyal (ilk 100 coin, 120 gün; son dönem = son 30 gün)

#### Kırılım 1H — ana: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 48 mum / yok / tp %10 | 78 | +0.12 | 21% | 1.14 | 40 | -0.63 | 12% | 0.32 | 12 |
| orta / 24 mum / yok / tp %10 | 61 | +0.10 | 20% | 1.12 | 32 | -0.54 | 16% | 0.40 | 12 |
| orta / 96 mum / yok / tp %10 | 92 | +0.10 | 23% | 1.12 | 48 | -0.64 | 12% | 0.30 | 17 |
| orta / 96 mum / yok / tp 2R | 92 | +0.06 | 37% | 1.09 | 49 | -0.25 | 27% | 0.68 | 11 |
| orta / 96 mum / be 1.5 / tp 2R | 95 | +0.04 | 47% | 1.09 | 49 | -0.30 | 33% | 0.51 | 8 |
| orta / 48 mum / yok / tp 2R | 78 | +0.03 | 36% | 1.05 | 41 | -0.31 | 24% | 0.61 | 9 |
| orta / 96 mum / be 2.0 / tp 2R | 95 | -0.01 | 42% | 0.98 | 49 | -0.29 | 31% | 0.53 | 8 |
| orta / 24 mum / yok / tp 2R | 61 | -0.02 | 34% | 0.98 | 32 | -0.09 | 31% | 0.87 | 8 |
| cizgi / 48 mum / be 1.5 / tp %33 | 109 | -0.02 | 53% | 0.97 | 52 | -0.20 | 42% | 0.66 | 5 |
| cizgi / 48 mum / be 1.5 / tp %10 | 109 | -0.02 | 53% | 0.96 | 52 | -0.19 | 42% | 0.68 | 5 |
| orta / 96 mum / be 3.0 / tp 2R | 95 | -0.02 | 29% | 0.96 | 49 | -0.29 | 22% | 0.53 | 10 |
| cizgi / 48 mum / be 1.5 / tp 2R | 109 | -0.02 | 53% | 0.96 | 52 | -0.21 | 42% | 0.65 | 5 |

**Kırılım 1H — ana — en iyi ayar: orta / 48 mum / yok / tp %10**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 117 | 1 | 85.2 $ | -14.8 $ | 32.3 $ | 83.2 $ | 5 |
| Sadece son dönem (100 $ ile başlayarak) | 41 | 1 | 73.9 $ | -26.1 $ | 28.0 $ | 72.0 $ | 4 |

#### Kırılım 1H — ana — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 35 | -0.08 | 23% | 0.91 | 32 | -0.74 | 9% | 0.23 | 8 |
| Short | 43 | +0.28 | 19% | 1.32 | 8 | -0.19 | 25% | 0.76 | 12 |
| ✅ var ⚠️az | 15 | -0.53 | 13% | 0.43 | 17 | -0.83 | 6% | 0.17 | 9 |
| ✅ yok | 63 | +0.27 | 22% | 1.33 | 23 | -0.48 | 17% | 0.44 | 17 |
| 2 yıldız ⚠️az | 27 | +0.80 | 30% | 2.07 | 10 | -0.36 | 20% | 0.57 | 5 |
| 3 yıldız | 46 | -0.32 | 13% | 0.65 | 28 | -0.69 | 11% | 0.26 | 14 |

#### Kırılım 1H — ana 2-3 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 48 mum / yok / tp %10 | 73 | +0.09 | 19% | 1.11 | 38 | -0.61 | 13% | 0.34 | 15 |
| orta / 24 mum / yok / tp %10 | 56 | +0.07 | 18% | 1.08 | 30 | -0.50 | 17% | 0.44 | 13 |
| orta / 96 mum / yok / tp %10 | 86 | +0.05 | 21% | 1.06 | 45 | -0.62 | 13% | 0.33 | 16 |
| orta / 96 mum / be 1.5 / tp 2R | 89 | +0.04 | 47% | 1.09 | 46 | -0.27 | 35% | 0.55 | 7 |
| orta / 96 mum / yok / tp 2R | 86 | +0.04 | 36% | 1.05 | 46 | -0.20 | 28% | 0.74 | 11 |
| orta / 48 mum / yok / tp 2R | 73 | +0.02 | 36% | 1.03 | 39 | -0.27 | 26% | 0.65 | 9 |
| orta / 96 mum / be 2.0 / tp 2R | 89 | -0.01 | 42% | 0.98 | 46 | -0.26 | 33% | 0.57 | 7 |
| cizgi / 48 mum / be 1.5 / tp %33 | 104 | -0.01 | 54% | 0.98 | 50 | -0.17 | 44% | 0.70 | 5 |
| cizgi / 48 mum / be 1.5 / tp %10 | 104 | -0.01 | 54% | 0.98 | 50 | -0.16 | 44% | 0.72 | 5 |
| cizgi / 48 mum / be 1.5 / tp 2R | 104 | -0.01 | 54% | 0.98 | 50 | -0.18 | 44% | 0.69 | 5 |
| cizgi / 96 mum / be 1.5 / tp %33 | 106 | -0.02 | 54% | 0.97 | 53 | -0.12 | 45% | 0.78 | 5 |
| cizgi / 96 mum / be 1.5 / tp %10 | 106 | -0.02 | 54% | 0.97 | 53 | -0.11 | 45% | 0.81 | 5 |

**Kırılım 1H — ana 2-3 yıldız — en iyi ayar: orta / 48 mum / yok / tp %10**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 110 | 1 | 84.8 $ | -15.2 $ | 31.6 $ | 82.8 $ | 5 |
| Sadece son dönem (100 $ ile başlayarak) | 39 | 1 | 76.0 $ | -24.0 $ | 26.0 $ | 74.0 $ | 4 |

#### Kırılım 1H — 0-1 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| cizgi / 24 mum / yok / tp %33 ⚠️az | 7 | +1.47 | 29% | 3.02 | 2 | -1.02 | 0% | 0.00 | 4 |
| cizgi / 48 mum / yok / tp %33 ⚠️az | 7 | +1.47 | 29% | 3.02 | 2 | -1.02 | 0% | 0.00 | 4 |
| orta / 24 mum / yok / tp %33 ⚠️az | 5 | +1.40 | 20% | 2.69 | 2 | -1.03 | 0% | 0.00 | 3 |
| orta / 48 mum / yok / tp %33 ⚠️az | 5 | +1.40 | 20% | 2.69 | 2 | -1.03 | 0% | 0.00 | 3 |
| cizgi / 96 mum / yok / tp %33 ⚠️az | 8 | +1.14 | 25% | 2.48 | 3 | -1.02 | 0% | 0.00 | 5 |
| orta / 96 mum / yok / tp %33 ⚠️az | 7 | +0.68 | 14% | 1.75 | 3 | -1.03 | 0% | 0.00 | 5 |
| orta / 24 mum / yok / tp %10 ⚠️az | 5 | +0.48 | 40% | 1.76 | 2 | -1.03 | 0% | 0.00 | 3 |
| orta / 48 mum / yok / tp %10 ⚠️az | 5 | +0.48 | 40% | 1.76 | 2 | -1.03 | 0% | 0.00 | 3 |
| orta / 96 mum / yok / tp %10 ⚠️az | 7 | +0.45 | 43% | 1.73 | 3 | -1.03 | 0% | 0.00 | 4 |
| cizgi / 24 mum / yok / tp %10 ⚠️az | 7 | +0.25 | 43% | 1.44 | 2 | -1.02 | 0% | 0.00 | 3 |
| cizgi / 48 mum / yok / tp %10 ⚠️az | 7 | +0.25 | 43% | 1.44 | 2 | -1.02 | 0% | 0.00 | 3 |
| orta / 96 mum / yok / tp 2R ⚠️az | 7 | +0.23 | 43% | 1.38 | 3 | -1.03 | 0% | 0.00 | 4 |

**Kırılım 1H — 0-1 yıldız — en iyi ayar: cizgi / 24 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 9 | 0 | 108.2 $ | +8.2 $ | 4.1 $ | 95.9 $ | 3 |
| Sadece son dönem (100 $ ile başlayarak) | 2 | 0 | 98.0 $ | -2.0 $ | 2.0 $ | 98.0 $ | 1 |

#### Kırılım 1H — ⚠️ notlu: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 96 mum / yok / tp 2R | 59 | -0.03 | 34% | 0.95 | 18 | -0.57 | 17% | 0.37 | 11 |
| orta / 96 mum / be 1.5 / tp %10 | 59 | -0.06 | 46% | 0.88 | 18 | -0.64 | 17% | 0.13 | 8 |
| orta / 96 mum / be 1.5 / tp %33 | 59 | -0.07 | 44% | 0.85 | 18 | -0.64 | 17% | 0.13 | 8 |
| orta / 48 mum / be 1.5 / tp %10 | 45 | -0.08 | 42% | 0.86 | 17 | -0.62 | 18% | 0.15 | 6 |
| orta / 24 mum / yok / tp 2R | 34 | -0.09 | 32% | 0.88 | 10 | -0.80 | 10% | 0.20 | 7 |
| orta / 96 mum / be 1.5 / tp 2R | 59 | -0.09 | 44% | 0.81 | 18 | -0.61 | 17% | 0.18 | 8 |
| orta / 48 mum / be 1.5 / tp %33 | 45 | -0.09 | 40% | 0.82 | 17 | -0.62 | 18% | 0.15 | 6 |
| orta / 96 mum / be 2.0 / tp %10 | 59 | -0.11 | 41% | 0.78 | 18 | -0.44 | 17% | 0.41 | 8 |
| orta / 48 mum / yok / tp 2R | 45 | -0.12 | 31% | 0.84 | 17 | -0.54 | 18% | 0.39 | 9 |
| orta / 96 mum / be 2.0 / tp %33 | 59 | -0.12 | 39% | 0.75 | 18 | -0.34 | 17% | 0.54 | 8 |
| orta / 96 mum / r1 / tp 2R | 60 | -0.13 | 33% | 0.63 | 18 | -0.26 | 28% | 0.47 | 9 |
| orta / 96 mum / be 3.0 / tp 2R | 59 | -0.13 | 25% | 0.74 | 18 | -0.53 | 11% | 0.29 | 10 |

**Kırılım 1H — ⚠️ notlu — en iyi ayar: orta / 96 mum / yok / tp 2R**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 74 | 3 | 85.0 $ | -15.0 $ | 25.5 $ | 83.2 $ | 4 |
| Sadece son dönem (100 $ ile başlayarak) | 19 | 1 | 88.9 $ | -11.1 $ | 13.0 $ | 87.0 $ | 3 |

### Kırılım 4H — EMA filtresinden geçen 1023 sinyal (bütün coinler, 2 yıl; son dönem = son 180 gün)

#### Kırılım 4H — ana: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 24 mum / yok / tp %33 | 185 | +0.21 | 19% | 1.26 | 109 | +0.63 | 24% | 1.81 | 30 |
| orta / 48 mum / yok / tp %33 | 253 | +0.19 | 21% | 1.23 | 142 | +0.40 | 20% | 1.49 | 34 |
| orta / 96 mum / yok / tp %33 | 287 | +0.19 | 21% | 1.23 | 165 | +0.17 | 17% | 1.21 | 32 |
| orta / 48 mum / be 2.0 / tp %33 | 261 | +0.16 | 38% | 1.31 | 144 | +0.02 | 44% | 1.04 | 18 |
| orta / 96 mum / be 2.0 / tp %33 | 296 | +0.14 | 39% | 1.28 | 167 | -0.09 | 41% | 0.81 | 14 |
| cizgi / 24 mum / be 3.0 / tp %33 | 313 | +0.14 | 46% | 1.27 | 183 | +0.13 | 51% | 1.31 | 15 |
| orta / 48 mum / be 3.0 / tp %33 | 261 | +0.13 | 29% | 1.25 | 144 | +0.15 | 32% | 1.38 | 23 |
| orta / 96 mum / be 3.0 / tp %33 | 296 | +0.12 | 30% | 1.24 | 168 | +0.02 | 30% | 1.04 | 14 |
| cizgi / 24 mum / be 2.0 / tp %33 | 313 | +0.12 | 49% | 1.24 | 183 | +0.14 | 55% | 1.33 | 13 |
| orta / 24 mum / be 3.0 / tp %33 | 190 | +0.11 | 26% | 1.21 | 110 | +0.26 | 35% | 1.71 | 22 |
| orta / 24 mum / be 2.0 / tp %33 | 190 | +0.11 | 33% | 1.21 | 110 | +0.11 | 45% | 1.31 | 17 |
| cizgi / 24 mum / yok / tp %33 | 299 | +0.10 | 29% | 1.14 | 178 | +0.25 | 31% | 1.37 | 41 |

**Kırılım 4H — ana — en iyi ayar: orta / 24 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 259 | 35 | 101.0 $ | +1.0 $ | 66.1 $ | 43.8 $ | 10 |
| Sadece son dönem (100 $ ile başlayarak) | 108 | 2 | 151.6 $ | +51.6 $ | 18.9 $ | 92.4 $ | 10 |

#### Kırılım 4H — ana — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 47 | -0.25 | 15% | 0.71 | 40 | +0.07 | 15% | 1.08 | 19 |
| Short | 138 | +0.37 | 21% | 1.46 | 69 | +0.96 | 29% | 2.31 | 33 |
| ✅ var | 53 | -0.17 | 15% | 0.81 | 30 | +1.05 | 30% | 2.47 | 24 |
| ✅ yok | 132 | +0.37 | 21% | 1.45 | 79 | +0.48 | 22% | 1.59 | 26 |
| 2 yıldız | 46 | -0.33 | 13% | 0.62 | 32 | -0.01 | 22% | 0.99 | 21 |
| 3 yıldız | 122 | +0.55 | 24% | 1.71 | 64 | +0.98 | 25% | 2.27 | 18 |

#### Kırılım 4H — ana 3 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 24 mum / yok / tp %33 | 125 | +0.57 | 24% | 1.73 | 64 | +0.98 | 25% | 2.27 | 18 |
| orta / 48 mum / yok / tp %33 | 168 | +0.42 | 23% | 1.53 | 85 | +0.63 | 21% | 1.78 | 25 |
| orta / 96 mum / yok / tp %33 | 190 | +0.40 | 23% | 1.51 | 103 | +0.40 | 18% | 1.48 | 26 |
| orta / 48 mum / be 2.0 / tp %33 | 172 | +0.28 | 40% | 1.62 | 86 | +0.06 | 43% | 1.17 | 14 |
| orta / 24 mum / be 2.0 / tp %33 | 127 | +0.27 | 35% | 1.57 | 65 | +0.15 | 42% | 1.43 | 18 |
| cizgi / 24 mum / be 3.0 / tp %33 | 212 | +0.27 | 49% | 1.58 | 110 | +0.26 | 57% | 1.67 | 13 |
| orta / 96 mum / be 2.0 / tp %33 | 195 | +0.26 | 41% | 1.58 | 104 | -0.02 | 41% | 0.95 | 14 |
| cizgi / 96 mum / be 3.0 / tp %33 | 246 | +0.26 | 49% | 1.56 | 129 | +0.16 | 53% | 1.39 | 15 |
| orta / 24 mum / be 3.0 / tp %33 | 127 | +0.25 | 29% | 1.53 | 65 | +0.21 | 34% | 1.60 | 18 |
| orta / 96 mum / be 3.0 / tp %33 | 195 | +0.25 | 32% | 1.55 | 104 | +0.02 | 29% | 1.04 | 15 |
| cizgi / 24 mum / yok / tp %33 | 206 | +0.25 | 31% | 1.35 | 108 | +0.55 | 38% | 1.87 | 30 |
| orta / 48 mum / be 3.0 / tp %33 | 172 | +0.24 | 31% | 1.53 | 86 | +0.12 | 30% | 1.33 | 16 |

**Kırılım 4H — ana 3 yıldız — en iyi ayar: orta / 24 mum / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 180 | 9 | 195.1 $ | +95.1 $ | 41.8 $ | 74.2 $ | 11 |
| Sadece son dönem (100 $ ile başlayarak) | 64 | 0 | 162.5 $ | +62.5 $ | 19.7 $ | 98.3 $ | 9 |

#### Kırılım 4H — ⚠️ notlu: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| cizgi / 24 mum / be 3.0 / tp %33 | 134 | +0.18 | 41% | 1.32 | 80 | +0.57 | 56% | 2.49 | 15 |
| cizgi / 48 mum / be 3.0 / tp %33 | 147 | +0.14 | 41% | 1.26 | 90 | +0.50 | 54% | 2.30 | 17 |
| cizgi / 96 mum / be 3.0 / tp %33 | 153 | +0.12 | 40% | 1.22 | 95 | +0.43 | 53% | 2.05 | 17 |
| cizgi / 24 mum / yok / tp %33 | 132 | +0.12 | 29% | 1.17 | 80 | +0.41 | 41% | 1.68 | 28 |
| cizgi / 48 mum / yok / tp 2R | 145 | +0.09 | 37% | 1.15 | 89 | +0.37 | 51% | 1.74 | 26 |
| cizgi / 96 mum / yok / tp 2R | 151 | +0.09 | 37% | 1.14 | 94 | +0.30 | 48% | 1.57 | 25 |
| cizgi / 24 mum / yok / tp 2R | 132 | +0.06 | 36% | 1.10 | 80 | +0.44 | 52% | 1.91 | 24 |
| cizgi / 48 mum / yok / tp %33 | 145 | +0.06 | 28% | 1.08 | 89 | +0.37 | 40% | 1.60 | 30 |
| cizgi / 24 mum / r1 / tp %33 | 135 | +0.04 | 28% | 1.11 | 81 | +0.18 | 36% | 1.65 | 16 |
| cizgi / 24 mum / be 2.0 / tp %33 | 134 | +0.04 | 44% | 1.08 | 80 | +0.46 | 60% | 2.21 | 15 |
| cizgi / 48 mum / be 2.0 / tp %33 | 147 | +0.04 | 44% | 1.07 | 90 | +0.41 | 59% | 2.06 | 17 |
| cizgi / 48 mum / r1 / tp %33 | 149 | +0.04 | 29% | 1.09 | 91 | +0.15 | 36% | 1.54 | 18 |

**Kırılım 4H — ⚠️ notlu — en iyi ayar: cizgi / 24 mum / be 3.0 / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 214 | 0 | 169.4 $ | +69.4 $ | 26.3 $ | 74.5 $ | 14 |
| Sadece son dönem (100 $ ile başlayarak) | 80 | 0 | 145.7 $ | +45.7 $ | 6.1 $ | 97.0 $ | 14 |

### Kırılım 1D — EMA filtresinden geçen 182 sinyal (bütün coinler, 2 yıl; son dönem = son 180 gün)

#### Kırılım 1D — ana: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| cizgi / 5 mum / yok / tp 2R | 40 | +0.36 | 45% | 1.66 | 14 | +0.23 | 43% | 1.41 | 9 |
| cizgi / 10 mum / yok / tp 2R | 51 | +0.28 | 43% | 1.50 | 18 | +0.12 | 39% | 1.20 | 10 |
| cizgi / 5 mum / yok / tp %33 | 40 | +0.16 | 52% | 1.34 | 14 | +0.26 | 43% | 1.48 | 6 |
| cizgi / 5 mum / be 3.0 / tp %33 | 40 | +0.16 | 55% | 1.35 | 15 | -0.21 | 33% | 0.60 | 6 |
| cizgi / 5 mum / be 1.5 / tp 2R | 40 | +0.14 | 55% | 1.30 | 15 | -0.10 | 47% | 0.80 | 7 |
| cizgi / 10 mum / be 3.0 / tp %33 | 51 | +0.13 | 53% | 1.29 | 19 | -0.15 | 32% | 0.68 | 7 |
| cizgi / 5 mum / be 1.5 / tp %33 | 40 | +0.13 | 55% | 1.29 | 15 | -0.08 | 47% | 0.85 | 7 |
| cizgi / 5 mum / be 2.0 / tp %33 | 40 | +0.12 | 55% | 1.27 | 15 | -0.11 | 47% | 0.78 | 7 |
| cizgi / 10 mum / be 1.5 / tp 2R | 51 | +0.12 | 55% | 1.26 | 19 | -0.02 | 47% | 0.96 | 7 |
| cizgi / 5 mum / be 3.0 / tp 2R | 40 | +0.12 | 52% | 1.26 | 15 | -0.29 | 33% | 0.44 | 8 |
| cizgi / 10 mum / be 1.5 / tp %33 | 51 | +0.12 | 55% | 1.26 | 19 | -0.04 | 47% | 0.92 | 7 |
| cizgi / 10 mum / yok / tp %33 | 51 | +0.12 | 51% | 1.23 | 18 | +0.11 | 39% | 1.19 | 7 |

**Kırılım 1D — ana — en iyi ayar: cizgi / 5 mum / yok / tp 2R**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 54 | 0 | 117.4 $ | +17.4 $ | 8.7 $ | 94.0 $ | 11 |
| Sadece son dönem (100 $ ile başlayarak) | 14 | 0 | 103.2 $ | +3.2 $ | 5.0 $ | 97.0 $ | 5 |

#### Kırılım 1D — ana — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long ⚠️az | 10 | -0.40 | 20% | 0.50 | 8 | +0.92 | 62% | 3.79 | 4 |
| Short | 30 | +0.61 | 53% | 2.33 | 6 | -0.70 | 17% | 0.17 | 6 |
| ✅ var ⚠️az | 27 | +0.33 | 44% | 1.59 | 10 | +0.38 | 50% | 1.76 | 6 |
| ✅ yok ⚠️az | 13 | +0.41 | 46% | 1.81 | 4 | -0.16 | 25% | 0.75 | 3 |
| 2 yıldız ⚠️az | 14 | +0.52 | 50% | 2.10 | 3 | -0.01 | 33% | 0.99 | 3 |
| 3 yıldız ⚠️az | 18 | +0.66 | 56% | 2.49 | 9 | +0.37 | 44% | 1.72 | 7 |

#### Kırılım 1D — ana 3 yıldız: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| cizgi / 5 mum / yok / tp 2R ⚠️az | 18 | +0.66 | 56% | 2.49 | 9 | +0.37 | 44% | 1.72 | 7 |
| orta / 3 mum / yok / tp %10 ⚠️az | 1 | +0.62 | 100% | - | 5 | -0.45 | 20% | 0.33 | 0 |
| orta / 3 mum / be 1.5 / tp %10 ⚠️az | 1 | +0.62 | 100% | - | 5 | -0.45 | 20% | 0.33 | 0 |
| orta / 3 mum / be 2.0 / tp %10 ⚠️az | 1 | +0.62 | 100% | - | 5 | -0.45 | 20% | 0.33 | 0 |
| orta / 3 mum / be 3.0 / tp %10 ⚠️az | 1 | +0.62 | 100% | - | 5 | -0.45 | 20% | 0.33 | 0 |
| orta / 3 mum / r1 / tp %10 ⚠️az | 1 | +0.62 | 100% | - | 5 | -0.44 | 20% | 0.34 | 0 |
| cizgi / 10 mum / yok / tp 2R ⚠️az | 24 | +0.47 | 50% | 1.93 | 12 | +0.28 | 42% | 1.50 | 10 |
| orta / 5 mum / yok / tp 2R ⚠️az | 11 | +0.36 | 45% | 1.65 | 6 | -0.39 | 17% | 0.46 | 6 |
| orta / 5 mum / yok / tp %33 ⚠️az | 11 | +0.33 | 45% | 1.61 | 6 | -0.11 | 17% | 0.85 | 6 |
| cizgi / 5 mum / be 3.0 / tp 2R ⚠️az | 18 | +0.22 | 56% | 1.49 | 10 | -0.24 | 30% | 0.48 | 7 |
| orta / 10 mum / yok / tp %33 ⚠️az | 15 | +0.20 | 40% | 1.33 | 9 | -0.01 | 22% | 0.99 | 7 |
| orta / 10 mum / yok / tp 2R ⚠️az | 15 | +0.19 | 40% | 1.32 | 9 | -0.26 | 22% | 0.63 | 7 |

**Kırılım 1D — ana 3 yıldız — en iyi ayar: cizgi / 5 mum / yok / tp 2R**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 27 | 0 | 115.3 $ | +15.3 $ | 7.0 $ | 93.0 $ | 9 |
| Sadece son dönem (100 $ ile başlayarak) | 9 | 0 | 103.3 $ | +3.3 $ | 2.6 $ | 100.0 $ | 3 |

#### Kırılım 1D — ⚠️ notlu: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| cizgi / 10 mum / r1 / tp %33 ⚠️az | 21 | +0.14 | 43% | 1.45 | 3 | +0.02 | 33% | 1.08 | 5 |
| cizgi / 10 mum / r1 / tp %10 ⚠️az | 21 | +0.12 | 67% | 1.56 | 3 | +0.20 | 67% | 2.26 | 3 |
| cizgi / 10 mum / yok / tp %33 ⚠️az | 21 | +0.10 | 48% | 1.19 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / be 1.5 / tp %33 ⚠️az | 21 | +0.08 | 52% | 1.16 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / r1 / tp 2R ⚠️az | 21 | +0.05 | 43% | 1.18 | 3 | +0.02 | 33% | 1.08 | 3 |
| cizgi / 10 mum / yok / tp 2R ⚠️az | 21 | +0.05 | 43% | 1.09 | 3 | -0.45 | 33% | 0.33 | 5 |
| cizgi / 10 mum / be 1.5 / tp 2R ⚠️az | 21 | +0.05 | 52% | 1.11 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / be 2.0 / tp %33 ⚠️az | 21 | +0.04 | 52% | 1.09 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / be 3.0 / tp %33 ⚠️az | 21 | +0.01 | 43% | 1.02 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / be 2.0 / tp 2R ⚠️az | 21 | +0.01 | 52% | 1.01 | 3 | -0.45 | 33% | 0.33 | 4 |
| cizgi / 10 mum / yok / tp %10 ⚠️az | 21 | +0.01 | 67% | 1.02 | 3 | +0.01 | 67% | 1.03 | 3 |
| cizgi / 10 mum / be 1.5 / tp %10 ⚠️az | 21 | +0.01 | 67% | 1.02 | 3 | +0.01 | 67% | 1.03 | 3 |

**Kırılım 1D — ⚠️ notlu — en iyi ayar: cizgi / 10 mum / r1 / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 24 | 0 | 102.9 $ | +2.9 $ | 3.7 $ | 99.3 $ | 3 |
| Sadece son dönem (100 $ ile başlayarak) | 3 | 0 | 100.0 $ | +0.0 $ | 0.6 $ | 99.4 $ | 1 |

## 2) FVG'den dönüş — 2463 sinyal (bütün coinler, 2 yıl; son dönem = son 180 gün)

Giriş: cizgi = tepki çizgisi (destekte üst, dirençte alt), orta = FVG ortası. Stop: FVG'nin öbür ucu + 0.1 x günlük ATR.


#### FVG — filtresiz: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 3 gün / yok / tp %10 | 947 | +0.23 | 31% | 1.32 | 403 | +0.05 | 25% | 1.07 | 33 |
| orta / 3 gün / yok / tp 2R | 951 | +0.23 | 42% | 1.38 | 407 | +0.12 | 39% | 1.19 | 28 |
| orta / 3 gün / yok / tp %33 | 919 | +0.21 | 13% | 1.24 | 393 | +0.08 | 10% | 1.09 | 99 |
| orta / 3 gün / be 2.0 / tp 2R | 953 | +0.19 | 33% | 1.49 | 408 | +0.05 | 29% | 1.12 | 27 |
| orta / 7 gün / yok / tp 2R | 1131 | +0.19 | 41% | 1.31 | 521 | +0.11 | 38% | 1.17 | 26 |
| orta / 3 gün / be 3.0 / tp 2R | 953 | +0.19 | 30% | 1.49 | 408 | +0.06 | 27% | 1.14 | 27 |
| orta / 3 gün / be 1.5 / tp 2R | 952 | +0.18 | 37% | 1.47 | 408 | +0.04 | 33% | 1.10 | 27 |
| orta / 1 gün / yok / tp %10 | 612 | +0.17 | 28% | 1.23 | 246 | -0.00 | 23% | 1.00 | 29 |
| orta / 7 gün / be 2.0 / tp 2R | 1135 | +0.17 | 33% | 1.41 | 522 | +0.03 | 29% | 1.06 | 25 |
| orta / 7 gün / be 3.0 / tp 2R | 1135 | +0.16 | 30% | 1.41 | 522 | +0.04 | 26% | 1.08 | 25 |
| orta / 1 gün / yok / tp 2R | 614 | +0.16 | 40% | 1.25 | 248 | +0.09 | 38% | 1.14 | 26 |
| orta / 7 gün / be 1.5 / tp 2R | 1134 | +0.16 | 37% | 1.39 | 522 | +0.02 | 34% | 1.05 | 25 |

**FVG — filtresiz — en iyi ayar: orta / 3 gün / yok / tp %10**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 1325 | 25 | 290.5 $ | +190.5 $ | 52.6 $ | 82.9 $ | 10 |
| Sadece son dönem (100 $ ile başlayarak) | 388 | 15 | 137.4 $ | +37.4 $ | 45.2 $ | 81.0 $ | 9 |

#### FVG — filtresiz — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long (🟩) | 503 | +0.27 | 30% | 1.37 | 203 | +0.03 | 26% | 1.04 | 23 |
| Short (🟥) | 444 | +0.20 | 31% | 1.27 | 200 | +0.08 | 25% | 1.10 | 29 |
| ⭐⭐ | 795 | +0.23 | 31% | 1.32 | 328 | +0.01 | 26% | 1.01 | 30 |
| ⭐⭐⭐ | 152 | +0.25 | 29% | 1.34 | 75 | +0.25 | 24% | 1.31 | 16 |
| yakın temas | 321 | +0.41 | 36% | 1.62 | 114 | +0.36 | 30% | 1.49 | 17 |
| gerçek temas | 626 | +0.14 | 28% | 1.19 | 289 | -0.07 | 24% | 0.91 | 21 |

#### FVG — EMA filtreli: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| orta / 1 gün / yok / tp %33 | 330 | +0.23 | 12% | 1.25 | 135 | -0.14 | 10% | 0.85 | 49 |
| cizgi / 3 gün / yok / tp %33 | 656 | +0.23 | 22% | 1.28 | 298 | -0.08 | 17% | 0.91 | 51 |
| cizgi / 7 gün / yok / tp %33 | 701 | +0.22 | 22% | 1.28 | 339 | -0.09 | 17% | 0.89 | 55 |
| orta / 3 gün / yok / tp %33 | 490 | +0.22 | 12% | 1.24 | 223 | -0.13 | 11% | 0.86 | 63 |
| cizgi / 1 gün / yok / tp %33 | 544 | +0.22 | 21% | 1.27 | 237 | -0.18 | 16% | 0.79 | 43 |
| orta / 3 gün / be 3.0 / tp 2R | 498 | +0.18 | 31% | 1.45 | 226 | +0.14 | 29% | 1.34 | 26 |
| orta / 3 gün / be 2.0 / tp 2R | 498 | +0.18 | 33% | 1.45 | 226 | +0.13 | 32% | 1.32 | 26 |
| orta / 3 gün / yok / tp 2R | 498 | +0.18 | 40% | 1.29 | 226 | +0.23 | 42% | 1.38 | 27 |
| orta / 3 gün / be 1.5 / tp 2R | 498 | +0.17 | 36% | 1.42 | 226 | +0.12 | 37% | 1.28 | 26 |
| orta / 7 gün / be 3.0 / tp 2R | 585 | +0.17 | 31% | 1.41 | 298 | +0.05 | 26% | 1.10 | 26 |
| orta / 7 gün / be 2.0 / tp 2R | 585 | +0.17 | 33% | 1.40 | 298 | +0.04 | 30% | 1.09 | 26 |
| orta / 7 gün / be 1.5 / tp 2R | 585 | +0.16 | 38% | 1.39 | 298 | +0.03 | 36% | 1.06 | 26 |

**FVG — EMA filtreli — en iyi ayar: orta / 1 gün / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 460 | 5 | 136.7 $ | +36.7 $ | 83.4 $ | 78.9 $ | 10 |
| Sadece son dönem (100 $ ile başlayarak) | 123 | 12 | 93.8 $ | -6.2 $ | 65.8 $ | 77.3 $ | 8 |

#### FVG — EMA filtreli — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long (🟩) | 112 | +0.37 | 10% | 1.39 | 39 | -0.87 | 3% | 0.14 | 48 |
| Short (🟥) | 218 | +0.17 | 13% | 1.18 | 96 | +0.16 | 12% | 1.17 | 47 |
| ⭐⭐ | 284 | +0.38 | 13% | 1.42 | 113 | -0.20 | 10% | 0.79 | 41 |
| ⭐⭐⭐ | 46 | -0.68 | 2% | 0.33 | 22 | +0.15 | 9% | 1.15 | 36 |
| yakın temas | 99 | +1.00 | 18% | 2.17 | 40 | -0.02 | 10% | 0.98 | 16 |
| gerçek temas | 231 | -0.09 | 9% | 0.90 | 95 | -0.19 | 9% | 0.80 | 43 |

## 3) EMA21 haftalık — 2433 kesişim (bütün coinler, bütün geçmiş; son dönem = son 180 gün)

Giriş: fvg = en yakın günlük FVG sınırı (%15 içinde), ema = EMA21 çizgisi. Stop: mum = kesişim mumunun dibi/tepesi, fvg = FVG'nin öbür ucu. İz: yok / r1be = 1R kârdan sonra 1R geriden.


#### EMA21 haftalık: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| giriş fvg / stop fvg / 8 hafta / yok / tp %33 | 804 | +0.40 | 25% | 1.52 | 185 | +0.30 | 23% | 1.38 | 40 |
| giriş fvg / stop fvg / 4 hafta / yok / tp %33 | 797 | +0.37 | 25% | 1.49 | 184 | +0.42 | 24% | 1.54 | 61 |
| giriş fvg / stop fvg / 2 hafta / yok / tp %33 | 783 | +0.34 | 24% | 1.43 | 172 | +0.33 | 24% | 1.42 | 58 |
| giriş fvg / stop fvg / 8 hafta / yok / tp 2R | 838 | +0.32 | 44% | 1.56 | 190 | +0.19 | 41% | 1.33 | 11 |
| giriş fvg / stop fvg / 8 hafta / yok / tp %10 | 872 | +0.31 | 49% | 1.59 | 192 | +0.20 | 45% | 1.35 | 12 |
| giriş fvg / stop fvg / 4 hafta / yok / tp 2R | 833 | +0.31 | 44% | 1.54 | 190 | +0.21 | 42% | 1.36 | 17 |
| giriş fvg / stop fvg / 2 hafta / yok / tp 2R | 803 | +0.30 | 44% | 1.52 | 177 | +0.20 | 41% | 1.33 | 17 |
| giriş fvg / stop fvg / 4 hafta / yok / tp %10 | 866 | +0.30 | 49% | 1.57 | 193 | +0.21 | 45% | 1.37 | 18 |
| giriş fvg / stop fvg / 2 hafta / yok / tp %10 | 834 | +0.30 | 48% | 1.56 | 179 | +0.21 | 45% | 1.37 | 19 |
| giriş fvg / stop fvg / 2 hafta / r1be / tp %10 | 843 | +0.22 | 56% | 1.58 | 183 | +0.09 | 53% | 1.20 | 14 |
| giriş fvg / stop fvg / 8 hafta / r1be / tp %10 | 880 | +0.22 | 56% | 1.57 | 195 | +0.12 | 53% | 1.28 | 12 |
| giriş fvg / stop fvg / 4 hafta / r1be / tp %10 | 875 | +0.21 | 56% | 1.54 | 196 | +0.11 | 53% | 1.26 | 12 |

**EMA21 haftalık — en iyi ayar: giriş fvg / stop fvg / 8 hafta / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 989 | 0 | 474.6 $ | +374.6 $ | 57.0 $ | 98.0 $ | 23 |
| Sadece son dönem (100 $ ile başlayarak) | 175 | 12 | 152.4 $ | +52.4 $ | 23.4 $ | 80.1 $ | 17 |

#### EMA21 haftalık — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 437 | +0.26 | 18% | 1.31 | 120 | +0.50 | 23% | 1.65 | 47 |
| Short | 367 | +0.56 | 34% | 1.84 | 65 | -0.07 | 23% | 0.91 | 25 |

## 4) RSI 1D — A: 11060 dönüş, B: 7792 dönüş + SMA kesişimi (bütün coinler, bütün geçmiş; son dönem = son 180 gün)


#### RSI 1D: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| B dönüş + SMA kesişimi / yok / tp %33 | 2918 | +0.01 | 34% | 1.01 | 705 | +0.09 | 33% | 1.14 | 83 |
| B dönüş + SMA kesişimi / yok / tp %10 | 3448 | -0.00 | 60% | 1.00 | 847 | -0.03 | 54% | 0.92 | 35 |
| B dönüş + SMA kesişimi / be 3.0 / tp %10 | 3452 | -0.00 | 59% | 0.99 | 848 | -0.03 | 54% | 0.93 | 35 |
| B dönüş + SMA kesişimi / be 2.0 / tp %10 | 3452 | -0.01 | 59% | 0.99 | 848 | -0.03 | 54% | 0.93 | 35 |
| B dönüş + SMA kesişimi / be 1.5 / tp %10 | 3452 | -0.01 | 60% | 0.98 | 848 | -0.04 | 54% | 0.91 | 35 |
| B dönüş + SMA kesişimi / be 2.0 / tp %33 | 3056 | -0.01 | 42% | 0.98 | 739 | -0.05 | 38% | 0.90 | 87 |
| B dönüş + SMA kesişimi / r1 / tp %10 | 3583 | -0.01 | 52% | 0.97 | 872 | -0.01 | 49% | 0.98 | 43 |
| B dönüş + SMA kesişimi / be 3.0 / tp %33 | 3018 | -0.01 | 35% | 0.98 | 733 | -0.03 | 32% | 0.95 | 74 |
| A dönüş / yok / tp %33 | 4728 | -0.02 | 27% | 0.98 | 1180 | -0.09 | 23% | 0.89 | 98 |
| B dönüş + SMA kesişimi / r1 / tp %33 | 3285 | -0.03 | 35% | 0.94 | 817 | -0.01 | 36% | 0.98 | 41 |
| B dönüş + SMA kesişimi / be 1.5 / tp %33 | 3069 | -0.03 | 45% | 0.95 | 743 | -0.08 | 42% | 0.85 | 58 |
| A dönüş / be 3.0 / tp %33 | 4987 | -0.04 | 26% | 0.93 | 1252 | -0.13 | 22% | 0.79 | 96 |

**RSI 1D — en iyi ayar: B dönüş + SMA kesişimi / yok / tp %33**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 2101 | 1522 | 3.0 $ | -97.0 $ | 220.6 $ | 3.0 $ | 56 |
| Sadece son dönem (100 $ ile başlayarak) | 393 | 312 | 114.5 $ | +14.5 $ | 68.3 $ | 79.9 $ | 57 |

#### RSI 1D — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 1590 | +0.07 | 32% | 1.11 | 329 | +0.34 | 31% | 1.50 | 81 |
| Short | 1328 | -0.07 | 35% | 0.89 | 376 | -0.13 | 36% | 0.80 | 104 |
| Kapanışla dönüş | 1658 | -0.04 | 34% | 0.94 | 422 | +0.12 | 36% | 1.19 | 49 |
| Fitille dönüş | 1260 | +0.07 | 34% | 1.11 | 283 | +0.04 | 30% | 1.06 | 47 |

## 4) RSI 1W — A: 1156 dönüş, B: 720 dönüş + SMA kesişimi (bütün coinler, bütün geçmiş; son dönem = son 180 gün)


#### RSI 1W: eğitim dönemine göre en iyi 12 ayar

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| B dönüş + SMA kesişimi / be 2.0 / tp 2R | 109 | +0.27 | 41% | 1.66 | 31 | +0.51 | 55% | 2.76 | 9 |
| B dönüş + SMA kesişimi / be 3.0 / tp 2R | 99 | +0.27 | 36% | 1.62 | 29 | +0.47 | 48% | 2.52 | 9 |
| B dönüş + SMA kesişimi / yok / tp 2R | 91 | +0.26 | 43% | 1.45 | 27 | +0.55 | 59% | 2.48 | 12 |
| B dönüş + SMA kesişimi / be 1.5 / tp %33 | 131 | +0.26 | 50% | 1.61 | 40 | +0.61 | 68% | 3.23 | 11 |
| B dönüş + SMA kesişimi / be 2.0 / tp %33 | 131 | +0.25 | 49% | 1.59 | 40 | +0.63 | 65% | 3.32 | 11 |
| B dönüş + SMA kesişimi / be 1.5 / tp 2R | 110 | +0.25 | 48% | 1.59 | 35 | +0.45 | 63% | 2.43 | 9 |
| B dönüş + SMA kesişimi / be 3.0 / tp %33 | 131 | +0.25 | 47% | 1.59 | 40 | +0.62 | 60% | 3.29 | 11 |
| B dönüş + SMA kesişimi / yok / tp %33 | 131 | +0.24 | 51% | 1.49 | 40 | +0.68 | 68% | 3.27 | 14 |
| A dönüş / yok / tp %33 | 345 | +0.16 | 44% | 1.29 | 105 | +0.32 | 41% | 1.55 | 19 |
| B dönüş + SMA kesişimi / yok / tp %10 | 169 | +0.15 | 78% | 1.67 | 47 | +0.15 | 77% | 1.73 | 6 |
| B dönüş + SMA kesişimi / be 1.5 / tp %10 | 169 | +0.15 | 78% | 1.67 | 47 | +0.17 | 77% | 1.92 | 6 |
| B dönüş + SMA kesişimi / be 2.0 / tp %10 | 169 | +0.15 | 78% | 1.67 | 47 | +0.17 | 77% | 1.92 | 6 |

**RSI 1W — en iyi ayar: B dönüş + SMA kesişimi / be 2.0 / tp 2R**

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Tüm dönem (100 $ ile başlayarak) | 140 | 0 | 145.7 $ | +45.7 $ | 9.0 $ | 92.9 $ | 24 |
| Sadece son dönem (100 $ ile başlayarak) | 31 | 0 | 115.8 $ | +15.8 $ | 3.2 $ | 97.8 $ | 12 |

#### RSI 1W — en iyi ayar, sinyal özelliklerine göre

| Ayar | Eğitim işlem | Eğitim ort. R | Eğitim kazanan | Eğitim PF | Son dönem işlem | Son dönem ort. R | Son dönem kazanan | Son dönem PF | En kötü seri |
|---|---|---|---|---|---|---|---|---|---|
| Long | 61 | +0.44 | 44% | 2.43 | 26 | +0.71 | 58% | 4.09 | 9 |
| Short | 48 | +0.06 | 38% | 1.11 | 5 | -0.53 | 40% | 0.12 | 12 |
| Kapanışla dönüş | 58 | +0.28 | 40% | 1.75 | 17 | +0.50 | 47% | 2.47 | 7 |
| Fitille dönüş | 51 | +0.26 | 43% | 1.58 | 14 | +0.53 | 64% | 3.28 | 5 |

## 5) Stratejiler birlikte — tek 100 $ bakiye (son 2 yıl)

Eğitimde ortalaması artı ve en az 30 işlemi olan stratejilerin en iyi ayarları aynı bakiyede birlikte çalışır. Aynı coinde aynı anda tek pozisyon (önce gelen alınır); teminat yetmezse işlem atlanır.

- EMA21 haftalık: giriş fvg / stop fvg / 8 hafta / yok / tp %33 (eğitim 804 işlem, ort. +0.40R)
- FVG — EMA filtreli: orta / 1 gün / yok / tp %33 (eğitim 330 işlem, ort. +0.23R)
- Kırılım 4H — ana 3 yıldız: orta / 24 mum / yok / tp %33 (eğitim 125 işlem, ort. +0.57R)
- Kırılım 4H — ⚠️ notlu: cizgi / 24 mum / be 3.0 / tp %33 (eğitim 134 işlem, ort. +0.18R)
- Kırılım 1D — ana: cizgi / 5 mum / yok / tp 2R (eğitim 40 işlem, ort. +0.36R)
- RSI 1W: B dönüş + SMA kesişimi / be 2.0 / tp 2R (eğitim 109 işlem, ort. +0.27R)

| Dönem | Alınan işlem | Teminat yetmediği için atlanan | Son bakiye | Kâr / zarar | En büyük düşüş | En düşük bakiye | Aynı anda en çok açık |
|---|---|---|---|---|---|---|---|
| Son 2 yıl (100 $ ile başlayarak) | 1386 | 11 | 529.0 $ | +429.0 $ | 92.2 $ | 72.5 $ | 38 |
| Son 180 gün (100 $ ile başlayarak) | 346 | 105 | 139.8 $ | +39.8 $ | 32.7 $ | 74.2 $ | 29 |

| Strateji | İşlem | Ort. R | Toplam $ |
|---|---|---|---|
| EMA21 haftalık | 508 | +0.33 | +166.4 $ |
| FVG — EMA filtreli | 406 | +0.12 | +48.0 $ |
| Kırılım 4H — ana 3 yıldız | 166 | +0.75 | +123.9 $ |
| Kırılım 4H — ⚠️ notlu | 178 | +0.40 | +71.1 $ |
| Kırılım 1D — ana | 50 | +0.37 | +18.4 $ |
| RSI 1W | 89 | +0.41 | +36.3 $ |

## 6) Aynı anda sınırlı işlem (tek işlem / en fazla 3 işlem)

a = bekleyen limit emirler serbest, ilk dolan alınır, yer yoksa dolan emir iptal sayılır. b = emir verildiği andan işlem kapanana (ya da emir iptal olana) kadar yer tutar, o sırada gelen sinyaller atlanır. Atlanan = yer olmadığı için alınmayan işlem. Hepsi 100 $ ile başlar, işlem başına 1 $ risk.

| Strateji | En fazla açık | Emir kuralı | Son 2 yıl: işlem / atlanan | Son 2 yıl bakiye | En büyük düşüş | Son 180 gün: işlem | Son 180 gün bakiye |
|---|---|---|---|---|---|---|---|
| EMA21 haftalık | 1 | a | 63 / 480 | 128.2 $ | 9.4 $ | 26 | 92.9 $ |
| EMA21 haftalık | 1 | b | 25 / 518 | 113.7 $ | 5.1 $ | 2 | 97.9 $ |
| EMA21 haftalık | 2 | a | 135 / 408 | 128.0 $ | 21.7 $ | 36 | 108.0 $ |
| EMA21 haftalık | 2 | b | 51 / 492 | 124.7 $ | 9.2 $ | 3 | 96.9 $ |
| EMA21 haftalık | 3 | a | 182 / 361 | 150.7 $ | 18.0 $ | 52 | 114.9 $ |
| EMA21 haftalık | 3 | b | 77 / 466 | 122.0 $ | 10.7 $ | 11 | 92.9 $ |
| FVG — EMA filtreli | 1 | a | 146 / 319 | 99.5 $ | 32.4 $ | 35 | 105.1 $ |
| FVG — EMA filtreli | 1 | b | 97 / 368 | 76.9 $ | 38.6 $ | 19 | 110.9 $ |
| FVG — EMA filtreli | 2 | a | 251 / 214 | 126.1 $ | 27.5 $ | 59 | 102.8 $ |
| FVG — EMA filtreli | 2 | b | 170 / 295 | 100.1 $ | 26.9 $ | 41 | 107.7 $ |
| FVG — EMA filtreli | 3 | a | 322 / 143 | 119.3 $ | 38.7 $ | 76 | 111.4 $ |
| FVG — EMA filtreli | 3 | b | 226 / 239 | 130.5 $ | 30.8 $ | 57 | 122.4 $ |
| Kırılım 4H — ana 3 yıldız | 1 | a | 53 / 136 | 119.3 $ | 12.3 $ | 21 | 107.4 $ |
| Kırılım 4H — ana 3 yıldız | 1 | b | 33 / 156 | 100.3 $ | 12.4 $ | 12 | 98.9 $ |
| Kırılım 4H — ana 3 yıldız | 2 | a | 104 / 85 | 122.4 $ | 18.7 $ | 43 | 109.6 $ |
| Kırılım 4H — ana 3 yıldız | 2 | b | 59 / 130 | 118.3 $ | 10.2 $ | 20 | 109.6 $ |
| Kırılım 4H — ana 3 yıldız | 3 | a | 132 / 57 | 144.7 $ | 27.5 $ | 52 | 136.5 $ |
| Kırılım 4H — ana 3 yıldız | 3 | b | 77 / 112 | 127.5 $ | 17.4 $ | 30 | 110.7 $ |
| Kırılım 4H — ⚠️ notlu | 1 | a | 53 / 161 | 96.8 $ | 12.8 $ | 13 | 114.4 $ |
| Kırılım 4H — ⚠️ notlu | 1 | b | 45 / 169 | 103.2 $ | 8.8 $ | 13 | 102.3 $ |
| Kırılım 4H — ⚠️ notlu | 2 | a | 94 / 120 | 108.8 $ | 12.9 $ | 28 | 113.9 $ |
| Kırılım 4H — ⚠️ notlu | 2 | b | 81 / 133 | 109.1 $ | 12.6 $ | 24 | 107.4 $ |
| Kırılım 4H — ⚠️ notlu | 3 | a | 129 / 85 | 111.9 $ | 19.4 $ | 40 | 116.1 $ |
| Kırılım 4H — ⚠️ notlu | 3 | b | 110 / 104 | 112.0 $ | 18.1 $ | 34 | 108.9 $ |
| Kırılım 1D — ana | 1 | a | 9 / 45 | 100.3 $ | 2.0 $ | 3 | 100.4 $ |
| Kırılım 1D — ana | 1 | b | 9 / 45 | 94.3 $ | 7.0 $ | 2 | 101.4 $ |
| Kırılım 1D — ana | 2 | a | 23 / 31 | 103.1 $ | 4.0 $ | 7 | 101.2 $ |
| Kırılım 1D — ana | 2 | b | 17 / 37 | 95.3 $ | 7.1 $ | 6 | 100.3 $ |
| Kırılım 1D — ana | 3 | a | 30 / 24 | 105.1 $ | 5.0 $ | 10 | 101.2 $ |
| Kırılım 1D — ana | 3 | b | 25 / 29 | 101.1 $ | 5.1 $ | 10 | 104.2 $ |
| RSI 1W | 1 | a | 14 / 76 | 106.9 $ | 4.0 $ | 9 | 109.4 $ |
| RSI 1W | 1 | b | 14 / 76 | 106.9 $ | 4.0 $ | 9 | 109.4 $ |
| RSI 1W | 2 | a | 26 / 64 | 107.9 $ | 4.1 $ | 12 | 110.5 $ |
| RSI 1W | 2 | b | 26 / 64 | 107.9 $ | 4.1 $ | 12 | 110.5 $ |
| RSI 1W | 3 | a | 39 / 51 | 113.4 $ | 5.1 $ | 16 | 109.5 $ |
| RSI 1W | 3 | b | 39 / 51 | 113.4 $ | 5.1 $ | 16 | 109.5 $ |
| HEPSİ BİRLİKTE | 1 | a | 109 / 1446 | 127.4 $ | 12.4 $ | 28 | 103.9 $ |
| HEPSİ BİRLİKTE | 1 | b | 51 / 1504 | 86.3 $ | 32.4 $ | 1 | 99.0 $ |
| HEPSİ BİRLİKTE | 2 | a | 187 / 1368 | 150.1 $ | 19.8 $ | 51 | 107.7 $ |
| HEPSİ BİRLİKTE | 2 | b | 112 / 1443 | 103.8 $ | 28.5 $ | 18 | 108.7 $ |
| HEPSİ BİRLİKTE | 3 | a | 287 / 1268 | 123.0 $ | 31.4 $ | 80 | 109.1 $ |
| HEPSİ BİRLİKTE | 3 | b | 164 / 1391 | 156.3 $ | 16.4 $ | 30 | 116.0 $ |
| EMA21 haftalık + FVG | 1 | a | 108 / 900 | 111.3 $ | 11.8 $ | 35 | 101.8 $ |
| EMA21 haftalık + FVG | 1 | b | 40 / 968 | 91.3 $ | 16.6 $ | 4 | 95.9 $ |
| EMA21 haftalık + FVG | 2 | a | 209 / 799 | 146.0 $ | 30.9 $ | 59 | 104.1 $ |
| EMA21 haftalık + FVG | 2 | b | 105 / 903 | 102.4 $ | 21.2 $ | 22 | 95.6 $ |
| EMA21 haftalık + FVG | 3 | a | 288 / 720 | 129.7 $ | 41.4 $ | 83 | 103.7 $ |
| EMA21 haftalık + FVG | 3 | b | 164 / 844 | 110.4 $ | 27.1 $ | 38 | 83.3 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 1 | a | 113 / 1084 | 120.9 $ | 15.4 $ | 33 | 103.8 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 1 | b | 46 / 1151 | 95.2 $ | 23.0 $ | 1 | 99.0 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 2 | a | 208 / 989 | 142.3 $ | 36.0 $ | 62 | 104.6 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 2 | b | 106 / 1091 | 101.7 $ | 31.0 $ | 18 | 116.6 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 3 | a | 280 / 917 | 152.0 $ | 38.1 $ | 86 | 90.9 $ |
| EMA21 + FVG + Kırılım 4H — ana 3 yıldız | 3 | b | 163 / 1034 | 121.1 $ | 25.5 $ | 32 | 105.0 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 1 | a | 111 / 1111 | 130.2 $ | 11.4 $ | 34 | 102.8 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 1 | b | 58 / 1164 | 89.2 $ | 21.2 $ | 17 | 101.6 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 2 | a | 215 / 1007 | 150.9 $ | 28.9 $ | 55 | 106.2 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 2 | b | 121 / 1101 | 104.4 $ | 24.4 $ | 23 | 102.3 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 3 | a | 297 / 925 | 153.6 $ | 32.8 $ | 67 | 111.9 $ |
| EMA21 + FVG + Kırılım 4H — ⚠️ notlu | 3 | b | 188 / 1034 | 91.6 $ | 27.5 $ | 45 | 93.1 $ |
| EMA21 + FVG + Kırılım 1D — ana | 1 | a | 108 / 954 | 114.4 $ | 11.8 $ | 33 | 106.9 $ |
| EMA21 + FVG + Kırılım 1D — ana | 1 | b | 32 / 1030 | 115.3 $ | 13.4 $ | 3 | 96.9 $ |
| EMA21 + FVG + Kırılım 1D — ana | 2 | a | 208 / 854 | 150.1 $ | 28.9 $ | 57 | 109.2 $ |
| EMA21 + FVG + Kırılım 1D — ana | 2 | b | 92 / 970 | 130.3 $ | 11.3 $ | 16 | 101.1 $ |
| EMA21 + FVG + Kırılım 1D — ana | 3 | a | 264 / 798 | 143.4 $ | 33.6 $ | 83 | 100.3 $ |
| EMA21 + FVG + Kırılım 1D — ana | 3 | b | 143 / 919 | 138.3 $ | 13.6 $ | 30 | 103.5 $ |

## 9) Önerilen kurulumun incelemesi (3x, dolum payı %0.10)

| En fazla açık | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Son 180 gün bakiye |
|---|---|---|---|---|
| 3 | 755 | 328 $ | 18 $ | 180 $ |
| 5 | 1041 | 418 $ | 44 $ | 224 $ |

**En fazla 3 işlemde alınan işlemler — çeyreklere göre**

| Çeyrek | İşlem | Kazanan | Toplam $ | EMA21 $ | FVG $ | Kırılım $ |
|---|---|---|---|---|---|---|
| 2024-Ç4 | 99 | 48% | +36.1 | +29.6 | -1.4 | +7.9 |
| 2025-Ç1 | 86 | 36% | +4.8 | -0.5 | +0.8 | +4.6 |
| 2025-Ç2 | 89 | 40% | +11.6 | +7.2 | +11.5 | -7.1 |
| 2025-Ç3 | 103 | 50% | +53.4 | +34.3 | +19.4 | -0.3 |
| 2025-Ç4 | 70 | 36% | +7.7 | +0.5 | -5.9 | +13.0 |
| 2026-Ç1 | 85 | 40% | +34.8 | +6.9 | +10.0 | +17.9 |
| 2026-Ç2 | 84 | 46% | +49.6 | +25.3 | +7.8 | +16.5 |
| 2026-Ç3 | 105 | 40% | +23.9 | +15.4 | +7.6 | +0.9 |
| 2026-Ç4 | 34 | 41% | +6.0 | +0.2 | +4.6 | +1.2 |

| Grup | İşlem | Ort. R | Toplam $ | Ort. süre (gün) | Ort. stop mesafesi |
|---|---|---|---|---|---|
| Long | 330 | +0.33 | +110.0 $ | 1.8 | %5.5 |
| Short | 425 | +0.28 | +118.0 $ | 2.0 | %4.0 |
| EMA21 | 291 | +0.41 | +119.0 $ | 2.3 | %6.6 |
| FVG | 386 | +0.14 | +54.4 $ | 0.9 | %3.1 |
| K4H★3 | 78 | +0.70 | +54.6 $ | 5.8 | %5.0 |

**Fonlama ücreti tahmini:** 8 saatte %0.01 ve hep aleyhe varsayılırsa en fazla 3 işlemde 2 yılda yaklaşık 10.8 $ (işlem başına 0.014 $).

**Bekleyen limit emirler (ilk dolan alınır kuralı):** aynı anda en çok 58, ortalama 11.1 emir. OKX'te her bekleyen emir teminat ayırır; 100 $'lık hesapta bu sayı önemli.

**Komşu ayarlar (tek başına, en fazla 5 işlem, son 2 yıl / son 180 gün)**


EMA21 haftalık — en iyi 8 ve seçilen

| Ayar | 2 yıl | Düşüş | Son 180 gün |
|---|---|---|---|
| giriş fvg / stop fvg / 4 hafta / yok / tp %10 | 274 $ | 16 $ | 136 $ |
| giriş fvg / stop fvg / 2 hafta / yok / tp %10 ⬅ seçilen | 268 $ | 14 $ | 134 $ |
| giriş fvg / stop fvg / 8 hafta / yok / tp %10 | 267 $ | 16 $ | 134 $ |
| giriş fvg / stop fvg / 2 hafta / r1be / tp %10 | 227 $ | 9 $ | 120 $ |
| giriş fvg / stop fvg / 8 hafta / r1be / tp %10 | 223 $ | 10 $ | 126 $ |
| giriş fvg / stop fvg / 4 hafta / r1be / tp %10 | 221 $ | 10 $ | 124 $ |
| giriş fvg / stop mum / 8 hafta / yok / tp %10 | 163 $ | 6 $ | 119 $ |
| giriş fvg / stop mum / 4 hafta / yok / tp %10 | 162 $ | 8 $ | 117 $ |

FVG — EMA filtreli — en iyi 8 ve seçilen

| Ayar | 2 yıl | Düşüş | Son 180 gün |
|---|---|---|---|
| orta / 3 gün / yok / tp 2R ⬅ seçilen | 236 $ | 26 $ | 147 $ |
| orta / 3 gün / be 3.0 / tp 2R | 229 $ | 25 $ | 132 $ |
| orta / 3 gün / be 2.0 / tp 2R | 227 $ | 27 $ | 130 $ |
| orta / 7 gün / yok / tp 2R | 225 $ | 33 $ | 134 $ |
| orta / 7 gün / be 3.0 / tp 2R | 222 $ | 26 $ | 116 $ |
| orta / 3 gün / be 1.5 / tp 2R | 217 $ | 26 $ | 127 $ |
| orta / 7 gün / be 2.0 / tp 2R | 215 $ | 27 $ | 113 $ |
| orta / 7 gün / be 1.5 / tp 2R | 208 $ | 28 $ | 109 $ |

Kırılım 4H — ana 3 yıldız — en iyi 8 ve seçilen

| Ayar | 2 yıl | Düşüş | Son 180 gün |
|---|---|---|---|
| orta / 24 mum / yok / tp %33 ⬅ seçilen | 159 $ | 36 $ | 145 $ |
| orta / 48 mum / yok / tp %33 | 142 $ | 39 $ | 129 $ |
| orta / 96 mum / yok / tp %33 | 142 $ | 41 $ | 120 $ |
| orta / 48 mum / be 3.0 / tp %33 | 120 $ | 20 $ | 108 $ |
| orta / 24 mum / be 3.0 / tp %33 | 120 $ | 25 $ | 112 $ |
| cizgi / 96 mum / be 1.5 / tp %33 | 119 $ | 18 $ | 98 $ |
| cizgi / 96 mum / be 2.0 / tp %33 | 119 $ | 18 $ | 100 $ |
| orta / 48 mum / be 2.0 / tp %33 | 117 $ | 14 $ | 104 $ |

## 8) Kâr al seviyesi karşılaştırması (giriş, stop ve bekleme en iyi ayardaki gibi sabit)

%N = fiyat N% lehe gidince kâr al (short'ta fiyat 1/(1+N%) oranına inince; %100 = yarısı). Teminat karşılığı: 10x'te %10, 5x'te %20, 3x'te %33, spotta %100 = teminatın iki katı. yok = kâr al yok, işlem stopla ya da süre dolunca kapanır. 'Tek başına 5 işlem' = strateji tek başına, en fazla 5 açık işlem.


#### EMA21 haftalık — giriş fvg / stop fvg / 8 hafta / yok

| Kâr al | Eğitim işlem | Eğitim ort. R | Son dönem işlem | Son dönem ort. R | Kazanan | Ort. süre (gün) | Tek başına 5 işlem: 2 yıl | düşüş | son 180 gün |
|---|---|---|---|---|---|---|---|---|---|
| %10 | 872 | +0.31 | 192 | +0.20 | 49% | 2.7 | 267 $ | 16 $ | 134 $ |
| %33 | 804 | +0.40 | 185 | +0.30 | 25% | 10.0 | 166 $ | 21 $ | 125 $ |
| 2R | 838 | +0.32 | 190 | +0.19 | 44% | 6.0 | 249 $ | 12 $ | 117 $ |

Eğitime göre en iyi kâr al: **%33**

#### FVG — EMA filtreli — orta / 1 gün / yok

| Kâr al | Eğitim işlem | Eğitim ort. R | Son dönem işlem | Son dönem ort. R | Kazanan | Ort. süre (gün) | Tek başına 5 işlem: 2 yıl | düşüş | son 180 gün |
|---|---|---|---|---|---|---|---|---|---|
| %10 | 332 | +0.10 | 135 | -0.07 | 26% | 1.1 | 124 $ | 45 $ | 90 $ |
| %33 | 330 | +0.23 | 135 | -0.14 | 12% | 3.2 | 120 $ | 56 $ | 105 $ |
| 2R | 332 | +0.08 | 136 | +0.20 | 37% | 0.7 | 156 $ | 32 $ | 126 $ |

Eğitime göre en iyi kâr al: **%33**

#### Kırılım 4H — ana 3 yıldız — orta / 24 mum / yok

| Kâr al | Eğitim işlem | Eğitim ort. R | Son dönem işlem | Son dönem ort. R | Kazanan | Ort. süre (gün) | Tek başına 5 işlem: 2 yıl | düşüş | son 180 gün |
|---|---|---|---|---|---|---|---|---|---|
| %10 | 127 | +0.07 | 65 | +0.38 | 38% | 1.9 | 107 $ | 26 $ | 118 $ |
| %33 | 125 | +0.57 | 64 | +0.98 | 24% | 5.3 | 159 $ | 36 $ | 145 $ |
| 2R | 127 | +0.19 | 65 | +0.23 | 40% | 1.9 | 110 $ | 22 $ | 109 $ |

Eğitime göre en iyi kâr al: **%33**

#### Üçü birlikte (EMA21, FVG, K4H★3; kâr al: eğitimde en iyi)

| En fazla açık | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Son 180 gün bakiye |
|---|---|---|---|---|
| 3 | 280 | 152 $ | 38 $ | 91 $ |
| 5 | 511 | 175 $ | 51 $ | 111 $ |
| 10 | 803 | 341 $ | 68 $ | 148 $ |

## 7) Bütün kombinasyonlar — 3x, ilk dolan alınır (a)

Stratejiler: EMA21 = EMA21 haftalık (giriş fvg / stop fvg / 8 hafta / yok / tp %33), FVG = FVG — EMA filtreli (orta / 1 gün / yok / tp %33), K4H★3 = Kırılım 4H — ana 3 yıldız (orta / 24 mum / yok / tp %33), K4H⚠️ = Kırılım 4H — ⚠️ notlu (cizgi / 24 mum / be 3.0 / tp %33), K1D = Kırılım 1D — ana (cizgi / 5 mum / yok / tp 2R), RSI-W = RSI 1W (B dönüş + SMA kesişimi / be 2.0 / tp 2R). Oran = 2 yıllık kâr / en büyük düşüş (yüksek = az dalgalanmayla çok kazanç). Hepsi 100 $ ile başlar, işlem başına 1 $ risk.


#### Açık işlem en fazla 1 — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| FVG + K4H★3 + K1D | 109 | 98 $ | 49 $ | -0.0 | 136 $ | 7 $ |
| FVG + K1D | 92 | 88 $ | 41 $ | -0.3 | 123 $ | 7 $ |
| FVG + K1D + RSI-W | 75 | 82 $ | 36 $ | -0.5 | 121 $ | 7 $ |
| FVG + K4H★3 | 133 | 99 $ | 45 $ | -0.0 | 121 $ | 15 $ |
| K4H⚠️ + RSI-W | 39 | 109 $ | 10 $ | 0.9 | 116 $ | 1 $ |

#### Açık işlem en fazla 1 — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + FVG + K4H⚠️ + RSI-W | 104 | 146 $ | 11 $ | 4.0 | 103 $ | 11 $ |
| EMA21 + FVG + K4H★3 + K4H⚠️ + RSI-W | 105 | 145 $ | 12 $ | 3.6 | 104 $ | 11 $ |
| EMA21 + RSI-W | 64 | 132 $ | 9 $ | 3.5 | 93 $ | 15 $ |
| EMA21 | 63 | 128 $ | 9 $ | 3.0 | 93 $ | 15 $ |
| EMA21 + K4H★3 | 68 | 128 $ | 10 $ | 2.7 | 93 $ | 16 $ |

#### Açık işlem en fazla 2 — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| K4H★3 + K4H⚠️ + K1D | 106 | 152 $ | 16 $ | 3.3 | 141 $ | 4 $ |
| FVG + K4H★3 + K1D + RSI-W | 159 | 112 $ | 36 $ | 0.3 | 136 $ | 9 $ |
| FVG + K4H★3 + K1D | 186 | 113 $ | 53 $ | 0.2 | 134 $ | 11 $ |
| K4H★3 + K4H⚠️ | 138 | 135 $ | 20 $ | 1.8 | 134 $ | 6 $ |
| FVG + K1D + RSI-W | 140 | 107 $ | 27 $ | 0.2 | 130 $ | 13 $ |

#### Açık işlem en fazla 2 — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + FVG + K4H⚠️ + K1D | 194 | 163 $ | 18 $ | 3.5 | 122 $ | 10 $ |
| K4H★3 + K4H⚠️ + K1D | 106 | 152 $ | 16 $ | 3.3 | 141 $ | 4 $ |
| K4H★3 + K1D + RSI-W | 64 | 134 $ | 11 $ | 3.2 | 123 $ | 3 $ |
| EMA21 + FVG + K4H⚠️ + K1D + RSI-W | 187 | 153 $ | 18 $ | 3.0 | 116 $ | 10 $ |
| K4H★3 + K4H⚠️ + K1D + RSI-W | 81 | 136 $ | 13 $ | 2.8 | 120 $ | 4 $ |

#### Açık işlem en fazla 3 — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| FVG + K4H★3 + K4H⚠️ + K1D + RSI-W | 208 | 126 $ | 45 $ | 0.6 | 139 $ | 11 $ |
| K4H★3 + K4H⚠️ + K1D + RSI-W | 118 | 161 $ | 13 $ | 4.7 | 138 $ | 4 $ |
| K4H★3 | 132 | 145 $ | 27 $ | 1.6 | 136 $ | 15 $ |
| K4H★3 + K4H⚠️ + K1D | 165 | 140 $ | 21 $ | 1.9 | 136 $ | 7 $ |
| K4H★3 + K1D | 117 | 121 $ | 21 $ | 1.0 | 127 $ | 10 $ |

#### Açık işlem en fazla 3 — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + K4H★3 | 213 | 180 $ | 17 $ | 4.8 | 116 $ | 12 $ |
| K4H★3 + K4H⚠️ + K1D + RSI-W | 118 | 161 $ | 13 $ | 4.7 | 138 $ | 4 $ |
| EMA21 + K4H★3 + RSI-W | 211 | 175 $ | 17 $ | 4.5 | 116 $ | 12 $ |
| EMA21 + K4H★3 + K1D | 184 | 164 $ | 17 $ | 3.8 | 124 $ | 12 $ |
| EMA21 + K4H★3 + K4H⚠️ | 228 | 160 $ | 18 $ | 3.4 | 118 $ | 11 $ |

#### Açık işlem en fazla 5 — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + K4H★3 + K4H⚠️ + K1D + RSI-W | 312 | 200 $ | 27 $ | 3.8 | 148 $ | 13 $ |
| K4H★3 + K1D + RSI-W | 159 | 141 $ | 23 $ | 1.8 | 147 $ | 7 $ |
| K4H★3 + K4H⚠️ + K1D + RSI-W | 210 | 153 $ | 24 $ | 2.2 | 147 $ | 7 $ |
| EMA21 + K4H★3 + K4H⚠️ + K1D | 324 | 196 $ | 29 $ | 3.4 | 146 $ | 13 $ |
| K4H★3 + K1D | 162 | 142 $ | 27 $ | 1.5 | 146 $ | 10 $ |

#### Açık işlem en fazla 5 — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + K4H★3 + RSI-W | 320 | 226 $ | 22 $ | 5.6 | 129 $ | 13 $ |
| EMA21 + K4H★3 | 322 | 219 $ | 25 $ | 4.9 | 133 $ | 13 $ |
| EMA21 + K4H★3 + K4H⚠️ + RSI-W | 348 | 222 $ | 25 $ | 4.8 | 135 $ | 13 $ |
| EMA21 + K4H★3 + K1D + RSI-W | 288 | 200 $ | 23 $ | 4.3 | 144 $ | 13 $ |
| EMA21 + K1D + RSI-W | 248 | 182 $ | 19 $ | 4.2 | 113 $ | 20 $ |

#### Açık işlem en fazla 10 — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| K4H★3 + K4H⚠️ | 346 | 208 $ | 45 $ | 2.4 | 183 $ | 16 $ |
| K4H★3 + K4H⚠️ + K1D + RSI-W | 339 | 172 $ | 38 $ | 1.9 | 182 $ | 9 $ |
| K4H★3 + K1D + RSI-W | 224 | 161 $ | 34 $ | 1.8 | 178 $ | 9 $ |
| K4H★3 + RSI-W | 217 | 177 $ | 37 $ | 2.1 | 176 $ | 7 $ |
| K4H★3 + K4H⚠️ + K1D | 347 | 165 $ | 45 $ | 1.4 | 175 $ | 15 $ |

#### Açık işlem en fazla 10 — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + K4H★3 | 528 | 349 $ | 32 $ | 7.8 | 158 $ | 21 $ |
| EMA21 + K4H★3 + K4H⚠️ | 592 | 338 $ | 33 $ | 7.3 | 154 $ | 29 $ |
| EMA21 + K4H★3 + K4H⚠️ + RSI-W | 570 | 320 $ | 32 $ | 6.9 | 144 $ | 23 $ |
| EMA21 + K4H★3 + RSI-W | 530 | 298 $ | 30 $ | 6.6 | 111 $ | 26 $ |
| EMA21 + K4H★3 + K1D + RSI-W | 502 | 328 $ | 37 $ | 6.2 | 136 $ | 23 $ |

#### Açık işlem sınırsız — son 180 günün kârına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| K4H★3 + K4H⚠️ + K1D + RSI-W | 494 | 283 $ | 42 $ | 4.3 | 213 $ | 11 $ |
| K4H★3 + K4H⚠️ + RSI-W | 452 | 276 $ | 40 $ | 4.5 | 209 $ | 11 $ |
| K4H★3 + K4H⚠️ + K1D | 411 | 246 $ | 48 $ | 3.0 | 197 $ | 17 $ |
| EMA21 + K4H⚠️ + K1D + RSI-W | 830 | 400 $ | 54 $ | 5.6 | 196 $ | 22 $ |
| K4H★3 + K4H⚠️ | 369 | 241 $ | 45 $ | 3.2 | 193 $ | 15 $ |

#### Açık işlem sınırsız — kâr / düşüş oranına göre en iyi 5

| Kombinasyon | 2 yıl işlem | 2 yıl bakiye | En büyük düşüş | Oran | Son 180 gün bakiye | Son 180 gün düşüş |
|---|---|---|---|---|---|---|
| EMA21 + K4H★3 + RSI-W | 793 | 453 $ | 42 $ | 8.5 | 175 $ | 24 $ |
| EMA21 + K4H★3 + K4H⚠️ + RSI-W | 966 | 521 $ | 51 $ | 8.3 | 184 $ | 28 $ |
| EMA21 + K4H★3 + K4H⚠️ | 899 | 485 $ | 51 $ | 7.5 | 171 $ | 33 $ |
| EMA21 + K4H★3 | 721 | 419 $ | 44 $ | 7.2 | 162 $ | 27 $ |
| K1D + RSI-W | 144 | 156 $ | 8 $ | 6.8 | 119 $ | 5 $ |

Toplam süre: 3 dk
