# ============================================================
#  formatter.py — Tin nhắn Telegram tiếng Việt + icon
# ============================================================
from datetime import datetime, timezone, timedelta
from config import SL_PERCENT, RR_RATIO

_TZ_VN = timezone(timedelta(hours=7))   # UTC+7 Việt Nam


def _now():
    return datetime.now(_TZ_VN).strftime("%d/%m %H:%M")


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC A — Ichimoku + StochRSI
# ════════════════════════════════════════════════════════════
def format_kumo_cross(symbol: str, direction: str, price: float, timeframe: str) -> str:
    coin = symbol.replace("USDT", "")
    if direction == "UP":
        bar    = "☁️🟢══════════════════🟢☁️"
        title  = f"🚀  KUMO CROSS TĂNG — {coin}/USDT"
        desc   = "📈 Giá vừa CẮT LÊN TRÊN mây Ichimoku"
        signal = "🐂 Tín hiệu TĂNG — chờ xác nhận entry"
    else:
        bar    = "☁️🔴══════════════════🔴☁️"
        title  = f"💥  KUMO CROSS GIẢM — {coin}/USDT"
        desc   = "📉 Giá vừa CẮT XUỐNG DƯỚI mây Ichimoku"
        signal = "🐻 Tín hiệu GIẢM — chờ xác nhận entry"
    return (
        f"{bar}\n{title}\n"
        f"⏰ Khung: {timeframe}  ·  🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại : {price:,.4f} USDT\n"
        f"{desc}\n{signal}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Chỉ báo 1 lần · Chiến lược A\n"
        f"{bar}"
    )


def format_ichimoku_entry(symbol: str, trend: str, timeframe: str, setup: dict) -> str:
    coin  = symbol.replace("USDT", "")
    entry = setup["entry"]
    sl, tp = setup["sl"], setup["tp"]
    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    if setup["type"] == "LONG":
        bar    = "🟢══════════════════🟢"
        title  = f"🚀  VÀO LỆNH LONG — {coin}/USDT"
        trend_l = "📈 Xu hướng: TĂNG 🐂  (H4 + H1)"
    else:
        bar    = "🔴══════════════════🔴"
        title  = f"📉  VÀO LỆNH SHORT — {coin}/USDT"
        trend_l = "📉 Xu hướng: GIẢM 🐻  (H4 + H1)"
    return (
        f"{bar}\n{title}\n"
        f"⏰ Khung vào lệnh: {timeframe}  ·  🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại  : {entry:,.4f} USDT\n"
        f"📍 Điểm vào      : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)  : {sl:,.4f}  (−{sl_pct}%)\n"
        f"🎯 Chốt lời (TP) : {tp:,.4f}  (+{tp_pct}%)\n"
        f"⚖️ R:R            : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{trend_l}\n"
        f"⚡ StochRSI 15m  : {setup['stoch']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️ Chiến lược A — Ichimoku + StochRSI\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC B — EMA Pullback + MACD
# ════════════════════════════════════════════════════════════
def format_ema_signal(symbol: str, sig: dict) -> str:
    coin  = symbol.replace("USDT", "")
    entry = sig["entry"]

    if sig["type"] == "LONG":
        bar    = "📈🟢══════════════════🟢📈"
        title  = f"🚀  EMA PULLBACK LONG — {coin}/USDT"
        trend_l = "🐂 Xu hướng H1: TĂNG  (EMA20 > EMA50)"
        sl_icon = "🛡"
    else:
        bar    = "📉🔴══════════════════🔴📉"
        title  = f"💥  EMA PULLBACK SHORT — {coin}/USDT"
        trend_l = "🐻 Xu hướng H1: GIẢM  (EMA20 < EMA50)"
        sl_icon = "🛡"

    # Hiện điều kiện đã pass
    passed_str = " · ".join(f"✅ {p}" for p in sig["passed"])

    return (
        f"{bar}\n{title}\n"
        f"⏰ Khung: H1 + 15m  ·  🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại  : {entry:,.4f} USDT\n"
        f"📍 Điểm vào      : {entry:,.4f}\n"
        f"{sl_icon} Cắt lỗ (SL)  : {sig['sl']:,.4f}  (−{sig['sl_pct']}%)\n"
        f"🎯 Chốt lời (TP) : {sig['tp']:,.4f}  (+{sig['tp_pct']}%)\n"
        f"⚖️ R:R            : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{trend_l}\n"
        f"📊 EMA H1: {sig['ema20_h1']} · {sig['ema50_h1']} · {sig['ema100_h1']}\n"
        f"📌 Pullback tại  : {sig['pullback_ema']}\n"
        f"📉 MACD histogram: đổi chiều {'🔼' if sig['macd_flip'] == 'UP' else '🔽'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Điều kiện đạt : {sig['score']}\n"
        f"{passed_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHUNG
# ════════════════════════════════════════════════════════════
def format_startup(symbols: list) -> str:
    coins = " · ".join(s.replace("USDT", "") for s in symbols)
    return (
        f"✅  BOT CRYPTO ALERT BẬT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Theo dõi  : {coins}\n"
        f"☁️  Chiến lược A : Ichimoku + StochRSI\n"
        f"📈 Chiến lược B : EMA Pullback + MACD\n"
        f"⚖️ R:R          : 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"/add /remove /list /status\n"
        f"/strategy_a  /strategy_b  (bật/tắt chiến lược)"
    )


def format_status(symbols: list) -> str:
    coins = "\n".join(f"  • {s}" for s in symbols) if symbols else "  (Trống)"
    return (
        f"📋  TRẠNG THÁI BOT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 Đang theo dõi:\n{coins}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ R:R = 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"⏱ H4 + H1 + 15m\n"
        f"🕐 {_now()}"
    )


def format_heartbeat(symbols: list, strategies: dict) -> str:
    coins = " · ".join(s.replace("USDT", "") for s in symbols) if symbols else "Trống"
    a = "✅" if strategies.get("ichimoku") else "❌"
    b = "✅" if strategies.get("ema")      else "❌"
    return (
        f"💚  BOT ĐANG HOẠT ĐỘNG\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {_now()}\n"
        f"📊 Theo dõi : {coins}\n"
        f"☁️  CL A Ichimoku : {a}\n"
        f"📈 CL B EMA+MACD  : {b}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Hoạt động bình thường"
    )


# Alias tránh lỗi import cũ
format_entry = format_ichimoku_entry
format_setup = format_ichimoku_entry