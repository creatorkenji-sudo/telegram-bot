# ============================================================
#  main.py — Vòng lặp chính xử lý song song từng coin
# ============================================================
import time
from data import get_klines
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from telegram_bot import run_telegram, send
from formatter import format_entry, format_kumo_cross, format_startup
from state import state
from config import CHECK_INTERVAL, TIMEFRAMES


def process_coin(symbol: str):
    """Xử lý toàn bộ logic cho 1 coin."""

    # ── 1. Lấy dữ liệu 3 khung giờ ──────────────────────────
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    price = df_m15["close"].iloc[-1]

    # ── 2. Xác định xu hướng H4 + H1 ─────────────────────────
    trend = multi_trend(df_h4, df_h1)

    # ── 3. Phát hiện Kumo Cross trên H1 (chỉ báo 1 lần) ──────
    kumo = detect_kumo_cross(df_h1)
    if kumo and kumo != state["last_kumo_cross"].get(symbol):
        msg = format_kumo_cross(symbol, kumo, price, "H1")
        send(msg)
        state["last_kumo_cross"][symbol] = kumo
        print(f"  ☁️  {symbol}: Kumo Cross {kumo} — đã gửi")
    elif not kumo:
        # Reset khi không còn ở trạng thái cross
        state["last_kumo_cross"][symbol] = None

    # ── 4. Tìm điểm vào lệnh 15m (chỉ khi trend đồng thuận) ──
    if trend == "NO_TREND":
        print(f"  ⏭  {symbol}: H4+H1 không đồng thuận — bỏ qua")
        return

    setup = check_entry(df_m15, trend)

    if setup and setup["type"] != state["last_entry_signal"].get(symbol):
        msg = format_entry(symbol, trend, "15m", setup)
        send(msg)
        state["last_entry_signal"][symbol] = setup["type"]
        print(f"  📍 {symbol}: {setup['type']} entry ${setup['entry']} — đã gửi")
    elif not setup:
        # Reset khi điều kiện không còn thỏa
        state["last_entry_signal"][symbol] = None
        print(f"  —  {symbol}: trend={trend} | giá=${price:,.4f} | chưa có setup")


def loop():
    symbols = list(state["symbols"])   # snapshot để tránh thay đổi giữa vòng lặp
    if not symbols:
        print("  ⚠️  Danh sách coin trống. Thêm bằng /add BTCUSDT")
        return

    for symbol in symbols:
        try:
            process_coin(symbol)
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")


def main():
    # Gửi tin khởi động
    send(format_startup(state["symbols"]))

    # Chạy Telegram polling (thread riêng)
    run_telegram()

    print(f"🚀 Bot chạy | coins: {state['symbols']} | interval: {CHECK_INTERVAL}s")

    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] ── Kiểm tra ──")
        loop()
        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
