import requests

url = "https://api.bytick.com/v5/market/tickers"

params = {
    "category": "linear",
    "symbol": "BTCUSDT"
}

try:
    res = requests.get(url, params=params, timeout=10)

    print("STATUS:", res.status_code)
    print("TEXT:")
    print(res.text)

except Exception as e:
    print("ERROR:", e)