import time
import requests

from config import SYMBOLS, TIMEFRAMES
from data import get_klines
from strategy import analyze
from telegram_bot import send, handle_command
from state import state


BASE_URL = f"https://api.telegram.org/bot"
last_update = None
last_report = 0


def get_updates():
    global last_update

    url = f"{BASE_URL}{TOKEN}/getUpdates"

    if last_update:
        url += f"?offset={last_update + 1}"

    res = requests.get(url).json()

    for msg in res["result"]:
        last_update = msg["update_id"]

        if "message" in msg:
            text = msg["message"]["text"]
            reply = handle_command(text)
            send(reply)


def scan_market():
    msg = "📊 BÁO CÁO THỊ TRƯỜNG (ĐA KHUNG THỜI GIAN)\n\n"

    for symbol in SYMBOLS:
        for tf_name, tf in TIMEFRAMES.items():

            highs, lows, closes = get_klines(symbol, tf)

            result = analyze(symbol, tf, highs, lows, closes, state)

            msg += f"🪙 {symbol} | {tf_name}\n"
            msg += f"📊 StochRSI: {result['stoch']}\n"

            if result["signals"]:
                msg += "⚠️ " + " | ".join(result["signals"]) + "\n\n"
            else:
                msg += "Không có tín hiệu\n\n"

    send(msg)


while True:
    try:
        get_updates()

        now = time.time()

        if now - last_report > state["report_interval"]:
            scan_market()
            last_report = now

        time.sleep(5)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)