# ============================================================
#  data.py — Lấy nến từ Bybit V5
# ============================================================
import requests
import pandas as pd
from config import BASE_URL, LIMIT


def get_klines(symbol: str, interval: str) -> pd.DataFrame:
    url = f"{BASE_URL}/v5/market/kline"
    params = {
        "category": "linear",
        "symbol":   symbol,
        "interval": interval,
        "limit":    LIMIT,
    }
    res  = requests.get(url, params=params, timeout=10).json()
    data = res["result"]["list"]
    df   = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df = df.astype(float)
    return df[::-1].reset_index(drop=True)   # cũ → mới
