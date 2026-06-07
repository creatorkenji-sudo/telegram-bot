# ============================================================
#  telegram_bot.py — Commands Telegram (PTB 13.x)
# ============================================================
from telegram.ext import Updater, CommandHandler
from state import state, add_symbol, remove_symbol, toggle_strategy, strategy_status
from config import TOKEN
from formatter import format_startup, format_status


def cmd_start(update, context):
    update.message.reply_text(format_startup(state["symbols"]))


def cmd_add(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /add BTCUSDT")
        return
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    if add_symbol(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol}\n"
            f"📋 Danh sách: {', '.join(state['symbols'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong danh sách rồi")


def cmd_remove(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /remove BTCUSDT")
        return
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    if remove_symbol(symbol):
        remaining = ', '.join(state['symbols']) if state['symbols'] else "Trống"
        update.message.reply_text(
            f"🗑 Đã xóa {symbol}\n"
            f"📋 Còn lại: {remaining}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong danh sách")


def cmd_list(update, context):
    if not state["symbols"]:
        update.message.reply_text("📋 Danh sách trống. Thêm bằng /add BTCUSDT")
        return
    coins = "\n".join(f"  • {s}" for s in state["symbols"])
    update.message.reply_text(f"📋 Đang theo dõi:\n{coins}")


def cmd_status(update, context):
    update.message.reply_text(format_status(state["symbols"], state["strategies"]))


def cmd_strategy_a(update, context):
    """Bật/tắt Chiến lược A (Ichimoku + StochRSI)."""
    new_state = toggle_strategy("ichimoku")
    icon  = "✅ BẬT" if new_state else "❌ TẮT"
    update.message.reply_text(
        f"☁️  Chiến lược A — Ichimoku + StochRSI\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )


def cmd_strategy_b(update, context):
    """Bật/tắt Chiến lược B (EMA Pullback + MACD)."""
    new_state = toggle_strategy("ema")
    icon  = "✅ BẬT" if new_state else "❌ TẮT"
    update.message.reply_text(
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )


def cmd_strategies(update, context):
    """Xem trạng thái tất cả chiến lược."""
    update.message.reply_text(strategy_status())


def run_telegram():
    updater = Updater(TOKEN, use_context=True)
    # Xóa webhook cũ trước khi polling — tránh conflict
    updater.bot.delete_webhook(drop_pending_updates=True)
    
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start",      cmd_start))
    dp.add_handler(CommandHandler("add",        cmd_add))
    dp.add_handler(CommandHandler("remove",     cmd_remove))
    dp.add_handler(CommandHandler("list",       cmd_list))
    dp.add_handler(CommandHandler("status",     cmd_status))
    dp.add_handler(CommandHandler("strategy_a", cmd_strategy_a))
    dp.add_handler(CommandHandler("strategy_b", cmd_strategy_b))
    dp.add_handler(CommandHandler("strategies", cmd_strategies))

    updater.start_polling()
    print("✅ Telegram bot polling...")