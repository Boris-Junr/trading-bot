import pandas as pd
from datetime import datetime
from typing import Optional


class DataNormalizer:
    """
    Normalizes market data from different sources into a consistent format.

    Standard format:
    - Columns: timestamp, open, high, low, close, volume, source
    - Index: timestamp (UTC, timezone-aware)
    - Data types: float64 for prices, int64 for volume
    - Column names: lowercase
    """

    REQUIRED_COLUMNS = ['open', 'high', 'low', 'close', 'volume']

    @staticmethod
    def normalize(
        df: pd.DataFrame,
        source: str,
        symbol: str,
        timeframe: str
    ) -> pd.DataFrame:
        """
        Normalize DataFrame to standard format.

        Args:
            df: Raw DataFrame from data source
            source: Data source name ('alpaca', 'yfinance', 'binance', etc.)
            symbol: Trading symbol
            timeframe: Timeframe used

        Returns:
            Normalized DataFrame with consistent format

        Raises:
            ValueError: If required columns are missing
        """
        if df.empty:
            raise ValueError(f"Empty DataFrame received from {source}")

        # Make a copy to avoid modifying original
        normalized = df.copy()

        # Ensure column names are lowercase
        normalized.columns = normalized.columns.str.lower()

        # Validate required columns exist
        missing_cols = set(DataNormalizer.REQUIRED_COLUMNS) - set(normalized.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns from {source}: {missing_cols}")

        # Ensure timestamp is in index
        if 'timestamp' in normalized.columns:
            normalized.set_index('timestamp', inplace=True)

        # Ensure index is datetime
        if not isinstance(normalized.index, pd.DatetimeIndex):
            normalized.index = pd.to_datetime(normalized.index)

        # Ensure timezone-aware (convert to UTC if not aware)
        if normalized.index.tz is None:
            normalized.index = normalized.index.tz_localize('UTC')
        else:
            normalized.index = normalized.index.tz_convert('UTC')

        # Ensure index is named 'timestamp'
        normalized.index.name = 'timestamp'

        # Keep only required columns (drop any extra columns)
        normalized = normalized[DataNormalizer.REQUIRED_COLUMNS]

        # Ensure correct data types
        for col in ['open', 'high', 'low', 'close']:
            normalized[col] = normalized[col].astype('float64')
        normalized['volume'] = normalized['volume'].astype('int64')

        # Add metadata columns
        normalized['source'] = source
        normalized['symbol'] = symbol
        normalized['timeframe'] = timeframe

        # Sort by timestamp
        normalized.sort_index(inplace=True)

        # Remove duplicates (keep last occurrence)
        normalized = normalized[~normalized.index.duplicated(keep='last')]

        return normalized

    @staticmethod
    def validate(df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame meets normalization standards.

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check index
            if not isinstance(df.index, pd.DatetimeIndex):
                return False
            if df.index.name != 'timestamp':
                return False
            if df.index.tz is None:
                return False

            # Check required columns
            expected_cols = DataNormalizer.REQUIRED_COLUMNS + ['source', 'symbol', 'timeframe']
            if not all(col in df.columns for col in expected_cols):
                return False

            # Check data types
            for col in ['open', 'high', 'low', 'close']:
                if df[col].dtype != 'float64':
                    return False
            if df['volume'].dtype != 'int64':
                return False

            # Check for NaN values in OHLCV
            if df[DataNormalizer.REQUIRED_COLUMNS].isna().any().any():
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def merge(dfs: list[pd.DataFrame], keep: str = 'last') -> pd.DataFrame:
        """
        Merge multiple normalized DataFrames, handling duplicates.

        Args:
            dfs: List of normalized DataFrames to merge
            keep: Which duplicate to keep ('first' or 'last')

        Returns:
            Merged DataFrame

        Raises:
            ValueError: If DataFrames are not normalized
        """
        if not dfs:
            raise ValueError("No DataFrames to merge")

        # Validate all DataFrames
        for i, df in enumerate(dfs):
            if not DataNormalizer.validate(df):
                raise ValueError(f"DataFrame at index {i} is not normalized")

        # Concatenate
        merged = pd.concat(dfs, axis=0)

        # Remove duplicates
        merged = merged[~merged.index.duplicated(keep=keep)]

        # Sort by timestamp
        merged.sort_index(inplace=True)

        return merged
