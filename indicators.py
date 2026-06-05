# indicators.py

import numpy as np


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