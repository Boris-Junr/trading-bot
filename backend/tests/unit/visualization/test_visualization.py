"""
Test data visualization with matplotlib.

Creates simple OHLCV candlestick chart to verify data quality visually.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from data import HistoricalDataFetcher
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


def plot_candlestick(df, symbol, save_path=None):
    """
    Create a candlestick chart from OHLCV data.

    Args:
        df: DataFrame with OHLCV data
        symbol: Symbol name for title
        save_path: Optional path to save the figure
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                     gridspec_kw={'height_ratios': [3, 1]})

    # Prepare data
    dates = df.index.to_pydatetime()
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    volumes = df['volume'].values

    # Color for up/down days
    colors = ['green' if c >= o else 'red'
              for o, c in zip(opens, closes)]

    # Plot candlesticks
    for i, (date, open_price, high, low, close_price, color) in enumerate(
        zip(dates, opens, highs, lows, closes, colors)
    ):
        # Wick (high-low line)
        ax1.plot([date, date], [low, high], color='black', linewidth=0.5)

        # Body (open-close rectangle)
        height = abs(close_price - open_price)
        bottom = min(open_price, close_price)

        # Use thin line for very small bodies
        if height < 0.01:
            ax1.plot([date, date], [open_price, close_price], color=color, linewidth=1)
        else:
            rect = Rectangle((mdates.date2num(date) - 0.3, bottom),
                           0.6, height,
                           facecolor=color, edgecolor='black', linewidth=0.5)
            ax1.add_patch(rect)

    # Format price chart
    ax1.set_title(f'{symbol} - OHLC Chart', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    # Plot volume
    ax2.bar(dates, volumes, color=colors, alpha=0.6, width=0.8)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    # Rotate date labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")

    plt.show()


def test_visualization():
    """Test data visualization."""

    print("=" * 70)
    print("Testing Data Visualization")
    print("=" * 70)

    # Fetch data
    fetcher = HistoricalDataFetcher(storage_type='parquet')
    symbol = 'AAPL'
    timeframe = '1d'

    print(f"\nFetching data for {symbol} ({timeframe})...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Last 3 months

    df = fetcher.fetch(
        symbol=symbol,
        timeframe=timeframe,
        start=start_date,
        end=end_date
    )

    print(f"  Bars: {len(df)}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")

    # Create output directory
    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)

    chart_path = output_dir / f'{symbol}_{timeframe}_chart.png'

    print(f"\nGenerating candlestick chart...")
    print(f"  Output: {chart_path}")

    try:
        plot_candlestick(df, symbol, save_path=chart_path)

        print("\n" + "=" * 70)
        print("VISUALIZATION TEST COMPLETED")
        print("=" * 70)
        print(f"\nChart saved successfully!")
        print(f"Open: {chart_path}")

        return True

    except Exception as e:
        print(f"\nError creating visualization: {e}")
        print("\nNote: Matplotlib may need to be installed:")
        print("  pip install matplotlib")
        return False


if __name__ == "__main__":
    try:
        success = test_visualization()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
