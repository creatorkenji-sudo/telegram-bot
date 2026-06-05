import requests
import json

url = "https://api.bybit.com/v5/market/tickers"

params = {
    "category": "linear",
    "symbol": "BTCUSDT"
}

try:
    res = requests.get(url, params=params, timeout=10)
    data = res.json()

    print("=== RESPONSE ===")
    print(json.dumps(data, indent=2))

    price = data["result"]["list"][0]["lastPrice"]
    print("\nBTC PRICE:", price)

except Exception as e:
    print("ERROR:", e)