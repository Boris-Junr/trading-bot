"""
Backtest Service - Provides backtesting capabilities through the API
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtesting.engine import BacktestEngine
from domain.strategies.registry import get_strategy_registry
from data.historical import HistoricalDataFetcher
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor
import math


def sanitize_metric(value: float) -> float:
    """Sanitize numeric values for JSON serialization (replace inf/nan with 0.0)"""
    if value is None or math.isnan(value) or math.isinf(value):
        return 0.0
    return value


def sanitize_dict(data: dict) -> dict:
    """Recursively sanitize all numeric values in a dictionary for JSON serialization"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, (list, tuple)):
            sanitized[key] = [sanitize_dict(item) if isinstance(item, dict) else
                             (sanitize_metric(item) if isinstance(item, (int, float)) else item)
                             for item in value]
        elif isinstance(value, (int, float)):
            sanitized[key] = sanitize_metric(value)
        else:
            sanitized[key] = value
    return sanitized


class BacktestService:
    """Service for running and managing backtests"""

    def __init__(self):
        """Initialize backtest service"""
        self.results_dir = Path(__file__).parent.parent.parent / 'output' / 'backtests'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.fetcher = HistoricalDataFetcher(
            trading_mode='paper',
            use_cache=True,
            storage_type='parquet'
        )

    def run_backtest(
        self,
        strategy: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_cash: float = 10000.0,
        **strategy_params
    ) -> Optional[Dict]:
        """
        Run a backtest

        Args:
            strategy: Strategy name (e.g., 'MLPredictive', 'RSI')
            symbol: Trading symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            initial_cash: Initial portfolio cash
            **strategy_params: Strategy-specific parameters

        Returns:
            Backtest results dictionary or None
        """
        try:
            print(f"\n{'='*80}")
            print(f"[BACKTEST] Starting backtest")
            print(f"[BACKTEST] Strategy: {strategy}")
            print(f"[BACKTEST] Symbol: {symbol}")
            print(f"[BACKTEST] Period: {start_date} to {end_date}")
            print(f"[BACKTEST] Initial cash: ${initial_cash:,.2f}")
            print(f"[BACKTEST] Parameters: {strategy_params}")
            print(f"{'='*80}\n")

            # Fetch historical data
            print(f"[BACKTEST] Step 1/4: Fetching historical data...")
            start_dt = pd.to_datetime(start_date).to_pydatetime()
            end_dt = pd.to_datetime(end_date).to_pydatetime()

            # If end date is same as start date, set to end of that day
            if start_dt.date() == end_dt.date() and end_dt.hour == 0 and end_dt.minute == 0:
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                print(f"[BACKTEST] Adjusted end date to end of day: {end_dt}")

            print(f"[BACKTEST] Timeframe: {strategy_params.get('timeframe', '1m')}")

            df = self.fetcher.fetch(
                symbol=symbol,
                start=start_dt,
                end=end_dt,
                timeframe=strategy_params.get('timeframe', '1m'),
                force_refresh=True
            )

            if df is None:
                print(f"[BACKTEST] ERROR: Failed to fetch data for {symbol}")
                return None

            if len(df) < 100:
                print(f"[BACKTEST] ERROR: Insufficient data - got {len(df)} rows, need at least 100")
                return None

            print(f"[BACKTEST] OK - Fetched {len(df):,} data points")
            print(f"[BACKTEST]   Date range: {df.index[0]} to {df.index[-1]}")
            print(f"[BACKTEST]   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

            # Create strategy instance
            print(f"\n[BACKTEST] Step 2/4: Creating strategy instance...")
            strategy_obj = self._create_strategy(strategy, symbol, strategy_params, start_date)
            if strategy_obj is None:
                print(f"[BACKTEST] ERROR: Failed to create strategy: {strategy}")
                return None
            print(f"[BACKTEST] OK - Strategy created: {strategy_obj}")

            # Run backtest
            print(f"\n[BACKTEST] Step 3/4: Running backtest engine...")
            print(f"[BACKTEST] Commission: 0.1%")
            print(f"[BACKTEST] Slippage: 0.05%")
            engine = BacktestEngine(
                strategy=strategy_obj,
                initial_cash=initial_cash,
                commission=0.001,
                slippage=0.0005,
                log_to_csv=False  # Disable CSV logging for API
            )

            print(f"[BACKTEST] Starting engine.run() with {len(df):,} bars...")
            results = engine.run(df)
            print(f"[BACKTEST] OK - Engine completed")

            if results is None:
                print("[BACKTEST] ERROR: Engine returned None")
                return None

            # Process results
            print(f"\n[BACKTEST] Step 4/4: Processing results...")
            performance = results.get('performance', {})
            trading = results.get('trading', {})
            trades = results.get('trades', [])

            print(f"[BACKTEST] OK - Results processed")
            print(f"\n{'='*80}")
            print(f"[BACKTEST] SUMMARY")
            print(f"{'='*80}")
            print(f"[BACKTEST] Initial Capital: ${performance.get('initial_cash', initial_cash):,.2f}")
            print(f"[BACKTEST] Final Equity:    ${performance.get('final_equity', initial_cash):,.2f}")
            print(f"[BACKTEST] Total P&L:       ${performance.get('total_pnl', 0.0):+,.2f} ({performance.get('total_return', 0.0) * 100:+.2f}%)")
            print(f"[BACKTEST] ")
            print(f"[BACKTEST] Total Trades:    {trading.get('total_trades', 0)}")
            print(f"[BACKTEST] Winning:         {trading.get('winning_trades', 0)}")
            print(f"[BACKTEST] Losing:          {trading.get('losing_trades', 0)}")
            print(f"[BACKTEST] Win Rate:        {trading.get('win_rate', 0.0) * 100:.1f}%")
            print(f"[BACKTEST] ")
            print(f"[BACKTEST] Sharpe Ratio:    {performance.get('sharpe_ratio', 0.0):.3f}")
            print(f"[BACKTEST] Max Drawdown:    {performance.get('max_drawdown', 0.0) * 100:.2f}%")
            print(f"[BACKTEST] Profit Factor:   {trading.get('profit_factor', 0.0):.3f}")
            print(f"{'='*80}\n")

            # Save results
            result_id = self._save_results(strategy, symbol, start_date, end_date, results)
            print(f"[BACKTEST] OK - Results saved with ID: {result_id}")

            return {
                'id': result_id,
                'status': 'success',
                'strategy': strategy,
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'created_at': datetime.now().isoformat(),
                'performance': {
                    'initial_cash': sanitize_metric(performance.get('initial_cash', initial_cash)),
                    'final_equity': sanitize_metric(performance.get('final_equity', initial_cash)),
                    'total_return': sanitize_metric(performance.get('total_return', 0.0)),
                    'total_pnl': sanitize_metric(performance.get('total_pnl', 0.0)),
                    'sharpe_ratio': sanitize_metric(performance.get('sharpe_ratio', 0.0)),
                    'max_drawdown': sanitize_metric(performance.get('max_drawdown', 0.0))
                },
                'trading': {
                    'total_trades': trading.get('total_trades', 0),
                    'winning_trades': trading.get('winning_trades', 0),
                    'losing_trades': trading.get('losing_trades', 0),
                    'win_rate': sanitize_metric(trading.get('win_rate', 0.0)),
                    'profit_factor': sanitize_metric(trading.get('profit_factor', 0.0)),
                    'avg_win': sanitize_metric(trading.get('avg_win', 0.0)),
                    'avg_loss': sanitize_metric(abs(trading.get('avg_loss', 0.0)))
                }
            }

        except Exception as e:
            print(f"Error running backtest: {e}")
            import traceback
            traceback.print_exc()
            return None

    def list_backtests(self) -> List[Dict]:
        """
        List all saved backtest results

        Returns:
            List of backtest result summaries
        """
        results = []

        try:
            for result_file in self.results_dir.glob('*.json'):
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        # Sanitize loaded data to handle inf/nan from old files
                        result = sanitize_dict(result)
                        results.append(result)
                except Exception as e:
                    print(f"Error loading result {result_file}: {e}")
                    continue

        except Exception as e:
            print(f"Error listing backtests: {e}")

        return results

    def get_backtest(self, backtest_id: str) -> Optional[Dict]:
        """
        Get a specific backtest result

        Args:
            backtest_id: Backtest result ID

        Returns:
            Backtest results or None
        """
        try:
            result_file = self.results_dir / f"{backtest_id}.json"
            if not result_file.exists():
                return None

            with open(result_file, 'r') as f:
                result = json.load(f)
                # Sanitize loaded data to handle inf/nan from old files
                return sanitize_dict(result)

        except Exception as e:
            print(f"Error getting backtest: {e}")
            return None

    def _create_strategy(self, strategy_name: str, symbol: str, params: Dict, backtest_start_date: str = None):
        """Create a strategy instance using the registry."""
        try:
            # Get the strategy registry
            registry = get_strategy_registry()

            # Special handling for MLPredictive strategy - needs model path
            if strategy_name == 'MLPredictive':
                model_path = params.get('model_path')
                if not model_path:
                    # Find a model for this symbol
                    models_dir = Path(__file__).parent.parent.parent / 'runtime' / 'models'
                    timeframe = params.get('timeframe', '1m')

                    # Normalize symbol for filesystem (replace / with _)
                    symbol_normalized = symbol.replace('/', '_')

                    # Try multi_ohlc models first, then fall back to autoregressive
                    pattern_multi = f"{symbol_normalized}_{timeframe}_*steps_multi_ohlc"
                    pattern_auto = f"{symbol_normalized}_{timeframe}_*steps_autoregressive"

                    matches = list(models_dir.glob(pattern_multi))
                    if not matches:
                        matches = list(models_dir.glob(pattern_auto))

                    if not matches:
                        # No model found - train one automatically
                        print(f"No model found for {symbol} {timeframe}, training new model...")
                        model_path = self._train_model_for_backtest(symbol, timeframe, backtest_start_date)
                        if not model_path:
                            print("Failed to train model")
                            return None
                    else:
                        model_path = str(matches[0])
                        print(f"Using existing model: {model_path}")

                        # CRITICAL: Validate that backtest period doesn't overlap with training period
                        if backtest_start_date:
                            is_valid, message = self._validate_model_for_backtest(model_path, backtest_start_date)
                            if not is_valid:
                                print(f"[WARNING] {message}")
                                print(f"[ACTION] Training new model with correct period...")
                                model_path = self._train_model_for_backtest(symbol, timeframe, backtest_start_date)
                                if not model_path:
                                    print("Failed to train model")
                                    return None

                # Add model_path to params
                params['model_path'] = model_path

            # Use registry to create strategy instance
            print(f"[BacktestService] Creating strategy: {strategy_name}")
            strategy = registry.create_strategy(strategy_name, **params)

            if strategy is None:
                print(f"[BacktestService] Failed to create strategy: {strategy_name}")
                available = registry.get_all_strategies()
                print(f"[BacktestService] Available strategies: {list(available.keys())}")

            return strategy

        except Exception as e:
            print(f"Error creating strategy: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _validate_model_for_backtest(self, model_path: str, backtest_start_date: str) -> tuple[bool, str]:
        """
        Validate that a model's training period doesn't overlap with backtest period

        Args:
            model_path: Path to the model directory
            backtest_start_date: Start date of the backtest (ISO format)

        Returns:
            (is_valid, message): True if valid, False if overlap detected
        """
        try:
            metadata_path = Path(model_path) / 'training_metadata.json'

            # If no metadata exists, we can't validate (old model)
            if not metadata_path.exists():
                return (False, f"Model has no training metadata - cannot verify data integrity. Model: {model_path}")

            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            training_end = pd.to_datetime(metadata['training_end'])
            backtest_start = pd.to_datetime(backtest_start_date)

            # Check if backtest starts AFTER training ended (safe)
            if backtest_start >= training_end:
                print(f"[VALIDATION] ✓ Model is safe to use:")
                print(f"  Training ended: {training_end.isoformat()}")
                print(f"  Backtest starts: {backtest_start.isoformat()}")
                print(f"  No data leakage detected")
                return (True, "")
            else:
                # DATA LEAKAGE DETECTED
                overlap_days = (training_end - backtest_start).days
                message = (
                    f"DATA LEAKAGE DETECTED! Backtest period overlaps with training data.\n"
                    f"  Model training period: {metadata['training_start']} to {metadata['training_end']}\n"
                    f"  Backtest period starts: {backtest_start_date}\n"
                    f"  Overlap: {overlap_days} days\n"
                    f"  This would invalidate backtest results!"
                )
                return (False, message)

        except Exception as e:
            return (False, f"Error validating model metadata: {e}")

    def _train_model_for_backtest(self, symbol: str, timeframe: str, backtest_start_date: str = None) -> Optional[str]:
        """
        Train a model automatically for backtesting

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., '1m', '5m')
            backtest_start_date: Start date of the backtest (ISO format)
                                If provided, training data will end BEFORE this date to prevent data leakage

        Returns:
            Path to trained model or None if failed
        """
        try:
            print(f"Training Multi-OHLC model for {symbol} {timeframe}...")

            # Determine n_steps based on timeframe
            timeframe_to_steps = {
                '1m': 300, '5m': 144, '15m': 96,
                '1h': 72, '4h': 42, '1d': 30,
            }
            n_steps = timeframe_to_steps.get(timeframe, 100)

            # Fetch training data (30 days)
            from datetime import datetime, timedelta

            # IMPORTANT: End training data BEFORE the backtest period to prevent data leakage
            if backtest_start_date:
                end_dt = pd.to_datetime(backtest_start_date).to_pydatetime() - timedelta(days=1)
                print(f"[TRAIN] Training data will end at {end_dt} (1 day before backtest start)")
            else:
                end_dt = datetime.now()
                print(f"[TRAIN] No backtest date provided, using current time: {end_dt}")

            start_dt = end_dt - timedelta(days=30)
            print(f"[TRAIN] Training period: {start_dt} to {end_dt} (30 days)")

            df = self.fetcher.fetch(
                symbol=symbol,
                start=start_dt,
                end=end_dt,
                timeframe=timeframe,
                force_refresh=True
            )

            if df is None or len(df) < 1000:
                print(f"Insufficient data for training (got {len(df) if df is not None else 0} rows)")
                return None

            # Initialize and train model
            model = MultiOHLCPredictor(n_steps_ahead=n_steps)
            train_data, test_data = model.prepare_data(df, test_size=0.2)

            print("Training model (this may take 2-5 minutes)...")
            metrics = model.train(train_data, validation_split=0.2, verbose=True)

            if metrics is None:
                print("Model training failed")
                return None

            # Save model
            models_dir = Path(__file__).parent.parent.parent / 'runtime' / 'models'
            models_dir.mkdir(parents=True, exist_ok=True)

            # Normalize symbol for filesystem (replace / with _)
            symbol_normalized = symbol.replace('/', '_')
            model_dirname = f"{symbol_normalized}_{timeframe}_{n_steps}steps_multi_ohlc"
            model_path = models_dir / model_dirname

            model.save(str(model_path))
            print(f"Model saved to {model_path}")

            # Save training metadata for validation
            metadata = {
                'symbol': symbol,
                'timeframe': timeframe,
                'n_steps': n_steps,
                'training_start': start_dt.isoformat(),
                'training_end': end_dt.isoformat(),
                'created_at': datetime.now().isoformat(),
                'backtest_safe_from': end_dt.isoformat()  # Can backtest from this date onwards
            }
            metadata_path = model_path / 'training_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"[TRAIN] Metadata saved - Safe to backtest from: {end_dt.isoformat()}")

            return str(model_path)

        except Exception as e:
            print(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_results(
        self,
        strategy: str,
        symbol: str,
        start_date: str,
        end_date: str,
        results: Dict
    ) -> str:
        """Save backtest results to file"""
        # Generate ID (normalize symbol for filesystem)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        symbol_normalized = symbol.replace('/', '_')
        result_id = f"{strategy}_{symbol_normalized}_{timestamp}"

        # Prepare results for saving (sanitize to handle inf/nan)
        save_data = {
            'id': result_id,
            'strategy': strategy,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'created_at': datetime.now().isoformat(),
            'results': sanitize_dict(results)
        }

        # Save to file
        result_file = self.results_dir / f"{result_id}.json"
        with open(result_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)

        return result_id


# Singleton instance
_backtest_service = None


def get_backtest_service() -> BacktestService:
    """Get or create backtest service singleton"""
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService()
    return _backtest_service
