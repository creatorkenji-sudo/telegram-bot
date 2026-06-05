import numpy as np
from indicators import *


def analyze(symbol, interval, highs, lows, closes, state):

    stoch = stoch_rsi(closes)

    peaks = swing_highs(highs)
    bottoms = swing_lows(lows)

    stoch_array = np.full(len(highs), stoch)

    trend_up, trend_down = ichimoku(highs, lows, closes)

    signals = []

    # ================= SHORT =================
    if state["ichimoku"] and trend_down:
        if bearish_divergence(peaks, stoch_array) and stoch > state["stoch_overbought"]:
            signals.append("🔴 TÍN HIỆU BÁN - ĐẢO CHIỀU GIẢM")

    # ================= LONG =================
    if state["ichimoku"] and trend_up:
        if bullish_divergence(bottoms, stoch_array) and stoch < state["stoch_oversold"]:
            signals.append("🟢 TÍN HIỆU MUA - ĐẢO CHIỀU TĂNG")

    return {
        "symbol": symbol,
        "stoch": round(stoch, 2),
        "signals": signals
    }