# 股票量化交易系统

一个基于 Python 的股票量化交易框架，支持技术指标计算、策略回测、投资组合管理和风险控制。

## 功能特性

| 模块 | 功能 |
|------|------|
| **数据获取** | 通过 yfinance 获取全球股票历史/实时数据（A股、美股等） |
| **技术指标** | SMA/EMA、MACD、RSI、随机振荡器、布林带、ATR |
| **交易策略** | 双均线金叉死叉、RSI均值回归、MACD金叉策略 |
| **回测引擎** | 基于事件驱动，含手续费/滑点模拟，输出完整绩效报告 |
| **投资组合** | 多股票持仓追踪、盈亏计算、持仓汇总 |
| **风险管理** | 最大仓位控制、最大回撤熔断、止损管理、波动率仓位sizing |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 回测示例

```bash
# 美股 AAPL - 双均线策略（默认2年数据）
python main.py backtest AAPL --strategy ma_cross

# A股茅台 - RSI策略（3年数据）
python main.py backtest 600519.SS --strategy rsi --period 3y

# TSLA - MACD策略，显示所有交易记录
python main.py backtest TSLA --strategy macd --capital 200000 --trades

# 自定义均线参数，保存图表
python main.py backtest MSFT --strategy ma_cross --fast 5 --slow 20 --ma-type ema --save-chart equity.png

# 自定义RSI参数
python main.py backtest 000858.SZ --strategy rsi --rsi-period 21 --oversold 25 --overbought 75
```

### 投资组合

```bash
# 等权买入多只股票
python main.py portfolio AAPL MSFT GOOGL --capital 300000
```

### 股票信息

```bash
python main.py info AAPL
python main.py info 600519.SS
```

## 项目结构

```
.
├── main.py              # CLI 入口
├── config.py            # 全局配置参数
├── requirements.txt
├── data/
│   └── fetcher.py       # 数据获取（yfinance）
├── indicators/
│   ├── trend.py         # 趋势指标：SMA, EMA, MACD
│   ├── momentum.py      # 动量指标：RSI, Stochastic
│   └── volatility.py    # 波动指标：布林带, ATR
├── strategies/
│   ├── base.py          # 策略基类
│   ├── ma_cross.py      # 双均线策略
│   ├── rsi_strategy.py  # RSI策略
│   └── macd_strategy.py # MACD策略
├── backtest/
│   └── engine.py        # 回测引擎
├── portfolio/
│   └── manager.py       # 投资组合管理
├── risk/
│   └── manager.py       # 风险管理
└── utils/
    ├── metrics.py        # 绩效指标计算
    └── plot.py           # 图表可视化
```

## 策略说明

### 双均线策略 (`ma_cross`)
- **买入**: 快线上穿慢线（金叉）
- **卖出**: 快线下穿慢线（死叉）
- **参数**: `--fast`（快线周期）, `--slow`（慢线周期）, `--ma-type sma/ema`

### RSI均值回归策略 (`rsi`)
- **买入**: RSI从超卖区（< 30）反弹时
- **卖出**: RSI从超买区（> 70）回落时
- **参数**: `--rsi-period`, `--oversold`, `--overbought`

### MACD策略 (`macd`)
- **买入**: MACD柱状图由负转正
- **卖出**: MACD柱状图由正转负
- **参数**: `--fast`, `--slow`, `--signal-period`

## 绩效指标

回测输出以下指标：
- 总收益率 / 年化收益率
- 夏普比率 / 索提诺比率 / 卡玛比率
- 最大回撤
- 胜率 / 盈亏比
- 总交易次数

## 扩展自定义策略

继承 `BaseStrategy` 并实现 `generate_signals` 方法：

```python
from strategies.base import BaseStrategy, Signal
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MyStrategy")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Signal"] = Signal.HOLD
        # 在此添加买卖逻辑
        return df
```

## 注意事项

- **本软件仅用于学习研究，不构成投资建议**
- 回测结果不代表未来收益，历史表现不保证未来效果
- A股代码格式：上交所 `xxxxxx.SS`，深交所 `xxxxxx.SZ`
- 美股直接使用 ticker 代码（如 `AAPL`、`TSLA`）
