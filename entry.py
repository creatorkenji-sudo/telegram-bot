# ============================================================
#  entry.py — Tìm điểm vào lệnh 15m (Chiến lược A)
# ============================================================
from indicators import ichimoku, stoch_rsi
from config import SL_PERCENT, RR_RATIO, STOCH_OVERSOLD, STOCH_OVERBOUGHT


def check_entry(df_m15, trend: str):
    if trend == "NO_TREND":
        return None

    tenkan, kijun, sa, sb, chikou = ichimoku(df_m15)
    stoch = stoch_rsi(df_m15)

    price     = df_m15["close"].iloc[-1]
    cloud_top = max(sa.iloc[-1], sb.iloc[-1])
    cloud_bot = min(sa.iloc[-1], sb.iloc[-1])
    curr_stoch = stoch.iloc[-1]
    prev_stoch = stoch.iloc[-2]
    curr_tenkan = tenkan.iloc[-1]
    curr_kijun  = kijun.iloc[-1]

    # LONG
    if trend == "UPTREND":
        stoch_cross_up = prev_stoch < STOCH_OVERSOLD and curr_stoch >= STOCH_OVERSOLD
        if price > cloud_top and curr_tenkan > curr_kijun and stoch_cross_up:
            sl = round(price * (1 - SL_PERCENT / 100), 6)
            tp = round(price + (price - sl) * RR_RATIO, 6)
            return {
                "type":  "LONG",
                "entry": round(price, 6),
                "sl":    sl,
                "tp":    tp,
                "stoch": round(curr_stoch, 1),
            }

    # SHORT
    if trend == "DOWNTREND":
        stoch_cross_dn = prev_stoch > STOCH_OVERBOUGHT and curr_stoch <= STOCH_OVERBOUGHT
        if price < cloud_bot and curr_tenkan < curr_kijun and stoch_cross_dn:
            sl = round(price * (1 + SL_PERCENT / 100), 6)
            tp = round(price - (sl - price) * RR_RATIO, 6)
            return {
                "type":  "SHORT",
                "entry": round(price, 6),
                "sl":    sl,
                "tp":    tp,
                "stoch": round(curr_stoch, 1),
            }

    return None
