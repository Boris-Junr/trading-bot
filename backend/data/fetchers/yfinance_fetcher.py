from datetime import datetime
from typing import Optional
import pandas as pd
import yfinance as yf


class YFinanceFetcher:
    """Fetches stock historical data using Yahoo Finance (free, no API key needed)."""

    TIMEFRAMES = {
        '1m': '1m',
        '2m': '2m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '1d': '1d',
        '1w': '1wk',
        '1mo': '1mo',
    }

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int]
    ) -> pd.DataFrame:
        """
        Fetch stock OHLCV data from Yahoo Finance.

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            timeframe: Bar interval ('1m', '5m', '1h', '1d', etc.)
            start: Start datetime
            end: End datetime
            limit: Maximum bars to fetch (applied after fetching)

        Returns:
            DataFrame with columns: open, high, low, close, volume (indexed by timestamp)
        """
        try:
            if timeframe not in self.TIMEFRAMES:
                raise ValueError(
                    f"Unsupported timeframe: {timeframe}. "
                    f"Supported: {', '.join(self.TIMEFRAMES.keys())}"
                )

            yf_timeframe = self.TIMEFRAMES[timeframe]

            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start,
                end=end,
                interval=yf_timeframe
            )

            if df.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Standardize column names (yfinance uses capitalized names)
            df.columns = df.columns.str.lower()

            # Keep only OHLCV columns
            df = df[['open', 'high', 'low', 'close', 'volume']]

            # Index is already timestamp
            df.index.name = 'timestamp'

            # Apply limit if specified
            if limit:
                df = df.tail(limit)

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch stock data for {symbol}: {str(e)}")
