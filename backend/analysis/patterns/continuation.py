"""
Continuation pattern recognition.

Patterns that suggest the current trend will continue:
- Flag: Rectangular consolidation against the trend
- Pennant: Small symmetrical triangle after sharp move
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict


class FlagPattern:
    """Detect flag continuation patterns."""

    @staticmethod
    def detect(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        window: int = 10
    ) -> Optional[Dict]:
        """
        Detect flag pattern.

        Characteristics:
        - Sharp price move (flagpole)
        - Rectangular consolidation against trend
        - Declining volume during consolidation
        - Breakout in direction of original trend

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume
            window: Lookback period

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(close) < window * 2:
            return None

        # Detect flagpole (sharp move before consolidation)
        pole_start = close.iloc[-(window*2)]
        pole_end = close.iloc[-window]
        pole_move = (pole_end - pole_start) / pole_start

        # Require significant move (>5%)
        if abs(pole_move) < 0.05:
            return None

        # Check consolidation (relatively flat price action)
        consolidation = close.tail(window)
        price_range = (consolidation.max() - consolidation.min()) / consolidation.mean()

        # Should be tight range (<3%)
        if price_range > 0.03:
            return None

        # Volume should be declining
        vol_recent = volume.tail(window)
        vol_trend = np.polyfit(range(len(vol_recent)), vol_recent, 1)[0]

        if vol_trend > 0:
            return None  # Volume not declining

        current_price = close.iloc[-1]
        trend = 'bullish' if pole_move > 0 else 'bearish'

        return {
            'pattern': 'flag',
            'type': f'{trend}_continuation',
            'flagpole_move': pole_move * 100,
            'consolidation_range': price_range * 100,
            'current_price': current_price,
            'target': pole_end + (pole_end - pole_start),  # Project flagpole length
            'signal': 'WAIT_FOR_BREAKOUT'
        }


class PennantPattern:
    """Detect pennant continuation patterns."""

    @staticmethod
    def detect(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 10
    ) -> Optional[Dict]:
        """
        Detect pennant pattern.

        Characteristics:
        - Sharp price move (pole)
        - Small converging triangle (pennant)
        - Breakout in direction of pole

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            window: Lookback period

        Returns:
            Pattern dict if found, None otherwise
        """
        if len(close) < window * 2:
            return None

        # Detect pole
        pole_start = close.iloc[-(window*2)]
        pole_end = close.iloc[-window]
        pole_move = (pole_end - pole_start) / pole_start

        # Require significant move
        if abs(pole_move) < 0.05:
            return None

        # Check for converging triangle
        recent_highs = high.tail(window)
        recent_lows = low.tail(window)

        # Simple check: price range should be tightening
        first_half_range = recent_highs.iloc[:window//2].max() - recent_lows.iloc[:window//2].min()
        second_half_range = recent_highs.iloc[window//2:].max() - recent_lows.iloc[window//2:].min()

        if second_half_range >= first_half_range:
            return None  # Not converging

        current_price = close.iloc[-1]
        trend = 'bullish' if pole_move > 0 else 'bearish'

        return {
            'pattern': 'pennant',
            'type': f'{trend}_continuation',
            'pole_move': pole_move * 100,
            'current_price': current_price,
            'target': pole_end + (pole_end - pole_start),
            'signal': 'WAIT_FOR_BREAKOUT'
        }
