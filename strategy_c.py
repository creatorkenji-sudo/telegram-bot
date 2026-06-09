# ============================================================
#  strategy_c.py — Chiến lược C: Supertrend + Confirmation động
#
#  Kiến trúc DIY Builder:
#  ┌─────────────────────────────────────────────────┐
#  │  Leading: Supertrend H1                         │
#  │  Confirmation: bật/tắt qua Telegram             │
#  │    - QQE Mod                                    │
#  │    - Choppiness Index (lọc sideway)             │
#  │    - ADX (xác nhận trend mạnh)                  │
#  │    - SSL Channel                                │
#  │    - EMA Filter                                 │
#  │    - Volume                                     │
#  │    - Stochastic                                 │
#  │  Cần: tất cả confirmation BẬT phải pass         │
#  │  + Signal Expiry: chờ tối đa 3 nến              │
#  └─────────────────────────────────────────────────┘
# ============================================================

import pandas as pd
import numpy as np
from indicators import calc_emas, calc_macd
from config import SL_PERCENT, RR_RATIO

# ── Trạng thái Signal Expiry ─────────────────────────────────
# Lưu tín hiệu pending chờ confirmation
_pending: dict[str, dict] = {}   # symbol -> {direction, candles_left}
SIGNAL_EXPIRY = 3                # chờ tối đa 3 nến


# ════════════════════════════════════════════════════════════
#  LEADING INDICATOR — Supertrend
# ════════════════════════════════════════════════════════════
def calc_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """
    Tính Supertrend.
    Trả về Series: 1 = uptrend, -1 = downtrend
    """
    hl2   = (df["high"] + df["low"]) / 2
    atr   = df["high"].combine(df["low"], max) - df["high"].combine(df["low"], min)
    # ATR đơn giản
    atr   = atr.ewm(span=period, adjust=False).mean()

    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    trend    = pd.Series(index=df.index, dtype=float)
    st_upper = pd.Series(index=df.index, dtype=float)
    st_lower = pd.Series(index=df.index, dtype=float)

    for i in range(1, len(df)):
        # Lower band
        if lower.iloc[i] > st_lower.iloc[i-1] or df["close"].iloc[i-1] < st_lower.iloc[i-1]:
            st_lower.iloc[i] = lower.iloc[i]
        else:
            st_lower.iloc[i] = st_lower.iloc[i-1]

        # Upper band
        if upper.iloc[i] < st_upper.iloc[i-1] or df["close"].iloc[i-1] > st_upper.iloc[i-1]:
            st_upper.iloc[i] = upper.iloc[i]
        else:
            st_upper.iloc[i] = st_upper.iloc[i-1]

        # Trend direction
        prev_trend = trend.iloc[i-1] if not pd.isna(trend.iloc[i-1]) else 1
        if prev_trend == -1 and df["close"].iloc[i] > st_upper.iloc[i]:
            trend.iloc[i] = 1
        elif prev_trend == 1 and df["close"].iloc[i] < st_lower.iloc[i]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = prev_trend

    # Supertrend line value
    st_line = pd.Series(index=df.index, dtype=float)
    for i in range(1, len(df)):
        st_line.iloc[i] = st_lower.iloc[i] if trend.iloc[i] == 1 else st_upper.iloc[i]

    return trend, st_line


def get_supertrend_signal(df: pd.DataFrame) -> str | None:
    """
    Phát hiện Supertrend vừa đổi chiều (leading signal).
    Trả về: 'LONG' | 'SHORT' | None
    """
    trend, _ = calc_supertrend(df)
    curr = trend.iloc[-1]
    prev = trend.iloc[-2]

    if prev == -1 and curr == 1:
        return "LONG"
    if prev == 1  and curr == -1:
        return "SHORT"
    return None


# ════════════════════════════════════════════════════════════
#  CONFIRMATION INDICATORS
# ════════════════════════════════════════════════════════════

def confirm_qqe(df: pd.DataFrame, direction: str,
                rsi_period: int = 14, sf: int = 5) -> bool:
    """
    QQE Mod đơn giản: RSI smoothed + trailing stop.
    LONG: QQE line > 50
    SHORT: QQE line < 50
    """
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0).ewm(com=rsi_period-1, adjust=False).mean()
    loss     = (-delta.clip(upper=0)).ewm(com=rsi_period-1, adjust=False).mean()
    rs       = gain / loss.replace(0, np.nan)
    rsi      = 100 - (100 / (1 + rs))
    qqe_line = rsi.ewm(span=sf, adjust=False).mean()
    val      = qqe_line.iloc[-1]

    if direction == "LONG":
        return val > 50
    return val < 50


def confirm_choppiness(df: pd.DataFrame, period: int = 14,
                       threshold: float = 61.8) -> bool:
    """
    Choppiness Index < threshold → thị trường đang trending → cho phép trade.
    CI >= threshold → sideway → lọc bỏ.
    """
    highest = df["high"].rolling(period).max()
    lowest  = df["low"].rolling(period).min()
    atr_sum = (df["high"] - df["low"]).rolling(period).sum()
    ci = 100 * np.log10(atr_sum / (highest - lowest).replace(0, np.nan)) / np.log10(period)
    return ci.iloc[-1] < threshold


def confirm_adx(df: pd.DataFrame, direction: str,
                period: int = 14, threshold: float = 25.0) -> bool:
    """
    ADX > threshold → trend đủ mạnh.
    +DI > -DI cho LONG, -DI > +DI cho SHORT.
    """
    high, low, close = df["high"], df["low"], df["close"]
    tr   = pd.concat([high - low,
                      (high - close.shift()).abs(),
                      (low  - close.shift()).abs()], axis=1).max(axis=1)
    atr  = tr.ewm(span=period, adjust=False).mean()

    dm_p = (high.diff()).clip(lower=0)
    dm_m = (-low.diff()).clip(lower=0)
    dm_p = dm_p.where(dm_p > dm_m, 0)
    dm_m = dm_m.where(dm_m > dm_p, 0)

    di_p = 100 * dm_p.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)
    di_m = 100 * dm_m.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan)
    dx   = 100 * (di_p - di_m).abs() / (di_p + di_m).replace(0, np.nan)
    adx  = dx.ewm(span=period, adjust=False).mean()

    adx_ok = adx.iloc[-1] > threshold
    if direction == "LONG":
        return adx_ok and di_p.iloc[-1] > di_m.iloc[-1]
    return adx_ok and di_m.iloc[-1] > di_p.iloc[-1]


def confirm_ssl(df: pd.DataFrame, direction: str, period: int = 10) -> bool:
    """
    SSL Channel:
    LONG:  close > SSL upper (high MA)
    SHORT: close < SSL lower (low MA)
    """
    ssl_high = df["high"].rolling(period).mean()
    ssl_low  = df["low"].rolling(period).mean()
    price    = df["close"].iloc[-1]

    if direction == "LONG":
        return price > ssl_high.iloc[-1]
    return price < ssl_low.iloc[-1]


def confirm_ema_filter(df: pd.DataFrame, direction: str,
                       period: int = 200) -> bool:
    """
    EMA Filter: price above EMA → LONG, below → SHORT.
    """
    ema_val = df["close"].ewm(span=period, adjust=False).mean().iloc[-1]
    price   = df["close"].iloc[-1]
    if direction == "LONG":
        return price > ema_val
    return price < ema_val


def confirm_volume(df: pd.DataFrame, period: int = 20,
                   multiplier: float = 1.1) -> bool:
    """Volume nến hiện tại > trung bình × multiplier."""
    avg = df["volume"].iloc[-period-1:-1].mean()
    return df["volume"].iloc[-1] > avg * multiplier


def confirm_stochastic(df: pd.DataFrame, direction: str,
                       k_period: int = 14, d_period: int = 3) -> bool:
    """
    Stochastic %K cross %D:
    LONG:  %K vừa cắt lên %D và %K < 80
    SHORT: %K vừa cắt xuống %D và %K > 20
    """
    lowest  = df["low"].rolling(k_period).min()
    highest = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - lowest) / (highest - lowest).replace(0, np.nan)
    d = k.rolling(d_period).mean()

    k_curr, k_prev = k.iloc[-1], k.iloc[-2]
    d_curr, d_prev = d.iloc[-1], d.iloc[-2]

    if direction == "LONG":
        return k_prev < d_prev and k_curr > d_curr and k_curr < 80
    return k_prev > d_prev and k_curr < d_curr and k_curr > 20


# ── Map tên → hàm ────────────────────────────────────────────
CONFIRMATION_MAP = {
    "qqe":        confirm_qqe,
    "choppiness": confirm_choppiness,
    "adx":        confirm_adx,
    "ssl":        confirm_ssl,
    "ema_filter": confirm_ema_filter,
    "volume":     confirm_volume,
    "stochastic": confirm_stochastic,
}

# Tên hiển thị đẹp
CONFIRMATION_LABELS = {
    "qqe":        "QQE Mod (RSI > 50)",
    "choppiness": "Choppiness Index (lọc sideway)",
    "adx":        "ADX (trend mạnh > 25)",
    "ssl":        "SSL Channel",
    "ema_filter": "EMA Filter (200)",
    "volume":     "Volume tăng",
    "stochastic": "Stochastic Cross",
}

# Confirmation không cần direction (chỉ lọc chung)
NO_DIRECTION_CONFIRMS = {"choppiness", "volume"}


# ════════════════════════════════════════════════════════════
#  MAIN CHECK
# ════════════════════════════════════════════════════════════
def check_strategy_c(symbol: str, df_h1: pd.DataFrame,
                     active_confirms: list[str]) -> dict | None:
    """
    Kiểm tra chiến lược C cho 1 coin.
    active_confirms: danh sách tên confirmation đang BẬT
    """
    # ── 1. Leading: Supertrend H1 ────────────────────────────
    new_signal = get_supertrend_signal(df_h1)

    # Cập nhật pending signal
    if new_signal:
        _pending[symbol] = {
            "direction":    new_signal,
            "candles_left": SIGNAL_EXPIRY,
        }
        print(f"    🔔 [C] {symbol}: Supertrend {new_signal} — chờ confirmation ({SIGNAL_EXPIRY} nến)")

    pending = _pending.get(symbol)
    if not pending or pending["candles_left"] <= 0:
        if symbol in _pending:
            del _pending[symbol]
        return None

    direction = pending["direction"]
    pending["candles_left"] -= 1

    # ── 2. Confirmation indicators ───────────────────────────
    if not active_confirms:
        # Không có confirmation → dùng Supertrend thuần
        results = {}
        passed  = []
        failed  = []
    else:
        results = {}
        for name in active_confirms:
            fn = CONFIRMATION_MAP.get(name)
            if not fn:
                continue
            try:
                if name in NO_DIRECTION_CONFIRMS:
                    ok = fn(df_h1)
                else:
                    ok = fn(df_h1, direction)
                results[name] = ok
            except Exception as e:
                print(f"    ⚠️  [C] {symbol} confirm {name} lỗi: {e}")
                results[name] = False

        passed = [CONFIRMATION_LABELS.get(k, k) for k, v in results.items() if v]
        failed = [CONFIRMATION_LABELS.get(k, k) for k, v in results.items() if not v]

        # Tất cả confirmation bật phải pass
        if failed:
            print(f"    ⏭  [C] {symbol}: {direction} — failed: {failed}")
            return None

    # ── 3. Signal confirmed! Tính Entry/SL/TP ────────────────
    # Lấy Supertrend line làm cơ sở SL
    trend, st_line = calc_supertrend(df_h1)
    price    = df_h1["close"].iloc[-1]
    st_val   = st_line.iloc[-1]
    entry    = round(price, 6)

    if direction == "LONG":
        sl = round(min(st_val * 0.998,
                       entry * (1 - SL_PERCENT / 100)), 6)
        tp = round(entry + (entry - sl) * RR_RATIO, 6)
    else:
        sl = round(max(st_val * 1.002,
                       entry * (1 + SL_PERCENT / 100)), 6)
        tp = round(entry - (sl - entry) * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    # Xóa pending sau khi xác nhận
    del _pending[symbol]

    return {
        "type":       direction,
        "entry":      entry,
        "sl":         sl,
        "tp":         tp,
        "sl_pct":     sl_pct,
        "tp_pct":     tp_pct,
        "st_val":     round(st_val, 4),
        "confirms":   active_confirms,
        "passed":     passed,
        "score":      f"{len(passed)}/{len(active_confirms)}" if active_confirms else "Supertrend only",
    }
