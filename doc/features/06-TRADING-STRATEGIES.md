# Trading Strategies

Pluggable trading strategy framework with auto-discovery, ML-based strategies, technical indicator strategies, and comprehensive backtesting support.

## Overview

The strategy system provides:
- **Abstract base class** for all trading strategies
- **Auto-discovery** of strategy implementations
- **ML Predictive Strategy** using gradient boosting models
- **Breakout Scalping Strategy** based on technical analysis
- **Signal generation** with confidence and position sizing
- **Position management** with stop loss and take profit
- **Strategy registry** for dynamic loading and instantiation
- **Metadata-driven** API for frontend integration

## Architecture

```
Strategy Registry (Auto-Discovery)
    ↓
Scan implementations/ folder
    ├─ MLPredictiveStrategy
    ├─ BreakoutScalpingStrategy
    └─ [Custom Strategies]
        ↓
Register with metadata
    ↓
Backtest Engine / Live Trading
    ↓
strategy.generate_signal(data)
    ├─ Analyze market data
    ├─ Apply indicators/ML models
    └─ Return Signal
        ↓
Signal
    ├─ Type: BUY/SELL/HOLD/CLOSE
    ├─ Confidence: 0.0 to 1.0
    ├─ Size: Position size (0.0 to 1.0)
    └─ Metadata: Strategy-specific data
        ↓
Portfolio Management
    ├─ Execute order
    ├─ Track position
    └─ Apply stop loss/take profit
```

## Backend Implementation

### Files

- **[backend/domain/strategies/base.py](../../backend/domain/strategies/base.py)** - Base classes (Strategy, Signal, Position)
- **[backend/domain/strategies/registry.py](../../backend/domain/strategies/registry.py)** - Strategy auto-discovery
- **[backend/domain/strategies/implementations/ml_predictive_strategy.py](../../backend/domain/strategies/implementations/ml_predictive_strategy.py)** - ML-based strategy
- **[backend/domain/strategies/implementations/breakout_scalping_strategy.py](../../backend/domain/strategies/implementations/breakout_scalping_strategy.py)** - Technical strategy
- **[backend/domain/strategies/portfolio.py](../../backend/domain/strategies/portfolio.py)** - Portfolio and position management

### Core Components

#### 1. Strategy Base Class

Abstract base class that all strategies must inherit from.

```python
from domain.strategies.base import Strategy, Signal, SignalType
import pandas as pd

class MyStrategy(Strategy):
    def __init__(self, param1=10, param2=0.5):
        super().__init__()
        self.param1 = param1
        self.param2 = param2

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on market data.

        Args:
            data: DataFrame with columns [open, high, low, close, volume]
                  Indexed by timestamp (DatetimeIndex)

        Returns:
            Signal object with trading decision
        """
        # Your strategy logic here
        current_price = data['close'].iloc[-1]

        if should_buy():
            return Signal(
                type=SignalType.BUY,
                timestamp=data.index[-1],
                price=current_price,
                confidence=0.8,
                size=1.0,  # Use 100% of available capital
                metadata={'reason': 'bullish_signal'}
            )

        return Signal(
            type=SignalType.HOLD,
            timestamp=data.index[-1],
            price=current_price
        )

    def get_name(self) -> str:
        return "MyStrategy"

    @classmethod
    def get_metadata(cls) -> dict:
        """Return strategy metadata for auto-discovery."""
        return {
            'name': 'MyStrategy',
            'label': 'My Custom Strategy',
            'description': 'A custom trading strategy',
            'requires_model': False,
            'category': 'technical',
            'parameters': {
                'param1': 10,
                'param2': 0.5
            }
        }
```

#### 2. Signal Types

```python
from domain.strategies.base import SignalType

# Available signal types
SignalType.BUY          # Open long position
SignalType.SELL         # Open short position (not used in spot trading)
SignalType.HOLD         # Do nothing
SignalType.CLOSE_LONG   # Close long position
SignalType.CLOSE_SHORT  # Close short position
```

**Signal Attributes:**
- `type`: Signal type (BUY/SELL/HOLD/CLOSE)
- `timestamp`: When signal was generated
- `price`: Price at signal generation
- `confidence`: Signal confidence (0.0 to 1.0)
- `size`: Position size as fraction of portfolio (0.0 to 1.0)
- `metadata`: Additional strategy-specific data (dict)

**Example Signals:**

```python
# Strong buy signal, full position
Signal(
    type=SignalType.BUY,
    timestamp=datetime.now(),
    price=42150.5,
    confidence=0.9,
    size=1.0,
    metadata={'indicator': 'golden_cross', 'strength': 'high'}
)

# Weak buy signal, small position
Signal(
    type=SignalType.BUY,
    timestamp=datetime.now(),
    price=42150.5,
    confidence=0.6,
    size=0.3,  # Only use 30% of capital
    metadata={'indicator': 'rsi_oversold', 'strength': 'medium'}
)

# Hold signal (do nothing)
Signal(
    type=SignalType.HOLD,
    timestamp=datetime.now(),
    price=42150.5,
    confidence=1.0,
    size=0.0
)
```

#### 3. Position Management

```python
from domain.strategies.base import Position
from datetime import datetime

# Create position
position = Position(
    symbol='BTC_USDT',
    side='long',
    entry_price=42000.0,
    entry_time=datetime.now(),
    size=0.1,  # 0.1 BTC
    current_price=42000.0,
    stop_loss=41500.0,  # -1.19% stop loss
    take_profit=43000.0  # +2.38% take profit
)

# Update current price
position.update_price(42500.0)

# Check P&L
print(f"Unrealized P&L: ${position.unrealized_pnl:.2f}")
print(f"Unrealized P&L %: {position.unrealized_pnl_pct:.2%}")

# Check exit conditions
if position.should_stop_loss():
    print("Stop loss hit!")

if position.should_take_profit():
    print("Take profit hit!")
```

**Position Properties:**
- `unrealized_pnl`: Profit/loss in currency (e.g., $50.00)
- `unrealized_pnl_pct`: Profit/loss as decimal fraction (e.g., 0.0119 = 1.19%)
- `should_stop_loss()`: Check if stop loss is hit
- `should_take_profit()`: Check if take profit is hit

#### 4. Strategy Registry (Auto-Discovery)

Automatically discovers and registers all strategies in the `implementations/` folder.

```python
from domain.strategies.registry import get_strategy_registry

registry = get_strategy_registry()

# List all available strategies
strategies = registry.get_all_strategies()
print(f"Available strategies: {list(strategies.keys())}")
# → ['MLPredictive', 'BreakoutScalping']

# Get strategy metadata (for API/frontend)
metadata_list = registry.get_available_strategies_metadata()
for meta in metadata_list:
    print(f"- {meta['label']}: {meta['description']}")

# Create strategy instance
strategy = registry.create_strategy(
    'MLPredictive',
    model_path='./models/BTC_USDT_1h_300steps_multi_ohlc',
    min_predicted_return=0.002
)

# Use strategy
signal = strategy.generate_signal(market_data)
```

**Auto-Discovery Process:**
1. Scan `domain/strategies/implementations/*.py`
2. Import each module
3. Find classes inheriting from `Strategy`
4. Call `get_metadata()` to register
5. Store in global registry

**Adding New Strategy:**
```python
# 1. Create file: implementations/my_strategy.py
# 2. Inherit from Strategy
# 3. Implement required methods
# 4. Add get_metadata() class method
# 5. That's it! Auto-discovered on next import
```

### Built-in Strategies

#### ML Predictive Strategy

Uses trained gradient boosting models to predict future prices and make trading decisions.

**Features:**
- Loads trained ML models (AutoregressivePricePredictor or MultiOHLCPredictor)
- Predicts N steps ahead
- Generates signals based on expected returns
- Configurable confidence thresholds
- Technical indicator pre-filtering
- Feature caching for fast backtesting

**Initialization:**
```python
from domain.strategies.implementations.ml_predictive_strategy import MLPredictiveStrategy

strategy = MLPredictiveStrategy(
    model_path='./models/BTC_USDT_1h_300steps_multi_ohlc',
    min_predicted_return=0.002,  # 0.2% minimum expected return
    confidence_threshold=0.6,
    prediction_window=60,  # Use first 60 minutes of predictions
    risk_per_trade=0.02,  # 2% risk per trade
    use_prefilter=True,  # Use technical indicator pre-filter
    prefilter_threshold=0.3  # Minimum setup score to trigger ML
)
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_path` | (required) | Path to trained ML model directory |
| `min_predicted_return` | 0.002 | Minimum predicted return to trigger signal (0.2%) |
| `confidence_threshold` | 0.6 | Minimum confidence for signal generation (0-1) |
| `prediction_window` | 60 | Number of future steps to consider |
| `risk_per_trade` | 0.02 | Fraction of capital to risk per trade |
| `use_prefilter` | True | Enable technical indicator pre-filtering |
| `prefilter_threshold` | 0.3 | Minimum setup score (0-1) to trigger ML |

**How It Works:**

1. **Pre-filtering (optional)**:
   - Check technical indicators (RSI, MACD, Bollinger Bands, etc.)
   - Calculate setup score (0-1)
   - Only call ML model if score > threshold
   - Reduces ML calls by ~80-90%

2. **ML Prediction**:
   - Load recent market data
   - Extract features (technical indicators, price patterns)
   - Run gradient boosting model
   - Get predicted OHLC prices for N steps ahead

3. **Signal Generation**:
   - Calculate expected return over prediction window
   - Check if return > min_predicted_return
   - Generate BUY signal if bullish
   - Set position size based on confidence

**Example Usage:**
```python
import pandas as pd

# Load market data
df = fetcher.fetch('BTC/USDT', '1h', ...)

# Generate signal
signal = strategy.generate_signal(df)

if signal.type == SignalType.BUY:
    print(f"BUY signal! Confidence: {signal.confidence:.2%}")
    print(f"Position size: {signal.size:.2%}")
    print(f"Metadata: {signal.metadata}")
```

**Feature Caching:**

For backtesting, pre-compute features for entire dataset:
```python
# Enable feature cache (10-50x faster backtests)
strategy.enable_feature_cache(full_data)

# Now backtesting will use cached features
engine = BacktestEngine(strategy=strategy, ...)
results = engine.run(full_data, ...)
```

#### Breakout Scalping Strategy

Technical analysis strategy based on range breakouts with EMA trend filtering.

**Features:**
- Consolidation range detection
- Breakout confirmation
- EMA trend filter
- 2:1 risk-reward ratio
- ATR-based stop loss (optional)
- Works best on volatile, liquid assets

**Initialization:**
```python
from domain.strategies.implementations.breakout_scalping_strategy import BreakoutScalpingStrategy

strategy = BreakoutScalpingStrategy(
    ema_period=20,
    range_lookback=20,  # Candles to look back for range detection
    range_threshold=0.003,  # Max range size (0.3% of price)
    breakout_confirmation=1,  # Candles to confirm breakout
    risk_reward_ratio=2.0,  # 2:1 risk-reward
    risk_per_trade=0.05,  # 5% per trade
    atr_period=14,
    use_atr_sl=False,  # Use ATR for stop loss
    min_range_size=0.0005  # Min 0.05% range to avoid micro-ranges
)
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ema_period` | 20 | Period for EMA trend filter |
| `range_lookback` | 20 | Candles to analyze for range detection |
| `range_threshold` | 0.003 | Max range size as fraction (0.3%) |
| `breakout_confirmation` | 1 | Candles needed to confirm breakout |
| `risk_reward_ratio` | 2.0 | Profit target as multiple of risk |
| `risk_per_trade` | 0.05 | Fraction of capital to risk per trade |
| `atr_period` | 14 | Period for ATR calculation |
| `use_atr_sl` | False | Use ATR-based stop loss |
| `min_range_size` | 0.0005 | Minimum range size (0.05%) |

**Entry Rules:**

1. **Identify Consolidation Range**:
   - Look back N candles
   - Calculate range: high_max - low_min
   - Range must be < threshold (e.g., 0.3% of price)
   - Range must be > min_range_size (avoid micro-ranges)

2. **Detect Breakout**:
   - Bullish: Close > range_high
   - Bearish: Close < range_low
   - Confirm for N candles

3. **Check EMA Filter**:
   - Long only if price > EMA(20)
   - Short only if price < EMA(20)

4. **Enter Position**:
   - Stop Loss: Just inside broken level
   - Take Profit: 2x stop loss distance

**Exit Rules:**
- **Stop Loss**: Set at range boundary (or ATR-based)
- **Take Profit**: 2:1 risk-reward ratio
- **Trailing Stop**: Not implemented (yet)

**Example Signal:**
```python
signal = strategy.generate_signal(df)

if signal.type == SignalType.BUY:
    # Metadata contains entry details
    print(f"Range: {signal.metadata['range_low']:.2f} - {signal.metadata['range_high']:.2f}")
    print(f"Entry: {signal.price:.2f}")
    print(f"Stop Loss: {signal.metadata['stop_loss']:.2f}")
    print(f"Take Profit: {signal.metadata['take_profit']:.2f}")
    print(f"Risk/Reward: 1:{signal.metadata['risk_reward']:.2f}")
```

### Creating Custom Strategies

**Step-by-Step Guide:**

1. **Create Strategy File**:
```python
# domain/strategies/implementations/my_custom_strategy.py

from domain.strategies.base import Strategy, Signal, SignalType
import pandas as pd

class MyCustomStrategy(Strategy):
    pass  # Implementation below
```

2. **Implement Required Methods**:
```python
def __init__(self, param1=10, param2=0.5):
    super().__init__()
    self.param1 = param1
    self.param2 = param2

def generate_signal(self, data: pd.DataFrame) -> Signal:
    """Your strategy logic here."""
    # Example: Simple moving average crossover
    if len(data) < self.param1:
        return Signal(
            type=SignalType.HOLD,
            timestamp=data.index[-1],
            price=data['close'].iloc[-1]
        )

    sma_short = data['close'].rolling(5).mean().iloc[-1]
    sma_long = data['close'].rolling(self.param1).mean().iloc[-1]

    if sma_short > sma_long:
        return Signal(
            type=SignalType.BUY,
            timestamp=data.index[-1],
            price=data['close'].iloc[-1],
            confidence=self.param2,
            size=1.0,
            metadata={'sma_short': sma_short, 'sma_long': sma_long}
        )

    return Signal(
        type=SignalType.HOLD,
        timestamp=data.index[-1],
        price=data['close'].iloc[-1]
    )

def get_name(self) -> str:
    return "MyCustomStrategy"

@classmethod
def get_metadata(cls) -> dict:
    return {
        'name': 'MyCustomStrategy',
        'label': 'My Custom Strategy',
        'description': 'Simple moving average crossover strategy',
        'requires_model': False,
        'category': 'technical',
        'parameters': {
            'param1': 10,
            'param2': 0.5
        }
    }
```

3. **Test Strategy**:
```python
from domain.strategies.registry import get_strategy_registry

# Auto-discovered!
registry = get_strategy_registry()
strategy = registry.create_strategy('MyCustomStrategy', param1=20)

# Backtest
from backtesting.engine import BacktestEngine
engine = BacktestEngine(strategy=strategy, initial_cash=10000)
results = engine.run(data, symbol='BTC_USDT')
```

**Best Practices:**

1. **Always validate data**:
```python
def generate_signal(self, data: pd.DataFrame) -> Signal:
    # Check minimum data requirements
    if len(data) < self.min_lookback:
        return Signal(SignalType.HOLD, data.index[-1], data['close'].iloc[-1])

    # Your logic here
```

2. **Use metadata for debugging**:
```python
return Signal(
    type=SignalType.BUY,
    timestamp=timestamp,
    price=price,
    metadata={
        'indicator_values': {...},
        'trigger': 'breakout',
        'confidence_breakdown': {...}
    }
)
```

3. **Handle edge cases**:
```python
# Avoid division by zero
if price > 0:
    return_pct = (predicted_price - price) / price
else:
    return_pct = 0.0

# Handle missing data
if data['close'].isna().any():
    return Signal(SignalType.HOLD, ...)
```

4. **Optimize for backtesting**:
```python
# Use vectorized operations (pandas/numpy)
# Good: Fast
sma = data['close'].rolling(20).mean()

# Bad: Slow
sma = [data['close'].iloc[i:i+20].mean() for i in range(len(data))]
```

## Usage Examples

### Example 1: Simple Backtest with ML Strategy

```python
from backtesting.engine import BacktestEngine
from domain.strategies.implementations.ml_predictive_strategy import MLPredictiveStrategy
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

# Fetch data
fetcher = HistoricalDataFetcher()
df = fetcher.fetch(
    'BTC/USDT',
    '1h',
    start=datetime.now() - timedelta(days=30),
    end=datetime.now()
)

# Create strategy
strategy = MLPredictiveStrategy(
    model_path='./models/BTC_USDT_1h_300steps_multi_ohlc',
    min_predicted_return=0.002,
    confidence_threshold=0.7
)

# Enable feature caching for faster backtest
strategy.enable_feature_cache(df)

# Run backtest
engine = BacktestEngine(
    strategy=strategy,
    initial_cash=10000.0,
    commission=0.001,
    slippage=0.0005
)

results = engine.run(df, symbol='BTC/USDT')

# Print results
print(f"Total Return: {results['performance']['total_return']:.2%}")
print(f"Sharpe Ratio: {results['performance']['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['performance']['max_drawdown']:.2%}")
print(f"Total Trades: {results['trading']['total_trades']}")
```

### Example 2: Compare Multiple Strategies

```python
from domain.strategies.registry import get_strategy_registry
from backtesting.engine import BacktestEngine

# Get registry
registry = get_strategy_registry()

# List available strategies
strategies = registry.get_all_strategies()

# Backtest each strategy
results_comparison = []

for strategy_name in strategies.keys():
    print(f"\nTesting {strategy_name}...")

    # Create strategy
    strategy = registry.create_strategy(
        strategy_name,
        # Add strategy-specific params here
    )

    # Run backtest
    engine = BacktestEngine(strategy=strategy, initial_cash=10000)
    results = engine.run(df, symbol='BTC/USDT')

    results_comparison.append({
        'strategy': strategy_name,
        'total_return': results['performance']['total_return'],
        'sharpe_ratio': results['performance']['sharpe_ratio'],
        'max_drawdown': results['performance']['max_drawdown'],
        'win_rate': results['trading']['win_rate']
    })

# Print comparison
import pandas as pd
comparison_df = pd.DataFrame(results_comparison)
print("\n=== Strategy Comparison ===")
print(comparison_df.to_string(index=False))
```

### Example 3: Live Signal Generation

```python
import time
from datetime import datetime, timedelta

strategy = MLPredictiveStrategy(
    model_path='./models/BTC_USDT_1h_300steps_multi_ohlc',
    min_predicted_return=0.003
)

while True:
    # Fetch latest data
    df = fetcher.fetch(
        'BTC/USDT',
        '1h',
        start=datetime.now() - timedelta(days=7),
        end=datetime.now(),
        force_refresh=True
    )

    # Generate signal
    signal = strategy.generate_signal(df)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if signal.type == SignalType.BUY:
        print(f"[{current_time}] BUY SIGNAL!")
        print(f"  Price: ${signal.price:,.2f}")
        print(f"  Confidence: {signal.confidence:.2%}")
        print(f"  Size: {signal.size:.2%}")
        print(f"  Metadata: {signal.metadata}")
        # Execute trade here

    elif signal.type == SignalType.HOLD:
        print(f"[{current_time}] HOLD - No action")

    # Wait 1 hour before next check
    time.sleep(3600)
```

### Example 4: Custom Strategy with Indicators

```python
from domain.strategies.base import Strategy, Signal, SignalType
import pandas as pd
import pandas_ta as ta

class RSIMACDStrategy(Strategy):
    """Combines RSI oversold/overbought with MACD crossover."""

    def __init__(self, rsi_period=14, rsi_oversold=30, rsi_overbought=70):
        super().__init__()
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        if len(data) < 50:
            return Signal(SignalType.HOLD, data.index[-1], data['close'].iloc[-1])

        # Calculate indicators
        rsi = ta.rsi(data['close'], length=self.rsi_period)
        macd = ta.macd(data['close'])

        current_rsi = rsi.iloc[-1]
        macd_line = macd['MACD_12_26_9'].iloc[-1]
        signal_line = macd['MACDs_12_26_9'].iloc[-1]

        # BUY: RSI oversold + MACD bullish crossover
        if current_rsi < self.rsi_oversold and macd_line > signal_line:
            return Signal(
                type=SignalType.BUY,
                timestamp=data.index[-1],
                price=data['close'].iloc[-1],
                confidence=0.8,
                size=1.0,
                metadata={'rsi': current_rsi, 'macd_cross': 'bullish'}
            )

        # CLOSE: RSI overbought
        if current_rsi > self.rsi_overbought and self.current_position:
            return Signal(
                type=SignalType.CLOSE_LONG,
                timestamp=data.index[-1],
                price=data['close'].iloc[-1],
                confidence=1.0,
                metadata={'rsi': current_rsi, 'reason': 'overbought'}
            )

        return Signal(SignalType.HOLD, data.index[-1], data['close'].iloc[-1])

    def get_name(self) -> str:
        return "RSIMACDStrategy"

    @classmethod
    def get_metadata(cls) -> dict:
        return {
            'name': 'RSIMACDStrategy',
            'label': 'RSI + MACD Strategy',
            'description': 'Combines RSI oversold/overbought with MACD crossover',
            'requires_model': False,
            'category': 'technical',
            'parameters': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
        }
```

## Performance Considerations

### Feature Caching

**Problem**: ML strategies recalculate features for overlapping data windows on every bar.

**Solution**: Pre-compute features for entire dataset once.

**Performance Gain**: 10-50x faster backtests

```python
# Without caching (SLOW)
strategy = MLPredictiveStrategy(model_path=...)
results = engine.run(df, symbol='BTC_USDT')
# → 300 bars: 45 seconds

# With caching (FAST)
strategy = MLPredictiveStrategy(model_path=...)
strategy.enable_feature_cache(df)
results = engine.run(df, symbol='BTC_USDT')
# → 300 bars: 3 seconds (15x faster)
```

### Vectorization

**Use pandas/numpy operations instead of loops:**

```python
# Bad: Slow (loops)
sma = []
for i in range(20, len(data)):
    sma.append(data['close'].iloc[i-20:i].mean())

# Good: Fast (vectorized)
sma = data['close'].rolling(20).mean()
```

### Indicator Caching

**Cache expensive calculations:**

```python
class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self._indicator_cache = {}

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        # Cache key based on data length (assumes appending data)
        cache_key = len(data)

        if cache_key not in self._indicator_cache:
            # Calculate expensive indicator
            self._indicator_cache[cache_key] = expensive_indicator(data)

        indicator = self._indicator_cache[cache_key]
        # Use indicator...
```

## Troubleshooting

### "Strategy not found" Error

**Symptoms:**
```
[StrategyRegistry] Strategy not found: MLPredictive
```

**Causes:**
1. Typo in strategy name
2. Strategy file not in `implementations/` folder
3. Strategy doesn't implement `get_metadata()`

**Solutions:**
```python
# List available strategies
registry = get_strategy_registry()
print("Available:", list(registry.get_all_strategies().keys()))

# Check strategy metadata
metadata = MyStrategy.get_metadata()
print(f"Name: {metadata['name']}")
```

### Signal Confidence Out of Range

**Symptoms:**
```
ValueError: Confidence must be between 0 and 1, got 1.5
```

**Solution:**
```python
# Clamp confidence to valid range
confidence = min(max(raw_confidence, 0.0), 1.0)

signal = Signal(
    type=SignalType.BUY,
    timestamp=timestamp,
    price=price,
    confidence=confidence
)
```

### Position Size Out of Range

**Symptoms:**
```
ValueError: Size must be between 0 and 1, got -0.5
```

**Solution:**
```python
# Validate size
size = max(0.0, min(calculated_size, 1.0))

signal = Signal(
    type=SignalType.BUY,
    timestamp=timestamp,
    price=price,
    size=size
)
```

### Strategy Not Generating Signals

**Debug checklist:**
1. Check minimum data requirements
2. Print indicator values
3. Verify entry conditions
4. Test with simpler logic

```python
def generate_signal(self, data: pd.DataFrame) -> Signal:
    # Add debug logging
    print(f"Data length: {len(data)}")
    print(f"Last close: {data['close'].iloc[-1]}")

    # Test entry conditions
    if should_buy():
        print("BUY condition met!")
        return Signal(SignalType.BUY, ...)
    else:
        print("BUY condition NOT met")
        return Signal(SignalType.HOLD, ...)
```

## Related Documentation

- [Backtesting System](03-BACKTESTING.md) - Uses strategies for historical simulation
- [ML & Predictions](02-ML-PREDICTIONS.md) - ML models used by MLPredictiveStrategy
- [Market Data](05-MARKET-DATA.md) - Provides OHLCV data to strategies
- [Portfolio Management](07-PORTFOLIO.md) - Position tracking and management
