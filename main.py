# ============================================================
#  main.py — Vòng lặp chính, chạy 2 chiến lược song song
# ============================================================
import time
import requests
from datetime import datetime

from data import get_klines
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from ema_strategy import check_ema_signal
from telegram_bot import run_telegram
from formatter import (
    format_kumo_cross, format_ichimoku_entry,
    format_ema_signal, format_startup,
    format_heartbeat
)
from state import state
from config import CHECK_INTERVAL, TIMEFRAMES, TOKEN, CHAT_ID


# ── Gửi Telegram ────────────────────────────────────────────
def send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text":    text,
        }, timeout=10)
    except Exception as e:
        print(f"  ❌ Gửi Telegram lỗi: {e}")


# ── Chiến lược A: Ichimoku + StochRSI ───────────────────────
def run_strategy_a(symbol: str, df_h4, df_h1, df_m15):
    if not state["strategies"]["ichimoku"]:
        return

    price = df_m15["close"].iloc[-1]
    trend = multi_trend(df_h4, df_h1)

    # Kumo Cross H1 — 1 lần
    kumo = detect_kumo_cross(df_h1)
    if kumo and kumo != state["last_kumo_cross"].get(symbol):
        send(format_kumo_cross(symbol, kumo, price, "H1"))
        state["last_kumo_cross"][symbol] = kumo
        print(f"  ☁️  [A] {symbol}: Kumo Cross {kumo}")
    elif not kumo:
        state["last_kumo_cross"][symbol] = None

    # Entry 15m
    if trend == "NO_TREND":
        print(f"  ⏭  [A] {symbol}: H4+H1 không đồng thuận")
        return

    setup = check_entry(df_m15, trend)
    if setup and setup["type"] != state["last_entry_signal"].get(symbol):
        send(format_ichimoku_entry(symbol, trend, "15m", setup))
        state["last_entry_signal"][symbol] = setup["type"]
        print(f"  📍 [A] {symbol}: {setup['type']} ${setup['entry']}")
    elif not setup:
        state["last_entry_signal"][symbol] = None
        print(f"  —  [A] {symbol}: trend={trend} | ${price:,.4f} | chưa setup")


# ── Chiến lược B: EMA Pullback + MACD ───────────────────────
def run_strategy_b(symbol: str, df_h1, df_m15):
    if not state["strategies"]["ema"]:
        return

    price = df_m15["close"].iloc[-1]
    sig   = check_ema_signal(df_h1, df_m15)

    if sig and sig["type"] != state["last_ema_signal"].get(symbol):
        send(format_ema_signal(symbol, sig))
        state["last_ema_signal"][symbol] = sig["type"]
        print(f"  📈 [B] {symbol}: {sig['type']} pullback {sig['pullback_ema']} score={sig['score']}")
    elif not sig:
        state["last_ema_signal"][symbol] = None
        print(f"  —  [B] {symbol}: ${price:,.4f} | chưa đủ 2/3 điều kiện")


# ── Xử lý 1 coin ────────────────────────────────────────────
def process_coin(symbol: str):
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    run_strategy_a(symbol, df_h4, df_h1, df_m15)
    run_strategy_b(symbol, df_h1, df_m15)


# ── Main loop ────────────────────────────────────────────────
def main():
    send(format_startup(state["symbols"]))
    run_telegram()

    print(f"🚀 Bot V4 | {state['symbols']} | interval={CHECK_INTERVAL}s")
    print(f"   Chiến lược A (Ichimoku): {'BẬT' if state['strategies']['ichimoku'] else 'TẮT'}")
    print(f"   Chiến lược B (EMA+MACD): {'BẬT' if state['strategies']['ema'] else 'TẮT'}")

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

        # Heartbeat
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            send(format_heartbeat(state["symbols"], state["strategies"]))
            print("  💚 Heartbeat OK")
            last_heartbeat = time.time()

        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
