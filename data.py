import requests
import pandas as pd
from config import BASE_URL, LIMIT

def get_klines(symbol, interval):
    url = f"{BASE_URL}/v5/market/kline"

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": LIMIT
    }

    res = requests.get(url, params=params).json()
    data = res["result"]["list"]

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ])

    df = df.astype(float)
    return df[::-1]