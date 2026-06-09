# ============================================================
#  trend.py — Xác định xu hướng Ichimoku H4 + H1
#  Dùng iloc[-2] = nến ĐÃ ĐÓNG để xác nhận trend
# ============================================================
from indicators import ichimoku


def get_trend(df):
    """
    Dùng nến đã đóng [-2] để xác định trend.
    Trả về: 'UP' | 'DOWN' | 'SIDE'
    """
    tenkan, kijun, sa, sb, _ = ichimoku(df)

    # Dùng nến đã đóng [-2]
    price     = df["close"].iloc[-2]
    cloud_top = max(sa.iloc[-2], sb.iloc[-2])
    cloud_bot = min(sa.iloc[-2], sb.iloc[-2])

    if price > cloud_top:
        return "UP"
    elif price < cloud_bot:
        return "DOWN"
    return "SIDE"


def multi_trend(df_h4, df_h1):
    """
    Cả H4 và H1 phải đồng thuận.
    Trả về: 'UPTREND' | 'DOWNTREND' | 'NO_TREND'
    """
    t4 = get_trend(df_h4)
    t1 = get_trend(df_h1)

    if t4 == "UP"   and t1 == "UP":
        return "UPTREND"
    if t4 == "DOWN" and t1 == "DOWN":
        return "DOWNTREND"
    return "NO_TREND"


def detect_kumo_cross(df):
    """
    Phát hiện giá vừa cắt qua mây — dùng nến [-2] và [-3].
    Trả về: 'UP' | 'DOWN' | None
    """
    tenkan, kijun, sa, sb, _ = ichimoku(df)

    # Nến đã đóng [-2] so với nến trước đó [-3]
    curr_price = df["close"].iloc[-2]
    prev_price = df["close"].iloc[-3]

    curr_top = max(sa.iloc[-2], sb.iloc[-2])
    curr_bot = min(sa.iloc[-2], sb.iloc[-2])
    prev_top = max(sa.iloc[-3], sb.iloc[-3])
    prev_bot = min(sa.iloc[-3], sb.iloc[-3])

    # Cắt lên trên mây
    if prev_price <= prev_top and curr_price > curr_top:
        return "UP"
    # Cắt xuống dưới mây
    if prev_price >= prev_bot and curr_price < curr_bot:
        return "DOWN"
    return None