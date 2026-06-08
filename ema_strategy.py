# ============================================================
#  ema_strategy.py — Chiến lược B nâng cấp
#
#  6 điều kiện lọc, cần 4/6 mới gửi alert:
#
#  [1] EMA alignment H1      — EMA20 > EMA50 (LONG) / < (SHORT)
#  [2] EMA alignment 15m     — cùng chiều H1
#  [3] MACD histogram đổi chiều 15m hoặc H1
#  [4] Nến xác nhận mạnh     — pin bar hoặc engulfing rõ nét
#  [5] Momentum xác nhận     — nến sau pullback đi đúng hướng
#  [6] Volume tăng           — volume nến hiện tại > trung bình 20 nến
#
#  + Cooldown: sau 1 tín hiệu phải chờ COOLDOWN_CANDLES nến mới báo lại
# ============================================================
import pandas as pd
import numpy as np
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO

COOLDOWN_CANDLES = 5   # chờ 5 nến 15m (~75 phút) trước khi báo lại

# Lưu cooldown: symbol -> số nến còn phải chờ
_cooldown: dict[str, int] = {}


# ── Helpers ──────────────────────────────────────────────────
def _histogram_flip(hist: pd.Series) -> str | None:
    prev, curr = hist.iloc[-2], hist.iloc[-1]
    if prev < 0 and curr >= 0:
        return "UP"
    if prev > 0 and curr <= 0:
        return "DOWN"
    return None


def _is_pin_bar(candle, ema_val: float, direction: str) -> bool:
    """
    Pin bar: thân nến nhỏ, bóng dài về phía EMA.
    Thân <= 30% tổng range, bóng >= 60% range về đúng hướng.
    """
    body   = abs(candle["close"] - candle["open"])
    rng    = candle["high"] - candle["low"]
    if rng == 0:
        return False
    body_ratio = body / rng

    if direction == "LONG":
        shadow = candle["open"] - candle["low"] if candle["close"] >= candle["open"] \
                 else candle["close"] - candle["low"]
        return body_ratio <= 0.3 and shadow / rng >= 0.6
    else:
        shadow = candle["high"] - candle["open"] if candle["close"] <= candle["open"] \
                 else candle["high"] - candle["close"]
        return body_ratio <= 0.3 and shadow / rng >= 0.6


def _is_engulfing(df: pd.DataFrame, direction: str) -> bool:
    """
    Engulfing mạnh: nến hiện tại nuốt toàn bộ thân nến trước.
    """
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    if direction == "LONG":
        return (
            curr["close"] > curr["open"] and          # nến xanh
            prev["close"] < prev["open"] and          # nến đỏ trước
            curr["open"]  <= prev["close"] and        # mở dưới đóng cũ
            curr["close"] >= prev["open"]             # đóng trên mở cũ
        )
    else:
        return (
            curr["close"] < curr["open"] and
            prev["close"] > prev["open"] and
            curr["open"]  >= prev["close"] and
            curr["close"] <= prev["open"]
        )


def _candle_confirm(df: pd.DataFrame, ema_val: float, direction: str) -> bool:
    """Nến xác nhận mạnh: pin bar HOẶC engulfing tại vùng EMA (±0.8%)."""
    candle    = df.iloc[-1]
    tolerance = ema_val * 0.008

    if direction == "LONG":
        near_ema = candle["low"] <= ema_val + tolerance
    else:
        near_ema = candle["high"] >= ema_val - tolerance

    if not near_ema:
        return False

    return _is_pin_bar(candle, ema_val, direction) or _is_engulfing(df, direction)


def _momentum_confirm(df: pd.DataFrame, direction: str) -> bool:
    """
    Momentum: nến sau pullback (nến -1) đi đúng hướng
    và mạnh hơn nến pullback (nến -2).
    LONG:  nến -1 xanh, close > open, body > body nến -2
    SHORT: nến -1 đỏ,   close < open, body > body nến -2
    """
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    curr_body = abs(curr["close"] - curr["open"])
    prev_body = abs(prev["close"] - prev["open"])

    if direction == "LONG":
        return curr["close"] > curr["open"] and curr_body > prev_body * 0.8
    else:
        return curr["close"] < curr["open"] and curr_body > prev_body * 0.8


def _volume_confirm(df: pd.DataFrame, period: int = 20) -> bool:
    """Volume nến hiện tại > trung bình 20 nến gần nhất."""
    avg_vol = df["volume"].iloc[-period-1:-1].mean()
    cur_vol = df["volume"].iloc[-1]
    return cur_vol > avg_vol * 1.1   # ít nhất 10% trên trung bình


# ── Main function ─────────────────────────────────────────────
def check_ema_signal(symbol: str, df_h1: pd.DataFrame, df_m15: pd.DataFrame) -> dict | None:
    # ── Cooldown check ────────────────────────────────────────
    if _cooldown.get(symbol, 0) > 0:
        _cooldown[symbol] -= 1
        print(f"    ⏳ [B] {symbol}: cooldown còn {_cooldown[symbol]} nến")
        return None

    # ── Chỉ báo H1 ───────────────────────────────────────────
    e20_h1, e50_h1, e100_h1 = calc_emas(df_h1)
    _, _, hist_h1            = calc_macd(df_h1)
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

    # ── Xác định hướng từ H1 ─────────────────────────────────
    if ema20_h1 > ema50_h1:
        direction = "LONG"
    elif ema20_h1 < ema50_h1:
        direction = "SHORT"
    else:
        return None

    # ── 6 điều kiện ──────────────────────────────────────────
    scores = []

    # [1] EMA alignment H1
    h1_align = (direction == "LONG"  and ema20_h1 > ema50_h1 > ema100_h1) or \
               (direction == "SHORT" and ema20_h1 < ema50_h1 < ema100_h1)
    scores.append(("EMA alignment H1 (3 tầng)", h1_align))

    # [2] EMA alignment 15m
    m15_align = (direction == "LONG"  and ema20_15 > ema50_15) or \
                (direction == "SHORT" and ema20_15 < ema50_15)
    scores.append(("EMA alignment 15m", m15_align))

    # [3] MACD histogram đổi chiều
    flip_15 = _histogram_flip(hist_15)
    flip_h1 = _histogram_flip(hist_h1)
    macd_ok = (
        (direction == "LONG"  and (flip_15 == "UP"   or flip_h1 == "UP"))  or
        (direction == "SHORT" and (flip_15 == "DOWN"  or flip_h1 == "DOWN"))
    )
    scores.append(("MACD histogram đổi chiều", macd_ok))

    # [4] Nến xác nhận mạnh (pin bar / engulfing)
    pullback_ema   = None
    pullback_label = None
    for ema_val, label in [
        (ema20_15,  "EMA20"),
        (ema50_15,  "EMA50"),
        (ema100_15, "EMA100"),
    ]:
        if _candle_confirm(df_m15, ema_val, direction):
            pullback_ema   = ema_val
            pullback_label = label
            break
    scores.append(("Nến xác nhận (pin bar/engulfing)", pullback_ema is not None))

    # [5] Momentum xác nhận
    momentum_ok = _momentum_confirm(df_m15, direction)
    scores.append(("Momentum xác nhận", momentum_ok))

    # [6] Volume tăng
    volume_ok = _volume_confirm(df_m15)
    scores.append(("Volume tăng", volume_ok))

    # ── Kiểm tra 4/6 ─────────────────────────────────────────
    passed = [name for name, ok in scores if ok]
    failed = [name for name, ok in scores if not ok]

    print(f"    📊 [B] {symbol} {direction}: {len(passed)}/6 — pass: {passed}")

    if len(passed) < 4:
        return None

    # ── Tính Entry / SL / TP ─────────────────────────────────
    entry = round(price, 6)
    if direction == "LONG":
        # SL đặt dưới EMA pullback (hoặc SL_PERCENT nếu không có)
        sl_base = pullback_ema * 0.998 if pullback_ema else entry * (1 - SL_PERCENT / 100)
        sl = round(min(sl_base, entry * (1 - SL_PERCENT / 100)), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl_base = pullback_ema * 1.002 if pullback_ema else entry * (1 + SL_PERCENT / 100)
        sl = round(max(sl_base, entry * (1 + SL_PERCENT / 100)), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    # Bật cooldown sau khi có tín hiệu
    _cooldown[symbol] = COOLDOWN_CANDLES

    return {
        "type":         direction,
        "entry":        entry,
        "sl":           sl,
        "tp":           tp,
        "sl_pct":       sl_pct,
        "tp_pct":       tp_pct,
        "pullback_ema": pullback_label or "—",
        "ema20_h1":     round(ema20_h1, 4),
        "ema50_h1":     round(ema50_h1, 4),
        "ema100_h1":    round(ema100_h1, 4),
        "macd_flip":    flip_15 or flip_h1,
        "passed":       passed,
        "failed":       failed,
        "score":        f"{len(passed)}/6",
    }