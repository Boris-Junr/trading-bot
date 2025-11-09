"""
CSV Logger for Backtesting Results

Appends all backtest runs to cumulative CSV files for A/B testing and parameter comparison.

Two files are maintained:
- backtest_trades.csv: All trades from all runs with run_id tracking
- backtest_daily.csv: All daily summaries from all runs with run_id tracking

Each run is identified by a unique run_id (timestamp), allowing easy comparison
of different strategies and parameters in a single spreadsheet.
"""

import pandas as pd
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class BacktestCSVLogger:
    """
    CSV logger for backtest results.

    Appends to cumulative CSV files:
    1. backtest_trades.csv: All trades from all runs with run_id
    2. backtest_daily.csv: All daily summaries from all runs with run_id

    This allows A/B testing and parameter comparison in a single place.
    """

    def __init__(self, output_dir: str = "output/backtests"):
        """
        Initialize CSV logger.

        Args:
            output_dir: Directory for CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use fixed filenames (append mode)
        self.trades_file = self.output_dir / "backtest_trades.csv"
        self.daily_file = self.output_dir / "backtest_daily.csv"

        self.run_id = None  # Set during initialize_files()

    def initialize_files(self, strategy_name: str, symbol: str, timestamp: datetime):
        """
        Initialize CSV files with headers (if needed).

        If files already exist, just append to them. This allows cumulative
        comparison of all backtest runs.

        Args:
            strategy_name: Name of strategy
            symbol: Trading symbol
            timestamp: Backtest start timestamp
        """
        # Create unique run ID for this backtest
        self.run_id = timestamp.strftime('%Y%m%d_%H%M%S')

        # Trades file headers (run_id and run_timestamp added for tracking)
        trades_headers = [
            'run_id',
            'run_timestamp',
            'strategy',
            'symbol',
            'trade_id',
            'entry_time',
            'exit_time',
            'side',
            'entry_price',
            'exit_price',
            'size',
            'pnl',
            'pnl_pct',
            'hold_hours',
            'exit_reason',
            # Indicator values at entry
            'entry_rsi',
            'entry_macd_hist',
            'entry_ema_fast',
            'entry_ema_slow',
            'entry_bb_width',
            'entry_bb_position',
            'entry_stoch_k',
            'entry_atr',
            'entry_volume_spike',
            # Signal metadata
            'signal_score',
            'signal_confidence',
            'signals_met',
            # Strategy parameters
            'min_score',
            'take_profit_pct',
            'stop_loss_pct',
            'trailing_stop_trigger',
            'trailing_stop_distance',
            'asset_type'
        ]

        # Create trades file with headers if it doesn't exist
        if not self.trades_file.exists():
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(trades_headers)
            print(f"[CSV Logger] Created: {self.trades_file.name}")
        else:
            print(f"[CSV Logger] Appending to: {self.trades_file.name}")

        # Daily file headers
        daily_headers = [
            'run_id',
            'run_timestamp',
            'strategy',
            'symbol',
            'date',
            'day_num',
            'daily_pnl',
            'daily_return_pct',
            'cumulative_pnl',
            'cumulative_return_pct',
            'equity',
            'trades_count',
            'winning_trades',
            'losing_trades',
            'daily_win_rate',
            'largest_win',
            'largest_loss',
            # Strategy parameters (for easy filtering/comparison)
            'min_score',
            'take_profit_pct',
            'stop_loss_pct',
            'trailing_stop_trigger',
            'trailing_stop_distance',
            'asset_type'
        ]

        # Create daily file with headers if it doesn't exist
        if not self.daily_file.exists():
            with open(self.daily_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(daily_headers)
            print(f"[CSV Logger] Created: {self.daily_file.name}")
        else:
            print(f"[CSV Logger] Appending to: {self.daily_file.name}")

        print(f"[CSV Logger] Run ID: {self.run_id}")

    def log_trade(
        self,
        trade_id: int,
        trade: Any,  # Trade object
        signal_metadata: Dict[str, Any],
        strategy_params: Dict[str, Any],
        strategy_name: str,
        symbol: str
    ):
        """
        Log a completed trade to CSV.

        Args:
            trade_id: Sequential trade ID
            trade: Trade object from portfolio
            signal_metadata: Metadata from entry signal
            strategy_params: Strategy parameters
            strategy_name: Strategy name
            symbol: Trading symbol
        """
        if not self.trades_file or not self.run_id:
            return

        # Extract indicator values from signal metadata
        indicators = {
            'entry_rsi': signal_metadata.get('rsi', None),
            'entry_macd_hist': signal_metadata.get('macd_hist', None),
            'entry_ema_fast': signal_metadata.get('ema_fast', None),
            'entry_ema_slow': signal_metadata.get('ema_slow', None),
            'entry_bb_width': signal_metadata.get('bb_width', None),
            'entry_bb_position': signal_metadata.get('bb_position', None),
            'entry_stoch_k': signal_metadata.get('stoch_k', None),
            'entry_atr': signal_metadata.get('atr', None) if 'atr' in signal_metadata else None,
            'entry_volume_spike': signal_metadata.get('volume_spike', None)
        }

        # Extract signal details
        signal_info = {
            'signal_score': signal_metadata.get('score', None),
            'signal_confidence': trade.entry_confidence if hasattr(trade, 'entry_confidence') else None,
            'signals_met': '|'.join(signal_metadata.get('signals', []))
        }

        # Calculate hold duration
        hold_hours = (trade.exit_time - trade.entry_time).total_seconds() / 3600

        row = [
            self.run_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy_name,
            symbol,
            trade_id,
            trade.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            trade.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            trade.side,
            trade.entry_price,
            trade.exit_price,
            trade.size,
            trade.pnl,
            trade.pnl_pct,
            round(hold_hours, 2),
            signal_metadata.get('exit_reason', 'unknown'),
            # Indicators
            indicators['entry_rsi'],
            indicators['entry_macd_hist'],
            indicators['entry_ema_fast'],
            indicators['entry_ema_slow'],
            indicators['entry_bb_width'],
            indicators['entry_bb_position'],
            indicators['entry_stoch_k'],
            indicators['entry_atr'],
            indicators['entry_volume_spike'],
            # Signal
            signal_info['signal_score'],
            signal_info['signal_confidence'],
            signal_info['signals_met'],
            # Strategy params
            strategy_params.get('min_score'),
            strategy_params.get('take_profit_pct'),
            strategy_params.get('stop_loss_pct'),
            strategy_params.get('trailing_stop_trigger'),
            strategy_params.get('trailing_stop_distance'),
            strategy_params.get('asset_type')
        ]

        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def log_daily_summary(
        self,
        date: datetime,
        day_num: int,
        daily_metrics: Dict[str, Any],
        cumulative_metrics: Dict[str, Any],
        strategy_name: str,
        symbol: str,
        strategy_params: Dict[str, Any]
    ):
        """
        Log daily performance summary.

        Args:
            date: Date for this summary
            day_num: Sequential day number
            daily_metrics: Metrics for this day
            cumulative_metrics: Cumulative metrics up to this day
            strategy_name: Strategy name
            symbol: Trading symbol
            strategy_params: Strategy parameters for comparison
        """
        if not self.daily_file or not self.run_id:
            return

        row = [
            self.run_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy_name,
            symbol,
            date.strftime('%Y-%m-%d'),
            day_num,
            daily_metrics.get('daily_pnl', 0),
            daily_metrics.get('daily_return_pct', 0),
            cumulative_metrics.get('cumulative_pnl', 0),
            cumulative_metrics.get('cumulative_return_pct', 0),
            cumulative_metrics.get('equity', 0),
            daily_metrics.get('trades_count', 0),
            daily_metrics.get('winning_trades', 0),
            daily_metrics.get('losing_trades', 0),
            daily_metrics.get('daily_win_rate', 0),
            daily_metrics.get('largest_win', 0),
            daily_metrics.get('largest_loss', 0),
            # Strategy params (for easy filtering)
            strategy_params.get('min_score'),
            strategy_params.get('take_profit_pct'),
            strategy_params.get('stop_loss_pct'),
            strategy_params.get('trailing_stop_trigger'),
            strategy_params.get('trailing_stop_distance'),
            strategy_params.get('asset_type')
        ]

        with open(self.daily_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def get_file_paths(self) -> Dict[str, Path]:
        """Get paths to generated CSV files."""
        return {
            'trades': self.trades_file,
            'daily': self.daily_file
        }
