import requests
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# EŞİKLER (UI–API farkı için toleranslı)
THRESHOLDS = [45, 75, 95]

def check_thresholds(symbol, change):
    for threshold in THRESHOLDS:
        if change >= threshold:
            send_telegram(f"🚀 {symbol} günlük %{change:.2f} yükseldi! (>{threshold}%)")

# ------------------ BINANCE ------------------

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
        if not symbol.endswith("USDT"):
            continue

        change = float(coin.get("priceChangePercent", 0))

        if change >= 45:
            time.sleep(2)
            final_data = fetch_binance()
            match = next((c for c in final_data if c.get("symbol") == symbol), None)

            if match:
                final_change = float(match.get("priceChangePercent", 0))
                if final_change >= 45:
                    check_thresholds(symbol, final_change)

# ------------------ MEXC ------------------

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
        if not symbol.endswith("_USDT"):
            continue

        symbol = symbol.replace("_", "")
        change = float(coin.get("riseFallRate", 0))

        if change >= 45:
            time.sleep(2)
            r2 = fetch_mexc()
            if r2.get("success") != True:
                continue

            match = next((c for c in r2.get("data", []) if c.get("symbol") == coin.get("symbol")), None)
            if match:
                final_change = float(match.get("riseFallRate", 0))
                if final_change >= 45:
                    check_thresholds(symbol, final_change)

# ------------------ MAIN ------------------

def main():
    send_telegram("🔎 Pump radar çalıştı (Binance + MEXC).")
    check_binance()
    check_mexc()

if __name__ == "__main__":
    main()
