# Data Storage Layer Architecture

## Overview

This module implements a **pluggable storage architecture** using the Strategy Pattern, allowing easy switching between different storage backends (Parquet, TimescaleDB, etc.) without changing application code.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│         HistoricalDataFetcher (Client)              │
│  - Fetches data from APIs (Alpaca, Binance, etc.)  │
│  - Normalizes data format                           │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ uses
                   ▼
         ┌─────────────────────┐
         │     DataLayer       │
         │  (Strategy Manager) │
         └──────────┬──────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────────┐  ┌────────────────────┐
│ ParquetAdapter   │  │ TimescaleAdapter   │
│  (PoC/Backtest)  │  │  (Live Trading)    │
└──────────────────┘  └────────────────────┘
        │                       │
        ▼                       ▼
┌──────────────────┐  ┌────────────────────┐
│  Parquet Files   │  │   PostgreSQL DB    │
│  (Local Cache)   │  │  (TimescaleDB)     │
└──────────────────┘  └────────────────────┘
```

## Components

### 1. StorageAdapter (Abstract Interface)
**File:** `base.py`

Defines the contract that all storage implementations must follow:
- `save()` - Store OHLCV data
- `load()` - Retrieve data with optional date filtering
- `exists()` - Check if data exists
- `delete()` - Remove stored data
- `get_date_range()` - Get min/max dates in storage

### 2. ParquetStorageAdapter
**File:** `parquet_adapter.py`

Implementation for local Parquet file storage:
- **Best for:** PoC, backtesting, historical analysis, cold storage
- **Pros:** Fast, no infrastructure, excellent compression, works offline
- **Cons:** Not optimized for real-time queries, no concurrent writes

### 3. TimescaleStorageAdapter (Stub)
**File:** `timescale_adapter.py`

Future implementation for TimescaleDB:
- **Best for:** Live trading, real-time data, hot storage
- **Pros:** Sub-millisecond queries, continuous aggregation, retention policies
- **Cons:** Requires PostgreSQL setup, infrastructure costs

### 4. DataLayer (Strategy Manager)
**File:** `data_layer.py`

High-level manager that abstracts the storage backend:
- Factory pattern for creating adapters
- Unified API regardless of backend
- Smart features: `get_missing_dates()` for incremental updates

## Usage Examples

### PoC / Backtesting (Parquet)
```python
from data.historical import HistoricalDataFetcher

# Use Parquet storage (default)
fetcher = HistoricalDataFetcher(storage_type='parquet')

# Fetch and cache data
df = fetcher.fetch('AAPL', '1d', start_date, end_date)
```

### Production / Live Trading (TimescaleDB)
```python
from data.historical import HistoricalDataFetcher

# Use TimescaleDB for real-time data
fetcher = HistoricalDataFetcher(
    storage_type='timescale',
    connection_string='postgresql://user:pass@localhost:5432/tradingdb'
)

# Same API!
df = fetcher.fetch('BTC/USDT', '1m', start_date, end_date)
```

### Incremental Updates
```python
from data.storage import DataLayer

data_layer = DataLayer(storage_type='parquet')

# Check what date range we need to fetch
missing = data_layer.get_missing_dates(
    symbol='AAPL',
    timeframe='1d',
    asset_type='stock',
    requested_start=two_years_ago,
    requested_end=today
)

if missing:
    # Only fetch the missing data
    fetch_start, fetch_end = missing
    print(f"Need to fetch: {fetch_start} to {fetch_end}")
else:
    print("All data is cached!")
```

## Design Benefits

1. **Separation of Concerns**
   - Data fetching logic separate from storage logic
   - Easy to test each component independently

2. **Future-Proof**
   - Add new storage backends without changing application code
   - Just implement the `StorageAdapter` interface

3. **Flexibility**
   - Switch backends via configuration
   - Hybrid approach possible (Parquet + TimescaleDB)

4. **Clean Code**
   - Small, focused modules (<100 lines each)
   - Strategy Pattern for elegant backend switching

## Recommended Production Architecture

For maximum performance and cost efficiency:

```
┌─────────────────────────────────────────────┐
│         Trading Bot Application             │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
  ┌─────────┐    ┌──────────────┐
  │ Hot Data│    │  Cold Data   │
  │ (7-30d) │    │ (Historical) │
  │         │    │              │
  │TimescaleDB   │   Parquet    │
  └─────────┘    └──────────────┘
       │                │
       │                │
  Real-time        Backtesting
  Trading          Analysis
```

## Testing

Run the test suite:
```bash
cd backend
python tests/test_data_layer.py
```

Tests verify:
- Parquet adapter functionality
- Storage backend switching
- Incremental fetch logic

## Adding a New Storage Backend

1. Create new file: `your_storage_adapter.py`
2. Implement `StorageAdapter` interface
3. Add to `data_layer.py` factory method
4. Update `__init__.py` exports

Example skeleton:
```python
from .base import StorageAdapter

class YourStorageAdapter(StorageAdapter):
    def save(self, df, symbol, timeframe, asset_type):
        # Implement save logic
        pass

    def load(self, symbol, timeframe, asset_type, start_date, end_date):
        # Implement load logic
        pass

    # ... implement other methods
```

## Next Steps

1. **Phase 2:** Implement TimescaleDB adapter for live trading
2. **Phase 3:** Add data update scheduler for automatic cache refresh
3. **Phase 4:** Implement hybrid storage (hot/cold data separation)
