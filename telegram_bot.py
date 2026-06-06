import requests
from config import TOKEN, CHAT_ID
from state import state
BASE = f"https://api.telegram.org/bot{TOKEN}"


def send(msg):
    requests.post(BASE + "/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })


def handle_command(text):

    # ================= STATUS =================
    if text == "/status":
        return (
            "🟢 BOT ĐANG CHẠY\n\n"
            f"🔄 Scan: {state['scan_count']}\n"
            f"🚨 Alerts: {state['alerts']}\n"
            f"☁️ Ichimoku: {state['ichimoku']}"
        )
    # ================= TOGGLE SCAN by TIME =================
    if text.startswith("/tf"):

        parts = text.split()

        if len(parts) != 2:
            return "Ví dụ:\n/tf M15\n/tf H1\n/tf H4\n/tf D1"

        tf = parts[1].lower()

        valid = ["m15", "h1", "h4", "d1"]

        if tf not in valid:
            return "Khung giờ không hợp lệ"

        state["active_timeframe"] = tf

        return f"⏰ Đã chuyển sang khung: {tf.upper()}"
    # ================= REPORT =================
    if text.startswith("/report"):

        parts = text.split()

        if len(parts) != 2:
            return "Ví dụ:\n/report BTC\n/report ETH\n/report SOL"

        return f"__REPORT__:{parts[1].upper()}"

    # ================= MENU =================
    if text == "/menu":
        return """📊 BẢNG ĐIỀU KHIỂN BOT

/settings
/status
/report BTC
/toggle_ichimoku
/toggle_alerts
"""

    # ================= TOGGLE ICHIMOKU =================
    if text == "/toggle_ichimoku":
        state["ichimoku"] = not state["ichimoku"]
        return f"☁️ Ichimoku = {state['ichimoku']}"

    # ================= TOGGLE ALERTS =================
    if text == "/toggle_alerts":
        state["alerts"] = not state["alerts"]
        return f"🚨 Alerts = {state['alerts']}"
    # ================= TOGGLE PAUSE vs RESUME =================
    if text == "/pause":
        state["alerts"] = False
        return "⛔ Đã tắt toàn bộ cảnh báo"

    if text == "/resume":
        state["alerts"] = True
        return "🟢 Đã bật lại cảnh báo"
    

    return "❓ Lệnh không hợp lệ"