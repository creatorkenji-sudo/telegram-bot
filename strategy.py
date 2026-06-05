# strategy.py

from indicators import ichimoku, stoch_rsi
from data import get_klines
from state import state


def analyze(symbol, interval):

    highs, lows, closes = get_klines(symbol, interval)

    price = closes[-1]
    stoch = stoch_rsi(closes)

    if state["ichimoku"]:
        up, down = ichimoku(highs, lows, closes)
    else:
        up, down = True, True

    signal = "NONE"

    if up and stoch < state["stoch_oversold"]:
        signal = "LONG"

    if down and stoch > state["stoch_overbought"]:
        signal = "SHORT"

    return {
        "symbol": symbol,
        "price": price,
        "stoch": round(stoch, 2),
        "signal": signal
    }