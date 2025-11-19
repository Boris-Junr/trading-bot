from datetime import datetime, timedelta
from typing import Optional, Literal
from pathlib import Path
import pandas as pd

from .utils.symbol_detector import SymbolDetector, AssetType
from .utils.normalizer import DataNormalizer
from .fetchers.crypto_fetcher import CryptoFetcher
from .fetchers.stock_fetcher import StockFetcher
from .storage import DataLayer


class HistoricalDataFetcher:
    """
    Unified interface for fetching historical data.
    - Auto-detects symbol type (crypto/stock)
    - Normalizes data from different sources
    - Pluggable storage backend (Parquet, TimescaleDB, etc.)
    """

    def __init__(
        self,
        trading_mode: Literal['paper', 'live'] = 'paper',
        use_cache: bool = True,
        storage_type: Literal['parquet', 'timescale'] = 'parquet',
        cache_dir: Optional[Path] = None,
        connection_string: Optional[str] = None
    ):
        """
        Initialize fetcher with pluggable storage backend.

        Args:
            trading_mode: 'paper' or 'live' (for stock data via Alpaca)
            use_cache: Whether to cache data (default: True)
            storage_type: 'parquet' (local files) or 'timescale' (database)
            cache_dir: Directory for Parquet storage (optional)
            connection_string: PostgreSQL URL for TimescaleDB (required if storage_type='timescale')
        """
        self.trading_mode = trading_mode
        self.use_cache = use_cache
        self._crypto_fetcher = None
        self._stock_fetcher = None
        self._data_layer = DataLayer(
            storage_type=storage_type,
            cache_dir=cache_dir,
            connection_string=connection_string
        ) if use_cache else None

    @property
    def crypto_fetcher(self):
        """Lazy load crypto fetcher."""
        if self._crypto_fetcher is None:
            self._crypto_fetcher = CryptoFetcher()
        return self._crypto_fetcher

    @property
    def stock_fetcher(self):
        """Lazy load stock fetcher."""
        if self._stock_fetcher is None:
            self._stock_fetcher = StockFetcher(self.trading_mode)
        return self._stock_fetcher

    def fetch(
        self,
        symbol: str,
        timeframe: str = '1h',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for any symbol.

        Data flow:
        1. Check cache (if enabled and not force_refresh)
        2. Fetch from API if needed
        3. Normalize data
        4. Save to cache (if enabled)
        5. Return normalized DataFrame

        Args:
            symbol: Trading symbol ('BTC/USDT', 'AAPL', 'BTCUSDT', etc.)
            timeframe: Bar interval ('1m', '5m', '1h', '1d', etc.)
            start: Start datetime (default: 30 days ago)
            end: End datetime (default: now)
            limit: Maximum bars to fetch
            force_refresh: Skip cache and fetch fresh data

        Returns:
            Normalized DataFrame with OHLCV data indexed by timestamp
        """
        # Detect and standardize symbol
        standardized_symbol, asset_type = SymbolDetector.get_standardized_symbol(symbol)

        if asset_type == AssetType.UNKNOWN:
            raise ValueError(
                f"Could not determine asset type for: {symbol}. "
                "Use 'BTC/USDT' for crypto or 'AAPL' for stocks."
            )

        # Set default date range
        if end is None:
            end = datetime.utcnow()
        if start is None:
            start = end - timedelta(days=30)

        asset_type_str = 'crypto' if asset_type == AssetType.CRYPTO else 'stock'

        # Try cache first (if enabled and not force refresh)
        if self.use_cache and not force_refresh:
            cached_data = self._data_layer.load(standardized_symbol, timeframe, asset_type_str, start, end)
            if cached_data is not None and not cached_data.empty:
                print(f"[HistoricalDataFetcher] Loaded {len(cached_data)} bars from cache")
                return cached_data

        # Fetch from API
        print(f"[HistoricalDataFetcher] Fetching from API...")
        if asset_type == AssetType.CRYPTO:
            raw_data = self.crypto_fetcher.fetch(standardized_symbol, timeframe, start, end, limit)
            source = 'binance'  # CCXT uses Binance
        else:  # STOCK
            raw_data = self.stock_fetcher.fetch(standardized_symbol, timeframe, start, end, limit)
            source = 'yfinance'  # Will be 'alpaca' or 'yfinance' depending on what worked

        # Normalize data
        normalized_data = DataNormalizer.normalize(
            raw_data,
            source=source,
            symbol=standardized_symbol,
            timeframe=timeframe
        )

        # Save to cache (if enabled)
        if self.use_cache:
            saved = self._data_layer.save(normalized_data, standardized_symbol, timeframe, asset_type_str)
            if saved:
                print(f"[HistoricalDataFetcher] Saved {len(normalized_data)} bars to storage")

        return normalized_data

    def get_cache_info(self) -> dict:
        """Get storage statistics (for Parquet adapter)."""
        if not self.use_cache:
            return {'cache_enabled': False}
        # Only available for Parquet adapter
        if hasattr(self._data_layer.storage, 'get_info'):
            return self._data_layer.storage.get_info()
        return {'cache_enabled': True, 'storage_type': self._data_layer.storage_type}

    def get_date_range(self, symbol: str, timeframe: str) -> Optional[tuple[datetime, datetime]]:
        """Get date range of cached data for a symbol."""
        if not self.use_cache:
            return None
        standardized_symbol, asset_type = SymbolDetector.get_standardized_symbol(symbol)
        asset_type_str = 'crypto' if asset_type == AssetType.CRYPTO else 'stock'
        return self._data_layer.get_date_range(standardized_symbol, timeframe, asset_type_str)

    def update(
        self,
        symbol: str,
        timeframe: str = '1h',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Smart update: Only fetch missing data, not already cached.

        This method checks what's already in cache and only fetches
        the data that's missing, making updates efficient.

        Args:
            symbol: Trading symbol
            timeframe: Bar interval
            start: Desired start date (default: 30 days ago)
            end: Desired end date (default: now)
            limit: Maximum bars to fetch

        Returns:
            Complete DataFrame including both cached and newly fetched data
        """
        # Detect symbol type
        standardized_symbol, asset_type = SymbolDetector.get_standardized_symbol(symbol)
        asset_type_str = 'crypto' if asset_type == AssetType.CRYPTO else 'stock'

        # Set default date range
        if end is None:
            end = datetime.utcnow()
        if start is None:
            start = end - timedelta(days=30)

        if not self.use_cache:
            # No cache, just fetch normally
            return self.fetch(symbol, timeframe, start, end, limit, force_refresh=True)

        # Check what we need to fetch
        missing_range = self._data_layer.get_missing_dates(
            standardized_symbol,
            timeframe,
            asset_type_str,
            start,
            end
        )

        if missing_range is None:
            # All data is cached
            print(f"[HistoricalDataFetcher] All data cached for {symbol} ({start} to {end})")
            return self._data_layer.load(standardized_symbol, timeframe, asset_type_str, start, end)

        # Load existing cached data
        existing_data = self._data_layer.load(standardized_symbol, timeframe, asset_type_str)

        # Check if cache is corrupted or too small (less than 100 bars is suspicious)
        min_bars_threshold = 100
        if existing_data is None or existing_data.empty:
            existing_data = pd.DataFrame()
            print(f"[HistoricalDataFetcher] No existing cache found")
        elif len(existing_data) < min_bars_threshold:
            print(f"[HistoricalDataFetcher] WARNING: Cache has only {len(existing_data)} bars (corrupted?)")
            print(f"[HistoricalDataFetcher] Deleting corrupted cache and fetching full history...")
            # Delete corrupted cache
            self._data_layer.delete(standardized_symbol, timeframe, asset_type_str)
            # Fetch full range instead of incremental update
            return self.fetch(symbol, timeframe, start, end, limit, force_refresh=True)
        else:
            print(f"[HistoricalDataFetcher] Loaded {len(existing_data)} existing bars from cache")

        # Fetch missing data
        fetch_start, fetch_end = missing_range
        print(f"[HistoricalDataFetcher] Fetching missing data: {fetch_start} to {fetch_end}")

        # Fetch new data WITHOUT saving it yet (skip cache)
        if asset_type == AssetType.CRYPTO:
            raw_data = self.crypto_fetcher.fetch(standardized_symbol, timeframe, fetch_start, fetch_end, limit)
            source = 'binance'
        else:
            raw_data = self.stock_fetcher.fetch(standardized_symbol, timeframe, fetch_start, fetch_end, limit)
            source = 'yfinance'

        # Normalize new data
        new_data = DataNormalizer.normalize(raw_data, source=source, symbol=standardized_symbol, timeframe=timeframe)

        # Merge existing and new data
        if not existing_data.empty:
            combined_data = pd.concat([existing_data, new_data])
            # Remove duplicates (keep last occurrence)
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            # Sort by timestamp
            combined_data = combined_data.sort_index()
            print(f"[HistoricalDataFetcher] Merged data: {len(existing_data)} old + {len(new_data)} new = {len(combined_data)} total bars")
        else:
            combined_data = new_data
            print(f"[HistoricalDataFetcher] New cache created with {len(combined_data)} bars")

        # Save the complete merged dataset
        self._data_layer.save(combined_data, standardized_symbol, timeframe, asset_type_str)
        print(f"[HistoricalDataFetcher] Saved {len(combined_data)} bars to cache")

        # Return the requested date range
        return self._data_layer.load(standardized_symbol, timeframe, asset_type_str, start, end)
