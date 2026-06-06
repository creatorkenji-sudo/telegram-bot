import numpy as np
from indicators import *


def analyze(symbol, interval, highs, lows, closes, state):

    stoch = stoch_rsi(closes)

    peaks = swing_highs(highs)
    bottoms = swing_lows(lows)

    stoch_array = np.full(len(highs), stoch)

    trend_up, trend_down = ichimoku(highs, lows, closes)

    signals = []

    # =========================================
    # 1. REVERSAL (GIỮ NGUYÊN LOGIC CŨ)
    # =========================================

    if state["ichimoku"] and trend_down:
        if bearish_divergence(peaks, stoch_array) and stoch > state["stoch_overbought"]:
            signals.append("BEARISH_REVERSAL")

    if state["ichimoku"] and trend_up:
        if bullish_divergence(bottoms, stoch_array) and stoch < state["stoch_oversold"]:
            signals.append("BULLISH_REVERSAL")

    # =========================================
    # 2. TREND + PULLBACK ENTRY (THÊM MỚI)
    # =========================================

    # LONG ENTRY
    if trend_up:
        if stoch < state["stoch_oversold"]:
            signals.append("LONG_ENTRY")

    # SHORT ENTRY
    if trend_down:
        if stoch > state["stoch_overbought"]:
            signals.append("SHORT_ENTRY")

    return {
        "symbol": symbol,
        "stoch": round(stoch, 2),
        "trend": "UP" if trend_up else "DOWN",
        "signals": signals
    }