"""Quick test to verify pagination is working"""
from datetime import datetime, timedelta
from data import HistoricalDataFetcher

print("Testing pagination...")

fetcher = HistoricalDataFetcher(storage_type='parquet')

# Test: Fetch 7 days of 5m data (should need ~2000 bars, requiring 4 API calls)
symbol = 'ETH/USDT'
days = 7
start = datetime.now() - timedelta(days=days)
end = datetime.now()

print(f"Fetching {symbol} for last {days} days (5m bars)...")
print(f"Expected bars: ~{days * 288} (288 bars per day at 5m)")

data = fetcher.fetch(
    symbol,
    '5m',
    start=start,
    end=end,
    force_refresh=True
)

print(f"Fetched {len(data)} bars")
print(f"Date range: {data.index[0]} to {data.index[-1]}")
print(f"\nFirst 5 bars:")
print(data.head())
print(f"\nLast 5 bars:")
print(data.tail())
