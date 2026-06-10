# ============================================================
#  entry.py — Chiến lược A: Ichimoku + StochRSI
#  Dùng iloc[-2] = nến ĐÃ ĐÓNG để xác nhận tín hiệu
#  iloc[-1] = nến đang chạy, KHÔNG dùng để xét điều kiện
# ============================================================
from indicators import ichimoku, stoch_rsi
from config import SL_PERCENT, RR_RATIO, STOCH_OVERSOLD, STOCH_OVERBOUGHT


def check_entry(df_m15, trend: str):
    if trend == "NO_TREND":
        return None

    tenkan, kijun, sa, sb, chikou = ichimoku(df_m15)
    stoch = stoch_rsi(df_m15)

    # ── Dùng nến đã đóng [-2] để xét điều kiện ──────────────
    price      = df_m15["close"].iloc[-2]   # giá đóng nến trước
    curr_stoch = stoch.iloc[-2]             # stoch nến đã đóng
    prev_stoch = stoch.iloc[-3]             # stoch nến trước đó

    cloud_top = max(sa.iloc[-2], sb.iloc[-2])
    cloud_bot = min(sa.iloc[-2], sb.iloc[-2])
    tk        = tenkan.iloc[-2]
    ki        = kijun.iloc[-2]

    # Entry dùng giá hiện tại (nến đang chạy) để phản ánh thực tế
    entry_price = df_m15["close"].iloc[-1]

    # ── LONG ─────────────────────────────────────────────────
    if trend == "UPTREND":
        stoch_cross_up = prev_stoch < STOCH_OVERSOLD and curr_stoch >= STOCH_OVERSOLD
        if price > cloud_top and tk > ki and stoch_cross_up:
            sl = round(entry_price * (1 - SL_PERCENT / 100), 6)
            tp = round(entry_price + (entry_price - sl) * RR_RATIO, 6)
            return {
                "type":  "LONG",
                "entry": round(entry_price, 6),
                "sl":    sl,
                "tp":    tp,
                "stoch": round(curr_stoch, 1),
            }

    # ── SHORT ────────────────────────────────────────────────
    if trend == "DOWNTREND":
        stoch_cross_dn = prev_stoch > STOCH_OVERBOUGHT and curr_stoch <= STOCH_OVERBOUGHT
        if price < cloud_bot and tk < ki and stoch_cross_dn:
            sl = round(entry_price * (1 + SL_PERCENT / 100), 6)
            tp = round(entry_price - (sl - entry_price) * RR_RATIO, 6)
            return {
                "type":  "SHORT",
                "entry": round(entry_price, 6),
                "sl":    sl,
                "tp":    tp,
                "stoch": round(curr_stoch, 1),
            }

    return None
