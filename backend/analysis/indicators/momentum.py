"""
Momentum indicators for measuring rate of price change.

Indicators:
- RSI: Relative Strength Index
- Stochastic: Stochastic Oscillator
"""
import pandas as pd
import numpy as np


class RSI:
    """
    Relative Strength Index.

    Momentum oscillator measuring speed and magnitude of price changes.
    Range: 0-100 (oversold < 30, overbought > 70)
    """

    @staticmethod
    def calculate(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI indicator.

        Args:
            data: Price series (typically close prices)
            period: Number of periods (default: 14)

        Returns:
            Series with RSI values (0-100)
        """
        # Calculate price changes
        delta = data.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate average gains and losses using EMA
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()

        # Calculate RS (Relative Strength)
        rs = avg_gains / avg_losses

        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))

        return rsi


class Stochastic:
    """
    Stochastic Oscillator.

    Momentum indicator comparing closing price to price range over time.
    Range: 0-100 (oversold < 20, overbought > 80)
    """

    @staticmethod
    def calculate(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator.

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period (default: 14)
            d_period: %D smoothing period (default: 3)

        Returns:
            DataFrame with columns: k (fast), d (slow)
        """
        # Find highest high and lowest low over period
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # Calculate %K (fast stochastic)
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # Calculate %D (slow stochastic - SMA of %K)
        d = k.rolling(window=d_period).mean()

        return pd.DataFrame({
            'k': k,
            'd': d
        }, index=close.index)
