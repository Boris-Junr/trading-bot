"""
ML Service - Provides ML predictions and model management through the API
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import pickle
import os
import json
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.ml.predictors.autoregressive_predictor import AutoregressivePricePredictor
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor
from data.historical import HistoricalDataFetcher
from infrastructure.supabase_client import get_admin_client


class MLService:
    """Service for ML predictions and model management"""

    def __init__(self):
        """Initialize ML service"""
        self.models_dir = Path(__file__).parent.parent.parent / 'analysis' / 'models' / 'saved'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.predictions_dir = Path(__file__).parent.parent.parent / 'runtime' / 'output' / 'predictions'
        self.predictions_dir.mkdir(parents=True, exist_ok=True)
        self.fetcher = HistoricalDataFetcher(
            trading_mode='paper',
            use_cache=True,
            storage_type='parquet'
        )
        self._model_cache = {}
        self.supabase = get_admin_client()
        # Get default user ID from Supabase
        self.default_user_id = self._get_default_user_id()

    def _get_default_user_id(self) -> Optional[str]:
        """Get the default user ID from Supabase"""
        try:
            result = self.supabase.table('users').select('id').limit(1).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            return None
        except Exception as e:
            print(f"[MLService] Error getting default user ID: {e}")
            return None

    def get_predictions(
        self,
        symbol: str,
        timeframe: str,
        model_path: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get price predictions for a symbol

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            model_path: Optional model file to use

        Returns:
            Dictionary with predictions or None
        """
        try:
            # Load or find model
            model = self._load_model(symbol, timeframe, model_path)
            if model is None:
                print(f"No model found for {symbol} {timeframe}")
                return None

            # Fetch recent data for prediction (optimized for day trading)
            # Lower timeframes need MORE data to capture diverse market conditions
            timeframe_days = {
                '1m': 60,     # 2 months - all sessions, weekdays/weekends, volatility variety (~86k bars)
                '5m': 90,     # 3 months - monthly patterns, full market cycles (~26k bars)
                '15m': 120,   # 4 months - seasonal variety, different conditions (~11.5k bars)
                '1h': 180,    # 6 months - half-year patterns (~4.3k bars)
                '4h': 365,    # 1 year - for swing trading (~2.2k bars)
                '1d': 730,    # 2 years - for position trading (~730 bars)
            }
            days = timeframe_days.get(timeframe, 90)

            end = datetime.utcnow()
            start = end - pd.Timedelta(days=days)

            df = self.fetcher.update(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end
            )

            if df is None or len(df) < 100:
                print(f"Insufficient data for predictions")
                return None

            # Generate predictions
            predictions_df = model.predict(df)

            if predictions_df is None or predictions_df.empty:
                return None

            # Get current price
            current_price = float(df['close'].iloc[-1])

            # Parse predictions from wide format to list
            predictions_list = []
            n_steps = model.n_steps_ahead

            # Get last timestamp for prediction timeline
            last_timestamp = df.index[-1]

            # Check if this is a Multi-OHLC model (has predicted_open_1, etc.)
            # or a single-output model (has predicted_price_1)
            is_multi_ohlc = f'predicted_open_1' in predictions_df.columns

            if is_multi_ohlc:
                # Multi-OHLC model: Use actual OHLC predictions
                print("[MLService] Using Multi-OHLC predictions")

                for step in range(1, n_steps + 1):
                    open_col = f'predicted_open_{step}'
                    high_col = f'predicted_high_{step}'
                    low_col = f'predicted_low_{step}'
                    close_col = f'predicted_close_{step}'
                    return_col = f'predicted_return_{step}'

                    if all(col in predictions_df.columns for col in [open_col, high_col, low_col, close_col, return_col]):
                        predicted_open = float(predictions_df[open_col].iloc[0])
                        predicted_high = float(predictions_df[high_col].iloc[0])
                        predicted_low = float(predictions_df[low_col].iloc[0])
                        predicted_close = float(predictions_df[close_col].iloc[0])
                        predicted_return = float(predictions_df[return_col].iloc[0])

                        # Calculate timestamp for this prediction
                        pred_timestamp = last_timestamp + pd.Timedelta(minutes=step)

                        predictions_list.append({
                            'step': step,
                            'minutes_ahead': step,
                            'timestamp': pred_timestamp.isoformat() if hasattr(pred_timestamp, 'isoformat') else str(pred_timestamp),
                            'predicted_open': predicted_open,
                            'predicted_high': predicted_high,
                            'predicted_low': predicted_low,
                            'predicted_close': predicted_close,
                            'predicted_return': predicted_return,
                            'confidence': 0.8  # Default confidence
                        })
            else:
                # Legacy single-output model: Generate synthetic OHLC from close price
                print("[MLService] Using legacy single-output model, generating synthetic OHLC")

                # Calculate volatility from recent data for OHLC spread generation
                recent_data = df.tail(100).copy()
                avg_spread = ((recent_data['high'] - recent_data['low']) / recent_data['close']).mean()

                for step in range(1, n_steps + 1):
                    price_col = f'predicted_price_{step}'
                    return_col = f'predicted_return_{step}'

                    if price_col in predictions_df.columns and return_col in predictions_df.columns:
                        predicted_close = float(predictions_df[price_col].iloc[0])
                        predicted_return = float(predictions_df[return_col].iloc[0])

                        # Generate synthetic OHLC based on predicted close and recent volatility
                        spread_factor = avg_spread * 0.5

                        # Open: slightly different from close
                        predicted_open = predicted_close * (1 + np.random.uniform(-spread_factor/2, spread_factor/2))

                        # High/Low: based on the spread and direction
                        if predicted_return >= 0:
                            predicted_high = max(predicted_open, predicted_close) * (1 + spread_factor * 0.6)
                            predicted_low = min(predicted_open, predicted_close) * (1 - spread_factor * 0.4)
                        else:
                            predicted_high = max(predicted_open, predicted_close) * (1 + spread_factor * 0.4)
                            predicted_low = min(predicted_open, predicted_close) * (1 - spread_factor * 0.6)

                        # Calculate timestamp for this prediction
                        pred_timestamp = last_timestamp + pd.Timedelta(minutes=step)

                        predictions_list.append({
                            'step': step,
                            'minutes_ahead': step,
                            'timestamp': pred_timestamp.isoformat() if hasattr(pred_timestamp, 'isoformat') else str(pred_timestamp),
                            'predicted_open': float(predicted_open),
                            'predicted_high': float(predicted_high),
                            'predicted_low': float(predicted_low),
                            'predicted_close': float(predicted_close),
                            'predicted_return': predicted_return,
                            'confidence': 0.8
                        })

            return {
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'predictions': predictions_list,
                'smoothness_score': self._calculate_smoothness(predictions_df, is_multi_ohlc)
            }

        except Exception as e:
            print(f"Error generating predictions: {e}")
            import traceback
            traceback.print_exc()
            return None

    def train_model(
        self,
        symbol: str,
        timeframe: str,
        n_steps_ahead: int = 300,
        days_history: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Train a new prediction model

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            n_steps_ahead: Number of steps to predict ahead
            days_history: Days of historical data to use for training

        Returns:
            Model metadata or None
        """
        try:
            print(f"Training model for {symbol} {timeframe}...")

            # Adapt history for day trading (optimized balance)
            # Lower timeframes need MORE data to capture diverse market conditions
            if days_history is None:
                timeframe_days = {
                    '1m': 60,     # 2 months - all sessions, weekdays/weekends, volatility variety (~86k bars)
                    '5m': 90,     # 3 months - monthly patterns, full market cycles (~26k bars)
                    '15m': 120,   # 4 months - seasonal variety, different conditions (~11.5k bars)
                    '1h': 180,    # 6 months - half-year patterns (~4.3k bars)
                    '4h': 365,    # 1 year - for swing trading (~2.2k bars)
                    '1d': 730,    # 2 years - for position trading (~730 bars)
                }
                days_history = timeframe_days.get(timeframe, 90)
                print(f"Using {days_history} days of history for {timeframe} timeframe")

            # Fetch training data (with incremental update)
            end = datetime.utcnow()
            start = end - pd.Timedelta(days=days_history)

            df = self.fetcher.update(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end
            )

            if df is None or len(df) < 1000:
                print(f"Insufficient data for training (got {len(df) if df is not None else 0} rows)")
                return None

            # Initialize Multi-OHLC model (predicts Open, High, Low, Close)
            print("Initializing Multi-OHLC Predictor (4 models)...")
            model = MultiOHLCPredictor(
                n_steps_ahead=n_steps_ahead
            )

            # Prepare data with features and targets
            print("Preparing training data...")
            train_data, test_data = model.prepare_data(df, test_size=0.2)

            # Train model (trains all 4 OHLC predictors)
            metrics = model.train(train_data, validation_split=0.2, verbose=True)

            if metrics is None:
                print("Training failed")
                return None

            # Save model to directory
            model_dirname = f"{symbol}_{timeframe}_{n_steps_ahead}steps_multi_ohlc"
            model_path = self.models_dir / model_dirname

            model.save(str(model_path))

            # Return metadata - calculate size of all files in directory
            def get_dir_size(path):
                total = 0
                for entry in path.rglob('*'):
                    if entry.is_file():
                        total += entry.stat().st_size
                return total

            model_size_kb = get_dir_size(model_path) / 1024

            # Flatten metrics structure for API response
            return {
                'name': model_dirname,
                'type': 'multi_ohlc',
                'symbol': symbol,
                'timeframe': timeframe,
                'n_steps_ahead': n_steps_ahead,
                'model_size_kb': model_size_kb,
                'trained_at': datetime.now().isoformat(),
                'performance': {
                    'train_r2': metrics.get('train', {}).get('r2', 0.0),
                    'val_r2': metrics.get('val', {}).get('r2', 0.0),
                    'train_rmse': metrics.get('train', {}).get('rmse', 0.0),
                    'val_rmse': metrics.get('val', {}).get('rmse', 0.0)
                }
            }

        except Exception as e:
            print(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def list_models(self) -> List[Dict]:
        """
        List all available trained models

        Returns:
            List of model metadata dictionaries
        """
        models = []

        try:
            # Scan models directory for subdirectories containing config.pkl
            for model_dir in self.models_dir.iterdir():
                if not model_dir.is_dir():
                    continue

                config_file = model_dir / 'config.pkl'
                if not config_file.exists():
                    continue

                try:
                    # Parse directory name: SYMBOL_TIMEFRAME_NUMBERsteps[_TYPE]
                    # Parse from right because symbol might contain underscores (e.g., ETH_USDT)
                    name = model_dir.name
                    parts = name.split('_')

                    if len(parts) >= 3:
                        # Check if last part contains 'steps' - if yes, no TYPE suffix
                        if 'steps' in parts[-1]:
                            # Format: SYMBOL_TIMEFRAME_NUMBERsteps
                            n_steps_str = parts[-1]
                            n_steps = int(n_steps_str.replace('steps', ''))
                            timeframe = parts[-2]
                            symbol = '_'.join(parts[:-2])
                            model_type = 'autoregressive'  # Default type
                        elif len(parts) >= 4 and 'steps' in parts[-2]:
                            # Format: SYMBOL_TIMEFRAME_NUMBERsteps_TYPE
                            model_type = parts[-1]
                            n_steps_str = parts[-2]
                            n_steps = int(n_steps_str.replace('steps', ''))
                            timeframe = parts[-3]
                            symbol = '_'.join(parts[:-3])
                        else:
                            continue  # Skip if doesn't match expected format

                        # Get size of all files in directory
                        size_kb = sum(f.stat().st_size for f in model_dir.iterdir()) / 1024
                        modified_time = datetime.fromtimestamp(config_file.stat().st_mtime)

                        # Try to load metrics from config
                        try:
                            with open(config_file, 'rb') as f:
                                config = pickle.load(f)
                                metrics = config.get('training_metrics', {})
                        except:
                            metrics = {}

                        models.append({
                            'name': name,
                            'type': model_type,
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'n_steps_ahead': n_steps,
                            'model_size_kb': size_kb,
                            'trained_at': modified_time.isoformat(),
                            'performance': {
                                'train_r2': metrics.get('train_r2', 0.0),
                                'val_r2': metrics.get('val_r2', 0.0),
                                'train_rmse': metrics.get('train_rmse', 0.0),
                                'val_rmse': metrics.get('val_rmse', 0.0)
                            }
                        })
                except Exception as e:
                    print(f"Error parsing model {model_dir}: {e}")
                    continue

        except Exception as e:
            print(f"Error listing models: {e}")

        return models

    def _load_model(
        self,
        symbol: str,
        timeframe: str,
        model_path: Optional[str] = None
    ):
        """Load a model from directory or cache (supports both Multi-OHLC and legacy Autoregressive)"""
        try:
            if model_path:
                # Load specific model directory
                full_path = self.models_dir / model_path if not Path(model_path).is_absolute() else Path(model_path)
            else:
                # Find best matching model directory
                # Try multi_ohlc first, then fall back to autoregressive
                pattern_multi = f"{symbol}_{timeframe}_*steps_multi_ohlc"
                pattern_auto = f"{symbol}_{timeframe}_*steps_autoregressive"

                matches = list(self.models_dir.glob(pattern_multi))
                if not matches:
                    matches = list(self.models_dir.glob(pattern_auto))

                if not matches:
                    print(f"No model found for {symbol} {timeframe}")
                    return None

                full_path = matches[0]  # Use first match
                print(f"Found model: {full_path.name}")

            # Check cache
            cache_key = str(full_path)
            if cache_key in self._model_cache:
                return self._model_cache[cache_key]

            # Load from directory
            if not full_path.exists() or not full_path.is_dir():
                return None

            # Check if config exists
            config_file = full_path / 'config.pkl'
            if not config_file.exists():
                return None

            # Determine model type from config
            with open(config_file, 'rb') as f:
                config = pickle.load(f)

            model_type = config.get('predictor_type', 'autoregressive')  # Default to autoregressive

            # Create appropriate predictor instance and load
            if model_type == 'multi_ohlc':
                print(f"Loading Multi-OHLC model from {full_path.name}")
                model = MultiOHLCPredictor()
                model.load(str(full_path))
            else:
                print(f"Loading legacy Autoregressive model from {full_path.name}")
                model = AutoregressivePricePredictor()
                model.load(str(full_path))

            self._model_cache[cache_key] = model
            return model

        except Exception as e:
            print(f"Error loading model: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _calculate_smoothness(predictions_df: pd.DataFrame, is_multi_ohlc: bool = False) -> float:
        """Calculate smoothness score for predictions"""
        # Extract prices from wide format
        if is_multi_ohlc:
            # Use close prices from Multi-OHLC predictions
            price_cols = [col for col in predictions_df.columns if col.startswith('predicted_close_')]
        else:
            # Use predicted prices from legacy model
            price_cols = [col for col in predictions_df.columns if col.startswith('predicted_price_')]

        if len(price_cols) < 2:
            return 1.0

        # Get prices in order
        prices = []
        for i in range(1, len(price_cols) + 1):
            if is_multi_ohlc:
                col = f'predicted_close_{i}'
            else:
                col = f'predicted_price_{i}'

            if col in predictions_df.columns:
                prices.append(float(predictions_df[col].iloc[0]))

        if len(prices) < 2:
            return 1.0

        prices_array = np.array(prices)
        diffs = np.diff(prices_array)
        second_diffs = np.diff(diffs)

        if len(second_diffs) == 0:
            return 1.0

        # Lower variance in second differences = smoother
        variance = np.var(second_diffs)
        smoothness = 1.0 / (1.0 + variance)

        return min(1.0, smoothness)

    def create_prediction_task(
        self,
        symbol: str,
        timeframe: str,
        prediction_id: Optional[str] = None,
        status: str = 'running',
        user_id: Optional[str] = None
    ) -> str:
        """
        Create a prediction task entry in Supabase (for tracking before completion)

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            prediction_id: Optional prediction ID (generates new one if not provided)
            status: Task status (running, queued, etc.)
            user_id: User ID (uses default if not provided)

        Returns:
            Prediction ID
        """
        if prediction_id is None:
            prediction_id = str(uuid.uuid4())

        uid = user_id or self.default_user_id
        if not uid:
            raise ValueError("No user ID available for creating prediction task")

        save_data = {
            'id': prediction_id,
            'user_id': uid,
            'symbol': symbol,
            'timeframe': timeframe,
            'status': status,
            'result': None
        }

        try:
            # Save to Supabase
            response = self.supabase.table('predictions').insert(save_data).execute()
            if response.data and len(response.data) > 0:
                print(f"[MLService] Prediction task created in Supabase: {prediction_id}")
                return prediction_id
            else:
                raise Exception("Failed to create prediction task in Supabase")
        except Exception as e:
            print(f"[MLService] Error creating prediction task: {e}")
            raise

    def save_prediction_result(
        self,
        symbol: str,
        timeframe: str,
        prediction_data: Dict,
        prediction_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Save prediction results to Supabase

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            prediction_data: Prediction data dictionary
            prediction_id: Optional prediction ID (generates new one if not provided)
            user_id: User ID (uses default if not provided)

        Returns:
            Prediction ID
        """
        if prediction_id is None:
            prediction_id = str(uuid.uuid4())

        uid = user_id or self.default_user_id
        if not uid:
            raise ValueError("No user ID available for saving prediction result")

        # Prepare update data
        update_data = {
            'status': 'completed',
            'result': prediction_data,
            'completed_at': datetime.now().isoformat()
        }

        try:
            # Update existing prediction record in Supabase
            response = self.supabase.table('predictions').update(update_data).eq('id', prediction_id).execute()

            if response.data and len(response.data) > 0:
                print(f"[MLService] Prediction result saved to Supabase: {prediction_id}")
                return prediction_id
            else:
                # If update failed, try insert (in case task wasn't created first)
                save_data = {
                    'id': prediction_id,
                    'user_id': uid,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'status': 'completed',
                    'result': prediction_data,
                    'completed_at': datetime.now().isoformat()
                }
                response = self.supabase.table('predictions').insert(save_data).execute()
                if response.data and len(response.data) > 0:
                    print(f"[MLService] Prediction result inserted to Supabase: {prediction_id}")
                    return prediction_id
                else:
                    raise Exception("Failed to save prediction result to Supabase")
        except Exception as e:
            print(f"[MLService] Error saving prediction result: {e}")
            import traceback
            traceback.print_exc()
            raise

    def get_prediction_result(self, prediction_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get a specific prediction result from Supabase

        Args:
            prediction_id: Prediction result ID
            user_id: User ID to verify ownership (optional)

        Returns:
            Prediction data or None if not found or doesn't belong to user
        """
        try:
            # Query from Supabase with optional user filter
            query = self.supabase.table('predictions').select('*').eq('id', prediction_id)

            if user_id:
                query = query.eq('user_id', user_id)

            response = query.execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None

        except Exception as e:
            print(f"[MLService] Error loading prediction {prediction_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def list_predictions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        List all saved prediction results from Supabase

        Args:
            user_id: User ID to filter by (uses default if not provided)

        Returns:
            List of prediction summaries
        """
        results = []

        try:
            uid = user_id or self.default_user_id
            if not uid:
                print("[MLService] No user ID available for listing predictions")
                return []

            # Query from Supabase - exclude result column to avoid fetching massive predictions array
            # The result column contains 300 steps of OHLC predictions which can be 100KB+ per row
            # For list view, we only need metadata - full details are fetched when viewing individual prediction
            response = self.supabase.table('predictions').select(
                'id, symbol, timeframe, created_at, status'
            ).eq('user_id', uid).order('created_at', desc=True).execute()

            if response.data:
                for prediction in response.data:
                    # Return summary data without predictions array
                    summary = {
                        'id': prediction['id'],
                        'symbol': prediction['symbol'],
                        'timeframe': prediction['timeframe'],
                        'created_at': prediction['created_at'],
                        'status': prediction.get('status', 'completed'),
                        'current_price': None  # Not fetched in list view for performance
                    }
                    results.append(summary)

        except Exception as e:
            print(f"[MLService] Error listing predictions from Supabase: {e}")
            import traceback
            traceback.print_exc()

        return results


# Singleton instance
_ml_service = None


def get_ml_service() -> MLService:
    """Get or create ML service singleton"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
    return _ml_service
