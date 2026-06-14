# ============================================================
#  state.py — Trạng thái runtime
# ============================================================
from config import DEFAULT_SYMBOLS, CHAT_ID

state = {
    "chat_id": CHAT_ID,

    # ── Danh sách coin riêng cho từng chiến lược ─────────────
    "symbols_a": list(DEFAULT_SYMBOLS),   # Chiến lược A
    "symbols_b": list(DEFAULT_SYMBOLS),   # Chiến lược B
    "symbols_c": list(DEFAULT_SYMBOLS),   # Chiến lược C
    "symbols_d": list(DEFAULT_SYMBOLS),   # Chiến lược D
    "symbols_sr": list(DEFAULT_SYMBOLS),  # Chiến lược SR
    "last_sr_signal": {},
    "sr_params": {
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
        "touch_signal": False,
    },

    # ── Bật/tắt chiến lược — khai báo đầy đủ ngay từ đầu ────
    "strategies": {
        "ichimoku":   True,
        "ema":        True,
        "supertrend": True,
        "ichistoch":  True,   # Chiến lược D
        "sr":         True,    # Chiến lược SR
    },

    # ── Confirmation CL C ─────────────────────────────────────
    "confirms_c": ["choppiness", "adx", "volume"],

    # ── Trạng thái tránh spam ─────────────────────────────────
    "last_kumo_cross":   {},
    "last_entry_signal": {},
    "last_ema_signal":   {},
    "last_c_signal":     {},
    "last_d_signal":     {},

    # ── Bộ lọc Chiến lược B ──────────────────────────────────
    "filters_b": {
        "ema_h1":   True,
        "ema_15m":  True,
        "macd":     True,
        "rsi":      True,
        "candle":   True,
        "trend":    True,
        "momentum": False,
    },
    "min_pass_b": 4,
}


# ── Chiến lược A ─────────────────────────────────────────────
def add_symbol_a(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols_a"]:
        state["symbols_a"].append(s)
        return True
    return False

def remove_symbol_a(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols_a"]:
        state["symbols_a"].remove(s)
        state["last_kumo_cross"].pop(s, None)
        state["last_entry_signal"].pop(s, None)
        return True
    return False


# ── Chiến lược B ─────────────────────────────────────────────
def add_symbol_b(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols_b"]:
        state["symbols_b"].append(s)
        return True
    return False

def remove_symbol_b(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols_b"]:
        state["symbols_b"].remove(s)
        state["last_ema_signal"].pop(s, None)
        return True
    return False


# ── Chiến lược C ─────────────────────────────────────────────
def add_symbol_c(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols_c"]:
        state["symbols_c"].append(s)
        return True
    return False

def remove_symbol_c(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols_c"]:
        state["symbols_c"].remove(s)
        state["last_c_signal"].pop(s, None)
        return True
    return False




def add_symbol_d(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols_d"]:
        state["symbols_d"].append(s)
        return True
    return False

def remove_symbol_d(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols_d"]:
        state["symbols_d"].remove(s)
        state["last_d_signal"].pop(s, None)
        return True
    return False



def add_symbol_sr(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols_sr"]:
        state["symbols_sr"].append(s)
        return True
    return False

def remove_symbol_sr(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols_sr"]:
        state["symbols_sr"].remove(s)
        state["last_sr_signal"].pop(s, None)
        return True
    return False

# ── Thêm/xóa cả 3 ────────────────────────────────────────────
def add_symbol(symbol: str) -> bool:
    s = symbol.upper()
    return add_symbol_a(s) | add_symbol_b(s) | add_symbol_c(s) | add_symbol_d(s) | add_symbol_sr(s)

def remove_symbol(symbol: str) -> bool:
    s = symbol.upper()
    return remove_symbol_a(s) | remove_symbol_b(s) | remove_symbol_c(s) | remove_symbol_d(s) | remove_symbol_sr(s)


# ── Bật/tắt chiến lược ───────────────────────────────────────
def toggle_strategy(name: str):
    if name not in state["strategies"]:
        return None
    state["strategies"][name] = not state["strategies"][name]
    return state["strategies"][name]


def strategy_status() -> str:
    sa = "✅ BẬT" if state["strategies"].get("ichimoku")   else "❌ TẮT"
    sb = "✅ BẬT" if state["strategies"].get("ema")         else "❌ TẮT"
    sc = "✅ BẬT" if state["strategies"].get("supertrend")  else "❌ TẮT"
    ca = ", ".join(s.replace("USDT","") for s in state["symbols_a"]) or "Trống"
    cb = ", ".join(s.replace("USDT","") for s in state["symbols_b"]) or "Trống"
    cc = ", ".join(s.replace("USDT","") for s in state["symbols_c"]) or "Trống"
    cf = ", ".join(state["confirms_c"]) or "Không có"
    return (
        f"⚙️  TRẠNG THÁI CHIẾN LƯỢC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A — Ichimoku    : {sa}\n"
        f"   Coin: {ca}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 CL B — EMA+MACD     : {sb}\n"
        f"   Coin: {cb}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ CL C — Supertrend   : {sc}\n"
        f"   Coin: {cc}\n"
        f"   Confirmation: {cf}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"/aa /ra — CL A  ·  /ab /rb — CL B  ·  /ac /rc — CL C\n"
        f"/add /remove — cả 3  ·  /confirms — xem CL C"
    )


# ── Confirmation CL C ─────────────────────────────────────────
from strategy_c import CONFIRMATION_MAP, CONFIRMATION_LABELS


def set_confirms_c(names: list) -> tuple:
    valid, invalid = [], []
    for n in names:
        (valid if n in CONFIRMATION_MAP else invalid).append(n)
    if valid:
        state["confirms_c"] = valid
    return valid, invalid


def confirms_status() -> str:
    lines = []
    for name, label in CONFIRMATION_LABELS.items():
        icon = "✅" if name in state["confirms_c"] else "⬜"
        lines.append(f"  {icon} {name:<14} — {label}")
    return (
        f"🔧  CONFIRMATION — CL C\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(lines) +
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Đang bật: {len(state['confirms_c'])} indicator\n"
        f"Lệnh: /set_confirm qqe adx volume ssl ..."
    )