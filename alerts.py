import requests
import os
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ALERT_FILE = "sent_alerts.json"

# ---------------------- LOAD ALERT MEMORY ----------------------

# Each coin will store: {"50": bool, "80": bool, "100": bool}
if os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, "r") as f:
        sent_alerts = json.load(f)
else:
    sent_alerts = {}

def save_alerts():
    with open(ALERT_FILE, "w") as f:
        json.dump(sent_alerts, f)

# ---------------------- TELEGRAM ----------------------

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ---------------------- CHECK THRESHOLDS ----------------------

THRESHOLDS = [50, 80, 100]

def check_thresholds(symbol, change):
    # Create entry if not exists
    if symbol not in sent_alerts:
        sent_alerts[symbol] = {"50": False, "80": False, "100": False}

    for threshold in THRESHOLDS:
        key = str(threshold)

        # If coin crosses threshold and alert wasn't sent
        if change >= threshold and not sent_alerts[symbol][key]:
            send_telegram(f"🚀 {symbol} günlük %{change:.2f} yükseldi! (>{threshold}%)")
            sent_alerts[symbol][key] = True

    save_alerts()

# ---------------------- BINANCE FUTURES ----------------------

def check_binance():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    r = requests.get(url).json()

    for coin in r:
        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue

        change = float(coin.get("priceChangePercent", 0))

        if change >= 50:
            check_thresholds(symbol, change)

# ---------------------- MEXC FUTURES ----------------------

def check_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    r = requests.get(url).json()

    if r.get("success") != True:
        return

    for coin in r.get("data", []):
        symbol = coin.get("symbol", "")
        if not symbol.endswith("_USDT"):
            continue

        # Convert symbol to match Binance style: BTC_USDT → BTCUSDT
        symbol = symbol.replace("_", "")

        change = float(coin.get("riseFallRate", 0))

        if change >= 50:
            check_thresholds(symbol, change)

# ---------------------- MAIN ----------------------

def main():
    send_telegram("🔎 Pump radar çalıştı (Binance + MEXC).")
    check_binance()
    check_mexc()

if __name__ == "__main__":
    main()
