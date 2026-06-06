# ============================================================
#  state.py — Trạng thái runtime (thay đổi được qua Telegram)
# ============================================================
from config import DEFAULT_SYMBOLS, CHAT_ID

state = {
    "chat_id": CHAT_ID,

    # Danh sách coin theo dõi — thêm/xóa qua /add /remove
    "symbols": list(DEFAULT_SYMBOLS),

    # Theo dõi Kumo cross để không gửi lặp lại
    # key: symbol, value: "UP" | "DOWN" | None
    "last_kumo_cross": {},

    # Theo dõi setup entry để không spam
    # key: symbol, value: "LONG" | "SHORT" | None
    "last_entry_signal": {},
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
        state["last_kumo_cross"].pop(s, None)
        state["last_entry_signal"].pop(s, None)
        return True
    return False
