# ============================================================
#  ema_strategy.py — Chiến lược B: EMA Pullback + MACD
#
#  Logic 2/3 đồng thuận:
#   1. EMA alignment (EMA20 > EMA50 cho LONG)
#   2. MACD histogram vừa đổi chiều (âm→dương hoặc ngược lại)
#   3. Nến xác nhận (giá bounce tại EMA, không đóng dưới EMA)
#
#  Cần ít nhất 2/3 điều kiện → gửi alert
# ============================================================
import pandas as pd
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO


def _histogram_flip(hist: pd.Series) -> str | None:
    """
    Phát hiện MACD histogram vừa đổi chiều.
    Trả về 'UP' (âm→dương), 'DOWN' (dương→âm), hoặc None.
    """
    prev = hist.iloc[-2]
    curr = hist.iloc[-1]
    if prev < 0 and curr >= 0:
        return "UP"
    if prev > 0 and curr <= 0:
        return "DOWN"
    return None


def _candle_confirm(df: pd.DataFrame, ema_val: float, direction: str) -> bool:
    """
    Nến xác nhận bounce tại EMA:
    - LONG: low chạm gần EMA (±0.5%) và close > open (nến xanh)
    - SHORT: high chạm gần EMA (±0.5%) và close < open (nến đỏ)
    """
    candle = df.iloc[-1]
    tolerance = ema_val * 0.005   # 0.5%

    if direction == "LONG":
        touched = abs(candle["low"] - ema_val) <= tolerance
        bullish = candle["close"] > candle["open"]
        return touched and bullish

    if direction == "SHORT":
        touched = abs(candle["high"] - ema_val) <= tolerance
        bearish = candle["close"] < candle["open"]
        return touched and bearish

    return False


def check_ema_signal(df_h1: pd.DataFrame, df_m15: pd.DataFrame) -> dict | None:
    """
    Kiểm tra tín hiệu EMA pullback trên H1 (alignment) + 15m (entry).
    Trả về dict tín hiệu hoặc None nếu không đủ 2/3.
    """
    # ── Chỉ báo H1 ───────────────────────────────────────────
    e20_h1, e50_h1, e100_h1 = calc_emas(df_h1)
    _, _, hist_h1            = calc_macd(df_h1)

    price_h1  = df_h1["close"].iloc[-1]
    ema20_h1  = e20_h1.iloc[-1]
    ema50_h1  = e50_h1.iloc[-1]
    ema100_h1 = e100_h1.iloc[-1]

    # ── Chỉ báo 15m ──────────────────────────────────────────
    e20_15, e50_15, e100_15 = calc_emas(df_m15)
    _, _, hist_15            = calc_macd(df_m15)

    price     = df_m15["close"].iloc[-1]
    ema20_15  = e20_15.iloc[-1]
    ema50_15  = e50_15.iloc[-1]
    ema100_15 = e100_15.iloc[-1]

    # ── Xác định direction từ H1 alignment ───────────────────
    h1_long  = ema20_h1 > ema50_h1   # EMA20 > EMA50 → uptrend H1
    h1_short = ema20_h1 < ema50_h1   # EMA20 < EMA50 → downtrend H1

    if not h1_long and not h1_short:
        return None

    direction = "LONG" if h1_long else "SHORT"

    # ── 3 điều kiện ──────────────────────────────────────────
    scores = []

    # 1. EMA alignment 15m
    if direction == "LONG":
        aligned = ema20_15 > ema50_15
    else:
        aligned = ema20_15 < ema50_15
    scores.append(("EMA alignment 15m", aligned))

    # 2. MACD histogram đổi chiều (15m hoặc H1)
    flip_15 = _histogram_flip(hist_15)
    flip_h1 = _histogram_flip(hist_h1)
    macd_ok = (
        (direction == "LONG"  and (flip_15 == "UP"   or flip_h1 == "UP"))   or
        (direction == "SHORT" and (flip_15 == "DOWN"  or flip_h1 == "DOWN"))
    )
    scores.append(("MACD histogram đổi chiều", macd_ok))

    # 3. Nến xác nhận pullback — thử EMA20 trước, EMA50, EMA100
    pullback_ema  = None
    pullback_prio = None
    for prio, ema_val, label in [
        (1, ema20_15,  "EMA20"),
        (2, ema50_15,  "EMA50"),
        (3, ema100_15, "EMA100"),
    ]:
        if _candle_confirm(df_m15, ema_val, direction):
            pullback_ema  = ema_val
            pullback_prio = label
            break

    candle_ok = pullback_ema is not None
    scores.append(("Nến xác nhận pullback", candle_ok))

    # ── Kiểm tra 2/3 ─────────────────────────────────────────
    passed = [name for name, ok in scores if ok]
    if len(passed) < 2:
        return None

    # ── Tính Entry / SL / TP (R:R 1:3) ───────────────────────
    entry = round(price, 6)
    if direction == "LONG":
        sl = round(entry * (1 - SL_PERCENT / 100), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl = round(entry * (1 + SL_PERCENT / 100), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    return {
        "type":         direction,
        "entry":        entry,
        "sl":           sl,
        "tp":           tp,
        "sl_pct":       sl_pct,
        "tp_pct":       tp_pct,
        "pullback_ema": pullback_prio or "EMA",
        "ema20_h1":     round(ema20_h1, 4),
        "ema50_h1":     round(ema50_h1, 4),
        "ema100_h1":    round(ema100_h1, 4),
        "macd_flip":    flip_15 or flip_h1,
        "passed":       passed,          # điều kiện nào đã pass
        "score":        f"{len(passed)}/3",
    }
