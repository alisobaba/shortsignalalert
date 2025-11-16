import requests
import os
import json
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_ID", "").split(",")

ALERT_FILE = "sent_alerts.json"

# Hafıza
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

    for cid in CHAT_IDS:
        cid = cid.strip()
        if not cid:
            continue
        requests.post(url, data={"chat_id": cid, "text": msg})

# ---------------------- MEXC ----------------------
def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return {"success": False, "data": []}

# Eşikler
THRESHOLDS = {50: "50", 80: "80", 100: "100"}

def check_mexc():
    r = fetch_mexc()

    if r.get("success") != True:
        return

    data = r.get("data", [])
    
    # DEBUG: Kaç coin geldi?
    send_telegram(f"DEBUG: MEXC veri OK. Enstrüman sayısı: {len(data)}")

    for coin in data:
        symbol = coin.get("symbol", "")

        if not symbol.endswith("_USDT"):
            continue

        symbol_clean = symbol.replace("_", "")
        change = float(coin.get("riseFallRate", 0))

        # Sadece %50 üstü takip edilecek
        if change < 50:
            continue

        # Threshold memory yoksa oluştur
        if symbol_clean not in sent_alerts:
            sent_alerts[symbol_clean] = {"50": False, "80": False, "100": False}

        # Anlık doğru ölçüm için 2. kontrol
        time.sleep(1)
        r2 = fetch_mexc()
        if r2.get("success") != True:
            continue

        match = next((x for x in r2["data"] if x.get("symbol") == symbol), None)
        if not match:
            continue

        final_change = float(match.get("riseFallRate", 0))

        # Eşik tetikleme
        for threshold in [50, 80, 100]:
            key = THRESHOLDS[threshold]

            if final_change >= threshold and not sent_alerts[symbol_clean][key]:

                send_telegram(
                    f"🔥 %{threshold}+ PUMP\n"
                    f"🚀 Coin: {symbol_clean}\n"
                    f"📈 24h Değişim: %{final_change:.2f}"
                )

                sent_alerts[symbol_clean][key] = True
                save_alerts()

# ---------------------- MAIN ----------------------
def main():
    check_mexc()

if __name__ == "__main__":
    main()
