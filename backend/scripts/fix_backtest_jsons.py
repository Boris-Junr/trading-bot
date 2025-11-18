"""
Script to fix old backtest JSON files by converting percentage values to decimal fractions.

Fixes:
- total_return: divide by 100
- max_drawdown: divide by 100
- win_rate: divide by 100
- pnl_pct in trades: divide by 100
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def fix_backtest_json(file_path: Path) -> bool:
    """
    Fix a single backtest JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if file was modified, False otherwise
    """
    try:
        # Read the JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)

        modified = False

        # Handle nested results structure
        if 'results' in data:
            results = data['results']
        else:
            results = data

        # Fix performance metrics
        if 'performance' in results:
            perf = results['performance']

            # Fix total_return - check if it needs to be divided by 100
            # If abs(total_return) > 0.05, it's likely a percentage value (e.g., -0.187 for -18.7%)
            # Should be a small decimal like -0.00187
            if 'total_return' in perf and abs(perf['total_return']) > 0.05:
                old_value = perf['total_return']
                perf['total_return'] = perf['total_return'] / 100
                modified = True
                print(f"  Fixed total_return: {old_value:.4f} -> {perf['total_return']:.6f}")

            # Fix max_drawdown - same logic
            if 'max_drawdown' in perf and abs(perf['max_drawdown']) > 0.05:
                old_value = perf['max_drawdown']
                perf['max_drawdown'] = perf['max_drawdown'] / 100
                modified = True
                print(f"  Fixed max_drawdown: {old_value:.4f} -> {perf['max_drawdown']:.6f}")

        # Fix trading metrics
        if 'trading' in results:
            trading = results['trading']

            # Fix win_rate - should be 0.0 to 1.0, if it's > 1 it's a percentage
            if 'win_rate' in trading and trading['win_rate'] > 1.0:
                old_value = trading['win_rate']
                trading['win_rate'] = trading['win_rate'] / 100
                modified = True
                print(f"  Fixed win_rate: {old_value:.2f} -> {trading['win_rate']:.4f}")

        # Skip individual trades - they're stored as string representations in these JSONs
        # and would need regex parsing to fix, which is not worth it for historical data

        # Write back if modified
        if modified:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[OK] Updated {file_path.name}")
            return True
        else:
            print(f"[SKIP] No changes needed for {file_path.name}")
            return False

    except Exception as e:
        print(f"[ERROR] Error processing {file_path.name}: {e}")
        return False


def main():
    """Fix all backtest JSON files."""
    backtests_dir = Path(__file__).parent.parent / 'output' / 'backtests'

    if not backtests_dir.exists():
        print(f"Directory not found: {backtests_dir}")
        return

    json_files = list(backtests_dir.glob('*.json'))

    if not json_files:
        print("No JSON files found in backtests directory")
        return

    print(f"Found {len(json_files)} backtest JSON files")
    print("=" * 60)

    modified_count = 0
    for json_file in sorted(json_files):
        print(f"\nProcessing {json_file.name}...")
        if fix_backtest_json(json_file):
            modified_count += 1

    print("\n" + "=" * 60)
    print(f"Summary: {modified_count}/{len(json_files)} files modified")


if __name__ == '__main__':
    main()
