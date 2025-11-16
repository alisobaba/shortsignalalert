import requests
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

def check_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    r = requests.get(url).json()

    for coin in r:
        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")
        change = float(coin.get("priceChangePercent", 0))

        if symbol.endswith("USDT") and change >= 50:
            send_telegram(f"🔥 {symbol} bugün %{change:.2f} yükseldi!")

def main():
    # Test mesajı → Telegram'a düşecek
    send_telegram("🚀 TEST: GitHub Actions çalışıyor!")
    check_binance()

if __name__ == "__main__":
    main()
