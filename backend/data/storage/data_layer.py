"""
Data layer manager using Strategy pattern.
Allows easy swapping between storage backends (Parquet, TimescaleDB, etc.)
"""
import pandas as pd
from datetime import datetime
from typing import Optional, Literal
from pathlib import Path
import logging

from .base import StorageAdapter
from .parquet_adapter import ParquetStorageAdapter

logger = logging.getLogger(__name__)

StorageType = Literal["parquet", "timescale"]


class DataLayer:
    """
    High-level data layer manager that abstracts storage backend.

    Usage:
        # For PoC: Use Parquet (fast, local, no infrastructure)
        data_layer = DataLayer(storage_type="parquet")

        # For production: Use TimescaleDB (real-time optimized)
        # data_layer = DataLayer(storage_type="timescale", connection_string="postgresql://...")

    Switch storage backends by changing one parameter!
    """

    def __init__(
        self,
        storage_type: StorageType = "parquet",
        cache_dir: Optional[Path] = None,
        connection_string: Optional[str] = None
    ):
        """
        Initialize data layer with chosen storage backend.

        Args:
            storage_type: "parquet" (local files) or "timescale" (database)
            cache_dir: For Parquet storage only
            connection_string: For TimescaleDB only
        """
        self.storage_type = storage_type
        self.storage: StorageAdapter = self._create_storage_adapter(
            storage_type, cache_dir, connection_string
        )
        logger.info(f"DataLayer initialized with {storage_type} storage")

    def _create_storage_adapter(
        self,
        storage_type: StorageType,
        cache_dir: Optional[Path],
        connection_string: Optional[str]
    ) -> StorageAdapter:
        """Factory method to create storage adapter."""
        if storage_type == "parquet":
            return ParquetStorageAdapter(cache_dir)

        elif storage_type == "timescale":
            if connection_string is None:
                raise ValueError("connection_string required for TimescaleDB")
            # Import only when needed (avoids dependency if not using TimescaleDB)
            from .timescale_adapter import TimescaleStorageAdapter
            return TimescaleStorageAdapter(connection_string)

        else:
            raise ValueError(f"Unknown storage type: {storage_type}")

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str,
             asset_type: str) -> bool:
        """
        Save market data to storage.

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe (e.g., '1Day')
            asset_type: 'stocks' or 'crypto'

        Returns:
            True if saved successfully
        """
        return self.storage.save(df, symbol, timeframe, asset_type)

    def load(
        self,
        symbol: str,
        timeframe: str,
        asset_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load market data from storage.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stocks' or 'crypto'
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame or None if not found
        """
        return self.storage.load(symbol, timeframe, asset_type, start_date, end_date)

    def exists(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Check if data exists in storage."""
        return self.storage.exists(symbol, timeframe, asset_type)

    def delete(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Delete data from storage."""
        return self.storage.delete(symbol, timeframe, asset_type)

    def get_date_range(
        self,
        symbol: str,
        timeframe: str,
        asset_type: str
    ) -> Optional[tuple[datetime, datetime]]:
        """
        Get date range of stored data.

        Returns:
            Tuple of (earliest_date, latest_date) or None if not found
        """
        return self.storage.get_date_range(symbol, timeframe, asset_type)

    def get_missing_dates(
        self,
        symbol: str,
        timeframe: str,
        asset_type: str,
        requested_start: datetime,
        requested_end: datetime
    ) -> Optional[tuple[datetime, datetime]]:
        """
        Calculate date ranges that are missing from storage.

        Useful for incremental updates: only fetch data we don't have.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            asset_type: 'stocks' or 'crypto'
            requested_start: Start of desired range
            requested_end: End of desired range

        Returns:
            Tuple of (fetch_start, fetch_end) if missing data, None if fully cached
        """
        if not self.exists(symbol, timeframe, asset_type):
            # No data cached at all - fetch full range
            return (requested_start, requested_end)

        cached_range = self.get_date_range(symbol, timeframe, asset_type)
        if cached_range is None:
            return (requested_start, requested_end)

        cached_start, cached_end = cached_range

        # Ensure timezone-aware comparison (make requested dates UTC aware if needed)
        import pandas as pd
        if requested_start.tzinfo is None:
            requested_start = requested_start.replace(tzinfo=pd.Timestamp.now(tz='UTC').tzinfo)
        if requested_end.tzinfo is None:
            requested_end = requested_end.replace(tzinfo=pd.Timestamp.now(tz='UTC').tzinfo)

        # Check if we need to fetch anything
        if cached_start <= requested_start and cached_end >= requested_end:
            # Fully cached
            logger.info(f"Data fully cached for {symbol} ({requested_start} to {requested_end})")
            return None

        # Check if cache can be updated incrementally or needs full refetch
        # We allow incremental update only if:
        # 1. Cache covers the START of requested range (no old gap)
        # 2. We only need newer data at the END

        needs_older_data = cached_start > requested_start
        needs_newer_data = cached_end < requested_end

        if needs_older_data and needs_newer_data:
            # Cache has gaps on BOTH ends - safer to refetch entire range
            logger.info(f"Cache has gaps on both ends. Refetching full range: {requested_start} to {requested_end}")
            return (requested_start, requested_end)
        elif needs_newer_data:
            # Only need to fetch newer data
            fetch_start = cached_end
            fetch_end = requested_end
            logger.info(f"Updating {symbol} with newer data: {fetch_start} to {fetch_end}")
            return (fetch_start, fetch_end)
        elif needs_older_data:
            # Only need to fetch older data
            fetch_start = requested_start
            fetch_end = cached_start
            logger.info(f"Updating {symbol} with older data: {fetch_start} to {fetch_end}")
            return (fetch_start, fetch_end)
        else:
            # Shouldn't reach here, but if we do, refetch everything
            logger.warning(f"Unexpected cache state for {symbol}. Refetching full range.")
            return (requested_start, requested_end)
