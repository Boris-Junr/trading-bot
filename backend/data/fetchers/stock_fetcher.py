from datetime import datetime
from typing import Optional, Literal
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from infrastructure.config.settings import Settings
from .yfinance_fetcher import YFinanceFetcher


class StockFetcher:
    """
    Fetches stock historical data.
    Primary: Alpaca (requires API key)
    Fallback: YFinance (free, no API key needed)
    """

    TIMEFRAMES = {
        '1m': TimeFrame(1, TimeFrameUnit.Minute),
        '5m': TimeFrame(5, TimeFrameUnit.Minute),
        '15m': TimeFrame(15, TimeFrameUnit.Minute),
        '30m': TimeFrame(30, TimeFrameUnit.Minute),
        '1h': TimeFrame(1, TimeFrameUnit.Hour),
        '4h': TimeFrame(4, TimeFrameUnit.Hour),
        '1d': TimeFrame(1, TimeFrameUnit.Day),
        '1w': TimeFrame(1, TimeFrameUnit.Week),
    }

    def __init__(self, trading_mode: Literal['paper', 'live'] = 'paper'):
        self.trading_mode = trading_mode
        self._alpaca_client = None
        self._yfinance_fetcher = YFinanceFetcher()
        self._use_alpaca = Settings.validate_alpaca_data_config()

    @property
    def alpaca_client(self):
        """Lazy load Alpaca client using Market Data API credentials."""
        if self._alpaca_client is None and self._use_alpaca:
            try:
                api_key, secret_key = Settings.get_alpaca_data_config()
                self._alpaca_client = StockHistoricalDataClient(api_key, secret_key)
            except ValueError:
                # Credentials not configured, will use yfinance
                self._use_alpaca = False
        return self._alpaca_client

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int]
    ) -> pd.DataFrame:
        """
        Fetch stock OHLCV data.
        Tries Alpaca first, falls back to YFinance if Alpaca fails.

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            timeframe: Bar interval ('1m', '5m', '1h', '1d', etc.)
            start: Start datetime
            end: End datetime
            limit: Maximum bars to fetch

        Returns:
            DataFrame with columns: open, high, low, close, volume (indexed by timestamp)
        """
        # Try Alpaca first if credentials are configured
        if self._use_alpaca and self.alpaca_client:
            print(f"[StockFetcher] Attempting to fetch {symbol} from Alpaca...")
            try:
                result = self._fetch_alpaca(symbol, timeframe, start, end, limit)
                print(f"[StockFetcher] Successfully fetched {len(result)} bars from Alpaca")
                return result
            except Exception as alpaca_error:
                print(f"[StockFetcher] Alpaca failed: {str(alpaca_error)}")
                print(f"[StockFetcher] Falling back to YFinance...")

        # Fallback to YFinance
        print(f"[StockFetcher] Fetching {symbol} from YFinance...")
        result = self._yfinance_fetcher.fetch(symbol, timeframe, start, end, limit)
        print(f"[StockFetcher] Successfully fetched {len(result)} bars from YFinance")
        return result

    def _fetch_alpaca(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int]
    ) -> pd.DataFrame:
        """Fetch data using Alpaca."""
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported: {', '.join(self.TIMEFRAMES.keys())}"
            )

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=self.TIMEFRAMES[timeframe],
            start=start,
            end=end
        )

        bars = self.alpaca_client.get_stock_bars(request)
        df = bars.df

        # Flatten MultiIndex if present
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0, drop=True)

        # Keep only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]
        df.index.name = 'timestamp'

        # Apply limit if specified
        if limit:
            df = df.tail(limit)

        return df
