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
    }
    requests.post(url, data=data)


# ------------------ EŞİKLER ------------------
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98)
]


def check_thresholds(symbol, change):
    for display_t, api_t in THRESHOLDS:
        if change >= api_t:
            msg = (
                f"🚀 MEXC Futures Pump Alert!\n"
                f"Coin: {symbol}\n"
                f"Yükseliş: %{change:.2f}\n"
                f"Eşik: >{display_t}%"
            )
            send_telegram(msg)


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
        print("[MEXC ERROR]", r)
        return

    for coin in r.get("data", []):
        try:
            raw = coin.get("symbol", "")
            if not raw.endswith("_USDT"):
                continue

            symbol = raw.replace("_", "")
            change = float(coin.get("riseFallRate", 0))

            if change >= 48:
                time.sleep(1)
                r2 = fetch_mexc()
                if r2.get("success") != True:
                    continue

                match = next((c for c in r2.get("data", [])
                              if c.get("symbol") == raw), None)

                if match:
                    final_change = float(match.get("riseFallRate", 0))
                    if final_change >= 48:
                        check_thresholds(symbol, final_change)

        except Exception as e:
            print("[MEXC ERROR]", e)


# ------------------ TEST MOD ------------------

def test_message():
    send_telegram("🧪 *TEST* — Sistem çalışıyor!")
    print("Test mesaj gönderildi.")


# ------------------ MAIN ------------------

def main():
    print("==== MEXC PUMP RADAR BAŞLADI ====")

    # İlk çalıştırmada test mesajı
    test_message()

    # Normal çalıştırma
    check_mexc()

    print("==== BİTTİ ====")


if __name__ == "__main__":
    main()
