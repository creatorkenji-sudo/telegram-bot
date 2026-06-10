# ============================================================
#  config.py — Toàn bộ cấu hình tại đây
# ============================================================
import os

# ── Telegram ─────────────────────────────────────────────────
TOKEN   = os.environ.get("TOKEN", "8965760476:AAHPcQYrJcse8Pk_8ynb7shJxTdmZVA-Qd8")
CHAT_ID = os.environ.get("CHAT_ID", "7648621364")

# ── Bybit ────────────────────────────────────────────────────
BASE_URL = "https://api.bybit.com"
LIMIT    = 200

# ── Coin mặc định khi khởi động ──────────────────────────────
DEFAULT_SYMBOLS = ["ETHUSDT","BTCUSDT","HYPEUSDT", "NEARUSDT", "BEATUSDT", "ASTERUSDT", "MAGMAUSDT", "EDGEUSDT", "ONDOUSDT", "AAVEUSDT", "RECALLUSDT", "VVVUSDT", "BSBUSDT", "CGPTUSDT", "LITUSDT", "WLDUSDT"]


# ── Khung thời gian ──────────────────────────────────────────
TIMEFRAMES = {
    "h4":  "240",
    "h1":  "60",
    "m15": "15",
}

# ── Risk / Reward ─────────────────────────────────────────────
SL_PERCENT = 2.0
RR_RATIO   = 3

# ── Stochastic ngưỡng ────────────────────────────────────────
STOCH_OVERSOLD   = 20
STOCH_OVERBOUGHT = 80

# ── Vòng lặp ─────────────────────────────────────────────────
CHECK_INTERVAL = 60   # giây
