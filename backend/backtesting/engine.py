"""
Backtesting Engine

Simulates strategy execution on historical data with day-by-day tracking and CSV logging.

Features:
- Event-driven simulation (bar-by-bar)
- Day-by-day performance tracking
- CSV logging with indicator values and strategy parameters
- Realistic position management
- Commission and slippage support
- Stop loss and take profit
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.strategies import Strategy, Portfolio, Signal, SignalType
from backtesting.reporting.csv_logger import BacktestCSVLogger


class BacktestEngine:
    """
    Backtesting engine with day-by-day tracking and optional CSV logging.
    """

    def __init__(
        self,
        strategy: Strategy,
        initial_cash: float = 100000.0,
        commission: float = 0.001,  # 0.1%
        slippage: float = 0.0005,   # 0.05%
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        log_to_csv: bool = True,
        output_dir: str = "output/backtests"
    ):
        """
        Initialize backtesting engine.

        Args:
            strategy: Trading strategy to test
            initial_cash: Starting portfolio cash
            commission: Commission rate (as fraction)
            slippage: Slippage rate (as fraction)
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            log_to_csv: Whether to log results to CSV
            output_dir: Directory for CSV output
        """
        self.strategy = strategy
        self.portfolio = Portfolio(initial_cash=initial_cash, commission=commission)
        self.slippage = slippage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        self.equity_curve: list = []
        self.signals_history: list = []

        # Daily tracking
        self.log_to_csv = log_to_csv
        self.csv_logger = BacktestCSVLogger(output_dir) if log_to_csv else None
        self.daily_metrics: Dict[str, Dict] = {}
        self.signal_metadata_map: Dict[str, Dict] = {}
        self.strategy_params: Dict[str, Any] = {}

    def run(
        self,
        data: pd.DataFrame,
        symbol: str = 'UNKNOWN',
        warmup_period: int = 100
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data with day-by-day tracking.

        Args:
            data: DataFrame with OHLCV data (indexed by timestamp)
            symbol: Trading symbol
            warmup_period: Number of bars to skip for indicator warmup

        Returns:
            Dictionary with backtest results including daily performance
        """
        # Validate data length
        if len(data) <= warmup_period:
            print(f"[ENGINE] ERROR: Insufficient data - got {len(data)} bars, need at least {warmup_period + 1} bars (warmup + 1)")
            return None

        # Extract strategy parameters for logging
        self._extract_strategy_params()

        # Store symbol for CSV logging
        self.current_symbol = symbol

        # Initialize CSV logger
        if self.csv_logger:
            self.csv_logger.initialize_files(
                strategy_name=self.strategy.get_name(),
                symbol=symbol,
                timestamp=datetime.now()
            )

        print(f"Running backtest: {self.strategy.get_name()}")
        print(f"Symbol: {symbol}")
        print(f"Period: {data.index[0]} to {data.index[-1]}")
        print(f"Bars: {len(data)}")
        print(f"Initial capital: ${self.portfolio.initial_cash:,.2f}\n")

        # Enable feature caching for ML strategies (massive performance boost)
        if hasattr(self.strategy, 'enable_feature_cache'):
            print(f"[ENGINE] Enabling feature cache for ML strategy...")
            self.strategy.enable_feature_cache(data)

        # Initialize daily tracking
        self._initialize_daily_tracking(data, warmup_period)

        # Progress tracking
        total_bars = len(data) - warmup_period
        last_progress_percent = 0

        print(f"[ENGINE] Starting simulation of {total_bars:,} bars (warmup: {warmup_period})...")

        # Event-driven simulation (bar by bar)
        for i in range(warmup_period, len(data)):
            # Progress logging every 10%
            bars_processed = i - warmup_period + 1
            progress_percent = int((bars_processed / total_bars) * 100)
            if progress_percent >= last_progress_percent + 10 and progress_percent % 10 == 0:
                print(f"[ENGINE] Progress: {progress_percent}% ({bars_processed:,}/{total_bars:,} bars) | Equity: ${self.portfolio.equity:,.2f} | Trades: {len(self.portfolio.trades)}")
                last_progress_percent = progress_percent

            current_data = data.iloc[:i+1]
            current_bar = data.iloc[i]
            timestamp = data.index[i]
            current_price = current_bar['close']

            # Update portfolio with current prices
            if self.portfolio.has_position(symbol):
                self.portfolio.update_prices({symbol: current_price})

            # Check stop loss / take profit
            self._check_exit_conditions(symbol, current_price, timestamp)

            # Generate signal from strategy
            signal = self.strategy.generate_signal(current_data)

            # Store signal metadata for CSV logging
            if self.log_to_csv:
                self.signal_metadata_map[timestamp.isoformat()] = signal.metadata if signal.metadata else {}

                # Track signal by day
                day_key = timestamp.normalize().strftime('%Y-%m-%d')
                if day_key in self.daily_metrics:
                    self.daily_metrics[day_key]['signals'].append({
                        'timestamp': timestamp,
                        'type': signal.type.value,
                        'price': current_price,
                        'confidence': signal.confidence
                    })

            self.signals_history.append({
                'timestamp': timestamp,
                'signal': signal.type.value,
                'price': current_price,
                'confidence': signal.confidence
            })

            # Execute signal
            self._execute_signal(signal, symbol, current_price, timestamp)

            # Track completed trades by day
            if self.log_to_csv and signal.type in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT]:
                if self.portfolio.trades:
                    latest_trade = self.portfolio.trades[-1]
                    day_key = timestamp.normalize().strftime('%Y-%m-%d')
                    if day_key in self.daily_metrics:
                        self.daily_metrics[day_key]['trades'].append(latest_trade)

            # Record equity
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': self.portfolio.equity,
                'cash': self.portfolio.cash
            })

        # Close any open positions at end
        print(f"\n[ENGINE] Simulation complete - processing final results...")
        if self.portfolio.has_position(symbol):
            final_price = data.iloc[-1]['close']
            final_time = data.index[-1]
            print(f"[ENGINE] Closing open position at ${final_price:,.2f}")
            self.portfolio.close_position(symbol, final_price, final_time)

        # Generate results
        print(f"[ENGINE] Generating performance metrics...")
        results = self._generate_results(data, symbol)

        # Add daily results
        if self.log_to_csv:
            daily_results = self._calculate_daily_summaries(data, symbol)
            results['daily_performance'] = daily_results
            results['csv_files'] = self.csv_logger.get_file_paths() if self.csv_logger else None

            # Log all trades to CSV
            self._log_all_trades()

            # Print daily summary
            self._print_daily_summary(daily_results)

        print(f"[ENGINE] OK - Backtest engine completed successfully\n")
        return results

    def _execute_signal(
        self,
        signal: Signal,
        symbol: str,
        price: float,
        timestamp: datetime
    ):
        """Execute trading signal."""
        # Apply slippage
        execution_price = price * (1 + self.slippage) if signal.type == SignalType.BUY else price * (1 - self.slippage)

        if signal.type == SignalType.BUY:
            if not self.portfolio.has_position(symbol):
                stop_loss = None
                take_profit = None

                if self.stop_loss_pct:
                    stop_loss = execution_price * (1 - self.stop_loss_pct)
                if self.take_profit_pct:
                    take_profit = execution_price * (1 + self.take_profit_pct)

                position = self.portfolio.open_position(
                    symbol=symbol,
                    side='long',
                    price=execution_price,
                    timestamp=timestamp,
                    size_pct=signal.size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

                if position:
                    self.strategy.on_position_opened(position)

        elif signal.type == SignalType.SELL:
            if not self.portfolio.has_position(symbol):
                stop_loss = None
                take_profit = None

                if self.stop_loss_pct:
                    stop_loss = execution_price * (1 + self.stop_loss_pct)
                if self.take_profit_pct:
                    take_profit = execution_price * (1 - self.take_profit_pct)

                position = self.portfolio.open_position(
                    symbol=symbol,
                    side='short',
                    price=execution_price,
                    timestamp=timestamp,
                    size_pct=signal.size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

                if position:
                    self.strategy.on_position_opened(position)

        elif signal.type == SignalType.CLOSE_LONG:
            if self.portfolio.has_position(symbol):
                position = self.portfolio.get_position(symbol)
                if position.side == 'long':
                    trade = self.portfolio.close_position(symbol, execution_price, timestamp)
                    if trade:
                        self.strategy.on_position_closed(position, execution_price, timestamp)

        elif signal.type == SignalType.CLOSE_SHORT:
            if self.portfolio.has_position(symbol):
                position = self.portfolio.get_position(symbol)
                if position.side == 'short':
                    trade = self.portfolio.close_position(symbol, execution_price, timestamp)
                    if trade:
                        self.strategy.on_position_closed(position, execution_price, timestamp)

    def _check_exit_conditions(self, symbol: str, price: float, timestamp: datetime):
        """Check if stop loss or take profit is hit."""
        if not self.portfolio.has_position(symbol):
            return

        position = self.portfolio.get_position(symbol)

        if position.should_stop_loss():
            print(f"[{timestamp}] Stop loss hit at ${price:.2f}")
            self.portfolio.close_position(symbol, price, timestamp)
            self.strategy.on_position_closed(position, price, timestamp)

        elif position.should_take_profit():
            print(f"[{timestamp}] Take profit hit at ${price:.2f}")
            self.portfolio.close_position(symbol, price, timestamp)
            self.strategy.on_position_closed(position, price, timestamp)

    def _extract_strategy_params(self):
        """Extract strategy parameters for CSV logging."""
        strategy_attrs = [
            'min_score', 'take_profit_pct', 'stop_loss_pct',
            'trailing_stop_trigger', 'trailing_stop_distance',
            'asset_type', 'ema_fast', 'ema_slow', 'rsi_period',
            'bb_period', 'max_hold_hours'
        ]

        for attr in strategy_attrs:
            if hasattr(self.strategy, attr):
                self.strategy_params[attr] = getattr(self.strategy, attr)

    def _initialize_daily_tracking(self, data: pd.DataFrame, warmup_period: int):
        """Initialize daily performance tracking."""
        if not self.log_to_csv:
            return

        trading_days = data.index[warmup_period:].normalize().unique()

        for day in trading_days:
            day_key = day.strftime('%Y-%m-%d')
            self.daily_metrics[day_key] = {
                'date': day,
                'start_equity': None,
                'end_equity': None,
                'trades': [],
                'signals': []
            }

    def _calculate_daily_summaries(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Calculate daily performance summaries."""
        daily_rows = []
        cumulative_pnl = 0
        initial_equity = self.portfolio.initial_cash
        day_num = 0

        for day_key in sorted(self.daily_metrics.keys()):
            day_data = self.daily_metrics[day_key]
            day_num += 1

            day_mask = data.index.normalize() == day_data['date']
            day_bars = data[day_mask]

            if len(day_bars) == 0:
                continue

            day_equity = [e for e in self.equity_curve if e['timestamp'].normalize() == day_data['date']]

            start_equity = day_equity[0]['equity'] if day_equity else initial_equity
            end_equity = day_equity[-1]['equity'] if day_equity else start_equity

            daily_pnl = end_equity - start_equity
            daily_return_pct = (daily_pnl / start_equity) * 100 if start_equity > 0 else 0
            cumulative_pnl += daily_pnl
            cumulative_return_pct = (cumulative_pnl / initial_equity) * 100

            day_trades = day_data['trades']
            trades_count = len(day_trades)
            winning_trades = sum(1 for t in day_trades if t.pnl > 0)
            losing_trades = sum(1 for t in day_trades if t.pnl < 0)
            daily_win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0

            wins = [t.pnl for t in day_trades if t.pnl > 0]
            losses = [t.pnl for t in day_trades if t.pnl < 0]
            largest_win = max(wins) if wins else 0
            largest_loss = min(losses) if losses else 0

            daily_metrics = {
                'daily_pnl': daily_pnl,
                'daily_return_pct': daily_return_pct,
                'trades_count': trades_count,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'daily_win_rate': daily_win_rate,
                'largest_win': largest_win,
                'largest_loss': largest_loss
            }

            cumulative_metrics = {
                'cumulative_pnl': cumulative_pnl,
                'cumulative_return_pct': cumulative_return_pct,
                'equity': end_equity
            }

            if self.csv_logger:
                self.csv_logger.log_daily_summary(
                    date=day_data['date'],
                    day_num=day_num,
                    daily_metrics=daily_metrics,
                    cumulative_metrics=cumulative_metrics,
                    strategy_name=self.strategy.get_name(),
                    symbol=symbol,
                    strategy_params=self.strategy_params
                )

            daily_rows.append({
                'date': day_data['date'],
                'day': day_num,
                'daily_pnl': daily_pnl,
                'daily_return': daily_return_pct,
                'cumulative_pnl': cumulative_pnl,
                'cumulative_return': cumulative_return_pct,
                'equity': end_equity,
                'trades': trades_count,
                'wins': winning_trades,
                'losses': losing_trades,
                'win_rate': daily_win_rate
            })

        return pd.DataFrame(daily_rows)

    def _log_all_trades(self):
        """Log all completed trades to CSV with indicator values."""
        if not self.csv_logger:
            return

        for i, trade in enumerate(self.portfolio.trades, 1):
            entry_key = trade.entry_time.isoformat()
            signal_metadata = self.signal_metadata_map.get(entry_key, {})

            exit_key = trade.exit_time.isoformat()
            exit_metadata = self.signal_metadata_map.get(exit_key, {})
            if 'exit_reason' in exit_metadata:
                signal_metadata['exit_reason'] = exit_metadata['exit_reason']

            self.csv_logger.log_trade(
                trade_id=i,
                trade=trade,
                signal_metadata=signal_metadata,
                strategy_params=self.strategy_params,
                strategy_name=self.strategy.get_name(),
                symbol=self.current_symbol
            )

    def _print_daily_summary(self, daily_df: pd.DataFrame):
        """Print daily performance summary."""
        if daily_df.empty:
            return

        print("\n" + "=" * 70)
        print("DAILY PERFORMANCE SUMMARY")
        print("=" * 70)

        print(f"\n{'Day':<5} {'Date':<12} {'Daily P&L':<12} {'Daily %':<10} {'Cum %':<10} {'Trades':<8}")
        print("-" * 70)

        for _, row in daily_df.iterrows():
            pnl_str = f"${row['daily_pnl']:,.0f}"
            daily_ret = f"{row['daily_return']:+.2f}%"
            cum_ret = f"{row['cumulative_return']:+.2f}%"
            trades_str = f"{int(row['trades'])}"

            print(f"{int(row['day']):<5} {row['date'].strftime('%Y-%m-%d'):<12} "
                  f"{pnl_str:<12} {daily_ret:<10} {cum_ret:<10} {trades_str:<8}")

        print("-" * 70)
        positive_days = len(daily_df[daily_df['daily_pnl'] > 0])
        total_days = len(daily_df)
        avg_daily_return = daily_df['daily_return'].mean()
        best_day = daily_df.loc[daily_df['daily_pnl'].idxmax()]
        worst_day = daily_df.loc[daily_df['daily_pnl'].idxmin()]

        print(f"\nPositive Days: {positive_days}/{total_days} ({positive_days/total_days*100:.1f}%)")
        print(f"Average Daily Return: {avg_daily_return:+.2f}%")
        print(f"Best Day: {best_day['date'].strftime('%Y-%m-%d')} ({best_day['daily_return']:+.2f}%)")
        print(f"Worst Day: {worst_day['date'].strftime('%Y-%m-%d')} ({worst_day['daily_return']:+.2f}%)")

        if self.csv_logger:
            files = self.csv_logger.get_file_paths()
            print(f"\nCSV Files (Cumulative):")
            print(f"  Trades: {files['trades']}")
            print(f"  Daily: {files['daily']}")
            print(f"  Run ID: {self.csv_logger.run_id}")

        print("=" * 70)

    def _generate_results(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate backtest results and metrics."""
        summary = self.portfolio.get_summary()

        equity_df = pd.DataFrame(self.equity_curve).set_index('timestamp')

        returns = equity_df['equity'].pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5) if len(returns) > 0 else 0

        equity_series = equity_df['equity']
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        print("\n" + "=" * 70)
        print("BACKTEST RESULTS")
        print("=" * 70)
        print(f"\nStrategy: {self.strategy.get_name()}")
        print(f"Symbol: {symbol}")
        print(f"Period: {data.index[0].date()} to {data.index[-1].date()}")

        print(f"\nPERFORMANCE:")
        print(f"  Initial Capital: ${summary['initial_cash']:,.2f}")
        print(f"  Final Equity: ${summary['equity']:,.2f}")
        print(f"  Total Return: {summary['total_return']:.2f}%")
        print(f"  Total P&L: ${summary['total_pnl']:,.2f}")

        print(f"\nRISK METRICS:")
        print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {max_drawdown:.2f}%")

        print(f"\nTRADING ACTIVITY:")
        print(f"  Total Trades: {summary['total_trades']}")
        print(f"  Winning Trades: {summary['winning_trades']}")
        print(f"  Losing Trades: {summary['losing_trades']}")
        print(f"  Win Rate: {summary['win_rate']:.2f}%")
        print(f"  Profit Factor: {summary['profit_factor']:.2f}")

        print(f"\nAVERAGE TRADE:")
        print(f"  Avg Win: ${summary['avg_win']:,.2f}")
        print(f"  Avg Loss: ${summary['avg_loss']:,.2f}")

        print("\n" + "=" * 70)

        return {
            'strategy': self.strategy.get_name(),
            'symbol': symbol,
            'start_date': data.index[0],
            'end_date': data.index[-1],
            'performance': {
                'initial_cash': summary['initial_cash'],
                'final_equity': summary['equity'],
                'total_return': summary['total_return'],
                'total_pnl': summary['total_pnl'],
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown
            },
            'trading': {
                'total_trades': summary['total_trades'],
                'winning_trades': summary['winning_trades'],
                'losing_trades': summary['losing_trades'],
                'win_rate': summary['win_rate'],
                'profit_factor': summary['profit_factor'],
                'avg_win': summary['avg_win'],
                'avg_loss': summary['avg_loss']
            },
            'equity_curve': equity_df,
            'trades': self.portfolio.trades,
            'signals': self.signals_history
        }
