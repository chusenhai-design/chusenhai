"""Base class for all trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    date: pd.Timestamp
    signal: Signal
    price: float
    reason: str = ""


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    Subclasses must implement `generate_signals()` which returns a
    DataFrame with a 'Signal' column containing Signal enum values.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from OHLCV data.

        Args:
            df: DataFrame with at least Open/High/Low/Close/Volume columns

        Returns:
            DataFrame with an added 'Signal' column (Signal enum values)
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
