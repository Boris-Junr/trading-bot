# Trading Bot Backend

Backend system for the trading bot, providing data retrieval, analysis, and trading logic.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `backend/.env` and add:
- **Alpaca** credentials (required for stock data): Get from https://alpaca.markets/
- **Binance** credentials (optional for crypto - public data works without keys): Get from https://www.binance.com/

### 3. Test the Setup

Run the example script to verify everything works:

```bash
python tests/example_fetch.py
```

Or run the 2-year historical data test:

```bash
python tests/test_historical.py
```

## Usage

### Fetching Historical Data

The `HistoricalDataFetcher` provides a unified interface for both crypto and stock data:

```python
from data import HistoricalDataFetcher

# Initialize with paper trading (default, safe for testing)
fetcher = HistoricalDataFetcher(trading_mode='paper')

# Or use live trading data (requires live API keys)
# fetcher = HistoricalDataFetcher(trading_mode='live')

# Fetch crypto data (auto-detects it's crypto)
btc_data = fetcher.fetch('BTC/USDT', timeframe='1h', limit=100)

# Fetch stock data (auto-detects it's a stock)
aapl_data = fetcher.fetch('AAPL', timeframe='1d', limit=100)

# Works with different symbol formats
eth_data = fetcher.fetch('ETHUSDT', timeframe='1h', limit=50)  # Auto-standardizes
```

### Paper vs Live Trading

The fetcher supports two trading modes for Alpaca (stocks):

- **Paper trading** (default): Uses paper trading API for testing without real money
  - Set `ALPACA_PAPERS_KEY` and `ALPACA_PAPERS_SECRET_KEY` in `backend/.env`
  - Initialize with `HistoricalDataFetcher(trading_mode='paper')`

- **Live trading**: Uses live API with real money
  - Set `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in `backend/.env`
  - Initialize with `HistoricalDataFetcher(trading_mode='live')`

**Important**: Always test your strategies with paper trading before switching to live trading!

### Parameters

- **symbol**: Trading symbol (e.g., `'BTC/USDT'`, `'AAPL'`, `'ETHUSDT'`)
- **timeframe**: Bar interval (`'1m'`, `'5m'`, `'15m'`, `'30m'`, `'1h'`, `'4h'`, `'1d'`, `'1w'`)
- **start**: Start datetime (optional, defaults to 30 days ago)
- **end**: End datetime (optional, defaults to now)
- **limit**: Maximum number of bars to fetch (optional)

### Return Format

All methods return a pandas DataFrame with columns:
- `timestamp` (index): Bar timestamp
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume

## Architecture

```
backend/
├── data/
│   ├── fetchers/           # Data fetcher implementations
│   │   ├── crypto_fetcher.py   # Crypto data via CCXT/Binance
│   │   └── stock_fetcher.py    # Stock data via Alpaca
│   ├── utils/              # Utility modules
│   │   └── symbol_detector.py  # Symbol type detection
│   └── historical.py       # Unified data fetcher interface
├── config/
│   └── settings.py         # Configuration and API keys
├── tests/                  # Test scripts and examples
│   ├── test_historical.py  # 2-year historical data test
│   └── example_fetch.py    # Usage examples
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features

### Symbol Detection
Automatically detects whether a symbol is crypto or stock:
- `'BTC/USDT'` → Crypto
- `'BTCUSDT'` → Crypto (auto-standardizes to `'BTC/USDT'`)
- `'AAPL'` → Stock

### Multi-Source Data
- **Crypto**: Uses CCXT with Binance (free, no API key needed for historical data)
- **Stocks**: Uses Alpaca (requires free API key)

### Unified Interface
Single method call works for any asset type - no need to know which API to call.

## Next Steps

- Add real-time data streaming
- Implement data caching
- Add more technical indicators
- Create backtesting framework
