"""Event-driven backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np

from strategies.base import BaseStrategy, Signal
from config import DEFAULT_INITIAL_CAPITAL, DEFAULT_COMMISSION, DEFAULT_SLIPPAGE


@dataclass
class Trade:
    date: pd.Timestamp
    action: str          # 'BUY' or 'SELL'
    price: float
    shares: float
    value: float
    commission: float
    pnl: float = 0.0     # Filled on closing trade


@dataclass
class BacktestResult:
    symbol: str
    strategy_name: str
    initial_capital: float
    final_capital: float
    trades: list[Trade]
    equity_curve: pd.Series    # Daily portfolio value
    metrics: dict = field(default_factory=dict)

    def summary(self) -> str:
        m = self.metrics
        lines = [
            f"\n{'='*55}",
            f"  回测结果: {self.strategy_name} | {self.symbol}",
            f"{'='*55}",
            f"  初始资金:     {self.initial_capital:>12,.2f}",
            f"  最终资金:     {self.final_capital:>12,.2f}",
            f"  总收益率:     {m.get('total_return', 0)*100:>11.2f}%",
            f"  年化收益率:   {m.get('annual_return', 0)*100:>11.2f}%",
            f"  夏普比率:     {m.get('sharpe_ratio', 0):>12.2f}",
            f"  最大回撤:     {m.get('max_drawdown', 0)*100:>11.2f}%",
            f"  胜率:         {m.get('win_rate', 0)*100:>11.2f}%",
            f"  总交易次数:   {m.get('total_trades', 0):>12}",
            f"  盈利次数:     {m.get('winning_trades', 0):>12}",
            f"  亏损次数:     {m.get('losing_trades', 0):>12}",
            f"  盈亏比:       {m.get('profit_factor', 0):>12.2f}",
            f"{'='*55}",
        ]
        return "\n".join(lines)


class BacktestEngine:
    """
    Simple position-based backtesting engine.

    Assumptions:
    - Single asset, long-only positions
    - Trades execute at next-day open price after signal
    - Commission applied on each trade
    - Slippage applied on entry/exit price
    """

    def __init__(
        self,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        commission: float = DEFAULT_COMMISSION,
        slippage: float = DEFAULT_SLIPPAGE,
        position_size: float = 1.0,  # fraction of capital per trade
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size  # 1.0 = all-in

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, symbol: str = "") -> BacktestResult:
        """
        Run backtest.

        Args:
            df: OHLCV DataFrame
            strategy: A BaseStrategy instance
            symbol: Ticker symbol for reporting

        Returns:
            BacktestResult with trades, equity curve, and metrics
        """
        signal_df = strategy.generate_signals(df)

        capital = self.initial_capital
        shares = 0.0
        entry_price = 0.0
        trades: list[Trade] = []
        equity_values: list[float] = []
        dates: list[pd.Timestamp] = []

        for i in range(1, len(signal_df)):
            today = signal_df.iloc[i]
            yesterday = signal_df.iloc[i - 1]
            date = signal_df.index[i]
            open_price = today["Open"]
            close_price = today["Close"]

            # Execute signal from previous bar at today's open
            sig = yesterday["Signal"]

            if sig == Signal.BUY and shares == 0:
                exec_price = open_price * (1 + self.slippage)
                invest = capital * self.position_size
                comm = invest * self.commission
                invest_net = invest - comm
                shares = invest_net / exec_price
                capital -= invest + comm
                entry_price = exec_price
                trades.append(Trade(
                    date=date,
                    action="BUY",
                    price=exec_price,
                    shares=shares,
                    value=invest,
                    commission=comm,
                ))

            elif sig == Signal.SELL and shares > 0:
                exec_price = open_price * (1 - self.slippage)
                proceeds = shares * exec_price
                comm = proceeds * self.commission
                net_proceeds = proceeds - comm
                pnl = net_proceeds - (shares * entry_price)
                capital += net_proceeds
                trades.append(Trade(
                    date=date,
                    action="SELL",
                    price=exec_price,
                    shares=shares,
                    value=proceeds,
                    commission=comm,
                    pnl=pnl,
                ))
                shares = 0.0
                entry_price = 0.0

            # Portfolio value = cash + market value of open position
            portfolio_value = capital + shares * close_price
            equity_values.append(portfolio_value)
            dates.append(date)

        # Close any open position at last price
        if shares > 0:
            last_price = signal_df.iloc[-1]["Close"] * (1 - self.slippage)
            proceeds = shares * last_price
            comm = proceeds * self.commission
            pnl = (proceeds - comm) - (shares * entry_price)
            capital += proceeds - comm
            trades.append(Trade(
                date=signal_df.index[-1],
                action="SELL",
                price=last_price,
                shares=shares,
                value=proceeds,
                commission=comm,
                pnl=pnl,
            ))

        final_capital = capital
        equity_curve = pd.Series(equity_values, index=dates, name="Portfolio")

        metrics = self._compute_metrics(equity_curve, trades, df)

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy.name,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
        )

    def _compute_metrics(
        self,
        equity: pd.Series,
        trades: list[Trade],
        price_df: pd.DataFrame,
    ) -> dict:
        if equity.empty or len(equity) < 2:
            return {}

        total_return = (equity.iloc[-1] - self.initial_capital) / self.initial_capital

        n_days = (equity.index[-1] - equity.index[0]).days
        annual_return = (1 + total_return) ** (365 / max(n_days, 1)) - 1

        daily_returns = equity.pct_change().dropna()
        sharpe = (
            daily_returns.mean() / daily_returns.std() * np.sqrt(252)
            if daily_returns.std() > 0
            else 0.0
        )

        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        sell_trades = [t for t in trades if t.action == "SELL"]
        total_trades = len(sell_trades)
        winning = [t for t in sell_trades if t.pnl > 0]
        losing = [t for t in sell_trades if t.pnl <= 0]
        win_rate = len(winning) / total_trades if total_trades > 0 else 0.0

        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "profit_factor": profit_factor,
        }
