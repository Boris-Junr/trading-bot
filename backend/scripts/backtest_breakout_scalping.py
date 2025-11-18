"""
Backtest Breakout Scalping Strategy

Script to backtest the breakout scalping strategy from the YouTube video.
Tests on 1-minute data with various liquid assets as recommended in the video.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from datetime import datetime, timedelta
from pathlib import Path

from backtesting.engine import BacktestEngine
from data.fetchers.crypto_fetcher import CryptoFetcher
from domain.strategies.implementations import BreakoutScalpingStrategy
from domain.config import (
    get_pair,
    is_valid_symbol,
    get_best_pairs_for_strategy,
    validate_trading_request,
    AssetType,
    ALLOWED_SYMBOLS,
)


def run_breakout_scalping_backtest(
    symbol: str = 'BTC/USDT',
    timeframe: str = '1m',
    days: int = 7,  # Test on recent week
    initial_cash: float = 10000.0,
    ema_period: int = 20,
    risk_per_trade: float = 0.05,  # 5% as in video (aggressive)
    risk_reward_ratio: float = 2.0,
    range_lookback: int = 20,
    range_threshold: float = 0.003,  # 0.3% max range
):
    """
    Run backtest for breakout scalping strategy.

    Args:
        symbol: Trading pair (e.g., 'BTC/USDT', 'ETH/USDT')
        timeframe: Candle timeframe ('1m', '5m')
        days: Number of days to backtest
        initial_cash: Starting capital
        ema_period: EMA period for trend filter
        risk_per_trade: Risk percentage per trade (0.05 = 5%)
        risk_reward_ratio: Profit target as multiple of risk
        range_lookback: Candles to analyze for range detection
        range_threshold: Max range size for consolidation
    """
    print("=" * 80)
    print("BREAKOUT SCALPING STRATEGY BACKTEST")
    print("Based on YouTube video strategy")
    print("=" * 80)

    # Validate symbol
    try:
        is_valid, error, pair_config = validate_trading_request(
            symbol=symbol,
            timeframe=timeframe,
            raise_error=False
        )

        if not is_valid:
            print(f"\n[WARNING] {error}")
            print(f"\n[INFO] Recommended pairs for scalping ({timeframe}):")
            recommended = get_best_pairs_for_strategy(
                strategy_type='scalping',
                timeframe=timeframe,
                top_n=5
            )
            for i, p in enumerate(recommended, 1):
                print(f"   {i}. {p.symbol:15s} | {p.avg_daily_range*100:.2f}% volatility")
            print(f"\nContinuing with backtest anyway...\n")
        else:
            print(f"\n[OK] Symbol validated: {pair_config.name}")
            print(f"  Volatility: {pair_config.avg_daily_range*100:.2f}% daily range")
            print(f"  Liquidity Rank: #{pair_config.liquidity_rank}")

    except Exception as e:
        print(f"\n[WARNING] Could not validate symbol: {e}")
        print("Continuing with backtest anyway...\n")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"\n[CONFIG]")
    print(f"  Symbol: {symbol}")
    print(f"  Timeframe: {timeframe}")
    print(f"  Period: {start_date.date()} to {end_date.date()} ({days} days)")
    print(f"  Initial Capital: ${initial_cash:,.2f}")
    print(f"  Risk per Trade: {risk_per_trade*100}%")
    print(f"  Risk:Reward Ratio: 1:{risk_reward_ratio}")
    print(f"  EMA Period: {ema_period}")
    print(f"  Range Lookback: {range_lookback} candles")
    print(f"  Range Threshold: {range_threshold*100}%")

    # Fetch data
    print(f"\n[DATA] Fetching {timeframe} data for {symbol}...")
    fetcher = CryptoFetcher()

    try:
        df = fetcher.fetch(
            symbol=symbol,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            limit=None
        )
        print(f"[DATA] Fetched {len(df)} candles")

        if len(df) < 100:
            print(f"[ERROR] Insufficient data: {len(df)} candles (need at least 100)")
            return None

    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
        return None

    # Create strategy
    print(f"\n[STRATEGY] Initializing BreakoutScalpingStrategy...")
    strategy = BreakoutScalpingStrategy(
        ema_period=ema_period,
        range_lookback=range_lookback,
        range_threshold=range_threshold,
        breakout_confirmation=1,  # Immediate entry as in video
        risk_reward_ratio=risk_reward_ratio,
        risk_per_trade=risk_per_trade,
        atr_period=14,
        use_atr_sl=False,  # Use range-based SL as in video
        min_range_size=0.0005,
    )
    print(f"[STRATEGY] {strategy}")

    # Create backtest engine
    print(f"\n[BACKTEST] Initializing backtest engine...")
    engine = BacktestEngine(
        strategy=strategy,
        initial_cash=initial_cash,
        commission=0.001,  # 0.1% maker fee (typical crypto exchange)
        slippage=0.0005,   # 0.05% slippage
        stop_loss_pct=None,  # Strategy manages its own SL/TP
        take_profit_pct=None,
        log_to_csv=True,
        output_dir="output/backtests"
    )

    # Run backtest
    print(f"\n[BACKTEST] Running backtest...")
    print("=" * 80)

    try:
        results = engine.run(
            data=df,
            symbol=symbol,
            warmup_period=max(ema_period, range_lookback) + 10
        )

        print("\n" + "=" * 80)
        print("[BACKTEST] Completed!")
        print("=" * 80)

        # Show CSV file locations
        if 'csv_files' in results and results['csv_files']:
            print(f"\n[OUTPUT] Results saved to:")
            if 'trades' in results['csv_files']:
                print(f"  Trades CSV: {results['csv_files']['trades']}")
            if 'daily' in results['csv_files']:
                print(f"  Daily CSV: {results['csv_files']['daily']}")

        return results

    except Exception as e:
        print(f"\n[ERROR] Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point with multiple test configurations."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Backtest Breakout Scalping Strategy',
        epilog='Example: python backtest_breakout_scalping.py --symbol ETH/USDT --timeframe 5m --days 7'
    )
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                        help='Trading pair (default: BTC/USDT)')
    parser.add_argument('--timeframe', type=str, default='1m',
                        help='Candle timeframe: 1m, 5m (default: 1m)')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to backtest (default: 7)')
    parser.add_argument('--capital', type=float, default=10000.0,
                        help='Initial capital (default: 10000)')
    parser.add_argument('--risk', type=float, default=0.05,
                        help='Risk per trade as decimal (default: 0.05 = 5%%)')
    parser.add_argument('--ema', type=int, default=20,
                        help='EMA period (default: 20)')
    parser.add_argument('--rr', type=float, default=2.0,
                        help='Risk:Reward ratio (default: 2.0)')
    parser.add_argument('--list-pairs', action='store_true',
                        help='List recommended trading pairs and exit')

    args = parser.parse_args()

    # Show recommended pairs if requested
    if args.list_pairs:
        print("=" * 80)
        print("RECOMMENDED PAIRS FOR BREAKOUT SCALPING")
        print("=" * 80)

        print(f"\nTop 10 pairs for {args.timeframe} scalping:")
        print("-" * 80)
        recommended = get_best_pairs_for_strategy(
            strategy_type='scalping',
            timeframe=args.timeframe,
            top_n=10
        )
        for i, pair in enumerate(recommended, 1):
            print(f"{i:2d}. {pair.symbol:15s} | Volatility: {pair.avg_daily_range*100:5.2f}% | "
                  f"Type: {pair.asset_type.value:10s} | "
                  f"Timeframes: {', '.join(pair.recommended_timeframes)}")

        print("\n" + "=" * 80)
        print(f"Total allowed symbols: {len(ALLOWED_SYMBOLS)}")
        print("=" * 80)
        sys.exit(0)

    # Run backtest
    results = run_breakout_scalping_backtest(
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
        initial_cash=args.capital,
        ema_period=args.ema,
        risk_per_trade=args.risk,
        risk_reward_ratio=args.rr,
    )

    if results:
        print("\n[SUCCESS] Backtest completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Backtest did not complete")
        sys.exit(1)


if __name__ == '__main__':
    main()
