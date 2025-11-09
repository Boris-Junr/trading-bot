"""
Test script to verify training data doesn't overlap with backtest period
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from api.services.backtest_service import BacktestService

def main():
    print("=" * 80)
    print("TRAINING PERIOD VALIDATION TEST")
    print("=" * 80)

    # Initialize backtest service
    service = BacktestService()

    # Use ETH/USDT to force model training (no existing model)
    strategy = 'MLPredictive'
    symbol = 'ETH/USDT'

    # Backtest period: Nov 2-9
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

    print(f"\nBacktest Configuration:")
    print(f"  Symbol: {symbol}")
    print(f"  Backtest Period: {start_date_str} to {end_date_str}")
    print(f"\nExpected Training Period:")
    print(f"  Should end BEFORE: {start_date_str}")
    print(f"  (30 days ending 1 day before backtest start)")
    print("\n" + "=" * 80)
    print("Watch for: [TRAIN] Training data will end at...")
    print("=" * 80 + "\n")

    initial_cash = 10000.0

    # Strategy parameters - minimal for quick test
    params = {
        'timeframe': '1m',
        'min_predicted_return': 0.002,
        'confidence_threshold': 0.6,
        'prediction_window': 60,
        'risk_per_trade': 0.02,
        'use_prefilter': True,
        'prefilter_threshold': 0.3
    }

    # Run the backtest (will trigger model training)
    result = service.run_backtest(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date_str,
        end_date=end_date_str,
        initial_cash=initial_cash,
        **params
    )

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    if result is None:
        print("ERROR: Backtest failed!")
        return 1

    print("\nVerification:")
    print("  1. Check logs above for '[TRAIN] Training data will end at...'")
    print("  2. Training end date should be BEFORE backtest start date")
    print("  3. If correct, training data has NO overlap with backtest period")

    print("\n" + "=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
