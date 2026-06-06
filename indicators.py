# ============================================================
#  indicators.py — Ichimoku Cloud + StochRSI
# ============================================================
import pandas as pd
import numpy as np


def ichimoku(df: pd.DataFrame):
    high = df["high"]
    low  = df["low"]

    tenkan  = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    kijun   = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou  = df["close"].shift(-26)

    return tenkan, kijun, senkou_a, senkou_b, chikou


def stoch_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0).rolling(period).mean()
    loss     = (-delta.clip(upper=0)).rolling(period).mean()
    rs       = gain / loss.replace(0, np.nan)
    rsi      = 100 - (100 / (1 + rs))
    lo       = rsi.rolling(period).min()
    hi       = rsi.rolling(period).max()
    stoch    = (rsi - lo) / (hi - lo).replace(0, np.nan)
    return (stoch * 100).round(2)
