"""
Migration script to transfer existing trading bot data to Supabase multi-tenant schema.

This script:
1. Creates a default tenant
2. Migrates market data from local files/database
3. Migrates predictions
4. Migrates backtests
5. Migrates ML models metadata

Usage:
    python backend/scripts/migrate_to_supabase.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from backend/.env file
from dotenv import load_dotenv
backend_env = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=backend_env)

# Supabase client
from supabase import create_client, Client

# ============================================================================
# Configuration
# ============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Default tenant details
DEFAULT_TENANT = {
    "name": "Default Organization",
    "slug": "default",
    "settings": {
        "timezone": "UTC",
        "currency": "USD"
    }
}

# ============================================================================
# Helper Functions
# ============================================================================

def set_tenant_context(tenant_id: str):
    """Set the tenant context for RLS policies."""
    # Note: This needs to be done via SQL for RLS to work
    # For now we'll include tenant_id in all inserts
    pass

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(text: str):
    """Print a step message."""
    print(f"\n> {text}")

def print_success(text: str):
    """Print a success message."""
    print(f"[OK] {text}")

def print_error(text: str):
    """Print an error message."""
    print(f"[ERROR] {text}")

def print_info(text: str):
    """Print an info message."""
    print(f"[INFO] {text}")

# ============================================================================
# Migration Steps
# ============================================================================

def create_default_tenant() -> str:
    """Create the default tenant and return its ID."""
    print_step("Creating default tenant...")

    try:
        # Check if tenant already exists
        result = supabase.table('tenants').select('id').eq('slug', DEFAULT_TENANT['slug']).execute()

        if result.data:
            tenant_id = result.data[0]['id']
            print_info(f"Tenant already exists with ID: {tenant_id}")
            return tenant_id

        # Create new tenant
        result = supabase.table('tenants').insert({
            'name': DEFAULT_TENANT['name'],
            'slug': DEFAULT_TENANT['slug'],
            'settings': DEFAULT_TENANT['settings']
        }).execute()

        tenant_id = result.data[0]['id']
        print_success(f"Created tenant with ID: {tenant_id}")
        return tenant_id

    except Exception as e:
        print_error(f"Failed to create tenant: {e}")
        raise

def migrate_market_data(tenant_id: str):
    """Migrate market data from local storage to Supabase."""
    print_step("Migrating market data...")

    # Path to local market data (adjust based on your structure)
    data_dir = Path(__file__).parent.parent / 'data' / 'market'

    if not data_dir.exists():
        print_info("No local market data found, skipping...")
        return

    total_rows = 0

    try:
        # Find all CSV/JSON files with market data
        for data_file in data_dir.glob('**/*'):
            if data_file.suffix not in ['.csv', '.json']:
                continue

            print_info(f"Processing {data_file.name}...")

            # Parse filename for symbol/timeframe (adjust based on your naming)
            # Example: BTC_USDT_1m.csv
            parts = data_file.stem.split('_')
            if len(parts) >= 3:
                symbol = f"{parts[0]}_{parts[1]}"
                timeframe = parts[2]
            else:
                print_info(f"Skipping {data_file.name} (unable to parse)")
                continue

            # Read and convert data
            if data_file.suffix == '.csv':
                import pandas as pd
                df = pd.read_csv(data_file)

                # Convert to records (adjust column names as needed)
                records = []
                for _, row in df.iterrows():
                    records.append({
                        'tenant_id': tenant_id,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': row.get('timestamp') or row.get('time'),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']),
                    })

                # Insert in batches
                batch_size = 1000
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    try:
                        supabase.table('market_data').insert(batch).execute()
                        total_rows += len(batch)
                    except Exception as e:
                        print_error(f"Failed to insert batch: {e}")
                        continue

        print_success(f"Migrated {total_rows} market data rows")

    except Exception as e:
        print_error(f"Failed to migrate market data: {e}")

def migrate_backtests(tenant_id: str):
    """Migrate backtest results from local storage to Supabase."""
    print_step("Migrating backtests...")

    # Path to backtest results
    backtests_dir = Path(__file__).parent.parent / 'output' / 'backtests'

    if not backtests_dir.exists():
        print_info("No local backtests found, skipping...")
        return

    total_backtests = 0

    try:
        for backtest_file in backtests_dir.glob('*.json'):
            print_info(f"Processing {backtest_file.name}...")

            with open(backtest_file, 'r') as f:
                data = json.load(f)

            # Extract backtest info
            backtest_record = {
                'tenant_id': tenant_id,
                'strategy': data.get('strategy', 'Unknown'),
                'symbol': data.get('symbol', 'Unknown'),
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'initial_capital': data.get('initial_capital', 10000),
                'status': 'completed',
                'performance': data.get('performance', {}),
                'trading': data.get('trading', {}),
                'trades_data': data.get('trades', []),
                'created_at': data.get('timestamp', datetime.utcnow().isoformat()),
                'completed_at': data.get('timestamp', datetime.utcnow().isoformat())
            }

            try:
                result = supabase.table('backtests').insert(backtest_record).execute()
                total_backtests += 1

                # Migrate individual trades if available
                backtest_id = result.data[0]['id']
                trades = data.get('trades', [])

                if trades:
                    trade_records = []
                    for trade in trades:
                        trade_records.append({
                            'tenant_id': tenant_id,
                            'backtest_id': backtest_id,
                            'symbol': trade.get('symbol', data.get('symbol')),
                            'side': trade.get('side', 'buy'),
                            'quantity': trade.get('quantity', 0),
                            'price': trade.get('price', 0),
                            'timestamp': trade.get('timestamp', datetime.utcnow().isoformat()),
                            'order_type': trade.get('order_type', 'market'),
                            'status': 'filled',
                            'pnl': trade.get('pnl'),
                            'fees': trade.get('fees', 0),
                            'metadata': trade.get('metadata', {})
                        })

                    if trade_records:
                        supabase.table('trades').insert(trade_records).execute()
                        print_info(f"  Migrated {len(trade_records)} trades")

            except Exception as e:
                print_error(f"Failed to insert backtest {backtest_file.name}: {e}")
                continue

        print_success(f"Migrated {total_backtests} backtests")

    except Exception as e:
        print_error(f"Failed to migrate backtests: {e}")

def migrate_predictions(tenant_id: str):
    """Migrate prediction history from local storage to Supabase."""
    print_step("Migrating predictions...")

    # This depends on how predictions are currently stored
    # Adjust based on your implementation

    predictions_dir = Path(__file__).parent.parent / 'output' / 'predictions'

    if not predictions_dir.exists():
        print_info("No local predictions found, skipping...")
        return

    total_predictions = 0

    try:
        for pred_file in predictions_dir.glob('*.json'):
            print_info(f"Processing {pred_file.name}...")

            with open(pred_file, 'r') as f:
                data = json.load(f)

            prediction_record = {
                'tenant_id': tenant_id,
                'symbol': data.get('symbol', 'Unknown'),
                'timeframe': data.get('timeframe', '1m'),
                'created_at': data.get('timestamp', datetime.utcnow().isoformat()),
                'status': 'completed',
                'result': data.get('result'),
                'current_price': data.get('current_price'),
                'predicted_prices': data.get('predictions', []),
                'confidence_scores': data.get('confidence', []),
                'metadata': data.get('metadata', {})
            }

            try:
                supabase.table('predictions').insert(prediction_record).execute()
                total_predictions += 1
            except Exception as e:
                print_error(f"Failed to insert prediction {pred_file.name}: {e}")
                continue

        print_success(f"Migrated {total_predictions} predictions")

    except Exception as e:
        print_error(f"Failed to migrate predictions: {e}")

def migrate_ml_models(tenant_id: str):
    """Migrate ML model metadata to Supabase."""
    print_step("Migrating ML model metadata...")

    models_dir = Path(__file__).parent.parent / 'analysis' / 'models' / 'saved'

    if not models_dir.exists():
        print_info("No local models found, skipping...")
        return

    total_models = 0

    try:
        # Iterate through model directories
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue

            print_info(f"Processing model {model_dir.name}...")

            # Parse model directory name (e.g., BTC_USDT_1m_300steps_multi_ohlc)
            parts = model_dir.name.split('_')
            if len(parts) >= 3:
                symbol = f"{parts[0]}_{parts[1]}"
                timeframe = parts[2]
            else:
                continue

            # Check for model files
            config_file = model_dir / 'close' / 'config.pkl'
            model_file = model_dir / 'close' / 'autoregressive_model.txt'

            if config_file.exists():
                model_record = {
                    'tenant_id': tenant_id,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'model_type': 'autoregressive',
                    'version': 'v1',
                    'training_data_start': '2024-01-01T00:00:00Z',  # Adjust as needed
                    'training_data_end': datetime.utcnow().isoformat(),
                    'metrics': {},
                    'config': {},
                    'file_path': str(model_file.relative_to(Path(__file__).parent.parent)),
                    'status': 'ready'
                }

                try:
                    supabase.table('ml_models').insert(model_record).execute()
                    total_models += 1
                except Exception as e:
                    print_error(f"Failed to insert model {model_dir.name}: {e}")
                    continue

        print_success(f"Migrated {total_models} ML models")

    except Exception as e:
        print_error(f"Failed to migrate ML models: {e}")

# ============================================================================
# Main Migration
# ============================================================================

def main():
    """Run the complete migration process."""
    print_header("Trading Bot to Supabase Multi-Tenant Migration")

    print_info(f"Supabase URL: {SUPABASE_URL}")
    print_info("Using service role key for migration")

    try:
        # Step 1: Create default tenant
        tenant_id = create_default_tenant()

        # Step 2: Migrate market data
        migrate_market_data(tenant_id)

        # Step 3: Migrate backtests
        migrate_backtests(tenant_id)

        # Step 4: Migrate predictions
        migrate_predictions(tenant_id)

        # Step 5: Migrate ML models metadata
        migrate_ml_models(tenant_id)

        print_header("Migration Complete!")
        print_success(f"All data migrated to tenant: {tenant_id}")
        print_info("\nNext steps:")
        print_info("1. Verify data in Supabase dashboard")
        print_info("2. Update backend to use Supabase client")
        print_info("3. Test API endpoints with new database")

    except Exception as e:
        print_header("Migration Failed")
        print_error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
