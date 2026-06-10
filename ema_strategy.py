# ============================================================
#  ema_strategy.py — Chiến lược B nâng cấp
#
#  Cơ chế theo dõi SL/TP:
#  1. Báo entry 1 lần → lưu trạng thái IN_TRADE
#  2. Mỗi vòng lặp kiểm tra giá hiện tại vs SL/TP
#  3. Nếu chạm SL → báo "Cắt lỗ" → reset → tìm lệnh mới
#  4. Nếu chạm TP → báo "Chốt lời" → reset → tìm lệnh mới
#  5. Timeout 8 giờ → reset
# ============================================================
import time
import pandas as pd
import numpy as np
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO

COOLDOWN_SECONDS  = 30 * 60    # 30 phút cooldown sau reset
MACD_MIN_FLIP     = 0.0001
TREND_CONSISTENCY = 3
TIMEOUT_SECONDS   = 2 * 3600  # 2 giờ timeout

# ── Trade state per symbol — lưu file để persist qua restart ──
import json, os

TRADE_FILE = "/tmp/ema_trades.json"

def _load_trades() -> dict:
    try:
        if os.path.exists(TRADE_FILE):
            with open(TRADE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_trades(trades: dict):
    try:
        with open(TRADE_FILE, "w") as f:
            json.dump(trades, f)
    except Exception as e:
        print(f"  ⚠️  Save trades lỗi: {e}")

# Load từ file khi khởi động
_trades: dict = _load_trades()


def get_trade_state(symbol: str) -> dict:
    if symbol not in _trades:
        _trades[symbol] = {
            "status":      "IDLE",
            "direction":   None,
            "entry":       None,
            "sl":          None,
            "tp":          None,
            "ts_entry":    None,
            "ts_cooldown": None,
        }
    return _trades[symbol]


def _in_cooldown(symbol: str) -> tuple[bool, int]:
    t = get_trade_state(symbol)
    if t["ts_cooldown"] is None:
        return False, 0
    remaining = COOLDOWN_SECONDS - (time.time() - t["ts_cooldown"])
    return (True, int(remaining // 60)) if remaining > 0 else (False, 0)


def _set_trade(symbol: str, direction: str, entry: float, sl: float, tp: float):
    t = get_trade_state(symbol)
    t["status"]    = "IN_TRADE"
    t["direction"] = direction
    t["entry"]     = entry
    t["sl"]        = sl
    t["tp"]        = tp
    t["ts_entry"]  = time.time()
    _save_trades(_trades)


def _reset_trade(symbol: str):
    t = get_trade_state(symbol)
    t["status"]      = "IDLE"
    t["direction"]   = None
    t["entry"]       = None
    t["sl"]          = None
    t["tp"]          = None
    t["ts_entry"]    = None
    t["ts_cooldown"] = time.time()
    _save_trades(_trades)


# ── Check SL/TP/Timeout ───────────────────────────────────────
def check_sltp(symbol: str, current_price: float) -> dict | None:
    """
    Kiểm tra lệnh đang mở.
    Trả về dict kết quả hoặc None nếu chưa chạm.
    """
    t = get_trade_state(symbol)
    if t["status"] != "IN_TRADE":
        return None

    direction = t["direction"]
    entry     = t["entry"]
    sl        = t["sl"]
    tp        = t["tp"]
    elapsed   = time.time() - t["ts_entry"]

    # Timeout 8 giờ
    if elapsed >= TIMEOUT_SECONDS:
        result = {
            "type":       "TIMEOUT",
            "direction":  direction,
            "entry":      entry,
            "sl":         sl,
            "tp":         tp,
            "exit_price": current_price,
            "pnl_pct":    round((current_price - entry) / entry * 100 * (1 if direction == "LONG" else -1), 2),
            "hours":      round(elapsed / 3600, 1),
        }
        _reset_trade(symbol)
        return result

    # Chạm TP
    if direction == "LONG"  and current_price >= tp:
        result = {"type": "TP", "direction": direction, "entry": entry, "sl": sl, "tp": tp, "exit_price": current_price, "pnl_pct": round((tp - entry) / entry * 100, 2)}
        _reset_trade(symbol)
        return result
    if direction == "SHORT" and current_price <= tp:
        result = {"type": "TP", "direction": direction, "entry": entry, "sl": sl, "tp": tp, "exit_price": current_price, "pnl_pct": round((entry - tp) / entry * 100, 2)}
        _reset_trade(symbol)
        return result

    # Chạm SL
    if direction == "LONG"  and current_price <= sl:
        result = {"type": "SL", "direction": direction, "entry": entry, "sl": sl, "tp": tp, "exit_price": current_price, "pnl_pct": round((sl - entry) / entry * 100, 2)}
        _reset_trade(symbol)
        return result
    if direction == "SHORT" and current_price >= sl:
        result = {"type": "SL", "direction": direction, "entry": entry, "sl": sl, "tp": tp, "exit_price": current_price, "pnl_pct": round((entry - sl) / entry * 100, 2)}
        _reset_trade(symbol)
        return result

    return None


# ════════════════════════════════════════════════════════════
#  INDICATORS
# ════════════════════════════════════════════════════════════
def _calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


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
    return all(c > ema_val for c in closes) if direction == "LONG" else all(c < ema_val for c in closes)


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
    ok   = (curr["close"] > curr["open"] and cb >= pb * 0.7) if direction == "LONG" else (curr["close"] < curr["open"] and cb >= pb * 0.7)
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


# ════════════════════════════════════════════════════════════
#  MAIN CHECK
# ════════════════════════════════════════════════════════════
def check_ema_signal(symbol: str, df_h1: pd.DataFrame, df_m15: pd.DataFrame,
                     active_filters: dict, min_pass: int) -> dict | None:
    """
    Trả về None nếu đang IN_TRADE hoặc cooldown.
    Trả về dict tín hiệu mới nếu đủ điều kiện.
    """
    t = get_trade_state(symbol)

    # Đang có lệnh → không tìm lệnh mới
    if t["status"] == "IN_TRADE":
        elapsed = round((time.time() - t["ts_entry"]) / 3600, 1)
        print(f"    🔒 [B] {symbol}: IN_TRADE {t['direction']} entry={t['entry']} ({elapsed}h / 8h)")
        return None

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

    enabled  = {k: v for k, v in raw.items() if active_filters.get(k, True)}
    passed   = [FILTER_LABELS[k] for k, v in enabled.items() if v]
    failed   = [FILTER_LABELS[k] for k, v in enabled.items() if not v]
    n_passed = len(passed)
    n_total  = len(enabled)

    print(f"    📊 [B] {symbol} {direction}: {n_passed}/{n_total} (cần {min_pass}) RSI={rsi_val}")

    if n_passed < min_pass:
        return None

    # Entry / SL / TP
    entry = round(price, 6)
    if direction == "LONG":
        sl_base = pullback_ema * 0.998 if pullback_ema else entry * (1 - SL_PERCENT/100)
        sl = round(min(sl_base, entry * (1 - SL_PERCENT/100)), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl_base = pullback_ema * 1.002 if pullback_ema else entry * (1 + SL_PERCENT/100)
        sl = round(max(sl_base, entry * (1 + SL_PERCENT/100)), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    # Lưu trạng thái IN_TRADE
    _set_trade(symbol, direction, entry, sl, tp)

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