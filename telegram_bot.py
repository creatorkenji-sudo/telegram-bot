# ============================================================
#  telegram_bot.py — Nhận lệnh Telegram + gửi tin nhắn
# ============================================================
import requests
from telegram import Bot
from telegram.ext import Updater, CommandHandler

from config import TOKEN, CHAT_ID
from state import state, add_symbol, remove_symbol
from formatter import format_status, format_startup

bot = Bot(token=TOKEN)


# ── Gửi tin nhắn ────────────────────────────────────────────
def send(text: str, chat_id: str = None):
    cid = chat_id or state["chat_id"]
    bot.send_message(chat_id=cid, text=text)


# ── Command handlers ─────────────────────────────────────────
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
        update.message.reply_text("📋 Danh sách đang trống. Thêm bằng /add BTCUSDT")
        return
    coins = "\n".join(f"  • {s}" for s in state["symbols"])
    update.message.reply_text(f"📋 Đang theo dõi:\n{coins}")


def cmd_status(update, context):
    update.message.reply_text(format_status(state["symbols"]))


# ── Khởi động polling ────────────────────────────────────────
def run_telegram():
    updater = Updater(TOKEN, use_context=True)
    dp      = updater.dispatcher

    dp.add_handler(CommandHandler("start",  cmd_start))
    dp.add_handler(CommandHandler("add",    cmd_add))
    dp.add_handler(CommandHandler("remove", cmd_remove))
    dp.add_handler(CommandHandler("list",   cmd_list))
    dp.add_handler(CommandHandler("status", cmd_status))

    updater.start_polling()
    print("✅ Telegram bot polling...")
