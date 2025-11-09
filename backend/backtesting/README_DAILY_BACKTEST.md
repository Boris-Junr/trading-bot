# Daily Backtesting

Day-by-day backtesting with comprehensive CSV logging for strategy comparison and analysis.

## Overview

The `BacktestEngine` includes built-in daily tracking capabilities:

1. **Day-by-day performance tracking** - Daily P&L, cumulative returns
2. **Detailed CSV logging** - Trades with indicator values, daily summaries
3. **Strategy comparison** - Log parameters for easy comparison

Perfect for **daily trading bots** that need to analyze performance on a per-day basis.

## Features

### Daily Performance Tracking
- Daily P&L and return percentage
- Cumulative performance over time
- Trades per day with win/loss breakdown
- Positive/negative day statistics
- Best/worst day identification

### CSV Logging

#### Trades CSV (`trades_*.csv`)
Every trade logged with:
- Entry/exit timestamps and prices
- P&L and P&L percentage
- Hold duration (hours)
- Exit reason (take_profit, stop_loss, trailing_stop, reversal, time_limit)
- **Indicator values at entry:**
  - RSI, MACD histogram
  - EMA fast/slow
  - Bollinger Bands width and position
  - Stochastic K
  - ATR
  - Volume spike (true/false)
- **Signal metadata:**
  - Signal score (0-100)
  - Confidence level
  - Signals met (list of conditions)
- **Strategy parameters:**
  - min_score, take_profit_pct, stop_loss_pct
  - trailing_stop_trigger, trailing_stop_distance
  - asset_type, period settings

#### Daily CSV (`daily_*.csv`)
Daily summary with:
- Date and day number
- Daily P&L and return %
- Cumulative P&L and return %
- Current equity
- Trades count, wins, losses
- Daily win rate
- Largest win/loss for the day
- Strategy name and symbol

## Usage

### Basic Example

```python
from backtesting import BacktestEngine
from strategies.implementations import MomentumScalper
from data import HistoricalDataFetcher
from datetime import datetime, timedelta

# Fetch data
fetcher = HistoricalDataFetcher()
data = fetcher.fetch(
    'TSLA',
    '5m',
    start=datetime.now() - timedelta(days=14),
    end=datetime.now()
)

# Create strategy
strategy = MomentumScalper(asset_type='stock', min_score=55)

# Run backtest with daily tracking and CSV logging
engine = BacktestEngine(
    strategy=strategy,
    initial_cash=100000,
    commission=0.001,
    log_to_csv=True,
    output_dir='output/backtests'
)

results = engine.run(data, symbol='TSLA', warmup_period=50)

# Access daily performance
daily_df = results['daily_performance']
print(daily_df[['date', 'daily_return', 'cumulative_return', 'trades']])

# CSV files location
csv_files = results['csv_files']
print(f"Trades: {csv_files['trades']}")
print(f"Daily: {csv_files['daily']}")
```

### Multi-Symbol Comparison

```python
symbols = ['TSLA', 'NVDA', 'AAPL']
all_results = {}

for symbol in symbols:
    data = fetcher.fetch(symbol, '5m', start, end)

    # Same strategy for all symbols
    strategy = MomentumScalper(asset_type='stock', min_score=55)
    engine = BacktestEngine(strategy, initial_cash=100000, log_to_csv=True)

    results = engine.run(data, symbol=symbol)
    all_results[symbol] = results

# Compare CSV files to see which symbol/strategy works best
```

### Strategy Parameter Comparison

```python
min_scores = [50, 55, 60, 65, 70]

for min_score in min_scores:
    strategy = MomentumScalper(asset_type='stock', min_score=min_score)
    engine = BacktestEngine(strategy, initial_cash=100000, log_to_csv=True)

    results = engine.run(data, symbol='TSLA')

    # Each test generates separate CSV files with parameters logged
    # Compare CSV files to find optimal min_score
```

## A/B Testing and Parameter Comparison

All backtest runs are appended to **two cumulative CSV files**:
- `output/backtests/backtest_trades.csv`: All trades from all runs
- `output/backtests/backtest_daily.csv`: All daily summaries from all runs

Each run has a unique `run_id` (timestamp) allowing easy comparison.

### Example: Finding Best Parameters

```python
import pandas as pd

# Load all backtest results
daily_df = pd.read_csv('output/backtests/backtest_daily.csv')

# Group by run_id to get final performance of each backtest
final_performance = daily_df.groupby('run_id').last()

# Sort by cumulative return to find best configuration
best_runs = final_performance.sort_values('cumulative_return_pct', ascending=False)

print("Top 5 Best Backtests:")
print(best_runs[['strategy', 'symbol', 'cumulative_return_pct', 'min_score',
                 'take_profit_pct', 'stop_loss_pct']].head())

# Find best min_score parameter
trades_df = pd.read_csv('output/backtests/backtest_trades.csv')
performance_by_min_score = trades_df.groupby('min_score').agg({
    'pnl': 'sum',
    'pnl_pct': 'mean',
    'trade_id': 'count'
})
print("\nPerformance by min_score:")
print(performance_by_min_score)
```

### Running Multiple Parameter Tests

```python
# Test different min_score values
for min_score in [50, 55, 60, 65, 70]:
    strategy = MomentumScalper(asset_type='stock', min_score=min_score)
    engine = BacktestEngine(strategy, initial_cash=100000, log_to_csv=True)
    engine.run(data, symbol='TSLA')

# All results now in backtest_trades.csv and backtest_daily.csv
# Compare them to find optimal min_score
```

## Output Format

### Console Output

```
======================================================================
DAILY PERFORMANCE SUMMARY
======================================================================

Day   Date         Daily P&L    Daily %    Cum %      Trades
----------------------------------------------------------------------
1     2025-10-27   $0           +0.00%     +0.00%     0
2     2025-10-28   $56          +0.06%     +0.06%     1
3     2025-10-29   $0           +0.00%     +0.06%     0
4     2025-10-30   $0           +0.00%     +0.06%     0
5     2025-10-31   $-264        -0.26%     -0.21%     1
----------------------------------------------------------------------

Positive Days: 1/5 (20.0%)
Average Daily Return: -0.04%
Best Day: 2025-10-28 (+0.06%)
Worst Day: 2025-10-31 (-0.26%)

CSV Files Generated:
  Appending to: output/backtests/backtest_trades.csv
  Appending to: output/backtests/backtest_daily.csv
  Run ID: 20251103_141523
```

### CSV Files

All runs are appended to cumulative files in `output/backtests/`:
- `backtest_trades.csv`: All trades from all runs with run_id
- `backtest_daily.csv`: All daily summaries from all runs with run_id

Each run is identified by a unique `run_id` (timestamp) column.

## Analyzing Results

### Using Pandas

```python
import pandas as pd

# Load cumulative trades CSV
trades_df = pd.read_csv('output/backtests/backtest_trades.csv')

# Filter to specific run or strategy
latest_run = trades_df['run_id'].max()
run_trades = trades_df[trades_df['run_id'] == latest_run]

# Analyze winning trades
winners = run_trades[run_trades['pnl'] > 0]
print(f"Winning trades: {len(winners)}")
print(f"Average RSI on winning entries: {winners['entry_rsi'].mean():.2f}")
print(f"Average hold time: {winners['hold_hours'].mean():.2f} hours")

# Find best entry conditions
print("\nBest entry signals:")
print(winners['signals_met'].value_counts())

# Load cumulative daily CSV
daily_df = pd.read_csv('output/backtests/backtest_daily.csv')
run_daily = daily_df[daily_df['run_id'] == latest_run]

# Plot cumulative performance
import matplotlib.pyplot as plt
plt.plot(run_daily['day_num'], run_daily['cumulative_return_pct'])
plt.xlabel('Day')
plt.ylabel('Cumulative Return %')
plt.title('Daily Cumulative Performance')
plt.show()
```

### Comparing Strategies

```python
# Load cumulative daily CSV
daily_df = pd.read_csv('output/backtests/backtest_daily.csv')

# Get final performance for each run
final_performance = daily_df.groupby('run_id').last()

# Filter to specific strategies or symbols
strategy1_runs = final_performance[final_performance['strategy'].str.contains('MomentumScalper_stock_55')]
strategy2_runs = final_performance[final_performance['strategy'].str.contains('MomentumScalper_stock_60')]

# Compare average returns
print(f"Strategy 1 avg return: {strategy1_runs['cumulative_return_pct'].mean():.2f}%")
print(f"Strategy 2 avg return: {strategy2_runs['cumulative_return_pct'].mean():.2f}%")

# Compare consistency (average positive day %)
all_daily = daily_df[daily_df['run_id'].isin(strategy1_runs.index)]
positive_rate = len(all_daily[all_daily['daily_pnl'] > 0]) / len(all_daily) * 100
print(f"Strategy 1 positive days: {positive_rate:.1f}%")
```

## Key Metrics

### Daily Metrics
- **Daily Return %**: Return for single day (day's P&L / starting equity)
- **Cumulative Return %**: Total return since start
- **Daily Win Rate**: % of winning trades for the day
- **Positive Days**: Days with net positive P&L

### Trade Metrics
- **Hold Hours**: Duration of trade in hours
- **Entry Indicators**: All technical indicator values at trade entry
- **Signal Score**: Strategy's confidence score (0-100)
- **Signals Met**: Which conditions triggered the entry

## Benefits for Daily Trading Bots

1. **Performance Attribution**: See exactly which days are profitable
2. **Parameter Optimization**: Compare CSV files to find best settings
3. **Risk Management**: Identify days with large losses
4. **Pattern Recognition**: Find common indicators in winning trades
5. **Strategy Validation**: Ensure strategy works across multiple days
6. **Reproducibility**: CSV files provide complete audit trail

## Notes

- CSV files include all strategy parameters for easy comparison
- Trades logged with full indicator context for analysis
- Daily summaries enable day-by-day performance review
- Perfect for optimizing daily trading strategies
- Use with 5-minute or 15-minute bars for intraday trading

## Example: Finding Optimal Strategy

```python
# Test multiple configurations
configs = [
    {'min_score': 50, 'max_hold_hours': 12},
    {'min_score': 55, 'max_hold_hours': 24},
    {'min_score': 60, 'max_hold_hours': 24},
]

results_summary = []

for config in configs:
    strategy = MomentumScalper(**config)
    engine = BacktestEngine(strategy, initial_cash=100000, log_to_csv=True)
    results = engine.run(data, symbol='TSLA')

    daily_df = results['daily_performance']

    results_summary.append({
        'config': config,
        'final_return': daily_df['cumulative_return'].iloc[-1],
        'positive_days': len(daily_df[daily_df['daily_pnl'] > 0]) / len(daily_df),
        'avg_daily_return': daily_df['daily_return'].mean(),
        'max_daily_loss': daily_df['daily_return'].min()
    })

# Find best configuration
best = max(results_summary, key=lambda x: x['final_return'])
print(f"Best config: {best['config']}")
print(f"Final return: {best['final_return']:.2f}%")
print(f"Positive days: {best['positive_days']*100:.1f}%")
```

## See Also

- [BacktestEngine](README.md) - Standard backtesting
- [Strategy Framework](../strategies/README.md) - Creating strategies
- [CSV Logger](csv_logger.py) - CSV logging implementation
