import requests
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("DEBUG TOKEN:", TELEGRAM_TOKEN)
print("DEBUG CHAT:", CHAT_ID)

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("TELEGRAM TOKEN/CHAT ID BOŞ! MESAJ GÖNDERİLMEDİ")
        print("TOKEN:", TELEGRAM_TOKEN)
        print("CHAT:", CHAT_ID)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": ""
    }
    print("Gönderiliyor:", msg)
    requests.post(url, data=data)


# ------------------ YENİ: GERÇEK PUMP % HESABI ------------------
def calc_ui_change(open_price, last_price):
    if open_price == 0:
        return 0
    return ((last_price - open_price) / open_price) * 100


# %50 / %75 / %100
THRESHOLDS = [50, 75, 100]


def send_if_threshold(symbol, change):
    for t in THRESHOLDS:
        if change >= t:
            send_telegram(f"🚀 {symbol} +%{change:.2f} (>{t}%)")
            break


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

        if "USDT" not in symbol:
            continue

        # API yüzdesi
        api_change = float(coin.get("priceChangePercent", 0))

        # UI yüzdesi hesapla
        open_price = float(coin.get("openPrice", 0))
        last_price = float(coin.get("lastPrice", 0))
        ui_change = calc_ui_change(open_price, last_price)

        final = max(api_change, ui_change)

        if final >= 50:
            send_if_threshold(symbol, final)


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
        if "USDT" not in symbol:
            continue

        symbol = symbol.replace("_", "")

        api_change = float(coin.get("riseFallRate", 0))
        if api_change >= 50:
            send_if_threshold(symbol, api_change)


# ------------------ MAIN ------------------
def main():
    print("Çalıştı. TOKEN:", TELEGRAM_TOKEN)
    check_binance()
    check_mexc()


if __name__ == "__main__":
    main()
