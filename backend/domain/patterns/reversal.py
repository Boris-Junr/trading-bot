"""
Reversal pattern recognition.

Patterns that suggest a trend reversal:
- Head and Shoulders: Classic reversal pattern
- Double Top/Bottom: Two failed attempts to break through level
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Optional, Dict, List


class HeadAndShoulders:
    """Detect head and shoulders reversal pattern."""

    @staticmethod
    def detect(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 60
    ) -> Optional[Dict]:
        """
        Detect head and shoulders pattern.

        Characteristics:
        - Left shoulder: Peak
        - Head: Higher peak
        - Right shoulder: Peak similar to left
        - Neckline: Support connecting lows between peaks
        - Bearish reversal when neckline breaks

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

        # Find peaks in highs
        peaks, _ = find_peaks(recent_highs.values, distance=window//6)

        if len(peaks) < 3:
            return None  # Need at least 3 peaks

        # Get last 3 peaks
        peak_indices = peaks[-3:]
        peak_values = recent_highs.iloc[peak_indices].values

        # Check pattern: left shoulder < head > right shoulder
        left_shoulder, head, right_shoulder = peak_values

        # Head should be highest
        if head <= left_shoulder or head <= right_shoulder:
            return None

        # Shoulders should be similar (within 5%)
        shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
        if shoulder_diff > 0.05:
            return None

        # Find neckline (lows between peaks)
        neckline_start_idx = peak_indices[0]
        neckline_end_idx = peak_indices[2]
        neckline_lows = recent_lows.iloc[neckline_start_idx:neckline_end_idx]
        neckline = neckline_lows.min()

        current_price = close.iloc[-1]

        # Calculate target (distance from head to neckline)
        target_distance = head - neckline

        return {
            'pattern': 'head_and_shoulders',
            'type': 'bearish_reversal',
            'left_shoulder': left_shoulder,
            'head': head,
            'right_shoulder': right_shoulder,
            'neckline': neckline,
            'current_price': current_price,
            'target': neckline - target_distance,  # Projected downside
            'signal': 'SELL' if current_price < neckline else 'WAIT'
        }


class DoubleTops:
    """Detect double top/bottom reversal patterns."""

    @staticmethod
    def detect_double_top(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 40,
        tolerance: float = 0.02
    ) -> Optional[Dict]:
        """
        Detect double top pattern.

        Characteristics:
        - Two peaks at similar levels
        - Trough between them
        - Bearish reversal pattern

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period
            tolerance: Price tolerance for "equal" peaks (2%)

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(high) < window:
            return None

        recent_highs = high.tail(window)

        # Find peaks
        peaks, _ = find_peaks(recent_highs.values, distance=window//4)

        if len(peaks) < 2:
            return None

        # Get last 2 peaks
        peak1_idx, peak2_idx = peaks[-2:]
        peak1_value = recent_highs.iloc[peak1_idx]
        peak2_value = recent_highs.iloc[peak2_idx]

        # Peaks should be similar
        peak_diff = abs(peak1_value - peak2_value) / peak1_value
        if peak_diff > tolerance:
            return None

        # Find trough between peaks
        between_peaks = low.iloc[peak1_idx:peak2_idx]
        trough = between_peaks.min()

        current_price = close.iloc[-1]
        resistance = (peak1_value + peak2_value) / 2

        return {
            'pattern': 'double_top',
            'type': 'bearish_reversal',
            'first_peak': peak1_value,
            'second_peak': peak2_value,
            'support': trough,
            'resistance': resistance,
            'current_price': current_price,
            'target': trough - (resistance - trough),
            'signal': 'SELL' if current_price < trough else 'WAIT'
        }

    @staticmethod
    def detect_double_bottom(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 40,
        tolerance: float = 0.02
    ) -> Optional[Dict]:
        """
        Detect double bottom pattern.

        Characteristics:
        - Two troughs at similar levels
        - Peak between them
        - Bullish reversal pattern

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period
            tolerance: Price tolerance

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(low) < window:
            return None

        recent_lows = low.tail(window)

        # Find troughs (invert to use find_peaks)
        troughs, _ = find_peaks(-recent_lows.values, distance=window//4)

        if len(troughs) < 2:
            return None

        # Get last 2 troughs
        trough1_idx, trough2_idx = troughs[-2:]
        trough1_value = recent_lows.iloc[trough1_idx]
        trough2_value = recent_lows.iloc[trough2_idx]

        # Troughs should be similar
        trough_diff = abs(trough1_value - trough2_value) / trough1_value
        if trough_diff > tolerance:
            return None

        # Find peak between troughs
        between_troughs = high.iloc[trough1_idx:trough2_idx]
        peak = between_troughs.max()

        current_price = close.iloc[-1]
        support = (trough1_value + trough2_value) / 2

        return {
            'pattern': 'double_bottom',
            'type': 'bullish_reversal',
            'first_bottom': trough1_value,
            'second_bottom': trough2_value,
            'support': support,
            'resistance': peak,
            'current_price': current_price,
            'target': peak + (peak - support),
            'signal': 'BUY' if current_price > peak else 'WAIT'
        }
