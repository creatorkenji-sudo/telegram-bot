import time
import requests
from datetime import datetime
from data import get_klines
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from telegram_bot import run_telegram
from formatter import format_entry, format_kumo_cross, format_startup, format_heartbeat
from state import state
from config import CHECK_INTERVAL, TIMEFRAMES, TOKEN, CHAT_ID


def send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
    }, timeout=10)


def process_coin(symbol: str):
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    price = df_m15["close"].iloc[-1]
    trend = multi_trend(df_h4, df_h1)

    # Kumo Cross H1 — chỉ báo 1 lần
    kumo = detect_kumo_cross(df_h1)
    if kumo and kumo != state["last_kumo_cross"].get(symbol):
        send(format_kumo_cross(symbol, kumo, price, "H1"))
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
        send(format_entry(symbol, trend, "15m", setup))
        state["last_entry_signal"][symbol] = setup["type"]
        print(f"  📍 {symbol}: {setup['type']} ${setup['entry']} — đã gửi")
    elif not setup:
        state["last_entry_signal"][symbol] = None
        print(f"  —  {symbol}: trend={trend} | ${price:,.4f} | chưa có setup")


def main():
    send(format_startup(state["symbols"]))
    run_telegram()   # chạy trong thread riêng (PTB 13.x tự handle)

    print(f"🚀 Bot chạy | {state['symbols']} | interval={CHECK_INTERVAL}s")

    last_heartbeat = time.time()
    HEARTBEAT_INTERVAL = 3600

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ── Kiểm tra ──")

        symbols = list(state["symbols"])
        if not symbols:
            print("  ⚠️  Danh sách trống. Dùng /add BTCUSDT")
        else:
            for symbol in symbols:
                try:
                    process_coin(symbol)
                except Exception as e:
                    print(f"  ❌ {symbol}: {e}")

        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            try:
                send(format_heartbeat(state["symbols"]))
                print("  💚 Heartbeat OK")
            except Exception as e:
                print(f"  ❌ Heartbeat lỗi: {e}")
            last_heartbeat = time.time()

        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()