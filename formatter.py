# ============================================================
#  formatter.py — Tin nhắn Telegram tiếng Việt + icon
# ============================================================
from datetime import datetime, timezone, timedelta
from config import SL_PERCENT, RR_RATIO

_TZ_VN = timezone(timedelta(hours=7))

def _now():
    return datetime.now(_TZ_VN).strftime("%d/%m %H:%M") + " (UTC+7)"


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC A
# ════════════════════════════════════════════════════════════
def format_kumo_cross(symbol, direction, price, timeframe):
    coin = symbol.replace("USDT","")
    if direction == "UP":
        bar = "☁️🟢══════════════════🟢☁️"
        title = f"🚀  KUMO CROSS TĂNG — {coin}/USDT"
        desc  = "📈 Giá vừa CẮT LÊN TRÊN mây Ichimoku"
        sig   = "🐂 Tín hiệu TĂNG — chờ xác nhận entry"
    else:
        bar = "☁️🔴══════════════════🔴☁️"
        title = f"💥  KUMO CROSS GIẢM — {coin}/USDT"
        desc  = "📉 Giá vừa CẮT XUỐNG DƯỚI mây Ichimoku"
        sig   = "🐻 Tín hiệu GIẢM — chờ xác nhận entry"
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ {timeframe}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại : {price:,.4f} USDT\n"
        f"{desc}\n{sig}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Chỉ báo 1 lần · ☁️ Chiến lược A\n"
        f"{bar}"
    )


def format_ichimoku_entry(symbol, trend, timeframe, setup):
    coin  = symbol.replace("USDT","")
    entry = setup["entry"]
    sl, tp = setup["sl"], setup["tp"]
    sl_pct = abs(round((sl-entry)/entry*100, 2))
    tp_pct = abs(round((tp-entry)/entry*100, 2))
    if setup["type"] == "LONG":
        bar = "🟢══════════════════🟢"
        title = f"🚀  VÀO LỆNH LONG — {coin}/USDT"
        tl    = "📈 Xu hướng: TĂNG 🐂 (H4+H1)"
    else:
        bar = "🔴══════════════════🔴"
        title = f"📉  VÀO LỆNH SHORT — {coin}/USDT"
        tl    = "📉 Xu hướng: GIẢM 🐻 (H4+H1)"
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ {timeframe}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại  : {entry:,.4f} USDT\n"
        f"📍 Điểm vào      : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)  : {sl:,.4f}  (−{sl_pct}%)\n"
        f"🎯 Chốt lời (TP) : {tp:,.4f}  (+{tp_pct}%)\n"
        f"⚖️ R:R            : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{tl}\n"
        f"⚡ StochRSI 15m  : {setup['stoch']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️ Chiến lược A — Ichimoku + StochRSI\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC B
# ════════════════════════════════════════════════════════════
def format_ema_signal(symbol, sig):
    coin  = symbol.replace("USDT","")
    entry = sig["entry"]
    if sig["type"] == "LONG":
        bar = "📈🟢══════════════════🟢📈"
        title = f"🚀  EMA PULLBACK LONG — {coin}/USDT"
        tl    = "🐂 Xu hướng H1: TĂNG (EMA20 > EMA50)"
    else:
        bar = "📉🔴══════════════════🔴📉"
        title = f"💥  EMA PULLBACK SHORT — {coin}/USDT"
        tl    = "🐻 Xu hướng H1: GIẢM (EMA20 < EMA50)"
    passed_str = " · ".join(f"✅ {p}" for p in sig["passed"])
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ H1+15m\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại  : {entry:,.4f} USDT\n"
        f"📍 Điểm vào      : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)  : {sig['sl']:,.4f}  (−{sig['sl_pct']}%)\n"
        f"🎯 Chốt lời (TP) : {sig['tp']:,.4f}  (+{sig['tp_pct']}%)\n"
        f"⚖️ R:R            : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{tl}\n"
        f"📊 EMA H1: {sig['ema20_h1']} · {sig['ema50_h1']} · {sig['ema100_h1']}\n"
        f"📌 Pullback tại  : {sig['pullback_ema']}\n"
        f"📉 MACD histogram: đổi chiều {'🔼' if sig['macd_flip']=='UP' else '🔽'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Điều kiện : {sig['score']}\n"
        f"{passed_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHUNG
# ════════════════════════════════════════════════════════════
def format_startup(symbols_a: list, symbols_b: list) -> str:
    ca = " · ".join(s.replace("USDT","") for s in symbols_a) or "Trống"
    cb = " · ".join(s.replace("USDT","") for s in symbols_b) or "Trống"
    return (
        f"✅  BOT CRYPTO ALERT BẬT\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A (Ichimoku) : {ca}\n"
        f"📈 CL B (EMA+MACD)  : {cb}\n"
        f"⚖️ R:R : 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"/aa /ra  — thêm/xóa coin CL A\n"
        f"/ab /rb  — thêm/xóa coin CL B\n"
        f"/add /remove  — cả 2\n"
        f"/strategy_a  /strategy_b  /status"
    )


def format_status(symbols_a: list, symbols_b: list, strategies: dict = None) -> str:
    ca = "\n".join(f"  • {s}" for s in symbols_a) if symbols_a else "  (Trống)"
    cb = "\n".join(f"  • {s}" for s in symbols_b) if symbols_b else "  (Trống)"
    if strategies:
        a = "✅ BẬT" if strategies.get("ichimoku") else "❌ TẮT"
        b = "✅ BẬT" if strategies.get("ema")      else "❌ TẮT"
        strat = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️  Chiến lược:\n"
            f"  ☁️  A — Ichimoku : {a}\n"
            f"  📈 B — EMA+MACD  : {b}\n"
        )
    else:
        strat = ""
    return (
        f"📋  TRẠNG THÁI BOT\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A (Ichimoku):\n{ca}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 CL B (EMA+MACD):\n{cb}\n"
        f"{strat}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ R:R = 1:{RR_RATIO}  ·  SL {SL_PERCENT}%"
    )


def format_heartbeat(symbols_a: list, symbols_b: list, strategies: dict) -> str:
    ca = " · ".join(s.replace("USDT","") for s in symbols_a) or "Trống"
    cb = " · ".join(s.replace("USDT","") for s in symbols_b) or "Trống"
    a  = "✅" if strategies.get("ichimoku") else "❌"
    b  = "✅" if strategies.get("ema")      else "❌"
    return (
        f"💚  BOT ĐANG HOẠT ĐỘNG\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A {a}: {ca}\n"
        f"📈 CL B {b}: {cb}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Hoạt động bình thường"
    )


# Alias
format_entry = format_ichimoku_entry
format_setup = format_ichimoku_entry