"""Visualization utilities for backtest results."""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from strategies.base import Signal


def plot_equity_curve(
    equity_curve: pd.Series,
    title: str = "净值曲线",
    benchmark: pd.Series | None = None,
    save_path: str | None = None,
) -> None:
    """Plot portfolio equity curve, optionally vs a benchmark."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle(title, fontsize=14, fontweight="bold")

    ax1 = axes[0]
    normalized = equity_curve / equity_curve.iloc[0]
    ax1.plot(equity_curve.index, normalized, label="策略", color="steelblue", linewidth=1.5)

    if benchmark is not None:
        norm_bench = benchmark / benchmark.iloc[0]
        ax1.plot(benchmark.index, norm_bench, label="基准(买入持有)", color="gray",
                 linewidth=1.2, linestyle="--", alpha=0.8)

    ax1.set_ylabel("归一化净值")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    # Drawdown subplot
    ax2 = axes[1]
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    ax2.fill_between(drawdown.index, drawdown, 0, color="crimson", alpha=0.4)
    ax2.plot(drawdown.index, drawdown, color="crimson", linewidth=0.8)
    ax2.set_ylabel("回撤 (%)")
    ax2.set_xlabel("日期")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"图表已保存至: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_signals(
    df: pd.DataFrame,
    signal_df: pd.DataFrame,
    symbol: str = "",
    save_path: str | None = None,
) -> None:
    """Plot price chart with buy/sell markers."""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_title(f"{symbol} 交易信号", fontsize=13, fontweight="bold")
    ax.plot(df.index, df["Close"], color="steelblue", linewidth=1.2, label="收盘价")

    buys = signal_df[signal_df["Signal"] == Signal.BUY]
    sells = signal_df[signal_df["Signal"] == Signal.SELL]

    ax.scatter(buys.index, df.loc[buys.index, "Close"],
               marker="^", color="green", s=80, zorder=5, label="买入")
    ax.scatter(sells.index, df.loc[sells.index, "Close"],
               marker="v", color="red", s=80, zorder=5, label="卖出")

    ax.set_ylabel("价格")
    ax.set_xlabel("日期")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"图表已保存至: {save_path}")
    else:
        plt.show()
    plt.close(fig)
