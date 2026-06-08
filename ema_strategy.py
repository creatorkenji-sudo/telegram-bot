# ============================================================
#  ema_strategy.py — Chiến lược B nâng cấp chống spam
#
#  Cải tiến:
#  [1] Hard cooldown 30 phút theo thời gian thực
#  [2] Chờ nến đóng cửa xác nhận (dùng nến -2, không dùng nến -1)
#  [3] MACD minimum threshold — lọc flip nhỏ
#  [4] Chống LONG+SHORT cùng lúc — khóa ngược chiều
#  [5] Trend consistency — giá phải đúng phía EMA 3 nến liên tiếp
#  [6] 4/6 điều kiện bắt buộc
# ============================================================

import time
import pandas as pd
import numpy as np
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO

# ── Cooldown config ───────────────────────────────────────────
COOLDOWN_MINUTES  = 30          # khóa X phút sau mỗi tín hiệu
MACD_MIN_FLIP     = 0.0001      # histogram phải đổi ít nhất giá trị này
TREND_CONSISTENCY = 3           # giá phải đúng phía EMA N nến liên tiếp

# ── State ─────────────────────────────────────────────────────
# symbol -> {"direction": "LONG"|"SHORT", "ts": timestamp}
_last_signal: dict[str, dict] = {}


def _in_cooldown(symbol: str) -> tuple[bool, int]:
    """Kiểm tra cooldown. Trả về (đang_cooldown, phút_còn_lại)."""
    if symbol not in _last_signal:
        return False, 0
    elapsed = time.time() - _last_signal[symbol]["ts"]
    remaining = COOLDOWN_MINUTES * 60 - elapsed
    if remaining > 0:
        return True, int(remaining // 60)
    return False, 0


def _set_cooldown(symbol: str, direction: str):
    _last_signal[symbol] = {"direction": direction, "ts": time.time()}


def _last_direction(symbol: str) -> str | None:
    return _last_signal.get(symbol, {}).get("direction")


# ── Indicators ───────────────────────────────────────────────
def _histogram_flip(hist: pd.Series) -> str | None:
    """
    Flip hợp lệ: đổi chiều VÀ độ lớn đủ ngưỡng MACD_MIN_FLIP.
    Dùng nến đã đóng [-3] → [-2] (không dùng nến đang chạy [-1]).
    """
    h2 = hist.iloc[-3]   # nến đóng trước
    h1 = hist.iloc[-2]   # nến đóng cuối cùng (xác nhận)
    if abs(h1) < MACD_MIN_FLIP:
        return None
    if h2 < 0 and h1 > MACD_MIN_FLIP:
        return "UP"
    if h2 > 0 and h1 < -MACD_MIN_FLIP:
        return "DOWN"
    return None


def _trend_consistent(df: pd.DataFrame, ema_val: float,
                      direction: str, n: int = TREND_CONSISTENCY) -> bool:
    """
    Giá phải đúng phía EMA trong N nến đóng gần nhất (bỏ nến đang chạy).
    """
    closes = df["close"].iloc[-(n+1):-1]   # N nến đã đóng
    if direction == "LONG":
        return all(c > ema_val for c in closes)
    return all(c < ema_val for c in closes)


def _is_pin_bar(candle, direction: str) -> bool:
    body  = abs(candle["close"] - candle["open"])
    rng   = candle["high"] - candle["low"]
    if rng == 0:
        return False
    if direction == "LONG":
        shadow = min(candle["open"], candle["close"]) - candle["low"]
        return body / rng <= 0.35 and shadow / rng >= 0.55
    shadow = candle["high"] - max(candle["open"], candle["close"])
    return body / rng <= 0.35 and shadow / rng >= 0.55


def _is_engulfing(df: pd.DataFrame, direction: str) -> bool:
    """Dùng nến -3 và -2 (đã đóng), không dùng nến -1 đang chạy."""
    prev = df.iloc[-3]
    curr = df.iloc[-2]
    if direction == "LONG":
        return (curr["close"] > curr["open"] and
                prev["close"] < prev["open"] and
                curr["open"]  <= prev["close"] and
                curr["close"] >= prev["open"])
    return (curr["close"] < curr["open"] and
            prev["close"] > prev["open"] and
            curr["open"]  >= prev["close"] and
            curr["close"] <= prev["open"])


def _candle_confirm(df: pd.DataFrame, ema_val: float,
                    direction: str) -> bool:
    """
    Xác nhận bằng nến ĐÃ ĐÓNG [-2], không dùng nến đang chạy [-1].
    Tolerance thu hẹp còn ±0.5%.
    """
    candle    = df.iloc[-2]
    tolerance = ema_val * 0.005

    if direction == "LONG":
        near = candle["low"] <= ema_val + tolerance
    else:
        near = candle["high"] >= ema_val - tolerance

    if not near:
        return False
    return _is_pin_bar(candle, direction) or _is_engulfing(df, direction)


def _momentum_confirm(df: pd.DataFrame, direction: str) -> bool:
    """
    Nến [-1] (nến hiện tại) phải đi đúng hướng sau pullback [-2].
    Đây là nến momentum xác nhận sau khi nến [-2] đã bounce.
    """
    curr      = df.iloc[-1]
    prev      = df.iloc[-2]
    curr_body = abs(curr["close"] - curr["open"])
    prev_body = abs(prev["close"] - prev["open"])
    if direction == "LONG":
        return curr["close"] > curr["open"] and curr_body >= prev_body * 0.7
    return curr["close"] < curr["open"] and curr_body >= prev_body * 0.7


def _volume_confirm(df: pd.DataFrame, period: int = 20) -> bool:
    """Volume nến [-2] (đã đóng) > trung bình."""
    avg = df["volume"].iloc[-(period+2):-2].mean()
    return df["volume"].iloc[-2] > avg * 1.1


# ── Main ─────────────────────────────────────────────────────
def check_ema_signal(symbol: str, df_h1: pd.DataFrame,
                     df_m15: pd.DataFrame) -> dict | None:

    # ── Cooldown check ────────────────────────────────────────
    in_cd, mins_left = _in_cooldown(symbol)
    if in_cd:
        print(f"    ⏳ [B] {symbol}: cooldown còn {mins_left} phút")
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

    # ── Xác định direction từ H1 ─────────────────────────────
    if ema20_h1 > ema50_h1:
        direction = "LONG"
    elif ema20_h1 < ema50_h1:
        direction = "SHORT"
    else:
        return None

    # ── Chống LONG+SHORT cùng lúc ────────────────────────────
    last_dir = _last_direction(symbol)
    if last_dir and last_dir != direction:
        # Vừa báo chiều ngược → bỏ qua, chưa hết cooldown
        in_cd2, _ = _in_cooldown(symbol)
        if in_cd2:
            print(f"    🚫 [B] {symbol}: vừa báo {last_dir}, bỏ qua {direction}")
            return None

    # ── 6 điều kiện ──────────────────────────────────────────
    scores = []

    # [1] EMA alignment H1 — 3 tầng
    h1_align = ((direction == "LONG"  and ema20_h1 > ema50_h1 > ema100_h1) or
                (direction == "SHORT" and ema20_h1 < ema50_h1 < ema100_h1))
    scores.append(("EMA alignment H1 (3 tầng)", h1_align))

    # [2] EMA alignment 15m
    m15_align = ((direction == "LONG"  and ema20_15 > ema50_15) or
                 (direction == "SHORT" and ema20_15 < ema50_15))
    scores.append(("EMA alignment 15m", m15_align))

    # [3] MACD histogram flip có ngưỡng (nến đã đóng)
    flip_15 = _histogram_flip(hist_15)
    flip_h1 = _histogram_flip(hist_h1)
    macd_ok = ((direction == "LONG"  and (flip_15 == "UP"   or flip_h1 == "UP"))  or
               (direction == "SHORT" and (flip_15 == "DOWN"  or flip_h1 == "DOWN")))
    scores.append(("MACD histogram flip (có ngưỡng)", macd_ok))

    # [4] Nến đóng xác nhận tại EMA (dùng nến -2)
    pullback_ema   = None
    pullback_label = None
    for ema_val, label in [(ema20_15, "EMA20"),
                            (ema50_15, "EMA50"),
                            (ema100_15, "EMA100")]:
        if _candle_confirm(df_m15, ema_val, direction):
            pullback_ema   = ema_val
            pullback_label = label
            break
    scores.append(("Nến đóng xác nhận pullback", pullback_ema is not None))

    # [5] Trend consistency — 3 nến đúng phía EMA
    ema_check = pullback_ema or ema20_15
    trend_ok  = _trend_consistent(df_m15, ema_check, direction)
    scores.append(("Trend consistency (3 nến)", trend_ok))

    # [6] Momentum + Volume
    mom_ok = _momentum_confirm(df_m15, direction)
    vol_ok = _volume_confirm(df_m15)
    scores.append(("Momentum + Volume xác nhận", mom_ok and vol_ok))

    # ── Kiểm tra 4/6 ─────────────────────────────────────────
    passed = [n for n, ok in scores if ok]
    failed = [n for n, ok in scores if not ok]
    print(f"    📊 [B] {symbol} {direction}: {len(passed)}/6 pass={passed}")

    if len(passed) < 4:
        return None

    # ── Entry / SL / TP ──────────────────────────────────────
    entry = round(price, 6)
    if direction == "LONG":
        sl_base = (pullback_ema * 0.998) if pullback_ema else entry * (1 - SL_PERCENT / 100)
        sl = round(min(sl_base, entry * (1 - SL_PERCENT / 100)), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl_base = (pullback_ema * 1.002) if pullback_ema else entry * (1 + SL_PERCENT / 100)
        sl = round(max(sl_base, entry * (1 + SL_PERCENT / 100)), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    # Bật cooldown
    _set_cooldown(symbol, direction)

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