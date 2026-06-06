def format_setup(symbol, trend, tf, setup):
    direction = "🟢 LONG" if setup["type"] == "LONG" else "🔴 SHORT"

    msg = f"""
📊 {symbol}

🧭 Trend: {trend}

⚡ SETUP: {direction}

📍 Entry: {setup['entry']}
🛑 SL: {setup['sl']}
🎯 TP: {setup['tp']}

📌 RR: ~1:2

━━━━━━━━━━━━━━
✔ H1 + H4 confirm trend
✔ M15 entry signal
✔ Ichimoku breakout
✔ StochRSI confirmation
"""

    return msg