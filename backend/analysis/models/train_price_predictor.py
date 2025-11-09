"""
Train Autoregressive Price Predictor

Script to train a single autoregressive gradient boosting model for multi-step price prediction.
Much more efficient than training 300 separate models.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from analysis.models.predictors.autoregressive_predictor import AutoregressivePricePredictor
from data.fetchers.crypto_fetcher import CryptoFetcher


def train_autoregressive_predictor(
    symbol: str = 'ETH/USDT',
    timeframe: str = '1m',
    n_steps_ahead: int = 300,
    days_history: int = 30,
    test_size: float = 0.2
):
    """
    Train autoregressive price prediction model.

    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe (1m, 5m, 15m, etc.)
        n_steps_ahead: Number of future steps to predict
        days_history: Number of days of historical data
        test_size: Fraction of data for testing
    """
    print("="*70)
    print("AUTOREGRESSIVE PRICE PREDICTION MODEL TRAINING")
    print("="*70)
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Predicting: {n_steps_ahead} steps ahead (autoregressive)")
    print(f"History: {days_history} days")
    print("="*70)

    # Fetch data
    print("\n1. Fetching historical data...")
    fetcher = CryptoFetcher()
    end = datetime.now()
    start = end - timedelta(days=days_history)

    df = fetcher.fetch(symbol, timeframe, start, end, limit=None)
    print(f"Fetched {len(df)} bars from {df.index[0]} to {df.index[-1]}")

    # Initialize predictor
    print("\n2. Initializing autoregressive predictor...")

    # Use standard parameters for autoregressive model
    model_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'min_data_in_leaf': 20,
        'max_depth': 7,
    }

    predictor = AutoregressivePricePredictor(
        n_steps_ahead=n_steps_ahead,
        lookback_periods=[5, 10, 20, 50],
        model_params=model_params
    )

    # Prepare data
    print("\n3. Preparing data...")
    train_df, test_df = predictor.prepare_data(df, test_size=test_size)

    # Train model
    print(f"\n4. Training single autoregressive model...")
    print(f"This will predict step-by-step up to {n_steps_ahead} steps ahead.")

    training_metrics = predictor.train(
        train_df,
        validation_split=0.2,
        num_boost_round=500,
        early_stopping_rounds=50,
        verbose=True
    )

    # Evaluate on test set
    print("\n5. Evaluating on test set...")
    print("="*70)

    # Evaluate at key intervals
    if n_steps_ahead >= 300:
        eval_steps = [1, 15, 30, 60, 120, 180, 240, 300]
    elif n_steps_ahead >= 60:
        eval_steps = [1, 5, 10, 15, 30, 60]
    else:
        eval_steps = [1, 5, 10, 15, 20]

    test_metrics = predictor.evaluate(test_df, eval_steps=eval_steps, verbose=True)

    # Feature importance
    print("\n6. Feature importance:")
    print("="*70)
    importance = predictor.get_feature_importance(top_n=15)
    print(importance.to_string(index=False))

    # Save model
    model_name = f"{symbol.replace('/', '_')}_{timeframe}_{n_steps_ahead}steps_autoregressive"
    save_path = f"analysis/models/saved/{model_name}"
    print(f"\n7. Saving model to {save_path}...")
    predictor.save(save_path)

    # Test prediction on last data point
    print("\n8. Testing autoregressive prediction on latest data:")
    print("="*70)
    predictions = predictor.predict(test_df.tail(100))

    current_price = test_df['close'].iloc[-1]
    print(f"Current price: ${current_price:.2f}")
    print("\nPredicted prices (showing key milestones):")

    # Show predictions at key intervals
    display_steps = [1, 15, 30, 60, 120, 180, 240, 300] if n_steps_ahead >= 300 else [1, 5, 10, 15, 30, 60] if n_steps_ahead >= 60 else list(range(1, min(n_steps_ahead + 1, 21)))
    display_steps = [i for i in display_steps if i <= n_steps_ahead]

    for step in display_steps:
        pred_price = predictions[f'predicted_price_{step}'].iloc[0]
        pred_return = predictions[f'predicted_return_{step}'].iloc[0]
        print(f"  +{step}min: ${pred_price:.2f} ({pred_return:+.2%})")

    # Visualize curve smoothness
    print("\n9. Analyzing prediction curve smoothness:")
    print("="*70)
    all_prices = [predictions[f'predicted_price_{i}'].iloc[0] for i in range(1, min(n_steps_ahead + 1, 61))]
    price_changes = [all_prices[i] - all_prices[i-1] for i in range(1, len(all_prices))]
    avg_change = np.mean(np.abs(price_changes))
    std_change = np.std(price_changes)
    max_jump = max([abs(c) for c in price_changes])

    print(f"First 60 predictions analysis:")
    print(f"  Average step change: ${avg_change:.2f}")
    print(f"  Std of step changes: ${std_change:.2f}")
    print(f"  Max single step jump: ${max_jump:.2f}")
    print(f"  Smoothness score: {std_change/avg_change:.2f} (lower is smoother)")

    # Summary
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Model saved to: {save_path}")
    print(f"\nModel Architecture:")
    print(f"  Type: Autoregressive (single model)")
    print(f"  Prediction method: Iterative step-by-step")
    print(f"  Max horizon: {n_steps_ahead} steps")
    print(f"  Model size: ~{os.path.getsize(os.path.join(save_path, 'autoregressive_model.txt')) / 1024:.0f} KB")

    print(f"\nTest Set Performance (at key intervals):")
    for step in eval_steps:
        if step in test_metrics:
            m = test_metrics[step]
            print(f"  +{step}min: RMSE={m['rmse']:.2f}, MAE={m['mae']:.2f}, R²={m['r2']:.3f}, MAPE={m['mape']:.2f}%")

    print("\nAdvantages of Autoregressive Approach:")
    print("  + ONE model instead of 300 separate models")
    print("  + Predictions form smooth, coherent curves")
    print("  + Faster training (~2-3 minutes)")
    print("  + Much smaller model size (~40KB vs ~13MB)")
    print("  + Natural sequential dependency learning")

    print("\nNote:")
    print("  - Prediction errors compound over time")
    print("  - Most accurate for short-term (1-60 min)")
    print("  - Longer horizons (180-300 min) are trend indicators")
    print("="*70)

    return predictor, test_metrics


if __name__ == '__main__':
    # Train autoregressive model on 1m timeframe
    predictor, metrics = train_autoregressive_predictor(
        symbol='ETH/USDT',
        timeframe='1m',
        n_steps_ahead=300,  # 5 hours ahead for 1m timeframe
        days_history=30,
        test_size=0.2
    )
