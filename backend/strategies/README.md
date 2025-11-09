# Trading Strategies Module

Complete framework for implementing and backtesting trading strategies.

## Overview

The strategies module provides:
- **Base Classes**: Abstract framework for creating custom strategies
- **Portfolio Management**: Position tracking, P&L calculation, performance metrics
- **Pre-built Strategies**: Ready-to-use trading strategies
- **Backtesting Engine**: Test strategies on historical data

## Quick Start

```python
from data import HistoricalDataFetcher
from strategies import SMACrossover
from backtesting import BacktestEngine
from datetime import datetime, timedelta

# 1. Fetch historical data
fetcher = HistoricalDataFetcher()
data = fetcher.fetch('AAPL', '1d',
                     start=datetime.now() - timedelta(days=730),
                     end=datetime.now())

# 2. Create strategy
strategy = SMACrossover(fast_period=20, slow_period=50)

# 3. Run backtest
engine = BacktestEngine(strategy, initial_cash=100000, commission=0.001)
results = engine.run(data, symbol='AAPL')

# 4. Review results
print(f"Total Return: {results['performance']['total_return']:.2f}%")
print(f"Sharpe Ratio: {results['performance']['sharpe_ratio']:.2f}")
print(f"Win Rate: {results['trading']['win_rate']:.2f}%")
```

## Architecture

### Base Classes

#### Strategy (Abstract)
All strategies must inherit from `Strategy` and implement:
- `generate_signal(data: pd.DataFrame) -> Signal`: Generate trading decision
- `get_name() -> str`: Return strategy name

Optional hooks:
- `on_position_opened(position: Position)`: Called when position opens
- `on_position_closed(position: Position, exit_price, exit_time)`: Called when position closes

#### Signal
Represents a trading decision:
```python
signal = Signal(
    type=SignalType.BUY,        # BUY, SELL, HOLD, CLOSE_LONG, CLOSE_SHORT
    timestamp=datetime.now(),
    price=100.0,
    confidence=0.8,             # 0.0 to 1.0
    size=0.5,                   # Fraction of portfolio (0.0 to 1.0)
    metadata={'reason': 'golden_cross'}
)
```

#### Position
Represents an open position:
```python
position = Position(
    symbol='AAPL',
    side='long',               # 'long' or 'short'
    entry_price=100.0,
    entry_time=datetime.now(),
    size=100,                  # Number of shares
    current_price=105.0,
    stop_loss=95.0,
    take_profit=110.0
)

# Properties
pnl = position.unrealized_pnl       # P&L in dollars
pnl_pct = position.unrealized_pnl_pct  # P&L as percentage
```

#### Portfolio
Manages cash, positions, and trades:
```python
portfolio = Portfolio(initial_cash=100000, commission=0.001)

# Open position
pos = portfolio.open_position('AAPL', 'long', price=100,
                              timestamp=now, size_pct=0.5)

# Update prices
portfolio.update_prices({'AAPL': 105.0})

# Close position
trade = portfolio.close_position('AAPL', price=105, timestamp=now)

# Performance metrics
summary = portfolio.get_summary()
# Returns: equity, total_return, win_rate, profit_factor, etc.
```

## Pre-built Strategies

### 1. SMA Crossover
Classic trend-following using two moving averages.

**Signals:**
- BUY: Fast SMA crosses above slow SMA (golden cross)
- SELL: Fast SMA crosses below slow SMA (death cross)

**Parameters:**
```python
strategy = SMACrossover(
    fast_period=20,    # Fast SMA period
    slow_period=50     # Slow SMA period
)
```

**Best For:** Trending markets, medium-term trades

### 2. RSI Mean Reversion
Counter-trend strategy using RSI oscillator.

**Signals:**
- BUY: RSI crosses below oversold threshold (expecting bounce)
- SELL: RSI crosses above overbought threshold (expecting pullback)
- EXIT: RSI returns to neutral zone (50)

**Parameters:**
```python
strategy = RSIMeanReversion(
    rsi_period=14,      # RSI calculation period
    oversold=30,        # Oversold threshold (0-100)
    overbought=70,      # Overbought threshold (0-100)
    neutral_exit=True   # Exit when RSI returns to 50
)
```

**Best For:** Range-bound markets, short-term trades

### 3. Multi-Indicator
Combines trend, momentum, and volatility indicators.

**Analysis:**
- **Trend**: MACD histogram, SMA(50)
- **Momentum**: RSI(14)
- **Volatility**: Bollinger Bands

**Scoring System (0-100):**
- Trend: 40 points (MACD bullish + price above SMA)
- Momentum: 30 points (RSI neutral zone)
- Volatility: 30 points (Bollinger Band position)

**Signals:**
- BUY: Score >= 70 OR all bullish signals present
- SELL: MACD bearish AND price below SMA
- EXIT: Opposite trend signals OR BB extremes hit

**Parameters:**
```python
strategy = MultiIndicator(
    sma_period=50,     # SMA period for trend
    rsi_period=14,     # RSI period for momentum
    bb_period=20,      # Bollinger Bands period
    bb_std=2.0         # BB standard deviation multiplier
)
```

**Best For:** All market conditions, balanced approach

## Creating Custom Strategies

### Simple Example

```python
from strategies import Strategy, Signal, SignalType
from analysis.indicators import RSI

class MyRSIStrategy(Strategy):
    def __init__(self, rsi_period=14, threshold=30):
        super().__init__(rsi_period=rsi_period, threshold=threshold)
        self.rsi_period = rsi_period
        self.threshold = threshold

    def generate_signal(self, data):
        close = data['close']

        # Calculate RSI
        rsi = RSI.calculate(close, self.rsi_period)
        current_rsi = rsi.iloc[-1]

        # Generate signal
        if current_rsi < self.threshold:
            return Signal(
                type=SignalType.BUY,
                timestamp=data.index[-1],
                price=close.iloc[-1],
                confidence=1.0 - (current_rsi / self.threshold)
            )
        else:
            return Signal(
                type=SignalType.HOLD,
                timestamp=data.index[-1],
                price=close.iloc[-1]
            )

    def get_name(self):
        return f"MyRSI_{self.rsi_period}_{self.threshold}"
```

### Advanced Example with Pattern Recognition

```python
from strategies import Strategy, Signal, SignalType
from analysis.indicators import MACD
from analysis.patterns import TrianglePatterns

class PatternMACDStrategy(Strategy):
    def generate_signal(self, data):
        close = data['close']

        # Calculate MACD
        macd = MACD.calculate(close)
        macd_bullish = macd['histogram'].iloc[-1] > 0

        # Detect patterns
        patterns = TrianglePatterns.scan_all(
            data['high'], data['low'], data['close']
        )

        # Look for bullish patterns
        bullish_pattern = any(
            p['type'].startswith('bullish') for p in patterns
        )

        # Combined signal
        if macd_bullish and bullish_pattern:
            return Signal(
                type=SignalType.BUY,
                timestamp=data.index[-1],
                price=close.iloc[-1],
                confidence=0.9,
                metadata={
                    'macd_hist': macd['histogram'].iloc[-1],
                    'patterns': [p['pattern'] for p in patterns]
                }
            )

        return Signal(type=SignalType.HOLD, ...)

    def get_name(self):
        return "PatternMACD"
```

## Backtesting

### Basic Backtest

```python
from backtesting import BacktestEngine

engine = BacktestEngine(
    strategy=strategy,
    initial_cash=100000,
    commission=0.001,      # 0.1% commission
    stop_loss_pct=0.05,    # 5% stop loss
    take_profit_pct=0.10   # 10% take profit
)

results = engine.run(data, symbol='AAPL', warmup_period=100)
```

### Results Structure

```python
results = {
    'strategy': 'SMA_Crossover_20_50',
    'symbol': 'AAPL',
    'start_date': datetime(...),
    'end_date': datetime(...),

    'performance': {
        'initial_cash': 100000,
        'final_equity': 115000,
        'total_return': 15.0,      # %
        'total_pnl': 15000,         # $
        'sharpe_ratio': 1.5,
        'max_drawdown': -12.5       # %
    },

    'trading': {
        'total_trades': 10,
        'winning_trades': 6,
        'losing_trades': 4,
        'win_rate': 60.0,           # %
        'profit_factor': 2.5,
        'avg_win': 3000,            # $
        'avg_loss': -1200           # $
    },

    'equity_curve': DataFrame,      # Timestamp, equity, cash
    'trades': [Trade, ...],         # List of all trades
    'signals': [Signal, ...]        # List of all signals
}
```

### Strategy Comparison

```python
strategies = [
    SMACrossover(20, 50),
    RSIMeanReversion(14, 30, 70),
    MultiIndicator()
]

for strategy in strategies:
    engine = BacktestEngine(strategy, initial_cash=100000)
    results = engine.run(data, symbol='AAPL')

    print(f"{strategy.get_name()}: {results['performance']['total_return']:.2f}%")
```

## Performance Metrics

### Sharpe Ratio
Risk-adjusted return (annualized):
- < 1.0: Poor
- 1.0 - 2.0: Good
- > 2.0: Excellent

### Max Drawdown
Maximum peak-to-trough decline:
- Lower is better
- Indicates worst-case scenario

### Profit Factor
Gross profit / gross loss:
- < 1.0: Losing strategy
- 1.0 - 2.0: Decent
- > 2.0: Strong

### Win Rate
Percentage of winning trades:
- Should be balanced with avg win/loss ratio
- 60%+ is generally good

## Testing

```bash
# Unit tests (strategies, portfolio, signals)
python tests/unit/strategies/test_strategies.py

# E2E backtesting tests
python tests/e2e/test_backtest.py
```

## File Structure

```
backend/strategies/
├── __init__.py              # Main exports
├── base.py                  # Abstract Strategy, Signal, Position
├── portfolio.py             # Portfolio management
├── sma_crossover.py         # SMA crossover strategy
├── rsi_mean_reversion.py    # RSI mean reversion strategy
├── multi_indicator.py       # Multi-indicator strategy
└── README.md                # This file

backend/backtesting/
├── __init__.py              # Main exports
└── engine.py                # Backtesting engine
```

## Next Steps

1. **Add More Strategies**: Implement additional strategies (MACD, Stochastic, etc.)
2. **Optimize Parameters**: Use grid search to find optimal parameters
3. **Walk-Forward Testing**: Test on rolling time windows
4. **Live Trading**: Connect to Alpaca API for paper/live trading
5. **Risk Management**: Add portfolio-level risk controls
6. **Machine Learning**: Integrate ML-based strategies

## Notes

- All strategies are **long-only** by default (shorts are supported but not recommended for beginners)
- Commission and slippage are configurable
- Stop loss and take profit are optional
- Backtests are **event-driven** (bar-by-bar simulation)
- No look-ahead bias (strategies only see historical data)
