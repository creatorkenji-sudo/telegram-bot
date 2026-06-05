import requests
import time
import numpy as np

# ================= CONFIG =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 200

# ================= TELEGRAM =================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# ================= PRICE DATA =================
def get_klines():
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": LIMIT}
    data = requests.get(url, params=params).json()

    closes = np.array([float(x[4]) for x in data])
    highs  = np.array([float(x[2]) for x in data])
    lows   = np.array([float(x[3]) for x in data])

    return highs, lows, closes


# ================= ICHIMOKU =================
def ichimoku(high, low):
    tenkan = (np.max(high[-9:]) + np.min(low[-9:])) / 2
    kijun  = (np.max(high[-26:]) + np.min(low[-26:])) / 2

    price = close[-1]

    trend_up = price > kijun and tenkan > kijun
    trend_down = price < kijun and tenkan < kijun

    return trend_up, trend_down


# ================= STOCH RSI =================
def stoch_rsi(closes, period=14):
    delta = np.diff(closes)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    stoch = (rsi - 20) / (80 - 20)
    return stoch


# ================= SWING HIGH DETECTION =================
def swing_highs(highs):
    peaks = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            peaks.append((i, highs[i]))
    return peaks


# ================= DOUBLE TOP =================
def detect_double_top(peaks):
    if len(peaks) < 2:
        return False, None

    p1, p2 = peaks[-2], peaks[-1]

    i1, v1 = p1
    i2, v2 = p2

    price_diff = abs(v1 - v2) / v1

    if price_diff < 0.01:  # 1%
        return True, (p1, p2)

    return False, None


# ================= DIVERGENCE =================
def bearish_divergence(peaks, stoch_values):
    if len(peaks) < 2:
        return False

    (i1, p1), (i2, p2) = peaks[-2], peaks[-1]

    if p2 >= p1 and stoch_values[i2] < stoch_values[i1]:
        return True

    return False


# ================= MAIN STRATEGY =================
def check_signal():
    global close

    highs, lows, closes = get_klines()
    close = closes

    # indicators
    trend_up, trend_down = ichimoku(highs, lows)
    stoch = stoch_rsi(closes)

    peaks = swing_highs(highs)

    double_top, points = detect_double_top(peaks)

    divergence = False
    if len(peaks) >= 2:
        stoch_values = np.full(len(highs), stoch)
        divergence = bearish_divergence(peaks, stoch_values)

    price = closes[-1]

    # ================= SIGNAL =================
    if trend_up and double_top and divergence and stoch > 0.8:
        send_telegram(
            f"🔴 SHORT SIGNAL\n"
            f"Symbol: {SYMBOL}\n"
            f"Pattern: Double Top + Bearish Divergence\n"
            f"Price: {price}\n"
            f"StochRSI: {stoch:.2f}"
        )

    if trend_down and stoch < 0.2:
        send_telegram(
            f"🟢 LONG WATCH\n"
            f"Symbol: {SYMBOL}\n"
            f"Price: {price}\n"
            f"StochRSI: {stoch:.2f}"
        )


# ================= LOOP =================
while True:
    try:
        check_signal()
        time.sleep(60 * 5)  # check mỗi 5 phút
    except Exception as e:
        print("Error:", e)
        time.sleep(10)