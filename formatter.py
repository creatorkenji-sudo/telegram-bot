# ============================================================
#  formatter.py — Tin nhắn Telegram tiếng Việt + icon
# ============================================================
from datetime import datetime
from config import SL_PERCENT, RR_RATIO


def _now():
    return datetime.now().strftime("%d/%m %H:%M")


# ── Alias để tránh lỗi import ───────────────────────────────
def format_setup(symbol, trend, timeframe, setup):
    """Alias cũ — gọi sang format_entry."""
    return format_entry(symbol, trend, timeframe, setup)


def format_entry(symbol: str, trend: str, timeframe: str, setup: dict) -> str:
    coin  = symbol.replace("USDT", "")
    entry = setup["entry"]
    sl    = setup["sl"]
    tp    = setup["tp"]
    stoch = setup["stoch"]

    sl_pct = abs(round((sl - entry) / entry * 100, 2))
    tp_pct = abs(round((tp - entry) / entry * 100, 2))

    if setup["type"] == "LONG":
        bar    = "🟢══════════════════🟢"
        title  = f"🚀  VÀO LỆNH LONG — {coin}/USDT"
        trend_l = "📈 Xu hướng : TĂNG 🐂  (H4 + H1)"
    else:
        bar    = "🔴══════════════════🔴"
        title  = f"📉  VÀO LỆNH SHORT — {coin}/USDT"
        trend_l = "📉 Xu hướng : GIẢM 🐻  (H4 + H1)"

    return (
        f"{bar}\n"
        f"{title}\n"
        f"⏰ Khung vào lệnh : {timeframe}\n"
        f"🕐 Thời gian      : {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại   : {entry:,.4f} USDT\n"
        f"📍 Điểm vào       : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)   : {sl:,.4f}  (−{sl_pct}%)\n"
        f"🎯 Chốt lời (TP)  : {tp:,.4f}  (+{tp_pct}%)\n"
        f"⚖️ Tỷ lệ R:R      : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{trend_l}\n"
        f"⚡ StochRSI 15m   : {stoch}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


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
        f"{bar}\n"
        f"{title}\n"
        f"⏰ Khung phát hiện : {timeframe}\n"
        f"🕐 Thời gian       : {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại    : {price:,.4f} USDT\n"
        f"{desc}\n"
        f"{signal}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Chỉ báo 1 lần — không lặp lại\n"
        f"{bar}"
    )


def format_startup(symbols: list) -> str:
    coin_list = " · ".join(s.replace("USDT", "") for s in symbols)
    return (
        f"✅  BOT CRYPTO ALERT BẬT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Theo dõi  : {coin_list}\n"
        f"⏱ Khung giờ : H4 + H1 (trend) · 15m (entry)\n"
        f"☁️ Chỉ báo   : Ichimoku + StochRSI\n"
        f"⚖️ R:R       : 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Lệnh: /add COIN · /remove COIN · /list · /status"
    )


def format_status(symbols: list) -> str:
    coin_list = "\n".join(f"  • {s}" for s in symbols) if symbols else "  (Trống)"
    return (
        f"📋  TRẠNG THÁI BOT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 Đang theo dõi:\n{coin_list}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ R:R = 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"⏱ Khung: H4 + H1 + 15m\n"
        f"🕐 Cập nhật: {_now()}"
    )


def format_heartbeat(symbols: list) -> str:
    """Báo trạng thái hoạt động mỗi 1 giờ."""
    coin_list = " · ".join(s.replace("USDT", "") for s in symbols) if symbols else "Trống"
    return (
        f"💚  BOT ĐANG HOẠT ĐỘNG\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {_now()}\n"
        f"📊 Theo dõi : {coin_list}\n"
        f"⏱ Đang quét : H4 · H1 · 15m\n"
        f"☁️ Ichimoku + StochRSI\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Tất cả hoạt động bình thường"
    )