# ============================================================
#  main.py — Vòng lặp chính, 2 chiến lược danh sách riêng
# ============================================================
import time
import requests
from datetime import datetime

from data import get_klines
from trade_tracker import track_entry, check_all, format_result, get_stats, reset_history
from strategy_c import check_strategy_c
from strategy_d import check_strategy_d
from strategy_sr import check_strategy_sr, check_zone_reaction, DEFAULT_PARAMS as SR_DEFAULT_PARAMS
from trend import multi_trend, detect_kumo_cross
from entry import check_entry
from ema_strategy import check_ema_signal, check_sltp, get_trade_state
from telegram_bot import run_telegram
from formatter import (
    format_kumo_cross, format_ichimoku_entry,
    format_ema_signal, format_sltp_result, format_startup, format_heartbeat,
    format_strategy_c, format_strategy_d,
    format_sr_long, format_sr_short, format_sr_bos_long, format_sr_bos_break,
    format_sr_touch, format_sr_break, format_sr_reject,
    format_menu, format_status
)
from state import state
from config import CHECK_INTERVAL, TIMEFRAMES, TOKEN, CHAT_ID


def send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"  ❌ Telegram lỗi: {e}")



def _get_current_price(symbol: str) -> float:
    """Lấy giá hiện tại cho tracker."""
    df = get_klines(symbol, "1")   # nến 1 phút để lấy giá mới nhất
    return df["close"].iloc[-1]

# ── Chiến lược A: Ichimoku + StochRSI ───────────────────────
def run_strategy_a(symbol: str):
    if not state["strategies"]["ichimoku"]:
        return
    df_h4  = get_klines(symbol, TIMEFRAMES["h4"])
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])

    # Giá đóng cửa nến [-2] — không dùng giá đang chạy
    price = df_h1["close"].iloc[-2]
    trend = multi_trend(df_h4, df_h1)

    # Kumo Cross H1 — nhạy hơn (so nến [-2] vs [-3])
    kumo_h1 = detect_kumo_cross(df_h1, "H1")
    # Kumo Cross H4 — thêm H4
    kumo_h4 = detect_kumo_cross(df_h4, "H4")

    for kumo, tf_label in [(kumo_h1, "H1"), (kumo_h4, "H4")]:
        state_key = f"last_kumo_{tf_label}_{symbol}"
        if kumo and kumo["direction"] != state["last_kumo_cross"].get(state_key):
            # Thêm vị trí giá H1 + H4 vào cảnh báo
            from trend import _price_vs_cloud
            cross_info = {
                "cloud_top":   kumo["cloud_top"],
                "cloud_bot":   kumo["cloud_bot"],
                "price_pos_h1": _price_vs_cloud(df_h1, "H1"),
                "price_pos_h4": _price_vs_cloud(df_h4, "H4"),
            }
            send(format_kumo_cross(symbol, kumo["direction"], kumo["price"], tf_label, cross_info))
            state["last_kumo_cross"][state_key] = kumo["direction"]
            print(f"  ☁️  [A] {symbol}: Kumo Cross {kumo['direction']} {tf_label}")
        elif not kumo:
            state_key2 = f"last_kumo_{tf_label}_{symbol}"
            state["last_kumo_cross"][state_key2] = None

    if trend == "NO_TREND":
        print(f"  ⏭  [A] {symbol}: H4+H1 không đồng thuận")
        return

    setup = check_entry(df_m15, trend)
    if setup and setup["type"] != state["last_entry_signal"].get(symbol):
        send(format_ichimoku_entry(symbol, trend, "15m", setup))
        state["last_entry_signal"][symbol] = setup["type"]
        track_entry(symbol, "CL_A", setup["type"], setup["entry"], setup["sl"], setup["tp"])
        print(f"  📍 [A] {symbol}: {setup['type']} ${setup['entry']}")
    elif not setup:
        state["last_entry_signal"][symbol] = None
        print(f"  —  [A] {symbol}: trend={trend} | ${price:,.4f}")



def _in_cooldown_b(symbol: str, t: dict) -> tuple[bool, int]:
    from ema_strategy import COOLDOWN_SECONDS
    if t["ts_cooldown"] is None:
        return False, 0
    remaining = COOLDOWN_SECONDS - (time.time() - t["ts_cooldown"])
    return (True, int(remaining // 60)) if remaining > 0 else (False, 0)

# ── Chiến lược B: EMA Pullback + MACD ───────────────────────
def run_strategy_b(symbol: str):
    if not state["strategies"]["ema"]:
        return
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])
    price  = df_m15["close"].iloc[-1]

    # 1. Kiểm tra trạng thái hiện tại
    t = get_trade_state(symbol)

    # Đang IN_TRADE — chỉ check SL/TP/Timeout, KHÔNG tìm lệnh mới
    if t["status"] == "IN_TRADE":
        elapsed = round((time.time() - t["ts_entry"]) / 3600, 1)
        result  = check_sltp(symbol, price)
        if result:
            send(format_sltp_result(symbol, result))
            label = {"TP": "✅ TP", "SL": "❌ SL", "TIMEOUT": "⏰ Timeout"}[result["type"]]
            print(f"  {label} [B] {symbol}: {result['direction']} pnl={result['pnl_pct']}%")
        else:
            print(f"  🔒 [B] {symbol}: IN_TRADE {t['direction']} {elapsed:.1f}h/2h | ${price:,.4f} | SL={t['sl']} TP={t['tp']}")
        return  # ← thoát hẳn, không tìm lệnh mới

    # 2. IDLE — kiểm tra cooldown rồi tìm lệnh mới
    in_cd, mins_left = _in_cooldown_b(symbol, t)
    if in_cd:
        print(f"  ⏳ [B] {symbol}: cooldown còn {mins_left} phút")
        return

    df_h1 = get_klines(symbol, TIMEFRAMES["h1"])
    sig   = check_ema_signal(symbol, df_h1, df_m15,
                              state["filters_b"], state["min_pass_b"])
    if sig:
        send(format_ema_signal(symbol, sig))
        state["last_ema_signal"][symbol] = sig["type"]
        track_entry(symbol, "CL_B", sig["type"], sig["entry"], sig["sl"], sig["tp"])
        print(f"  📈 [B] {symbol}: {sig['type']} entry={sig['entry']} score={sig['score']}")
    else:
        print(f"  —  [B] {symbol}: ${price:,.4f} | tìm setup...")



# ── Chiến lược C: Supertrend + Confirmation ──────────────────
def run_strategy_c(symbol: str):
    if not state["strategies"].get("supertrend"):
        return
    df_h1 = get_klines(symbol, TIMEFRAMES["h1"])
    price = df_h1["close"].iloc[-1]
    sig   = check_strategy_c(symbol, df_h1, state["confirms_c"])

    if sig and sig["type"] != state["last_c_signal"].get(symbol):
        send(format_strategy_c(symbol, sig))
        state["last_c_signal"][symbol] = sig["type"]
        track_entry(symbol, "CL_C", sig["type"], sig["entry"], sig["sl"], sig["tp"])
        print(f"  ⚡ [C] {symbol}: {sig['type']} ${sig['entry']} score={sig['score']}")
    elif not sig:
        state["last_c_signal"][symbol] = None
        print(f"  —  [C] {symbol}: ${price:,.4f} | chờ tín hiệu")


# ── Chiến lược D: Ichimoku + Stochastic ─────────────────────
def run_strategy_d(symbol: str):
    if not state["strategies"].get("ichistoch"):
        return
    df_h1  = get_klines(symbol, TIMEFRAMES["h1"])
    df_m15 = get_klines(symbol, TIMEFRAMES["m15"])
    sig    = check_strategy_d(symbol, df_h1, df_m15)
    if sig:
        send(format_strategy_d(symbol, sig))
        state["last_d_signal"][symbol] = sig["type"]
        track_entry(symbol, "CL_D", sig["type"], sig["entry"], sig["sl"], sig["tp"])
        label = "⚡ Early" if sig["signal_type"] == "early" else "🚀 Confirm"
        print(f"  {label} [D] {symbol}: {sig['type']} ${sig['entry']}")
    else:
        price = df_m15["close"].iloc[-1]
        print(f"  —  [D] {symbol}: ${price:,.4f} | chờ tín hiệu")


# ── Chiến lược SR: Hỗ trợ Kháng cự ──────────────────────────
def _send_sr_signals(symbol: str, signals: list, tf_label: str, include_bos_break: bool):
    for sig in signals:
        t = sig["type"]
        sig["tf"] = tf_label
        if t == "LONG":
            send(format_sr_long(symbol, sig))
            track_entry(symbol, "CL_SR", "LONG", sig["entry"], sig["sl"], sig["tp"])
        elif t == "SHORT":
            send(format_sr_short(symbol, sig))
            track_entry(symbol, "CL_SR", "SHORT", sig["entry"], sig["sl"], sig["tp"])
        elif t == "BOS_LONG":
            send(format_sr_bos_long(symbol, sig))
        elif t == "BOS_BREAK" and include_bos_break:
            send(format_sr_bos_break(symbol, sig))
        elif t == "TOUCH":
            send(format_sr_touch(symbol, sig))
        elif t == "BREAK":
            send(format_sr_break(symbol, sig))
        elif t == "REJECT":
            send(format_sr_reject(symbol, sig))

def run_strategy_sr(symbol: str):
    if not state["strategies"].get("sr"):
        return
    # Check M5 — chỉ LONG/SHORT/BOS_LONG, KHÔNG báo BOS_BREAK (tránh spam)
    df_m5  = get_klines(symbol, TIMEFRAMES["m5"])
    sigs_m5 = check_strategy_sr(symbol + "_m5", df_m5, state)
    _send_sr_signals(symbol, sigs_m5, "5m", include_bos_break=True)
    # Check M15 — đầy đủ tất cả signal, BOS_BREAK xác nhận trên nến 15m đã đóng
    df_m15  = get_klines(symbol, TIMEFRAMES["m15"])
    sigs_m15 = check_strategy_sr(symbol + "_m15", df_m15, state)
    _send_sr_signals(symbol, sigs_m15, "15m", include_bos_break=True)

    # ── Zone Reaction (TOUCH/BREAK/REJECT) — khung tùy chỉnh qua /sr_set zone_reaction_tf ──
    sr_params = state.get("sr_params", {})
    if sr_params.get("touch_signal", False):
        zr_tf = sr_params.get("zone_reaction_tf", "h1")
        tf_code  = TIMEFRAMES.get(zr_tf, TIMEFRAMES["h1"])
        tf_label = {"m5": "5m", "m15": "15m", "h1": "1h", "h4": "4h"}.get(zr_tf, "1h")
        df_zr = get_klines(symbol, tf_code)
        sigs_zr = check_zone_reaction(symbol + "_" + zr_tf, df_zr, state)
        _send_sr_signals(symbol, sigs_zr, tf_label, include_bos_break=False)

# ── Main loop ────────────────────────────────────────────────
def main():
    send(format_startup(state["symbols_a"], state["symbols_b"], state["symbols_c"], state["symbols_d"], state["symbols_sr"], state["strategies"]))
    run_telegram()

    print(f"🚀 Bot V4 chạy | interval={CHECK_INTERVAL}s")
    print(f"   CL A coins: {state['symbols_a']}")
    print(f"   CL B coins: {state['symbols_b']}")

    last_heartbeat = time.time()

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ── Kiểm tra ──")

        # Chiến lược A — danh sách riêng
        for symbol in list(state["symbols_a"]):
            try:
                run_strategy_a(symbol)
            except Exception as e:
                print(f"  ❌ [A] {symbol}: {e}")

        # Chiến lược C — danh sách riêng
        for symbol in list(state["symbols_c"]):
            try:
                run_strategy_c(symbol)
            except Exception as e:
                print(f"  ❌ [C] {symbol}: {e}")

        # Chiến lược SR — Hỗ trợ Kháng cự
        for symbol in list(state["symbols_sr"]):
            try:
                run_strategy_sr(symbol)
            except Exception as e:
                print(f"  ❌ [SR] {symbol}: {e}")

        # Chiến lược D — danh sách riêng
        for symbol in list(state["symbols_d"]):
            try:
                run_strategy_d(symbol)
            except Exception as e:
                print(f"  ❌ [D] {symbol}: {e}")

        # Chiến lược B — danh sách riêng
        for symbol in list(state["symbols_b"]):
            try:
                run_strategy_b(symbol)
            except Exception as e:
                print(f"  ❌ [B] {symbol}: {e}")

        # Tracker: check SL/TP tất cả lệnh đang mở
        try:
            closed = check_all(_get_current_price)
            for record in closed:
                send(format_result(record))
        except Exception as e:
            print(f"  ⚠️  Tracker check lỗi: {e}")

        # Heartbeat mỗi 1 giờ
        if time.time() - last_heartbeat >= 3600:
            send(format_heartbeat(state["symbols_a"], state["symbols_b"], state["strategies"], state["symbols_c"], state["symbols_d"], state["symbols_sr"]))
            print("  💚 Heartbeat OK")
            last_heartbeat = time.time()

        print(f"  ⏳ Chờ {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()