# data.py

import requests
import numpy as np
from config import LIMIT

BASE_URL = "https://api.binance.com/api/v3/klines"


def get_klines(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": LIMIT
    }

    data = requests.get(BASE_URL, params=params).json()

    highs = np.array([float(x[2]) for x in data])
    lows = np.array([float(x[3]) for x in data])
    closes = np.array([float(x[4]) for x in data])

    return highs, lows, closes