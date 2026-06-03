import requests
import pandas as pd
import time
from ta.trend import EMAIndicator
from ta.momentum import StochRSIIndicator

# ================= CONFIG =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"

SYMBOLS = ["HYPEUSDT", "NEARUSDT"]
INTERVAL = "15m"
LIMIT = 200
CHECK_EVERY = 60

# ================= TELEGRAM =================
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ================= DATA =================
def get_data(symbol):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        # check API valid
        if not isinstance(data, list):
            return pd.DataFrame()

        df = pd.DataFrame(data).iloc[:, :6]
        df.columns = ["time", "open", "high", "low", "close", "volume"]

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        return df

    except Exception as e:
        print(f"get_data error {symbol}:", e)
        return pd.DataFrame()

# ================= INDICATORS =================
def add_indicators(df):
    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["ema100"] = EMAIndicator(df["close"], window=100).ema_indicator()

    stoch = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    df["stoch_k"] = stoch.stochrsi_k()
    df["stoch_d"] = stoch.stochrsi_d()

    return df

# ================= SIGNAL =================
            send_message(f"{symbol}\n" + "\n".join(signals))


# ================= MAIN LOOP =================
def run():
    send_message("🤖 Strategy Builder Bot Started")

    while True:
        for symbol in STRATEGY["symbols"]:
            try:
                print(f"Checking {symbol}...")

                df = get_data(symbol)

                if df.empty:
                    continue

                check_signal(symbol, df)

            except Exception as e:
                print(e)
                send_message(f"❌ Error {symbol}: {e}")

        time.sleep(STRATEGY["check_interval"])

# ================= START =================
if __name__ == "__main__":
    run()