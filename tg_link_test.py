"""Telegram'a farklı TradingView bağlantı biçimlerini içeren bir deneme mesajı gönderir (bot ayarlarına dokunmaz)."""
import os, requests
v = [
    ("1", "https://www.tradingview.com/chart/?symbol=OKX%3ABTCUSDT.P&amp;interval=15", "www · chart (şu anki)"),
    ("2", "https://tr.tradingview.com/chart/?symbol=OKX%3ABTCUSDT.P&amp;interval=15", "tr · chart"),
    ("3", "https://www.tradingview.com/symbols/OKX-BTCUSDT.P/", "www · sembol sayfası"),
    ("4", "https://tr.tradingview.com/symbols/OKX-BTCUSDT.P/", "tr · sembol sayfası"),
    ("5", "https://tr.tradingview.com/chart/?symbol=OKX:BTCUSDT.P", "tr · chart (sade)"),
]
lines = ["🔗 Bağlantı denemesi: hangisi TradingView uygulamasını açıyor?", ""]
lines += [f'{n}) <a href="{u}">BTC</a>  — {d}' for n, u, d in v]
r = requests.post(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
                  data={"chat_id": os.environ["TG_CHAT_ID"], "text": "\n".join(lines),
                        "parse_mode": "HTML", "disable_web_page_preview": "true"}, timeout=10)
print("::notice::Telegram yanıtı: " + str(r.status_code))
