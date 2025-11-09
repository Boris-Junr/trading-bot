"""
Trading Strategies Module

Provides base classes and pre-built strategies for trading.
"""

# Base classes and shared logic
from .base import Strategy, Signal, SignalType, Position
from .portfolio import Portfolio, Trade

# Strategy implementations (re-export for convenience)
from .implementations import MLPredictiveStrategy

__all__ = [
    # Base classes
    'Strategy',
    'Signal',
    'SignalType',
    'Position',
    'Portfolio',
    'Trade',

    # Strategies
    'MLPredictiveStrategy',
]
