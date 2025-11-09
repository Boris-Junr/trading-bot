"""
Volatility indicators for measuring price variability.

Indicators:
- Bollinger Bands: Price envelope based on standard deviation
- ATR: Average True Range
"""
import pandas as pd
import numpy as np


class BollingerBands:
    """
    Bollinger Bands.

    Volatility bands placed above and below moving average.
    Useful for identifying overbought/oversold conditions.
    """

    @staticmethod
    def calculate(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            data: Price series (typically close prices)
            period: Moving average period (default: 20)
            std_dev: Number of standard deviations (default: 2.0)

        Returns:
            DataFrame with columns: upper, middle, lower, bandwidth
        """
        # Calculate middle band (SMA)
        middle = data.rolling(window=period).mean()

        # Calculate standard deviation
        std = data.rolling(window=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Calculate bandwidth (measures volatility)
        bandwidth = (upper - lower) / middle * 100

        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth
        }, index=data.index)


class ATR:
    """
    Average True Range.

    Volatility indicator measuring degree of price movement.
    Higher ATR = higher volatility.
    """

    @staticmethod
    def calculate(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Smoothing period (default: 14)

        Returns:
            Series with ATR values
        """
        # Calculate True Range components
        tr1 = high - low  # Current high - low
        tr2 = abs(high - close.shift(1))  # Current high - previous close
        tr3 = abs(low - close.shift(1))  # Current low - previous close

        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR using EMA smoothing
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr
