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
        "parse_mode": ""  # güvenli mod
    }
    requests.post(url, data=data)


# ------------------ EŞİKLER ------------------
# Gösterilecek değer – API tetik eşiği
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98)
]


def check_thresholds(symbol, change):
    """
    Coin eşikleri geçince telegram uyarı yollar
    """
    for display_threshold, api_threshold in THRESHOLDS:
        if change >= api_threshold:
            msg = (
                f"🚀 MEXC Futures Pump Alert!\n"
                f"Coin: {symbol}\n"
                f"Yükseliş: %{change:.2f}\n"
                f"Eşik: >{display_threshold}%"
            )
            send_telegram(msg)


# ------------------ MEXC FUTURES ------------------

def fetch_mexc():
    """
    MEXC Futures tüm coin listesini çeker
    """
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return {"success": False, "data": []}


def check_mexc():
    """
    MEXC Pump Radar
    """
    r = fetch_mexc()
    if r.get("success") != True:
        print("[MEXC ERROR] Response hatalı:", r)
        return

    for coin in r.get("data", []):
        try:
            raw_symbol = coin.get("symbol", "")  # örn: BTC_USDT
            if not raw_symbol.endswith("_USDT"):
                continue

            # Sembol formatı dönüşümü: BTC_USDT → BTCUSDT
            symbol = raw_symbol.replace("_", "")

            change = float(coin.get("riseFallRate", 0))

            # %48 geçtiyse ekstra doğrulama
            if change >= 48:
                time.sleep(1)
                r2 = fetch_mexc()
                if r2.get("success") != True:
                    continue

                match = next((c for c in r2.get("data", [])
                              if c.get("symbol") == raw_symbol), None)

                if match:
                    final_change = float(match.get("riseFallRate", 0))
                    if final_change >= 48:
                        check_thresholds(symbol, final_change)

        except Exception as e:
            print("[MEXC ERROR]", e)


# ------------------ MAIN ------------------

def main():
    print("==== MEXC PUMP RADAR BAŞLADI ====")
    check_mexc()
    print("==== BİTTİ ====")


if __name__ == "__main__":
    main()
