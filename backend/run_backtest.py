"""
Run Backtest

Script to run backtests from scenario JSON files.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from backtesting.engine import BacktestEngine
from data.fetchers.crypto_fetcher import CryptoFetcher
from strategies.implementations import MLPredictiveStrategy


def load_scenario(scenario_file: str) -> dict:
    """Load backtest scenario from JSON file."""
    with open(scenario_file, 'r') as f:
        return json.load(f)


def create_strategy(strategy_config: dict):
    """Create strategy instance from configuration."""
    strategy_type = strategy_config['type']
    params = strategy_config.get('params', {})

    if strategy_type == 'MLPredictiveStrategy':
        return MLPredictiveStrategy(**params)
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


def run_backtest_from_scenario(scenario_file: str):
    """
    Run backtest from a scenario JSON file.

    Args:
        scenario_file: Path to scenario JSON file
    """
    print("=" * 70)
    print("BACKTEST RUNNER")
    print("=" * 70)

    # Load scenario
    scenario = load_scenario(scenario_file)
    print(f"\nLoaded scenario: {scenario['name']}")
    print(f"Description: {scenario['description']}\n")

    # Fetch data
    fetcher = CryptoFetcher()
    market = scenario['market']

    start_date = datetime.strptime(market['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(market['end_date'], '%Y-%m-%d')

    print(f"Fetching data...")
    print(f"  Symbol: {market['symbol']}")
    print(f"  Timeframe: {market['timeframe']}")
    print(f"  Period: {start_date.date()} to {end_date.date()}")

    df = fetcher.fetch(
        symbol=market['symbol'],
        timeframe=market['timeframe'],
        start=start_date,
        end=end_date,
        limit=None
    )

    print(f"  Fetched: {len(df)} bars\n")

    # Create strategy
    print(f"Initializing strategy...")
    strategy = create_strategy(scenario['strategy'])
    print(f"  Strategy: {strategy}\n")

    # Create backtest engine
    fees = scenario.get('fees', {})
    risk_mgmt = scenario.get('risk_management', {})

    engine = BacktestEngine(
        strategy=strategy,
        initial_cash=scenario['capital']['initial'],
        commission=fees.get('maker', 0.001),
        slippage=fees.get('slippage', 0.0005),
        stop_loss_pct=risk_mgmt.get('stop_loss'),
        take_profit_pct=risk_mgmt.get('take_profit'),
        log_to_csv=True,
        output_dir="output/backtests"
    )

    # Run backtest
    results = engine.run(
        data=df,
        symbol=market['symbol'],
        warmup_period=100
    )

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run backtest from scenario file')
    parser.add_argument(
        'scenario',
        nargs='?',
        help='Path to scenario JSON file (relative to backtesting/scenarios/)',
        default='ml_predictive_eth_1m.json'
    )

    args = parser.parse_args()

    # Resolve scenario path
    if os.path.isabs(args.scenario):
        scenario_file = args.scenario
    else:
        # Try relative to scenarios directory
        scenarios_dir = Path(__file__).parent / 'backtesting' / 'scenarios'
        scenario_file = scenarios_dir / args.scenario

    if not scenario_file.exists():
        print(f"Error: Scenario file not found: {scenario_file}")
        print(f"\nAvailable scenarios:")
        scenarios_dir = Path(__file__).parent / 'backtesting' / 'scenarios'
        for f in scenarios_dir.glob('*.json'):
            print(f"  - {f.name}")
        sys.exit(1)

    try:
        results = run_backtest_from_scenario(str(scenario_file))
        print(f"\n\nBacktest completed successfully!")

        # Show CSV file locations
        if 'csv_files' in results and results['csv_files']:
            print(f"\nResults saved to:")
            print(f"  Trades: {results['csv_files']['trades']}")
            print(f"  Daily: {results['csv_files']['daily']}")

    except Exception as e:
        print(f"\n\nError running backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
