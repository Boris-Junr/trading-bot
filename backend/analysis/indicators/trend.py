"""
Trend indicators for identifying market direction.

Indicators:
- SMA: Simple Moving Average
- EMA: Exponential Moving Average
- MACD: Moving Average Convergence Divergence
"""
import pandas as pd
import numpy as np


class SMA:
    """Simple Moving Average - basic trend indicator."""

    @staticmethod
    def calculate(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            data: Price series (typically close prices)
            period: Number of periods (default: 20)

        Returns:
            Series with SMA values
        """
        return data.rolling(window=period).mean()


class EMA:
    """Exponential Moving Average - weighted trend indicator."""

    @staticmethod
    def calculate(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            data: Price series (typically close prices)
            period: Number of periods (default: 20)

        Returns:
            Series with EMA values
        """
        return data.ewm(span=period, adjust=False).mean()


class MACD:
    """
    Moving Average Convergence Divergence.

    Trend-following momentum indicator showing relationship
    between two moving averages.
    """

    @staticmethod
    def calculate(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        Calculate MACD indicator.

        Args:
            data: Price series (typically close prices)
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)

        Returns:
            DataFrame with columns: macd, signal, histogram
        """
        # Calculate EMAs
        fast_ema = data.ewm(span=fast_period, adjust=False).mean()
        slow_ema = data.ewm(span=slow_period, adjust=False).mean()

        # MACD line
        macd_line = fast_ema - slow_ema

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }, index=data.index)
