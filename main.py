#!/usr/bin/env python3
"""
股票量化交易系统 - 主入口
Stock Quantitative Trading System - CLI entry point
"""

import sys
import argparse

from data import DataFetcher
from backtest import BacktestEngine
from strategies import MACrossStrategy, RSIStrategy, MACDStrategy
from portfolio import Portfolio
from risk import RiskManager
from utils import plot_equity_curve, plot_signals


STRATEGIES = {
    "ma_cross": MACrossStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
}


def cmd_backtest(args):
    """Run a strategy backtest."""
    print(f"\n正在获取 {args.symbol} 的历史数据 ({args.period})...")
    fetcher = DataFetcher()
    df = fetcher.fetch(args.symbol, period=args.period, start=args.start, end=args.end)
    print(f"获取完成: {len(df)} 条记录  ({df.index[0].date()} ~ {df.index[-1].date()})")

    strategy_cls = STRATEGIES.get(args.strategy)
    if strategy_cls is None:
        print(f"未知策略 '{args.strategy}'。可用策略: {', '.join(STRATEGIES.keys())}")
        sys.exit(1)

    # Build strategy with optional param overrides
    kwargs = {}
    if args.strategy == "ma_cross":
        kwargs = {"fast_period": args.fast, "slow_period": args.slow, "ma_type": args.ma_type}
    elif args.strategy == "rsi":
        kwargs = {"period": args.rsi_period, "oversold": args.oversold, "overbought": args.overbought}
    elif args.strategy == "macd":
        kwargs = {"fast": args.fast, "slow": args.slow, "signal": args.signal_period}

    strategy = strategy_cls(**kwargs)
    print(f"策略: {strategy.name}")

    engine = BacktestEngine(
        initial_capital=args.capital,
        commission=args.commission,
        slippage=args.slippage,
    )
    result = engine.run(df, strategy, symbol=args.symbol)
    print(result.summary())

    if not args.no_plot:
        # Build buy-and-hold benchmark
        bah = (df["Close"] / df["Close"].iloc[0]) * args.capital
        signal_df = strategy.generate_signals(df)

        plot_equity_curve(
            result.equity_curve,
            title=f"{args.symbol} | {strategy.name}",
            benchmark=bah,
            save_path=args.save_chart,
        )
        if args.show_signals:
            plot_signals(df, signal_df, symbol=args.symbol, save_path=args.save_signals)

    if args.trades:
        print(f"\n  {'日期':<12} {'操作':<6} {'价格':>10} {'股数':>10} {'盈亏':>12}")
        print(f"  {'-'*55}")
        for t in result.trades:
            pnl_str = f"{t.pnl:>+12.2f}" if t.action == "SELL" else f"{'':>12}"
            print(f"  {str(t.date.date()):<12} {t.action:<6} {t.price:>10.2f}"
                  f" {t.shares:>10.1f}{pnl_str}")


def cmd_portfolio(args):
    """Show a simple portfolio demo."""
    p = Portfolio(initial_cash=args.capital)
    fetcher = DataFetcher()

    for sym in args.symbols:
        df = fetcher.fetch(sym, period="5d")
        price = df["Close"].iloc[-1]
        shares = (args.capital / len(args.symbols)) / price
        p.buy(sym, shares=shares, price=price)
        p.update_prices({sym: price})
        print(f"买入 {sym}: {shares:.2f}股 @ {price:.2f}")

    print(p.summary())


def cmd_info(args):
    """Show ticker info."""
    fetcher = DataFetcher()
    df = fetcher.fetch(args.symbol, period="5d")
    info = fetcher.get_info(args.symbol)
    print(f"\n  股票信息: {args.symbol}")
    print(f"  {'='*40}")
    for k, v in info.items():
        print(f"  {k:<15}: {v}")
    print(f"\n  最新价格: {df['Close'].iloc[-1]:.2f}")
    print(f"  数据日期: {df.index[-1].date()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quant",
        description="股票量化交易系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py backtest 600519 --strategy ma_cross          # 茅台 双均线
  python main.py backtest 600519 --strategy rsi --period 3y   # 茅台 RSI
  python main.py backtest 000858 --strategy macd --trades     # 五粮液 MACD
  python main.py portfolio 600519 000858 --capital 300000     # 投资组合
  python main.py info 600519                                   # 股票信息
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- backtest ---
    bt = sub.add_parser("backtest", help="运行策略回测")
    bt.add_argument("symbol", help="股票代码 (e.g. AAPL, 600519.SS)")
    bt.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="ma_cross",
                    help="交易策略 (default: ma_cross)")
    bt.add_argument("--period", default="2y", help="数据周期 (default: 2y)")
    bt.add_argument("--start", default=None, help="开始日期 YYYY-MM-DD")
    bt.add_argument("--end", default=None, help="结束日期 YYYY-MM-DD")
    bt.add_argument("--capital", type=float, default=100_000, help="初始资金 (default: 100000)")
    bt.add_argument("--commission", type=float, default=0.0003, help="佣金率 (default: 0.0003)")
    bt.add_argument("--slippage", type=float, default=0.001, help="滑点 (default: 0.001)")
    # MA Cross params
    bt.add_argument("--fast", type=int, default=10, help="快线周期 (MA/MACD, default: 10)")
    bt.add_argument("--slow", type=int, default=30, help="慢线周期 (MA/MACD, default: 30)")
    bt.add_argument("--ma-type", default="sma", choices=["sma", "ema"],
                    help="均线类型 (default: sma)")
    # RSI params
    bt.add_argument("--rsi-period", type=int, default=14, help="RSI周期 (default: 14)")
    bt.add_argument("--oversold", type=float, default=30.0, help="超卖阈值 (default: 30)")
    bt.add_argument("--overbought", type=float, default=70.0, help="超买阈值 (default: 70)")
    # MACD signal
    bt.add_argument("--signal-period", type=int, default=9, help="MACD信号线周期 (default: 9)")
    # Output options
    bt.add_argument("--no-plot", action="store_true", help="不显示图表")
    bt.add_argument("--show-signals", action="store_true", help="显示交易信号图")
    bt.add_argument("--save-chart", default=None, help="保存净值曲线图到文件")
    bt.add_argument("--save-signals", default=None, help="保存信号图到文件")
    bt.add_argument("--trades", action="store_true", help="打印所有交易记录")

    # --- portfolio ---
    pf = sub.add_parser("portfolio", help="查看投资组合")
    pf.add_argument("symbols", nargs="+", help="股票代码列表")
    pf.add_argument("--capital", type=float, default=100_000, help="初始资金")

    # --- info ---
    inf = sub.add_parser("info", help="查看股票基本信息")
    inf.add_argument("symbol", help="股票代码")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "portfolio":
        cmd_portfolio(args)
    elif args.command == "info":
        cmd_info(args)


if __name__ == "__main__":
    main()
