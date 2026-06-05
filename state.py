# state.py

state = {
    "symbols": ["BTCUSDT"],

    "timeframes": {
        "M15": True,
        "H1": True,
        "H4": True,
        "D1": False
    },

    "stoch_overbought": 0.8,
    "stoch_oversold": 0.2,

    "ichimoku": True,
    "alerts": True,

    "report_interval": 3600,  # 1 giờ
    "mode": "swing"
}