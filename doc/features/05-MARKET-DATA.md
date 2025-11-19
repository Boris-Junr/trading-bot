# Market Data Management

Unified interface for fetching, caching, and managing historical market data from multiple sources (crypto and stocks) with pluggable storage backends and automatic symbol detection.

## Overview

The market data system provides:
- Automatic asset type detection (crypto vs stocks)
- Multiple data sources (CCXT/Binance for crypto, Alpaca/yFinance for stocks)
- Pluggable storage backends (Parquet, TimescaleDB)
- Intelligent caching with incremental updates
- Data normalization across different sources
- Multi-timeframe support (1m, 5m, 1h, 1d, etc.)

## Architecture

```
User Request
    ↓
Historical Data Fetcher
    ├─ Symbol Detector
    │   ├─→ BTC/USDT → Crypto
    │   ├─→ AAPL → Stock
    │   └─→ Standardize symbol format
    ↓
Check Cache (DataLayer)
    ├─→ Cache Hit → Return cached data
    └─→ Cache Miss → Fetch from API
        ↓
    Source-Specific Fetcher
        ├─ CryptoFetcher (CCXT/Binance)
        │   ├─ Automatic pagination
        │   └─ Rate limit handling
        │
        └─ StockFetcher (Alpaca/yFinance)
            ├─ Paper trading (yFinance)
            └─ Live trading (Alpaca)
        ↓
    Data Normalizer
        ├─ Standardize column names
        ├─ Convert to datetime index
        └─ Filter by date range
        ↓
    Save to Cache (DataLayer)
        ├─→ Parquet (local files)
        └─→ TimescaleDB (database)
        ↓
    Return DataFrame
```

## Backend Implementation

### Files

- **[backend/data/historical.py](../../backend/data/historical.py)** - Main unified fetcher interface
- **[backend/data/fetchers/crypto_fetcher.py](../../backend/data/fetchers/crypto_fetcher.py)** - CCXT/Binance fetcher
- **[backend/data/fetchers/stock_fetcher.py](../../backend/data/fetchers/stock_fetcher.py)** - Alpaca/yFinance fetcher
- **[backend/data/utils/symbol_detector.py](../../backend/data/utils/symbol_detector.py)** - Symbol type detection
- **[backend/data/utils/normalizer.py](../../backend/data/utils/normalizer.py)** - Data normalization
- **[backend/data/storage/data_layer.py](../../backend/data/storage/data_layer.py)** - Storage abstraction layer
- **[backend/data/storage/parquet_adapter.py](../../backend/data/storage/parquet_adapter.py)** - Parquet storage
- **[backend/data/storage/timescale_adapter.py](../../backend/data/storage/timescale_adapter.py)** - TimescaleDB storage
- **[backend/api/routers/market.py](../../backend/api/routers/market.py)** - Market data API endpoints

### Core Components

#### 1. Historical Data Fetcher

Unified interface for fetching market data regardless of asset type.

**Basic Usage:**
```python
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

# Initialize fetcher (uses Parquet storage by default)
fetcher = HistoricalDataFetcher(
    trading_mode='paper',
    use_cache=True,
    storage_type='parquet'
)

# Fetch crypto data (auto-detected)
df = fetcher.fetch(
    symbol='BTC/USDT',  # or 'BTCUSDT' or 'BTC_USDT' - all formats work
    timeframe='1h',
    start=datetime.utcnow() - timedelta(days=30),
    end=datetime.utcnow()
)

# Fetch stock data (auto-detected)
df = fetcher.fetch(
    symbol='AAPL',
    timeframe='1d',
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31)
)
```

**With TimescaleDB:**
```python
fetcher = HistoricalDataFetcher(
    storage_type='timescale',
    connection_string='postgresql://user:pass@localhost:5432/trading_db'
)

df = fetcher.fetch('BTC/USDT', '1h')
```

**Force Refresh (bypass cache):**
```python
df = fetcher.fetch(
    'ETH/USDT',
    '5m',
    force_refresh=True  # Always fetch from API
)
```

**Data Structure:**

Returned DataFrame has standardized format:
```python
                         open     high      low    close       volume
timestamp
2024-01-15 10:00:00  42150.5  42200.0  42100.0  42180.0  1234567.89
2024-01-15 11:00:00  42180.0  42250.0  42150.0  42220.0  2345678.90
2024-01-15 12:00:00  42220.0  42280.0  42200.0  42260.0  3456789.01
```

**Index:** DatetimeIndex (UTC timezone-aware)
**Columns:**
- `open`: Opening price
- `high`: Highest price in period
- `low`: Lowest price in period
- `close`: Closing price
- `volume`: Trading volume in base currency

#### 2. Symbol Detection

Automatically detects asset type and standardizes symbol format.

```python
from data.utils.symbol_detector import SymbolDetector, AssetType

# Crypto detection
symbol, asset_type = SymbolDetector.get_standardized_symbol('BTCUSDT')
# → ('BTC/USDT', AssetType.CRYPTO)

symbol, asset_type = SymbolDetector.get_standardized_symbol('BTC_USDT')
# → ('BTC/USDT', AssetType.CRYPTO)

symbol, asset_type = SymbolDetector.get_standardized_symbol('BTC/USDT')
# → ('BTC/USDT', AssetType.CRYPTO)

# Stock detection
symbol, asset_type = SymbolDetector.get_standardized_symbol('AAPL')
# → ('AAPL', AssetType.STOCK)

symbol, asset_type = SymbolDetector.get_standardized_symbol('TSLA')
# → ('TSLA', AssetType.STOCK)
```

**Detection Logic:**
1. Check against known crypto pairs (BTC, ETH, etc.)
2. Check separators (`/`, `_`, or concatenated like 'BTCUSDT')
3. Check against known stock symbols
4. Default to `AssetType.UNKNOWN` if indeterminate

#### 3. Crypto Fetcher (CCXT)

Fetches cryptocurrency data from Binance using CCXT.

```python
from data.fetchers.crypto_fetcher import CryptoFetcher
from datetime import datetime

fetcher = CryptoFetcher()

df = fetcher.fetch(
    symbol='BTC/USDT',
    timeframe='1m',
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 2),
    limit=None  # Fetch all in range
)
```

**Features:**
- **Automatic pagination**: Binance limits ~500 bars per request, automatically fetches multiple pages
- **Rate limit handling**: Built-in rate limiting via CCXT
- **Public data**: No API keys needed for OHLCV data
- **Fallback logic**: Safety limit of 100 iterations to prevent infinite loops

**Timeframes Supported:**
- `1m`, `3m`, `5m`, `15m`, `30m`
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- `1d`, `3d`, `1w`, `1M`

**Example Pagination:**
```
Request 1: 2024-01-01 00:00 → 2024-01-01 08:20 (500 bars @ 1m)
Request 2: 2024-01-01 08:21 → 2024-01-01 16:41 (500 bars @ 1m)
Request 3: 2024-01-01 16:42 → 2024-01-02 00:00 (438 bars @ 1m)
Total: 1438 bars
```

#### 4. Stock Fetcher (Alpaca/yFinance)

Fetches stock data with fallback logic.

```python
from data.fetchers.stock_fetcher import StockFetcher

# Paper trading mode (uses yFinance)
fetcher = StockFetcher(trading_mode='paper')
df = fetcher.fetch('AAPL', '1d', start, end)

# Live trading mode (uses Alpaca, falls back to yFinance)
fetcher = StockFetcher(trading_mode='live')
df = fetcher.fetch('AAPL', '1d', start, end)
```

**Source Selection:**
- **Paper mode**: Always uses yFinance (free, no API keys required)
- **Live mode**: Tries Alpaca first (requires API keys), falls back to yFinance if unavailable

**Alpaca Configuration:**

Set environment variables:
```bash
export APCA_API_KEY_ID=your_key
export APCA_API_SECRET_KEY=your_secret
```

Or use `infrastructure/config/settings.py`:
```python
ALPACA_API_KEY_ID = os.getenv('APCA_API_KEY_ID')
ALPACA_API_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
```

**Timeframes Supported:**
- yFinance: `1m`, `5m`, `15m`, `1h`, `1d`
- Alpaca: `1Min`, `5Min`, `15Min`, `1Hour`, `1Day`

#### 5. Data Storage (Pluggable Backends)

**Strategy Pattern** allows easy swapping between storage backends.

##### Parquet Storage (Default)

Fast local storage using Parquet files.

```python
from data.storage import DataLayer
from datetime import datetime

# Initialize Parquet storage
data_layer = DataLayer(
    storage_type='parquet',
    cache_dir='./cache/market_data'  # Optional, defaults to './cache/parquet'
)

# Save data
data_layer.save(
    df=df,
    symbol='BTC/USDT',
    timeframe='1h',
    asset_type='crypto'
)

# Load data
df = data_layer.load(
    symbol='BTC/USDT',
    timeframe='1h',
    asset_type='crypto',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

**File Structure:**
```
cache/parquet/
├── crypto/
│   ├── BTC_USDT_1h.parquet
│   ├── ETH_USDT_5m.parquet
│   └── ...
└── stocks/
    ├── AAPL_1d.parquet
    ├── TSLA_1h.parquet
    └── ...
```

**Advantages:**
- Fast read/write performance
- No infrastructure needed
- Columnar format (efficient storage)
- Good for PoC and development

**Incremental Updates:**

Parquet adapter automatically merges new data with existing cache:
```python
# First fetch: 2024-01-01 to 2024-01-15
df1 = fetcher.fetch('BTC/USDT', '1h', start=datetime(2024, 1, 1), end=datetime(2024, 1, 15))
# Saves to BTC_USDT_1h.parquet

# Second fetch: 2024-01-10 to 2024-01-31 (overlaps with first)
df2 = fetcher.fetch('BTC/USDT', '1h', start=datetime(2024, 1, 10), end=datetime(2024, 1, 31))
# Automatically merges with existing data, deduplicates, and saves

# Result: BTC_USDT_1h.parquet contains 2024-01-01 to 2024-01-31 (deduplicated)
```

##### TimescaleDB Storage (Production)

Time-series optimized PostgreSQL storage.

```python
from data.storage import DataLayer

# Initialize TimescaleDB storage
data_layer = DataLayer(
    storage_type='timescale',
    connection_string='postgresql://user:pass@localhost:5432/trading_db'
)

# Save/load works identically
data_layer.save(df, 'BTC/USDT', '1h', 'crypto')
df = data_layer.load('BTC/USDT', '1h', 'crypto', start, end)
```

**Database Schema:**
```sql
CREATE TABLE market_data (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (timestamp, symbol, timeframe, asset_type)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('market_data', 'timestamp');

-- Indexes for fast queries
CREATE INDEX idx_symbol_timeframe ON market_data (symbol, timeframe, timestamp DESC);
CREATE INDEX idx_asset_type ON market_data (asset_type, timestamp DESC);
```

**Advantages:**
- Real-time optimized queries
- Automatic data retention policies
- Built-in compression
- Multi-user concurrent access
- Good for production deployments

#### 6. Data Normalization

Standardizes data from different sources into uniform format.

```python
from data.utils.normalizer import DataNormalizer

# Normalize Binance data
normalized_df = DataNormalizer.normalize(
    df=raw_df,
    source='binance',
    symbol='BTC/USDT',
    timeframe='1h'
)

# Normalize yFinance data
normalized_df = DataNormalizer.normalize(
    df=raw_df,
    source='yfinance',
    symbol='AAPL',
    timeframe='1d'
)
```

**Normalization Steps:**
1. Rename columns to standard format (`open`, `high`, `low`, `close`, `volume`)
2. Convert timestamp to DatetimeIndex with UTC timezone
3. Sort by timestamp (ascending)
4. Remove duplicates
5. Filter to requested date range (if provided)

**Source-Specific Handling:**

| Source | Timestamp Format | Column Names | Timezone |
|--------|-----------------|--------------|----------|
| Binance (CCXT) | Unix milliseconds | `[timestamp, open, high, low, close, volume]` | UTC |
| yFinance | DatetimeIndex | `Open, High, Low, Close, Volume` | Local |
| Alpaca | ISO string | `open, high, low, close, volume` | US/Eastern |

Normalizer handles all these differences automatically.

### API Endpoints

#### GET /api/market/data

Get historical market data for a symbol.

**Query Parameters:**
- `symbol` (required): Trading symbol (e.g., `BTC_USDT`, `AAPL`)
- `timeframe` (required): Bar interval (`1m`, `5m`, `1h`, `1d`)
- `start` (optional): Start date (ISO format)
- `end` (optional): End date (ISO format)

**Example Request:**
```bash
curl "http://localhost:8000/api/market/data?symbol=BTC_USDT&timeframe=1h&start=2024-01-01T00:00:00&end=2024-01-31T23:59:59"
```

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T10:00:00Z",
    "open": 42150.5,
    "high": 42200.0,
    "low": 42100.0,
    "close": 42180.0,
    "volume": 1234567.89
  },
  {
    "timestamp": "2024-01-15T11:00:00Z",
    "open": 42180.0,
    "high": 42250.0,
    "low": 42150.0,
    "close": 42220.0,
    "volume": 2345678.90
  }
]
```

**Usage (Frontend):**
```typescript
import axios from 'axios'

const response = await axios.get('/api/market/data', {
  params: {
    symbol: 'BTC_USDT',
    timeframe: '1h',
    start: '2024-01-01T00:00:00',
    end: '2024-01-31T23:59:59'
  }
})

const candles = response.data
```

#### GET /api/market/symbols

Get list of available trading symbols.

**Query Parameters:**
- `asset_type` (optional): Filter by type - `crypto`, `forex`, `indices`, or `all` (default)

**Example Requests:**
```bash
# All symbols
curl "http://localhost:8000/api/market/symbols"

# Only crypto
curl "http://localhost:8000/api/market/symbols?asset_type=crypto"

# Only stocks
curl "http://localhost:8000/api/market/symbols?asset_type=stocks"
```

**Response:**
```json
{
  "symbols": [
    "BTC_USDT",
    "ETH_USDT",
    "AAPL",
    "TSLA"
  ],
  "asset_type": "all"
}
```

**Usage (Frontend):**
```typescript
import { useSymbols } from '@/composables/useSymbols'

const { symbols, loading, fetch } = useSymbols('crypto')
await fetch()

console.log(symbols.value)  // ['BTC_USDT', 'ETH_USDT', ...]
```

## Frontend Implementation

### Files

- **[frontend/src/composables/useSymbols.ts](../../frontend/src/composables/useSymbols.ts)** - Symbols fetching composable

### Symbols Composable

**Usage:**
```vue
<script setup lang="ts">
import { useSymbols } from '@/composables/useSymbols'

const { symbols, loading, error, fetch } = useSymbols('crypto')

onMounted(async () => {
  await fetch()
})
</script>

<template>
  <Select v-model="selectedSymbol">
    <option v-for="symbol in symbols" :key="symbol" :value="symbol">
      {{ symbol }}
    </option>
  </Select>
</template>
```

## Usage Examples

### Example 1: Fetch Recent Crypto Data

```python
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

# Initialize fetcher
fetcher = HistoricalDataFetcher()

# Fetch last 7 days of BTC hourly data
df = fetcher.fetch(
    symbol='BTC/USDT',
    timeframe='1h',
    start=datetime.utcnow() - timedelta(days=7),
    end=datetime.utcnow()
)

print(f"Fetched {len(df)} bars")
print(df.head())
```

### Example 2: Backfill Historical Data

```python
from data.historical import HistoricalDataFetcher
from datetime import datetime

fetcher = HistoricalDataFetcher(storage_type='parquet')

# Backfill 1 year of daily data for multiple symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'AAPL', 'TSLA']
start = datetime(2023, 1, 1)
end = datetime(2024, 1, 1)

for symbol in symbols:
    print(f"Backfilling {symbol}...")
    df = fetcher.fetch(symbol, '1d', start, end)
    print(f"  → Cached {len(df)} bars")
```

### Example 3: Real-Time Data Updates

```python
import asyncio
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

async def update_data_continuously():
    fetcher = HistoricalDataFetcher()

    while True:
        # Fetch last hour of data
        df = fetcher.fetch(
            'BTC/USDT',
            '1m',
            start=datetime.utcnow() - timedelta(hours=1),
            end=datetime.utcnow(),
            force_refresh=True  # Always get latest
        )

        latest_price = df['close'].iloc[-1]
        print(f"[{datetime.now()}] BTC/USDT: ${latest_price:,.2f}")

        await asyncio.sleep(60)  # Update every minute

# Run
asyncio.run(update_data_continuously())
```

### Example 4: Switch Storage Backend

```python
from data.historical import HistoricalDataFetcher
from datetime import datetime, timedelta

# Development: Use Parquet (fast, local)
dev_fetcher = HistoricalDataFetcher(
    storage_type='parquet',
    cache_dir='./cache/dev'
)

df = dev_fetcher.fetch('BTC/USDT', '1h')

# Production: Use TimescaleDB (scalable, concurrent)
prod_fetcher = HistoricalDataFetcher(
    storage_type='timescale',
    connection_string='postgresql://user:pass@prod-db:5432/trading'
)

df = prod_fetcher.fetch('BTC/USDT', '1h')

# Same interface, different backend!
```

### Example 5: Custom Date Ranges

```python
from data.historical import HistoricalDataFetcher
from datetime import datetime

fetcher = HistoricalDataFetcher()

# Fetch specific month
df = fetcher.fetch(
    'ETH/USDT',
    '5m',
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31, 23, 59, 59)
)

# Fetch last N bars using limit
df = fetcher.fetch(
    'ETH/USDT',
    '5m',
    limit=1000  # Last 1000 5-minute bars
)
```

## Performance Considerations

### Caching Strategy

**First Fetch (Cache Miss):**
```
Request: BTC/USDT 1h, 2024-01-01 to 2024-01-31
  ↓
Cache Miss (no file exists)
  ↓
Fetch from Binance API (~744 bars)
  ↓
Save to cache/parquet/crypto/BTC_USDT_1h.parquet
  ↓
Return DataFrame (3-5 seconds)
```

**Second Fetch (Cache Hit):**
```
Request: BTC/USDT 1h, 2024-01-15 to 2024-01-31
  ↓
Cache Hit (file exists, contains 2024-01-01 to 2024-01-31)
  ↓
Filter to requested range
  ↓
Return DataFrame (<100ms)
```

**Third Fetch (Partial Cache Hit):**
```
Request: BTC/USDT 1h, 2024-01-15 to 2024-02-15
  ↓
Partial Cache Hit (have 2024-01-01 to 2024-01-31)
  ↓
Fetch missing range (2024-02-01 to 2024-02-15) from API
  ↓
Merge with cached data
  ↓
Save updated cache (2024-01-01 to 2024-02-15)
  ↓
Return DataFrame (2-3 seconds)
```

### Rate Limits

**Binance (CCXT):**
- Weight-based rate limiting (1200 weight per minute)
- `fetch_ohlcv` uses 1 weight per request
- CCXT automatically handles rate limits via `enableRateLimit: true`
- Max 500 bars per request (automatically paginated)

**yFinance:**
- No official rate limits (community library)
- Recommended: max 2000 requests per hour per IP
- Max 7 days of 1-minute data per request

**Alpaca:**
- Free tier: 200 requests per minute
- Paid tiers: Higher limits
- Max 10,000 bars per request

### Storage Size Estimates

**Parquet Files:**

| Symbol | Timeframe | Duration | Bars | File Size |
|--------|-----------|----------|------|-----------|
| BTC/USDT | 1m | 30 days | 43,200 | ~2.5 MB |
| BTC/USDT | 1h | 1 year | 8,760 | ~500 KB |
| BTC/USDT | 1d | 5 years | 1,825 | ~100 KB |
| AAPL | 1d | 10 years | 2,520 | ~150 KB |

**TimescaleDB:**
- Similar storage requirements
- Automatic compression (50-95% reduction after 7 days)
- Indexes add ~20-30% overhead

### Query Performance

**Parquet (local):**
- Load entire file: 50-200ms (depending on size)
- Filter by date: 10-50ms (pandas filtering)
- Works well for <100MB files

**TimescaleDB:**
- Indexed query: 5-50ms
- Full table scan: 100-500ms
- Works well for TB-scale data

## Troubleshooting

### "No data returned for symbol"

**Symptoms:**
```
Exception: No data returned for BTC/USDT
```

**Causes:**
1. Invalid symbol format
2. API connectivity issues
3. Symbol not supported by exchange

**Solutions:**
```python
# Verify symbol format
from data.utils.symbol_detector import SymbolDetector
symbol, asset_type = SymbolDetector.get_standardized_symbol('BTC/USDT')
print(f"Standardized: {symbol}, Type: {asset_type}")

# Test API connectivity
from data.fetchers.crypto_fetcher import CryptoFetcher
fetcher = CryptoFetcher()
markets = fetcher.exchange.load_markets()
print(f"Available symbols: {len(markets)}")
```

### Rate Limit Errors

**Symptoms:**
```
ccxt.ExchangeError: binance rate limit exceeded
```

**Solutions:**
1. Reduce request frequency
2. Use larger timeframes (fewer bars needed)
3. Enable caching to reduce API calls

```python
# Good: Fetch once, cache for reuse
fetcher = HistoricalDataFetcher(use_cache=True)
df = fetcher.fetch('BTC/USDT', '1h')  # Cached automatically

# Bad: Fetching repeatedly without cache
fetcher = HistoricalDataFetcher(use_cache=False)
for _ in range(10):
    df = fetcher.fetch('BTC/USDT', '1h')  # 10 API calls!
```

### Missing Data Gaps

**Symptoms:**
```
Expected 1440 bars (24 hours @ 1m), got 1380 bars
```

**Causes:**
1. Exchange downtime
2. Market closure (stocks only)
3. Low liquidity (crypto pairs)

**Detection:**
```python
import pandas as pd

# Detect gaps
expected_freq = '1H'  # Expected frequency
df_resampled = df.resample(expected_freq).ffill()  # Forward-fill gaps

gaps = df_resampled[df_resampled.index.isin(df.index) == False]
print(f"Found {len(gaps)} missing bars")
print(gaps.index)
```

### Cache Corruption

**Symptoms:**
```
Exception: Failed to read Parquet file
```

**Solutions:**
```python
# Clear cache for specific symbol
import os
from pathlib import Path

cache_file = Path('./cache/parquet/crypto/BTC_USDT_1h.parquet')
if cache_file.exists():
    os.remove(cache_file)
    print(f"Deleted corrupted cache: {cache_file}")

# Re-fetch data
df = fetcher.fetch('BTC/USDT', '1h', force_refresh=True)
```

## Related Documentation

- [Backtesting System](03-BACKTESTING.md) - Uses market data for historical simulations
- [ML & Predictions](02-ML-PREDICTIONS.md) - Uses market data for model training
- [Trading Strategies](06-TRADING-STRATEGIES.md) - Consumes market data for signals
