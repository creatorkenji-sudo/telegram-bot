# ============================================================
#  config.py — Toàn bộ cấu hình tại đây
# ============================================================

TOKEN   = "8965760476:AAGkOaVyGQ4IP-iBVKRqkGl76K-_fx5tS-g"
CHAT_ID = "7648621364"

# Danh sách coin mặc định khi khởi động (thêm/xóa qua Telegram)
DEFAULT_SYMBOLS = ["HYPEUSDT", "NEARUSDT"]

# Bybit
BASE_URL = "https://api.bybit.com"
LIMIT    = 200

# Khung giờ cố định
TIMEFRAMES = {
    "h4":   "240",   # xác định xu hướng lớn
    "h1":   "60",    # xác nhận trend
    "m15":  "15",    # tìm điểm vào lệnh
}

# Risk:Reward — SL = X%, TP = X% * RR_RATIO
SL_PERCENT = 2.0       # % cắt lỗ tính từ entry
RR_RATIO   = 3         # TP = SL * 3  →  R:R = 1:3

# Ngưỡng StochRSI
STOCH_OVERSOLD   = 20
STOCH_OVERBOUGHT = 80

# Vòng lặp
CHECK_INTERVAL = 60    # giây
