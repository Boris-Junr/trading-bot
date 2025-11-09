"""
Quick analysis of optimization results to find configurations achieving 1-2% daily profit
"""
import pandas as pd
from pathlib import Path

# Load cumulative results
csv_path = Path('output/backtests/backtest_daily.csv')

if not csv_path.exists():
    print("No results found yet")
    exit(1)

# Load all daily data
daily_df = pd.read_csv(csv_path)

# Get final performance for each run
final_performance = daily_df.groupby('run_id').agg({
    'cumulative_return_pct': 'last',
    'strategy': 'first',
    'symbol': 'first',
    'min_score': 'first',
    'take_profit_pct': 'first',
    'stop_loss_pct': 'first',
    'asset_type': 'first',
    'daily_return_pct': 'mean',  # Average daily return across all days
    'trades_count': 'sum',
}).reset_index()

# Filter to profitable runs
profitable = final_performance[final_performance['cumulative_return_pct'] > 0].copy()

if profitable.empty:
    print("No profitable runs yet")
    exit(0)

print(f"\n{'='*80}")
print(f"OPTIMIZATION RESULTS ANALYSIS")
print(f"{'='*80}")
print(f"\nTotal runs: {len(final_performance)}")
print(f"Profitable runs: {len(profitable)} ({len(profitable)/len(final_performance)*100:.1f}%)")

# Sort by average daily return
profitable_sorted = profitable.sort_values('daily_return_pct', ascending=False)

print(f"\n{'='*80}")
print(f"TOP 20 CONFIGURATIONS BY AVERAGE DAILY RETURN")
print(f"{'='*80}")
print(f"{'Symbol':<12} {'Score':<6} {'TP%':<6} {'SL%':<6} {'Daily%':<8} {'Total%':<8} {'Trades':<7}")
print(f"{'-'*80}")

for idx, row in profitable_sorted.head(20).iterrows():
    print(f"{row['symbol']:<12} {row['min_score']:<6.0f} {row['take_profit_pct']*100:<6.1f} "
          f"{row['stop_loss_pct']*100:<6.1f} {row['daily_return_pct']:<8.2f} "
          f"{row['cumulative_return_pct']:<8.2f} {row['trades_count']:<7.0f}")

# Find configurations meeting 1-2% daily target
target_configs = profitable_sorted[(profitable_sorted['daily_return_pct'] >= 1.0) &
                                  (profitable_sorted['daily_return_pct'] <= 2.5)]

print(f"\n{'='*80}")
print(f"CONFIGURATIONS ACHIEVING 1-2% DAILY TARGET: {len(target_configs)}")
print(f"{'='*80}")

if len(target_configs) > 0:
    print(f"\n{'Symbol':<12} {'Score':<6} {'TP%':<6} {'SL%':<6} {'Daily%':<8} {'Total%':<8} {'Trades':<7}")
    print(f"{'-'*80}")
    for idx, row in target_configs.iterrows():
        print(f"{row['symbol']:<12} {row['min_score']:<6.0f} {row['take_profit_pct']*100:<6.1f} "
              f"{row['stop_loss_pct']*100:<6.1f} {row['daily_return_pct']:<8.2f} "
              f"{row['cumulative_return_pct']:<8.2f} {row['trades_count']:<7.0f}")

    # Best config
    best = target_configs.iloc[0]
    print(f"\n{'='*80}")
    print(f"BEST CONFIGURATION FOR 1-2% DAILY TARGET")
    print(f"{'='*80}")
    print(f"Symbol: {best['symbol']}")
    print(f"Strategy: {best['strategy']}")
    print(f"Min Score: {best['min_score']:.0f}")
    print(f"Take Profit: {best['take_profit_pct']*100:.1f}%")
    print(f"Stop Loss: {best['stop_loss_pct']*100:.1f}%")
    print(f"Average Daily Return: {best['daily_return_pct']:.2f}%")
    print(f"Total Return: {best['cumulative_return_pct']:.2f}%")
    print(f"Total Trades: {best['trades_count']:.0f}")
else:
    best = profitable_sorted.iloc[0]
    print(f"\nNo configurations hit 1-2% daily target yet")
    print(f"\nBest daily return achieved: {best['daily_return_pct']:.2f}%")
    print(f"Symbol: {best['symbol']}")
    print(f"Min Score: {best['min_score']:.0f}")
    print(f"TP/SL: {best['take_profit_pct']*100:.1f}% / {best['stop_loss_pct']*100:.1f}%")
    print(f"\nRECOMMENDATIONS TO HIT TARGET:")
    print(f"  1. Lower min_score to 30-35 (allow more trades)")
    print(f"  2. Test on ultra-volatile assets (DOGE, SHIB, meme stocks)")
    print(f"  3. Increase position sizing beyond 90%")
    print(f"  4. Test 1-minute bars for more opportunities")

print(f"\n{'='*80}")
