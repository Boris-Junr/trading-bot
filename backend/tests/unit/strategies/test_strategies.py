"""
Unit tests for trading strategies.

Tests:
- Base classes (Strategy, Signal, Position, Portfolio)
- Individual strategies (SMA, RSI, Multi-Indicator)
"""

import sys
from pathlib import Path
# Add backend directory to path
# test_strategies.py -> strategies/ -> unit/ -> tests/ -> backend/
backend_path = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from strategies import (
    Strategy, Signal, SignalType, Position, Portfolio,
    SMACrossover, RSIMeanReversion, MultiIndicator
)


def generate_sample_data(bars: int = 200, trend: str = 'up') -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=bars, freq='1D')

    if trend == 'up':
        close = np.linspace(100, 150, bars) + np.random.randn(bars) * 2
    elif trend == 'down':
        close = np.linspace(150, 100, bars) + np.random.randn(bars) * 2
    else:  # sideways
        close = 125 + np.random.randn(bars) * 5

    high = close + np.random.rand(bars) * 2
    low = close - np.random.rand(bars) * 2
    open_price = close + np.random.randn(bars) * 1
    volume = np.random.randint(1000000, 10000000, bars)

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)


def test_signal_creation():
    """Test Signal class."""
    print("\n[TEST] Signal Creation")

    signal = Signal(
        type=SignalType.BUY,
        timestamp=datetime.now(),
        price=100.0,
        confidence=0.8,
        size=0.5,
        metadata={'reason': 'test'}
    )

    assert signal.type == SignalType.BUY
    assert signal.confidence == 0.8
    assert signal.size == 0.5
    assert signal.metadata['reason'] == 'test'

    print("  [OK] Signal created successfully")


def test_position():
    """Test Position class."""
    print("\n[TEST] Position Management")

    # Create long position
    pos = Position(
        symbol='AAPL',
        side='long',
        entry_price=100.0,
        entry_time=datetime.now(),
        size=10,
        current_price=105.0,
        stop_loss=95.0,
        take_profit=110.0
    )

    # Test P&L calculation
    assert pos.unrealized_pnl == 50.0  # (105 - 100) * 10
    assert pos.unrealized_pnl_pct == 5.0

    # Test stop loss
    pos.update_price(94.0)
    assert pos.should_stop_loss() == True

    # Test take profit
    pos.update_price(111.0)
    assert pos.should_take_profit() == True

    print("  [OK] Position calculations correct")


def test_portfolio():
    """Test Portfolio management."""
    print("\n[TEST] Portfolio Management")

    portfolio = Portfolio(initial_cash=100000, commission=0.001)

    # Open position
    pos = portfolio.open_position(
        symbol='AAPL',
        side='long',
        price=100.0,
        timestamp=datetime.now(),
        size_pct=0.5  # Use 50% of cash
    )

    assert pos is not None
    assert portfolio.cash == 50000  # Half remaining (50% used)
    assert portfolio.has_position('AAPL')

    # Update price
    portfolio.update_prices({'AAPL': 110.0})
    equity_before_close = portfolio.equity

    # Close position
    trade = portfolio.close_position('AAPL', 110.0, datetime.now())

    assert trade is not None
    assert trade.is_winner == True
    assert not portfolio.has_position('AAPL')

    # Check summary
    summary = portfolio.get_summary()
    assert summary['total_trades'] == 1
    assert summary['winning_trades'] == 1
    assert summary['win_rate'] == 100.0

    print(f"  [OK] Trade P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")
    print(f"  [OK] Win rate: {summary['win_rate']:.0f}%")


def test_sma_crossover():
    """Test SMA Crossover strategy."""
    print("\n[TEST] SMA Crossover Strategy")

    strategy = SMACrossover(fast_period=20, slow_period=50)

    # Test with uptrend data
    data = generate_sample_data(200, trend='up')
    signal = strategy.generate_signal(data)

    print(f"  Signal: {signal.type.value}")
    print(f"  Price: ${signal.price:.2f}")
    print(f"  Confidence: {signal.confidence:.2f}")

    assert signal is not None
    print("  [OK] Strategy generated signal")


def test_rsi_strategy():
    """Test RSI Mean Reversion strategy."""
    print("\n[TEST] RSI Mean Reversion Strategy")

    strategy = RSIMeanReversion(rsi_period=14, oversold=30, overbought=70)

    # Create data that will trigger oversold
    data = generate_sample_data(100, trend='down')
    signal = strategy.generate_signal(data)

    print(f"  Signal: {signal.type.value}")
    print(f"  Price: ${signal.price:.2f}")
    print(f"  RSI: {signal.metadata.get('rsi', 0):.2f}")

    assert signal is not None
    print("  [OK] Strategy generated signal")


def test_multi_indicator():
    """Test Multi-Indicator strategy."""
    print("\n[TEST] Multi-Indicator Strategy")

    strategy = MultiIndicator(sma_period=50, rsi_period=14, bb_period=20)

    # Test with uptrend
    data = generate_sample_data(200, trend='up')
    signal = strategy.generate_signal(data)

    print(f"  Signal: {signal.type.value}")
    print(f"  Price: ${signal.price:.2f}")
    print(f"  Confidence: {signal.confidence:.2f}")
    print(f"  Score: {signal.metadata.get('score', 0)}/100")
    print(f"  Signals met: {signal.metadata.get('signals', [])}")

    assert signal is not None
    print("  [OK] Strategy generated signal")


def main():
    """Run all strategy tests."""
    print("=" * 70)
    print("STRATEGY UNIT TESTS")
    print("=" * 70)

    try:
        test_signal_creation()
        test_position()
        test_portfolio()
        test_sma_crossover()
        test_rsi_strategy()
        test_multi_indicator()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
