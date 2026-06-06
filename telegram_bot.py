# ============================================================
#  telegram_bot.py — PTB v20 (Python 3.12 compatible)
# ============================================================
import asyncio
import threading
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

from config import TOKEN, CHAT_ID
from state import state, add_symbol, remove_symbol
from formatter import format_status, format_startup

# Bot instance dùng chung để gửi tin
_bot = Bot(token=TOKEN)


# ── Gửi tin nhắn (sync — gọi từ main loop) ──────────────────
def send(text: str, chat_id: str = None):
    cid = chat_id or state["chat_id"]
    asyncio.run(_bot.send_message(chat_id=cid, text=text))


# ── Command handlers (async — PTB v20) ──────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_startup(state["symbols"]))


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Dùng: /add BTCUSDT")
        return
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    if add_symbol(symbol):
        await update.message.reply_text(
            f"✅ Đã thêm {symbol}\n"
            f"📋 Danh sách: {', '.join(state['symbols'])}"
        )
    else:
        await update.message.reply_text(f"⚠️ {symbol} đã có trong danh sách rồi")


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Dùng: /remove BTCUSDT")
        return
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    if remove_symbol(symbol):
        remaining = ', '.join(state['symbols']) if state['symbols'] else "Trống"
        await update.message.reply_text(
            f"🗑 Đã xóa {symbol}\n"
            f"📋 Còn lại: {remaining}"
        )
    else:
        await update.message.reply_text(f"⚠️ {symbol} không có trong danh sách")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state["symbols"]:
        await update.message.reply_text("📋 Danh sách trống. Thêm bằng /add BTCUSDT")
        return
    coins = "\n".join(f"  • {s}" for s in state["symbols"])
    await update.message.reply_text(f"📋 Đang theo dõi:\n{coins}")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_status(state["symbols"]))


# ── Chạy polling trong thread riêng ─────────────────────────
def run_telegram():
    def _run():
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start",  cmd_start))
        app.add_handler(CommandHandler("add",    cmd_add))
        app.add_handler(CommandHandler("remove", cmd_remove))
        app.add_handler(CommandHandler("list",   cmd_list))
        app.add_handler(CommandHandler("status", cmd_status))
        print("✅ Telegram bot polling...")
        app.run_polling()

    t = threading.Thread(target=_run, daemon=True)
    t.start()