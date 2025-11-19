"""
Abstract storage interface for market data persistence.
Allows easy swapping between Parquet, TSDB, or other storage backends.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd


class StorageAdapter(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    def save(self, df: pd.DataFrame, symbol: str, timeframe: str,
             asset_type: str) -> bool:
        """
        Save market data to storage.

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol (e.g., 'AAPL', 'BTC/USDT')
            timeframe: Timeframe (e.g., '1Day', '1Hour')
            asset_type: 'stocks' or 'crypto'

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    def load(self, symbol: str, timeframe: str, asset_type: str,
             start_date: Optional[datetime] = None,
             end_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
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
        pass

    @abstractmethod
    def exists(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Check if data exists in storage."""
        pass

    @abstractmethod
    def delete(self, symbol: str, timeframe: str, asset_type: str) -> bool:
        """Delete data from storage."""
        pass

    @abstractmethod
    def get_date_range(self, symbol: str, timeframe: str,
                       asset_type: str) -> Optional[tuple[datetime, datetime]]:
        """
        Get the date range of stored data.

        Returns:
            Tuple of (earliest_date, latest_date) or None if not found
        """
        pass
