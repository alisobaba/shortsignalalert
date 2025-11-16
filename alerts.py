import requests
import os
import json
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ALERT_FILE = "sent_alerts.json"

# ---------------------- LOAD MEMORY ----------------------

if os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, "r") as f:
        sent_alerts = json.load(f)
else:
    sent_alerts = {}

def save_alerts():
    with open(ALERT_FILE, "w") as f:
        json.dump(sent_alerts, f, indent=2)

# ---------------------- TELEGRAM ----------------------

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ---------------------- THRESHOLDS ----------------------

THRESHOLDS = [50, 80, 100]

def check_thresholds(symbol, change):
    if symbol not in sent_alerts:
        sent_alerts[symbol] = {"50": False, "80": False, "100": False}

    for th in THRESHOLDS:
        key = str(th)

        if change >= th and not sent_alerts[symbol][key]:
            send_telegram(
                f"🚀 MEXC Pump\n"
                f"Coin: {symbol}\n"
                f"Yükseliş: %{change:.2f}\n"
                f"Eşik: %{th}"
            )
            sent_alerts[symbol][key] = True

    save_alerts()

# ---------------------- MEXC ----------------------

def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return None

def check_mexc():
    r = fetch_mexc()

    if not r or not r.get("success"):
        send_telegram("❌ DEBUG: MEXC API başarısız.")
        return

    data = r["data"]

    send_telegram(f"DEBUG: MEXC enstrüman sayısı: {len(data)}")

    # Debug top 5 gönder
    top5 = sorted(data, key=lambda x: float(x["riseFallRate"]), reverse=True)[:5]
    dbg = "\n".join([f"- {c['symbol']}: %{float(c['riseFallRate']):.2f}" for c in top5])
    send_telegram(f"DEBUG: Top 5:\n{dbg}")

    # Pump kontrolü
    for c in data:
        symbol = c["symbol"]
        if not symbol.endswith("_USDT"):
            continue

        clean = symbol.replace("_", "")
        change = float(c["riseFallRate"])

        if change >= 50:
            check_thresholds(clean, change)

# ---------------------- MAIN ----------------------

def main():
    send_telegram("🛰 MEXC pump radar çalıştı.")
    check_mexc()

if __name__ == "__main__":
    main()
