import time

from state import state
from data import get_klines
from trend import multi_trend
from entry import check_entry
from telegram_bot import run_telegram, bot
from formatter import format_setup
from config import CHECK_INTERVAL


def loop():
    symbol = state["symbol"]

    # trend timeframe
    df_h1 = get_klines(symbol, "60")
    df_h4 = get_klines(symbol, "240")

    trend = multi_trend(df_h1, df_h4)

    # entry timeframe
    df_m15 = get_klines(symbol, "15")

    setup = check_entry(df_m15, trend)

    if setup:
        msg = format_setup(symbol, trend, "15m", setup)
        bot.send_message(chat_id=state["chat_id"], text=msg)


def main():
    run_telegram()

    while True:
        try:
            loop()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()