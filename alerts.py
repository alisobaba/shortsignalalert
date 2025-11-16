import requests
import os
import json
import time

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

# Tolerans eklendi → %49.5, %79.5, %99.5
THRESHOLDS = [49.5, 79.5, 99.5]

def check_thresholds(symbol, change):
    if symbol not in sent_alerts:
        sent_alerts[symbol] = {"50": False, "80": False, "100": False}

    # threshold key mapping
    mapping = {49.5: "50", 79.5: "80", 99.5: "100"}

    for threshold in THRESHOLDS:
        key = mapping[threshold]

        if change >= threshold and not sent_alerts[symbol][key]:
            send_telegram(f"🚀 {symbol} günlük %{change:.2f} yükseldi! (>{key}%)")
            sent_alerts[symbol][key] = True

    save_alerts()

# ---------------------- BINANCE FUTURES ----------------------

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

        if change >= 49.5:
            # Binance API gecikmesi için ikinci kontrol
            time.sleep(3)
            data2 = fetch_binance()
            match = next((c for c in data2 if c.get("symbol") == symbol), None)

            if match:
                final_change = float(match.get("priceChangePercent", 0))
                if final_change >= 49.5:
                    check_thresholds(symbol, final_change)

# ---------------------- MEXC FUTURES ----------------------

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

        if change >= 49.5:
            time.sleep(3)
            r2 = fetch_mexc()

            if r2.get("success") != True:
                continue

            match = next((c for c in r2.get("data", []) if c.get("symbol") == coin.get("symbol")), None)

            if match:
                final_change = float(match.get("riseFallRate", 0))
                if final_change >= 49.5:
                    check_thresholds(symbol, final_change)

# ---------------------- MAIN ----------------------

def main():
    send_telegram("🔎 Pump radar çalıştı (Binance + MEXC).")
    check_binance()
    check_mexc()

if __name__ == "__main__":
    main()
