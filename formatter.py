def format_long_entry(symbol, timeframe, stoch):
    return f"""
🟢══════════════════🟢

🪙 {symbol} | ⏰ {timeframe}

🚀 LONG ENTRY

📈 Xu hướng: TĂNG
📊 StochRSI: {stoch}

📋 Lý do:

✅ Giá nằm trên mây Ichimoku

✅ Xu hướng được xác nhận

✅ Pullback về vùng quá bán

🎯 Có thể theo dõi cơ hội LONG

🟢══════════════════🟢
"""
def format_short_entry(symbol, timeframe, stoch):
    return f"""
🔴══════════════════🔴

🪙 {symbol} | ⏰ {timeframe}

📉 SHORT ENTRY

📉 Xu hướng: GIẢM
📊 StochRSI: {stoch}

📋 Lý do:

✅ Giá nằm dưới mây Ichimoku

✅ Xu hướng được xác nhận

✅ Retest vùng quá mua

🎯 Có thể theo dõi cơ hội SHORT

🔴══════════════════🔴
"""
def format_bullish_reversal(symbol, timeframe, stoch):
    return f"""
⚠️══════════════════⚠️

🪙 {symbol} | ⏰ {timeframe}

🔄 CẢNH BÁO ĐẢO CHIỀU TĂNG

📊 StochRSI: {stoch}

📋 Dấu hiệu:

⚠️ Phân kỳ tăng

⚠️ Nhiều đáy gần nhau

⚠️ Lực bán suy yếu

📌 Chờ nến xác nhận

⚠️══════════════════⚠️
"""
def format_bearish_reversal(symbol, timeframe, stoch):
    return f"""
⚠️══════════════════⚠️

🪙 {symbol} | ⏰ {timeframe}

🔄 CẢNH BÁO ĐẢO CHIỀU GIẢM

📊 StochRSI: {stoch}

📋 Dấu hiệu:

⚠️ Phân kỳ giảm

⚠️ Nhiều đỉnh gần nhau

⚠️ Lực mua suy yếu

📌 Chờ nến xác nhận

⚠️══════════════════⚠️
"""