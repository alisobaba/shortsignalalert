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
        "parse_mode": ""
    }
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

# ============================================================
#                    EŞİK LİSTESİ (%)
# ============================================================

# Görünen %   –   API kontrol eşiği
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98),
]

def check_thresholds(symbol, price, change):
    for display, api in THRESHOLDS:
        if change >= api:
            send_telegram(
                f"🚀 {symbol}\n"
                f"📈 Fiyat: {price}\n"
                f"🔥 24h Değişim: %{change:.2f}\n"
                f"(>{display}% eşiği aşıldı!)"
            )
            print(f"[ALERT] {symbol} %{change:.2f} gönderildi")


# ============================================================
#                       MEXC API
# ============================================================

def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        r = requests.get(url, timeout=5).json()
        if r.get("success") is True:
            return r.get("data", [])
        return []
    except:
        return []

def check_mexc():
    print("==== MEXC KONTROL BAŞLADI ====")
    data = fetch_mexc()

    for coin in data:
        raw_symbol = coin.get("symbol", "")
        if not raw_symbol.endswith("_USDT"):
            continue

        symbol = raw_symbol.replace("_", "")
        price = coin.get("lastPrice", 0)
        change = float(coin.get("riseFallRate", 0))

        # Eşik denenir
        if change >= 48:
            print(f"[CHECK-1] {symbol} %{change}")

            # İkinci doğrulama
            time.sleep(2)
            data2 = fetch_mexc()
            match = next((c for c in data2 if c.get("symbol") == raw_symbol), None)

            if match:
                final_change = float(match.get("riseFallRate", 0))
                final_price = match.get("lastPrice", price)

                if final_change >= 48:
                    print(f"[CHECK-2] {symbol} %{final_change} doğrulandı")
                    check_thresholds(symbol, final_price, final_change)

    print("==== MEXC KONTROL BİTTİ ====")


# ============================================================
#                       MAIN
# ============================================================

def main():
    check_mexc()

if __name__ == "__main__":
    main()
