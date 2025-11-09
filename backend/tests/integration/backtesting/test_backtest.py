"""
Test script to run a backtest from command line
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from api.services.backtest_service import BacktestService

def main():
    print("=" * 80)
    print("MANUAL BACKTEST TEST")
    print("=" * 80)

    # Initialize backtest service
    service = BacktestService()

    # Configure backtest parameters
    strategy = 'MLPredictive'
    symbol = 'BTC/USDT'

    # Use a 7-day period to see pre-filter optimization in action (~10,000 bars)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    initial_cash = 10000.0

    # Strategy parameters
    params = {
        'timeframe': '1m',
        'min_predicted_return': 0.002,
        'confidence_threshold': 0.6,
        'prediction_window': 60,
        'risk_per_trade': 0.02,
        'use_prefilter': True,  # Enable pre-filter for 10-20x speedup
        'prefilter_threshold': 0.3  # Only call ML when setup score > 0.3
    }

    print(f"\nRunning backtest with:")
    print(f"  Strategy: {strategy}")
    print(f"  Symbol: {symbol}")
    print(f"  Date range: {start_date_str} to {end_date_str}")
    print(f"  Initial cash: ${initial_cash:,.2f}")
    print(f"  Parameters: {params}")
    print("\n" + "=" * 80)
    print("Starting backtest execution...")
    print("=" * 80 + "\n")

    # Run the backtest
    result = service.run_backtest(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date_str,
        end_date=end_date_str,
        initial_cash=initial_cash,
        **params
    )

    # Print results
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)

    if result is None:
        print("ERROR: Backtest failed!")
        return 1

    print(f"\nResult ID: {result.get('id')}")
    print(f"Symbol: {result.get('symbol')}")
    print(f"Strategy: {result.get('strategy')}")

    perf = result.get('performance', {})
    print(f"\nPerformance:")
    print(f"  Initial Cash: ${perf.get('initial_cash', 0):,.2f}")
    print(f"  Final Equity: ${perf.get('final_equity', 0):,.2f}")
    print(f"  Total Return: {perf.get('total_return', 0):.2%}")
    print(f"  Sharpe Ratio: {perf.get('sharpe_ratio', 0):.3f}")
    print(f"  Max Drawdown: {perf.get('max_drawdown', 0):.2%}")

    trading = result.get('trading', {})
    print(f"\nTrading:")
    print(f"  Total Trades: {trading.get('total_trades', 0)}")
    print(f"  Win Rate: {trading.get('win_rate', 0):.2%}")
    print(f"  Profit Factor: {trading.get('profit_factor', 0):.3f}")

    print("\n" + "=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
