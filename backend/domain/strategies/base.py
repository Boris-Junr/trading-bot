"""
Base classes for trading strategies.

This module provides the foundation for all trading strategies:
- Strategy: Abstract base class that all strategies must implement
- Signal: Trading signal (BUY/SELL/HOLD) with metadata
- Position: Represents an open position
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import pandas as pd


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


@dataclass
class Signal:
    """
    Trading signal with metadata.

    Attributes:
        type: Signal type (BUY/SELL/HOLD/CLOSE)
        timestamp: When signal was generated
        price: Price at signal generation
        confidence: Signal confidence (0.0 to 1.0)
        size: Position size (fraction of portfolio, 0.0 to 1.0)
        metadata: Additional strategy-specific data
    """
    type: SignalType
    timestamp: datetime
    price: float
    confidence: float = 1.0
    size: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # Validate confidence
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

        # Validate size
        if not 0.0 <= self.size <= 1.0:
            raise ValueError(f"Size must be between 0 and 1, got {self.size}")


@dataclass
class Position:
    """
    Represents an open trading position.

    Attributes:
        symbol: Trading symbol
        side: 'long' or 'short'
        entry_price: Price at entry
        entry_time: Timestamp of entry
        size: Position size (shares/units)
        current_price: Current market price
        stop_loss: Stop loss price (optional)
        take_profit: Take profit price (optional)
    """
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    entry_time: datetime
    size: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss."""
        if self.side == 'long':
            return (self.current_price - self.entry_price) * self.size
        else:  # short
            return (self.entry_price - self.current_price) * self.size

    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L as decimal fraction."""
        if self.side == 'long':
            return (self.current_price - self.entry_price) / self.entry_price
        else:  # short
            return (self.entry_price - self.current_price) / self.entry_price

    def update_price(self, price: float):
        """Update current price."""
        self.current_price = price

    def should_stop_loss(self) -> bool:
        """Check if stop loss is hit."""
        if self.stop_loss is None:
            return False

        if self.side == 'long':
            return self.current_price <= self.stop_loss
        else:  # short
            return self.current_price >= self.stop_loss

    def should_take_profit(self) -> bool:
        """Check if take profit is hit."""
        if self.take_profit is None:
            return False

        if self.side == 'long':
            return self.current_price >= self.take_profit
        else:  # short
            return self.current_price <= self.take_profit


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.

    All strategies must implement:
    - generate_signal(): Generate trading signal based on market data
    - get_name(): Return strategy name
    - get_metadata(): Return strategy metadata (class method)

    Optional overrides:
    - on_position_opened(): Called when position is opened
    - on_position_closed(): Called when position is closed
    """

    def __init__(self, **params):
        """
        Initialize strategy with parameters.

        Args:
            **params: Strategy-specific parameters
        """
        self.params = params
        self.current_position: Optional[Position] = None

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on market data.

        Args:
            data: DataFrame with OHLCV data (indexed by timestamp)
                  Must have columns: open, high, low, close, volume

        Returns:
            Signal object with trading decision
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return strategy name."""
        pass

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """
        Return strategy metadata for auto-discovery.

        Returns:
            Dictionary with:
                - name: Strategy identifier (e.g., 'MLPredictive')
                - label: Human-readable name (e.g., 'ML Predictive Strategy')
                - description: Strategy description
                - requires_model: Whether strategy requires a trained model
                - category: Strategy category (e.g., 'machine_learning', 'technical', 'breakout')
                - parameters: Dict of parameter names and their default values
        """
        pass

    def on_position_opened(self, position: Position):
        """
        Called when a position is opened.

        Args:
            position: The opened position
        """
        self.current_position = position

    def on_position_closed(self, position: Position, exit_price: float, exit_time: datetime):
        """
        Called when a position is closed.

        Args:
            position: The closed position
            exit_price: Price at exit
            exit_time: Timestamp of exit
        """
        self.current_position = None

    def get_params(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.params.copy()

    def __str__(self) -> str:
        return f"{self.get_name()}({self.params})"
