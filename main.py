# ============================================================
#  main.py — Vòng lặp chính (PTB v20 compatible)
# ============================================================
import time
import asyncio
from telegram import Bot

from data import get_klines
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from telegram_bot import run_telegram
from formatter import format_entry, format_kumo_cross, format_startup
from state import state
from config import CHECK_INTERVAL, TIMEFRAMES, TOKEN, CHAT_ID

_bot = Bot(token=TOKEN)


def send(text: str):
    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(
            _bot.send_message(
                chat_id=state["chat_id"],
                text=text
            )
        )
    finally:
        loop.close()


def process_coin(symbol: str):
    # 1. Lấy dữ liệu 3 khung giờ
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    price = df_m15["close"].iloc[-1]

    # 2. Xu hướng H4 + H1
    trend = multi_trend(df_h4, df_h1)

    # 3. Kumo Cross H1 — chỉ báo 1 lần
    kumo = detect_kumo_cross(df_h1)
    if kumo and kumo != state["last_kumo_cross"].get(symbol):
        send(format_kumo_cross(symbol, kumo, price, "H1"))
        state["last_kumo_cross"][symbol] = kumo
        print(f"  ☁️  {symbol}: Kumo Cross {kumo} — đã gửi")
    elif not kumo:
        state["last_kumo_cross"][symbol] = None

    # 4. Entry 15m — chỉ khi H4+H1 đồng thuận
    if trend == "NO_TREND":
        print(f"  ⏭  {symbol}: H4+H1 không đồng thuận — bỏ qua")
        return

    setup = check_entry(df_m15, trend)
    if setup and setup["type"] != state["last_entry_signal"].get(symbol):
        send(format_entry(symbol, trend, "15m", setup))
        state["last_entry_signal"][symbol] = setup["type"]
        print(f"  📍 {symbol}: {setup['type']} ${setup['entry']} — đã gửi")
    elif not setup:
        state["last_entry_signal"][symbol] = None
        print(f"  —  {symbol}: trend={trend} | giá=${price:,.4f} | chưa có setup")


def loop():
    symbols = list(state["symbols"])
    if not symbols:
        print("  ⚠️  Danh sách trống. Dùng /add BTCUSDT")
        return
    for symbol in symbols:
        try:
            process_coin(symbol)
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")


def main():
    # Gửi tin khởi động
    run_telegram()

    time.sleep(3)

    send(format_startup(state["symbols"]))
    
    print(f"🚀 Bot chạy | {state['symbols']} | interval={CHECK_INTERVAL}s")

    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] ── Kiểm tra ──")
        loop()
        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()