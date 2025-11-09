# Price Prediction Model

Autoregressive gradient boosting model for predicting future cryptocurrency prices.

## Overview

The prediction system uses **autoregressive gradient boosting** to predict future prices for multiple steps ahead. The model predicts one step at a time, feeding each prediction back to generate the next, creating smooth and coherent price curves.

### Key Features

- **Single model architecture**: ONE LightGBM model predicts entire curve autoregressively
- **Smooth predictions**: Sequential predictions form realistic, coherent price movements
- **Fast training**: ~2-3 minutes for 300-step prediction model
- **Small model size**: ~400KB vs multi-gigabyte alternatives
- **Comprehensive features**: 85 engineered features including:
  - Price-based: returns, momentum, acceleration, volatility
  - Technical indicators: EMA, MACD, RSI, Stochastic, Bollinger Bands, ATR
  - Rolling statistics: mean, std, z-score, position in range
  - Pattern features: trend direction, candle patterns, volume patterns
  - Time features: hour, day of week (cyclically encoded)
- **Time-series aware**: Proper train/test split preserving temporal order
- **Production-ready**: Model saving/loading, feature importance analysis

## How It Works

### Autoregressive Prediction

Unlike traditional approaches that train separate models for each time step, we use a single model that:

1. **Trains on next-step prediction**: The model learns to predict price at t+1 given features at t
2. **Iteratively generates curve**:
   - Start with current market data
   - Predict next price (t+1)
   - Update features with predicted price
   - Predict next price (t+2)
   - Repeat for N steps
3. **Creates smooth curves**: Since each prediction builds on the previous, the curve is naturally smooth and realistic

**Advantages:**
- ✅ Predictions form coherent price curves
- ✅ Natural sequential dependency learning
- ✅ Fast training (single model)
- ✅ Compact model size
- ✅ Realistic price movements

**Trade-offs:**
- ⚠️ Prediction errors compound over time
- ⚠️ Most accurate for short-term (1-60 minutes)
- ⚠️ Longer horizons (180-300 min) better for trend direction than exact prices

## Architecture

```
analysis/models/
├── features/
│   └── price_features.py              # Feature engineering (PriceFeatureEngineer)
├── predictors/
│   └── autoregressive_predictor.py   # Main predictor (AutoregressivePricePredictor)
├── saved/                             # Trained models saved here
└── train_price_predictor.py          # Training script
```

## Usage

### 1. Training a Model

```python
from analysis.models.predictors.autoregressive_predictor import AutoregressivePricePredictor
from data.fetchers.crypto_fetcher import CryptoFetcher
from datetime import datetime, timedelta

# Fetch data
fetcher = CryptoFetcher()
end = datetime.now()
start = end - timedelta(days=30)
df = fetcher.fetch('ETH/USDT', '1m', start, end, limit=None)

# Initialize predictor
predictor = AutoregressivePricePredictor(
    n_steps_ahead=300,  # Predict next 300 steps (5 hours for 1m)
    lookback_periods=[5, 10, 20, 50]
)

# Prepare data
train_df, test_df = predictor.prepare_data(df, test_size=0.2)

# Train
training_metrics = predictor.train(
    train_df,
    validation_split=0.2,
    num_boost_round=500,
    early_stopping_rounds=50
)

# Evaluate
eval_steps = [1, 15, 30, 60, 120, 180, 240, 300]
test_metrics = predictor.evaluate(test_df, eval_steps=eval_steps)

# Save
predictor.save('analysis/models/saved/eth_1m_300steps_autoregressive')
```

### 2. Loading and Using a Trained Model

```python
from analysis.models.predictors.autoregressive_predictor import AutoregressivePricePredictor

# Load model
predictor = AutoregressivePricePredictor(n_steps_ahead=300)
predictor.load('analysis/models/saved/ETH_USDT_1m_300steps_autoregressive')

# Predict on new data
predictions = predictor.predict(current_df)

# Get predictions
for step in [1, 5, 15, 30, 60]:
    pred_price = predictions[f'predicted_price_{step}'].iloc[0]
    pred_return = predictions[f'predicted_return_{step}'].iloc[0]
    print(f"Step {step}: ${pred_price:.2f} ({pred_return:+.2%})")
```

### 3. Quick Training Script

```bash
cd backend
python analysis/models/train_price_predictor.py
```

This will:
- Fetch 30 days of ETH/USDT 1m data
- Train autoregressive model for 300 steps ahead
- Save to `analysis/models/saved/ETH_USDT_1m_300steps_autoregressive/`
- Display performance metrics and smoothness analysis

## Model Configuration

### Default Hyperparameters

```python
model_params = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'num_leaves': 31,           # Max leaves per tree
    'learning_rate': 0.05,       # Learning rate
    'feature_fraction': 0.8,     # Use 80% of features per tree
    'bagging_fraction': 0.8,     # Use 80% of data per tree
    'bagging_freq': 5,           # Bagging every 5 iterations
    'verbose': -1,
    'min_data_in_leaf': 20,      # Min samples per leaf
    'max_depth': 7,              # Max tree depth
}
```

### Customization

```python
# For faster training (less accuracy)
predictor = AutoregressivePricePredictor(
    n_steps_ahead=60,
    lookback_periods=[5, 10, 20],
    model_params={
        'learning_rate': 0.1,
        'num_leaves': 15,
        'max_depth': 5,
    }
)

# For better accuracy (slower training)
predictor = AutoregressivePricePredictor(
    n_steps_ahead=300,
    lookback_periods=[5, 10, 20, 50, 100],
    model_params={
        'learning_rate': 0.03,
        'num_leaves': 50,
        'max_depth': 9,
    }
)
```

## Feature Engineering

### Automatic Feature Extraction

The `PriceFeatureEngineer` automatically creates 85 features:

**Price Features (13)**
- Returns: 1, 2, 5, 10 periods
- Log returns: 1, 5 periods
- Momentum: 5, 10, 20 periods
- Acceleration, HL range, OC range, body-to-range ratio, gaps

**Technical Indicators (20)**
- EMAs: 5, 10, 20, 50
- Price to EMA ratios
- MACD + signal + histogram
- RSI: 7, 14, 21
- Stochastic K and D
- Bollinger Bands (upper, middle, lower, width, position)
- ATR and ATR percentage

**Rolling Statistics (per lookback period × 4 periods = 24)**
- Mean, std, z-score
- Min, max, position in range
- Return volatility

**Pattern Features (11)**
- Trend direction (short, medium, long)
- Candle type (bullish/bearish)
- Shadow ratios
- Consecutive candles
- Volume patterns

**Time Features (8)**
- Hour, minute, day of week
- Cyclical encoding (sine/cosine)

## Evaluation Metrics

The model reports:
- **RMSE**: Root Mean Squared Error (lower is better)
- **MAE**: Mean Absolute Error (lower is better)
- **R²**: Coefficient of determination (higher is better, max 1.0)
- **MAPE**: Mean Absolute Percentage Error (lower is better)

### Interpreting Results

**Short-term (1-15 minutes):**
- R² > 0.8: Excellent predictions
- MAPE < 0.5%: Very accurate

**Medium-term (15-60 minutes):**
- R² > 0.5: Good trend prediction
- MAPE < 2%: Reasonable accuracy

**Long-term (60-300 minutes):**
- R² may be negative (errors compounding)
- Use for trend direction, not exact prices
- MAPE < 5%: Acceptable for directional signals

### Typical Performance (ETH/USDT 1m)

```
Step   RMSE    MAE     R²      MAPE
1min   1.92    1.63    0.914   0.04%   ← Excellent
15min  65.26   63.83   varying 1.59%   ← Good
60min  varies  varies  varying ~5-10%  ← Trend indicator
300min varies  varies  varying ~4-10%  ← Direction only
```

## Production Integration

### Using in a Trading Strategy

```python
from strategies.implementations import MLPredictiveStrategy

# Initialize strategy with trained model
strategy = MLPredictiveStrategy(
    model_path='analysis/models/saved/ETH_USDT_1m_300steps_autoregressive',
    min_predicted_return=0.002,  # 0.2% threshold
    confidence_threshold=0.65,    # 65% confidence required
    prediction_window=60,         # Use first hour of predictions
    risk_per_trade=0.02          # 2% risk per trade
)

# The strategy will:
# 1. Generate predictions for next 300 minutes
# 2. Calculate average return over prediction window (60 min)
# 3. Assess prediction consistency and confidence
# 4. Generate BUY/SELL/HOLD signal
# 5. Size positions based on confidence and risk management
```

### Running Backtests

```bash
cd backend
python run_backtest.py ml_predictive_eth_1m.json
```

Or programmatically:

```python
from backtesting.engine import BacktestEngine
from strategies.implementations import MLPredictiveStrategy

strategy = MLPredictiveStrategy(
    model_path='analysis/models/saved/ETH_USDT_1m_300steps_autoregressive',
    min_predicted_return=0.002,
    confidence_threshold=0.65,
    prediction_window=60
)

engine = BacktestEngine(
    strategy=strategy,
    initial_cash=10000,
    commission=0.001,
    stop_loss_pct=0.02,
    take_profit_pct=0.04
)

results = engine.run(historical_df, symbol='ETH/USDT')
```

## Best Practices

### 1. Data Requirements

- **Minimum**: 10,000+ bars (7 days at 1m)
- **Recommended**: 30,000+ bars (20 days at 1m)
- **Optimal**: 60,000+ bars (40 days at 1m)

### 2. Retraining Schedule

- **1m timeframe**: Retrain every 1-2 days
- **5m timeframe**: Retrain every 3-5 days
- **15m+ timeframe**: Retrain every 7-10 days

### 3. Prediction Horizons

**Use different windows for different strategies:**
- **Scalping (< 5 min)**: prediction_window=5-15
- **Day trading (30-60 min)**: prediction_window=30-60
- **Swing trading (2-4 hours)**: prediction_window=120-240
- **Position trading**: Use longer prediction horizon as trend indicator

### 4. Validation

- Always use time-series split (not random shuffle)
- Test on recent data (last 20% chronologically)
- Monitor prediction drift in production
- Check curve smoothness (should be < 2.0)

### 5. Feature Selection

- Check feature importance after training
- Top features typically: close_min/max, EMA values
- Remove low-importance features (<1% gain) for faster inference

## Performance Tips

### Speed Optimization

```python
# Faster training for development
model_params = {
    'num_leaves': 15,        # Fewer leaves = faster
    'max_depth': 5,          # Shallower trees = faster
    'feature_fraction': 0.6, # Fewer features = faster
    'learning_rate': 0.1,    # Faster convergence
}
```

### Memory Optimization

```python
# Reduce memory for very large datasets
lookback_periods = [5, 10, 20]  # Fewer rolling periods
n_steps_ahead = 60               # Predict fewer steps
```

## Smoothness Analysis

After training, the script analyzes prediction curve smoothness:

```
First 60 predictions analysis:
  Average step change: $8.25
  Std of step changes: $10.68
  Max single step jump: $26.19
  Smoothness score: 1.29 (lower is smoother)
```

**Ideal smoothness scores:**
- < 1.5: Very smooth, realistic curves
- 1.5 - 2.5: Smooth, acceptable
- > 2.5: May need parameter tuning

## Troubleshooting

### Low R² Score on Training

- Increase training data (more days)
- Tune hyperparameters (higher num_leaves, max_depth)
- Add more relevant features
- Check for data quality issues

### Overfitting (Train R² >> Val R²)

- Reduce max_depth
- Increase min_data_in_leaf
- Lower learning_rate
- Enable early stopping (already enabled by default)

### High MAPE

- Crypto is inherently volatile
- Focus on short-term predictions (1-60 min)
- Use prediction window of 15-60 minutes
- Consider predictions as directional signals, not exact prices

### Negative R² on Test Set (Long Horizons)

- **This is expected** for autoregressive models beyond 60-120 minutes
- Errors compound over time
- Use long-horizon predictions for trend direction only
- Focus trading decisions on short-term predictions (1-60 min)

### Prediction Drift in Production

- Retrain model regularly (daily for 1m timeframe)
- Monitor MAE over time
- Check if market regime has changed
- Validate on recent out-of-sample data

## Future Enhancements

Potential improvements:
- [ ] Ensemble with LSTM for very long horizons
- [ ] Volatility regime detection (adjust prediction confidence)
- [ ] Market state classification (trending/ranging)
- [ ] Multi-timeframe predictions (1m + 5m)
- [ ] Online learning (incremental updates)
- [ ] Prediction uncertainty estimation
- [ ] Order book imbalance features

## References

- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Time Series Cross-Validation](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)
- [Autoregressive Models](https://en.wikipedia.org/wiki/Autoregressive_model)
- [Feature Engineering for Time Series](https://www.kaggle.com/code/kashnitsky/topic-9-part-1-time-series-analysis-in-python)
