from indicators import ichimoku

def get_trend(df):
    tenkan, kijun, sa, sb = ichimoku(df)

    price = df["close"].iloc[-1]

    cloud_top = max(sa.iloc[-1], sb.iloc[-1])
    cloud_bottom = min(sa.iloc[-1], sb.iloc[-1])

    if price > cloud_top:
        return "UP"
    elif price < cloud_bottom:
        return "DOWN"
    else:
        return "SIDE"


def multi_trend(df_h1, df_h4):
    t1 = get_trend(df_h1)
    t2 = get_trend(df_h4)

    if t1 == "UP" and t2 == "UP":
        return "UPTREND"
    if t1 == "DOWN" and t2 == "DOWN":
        return "DOWNTREND"

    return "NO_TREND"