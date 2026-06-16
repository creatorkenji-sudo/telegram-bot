# ============================================================
#  strategy_sr.py — Chiến lược Hỗ trợ Kháng cự (ZoneCandle)
#
#  Signal 1: LONG/SHORT Zone — giá chạm Demand/Supply
#  Signal 2: BOS Pullback    — phá kháng cự + pullback MA20
#  Signal 3: BOS Break       — thông báo khi phá vùng
# ============================================================
import time
import numpy as np
import pandas as pd

# ── Cooldown ──────────────────────────────────────────────────
_last_signal: dict = {}

# ── Default params ────────────────────────────────────────────
DEFAULT_PARAMS = {
    "swing_length": 10,
    "box_width":    2.5,
    "stoch_k":      14,
    "stoch_sm":     3,
    "stoch_d":      3,
    "stoch_ob":     70,
    "stoch_os":     30,
    "vol_ma":       20,
    "vol_mult":     1.2,
    "wait_bars":    3,
    "ma_len":       20,
    "ema200_len":   200,
    "ma_buf_pct":   0.3,
    "bos_wait":     20,
    "cooldown_min": 30,
    "touch_signal": False,  # bật/tắt báo TOUCH/BREAK/REJECT (chạm vùng kháng cự/hỗ trợ)
    "zone_reaction_tf": "h1",  # khung tính TOUCH/BREAK/REJECT: m5/m15/h1/h4
}

# ── Zone state per symbol ─────────────────────────────────────
_zone_state: dict = {}
_bos_state:  dict = {}


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
            "reported_levels": {},  # {(direction, level): {"ts": time, "in_zone": bool}}
            "touched_zones": {},    # {(type, level): True}  — đã báo "chạm", chờ kết quả
            "initialized": False,   # False = lần check đầu tiên, bỏ qua TOUCH/BREAK/REJECT/BOS_BREAK
        }
    return _bos_state[symbol]


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
#  ZONE DETECTION
# ════════════════════════════════════════════════════════════
def _merge_zones(zone_list: list, atr: float) -> list:
    """Gộp các vùng chồng lấp/gần nhau (khoảng cách < ATR*2) thành 1 vùng"""
    if not zone_list:
        return []
    zone_list = sorted(zone_list, key=lambda z: z["bot"])
    merged = [zone_list[0]]
    for z in zone_list[1:]:
        last = merged[-1]
        # Nếu 2 vùng chồng lấp hoặc gần nhau (gap < ATR*2) → gộp
        if z["bot"] <= last["top"] + atr * 2:
            last["top"] = max(last["top"], z["top"])
            last["bot"] = min(last["bot"], z["bot"])
            last["mid"] = (last["top"] + last["bot"]) / 2
        else:
            merged.append(z)
    return merged


def _get_zones(df: pd.DataFrame, params: dict):
    swing  = params["swing_length"]
    bw     = params["box_width"]
    atr    = _atr(df)
    buf    = atr * (bw / 10)

    ph_list = _pivot_high(df, swing)[-5:]
    pl_list = _pivot_low(df,  swing)[-5:]

    sup_zones = []
    dem_zones = []
    for val in ph_list:
        sup_zones.append({"type": "supply", "top": val, "bot": val - buf, "mid": val - buf/2})
    for val in pl_list:
        dem_zones.append({"type": "demand", "top": val + buf, "bot": val, "mid": val + buf/2})

    # Gộp các vùng gần/chồng nhau
    sup_zones = _merge_zones(sup_zones, atr)
    dem_zones = _merge_zones(dem_zones, atr)
    for z in sup_zones:
        z["type"] = "supply"
    for z in dem_zones:
        z["type"] = "demand"

    return sup_zones + dem_zones, atr


def _price_in_zone(df: pd.DataFrame, zones: list, zone_type: str) -> list:
    """Trả về list các vùng mà giá hiện tại đang chạm"""
    high = df["high"].iloc[-1]
    low  = df["low"].iloc[-1]
    matched = []
    for z in zones:
        if z["type"] != zone_type:
            continue
        if high >= z["bot"] and low <= z["top"]:
            matched.append(z)
    return matched


def _nearest_supply_above(price: float, zones: list):
    candidates = [z for z in zones if z["type"] == "supply" and z["bot"] > price]
    return min(candidates, key=lambda z: z["bot"]) if candidates else None


# ════════════════════════════════════════════════════════════
#  CANDLE PATTERNS
# ════════════════════════════════════════════════════════════
def _detect_pattern(df: pd.DataFrame) -> str:
    c, o = df["close"], df["open"]
    # Bull Engulfing
    if (c.iloc[-1] > o.iloc[-1] and c.iloc[-2] < o.iloc[-2] and
            c.iloc[-1] > o.iloc[-2] and o.iloc[-1] < c.iloc[-2]):
        return "Bull Engulfing"
    # Three Outside Up
    c1 = c.iloc[-3] < o.iloc[-3]
    c2 = c.iloc[-2] > o.iloc[-2]
    c3 = c.iloc[-1] > o.iloc[-1] and o.iloc[-1] <= o.iloc[-3] and c.iloc[-1] >= c.iloc[-2]
    if c1 and c2 and c3:
        return "3LS↑"
    # Bear Engulfing
    if (c.iloc[-1] < o.iloc[-1] and c.iloc[-2] > o.iloc[-2] and
            c.iloc[-1] < o.iloc[-2] and o.iloc[-1] > c.iloc[-2]):
        return "Bear Engulfing"
    # Three Outside Down
    d1 = c.iloc[-3] > o.iloc[-3]
    d2 = c.iloc[-2] < o.iloc[-2]
    d3 = c.iloc[-1] < o.iloc[-1] and o.iloc[-1] >= o.iloc[-3] and c.iloc[-1] <= c.iloc[-2]
    if d1 and d2 and d3:
        return "3LS↓"
    return ""


# ════════════════════════════════════════════════════════════
#  MAIN CHECK
# ════════════════════════════════════════════════════════════
def check_strategy_sr(symbol: str, df: pd.DataFrame, state: dict) -> list:
    """
    Trả về list các signal dict (có thể nhiều signal cùng lúc).
    Mỗi signal: {type, sub_type, price, ...}
    """
    params  = get_params(state)
    zs      = get_zone_state(symbol)
    bs      = get_bos_state(symbol)
    cd_min  = params["cooldown_min"]
    wait    = params["wait_bars"]
    bos_wait = params["bos_wait"]
    ma_buf  = params["ma_buf_pct"] / 100

    # Dùng nến ĐÃ ĐÓNG — bỏ nến cuối (đang chạy) ra khỏi mọi tính toán
    df_closed = df.iloc[:-1].reset_index(drop=True)

    price   = float(df_closed["close"].iloc[-1])   # nến đã đóng gần nhất
    price_1 = float(df_closed["close"].iloc[-2])   # nến đã đóng trước đó
    candle_ts = float(df_closed["timestamp"].iloc[-1])  # mốc thời gian nến đã đóng gần nhất

    # Indicators — tính trên df_closed
    ma      = _ema(df_closed["close"], params["ma_len"])
    ema200  = _ema(df_closed["close"], params["ema200_len"])
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
    now = time.time()
    BOS_LOCK_SEC = 15 * 60  # 15 phút
    first_run = not bs["initialized"]

    # ── BOS BREAK detection — lock 15 phút, báo lại khi thoát-vào-lại vùng ──
    # Supply bị phá (close[1] >= top supply) → giá đang TRÊN vùng (phá lên)
    for z in [z for z in zones if z["type"] == "supply"]:
        level_key = ("UP", round(z["top"], 4))
        price_above = price_1 >= z["top"]   # giá đang trên/trong vùng (đã phá)
        rec = bs["reported_levels"].get(level_key)

        if price_above:
            if rec is None:
                # Lần đầu phá vùng → báo ngay
                signals.append({"type": "BOS_BREAK", "direction": "UP",
                                 "price": round(price, 4), "zone_level": round(z["top"], 4)})
                bs["reported_levels"][level_key] = {"ts": now, "in_zone": True}
                if price_1 > ma_val and ma_val > ma_val1:
                    bs["bos_up"] = True
                    bs["ma_touched"] = False
                    bs["bos_bars"] = 0
            else:
                # Đã báo trước đó — chỉ báo lại nếu đã qua 15p VÀ giá vẫn trong vùng
                if now - rec["ts"] >= BOS_LOCK_SEC and rec["in_zone"]:
                    signals.append({"type": "BOS_BREAK", "direction": "UP",
                                     "price": round(price, 4), "zone_level": round(z["top"], 4)})
                    rec["ts"] = now
                rec["in_zone"] = True
        else:
            # Giá thoát khỏi vùng → reset để lần sau vào lại báo ngay
            if rec is not None:
                rec["in_zone"] = False
        break

    # Demand bị phá (close[1] <= bot demand) → giá đang DƯỚI vùng (phá xuống)
    for z in [z for z in zones if z["type"] == "demand"]:
        level_key = ("DOWN", round(z["bot"], 4))
        price_below = price_1 <= z["bot"]
        rec = bs["reported_levels"].get(level_key)

        if price_below:
            if rec is None:
                signals.append({"type": "BOS_BREAK", "direction": "DOWN",
                                 "price": round(price, 4), "zone_level": round(z["bot"], 4)})
                bs["reported_levels"][level_key] = {"ts": now, "in_zone": True}
            else:
                if now - rec["ts"] >= BOS_LOCK_SEC and rec["in_zone"]:
                    signals.append({"type": "BOS_BREAK", "direction": "DOWN",
                                     "price": round(price, 4), "zone_level": round(z["bot"], 4)})
                    rec["ts"] = now
                rec["in_zone"] = True
        else:
            if rec is not None:
                rec["in_zone"] = False
        break

    # Giới hạn kích thước dict tránh phình to vô hạn
    if len(bs["reported_levels"]) > 50:
        keys = list(bs["reported_levels"].keys())[-30:]
        bs["reported_levels"] = {k: bs["reported_levels"][k] for k in keys}

    # ── BOS PULLBACK tracking ──────────────────────────────────
    if bs["bos_up"]:
        bs["bos_bars"] += 1
        # Chạm MA20 trong buffer
        low_cur = float(df_closed["low"].iloc[-1])
        if low_cur <= ma_val and price >= ma_val - ma_val * ma_buf and ma_val > ma_val1:
            bs["ma_touched"] = True
        # Reset nếu MA dốc xuống 2 nến
        if ma_val < ma_val2 and ma_val1 < ma_val2:
            bs["bos_up"] = bs["ma_touched"] = False
            bs["bos_bars"] = 0
        # Timeout
        if bs["bos_bars"] > bos_wait:
            bs["bos_up"] = bs["ma_touched"] = False
            bs["bos_bars"] = 0

    # ── BOS LONG signal ────────────────────────────────────────
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

    # ── Zone LONG signal ───────────────────────────────────────
    if zs["demand_active"] and bull_candle and vol_strong and stoch_long and price > price_1:
        cd_key = f"{symbol}_long"
        elapsed = time.time() - _last_signal.get(cd_key, {}).get("ts", 0)
        if elapsed >= cd_min * 60:
            pattern = _detect_pattern(df_closed)
            zone    = dem_zones[0] if dem_zones else {}
            entry   = price
            sl      = zone.get("bot", entry * 0.985)
            risk    = entry - sl
            tp      = entry + risk * 2   # R:R 1:2
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

    # ── Zone SHORT signal ──────────────────────────────────────
    if zs["supply_active"] and bear_candle and vol_strong and stoch_short and price < price_1:
        cd_key = f"{symbol}_short"
        elapsed = time.time() - _last_signal.get(cd_key, {}).get("ts", 0)
        if elapsed >= cd_min * 60:
            pattern = _detect_pattern(df_closed)
            zone    = sup_zones[0] if sup_zones else {}
            entry   = price
            sl      = zone.get("top", entry * 1.015)
            risk    = sl - entry
            tp      = entry - risk * 2   # R:R 1:2
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

    # Lần check đầu tiên của symbol — chỉ ghi nhận trạng thái, không báo
    if first_run:
        bs["initialized"] = True
        signals = [s for s in signals if s["type"] not in ("TOUCH", "BREAK", "REJECT", "BOS_BREAK")]

    if signals:
        print(f"  📊 [SR] {symbol}: {[s['type'] for s in signals]}")
    else:
        print(f"    — [SR] {symbol}: ${price:.4f} | dem={zs['demand_active']} sup={zs['supply_active']} bos={bs['bos_up']} k={k_cur:.1f}")

    return signals


# ════════════════════════════════════════════════════════════
#  ZONE REACTION — TOUCH / BREAK / REJECT (chạy trên H1 riêng)
# ════════════════════════════════════════════════════════════
_zone_reaction_state: dict = {}


def get_zone_reaction_state(symbol: str) -> dict:
    if symbol not in _zone_reaction_state:
        _zone_reaction_state[symbol] = {
            "touched_zones": {},   # {(type, mid): last_candle_ts}
            "initialized":   False,
        }
    return _zone_reaction_state[symbol]


def check_zone_reaction(symbol: str, df: pd.DataFrame, state: dict) -> list:
    """
    Check TOUCH/BREAK/REJECT trên khung thời gian truyền vào (thường là H1).
    Độc lập hoàn toàn với check_strategy_sr (LONG/SHORT/BOS).
    """
    params = get_params(state)
    if not params.get("touch_signal", False):
        return []

    rs = get_zone_reaction_state(symbol)

    df_closed = df.iloc[:-1].reset_index(drop=True)
    price     = float(df_closed["close"].iloc[-1])
    candle_ts = float(df_closed["timestamp"].iloc[-1])

    zones, atr = _get_zones(df_closed, params)
    signals = []
    first_run = not rs["initialized"]

    for z in [z for z in zones if z["type"] == "supply"]:
        zkey = ("supply", round(z["mid"], 4))
        last_ts = rs["touched_zones"].get(zkey, 0)
        if candle_ts <= last_ts:
            continue
        touched_now = (df_closed["high"].iloc[-1] >= z["bot"] and df_closed["low"].iloc[-1] <= z["top"])
        if not touched_now:
            continue
        rs["touched_zones"][zkey] = candle_ts
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

    for z in [z for z in zones if z["type"] == "demand"]:
        zkey = ("demand", round(z["mid"], 4))
        last_ts = rs["touched_zones"].get(zkey, 0)
        if candle_ts <= last_ts:
            continue
        touched_now = (df_closed["high"].iloc[-1] >= z["bot"] and df_closed["low"].iloc[-1] <= z["top"])
        if not touched_now:
            continue
        rs["touched_zones"][zkey] = candle_ts
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

    if len(rs["touched_zones"]) > 30:
        keys = list(rs["touched_zones"].keys())[-20:]
        rs["touched_zones"] = {k: rs["touched_zones"][k] for k in keys}

    if first_run:
        rs["initialized"] = True

    return signals
