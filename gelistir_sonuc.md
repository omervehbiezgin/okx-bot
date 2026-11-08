# Trend stratejisi — geliştirme testi
50 coin, 1646 işlem. Eğitim 08.11.2024 – 08.03.2026, doğrulama son 245 gün (veri 08.11.2026 tarihine kadar). Seçim sadece eğitime göre (getiri ÷ en büyük düşüş). 100 USDT başlangıç, bileşik, acil fren 60 USDT. Kurallar botla aynı.

## 1) 8 yer dolunca öncelik (8 yer × %1)
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| 24s hacim (bugünkü bot) | 1.61 | 254 | +62% / +57% | %40 | 481 / 935 |
| kırılım hacmi oranı | 2.94 | 328 | +108% / +57% | %41 | 478 / 938 |
| kırılım mumu boyu | 2.47 | 303 | +96% / +55% | %40 | 466 / 950 |
| hacim oranı + mum boyu | 2.57 | 281 | +102% / +39% | %41 | 472 / 943 |
| rastgele sıra (30 deneme ortalaması) | 1.64 | 255 (en kötü 149, en iyi 375) | +63% / +56% | %46 | - |

Eğitimde en iyi öncelik: **kırılım hacmi oranı**. Rastgele sıranın eğitim skoru 1.64 (30 denemede 0.60–3.13).

## 2) Yer sayısı × işlem başı risk
### Öncelik: 24s hacim (bugünkü bot)
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| 6 yer × %1.33 | 1.02 | 303 | +54% / +97% | %47 | 368 / 1081 |
| 8 yer × %1.0 | 1.61 | 254 | +62% / +57% | %40 | 481 / 935 |
| 10 yer × %0.8 | 2.25 | 277 | +78% / +56% | %39 | 578 / 817 |
| 12 yer × %0.67 | 2.60 | 281 | +90% / +48% | %38 | 659 / 702 |
| 16 yer × %0.5 | 1.13 | 193 | +37% / +42% | %36 | 845 / 469 |
| 12 yer × %1.0 | 2.64 | 362 | +120% / +64% | %51 | 659 / 702 |

### Öncelik: kırılım hacmi oranı
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| 6 yer × %1.33 | 2.50 | 372 | +111% / +76% | %48 | 372 / 1078 |
| 8 yer × %1.0 | 2.94 | 328 | +108% / +57% | %41 | 478 / 938 |
| 10 yer × %0.8 | 2.38 | 265 | +85% / +43% | %39 | 586 / 801 |
| 12 yer × %0.67 | 2.23 | 253 | +77% / +43% | %37 | 674 / 687 |
| 16 yer × %0.5 | 0.82 | 172 | +25% / +38% | %38 | 847 / 472 |
| 12 yer × %1.0 | 2.22 | 316 | +101% / +57% | %51 | 674 / 687 |

## 3) Aynı yöne en fazla N pozisyon (8 yer × %1)
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| 24s hacim (bugünkü bot) · yön sınırı yok | 1.61 | 254 | +62% / +57% | %40 | 481 / 935 |
| 24s hacim (bugünkü bot) · yön sınırı 6 | 2.35 | 290 | +93% / +50% | %38 | 437 / 999 |
| 24s hacim (bugünkü bot) · yön sınırı 5 | 2.21 | 259 | +75% / +48% | %31 | 395 / 1054 |
| 24s hacim (bugünkü bot) · yön sınırı 4 | 2.33 | 242 | +64% / +48% | %26 | 344 / 1129 |
| kırılım hacmi oranı · yön sınırı yok | 2.94 | 328 | +108% / +57% | %41 | 478 / 938 |
| kırılım hacmi oranı · yön sınırı 6 | 1.98 | 272 | +67% / +62% | %40 | 435 / 1004 |
| kırılım hacmi oranı · yön sınırı 5 | 1.49 | 269 | +44% / +87% | %37 | 393 / 1058 |
| kırılım hacmi oranı · yön sınırı 4 | 1.26 | 240 | +36% / +76% | %33 | 346 / 1124 |

## 4) Eğitime göre en iyi birleşim (tüm ızgara)
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| kırılım hacmi oranı · 8×%1.0 · yön sınırı yok | 2.94 | 328 | +108% / +57% | %41 | 478 / 938 |
| 24s hacim (bugünkü bot) · 6×%1.33 · yön sınırı 3 | 2.91 | 345 | +90% / +81% | %29 | 268 / 1227 |
| 24s hacim (bugünkü bot) · 10×%0.8 · yön sınırı 8 | 2.62 | 261 | +84% / +42% | %36 | 535 / 867 |
| 24s hacim (bugünkü bot) · 12×%0.67 · yön sınırı yok | 2.60 | 281 | +90% / +48% | %38 | 659 / 702 |
| hacim oranı + mum boyu · 8×%1.0 · yön sınırı yok | 2.57 | 281 | +102% / +39% | %41 | 472 / 943 |
| kırılım hacmi oranı · 6×%1.33 · yön sınırı yok | 2.50 | 372 | +111% / +76% | %48 | 372 / 1078 |
| kırılım mumu boyu · 8×%1.0 · yön sınırı yok | 2.47 | 303 | +96% / +55% | %40 | 466 / 950 |
| 24s hacim (bugünkü bot) · 10×%0.8 · yön sınırı 7 | 2.40 | 272 | +78% / +53% | %33 | 497 / 918 |

**Bugünkü bot (karşılaştırma):**
| Ayar | Eğitim skoru | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | Alınan / atlanan |
|---|---|---|---|---|---|
| 24s hacim · 8×%1 · yön sınırı yok | 1.61 | 254 | +62% / +57% | %40 | 481 / 935 |

## 5) Sağlamlık kontrolü: yön sınırı, 30 rastgele sinyal sırasında (8 yer × %1)
| Yön sınırı | Ortalama son bakiye | Ortalama en büyük düşüş | Ortalama eğitim / doğrulama getiri | Sınırsıza göre düşüşü azalttığı deneme |
|---|---|---|---|---|
| yok | 252 | %46 | +61% / +56% | - |
| 6 | 266 | %46 | +70% / +56% | 15/30 |
| 5 | 253 | %42 | +57% / +60% | 24/30 |
| 4 | 239 | %35 | +54% / +55% | 30/30 |

Not: Fonlama oranına göre filtre test edilemedi; OKX 2 yıllık fonlama geçmişi vermiyor (yaklaşık 3 ay). Testte longlara sabit fonlama maliyeti eklenmişti.

Süre: 0 dk
