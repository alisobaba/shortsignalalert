import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MEXC_URL = "https://contract.mexc.com/api/v1/contract/ticker"

# ---------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------

def send_telegram(text: str):
    """Düz, formatlanmamış metin gönder (en sorunsuz mod)."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        # Telegram'a bile log basamazsak yapacak bir şey yok
        print("Telegram error:", e)

# ---------------------------------------------------------------------
# MEXC
# ---------------------------------------------------------------------

def fetch_mexc_tickers():
    """MEXC futures ticker listesini çeker. Hata olursa [] döner."""
    try:
        resp = requests.get(MEXC_URL, timeout=10)
        data = resp.json()
    except Exception as e:
        send_telegram(f"DEBUG: MEXC isteği hata verdi: {e}")
        return []

    if not data.get("success"):
        send_telegram(f"DEBUG: MEXC success=False, raw={str(data)[:200]}")
        return []

    tickers = data.get("data", [])
    return tickers

# ---------------------------------------------------------------------
# ALARM LOGİĞİ
# ---------------------------------------------------------------------

# Eşikler – spam filan yok, her çalıştırmada yeniden bakıyoruz.
LEVELS = [
    (100, "💥 100%+ SERT PUMP"),
    (80,  "🔥 80%+ GÜÇLÜ PUMP"),
    (50,  "⚡ 50%+ PUMP"),
]

def check_mexc():
    tickers = fetch_mexc_tickers()

    # DEBUG 1: Kaç tane ürün geldi?
    send_telegram(f"DEBUG: MEXC'ten gelen enstrüman sayısı: {len(tickers)}")

    if not tickers:
        return

    # Sadece *_USDT kontratlarını al, değişime göre sırala (en çok yükselen en başta)
    cleaned = []
    for c in tickers:
        sym = c.get("symbol", "")
        if not sym.endswith("_USDT"):
            continue
        try:
            change = float(c.get("riseFallRate", 0))
        except Exception:
            continue
        cleaned.append((sym, change, c))

    if not cleaned:
        send_telegram("DEBUG: *_USDT kontratı bulunamadı.")
        return

    cleaned.sort(key=lambda x: x[1], reverse=True)

    # DEBUG 2: En çok yükselen ilk 5 coin
    top_lines = ["DEBUG: MEXC Top 5 (riseFallRate):"]
    for sym, chg, _raw in cleaned[:5]:
        top_lines.append(f"- {sym}: %{chg:.2f}")
    send_telegram("\n".join(top_lines))

    # ALARM: %50 / 80 / 100 üzerindekiler
    for sym, chg, raw in cleaned:
        # sıfırın altındaki dump'larla uğraşmıyoruz şu an
        if chg < 50:
            break  # liste büyükten küçüğe, devamında zaten daha küçüktür

        level_text = None
        for level, text in LEVELS:
            if chg >= level:
                level_text = text
                break

        if level_text:
            send_telegram(
                f"{level_text}\n"
                f"🎯 Sembol: {sym}\n"
                f"📈 24h Değişim: %{chg:.2f}"
            )

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    send_telegram("🛰 MEXC pump radarı çalıştı.")
    check_mexc()

if __name__ == "__main__":
    main()
