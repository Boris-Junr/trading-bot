"""
Trading Pairs Configuration

Global configuration for allowed trading pairs and symbols.
Focuses on high-volatility, liquid assets suitable for day trading and scalping strategies.

Categories:
- Crypto: Most volatile cryptocurrency pairs
- Forex: Major and volatile forex pairs
- Indices: Stock indices with high daily movement
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AssetType(Enum):
    """Asset types supported by the platform."""
    CRYPTO = "crypto"
    FOREX = "forex"
    INDICES = "indices"
    STOCKS = "stocks"


@dataclass
class TradingPair:
    """
    Represents a trading pair configuration.

    Attributes:
        symbol: Trading symbol (e.g., 'BTC/USDT', 'EUR/USD')
        name: Human-readable name
        asset_type: Type of asset
        base_currency: Base currency
        quote_currency: Quote currency
        min_volatility: Minimum daily volatility (as decimal, e.g., 0.02 = 2%)
        avg_daily_range: Average daily price range percentage
        liquidity_rank: Liquidity ranking (1 = highest)
        recommended_timeframes: Best timeframes for this pair
        trading_hours: Trading hours (UTC) or 24/7
        tick_size: Minimum price movement
        min_position_size: Minimum position size
    """
    symbol: str
    name: str
    asset_type: AssetType
    base_currency: str
    quote_currency: str
    min_volatility: float
    avg_daily_range: float
    liquidity_rank: int
    recommended_timeframes: List[str]
    trading_hours: str = "24/7"
    tick_size: Optional[float] = None
    min_position_size: Optional[float] = None


# ============================================================================
# CRYPTOCURRENCY PAIRS
# ============================================================================
# Most volatile and liquid crypto pairs suitable for day trading

CRYPTO_PAIRS = [
    TradingPair(
        symbol="BTC/USDT",
        name="Bitcoin / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="BTC",
        quote_currency="USDT",
        min_volatility=0.02,  # 2% minimum daily movement
        avg_daily_range=0.035,  # 3.5% average daily range
        liquidity_rank=1,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        tick_size=0.01,
        min_position_size=0.00001,
    ),
    TradingPair(
        symbol="ETH/USDT",
        name="Ethereum / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="ETH",
        quote_currency="USDT",
        min_volatility=0.025,  # 2.5%
        avg_daily_range=0.045,  # 4.5%
        liquidity_rank=2,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        tick_size=0.01,
        min_position_size=0.0001,
    ),
    TradingPair(
        symbol="BNB/USDT",
        name="Binance Coin / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="BNB",
        quote_currency="USDT",
        min_volatility=0.03,  # 3%
        avg_daily_range=0.05,  # 5%
        liquidity_rank=3,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        tick_size=0.01,
        min_position_size=0.001,
    ),
    TradingPair(
        symbol="SOL/USDT",
        name="Solana / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="SOL",
        quote_currency="USDT",
        min_volatility=0.04,  # 4%
        avg_daily_range=0.06,  # 6%
        liquidity_rank=4,
        recommended_timeframes=["1m", "5m", "15m"],
        tick_size=0.01,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="XRP/USDT",
        name="Ripple / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="XRP",
        quote_currency="USDT",
        min_volatility=0.035,  # 3.5%
        avg_daily_range=0.055,  # 5.5%
        liquidity_rank=5,
        recommended_timeframes=["1m", "5m", "15m"],
        tick_size=0.0001,
        min_position_size=1.0,
    ),
    TradingPair(
        symbol="ADA/USDT",
        name="Cardano / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="ADA",
        quote_currency="USDT",
        min_volatility=0.035,  # 3.5%
        avg_daily_range=0.055,  # 5.5%
        liquidity_rank=6,
        recommended_timeframes=["1m", "5m", "15m"],
        tick_size=0.0001,
        min_position_size=1.0,
    ),
    TradingPair(
        symbol="DOGE/USDT",
        name="Dogecoin / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="DOGE",
        quote_currency="USDT",
        min_volatility=0.05,  # 5% (highly volatile)
        avg_daily_range=0.08,  # 8%
        liquidity_rank=7,
        recommended_timeframes=["1m", "5m", "15m"],
        tick_size=0.00001,
        min_position_size=10.0,
    ),
    TradingPair(
        symbol="MATIC/USDT",
        name="Polygon / Tether",
        asset_type=AssetType.CRYPTO,
        base_currency="MATIC",
        quote_currency="USDT",
        min_volatility=0.04,  # 4%
        avg_daily_range=0.06,  # 6%
        liquidity_rank=8,
        recommended_timeframes=["1m", "5m", "15m"],
        tick_size=0.0001,
        min_position_size=1.0,
    ),
]


# ============================================================================
# FOREX PAIRS
# ============================================================================
# Major and volatile forex pairs (as mentioned in the YouTube video)

FOREX_PAIRS = [
    TradingPair(
        symbol="EUR/USD",
        name="Euro / US Dollar",
        asset_type=AssetType.FOREX,
        base_currency="EUR",
        quote_currency="USD",
        min_volatility=0.005,  # 0.5% daily
        avg_daily_range=0.008,  # 80 pips average
        liquidity_rank=1,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="24/5 (Sun 22:00 - Fri 22:00 UTC)",
        tick_size=0.00001,
        min_position_size=1000.0,  # Micro lot
    ),
    TradingPair(
        symbol="GBP/USD",
        name="British Pound / US Dollar",
        asset_type=AssetType.FOREX,
        base_currency="GBP",
        quote_currency="USD",
        min_volatility=0.007,  # 0.7% (more volatile than EUR/USD)
        avg_daily_range=0.01,  # 100 pips average
        liquidity_rank=2,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="24/5 (Sun 22:00 - Fri 22:00 UTC)",
        tick_size=0.00001,
        min_position_size=1000.0,
    ),
    TradingPair(
        symbol="USD/JPY",
        name="US Dollar / Japanese Yen",
        asset_type=AssetType.FOREX,
        base_currency="USD",
        quote_currency="JPY",
        min_volatility=0.006,  # 0.6%
        avg_daily_range=0.009,  # 90 pips average
        liquidity_rank=3,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="24/5 (Sun 22:00 - Fri 22:00 UTC)",
        tick_size=0.001,
        min_position_size=1000.0,
    ),
    TradingPair(
        symbol="GBP/JPY",
        name="British Pound / Japanese Yen",
        asset_type=AssetType.FOREX,
        base_currency="GBP",
        quote_currency="JPY",
        min_volatility=0.01,  # 1% (very volatile cross)
        avg_daily_range=0.015,  # 150 pips average
        liquidity_rank=5,
        recommended_timeframes=["1m", "5m", "15m"],
        trading_hours="24/5 (Sun 22:00 - Fri 22:00 UTC)",
        tick_size=0.001,
        min_position_size=1000.0,
    ),
    TradingPair(
        symbol="EUR/GBP",
        name="Euro / British Pound",
        asset_type=AssetType.FOREX,
        base_currency="EUR",
        quote_currency="GBP",
        min_volatility=0.006,  # 0.6%
        avg_daily_range=0.008,  # 80 pips average
        liquidity_rank=6,
        recommended_timeframes=["1m", "5m", "15m"],
        trading_hours="24/5 (Sun 22:00 - Fri 22:00 UTC)",
        tick_size=0.00001,
        min_position_size=1000.0,
    ),
]


# ============================================================================
# STOCK INDICES
# ============================================================================
# Major indices with high volatility (as mentioned in the video)

INDICES_PAIRS = [
    TradingPair(
        symbol="US30",  # Dow Jones
        name="Dow Jones Industrial Average",
        asset_type=AssetType.INDICES,
        base_currency="US30",
        quote_currency="USD",
        min_volatility=0.01,  # 1%
        avg_daily_range=0.015,  # 1.5%
        liquidity_rank=1,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="Mon-Fri 14:30-21:00 UTC (Market hours)",
        tick_size=1.0,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="NAS100",  # NASDAQ-100
        name="NASDAQ 100",
        asset_type=AssetType.INDICES,
        base_currency="NAS100",
        quote_currency="USD",
        min_volatility=0.012,  # 1.2% (tech-heavy, more volatile)
        avg_daily_range=0.02,  # 2%
        liquidity_rank=2,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="Mon-Fri 14:30-21:00 UTC (Market hours)",
        tick_size=0.25,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="SPX500",  # S&P 500
        name="S&P 500",
        asset_type=AssetType.INDICES,
        base_currency="SPX500",
        quote_currency="USD",
        min_volatility=0.01,  # 1%
        avg_daily_range=0.015,  # 1.5%
        liquidity_rank=1,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="Mon-Fri 14:30-21:00 UTC (Market hours)",
        tick_size=0.25,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="GER40",  # DAX (mentioned in video)
        name="German DAX 40",
        asset_type=AssetType.INDICES,
        base_currency="GER40",
        quote_currency="EUR",
        min_volatility=0.012,  # 1.2%
        avg_daily_range=0.018,  # 1.8% (very volatile)
        liquidity_rank=3,
        recommended_timeframes=["1m", "5m", "15m", "1h"],
        trading_hours="Mon-Fri 08:00-16:30 UTC (XETRA hours)",
        tick_size=0.5,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="UK100",  # FTSE 100
        name="FTSE 100",
        asset_type=AssetType.INDICES,
        base_currency="UK100",
        quote_currency="GBP",
        min_volatility=0.01,  # 1%
        avg_daily_range=0.014,  # 1.4%
        liquidity_rank=4,
        recommended_timeframes=["1m", "5m", "15m"],
        trading_hours="Mon-Fri 08:00-16:30 UTC (LSE hours)",
        tick_size=0.5,
        min_position_size=0.01,
    ),
    TradingPair(
        symbol="FRA40",  # CAC 40 (mentioned in video)
        name="French CAC 40",
        asset_type=AssetType.INDICES,
        base_currency="FRA40",
        quote_currency="EUR",
        min_volatility=0.011,  # 1.1%
        avg_daily_range=0.016,  # 1.6%
        liquidity_rank=5,
        recommended_timeframes=["1m", "5m", "15m"],
        trading_hours="Mon-Fri 08:00-16:30 UTC (Euronext hours)",
        tick_size=0.5,
        min_position_size=0.01,
    ),
]


# ============================================================================
# AGGREGATED CONFIGURATION
# ============================================================================

# All trading pairs by category
TRADING_PAIRS_BY_TYPE: Dict[AssetType, List[TradingPair]] = {
    AssetType.CRYPTO: CRYPTO_PAIRS,
    AssetType.FOREX: FOREX_PAIRS,
    AssetType.INDICES: INDICES_PAIRS,
}

# All trading pairs as flat list
ALL_TRADING_PAIRS: List[TradingPair] = (
    CRYPTO_PAIRS + FOREX_PAIRS + INDICES_PAIRS
)

# Symbol to TradingPair mapping for quick lookup
TRADING_PAIRS_MAP: Dict[str, TradingPair] = {
    pair.symbol: pair for pair in ALL_TRADING_PAIRS
}

# Symbols only (for quick validation)
ALLOWED_SYMBOLS: List[str] = [pair.symbol for pair in ALL_TRADING_PAIRS]

# High volatility pairs (> 3% daily range) - best for scalping
HIGH_VOLATILITY_PAIRS: List[TradingPair] = [
    pair for pair in ALL_TRADING_PAIRS
    if pair.avg_daily_range >= 0.03
]

# 24/7 trading pairs (crypto only)
ALWAYS_TRADEABLE: List[TradingPair] = [
    pair for pair in ALL_TRADING_PAIRS
    if pair.asset_type == AssetType.CRYPTO
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_pair(symbol: str) -> Optional[TradingPair]:
    """
    Get trading pair configuration by symbol.

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')

    Returns:
        TradingPair object or None if not found
    """
    return TRADING_PAIRS_MAP.get(symbol)


def is_valid_symbol(symbol: str) -> bool:
    """
    Check if a symbol is allowed for trading.

    Args:
        symbol: Trading symbol

    Returns:
        True if symbol is allowed
    """
    return symbol in ALLOWED_SYMBOLS


def get_pairs_by_type(asset_type: AssetType) -> List[TradingPair]:
    """
    Get all trading pairs of a specific type.

    Args:
        asset_type: Asset type to filter by

    Returns:
        List of trading pairs
    """
    return TRADING_PAIRS_BY_TYPE.get(asset_type, [])


def get_recommended_pairs_for_scalping(min_volatility: float = 0.03) -> List[TradingPair]:
    """
    Get trading pairs recommended for scalping strategies.

    Args:
        min_volatility: Minimum daily volatility required

    Returns:
        List of suitable trading pairs sorted by liquidity
    """
    suitable_pairs = [
        pair for pair in ALL_TRADING_PAIRS
        if pair.avg_daily_range >= min_volatility
    ]
    return sorted(suitable_pairs, key=lambda p: p.liquidity_rank)


def get_pairs_by_timeframe(timeframe: str) -> List[TradingPair]:
    """
    Get pairs that are recommended for a specific timeframe.

    Args:
        timeframe: Timeframe string (e.g., '1m', '5m', '15m')

    Returns:
        List of suitable pairs
    """
    return [
        pair for pair in ALL_TRADING_PAIRS
        if timeframe in pair.recommended_timeframes
    ]


def print_trading_pairs_summary():
    """Print a formatted summary of all trading pairs."""
    print("=" * 80)
    print("TRADING PAIRS CONFIGURATION")
    print("=" * 80)

    for asset_type in AssetType:
        pairs = get_pairs_by_type(asset_type)
        if not pairs:
            continue

        print(f"\n{asset_type.value.upper()} ({len(pairs)} pairs)")
        print("-" * 80)

        for pair in pairs:
            print(f"  {pair.symbol:15s} | Volatility: {pair.avg_daily_range*100:5.2f}% | "
                  f"Rank: {pair.liquidity_rank} | Timeframes: {', '.join(pair.recommended_timeframes)}")

    print(f"\n{'=' * 80}")
    print(f"Total pairs: {len(ALL_TRADING_PAIRS)}")
    print(f"High volatility (>3%): {len(HIGH_VOLATILITY_PAIRS)}")
    print(f"24/7 tradeable: {len(ALWAYS_TRADEABLE)}")
    print("=" * 80)


if __name__ == '__main__':
    # Print summary when run directly
    print_trading_pairs_summary()

    # Example usage
    print("\nExample queries:")
    print(f"\n1. Get BTC/USDT config:")
    btc_pair = get_pair('BTC/USDT')
    if btc_pair:
        print(f"   {btc_pair.symbol}: {btc_pair.avg_daily_range*100:.2f}% daily range")

    print(f"\n2. Recommended pairs for 1m scalping:")
    scalping_pairs = get_recommended_pairs_for_scalping(min_volatility=0.04)
    for p in scalping_pairs[:5]:
        print(f"   {p.symbol:15s} | {p.avg_daily_range*100:.2f}%")

    print(f"\n3. Crypto pairs for 5m timeframe:")
    crypto_5m = [p for p in get_pairs_by_timeframe('5m') if p.asset_type == AssetType.CRYPTO]
    for p in crypto_5m[:5]:
        print(f"   {p.symbol}")
