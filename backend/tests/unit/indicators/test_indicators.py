"""
Test script for technical indicators.

Tests all indicator categories:
- Trend: SMA, EMA, MACD
- Momentum: RSI, Stochastic
- Volatility: Bollinger Bands, ATR
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from data import HistoricalDataFetcher
from analysis.indicators import SMA, EMA, MACD, RSI, Stochastic, BollingerBands, ATR
import pandas as pd


def test_trend_indicators():
    """Test trend indicators (SMA, EMA, MACD)."""
    print("\n" + "=" * 70)
    print("TESTING TREND INDICATORS")
    print("=" * 70)

    # Fetch data
    fetcher = HistoricalDataFetcher(storage_type='parquet')
    df = fetcher.fetch('AAPL', '1d',
                       start=datetime.now() - timedelta(days=180),
                       end=datetime.now())

    close = df['close']

    # Test SMA
    print("\n[SMA - Simple Moving Average]")
    sma_20 = SMA.calculate(close, period=20)
    sma_50 = SMA.calculate(close, period=50)
    print(f"  SMA(20) last 5 values:")
    print(f"  {sma_20.tail().round(2).to_dict()}")
    print(f"  SMA(50) last value: ${sma_50.iloc[-1]:.2f}")

    # Test EMA
    print("\n[EMA - Exponential Moving Average]")
    ema_12 = EMA.calculate(close, period=12)
    ema_26 = EMA.calculate(close, period=26)
    print(f"  EMA(12) last value: ${ema_12.iloc[-1]:.2f}")
    print(f"  EMA(26) last value: ${ema_26.iloc[-1]:.2f}")

    # Test MACD
    print("\n[MACD - Moving Average Convergence Divergence]")
    macd = MACD.calculate(close)
    print(f"  MACD line: {macd['macd'].iloc[-1]:.2f}")
    print(f"  Signal line: {macd['signal'].iloc[-1]:.2f}")
    print(f"  Histogram: {macd['histogram'].iloc[-1]:.2f}")
    print(f"  Signal: {'BULLISH' if macd['histogram'].iloc[-1] > 0 else 'BEARISH'}")

    return df


def test_momentum_indicators(df):
    """Test momentum indicators (RSI, Stochastic)."""
    print("\n" + "=" * 70)
    print("TESTING MOMENTUM INDICATORS")
    print("=" * 70)

    # Test RSI
    print("\n[RSI - Relative Strength Index]")
    rsi = RSI.calculate(df['close'], period=14)
    current_rsi = rsi.iloc[-1]
    print(f"  Current RSI: {current_rsi:.2f}")
    if current_rsi > 70:
        print(f"  Status: OVERBOUGHT (> 70)")
    elif current_rsi < 30:
        print(f"  Status: OVERSOLD (< 30)")
    else:
        print(f"  Status: NEUTRAL (30-70)")

    # Test Stochastic
    print("\n[Stochastic Oscillator]")
    stoch = Stochastic.calculate(df['high'], df['low'], df['close'])
    print(f"  %K (fast): {stoch['k'].iloc[-1]:.2f}")
    print(f"  %D (slow): {stoch['d'].iloc[-1]:.2f}")
    if stoch['k'].iloc[-1] > 80:
        print(f"  Status: OVERBOUGHT (> 80)")
    elif stoch['k'].iloc[-1] < 20:
        print(f"  Status: OVERSOLD (< 20)")
    else:
        print(f"  Status: NEUTRAL (20-80)")


def test_volatility_indicators(df):
    """Test volatility indicators (Bollinger Bands, ATR)."""
    print("\n" + "=" * 70)
    print("TESTING VOLATILITY INDICATORS")
    print("=" * 70)

    # Test Bollinger Bands
    print("\n[Bollinger Bands]")
    bb = BollingerBands.calculate(df['close'], period=20, std_dev=2.0)
    current_price = df['close'].iloc[-1]
    print(f"  Upper Band: ${bb['upper'].iloc[-1]:.2f}")
    print(f"  Middle Band: ${bb['middle'].iloc[-1]:.2f}")
    print(f"  Lower Band: ${bb['lower'].iloc[-1]:.2f}")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  Bandwidth: {bb['bandwidth'].iloc[-1]:.2f}%")

    # Price position
    if current_price > bb['upper'].iloc[-1]:
        print(f"  Position: Above upper band (potential overbought)")
    elif current_price < bb['lower'].iloc[-1]:
        print(f"  Position: Below lower band (potential oversold)")
    else:
        print(f"  Position: Within bands (normal)")

    # Test ATR
    print("\n[ATR - Average True Range]")
    atr = ATR.calculate(df['high'], df['low'], df['close'], period=14)
    current_atr = atr.iloc[-1]
    atr_pct = (current_atr / current_price) * 100
    print(f"  Current ATR: ${current_atr:.2f}")
    print(f"  ATR as % of price: {atr_pct:.2f}%")
    print(f"  Volatility: {'HIGH' if atr_pct > 3 else 'MODERATE' if atr_pct > 1.5 else 'LOW'}")


def create_indicator_summary(df):
    """Create a comprehensive indicator summary."""
    print("\n" + "=" * 70)
    print("INDICATOR SUMMARY")
    print("=" * 70)

    close = df['close']
    current_price = close.iloc[-1]

    # Calculate all indicators
    sma_50 = SMA.calculate(close, 50)
    ema_20 = EMA.calculate(close, 20)
    macd = MACD.calculate(close)
    rsi = RSI.calculate(close)
    bb = BollingerBands.calculate(close)
    atr = ATR.calculate(df['high'], df['low'], close)

    print(f"\nSymbol: AAPL")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Date: {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"\nTrend Indicators:")
    print(f"  SMA(50): ${sma_50.iloc[-1]:.2f} - {'ABOVE' if current_price > sma_50.iloc[-1] else 'BELOW'}")
    print(f"  EMA(20): ${ema_20.iloc[-1]:.2f} - {'ABOVE' if current_price > ema_20.iloc[-1] else 'BELOW'}")
    print(f"  MACD: {macd['histogram'].iloc[-1]:.2f} - {'BULLISH' if macd['histogram'].iloc[-1] > 0 else 'BEARISH'}")

    print(f"\nMomentum Indicators:")
    print(f"  RSI(14): {rsi.iloc[-1]:.2f} - ", end="")
    if rsi.iloc[-1] > 70:
        print("OVERBOUGHT")
    elif rsi.iloc[-1] < 30:
        print("OVERSOLD")
    else:
        print("NEUTRAL")

    print(f"\nVolatility Indicators:")
    print(f"  BB Width: {bb['bandwidth'].iloc[-1]:.2f}% - {'HIGH' if bb['bandwidth'].iloc[-1] > 10 else 'NORMAL'}")
    print(f"  ATR: ${atr.iloc[-1]:.2f} ({(atr.iloc[-1]/current_price*100):.2f}%)")


def main():
    """Run all indicator tests."""
    print("\n")
    print("=" * 70)
    print("        TECHNICAL INDICATORS TEST SUITE")
    print("=" * 70)

    try:
        # Test each category
        df = test_trend_indicators()
        test_momentum_indicators(df)
        test_volatility_indicators(df)

        # Create summary
        create_indicator_summary(df)

        print("\n" + "=" * 70)
        print("ALL INDICATOR TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print("\nAvailable Indicators:")
        print("  Trend: SMA, EMA, MACD")
        print("  Momentum: RSI, Stochastic")
        print("  Volatility: Bollinger Bands, ATR")

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
