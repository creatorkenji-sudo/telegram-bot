import requests
import time

# ================= CONFIG =================
try:
    from config import STRATEGY
except:
    STRATEGY = {
        "exchange": "bybit",
        "symbols": ["WLDUSDT"],
        "check_interval": 300
    }

# ================= TELEGRAM =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=10
        )

        print("Telegram:", r.status_code)

    except Exception as e:
        print("Telegram error:", e)


# ================= GET PRICE =================
def get_price(symbol):

   try:

        url = "https://api.coingecko.com/api/v3/simple/price"

        params = {
            "ids": "worldcoin-wld",
            "vs_currencies": "usd"
        }

        r = requests.get(url, params=params, timeout=10)

        data = r.json()

        print(data)

        return {
            "price": float(data["worldcoin-wld"]["usd"])
        }

    except Exception as e:

        print("Price error:", e)

        return None
# ================= MAIN =================
def run():

    send_message("🤖 WLD Bybit Bot Started")

    while True:

        try:

            for symbol in STRATEGY["symbols"]:

                print(f"Checking {symbol}...")

                info = get_price()

                if not info:
                    continue

                msg = (
                    f"🪙 WLD (CoinGecko)\n\n"
                    f"💰 Giá hiện tại: ${info['price']:.4f}"
                )

                send_message(msg)

                print(msg)

        except Exception as e:

            print("Main error:", e)

            send_message(f"❌ Error: {e}")

        time.sleep(STRATEGY["check_interval"])


# ================= START =================
if __name__ == "__main__":
    run()