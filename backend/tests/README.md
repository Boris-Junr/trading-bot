# Test Suite Documentation

Comprehensive test suite for the trading bot, organized into unit tests and end-to-end tests.

## Directory Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── data/                      # Data fetching & storage tests
│   │   ├── test_historical.py     # Historical data fetching
│   │   ├── test_data_layer.py     # Storage layer architecture
│   │   └── test_incremental_update.py  # Smart update logic
│   ├── indicators/                # Technical indicator tests
│   │   └── test_indicators.py     # All 7 indicators (SMA, RSI, etc.)
│   └── visualization/             # Charting tests
│       └── test_visualization.py  # Candlestick chart generation
└── e2e/                           # End-to-end integration tests
    └── test_data_to_indicators.py # Full pipeline: data -> signals
```

## Running Tests

### All Tests
```bash
cd backend
python -m pytest tests/
```

### Unit Tests Only
```bash
# All unit tests
python -m pytest tests/unit/

# Specific category
python -m pytest tests/unit/data/
python -m pytest tests/unit/indicators/
python -m pytest tests/unit/visualization/
```

### E2E Tests
```bash
python -m pytest tests/e2e/
```

### Individual Tests
```bash
# Data tests
python tests/unit/data/test_historical.py
python tests/unit/data/test_data_layer.py
python tests/unit/data/test_incremental_update.py

# Indicator tests
python tests/unit/indicators/test_indicators.py

# Visualization tests
python tests/unit/visualization/test_visualization.py

# E2E test
python tests/e2e/test_data_to_indicators.py
```

## Test Categories

### Unit Tests

#### Data Tests (`unit/data/`)
- **test_historical.py**: Tests historical data fetching from multiple sources
  - Alpaca API integration
  - YFinance fallback
  - Symbol auto-detection (stocks vs crypto)
  - Accepts CLI args: `python test_historical.py AAPL 1d`

- **test_data_layer.py**: Tests storage architecture
  - Parquet storage adapter
  - Storage backend switching
  - Incremental fetch support

- **test_incremental_update.py**: Tests smart update logic
  - Only fetches missing data
  - Cache reuse optimization
  - Date range detection

#### Indicator Tests (`unit/indicators/`)
- **test_indicators.py**: Tests all 7 technical indicators
  - Trend: SMA, EMA, MACD
  - Momentum: RSI, Stochastic
  - Volatility: Bollinger Bands, ATR
  - Real market data validation

#### Visualization Tests (`unit/visualization/`)
- **test_visualization.py**: Tests chart generation
  - Candlestick charts
  - Volume bars
  - Chart export to PNG

### End-to-End Tests

#### test_data_to_indicators.py
Complete trading pipeline test:
1. **Data Fetching**: Fetch 1 year of AAPL data
2. **Indicator Calculation**: Calculate all 7 indicators
3. **Signal Generation**: Multi-indicator analysis
4. **Trading Decision**: BUY/SELL/HOLD recommendation
5. **Quality Verification**: Data integrity checks

Example output:
```
TREND ANALYSIS:
  Price vs SMA(50): ABOVE
  Golden Cross: YES
  MACD: BULLISH

MOMENTUM ANALYSIS:
  RSI: 73.25
  Status: OVERBOUGHT

OVERALL SIGNAL: HOLD @ $270.37
Confidence: 60.0%
```

## Test Data

Tests use real market data:
- **Symbol**: AAPL (Apple Inc.)
- **Timeframe**: 1d (daily)
- **Period**: 1-2 years of historical data
- **Source**: YFinance (free, no API key needed)

## Coverage

Current test coverage:
- ✅ Data fetching (stocks & crypto)
- ✅ Data storage (Parquet)
- ✅ Data normalization
- ✅ Technical indicators (7 indicators)
- ✅ Visualization (candlestick charts)
- ✅ End-to-end pipeline
- ⏳ Backtesting (coming soon)
- ⏳ Strategy testing (coming soon)

## Writing New Tests

### Unit Test Template
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_my_feature():
    \"\"\"Test description.\"\"\"
    # Arrange
    # Act
    # Assert
    pass

if __name__ == "__main__":
    test_my_feature()
```

### E2E Test Template
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data import HistoricalDataFetcher
from indicators import RSI

def test_full_workflow():
    \"\"\"Test complete workflow.\"\"\"
    # Fetch data
    fetcher = HistoricalDataFetcher()
    df = fetcher.fetch('AAPL', '1d')

    # Calculate indicators
    rsi = RSI.calculate(df['close'])

    # Verify results
    assert len(df) > 0
    assert rsi.iloc[-1] > 0

if __name__ == "__main__":
    test_full_workflow()
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Speed**: Use cached data when possible
3. **Clarity**: Clear test names and documentation
4. **Real Data**: Use actual market data for realistic tests
5. **Cleanup**: No test artifacts left behind

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No external dependencies (uses YFinance)
- Deterministic results
- Fast execution (<30s for unit tests)
- Clear pass/fail criteria

## Troubleshooting

### Tests failing due to API limits
- Use `force_refresh=False` to use cached data
- YFinance is free and doesn't require API keys

### Unicode errors on Windows
- Tests avoid Unicode characters for Windows compatibility
- Use ASCII characters in output

### Missing dependencies
```bash
pip install -r requirements.txt
```

## Next Steps

Planned test additions:
1. Backtesting framework tests
2. Strategy performance tests
3. Pattern recognition tests
4. Real-time data streaming tests
5. TimescaleDB integration tests
