import requests
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": ""  # format kapalı
    }
    requests.post(url, data=data)

# ------------------ EŞİKLER ------------------
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98)
]

def check_thresholds(symbol, change):
    for display_treshold, api_threshold in THRESHOLDS:
        if change >= api_threshold:
            send_telegram(
                f"🚀 {symbol} günlük %{change:.2f} yükseldi! (>{display_treshold}%)"
            )

# ------------------ BINANCE FUTURES ------------------

def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return []

def check_binance():
    data = fetch_binance()

    for coin in data:
        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")

        # SADECE USDT içeren FUTURES coinler
        if "USDT" not in symbol:
            continue

        change = float(coin.get("priceChangePercent", 0))

        # Ön alarm
        if change >= 48:
            time.sleep(2)
            final_data = fetch_binance()
            match = next((c for c in final_data if c.get("symbol") == symbol), None)

            if match:
                final_change = float(match.get("priceChangePercent", 0))
                if final_change >= 48:
                    check_thresholds(symbol, final_change)

# ------------------ MEXC FUTURES ------------------

def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return {"success": False, "data": []}

def check_mexc():
    r = fetch_mexc()
    if r.get("success") != True:
        return

    for coin in r.get("data", []):
        symbol = coin.get("symbol", "")

        if "USDT" not in symbol:
            continue

        symbol = symbol.replace("_", "")
        change = float(coin.get("riseFallRate", 0))

        if change >= 48:
            time.sleep(2)
            r2 = fetch_mexc()
            if r2.get("success") != True:
                continue

            match = next((c for c in r2.get("data", []) if c.get("symbol") == coin.get("symbol")), None)
            if match:
                final_change = float(match.get("riseFallRate", 0))
                if final_change >= 48:
                    check_thresholds(symbol, final_change)

# ------------------ MAIN ------------------

def main():
    check_binance()
    check_mexc()


if __name__ == "__main__":
    main()
