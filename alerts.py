import requests
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    requests.post(url, data=data)

# EŞİKLER
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98)
]

def check_thresholds(symbol, change):
    print(f"CHECK: {symbol} --> {change}")
    for display_treshold, api_threshold in THRESHOLDS:
        if change >= api_threshold:
            send_telegram(
                f"🚀 {symbol} günlük %{change:.2f} yükseldi! (>{display_treshold}%)"
            )

# ------------------ BINANCE ------------------

def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        data = requests.get(url, timeout=5).json()
        print("BINANCE RAW DATA:")
        print(data[:5])   # ilk 5 coin göster
        return data
    except Exception as e:
        print("BINANCE ERROR:", e)
        return []

def check_binance():
    data = fetch_binance()

    for coin in data:
        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")
        change_raw = coin.get("priceChangePercent", 0)

        print(f"-> COIN: {symbol} CHANGE RAW = {change_raw}")

        if not symbol.endswith("USDT"):
            continue

        try:
            change = float(change_raw)
        except:
            print("FLOAT ERROR:", change_raw)
            continue

        if change >= 48:
            print(f"MATCH: {symbol} >= 48")
            time.sleep(2)

            final_data = fetch_binance()
            match = next((c for c in final_data if c.get("symbol") == symbol), None)

            if match:
                final_change = float(match.get("priceChangePercent", 0))
                print(f"FINAL: {symbol} = {final_change}")

                if final_change >= 48:
                    check_thresholds(symbol, final_change)
