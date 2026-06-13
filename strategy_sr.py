# ============================================================
#  strategy_sr.py — Chiến lược Hỗ trợ Kháng cự
#
#  Logic từ ZoneCandle_v1:
#  ┌─────────────────────────────────────────────────────────┐
#  │  1. Xác định vùng Supply/Demand (Pivot High/Low + ATR) │
#  │  2. Phát hiện mẫu nến đảo chiều trong vùng             │
#  │     - Bull Engulfing, Three Outside Up                  │
#  │     - Bear Engulfing, Three Outside Down                │
#  │  3. Xác nhận bằng Stoch + Volume + giá tăng/giảm       │
#  │                                                         │
#  │  LONG  = Demand active + bull candle + vol + stoch↑    │
#  │  SHORT = Supply active + bear candle + vol + stoch↓    │
#  └─────────────────────────────────────────────────────────┘
# ============================================================
import time
import numpy as np
import pandas as pd

# ── Cooldown state ────────────────────────────────────────────
_last_signal: dict = {}   # symbol -> {direction, ts}
_COOLDOWN = 30 * 60       # 30 phút mặc định

# ── Default params (có thể chỉnh qua Telegram) ───────────────
DEFAULT_PARAMS = {
    "swing_length": 10,      # Pivot lookback
    "box_width":    2.5,     # ATR multiplier cho zone width
    "stoch_k":      14,      # Stoch K period
    "stoch_sm":     3,       # Stoch smooth
    "stoch_d":      3,       # Stoch D period
    "stoch_ob":     80,      # Overbought
    "stoch_os":     20,      # Oversold
    "vol_ma":       20,      # Volume MA period
    "vol_mult":     1.2,     # Volume multiplier
    "wait_bars":    3,       # Bars chờ sau khi vào vùng
    "ma_len":       20,      # EMA length
    "cooldown_min": 30,      # Cooldown giữa 2 lệnh (phút)
}

# State riêng cho từng symbol
_zone_state: dict = {}  # symbol -> {demand_active, supply_active, demand_bars, supply_bars}


def get_params(state: dict) -> dict:
    """Lấy params từ state bot, fallback về default."""
    return state.get("sr_params", DEFAULT_PARAMS.copy())


def get_zone_state(symbol: str) -> dict:
    if symbol not in _zone_state:
        _zone_state[symbol] = {
            "demand_active": False,
            "supply_active": False,
            "demand_bars":   0,
            "supply_bars":   0,
        }
    return _zone_state[symbol]


# ════════════════════════════════════════════════════════════
#  INDICATORS
# ════════════════════════════════════════════════════════════
def _pivot_high(df: pd.DataFrame, length: int):
    highs = df["high"]
    ph = []
    for i in range(length, len(df) - length):
        if highs.iloc[i] == highs.iloc[i-length:i+length+1].max():
            ph.append((i, highs.iloc[i]))
    return ph

def _pivot_low(df: pd.DataFrame, length: int):
    lows = df["low"]
    pl = []
    for i in range(length, len(df) - length):
        if lows.iloc[i] == lows.iloc[i-length:i+length+1].min():
            pl.append((i, lows.iloc[i]))
    return pl

def _atr(df: pd.DataFrame, period: int = 50) -> float:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def _stoch(df: pd.DataFrame, k: int, sm: int, d: int):
    lo = df["low"].rolling(k).min()
    hi = df["high"].rolling(k).max()
    k_raw  = 100 * (df["close"] - lo) / (hi - lo).replace(0, np.nan)
    k_line = k_raw.rolling(sm).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


# ════════════════════════════════════════════════════════════
#  ZONE DETECTION
# ════════════════════════════════════════════════════════════
def _get_zones(df: pd.DataFrame, params: dict):
    """
    Trả về list các vùng Supply và Demand.
    Mỗi zone: {'type': 'supply'/'demand', 'top': float, 'bot': float}
    """
    swing  = params["swing_length"]
    bw     = params["box_width"]
    atr    = _atr(df)
    buf    = atr * (bw / 10)

    ph_list = _pivot_high(df, swing)
    pl_list = _pivot_low(df,  swing)

    zones = []

    for _, val in ph_list[-5:]:   # 5 pivot gần nhất
        top = val
        bot = val - buf
        zones.append({"type": "supply", "top": top, "bot": bot, "mid": (top+bot)/2})

    for _, val in pl_list[-5:]:
        bot = val
        top = val + buf
        zones.append({"type": "demand", "top": top, "bot": bot, "mid": (top+bot)/2})

    return zones


def _price_in_zone(df: pd.DataFrame, zones: list, zone_type: str) -> bool:
    high = df["high"].iloc[-1]
    low  = df["low"].iloc[-1]
    for z in zones:
        if z["type"] != zone_type:
            continue
        if high >= z["bot"] and low <= z["top"]:
            return True
    return False


# ════════════════════════════════════════════════════════════
#  CANDLE PATTERNS
# ════════════════════════════════════════════════════════════
def _bull_engulf(df: pd.DataFrame) -> bool:
    c, o = df["close"], df["open"]
    return (c.iloc[-1] > o.iloc[-1] and
            c.iloc[-2] < o.iloc[-2] and
            c.iloc[-1] > o.iloc[-2] and
            o.iloc[-1] < c.iloc[-2])

def _three_outside_up(df: pd.DataFrame) -> bool:
    c, o = df["close"], df["open"]
    c1 = c.iloc[-3] < o.iloc[-3]                          # nến đỏ
    c2 = c.iloc[-2] > o.iloc[-2]                          # nến xanh nhỏ
    c3 = (c.iloc[-1] > o.iloc[-1] and
          o.iloc[-1] <= o.iloc[-3] and
          c.iloc[-1] >= c.iloc[-2])                        # xanh lớn nuốt cả 2
    return c1 and c2 and c3

def _bear_engulf(df: pd.DataFrame) -> bool:
    c, o = df["close"], df["open"]
    return (c.iloc[-1] < o.iloc[-1] and
            c.iloc[-2] > o.iloc[-2] and
            c.iloc[-1] < o.iloc[-2] and
            o.iloc[-1] > c.iloc[-2])

def _three_outside_down(df: pd.DataFrame) -> bool:
    c, o = df["close"], df["open"]
    c1 = c.iloc[-3] > o.iloc[-3]
    c2 = c.iloc[-2] < o.iloc[-2]
    c3 = (c.iloc[-1] < o.iloc[-1] and
          o.iloc[-1] >= o.iloc[-3] and
          c.iloc[-1] <= c.iloc[-2])
    return c1 and c2 and c3


# ════════════════════════════════════════════════════════════
#  MAIN CHECK
# ════════════════════════════════════════════════════════════
def check_strategy_sr(symbol: str, df: pd.DataFrame, state: dict):
    """
    Trả về dict signal hoặc None.
    df: DataFrame 15m
    """
    params = get_params(state)
    zs     = get_zone_state(symbol)
    wait   = params["wait_bars"]
    cd_min = params["cooldown_min"]

    # Cooldown check
    if symbol in _last_signal:
        elapsed = time.time() - _last_signal[symbol]["ts"]
        if elapsed < cd_min * 60:
            mins_left = int((cd_min * 60 - elapsed) / 60)
            print(f"    ⏳ [SR] {symbol}: cooldown còn {mins_left} phút")
            return None

    # Tính indicators
    price  = df["close"].iloc[-1]
    k_line, d_line = _stoch(df, params["stoch_k"], params["stoch_sm"], params["stoch_d"])
    k_cur, k_prv   = k_line.iloc[-1], k_line.iloc[-2]
    d_cur, d_prv   = d_line.iloc[-1], d_line.iloc[-2]
    vol_ma  = df["volume"].rolling(params["vol_ma"]).mean().iloc[-1]
    vol_ok  = df["volume"].iloc[-1] > vol_ma * params["vol_mult"]
    stoch_long  = k_cur > d_cur and k_prv <= d_prv and k_cur < params["stoch_ob"]
    stoch_short = k_cur < d_cur and k_prv >= d_prv and k_cur > params["stoch_os"]
    bull_candle  = df["close"].iloc[-1] > df["open"].iloc[-1]
    bear_candle  = df["close"].iloc[-1] < df["open"].iloc[-1]
    price_rising  = df["close"].iloc[-1] > df["close"].iloc[-2]
    price_falling = df["close"].iloc[-1] < df["close"].iloc[-2]

    # Zones
    zones      = _get_zones(df, params)
    in_demand  = _price_in_zone(df, zones, "demand")
    in_supply  = _price_in_zone(df, zones, "supply")

    # Cập nhật zone active state
    if in_demand:
        zs["demand_active"] = True
        zs["demand_bars"]   = 0
    elif zs["demand_active"]:
        zs["demand_bars"] += 1
        if zs["demand_bars"] > wait:
            zs["demand_active"] = False
            zs["demand_bars"]   = 0

    if in_supply:
        zs["supply_active"] = True
        zs["supply_bars"]   = 0
    elif zs["supply_active"]:
        zs["supply_bars"] += 1
        if zs["supply_bars"] > wait:
            zs["supply_active"] = False
            zs["supply_bars"]   = 0

    # Mẫu nến
    bull_pat = _bull_engulf(df) or _three_outside_up(df)
    bear_pat = _bear_engulf(df) or _three_outside_down(df)

    # Signal
    long_signal  = zs["demand_active"] and bull_candle and vol_ok and stoch_long and price_rising
    short_signal = zs["supply_active"] and bear_candle and vol_ok and stoch_short and price_falling

    print(f"    — [SR] {symbol}: ${price:.4f} | demand={zs['demand_active']} supply={zs['supply_active']} | k={k_cur:.1f} vol={'✓' if vol_ok else '✗'}")

    if long_signal or short_signal:
        direction = "LONG" if long_signal else "SHORT"
        pattern   = "Bull Engulfing" if _bull_engulf(df) else "Three Outside Up" if _three_outside_up(df) else "Bear Engulfing" if _bear_engulf(df) else "Three Outside Down" if _three_outside_down(df) else "—"
        _last_signal[symbol] = {"direction": direction, "ts": time.time()}
        return {
            "type":    direction,
            "price":   round(price, 4),
            "k_line":  round(k_cur, 1),
            "d_line":  round(d_cur, 1),
            "vol_pct": round(df["volume"].iloc[-1] / vol_ma * 100, 0),
            "pattern": pattern,
            "in_demand": in_demand,
            "in_supply": in_supply,
        }

    return None