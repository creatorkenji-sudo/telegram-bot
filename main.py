# ============================================================
#  main.py — Chạy hoàn toàn async, không dùng threading
# ============================================================
import asyncio
import time
from datetime import datetime
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

from data import get_klines
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from formatter import (
    format_entry, format_kumo_cross,
    format_startup, format_status,
    format_heartbeat
)
from state import state, add_symbol, remove_symbol
from config import CHECK_INTERVAL, TIMEFRAMES, TOKEN

# ── Bot instance dùng chung ──────────────────────────────────
bot = Bot(token=TOKEN)


# ── Gửi tin nhắn (async) ─────────────────────────────────────
async def send(text: str):
    await bot.send_message(chat_id=state["chat_id"], text=text)


# ── Telegram command handlers ────────────────────────────────
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


# ── Xử lý từng coin ─────────────────────────────────────────
async def process_coin(symbol: str):
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    price = df_m15["close"].iloc[-1]
    trend = multi_trend(df_h4, df_h1)

    # Kumo Cross H1 — chỉ báo 1 lần
    kumo = detect_kumo_cross(df_h1)
    if kumo and kumo != state["last_kumo_cross"].get(symbol):
        await send(format_kumo_cross(symbol, kumo, price, "H1"))
        state["last_kumo_cross"][symbol] = kumo
        print(f"  ☁️  {symbol}: Kumo Cross {kumo} — đã gửi")
    elif not kumo:
        state["last_kumo_cross"][symbol] = None

    # Entry 15m — chỉ khi H4+H1 đồng thuận
    if trend == "NO_TREND":
        print(f"  ⏭  {symbol}: không đồng thuận — bỏ qua")
        return

    setup = check_entry(df_m15, trend)
    if setup and setup["type"] != state["last_entry_signal"].get(symbol):
        await send(format_entry(symbol, trend, "15m", setup))
        state["last_entry_signal"][symbol] = setup["type"]
        print(f"  📍 {symbol}: {setup['type']} ${setup['entry']} — đã gửi")
    elif not setup:
        state["last_entry_signal"][symbol] = None
        print(f"  —  {symbol}: trend={trend} | ${price:,.4f} | chưa có setup")


# ── Vòng lặp quét tín hiệu ──────────────────────────────────
async def scanner_loop():
    last_heartbeat = time.time()
    HEARTBEAT_INTERVAL = 3600   # 1 giờ

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ── Kiểm tra ──")

        symbols = list(state["symbols"])
        if not symbols:
            print("  ⚠️  Danh sách trống. Dùng /add BTCUSDT")
        else:
            for symbol in symbols:
                try:
                    await process_coin(symbol)
                except Exception as e:
                    print(f"  ❌ {symbol}: {e}")

        # Heartbeat mỗi 1 giờ
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                await send(format_heartbeat(state["symbols"]))
                print("  💚 Heartbeat gửi OK")
            except Exception as e:
                print(f"  ❌ Heartbeat lỗi: {e}")
            last_heartbeat = time.time()

        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        await asyncio.sleep(CHECK_INTERVAL)


# ── Main: chạy scanner + Telegram polling song song ─────────
async def main():
    # Khởi động Telegram app
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("add",    cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("status", cmd_status))

    # Gửi tin khởi động
    await send(format_startup(state["symbols"]))
    print(f"🚀 Bot chạy | {state['symbols']} | interval={CHECK_INTERVAL}s")
    print("✅ Telegram bot polling...")

    # Chạy song song: polling + scanner
    async with app:
        await app.start()
        await app.updater.start_polling()

        # Chạy scanner loop
        await scanner_loop()

        # Dừng (sẽ không bao giờ tới đây trừ khi có lỗi)
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())