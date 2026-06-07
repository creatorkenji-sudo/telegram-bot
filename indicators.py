# ============================================================
#  indicators.py — Tất cả chỉ báo
# ============================================================
import pandas as pd
import numpy as np


# ── Ichimoku ─────────────────────────────────────────────────
def ichimoku(df: pd.DataFrame):
    hi, lo = df["high"], df["low"]
    tenkan   = (hi.rolling(9).max()  + lo.rolling(9).min())  / 2
    kijun    = (hi.rolling(26).max() + lo.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((hi.rolling(52).max() + lo.rolling(52).min()) / 2).shift(26)
    chikou   = df["close"].shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou


# ── StochRSI ─────────────────────────────────────────────────
def stoch_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0).rolling(period).mean()
    loss     = (-delta.clip(upper=0)).rolling(period).mean()
    rs       = gain / loss.replace(0, np.nan)
    rsi      = 100 - (100 / (1 + rs))
    lo       = rsi.rolling(period).min()
    hi       = rsi.rolling(period).max()
    return ((rsi - lo) / (hi - lo).replace(0, np.nan) * 100).round(2)


# ── EMA ──────────────────────────────────────────────────────
def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_emas(df: pd.DataFrame):
    """Trả về EMA20, EMA50, EMA100."""
    e20  = ema(df["close"], 20)
    e50  = ema(df["close"], 50)
    e100 = ema(df["close"], 100)
    return e20, e50, e100


# ── MACD ─────────────────────────────────────────────────────
def calc_macd(df: pd.DataFrame, fast=12, slow=26, signal=9):
    """
    Trả về:
      macd_line   = EMA_fast - EMA_slow
      signal_line = EMA(macd_line, signal)
      histogram   = macd_line - signal_line
    """
    macd_line   = ema(df["close"], fast) - ema(df["close"], slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram
