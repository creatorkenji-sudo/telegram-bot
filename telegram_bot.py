# ============================================================
#  telegram_bot.py — Commands Telegram (PTB 13.x)
# ============================================================
from telegram.ext import Updater, CommandHandler
from panel_b import format_panel_b, format_filter_update, format_minpass_update
from ema_strategy import FILTER_KEYS, FILTER_LABELS
from state import (
    state,
    add_symbol, remove_symbol,
    add_symbol_a, remove_symbol_a,
    add_symbol_b, remove_symbol_b,
    add_symbol_c, remove_symbol_c,
    add_symbol_d, remove_symbol_d,
    add_symbol_sr, remove_symbol_sr,
    toggle_strategy, strategy_status,
)
from config import TOKEN
from formatter import format_startup, format_status, format_menu


def _fmt_list(symbols: list) -> str:
    return ", ".join(s.replace("USDT","") for s in symbols) if symbols else "Trống"


# ── Lệnh chung ───────────────────────────────────────────────
def cmd_start(update, context):
    update.message.reply_text(format_startup(
        state["symbols_a"], state["symbols_b"], state["symbols_c"], state["symbols_d"]
    ))

def cmd_add(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /add BTCUSDT  (thêm vào cả 2 chiến lược)")
        return
    symbol = _clean(context.args[0])
    if add_symbol(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào cả 2 chiến lược\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong cả 2 rồi")

def cmd_remove(update, context):
    if not context.args:
        update.message.reply_text("❌ Dùng: /remove BTCUSDT  (xóa khỏi cả 2 chiến lược)")
        return
    symbol = _clean(context.args[0])
    if remove_symbol(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi cả 2 chiến lược\n"
            f"☁️  CL A: {_fmt_list(state['symbols_a'])}\n"
            f"📈 CL B: {_fmt_list(state['symbols_b'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong danh sách nào")

def cmd_list(update, context):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m %H:%M (UTC+7)")
    def fl(syms): return ", ".join(s.replace("USDT","") for s in syms) if syms else "Trống"
    msg  = f"📋 DANH SÁCH COIN
🕐 {now}
━━━━━━━━━━━━━━━━━━━━
"
    msg += f"☁️  CL A ({len(state['symbols_a'])}): {fl(state['symbols_a'])}
"
    msg += f"📈 CL B ({len(state['symbols_b'])}): {fl(state['symbols_b'])}
"
    msg += f"⚡ CL C ({len(state['symbols_c'])}): {fl(state['symbols_c'])}
"
    msg += f"🌊 CL D ({len(state['symbols_d'])}): {fl(state['symbols_d'])}
"
    msg += f"📊 CL SR ({len(state['symbols_sr'])}): {fl(state['symbols_sr'])}
"
    update.message.reply_text(msg)

def cmd_sr_set(update, context):
    """Chỉnh sửa 1 param: /sr_set [key] [value]"""
    if len(context.args) < 2:
        update.message.reply_text("❌ Dùng: /sr_set [param] [value]\nVí dụ: /sr_set swing_length 8")
        return
    key = context.args[0].lower()
    try:
        val = float(context.args[1])
    except ValueError:
        update.message.reply_text("❌ Giá trị phải là số")
        return

    valid_keys = ["swing_length","box_width","stoch_k","stoch_sm","stoch_d",
                  "stoch_ob","stoch_os","vol_ma","vol_mult","wait_bars","ma_len","cooldown_min"]
    int_keys   = ["swing_length","stoch_k","stoch_sm","stoch_d","stoch_ob",
                  "stoch_os","vol_ma","wait_bars","ma_len","cooldown_min"]

    if key not in valid_keys:
        update.message.reply_text(f"❌ Param không hợp lệ\nCác param: {', '.join(valid_keys)}")
        return

    if "sr_params" not in state:
        from strategy_sr import DEFAULT_PARAMS
        state["sr_params"] = DEFAULT_PARAMS.copy()

    state["sr_params"][key] = int(val) if key in int_keys else round(val, 2)
    update.message.reply_text(f"✅ Đã cập nhật: {key} = {state['sr_params'][key]}\n\nGõ /sr_params để xem tất cả")

def cmd_sr_reset(update, context):
    """Reset về params mặc định."""
    from strategy_sr import DEFAULT_PARAMS
    state["sr_params"] = DEFAULT_PARAMS.copy()
    update.message.reply_text("🔄 Đã reset CL SR về params mặc định\n\nGõ /sr_params để xem")



def cmd_menu(update, context):
    update.message.reply_text(format_menu())


def run_telegram():
    updater = Updater(TOKEN, use_context=True)
    updater.bot.delete_webhook(drop_pending_updates=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",      cmd_start))
    dp.add_handler(CommandHandler("add",        cmd_add))
    dp.add_handler(CommandHandler("remove",     cmd_remove))
    dp.add_handler(CommandHandler("list",       cmd_list))
    dp.add_handler(CommandHandler("status",     cmd_status))
    dp.add_handler(CommandHandler("aa",         cmd_aa))
    dp.add_handler(CommandHandler("ra",         cmd_ra))
    dp.add_handler(CommandHandler("ab",         cmd_ab))
    dp.add_handler(CommandHandler("rb",         cmd_rb))
    dp.add_handler(CommandHandler("strategy_a", cmd_strategy_a))
    dp.add_handler(CommandHandler("strategy_b", cmd_strategy_b))
    dp.add_handler(CommandHandler("strategies", cmd_strategies))

    updater.start_polling()
    print("✅ Telegram bot polling...")




def cmd_strategy_a(update, context):
    new = toggle_strategy("ichimoku")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(f"☁️ CL A — Ichimoku\nTrạng thái: {icon}")

def cmd_strategy_b(update, context):
    new = toggle_strategy("ema")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(f"📈 CL B — EMA+MACD\nTrạng thái: {icon}")

def cmd_strategies(update, context):
    s   = state["strategies"]
    sa  = "✅ BẬT" if s.get("ichimoku")  else "❌ TẮT"
    sb  = "✅ BẬT" if s.get("ema")        else "❌ TẮT"
    sc  = "✅ BẬT" if s.get("supertrend") else "❌ TẮT"
    sd  = "✅ BẬT" if s.get("ichistoch")  else "❌ TẮT"
    ssr = "✅ BẬT" if s.get("sr")         else "❌ TẮT"
    confirms = ", ".join(state.get("confirms_c", [])) or "Không có"
    msg = (
        f"⚙️ TRẠNG THÁI CHIẾN LƯỢC\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"☁️  CL A — Ichimoku    : {sa}\n"
        f"📈 CL B — EMA+MACD    : {sb}\n"
        f"⚡ CL C — Supertrend  : {sc}\n"
        f"  └ Confirmation: {confirms}\n"
        f"🌊 CL D — IchiStoch   : {sd}\n"
        f"📊 CL SR— H/T Kháng cự: {ssr}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Dùng /cl_a /cl_b /cl_c /cl_d /cl_sr để bật/tắt"
    )
    update.message.reply_text(msg)

# ════════════════════════════════════════════════════════════
#  CHIẾN LƯỢC C — Commands
# ════════════════════════════════════════════════════════════
from state import (
    add_symbol_c, remove_symbol_c,
    set_confirms_c, confirms_status,
)
from strategy_c import CONFIRMATION_MAP, CONFIRMATION_LABELS


def cmd_strategy_c(update, context):
    """Bật/tắt Chiến lược C."""
    new = toggle_strategy("supertrend")
    icon = "✅ BẬT" if new else "❌ TẮT"
    update.message.reply_text(
        f"⚡ Chiến lược C — Supertrend + Confirmation\n"
        f"Trạng thái mới: {icon}\n\n"
        f"{strategy_status()}"
    )


def cmd_ac(update, context):
    """Thêm coin vào CL C."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /ac BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if add_symbol_c(symbol):
        update.message.reply_text(
            f"✅ Đã thêm {symbol} vào CL C\n"
            f"⚡ CL C: {_fmt_list(state['symbols_c'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} đã có trong CL C rồi")


def cmd_rc(update, context):
    """Xóa coin khỏi CL C."""
    if not context.args:
        update.message.reply_text("❌ Dùng: /rc BTCUSDT")
        return
    symbol = _clean(context.args[0])
    if remove_symbol_c(symbol):
        update.message.reply_text(
            f"🗑 Đã xóa {symbol} khỏi CL C\n"
            f"⚡ CL C: {_fmt_list(state['symbols_c'])}"
        )
    else:
        update.message.reply_text(f"⚠️ {symbol} không có trong CL C")


def cmd_set_confirm(update, context):
    """
    /set_confirm qqe adx volume ssl ...
    Đặt lại danh sách confirmation cho CL C.
    """
    if not context.args:
        update.message.reply_text(
            f"❌ Dùng: /set_confirm qqe adx volume\n\n"
            f"Các confirmation có sẵn:\n"
            + "\n".join(f"  • {k} — {v}" for k, v in CONFIRMATION_LABELS.items())
        )
        return

    names = [a.lower() for a in context.args]
    valid, invalid = set_confirms_c(names)

    msg = ""
    if valid:
        msg += f"✅ Đã bật: {', '.join(valid)}\n"
    if invalid:
        msg += f"⚠️ Không tìm thấy: {', '.join(invalid)}\n"
    msg += f"\n{confirms_status()}"
    update.message.reply_text(msg)


def cmd_confirms(update, context):
    """Xem trạng thái confirmation CL C."""
    update.message.reply_text(confirms_status())


def cmd_add_confirm(update, context):
    """
    /add_confirm qqe  — thêm 1 confirmation vào CL C.
    """
    if not context.args:
        update.message.reply_text("❌ Dùng: /add_confirm qqe")
        return
    name = context.args[0].lower()
    if name not in CONFIRMATION_MAP:
        update.message.reply_text(
            f"⚠️ '{name}' không tồn tại.\n"
            f"Dùng: {', '.join(CONFIRMATION_MAP.keys())}"
        )
        return
    if name in state["confirms_c"]:
        update.message.reply_text(f"⚠️ '{name}' đã có rồi")
        return
    state["confirms_c"].append(name)
    update.message.reply_text(
        f"✅ Đã thêm: {CONFIRMATION_LABELS[name]}\n\n"
        f"{confirms_status()}"
    )


def cmd_remove_confirm(update, context):
    """
    /remove_confirm qqe — xóa 1 confirmation khỏi CL C.
    """
    if not context.args:
        update.message.reply_text("❌ Dùng: /remove_confirm qqe")
        return
    name = context.args[0].lower()
    if name not in state["confirms_c"]:
        update.message.reply_text(f"⚠️ '{name}' chưa được bật")
        return
    state["confirms_c"].remove(name)
    update.message.reply_text(
        f"🗑 Đã xóa: {CONFIRMATION_LABELS.get(name, name)}\n\n"
        f"{confirms_status()}"
    )


# ── Đăng ký handler mới vào run_telegram ────────────────────
_original_run = run_telegram


def cmd_panel_b(update, context):
    """Hiện bảng điều khiển CL B."""
    update.message.reply_text(
        format_panel_b(state["strategies"], state["filters_b"], state["min_pass_b"])
    )


def cmd_filter_b(update, context):
    """
    /filter_b on ema_h1
    /filter_b off macd
    """
    if len(context.args) < 2:
        update.message.reply_text(
            "❌ Dùng: /filter_b on ema_h1\n"
            "hoặc : /filter_b off macd\n\n"
            "Các bộ lọc: " + ", ".join(FILTER_KEYS)
        )
        return
    action = context.args[0].lower()
    key    = context.args[1].lower()
    if key not in FILTER_KEYS:
        update.message.reply_text(
            f"⚠️ Không tìm thấy bộ lọc '{key}'\n"
            f"Danh sách: {', '.join(FILTER_KEYS)}"
        )
        return
    if action not in ("on", "off"):
        update.message.reply_text("❌ Dùng: on hoặc off")
        return
    is_on = action == "on"
    state["filters_b"][key] = is_on
    # Đảm bảo min_pass không vượt số bộ lọc đang bật
    n_on = sum(1 for v in state["filters_b"].values() if v)
    if state["min_pass_b"] > n_on:
        state["min_pass_b"] = max(1, n_on)
    update.message.reply_text(
        format_filter_update(key, is_on, state["filters_b"], state["min_pass_b"])
    )


def cmd_minpass_b(update, context):
    """
    /minpass_b 4
    Đặt ngưỡng tối thiểu cần pass cho CL B.
    """
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text("❌ Dùng: /minpass_b 4")
        return
    val  = int(context.args[0])
    n_on = sum(1 for v in state["filters_b"].values() if v)
    if val < 1 or val > n_on:
        update.message.reply_text(
            f"⚠️ Ngưỡng phải từ 1 đến {n_on} (số bộ lọc đang bật)"
        )
        return
    state["min_pass_b"] = val
    update.message.reply_text(
        format_minpass_update(val, state["filters_b"])
    )


def _error_handler(update, context):
    """Bắt lỗi Conflict — log và tiếp tục, không crash."""
    from telegram.error import Conflict, NetworkError
    err = context.error
    if isinstance(err, Conflict):
        print(f"  ⚠️  Telegram Conflict — có instance khác đang chạy. Bỏ qua.")
    elif isinstance(err, NetworkError):
        print(f"  ⚠️  NetworkError: {err}. Sẽ thử lại...")
    else:
        print(f"  ❌ Telegram error: {err}")


def run_telegram():
    import time
    from telegram.error import Conflict

    # Xóa webhook + pending updates trước khi polling
    try:
        from telegram import Bot
        Bot(token=TOKEN).delete_webhook(drop_pending_updates=True)
        print("  🧹 Webhook đã xóa")
    except Exception as e:
        print(f"  ⚠️  Xóa webhook lỗi: {e}")

    # Đợi 3 giây để instance cũ có thời gian tắt hoàn toàn
    time.sleep(3)

    updater = Updater(TOKEN, use_context=True)
    dp      = updater.dispatcher

    # Đăng ký error handler — tránh crash khi có conflict
    dp.add_error_handler(_error_handler)

    dp.add_handler(CommandHandler("start",          cmd_start))
    dp.add_handler(CommandHandler("add",            cmd_add))
    dp.add_handler(CommandHandler("remove",         cmd_remove))
    dp.add_handler(CommandHandler("list",           cmd_list))
    dp.add_handler(CommandHandler("status",         cmd_status))
    dp.add_handler(CommandHandler("aa",             cmd_aa))
    dp.add_handler(CommandHandler("ra",             cmd_ra))
    dp.add_handler(CommandHandler("ab",             cmd_ab))
    dp.add_handler(CommandHandler("rb",             cmd_rb))
    dp.add_handler(CommandHandler("ac",             cmd_ac))
    dp.add_handler(CommandHandler("rc",             cmd_rc))
    dp.add_handler(CommandHandler("strategy_a",     cmd_strategy_a))
    dp.add_handler(CommandHandler("cl_a",      cmd_strategy_a))
    dp.add_handler(CommandHandler("strategy_b",     cmd_strategy_b))
    dp.add_handler(CommandHandler("cl_b",      cmd_strategy_b))
    dp.add_handler(CommandHandler("strategy_c",     cmd_strategy_c))
    dp.add_handler(CommandHandler("cl_c",      cmd_strategy_c))
    dp.add_handler(CommandHandler("strategies",     cmd_strategies))
    dp.add_handler(CommandHandler("set_confirm",    cmd_set_confirm))
    dp.add_handler(CommandHandler("add_confirm",    cmd_add_confirm))
    dp.add_handler(CommandHandler("remove_confirm", cmd_remove_confirm))
    dp.add_handler(CommandHandler("confirms",       cmd_confirms))
    dp.add_handler(CommandHandler("panel_b",        cmd_panel_b))
    dp.add_handler(CommandHandler("filter_b",       cmd_filter_b))
    dp.add_handler(CommandHandler("minpass_b",      cmd_minpass_b))
    dp.add_handler(CommandHandler("reset_b",         cmd_reset_b))
    dp.add_handler(CommandHandler("stats",           cmd_stats))
    dp.add_handler(CommandHandler("reset_tracker",   cmd_reset_tracker))
    dp.add_handler(CommandHandler("strategy_d",     cmd_strategy_d))
    dp.add_handler(CommandHandler("cl_d",      cmd_strategy_d))
    dp.add_handler(CommandHandler("strategy_sr",    cmd_strategy_sr))
    dp.add_handler(CommandHandler("asr",            cmd_asr))
    dp.add_handler(CommandHandler("rsr",            cmd_rsr))
    dp.add_handler(CommandHandler("sr_params",      cmd_sr_params))
    dp.add_handler(CommandHandler("sr_set",         cmd_sr_set))
    dp.add_handler(CommandHandler("sr_reset",       cmd_sr_reset))
    dp.add_handler(CommandHandler("menu",            cmd_menu))
    dp.add_handler(CommandHandler("ad",             cmd_ad))
    dp.add_handler(CommandHandler("rd",             cmd_rd))

    # start_polling với allowed_updates để giảm load
    updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message"],
    )
    print("✅ Telegram bot polling...")