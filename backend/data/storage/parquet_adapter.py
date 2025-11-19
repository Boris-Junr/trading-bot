"""
Parquet storage adapter implementation.
Wraps existing ParquetCache with the StorageAdapter interface.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from .base import StorageAdapter
from .cache import ParquetCache

logger = logging.getLogger(__name__)


class ParquetStorageAdapter(StorageAdapter):
    """Parquet-based storage implementation using local files."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize Parquet storage adapter.

        Args:
            cache_dir: Directory for Parquet files (default: backend/runtime/cache)
        """
        self.cache = ParquetCache(cache_dir)
        logger.info(f"ParquetStorageAdapter initialized: {self.cache.cache_dir}")

    def save(self, df: pd.DataFrame, symbol: str, timeframe: str,
             asset_type: str) -> bool:
        """Save market data to Parquet file."""
        try:
            file_path = self.cache.save(df, symbol, timeframe, asset_type)
            logger.info(f"Saved {len(df)} bars to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False

    def load(self, symbol: str, timeframe: str, asset_type: str,
             start_date: Optional[datetime] = None,
             end_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Load market data from Parquet file."""
        df = self.cache.load(symbol, timeframe, asset_type, start_date, end_date)
        if df is not None:
            logger.info(f"Loaded {len(df)} bars from cache for {symbol}")
        return df

    def exists(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Check if Parquet file exists."""
        return self.cache.exists(symbol, timeframe, asset_type)

    def delete(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Delete Parquet file."""
        result = self.cache.delete(symbol, timeframe, asset_type)
        if result:
            logger.info(f"Deleted cache for {symbol} {timeframe}")
        return result

    def get_date_range(self, symbol: str, timeframe: str,
                       asset_type: str) -> Optional[tuple[datetime, datetime]]:
        """Get date range from Parquet file."""
        return self.cache.get_date_range(symbol, timeframe, asset_type)

    def get_info(self) -> dict:
        """Get cache statistics (Parquet-specific method)."""
        return self.cache.get_cache_info()
