# Portföy ve bütçe kuralları testi — günlük trend stratejisi
1189 sinyal (dolan limit emirler), son 365 gün. 100 USDT başlangıç, bileşik: her işlemin riski o anki bakiyeye göre. Eğitim ilk 240 gün, doğrulama son 125 gün. Kurgu: günlük kırılım (EMA50), sabah fiyatına limit, stop seviye − 0,5 ATR, TP 5R. Komisyon, long funding ve stoplarda %0,05 kayma dahil. "Düşüş": bakiyenin zirveden en fazla geri çekilmesi (kapanan işlemlere göre).

## %1 risk
| Kurallar | Yıl sonu bakiye | Eğitim dönemi getiri | Doğrulama dönemi getiri | En büyük düşüş | En düşük bakiye | İşlem / atlanan | En uzun kayıp serisi | Aynı anda en fazla açık risk |
|---|---|---|---|---|---|---|---|---|
| %1 risk · en fazla 8 pozisyon · öncelik: 24s hacim | 154 USDT | %+43 | %+8 | %21 | 91 USDT | 221 / 968 | 22 | %9 |
| %1 risk · en fazla 5 pozisyon · öncelik: 24s hacim | 147 USDT | %+47 | %+0 | %15 | 93 USDT | 134 / 1055 | 13 | %5 |
| %1 risk · en fazla 3 pozisyon · öncelik: 24s hacim | 133 USDT | %+41 | %-6 | %9 | 94 USDT | 87 / 1102 | 9 | %3 |
| %1 risk · en fazla 8 pozisyon · öncelik: kırılım hacmi | 129 USDT | %+28 | %+1 | %23 | 88 USDT | 223 / 966 | 15 | %9 |
| %1 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim | 123 USDT | %+22 | %+0 | %17 | 84 USDT | 125 / 1064 | 11 | %5 |
| %1 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim | 119 USDT | %+22 | %-3 | %15 | 85 USDT | 143 / 1046 | 12 | %6 |
| %1 risk · en fazla 3 pozisyon · öncelik: kırılım hacmi | 111 USDT | %+1 | %+11 | %13 | 87 USDT | 91 / 1098 | 11 | %3 |
| %1 risk · en fazla 5 pozisyon · öncelik: kırılım hacmi | 101 USDT | %-10 | %+11 | %19 | 82 USDT | 152 / 1037 | 13 | %5 |
| %1 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi | 95 USDT | %-4 | %-1 | %24 | 76 USDT | 133 / 1056 | 14 | %5 |
| %1 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi | 87 USDT | %-15 | %+2 | %24 | 76 USDT | 155 / 1034 | 14 | %6 |

## %2 risk
| Kurallar | Yıl sonu bakiye | Eğitim dönemi getiri | Doğrulama dönemi getiri | En büyük düşüş | En düşük bakiye | İşlem / atlanan | En uzun kayıp serisi | Aynı anda en fazla açık risk |
|---|---|---|---|---|---|---|---|---|
| %2 risk · en fazla 8 pozisyon · öncelik: 24s hacim | 196 USDT | %+77 | %+11 | %38 | 82 USDT | 221 / 968 | 22 | %18 |
| %2 risk · en fazla 5 pozisyon · öncelik: 24s hacim | 195 USDT | %+96 | %-0 | %28 | 86 USDT | 134 / 1055 | 13 | %11 |
| %2 risk · en fazla 3 pozisyon · öncelik: 24s hacim | 165 USDT | %+87 | %-12 | %17 | 88 USDT | 87 / 1102 | 9 | %6 |
| %2 risk · en fazla 8 pozisyon · öncelik: kırılım hacmi | 148 USDT | %+48 | %+0 | %40 | 76 USDT | 223 / 966 | 15 | %18 |
| %2 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim | 141 USDT | %+41 | %-0 | %32 | 70 USDT | 125 / 1064 | 11 | %11 |
| %2 risk · en fazla 5 pozisyon · öncelik: kırılım hacmi · toplam açık risk ≤ %8 | 133 USDT | %+16 | %+15 | %28 | 72 USDT | 106 / 1083 | 9 | %8 |
| %2 risk · en fazla 8 pozisyon · öncelik: kırılım hacmi · toplam açık risk ≤ %8 | 133 USDT | %+16 | %+15 | %28 | 72 USDT | 106 / 1083 | 9 | %8 |
| %2 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim | 127 USDT | %+38 | %-8 | %29 | 71 USDT | 143 / 1046 | 12 | %13 |
| %2 risk · en fazla 3 pozisyon · öncelik: kırılım hacmi | 119 USDT | %-1 | %+20 | %26 | 74 USDT | 91 / 1098 | 11 | %6 |
| %2 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim · toplam açık risk ≤ %8 | 107 USDT | %+43 | %-25 | %32 | 88 USDT | 101 / 1088 | 11 | %8 |
| %2 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim · toplam açık risk ≤ %8 | 107 USDT | %+43 | %-25 | %32 | 88 USDT | 101 / 1088 | 11 | %8 |
| %2 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi · toplam açık risk ≤ %8 | 97 USDT | %-13 | %+12 | %30 | 70 USDT | 104 / 1085 | 11 | %8 |
| %2 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi · toplam açık risk ≤ %8 | 97 USDT | %-13 | %+12 | %30 | 70 USDT | 104 / 1085 | 11 | %8 |
| %2 risk · en fazla 5 pozisyon · öncelik: kırılım hacmi | 95 USDT | %-21 | %+20 | %36 | 65 USDT | 152 / 1037 | 13 | %11 |
| %2 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi | 87 USDT | %-10 | %-3 | %43 | 57 USDT | 133 / 1056 | 14 | %11 |
| %2 risk · en fazla 5 pozisyon · öncelik: 24s hacim · toplam açık risk ≤ %8 | 84 USDT | %-1 | %-15 | %39 | 77 USDT | 98 / 1091 | 13 | %8 |
| %2 risk · en fazla 8 pozisyon · öncelik: 24s hacim · toplam açık risk ≤ %8 | 84 USDT | %-1 | %-15 | %39 | 77 USDT | 98 / 1091 | 13 | %8 |
| %2 risk · en fazla 8 pozisyon · aynı yönde en fazla 3 · öncelik: kırılım hacmi | 72 USDT | %-29 | %+1 | %43 | 57 USDT | 155 / 1034 | 14 | %13 |

## Seçilen kurgu (eğitim döneminde getiri / düşüş oranı en iyi, %2 risk)
**%2 risk · en fazla 3 pozisyon · öncelik: 24s hacim**
- Eğitim döneminde (tek başına, 100 USDT'den): %+92 getiri, en büyük düşüş %17
- Tüm yıl: 100 → **165 USDT**, eğitim %+87, doğrulama %-12, en büyük düşüş %17, en düşük bakiye 88 USDT, 87 işlem (haftada ~1.7), en uzun kayıp serisi 9
- Aylık getiri: 2025-10 %-6 · 2025-11 %+17 · 2025-12 %+4 · 2026-01 %-5 · 2026-02 %+5 · 2026-03 %-5 · 2026-04 %+9 · 2026-05 %+34 · 2026-06 %+11 · 2026-07 %-7 · 2026-08 %+1 · 2026-09 %+13 · 2026-10 %-12
- Artı kapanan ay: 8/13
- **Kötü şans simülasyonu** (gerçek işlemlerden rastgele seçilmiş 2.000 farklı yıl): yıl sonu bakiye en kötü %5'te 87 USDT, ortada 168, en iyi %5'te 343. En büyük düşüş ortada %23, en kötü %5'te %40. Bakiyenin yıl içinde inebileceği en düşük seviye (en kötü %5): 68 USDT. Yılı zararla kapatma ihtimali: %10

İlk 5 aday (eğitim skoruna göre):
- %2 risk · en fazla 3 pozisyon · öncelik: 24s hacim: eğitim skoru 5.29 · yıl sonu 165 USDT · doğrulama %-12 · düşüş %17
- %2 risk · en fazla 5 pozisyon · öncelik: 24s hacim: eğitim skoru 3.82 · yıl sonu 195 USDT · doğrulama %-0 · düşüş %28
- %2 risk · en fazla 8 pozisyon · öncelik: kırılım hacmi: eğitim skoru 2.33 · yıl sonu 148 USDT · doğrulama %+0 · düşüş %40
- %2 risk · en fazla 8 pozisyon · öncelik: 24s hacim: eğitim skoru 2.17 · yıl sonu 196 USDT · doğrulama %+11 · düşüş %38
- %2 risk · en fazla 5 pozisyon · aynı yönde en fazla 3 · öncelik: 24s hacim · toplam açık risk ≤ %8: eğitim skoru 1.93 · yıl sonu 107 USDT · doğrulama %-25 · düşüş %32

Süre: 0 dk
