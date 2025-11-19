# API Reference

Complete reference for all REST API endpoints in the trading bot backend.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication via Supabase. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Table of Contents

1. [Health Check](#health-check)
2. [API Keys Management](#api-keys-management)
3. [Market Data](#market-data)
4. [ML Models](#ml-models)
5. [Predictions](#predictions)
6. [Backtests](#backtests)
7. [Trading Strategies](#trading-strategies)
8. [System Resources & Monitoring](#system-resources--monitoring)
9. [Portfolio](#portfolio)

---

## Health Check

### GET /api/health

Check if the API is running.

**Authentication:** None required

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## API Keys Management

Endpoints for storing and managing encrypted API keys for exchanges (Binance, Alpaca, etc.).

### GET /api/keys/

List all API keys for the authenticated user.

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "provider_id": "binance",
    "provider_name": "Binance",
    "environment": "testnet",
    "label": "My Trading Account",
    "api_key_hint": "abcd...1234",
    "api_secret_hint": "wxyz...5678",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### POST /api/keys/

Store new API credentials (encrypted).

**Authentication:** Required

**Request Body:**
```json
{
  "provider_id": "binance",
  "environment": "testnet",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "label": "My Trading Account"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "API key stored successfully"
}
```

**Notes:**
- Keys are encrypted before storage using environment-specific encryption key
- Only hints (first 4 + last 4 chars) are stored in plaintext

### PUT /api/keys/{api_key_id}

Update an existing API key.

**Authentication:** Required

**Path Parameters:**
- `api_key_id` (string): UUID of the API key to update

**Request Body:**
```json
{
  "api_key": "new-api-key",
  "api_secret": "new-api-secret",
  "label": "Updated Label"
}
```

**Notes:**
- All fields are optional
- Omit `api_key` or `api_secret` to keep existing values

**Response:**
```json
{
  "message": "API key updated successfully"
}
```

### DELETE /api/keys/{api_key_id}

Deactivate (soft delete) an API key.

**Authentication:** Required

**Path Parameters:**
- `api_key_id` (string): UUID of the API key to delete

**Response:**
```json
{
  "message": "API key deleted successfully"
}
```

**Errors:**
- `404`: API key not found

---

## Market Data

Endpoints for fetching historical market data and available trading symbols.

### GET /api/market/data

Get historical OHLCV candles for a trading pair.

**Authentication:** None required

**Query Parameters:**
- `symbol` (string, required): Trading pair (e.g., `BTC_USDT`, `AAPL`)
- `timeframe` (string, required): Candle timeframe (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`)
- `start` (string, optional): Start date in ISO format
- `end` (string, optional): End date in ISO format

**Example Request:**
```
GET /api/market/data?symbol=ETH_USDT&timeframe=1h&start=2025-01-01T00:00:00Z&end=2025-01-15T00:00:00Z
```

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00Z",
    "open": 2300.50,
    "high": 2350.75,
    "low": 2280.00,
    "close": 2345.25,
    "volume": 15234.56
  }
]
```

**Notes:**
- Data is fetched from cache (Parquet/TimescaleDB) if available
- Falls back to exchange APIs (Binance for crypto, Alpaca/yFinance for stocks)
- Symbol type is auto-detected based on naming convention

### GET /api/market/symbols

Get list of available trading symbols.

**Authentication:** None required

**Query Parameters:**
- `asset_type` (string, optional): Filter by type - `crypto`, `forex`, `indices`, or `all` (default)

**Example Requests:**
```
GET /api/market/symbols
GET /api/market/symbols?asset_type=crypto
GET /api/market/symbols?asset_type=forex
```

**Response:**
```json
{
  "symbols": [
    "BTC_USDT",
    "ETH_USDT",
    "SOL_USDT"
  ],
  "asset_type": "crypto"
}
```

---

## ML Models

Endpoints for managing and training machine learning models.

### GET /api/models/

Get all trained ML models.

**Authentication:** None required

**Response:**
```json
[
  {
    "name": "ETH_USDT_1m_300steps_multi_ohlc",
    "type": "multi_ohlc",
    "symbol": "ETH_USDT",
    "timeframe": "1m",
    "n_steps_ahead": 300,
    "model_size_kb": 2456.78,
    "trained_at": "2025-01-15T08:30:00Z",
    "performance": {
      "train_r2": 0.9234,
      "val_r2": 0.8876,
      "train_mae": 12.45,
      "val_mae": 15.32,
      "train_rmse": 18.67,
      "val_rmse": 22.14
    }
  }
]
```

**Notes:**
- Returns all models found in `backend/analysis/models/saved/`
- Performance metrics include R² scores and error metrics

### GET /api/models/{model_name}

Get detailed information about a specific model.

**Authentication:** None required

**Path Parameters:**
- `model_name` (string): Name of the model (e.g., `ETH_USDT_1m_300steps_multi_ohlc`)

**Response:** Same format as single item from GET /api/models/

**Errors:**
- `404`: Model not found

### POST /api/models/train

Train a new ML model with resource checking and queuing.

**Authentication:** None required

**Request Body:**
```json
{
  "symbol": "ETH_USDT",
  "timeframe": "1m",
  "n_steps_ahead": 300,
  "days_history": 30
}
```

**Response (immediate execution):**
```json
{
  "name": "ETH_USDT_1m_300steps_multi_ohlc",
  "type": "multi_ohlc",
  "symbol": "ETH_USDT",
  "timeframe": "1m",
  "n_steps_ahead": 300,
  "model_size_kb": 2456.78,
  "trained_at": "2025-01-15T08:30:00Z",
  "performance": {
    "train_r2": 0.9234,
    "val_r2": 0.8876,
    "train_mae": 12.45,
    "val_mae": 15.32,
    "train_rmse": 18.67,
    "val_rmse": 22.14
  }
}
```

**Response (queued due to insufficient resources):**
```json
{
  "status": "queued",
  "task_id": "uuid",
  "queue_position": 3,
  "reason": "Insufficient RAM: 8.5 GB available, 12.0 GB required",
  "message": "Model training queued due to insufficient resources. Position in queue: 3"
}
```

**Notes:**
- Training is CPU/RAM intensive and can take 2-5 minutes
- Model is automatically saved to filesystem upon completion
- Training uses LightGBM with 100+ engineered technical indicators

**Errors:**
- `500`: Training failed (e.g., insufficient historical data)

---

## Predictions

Endpoints for generating and managing price predictions.

### GET /api/predictions/

Get predictions for a symbol (synchronous, may train model if needed).

**Authentication:** None required

**Query Parameters:**
- `symbol` (string, required): Trading symbol (e.g., `ETH_USDT`)
- `timeframe` (string, required): Timeframe (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`)
- `auto_train` (boolean, optional): Auto-train if no model exists or is outdated (default: `true`)
- `force_retrain` (boolean, optional): Force retraining even if model is fresh (default: `false`)

**Example Request:**
```
GET /api/predictions/?symbol=ETH_USDT&timeframe=1m&auto_train=true
```

**Response:**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "current_price": 2345.67,
  "predictions": [
    {
      "step": 1,
      "minutes_ahead": 1,
      "predicted_open": 2346.12,
      "predicted_high": 2348.50,
      "predicted_low": 2344.80,
      "predicted_close": 2347.25,
      "predicted_return": 0.000673,
      "confidence": 0.85,
      "timestamp": "2025-01-15T10:31:00Z"
    }
  ],
  "smoothness_score": 0.92,
  "model_trained": false,
  "model_name": "ETH_USDT_1m_300steps_multi_ohlc",
  "model_age_days": 1
}
```

**Notes:**
- Returns predictions for next N steps (e.g., 300 steps = 5 hours for 1m timeframe)
- Model age limits vary by timeframe (1m: 2 days, 1h: 7 days, 1d: 30 days)
- Synchronous endpoint - may block for 2-5 minutes if training needed

**Errors:**
- `503`: Training required but insufficient resources
- `500`: Prediction generation failed

### POST /api/predictions/generate

Generate predictions in the background (non-blocking).

**Authentication:** Required

**Query Parameters:**
- `symbol` (string, required): Trading symbol
- `timeframe` (string, required): Timeframe
- `auto_train` (boolean, optional): Auto-train if needed (default: `true`)

**Example Request:**
```
POST /api/predictions/generate?symbol=ETH_USDT&timeframe=1m&auto_train=true
```

**Response (queued):**
```json
{
  "status": "queued",
  "prediction_id": "uuid",
  "task_id": "uuid",
  "queue_position": 2,
  "reason": "Insufficient RAM: 8.5 GB available, 12.0 GB required",
  "message": "Prediction queued. Position in queue: 2. Check status at /api/predictions/{prediction_id}"
}
```

**Response (running immediately):**
```json
{
  "status": "running",
  "prediction_id": "uuid",
  "message": "Prediction started. Check status at /api/predictions/{prediction_id}"
}
```

**Notes:**
- Predictions are saved to Supabase `predictions` table
- Progress can be monitored via Status Center SSE stream
- Use GET /api/predictions/{prediction_id} to retrieve results

### GET /api/predictions/list

Get list of all predictions for authenticated user.

**Authentication:** Required

**Response:**
```json
[
  {
    "id": "uuid",
    "symbol": "ETH_USDT",
    "timeframe": "1m",
    "status": "completed",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### GET /api/predictions/{prediction_id}

Get prediction result by ID.

**Authentication:** Required

**Path Parameters:**
- `prediction_id` (string): UUID of the prediction

**Response:** Same format as GET /api/predictions/ response

**Errors:**
- `404`: Prediction not found or doesn't belong to user

### GET /api/predictions/stream

Stream predictions with real-time progress via Server-Sent Events.

**Authentication:** None required

**Query Parameters:**
- `symbol` (string, required): Trading symbol
- `timeframe` (string, required): Timeframe

**Example Request:**
```
GET /api/predictions/stream?symbol=ETH_USDT&timeframe=1m
```

**SSE Events:**

1. **status** - Progress updates
```json
{
  "step": "check",
  "status": "in-progress",
  "title": "Checking for model",
  "message": "Looking for trained model..."
}
```

2. **complete** - Final prediction data
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "current_price": 2345.67,
  "predictions": [...],
  "model_name": "ETH_USDT_1m_300steps_multi_ohlc"
}
```

3. **error** - Error message
```json
{
  "message": "Failed to train model"
}
```

**Steps:**
- `check`: Checking for existing model
- `fetch`: Fetching market data
- `train`: Training/loading model
- `predict`: Generating predictions

---

## Backtests

Endpoints for running and managing strategy backtests.

### GET /api/backtests/

Get list of all backtest results.

**Authentication:** None required

**Response:**
```json
[
  {
    "id": "uuid",
    "status": "success",
    "strategy": "MLPredictive",
    "symbol": "ETH_USDT",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-15T00:00:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "performance": {
      "total_return": 0.1234,
      "sharpe_ratio": 1.45,
      "max_drawdown": -0.0856,
      "win_rate": 0.62
    },
    "trading": {
      "total_trades": 42,
      "winning_trades": 26,
      "losing_trades": 16,
      "avg_win": 45.67,
      "avg_loss": -23.45
    }
  }
]
```

**Notes:**
- Returns both successful and failed backtests
- Failed backtests include `error` field instead of performance metrics

### GET /api/backtests/{backtest_id}

Get detailed backtest results by ID.

**Authentication:** None required

**Path Parameters:**
- `backtest_id` (string): UUID of the backtest

**Response:**
```json
{
  "strategy": "MLPredictive",
  "symbol": "ETH_USDT",
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-01-15T00:00:00Z",
  "performance": {
    "total_return": 0.1234,
    "sharpe_ratio": 1.45,
    "max_drawdown": -0.0856,
    "win_rate": 0.62,
    "sortino_ratio": 1.87,
    "calmar_ratio": 1.44
  },
  "trading": {
    "total_trades": 42,
    "winning_trades": 26,
    "losing_trades": 16,
    "avg_win": 45.67,
    "avg_loss": -23.45,
    "avg_trade_duration": 125.5,
    "profit_factor": 1.95
  }
}
```

**Errors:**
- `404`: Backtest not found

### POST /api/backtests/run

Run a new backtest in background with task queuing.

**Authentication:** Required

**Request Body:**
```json
{
  "strategy": "MLPredictive",
  "symbol": "ETH_USDT",
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-01-15T00:00:00Z",
  "initial_capital": 10000.0,
  "params": {
    "model_path": "ETH_USDT_1m_300steps_multi_ohlc",
    "position_size": 0.1,
    "stop_loss_pct": 0.02
  }
}
```

**Response (queued):**
```json
{
  "status": "queued",
  "backtest_id": "uuid",
  "task_id": "uuid",
  "queue_position": 1,
  "message": "Backtest queued. Position in queue: 1"
}
```

**Response (running immediately):**
```json
{
  "status": "running",
  "backtest_id": "uuid",
  "message": "Backtest started in background. Check Status Center for progress."
}
```

**Notes:**
- Backtests are saved to `backend/output/backtests/` as JSON files
- Progress can be monitored via Status Center SSE stream
- Failed backtests are saved with `status: "failed"` and error message

**Errors:**
- `500`: Backtest failed to start

### GET /api/backtests/stream

Stream backtest execution with real-time progress (legacy, not used by frontend).

**Authentication:** None required

**Query Parameters:**
- `strategy` (string, required): Strategy name
- `symbol` (string, required): Trading symbol
- `start_date` (string, required): ISO format start date
- `end_date` (string, required): ISO format end date
- `initial_capital` (float, required): Starting cash
- `params` (string, optional): JSON string of strategy parameters

**SSE Events:** Similar to predictions stream

**Notes:**
- This endpoint is deprecated in favor of POST /run with Status Center monitoring

---

## Trading Strategies

Endpoints for managing trading strategies (mostly mock data).

### GET /api/strategies/available

Get list of available strategy types (auto-discovered).

**Authentication:** None required

**Response:**
```json
[
  {
    "name": "MLPredictive",
    "description": "ML-based predictive strategy using trained models",
    "parameters": {
      "model_path": {
        "type": "string",
        "required": true,
        "description": "Path to trained model"
      },
      "position_size": {
        "type": "float",
        "required": false,
        "default": 0.1,
        "description": "Position size as fraction of capital"
      }
    }
  }
]
```

**Notes:**
- Strategies are auto-discovered from `backend/domain/strategies/` directory
- Uses strategy registry with `@register_strategy` decorator

### GET /api/strategies/

Get all configured trading strategies (mock data).

**Authentication:** None required

**Response:**
```json
[
  {
    "id": "ml-pred-1",
    "name": "ML Predictive Strategy",
    "type": "MLPredictive",
    "status": "active",
    "params": {
      "symbols": ["ETH_USDT", "BTC_USDT"],
      "timeframe": "1m",
      "model_path": "ETH_USDT_1m_300steps_autoregressive"
    },
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### GET /api/strategies/{strategy_id}

Get strategy details by ID (mock data).

**Authentication:** None required

**Errors:**
- `404`: Strategy not found

### POST /api/strategies/

Create a new strategy (mock data).

**Authentication:** None required

**Request Body:**
```json
{
  "name": "My New Strategy",
  "type": "MLPredictive",
  "params": {
    "symbols": ["BTC_USDT"],
    "timeframe": "5m"
  }
}
```

### PUT /api/strategies/{strategy_id}

Update an existing strategy (mock data).

**Authentication:** None required

### DELETE /api/strategies/{strategy_id}

Delete a strategy (mock data).

**Authentication:** None required

### POST /api/strategies/{strategy_id}/activate

Activate a strategy for live trading (mock data).

**Authentication:** None required

### POST /api/strategies/{strategy_id}/deactivate

Deactivate a strategy (mock data).

**Authentication:** None required

---

## System Resources & Monitoring

Endpoints for monitoring system resources and task queue status.

### GET /api/system/resources

Get current system resources and task queue status.

**Authentication:** Required

**Response (admin user):**
```json
{
  "resources": {
    "cpu": {
      "available_cores": 8,
      "in_use_cores": 2.5,
      "usage_percent": 31.25
    },
    "ram": {
      "total_gb": 16.0,
      "available_gb": 8.5,
      "in_use_gb": 7.5,
      "usage_percent": 46.88
    }
  },
  "queue": {
    "running_count": 1,
    "queued_count": 2,
    "running_tasks": [
      {
        "task_id": "uuid",
        "task_type": "backtest",
        "estimated_cpu_cores": 2.0,
        "estimated_ram_gb": 4.0,
        "description": "Running backtest for ETH_USDT..."
      }
    ],
    "queued_tasks": [
      {
        "task_id": "uuid",
        "task_type": "model_training",
        "queue_position": 1,
        "estimated_cpu_cores": 4.0,
        "estimated_ram_gb": 8.0,
        "queued_at": "2025-01-15T10:30:00Z"
      }
    ]
  },
  "is_admin": true
}
```

**Response (non-admin user):**
```json
{
  "queue": {
    "running_count": 1,
    "queued_count": 0,
    "running_tasks": [
      {
        "task_id": "uuid",
        "task_type": "prediction",
        "description": "Generating predictions for BTC_USDT..."
      }
    ],
    "queued_tasks": []
  },
  "is_admin": false
}
```

**Notes:**
- Non-admin users see only their own tasks
- Admin users see all tasks and system resource metrics
- This is the primary endpoint for Status Center

### GET /api/system/resources-only

Get system resources only (CPU/RAM, no queue status).

**Authentication:** Required (admin only)

**Response:**
```json
{
  "resources": {
    "cpu": {
      "available_cores": 8,
      "in_use_cores": 2.5,
      "usage_percent": 31.25
    },
    "ram": {
      "total_gb": 16.0,
      "available_gb": 8.5,
      "in_use_gb": 7.5,
      "usage_percent": 46.88
    }
  }
}
```

**Errors:**
- `401`: Unauthorized (non-admin user)

### GET /api/system/queue

Get task queue status only (no system resources).

**Authentication:** Required

**Response:**
```json
{
  "running_count": 1,
  "queued_count": 2,
  "running_tasks": [...],
  "queued_tasks": [...]
}
```

**Notes:**
- Non-admin users see only their own tasks

### GET /api/system/task-events

Stream task status events via Server-Sent Events (SSE).

**Authentication:** Required

**Query Parameters:**
- `token` (string, optional): JWT token as query parameter (for EventSource compatibility)

**Alternative:**
- Use `Authorization: Bearer <token>` header

**SSE Events:**

1. **initial_state** - Current state on connection
```json
{
  "type": "initial_state",
  "data": {
    "running_count": 1,
    "queued_count": 2,
    "running_tasks": [...],
    "queued_tasks": [...]
  },
  "is_admin": false
}
```

2. **task_queued** - New task queued
```json
{
  "type": "task_queued",
  "data": {
    "task_id": "uuid",
    "task_type": "backtest",
    "queue_position": 3
  }
}
```

3. **task_running** - Task started running
```json
{
  "type": "task_running",
  "data": {
    "task_id": "uuid",
    "task_type": "backtest",
    "description": "Running backtest for ETH_USDT..."
  }
}
```

4. **task_completed** - Task finished
```json
{
  "type": "task_completed",
  "data": {
    "task_id": "uuid"
  }
}
```

5. **task_description_update** - Task description updated
```json
{
  "type": "task_description_update",
  "data": {
    "task_id": "uuid",
    "description": "Fetching historical data..."
  }
}
```

6. **heartbeat** - Periodic update (every 5 seconds)
```json
{
  "type": "heartbeat",
  "timestamp": "2025-01-15T10:30:00Z",
  "resources": {
    "cpu": {...},
    "ram": {...}
  },
  "is_admin": true
}
```

**Notes:**
- Admin users receive resource metrics in heartbeat events
- Non-admin users receive only their own task events
- Connection is persistent and auto-reconnects on disconnect

---

## Portfolio

Mock endpoints for portfolio management (not yet implemented).

### GET /portfolio

Get current portfolio state (mock data).

**Authentication:** None required

**Response:**
```json
{
  "total_value": 12345.67,
  "cash": 5000.00,
  "positions": [
    {
      "symbol": "ETH_USDT",
      "side": "long",
      "quantity": 3.0,
      "entry_price": 2300.00,
      "current_price": 2345.67,
      "pnl": 137.01,
      "pnl_pct": 1.98,
      "opened_at": "2025-01-15T08:30:00Z"
    }
  ],
  "daily_pnl": 145.50,
  "daily_pnl_pct": 1.18,
  "total_pnl": 534.23,
  "total_pnl_pct": 4.52
}
```

### GET /portfolio/history

Get portfolio value history (mock data).

**Authentication:** None required

**Query Parameters:**
- `days` (int, optional): Number of days of history (default: 30)

**Response:**
```json
[
  {
    "date": "2025-01-01T00:00:00Z",
    "value": 10000.00
  },
  {
    "date": "2025-01-02T00:00:00Z",
    "value": 10150.50
  }
]
```

---

## Error Responses

All endpoints use standard HTTP status codes and return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or invalid token
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server-side error
- `503 Service Unavailable` - Temporary unavailability (e.g., insufficient resources)

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions may include:
- Per-user request limits
- Per-endpoint throttling
- Resource-based throttling for expensive operations

---

## WebSocket Support

Currently, real-time updates use Server-Sent Events (SSE). Future versions may add WebSocket support for:
- Live market data streaming
- Order execution updates
- Portfolio changes

---

## Related Documentation

- [Authentication & Security](03-AUTHENTICATION-SECURITY.md)
- [System Monitoring](04-SYSTEM-MONITORING.md)
- [Market Data](05-MARKET-DATA.md)
- [Model Management](07-MODEL-MANAGEMENT.md)
