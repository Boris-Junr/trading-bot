# Trading Strategy Implementations

This directory contains implemented trading strategies ready for backtesting and live trading.

## Available Strategies

### MLPredictiveStrategy

Machine learning-based strategy that uses gradient boosting models to predict future prices and generate trading signals.

#### Overview

The ML Predictive Strategy leverages trained LightGBM models to forecast price movements over the next N minutes. It generates BUY/SELL signals based on:
- **Predicted average return** over a prediction window
- **Prediction consistency** (consecutive positive/negative forecasts)
- **Prediction confidence** (based on return volatility)

#### Parameters

```python
MLPredictiveStrategy(
    model_path: str,                    # Path to saved model directory
    min_predicted_return: float = 0.002,  # 0.2% minimum expected gain
    confidence_threshold: float = 0.6,    # Minimum confidence for signals
    prediction_window: int = 60,          # Use first 60 minutes of predictions
    risk_per_trade: float = 0.02          # 2% risk per trade
)
```

**Parameter Details:**

- **model_path**: Directory containing the trained GradientBoostingPredictor model
  - Example: `"analysis/models/saved/ETH_USDT_1m_300steps"`

- **min_predicted_return**: Minimum predicted return to trigger a signal
  - Too low (< 0.001): More trades but lower quality
  - Too high (> 0.005): Fewer trades but higher quality
  - Recommended: 0.002 (0.2%) for 1m timeframe

- **confidence_threshold**: Minimum confidence required to execute a trade
  - Range: 0.0 to 1.0
  - Higher values = fewer but higher conviction trades
  - Recommended: 0.6 (60% confidence)

- **prediction_window**: Number of future minutes to consider
  - Should be ≤ model's n_steps_ahead
  - Shorter window = more reactive to near-term predictions
  - Longer window = smoother, trend-following behavior
  - Recommended: 60 minutes for 5-hour prediction models

- **risk_per_trade**: Fraction of capital to risk per trade
  - Range: 0.01 (1%) to 0.05 (5%)
  - Used for position sizing based on stop loss distance
  - Recommended: 0.02 (2%)

#### Signal Generation Logic

**BUY Signal** is generated when:
1. Average predicted return > `min_predicted_return`
2. Confidence score ≥ `confidence_threshold`
3. No existing position

**Confidence Calculation:**
```
confidence = (
    |avg_return| / min_predicted_return * 0.5 +
    consecutive_positive / window * 0.3 +
    (1 - min(1, std / 0.01)) * 0.2
)
```

Components:
- **50%**: Magnitude of predicted return relative to threshold
- **30%**: Consistency of direction (consecutive positive/negative)
- **20%**: Certainty (inverse of prediction volatility)

**SELL Signal** (for short positions):
- Same logic as BUY, but for negative predicted returns

**HOLD Signal**:
- When predicted return is below threshold
- When confidence is below threshold
- When prediction is neutral

#### Position Management

**Entry:**
- Position size calculated using risk-based sizing
- Stop loss set at `current_price * (1 - risk_per_trade)`
- Take profit set at `current_price * (1 + max_predicted_return)`

**Exit:**
- Stop loss or take profit hit
- Predictions turn against position (next 15 minutes)
- Manual close signal from strategy

**Dynamic Adjustment:**
- Position size scaled by signal confidence
- Maximum position limited to 20% of capital

#### Usage Example

```python
from strategies.implementations import MLPredictiveStrategy
from backtesting.engine import BacktestEngine
from data.fetchers.crypto_fetcher import CryptoFetcher
from datetime import datetime, timedelta

# Initialize strategy with trained model
strategy = MLPredictiveStrategy(
    model_path='analysis/models/saved/ETH_USDT_1m_300steps',
    min_predicted_return=0.002,  # 0.2% threshold
    confidence_threshold=0.65,    # 65% confidence required
    prediction_window=60,         # Use first hour of predictions
    risk_per_trade=0.02          # 2% risk per trade
)

# Fetch historical data
fetcher = CryptoFetcher()
end = datetime.now()
start = end - timedelta(days=20)
df = fetcher.fetch('ETH/USDT', '1m', start, end, limit=None)

# Create backtest engine
engine = BacktestEngine(
    strategy=strategy,
    initial_cash=10000,
    commission=0.001,
    stop_loss_pct=0.02,
    take_profit_pct=0.04
)

# Run backtest
results = engine.run(df, symbol='ETH/USDT')
```

#### Running with Scenario File

```bash
# Using the pre-configured scenario
cd backend
python run_backtest.py ml_predictive_eth_1m.json
```

#### Interpreting Signal Metadata

Each signal includes metadata with prediction details:

```python
signal.metadata = {
    'predicted_avg_return': 0.0035,      # Average predicted return
    'predicted_max_return': 0.0068,      # Best case in window
    'predicted_min_return': 0.0012,      # Worst case in window
    'return_std': 0.0008,                # Volatility of predictions
    'consecutive_positive': 15,           # Consecutive bullish predictions
    'target_price': 2050.50,             # Calculated target
    'stop_loss': 2009.80,                # Calculated stop
    'prediction_window': 60              # Minutes analyzed
}
```

#### Performance Tuning

**For more aggressive trading:**
```python
strategy = MLPredictiveStrategy(
    min_predicted_return=0.0015,  # Lower threshold
    confidence_threshold=0.5,      # Lower confidence
    prediction_window=30,          # Shorter window
    risk_per_trade=0.03           # Higher risk
)
```

**For conservative trading:**
```python
strategy = MLPredictiveStrategy(
    min_predicted_return=0.003,   # Higher threshold
    confidence_threshold=0.75,     # Higher confidence
    prediction_window=120,         # Longer window
    risk_per_trade=0.01           # Lower risk
)
```

**For scalping (very short-term):**
```python
strategy = MLPredictiveStrategy(
    min_predicted_return=0.001,   # Small moves
    confidence_threshold=0.7,      # High confidence still needed
    prediction_window=15,          # Next 15 minutes only
    risk_per_trade=0.02
)
```

#### Model Requirements

The strategy requires a trained GradientBoostingPredictor model:

1. **Train a model** first:
```bash
cd backend
python analysis/models/train_price_predictor.py
```

2. **Verify model exists**:
```
analysis/models/saved/ETH_USDT_1m_300steps/
├── config.pkl
├── model_step_1.txt
├── model_step_2.txt
...
└── model_step_300.txt
```

3. **Use model path** in strategy initialization

#### Limitations

- Requires at least 100 bars of historical data for feature engineering
- Model predictions degrade for horizons beyond training data characteristics
- Works best on timeframes it was trained on (e.g., 1m model for 1m trading)
- Does not account for fundamental news or black swan events
- Assumes market conditions similar to training period

#### Best Practices

1. **Retrain models regularly** (every 1-2 days for 1m timeframe)
2. **Validate on recent data** before live trading
3. **Monitor prediction drift** in production
4. **Combine with risk management** (stop loss, position sizing)
5. **Test different parameter combinations** via backtesting
6. **Consider ensemble approaches** (multiple models, timeframes)

#### Comparison with Other Strategies

| Feature | ML Predictive | Technical (MACD/RSI) | Pattern-Based |
|---------|---------------|----------------------|---------------|
| Prediction horizon | 5 hours | Current state | Pattern completion |
| Signal frequency | Medium | High | Low |
| Adaptability | High (retrains) | Low (fixed params) | Medium |
| Data requirements | High (30+ days) | Low (100 bars) | Medium |
| Interpretability | Medium (feature importance) | High (clear rules) | High (visual) |
| Computational cost | High (training) | Low | Low |

#### Future Enhancements

Potential improvements:
- [ ] Multi-timeframe ensemble (1m + 5m predictions)
- [ ] Volatility regime detection (adjust thresholds)
- [ ] Market state classification (trending/ranging)
- [ ] Incorporate bid-ask spread in prediction
- [ ] Dynamic prediction window based on volatility
- [ ] Probability distribution instead of point predictions

## Adding New Strategies

To add a new strategy:

1. Create new file: `strategies/implementations/your_strategy.py`
2. Inherit from `Strategy` base class
3. Implement required methods:
   - `generate_signal(df: pd.DataFrame) -> Signal`
   - `should_close_position(position: Position, df: pd.DataFrame) -> bool`
   - `get_position_size(signal: Signal, capital: float, price: float) -> float`
4. Add to `__init__.py` exports
5. Create backtest scenario in `backtesting/scenarios/`
6. Test with `run_backtest.py`

## Testing Strategies

```bash
# Run specific scenario
python run_backtest.py ml_predictive_eth_1m.json

# Use slash command (if available)
/backtest ml_predictive_eth_1m.json
```
