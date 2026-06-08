# ============================================================
#  telegram_bot.py — Commands Telegram (PTB 13.x)
# ============================================================
from telegram.ext import Updater, CommandHandler
from state import (
    state,
    add_symbol, remove_symbol,
    add_symbol_a, remove_symbol_a,
    add_symbol_b, remove_symbol_b,
    toggle_strategy, strategy_status,
)
from config import TOKEN
from formatter import format_startup, format_status


def _fmt_list(symbols: list) -> str:
    return ", ".join(s.replace("USDT","") for s in symbols) if symbols else "Trống"


# ── Lệnh chung ───────────────────────────────────────────────
def cmd_start(update, context):
    update.message.reply_text(format_startup(
        state["symbols_a"], state["symbols_b"], state["symbols_c"]
    ))

def cmd_add(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /add BTCUSDT  (thêm vào cả 2 chiến lược)")
        return
    symbol = _clean(context.args[0])
    if add_symbol(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào cả 2 chiến lược\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong cả 2 rồi")

def cmd_remove(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /remove BTCUSDT  (xóa khỏi cả 2 chiến lược)")
        return
    symbol = _clean(context.args[0])
    if remove_symbol(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi cả 2 chiến lược\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong danh sách nào")

def cmd_list(update, context):
    update.message.reply_text(
        f"📋 DANH SÁCH COIN\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A (Ichimoku):\n"
        + "\n".join(f"  • {s}" for s in state["symbols_a"] or ["(Trống)"]) +
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 CL B (EMA+MACD):\n"
        + "\n".join(f"  • {s}" for s in state["symbols_b"] or ["(Trống)"])
    )

def cmd_status(update, context):
    update.message.reply_text(format_status(
        state["symbols_a"], state["symbols_b"], state["strategies"],
        state["symbols_c"], state["confirms_c"]
    ))


# ── Lệnh riêng Chiến lược A ──────────────────────────────────
def cmd_aa(update, context):
    """Thêm coin vào Chiến lược A."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /aa BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if add_symbol_a(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào CL A\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong CL A rồi")

def cmd_ra(update, context):
    """Xóa coin khỏi Chiến lược A."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /ra BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if remove_symbol_a(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi CL A\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong CL A")


# ── Lệnh riêng Chiến lược B ──────────────────────────────────
def cmd_ab(update, context):
    """Thêm coin vào Chiến lược B."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /ab HYPEUSDT")
        return
    symbol = _clean(context.args[0])
    if add_symbol_b(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào CL B\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong CL B rồi")

def cmd_rb(update, context):
    """Xóa coin khỏi Chiến lược B."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /rb HYPEUSDT")
        return
    symbol = _clean(context.args[0])
    if remove_symbol_b(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi CL B\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong CL B")


# ── Bật/tắt chiến lược ───────────────────────────────────────
def cmd_strategy_a(update, context):
    new = toggle_strategy("ichimoku")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(
        f"☁️  Chiến lược A — Ichimoku + StochRSI\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )

def cmd_strategy_b(update, context):
    new = toggle_strategy("ema")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )

def cmd_strategies(update, context):
    update.message.reply_text(strategy_status())


# ── Helper ────────────────────────────────────────────────────
def _clean(symbol: str) -> str:
    s = symbol.upper()
    if not s.endswith("USDT"):
        s += "USDT"
    return s


# ── Khởi động polling ─────────────────────────────────────────
def run_telegram():
    updater = Updater(TOKEN, use_context=True)
    updater.bot.delete_webhook(drop_pending_updates=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",      cmd_start))
    dp.add_handler(CommandHandler("add",        cmd_add))
    dp.add_handler(CommandHandler("remove",     cmd_remove))
    dp.add_handler(CommandHandler("list",       cmd_list))
    dp.add_handler(CommandHandler("status",     cmd_status))
    dp.add_handler(CommandHandler("aa",         cmd_aa))
    dp.add_handler(CommandHandler("ra",         cmd_ra))
    dp.add_handler(CommandHandler("ab",         cmd_ab))
    dp.add_handler(CommandHandler("rb",         cmd_rb))
    dp.add_handler(CommandHandler("strategy_a", cmd_strategy_a))
    dp.add_handler(CommandHandler("strategy_b", cmd_strategy_b))
    dp.add_handler(CommandHandler("strategies", cmd_strategies))

    updater.start_polling()
    print("✅ Telegram bot polling...")


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC C — Commands
# ════════════════════════════════════════════════════════════
from state import (
    add_symbol_c, remove_symbol_c,
    set_confirms_c, confirms_status,
)
from strategy_c import CONFIRMATION_MAP, CONFIRMATION_LABELS


def cmd_strategy_c(update, context):
    """Bật/tắt Chiến lược C."""
    new = toggle_strategy("supertrend")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(
        f"⚡ Chiến lược C — Supertrend + Confirmation\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )


def cmd_ac(update, context):
    """Thêm coin vào CL C."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /ac BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if add_symbol_c(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào CL C\n"
            f"⚡ CL C: {_fmt_list(state['symbols_c'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong CL C rồi")


def cmd_rc(update, context):
    """Xóa coin khỏi CL C."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /rc BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if remove_symbol_c(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi CL C\n"
            f"⚡ CL C: {_fmt_list(state['symbols_c'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong CL C")


def cmd_set_confirm(update, context):
    """
    /set_confirm qqe adx volume ssl ...
    Đặt lại danh sách confirmation cho CL C.
    """
    if not context.args:
        update.message.reply_text(
            f"❌ Dùng: /set_confirm qqe adx volume\n\n"
            f"Các confirmation có sẵn:\n"
            + "\n".join(f"  • {k} — {v}" for k, v in CONFIRMATION_LABELS.items())
        )
        return

    names = [a.lower() for a in context.args]
    valid, invalid = set_confirms_c(names)

    msg = ""
    if valid:
        msg += f"✅ Đã bật: {', '.join(valid)}\n"
    if invalid:
        msg += f"⚠️ Không tìm thấy: {', '.join(invalid)}\n"
    msg += f"\n{confirms_status()}"
    update.message.reply_text(msg)


def cmd_confirms(update, context):
    """Xem trạng thái confirmation CL C."""
    update.message.reply_text(confirms_status())


def cmd_add_confirm(update, context):
    """
    /add_confirm qqe  — thêm 1 confirmation vào CL C.
    """
    if not context.args:
        update.message.reply_text("❌ Dùng: /add_confirm qqe")
        return
    name = context.args[0].lower()
    if name not in CONFIRMATION_MAP:
        update.message.reply_text(
            f"⚠️ '{name}' không tồn tại.\n"
            f"Dùng: {', '.join(CONFIRMATION_MAP.keys())}"
        )
        return
    if name in state["confirms_c"]:
        update.message.reply_text(f"⚠️ '{name}' đã có rồi")
        return
    state["confirms_c"].append(name)
    update.message.reply_text(
        f"✅ Đã thêm: {CONFIRMATION_LABELS[name]}\n\n"
        f"{confirms_status()}"
    )


def cmd_remove_confirm(update, context):
    """
    /remove_confirm qqe — xóa 1 confirmation khỏi CL C.
    """
    if not context.args:
        update.message.reply_text("❌ Dùng: /remove_confirm qqe")
        return
    name = context.args[0].lower()
    if name not in state["confirms_c"]:
        update.message.reply_text(f"⚠️ '{name}' chưa được bật")
        return
    state["confirms_c"].remove(name)
    update.message.reply_text(
        f"🗑 Đã xóa: {CONFIRMATION_LABELS.get(name, name)}\n\n"
        f"{confirms_status()}"
    )


# ── Đăng ký handler mới vào run_telegram ────────────────────
_original_run = run_telegram

def run_telegram():
    updater = Updater(TOKEN, use_context=True)
    updater.bot.delete_webhook(drop_pending_updates=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",          cmd_start))
    dp.add_handler(CommandHandler("add",            cmd_add))
    dp.add_handler(CommandHandler("remove",         cmd_remove))
    dp.add_handler(CommandHandler("list",           cmd_list))
    dp.add_handler(CommandHandler("status",         cmd_status))
    dp.add_handler(CommandHandler("aa",             cmd_aa))
    dp.add_handler(CommandHandler("ra",             cmd_ra))
    dp.add_handler(CommandHandler("ab",             cmd_ab))
    dp.add_handler(CommandHandler("rb",             cmd_rb))
    dp.add_handler(CommandHandler("ac",             cmd_ac))
    dp.add_handler(CommandHandler("rc",             cmd_rc))
    dp.add_handler(CommandHandler("strategy_a",     cmd_strategy_a))
    dp.add_handler(CommandHandler("strategy_b",     cmd_strategy_b))
    dp.add_handler(CommandHandler("strategy_c",     cmd_strategy_c))
    dp.add_handler(CommandHandler("strategies",     cmd_strategies))
    dp.add_handler(CommandHandler("set_confirm",    cmd_set_confirm))
    dp.add_handler(CommandHandler("add_confirm",    cmd_add_confirm))
    dp.add_handler(CommandHandler("remove_confirm", cmd_remove_confirm))
    dp.add_handler(CommandHandler("confirms",       cmd_confirms))

    updater.start_polling()
    print("✅ Telegram bot polling...")