"""RSI mean-reversion strategy."""

import pandas as pd
from .base import BaseStrategy, Signal
from indicators.momentum import rsi


class RSIStrategy(BaseStrategy):
    """
    RSI Mean-Reversion strategy.

    Buy when RSI drops below oversold threshold.
    Sell when RSI rises above overbought threshold.
    """

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        super().__init__(f"RSI({period},{oversold},{overbought})")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["RSI"] = rsi(df["Close"], self.period)

        df["Signal"] = Signal.HOLD
        prev_rsi = df["RSI"].shift(1)

        # Buy when RSI crosses back above oversold from below
        buy_mask = (prev_rsi < self.oversold) & (df["RSI"] >= self.oversold)
        # Sell when RSI crosses back below overbought from above
        sell_mask = (prev_rsi > self.overbought) & (df["RSI"] <= self.overbought)

        df.loc[buy_mask, "Signal"] = Signal.BUY
        df.loc[sell_mask, "Signal"] = Signal.SELL

        return df
