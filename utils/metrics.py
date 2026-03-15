"""Standalone performance metric utilities."""

import pandas as pd
import numpy as np


def compute_metrics(equity_curve: pd.Series, risk_free_rate: float = 0.02) -> dict:
    """
    Compute comprehensive performance metrics from an equity curve.

    Args:
        equity_curve: Daily portfolio values indexed by date
        risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculation

    Returns:
        Dictionary of metric names to values
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return {}

    returns = equity_curve.pct_change().dropna()
    initial = equity_curve.iloc[0]
    final = equity_curve.iloc[-1]
    n_days = (equity_curve.index[-1] - equity_curve.index[0]).days or 1

    total_return = (final - initial) / initial
    annual_return = (1 + total_return) ** (365 / n_days) - 1

    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
    excess = returns - daily_rf
    sharpe = excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else 0.0

    downside = returns[returns < 0]
    sortino = (
        excess.mean() / downside.std() * np.sqrt(252)
        if len(downside) > 0 and downside.std() > 0
        else 0.0
    )

    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

    volatility = returns.std() * np.sqrt(252)

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown": max_drawdown,
        "n_days": n_days,
    }


def print_metrics(metrics: dict) -> None:
    labels = {
        "total_return": ("总收益率", "%"),
        "annual_return": ("年化收益率", "%"),
        "volatility": ("年化波动率", "%"),
        "sharpe_ratio": ("夏普比率", ""),
        "sortino_ratio": ("索提诺比率", ""),
        "calmar_ratio": ("卡玛比率", ""),
        "max_drawdown": ("最大回撤", "%"),
        "n_days": ("回测天数", "天"),
    }
    print(f"\n{'='*40}")
    print("  策略绩效指标")
    print(f"{'='*40}")
    for key, (label, unit) in labels.items():
        val = metrics.get(key, 0)
        if unit == "%":
            print(f"  {label:<12} {val*100:>10.2f}%")
        elif unit == "天":
            print(f"  {label:<12} {int(val):>10}天")
        else:
            print(f"  {label:<12} {val:>11.2f}")
    print(f"{'='*40}")
