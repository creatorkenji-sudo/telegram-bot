import time
import requests

from logger import log_info, log_error
from config import SYMBOLS, TIMEFRAMES, TOKEN
from data import get_klines
from strategy import analyze
from telegram_bot import send, handle_command
from state import state
from formatter import *

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
last_update = None
last_report = 0
last_heartbeat = 0


 # ================= GET UPDATE =================
def get_updates():
    global last_update

    url = f"{BASE_URL}/getUpdates"

    if last_update:
        url += f"?offset={last_update + 1}"

    res = requests.get(url).json()

    for msg in res["result"]:
        last_update = msg["update_id"]

        if "message" in msg:
            text = msg["message"]["text"]
            reply = handle_command(text)
            if reply.startswith("__REPORT__:"):
                coin = reply.split(":")[1]
                symbol = f"{coin}USDT"
                scan_single_coin(symbol)
            else:
                send(reply)
 # ================= SCAN SINGLE COIN =================
def scan_single_coin(symbol):

    msg = f"📊 PHÂN TÍCH {symbol}\n\n"

    for tf_name, tf in TIMEFRAMES.items():

        highs, lows, closes = get_klines(symbol, tf)

        result = analyze(
            symbol,
            tf,
            highs,
            lows,
            closes,
            state
        )

        msg += f"⏰ {tf_name}\n"
        msg += f"📊 StochRSI: {result['stoch']}\n"

        if "trend" in result:
            msg += f"📈 Trend: {result['trend']}\n"

        if result["signals"]:
            for s in result["signals"]:
                msg += f"{s}\n"

        msg += "\n"

    send(msg)
 # ================= SCAN MARKET =================
def scan_market():

    state["scan_count"] += 1

    log_info("Bắt đầu scan market")

    setup_found = False  # 👈 quan trọng: kiểm soát có signal hay không

    for symbol in SYMBOLS:

        for tf_name, tf in TIMEFRAMES.items():

            log_info(f"Đang quét {symbol} {tf_name}")

            highs, lows, closes = get_klines(symbol, tf)

            result = analyze(symbol, tf, highs, lows, closes, state)

            stoch = result["stoch"]

            # ================= KHÔNG CÒN REPORT RÁC =================
            # chỉ log nội bộ, không gửi Telegram
            log_info(f"{symbol} {tf_name} StochRSI={stoch}")

            # ================= CHỈ XỬ LÝ SIGNAL =================
            if not result["signals"]:
                continue

            for signal in result["signals"]:

                setup_found = True

                # ================= LONG =================
                if signal == "LONG_ENTRY":
                    send(
                        format_long_entry(symbol, tf_name, stoch)
                    )

                # ================= SHORT =================
                elif signal == "SHORT_ENTRY":
                    send(
                        format_short_entry(symbol, tf_name, stoch)
                    )

                # ================= REVERSAL =================
                elif signal == "BULLISH_REVERSAL":
                    send(
                        format_bullish_reversal(symbol, tf_name, stoch)
                    )

                elif signal == "BEARISH_REVERSAL":
                    send(
                        format_bearish_reversal(symbol, tf_name, stoch)
                    )

    # ================= CHỈ BÁO KHI CÓ SETUP =================
    if not setup_found:
        log_info("Không có setup nào")
 # ================= WHILE =================
while True:
    try:
        now = time.time()

        if now - last_heartbeat > state["heartbeat_interval"]:
         
            send(
                "💓 BOT VẪN ĐANG HOẠT ĐỘNG\n"
                f"🔄 Số lần quét: {state['scan_count']}\n"
                f"📊 Coins: {len(SYMBOLS)}"
                )
            last_heartbeat = now

         # ================= TELEGRAM COMMAND =================
        get_updates()

        # ================= MARKET SCAN =================
        if now - last_report > state["report_interval"]:
            scan_market()
            last_report = now

        # ================= CPU RELAX =================
        time.sleep(2)

    except Exception as e:
        log_error(str(e))
        time.sleep(5)