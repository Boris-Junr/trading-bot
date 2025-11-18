"""
Data Service - Provides market data through the API
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.historical import HistoricalDataFetcher


class DataService:
    """Service for fetching market data"""

    def __init__(self):
        """Initialize data service with historical fetcher"""
        self.fetcher = HistoricalDataFetcher(
            trading_mode='paper',
            use_cache=True,
            storage_type='parquet'
        )

    def get_market_data(
        self,
        symbol: str,
        timeframe: str = '1m',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> list[dict]:
        """
        Fetch market data for a symbol

        Args:
            symbol: Trading symbol (e.g., 'ETH_USDT', 'AAPL')
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 1d)
            start: Start date (optional)
            end: End date (optional)
            limit: Maximum number of candles to return

        Returns:
            List of candle dictionaries
        """
        try:
            # Default to last 1000 candles if no dates provided
            if end is None:
                end = datetime.now()
            if start is None:
                # Estimate start based on timeframe
                minutes_per_candle = self._timeframe_to_minutes(timeframe)
                start = end - timedelta(minutes=minutes_per_candle * limit)

            # Fetch data
            df = self.fetcher.get_data(
                symbol=symbol,
                start_date=start,
                end_date=end,
                timeframe=timeframe
            )

            if df is None or df.empty:
                return []

            # Convert to list of dicts
            df = df.tail(limit)  # Limit results
            df_reset = df.reset_index()

            candles = []
            for _, row in df_reset.iterrows():
                candles.append({
                    'timestamp': row['timestamp'].isoformat() if 'timestamp' in row else row.name.isoformat(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0.0
                })

            return candles

        except Exception as e:
            print(f"Error fetching market data: {e}")
            return []

    def get_current_price(self, symbol: str, timeframe: str = '1m') -> Optional[float]:
        """
        Get the most recent price for a symbol

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            Current price or None
        """
        try:
            candles = self.get_market_data(symbol, timeframe, limit=1)
            if candles:
                return candles[-1]['close']
            return None
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None

    def get_available_symbols(self, asset_type: str = 'all') -> list[str]:
        """
        Get list of available trading symbols from global trading pairs configuration

        Args:
            asset_type: 'crypto', 'forex', 'indices', or 'all' (default: 'all')

        Returns:
            List of allowed symbol strings from trading pairs config
        """
        try:
            from domain.config import (
                get_pairs_by_type,
                ALLOWED_SYMBOLS,
                AssetType
            )

            # If requesting all symbols, return everything
            if asset_type == 'all':
                return list(ALLOWED_SYMBOLS)

            # Map request to AssetType enum
            asset_type_map = {
                'crypto': AssetType.CRYPTO,
                'forex': AssetType.FOREX,
                'indices': AssetType.INDICES
            }

            if asset_type not in asset_type_map:
                # Fallback to all symbols if invalid asset_type
                return list(ALLOWED_SYMBOLS)

            # Get pairs for specific asset type
            pairs = get_pairs_by_type(asset_type_map[asset_type])
            return [pair.symbol for pair in pairs]
        except Exception as e:
            print(f"Error getting available symbols: {e}")
            return []

    @staticmethod
    def _timeframe_to_minutes(timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        mapping = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
        }
        return mapping.get(timeframe, 1)


# Singleton instance
_data_service = None


def get_data_service() -> DataService:
    """Get or create data service singleton"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
