"""
ML Predictive Strategy

Trading strategy based on gradient boosting price predictions.
Uses trained ML models to predict future prices and makes decisions based on expected returns.
"""

import pandas as pd
import numpy as np
from typing import Optional
import os

from domain.strategies.base import Strategy, Signal, SignalType
from domain.strategies.portfolio import Position
from domain.ml.predictors.autoregressive_predictor import AutoregressivePricePredictor
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor
import pickle
from pathlib import Path


class MLPredictiveStrategy(Strategy):
    """
    Strategy that uses ML predictions to make trading decisions.

    Loads a trained AutoregressivePricePredictor and generates signals based on
    predicted price movements over the next N minutes.
    Uses autoregressive gradient boosting for smooth, coherent price curves.
    """

    def __init__(
        self,
        model_path: str,
        min_predicted_return: float = 0.002,  # 0.2% minimum expected gain
        confidence_threshold: float = 0.6,
        prediction_window: int = 60,  # Use first 60 minutes of predictions
        risk_per_trade: float = 0.02,  # 2% risk per trade
        use_prefilter: bool = True,  # Use technical indicator pre-filter
        prefilter_threshold: float = 0.3  # Minimum setup score to trigger ML
    ):
        """
        Initialize ML Predictive Strategy.

        Args:
            model_path: Path to saved model directory
            min_predicted_return: Minimum predicted return to trigger a signal
            confidence_threshold: Minimum confidence for signal generation
            prediction_window: Number of future steps to consider for decision
            risk_per_trade: Fraction of capital to risk per trade
            use_prefilter: Whether to use technical indicator pre-filtering
            prefilter_threshold: Minimum setup score (0-1) to trigger ML prediction
        """
        super().__init__()

        self.model_path = model_path
        self.min_predicted_return = min_predicted_return
        self.confidence_threshold = confidence_threshold
        self.prediction_window = prediction_window
        self.risk_per_trade = risk_per_trade
        self.use_prefilter = use_prefilter
        self.prefilter_threshold = prefilter_threshold

        # Load the trained predictor (can be either AutoregressivePricePredictor or MultiOHLCPredictor)
        self.predictor = None
        self._load_model()

        # Feature cache for backtesting performance
        self._feature_cache = None
        self._cache_enabled = False

        # Track ML call statistics
        self._ml_calls = 0
        self._total_signals = 0

    def _load_model(self):
        """Load the trained ML model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model path not found: {self.model_path}")

        # Determine model type by checking config
        model_path_obj = Path(self.model_path)
        config_file = model_path_obj / 'config.pkl'

        if not config_file.exists():
            raise FileNotFoundError(f"Model config not found: {config_file}")

        with open(config_file, 'rb') as f:
            config = pickle.load(f)

        model_type = config.get('predictor_type', 'autoregressive')

        # Load appropriate predictor
        if model_type == 'multi_ohlc':
            print(f"Loading Multi-OHLC predictor from {self.model_path}")
            self.predictor = MultiOHLCPredictor(n_steps_ahead=1)  # Placeholder
            self.predictor.load(self.model_path)
        else:
            print(f"Loading Autoregressive predictor from {self.model_path}")
            self.predictor = AutoregressivePricePredictor(n_steps_ahead=1)  # Placeholder
            self.predictor.load(self.model_path)

        print(f"Loaded ML model from {self.model_path}")
        print(f"Model predicts {self.predictor.n_steps_ahead} steps ahead")

    def enable_feature_cache(self, full_data: pd.DataFrame):
        """
        Pre-compute features for entire dataset to optimize backtesting.

        This dramatically improves performance by calculating features once
        instead of recalculating overlapping windows on every bar.

        Args:
            full_data: Complete OHLCV dataset for backtest
        """
        if self.predictor is None:
            return

        print(f"[STRATEGY] Pre-computing features for {len(full_data):,} bars...")
        import time
        start_time = time.time()

        # Get feature engineer (works for both AutoregressivePredictor and MultiOHLCPredictor)
        if hasattr(self.predictor, 'feature_engineer'):
            feature_engineer = self.predictor.feature_engineer
        elif hasattr(self.predictor, 'close_predictor'):
            # MultiOHLCPredictor uses sub-predictors
            feature_engineer = self.predictor.close_predictor.feature_engineer
        else:
            print("[STRATEGY] WARNING: Could not find feature engineer, caching disabled")
            return

        # Pre-compute features for the entire dataset
        self._feature_cache = feature_engineer.engineer_features(full_data.copy())
        self._cache_enabled = True

        elapsed = time.time() - start_time
        print(f"[STRATEGY] Feature pre-computation complete in {elapsed:.2f}s ({len(full_data)/elapsed:.0f} bars/sec)")

    def _check_triggers(self, df: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if any simple trigger conditions are met.

        Uses a trigger-based approach: ANY trigger firing → call ML for final decision
        This generates more trading opportunities compared to requiring all conditions.

        Returns:
            (trigger_fired: bool, trigger_name: str)
        """
        if len(df) < 50:
            return False, "insufficient_data"

        recent = df.tail(50)
        current_close = recent['close'].iloc[-1]

        # TRIGGER 1: RSI Extremes (Oversold/Overbought)
        # Simple mean reversion setup - 1 indicator
        rsi_period = 14
        if len(recent) >= rsi_period:
            delta = recent['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            # Trigger on extreme RSI
            if current_rsi < 30 or current_rsi > 70:
                return True, f"rsi_extreme_{current_rsi:.1f}"

        # TRIGGER 2: MACD Crossover
        # Simple momentum setup - 1 indicator
        if len(recent) >= 26:
            ema12 = recent['close'].ewm(span=12, adjust=False).mean()
            ema26 = recent['close'].ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9, adjust=False).mean()

            macd_vals = macd.tail(2).values
            signal_vals = signal_line.tail(2).values

            # Trigger on fresh crossover (happened in last bar)
            if (macd_vals[-2] <= signal_vals[-2] and macd_vals[-1] > signal_vals[-1]):
                return True, "macd_bullish_cross"
            if (macd_vals[-2] >= signal_vals[-2] and macd_vals[-1] < signal_vals[-1]):
                return True, "macd_bearish_cross"

        # TRIGGER 3: Volume Spike + Price Move
        # 2 indicators - confirms market interest
        if 'volume' in recent.columns and len(recent) >= 20:
            avg_volume = recent['volume'].rolling(window=20).mean().iloc[-1]
            current_volume = recent['volume'].iloc[-1]

            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                price_change = abs(current_close / recent['close'].iloc[-2] - 1)

                # Trigger on volume spike (2x) + significant price move (>0.3%)
                if volume_ratio > 2.0 and price_change > 0.003:
                    return True, f"volume_spike_{volume_ratio:.1f}x"

        # TRIGGER 4: Strong Momentum
        # Price action setup - 1 concept
        if len(recent) >= 10:
            momentum_5 = (current_close / recent['close'].iloc[-6] - 1) if len(recent) >= 6 else 0

            # Trigger on strong 5-bar momentum (>0.5%)
            if abs(momentum_5) > 0.005:
                direction = "bullish" if momentum_5 > 0 else "bearish"
                return True, f"strong_momentum_{direction}_{abs(momentum_5)*100:.2f}%"

        # TRIGGER 5: Bollinger Band Squeeze + Breakout
        # 2-3 indicators - volatility breakout setup
        if len(recent) >= 20:
            sma20 = recent['close'].rolling(window=20).mean()
            std20 = recent['close'].rolling(window=20).std()
            upper_band = sma20 + (2 * std20)
            lower_band = sma20 - (2 * std20)

            bb_width = (upper_band - lower_band) / sma20
            avg_bb_width = bb_width.rolling(window=20).mean().iloc[-1]
            current_bb_width = bb_width.iloc[-1]

            # Squeeze: BB width < 80% of average width
            is_squeeze = current_bb_width < avg_bb_width * 0.8

            # Breakout: Price broke above upper or below lower band
            broke_upper = current_close > upper_band.iloc[-1]
            broke_lower = current_close < lower_band.iloc[-1]

            if is_squeeze and (broke_upper or broke_lower):
                direction = "up" if broke_upper else "down"
                return True, f"bb_breakout_{direction}"

        # TRIGGER 6: Moving Average Cross
        # Classic trend-following setup - 2 indicators
        if len(recent) >= 50:
            sma20 = recent['close'].rolling(window=20).mean()
            sma50 = recent['close'].rolling(window=50).mean()

            sma20_vals = sma20.tail(2).values
            sma50_vals = sma50.tail(2).values

            # Golden cross or death cross
            if (sma20_vals[-2] <= sma50_vals[-2] and sma20_vals[-1] > sma50_vals[-1]):
                return True, "golden_cross"
            if (sma20_vals[-2] >= sma50_vals[-2] and sma20_vals[-1] < sma50_vals[-1]):
                return True, "death_cross"

        return False, "no_trigger"

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on ML predictions.

        Args:
            df: DataFrame with OHLCV data (must have sufficient history for features)

        Returns:
            Signal with type, confidence, and metadata
        """
        # Track signal generation count
        if not hasattr(self, '_signal_count'):
            self._signal_count = 0
            self._last_log_time = None

        self._signal_count += 1
        self._total_signals += 1

        # Log every 1000 signals with ML efficiency stats
        import time
        if self._signal_count % 1000 == 0:
            current_time = time.time()
            ml_efficiency = (1 - self._ml_calls / self._total_signals) * 100 if self._total_signals > 0 else 0
            if self._last_log_time:
                elapsed = current_time - self._last_log_time
                signals_per_sec = 1000 / elapsed if elapsed > 0 else 0
                print(f"[STRATEGY] Generated {self._signal_count:,} signals | Speed: {signals_per_sec:.1f} signals/sec | ML calls: {self._ml_calls:,} ({ml_efficiency:.1f}% reduction)")
            else:
                print(f"[STRATEGY] Generated {self._signal_count:,} signals | ML calls: {self._ml_calls:,}")
            self._last_log_time = current_time

        if self.predictor is None:
            return Signal(
                type=SignalType.HOLD,
                timestamp=df.index[-1],
                price=df['close'].iloc[-1],
                confidence=0.0
            )

        # Need at least 100 bars for feature engineering
        if len(df) < 100:
            return Signal(
                type=SignalType.HOLD,
                timestamp=df.index[-1],
                price=df['close'].iloc[-1],
                confidence=0.0
            )

        # PERFORMANCE OPTIMIZATION: Use fast trigger-based pre-filter before expensive ML call
        # This reduces ML calls by checking simple technical setups first
        trigger_name = None  # Track which trigger fired (if any)
        if self.use_prefilter:
            trigger_fired, trigger_name = self._check_triggers(df)

            # If no trigger fired, skip ML prediction entirely
            if not trigger_fired:
                return Signal(
                    type=SignalType.HOLD,
                    timestamp=df.index[-1],
                    price=df['close'].iloc[-1],
                    confidence=0.0,
                    metadata={'trigger': trigger_name, 'reason': 'no_trigger'}
                )
            # Otherwise, a trigger fired - validate with ML
            # Trigger name will be included in final signal metadata

        # Get predictions (EXPENSIVE - only called when pre-filter passes or if prefilter disabled)
        try:
            self._ml_calls += 1  # Track expensive ML calls

            # Use cached features if available (massive performance boost for backtesting)
            if self._cache_enabled and self._feature_cache is not None:
                # Get the indices we need from the original df
                needed_indices = df.tail(100).index

                # Slice the cached features to match
                # This avoids recalculating features for overlapping windows
                cached_slice = self._feature_cache.loc[needed_indices]

                # Predict using cached features
                predictions = self.predictor.predict(cached_slice)
            else:
                # Original path - recalculate features (slower for backtesting)
                predictions = self.predictor.predict(df.tail(100))
        except Exception as e:
            print(f"[STRATEGY ERROR] Error generating predictions at signal {self._signal_count}: {e}")
            import traceback
            traceback.print_exc()
            return Signal(
                type=SignalType.HOLD,
                timestamp=df.index[-1],
                price=df['close'].iloc[-1],
                confidence=0.0
            )

        # Extract predicted returns for the prediction window
        prediction_steps = min(self.prediction_window, self.predictor.n_steps_ahead)
        pred_returns = [
            predictions[f'predicted_return_{i}'].iloc[0]
            for i in range(1, prediction_steps + 1)
        ]

        # Calculate statistics on predicted returns
        avg_return = np.mean(pred_returns)
        max_return = np.max(pred_returns)
        min_return = np.min(pred_returns)
        return_std = np.std(pred_returns)

        # Count consecutive positive/negative predictions
        consecutive_positive = 0
        consecutive_negative = 0
        for ret in pred_returns:
            if ret > 0:
                consecutive_positive += 1
                consecutive_negative = 0
            elif ret < 0:
                consecutive_negative += 1
                consecutive_positive = 0
            else:
                break

        # Calculate confidence based on prediction consistency
        if avg_return > 0:
            # For bullish prediction, confidence increases with:
            # - Higher average return
            # - More consecutive positive predictions
            # - Lower standard deviation (more certain)
            confidence = min(1.0, abs(avg_return) / self.min_predicted_return * 0.5 +
                           consecutive_positive / prediction_steps * 0.3 +
                           (1 - min(1.0, return_std / 0.01)) * 0.2)
        elif avg_return < 0:
            # For bearish prediction, similar logic
            confidence = min(1.0, abs(avg_return) / self.min_predicted_return * 0.5 +
                           consecutive_negative / prediction_steps * 0.3 +
                           (1 - min(1.0, return_std / 0.01)) * 0.2)
        else:
            confidence = 0.0

        # Decision logic
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]

        # BUY signal: Strong upward prediction
        if avg_return > self.min_predicted_return and confidence >= self.confidence_threshold:
            # Calculate target and stop based on predictions
            target_price = current_price * (1 + max_return)
            stop_price = current_price * (1 - self.risk_per_trade)

            metadata = {
                'predicted_avg_return': avg_return,
                'predicted_max_return': max_return,
                'predicted_min_return': min_return,
                'return_std': return_std,
                'consecutive_positive': consecutive_positive,
                'target_price': target_price,
                'stop_loss': stop_price,
                'prediction_window': prediction_steps
            }

            # Include trigger info if available
            if trigger_name:
                metadata['trigger'] = trigger_name

            return Signal(
                type=SignalType.BUY,
                timestamp=current_time,
                price=current_price,
                confidence=confidence,
                metadata=metadata
            )

        # SELL signal: Strong downward prediction
        elif avg_return < -self.min_predicted_return and confidence >= self.confidence_threshold:
            # For short positions (if supported)
            target_price = current_price * (1 + min_return)
            stop_price = current_price * (1 + self.risk_per_trade)

            metadata = {
                'predicted_avg_return': avg_return,
                'predicted_max_return': max_return,
                'predicted_min_return': min_return,
                'return_std': return_std,
                'consecutive_negative': consecutive_negative,
                'target_price': target_price,
                'stop_loss': stop_price,
                'prediction_window': prediction_steps
            }

            # Include trigger info if available
            if trigger_name:
                metadata['trigger'] = trigger_name

            return Signal(
                type=SignalType.SELL,
                timestamp=current_time,
                price=current_price,
                confidence=confidence,
                metadata=metadata
            )

        # HOLD: Prediction not strong enough
        else:
            return Signal(
                type=SignalType.HOLD,
                timestamp=current_time,
                price=current_price,
                confidence=1.0 - confidence,  # High confidence to hold
                metadata={
                    'predicted_avg_return': avg_return,
                    'return_std': return_std,
                    'reason': 'insufficient_signal' if confidence < self.confidence_threshold else 'neutral_prediction'
                }
            )

    def should_close_position(self, position: Position, df: pd.DataFrame) -> bool:
        """
        Determine if an open position should be closed based on new predictions.

        Args:
            position: Current open position
            df: Updated OHLCV data

        Returns:
            True if position should be closed, False otherwise
        """
        if self.predictor is None or len(df) < 100:
            return False

        # Get new predictions
        try:
            predictions = self.predictor.predict(df.tail(100))
        except Exception:
            return False

        # Extract short-term predicted returns (next 15 minutes)
        short_term_steps = min(15, self.predictor.n_steps_ahead)
        short_term_returns = [
            predictions[f'predicted_return_{i}'].iloc[0]
            for i in range(1, short_term_steps + 1)
        ]
        avg_short_term = np.mean(short_term_returns)

        # Close long position if predictions turn negative
        if position.side == 'long' and avg_short_term < -0.001:
            return True

        # Close short position if predictions turn positive
        if position.side == 'short' and avg_short_term > 0.001:
            return True

        return False

    def get_position_size(self, signal: Signal, capital: float, current_price: float) -> float:
        """
        Calculate position size based on risk management.

        Args:
            signal: Generated trading signal
            capital: Available capital
            current_price: Current asset price

        Returns:
            Position size (quantity to trade)
        """
        if signal.signal_type == SignalType.HOLD:
            return 0.0

        # Risk-based position sizing
        risk_amount = capital * self.risk_per_trade

        # Calculate stop distance
        if 'stop_loss' in signal.metadata:
            stop_loss = signal.metadata['stop_loss']
            stop_distance = abs(current_price - stop_loss)

            if stop_distance > 0:
                # Position size = Risk Amount / Stop Distance
                position_size = risk_amount / stop_distance

                # Adjust by confidence
                position_size *= signal.confidence

                # Convert to quantity
                quantity = position_size / current_price

                # Ensure we don't use more than 20% of capital per trade
                max_position_value = capital * 0.2
                max_quantity = max_position_value / current_price

                return min(quantity, max_quantity)

        # Fallback: Use fixed percentage of capital
        position_value = capital * self.risk_per_trade * signal.confidence
        return position_value / current_price

    def get_name(self) -> str:
        """Return strategy name."""
        return "MLPredictiveStrategy"

    @classmethod
    def get_metadata(cls) -> dict:
        """Return strategy metadata for auto-discovery."""
        return {
            'name': 'MLPredictive',
            'label': 'ML Predictive Strategy',
            'description': 'Uses machine learning to predict future price movements and generates signals based on expected returns',
            'requires_model': True,
            'category': 'machine_learning',
            'parameters': {
                'model_path': {'type': 'string', 'required': True, 'description': 'Path to trained model'},
                'min_predicted_return': {'type': 'float', 'default': 0.002, 'description': 'Minimum predicted return (0.2%)'},
                'confidence_threshold': {'type': 'float', 'default': 0.6, 'description': 'Minimum confidence (0-1)'},
                'prediction_window': {'type': 'int', 'default': 60, 'description': 'Prediction window in minutes'},
                'risk_per_trade': {'type': 'float', 'default': 0.02, 'description': 'Risk per trade (2%)'},
                'use_prefilter': {'type': 'bool', 'default': True, 'description': 'Use technical indicator pre-filter'},
                'prefilter_threshold': {'type': 'float', 'default': 0.3, 'description': 'Minimum setup score (0-1)'}
            }
        }

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return (f"MLPredictiveStrategy(model={os.path.basename(self.model_path)}, "
                f"min_return={self.min_predicted_return:.2%}, "
                f"window={self.prediction_window}min)")
