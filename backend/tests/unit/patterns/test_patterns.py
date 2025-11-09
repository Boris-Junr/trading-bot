"""
Test pattern recognition module.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime, timedelta
from data import HistoricalDataFetcher
from domain.patterns import TrianglePatterns, FlagPattern, PennantPattern, HeadAndShoulders, DoubleTops

def main():
    print("=" * 70)
    print("PATTERN RECOGNITION TEST")
    print("=" * 70)

    fetcher = HistoricalDataFetcher(storage_type='parquet')
    df = fetcher.fetch('AAPL', '1d',
                       start=datetime.now() - timedelta(days=180),
                       end=datetime.now())

    print(f"\nScanning for patterns in AAPL (180 days)...\n")

    # Scan triangles
    triangles = TrianglePatterns.scan_all(df['high'], df['low'], df['close'], window=40)
    print(f"[Triangles] Found {len(triangles)} patterns")
    for p in triangles:
        print(f"  - {p['pattern']}: {p['type']} (confidence: {p['confidence']:.2f})")

    # Scan flags
    flag = FlagPattern.detect(df['high'], df['low'], df['close'], df['volume'], window=15)
    if flag:
        print(f"\n[Flag] Found: {flag['type']}")
        print(f"  Flagpole move: {flag['flagpole_move']:.2f}%")

    # Scan head & shoulders
    hs = HeadAndShoulders.detect(df['high'], df['low'], df['close'], window=60)
    if hs:
        print(f"\n[Head & Shoulders] Found!")
        print(f"  Neckline: ${hs['neckline']:.2f}")
        print(f"  Signal: {hs['signal']}")

    # Scan double tops
    dt = DoubleTops.detect_double_top(df['high'], df['low'], df['close'], window=60)
    if dt:
        print(f"\n[Double Top] Found!")
        print(f"  Resistance: ${dt['resistance']:.2f}")

    print("\n" + "=" * 70)
    print("PATTERN SCAN COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
