"""
Autoregressive Gradient Boosting Price Predictor

Uses ONE LightGBM model to predict future prices autoregressively.
The model predicts the next step, then feeds that prediction back to predict the next, etc.
This creates smooth, coherent price curves without needing 300 separate models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import os
from datetime import datetime

from analysis.models.features.price_features import PriceFeatureEngineer


class AutoregressivePricePredictor:
    """
    Single-model autoregressive price prediction using Gradient Boosting.

    Instead of training N models for N steps, we train ONE model that predicts
    the next price given current features. To predict multiple steps ahead,
    we iteratively:
    1. Predict next price
    2. Update the data with predicted price
    3. Recalculate features
    4. Predict next price again
    5. Repeat for N steps

    This creates smooth, coherent price curves.
    """

    def __init__(
        self,
        n_steps_ahead: int = 300,
        lookback_periods: List[int] = [5, 10, 20, 50],
        model_params: Optional[Dict] = None
    ):
        """
        Initialize autoregressive predictor.

        Args:
            n_steps_ahead: Number of future steps to predict
            lookback_periods: Periods for rolling features
            model_params: LightGBM parameters (uses defaults if None)
        """
        self.n_steps_ahead = n_steps_ahead
        self.lookback_periods = lookback_periods

        # Feature engineer
        self.feature_engineer = PriceFeatureEngineer(lookback_periods=lookback_periods)

        # Single model
        self.model: Optional[lgb.Booster] = None

        # Feature names
        self.feature_names: Optional[List[str]] = None

        # Training metrics
        self.training_metrics: Dict = {}

        # Default LightGBM parameters
        self.model_params = model_params or {
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

    def prepare_data(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare training data with features and next-step targets.

        Args:
            df: DataFrame with OHLCV data
            test_size: Fraction of data for testing

        Returns:
            Tuple of (train_df, test_df) with features and targets
        """
        # Engineer features
        print("Engineering features...")
        data = self.feature_engineer.engineer_features(df)

        # Create target variable (next close price)
        print("Creating target variable (next close price)...")
        data['target_price_next'] = data['close'].shift(-1)

        # Also create target return for evaluation
        data['target_return_next'] = (
            (data['target_price_next'] - data['close']) / data['close']
        )

        # Drop rows with NaN
        initial_rows = len(data)
        data = data.dropna()
        print(f"Dropped {initial_rows - len(data)} rows with NaN values")

        # Split by time
        split_idx = int(len(data) * (1 - test_size))
        train_data = data.iloc[:split_idx].copy()
        test_data = data.iloc[split_idx:].copy()

        print(f"Train set: {len(train_data)} samples")
        print(f"Test set: {len(test_data)} samples")

        return train_data, test_data

    def train(
        self,
        train_df: pd.DataFrame,
        validation_split: float = 0.2,
        num_boost_round: int = 500,
        early_stopping_rounds: int = 50,
        verbose: bool = True
    ) -> Dict:
        """
        Train the autoregressive model.

        Args:
            train_df: Training data with features and targets
            validation_split: Fraction of training data for validation
            num_boost_round: Maximum number of boosting rounds
            early_stopping_rounds: Stop if no improvement for N rounds
            verbose: Print training progress

        Returns:
            Dictionary of training metrics
        """
        # Get feature columns
        self.feature_names = self.feature_engineer.get_feature_names(train_df)

        if verbose:
            print(f"\nTraining autoregressive model with {len(self.feature_names)} features")
            print(f"Features: {', '.join(self.feature_names[:10])}...")

        # Split training data for validation
        split_idx = int(len(train_df) * (1 - validation_split))
        train_set = train_df.iloc[:split_idx]
        val_set = train_df.iloc[split_idx:]

        # Prepare datasets
        X_train = train_set[self.feature_names]
        y_train = train_set['target_price_next']
        X_val = val_set[self.feature_names]
        y_val = val_set['target_price_next']

        # Create LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        # Train model
        callbacks = [lgb.log_evaluation(period=50)] if verbose else []
        if early_stopping_rounds:
            callbacks.append(lgb.early_stopping(stopping_rounds=early_stopping_rounds))

        print("\nTraining single autoregressive model...")
        self.model = lgb.train(
            self.model_params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'val'],
            callbacks=callbacks
        )

        # Calculate metrics
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_metrics = self._calculate_metrics(y_train, train_pred)
        val_metrics = self._calculate_metrics(y_val, val_pred)

        self.training_metrics = {
            'train': train_metrics,
            'val': val_metrics,
            'best_iteration': self.model.best_iteration,
            'num_trees': self.model.num_trees()
        }

        if verbose:
            print(f"\nTraining Results:")
            print(f"  Train RMSE: {train_metrics['rmse']:.4f}")
            print(f"  Val RMSE: {val_metrics['rmse']:.4f}")
            print(f"  Train MAE: {train_metrics['mae']:.4f}")
            print(f"  Val MAE: {val_metrics['mae']:.4f}")
            print(f"  Train R²: {train_metrics['r2']:.4f}")
            print(f"  Val R²: {val_metrics['r2']:.4f}")
            print(f"  Best iteration: {self.model.best_iteration}")

        return self.training_metrics

    def predict(self, df: pd.DataFrame, n_steps: Optional[int] = None) -> pd.DataFrame:
        """
        Predict future prices autoregressively.

        Args:
            df: DataFrame with OHLCV data (must have sufficient history for features)
            n_steps: Number of steps to predict (defaults to self.n_steps_ahead)

        Returns:
            DataFrame with predictions for each step
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        n_steps = n_steps or self.n_steps_ahead

        # Start with the full historical data
        working_df = df.copy()

        # Store predictions
        predicted_prices = []
        predicted_returns = []

        current_price = df['close'].iloc[-1]

        # Predict step by step
        for step in range(1, n_steps + 1):
            # Engineer features from current state
            features_df = self.feature_engineer.engineer_features(working_df)

            # Get features for last row (current state)
            current_features = features_df[self.feature_names].iloc[[-1]]

            # Predict next price
            next_price = self.model.predict(current_features)[0]

            # Calculate return
            next_return = (next_price - current_price) / current_price

            # Store predictions
            predicted_prices.append(next_price)
            predicted_returns.append(next_return)

            # Create new row with predicted values
            # Use the predicted close as OHLCV for next step
            last_timestamp = working_df.index[-1]
            new_row = pd.DataFrame({
                'open': [next_price],
                'high': [next_price * 1.001],  # Small spread
                'low': [next_price * 0.999],
                'close': [next_price],
                'volume': [working_df['volume'].iloc[-1]]  # Use last volume
            }, index=[last_timestamp + pd.Timedelta(minutes=1)])

            # Append to working dataframe
            working_df = pd.concat([working_df, new_row])

            # Keep only recent history to prevent memory issues
            if len(working_df) > 1000:
                working_df = working_df.iloc[-1000:]

        # Create predictions dataframe
        predictions = {}
        for step in range(1, n_steps + 1):
            predictions[f'predicted_price_{step}'] = predicted_prices[step - 1]
            predictions[f'predicted_return_{step}'] = predicted_returns[step - 1]

        return pd.DataFrame([predictions])

    def evaluate(self, test_df: pd.DataFrame, eval_steps: List[int] = None, verbose: bool = True) -> Dict[int, Dict]:
        """
        Evaluate model on test set using multi-step autoregressive predictions.

        Args:
            test_df: Test data with actual prices
            eval_steps: Steps to evaluate (e.g., [1, 5, 15, 30, 60, 120, 180, 240, 300])
            verbose: Print evaluation results

        Returns:
            Dictionary of evaluation metrics per step
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Default evaluation steps
        if eval_steps is None:
            if self.n_steps_ahead >= 300:
                eval_steps = [1, 15, 30, 60, 120, 180, 240, 300]
            elif self.n_steps_ahead >= 60:
                eval_steps = [1, 5, 10, 15, 30, 60]
            else:
                eval_steps = [1, 5, 10, 15, 20]
        eval_steps = [s for s in eval_steps if s <= self.n_steps_ahead]

        print(f"\nEvaluating autoregressive predictions at steps: {eval_steps}")

        results = {}

        # We'll evaluate on multiple starting points from the test set
        # to get robust metrics
        num_eval_points = min(100, len(test_df) - self.n_steps_ahead - 100)

        if num_eval_points < 1:
            print("Warning: Test set too small for multi-step evaluation")
            return results

        # Collect predictions and actuals for each step
        step_predictions = {step: [] for step in eval_steps}
        step_actuals = {step: [] for step in eval_steps}

        print(f"Generating predictions from {num_eval_points} test points...")

        for i in range(0, num_eval_points, max(1, num_eval_points // 20)):  # 20 evaluation points
            # Get history up to this point
            history_end = 100 + i
            history = test_df.iloc[:history_end]

            # Get actual future prices
            future_actuals = test_df.iloc[history_end:history_end + max(eval_steps)]['close'].values

            if len(future_actuals) < max(eval_steps):
                continue

            # Generate predictions
            predictions = self.predict(history, n_steps=max(eval_steps))

            # Store for each evaluation step
            for step in eval_steps:
                pred_price = predictions[f'predicted_price_{step}'].iloc[0]
                actual_price = future_actuals[step - 1]

                step_predictions[step].append(pred_price)
                step_actuals[step].append(actual_price)

        # Calculate metrics for each step
        for step in eval_steps:
            if len(step_predictions[step]) > 0:
                y_true = np.array(step_actuals[step])
                y_pred = np.array(step_predictions[step])

                metrics = self._calculate_metrics(y_true, y_pred)
                results[step] = metrics

                if verbose:
                    print(f"\nStep {step} Test Results:")
                    print(f"  RMSE: {metrics['rmse']:.4f}")
                    print(f"  MAE: {metrics['mae']:.4f}")
                    print(f"  R²: {metrics['r2']:.4f}")
                    print(f"  MAPE: {metrics['mape']:.2f}%")

        return results

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance.

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importance
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=False).head(top_n)

        return importance

    def save(self, path: str):
        """
        Save trained model and configuration.

        Args:
            path: Directory path to save model
        """
        os.makedirs(path, exist_ok=True)

        # Save model
        model_path = os.path.join(path, 'autoregressive_model.txt')
        self.model.save_model(model_path)

        # Save configuration
        config = {
            'n_steps_ahead': self.n_steps_ahead,
            'lookback_periods': self.lookback_periods,
            'model_params': self.model_params,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics
        }
        config_path = os.path.join(path, 'config.pkl')
        with open(config_path, 'wb') as f:
            pickle.dump(config, f)

        print(f"Autoregressive model saved to {path}")

    def load(self, path: str):
        """
        Load trained model and configuration.

        Args:
            path: Directory path containing saved model
        """
        # Load configuration
        config_path = os.path.join(path, 'config.pkl')
        with open(config_path, 'rb') as f:
            config = pickle.load(f)

        self.n_steps_ahead = config['n_steps_ahead']
        self.lookback_periods = config['lookback_periods']
        self.model_params = config['model_params']
        self.feature_names = config['feature_names']
        self.training_metrics = config['training_metrics']

        # Recreate feature engineer
        self.feature_engineer = PriceFeatureEngineer(lookback_periods=self.lookback_periods)

        # Load model
        model_path = os.path.join(path, 'autoregressive_model.txt')
        self.model = lgb.Booster(model_file=model_path)

        print(f"Autoregressive model loaded from {path}")

    def _calculate_metrics(self, y_true, y_pred) -> Dict:
        """Calculate regression metrics."""
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape
        }
