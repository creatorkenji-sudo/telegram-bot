from indicators import ichimoku, stoch_rsi
from trend import get_trend


def check_entry(df_m15, trend):
    tenkan, kijun, sa, sb = ichimoku(df_m15)

    price = df_m15["close"].iloc[-1]

    stoch = stoch_rsi(df_m15).iloc[-1]
    prev_stoch = stoch_rsi(df_m15).iloc[-2]

    cloud_top = max(sa.iloc[-1], sb.iloc[-1])
    cloud_bottom = min(sa.iloc[-1], sb.iloc[-1])

    # LONG SETUP
    if trend == "UPTREND":
        if price > cloud_top and tenkan.iloc[-1] > kijun.iloc[-1] and prev_stoch < 20 and stoch > 20:
            return {
                "type": "LONG",
                "entry": price,
                "sl": cloud_bottom,
                "tp": price + (price - cloud_bottom) * 2
            }

    # SHORT SETUP
    if trend == "DOWNTREND":
        if price < cloud_bottom and tenkan.iloc[-1] < kijun.iloc[-1] and prev_stoch > 80 and stoch < 80:
            return {
                "type": "SHORT",
                "entry": price,
                "sl": cloud_top,
                "tp": price - (cloud_top - price) * 2
            }

    return None