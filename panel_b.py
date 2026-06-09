# ============================================================
#  panel_b.py — Bảng điều khiển Chiến lược B
#  Gọi bằng /panel_b trong Telegram
# ============================================================
from datetime import datetime, timezone, timedelta
from ema_strategy import FILTER_KEYS, FILTER_LABELS, FILTER_DESC
from config import SL_PERCENT, RR_RATIO

_TZ_VN = timezone(timedelta(hours=7))
def _now(): return datetime.now(_TZ_VN).strftime("%d/%m %H:%M") + " (UTC+7)"


def format_panel_b(strategies: dict, filters_b: dict, min_pass_b: int) -> str:
    """
    Hiện toàn bộ trạng thái CL B:
    - Đang BẬT/TẮT
    - Từng bộ lọc: BẬT/TẮT + tên lệnh
    - Ngưỡng min_pass
    - Cooldown, R:R, SL
    """
    is_on   = strategies.get("ema", True)
    cl_icon = "✅ BẬT" if is_on else "❌ TẮT"
    n_on    = sum(1 for k in FILTER_KEYS if filters_b.get(k, True))

    lines = [
        f"📈  BẢNG ĐIỀU KHIỂN — CHIẾN LƯỢC B",
        f"🕐 {_now()}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"Trạng thái    : {cl_icon}",
        f"Khung         : H1 + 15m",
        f"Cooldown      : 30 phút",
        f"R:R / SL      : 1:{RR_RATIO} · {SL_PERCENT}%",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"BỘ LỌC ({n_on}/{len(FILTER_KEYS)} đang bật · cần {min_pass_b})",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    for key in FILTER_KEYS:
        is_active = filters_b.get(key, True)
        icon      = "✅" if is_active else "⬜"
        label     = FILTER_LABELS[key]
        desc      = FILTER_DESC[key]
        lines.append(
            f"{icon} {label}\n"
            f"   {desc}\n"
            f"   Bật: /filter_b on {key}\n"
            f"   Tắt: /filter_b off {key}"
        )
        lines.append("─ ─ ─ ─ ─ ─ ─ ─ ─ ─")

    lines[-1] = "━━━━━━━━━━━━━━━━━━━━"   # thay dòng phân cách cuối
    lines += [
        f"Ngưỡng tối thiểu : {min_pass_b}/{n_on}",
        f"Đổi ngưỡng       : /minpass_b [số]",
        f"Bật/tắt CL B     : /strategy_b",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


def format_filter_update(key: str, is_on: bool,
                         filters_b: dict, min_pass_b: int) -> str:
    """Phản hồi sau khi bật/tắt 1 bộ lọc."""
    label  = FILTER_LABELS.get(key, key)
    icon   = "✅ BẬT" if is_on else "❌ TẮT"
    n_on   = sum(1 for k in FILTER_KEYS if filters_b.get(k, True))
    return (
        f"{'✅' if is_on else '⬜'}  Bộ lọc cập nhật\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Bộ lọc   : {label}\n"
        f"Trạng thái: {icon}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Đang bật  : {n_on}/{len(FILTER_KEYS)} bộ lọc\n"
        f"Cần pass  : {min_pass_b}/{n_on}\n"
        f"Xem đầy đủ: /panel_b"
    )


def format_minpass_update(min_pass_b: int, filters_b: dict) -> str:
    """Phản hồi sau khi đổi ngưỡng."""
    n_on = sum(1 for k in FILTER_KEYS if filters_b.get(k, True))
    return (
        f"⚙️  Ngưỡng cập nhật\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Cần pass tối thiểu : {min_pass_b}/{n_on}\n"
        f"Xem đầy đủ         : /panel_b"
    )
