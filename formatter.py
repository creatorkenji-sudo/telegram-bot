# ============================================================
#  formatter.py — Tin nhắn Telegram tiếng Việt + icon
# ============================================================
from datetime import datetime, timezone, timedelta
from config import SL_PERCENT, RR_RATIO

_TZ_VN = timezone(timedelta(hours=7))

def _now():
    return datetime.now(_TZ_VN).strftime("%d/%m %H:%M") + " (UTC+7)"

def _fmt(symbols): 
    return " · ".join(s.replace("USDT","") for s in symbols) or "Trống"

def _fmt_list(symbols):
    return "\n".join(f"  • {s}" for s in symbols) if symbols else "  (Trống)"


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC A — Ichimoku + StochRSI
# ════════════════════════════════════════════════════════════
def format_kumo_cross(symbol, direction, price, timeframe, cross_info=None):
    coin = symbol.replace("USDT","")
    if direction == "UP":
        bar   = "☁️🟢══════════════════🟢☁️"
        title = f"🚀  KUMO CROSS TĂNG — {coin}/USDT"
        desc  = "📈 Giá vừa ĐÓNG CẮT LÊN TRÊN mây"
        sig   = "🐂 Tín hiệu TĂNG — chờ xác nhận entry"
    else:
        bar   = "☁️🔴══════════════════🔴☁️"
        title = f"💥  KUMO CROSS GIẢM — {coin}/USDT"
        desc  = "📉 Giá vừa ĐÓNG CẮT XUỐNG DƯỚI mây"
        sig   = "🐻 Tín hiệu GIẢM — chờ xác nhận entry"
    detail = ""
    if cross_info:
        ktop   = cross_info.get("cloud_top", 0)
        kbot   = cross_info.get("cloud_bot", 0)
        pos_h1 = cross_info.get("price_pos_h1", "")
        pos_h4 = cross_info.get("price_pos_h4", "")
        detail = f"━━━━━━━━━━━━━━━━━━━━\n📊 Vùng mây: {kbot:,.4f} – {ktop:,.4f}\n"
        if pos_h1:
            detail += f"{pos_h1}\n"
        if pos_h4:
            detail += f"{pos_h4}\n"
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ {timeframe}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá đóng cửa : {price:,.4f} USDT\n"
        f"{desc}\n{sig}\n"
        f"{detail}"
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
#  CHIẾN LƯỢC B — EMA Pullback + MACD
# ════════════════════════════════════════════════════════════
def format_ema_signal(symbol, sig):
    coin  = symbol.replace("USDT","")
    entry = sig["entry"]
    if sig["type"] == "LONG":
        bar   = "📈🟢══════════════════🟢📈"
        title = f"🚀  EMA PULLBACK LONG — {coin}/USDT"
        tl    = "🐂 Xu hướng H1: TĂNG (EMA20 > EMA50)"
    else:
        bar   = "📉🔴══════════════════🔴📉"
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
        f"📊 RSI 15m        : {sig.get('rsi_val','—')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Điều kiện : {sig['score']}\n"
        f"{passed_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC C — Supertrend + Confirmation
# ════════════════════════════════════════════════════════════
def format_strategy_c(symbol: str, sig: dict) -> str:
    coin  = symbol.replace("USDT","")
    entry = sig["entry"]
    if sig["type"] == "LONG":
        bar   = "⚡🟢══════════════════🟢⚡"
        title = f"🚀  SUPERTREND LONG — {coin}/USDT"
        tl    = "🐂 Xu hướng: TĂNG  (Supertrend H1)"
    else:
        bar   = "⚡🔴══════════════════🔴⚡"
        title = f"💥  SUPERTREND SHORT — {coin}/USDT"
        tl    = "🐻 Xu hướng: GIẢM  (Supertrend H1)"
    confirms_str = (
        " · ".join(f"✅ {p}" for p in sig["passed"])
        if sig["passed"] else "⚡ Supertrend only"
    )
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ H1\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại   : {entry:,.4f} USDT\n"
        f"📍 Điểm vào       : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)   : {sig['sl']:,.4f}  (−{sig['sl_pct']}%)\n"
        f"🎯 Chốt lời (TP)  : {sig['tp']:,.4f}  (+{sig['tp_pct']}%)\n"
        f"⚖️ R:R             : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{tl}\n"
        f"📌 Supertrend     : {sig['st_val']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Confirmation   : {sig['score']}\n"
        f"{confirms_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Chiến lược C — Supertrend + Confirmation\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )


# ════════════════════════════════════════════════════════════
#  CHUNG — startup / status / heartbeat
# ════════════════════════════════════════════════════════════
def format_startup(symbols_a, symbols_b, symbols_c=None, symbols_d=None) -> str:
    ca = _fmt(symbols_a)
    cb = _fmt(symbols_b)
    cc = _fmt(symbols_c) if symbols_c is not None else "Trống"
    cd = _fmt(symbols_d) if symbols_d is not None else "Trống"
    return (
        f"✅  BOT CRYPTO ALERT BẬT\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A (Ichimoku)    : {ca}\n"
        f"📈 CL B (EMA+MACD)     : {cb}\n"
        f"⚡ CL C (Supertrend)   : {cc}\n"
        f"🌊 CL D (IchiStoch)    : {cd}\n"
        f"⚖️ R:R : 1:{RR_RATIO}  ·  SL {SL_PERCENT}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"/aa /ra — CL A  ·  /ab /rb — CL B\n"
        f"/ac /rc — CL C  ·  /ad /rd — CL D\n"
        f"/add /remove — cả 4\n"
        f"/strategy_a /strategy_b /strategy_c /strategy_d\n"
        f"/confirms /set_confirm /status"
    )


def format_status(symbols_a, symbols_b, strategies=None,
                  symbols_c=None, confirms_c=None, symbols_d=None) -> str:
    ca = _fmt_list(symbols_a)
    cb = _fmt_list(symbols_b)
    cc = _fmt_list(symbols_c) if symbols_c else "  (Trống)"
    cd = _fmt_list(symbols_d) if symbols_d else "  (Trống)"

    if strategies:
        sa = "✅ BẬT" if strategies.get("ichimoku")   else "❌ TẮT"
        sb = "✅ BẬT" if strategies.get("ema")         else "❌ TẮT"
        sc = "✅ BẬT" if strategies.get("supertrend")  else "❌ TẮT"
        sd = "✅ BẬT" if strategies.get("ichistoch")   else "❌ TẮT"
        strat = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️  Chiến lược:\n"
            f"  ☁️  A — Ichimoku    : {sa}\n"
            f"  📈 B — EMA+MACD    : {sb}\n"
            f"  ⚡ C — Supertrend  : {sc}\n"
            f"  🌊 D — IchiStoch   : {sd}\n"
        )
    else:
        strat = ""

    conf_line = ""
    if confirms_c is not None:
        active = ", ".join(confirms_c) if confirms_c else "Không có"
        conf_line = f"━━━━━━━━━━━━━━━━━━━━\n🔧 CL C confirmation: {active}\n"

    return (
        f"📋  TRẠNG THÁI BOT\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A (Ichimoku):\n{ca}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 CL B (EMA+MACD):\n{cb}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ CL C (Supertrend):\n{cc}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌊 CL D (IchiStoch):\n{cd}\n"
        f"{strat}"
        f"{conf_line}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ R:R = 1:{RR_RATIO}  ·  SL {SL_PERCENT}%"
    )


def format_heartbeat(symbols_a, symbols_b, strategies,
                     symbols_c=None, symbols_d=None) -> str:
    ca = _fmt(symbols_a)
    cb = _fmt(symbols_b)
    cc = _fmt(symbols_c) if symbols_c else "Trống"
    cd = _fmt(symbols_d) if symbols_d else "Trống"
    sa = "✅" if strategies.get("ichimoku")  else "❌"
    sb = "✅" if strategies.get("ema")        else "❌"
    sc = "✅" if strategies.get("supertrend") else "❌"
    sd = "✅" if strategies.get("ichistoch")  else "❌"
    return (
        f"💚  BOT ĐANG HOẠT ĐỘNG\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A {sa}: {ca}\n"
        f"📈 CL B {sb}: {cb}\n"
        f"⚡ CL C {sc}: {cc}\n"
        f"🌊 CL D {sd}: {cd}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Hoạt động bình thường"
    )




# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC D — Ichimoku + Stochastic
# ════════════════════════════════════════════════════════════
def format_strategy_d(symbol: str, sig: dict) -> str:
    coin  = symbol.replace("USDT", "")
    entry = sig["entry"]
    is_early   = sig["signal_type"] == "early"
    is_long    = sig["type"] == "LONG"

    if is_long:
        bar   = "🌊🟢══════════════════🟢🌊"
        title = f"{'⚡ CẢNH BÁO SỚM' if is_early else '🚀 VÀO LỆNH'} LONG — {coin}/USDT"
        trend = "🐂 Xu hướng H1: TĂNG (Giá > Kumo + Tenkan > Kijun)"
    else:
        bar   = "🌊🔴══════════════════🔴🌊"
        title = f"{'⚡ CẢNH BÁO SỚM' if is_early else '🚀 VÀO LỆNH'} SHORT — {coin}/USDT"
        trend = "🐻 Xu hướng H1: GIẢM (Giá < Kumo + Tenkan < Kijun)"

    note = "⚡ Chờ nến xác nhận đóng cửa trước khi vào!" if is_early else "✅ Nến đã xác nhận — có thể vào lệnh"

    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()} · ⏰ H1 + 15m\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá hiện tại  : {entry:,.4f} USDT\n"
        f"📍 Điểm vào      : {entry:,.4f}\n"
        f"🛡 Cắt lỗ (SL)  : {sig['sl']:,.4f}  (−{sig['sl_pct']}%)\n"
        f"🎯 Chốt lời (TP) : {sig['tp']:,.4f}  (+{sig['tp_pct']}%)\n"
        f"⚖️ R:R            : 1:{RR_RATIO}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{trend}\n"
        f"📊 Tenkan H1     : {sig['h1_tenkan']}\n"
        f"📊 Kijun H1      : {sig['h1_kijun']}\n"
        f"⚡ Stoch H1      : {sig['h1_k']}\n"
        f"⚡ Stoch 15m     : {sig['m15_k']}\n"
        f"📌 Lý do         : {sig['stoch_reason']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{note}\n"
        f"🌊 Chiến lược D — Ichimoku + Stochastic\n"
        f"⚠️ Không phải lời khuyên đầu tư!\n"
        f"{bar}"
    )



def format_sltp_result(symbol: str, result: dict) -> str:
    """Thông báo khi SL/TP/Timeout chạm."""
    coin      = symbol.replace("USDT","")
    rtype     = result["type"]
    direction = result["direction"]
    entry     = result["entry"]
    exit_p    = result["exit_price"]
    pnl       = result["pnl_pct"]

    if rtype == "TP":
        bar   = "🎯🟢══════════════════🟢🎯"
        title = f"✅ CHỐT LỜI — {coin}/USDT"
        icon  = "💰"
        pnl_str = f"+{pnl}%"
        note  = "Tìm lệnh mới sau cooldown 30 phút"
    elif rtype == "SL":
        bar   = "🛡🔴══════════════════🔴🛡"
        title = f"❌ CẮT LỖ — {coin}/USDT"
        icon  = "💸"
        pnl_str = f"{pnl}%"
        note  = "Tìm lệnh mới sau cooldown 30 phút"
    else:
        bar   = "⏰⬜══════════════════⬜⏰"
        title = f"⏰ TIMEOUT 8H — {coin}/USDT"
        icon  = "📊"
        pnl_str = f"{pnl:+.2f}%"
        note  = f"Đã giữ {result.get('hours',8)}h — reset tìm lệnh mới"

    dir_icon = "🟢 LONG" if direction == "LONG" else "🔴 SHORT"
    return (
        f"{bar}\n{title}\n"
        f"🕐 {_now()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Hướng lệnh   : {dir_icon}\n"
        f"📍 Giá vào      : {entry:,.4f}\n"
        f"{icon} Giá thoát    : {exit_p:,.4f}\n"
        f"📊 P&L          : {pnl_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"ℹ️ {note}\n"
        f"📈 Chiến lược B — EMA Pullback + MACD\n"
        f"{bar}"
    )

# Alias
format_entry = format_ichimoku_entry
format_setup = format_ichimoku_entry
