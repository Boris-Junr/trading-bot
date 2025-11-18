"""
Strategy Implementations

Pre-built trading strategies ready to use.

Usage:
    from domain.strategies.implementations import YourStrategy

    strategy = YourStrategy(asset_type='crypto')
"""

# Strategy implementations
from .ml_predictive_strategy import MLPredictiveStrategy
from .breakout_scalping_strategy import BreakoutScalpingStrategy

__all__ = [
    'MLPredictiveStrategy',
    'BreakoutScalpingStrategy',
]
