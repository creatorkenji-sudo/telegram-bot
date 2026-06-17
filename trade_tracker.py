# ============================================================
#  trade_tracker.py — Theo dõi SL/TP độc lập
#
#  Không đụng vào CL A/B/C/D
#  Chỉ cần các CL gọi track_entry() khi có signal
#  Tự động check SL/TP mỗi vòng lặp
#  Báo Telegram khi chạm + lưu thống kê 7 ngày
# ============================================================
import json
import os
import time
from datetime import datetime, timezone, timedelta

TRACKER_FILE = "/tmp/trade_tracker.json"
TZ_VN        = timezone(timedelta(hours=7))
RR_RATIO     = 2      # R:R 1:2 cho tất cả CL
STATS_DAYS   = 7      # thống kê 7 ngày


# ════════════════════════════════════════════════════════════
#  FILE I/O
# ════════════════════════════════════════════════════════════
def _load() -> dict:
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"active": {}, "history": []}


def _save(data: dict):
    try:
        with open(TRACKER_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠️  Tracker save lỗi: {e}")


def _now_ts() -> float:
    return time.time()


def _now_str() -> str:
    return datetime.now(TZ_VN).strftime("%d/%m %H:%M") + " (UTC+7)"


# ════════════════════════════════════════════════════════════
#  TRACK ENTRY — gọi từ CL khi có signal
# ════════════════════════════════════════════════════════════
def track_entry(symbol: str, strategy: str,
                direction: str, entry: float,
                sl: float, tp: float):
    """
    Lưu lệnh mới vào tracker.
    Tự tính lại TP theo R:R 1:2 từ SL.
    """
    data = _load()

    # Tính lại TP theo R:R 1:2
    if direction == "LONG":
        risk = entry - sl
        tp_rr2 = round(entry + risk * RR_RATIO, 6)
    else:
        risk = sl - entry
        tp_rr2 = round(entry - risk * RR_RATIO, 6)

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp_rr2 - entry) / entry * 100, 2))

    key = f"{strategy}_{symbol}"
    data["active"][key] = {
        "symbol":    symbol,
        "strategy":  strategy,
        "direction": direction,
        "entry":     entry,
        "sl":        sl,
        "tp":        tp_rr2,      # TP theo R:R 1:2
        "tp_orig":   tp,          # TP gốc của CL
        "sl_pct":    sl_pct,
        "tp_pct":    tp_pct,
        "ts_entry":  _now_ts(),
        "time_str":  _now_str(),
    }
    _save(data)
    print(f"  📝 Tracker: {strategy} {symbol} {direction} entry={entry} sl={sl} tp={tp_rr2}")


# ════════════════════════════════════════════════════════════
#  CHECK SL/TP — gọi mỗi vòng lặp
# ════════════════════════════════════════════════════════════
def check_all(get_price_fn) -> list[dict]:
    """
    Kiểm tra tất cả lệnh đang active.
    get_price_fn(symbol) -> float: hàm lấy giá hiện tại

    Trả về list các lệnh đã đóng trong vòng này.
    """
    data    = _load()
    closed  = []
    to_del  = []

    for key, trade in data["active"].items():
        symbol    = trade["symbol"]
        direction = trade["direction"]
        entry     = trade["entry"]
        sl        = trade["sl"]
        tp        = trade["tp"]

        try:
            price = get_price_fn(symbol)
        except Exception as e:
            print(f"  ⚠️  Tracker get_price {symbol}: {e}")
            continue

        result_type = None

        if direction == "LONG":
            if price >= tp:
                result_type = "TP"
            elif price <= sl:
                result_type = "SL"
        else:
            if price <= tp:
                result_type = "TP"
            elif price >= sl:
                result_type = "SL"

        if result_type:
            pnl = round((price - entry) / entry * 100 * (1 if direction == "LONG" else -1), 2)
            record = {
                **trade,
                "result":     result_type,
                "exit_price": price,
                "pnl_pct":    pnl,
                "ts_exit":    _now_ts(),
                "time_exit":  _now_str(),
            }
            closed.append(record)
            to_del.append(key)

            # Lưu vào history
            data["history"].append(record)
            print(f"  {'✅' if result_type=='TP' else '❌'} Tracker: {trade['strategy']} {symbol} {result_type} pnl={pnl}%")

    # Xóa lệnh đã đóng
    for key in to_del:
        del data["active"][key]

    _save(data)
    return closed


# ════════════════════════════════════════════════════════════
#  FORMAT ALERT — tin nhắn Telegram khi SL/TP
# ════════════════════════════════════════════════════════════
def format_result(record: dict) -> str:
    coin     = record["symbol"].replace("USDT","")
    strategy = record["strategy"].upper()
    rtype    = record["result"]
    direction= record["direction"]
    entry    = record["entry"]
    exit_p   = record["exit_price"]
    pnl      = record["pnl_pct"]
    dir_icon = "🟢 LONG" if direction == "LONG" else "🔴 SHORT"
    cl_map   = {"A": "☁️", "B": "📈", "C": "⚡", "D": "🌊"}
    cl_icon  = cl_map.get(strategy.replace("CL","").strip(), "📊")

    if rtype == "TP":
        bar   = "🎯🟢══════════════════🟢🎯"
        title = f"✅ CHỐT LỜI — {coin}/USDT"
        pstr  = f"+{abs(pnl):.2f}%"
    else:
        bar   = "🛡🔴══════════════════🔴🛡"
        title = f"❌ CẮT LỖ — {coin}/USDT"
        pstr  = f"-{abs(pnl):.2f}%"

    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now_str()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Hướng lệnh  : {dir_icon}\n"
        f"📍 Giá vào     : {entry:,.4f}\n"
        f"💰 Giá thoát   : {exit_p:,.4f}\n"
        f"📊 P&L         : {pstr}\n"
        f"⚖️ R:R          : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{cl_icon} {record['strategy']} · Vào lệnh: {record['time_str']}\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  STATS — thống kê 7 ngày
# ════════════════════════════════════════════════════════════
def get_stats() -> str:
    data     = _load()
    history  = data.get("history", [])
    active   = data.get("active", {})
    cutoff   = _now_ts() - STATS_DAYS * 86400

    # Lọc 7 ngày
    recent = [h for h in history if h.get("ts_exit", 0) >= cutoff]

    if not recent and not active:
        return (
            f"📊 THỐNG KÊ BOT — 7 ngày\n"
            f"🕐 {_now_str()}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Chưa có lệnh đã đóng.\n"
            f"(Lệnh đang mở sẽ được tính khi chạm TP/SL)"
        )

    # Tổng hợp theo chiến lược
    strategies = ["A", "B", "C", "D"]
    cl_map = {"A": "☁️ CL A", "B": "📈 CL B", "C": "⚡ CL C", "D": "🌊 CL D"}

    total_tp = sum(1 for h in recent if h["result"] == "TP")
    total_sl = sum(1 for h in recent if h["result"] == "SL")
    total    = len(recent)
    winrate  = round(total_tp / total * 100) if total > 0 else 0
    avg_pnl  = round(sum(h["pnl_pct"] for h in recent) / total, 2) if total > 0 else 0

    lines = [
        f"📊 THỐNG KÊ BOT — 7 ngày",
        f"🕐 {_now_str()}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📈 Tổng lệnh  : {total}",
        f"✅ TP         : {total_tp}",
        f"❌ SL         : {total_sl}",
        f"🎯 Win rate   : {winrate}%",
        f"💰 PnL TB     : {avg_pnl:+.2f}%",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    # Chi tiết từng CL
    for s in strategies:
        cl_trades = [h for h in recent if h.get("strategy","").upper() == f"CL_{s}"]
        if not cl_trades:
            continue
        cl_tp = sum(1 for h in cl_trades if h["result"] == "TP")
        cl_sl = sum(1 for h in cl_trades if h["result"] == "SL")
        cl_n  = len(cl_trades)
        cl_wr = round(cl_tp / cl_n * 100) if cl_n > 0 else 0
        lines.append(f"{cl_map[s]}: {cl_n} lệnh | ✅{cl_tp} ❌{cl_sl} | WR {cl_wr}%")

    # Đang mở
    n_active = len(active)
    if n_active:
        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"🔒 Đang mở: {n_active} lệnh")
        for k, t in sorted(active.items(), key=lambda x: x[1].get("ts_entry",0), reverse=True)[:5]:
            elapsed = round((time.time() - t["ts_entry"]) / 3600, 1)
            lines.append(f"  • {t['strategy']} {t['symbol'].replace('USDT','')} {t['direction']} {elapsed}h")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"💡 /reset_tracker để xóa lịch sử")
    return "\n".join(lines)


def reset_history():
    """Xóa toàn bộ lịch sử, giữ active."""
    data = _load()
    data["history"] = []
    _save(data)