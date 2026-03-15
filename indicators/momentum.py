"""Momentum-based technical indicators."""

import pandas as pd
import numpy as np


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (RSI).

    Values > 70 indicate overbought; < 30 indicate oversold.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator (%K, %D).

    Args:
        df: DataFrame with High, Low, Close columns
        k_period: Lookback period for %K
        d_period: Smoothing period for %D

    Returns:
        (%K, %D) series
    """
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()
    k = 100 * (df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(window=d_period).mean()
    return k, d


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common momentum indicators to a OHLCV DataFrame."""
    df = df.copy()
    df["RSI_14"] = rsi(df["Close"], 14)
    k, d = stochastic(df)
    df["Stoch_K"] = k
    df["Stoch_D"] = d
    return df
