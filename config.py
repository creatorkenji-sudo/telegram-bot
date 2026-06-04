STRATEGY = {

    # ===== EXCHANGE =====
    "exchange": "bybit",

    # ===== SYMBOLS =====
    "symbols": ["WLDUSDT"],

    # ===== BOT =====
    "check_interval": 60,  # 5 phút

    # ===== EMA =====
    "ema_cross": False,
    "ema_fast": 20,
    "ema_slow": 50,

    # ===== STOCH RSI =====
    "use_stochrsi": False,
    "stoch_overbought": 0.7,
    "stoch_oversold": 0.3,

    # ===== FILTER =====
    "min_candles": 120,

    # ===== FUTURE FEATURES =====
    "use_rsi": False,
    "rsi_period": 14,

    "use_macd": False,

    "use_volume_filter": False,

    "use_tp_sl": False,
    "tp_percent": 5,
    "sl_percent": 2,

    "send_dashboard": False,
    "dashboard_interval": 3600
}