"""
Storage module for market data persistence.

Supports multiple storage backends via adapter pattern:
- Parquet: Local files (PoC, backtesting, cold storage)
- TimescaleDB: PostgreSQL extension (live trading, hot data)
"""
from .cache import ParquetCache
from .base import StorageAdapter
from .parquet_adapter import ParquetStorageAdapter
from .data_layer import DataLayer

__all__ = [
    'ParquetCache',
    'StorageAdapter',
    'ParquetStorageAdapter',
    'DataLayer',
]
