"""
Trading Configuration Validation

Utilities to validate trading requests against allowed pairs and configurations.
"""

from typing import Optional, Tuple, List
from .trading_pairs import (
    get_pair,
    is_valid_symbol,
    get_recommended_pairs_for_scalping,
    AssetType,
    TradingPair,
)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_symbol(symbol: str, raise_error: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate if a symbol is allowed for trading.

    Args:
        symbol: Trading symbol to validate
        raise_error: If True, raise ValidationError on failure

    Returns:
        (is_valid, error_message)

    Raises:
        ValidationError: If raise_error=True and validation fails
    """
    if not symbol:
        error = "Symbol cannot be empty"
        if raise_error:
            raise ValidationError(error)
        return False, error

    if not is_valid_symbol(symbol):
        error = f"Symbol '{symbol}' is not in the allowed trading pairs list"
        if raise_error:
            raise ValidationError(error)
        return False, error

    return True, None


def validate_timeframe(
    symbol: str,
    timeframe: str,
    raise_error: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Validate if a timeframe is recommended for a symbol.

    Args:
        symbol: Trading symbol
        timeframe: Timeframe to validate (e.g., '1m', '5m')
        raise_error: If True, raise ValidationError on failure

    Returns:
        (is_valid, error_message)

    Raises:
        ValidationError: If raise_error=True and validation fails
    """
    pair = get_pair(symbol)
    if not pair:
        error = f"Symbol '{symbol}' not found in configuration"
        if raise_error:
            raise ValidationError(error)
        return False, error

    if timeframe not in pair.recommended_timeframes:
        error = (
            f"Timeframe '{timeframe}' is not recommended for {symbol}. "
            f"Recommended: {', '.join(pair.recommended_timeframes)}"
        )
        if raise_error:
            raise ValidationError(error)
        return False, error

    return True, None


def validate_trading_request(
    symbol: str,
    timeframe: Optional[str] = None,
    asset_type: Optional[AssetType] = None,
    raise_error: bool = True
) -> Tuple[bool, Optional[str], Optional[TradingPair]]:
    """
    Comprehensive validation for a trading request.

    Args:
        symbol: Trading symbol
        timeframe: Optional timeframe to validate
        asset_type: Optional asset type to validate
        raise_error: If True, raise ValidationError on failure

    Returns:
        (is_valid, error_message, trading_pair)

    Raises:
        ValidationError: If raise_error=True and validation fails
    """
    # Validate symbol
    is_valid, error = validate_symbol(symbol, raise_error=False)
    if not is_valid:
        if raise_error:
            raise ValidationError(error)
        return False, error, None

    # Get pair config
    pair = get_pair(symbol)
    if not pair:
        error = f"Configuration not found for symbol '{symbol}'"
        if raise_error:
            raise ValidationError(error)
        return False, error, None

    # Validate asset type if provided
    if asset_type and pair.asset_type != asset_type:
        error = (
            f"Symbol '{symbol}' is {pair.asset_type.value}, "
            f"but {asset_type.value} was expected"
        )
        if raise_error:
            raise ValidationError(error)
        return False, error, None

    # Validate timeframe if provided
    if timeframe:
        is_valid, error = validate_timeframe(symbol, timeframe, raise_error=False)
        if not is_valid:
            if raise_error:
                raise ValidationError(error)
            return False, error, pair

    return True, None, pair


def get_best_pairs_for_strategy(
    strategy_type: str,
    min_volatility: Optional[float] = None,
    timeframe: Optional[str] = None,
    asset_type: Optional[AssetType] = None,
    top_n: int = 5
) -> List[TradingPair]:
    """
    Get the best trading pairs for a specific strategy type.

    Args:
        strategy_type: Type of strategy ('scalping', 'day_trading', 'swing', etc.)
        min_volatility: Minimum volatility required
        timeframe: Filter by timeframe
        asset_type: Filter by asset type
        top_n: Number of top pairs to return

    Returns:
        List of recommended trading pairs
    """
    # Define volatility requirements by strategy type
    volatility_requirements = {
        'scalping': 0.03,  # 3% minimum for scalping
        'breakout': 0.03,  # 3% for breakout strategies
        'day_trading': 0.02,  # 2% for day trading
        'swing': 0.015,  # 1.5% for swing trading
        'momentum': 0.025,  # 2.5% for momentum
    }

    # Use provided min_volatility or strategy default
    if min_volatility is None:
        min_volatility = volatility_requirements.get(strategy_type.lower(), 0.02)

    # Get recommended pairs
    pairs = get_recommended_pairs_for_scalping(min_volatility=min_volatility)

    # Filter by asset type if provided
    if asset_type:
        pairs = [p for p in pairs if p.asset_type == asset_type]

    # Filter by timeframe if provided
    if timeframe:
        pairs = [p for p in pairs if timeframe in p.recommended_timeframes]

    # Return top N pairs
    return pairs[:top_n]


def print_validation_summary(symbol: str, timeframe: Optional[str] = None):
    """
    Print a formatted validation summary for a trading request.

    Args:
        symbol: Trading symbol
        timeframe: Optional timeframe
    """
    print(f"\n{'=' * 60}")
    print(f"VALIDATION SUMMARY: {symbol}")
    print('=' * 60)

    try:
        is_valid, error, pair = validate_trading_request(
            symbol=symbol,
            timeframe=timeframe,
            raise_error=False
        )

        if not is_valid:
            print(f"❌ INVALID: {error}")
            print('=' * 60)
            return

        print(f"✓ Symbol: {pair.symbol}")
        print(f"✓ Name: {pair.name}")
        print(f"✓ Asset Type: {pair.asset_type.value}")
        print(f"✓ Volatility: {pair.avg_daily_range * 100:.2f}% daily range")
        print(f"✓ Liquidity Rank: #{pair.liquidity_rank}")
        print(f"✓ Recommended Timeframes: {', '.join(pair.recommended_timeframes)}")
        print(f"✓ Trading Hours: {pair.trading_hours}")

        if timeframe:
            if timeframe in pair.recommended_timeframes:
                print(f"✓ Timeframe '{timeframe}': Recommended ✓")
            else:
                print(f"⚠ Timeframe '{timeframe}': Not recommended (use {', '.join(pair.recommended_timeframes)})")

    except ValidationError as e:
        print(f"❌ VALIDATION ERROR: {e}")

    print('=' * 60)


if __name__ == '__main__':
    # Test validation
    print("Testing validation utilities:\n")

    # Valid requests
    print_validation_summary('BTC/USDT', '1m')
    print_validation_summary('EUR/USD', '5m')

    # Invalid requests
    print_validation_summary('INVALID/PAIR')
    print_validation_summary('BTC/USDT', '4h')  # Not recommended timeframe

    # Get best pairs for scalping
    print("\n" + "=" * 60)
    print("BEST PAIRS FOR SCALPING (1m)")
    print("=" * 60)
    best_pairs = get_best_pairs_for_strategy(
        strategy_type='scalping',
        timeframe='1m',
        asset_type=AssetType.CRYPTO,
        top_n=5
    )
    for i, pair in enumerate(best_pairs, 1):
        print(f"{i}. {pair.symbol:15s} | {pair.avg_daily_range*100:.2f}% daily range")
