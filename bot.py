import requests
import time
import threading

from config import (
    TOKEN, CHAT_ID,
    SYMBOL, INTERVAL, LIMIT,
    CHECK_INTERVAL,
    THRESHOLD_SHORT,
    MA_PERIOD,
    MIN_SEND_CHANGE
)

# ================= TELEGRAM =================
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=10
        )

    except Exception as e:
        print("Telegram error:", e)


# ================= GET CANDLES =================
def get_candles():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"

        params = {
            "category": "linear",
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }

        r = requests.get(url, params=params, timeout=10)

        print("RAW:", r.text[:200])

        data = r.json()

        # ✅ check API error đúng cách
        if data.get("retCode") != 0:
            print("API ERROR:", data)
            return None

        candles = []

        # ✅ đúng structure Bybit
        for c in data["result"]["list"]:
            candles.append({
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5]) if len(c) > 5 else 0,
            })

        return candles

    except Exception as e:
        print("Candle error:", e)
        return None

# ================= ANALYZE =================
def analyze(candles):
    
    if not candles or len(candles) < 2:
        return 0, 0, "no data", "no data"
        
    closes = [c["close"] for c in candles]

    last = closes[-1]
    prev = closes[-2]

    change = ((last - prev) / prev) * 100

    if change > THRESHOLD_SHORT:
        trend = "📈 Uptrend ngắn hạn"
    elif change < -THRESHOLD_SHORT:
        trend = "📉 Downtrend ngắn hạn"
    else:
        trend = "➡️ Sideway"

    ma = sum(closes[-MA_PERIOD:]) / MA_PERIOD

    if last > ma:
        bias = "🟢 Bull bias"
    else:
        bias = "🔴 Bear bias"
    
        
    return last, change, trend, bias
# ================= GET PRICE =================
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "category": "linear",
        "symbol": "BTCUSDT"
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    return float(data["result"]["list"][0]["lastPrice"])
    
def handle_message(text):
    if text == "/price" or text == "/btc":
        price = get_btc_price()
        return f"₿ BTC hiện tại: ${price:.2f}"

    return None
    
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    params = {"timeout": 100, "offset": offset}

    r = requests.get(url, params=params)
    return r.json()   
# ================= MAIN LOOP =================
def telegram_loop():
    offset = None

    while True:
        try:
            data = get_updates(offset)

            if "result" in data:
                for update in data["result"]:

                    offset = update["update_id"] + 1

                    if "message" in update:
                        text = update["message"].get("text", "")

                        reply = handle_message(text)

                        if reply:
                            send_message(reply)

        except Exception as e:
            print("Telegram error:", e)
def run():
    send_message(f"🤖 Bot Started: {SYMBOL} {INTERVAL}")

    last_sent_price = None

    while True:
        try:
            candles = get_candles()

            if not candles:
                continue

            price, change, trend, bias = analyze(candles)

            # chống spam
            if last_sent_price:
                if abs(price - last_sent_price) / last_sent_price * 100 < MIN_SEND_CHANGE:
                    time.sleep(CHECK_INTERVAL)
                    continue

            last_sent_price = price

            msg = (
                f"📊 {SYMBOL} / {INTERVAL}\n\n"
                f"💰 Price: {price:.2f}\n"
                f"📊 Change: {change:.2f}%\n"
                f"{trend}\n"
                f"{bias}"
            )

            print(msg)
            send_message(msg)

        except Exception as e:
            print("Main error:", e)
            send_message(f"❌ Error: {e}")

        time.sleep(CHECK_INTERVAL)


# ================= START =================
if __name__ == "__main__":   
    threading.Thread(target=telegram_loop, daemon=True).start()
    run()