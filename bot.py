import requests
import pandas as pd
import time
import os

from ta.trend import EMAIndicator
from ta.momentum import StochRSIIndicator

# ================= CONFIG IMPORT =================
try:
    from config import STRATEGY
except:
    STRATEGY = {
        "ema_cross": True,
        "ema_fast": 20,
        "ema_slow": 50,
        "use_stochrsi": True,
        "stoch_overbought": 0.7,
        "stoch_oversold": 0.3,
        "symbols": ["HYPEUSDT", "NEARUSDT"],
        "check_interval": 60,
        "min_candles": 120
    }

# ================= ENV (Railway safe) =================
TOKEN = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"

# ================= STATE =================
last_signal = {}

# ================= TELEGRAM =================
def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Missing TOKEN or CHAT_ID")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ================= DATA =================
def get_data(symbol):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "15m", "limit": 200}

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if not isinstance(data, list):
            return pd.DataFrame()

        df = pd.DataFrame(data).iloc[:, :6]
        df.columns = ["time", "open", "high", "low", "close", "volume"]
        

        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        
        return df

    except Exception as e:
        print("get_data error:", e)
        return pd.DataFrame()

# ================= INDICATORS =================
def add_indicators(df):
    df["ema_fast"] = EMAIndicator(df["close"], STRATEGY["ema_fast"]).ema_indicator()
    df["ema_slow"] = EMAIndicator(df["close"], STRATEGY["ema_slow"]).ema_indicator()

    stoch = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    df["stoch_k"] = stoch.stochrsi_k()

    return df

# ================= STRATEGY ENGINE =================
def check_signal(symbol, df):
    global last_signal

    if df.empty or "close" not in df.columns:
        return

    df = add_indicators(df).dropna()

    if len(df) < STRATEGY["min_candles"]:
        return

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    signals = []

    # ===== EMA SIGNAL =====
    if STRATEGY["ema_cross"]:

        # EMA vừa cắt lên
        if prev["ema_fast"] < prev["ema_slow"] and curr["ema_fast"] > curr["ema_slow"]:
            signals.append("🚀 EMA CROSS UP")

        # EMA vừa cắt xuống
        elif prev["ema_fast"] > prev["ema_slow"] and curr["ema_fast"] < curr["ema_slow"]:
            signals.append("💥 EMA CROSS DOWN")

        # Xu hướng tăng + hồi
        elif curr["ema_fast"] > curr["ema_slow"] and curr["stoch_k"] < 0.3:
            signals.append("🟢 BULL TREND + STOCH OVERSOLD")

        # Xu hướng giảm + hồi
        elif curr["ema_fast"] < curr["ema_slow"] and curr["stoch_k"] > 0.7:
            signals.append("🔴 BEAR TREND + STOCH OVERBOUGHT")

    # ===== STOCH RSI =====
    if STRATEGY["use_stochrsi"]:

        # Thoát quá bán
        if (
            prev["stoch_k"] < STRATEGY["stoch_oversold"]
            and curr["stoch_k"] > STRATEGY["stoch_oversold"]
        ):
            signals.append("🟢 STOCH RSI EXIT OVERSOLD")

        # Thoát quá mua
        elif (
            prev["stoch_k"] > STRATEGY["stoch_overbought"]
            and curr["stoch_k"] < STRATEGY["stoch_overbought"]
        ):
            signals.append("🔴 STOCH RSI EXIT OVERBOUGHT")

    # ===== SEND =====
    if signals:

        key = symbol + str(signals)

        if last_signal.get(symbol) != key:

            last_signal[symbol] = key

            message = (
                f"📊 {symbol}\n\n"
                + "\n".join(signals)
                + f"\n\n💰 Price: {curr['close']}"
            )

            send_message(message)
# ================= MAIN LOOP =================
def run():
    send_message("🤖 Strategy Bot Started")
    send_message("🧪 Test Telegram OK")

    while True:
        for symbol in STRATEGY["symbols"]:
            try:
                print(f"Checking {symbol}...")

                df = get_data(symbol)

                if df.empty:
                    continue

                check_signal(symbol, df)

            except Exception as e:
                print(f"Error {symbol}:", e)
                send_message(f"❌ {symbol}: {e}")

        time.sleep(STRATEGY["check_interval"])

# ================= START =================
if __name__ == "__main__":
    run()