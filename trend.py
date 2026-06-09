# ============================================================
#  trend.py — Xác định xu hướng Ichimoku H4 + H1
# ============================================================
from indicators import ichimoku


def get_trend(df):
    tenkan, kijun, sa, sb, chikou = ichimoku(df)
    price     = df["close"].iloc[-1]
    cloud_top = max(sa.iloc[-1], sb.iloc[-1])
    cloud_bot = min(sa.iloc[-1], sb.iloc[-1])
    if price > cloud_top:
        return "UP"
    elif price < cloud_bot:
        return "DOWN"
    return "SIDE"


def multi_trend(df_h4, df_h1):
    t4 = get_trend(df_h4)
    t1 = get_trend(df_h1)
    if t4 == "UP"   and t1 == "UP":
        return "UPTREND"
    if t4 == "DOWN" and t1 == "DOWN":
        return "DOWNTREND"
    return "NO_TREND"


def detect_kumo_cross(df):
    tenkan, kijun, sa, sb, chikou = ichimoku(df)
    cloud_top_cur  = max(sa.iloc[-1], sb.iloc[-1])
    cloud_top_prev = max(sa.iloc[-2], sb.iloc[-2])
    cloud_bot_cur  = min(sa.iloc[-1], sb.iloc[-1])
    cloud_bot_prev = min(sa.iloc[-2], sb.iloc[-2])
    prev_price = df["close"].iloc[-2]
    curr_price = df["close"].iloc[-1]
    if prev_price <= cloud_top_prev and curr_price > cloud_top_cur:
        return "UP"
    if prev_price >= cloud_bot_prev and curr_price < cloud_bot_cur:
        return "DOWN"
    return None
