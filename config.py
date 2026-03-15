"""Global configuration for the quant trading system."""

# Default backtesting settings
DEFAULT_INITIAL_CAPITAL = 100_000.0  # CNY
DEFAULT_COMMISSION = 0.0003          # 0.03% per trade
DEFAULT_SLIPPAGE = 0.001             # 0.1% slippage

# Risk management defaults
MAX_POSITION_SIZE = 0.2              # Max 20% of capital per position
MAX_DRAWDOWN_LIMIT = 0.15            # Stop trading if drawdown > 15%
DEFAULT_STOP_LOSS = 0.05             # 5% stop loss per position

# Data settings
DEFAULT_PERIOD = "2y"                # Default historical data period
DEFAULT_INTERVAL = "1d"             # Default data interval

# Logging
LOG_LEVEL = "INFO"
