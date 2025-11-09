"""
Triangle pattern recognition.

Triangle patterns are continuation patterns formed by converging trendlines.
Types:
- Ascending Triangle: Flat top, rising bottom (bullish)
- Descending Triangle: Flat bottom, falling top (bearish)
- Symmetrical Triangle: Converging trendlines (neutral until breakout)
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress
from typing import Optional, Dict, List, Tuple


class TrianglePatterns:
    """Detect triangle chart patterns."""

    @staticmethod
    def detect_ascending_triangle(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 20,
        tolerance: float = 0.02
    ) -> Optional[Dict]:
        """
        Detect ascending triangle pattern.

        Characteristics:
        - Flat resistance line (horizontal highs)
        - Rising support line (higher lows)
        - Bullish continuation pattern

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period
            tolerance: Price tolerance for flat line (2% default)

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(high) < window:
            return None

        recent_highs = high.tail(window)
        recent_lows = low.tail(window)

        # Check for flat top (resistance)
        highs_std = recent_highs.std() / recent_highs.mean()
        if highs_std > tolerance:
            return None  # Top not flat enough

        # Check for rising bottom (support)
        x = np.arange(len(recent_lows))
        slope, intercept, r_value, _, _ = linregress(x, recent_lows)

        if slope <= 0 or r_value**2 < 0.7:  # Must be rising with good fit
            return None

        # Pattern detected
        resistance = recent_highs.mean()
        current_price = close.iloc[-1]

        return {
            'pattern': 'ascending_triangle',
            'type': 'bullish_continuation',
            'resistance': resistance,
            'support_slope': slope,
            'current_price': current_price,
            'breakout_target': resistance,
            'confidence': r_value**2,
            'signal': 'BUY' if current_price > resistance else 'WAIT'
        }

    @staticmethod
    def detect_descending_triangle(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 20,
        tolerance: float = 0.02
    ) -> Optional[Dict]:
        """
        Detect descending triangle pattern.

        Characteristics:
        - Flat support line (horizontal lows)
        - Falling resistance line (lower highs)
        - Bearish continuation pattern

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period
            tolerance: Price tolerance for flat line

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(low) < window:
            return None

        recent_highs = high.tail(window)
        recent_lows = low.tail(window)

        # Check for flat bottom (support)
        lows_std = recent_lows.std() / recent_lows.mean()
        if lows_std > tolerance:
            return None

        # Check for falling top (resistance)
        x = np.arange(len(recent_highs))
        slope, intercept, r_value, _, _ = linregress(x, recent_highs)

        if slope >= 0 or r_value**2 < 0.7:  # Must be falling
            return None

        # Pattern detected
        support = recent_lows.mean()
        current_price = close.iloc[-1]

        return {
            'pattern': 'descending_triangle',
            'type': 'bearish_continuation',
            'support': support,
            'resistance_slope': slope,
            'current_price': current_price,
            'breakdown_target': support,
            'confidence': r_value**2,
            'signal': 'SELL' if current_price < support else 'WAIT'
        }

    @staticmethod
    def detect_symmetrical_triangle(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 20
    ) -> Optional[Dict]:
        """
        Detect symmetrical triangle pattern.

        Characteristics:
        - Converging trendlines (lower highs and higher lows)
        - Neutral pattern - direction depends on breakout
        - Decreasing volume during formation

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(high) < window:
            return None

        recent_highs = high.tail(window)
        recent_lows = low.tail(window)
        x = np.arange(len(recent_highs))

        # Analyze upper trendline (should be descending)
        slope_high, intercept_high, r_high, _, _ = linregress(x, recent_highs)

        # Analyze lower trendline (should be ascending)
        slope_low, intercept_low, r_low, _, _ = linregress(x, recent_lows)

        # Check for convergence
        if slope_high >= 0 or slope_low <= 0:
            return None  # Not converging

        # Both trendlines should have good fit
        if r_high**2 < 0.6 or r_low**2 < 0.6:
            return None

        # Calculate apex (where lines would meet)
        # slope_high * x + intercept_high = slope_low * x + intercept_low
        if abs(slope_high - slope_low) < 0.001:
            return None  # Lines parallel

        apex_x = (intercept_low - intercept_high) / (slope_high - slope_low)
        apex_price = slope_high * apex_x + intercept_high

        current_price = close.iloc[-1]
        upper_line = slope_high * len(x) + intercept_high
        lower_line = slope_low * len(x) + intercept_low

        return {
            'pattern': 'symmetrical_triangle',
            'type': 'neutral_continuation',
            'upper_trendline': upper_line,
            'lower_trendline': lower_line,
            'apex_price': apex_price,
            'apex_bars_away': apex_x - len(x),
            'current_price': current_price,
            'confidence': (r_high**2 + r_low**2) / 2,
            'signal': 'WAIT_FOR_BREAKOUT'
        }

    @classmethod
    def scan_all(
        cls,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 20
    ) -> List[Dict]:
        """
        Scan for all triangle patterns.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period

        Returns:
            List of detected patterns
        """
        patterns = []

        # Check each pattern type
        ascending = cls.detect_ascending_triangle(high, low, close, window)
        if ascending:
            patterns.append(ascending)

        descending = cls.detect_descending_triangle(high, low, close, window)
        if descending:
            patterns.append(descending)

        symmetrical = cls.detect_symmetrical_triangle(high, low, close, window)
        if symmetrical:
            patterns.append(symmetrical)

        return patterns
