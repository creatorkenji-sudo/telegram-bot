import numpy as np


# ================= ICHIMOKU =================
def ichimoku(high, low, close):
    tenkan = (np.max(high[-9:]) + np.min(low[-9:])) / 2
    kijun = (np.max(high[-26:]) + np.min(low[-26:])) / 2

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
    avg_loss = np.mean(loss[-14:]) + 1e-9

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    stoch = (rsi - 20) / 60
    return stoch


# ================= SWING HIGH =================
def swing_highs(highs):
    peaks = []
    for i in range(1, len(highs)-1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            peaks.append((i, highs[i]))
    return peaks


# ================= SWING LOW =================
def swing_lows(lows):
    bottoms = []
    for i in range(1, len(lows)-1):
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            bottoms.append((i, lows[i]))
    return bottoms


# ================= DIVERGENCE =================
def bearish_divergence(peaks, stoch_array):
    if len(peaks) < 2:
        return False

    (i1, p1), (i2, p2) = peaks[-2], peaks[-1]

    return p2 >= p1 and stoch_array[i2] < stoch_array[i1]


def bullish_divergence(bottoms, stoch_array):
    if len(bottoms) < 2:
        return False

    (i1, p1), (i2, p2) = bottoms[-2], bottoms[-1]

    return p2 <= p1 and stoch_array[i2] > stoch_array[i1]