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

CHECK_EVERY = 60  # giây

# ================= TELEGRAM =================
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= DATA =================
def get_data(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}

    try:
        data = requests.get(url, params=params, timeout=10).json()

        # ❌ API lỗi → không phải list
        if not isinstance(data, list):
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Binance format chuẩn: close = index 4
        df = df.iloc[:, :6]
        df.columns = ["time","open","high","low","close","volume"]

        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        return df

    except:
        return pd.DataFrame()

# ================= INDICATORS =================
def add_indicators(df):
    if df.empty or "close" not in df.columns:
    return
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

    if df.empty or len(df) < 120:
    return

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
                print(f"Checking {symbol}...")
                df = get_data(symbol)
                check_signal(symbol, df)

        except Exception as e:
            send_message(f"❌ Error: {str(e)}")

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    run()