# main.py

import time
import requests

from config import TOKEN, SYMBOLS, TIMEFRAMES
from telegram_bot import send, handle_command
from strategy import analyze
from state import state


BASE_URL = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
last_update_id = None
last_report = 0


def check_telegram():
    global last_update_id

    url = BASE_URL
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    res = requests.get(url).json()

    for msg in res.get("result", []):

        last_update_id = msg["update_id"]

        if "message" in msg:
            text = msg["message"].get("text", "")
            reply = handle_command(text)
            send(reply)


def scan_market():
    report = "📊 MARKET REPORT\n\n"

    for symbol in SYMBOLS:
        for tf_name, tf in TIMEFRAMES.items():

            result = analyze(symbol, tf)

            report += (
                f"{symbol} | {tf_name}\n"
                f"Price: {result['price']}\n"
                f"Stoch: {result['stoch']}\n"
                f"Signal: {result['signal']}\n\n"
            )

    send(report)


while True:
    try:
        check_telegram()

        now = time.time()

        if now - last_report > state["report_interval"]:
            scan_market()
            last_report = now

        time.sleep(5)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)