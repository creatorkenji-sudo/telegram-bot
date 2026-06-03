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
last_signal = {}

def check_signal(symbol, df):
    global last_signal

    if df.empty or "close" not in df.columns:
        return

    df = add_indicators(df).dropna()

    # MUST HAVE ENOUGH DATA
    if len(df) < 120:
        print(f"Not enough data for {symbol}")
        return

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signals = []

    # EMA CROSS
    if prev["ema20"] < prev["ema100"] and curr["ema20"] > curr["ema100"]:
        signals.append("📈 EMA20 cắt lên EMA100 (BULLISH)")
    elif prev["ema20"] > prev["ema100"] and curr["ema20"] < curr["ema100"]:
        signals.append("📉 EMA20 cắt xuống EMA100 (BEARISH)")

    # STOCH RSI
    if curr["stoch_k"] > 0.8:
        signals.append("⚠️ StochRSI QUÁ MUA")
    elif curr["stoch_k"] < 0.2:
        signals.append("⚠️ StochRSI QUÁ BÁN")

    # SEND SIGNAL (NO SPAM)
    if signals:
        key = symbol + str(signals)

        if last_signal.get(symbol) != key:
            last_signal[symbol] = key
            send_message(f"{symbol}\n" + "\n".join(signals))

# ================= MAIN LOOP =================
def run():
    send_message("🤖 Bot started")

    while True:
        for symbol in SYMBOLS:
            try:
                print(f"Checking {symbol}...")

                df = get_data(symbol)

                if df.empty:
                    continue

                check_signal(symbol, df)

            except Exception as e:
                print(f"Error {symbol}:", e)
                send_message(f"❌ {symbol}: {e}")

        time.sleep(CHECK_EVERY)

# ================= START =================
if __name__ == "__main__":
    run()