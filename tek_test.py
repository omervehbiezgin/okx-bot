import os, requests
url = "https://tr.tradingview.com/symbols/BTCUSDT.P/?exchange=OKX"
r = requests.post(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
                  data={"chat_id": os.environ["TG_CHAT_ID"],
                        "text": f'🔗 Örnek bağlantı testi (borsa: OKX): <a href="{url}">BTC</a>',
                        "parse_mode": "HTML", "disable_web_page_preview": "true"}, timeout=10)
print("::notice::Telegram yanıtı: " + str(r.status_code))
