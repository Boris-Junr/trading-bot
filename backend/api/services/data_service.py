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

    def get_available_symbols(self, asset_type: str = 'crypto') -> list[str]:
        """
        Get list of available trading symbols

        Args:
            asset_type: 'crypto' or 'stock'

        Returns:
            List of available symbol strings
        """
        try:
            if asset_type == 'crypto':
                # Get popular crypto pairs from Binance
                # Using a curated list of top trading pairs
                return [
                    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT',
                    'SOL/USDT', 'ADA/USDT', 'DOGE/USDT', 'DOT/USDT',
                    'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT',
                    'ATOM/USDT', 'LTC/USDT', 'BCH/USDT', 'NEAR/USDT',
                    'APT/USDT', 'ARB/USDT', 'OP/USDT', 'INJ/USDT'
                ]
            elif asset_type == 'stock':
                # Return popular US stocks
                return [
                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
                    'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
                    'WMT', 'PG', 'DIS', 'MA', 'NFLX'
                ]
            else:
                return []
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
