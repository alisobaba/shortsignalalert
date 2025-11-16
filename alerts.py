import requests
import json
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

sent_alerts = set()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

def check_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    r = requests.get(url).json()

    for coin in r:
        symbol = coin["symbol"]
        if not symbol.endswith("USDT"):
            continue

        change = float(coin["priceChangePercent"])

        if change >= 50:
            if symbol not in sent_alerts:
                msg = f"🔥 {symbol} günlük %{change:.2f} yükseldi!"
                send_telegram(msg)
                sent_alerts.add(symbol)

def main():
    check_binance()

if __name__ == "__main__":
    main()
