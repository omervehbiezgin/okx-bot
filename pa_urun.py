"""
Ürün listesi kontrolü: OKX gerçek ve demo SWAP listeleri, kontrat kategorileri, hacme göre ilk 150 kontratın hangisinin
demoda olduğu. Mesaj göndermez, emir vermez. Çıktı: urun_sonuc.md
"""
import requests

import pa_scan_once as p

BASE = "https://www.okx.com"


def get(path, params, demo=False):
    h = {"x-simulated-trading": "1"} if demo else {}
    r = requests.get(BASE + path, params=params, headers=h, timeout=20)
    r.raise_for_status()
    return r.json()["data"]


live = get("/api/v5/public/instruments", {"instType": "SWAP"})
demo = get("/api/v5/public/instruments", {"instType": "SWAP"}, demo=True)
tick = get("/api/v5/market/tickers", {"instType": "SWAP"})
kat = {d["instId"]: str(d.get("instCategory", "")) for d in live}
demo_ids = {d["instId"] for d in demo if d.get("state", "live") == "live"}
vol = {}
for t in tick:
    try:
        vol[t["instId"]] = float(t["volCcy24h"]) * float(t["last"])
    except (KeyError, ValueError):
        pass

L = ["# OKX ürün listesi kontrolü", ""]
usdt = [i for i in kat if i.endswith("-USDT-SWAP")]
cnt = {}
for i in usdt:
    cnt[kat[i]] = cnt.get(kat[i], 0) + 1
L.append(f"Gerçek hesap USDT perpetual: {len(usdt)} · demo: {len([i for i in demo_ids if i.endswith('-USDT-SWAP')])}")
L.append(f"Kategori sayıları (instCategory): {cnt}")
L.append("")
for c in sorted(cnt):
    ex = sorted((i for i in usdt if kat[i] == c), key=lambda i: -vol.get(i, 0))[:25]
    L.append(f"- Kategori '{c}': " + " ".join(i.replace("-USDT-SWAP", "") for i in ex))
L.append("")
L.append("## Hacme göre ilk 150 USDT perpetual (24s hacim ≥ 5M)")
L.append("| # | Kontrat | Kategori | 24s hacim (M USDT) | Demoda |")
L.append("|---|---|---|---|---|")
rows = sorted((i for i in usdt if vol.get(i, 0) >= p.MIN_24H_USDT), key=lambda i: -vol[i])[:150]
for n, i in enumerate(rows, 1):
    L.append(f"| {n} | {i.replace('-USDT-SWAP', '')} | {kat[i]} | {vol[i] / 1e6:.0f} | {'✅' if i in demo_ids else '—'} |")
sel = p.get_symbols()
L.append("")
L.append(f"## Botun bugünkü filtresiyle seçilen ilk {len(sel)} (gerçek hesap)")
L.append(" ".join(i.replace("-USDT-SWAP", "") for i in sel))
ins = [i for i in sel if i in demo_ids]
L.append(f"\nBunlardan demoda olan: {len(ins)}; demoda olmayan: "
         + " ".join(i.replace("-USDT-SWAP", "") for i in sel if i not in demo_ids))
open("urun_sonuc.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
