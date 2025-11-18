"""
Configuration Module

Global configuration for trading parameters, allowed pairs, and system settings.
"""

from .trading_pairs import (
    AssetType,
    TradingPair,
    ALL_TRADING_PAIRS,
    TRADING_PAIRS_MAP,
    ALLOWED_SYMBOLS,
    HIGH_VOLATILITY_PAIRS,
    ALWAYS_TRADEABLE,
    CRYPTO_PAIRS,
    FOREX_PAIRS,
    INDICES_PAIRS,
    get_pair,
    is_valid_symbol,
    get_pairs_by_type,
    get_recommended_pairs_for_scalping,
    get_pairs_by_timeframe,
)

from .validation import (
    ValidationError,
    validate_symbol,
    validate_timeframe,
    validate_trading_request,
    get_best_pairs_for_strategy,
    print_validation_summary,
)

__all__ = [
    # Trading pairs
    'AssetType',
    'TradingPair',
    'ALL_TRADING_PAIRS',
    'TRADING_PAIRS_MAP',
    'ALLOWED_SYMBOLS',
    'HIGH_VOLATILITY_PAIRS',
    'ALWAYS_TRADEABLE',
    'CRYPTO_PAIRS',
    'FOREX_PAIRS',
    'INDICES_PAIRS',
    'get_pair',
    'is_valid_symbol',
    'get_pairs_by_type',
    'get_recommended_pairs_for_scalping',
    'get_pairs_by_timeframe',
    # Validation
    'ValidationError',
    'validate_symbol',
    'validate_timeframe',
    'validate_trading_request',
    'get_best_pairs_for_strategy',
    'print_validation_summary',
]
