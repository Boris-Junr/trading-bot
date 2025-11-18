"""
Market Data Router

Endpoints for historical market data and trading symbols.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from api.services.data_service import get_data_service
from domain.config import get_pairs_by_type, ALLOWED_SYMBOLS, AssetType

router = APIRouter(prefix="/api/market", tags=["market"])

# Service initialization (singleton)
data_service = get_data_service()


@router.get("/data")
async def get_market_data(
    symbol: str,
    timeframe: str,
    start: Optional[str] = None,
    end: Optional[str] = None
):
    """
    Get historical market data for a symbol and timeframe.

    Args:
        symbol: Trading pair symbol (e.g., BTC_USDT)
        timeframe: Candle timeframe (e.g., 1m, 5m, 1h, 1d)
        start: Start date in ISO format (optional)
        end: End date in ISO format (optional)

    Returns:
        List of OHLCV candles
    """
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None

    candles = data_service.get_market_data(
        symbol=symbol,
        timeframe=timeframe,
        start=start_dt,
        end=end_dt
    )

    return candles


@router.get("/symbols")
async def get_symbols(asset_type: str = 'all'):
    """
    Get list of available trading symbols from global trading pairs configuration.

    Args:
        asset_type: Filter by asset type - 'crypto', 'forex', 'indices', or 'all' (default)

    Returns:
        Dict with symbols list and asset_type

    Examples:
        - /api/market/symbols → All symbols
        - /api/market/symbols?asset_type=crypto → Only cryptocurrency pairs
        - /api/market/symbols?asset_type=forex → Only forex pairs
    """
    # If requesting all symbols, return everything
    if asset_type == 'all':
        return {"symbols": list(ALLOWED_SYMBOLS), "asset_type": asset_type}

    # Map request to AssetType enum
    asset_type_map = {
        'crypto': AssetType.CRYPTO,
        'forex': AssetType.FOREX,
        'indices': AssetType.INDICES
    }

    if asset_type not in asset_type_map:
        # Fallback to all symbols if invalid asset_type
        return {"symbols": list(ALLOWED_SYMBOLS), "asset_type": 'all'}

    # Get pairs for specific asset type
    pairs = get_pairs_by_type(asset_type_map[asset_type])
    symbols = [pair.symbol for pair in pairs]

    return {"symbols": symbols, "asset_type": asset_type}
