# Machine Learning & Price Predictions

AI-powered price prediction system using Multi-OHLC autoregressive models with LightGBM to forecast future candlestick patterns.

## Overview

The ML predictions system provides:
- Multi-OHLC predictions (Open, High, Low, Close) for each future candlestick
- Autoregressive models that predict multiple steps ahead (up to 300 steps)
- Automatic model training and retraining based on age limits
- Real-time predictions with confidence scores
- Background task execution with progress tracking
- Multi-user support with database persistence

## Architecture

```
User Request (Frontend)
    ↓ POST /api/predictions/generate
Backend API (FastAPI)
    ↓ Check for existing model
    ├─→ Model exists & fresh → Use existing
    ├─→ Model exists & stale → Retrain
    └─→ No model → Train new
        ↓
    MLService
        ├─ Fetch historical data (60-730 days based on timeframe)
        ├─ Train Multi-OHLC Predictor (4 separate models)
        │   ├─ Open predictor (LightGBM)
        │   ├─ High predictor (LightGBM)
        │   ├─ Low predictor (LightGBM)
        │   └─ Close predictor (LightGBM)
        └─ Save model to filesystem
            ↓
    Generate Predictions
        ├─ Fetch latest market data
        ├─ Run all 4 models
        ├─ Post-process (ensure High >= max(Open, Close), etc.)
        └─ Return predictions
            ↓
    Save to Database (Supabase)
        ↓ Real-time update (PostgreSQL NOTIFY)
Frontend (Vue 3)
    ↓ Realtime subscription
    UI Update (Chart + Tables)
```

## ML Model Architecture

### Multi-OHLC Predictor

The system uses a sophisticated multi-output prediction approach:

**Why Multi-OHLC instead of single close price?**
- **Better for trading**: Knowing High/Low helps set stop loss and take profit
- **More realistic**: Captures intra-period volatility, not just end price
- **Specialized models**: Each model optimizes for its specific target
- **Smoother predictions**: Autoregressive approach produces realistic price curves

**Architecture:**
```python
MultiOHLCPredictor
├── open_predictor: AutoregressivePricePredictor
├── high_predictor: AutoregressivePricePredictor
├── low_predictor: AutoregressivePricePredictor
└── close_predictor: AutoregressivePricePredictor
```

Each predictor is trained separately on the same features but different targets.

### Autoregressive Predictor

Uses LightGBM gradient boosting with recursive multi-step prediction.

**Features Used:**
- Price features: Returns, momentum, volatility
- Technical indicators: RSI, MACD, Bollinger Bands
- Volume features: Volume changes, OBV
- Temporal features: Hour of day, day of week

**Prediction Process:**
```
1. Use last 100 bars to create features
2. Predict next price (step 1)
3. Append predicted price to history
4. Predict next price (step 2)
5. Repeat for n_steps (e.g., 300 steps)
```

**Example:**
```python
from domain.ml.predictors.multi_ohlc_predictor import MultiOHLCPredictor

# Initialize predictor
predictor = MultiOHLCPredictor(n_steps_ahead=300)

# Train
train_data, test_data = predictor.prepare_data(df, test_size=0.2)
metrics = predictor.train(train_data, validation_split=0.2, verbose=True)

# Predict
predictions = predictor.predict(df)
```

**Training Output:**
```
=== Training Multi-OHLC Predictor ===
Training 4 separate models for 300 steps ahead

[1/4] Training OPEN predictor...
Train R²: 0.9842, Val R²: 0.9635

[2/4] Training HIGH predictor...
Train R²: 0.9856, Val R²: 0.9651

[3/4] Training LOW predictor...
Train R²: 0.9849, Val R²: 0.9642

[4/4] Training CLOSE predictor...
Train R²: 0.9851, Val R²: 0.9648

=== Training Complete ===
Average across all 4 models:
  Train R²: 0.9850, RMSE: 42.5
  Val R²: 0.9644, RMSE: 58.3
```

**Predictions Format:**
```python
{
    'predicted_open_1': 42150.0,
    'predicted_high_1': 42280.0,
    'predicted_low_1': 42050.0,
    'predicted_close_1': 42200.0,
    'predicted_return_1': 0.0012,  # 0.12% return
    'predicted_open_2': 42210.0,
    # ... up to step 300
}
```

### Post-Processing

Ensures candlestick validity:
```python
# Ensure High is the highest value
predicted_high = max(predicted_open, predicted_high, predicted_close)

# Ensure Low is the lowest value
predicted_low = min(predicted_open, predicted_low, predicted_close)
```

## Backend Implementation

### Files

- **[backend/domain/ml/predictors/multi_ohlc_predictor.py](../../backend/domain/ml/predictors/multi_ohlc_predictor.py)** - Multi-OHLC predictor
- **[backend/domain/ml/predictors/autoregressive_predictor.py](../../backend/domain/ml/predictors/autoregressive_predictor.py)** - Base predictor
- **[backend/domain/ml/features/price_features.py](../../backend/domain/ml/features/price_features.py)** - Feature engineering
- **[backend/api/services/ml_service.py](../../backend/api/services/ml_service.py)** - Service layer
- **[backend/api/routers/predictions.py](../../backend/api/routers/predictions.py)** - REST API endpoints

### MLService

Service layer for ML operations.

```python
from api.services.ml_service import get_ml_service

ml_service = get_ml_service()

# Train a model
result = ml_service.train_model(
    symbol='BTC_USDT',
    timeframe='1m',
    n_steps_ahead=300,
    days_history=60  # 2 months for 1m timeframe
)

# Get predictions
predictions = ml_service.get_predictions(
    symbol='BTC_USDT',
    timeframe='1m'
)
```

**Key Methods:**

#### `train_model(symbol, timeframe, n_steps_ahead, days_history)`

Trains a new Multi-OHLC prediction model.

**Training Data Requirements:**
```python
# Optimized for each timeframe
timeframe_days = {
    '1m': 60,     # 2 months (~86k bars) - captures all sessions, volatility variety
    '5m': 90,     # 3 months (~26k bars) - monthly patterns, full cycles
    '15m': 120,   # 4 months (~11.5k bars) - seasonal variety
    '1h': 180,    # 6 months (~4.3k bars) - half-year patterns
    '4h': 365,    # 1 year (~2.2k bars) - for swing trading
    '1d': 730,    # 2 years (~730 bars) - for position trading
}
```

**Returns:**
```python
{
    'name': 'BTC_USDT_1m_300steps_multi_ohlc',
    'symbol': 'BTC_USDT',
    'timeframe': '1m',
    'n_steps': 300,
    'trained_at': '2024-01-31T12:00:00Z',
    'performance': {
        'train_r2': 0.9850,
        'train_rmse': 42.5,
        'val_r2': 0.9644,
        'val_rmse': 58.3
    }
}
```

#### `get_predictions(symbol, timeframe, model_path)`

Generates price predictions using a trained model.

**Returns:**
```python
{
    'timestamp': '2024-01-31T12:00:00Z',
    'current_price': 42000.0,
    'predictions': [
        {
            'step': 1,
            'minutes_ahead': 1,
            'timestamp': '2024-01-31T12:01:00Z',
            'predicted_open': 42150.0,
            'predicted_high': 42280.0,
            'predicted_low': 42050.0,
            'predicted_close': 42200.0,
            'predicted_return': 0.0012,
            'confidence': 0.8
        },
        # ... 299 more steps
    ],
    'smoothness_score': 0.95
}
```

**Smoothness Score:**
Measures prediction quality (0-1):
- **> 0.9**: Excellent, very smooth predictions
- **0.7-0.9**: Good, reasonable predictions
- **< 0.7**: Poor, erratic predictions (model may need retraining)

### API Endpoints

#### GET `/api/predictions/`
Get predictions for a symbol with automatic model training.

**Query Parameters:**
```
symbol: str              # Trading symbol (e.g., BTC_USDT)
timeframe: str           # Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
auto_train: bool = true  # Automatically train if model missing/stale
force_retrain: bool = false  # Force retraining even if model fresh
```

**Response:**
```json
{
  "timestamp": "2024-01-31T12:00:00Z",
  "current_price": 42000.0,
  "predictions": [
    {
      "step": 1,
      "minutes_ahead": 1,
      "timestamp": "2024-01-31T12:01:00Z",
      "predicted_open": 42150.0,
      "predicted_high": 42280.0,
      "predicted_low": 42050.0,
      "predicted_close": 42200.0,
      "predicted_return": 0.0012,
      "confidence": 0.8
    }
  ],
  "smoothness_score": 0.95,
  "model_trained": false,
  "model_name": "BTC_USDT_1m_300steps_multi_ohlc",
  "model_age_days": 1
}
```

**Model Age Limits:**
Models are automatically retrained when they exceed age limits:
```python
{
    '1m': 2,    # 2 days - very short-term, retrain frequently
    '5m': 3,    # 3 days
    '15m': 5,   # 5 days
    '1h': 7,    # 1 week
    '4h': 14,   # 2 weeks
    '1d': 30,   # 1 month - longer-term trends
}
```

**Implementation:**
```python
@router.get("/")
async def get_predictions(
    symbol: str,
    timeframe: str,
    auto_train: bool = True,
    force_retrain: bool = False
):
    # Check for existing model
    models_list = await asyncio.to_thread(ml_service.list_models)
    matching_model = next(
        (m for m in models_list
         if m['symbol'] == symbol and m['timeframe'] == timeframe),
        None
    )

    # Determine if training needed
    should_train = force_retrain
    if matching_model and auto_train:
        age_days = (datetime.now() - datetime.fromisoformat(matching_model['trained_at'])).days
        max_age = timeframe_age_limits.get(timeframe, 7)
        if age_days > max_age:
            should_train = True
    elif not matching_model and auto_train:
        should_train = True

    # Train if needed
    if should_train:
        # Check resources first
        can_run, reason = resource_monitor.can_run_task(TaskType.MODEL_TRAINING)
        if not can_run:
            raise HTTPException(503, detail=f"Insufficient resources: {reason}")

        # Determine n_steps based on timeframe
        n_steps = timeframe_to_steps.get(timeframe, 100)

        train_result = await asyncio.to_thread(
            ml_service.train_model,
            symbol=symbol,
            timeframe=timeframe,
            n_steps_ahead=n_steps,
            days_history=30
        )

    # Get predictions
    predictions_data = await asyncio.to_thread(ml_service.get_predictions, symbol, timeframe)

    return predictions_data
```

#### POST `/api/predictions/generate`
Generate predictions in the background (non-blocking).

**Request:**
```json
{
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "auto_train": true
}
```

**Response (Running):**
```json
{
  "status": "running",
  "prediction_id": "uuid",
  "message": "Prediction started. Check status at /api/predictions/{prediction_id}"
}
```

**Response (Queued):**
```json
{
  "status": "queued",
  "prediction_id": "uuid",
  "task_id": "uuid",
  "queue_position": 2,
  "message": "Prediction queued. Position in queue: 2"
}
```

**Progress Logging:**
```python
async def run_prediction_task():
    await log(f"🎯 Preparing to train new model for {symbol} ({timeframe})")
    await log(f"📊 Gathering 30 days of historical market data...")
    await log(f"🧠 Training AI model to predict 5 hours into the future...")

    # Train
    train_result = await asyncio.to_thread(ml_service.train_model, ...)

    await log(f"✅ Model training complete!")
    await log(f"🔮 Generating future price predictions...")

    # Predict
    predictions_data = await asyncio.to_thread(ml_service.get_predictions, ...)

    await log(f"💾 Saving prediction results to database...")
    await log(f"✅ Prediction complete! Results are ready to view")
```

#### GET `/api/predictions/list`
List all predictions for the current user.

**Response:**
```json
[
  {
    "id": "uuid",
    "symbol": "BTC_USDT",
    "timeframe": "1m",
    "status": "completed",
    "current_price": 42000.0,
    "created_at": "2024-01-31T12:00:00Z"
  }
]
```

#### GET `/api/predictions/{prediction_id}`
Get prediction result by ID.

**Response:**
```json
{
  "id": "uuid",
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "status": "completed",
  "result": {
    "timestamp": "2024-01-31T12:00:00Z",
    "current_price": 42000.0,
    "predictions": [...],
    "smoothness_score": 0.95
  },
  "created_at": "2024-01-31T12:00:00Z"
}
```

#### GET `/api/predictions/stream` (SSE)
Stream predictions with real-time progress updates.

**Events:**
- `status`: Progress updates for each step (check, fetch, train, predict)
- `complete`: Final prediction data
- `error`: Error messages

```javascript
const eventSource = new EventSource('/api/predictions/stream?symbol=BTC_USDT&timeframe=1m')

eventSource.addEventListener('status', (event) => {
  const data = JSON.parse(event.data)
  console.log(data.title, data.message)
})

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data)
  console.log('Predictions:', data.predictions)
})
```

### Resource Management

Predictions can require significant CPU for model training:

```python
# Check if system can handle training
resource_monitor = get_resource_monitor()
can_run, reason = resource_monitor.can_run_task(TaskType.MODEL_TRAINING)

if can_run:
    # Train immediately
    train_result = ml_service.train_model(...)
else:
    # Queue for later
    await task_queue.enqueue(TaskType.PREDICTION, run_prediction_task)
```

**Resource Limits:**
- CPU usage threshold: 80%
- RAM usage threshold: 85%
- Max concurrent training: 1 (training is CPU-intensive)

## Frontend Implementation

### Files

- **[frontend/src/views/PredictionsView.vue](../../frontend/src/views/PredictionsView.vue)** - Predictions list page
- **[frontend/src/features/predictions/components/PredictionResultsCard.vue](../../frontend/src/features/predictions/components/PredictionResultsCard.vue)** - Results display
- **[frontend/src/composables/usePredictionPolling.ts](../../frontend/src/composables/usePredictionPolling.ts)** - Polling logic

### PredictionsView

Main page for generating and viewing predictions.

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { PredictionListItem, PredictionData } from '@/types'
import api from '@/services/api'
import { supabase } from '@/lib/supabase'

const predictions = ref<PredictionListItem[]>([])
const loading = ref(false)
const showGenerateModal = ref(false)
const generating = ref(false)

const newPrediction = ref({
  symbol: 'BTC_USDT',
  timeframe: '1m'
})

const sortedPredictions = computed(() => {
  return [...predictions.value].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

async function loadPredictions() {
  loading.value = true
  try {
    predictions.value = await api.listPredictions()
  } finally {
    loading.value = false
  }
}

async function generatePrediction() {
  generating.value = true
  try {
    await api.generatePredictions(
      newPrediction.value.symbol,
      newPrediction.value.timeframe,
      true // auto_train
    )

    // Close modal - prediction runs in background
    showGenerateModal.value = false

    // Refresh list
    setTimeout(() => loadPredictions(), 1000)
  } finally {
    generating.value = false
  }
}

onMounted(async () => {
  await loadPredictions()
  setupRealtimeSubscription()
})
</script>

<template>
  <div>
    <!-- Predictions Grid -->
    <Card
      v-for="prediction in sortedPredictions"
      :key="prediction.id"
      @click="viewPrediction(prediction)"
    >
      <h3>{{ prediction.symbol }}</h3>
      <Badge>{{ prediction.timeframe }}</Badge>
      <Badge :variant="getStatusVariant(prediction.status)">
        {{ prediction.status.toUpperCase() }}
      </Badge>

      <!-- Failed Prediction -->
      <div v-if="prediction.status === 'failed'">
        {{ prediction.error }}
      </div>

      <!-- Completed Prediction -->
      <div v-else-if="prediction.status === 'completed'">
        <div>Current Price: ${{ prediction.current_price }}</div>
      </div>
    </Card>

    <!-- Generate Modal -->
    <Modal v-model="showGenerateModal" title="Generate New Prediction">
      <Select v-model="newPrediction.symbol" label="Symbol">
        <option value="BTC_USDT">BTC/USDT</option>
        <option value="ETH_USDT">ETH/USDT</option>
      </Select>

      <Select v-model="newPrediction.timeframe" label="Timeframe">
        <option value="1m">1 Minute</option>
        <option value="5m">5 Minutes</option>
        <option value="15m">15 Minutes</option>
        <option value="1h">1 Hour</option>
      </Select>

      <Button @click="generatePrediction" :disabled="generating">
        {{ generating ? 'Generating...' : 'Generate Prediction' }}
      </Button>
    </Modal>
  </div>
</template>
```

### Real-time Updates

Predictions subscribe to database changes:

```typescript
function setupRealtimeSubscription() {
  realtimeChannel = supabase
    .channel('predictions_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'predictions',
        filter: `user_id=eq.${user.value.id}`
      },
      (payload) => {
        if (payload.eventType === 'INSERT') {
          // New prediction added
          predictions.value.unshift(payload.new)
        } else if (payload.eventType === 'UPDATE') {
          // Prediction updated (status changed)
          const index = predictions.value.findIndex(p => p.id === payload.new.id)
          if (index !== -1) {
            predictions.value[index] = {
              ...predictions.value[index],
              status: payload.new.status,
              result: payload.new.result
            }
          }
        }
      }
    )
    .subscribe()
}
```

### PredictionResultsCard

Displays prediction results with interactive chart.

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { PredictionData } from '@/types'
import { Line } from 'vue-chartjs'

const props = defineProps<{
  data: PredictionData
}>()

// Prepare chart data
const chartData = computed(() => {
  const labels = props.data.predictions.map(p => p.timestamp)

  return {
    labels,
    datasets: [
      {
        label: 'Predicted High',
        data: props.data.predictions.map(p => p.predicted_high),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
      },
      {
        label: 'Predicted Close',
        data: props.data.predictions.map(p => p.predicted_close),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
      },
      {
        label: 'Predicted Low',
        data: props.data.predictions.map(p => p.predicted_low),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
      }
    ]
  }
})
</script>

<template>
  <div>
    <div class="mb-4">
      <div>Current Price: ${{ data.current_price }}</div>
      <div>Smoothness: {{ (data.smoothness_score * 100).toFixed(1) }}%</div>
    </div>

    <!-- Chart -->
    <Line :data="chartData" :options="chartOptions" />

    <!-- Predictions Table -->
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Open</th>
          <th>High</th>
          <th>Low</th>
          <th>Close</th>
          <th>Return</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="pred in data.predictions.slice(0, 10)" :key="pred.step">
          <td>{{ formatTime(pred.timestamp) }}</td>
          <td>${{ pred.predicted_open.toFixed(2) }}</td>
          <td>${{ pred.predicted_high.toFixed(2) }}</td>
          <td>${{ pred.predicted_low.toFixed(2) }}</td>
          <td>${{ pred.predicted_close.toFixed(2) }}</td>
          <td :class="pred.predicted_return >= 0 ? 'text-green' : 'text-red'">
            {{ (pred.predicted_return * 100).toFixed(2) }}%
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

## Database Schema

### `predictions` Table

```sql
CREATE TABLE public.predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Prediction configuration
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,

  -- Status tracking
  status TEXT NOT NULL DEFAULT 'running',  -- 'running', 'completed', 'failed'
  error TEXT,

  -- Results (JSONB)
  result JSONB,  -- Full prediction data
  current_price NUMERIC(20, 8),

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,

  CONSTRAINT predictions_status_check CHECK (status IN ('running', 'queued', 'completed', 'failed'))
);

-- Indexes
CREATE INDEX idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX idx_predictions_created_at ON public.predictions(created_at DESC);
CREATE INDEX idx_predictions_status ON public.predictions(status);
CREATE INDEX idx_predictions_symbol_timeframe ON public.predictions(symbol, timeframe);

-- Row Level Security
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own predictions"
  ON public.predictions
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own predictions"
  ON public.predictions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own predictions"
  ON public.predictions
  FOR UPDATE
  USING (auth.uid() = user_id);
```

**JSONB `result` Column:**
```json
{
  "timestamp": "2024-01-31T12:00:00Z",
  "current_price": 42000.0,
  "smoothness_score": 0.95,
  "predictions": [
    {
      "step": 1,
      "minutes_ahead": 1,
      "timestamp": "2024-01-31T12:01:00Z",
      "predicted_open": 42150.0,
      "predicted_high": 42280.0,
      "predicted_low": 42050.0,
      "predicted_close": 42200.0,
      "predicted_return": 0.0012,
      "confidence": 0.8
    }
  ]
}
```

## Model Storage

Models are saved to the filesystem in a structured format:

```
backend/analysis/models/saved/
└── BTC_USDT_1m_300steps_multi_ohlc/
    ├── config.pkl               # Model configuration
    ├── training_metadata.json   # Training info
    ├── open/
    │   ├── model.txt           # LightGBM model (text format)
    │   ├── config.pkl
    │   └── features.json
    ├── high/
    │   └── ...
    ├── low/
    │   └── ...
    └── close/
        └── ...
```

**training_metadata.json:**
```json
{
  "symbol": "BTC_USDT",
  "timeframe": "1m",
  "n_steps": 300,
  "training_start": "2024-01-01T00:00:00Z",
  "training_end": "2024-01-31T00:00:00Z",
  "created_at": "2024-01-31T12:00:00Z",
  "backtest_safe_from": "2024-01-31T00:00:00Z"
}
```

## Performance Metrics

### Training Performance

**Typical Training Times:**
- 1m timeframe: 2-4 minutes (60 days, ~86k bars)
- 5m timeframe: 1-2 minutes (90 days, ~26k bars)
- 15m timeframe: 30-60 seconds (120 days, ~11.5k bars)
- 1h timeframe: 20-40 seconds (180 days, ~4.3k bars)

**Model Accuracy (R² score):**
- **> 0.95**: Excellent - very predictable market conditions
- **0.85-0.95**: Good - normal conditions
- **0.70-0.85**: Fair - volatile conditions
- **< 0.70**: Poor - highly chaotic market (may need more data or different features)

### Prediction Performance

**API Response Times:**
- With existing model: 1-3 seconds
- With training: 2-5 minutes (depends on timeframe and data size)
- Background mode: Immediate response (runs in background)

## Common Patterns

### Generate Predictions from CLI

```python
from api.services.ml_service import get_ml_service

ml_service = get_ml_service()

# Train model
train_result = ml_service.train_model(
    symbol='BTC_USDT',
    timeframe='1m',
    n_steps_ahead=300,
    days_history=60
)

print(f"Trained model: {train_result['name']}")
print(f"Val R²: {train_result['performance']['val_r2']:.4f}")

# Get predictions
predictions = ml_service.get_predictions('BTC_USDT', '1m')

print(f"Current price: ${predictions['current_price']:.2f}")
print(f"First 5 predictions:")
for pred in predictions['predictions'][:5]:
    print(f"  Step {pred['step']}: Close=${pred['predicted_close']:.2f}, Return={pred['predicted_return']*100:.2f}%")
```

### Use Predictions in Trading Strategy

```python
from domain.strategies import Strategy, Signal, SignalType

class MLPredictiveStrategy(Strategy):
    def __init__(self, model_path: str):
        self.predictor = MultiOHLCPredictor()
        self.predictor.load(model_path)

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        # Get predictions
        predictions = self.predictor.predict(data)

        # Extract next predicted return
        predicted_return_1 = predictions['predicted_return_1'].iloc[0]

        # Generate signal based on prediction
        if predicted_return_1 > 0.002:  # > 0.2% predicted gain
            return Signal(SignalType.BUY, confidence=0.8)
        elif predicted_return_1 < -0.002:  # < -0.2% predicted loss
            return Signal(SignalType.SELL, confidence=0.8)
        else:
            return Signal(SignalType.HOLD)
```

## Troubleshooting

### Issue: "Insufficient data for training"

**Cause:** Not enough historical data available

**Solution:**
- Reduce `days_history` parameter
- Check if symbol is available on the data provider
- Verify timeframe is supported

### Issue: Training Takes Too Long

**Cause:** Large dataset or slow machine

**Solution:**
- Reduce `days_history`
- Reduce `n_steps_ahead`
- Use a more powerful machine
- Enable background mode (returns immediately)

### Issue: Low R² Score (< 0.7)

**Cause:** Market conditions too volatile or not enough training data

**Solution:**
- Increase `days_history` to get more diverse market conditions
- Try different timeframe (longer timeframes are more predictable)
- Check if data quality is good (no gaps, no errors)
- Consider that some markets are inherently unpredictable

### Issue: Predictions Look Unrealistic

**Cause:** Model overfitting or data issues

**Solution:**
- Check `smoothness_score` (should be > 0.7)
- Retrain with more data
- Verify historical data doesn't have errors
- Check if post-processing is working (High >= Close, Low <= Close)

### Issue: "Model is X days old, retraining..."

**Cause:** Model exceeded age limit for its timeframe

**Solution:**
- This is expected behavior - model will be retrained automatically
- Wait for retraining to complete (~2-5 minutes)
- Consider using longer timeframe if frequent retraining is annoying

## Next Steps

- [Model Management](05-MODEL_MANAGEMENT.md) - Train and manage ML models
- [Trading Strategies](06-TRADING_STRATEGIES.md) - Use predictions in strategies
- [Backtesting](03-BACKTESTING.md) - Test predictive strategies
- [System Monitoring](08-SYSTEM_MONITORING.md) - Monitor training/prediction tasks
