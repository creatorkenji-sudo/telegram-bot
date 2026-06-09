# ============================================================
#  strategy_d.py — Chiến lược D: Ichimoku + Stochastic
#
#  Logic (theo Pine Script IchiStoch v1):
#  ┌─────────────────────────────────────────────────────────┐
#  │  H1 Ichimoku xác nhận trend                            │
#  │    BULL: giá > Kumo + Tenkan > Kijun                   │
#  │    BEAR: giá < Kumo + Tenkan < Kijun                   │
#  │                                                         │
#  │  H1 Stoch entry:                                        │
#  │    LONG : %K vượt 50 từ dưới lên HOẶC >50 đang tăng   │
#  │    SHORT: %K xuống 50 từ trên HOẶC <50 đang giảm       │
#  │                                                         │
#  │  15m Stoch entry:                                       │
#  │    LONG : %K thoát lên trên 50                         │
#  │    SHORT: %K thoát xuống 80 + cắt %D                   │
#  │           HOẶC %K cắt xuống %D trong vùng 50-80        │
#  │                                                         │
#  │  Cảnh báo sớm ⚡ : H1 + 15m đủ điều kiện              │
#  │  Xác nhận 🚀    : nến sau cảnh báo đóng đúng chiều     │
#  │                                                         │
#  │  SL: swing low/high gần nhất (10 nến)                  │
#  │  TP: R:R 1:3                                            │
#  └─────────────────────────────────────────────────────────┘
# ============================================================

import time
import pandas as pd
import numpy as np
from config import SL_PERCENT, RR_RATIO

COOLDOWN_SECONDS = 30 * 60   # 30 phút
SWING_BARS       = 10        # swing lookback

# ── Cooldown state ────────────────────────────────────────────
_last_signal: dict = {}   # symbol -> {direction, ts, early_sent}


def _in_cooldown(symbol):
    if symbol not in _last_signal:
        return False, 0
    remaining = COOLDOWN_SECONDS - (time.time() - _last_signal[symbol]["ts"])
    return (True, int(remaining // 60)) if remaining > 0 else (False, 0)


def _set_cooldown(symbol, direction, early=False):
    if symbol not in _last_signal or not early:
        _last_signal[symbol] = {"direction": direction, "ts": time.time(), "early_sent": early}
    else:
        _last_signal[symbol]["early_sent"] = early


def _last_direction(symbol):
    return _last_signal.get(symbol, {}).get("direction")


def _early_sent(symbol):
    return _last_signal.get(symbol, {}).get("early_sent", False)


# ════════════════════════════════════════════════════════════
#  ICHIMOKU
# ════════════════════════════════════════════════════════════
def _ichimoku(df, tenkan=9, kijun=26, senkou_b=52):
    hi, lo = df["high"], df["low"]
    tenkan_s  = (hi.rolling(tenkan).max()   + lo.rolling(tenkan).min())   / 2
    kijun_s   = (hi.rolling(kijun).max()    + lo.rolling(kijun).min())    / 2
    senkou_a  = ((tenkan_s + kijun_s) / 2).shift(kijun)
    senkou_b_ = ((hi.rolling(senkou_b).max() + lo.rolling(senkou_b).min()) / 2).shift(kijun)
    chikou    = df["close"].shift(-kijun)
    return tenkan_s, kijun_s, senkou_a, senkou_b_, chikou


def _ichi_trend(df):
    """
    Trả về: 'BULL' | 'BEAR' | 'SIDE'
    Điều kiện: giá > Kumo + Tenkan > Kijun (BULL) / ngược lại (BEAR)
    """
    tenkan, kijun, sa, sb, _ = _ichimoku(df)
    price    = df["close"].iloc[-1]
    ktop     = max(sa.iloc[-1], sb.iloc[-1])
    kbot     = min(sa.iloc[-1], sb.iloc[-1])
    tk_cur   = tenkan.iloc[-1]
    ki_cur   = kijun.iloc[-1]

    if price > ktop and tk_cur > ki_cur:
        return "BULL", ktop, kbot, tk_cur, ki_cur
    if price < kbot and tk_cur < ki_cur:
        return "BEAR", ktop, kbot, tk_cur, ki_cur
    return "SIDE", ktop, kbot, tk_cur, ki_cur


# ════════════════════════════════════════════════════════════
#  STOCHASTIC
# ════════════════════════════════════════════════════════════
def _stoch(df, k=14, sm=3, d=3):
    lo_k   = df["low"].rolling(k).min()
    hi_k   = df["high"].rolling(k).max()
    k_raw  = 100 * (df["close"] - lo_k) / (hi_k - lo_k).replace(0, np.nan)
    k_line = k_raw.rolling(sm).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line


def _h1_stoch_long(k, k_prev, mid=50):
    """H1 LONG: %K vượt 50 từ dưới HOẶC >50 đang tăng."""
    cross_up   = k > mid and k_prev <= mid
    above_up   = k > mid and k > k_prev
    return cross_up or above_up


def _h1_stoch_short(k, k_prev, mid=50):
    """H1 SHORT: %K xuống 50 từ trên HOẶC <50 đang giảm."""
    cross_dn   = k < mid and k_prev >= mid
    below_dn   = k < mid and k < k_prev
    return cross_dn or below_dn


def _m15_stoch_long(k, k_prev, mid=50):
    """15m LONG: %K thoát lên trên 50."""
    return k > mid and k_prev <= mid


def _m15_stoch_short(k, k_prev, d, d_prev, ob=80, mid=50):
    """15m SHORT: thoát xuống 80+cắt %D HOẶC cắt %D trong 50-80."""
    cond_a = k < ob  and k_prev >= ob  and k < d
    cond_b = k < d   and k_prev >= d_prev and k > mid and k < ob
    return cond_a or cond_b


# ════════════════════════════════════════════════════════════
#  SL / TP
# ════════════════════════════════════════════════════════════
def _calc_sl_tp(price, direction, swing_low, swing_high):
    if direction == "LONG":
        sl = round(min(swing_low, price * (1 - SL_PERCENT / 100)), 6)
        tp = round(price + (price - sl) * RR_RATIO, 6)
    else:
        sl = round(max(swing_high, price * (1 + SL_PERCENT / 100)), 6)
        tp = round(price - (sl - price) * RR_RATIO, 6)
    sl_pct = abs(round((sl - price) / price * 100, 2))
    tp_pct = abs(round((tp - price) / price * 100, 2))
    return sl, tp, sl_pct, tp_pct


# ════════════════════════════════════════════════════════════
#  MAIN CHECK
# ════════════════════════════════════════════════════════════
def check_strategy_d(symbol: str, df_h1: pd.DataFrame, df_m15: pd.DataFrame):
    """
    Trả về dict hoặc None.
    dict có key:
      signal_type: 'early' | 'confirm'
      type:        'LONG' | 'SHORT'
      entry, sl, tp, sl_pct, tp_pct
      h1_trend, h1_k, m15_k, stoch_reason
    """
    # Cooldown
    in_cd, mins_left = _in_cooldown(symbol)
    if in_cd and _early_sent(symbol):
        print(f"    ⏳ [D] {symbol}: cooldown còn {mins_left} phút")
        return None

    # ── H1 Ichimoku + Stoch ──────────────────────────────────
    h1_trend, h1_ktop, h1_kbot, h1_tk, h1_ki = _ichi_trend(df_h1)
    if h1_trend == "SIDE":
        print(f"    ⏭  [D] {symbol}: H1 SIDE — bỏ qua")
        return None

    h1_k_s, h1_d_s = _stoch(df_h1)
    h1_k     = h1_k_s.iloc[-1]
    h1_k_p   = h1_k_s.iloc[-2]

    # ── 15m Stoch ────────────────────────────────────────────
    m15_k_s, m15_d_s = _stoch(df_m15)
    m15_k    = m15_k_s.iloc[-1]
    m15_k_p  = m15_k_s.iloc[-2]
    m15_d    = m15_d_s.iloc[-1]
    m15_d_p  = m15_d_s.iloc[-2]
    price    = df_m15["close"].iloc[-1]

    # Swing SL
    sw_low  = df_m15["low"].iloc[-SWING_BARS:].min()
    sw_high = df_m15["high"].iloc[-SWING_BARS:].max()

    # ── Xác định tín hiệu ────────────────────────────────────
    direction = None
    stoch_reason = ""

    if h1_trend == "BULL":
        h1_ok  = _h1_stoch_long(h1_k, h1_k_p)
        m15_ok = _m15_stoch_long(m15_k, m15_k_p)
        if h1_ok and m15_ok:
            direction    = "LONG"
            stoch_reason = f"H1 Stoch {'vượt 50' if h1_k > 50 and h1_k_p <= 50 else '>50 tăng'} · 15m %K thoát 50"

    elif h1_trend == "BEAR":
        h1_ok  = _h1_stoch_short(h1_k, h1_k_p)
        m15_ok = _m15_stoch_short(m15_k, m15_k_p, m15_d, m15_d_p)
        if h1_ok and m15_ok:
            direction    = "SHORT"
            stoch_reason = f"H1 Stoch {'xuống 50' if h1_k < 50 and h1_k_p >= 50 else '<50 giảm'} · 15m cắt xuống"

    if not direction:
        print(f"    —  [D] {symbol}: H1={h1_trend} h1_k={h1_k:.1f} m15_k={m15_k:.1f} | chưa có setup")
        return None

    # ── Cảnh báo sớm (early) ─────────────────────────────────
    if not _early_sent(symbol) or _last_direction(symbol) != direction:
        sl, tp, sl_pct, tp_pct = _calc_sl_tp(price, direction, sw_low, sw_high)
        _set_cooldown(symbol, direction, early=True)
        print(f"    ⚡ [D] {symbol}: {direction} early — ${price:.4f}")
        return {
            "signal_type": "early",
            "type":        direction,
            "entry":       round(price, 6),
            "sl":          sl,
            "tp":          tp,
            "sl_pct":      sl_pct,
            "tp_pct":      tp_pct,
            "h1_trend":    h1_trend,
            "h1_k":        round(h1_k, 1),
            "m15_k":       round(m15_k, 1),
            "h1_tenkan":   round(h1_tk, 4),
            "h1_kijun":    round(h1_ki, 4),
            "stoch_reason":stoch_reason,
        }

    # ── Xác nhận (nến đóng đúng chiều sau early) ─────────────
    prev_close = df_m15["close"].iloc[-2]
    prev_open  = df_m15["open"].iloc[-2]
    confirm_long  = direction == "LONG"  and prev_close > prev_open
    confirm_short = direction == "SHORT" and prev_close < prev_open

    if confirm_long or confirm_short:
        sl, tp, sl_pct, tp_pct = _calc_sl_tp(price, direction, sw_low, sw_high)
        _set_cooldown(symbol, direction, early=False)
        print(f"    🚀 [D] {symbol}: {direction} confirm — ${price:.4f}")
        return {
            "signal_type": "confirm",
            "type":        direction,
            "entry":       round(price, 6),
            "sl":          sl,
            "tp":          tp,
            "sl_pct":      sl_pct,
            "tp_pct":      tp_pct,
            "h1_trend":    h1_trend,
            "h1_k":        round(h1_k, 1),
            "m15_k":       round(m15_k, 1),
            "h1_tenkan":   round(h1_tk, 4),
            "h1_kijun":    round(h1_ki, 4),
            "stoch_reason":stoch_reason,
        }

    print(f"    ⏳ [D] {symbol}: early đã gửi, chờ nến xác nhận...")
    return None
