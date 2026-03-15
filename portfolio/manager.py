"""Portfolio management – tracks holdings, cash, and P&L."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class Position:
    symbol: str
    shares: float
    avg_cost: float        # Average cost per share
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        return self.unrealized_pnl / self.cost_basis if self.cost_basis > 0 else 0.0


class Portfolio:
    """
    Tracks a multi-asset portfolio.

    Usage:
        p = Portfolio(initial_cash=100_000)
        p.buy("AAPL", shares=10, price=150.0, commission=1.5)
        p.update_prices({"AAPL": 160.0})
        print(p.summary())
    """

    def __init__(self, initial_cash: float = 100_000.0):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions: dict[str, Position] = {}
        self._trade_history: list[dict] = []

    def buy(
        self,
        symbol: str,
        shares: float,
        price: float,
        commission: float = 0.0,
        date: Optional[pd.Timestamp] = None,
    ) -> bool:
        """Buy shares. Returns False if insufficient cash."""
        total_cost = shares * price + commission
        if total_cost > self.cash:
            return False

        if symbol in self.positions:
            pos = self.positions[symbol]
            total_shares = pos.shares + shares
            pos.avg_cost = (pos.cost_basis + shares * price) / total_shares
            pos.shares = total_shares
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                avg_cost=price,
                current_price=price,
            )

        self.cash -= total_cost
        self._trade_history.append({
            "date": date or pd.Timestamp.now(),
            "action": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "commission": commission,
        })
        return True

    def sell(
        self,
        symbol: str,
        shares: float,
        price: float,
        commission: float = 0.0,
        date: Optional[pd.Timestamp] = None,
    ) -> bool:
        """Sell shares. Returns False if insufficient shares."""
        if symbol not in self.positions or self.positions[symbol].shares < shares:
            return False

        pos = self.positions[symbol]
        proceeds = shares * price - commission
        pnl = (price - pos.avg_cost) * shares - commission
        self.cash += proceeds
        pos.shares -= shares

        if pos.shares <= 1e-9:
            del self.positions[symbol]

        self._trade_history.append({
            "date": date or pd.Timestamp.now(),
            "action": "SELL",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "commission": commission,
            "pnl": pnl,
        })
        return True

    def update_prices(self, prices: dict[str, float]) -> None:
        """Update current market prices for all positions."""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price

    @property
    def total_market_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_value(self) -> float:
        return self.cash + self.total_market_value

    @property
    def total_return(self) -> float:
        return (self.total_value - self.initial_cash) / self.initial_cash

    @property
    def trade_history(self) -> pd.DataFrame:
        return pd.DataFrame(self._trade_history)

    def summary(self) -> str:
        lines = [
            f"\n{'='*55}",
            f"  投资组合概览",
            f"{'='*55}",
            f"  现金:         {self.cash:>12,.2f}",
            f"  持仓市值:     {self.total_market_value:>12,.2f}",
            f"  总资产:       {self.total_value:>12,.2f}",
            f"  总收益率:     {self.total_return*100:>11.2f}%",
            f"{'='*55}",
        ]
        if self.positions:
            lines.append(f"  {'股票':<10} {'股数':>8} {'均价':>10} {'现价':>10} {'盈亏%':>8}")
            lines.append(f"  {'-'*50}")
            for sym, pos in self.positions.items():
                lines.append(
                    f"  {sym:<10} {pos.shares:>8.1f} {pos.avg_cost:>10.2f}"
                    f" {pos.current_price:>10.2f} {pos.unrealized_pnl_pct*100:>7.2f}%"
                )
        lines.append(f"{'='*55}")
        return "\n".join(lines)
