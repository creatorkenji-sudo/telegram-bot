import requests
import pandas as pd
import time
from ta.trend import EMAIndicator
from ta.momentum import StochRSIIndicator

# ================= CONFIG =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "8965760476"

SYMBOLS = ["HYPEUSDT", "NEARUSDT"]
INTERVAL = "15m"
LIMIT = 200

CHECK_EVERY = 60  # giây

# ================= TELEGRAM =================
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= DATA =================
def get_data(symbol):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}
    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "c1","c2","c3","c4","c5","c6"
    ])

    df["close"] = df["close"].astype(float)
    return df

# ================= INDICATORS =================
def add_indicators(df):
    df["ema20"] = EMAIndicator(df["close"], 20).ema_indicator()
    df["ema100"] = EMAIndicator(df["close"], 100).ema_indicator()

    stoch = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    df["stoch_k"] = stoch.stochrsi_k()
    df["stoch_d"] = stoch.stochrsi_d()

    return df

# ================= SIGNAL CHECK =================
last_signal = {}

def check_signal(symbol, df):
    global last_signal

    df = add_indicators(df).dropna()

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signal = []

    # EMA cross
    if prev["ema20"] < prev["ema100"] and curr["ema20"] > curr["ema100"]:
        signal.append("📈 EMA20 cắt lên EMA100 (BULLISH)")
    elif prev["ema20"] > prev["ema100"] and curr["ema20"] < curr["ema100"]:
        signal.append("📉 EMA20 cắt xuống EMA100 (BEARISH)")

    # StochRSI
    if curr["stoch_k"] > 0.8:
        signal.append("⚠️ StochRSI QUÁ MUA")
    elif curr["stoch_k"] < 0.2:
        signal.append("⚠️ StochRSI QUÁ BÁN")

    # tránh spam
    if signal:
        key = symbol + str(signal)
        if last_signal.get(symbol) != key:
            last_signal[symbol] = key
            send_message(f"{symbol}\n" + "\n".join(signal))

# ================= MAIN LOOP =================
def run():
    send_message("🤖 Bot started")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_data(symbol)
                check_signal(symbol, df)

        except Exception as e:
            send_message(f"❌ Error: {str(e)}")

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    run()