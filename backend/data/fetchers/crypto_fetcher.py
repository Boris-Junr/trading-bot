from datetime import datetime
from typing import Optional
import pandas as pd
import ccxt

from infrastructure.config.settings import Settings


class CryptoFetcher:
    """Fetches cryptocurrency historical data using CCXT (Binance)."""

    def __init__(self):
        self._exchange = None

    @property
    def exchange(self):
        """Lazy load CCXT exchange."""
        if self._exchange is None:
            self._exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                }
            })

            # Don't add API keys for public data (OHLCV is public)
            # API keys would be needed only for private endpoints (balances, orders, etc.)

        return self._exchange

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int]
    ) -> pd.DataFrame:
        """
        Fetch crypto OHLCV data with automatic pagination.

        Binance API limits each request to ~500 bars, so this method
        automatically paginates to fetch larger date ranges.

        Args:
            symbol: Crypto pair in CCXT format (e.g., 'BTC/USDT')
            timeframe: Bar interval ('1m', '5m', '1h', '1d', etc.)
            start: Start datetime
            end: End datetime
            limit: Maximum bars to fetch (None = fetch all in range)

        Returns:
            DataFrame with columns: open, high, low, close, volume (indexed by timestamp)
        """
        try:
            all_data = []
            since = int(start.timestamp() * 1000)
            end_ms = int(end.timestamp() * 1000)

            # Determine bars per request (Binance max is 1000, use 500 for safety)
            bars_per_request = 500 if limit is None else min(limit, 500)

            # Calculate timeframe duration in milliseconds
            timeframe_ms = self._timeframe_to_ms(timeframe)

            total_fetched = 0
            max_iterations = 100  # Safety limit to prevent infinite loops
            iteration = 0

            while since < end_ms and iteration < max_iterations:
                # Fetch batch
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=bars_per_request
                )

                if not ohlcv:
                    break

                all_data.extend(ohlcv)
                total_fetched += len(ohlcv)

                # Update since to last timestamp + 1 timeframe
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + timeframe_ms

                # Check if we've hit requested limit
                if limit and total_fetched >= limit:
                    break

                iteration += 1

            if not all_data:
                raise Exception(f"No data returned for {symbol}")

            df = pd.DataFrame(
                all_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Ensure end datetime is timezone-naive for comparison
            end_naive = end.replace(tzinfo=None) if hasattr(end, 'tzinfo') and end.tzinfo else end
            df = df[df['timestamp'] <= end_naive]

            # Remove duplicates (can happen at pagination boundaries)
            df = df.drop_duplicates(subset=['timestamp'])

            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch crypto data for {symbol}: {str(e)}")

    def _timeframe_to_ms(self, timeframe: str) -> int:
        """Convert timeframe string to milliseconds."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])

        multipliers = {
            'm': 60 * 1000,           # minutes
            'h': 60 * 60 * 1000,      # hours
            'd': 24 * 60 * 60 * 1000, # days
            'w': 7 * 24 * 60 * 60 * 1000  # weeks
        }

        return value * multipliers.get(unit, 60 * 1000)
