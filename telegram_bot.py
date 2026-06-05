# telegram_bot.py

import requests
from config import TOKEN, CHAT_ID
from state import state


BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def send(msg):
    requests.post(BASE_URL + "/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": msg
    })


def handle_command(text):

    if text == "/menu":
        return """📊 BOT MENU
/settings - config
/status - trạng thái
/toggle_ichimoku
/toggle_alerts
"""

    if text == "/status":
        return str(state)

    if text == "/toggle_ichimoku":
        state["ichimoku"] = not state["ichimoku"]
        return f"Ichimoku = {state['ichimoku']}"

    if text == "/toggle_alerts":
        state["alerts"] = not state["alerts"]
        return f"Alerts = {state['alerts']}"

    return "Unknown command"