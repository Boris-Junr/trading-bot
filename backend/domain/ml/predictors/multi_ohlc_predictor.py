"""
Multi-OHLC Predictor

Predicts all 4 components of candlesticks: Open, High, Low, Close.
Uses 4 separate autoregressive models for each component.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
import pickle
from pathlib import Path

from .autoregressive_predictor import AutoregressivePricePredictor


class MultiOHLCPredictor:
    """
    Multi-output predictor for OHLC candlestick predictions.

    Trains 4 separate autoregressive models:
    - Open predictor
    - High predictor
    - Low predictor
    - Close predictor

    This allows each model to specialize in its target while maintaining
    the smooth autoregressive prediction curves.
    """

    def __init__(self, n_steps_ahead: int = 100):
        """
        Initialize Multi-OHLC Predictor.

        Args:
            n_steps_ahead: Number of future steps to predict
        """
        self.n_steps_ahead = n_steps_ahead

        # Create 4 separate predictors
        self.open_predictor = AutoregressivePricePredictor(n_steps_ahead=n_steps_ahead)
        self.high_predictor = AutoregressivePricePredictor(n_steps_ahead=n_steps_ahead)
        self.low_predictor = AutoregressivePricePredictor(n_steps_ahead=n_steps_ahead)
        self.close_predictor = AutoregressivePricePredictor(n_steps_ahead=n_steps_ahead)

        self.is_trained = False

    def prepare_data(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare data for training.

        Uses the same feature engineering as AutoregressivePredictor but creates
        4 different target columns (open_next, high_next, low_next, close_next).

        Args:
            df: DataFrame with OHLCV data
            test_size: Fraction of data to use for testing

        Returns:
            Tuple of (train_data, test_data)
        """
        # Use the close predictor to prepare base features
        # (all predictors use same features, just different targets)
        train_data, test_data = self.close_predictor.prepare_data(df, test_size)

        return train_data, test_data

    def train(
        self,
        train_data: pd.DataFrame,
        validation_split: float = 0.2,
        verbose: bool = False
    ) -> Optional[Dict]:
        """
        Train all 4 OHLC predictors.

        Args:
            train_data: Prepared training data
            validation_split: Fraction of training data to use for validation
            verbose: Whether to print training progress

        Returns:
            Dictionary with combined metrics for all 4 models
        """
        print("\n=== Training Multi-OHLC Predictor ===")
        print(f"Training 4 separate models for {self.n_steps_ahead} steps ahead")

        all_metrics = {}

        # Prepare training data with all 4 targets
        data = train_data.copy()

        # Create target columns for each OHLC component
        # These are shifted versions of the current OHLC
        data['target_open_next'] = data['open'].shift(-1)
        data['target_high_next'] = data['high'].shift(-1)
        data['target_low_next'] = data['low'].shift(-1)
        data['target_close_next'] = data['close'].shift(-1)

        # Drop rows with NaN targets
        data = data.dropna()

        # Train Open predictor
        print("\n[1/4] Training OPEN predictor...")
        # Temporarily swap target column
        data_open = data.copy()
        if 'target_price_next' in data_open.columns:
            data_open = data_open.drop(columns=['target_price_next'])
        data_open['target_price_next'] = data_open['target_open_next']

        metrics_open = self.open_predictor.train(data_open, validation_split=validation_split, verbose=verbose)
        if metrics_open:
            all_metrics['open'] = metrics_open
            if verbose:
                print(f"Open - Train R²: {metrics_open['train']['r2']:.4f}, Val R²: {metrics_open['val']['r2']:.4f}")

        # Train High predictor
        print("\n[2/4] Training HIGH predictor...")
        data_high = data.copy()
        if 'target_price_next' in data_high.columns:
            data_high = data_high.drop(columns=['target_price_next'])
        data_high['target_price_next'] = data_high['target_high_next']

        metrics_high = self.high_predictor.train(data_high, validation_split=validation_split, verbose=verbose)
        if metrics_high:
            all_metrics['high'] = metrics_high
            if verbose:
                print(f"High - Train R²: {metrics_high['train']['r2']:.4f}, Val R²: {metrics_high['val']['r2']:.4f}")

        # Train Low predictor
        print("\n[3/4] Training LOW predictor...")
        data_low = data.copy()
        if 'target_price_next' in data_low.columns:
            data_low = data_low.drop(columns=['target_price_next'])
        data_low['target_price_next'] = data_low['target_low_next']

        metrics_low = self.low_predictor.train(data_low, validation_split=validation_split, verbose=verbose)
        if metrics_low:
            all_metrics['low'] = metrics_low
            if verbose:
                print(f"Low - Train R²: {metrics_low['train']['r2']:.4f}, Val R²: {metrics_low['val']['r2']:.4f}")

        # Train Close predictor
        print("\n[4/4] Training CLOSE predictor...")
        data_close = data.copy()
        if 'target_price_next' in data_close.columns:
            data_close = data_close.drop(columns=['target_price_next'])
        data_close['target_price_next'] = data_close['target_close_next']

        metrics_close = self.close_predictor.train(data_close, validation_split=validation_split, verbose=verbose)
        if metrics_close:
            all_metrics['close'] = metrics_close
            if verbose:
                print(f"Close - Train R²: {metrics_close['train']['r2']:.4f}, Val R²: {metrics_close['val']['r2']:.4f}")

        if len(all_metrics) == 4:
            self.is_trained = True
            print("\n=== Training Complete ===")

            # Calculate average metrics across all 4 models
            avg_metrics = {
                'train': {
                    'r2': np.mean([all_metrics[k]['train']['r2'] for k in ['open', 'high', 'low', 'close']]),
                    'rmse': np.mean([all_metrics[k]['train']['rmse'] for k in ['open', 'high', 'low', 'close']])
                },
                'val': {
                    'r2': np.mean([all_metrics[k]['val']['r2'] for k in ['open', 'high', 'low', 'close']]),
                    'rmse': np.mean([all_metrics[k]['val']['rmse'] for k in ['open', 'high', 'low', 'close']])
                },
                'individual': all_metrics
            }

            print(f"\nAverage across all 4 models:")
            print(f"  Train R²: {avg_metrics['train']['r2']:.4f}, RMSE: {avg_metrics['train']['rmse']:.4f}")
            print(f"  Val R²: {avg_metrics['val']['r2']:.4f}, RMSE: {avg_metrics['val']['rmse']:.4f}")

            return avg_metrics
        else:
            print("ERROR: Some models failed to train")
            return None

    def predict(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate OHLC predictions.

        Args:
            df: DataFrame with recent OHLC data (needs at least 100 rows for features)

        Returns:
            DataFrame with predictions for all 4 OHLC components:
            - predicted_open_1, predicted_open_2, ...
            - predicted_high_1, predicted_high_2, ...
            - predicted_low_1, predicted_low_2, ...
            - predicted_close_1, predicted_close_2, ...
        """
        if not self.is_trained:
            print("ERROR: Models not trained yet")
            return None

        if len(df) < 100:
            print("ERROR: Need at least 100 bars for predictions")
            return None

        # Get predictions from all 4 models
        pred_open = self.open_predictor.predict(df)
        pred_high = self.high_predictor.predict(df)
        pred_low = self.low_predictor.predict(df)
        pred_close = self.close_predictor.predict(df)

        if any(p is None or p.empty for p in [pred_open, pred_high, pred_low, pred_close]):
            print("ERROR: Some predictions failed")
            return None

        # Combine predictions into single DataFrame
        # Build all columns at once to avoid DataFrame fragmentation
        all_columns = {}

        for step in range(1, self.n_steps_ahead + 1):
            # Extract predictions for this step from each model
            all_columns[f'predicted_open_{step}'] = pred_open[f'predicted_price_{step}']
            all_columns[f'predicted_high_{step}'] = pred_high[f'predicted_price_{step}']
            all_columns[f'predicted_low_{step}'] = pred_low[f'predicted_price_{step}']
            all_columns[f'predicted_close_{step}'] = pred_close[f'predicted_price_{step}']
            all_columns[f'predicted_return_{step}'] = pred_close[f'predicted_return_{step}']

        # Create DataFrame from all columns at once (avoids fragmentation)
        result = pd.DataFrame(all_columns)

        # Post-process: Ensure High >= max(Open, Close) and Low <= min(Open, Close)
        for step in range(1, self.n_steps_ahead + 1):
            open_col = f'predicted_open_{step}'
            high_col = f'predicted_high_{step}'
            low_col = f'predicted_low_{step}'
            close_col = f'predicted_close_{step}'

            # Ensure High is highest
            result[high_col] = result[[open_col, high_col, close_col]].max(axis=1)

            # Ensure Low is lowest
            result[low_col] = result[[open_col, low_col, close_col]].min(axis=1)

        return result

    def save(self, directory: str):
        """
        Save all 4 models to a directory.

        Args:
            directory: Directory path to save models
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Save each predictor to a subdirectory
        self.open_predictor.save(str(dir_path / 'open'))
        self.high_predictor.save(str(dir_path / 'high'))
        self.low_predictor.save(str(dir_path / 'low'))
        self.close_predictor.save(str(dir_path / 'close'))

        # Save config
        config = {
            'n_steps_ahead': self.n_steps_ahead,
            'is_trained': self.is_trained,
            'predictor_type': 'multi_ohlc'
        }

        with open(dir_path / 'config.pkl', 'wb') as f:
            pickle.dump(config, f)

        print(f"Saved Multi-OHLC Predictor to {directory}")

    def load(self, directory: str):
        """
        Load all 4 models from a directory.

        Args:
            directory: Directory path containing saved models
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Load config
        config_file = dir_path / 'config.pkl'
        if config_file.exists():
            with open(config_file, 'rb') as f:
                config = pickle.load(f)
            self.n_steps_ahead = config['n_steps_ahead']
            self.is_trained = config.get('is_trained', False)

        # Load each predictor
        self.open_predictor.load(str(dir_path / 'open'))
        self.high_predictor.load(str(dir_path / 'high'))
        self.low_predictor.load(str(dir_path / 'low'))
        self.close_predictor.load(str(dir_path / 'close'))

        print(f"Loaded Multi-OHLC Predictor from {directory}")
