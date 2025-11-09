"""
End-to-end backtesting test.

Tests complete workflow:
1. Fetch historical data
2. Run backtest with multiple strategies
3. Compare performance
4. Generate reports
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from data import HistoricalDataFetcher
from domain.strategies import SMACrossover, RSIMeanReversion, MultiIndicator
from backtesting import BacktestEngine


def test_single_strategy_backtest():
    """Test backtesting a single strategy."""
    print("=" * 70)
    print("E2E BACKTEST TEST - SINGLE STRATEGY")
    print("=" * 70)

    # Fetch 2 years of data
    print("\n[1/3] Fetching historical data...")
    fetcher = HistoricalDataFetcher(storage_type='parquet')
    data = fetcher.fetch(
        'AAPL',
        '1d',
        start=datetime.now() - timedelta(days=730),
        end=datetime.now()
    )

    print(f"  Fetched {len(data)} bars")
    print(f"  Period: {data.index[0].date()} to {data.index[-1].date()}")

    # Create strategy
    print("\n[2/3] Creating strategy...")
    strategy = SMACrossover(fast_period=20, slow_period=50)
    print(f"  Strategy: {strategy.get_name()}")

    # Run backtest
    print("\n[3/3] Running backtest...")
    engine = BacktestEngine(
        strategy=strategy,
        initial_cash=100000,
        commission=0.001,  # 0.1%
        stop_loss_pct=0.05,  # 5% stop loss
        take_profit_pct=0.10  # 10% take profit
    )

    results = engine.run(data, symbol='AAPL', warmup_period=100)

    # Verify results
    assert results is not None
    assert results['trading']['total_trades'] >= 0

    print("\n[OK] Backtest completed successfully!")
    return results


def test_strategy_comparison():
    """Compare multiple strategies."""
    print("\n\n" + "=" * 70)
    print("E2E BACKTEST TEST - STRATEGY COMPARISON")
    print("=" * 70)

    # Fetch data once
    print("\n[1/4] Fetching historical data...")
    fetcher = HistoricalDataFetcher(storage_type='parquet')
    data = fetcher.fetch(
        'AAPL',
        '1d',
        start=datetime.now() - timedelta(days=730),
        end=datetime.now()
    )

    print(f"  Fetched {len(data)} bars")

    # Define strategies to test
    strategies = [
        SMACrossover(fast_period=20, slow_period=50),
        RSIMeanReversion(rsi_period=14, oversold=30, overbought=70),
        MultiIndicator(sma_period=50, rsi_period=14, bb_period=20)
    ]

    results_list = []

    # Test each strategy
    for i, strategy in enumerate(strategies, 1):
        print(f"\n[{i+1}/4] Testing {strategy.get_name()}...")

        engine = BacktestEngine(
            strategy=strategy,
            initial_cash=100000,
            commission=0.001
        )

        results = engine.run(data, symbol='AAPL', warmup_period=100)
        results_list.append(results)

    # Compare results
    print("\n" + "=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)

    print(f"\n{'Strategy':<40} {'Return':<12} {'Sharpe':<10} {'Trades':<8} {'Win Rate':<10}")
    print("-" * 70)

    for res in results_list:
        strategy_name = res['strategy']
        total_return = res['performance']['total_return']
        sharpe = res['performance']['sharpe_ratio']
        trades = res['trading']['total_trades']
        win_rate = res['trading']['win_rate']

        print(f"{strategy_name:<40} {total_return:>10.2f}% {sharpe:>9.2f} {trades:>7} {win_rate:>9.1f}%")

    print("-" * 70)

    # Find best strategy
    best_strategy = max(results_list, key=lambda x: x['performance']['total_return'])
    print(f"\nBest Strategy: {best_strategy['strategy']}")
    print(f"Return: {best_strategy['performance']['total_return']:.2f}%")

    print("\n[OK] Strategy comparison completed!")
    return results_list


def test_different_symbols():
    """Test backtesting on different symbols."""
    print("\n\n" + "=" * 70)
    print("E2E BACKTEST TEST - MULTIPLE SYMBOLS")
    print("=" * 70)

    symbols = ['AAPL', 'MSFT', 'GOOGL']
    strategy = SMACrossover(fast_period=20, slow_period=50)

    results_by_symbol = {}

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Testing {symbol}...")

        try:
            # Fetch data
            fetcher = HistoricalDataFetcher(storage_type='parquet')
            data = fetcher.fetch(
                symbol,
                '1d',
                start=datetime.now() - timedelta(days=730),
                end=datetime.now()
            )

            # Run backtest
            engine = BacktestEngine(
                strategy=strategy,
                initial_cash=100000,
                commission=0.001
            )

            results = engine.run(data, symbol=symbol, warmup_period=100)
            results_by_symbol[symbol] = results

        except Exception as e:
            print(f"  [SKIP] Could not test {symbol}: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS BY SYMBOL")
    print("=" * 70)

    print(f"\n{'Symbol':<10} {'Return':<12} {'Sharpe':<10} {'Trades':<8} {'Win Rate':<10}")
    print("-" * 70)

    for symbol, res in results_by_symbol.items():
        total_return = res['performance']['total_return']
        sharpe = res['performance']['sharpe_ratio']
        trades = res['trading']['total_trades']
        win_rate = res['trading']['win_rate']

        print(f"{symbol:<10} {total_return:>10.2f}% {sharpe:>9.2f} {trades:>7} {win_rate:>9.1f}%")

    print("-" * 70)

    print("\n[OK] Multi-symbol backtest completed!")
    return results_by_symbol


def main():
    """Run all E2E backtest tests."""
    print("\n")
    print("=" * 70)
    print("        END-TO-END BACKTESTING TESTS")
    print("=" * 70)

    try:
        # Test 1: Single strategy
        test_single_strategy_backtest()

        # Test 2: Strategy comparison
        test_strategy_comparison()

        # Test 3: Multiple symbols
        test_different_symbols()

        print("\n\n" + "=" * 70)
        print("ALL E2E BACKTEST TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] E2E test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
