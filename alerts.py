import requests
import os
import json
from datetime import datetime

# -------------------------------------------------
# TELEGRAM AYARLARI
# -------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Tek kullanıcı

ALERT_FILE = "sent_alerts.json"

# -------------------------------------------------
# HAFIZA (GÜNLÜK EŞİK TAKİBİ)
# -------------------------------------------------
if os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, "r") as f:
        sent_alerts = json.load(f)
else:
    sent_alerts = {}

TODAY = datetime.utcnow().date().isoformat()  # "2025-11-17" gibi


def get_symbol_state(symbol: str):
    """
    Her coin için sözlük:
    {
      "date": "2025-11-17",
      "50": bool,
      "75": bool,
      "100": bool
    }
    Tarih değiştiyse o coin için hafızayı sıfırlar.
    """
    state = sent_alerts.get(symbol)

    if not isinstance(state, dict) or state.get("date") != TODAY:
        state = {"date": TODAY, "50": False, "75": False, "100": False}
        sent_alerts[symbol] = state

    return state


def save_alerts():
    with open(ALERT_FILE, "w") as f:
        json.dump(sent_alerts, f)


# -------------------------------------------------
# TELEGRAM GÖNDERİM
# -------------------------------------------------
def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# -------------------------------------------------
# MEXC API
# -------------------------------------------------
def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/ticker"
    try:
        return requests.get(url, timeout=5).json()
    except Exception as e:
        print("MEXC error:", e)
        return {"success": False, "data": []}


# Eşikler (yazıda 50–75–100 istedin)
THRESHOLDS = [
    (50, "50"),
    (75, "75"),
    (100, "100"),
]


def check_mexc():
    r = fetch_mexc()

    if r.get("success") != True:
        print("MEXC API error:", r)
        return

    data = r.get("data", [])
    print(f"DEBUG (log): MEXC enstrüman sayısı = {len(data)}")

    changed = False  # sent_alerts.json'a yazmamız gerekip gerekmediği

    for coin in data:
        symbol = coin.get("symbol", "")
        # Sadece USDT kontratlar
        if not symbol.endswith("_USDT"):
            continue

        # Örn: LIGHT_USDT -> LIGHTUSDT
        symbol_clean = symbol.replace("_", "")

        # MEXC riseFallRate genelde % olarak geliyor (örn 71.67)
        try:
            change = float(coin.get("riseFallRate", 0))
        except (TypeError, ValueError):
            continue

        # %50 altını hiç uğraşma
        if change < 50:
            continue

        state = get_symbol_state(symbol_clean)

        for threshold_value, key in THRESHOLDS:
            if change >= threshold_value and not state[key]:
                # Bu eşiği ilk defa geçiyor → sinyal gönder
                send_telegram(
                    f"🚀 %{threshold_value}+ PUMP!\n"
                    f"📌 Coin: {symbol_clean}\n"
                    f"📈 24h Değişim: %{change:.2f}"
                )
                state[key] = True
                changed = True

    if changed:
        save_alerts()


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    check_mexc()


if __name__ == "__main__":
    main()
