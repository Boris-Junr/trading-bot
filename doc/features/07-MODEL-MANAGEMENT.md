# Model Management & Machine Learning

Comprehensive ML model training, prediction, and lifecycle management using gradient boosting for time-series price forecasting with autoregressive and multi-output architectures.

## Overview

The ML system provides:
- **Autoregressive prediction** - Single model predicts iteratively for smooth price curves
- **Multi-OHLC prediction** - Four specialized models predict Open, High, Low, Close
- **Feature engineering** - 100+ technical indicators and patterns
- **Model persistence** - Save/load trained models
- **Training pipeline** - Automated data preparation and validation
- **Performance metrics** - R², RMSE, MAE tracking
- **API integration** - Train and predict via REST API

## Architecture

```
Historical Data (OHLCV)
    ↓
Feature Engineering (100+ features)
    ├─ Price features (returns, momentum)
    ├─ Technical indicators (RSI, MACD, BB, ATR)
    ├─ Rolling statistics (SMA, volatility)
    ├─ Pattern features (candlestick patterns)
    └─ Time features (hour, day of week)
        ↓
Model Training
    ├─ Autoregressive Predictor (1 model)
    │   └─ Predicts next price iteratively
    │
    └─ Multi-OHLC Predictor (4 models)
        ├─ Open predictor
        ├─ High predictor
        ├─ Low predictor
        └─ Close predictor
            ↓
Model Evaluation
    ├─ Train/Val split
    ├─ Early stopping
    ├─ Metrics (R², RMSE, MAE)
    └─ Validation plots
        ↓
Model Persistence
    ├─ LightGBM models (.txt)
    ├─ Config (n_steps, features, etc.)
    └─ Training metrics
        ↓
Prediction Service
    ├─ Load model
    ├─ Fetch recent data
    ├─ Engineer features
    ├─ Generate predictions
    └─ Return forecasts (JSON)
```

## Backend Implementation

### Files

- **[backend/domain/ml/predictors/autoregressive_predictor.py](../../backend/domain/ml/predictors/autoregressive_predictor.py)** - Single-model autoregressive predictor
- **[backend/domain/ml/predictors/multi_ohlc_predictor.py](../../backend/domain/ml/predictors/multi_ohlc_predictor.py)** - Four-model OHLC predictor
- **[backend/domain/ml/features/price_features.py](../../backend/domain/ml/features/price_features.py)** - Feature engineering
- **[backend/api/services/ml_service.py](../../backend/api/services/ml_service.py)** - ML service layer
- **[backend/api/routers/predictions.py](../../backend/api/routers/predictions.py)** - Prediction API endpoints

### Core Components

#### 1. Autoregressive Predictor

Single LightGBM model that predicts N steps ahead by iteratively feeding predictions back as inputs.

**Architecture:**
```
Input Features → LightGBM Model → Next Price Prediction
                      ↑_______________|
                   (Feed prediction back)
```

**Why Autoregressive?**
- **Smooth predictions**: Feeding predictions back creates coherent price curves
- **Single model**: Train one model instead of 300 separate models
- **Fast inference**: One model = fast prediction
- **Memory efficient**: Store one model instead of hundreds

**Initialization:**
```python
from domain.ml.predictors.autoregressive_predictor import AutoregressivePricePredictor

predictor = AutoregressivePricePredictor(
    n_steps_ahead=300,  # Predict 300 steps into future
    lookback_periods=[5, 10, 20, 50],  # Rolling window sizes
    model_params={
        'objective': 'regression',
        'metric': 'rmse',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'max_depth': 7
    }
)
```

**Training:**
```python
import pandas as pd
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

# Fetch training data
fetcher = HistoricalDataFetcher()
df = fetcher.fetch(
    'BTC/USDT',
    '1m',
    start=datetime.now() - timedelta(days=30),
    end=datetime.now()
)

# Prepare data
train_data, test_data = predictor.prepare_data(df, test_size=0.2)

# Train model
metrics = predictor.train(
    train_data,
    validation_split=0.2,
    num_boost_round=500,
    early_stopping_rounds=50,
    verbose=True
)

print(f"Train R²: {metrics['train']['r2']:.4f}")
print(f"Val R²: {metrics['val']['r2']:.4f}")
print(f"Val RMSE: {metrics['val']['rmse']:.4f}")
```

**Prediction:**
```python
# Predict future prices
predictions = predictor.predict(test_data)

# Returns DataFrame with columns:
# - predicted_price_1, predicted_price_2, ..., predicted_price_300
# - predicted_return_1, predicted_return_2, ..., predicted_return_300
# - confidence (optional)

print(predictions.head())
```

**Iterative Prediction Process:**
```
Step 1: Features from real data → Model → Price_1
Step 2: Features from [...real data..., Price_1] → Model → Price_2
Step 3: Features from [...real data..., Price_1, Price_2] → Model → Price_3
...
Step 300: Features from [..., Price_299] → Model → Price_300
```

**Model Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_steps_ahead` | 300 | Number of future steps to predict |
| `lookback_periods` | [5,10,20,50] | Rolling window sizes for features |
| `learning_rate` | 0.05 | LightGBM learning rate |
| `num_leaves` | 31 | Max leaves in tree |
| `max_depth` | 7 | Max tree depth |
| `feature_fraction` | 0.8 | Feature sampling ratio |
| `bagging_fraction` | 0.8 | Data sampling ratio |

#### 2. Multi-OHLC Predictor

Four separate autoregressive models, one for each OHLC component.

**Why Multi-OHLC?**
- **Realistic candlesticks**: Predicts full OHLC bars, not just close prices
- **Specialized models**: Each model optimizes for its target (Open, High, Low, Close)
- **Better accuracy**: Specialized models perform better than single multi-output model
- **Candlestick patterns**: Enables pattern recognition in predictions

**Architecture:**
```
Input Features
    ├─→ Open Model → predicted_open_1...N
    ├─→ High Model → predicted_high_1...N
    ├─→ Low Model → predicted_low_1...N
    └─→ Close Model → predicted_close_1...N
```

**Initialization:**
```python
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor

predictor = MultiOHLCPredictor(n_steps_ahead=300)
```

**Training:**
```python
# Prepare data
train_data, test_data = predictor.prepare_data(df, test_size=0.2)

# Train all 4 models
metrics = predictor.train(
    train_data,
    validation_split=0.2,
    verbose=True
)

# Metrics for each model
print("Open Model:")
print(f"  Train R²: {metrics['open']['train']['r2']:.4f}")
print(f"  Val R²: {metrics['open']['val']['r2']:.4f}")

print("High Model:")
print(f"  Train R²: {metrics['high']['train']['r2']:.4f}")
print(f"  Val R²: {metrics['high']['val']['r2']:.4f}")

print("Low Model:")
print(f"  Train R²: {metrics['low']['train']['r2']:.4f}")
print(f"  Val R²: {metrics['low']['val']['r2']:.4f}")

print("Close Model:")
print(f"  Train R²: {metrics['close']['train']['r2']:.4f}")
print(f"  Val R²: {metrics['close']['val']['r2']:.4f}")
```

**Prediction:**
```python
predictions = predictor.predict(test_data)

# Returns DataFrame with columns for each step and OHLC component:
# - predicted_open_1, predicted_open_2, ..., predicted_open_300
# - predicted_high_1, predicted_high_2, ..., predicted_high_300
# - predicted_low_1, predicted_low_2, ..., predicted_low_300
# - predicted_close_1, predicted_close_2, ..., predicted_close_300
# - predicted_return_1, ..., predicted_return_300 (based on close)
```

**Training Time Comparison:**

| Model Type | Models | Training Time (30 days, 1m) | File Size |
|------------|--------|----------------------------|-----------|
| Autoregressive | 1 | ~2-3 minutes | ~5 MB |
| Multi-OHLC | 4 | ~8-12 minutes | ~20 MB |

#### 3. Feature Engineering

Extracts 100+ features from OHLCV data for ML models.

```python
from domain.ml.features.price_features import PriceFeatureEngineer

engineer = PriceFeatureEngineer(lookback_periods=[5, 10, 20, 50])

# Engineer features
features_df = engineer.engineer_features(ohlcv_df)

# Get feature names
feature_names = engineer.get_feature_names(features_df)
print(f"Total features: {len(feature_names)}")
```

**Feature Categories:**

1. **Price Features** (20 features):
   - Returns: `return_1`, `return_2`, `return_5`, `return_10`
   - Log returns: `log_return_1`, `log_return_5`
   - Momentum: `momentum_5`, `momentum_10`, `momentum_20`
   - Acceleration: `acceleration_5`
   - Ranges: `hl_range`, `hl_range_pct`, `oc_range`, `oc_range_pct`
   - Body ratio: `body_to_range`

2. **Technical Indicators** (30 features):
   - **Trend**: EMA (10, 20, 50, 200)
   - **Momentum**: RSI (14), Stochastic (14)
   - **Volatility**: Bollinger Bands (20), ATR (14)
   - **Volume**: Volume SMA, Volume ratio

3. **Rolling Statistics** (40 features):
   - SMA: `sma_5`, `sma_10`, `sma_20`, `sma_50`
   - Volatility: `volatility_5`, `volatility_10`, `volatility_20`
   - Min/Max: `min_5`, `max_5`, `min_10`, `max_10`, etc.
   - Z-scores: Price deviations from moving averages

4. **Pattern Features** (10 features):
   - Candlestick patterns (bullish/bearish)
   - Volume patterns
   - Support/resistance levels

5. **Time Features** (5 features):
   - Hour of day
   - Day of week
   - Day of month
   - Month of year
   - Quarter

**Feature Caching:**

For backtesting performance, pre-compute features once:
```python
# Without caching: recalculate features on every bar (SLOW)
for i in range(len(data)):
    window = data.iloc[:i+1]
    features = engineer.engineer_features(window)
    # Use features...

# With caching: compute features once (FAST)
all_features = engineer.engineer_features(data)
for i in range(len(data)):
    features = all_features.iloc[:i+1]
    # Use features...
```

#### 4. Model Persistence

Save and load trained models with configuration and metrics.

**Directory Structure:**
```
models/
└── BTC_USDT_1m_300steps_multi_ohlc/
    ├── open/
    │   ├── autoregressive_model.txt  (LightGBM model)
    │   └── config.pkl                (Model config)
    ├── high/
    │   ├── autoregressive_model.txt
    │   └── config.pkl
    ├── low/
    │   ├── autoregressive_model.txt
    │   └── config.pkl
    ├── close/
    │   ├── autoregressive_model.txt
    │   └── config.pkl
    └── config.pkl  (Top-level config)
```

**Save Model:**
```python
# Save autoregressive model
predictor.save('./models/BTC_USDT_1m_300steps')

# Save multi-OHLC model
predictor.save('./models/BTC_USDT_1m_300steps_multi_ohlc')
```

**Load Model:**
```python
# Load autoregressive model
predictor = AutoregressivePricePredictor()
predictor.load('./models/BTC_USDT_1m_300steps')

# Load multi-OHLC model
predictor = MultiOHLCPredictor()
predictor.load('./models/BTC_USDT_1m_300steps_multi_ohlc')
```

**Config Structure:**
```python
# config.pkl contains:
{
    'predictor_type': 'multi_ohlc',  # or 'autoregressive'
    'n_steps_ahead': 300,
    'lookback_periods': [5, 10, 20, 50],
    'feature_names': ['return_1', 'ema_10', ...],
    'training_metrics': {
        'train_r2': 0.95,
        'val_r2': 0.87,
        'train_rmse': 42.5,
        'val_rmse': 68.3
    },
    'trained_at': '2024-01-15T10:30:00',
    'symbol': 'BTC/USDT',
    'timeframe': '1m'
}
```

#### 5. ML Service API

High-level service for training and prediction via API.

```python
from api.services.ml_service import get_ml_service

ml_service = get_ml_service()
```

**Train Model:**
```python
# Train new model
model_info = ml_service.train_model(
    symbol='BTC/USDT',
    timeframe='1m',
    n_steps_ahead=300,
    days_history=30  # Use last 30 days of data
)

if model_info:
    print(f"Model trained: {model_info['name']}")
    print(f"Size: {model_info['model_size_kb']:.2f} KB")
    print(f"Train R²: {model_info['performance']['train_r2']:.4f}")
    print(f"Val R²: {model_info['performance']['val_r2']:.4f}")
```

**List Models:**
```python
models = ml_service.list_models()

for model in models:
    print(f"{model['name']}:")
    print(f"  Symbol: {model['symbol']}")
    print(f"  Timeframe: {model['timeframe']}")
    print(f"  Steps ahead: {model['n_steps_ahead']}")
    print(f"  Trained: {model['trained_at']}")
    print(f"  Val R²: {model['performance']['val_r2']:.4f}")
```

**Generate Predictions:**
```python
predictions = ml_service.get_predictions(
    symbol='BTC/USDT',
    timeframe='1m'
)

if predictions:
    print(f"Current price: ${predictions['current_price']:,.2f}")
    print(f"Predictions: {len(predictions['predictions'])} steps")

    for i, pred in enumerate(predictions['predictions'][:5], 1):
        print(f"Step {i}:")
        print(f"  Predicted close: ${pred['predicted_close']:,.2f}")
        print(f"  Return: {pred['predicted_return']:+.2%}")
```

**Save Prediction:**
```python
prediction_id = ml_service.save_prediction_result(
    symbol='BTC/USDT',
    timeframe='1m',
    prediction_data=predictions,
    user_id='user-123'
)

print(f"Prediction saved: {prediction_id}")
```

### API Endpoints

#### GET /api/predictions

Get predictions for a symbol and timeframe. Auto-trains model if needed.

**Query Parameters:**
- `symbol` (required): Trading symbol (e.g., `BTC_USDT`)
- `timeframe` (required): Bar interval (`1m`, `5m`, `1h`)
- `auto_train` (default: `true`): Auto-train if model missing/outdated
- `force_retrain` (default: `false`): Force retraining

**Example:**
```bash
curl "http://localhost:8000/api/predictions?symbol=BTC_USDT&timeframe=1m"
```

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "current_price": 42150.5,
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "predictions": [
    {
      "step": 1,
      "minutes_ahead": 1,
      "timestamp": "2024-01-15T10:31:00Z",
      "predicted_open": 42152.0,
      "predicted_high": 42180.0,
      "predicted_low": 42140.0,
      "predicted_close": 42165.0,
      "predicted_return": 0.000345,
      "confidence": 0.8
    },
    ...
  ],
  "model_info": {
    "name": "BTC_USDT_1m_300steps_multi_ohlc",
    "type": "multi_ohlc",
    "trained_at": "2024-01-15T08:00:00Z",
    "n_steps_ahead": 300
  }
}
```

#### POST /api/predictions/generate

Generate predictions in background with task queuing.

**Request Body:**
```json
{
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "auto_train": true
}
```

**Response:**
```json
{
  "status": "running",
  "prediction_id": "abc-123-def-456",
  "message": "Prediction started. Check status at /api/predictions/abc-123-def-456"
}
```

#### GET /api/predictions/{prediction_id}

Get prediction result by ID.

**Response:**
```json
{
  "id": "abc-123-def-456",
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "result": {
    "timestamp": "2024-01-15T10:30:00Z",
    "current_price": 42150.5,
    "predictions": [...]
  }
}
```

#### GET /api/models

List all trained models.

**Response:**
```json
[
  {
    "name": "BTC_USDT_1m_300steps_multi_ohlc",
    "type": "multi_ohlc",
    "symbol": "BTC_USDT",
    "timeframe": "1m",
    "n_steps_ahead": 300,
    "model_size_kb": 20480.5,
    "trained_at": "2024-01-15T08:00:00Z",
    "performance": {
      "train_r2": 0.95,
      "val_r2": 0.87,
      "train_rmse": 42.5,
      "val_rmse": 68.3
    }
  },
  ...
]
```

#### POST /api/models/train

Train a new model.

**Request Body:**
```json
{
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "n_steps_ahead": 300,
  "days_history": 30
}
```

**Response:**
```json
{
  "name": "BTC_USDT_1m_300steps_multi_ohlc",
  "type": "multi_ohlc",
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "n_steps_ahead": 300,
  "model_size_kb": 20480.5,
  "trained_at": "2024-01-15T10:45:00Z",
  "performance": {
    "train_r2": 0.95,
    "val_r2": 0.87
  }
}
```

## Usage Examples

### Example 1: Train and Predict

```python
from api.services.ml_service import get_ml_service

ml_service = get_ml_service()

# Train model
print("Training model...")
model_info = ml_service.train_model(
    symbol='BTC/USDT',
    timeframe='1m',
    n_steps_ahead=300,
    days_history=30
)

if model_info:
    print(f"✓ Model trained: {model_info['name']}")
    print(f"  Val R²: {model_info['performance']['val_r2']:.4f}")

    # Generate predictions
    print("\nGenerating predictions...")
    predictions = ml_service.get_predictions('BTC/USDT', '1m')

    if predictions:
        print(f"✓ {len(predictions['predictions'])} predictions generated")
        print(f"  Current: ${predictions['current_price']:,.2f}")

        # Show first 5 predictions
        for pred in predictions['predictions'][:5]:
            print(f"  {pred['timestamp']}: ${pred['predicted_close']:,.2f} ({pred['predicted_return']:+.2%})")
```

### Example 2: Compare Model Types

```python
from domain.ml.predictors.autoregressive_predictor import AutoregressivePricePredictor
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor
from data.historical import HistoricalDataFetcher
import time

# Fetch data
fetcher = HistoricalDataFetcher()
df = fetcher.fetch('BTC/USDT', '1m', ...)

# Train Autoregressive Model
print("Training Autoregressive Model...")
start = time.time()
auto_predictor = AutoregressivePricePredictor(n_steps_ahead=300)
train_data, test_data = auto_predictor.prepare_data(df)
metrics_auto = auto_predictor.train(train_data)
time_auto = time.time() - start

print(f"  Time: {time_auto:.1f}s")
print(f"  Val R²: {metrics_auto['val']['r2']:.4f}")

# Train Multi-OHLC Model
print("\nTraining Multi-OHLC Model...")
start = time.time()
multi_predictor = MultiOHLCPredictor(n_steps_ahead=300)
train_data, test_data = multi_predictor.prepare_data(df)
metrics_multi = multi_predictor.train(train_data)
time_multi = time.time() - start

print(f"  Time: {time_multi:.1f}s")
print(f"  Close Val R²: {metrics_multi['close']['val']['r2']:.4f}")

# Compare
print("\n=== Comparison ===")
print(f"Training Time: {time_multi/time_auto:.1f}x longer for Multi-OHLC")
print(f"Autoregressive Val R²: {metrics_auto['val']['r2']:.4f}")
print(f"Multi-OHLC Close R²: {metrics_multi['close']['val']['r2']:.4f}")
```

### Example 3: Feature Importance Analysis

```python
import matplotlib.pyplot as plt

# Train model
predictor = AutoregressivePricePredictor(n_steps_ahead=300)
train_data, test_data = predictor.prepare_data(df)
predictor.train(train_data)

# Get feature importances
importances = predictor.model.feature_importance()
feature_names = predictor.feature_names

# Sort by importance
indices = np.argsort(importances)[-20:]  # Top 20

# Plot
plt.figure(figsize=(10, 8))
plt.barh(range(len(indices)), importances[indices])
plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
plt.xlabel('Feature Importance')
plt.title('Top 20 Most Important Features')
plt.tight_layout()
plt.savefig('feature_importance.png')

print("Feature importance saved to feature_importance.png")
```

### Example 4: Backtesting with ML Strategy

```python
from backtesting.engine import BacktestEngine
from domain.strategies.implementations.ml_predictive_strategy import MLPredictiveStrategy

# Train model first
ml_service = get_ml_service()
model_info = ml_service.train_model('BTC/USDT', '1h', 300, 30)

# Create strategy
strategy = MLPredictiveStrategy(
    model_path=f"./models/{model_info['name']}",
    min_predicted_return=0.002,
    confidence_threshold=0.7
)

# Enable feature caching for faster backtest
strategy.enable_feature_cache(df)

# Run backtest
engine = BacktestEngine(strategy=strategy, initial_cash=10000)
results = engine.run(df, symbol='BTC/USDT')

print(f"Total Return: {results['performance']['total_return']:.2%}")
print(f"Sharpe Ratio: {results['performance']['sharpe_ratio']:.2f}")
print(f"Total Trades: {results['trading']['total_trades']}")
```

## Performance Considerations

### Training Time

| Dataset | Timeframe | Bars | Autoregressive | Multi-OHLC |
|---------|-----------|------|---------------|------------|
| 7 days | 1m | 10,080 | ~1 min | ~4 min |
| 30 days | 1m | 43,200 | ~3 min | ~12 min |
| 90 days | 5m | 25,920 | ~5 min | ~20 min |
| 1 year | 1h | 8,760 | ~2 min | ~8 min |

### Inference Time

| Model Type | Steps | Time (single prediction) |
|------------|-------|--------------------------|
| Autoregressive | 300 | ~50-100ms |
| Multi-OHLC | 300 | ~200-400ms (4 models) |

### Model Size

| Model Type | File Size | Memory Usage |
|------------|-----------|--------------|
| Autoregressive | ~5 MB | ~20 MB (loaded) |
| Multi-OHLC | ~20 MB (4 models) | ~80 MB (loaded) |

### Feature Caching Benefits

| Operation | Without Cache | With Cache | Speedup |
|-----------|--------------|------------|---------|
| Backtest (300 bars) | 45s | 3s | 15x |
| Backtest (1000 bars) | 180s | 8s | 22x |
| Live prediction | 100ms | 50ms | 2x |

## Troubleshooting

### "Insufficient data for training"

**Symptoms:**
```
Insufficient data for training (got 500 rows)
```

**Minimum data requirements:**
- 1m timeframe: 1,000+ bars (recommended: 10,000+)
- 5m timeframe: 1,000+ bars
- 1h timeframe: 500+ bars

**Solution:**
```python
# Increase days_history
model_info = ml_service.train_model(
    symbol='BTC/USDT',
    timeframe='1m',
    n_steps_ahead=300,
    days_history=60  # Increase from 30 to 60
)
```

### Low Validation R²

**Symptoms:**
```
Val R²: 0.25 (expected > 0.7)
```

**Causes:**
1. Insufficient training data
2. Market regime change
3. High noise in lower timeframes

**Solutions:**
```python
# 1. More data
days_history=90  # Instead of 30

# 2. Tune hyperparameters
predictor = AutoregressivePricePredictor(
    model_params={
        'learning_rate': 0.03,  # Lower learning rate
        'num_leaves': 15,       # Simpler trees
        'max_depth': 5
    }
)

# 3. Use higher timeframe
# Use 5m or 15m instead of 1m
```

### Model Overfitting

**Symptoms:**
```
Train R²: 0.98
Val R²: 0.55
```

**Solutions:**
```python
# Regularize model
model_params = {
    'learning_rate': 0.03,      # Lower learning rate
    'num_leaves': 15,            # Fewer leaves
    'max_depth': 5,              # Shallower trees
    'min_data_in_leaf': 50,     # More data per leaf
    'feature_fraction': 0.7,    # Sample fewer features
    'bagging_fraction': 0.7,    # Sample less data
    'lambda_l1': 0.1,           # L1 regularization
    'lambda_l2': 0.1            # L2 regularization
}
```

## Related Documentation

- [ML & Predictions](02-ML-PREDICTIONS.md) - Prediction generation and API
- [Trading Strategies](06-TRADING-STRATEGIES.md) - ML Predictive Strategy
- [Backtesting System](03-BACKTESTING.md) - Testing ML strategies
- [Market Data](05-MARKET-DATA.md) - Training data source
