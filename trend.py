# ============================================================
#  trend.py — Xu hướng Ichimoku + Kumo Cross
#
#  Dùng iloc[-2] (nến VỪA ĐÓNG) để xác nhận
#  Kumo cross: so sánh nến [-2] và [-1] để nhạy hơn
#  Cảnh báo cross kèm vị trí giá so với mây H1 + H4
# ============================================================
from indicators import ichimoku


def get_trend(df):
    """
    Dùng nến đã đóng [-2].
    Trả về: 'UP' | 'DOWN' | 'SIDE'
    """
    tenkan, kijun, sa, sb, _ = ichimoku(df)
    price     = df["close"].iloc[-2]
    cloud_top = max(sa.iloc[-2], sb.iloc[-2])
    cloud_bot = min(sa.iloc[-2], sb.iloc[-2])
    if price > cloud_top:
        return "UP"
    elif price < cloud_bot:
        return "DOWN"
    return "SIDE"


def multi_trend(df_h4, df_h1):
    """Chỉ dùng H1 xác nhận trend."""
    t1 = get_trend(df_h1)
    if t1 == "UP":
        return "UPTREND"
    if t1 == "DOWN":
        return "DOWNTREND"
    return "NO_TREND"


def _price_vs_cloud(df, label: str) -> str:
    """
    Mô tả vị trí giá đóng cửa [-2] so với mây.
    Dùng để note trong cảnh báo.
    """
    tenkan, kijun, sa, sb, _ = ichimoku(df)
    price     = df["close"].iloc[-2]
    cloud_top = max(sa.iloc[-2], sb.iloc[-2])
    cloud_bot = min(sa.iloc[-2], sb.iloc[-2])
    if price > cloud_top:
        return f"☁️ {label}: Giá TRÊN mây ({price:,.4f} > {cloud_top:,.4f})"
    elif price < cloud_bot:
        return f"☁️ {label}: Giá DƯỚI mây ({price:,.4f} < {cloud_bot:,.4f})"
    else:
        return f"☁️ {label}: Giá TRONG mây ({cloud_bot:,.4f} – {cloud_top:,.4f})"


def detect_kumo_cross(df, label: str = "H1"):
    """
    Phát hiện Kumo Cross nhạy hơn:
    - So sánh nến [-2] (vừa đóng) với nến [-1] (đang chạy)
    - Trả về dict với direction + thông tin vị trí giá
    - Trả về None nếu không có cross
    """
    tenkan, kijun, sa, sb, _ = ichimoku(df)

    # Nến vừa đóng [-2] và nến trước đó [-3]
    curr_price = df["close"].iloc[-2]
    prev_price = df["close"].iloc[-3]

    curr_top = max(sa.iloc[-2], sb.iloc[-2])
    curr_bot = min(sa.iloc[-2], sb.iloc[-2])
    prev_top = max(sa.iloc[-3], sb.iloc[-3])
    prev_bot = min(sa.iloc[-3], sb.iloc[-3])

    # Vị trí giá hiện tại
    price_pos = _price_vs_cloud(df, label)

    # Cross lên trên mây
    if prev_price <= prev_top and curr_price > curr_top:
        return {
            "direction": "UP",
            "label":     label,
            "price":     curr_price,
            "cloud_top": round(curr_top, 4),
            "cloud_bot": round(curr_bot, 4),
            "price_pos": price_pos,
        }

    # Cross xuống dưới mây
    if prev_price >= prev_bot and curr_price < curr_bot:
        return {
            "direction": "DOWN",
            "label":     label,
            "price":     curr_price,
            "cloud_top": round(curr_top, 4),
            "cloud_bot": round(curr_bot, 4),
            "price_pos": price_pos,
        }

    return None