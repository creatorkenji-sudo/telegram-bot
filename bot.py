import requests
import time
import numpy as np

# ================= CONFIG =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"


SYMBOL = "BTCUSDT"

TIMEFRAMES = {
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d"
}

LIMIT = 200

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# ================= DATA =================
def get_data(interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": SYMBOL, "interval": interval, "limit": LIMIT}
    data = requests.get(url, params=params).json()

    highs = np.array([float(x[2]) for x in data])
    lows  = np.array([float(x[3]) for x in data])
    closes= np.array([float(x[4]) for x in data])

    return highs, lows, closes


# ================= ICHIMOKU =================
def ichimoku(high, low, close):
    tenkan = (np.max(high[-9:]) + np.min(low[-9:])) / 2
    kijun  = (np.max(high[-26:]) + np.min(low[-26:])) / 2

    price = close[-1]

    up = price > kijun and tenkan > kijun
    down = price < kijun and tenkan < kijun

    return up, down


# ================= STOCH RSI =================
def stoch_rsi(closes):
    delta = np.diff(closes)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-14:])
    avg_loss = np.mean(loss[-14:])

    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    stoch = (rsi - 20) / 60
    return stoch


# ================= SIGNAL =================
def analyze_tf(tf, interval):
    highs, lows, closes = get_data(interval)

    price = closes[-1]
    stoch = stoch_rsi(closes)
    up, down = ichimoku(highs, lows, closes)

    signal = "NONE"

    if up and stoch < 0.2:
        signal = "🟢 LONG"
    elif down and stoch > 0.8:
        signal = "🔴 SHORT"

    return {
        "tf": tf,
        "price": price,
        "stoch": round(stoch, 2),
        "trend": "UP" if up else "DOWN" if down else "SIDE",
        "signal": signal
    }


# ================= REPORT =================
def send_report():
    results = []

    for tf, interval in TIMEFRAMES.items():
        try:
            r = analyze_tf(tf, interval)
            results.append(r)
        except Exception as e:
            results.append({"tf": tf, "error": str(e)})

    msg = "📊 MULTI-TIMEFRAME REPORT\n\n"

    for r in results:
        if "error" in r:
            msg += f"{r['tf']} ❌ ERROR\n"
            continue

        msg += (
            f"{r['tf']} | Price: {r['price']}\n"
            f"Trend: {r['trend']}\n"
            f"StochRSI: {r['stoch']}\n"
            f"Signal: {r['signal']}\n\n"
        )

    send(msg)


# ================= LOOP =================
last_report = 0

while True:
    try:
        now = time.time()

        # gửi report mỗi 1 giờ
        if now - last_report >= 3600:
            send_report()
            last_report = now

        time.sleep(10)

    except Exception as e:
        print("Error:", e)
        time.sleep(5)