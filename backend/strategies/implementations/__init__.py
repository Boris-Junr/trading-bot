"""
Strategy Implementations

Pre-built trading strategies ready to use.

Usage:
    from strategies.implementations import YourStrategy

    strategy = YourStrategy(asset_type='crypto')
"""

# Strategy implementations
from .ml_predictive_strategy import MLPredictiveStrategy

__all__ = [
    'MLPredictiveStrategy',
]
