# Final kurgu — risk oranı karşılaştırması
Kurgu: 03:00 kapanışında limit giriş, günlük stop 10 gün dibi, BTC filtresiz, 100 USDT başlangıç, bileşik, 2 yıl. Bootstrap: aynı işlemlerden rastgele kurulmuş 2.000 farklı 2 yıl (portföy kısıtı olmadan, işlem başı risk aynı).

| Risk × en fazla pozisyon | Aynı anda en fazla açık risk | Düşüşte risk yarıya | Son bakiye | Eğitim / doğrulama getiri | En büyük düşüş | En düşük bakiye | Acil fren | Bootstrap: kötü %5 / orta / iyi %5 | Bootstrap: düşüş orta / kötü %5 | Zararla bitirme ihtimali |
|---|---|---|---|---|---|---|---|---|---|---|
| %1 × 6 | %6 | hayır | 179 USDT | %+30 / %+38 | %35 | 81 USDT | hayır | 89 / 216 / 572 | %28 / %46 | %8 |
| %1 × 6 | %6 | evet | 145 USDT | %+16 / %+25 | %26 | 85 USDT | hayır | 89 / 216 / 572 | %28 / %46 | %8 |
| %1 × 8 | %8 | hayır | 190 USDT | %+32 / %+44 | %39 | 73 USDT | hayır | 102 / 265 / 746 | %29 / %47 | %4 |
| %1 × 8 | %8 | evet | 133 USDT | %+13 / %+18 | %28 | 74 USDT | hayır | 102 / 265 / 746 | %29 / %47 | %4 |
| %1.5 × 6 | %9 | hayır | 195 USDT | %+34 / %+46 | %49 | 71 USDT | hayır | 78 / 285 / 1183 | %40 / %61 | %10 |
| %1.5 × 6 | %9 | evet | 137 USDT | %+15 / %+19 | %33 | 72 USDT | hayır | 78 / 285 / 1183 | %40 / %61 | %10 |
| %2 × 4 | %8 | hayır | 121 USDT | %+1 / %+20 | %54 | 69 USDT | hayır | 38 / 144 / 609 | %49 / %74 | %34 |
| %2 × 4 | %8 | evet | 109 USDT | %-4 / %+12 | %38 | 72 USDT | hayır | 38 / 144 / 609 | %49 / %74 | %34 |
| %2 × 6 | %12 | hayır | 195 USDT | %+31 / %+49 | %60 | 61 USDT | hayır | 66 / 355 / 2258 | %50 / %72 | %11 |
| %2 × 6 | %12 | evet | 150 USDT | %+22 / %+23 | %39 | 67 USDT | hayır | 66 / 355 / 2258 | %50 / %72 | %11 |
| %2 × 8 | %16 | hayır | 162 USDT | %+4 / %+56 | %64 | 57 USDT | ÇALIŞTI | 54 / 331 / 2441 | %54 / %78 | %14 |
| %2 × 8 | %16 | evet | 179 USDT | %+35 / %+33 | %42 | 61 USDT | hayır | 82 / 508 / 3673 | %51 / %74 | %7 |
| %3 × 6 | %18 | hayır | 53 USDT | %-47 / %+0 | %53 | 52 USDT | ÇALIŞTI | 31 / 64 / 157 | %52 / %72 | %81 |
| %3 × 6 | %18 | evet | 58 USDT | %-42 / %+0 | %43 | 57 USDT | ÇALIŞTI | 26 / 56 / 132 | %57 / %76 | %86 |

Süre: 1 dk
