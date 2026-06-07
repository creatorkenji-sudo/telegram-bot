# ============================================================
#  state.py — Trạng thái runtime
# ============================================================
from config import DEFAULT_SYMBOLS, CHAT_ID

state = {
    "chat_id": CHAT_ID,
    "symbols": list(DEFAULT_SYMBOLS),

    # ── Bật/tắt từng chiến lược ──────────────────────────────
    "strategies": {
        "ichimoku": True,   # Chiến lược A: Ichimoku + StochRSI
        "ema":      True,   # Chiến lược B: EMA pullback + MACD
    },

    # ── Trạng thái Ichimoku (tránh spam) ─────────────────────
    "last_kumo_cross":    {},   # symbol -> "UP" | "DOWN" | None
    "last_entry_signal":  {},   # symbol -> "LONG" | "SHORT" | None

    # ── Trạng thái EMA (tránh spam) ──────────────────────────
    "last_ema_signal":    {},   # symbol -> "LONG" | "SHORT" | None
}


def add_symbol(symbol: str) -> bool:
    s = symbol.upper()
    if s not in state["symbols"]:
        state["symbols"].append(s)
        return True
    return False


def remove_symbol(symbol: str) -> bool:
    s = symbol.upper()
    if s in state["symbols"]:
        state["symbols"].remove(s)
        for key in ["last_kumo_cross", "last_entry_signal", "last_ema_signal"]:
            state[key].pop(s, None)
        return True
    return False


def toggle_strategy(name: str) -> bool | None:
    """Bật/tắt chiến lược. Trả về trạng thái mới hoặc None nếu không tồn tại."""
    if name not in state["strategies"]:
        return None
    state["strategies"][name] = not state["strategies"][name]
    return state["strategies"][name]


def strategy_status() -> str:
    a = "✅ BẬT" if state["strategies"]["ichimoku"] else "❌ TẮT"
    b = "✅ BẬT" if state["strategies"]["ema"]      else "❌ TẮT"
    return (
        f"⚙️  TRẠNG THÁI CHIẾN LƯỢC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  Chiến lược A — Ichimoku + StochRSI : {a}\n"
        f"📈 Chiến lược B — EMA Pullback + MACD  : {b}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Lệnh: /strategy_a · /strategy_b"
    )
