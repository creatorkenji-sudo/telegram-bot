# ============================================================
#  ema_strategy.py — Chiến lược B nâng cấp
#
#  7 bộ lọc — bật/tắt động, ngưỡng min_pass tùy chỉnh
#  RSI > 50 LONG / < 50 SHORT
#  Cooldown 30 phút theo thời gian thực
#  Chống LONG+SHORT cùng lúc
#  Dùng nến đã đóng [-2] để xác nhận
# ============================================================
import time
import pandas as pd
import numpy as np
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO

COOLDOWN_SECONDS  = 30 * 60
MACD_MIN_FLIP     = 0.0001
TREND_CONSISTENCY = 3

_last_signal: dict = {}


def _in_cooldown(symbol):
    if symbol not in _last_signal:
        return False, 0
    remaining = COOLDOWN_SECONDS - (time.time() - _last_signal[symbol]["ts"])
    return (True, int(remaining // 60)) if remaining > 0 else (False, 0)


def _set_cooldown(symbol, direction):
    _last_signal[symbol] = {"direction": direction, "ts": time.time()}


def _last_direction(symbol):
    return _last_signal.get(symbol, {}).get("direction")


# ── RSI ──────────────────────────────────────────────────────
def _calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ── Filter helpers ────────────────────────────────────────────
def _histogram_flip(hist):
    h2, h1 = hist.iloc[-3], hist.iloc[-2]
    if abs(h1) < MACD_MIN_FLIP:
        return None
    if h2 < 0 and h1 > MACD_MIN_FLIP:
        return "UP"
    if h2 > 0 and h1 < -MACD_MIN_FLIP:
        return "DOWN"
    return None


def _trend_consistent(df, ema_val, direction):
    closes = df["close"].iloc[-(TREND_CONSISTENCY+1):-1]
    return all(c > ema_val for c in closes) if direction == "LONG" \
           else all(c < ema_val for c in closes)


def _is_pin_bar(candle, direction):
    body = abs(candle["close"] - candle["open"])
    rng  = candle["high"] - candle["low"]
    if rng == 0:
        return False
    if direction == "LONG":
        shadow = min(candle["open"], candle["close"]) - candle["low"]
        return body/rng <= 0.35 and shadow/rng >= 0.55
    shadow = candle["high"] - max(candle["open"], candle["close"])
    return body/rng <= 0.35 and shadow/rng >= 0.55


def _is_engulfing(df, direction):
    prev, curr = df.iloc[-3], df.iloc[-2]
    if direction == "LONG":
        return (curr["close"] > curr["open"] and prev["close"] < prev["open"] and
                curr["open"] <= prev["close"] and curr["close"] >= prev["open"])
    return (curr["close"] < curr["open"] and prev["close"] > prev["open"] and
            curr["open"] >= prev["close"] and curr["close"] <= prev["open"])


def _candle_confirm(df, ema_val, direction):
    candle    = df.iloc[-2]
    tolerance = ema_val * 0.005
    near = (candle["low"] <= ema_val + tolerance if direction == "LONG"
            else candle["high"] >= ema_val - tolerance)
    return near and (_is_pin_bar(candle, direction) or _is_engulfing(df, direction))


def _momentum_ok(df, direction):
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    cb   = abs(curr["close"] - curr["open"])
    pb   = abs(prev["close"] - prev["open"])
    ok   = (curr["close"] > curr["open"] and cb >= pb * 0.7) if direction == "LONG" \
           else (curr["close"] < curr["open"] and cb >= pb * 0.7)
    avg_vol = df["volume"].iloc[-22:-2].mean()
    vol_ok  = df["volume"].iloc[-2] > avg_vol * 1.1
    return ok and vol_ok


# ── Filter metadata ───────────────────────────────────────────
FILTER_KEYS = ["ema_h1","ema_15m","macd","rsi","candle","trend","momentum"]

FILTER_LABELS = {
    "ema_h1":   "EMA alignment H1 (3 tầng)",
    "ema_15m":  "EMA alignment 15m",
    "macd":     "MACD histogram flip",
    "rsi":      "RSI xác nhận động lực",
    "candle":   "Nến đóng xác nhận pullback",
    "trend":    "Trend consistency (3 nến)",
    "momentum": "Momentum + Volume",
}

FILTER_DESC = {
    "ema_h1":   "EMA20 > EMA50 > EMA100",
    "ema_15m":  "EMA20 > EMA50 cùng chiều H1",
    "macd":     "Đổi chiều nến đóng, có ngưỡng",
    "rsi":      "RSI > 50 LONG / < 50 SHORT",
    "candle":   "Pin bar / Engulfing tại EMA[-2]",
    "trend":    "Giá đúng phía EMA 3 nến liên tiếp",
    "momentum": "Nến mạnh hơn + volume tăng 10%",
}


# ── Main check ────────────────────────────────────────────────
def check_ema_signal(symbol, df_h1, df_m15, active_filters, min_pass):
    # Cooldown
    in_cd, mins_left = _in_cooldown(symbol)
    if in_cd:
        print(f"    ⏳ [B] {symbol}: cooldown còn {mins_left} phút")
        return None

    # Indicators H1
    e20_h1, e50_h1, e100_h1 = calc_emas(df_h1)
    _, _, hist_h1            = calc_macd(df_h1)
    ema20_h1  = e20_h1.iloc[-1]
    ema50_h1  = e50_h1.iloc[-1]
    ema100_h1 = e100_h1.iloc[-1]

    # Indicators 15m
    e20_15, e50_15, e100_15 = calc_emas(df_m15)
    _, _, hist_15            = calc_macd(df_m15)
    price     = df_m15["close"].iloc[-1]
    ema20_15  = e20_15.iloc[-1]
    ema50_15  = e50_15.iloc[-1]
    ema100_15 = e100_15.iloc[-1]

    # Direction
    if ema20_h1 > ema50_h1:
        direction = "LONG"
    elif ema20_h1 < ema50_h1:
        direction = "SHORT"
    else:
        return None

    # Chống ngược chiều
    last_dir = _last_direction(symbol)
    if last_dir and last_dir != direction and _in_cooldown(symbol)[0]:
        print(f"    🚫 [B] {symbol}: vừa báo {last_dir}, bỏ qua {direction}")
        return None

    # Pullback EMA
    flip_15 = _histogram_flip(hist_15)
    flip_h1 = _histogram_flip(hist_h1)
    pullback_ema, pullback_label = None, None
    for ev, lbl in [(ema20_15,"EMA20"),(ema50_15,"EMA50"),(ema100_15,"EMA100")]:
        if _candle_confirm(df_m15, ev, direction):
            pullback_ema, pullback_label = ev, lbl
            break

    # RSI
    rsi_series = _calc_rsi(df_m15["close"])
    rsi_val    = round(rsi_series.iloc[-2], 1)
    rsi_ok     = rsi_val > 50 if direction == "LONG" else rsi_val < 50

    # Raw results
    raw = {
        "ema_h1":   ((direction == "LONG"  and ema20_h1 > ema50_h1 > ema100_h1) or
                     (direction == "SHORT" and ema20_h1 < ema50_h1 < ema100_h1)),
        "ema_15m":  ((direction == "LONG"  and ema20_15 > ema50_15) or
                     (direction == "SHORT" and ema20_15 < ema50_15)),
        "macd":     ((direction == "LONG"  and (flip_15=="UP"   or flip_h1=="UP")) or
                     (direction == "SHORT" and (flip_15=="DOWN"  or flip_h1=="DOWN"))),
        "rsi":      rsi_ok,
        "candle":   pullback_ema is not None,
        "trend":    _trend_consistent(df_m15, pullback_ema or ema20_15, direction),
        "momentum": _momentum_ok(df_m15, direction),
    }

    # Chỉ tính bộ lọc đang BẬT
    enabled  = {k: v for k, v in raw.items() if active_filters.get(k, True)}
    passed   = [FILTER_LABELS[k] for k, v in enabled.items() if v]
    failed   = [FILTER_LABELS[k] for k, v in enabled.items() if not v]
    n_passed = len(passed)
    n_total  = len(enabled)

    print(f"    📊 [B] {symbol} {direction}: {n_passed}/{n_total} "
          f"(cần {min_pass}) — RSI={rsi_val}")

    if n_passed < min_pass:
        return None

    # Entry/SL/TP
    entry = round(price, 6)
    if direction == "LONG":
        sl = round(min(
            pullback_ema * 0.998 if pullback_ema else entry,
            entry * (1 - SL_PERCENT/100)
        ), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl = round(max(
            pullback_ema * 1.002 if pullback_ema else entry,
            entry * (1 + SL_PERCENT/100)
        ), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

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
        "rsi_val":      rsi_val,
        "passed":       passed,
        "failed":       failed,
        "score":        f"{n_passed}/{n_total}",
    }
