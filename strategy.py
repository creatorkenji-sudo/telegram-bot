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
            signals.append("⚠️ ĐẢO CHIỀU GIẢM TIỀM NĂNG - CẢNH BÁO BÁN")

    if state["ichimoku"] and trend_up:
        if bullish_divergence(bottoms, stoch_array) and stoch < state["stoch_oversold"]:
            signals.append("⚠️ ĐẢO CHIỀU TĂNG TIỀM NĂNG - CẢNH BÁO MUA")

    # =========================================
    # 2. TREND + PULLBACK ENTRY (THÊM MỚI)
    # =========================================

    # LONG ENTRY
    if trend_up:
        if stoch < state["stoch_oversold"]:
            signals.append("🟢 LONG ENTRY - TREND UP + PULLBACK (M15/H1)")

    # SHORT ENTRY
    if trend_down:
        if stoch > state["stoch_overbought"]:
            signals.append("🔴 SHORT ENTRY - TREND DOWN + RETEST (M15/H1)")

    return {
        "symbol": symbol,
        "stoch": round(stoch, 2),
        "trend": "UP" if trend_up else "DOWN",
        "signals": signals
    }