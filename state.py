# ============================================================
#  state.py — Trạng thái runtime
# ============================================================
from config import DEFAULT_SYMBOLS, CHAT_ID

state = {
    "chat_id": CHAT_ID,

    # ── Danh sách coin riêng cho từng chiến lược ─────────────
    "symbols_a": list(DEFAULT_SYMBOLS),   # Chiến lược A: Ichimoku
    "symbols_b": list(DEFAULT_SYMBOLS),   # Chiến lược B: EMA+MACD

    # ── Bật/tắt từng chiến lược ──────────────────────────────
    "strategies": {
        "ichimoku": True,
        "ema":      True,
    },

    # ── Trạng thái tránh spam ─────────────────────────────────
    "last_kumo_cross":   {},
    "last_entry_signal": {},
    "last_ema_signal":   {},
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


# ── Thêm/xóa cả 2 (lệnh chung) ───────────────────────────────
def add_symbol(symbol: str) -> bool:
    s = symbol.upper()
    a = add_symbol_a(s)
    b = add_symbol_b(s)
    return a or b

def remove_symbol(symbol: str) -> bool:
    s = symbol.upper()
    a = remove_symbol_a(s)
    b = remove_symbol_b(s)
    return a or b


# ── Bật/tắt chiến lược ───────────────────────────────────────
def toggle_strategy(name: str):
    if name not in state["strategies"]:
        return None
    state["strategies"][name] = not state["strategies"][name]
    return state["strategies"][name]


def strategy_status() -> str:
    a = "✅ BẬT" if state["strategies"]["ichimoku"] else "❌ TẮT"
    b = "✅ BẬT" if state["strategies"]["ema"]      else "❌ TẮT"
    coins_a = ", ".join(s.replace("USDT","") for s in state["symbols_a"]) or "Trống"
    coins_b = ", ".join(s.replace("USDT","") for s in state["symbols_b"]) or "Trống"
    return (
        f"⚙️  TRẠNG THÁI CHIẾN LƯỢC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  Chiến lược A — Ichimoku : {a}\n"
        f"   Coin: {coins_a}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Chiến lược B — EMA+MACD  : {b}\n"
        f"   Coin: {coins_b}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Lệnh:\n"
        f"/aa COIN · /ra COIN  (thêm/xóa CL A)\n"
        f"/ab COIN · /rb COIN  (thêm/xóa CL B)\n"
        f"/add COIN · /remove COIN  (cả 2)"
    )