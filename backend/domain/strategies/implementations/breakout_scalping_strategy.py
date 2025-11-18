"""
Breakout Scalping Strategy

Based on the strategy from the YouTube video transcript.
Scalps quick movements by identifying consolidation ranges and trading breakouts
with EMA trend filter and 2:1 risk-reward ratio.

Key features:
- Range detection (consolidation zones)
- Breakout confirmation
- EMA trend filter (20-period by default)
- 2:1 risk-reward ratio
- Works best on volatile, liquid assets
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple

from domain.strategies.base import Strategy, Signal, SignalType


class BreakoutScalpingStrategy(Strategy):
    """
    Scalping strategy based on range breakouts with trend filtering.

    Entry Rules:
    1. Identify a price range (consolidation)
    2. Wait for breakout (close beyond range)
    3. Check EMA filter:
       - Long only if price > EMA
       - Short only if price < EMA
    4. Enter on breakout confirmation

    Exit Rules:
    - Stop Loss: Just inside the broken level
    - Take Profit: 2:1 risk-reward ratio
    """

    def __init__(
        self,
        ema_period: int = 20,
        range_lookback: int = 20,  # Candles to look back for range detection
        range_threshold: float = 0.003,  # Max range size (0.3% of price) to consider consolidation
        breakout_confirmation: int = 1,  # Number of candles to confirm breakout
        risk_reward_ratio: float = 2.0,  # Target profit / risk
        risk_per_trade: float = 0.05,  # 5% per trade (as in video, but aggressive)
        atr_period: int = 14,  # For volatility-based SL
        use_atr_sl: bool = False,  # Use ATR for SL instead of range boundary
        min_range_size: float = 0.0005,  # Minimum range size (0.05%) to avoid micro-ranges
        **kwargs  # Accept and ignore extra parameters (e.g., timeframe from backtest service)
    ):
        """
        Initialize Breakout Scalping Strategy.

        Args:
            ema_period: Period for EMA trend filter
            range_lookback: Number of candles to analyze for range detection
            range_threshold: Maximum price range size (as fraction) for consolidation
            breakout_confirmation: Candles needed to confirm breakout
            risk_reward_ratio: Profit target as multiple of risk
            risk_per_trade: Fraction of capital to risk per trade
            atr_period: Period for ATR calculation
            use_atr_sl: Whether to use ATR-based stop loss
            min_range_size: Minimum range size to avoid false consolidations
        """
        self.ema_period = ema_period
        self.range_lookback = range_lookback
        self.range_threshold = range_threshold
        self.breakout_confirmation = breakout_confirmation
        self.risk_reward_ratio = risk_reward_ratio
        self.risk_per_trade = risk_per_trade
        self.atr_period = atr_period
        self.use_atr_sl = use_atr_sl
        self.min_range_size = min_range_size

        # State tracking
        self.current_range: Optional[Tuple[float, float]] = None  # (low, high)
        self.range_formed_at: Optional[int] = None
        self.breakout_candles: int = 0
        self.last_breakout_direction: Optional[str] = None  # 'up' or 'down'

    def calculate_ema(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data['close'].ewm(span=period, adjust=False).mean()

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def detect_range(self, data: pd.DataFrame, current_idx: int) -> Optional[Tuple[float, float]]:
        """
        Detect if price is in a consolidation range.

        Returns:
            (range_low, range_high) if consolidation detected, None otherwise
        """
        # Need enough data
        if current_idx < self.range_lookback:
            return None

        # Get recent candles
        lookback_data = data.iloc[current_idx - self.range_lookback:current_idx]

        # Calculate range
        range_high = lookback_data['high'].max()
        range_low = lookback_data['low'].min()
        range_size = range_high - range_low
        range_mid = (range_high + range_low) / 2

        # Check if range is tight enough (consolidation)
        range_pct = range_size / range_mid if range_mid > 0 else 1.0

        if range_pct <= self.range_threshold and range_pct >= self.min_range_size:
            return (range_low, range_high)

        return None

    def detect_breakout(
        self,
        data: pd.DataFrame,
        current_idx: int,
        range_bounds: Tuple[float, float]
    ) -> Optional[str]:
        """
        Detect if price has broken out of the range.

        Args:
            data: Price data
            current_idx: Current index
            range_bounds: (low, high) range boundaries

        Returns:
            'up' for bullish breakout, 'down' for bearish breakout, None otherwise
        """
        range_low, range_high = range_bounds
        current_close = data.iloc[current_idx]['close']

        # Bullish breakout - close above range high
        if current_close > range_high:
            return 'up'

        # Bearish breakout - close below range low
        if current_close < range_low:
            return 'down'

        return None

    def check_trend_filter(self, current_price: float, ema_value: float, direction: str) -> bool:
        """
        Check if breakout direction aligns with EMA trend.

        Args:
            current_price: Current price
            ema_value: EMA value
            direction: 'up' or 'down'

        Returns:
            True if aligned with trend, False otherwise
        """
        if direction == 'up':
            # Only long if price is above EMA (uptrend)
            return current_price > ema_value
        elif direction == 'down':
            # Only short if price is below EMA (downtrend)
            return current_price < ema_value

        return False

    def calculate_position_levels(
        self,
        entry_price: float,
        direction: str,
        range_bounds: Tuple[float, float],
        atr: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels.

        Args:
            entry_price: Entry price
            direction: 'up' or 'down'
            range_bounds: (low, high) of the broken range
            atr: ATR value for volatility-based SL

        Returns:
            (stop_loss, take_profit)
        """
        range_low, range_high = range_bounds

        if self.use_atr_sl and atr is not None:
            # Use ATR-based stop loss
            if direction == 'up':
                stop_loss = entry_price - (atr * 1.5)
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * self.risk_reward_ratio)
            else:  # down
                stop_loss = entry_price + (atr * 1.5)
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * self.risk_reward_ratio)
        else:
            # Use range-based stop loss (as in video)
            if direction == 'up':
                # Long: SL just below broken resistance
                stop_loss = range_high * 0.999  # Slightly inside
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * self.risk_reward_ratio)
            else:  # down
                # Short: SL just above broken support
                stop_loss = range_low * 1.001  # Slightly inside
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * self.risk_reward_ratio)

        return (stop_loss, take_profit)

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on breakout logic.

        Args:
            data: OHLCV DataFrame with at least ema_period + range_lookback candles
                  The last row is the current candle

        Returns:
            Signal object with trading decision
        """
        # Default: HOLD
        signal_type = SignalType.HOLD
        confidence = 0.0
        metadata = {}

        current_idx = len(data) - 1
        current_timestamp = data.index[-1]
        current_price = data['close'].iloc[-1]

        # Need minimum data
        min_required = max(self.ema_period, self.range_lookback) + 5
        if len(data) < min_required:
            return Signal(
                type=signal_type,
                timestamp=current_timestamp,
                price=current_price,
                confidence=confidence,
                metadata={'reason': 'insufficient_data'}
            )

        # Calculate indicators
        ema = self.calculate_ema(data, self.ema_period)
        atr = self.calculate_atr(data, self.atr_period) if self.use_atr_sl else None

        current_ema = ema.iloc[-1]
        current_atr = atr.iloc[-1] if atr is not None else None

        # Detect or update range
        detected_range = self.detect_range(data, current_idx)

        if detected_range is not None:
            # Update current range
            if self.current_range is None or self.current_range != detected_range:
                self.current_range = detected_range
                self.range_formed_at = current_idx
                self.breakout_candles = 0
                self.last_breakout_direction = None

        # If we have a range, check for breakout
        if self.current_range is not None:
            breakout_direction = self.detect_breakout(data, current_idx, self.current_range)

            if breakout_direction is not None:
                # Track breakout confirmation
                if breakout_direction == self.last_breakout_direction:
                    self.breakout_candles += 1
                else:
                    self.last_breakout_direction = breakout_direction
                    self.breakout_candles = 1

                # Check if we have enough confirmation candles
                if self.breakout_candles >= self.breakout_confirmation:
                    # Check trend filter
                    trend_aligned = self.check_trend_filter(
                        current_price,
                        current_ema,
                        breakout_direction
                    )

                    if trend_aligned:
                        # Calculate levels
                        stop_loss, take_profit = self.calculate_position_levels(
                            current_price,
                            breakout_direction,
                            self.current_range,
                            current_atr
                        )

                        # Generate signal
                        if breakout_direction == 'up':
                            signal_type = SignalType.BUY
                        else:
                            signal_type = SignalType.SELL

                        # Calculate confidence based on:
                        # 1. How far from range (stronger breakout = higher confidence)
                        # 2. Trend alignment strength
                        range_low, range_high = self.current_range
                        range_size = range_high - range_low

                        if breakout_direction == 'up':
                            breakout_strength = (current_price - range_high) / range_size if range_size > 0 else 0
                            trend_strength = (current_price - current_ema) / current_ema if current_ema > 0 else 0
                        else:
                            breakout_strength = (range_low - current_price) / range_size if range_size > 0 else 0
                            trend_strength = (current_ema - current_price) / current_ema if current_ema > 0 else 0

                        # Normalize confidence to 0-1
                        confidence = min(0.9, 0.5 + (breakout_strength * 2) + (abs(trend_strength) * 2))

                        metadata = {
                            'entry_price': current_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'range_low': range_low,
                            'range_high': range_high,
                            'ema': current_ema,
                            'breakout_direction': breakout_direction,
                            'breakout_strength': breakout_strength,
                            'trend_strength': trend_strength,
                            'risk_amount': abs(current_price - stop_loss),
                            'reward_amount': abs(take_profit - current_price),
                            'risk_reward_ratio': self.risk_reward_ratio
                        }

                        # Reset range after taking signal
                        self.current_range = None
                        self.range_formed_at = None
                        self.breakout_candles = 0
                        self.last_breakout_direction = None
                    else:
                        # Breakout against trend - ignore
                        metadata = {
                            'reason': 'breakout_against_trend',
                            'breakout_direction': breakout_direction,
                            'price': current_price,
                            'ema': current_ema
                        }
                else:
                    # Waiting for confirmation
                    metadata = {
                        'reason': 'awaiting_breakout_confirmation',
                        'breakout_candles': self.breakout_candles,
                        'required_candles': self.breakout_confirmation
                    }
            else:
                # Price still in range
                metadata = {
                    'reason': 'price_in_range',
                    'range': self.current_range
                }
        else:
            # No range detected
            metadata = {
                'reason': 'no_range_detected',
                'price': current_price,
                'ema': current_ema
            }

        return Signal(
            type=signal_type,
            timestamp=current_timestamp,
            price=current_price,
            confidence=confidence,
            metadata=metadata
        )

    def get_position_size(self, signal: Signal, portfolio_value: float, current_price: float) -> float:
        """
        Calculate position size based on risk management.

        Uses fixed percentage risk per trade (as in video: 5% per trade).
        Position size = (Portfolio Value * Risk %) / Risk Amount

        Args:
            signal: Trading signal with stop loss in metadata
            portfolio_value: Current portfolio value
            current_price: Current asset price

        Returns:
            Position size (number of units to trade)
        """
        if signal.signal_type == SignalType.HOLD:
            return 0.0

        # Get stop loss from metadata
        stop_loss = signal.metadata.get('stop_loss', 0.0)
        if stop_loss == 0.0:
            return 0.0

        # Calculate risk per unit
        risk_per_unit = abs(current_price - stop_loss)
        if risk_per_unit == 0.0:
            return 0.0

        # Calculate position size
        risk_amount = portfolio_value * self.risk_per_trade
        position_size = risk_amount / risk_per_unit

        return position_size

    def get_name(self) -> str:
        """Return strategy name."""
        return "BreakoutScalpingStrategy"

    @classmethod
    def get_metadata(cls) -> dict:
        """Return strategy metadata for auto-discovery."""
        return {
            'name': 'BreakoutScalping',
            'label': 'Breakout Scalping Strategy',
            'description': 'Range breakout strategy with EMA trend filter and 2:1 risk-reward ratio, based on YouTube trading video',
            'requires_model': False,
            'category': 'breakout',
            'parameters': {
                'ema_period': {'type': 'int', 'default': 20, 'description': 'EMA period for trend filter'},
                'range_lookback': {'type': 'int', 'default': 20, 'description': 'Candles to analyze for range detection'},
                'range_threshold': {'type': 'float', 'default': 0.003, 'description': 'Max range size (0.3%)'},
                'breakout_confirmation': {'type': 'int', 'default': 1, 'description': 'Candles for breakout confirmation'},
                'risk_reward_ratio': {'type': 'float', 'default': 2.0, 'description': 'Risk:Reward ratio'},
                'risk_per_trade': {'type': 'float', 'default': 0.05, 'description': 'Risk per trade (5%)'},
                'atr_period': {'type': 'int', 'default': 14, 'description': 'ATR period'},
                'use_atr_sl': {'type': 'bool', 'default': False, 'description': 'Use ATR for stop loss'},
                'min_range_size': {'type': 'float', 'default': 0.0005, 'description': 'Minimum range size (0.05%)'}
            }
        }

    def __str__(self) -> str:
        return f"BreakoutScalping(EMA={self.ema_period}, RR={self.risk_reward_ratio}:1, Risk={self.risk_per_trade*100}%)"
