"""Final kurgu için risk oranı karşılaştırması (mesaj göndermez). Çıktı: final_risk.md"""
import sys
import time
import pa_final as F

OUT = "final_risk.md"
lines = []


def out(t=""):
    print(t, flush=True)
    lines.append(t)


def main():
    T0 = time.time()
    data, created = F.T.load()
    t0 = created - F.DAYS * 86400
    t_split = created - F.TEST_DAYS * 86400
    coins = {(k, 0): F.Coin(k, v, 0) for k, v in data.items()}
    btc = F.Btc(coins[("BTC-USDT-SWAP", 0)])
    evs = []
    for c in coins.values():
        evs += F.events(c, btc)
    rs = F.trades_for(coins, evs, 0, "don10", False)
    out("# Final kurgu — risk oranı karşılaştırması")
    out("Kurgu: 03:00 kapanışında limit giriş, günlük stop 10 gün dibi, BTC filtresiz, 100 USDT başlangıç, bileşik, 2 yıl. "
        "Bootstrap: aynı işlemlerden rastgele kurulmuş 2.000 farklı 2 yıl (portföy kısıtı olmadan, işlem başı risk aynı).")
    out()
    out("| Risk × en fazla pozisyon | Aynı anda en fazla açık risk | Düşüşte risk yarıya | Son bakiye | Eğitim / doğrulama getiri | "
        "En büyük düşüş | En düşük bakiye | Acil fren | Bootstrap: kötü %5 / orta / iyi %5 | Bootstrap: düşüş orta / kötü %5 | "
        "Zararla bitirme ihtimali |")
    out("|---|---|---|---|---|---|---|---|---|---|---|")
    for risk, maxn in ((1.0, 6), (1.0, 8), (1.5, 6), (2.0, 4), (2.0, 6), (2.0, 8), (3.0, 6)):
        for dd in (False, True):
            s = F.portfolio(rs, risk, maxn, t0, t_split, dd)
            b = F.bootstrap([r["net"] for r in s["alinan"]], risk)
            out(f"| %{risk:g} × {maxn} | %{risk * maxn:g} | {'evet' if dd else 'hayır'} | {s['son']:.0f} USDT | "
                f"%{s['egit']:+.0f} / %{s['dogr']:+.0f} | %{s['mdd']:.0f} | {s['low']:.0f} USDT | "
                f"{'ÇALIŞTI' if s['killed'] else 'hayır'} | {b['s5']:.0f} / {b['s50']:.0f} / {b['s95']:.0f} | "
                f"%{b['m50']:.0f} / %{b['m95']:.0f} | %{b['kayip']:.0f} |")
    out(f"\nSüre: {(time.time() - T0) / 60:.0f} dk")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        out(f"HATA: {e}")
        sys.exit(1)
    finally:
        with open(OUT, "w") as f:
            f.write("\n".join(lines) + "\n")
