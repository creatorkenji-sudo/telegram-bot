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
    if text == "/status":
        return (
        "🟢 BOT ĐANG CHẠY\n\n"
        f"🔄 Scan: {state['scan_count']}\n"
        f"🚨 Alerts: {state['alerts']}\n"
        f"☁️ Ichimoku: {state['ichimoku']}"
    )
    
    if text.startswith("/report"):
        parts = text.split()

        if len(parts) != 2:
            return "Ví dụ:\n/report BTC\n/report ETH\n/report SOL"

        return f"__REPORT__:{parts[1].upper()}"
    
    if text == "/menu":
        return """📊 BẢNG ĐIỀU KHIỂN BOT
    
        /settings - cài đặt
        /status - trạng thái bot
        /toggle_ichimoku - bật/tắt Ichimoku
        /toggle_alerts - bật/tắt cảnh báo
        """

    if text == "/status":
        return "🟢 Bot đang hoạt động bình thường"

    if text == "/toggle_ichimoku":
        return "☁️ Đã chuyển trạng thái Ichimoku"

    if text == "/toggle_alerts":
        return "🚨 Đã bật/tắt cảnh báo"

    return "❓ Lệnh không hợp lệ"