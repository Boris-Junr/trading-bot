"""
Price Feature Engineering

Extracts features from OHLCV data and technical indicators for ML models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from domain.indicators.trend import EMA
from domain.indicators.momentum import RSI, Stochastic
from domain.indicators.volatility import BollingerBands, ATR


class PriceFeatureEngineer:
    """
    Feature engineering for price prediction models.

    Extracts comprehensive features including:
    - Price-based features (returns, volatility, momentum)
    - Technical indicators (MACD, RSI, Bollinger Bands, etc.)
    - Pattern features (price patterns, volume patterns)
    - Time-based features (hour of day, day of week)
    """

    def __init__(self, lookback_periods: List[int] = [5, 10, 20, 50]):
        """
        Initialize feature engineer.

        Args:
            lookback_periods: Periods to calculate rolling features
        """
        self.lookback_periods = lookback_periods

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer all features from OHLCV data.

        Args:
            df: DataFrame with columns [open, high, low, close, volume]

        Returns:
            DataFrame with engineered features
        """
        # Performance optimization: if features already exist, return as-is
        # This allows pre-computed feature caching for backtesting
        expected_features = ['return_1', 'ema_10', 'rsi_14']  # Sample key features
        if all(col in df.columns for col in expected_features):
            return df

        features = df.copy()

        # Basic price features
        features = self._add_price_features(features)

        # Technical indicators
        features = self._add_technical_indicators(features)

        # Rolling statistics
        features = self._add_rolling_features(features)

        # Pattern features
        features = self._add_pattern_features(features)

        # Time-based features (if datetime index)
        if isinstance(features.index, pd.DatetimeIndex):
            features = self._add_time_features(features)

        return features

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic price-based features."""

        # Returns
        df['return_1'] = df['close'].pct_change(1)
        df['return_2'] = df['close'].pct_change(2)
        df['return_5'] = df['close'].pct_change(5)
        df['return_10'] = df['close'].pct_change(10)

        # Log returns (more stable for ML)
        df['log_return_1'] = np.log(df['close'] / df['close'].shift(1))
        df['log_return_5'] = np.log(df['close'] / df['close'].shift(5))

        # Price momentum
        df['momentum_5'] = df['close'] - df['close'].shift(5)
        df['momentum_10'] = df['close'] - df['close'].shift(10)
        df['momentum_20'] = df['close'] - df['close'].shift(20)

        # Price acceleration (rate of change of momentum)
        df['acceleration_5'] = df['momentum_5'] - df['momentum_5'].shift(5)

        # High-Low range
        df['hl_range'] = df['high'] - df['low']
        df['hl_range_pct'] = (df['high'] - df['low']) / df['close']

        # Open-Close relationship
        df['oc_range'] = df['close'] - df['open']
        df['oc_range_pct'] = (df['close'] - df['open']) / df['open']

        # Body to range ratio (candle body size)
        df['body_to_range'] = np.abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10)

        # Gap from previous close
        df['gap'] = df['open'] - df['close'].shift(1)
        df['gap_pct'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        return df

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features."""

        # Moving averages
        for period in [5, 10, 20, 50]:
            ema = EMA.calculate(df['close'], period=period)
            df[f'ema_{period}'] = ema
            df[f'price_to_ema_{period}'] = (df['close'] - ema) / ema

        # MACD
        ema_12 = EMA.calculate(df['close'], period=12)
        ema_26 = EMA.calculate(df['close'], period=26)
        macd = ema_12 - ema_26
        signal = EMA.calculate(macd, period=9)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_histogram'] = macd - signal

        # RSI
        for period in [7, 14, 21]:
            df[f'rsi_{period}'] = RSI.calculate(df['close'], period=period)

        # Stochastic
        stoch = Stochastic.calculate(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch['k']
        df['stoch_d'] = stoch['d']

        # Bollinger Bands
        bb = BollingerBands.calculate(df['close'])
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        df['bb_width'] = bb['bandwidth']  # Note: BB returns 'bandwidth', not 'width'
        df['bb_position'] = (df['close'] - bb['lower']) / (bb['upper'] - bb['lower'] + 1e-10)

        # ATR (volatility)
        df['atr'] = ATR.calculate(df['high'], df['low'], df['close'])
        df['atr_pct'] = df['atr'] / df['close']

        # Volume indicators
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / (df['volume_ma_20'] + 1e-10)

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling statistical features."""

        for period in self.lookback_periods:
            # Rolling mean and std
            df[f'close_mean_{period}'] = df['close'].rolling(window=period).mean()
            df[f'close_std_{period}'] = df['close'].rolling(window=period).std()

            # Z-score (how many standard deviations from mean)
            df[f'close_zscore_{period}'] = (
                (df['close'] - df[f'close_mean_{period}']) /
                (df[f'close_std_{period}'] + 1e-10)
            )

            # Rolling min/max
            df[f'close_min_{period}'] = df['close'].rolling(window=period).min()
            df[f'close_max_{period}'] = df['close'].rolling(window=period).max()

            # Position in range
            df[f'position_in_range_{period}'] = (
                (df['close'] - df[f'close_min_{period}']) /
                (df[f'close_max_{period}'] - df[f'close_min_{period}'] + 1e-10)
            )

            # Rolling return volatility
            df[f'return_volatility_{period}'] = df['return_1'].rolling(window=period).std()

        return df

    def _add_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add pattern-based features."""

        # Trend direction (simple: price vs moving average)
        df['trend_short'] = np.where(df['close'] > df['ema_10'], 1, -1)
        df['trend_medium'] = np.where(df['close'] > df['ema_20'], 1, -1)
        df['trend_long'] = np.where(df['close'] > df['ema_50'], 1, -1)

        # Candle patterns (simplified)
        body = df['close'] - df['open']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']

        df['is_bullish'] = (body > 0).astype(int)
        df['upper_shadow_ratio'] = upper_shadow / (df['hl_range'] + 1e-10)
        df['lower_shadow_ratio'] = lower_shadow / (df['hl_range'] + 1e-10)

        # Consecutive candles
        df['consecutive_up'] = (df['is_bullish'].groupby(
            (df['is_bullish'] != df['is_bullish'].shift()).cumsum()
        ).cumsum())

        # Volume patterns
        df['volume_increasing'] = (df['volume'] > df['volume'].shift(1)).astype(int)

        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features (for intraday data)."""

        # Hour of day (for intraday trading)
        df['hour'] = df.index.hour
        df['minute'] = df.index.minute

        # Day of week (0 = Monday, 6 = Sunday)
        df['day_of_week'] = df.index.dayofweek

        # Cyclical encoding (so hour 23 and hour 0 are close)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        return df

    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of feature column names (excluding OHLCV and target).

        Args:
            df: DataFrame with features

        Returns:
            List of feature column names
        """
        # Exclude original OHLCV columns, metadata, and any target columns
        exclude_cols = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        exclude_cols += ['source', 'symbol', 'timeframe']  # Metadata columns
        exclude_cols += [col for col in df.columns if col.startswith('target_')]

        # Only include numeric columns (exclude any remaining object/string types)
        feature_cols = [
            col for col in df.columns
            if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])
        ]
        return feature_cols
