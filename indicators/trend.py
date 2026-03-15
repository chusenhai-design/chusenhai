"""Trend-following technical indicators."""

import pandas as pd
import numpy as np


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD indicator.

    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common trend indicators to a OHLCV DataFrame."""
    close = df["Close"]
    df = df.copy()
    df["SMA_5"] = sma(close, 5)
    df["SMA_10"] = sma(close, 10)
    df["SMA_20"] = sma(close, 20)
    df["SMA_60"] = sma(close, 60)
    df["EMA_12"] = ema(close, 12)
    df["EMA_26"] = ema(close, 26)
    macd_line, signal_line, histogram = macd(close)
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = histogram
    return df
