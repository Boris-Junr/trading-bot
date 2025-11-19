import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional


class ParquetCache:
    """
    Local Parquet cache for normalized market data.

    Structure:
    data_cache/
    ├── stocks/
    │   ├── AAPL_1d.parquet
    │   └── TSLA_1h.parquet
    └── crypto/
        ├── BTC_USDT_1h.parquet
        └── ETH_USDT_1d.parquet
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache storage (default: backend/runtime/cache)
        """
        if cache_dir is None:
            # Default to backend/runtime/cache
            cache_dir = Path(__file__).parent.parent.parent / 'data_cache'

        self.cache_dir = cache_dir
        self.stocks_dir = cache_dir / 'stocks'
        self.crypto_dir = cache_dir / 'crypto'

        # Create directories if they don't exist
        self.stocks_dir.mkdir(parents=True, exist_ok=True)
        self.crypto_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, symbol: str, timeframe: str, asset_type: str) -> Path:
        """
        Get cache file path for symbol/timeframe.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'

        Returns:
            Path to cache file
        """
        # Clean symbol for filename (remove / and special chars)
        safe_symbol = symbol.replace('/', '_').replace(' ', '_')
        filename = f"{safe_symbol}_{timeframe}.parquet"

        if asset_type == 'crypto':
            return self.crypto_dir / filename
        else:
            return self.stocks_dir / filename

    def save(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        asset_type: str
    ) -> Path:
        """
        Save normalized DataFrame to cache.

        Args:
            df: Normalized DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'

        Returns:
            Path where data was saved

        Raises:
            ValueError: If DataFrame is empty or invalid
        """
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")

        file_path = self._get_file_path(symbol, timeframe, asset_type)

        # Save to parquet with compression
        df.to_parquet(
            file_path,
            engine='pyarrow',
            compression='snappy',
            index=True
        )

        return file_path

    def load(
        self,
        symbol: str,
        timeframe: str,
        asset_type: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load data from cache.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'
            start: Optional start datetime filter
            end: Optional end datetime filter

        Returns:
            DataFrame if found, None if not cached
        """
        file_path = self._get_file_path(symbol, timeframe, asset_type)

        if not file_path.exists():
            return None

        try:
            df = pd.read_parquet(file_path, engine='pyarrow')

            # Apply date filters if provided (ensure timezone-aware comparison)
            if start is not None:
                # Make start timezone-aware if it isn't
                if start.tzinfo is None:
                    start = start.replace(tzinfo=pd.Timestamp.now(tz='UTC').tzinfo)
                df = df[df.index >= start]

            if end is not None:
                # Make end timezone-aware if it isn't
                if end.tzinfo is None:
                    end = end.replace(tzinfo=pd.Timestamp.now(tz='UTC').tzinfo)
                df = df[df.index <= end]

            return df

        except Exception as e:
            print(f"[ParquetCache] Error loading cache: {e}")
            return None

    def exists(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """
        Check if data exists in cache.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'

        Returns:
            True if cache file exists
        """
        file_path = self._get_file_path(symbol, timeframe, asset_type)
        return file_path.exists()

    def get_date_range(
        self,
        symbol: str,
        timeframe: str,
        asset_type: str
    ) -> Optional[tuple[datetime, datetime]]:
        """
        Get date range of cached data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'

        Returns:
            Tuple of (start_date, end_date) or None if not cached
        """
        df = self.load(symbol, timeframe, asset_type)
        if df is None or df.empty:
            return None

        return (df.index.min(), df.index.max())

    def delete(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """
        Delete cached data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stock' or 'crypto'

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(symbol, timeframe, asset_type)

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def clear_all(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of files deleted
        """
        count = 0

        for file_path in self.cache_dir.rglob('*.parquet'):
            file_path.unlink()
            count += 1

        return count

    def get_cache_info(self) -> dict:
        """
        Get information about cached data.

        Returns:
            Dictionary with cache statistics
        """
        stocks = list(self.stocks_dir.glob('*.parquet'))
        crypto = list(self.crypto_dir.glob('*.parquet'))

        total_size = sum(f.stat().st_size for f in stocks + crypto)

        return {
            'total_files': len(stocks) + len(crypto),
            'stock_files': len(stocks),
            'crypto_files': len(crypto),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
