# Backtesting System

Comprehensive backtesting engine that simulates trading strategies on historical data with realistic execution, performance metrics, and real-time progress tracking.

## Overview

The backtesting system provides:
- Event-driven bar-by-bar simulation
- Realistic order execution with commission and slippage
- Background task execution with resource management
- Real-time progress updates via Server-Sent Events
- Automatic model training and validation
- Comprehensive performance metrics and trade logging
- Multi-user support with RLS

## Architecture

```
User Request (Frontend)
    ↓ POST /api/backtests/run
Backend API (FastAPI)
    ↓ Check system resources
    ├─→ Queue task (if resources unavailable)
    └─→ Run immediately (if resources available)
        ↓
    BacktestService
        ├─ Fetch historical data (CCXT/Alpaca)
        ├─ Create/validate ML model
        └─ Run BacktestEngine
            ↓ Event-driven simulation
        Portfolio Management
            ├─ Position tracking
            ├─ Commission/slippage
            └─ Stop loss/take profit
                ↓
    Performance Metrics
        ├─ Sharpe Ratio
        ├─ Max Drawdown
        ├─ Win Rate
        └─ Profit Factor
            ↓
    Save to Database (Supabase)
        ↓ Real-time update (PostgreSQL NOTIFY)
Frontend (Vue 3)
    ↓ Realtime subscription
    UI Update
```

## Backend Implementation

### Files

- **[backend/backtesting/engine.py](../../backend/backtesting/engine.py)** - Core backtesting engine
- **[backend/api/services/backtest_service.py](../../backend/api/services/backtest_service.py)** - Service layer for API
- **[backend/api/routers/backtests.py](../../backend/api/routers/backtests.py)** - REST API endpoints
- **[backend/backtesting/reporting/csv_logger.py](../../backend/backtesting/reporting/csv_logger.py)** - CSV logging for results

### Core Components

#### BacktestEngine

The backtesting engine simulates strategy execution bar-by-bar on historical data.

```python
from backtesting.engine import BacktestEngine
from domain.strategies import Strategy

# Initialize engine
engine = BacktestEngine(
    strategy=strategy_instance,
    initial_cash=10000.0,
    commission=0.001,      # 0.1% per trade
    slippage=0.0005,       # 0.05% slippage
    stop_loss_pct=0.02,    # 2% stop loss
    take_profit_pct=0.05,  # 5% take profit
    log_to_csv=True
)

# Run backtest
results = engine.run(
    data=historical_df,    # DataFrame with OHLCV data
    symbol='BTC_USDT',
    warmup_period=100      # Bars to skip for indicator warmup
)
```

**Key Features:**
- **Event-driven simulation**: Processes each bar sequentially
- **Realistic execution**: Applies commission and slippage
- **Position management**: Automatic stop loss and take profit
- **Progress tracking**: Console output every 10%
- **Performance optimization**: Feature caching for ML strategies

**Results Structure:**
```python
{
    'strategy': 'MLPredictive',
    'symbol': 'BTC_USDT',
    'start_date': '2024-01-01',
    'end_date': '2024-01-31',
    'performance': {
        'initial_cash': 10000.0,
        'final_equity': 12500.0,
        'total_return': 0.25,      # 25%
        'total_pnl': 2500.0,
        'sharpe_ratio': 1.85,
        'max_drawdown': -0.08      # -8%
    },
    'trading': {
        'total_trades': 45,
        'winning_trades': 28,
        'losing_trades': 17,
        'win_rate': 0.622,         # 62.2%
        'profit_factor': 2.15,
        'avg_win': 120.50,
        'avg_loss': 65.30
    },
    'equity_curve': DataFrame,     # Timestamped equity values
    'trades': [Trade, ...],        # List of completed trades
    'signals': [Signal, ...]       # All generated signals
}
```

#### BacktestService

Service layer that orchestrates the backtesting process.

```python
from api.services.backtest_service import get_backtest_service

service = get_backtest_service()

# Run a backtest
result = service.run_backtest(
    strategy='MLPredictive',
    symbol='ETH_USDT',
    start_date='2024-01-01',
    end_date='2024-01-31',
    initial_cash=10000.0,
    user_id='user-uuid',
    # Strategy-specific parameters
    timeframe='1m',
    min_predicted_return=0.002,
    confidence_threshold=0.6
)
```

**Service Responsibilities:**

1. **Data Fetching**
   ```python
   df = self.fetcher.fetch(
       symbol=symbol,
       start=start_dt,
       end=end_dt,
       timeframe='1m',
       force_refresh=True
   )
   ```

2. **Model Management**
   - Auto-discovers existing models
   - Trains new models if needed
   - Validates training/backtest period separation (prevents data leakage)

   ```python
   # Prevents using models trained on data that overlaps with backtest period
   is_valid, message = self._validate_model_for_backtest(
       model_path,
       backtest_start_date
   )
   ```

3. **Strategy Creation**
   ```python
   strategy = registry.create_strategy(
       strategy_name='MLPredictive',
       model_path='/path/to/model',
       **params
   )
   ```

4. **Results Persistence**
   - Saves to Supabase database
   - Serializes Trade objects to JSON
   - Stores performance metrics and trade data

### API Endpoints

#### POST `/api/backtests/run`
Run a new backtest with background execution and task queuing.

**Request:**
```json
{
  "strategy": "MLPredictive",
  "symbol": "BTC_USDT",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 10000,
  "params": {
    "timeframe": "1m",
    "min_predicted_return": 0.002,
    "confidence_threshold": 0.6,
    "prediction_window": 60,
    "risk_per_trade": 0.02
  }
}
```

**Response (Running Immediately):**
```json
{
  "status": "running",
  "backtest_id": "uuid-here",
  "message": "Backtest started in background. Check Status Center for progress."
}
```

**Response (Queued):**
```json
{
  "status": "queued",
  "backtest_id": "uuid-here",
  "task_id": "uuid-here",
  "queue_position": 2,
  "message": "Backtest queued. Position in queue: 2"
}
```

**Implementation:**
```python
@router.post("/run")
async def run_backtest(
    request: models.BacktestRequest,
    user_id: str = Depends(get_current_user_id)
):
    backtest_id = str(uuid.uuid4())

    # Check system resources
    resource_monitor = get_resource_monitor()
    can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

    if not can_run:
        # Queue for later execution
        task_id = await task_queue.enqueue(
            TaskType.BACKTEST,
            run_backtest_task,
            priority=0,
            task_id=backtest_id
        )
        return {"status": "queued", ...}

    # Run immediately in background
    await task_queue.register_running_task(
        task_type=TaskType.BACKTEST,
        task_func=run_backtest_task,
        task_id=backtest_id
    )
    return {"status": "running", ...}
```

**Progress Logging:**
The backtest task streams progress updates to the Status Center:
```python
async def run_backtest_task():
    await log(f"🎯 Preparing to backtest {strategy} on {symbol}")
    await log(f"📅 Testing {days} days of historical data")
    await log(f"💰 Starting with ${initial_capital:,.2f}")
    await log(f"🔄 Running backtest simulation...")

    # Run backtest
    result = await asyncio.to_thread(backtest_service.run_backtest, ...)

    if result:
        await log(f"✅ Backtest complete!")
        await log(f"📊 Return: {total_return:+.2%} | Sharpe: {sharpe:.2f}")
```

#### GET `/api/backtests/`
List all backtests for the current user.

**Response:**
```json
[
  {
    "id": "uuid",
    "status": "completed",
    "strategy": "MLPredictive",
    "symbol": "BTC_USDT",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "created_at": "2024-01-31T12:00:00Z",
    "performance": {
      "total_return": 0.25,
      "sharpe_ratio": 1.85,
      "max_drawdown": -0.08
    },
    "trading": {
      "total_trades": 45,
      "win_rate": 0.622,
      "profit_factor": 2.15
    }
  },
  {
    "id": "uuid-2",
    "status": "failed",
    "strategy": "BreakoutScalping",
    "symbol": "ETH_USDT",
    "start_date": "2024-02-01",
    "end_date": "2024-02-28",
    "error": "Insufficient data for backtest"
  }
]
```

#### GET `/api/backtests/{backtest_id}`
Get detailed results for a specific backtest.

**Response:**
```json
{
  "id": "uuid",
  "strategy": "MLPredictive",
  "symbol": "BTC_USDT",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "performance": { ... },
  "trading": { ... },
  "results": {
    "performance": { ... },
    "trading": { ... },
    "trades": [
      {
        "symbol": "BTC_USDT",
        "side": "long",
        "entry_price": 42000.0,
        "entry_time": "2024-01-05T10:30:00Z",
        "exit_price": 43500.0,
        "exit_time": "2024-01-05T14:15:00Z",
        "size": 0.1,
        "pnl": 150.0,
        "pnl_pct": 0.0357,
        "commission": 8.4
      }
    ]
  }
}
```

#### GET `/api/backtests/stream` (Deprecated)
Server-Sent Events endpoint for real-time backtest streaming.

**Note:** This endpoint is no longer used. The `/run` endpoint with background execution and Status Center monitoring is used instead.

### Resource Management

Backtests are resource-intensive operations. The system manages resources automatically:

```python
# Check if system can handle a new backtest
resource_monitor = get_resource_monitor()
can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

if can_run:
    # Run immediately
    await task_queue.register_running_task(...)
else:
    # Queue for later (when resources become available)
    await task_queue.enqueue(TaskType.BACKTEST, ...)
```

**Resource Limits:**
- CPU usage threshold: 80%
- RAM usage threshold: 85%
- Max concurrent backtests: 2

See [System Monitoring](08-SYSTEM_MONITORING.md) for details.

## Frontend Implementation

### Files

- **[frontend/src/views/BacktestsView.vue](../../frontend/src/views/BacktestsView.vue)** - Backtests list page
- **[frontend/src/views/BacktestDetailView.vue](../../frontend/src/views/BacktestDetailView.vue)** - Detailed results page
- **[frontend/src/stores/backtest.ts](../../frontend/src/stores/backtest.ts)** - Pinia store for state management

### BacktestsView

Main page for viewing and running backtests.

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBacktestStore } from '../stores/backtest'
import { storeToRefs } from 'pinia'

const backtestStore = useBacktestStore()
const { loading, error, sortedBacktests } = storeToRefs(backtestStore)

const showRunModal = ref(false)
const newBacktest = ref({
  strategy: 'MLPredictive',
  symbol: 'BTC_USDT',
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  initial_capital: 10000,
})

onMounted(async () => {
  await backtestStore.fetchBacktests()
})

async function runBacktest() {
  const response = await fetch('/api/backtests/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
    },
    body: JSON.stringify({
      strategy: newBacktest.value.strategy,
      symbol: newBacktest.value.symbol,
      start_date: newBacktest.value.start_date,
      end_date: newBacktest.value.end_date,
      initial_capital: newBacktest.value.initial_capital,
      params: {
        timeframe: '1m',
        min_predicted_return: 0.002,
        confidence_threshold: 0.6
      }
    })
  })

  // Close modal - backtest runs in background
  showRunModal.value = false

  // Refresh list after short delay
  setTimeout(() => backtestStore.fetchBacktests(), 1000)
}
</script>

<template>
  <div>
    <!-- Backtests Grid -->
    <Card
      v-for="backtest in sortedBacktests"
      :key="backtest.id"
      :hoverable="backtest.status !== 'failed'"
      @click="goToDetail(backtest)"
    >
      <h3>{{ backtest.strategy }}</h3>
      <Badge>{{ backtest.symbol }}</Badge>

      <!-- Failed Backtest Error -->
      <div v-if="backtest.status === 'failed'">
        ❌ {{ backtest.error }}
      </div>

      <!-- Performance Metrics -->
      <div v-else class="grid grid-cols-4 gap-4">
        <div>
          <div>Total Return</div>
          <div :class="backtest.performance.total_return >= 0 ? 'text-green' : 'text-red'">
            {{ (backtest.performance.total_return * 100).toFixed(2) }}%
          </div>
        </div>
        <!-- More metrics... -->
      </div>
    </Card>

    <!-- Run Backtest Modal -->
    <Modal v-model="showRunModal" title="Run New Backtest">
      <Select v-model="newBacktest.strategy" label="Strategy">
        <option value="MLPredictive">ML Predictive</option>
        <option value="BreakoutScalping">Breakout Scalping</option>
      </Select>
      <!-- More inputs... -->

      <Button @click="runBacktest">Run Backtest</Button>
    </Modal>
  </div>
</template>
```

**Key Features:**
- **Model Detection**: Shows if a trained model exists for the selected symbol
- **Auto-training Notice**: Warns user if model will be trained (2-5 minutes)
- **Background Execution**: Modal closes immediately, backtest runs in background
- **Failed Backtests**: Displays error messages for failed backtests
- **Sorting**: Backtests sorted by creation time (most recent first)

### Backtest Store

Pinia store for backtest state management with real-time updates.

```typescript
// frontend/src/stores/backtest.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/lib/supabase'

export const useBacktestStore = defineStore('backtest', () => {
  const backtests = ref<BacktestResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  let realtimeChannel: RealtimeChannel | null = null

  const sortedBacktests = computed(() => {
    return [...backtests.value].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime()
      const dateB = new Date(b.created_at).getTime()
      return dateB - dateA  // Most recent first
    })
  })

  async function fetchBacktests() {
    loading.value = true
    try {
      const { data, error: fetchError } = await supabase
        .from('backtests')
        .select('*')
        .eq('user_id', user.value.id)
        .order('created_at', { ascending: false })

      if (fetchError) throw fetchError

      backtests.value = data.map(bt => ({
        id: bt.id,
        strategy: bt.strategy,
        symbol: bt.symbol,
        start_date: bt.start_date,
        end_date: bt.end_date,
        created_at: bt.created_at,
        status: bt.status || 'completed',
        performance: bt.performance || {},
        trading: bt.trading || {},
        error: bt.error
      }))

      // Set up real-time subscription
      if (!realtimeChannel) {
        setupRealtimeSubscription()
      }
    } finally {
      loading.value = false
    }
  }

  function setupRealtimeSubscription() {
    realtimeChannel = supabase
      .channel('backtests_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'backtests',
          filter: `user_id=eq.${user.value.id}`
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            // New backtest added - prepend to list
            backtests.value.unshift(payload.new)
          } else if (payload.eventType === 'UPDATE') {
            // Backtest updated (status changed)
            const index = backtests.value.findIndex(bt => bt.id === payload.new.id)
            if (index !== -1) {
              backtests.value[index] = {
                ...backtests.value[index],
                status: payload.new.status,
                performance: payload.new.performance,
                trading: payload.new.trading,
                error: payload.new.error
              }
            }
          }
        }
      )
      .subscribe()
  }

  return {
    backtests,
    loading,
    error,
    sortedBacktests,
    fetchBacktests,
    setupRealtimeSubscription
  }
})
```

**Real-time Updates:**
- Uses Supabase Realtime subscriptions
- Automatically adds new backtests to the list
- Updates backtest status when completed
- Filters by current user (RLS enforced)

### Model Detection

The frontend detects available models to inform users:

```typescript
const availableModels = ref<ModelInfo[]>([])

async function fetchModels() {
  availableModels.value = await api.getModels()
}

const modelsSymbols = computed(() => {
  const symbols = new Set(availableModels.value.map(m => m.symbol))
  return Array.from(symbols)
})

const hasModels = computed(() => availableModels.value.length > 0)
```

**UI Hints:**
```vue
<Select
  v-model="newBacktest.symbol"
  :hint="hasModels && modelsSymbols.includes(newBacktest.symbol)
    ? `✓ Model available for ${newBacktest.symbol}`
    : 'Model will be trained automatically (2-5 minutes)'"
>
```

## Database Schema

### `backtests` Table

```sql
CREATE TABLE public.backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Backtest configuration
  strategy TEXT NOT NULL,
  symbol TEXT NOT NULL,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ NOT NULL,
  initial_capital NUMERIC(15, 2) NOT NULL DEFAULT 10000.00,

  -- Status tracking
  status TEXT NOT NULL DEFAULT 'running',  -- 'running', 'completed', 'failed'
  error TEXT,

  -- Results (JSONB for flexibility)
  performance JSONB,
  trading JSONB,
  trades_data JSONB,  -- Array of trade objects

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,

  -- Indexes
  CONSTRAINT backtests_status_check CHECK (status IN ('running', 'completed', 'failed'))
);

-- Index for user queries
CREATE INDEX idx_backtests_user_id ON public.backtests(user_id);
CREATE INDEX idx_backtests_created_at ON public.backtests(created_at DESC);
CREATE INDEX idx_backtests_status ON public.backtests(status);

-- Row Level Security
ALTER TABLE public.backtests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own backtests"
  ON public.backtests
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own backtests"
  ON public.backtests
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own backtests"
  ON public.backtests
  FOR UPDATE
  USING (auth.uid() = user_id);
```

**JSONB Columns:**

`performance`:
```json
{
  "initial_cash": 10000.0,
  "final_equity": 12500.0,
  "total_return": 0.25,
  "total_pnl": 2500.0,
  "sharpe_ratio": 1.85,
  "max_drawdown": -0.08
}
```

`trading`:
```json
{
  "total_trades": 45,
  "winning_trades": 28,
  "losing_trades": 17,
  "win_rate": 0.622,
  "profit_factor": 2.15,
  "avg_win": 120.5,
  "avg_loss": 65.3
}
```

`trades_data`:
```json
[
  {
    "symbol": "BTC_USDT",
    "side": "long",
    "entry_price": 42000.0,
    "entry_time": "2024-01-05T10:30:00Z",
    "exit_price": 43500.0,
    "exit_time": "2024-01-05T14:15:00Z",
    "size": 0.1,
    "pnl": 150.0,
    "pnl_pct": 0.0357,
    "commission": 8.4
  }
]
```

## Performance Metrics

### Trading Metrics

**Win Rate:**
```python
win_rate = winning_trades / total_trades
```

**Profit Factor:**
```python
profit_factor = total_wins / abs(total_losses)
# > 1.0 is profitable
# > 2.0 is excellent
```

**Average Win/Loss:**
```python
avg_win = sum(wins) / len(wins)
avg_loss = sum(losses) / len(losses)
```

### Risk Metrics

**Sharpe Ratio:**
```python
returns = equity.pct_change()
sharpe_ratio = (returns.mean() / returns.std()) * sqrt(252)
# Annualized risk-adjusted return
# > 1.0 is good
# > 2.0 is very good
# > 3.0 is excellent
```

**Max Drawdown:**
```python
running_max = equity.cummax()
drawdown = (equity - running_max) / running_max
max_drawdown = drawdown.min()
# Worst peak-to-trough decline
```

## Data Leakage Prevention

The system automatically prevents data leakage when training models for backtesting.

### Problem: Look-Ahead Bias

If a model is trained on data that overlaps with the backtest period, it "sees the future" and results are invalid.

```
INVALID:
Training:  |-------------- 30 days --------------|
Backtest:           |-------- 10 days --------|
                    ^^^ OVERLAP = CHEATING ^^^

VALID:
Training:  |-------------- 30 days --------------|
Backtest:                                       |---- 10 days ----|
```

### Solution: Automatic Validation

```python
def _validate_model_for_backtest(model_path, backtest_start_date):
    """Ensure training data doesn't overlap with backtest period"""

    # Load model metadata
    with open(model_path / 'training_metadata.json') as f:
        metadata = json.load(f)

    training_end = pd.to_datetime(metadata['training_end'])
    backtest_start = pd.to_datetime(backtest_start_date)

    # Check for overlap
    if backtest_start >= training_end:
        print("✓ Model is safe to use - no data leakage")
        return (True, "")
    else:
        overlap_days = (training_end - backtest_start).days
        message = (
            f"DATA LEAKAGE DETECTED! "
            f"Overlap: {overlap_days} days. "
            f"Training new model..."
        )
        return (False, message)
```

If overlap is detected, a new model is automatically trained with proper period separation:

```python
# Train model ending 1 day BEFORE backtest starts
end_dt = pd.to_datetime(backtest_start_date) - timedelta(days=1)
start_dt = end_dt - timedelta(days=30)

model.train(data[start_dt:end_dt])
```

## CSV Logging (Optional)

For advanced analysis, backtests can export detailed CSV logs:

```python
engine = BacktestEngine(
    strategy=strategy,
    log_to_csv=True,
    output_dir="output/backtests"
)
```

**Generated Files:**
- `trades_{strategy}_{symbol}_{timestamp}.csv` - All trades with entry/exit details
- `daily_{strategy}_{symbol}_{timestamp}.csv` - Daily performance summary

**Trades CSV:**
```csv
trade_id,symbol,side,entry_time,entry_price,exit_time,exit_price,size,pnl,pnl_pct,commission,rsi,macd,strategy_min_score
1,BTC_USDT,long,2024-01-05 10:30:00,42000.0,2024-01-05 14:15:00,43500.0,0.1,150.0,0.0357,8.4,65.3,12.5,0.6
```

**Daily CSV:**
```csv
date,day,daily_pnl,daily_return,cumulative_pnl,cumulative_return,equity,trades,wins,losses,win_rate
2024-01-01,1,250.0,2.5,250.0,2.5,10250.0,5,3,2,60.0
2024-01-02,2,-100.0,-0.98,150.0,1.5,10150.0,3,1,2,33.3
```

## Common Patterns

### Running a Backtest from CLI

```python
from api.services.backtest_service import get_backtest_service

service = get_backtest_service()

result = service.run_backtest(
    strategy='MLPredictive',
    symbol='BTC_USDT',
    start_date='2024-01-01',
    end_date='2024-01-31',
    initial_cash=10000.0,
    timeframe='1m',
    min_predicted_return=0.002
)

if result:
    print(f"Total Return: {result['performance']['total_return'] * 100:.2f}%")
    print(f"Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
    print(f"Win Rate: {result['trading']['win_rate'] * 100:.1f}%")
```

### Querying Backtests from Database

```python
from infrastructure.supabase_client import get_admin_client

supabase = get_admin_client()

# Get user's backtests
response = supabase.table('backtests') \
    .select('*') \
    .eq('user_id', user_id) \
    .order('created_at', desc=True) \
    .execute()

backtests = response.data
```

### Monitoring Backtest Progress

Frontend listens to Status Center for real-time updates:

```typescript
// Status Center automatically displays backtest progress
// No additional code needed - uses taskManager composable
```

Backend logs progress during execution:

```python
async def run_backtest_task():
    await log(f"🎯 Preparing backtest...")
    await log(f"📊 Return: {return_pct:+.2%}")
```

## Troubleshooting

### Issue: "Insufficient data" Error

**Cause:** Not enough historical data for the selected period

**Solution:**
- Reduce the date range
- Check if symbol is available on the data provider
- Verify timeframe is supported (1m, 5m, 15m, 1h, 4h, 1d)

### Issue: Model Training Takes Too Long

**Cause:** Large dataset or slow machine

**Solution:**
- Use shorter training period (default: 30 days)
- Reduce `n_steps` parameter
- Use pre-trained models (check [Models](05-MODEL_MANAGEMENT.md))

### Issue: Backtest Stays in "Running" Status

**Cause:** Backend crashed or exception occurred

**Solution:**
- Check backend logs for errors
- Verify database connection
- Check resource usage (CPU/RAM)
- Restart backend server

### Issue: "DATA LEAKAGE DETECTED" Warning

**Cause:** Attempting to use a model trained on data that overlaps with backtest period

**Solution:**
- This is automatically handled - a new model will be trained
- If you see this, it means the system is working correctly
- Wait for the new model to train (~2-5 minutes)

### Issue: Low Win Rate or Negative Returns

**Cause:** Strategy may not be profitable for this symbol/period

**Solution:**
- Try different strategy parameters
- Test on different symbols
- Use longer backtesting periods for more reliable statistics
- Check if commission/slippage are too high

## Next Steps

- [ML & Predictions](04-ML_PREDICTIONS.md) - Understand the ML models used in strategies
- [Trading Strategies](06-TRADING_STRATEGIES.md) - Learn about available strategies
- [System Monitoring](08-SYSTEM_MONITORING.md) - Monitor backtest execution in real-time
- [Model Management](05-MODEL_MANAGEMENT.md) - Train and manage ML models
