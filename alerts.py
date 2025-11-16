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

    return data.get("data", [])

# ---------------------------------------------------------------------
# ALARM LOGİĞİ
# ---------------------------------------------------------------------

# Eşikler (yüzde olarak)
THRESHOLDS = [50, 80, 100]

def check_mexc():
    tickers = fetch_mexc_tickers()

    # DEBUG 1: Kaç tane ürün geldi?
    send_telegram(f"DEBUG: MEXC'ten gelen enstrüman sayısı: {len(tickers)}")

    if not tickers:
        return

    cleaned = []
    for c in tickers:
        sym = c.get("symbol", "")
        if not sym.endswith("_USDT"):
            continue

        try:
            rate = float(c.get("riseFallRate", 0.0))
        except Exception:
            continue

        # MEXC 'rate' genelde 0.72 => %72 gibi. %'ye çevir:
        pct = rate * 100.0
        cleaned.append((sym, pct))

    if not cleaned:
        send_telegram("DEBUG: *_USDT kontratı bulunamadı.")
        return

    # En çok yükselenden az yükselene
    cleaned.sort(key=lambda x: x[1], reverse=True)

    # DEBUG 2: En çok yükselen ilk 5 coin
    top_lines = ["DEBUG: MEXC Top 5 (24h change):"]
    for sym, pct in cleaned[:5]:
        top_lines.append(f"- {sym}: %{pct:.2f}")
    send_telegram("\n".join(top_lines))

    # ALARM: %50 üstü coinler
    for sym, pct in cleaned:
        if pct < 50:
            break  # liste azalan sıralı, devamı zaten < 50 olur

        if pct >= 100:
            level_text = "💥 100%+ SERT PUMP"
        elif pct >= 80:
            level_text = "🔥 80%+ GÜÇLÜ PUMP"
        else:
            level_text = "⚡ 50%+ PUMP"

        send_telegram(
            f"{level_text}\n"
            f"🎯 Sembol: {sym}\n"
            f"📈 24h Değişim: %{pct:.2f}"
        )

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    send_telegram("🛰 MEXC pump radarı çalıştı.")
    check_mexc()

if __name__ == "__main__":
    main()
