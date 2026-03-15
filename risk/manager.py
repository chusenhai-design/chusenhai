"""Risk management – position sizing and drawdown controls."""

from __future__ import annotations

import pandas as pd
import numpy as np
from config import MAX_POSITION_SIZE, MAX_DRAWDOWN_LIMIT, DEFAULT_STOP_LOSS


class RiskManager:
    """
    Evaluates and enforces risk rules before each trade.

    Features:
    - Maximum position size as a fraction of portfolio
    - Maximum portfolio drawdown circuit-breaker
    - Per-position stop-loss
    - Volatility-adjusted position sizing (ATR-based)
    """

    def __init__(
        self,
        max_position_size: float = MAX_POSITION_SIZE,
        max_drawdown_limit: float = MAX_DRAWDOWN_LIMIT,
        stop_loss_pct: float = DEFAULT_STOP_LOSS,
    ):
        self.max_position_size = max_position_size
        self.max_drawdown_limit = max_drawdown_limit
        self.stop_loss_pct = stop_loss_pct
        self._peak_value: float = 0.0
        self._trading_halted: bool = False

    def update_peak(self, portfolio_value: float) -> None:
        """Call after each bar to track the high-water mark."""
        if portfolio_value > self._peak_value:
            self._peak_value = portfolio_value

    def current_drawdown(self, portfolio_value: float) -> float:
        """Return current drawdown as a negative fraction."""
        if self._peak_value <= 0:
            return 0.0
        return (portfolio_value - self._peak_value) / self._peak_value

    def check_drawdown_halt(self, portfolio_value: float) -> bool:
        """
        Returns True (and halts trading) if max drawdown exceeded.
        """
        dd = self.current_drawdown(portfolio_value)
        if dd <= -self.max_drawdown_limit:
            self._trading_halted = True
        return self._trading_halted

    def reset_halt(self) -> None:
        """Manually reset the trading halt."""
        self._trading_halted = False

    def position_size_shares(
        self,
        portfolio_value: float,
        price: float,
        atr: float | None = None,
        risk_per_trade: float = 0.01,
    ) -> float:
        """
        Calculate the number of shares to buy.

        If ATR is provided, uses volatility-adjusted sizing:
            shares = (portfolio * risk_per_trade) / atr

        Otherwise, uses fixed fraction:
            shares = (portfolio * max_position_size) / price
        """
        if self._trading_halted:
            return 0.0

        max_invest = portfolio_value * self.max_position_size

        if atr and atr > 0:
            risk_amount = portfolio_value * risk_per_trade
            shares = risk_amount / atr
            # Cap at max position size
            shares = min(shares, max_invest / price)
        else:
            shares = max_invest / price

        return max(0.0, shares)

    def stop_loss_price(self, entry_price: float) -> float:
        """Return the stop-loss price for a given entry."""
        return entry_price * (1 - self.stop_loss_pct)

    def is_stop_loss_triggered(self, entry_price: float, current_price: float) -> bool:
        """Check if current price has breached the stop-loss."""
        return current_price <= self.stop_loss_price(entry_price)

    def summary(self, portfolio_value: float) -> str:
        dd = self.current_drawdown(portfolio_value)
        lines = [
            f"\n{'='*45}",
            f"  风险管理状态",
            f"{'='*45}",
            f"  最大仓位比例:   {self.max_position_size*100:.1f}%",
            f"  最大回撤限制:   {self.max_drawdown_limit*100:.1f}%",
            f"  当前回撤:       {dd*100:.2f}%",
            f"  止损比例:       {self.stop_loss_pct*100:.1f}%",
            f"  交易暂停:       {'是' if self._trading_halted else '否'}",
            f"{'='*45}",
        ]
        return "\n".join(lines)
