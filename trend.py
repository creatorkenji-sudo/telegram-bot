# ============================================================
#  trend.py — Xác định xu hướng H4 + H1, phát hiện Kumo Cross
# ============================================================
from indicators import ichimoku


def get_trend(df):
    """
    Trả về: "UP" | "DOWN" | "SIDE"
    dựa trên vị trí giá so với mây Ichimoku.
    """
    tenkan, kijun, sa, sb, chikou = ichimoku(df)

    price       = df["close"].iloc[-1]
    cloud_top   = max(sa.iloc[-1], sb.iloc[-1])
    cloud_bot   = min(sa.iloc[-1], sb.iloc[-1])

    if price > cloud_top:
        return "UP"
    elif price < cloud_bot:
        return "DOWN"
    return "SIDE"


def multi_trend(df_h4, df_h1):
    """
    Cả H4 và H1 phải đồng thuận mới ra tín hiệu.
    Trả về: "UPTREND" | "DOWNTREND" | "NO_TREND"
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
    Phát hiện giá vừa cắt qua mây Ichimoku (nến -2 → nến -1).
    Trả về: "UP" | "DOWN" | None
    """
    tenkan, kijun, sa, sb, chikou = ichimoku(df)

    def cloud_top(i):
        return max(sa.iloc[i], sb.iloc[i])

    def cloud_bot(i):
        return min(sa.iloc[i], sb.iloc[i])

    prev_price = df["close"].iloc[-2]
    curr_price = df["close"].iloc[-1]

    # Vừa cắt lên trên mây
    if prev_price <= cloud_top(-2) and curr_price > cloud_top(-1):
        return "UP"
    # Vừa cắt xuống dưới mây
    if prev_price >= cloud_bot(-2) and curr_price < cloud_bot(-1):
        return "DOWN"
    return None
