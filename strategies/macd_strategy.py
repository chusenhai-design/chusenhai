"""MACD crossover strategy."""

import pandas as pd
from .base import BaseStrategy, Signal
from indicators.trend import macd


class MACDStrategy(BaseStrategy):
    """
    MACD Signal Line Crossover strategy.

    Buy when MACD line crosses above signal line.
    Sell when MACD line crosses below signal line.
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD({fast},{slow},{signal})")
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        macd_line, signal_line, histogram = macd(
            df["Close"], self.fast, self.slow, self.signal
        )
        df["MACD"] = macd_line
        df["MACD_Signal"] = signal_line
        df["MACD_Hist"] = histogram

        df["Signal"] = Signal.HOLD
        prev_hist = df["MACD_Hist"].shift(1)

        buy_mask = (prev_hist <= 0) & (df["MACD_Hist"] > 0)
        sell_mask = (prev_hist >= 0) & (df["MACD_Hist"] < 0)

        df.loc[buy_mask, "Signal"] = Signal.BUY
        df.loc[sell_mask, "Signal"] = Signal.SELL

        return df
