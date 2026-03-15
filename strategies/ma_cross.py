"""Moving Average Crossover strategy."""

import pandas as pd
from .base import BaseStrategy, Signal
from indicators.trend import sma, ema


class MACrossStrategy(BaseStrategy):
    """
    Dual Moving Average Crossover strategy.

    Buy when the fast MA crosses above the slow MA.
    Sell when the fast MA crosses below the slow MA.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 30,
        ma_type: str = "sma",
    ):
        name = f"MACross({ma_type.upper()},{fast_period},{slow_period})"
        super().__init__(name)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_func = ema if ma_type.lower() == "ema" else sma

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["MA_Fast"] = self.ma_func(df["Close"], self.fast_period)
        df["MA_Slow"] = self.ma_func(df["Close"], self.slow_period)

        df["Signal"] = Signal.HOLD
        prev_fast = df["MA_Fast"].shift(1)
        prev_slow = df["MA_Slow"].shift(1)

        # Golden cross: fast crosses above slow
        buy_mask = (prev_fast <= prev_slow) & (df["MA_Fast"] > df["MA_Slow"])
        # Death cross: fast crosses below slow
        sell_mask = (prev_fast >= prev_slow) & (df["MA_Fast"] < df["MA_Slow"])

        df.loc[buy_mask, "Signal"] = Signal.BUY
        df.loc[sell_mask, "Signal"] = Signal.SELL

        return df
