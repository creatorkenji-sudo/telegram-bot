# ============================================================
#  strategy_sr.py — Chiến lược Hỗ trợ Kháng cự (ZoneCandle v1)
#
#  Đồng bộ logic với Pine Script "Zone Candle v1" trên TradingView
#
#  Signal 1: LONG/SHORT Zone     — chạy trên H1 + H4
#  Signal 2: BOS Pullback        — chạy trên M15 + H1
#  Signal 3: TOUCH/BREAK/REJECT  — chạy trên H1 + H4 (mặc định BẬT)
#  Signal 4: MA20/EMA200 Cross   — chạy độc lập trên M15, H1, H4
# ============================================================
import time
import numpy as np
import pandas as pd

# ── Cooldown ──────────────────────────────────────────────────
_last_signal: dict = {}

# ── Default params (khớp Pine Script) ─────────────────────────
DEFAULT_PARAMS = {
    "swing_length": 10,
    "box_width":    2.5,
    "history":      20,
    "filter_zone":  True,
    "min_atr":      1.5,
    "stoch_k":      14,
    "stoch_sm":     3,
    "stoch_d":      3,
    "stoch_ob":     80,       # Pine: 80 (was 70)
    "stoch_os":     20,       # Pine: 20 (was 30)
    "vol_ma":       20,
    "vol_mult":     1.2,
    "wait_bars":    3,
    "ma_len":       20,
    "ema200_len":   200,
    "ma_buf_pct":   0.3,
    "bos_wait":     20,
    "cooldown_min": 30,
    "touch_signal": True,
}

# ── State riêng theo symbol+suffix khung ──────────────────────
_zone_state: dict = {}
_bos_state:  dict = {}
_ma_cross_state: dict = {}


def get_params(state: dict) -> dict:
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


def get_bos_state(symbol: str) -> dict:
    if symbol not in _bos_state:
        _bos_state[symbol] = {
            "bos_up":     False,
            "ma_touched": False,
            "bos_bars":   0,
            "touched_zones": {},
            "initialized":   False,
        }
    return _bos_state[symbol]


def get_ma_cross_state(symbol: str) -> dict:
    if symbol not in _ma_cross_state:
        _ma_cross_state[symbol] = {"initialized": False}
    return _ma_cross_state[symbol]


# ════════════════════════════════════════════════════════════
#  INDICATORS
# ════════════════════════════════════════════════════════════
def _atr(df: pd.DataFrame, period: int = 50) -> float:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _stoch(df: pd.DataFrame, k: int, sm: int, d: int):
    lo = df["low"].rolling(k).min()
    hi = df["high"].rolling(k).max()
    k_raw  = 100 * (df["close"] - lo) / (hi - lo).replace(0, np.nan)
    k_line = k_raw.rolling(sm).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line


def _pivot_high(df: pd.DataFrame, length: int):
    highs = df["high"]
    ph = []
    for i in range(length, len(df) - length):
        if highs.iloc[i] == highs.iloc[i-length:i+length+1].max():
            ph.append(highs.iloc[i])
    return ph


def _pivot_low(df: pd.DataFrame, length: int):
    lows = df["low"]
    pl = []
    for i in range(length, len(df) - length):
        if lows.iloc[i] == lows.iloc[i-length:i+length+1].min():
            pl.append(lows.iloc[i])
    return pl


# ════════════════════════════════════════════════════════════
#  ZONE DETECTION — khớp Pine Script f_overlap + f_draw_zone
#  KHÔNG merge zone — chỉ skip zone mới nếu trùng zone cũ
# ════════════════════════════════════════════════════════════
def _overlap(mid: float, existing_zones: list, atr: float) -> bool:
    for z in existing_zones:
        if mid >= z["mid"] - atr * 2 and mid <= z["mid"] + atr * 2:
            return True
    return False


def _get_zones(df: pd.DataFrame, params: dict):
    swing  = params["swing_length"]
    bw     = params["box_width"]
    atr    = _atr(df)
    buf    = atr * (bw / 10)
    history    = params.get("history", 20)
    filter_on  = params.get("filter_zone", True)
    min_atr    = params.get("min_atr", 1.5)

    ph_list = _pivot_high(df, swing)[-(history):]
    pl_list = _pivot_low(df,  swing)[-(history):]

    # Supply zones — overlap skip (như Pine f_overlap)
    sup_zones = []
    for idx, v in enumerate(ph_list):
        if filter_on and idx > 0:
            if abs(v - ph_list[idx - 1]) < atr * min_atr:
                continue
        mid = v - buf / 2
        if not _overlap(mid, sup_zones, atr):
            sup_zones.append({"type": "supply", "top": v, "bot": v - buf, "mid": mid})

    # Demand zones — overlap skip
    dem_zones = []
    for idx, v in enumerate(pl_list):
        if filter_on and idx > 0:
            if abs(v - pl_list[idx - 1]) < atr * min_atr:
                continue
        mid = v + buf / 2
        if not _overlap(mid, dem_zones, atr):
            dem_zones.append({"type": "demand", "top": v + buf, "bot": v, "mid": mid})

    return sup_zones + dem_zones, atr


def _price_in_zone(df: pd.DataFrame, zones: list, zone_type: str) -> list:
    high = df["high"].iloc[-1]
    low  = df["low"].iloc[-1]
    matched = []
    for z in zones:
        if z["type"] != zone_type:
            continue
        if high >= z["bot"] and low <= z["top"]:
            matched.append(z)
    return matched


# ════════════════════════════════════════════════════════════
#  SL LOOKUP — khớp Pine f_demand_bottom / f_supply_top
# ════════════════════════════════════════════════════════════
def _demand_bottom(price: float, zones: list) -> float:
    """Pine: f_demand_bottom — tìm demand zone có top ≈ price (±1%), trả về bot."""
    for z in zones:
        if z["type"] != "demand":
            continue
        if z["top"] >= price * 0.99 and z["top"] <= price * 1.01:
            return z["bot"]
    return float("nan")


def _supply_top(price: float, zones: list) -> float:
    """Pine: f_supply_top — tìm supply zone có bot ≈ price (±1%), trả về top."""
    for z in zones:
        if z["type"] != "supply":
            continue
        if z["bot"] >= price * 0.99 and z["bot"] <= price * 1.01:
            return z["top"]
    return float("nan")


# ════════════════════════════════════════════════════════════
#  CANDLE PATTERNS
# ════════════════════════════════════════════════════════════
def _detect_pattern(df: pd.DataFrame) -> str:
    c, o = df["close"], df["open"]
    if (c.iloc[-1] > o.iloc[-1] and c.iloc[-2] < o.iloc[-2] and
            c.iloc[-1] > o.iloc[-2] and o.iloc[-1] < c.iloc[-2]):
        return "Bull Engulfing"
    c1 = c.iloc[-3] < o.iloc[-3]
    c2 = c.iloc[-2] > o.iloc[-2]
    c3 = c.iloc[-1] > o.iloc[-1] and o.iloc[-1] <= o.iloc[-3] and c.iloc[-1] >= c.iloc[-2]
    if c1 and c2 and c3:
        return "3LS↑"
    if (c.iloc[-1] < o.iloc[-1] and c.iloc[-2] > o.iloc[-2] and
            c.iloc[-1] < o.iloc[-2] and o.iloc[-1] > c.iloc[-2]):
        return "Bear Engulfing"
    d1 = c.iloc[-3] > o.iloc[-3]
    d2 = c.iloc[-2] < o.iloc[-2]
    d3 = c.iloc[-1] < o.iloc[-1] and o.iloc[-1] >= o.iloc[-3] and c.iloc[-1] <= c.iloc[-2]
    if d1 and d2 and d3:
        return "3LS↓"
    return ""


def _nearest_supply_above(price: float, zones: list):
    candidates = [z for z in zones if z["type"] == "supply" and z["bot"] > price]
    return min(candidates, key=lambda z: z["bot"]) if candidates else None


# ════════════════════════════════════════════════════════════
#  SIGNAL 1 — LONG/SHORT ZONE  (chạy trên H1 + H4)
#  SIGNAL 2 — BOS PULLBACK     (chạy trên M15 + H1)
# ════════════════════════════════════════════════════════════
def check_strategy_sr(symbol: str, df: pd.DataFrame, state: dict) -> list:
    params  = get_params(state)
    zs      = get_zone_state(symbol)
    bs      = get_bos_state(symbol)
    cd_min  = params["cooldown_min"]
    wait    = params["wait_bars"]
    bos_wait = params["bos_wait"]
    ma_buf  = params["ma_buf_pct"] / 100

    df_closed = df.iloc[:-1].reset_index(drop=True)
    if len(df_closed) < 60:
        return []

    price   = float(df_closed["close"].iloc[-1])
    price_1 = float(df_closed["close"].iloc[-2])

    ma      = _ema(df_closed["close"], params["ma_len"])
    ma_val  = float(ma.iloc[-1])
    ma_val1 = float(ma.iloc[-2])
    ma_val2 = float(ma.iloc[-3])

    k_line, d_line = _stoch(df_closed, params["stoch_k"], params["stoch_sm"], params["stoch_d"])
    k_cur  = float(k_line.iloc[-1])
    k_prv  = float(k_line.iloc[-2])
    d_cur  = float(d_line.iloc[-1])
    d_prv  = float(d_line.iloc[-2])

    vol_ma     = float(df_closed["volume"].rolling(params["vol_ma"]).mean().iloc[-1])
    vol_strong = float(df_closed["volume"].iloc[-1]) > vol_ma * params["vol_mult"]
    vol_pct    = round(float(df_closed["volume"].iloc[-1]) / vol_ma * 100)

    bull_candle = price > float(df_closed["open"].iloc[-1])
    bear_candle = price < float(df_closed["open"].iloc[-1])
    stoch_long  = k_cur > d_cur and k_prv <= d_cur and k_cur < params["stoch_ob"]
    stoch_short = k_cur < d_cur and k_prv >= d_cur and k_cur > params["stoch_os"]

    zones, atr  = _get_zones(df_closed, params)
    dem_zones   = _price_in_zone(df_closed, zones, "demand")
    sup_zones   = _price_in_zone(df_closed, zones, "supply")
    in_demand   = len(dem_zones) > 0
    in_supply   = len(sup_zones) > 0

    signals = []

    # ── Kích hoạt BOS UP khi Supply bị phá (close >= top supply) ──
    for z in [z for z in zones if z["type"] == "supply"]:
        if price_1 >= z["top"]:
            if price_1 > ma_val and ma_val > ma_val1:
                bs["bos_up"]     = True
                bs["ma_touched"] = False
                bs["bos_bars"]   = 0
            break

    # ── BOS PULLBACK tracking ──────────────────────────────────
    if bs["bos_up"]:
        bs["bos_bars"] += 1
        low_cur = float(df_closed["low"].iloc[-1])
        if low_cur <= ma_val and price >= ma_val - ma_val * ma_buf and ma_val > ma_val1:
            bs["ma_touched"] = True
        if ma_val < ma_val2 and ma_val1 < ma_val2:
            bs["bos_up"] = bs["ma_touched"] = False
            bs["bos_bars"] = 0
        if bs["bos_bars"] > bos_wait:
            bs["bos_up"] = bs["ma_touched"] = False
            bs["bos_bars"] = 0

    if bs["bos_up"] and bs["ma_touched"] and price > ma_val and price_1 <= ma_val and bull_candle:
        cd_key = f"{symbol}_bos"
        elapsed = time.time() - _last_signal.get(cd_key, {}).get("ts", 0)
        if elapsed >= cd_min * 60:
            signals.append({
                "type":    "BOS_LONG",
                "price":   round(price, 4),
                "ma_val":  round(ma_val, 4),
                "k_line":  round(k_cur, 1),
            })
            _last_signal[cd_key] = {"ts": time.time()}
            bs["bos_up"] = bs["ma_touched"] = False
            bs["bos_bars"] = 0

    # ── Zone active update ─────────────────────────────────────
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

    # ── Zone LONG ───────────────────────────────────────────────
    if zs["demand_active"] and bull_candle and vol_strong and stoch_long and price > price_1:
        cd_key = f"{symbol}_long"
        elapsed = time.time() - _last_signal.get(cd_key, {}).get("ts", 0)
        if elapsed >= cd_min * 60:
            pattern = _detect_pattern(df_closed)
            entry   = price
            # SL: Pine f_demand_bottom — tìm zone có top ≈ giá, SL = bot
            sl = _demand_bottom(price, zones)
            if np.isnan(sl):
                sl = entry * 0.985
            sl = min(sl, entry * 0.995)
            risk = entry - sl
            if risk <= 0:
                return signals
            tp = entry + risk * 2
            # Tìm zone match để hiển thị
            zone = dem_zones[0] if dem_zones else {}
            signals.append({
                "type":     "LONG",
                "price":    round(price, 4),
                "entry":    round(entry, 4),
                "sl":       round(sl, 4),
                "tp":       round(tp, 4),
                "zone_top": round(zone.get("top", price), 4),
                "zone_bot": round(zone.get("bot", price), 4),
                "pattern":  pattern or "—",
                "k_line":   round(k_cur, 1),
                "d_line":   round(d_cur, 1),
                "vol_pct":  vol_pct,
            })
            _last_signal[cd_key] = {"ts": time.time()}

    # ── Zone SHORT ──────────────────────────────────────────────
    if zs["supply_active"] and bear_candle and vol_strong and stoch_short and price < price_1:
        cd_key = f"{symbol}_short"
        elapsed = time.time() - _last_signal.get(cd_key, {}).get("ts", 0)
        if elapsed >= cd_min * 60:
            pattern = _detect_pattern(df_closed)
            entry   = price
            # SL: Pine f_supply_top — tìm zone có bot ≈ giá, SL = top
            sl = _supply_top(price, zones)
            if np.isnan(sl):
                sl = entry * 1.015
            sl = max(sl, entry * 1.005)
            risk = sl - entry
            if risk <= 0:
                return signals
            tp = entry - risk * 2
            zone = sup_zones[0] if sup_zones else {}
            signals.append({
                "type":     "SHORT",
                "price":    round(price, 4),
                "entry":    round(entry, 4),
                "sl":       round(sl, 4),
                "tp":       round(tp, 4),
                "zone_top": round(zone.get("top", price), 4),
                "zone_bot": round(zone.get("bot", price), 4),
                "pattern":  pattern or "—",
                "k_line":   round(k_cur, 1),
                "d_line":   round(d_cur, 1),
                "vol_pct":  vol_pct,
            })
            _last_signal[cd_key] = {"ts": time.time()}

    if signals:
        print(f"  📊 [SR] {symbol}: {[s['type'] for s in signals]}")

    return signals


# ════════════════════════════════════════════════════════════
#  SIGNAL 3 — TOUCH / BREAK / REJECT  (chạy trên H1 + H4)
# ════════════════════════════════════════════════════════════
def check_zone_reaction(symbol: str, df: pd.DataFrame, state: dict) -> list:
    params = get_params(state)
    if not params.get("touch_signal", True):
        return []

    bs = get_bos_state(symbol)

    df_closed = df.iloc[:-1].reset_index(drop=True)
    if len(df_closed) < 60:
        return []

    price     = float(df_closed["close"].iloc[-1])
    candle_ts = float(df_closed["timestamp"].iloc[-1])

    zones, atr = _get_zones(df_closed, params)
    signals = []
    first_run = not bs["initialized"]

    # Supply (Kháng cự)
    for z in [z for z in zones if z["type"] == "supply"]:
        zkey = ("supply", round(z["mid"], 4))
        last_ts = bs["touched_zones"].get(zkey, 0)
        if candle_ts <= last_ts:
            continue
        touched_now = (df_closed["high"].iloc[-1] >= z["bot"] and df_closed["low"].iloc[-1] <= z["top"])
        if not touched_now:
            continue
        bs["touched_zones"][zkey] = candle_ts
        if first_run:
            continue
        if price > z["top"]:
            signals.append({"type": "BREAK", "zone_type": "supply", "direction": "UP",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})
        elif price < z["bot"]:
            signals.append({"type": "REJECT", "zone_type": "supply", "direction": "DOWN",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})
        else:
            signals.append({"type": "TOUCH", "zone_type": "supply",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})

    # Demand (Hỗ trợ)
    for z in [z for z in zones if z["type"] == "demand"]:
        zkey = ("demand", round(z["mid"], 4))
        last_ts = bs["touched_zones"].get(zkey, 0)
        if candle_ts <= last_ts:
            continue
        touched_now = (df_closed["high"].iloc[-1] >= z["bot"] and df_closed["low"].iloc[-1] <= z["top"])
        if not touched_now:
            continue
        bs["touched_zones"][zkey] = candle_ts
        if first_run:
            continue
        if price < z["bot"]:
            signals.append({"type": "BREAK", "zone_type": "demand", "direction": "DOWN",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})
        elif price > z["top"]:
            signals.append({"type": "REJECT", "zone_type": "demand", "direction": "UP",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})
        else:
            signals.append({"type": "TOUCH", "zone_type": "demand",
                             "price": round(price, 4), "zone_top": round(z["top"], 4), "zone_bot": round(z["bot"], 4)})

    if len(bs["touched_zones"]) > 30:
        keys = list(bs["touched_zones"].keys())[-20:]
        bs["touched_zones"] = {k: bs["touched_zones"][k] for k in keys}

    if first_run:
        bs["initialized"] = True

    return signals


# ════════════════════════════════════════════════════════════
#  SIGNAL 4 — MA20 / EMA200 CROSS  (chạy độc lập trên M15, H1, H4)
# ════════════════════════════════════════════════════════════
def check_ma_cross(symbol: str, df: pd.DataFrame, state: dict) -> list:
    params = get_params(state)
    ms = get_ma_cross_state(symbol)

    df_closed = df.iloc[:-1].reset_index(drop=True)
    if len(df_closed) < params["ema200_len"] + 5:
        return []

    ma20    = _ema(df_closed["close"], params["ma_len"])
    ema200  = _ema(df_closed["close"], params["ema200_len"])

    ma_cur,  ma_prv  = float(ma20.iloc[-1]),   float(ma20.iloc[-2])
    ema_cur, ema_prv = float(ema200.iloc[-1]), float(ema200.iloc[-2])

    golden_cross = ma_prv <= ema_prv and ma_cur > ema_cur
    death_cross  = ma_prv >= ema_prv and ma_cur < ema_cur

    signals = []
    first_run = not ms["initialized"]
    ms["initialized"] = True

    if first_run:
        return []

    price = float(df_closed["close"].iloc[-1])

    if golden_cross:
        signals.append({
            "type":  "MA_CROSS",
            "direction": "GOLDEN",
            "price": round(price, 4),
            "ma20":  round(ma_cur, 4),
            "ema200": round(ema_cur, 4),
        })
    elif death_cross:
        signals.append({
            "type":  "MA_CROSS",
            "direction": "DEATH",
            "price": round(price, 4),
            "ma20":  round(ma_cur, 4),
            "ema200": round(ema_cur, 4),
        })

    return signals
