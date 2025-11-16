import requests
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    print("[TELEGRAM] Sending:", msg, flush=True)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": ""
    }
    requests.post(url, data=data)


# ------------------ EŞİKLER ------------------
THRESHOLDS = [
    (50, 48),
    (75, 73),
    (100, 98)
]

def check_thresholds(symbol, change):
    print(f"[CHECK_THRESHOLDS] {symbol} → %{change}", flush=True)

    for display, real in THRESHOLDS:
        if change >= real:
            msg = f"🚀 COIN: {symbol}\n24h Değişim: %{change:.2f}\nEşik: >{display}%"
            send_telegram(msg)


# ------------------ BINANCE ------------------

def fetch_binance():
    print("[FETCH] Binance verisi alınıyor...", flush=True)
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        data = requests.get(url, timeout=5).json()
        print("[BINANCE RAW SAMPLE]", str(data[:3]), flush=True)
        return data
    except Exception as e:
        print("[BINANCE ERROR]", e, flush=True)
        return []


def check_binance():
    data = fetch_binance()

    for coin in data:
        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")

        # sadece USDT perpetual
        if not symbol.endswith("USDT"):
            continue

        change = float(coin.get("priceChangePercent", 0))

        print(f"[BINANCE] {symbol}: %{change}", flush=True)

        # Eğer %48 üstü ise → teyit
        if change >= 48:
            print(f"[BINANCE] {symbol} teyit ediliyor...", flush=True)
            time.sleep(2)

            final_data = fetch_binance()
            match = next((c for c in final_data if c.get("symbol") == symbol), None)

            if match:
                final_change = float(match.get("priceChangePercent", 0))
                print(f"[BINANCE CONFIRMED] {symbol}: %{final_change}", flush=True)

                if final_change >= 48:
                    check_thresholds(symbol, final_change)



# ------------------ MAIN ------------------

def main():
    print("==== SCRIPT BAŞLADI ====", flush=True)
    print("TOKEN OK:", TELEGRAM_TOKEN is not None, flush=True)
    print("CHAT OK:", CHAT_ID is not None, flush=True)

    check_binance()

    print("==== BİTTİ ====", flush=True)


if __name__ == "__main__":
    main()
