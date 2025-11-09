"""
Backtesting Module

Provides backtesting capabilities for trading strategies.

Components:
- BacktestEngine: Main backtesting engine with day-by-day tracking and CSV logging
- BacktestCSVLogger: CSV logger for trades and daily performance

Features:
- Event-driven bar-by-bar simulation
- Day-by-day performance tracking
- Cumulative CSV logging for A/B testing and parameter comparison
- All runs appended to single files (backtest_trades.csv, backtest_daily.csv)
- Realistic commission and slippage

Usage:
    from backtesting import BacktestEngine
    from domain.strategies import MomentumScalper
    from data import HistoricalDataFetcher

    # Get data
    fetcher = HistoricalDataFetcher()
    data = fetcher.fetch('AAPL', '5m', start, end)

    # Create strategy
    strategy = MomentumScalper(asset_type='stock', min_score=55)

    # Run backtest with day-by-day tracking and CSV logging
    engine = BacktestEngine(
        strategy,
        initial_cash=100000,
        log_to_csv=True  # Appends to cumulative CSV files
    )

    results = engine.run(data, symbol='AAPL')

    # Access daily performance
    daily_df = results['daily_performance']
    csv_files = results['csv_files']

    # All runs are appended to:
    # - output/backtests/backtest_trades.csv
    # - output/backtests/backtest_daily.csv
"""

from .engine import BacktestEngine
from .reporting.csv_logger import BacktestCSVLogger

__all__ = ['BacktestEngine', 'BacktestCSVLogger']
