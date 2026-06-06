from telegram.ext import Updater, CommandHandler
from state import state
from config import TOKEN


def start(update, context):
    update.message.reply_text("Bot Multi-Timeframe đã chạy")


def set_symbol(update, context):
    state["symbol"] = context.args[0].upper()
    update.message.reply_text(f"Symbol: {state['symbol']}")


def set_tf(update, context):
    # không bắt buộc nhưng để mở rộng
    update.message.reply_text("Bot dùng H1 + H4 + M15 cố định")


def run_telegram():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_symbol))
    dp.add_handler(CommandHandler("tf", set_tf))

    updater.start_polling()