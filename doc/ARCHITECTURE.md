# Architecture Overview

High-level architecture of the multi-user trading bot platform.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │Dashboard │ │Backtests │ │Predictions│ │Profile/API Keys │   │
│  └──────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│                            ↓ Axios HTTP + SSE                   │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ API Layer (Routers)                                       │  │
│  │ /api/backtests  /api/predictions  /api/keys  /api/system │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Service Layer                                             │  │
│  │ BacktestService │ MLService │ ApiKeyManager │ DataService│  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Domain Layer                                              │  │
│  │ Strategies │ ML Models │ Indicators │ Patterns │ Config  │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Data Layer                                                │  │
│  │ CCXT │ Alpaca │ yFinance │ Parquet Cache │ TimescaleDB  │  │
│  └───────────────────────────┬──────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Database (Supabase/PostgreSQL)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │  Users   │ │Backtests │ │Predictions│ │Encrypted API Keys│  │
│  │  (RLS)   │ │  (RLS)   │ │   (RLS)   │ │     (RLS+PGP)    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### Frontend (Vue 3 + TypeScript)

**Technology Stack:**
- Vue 3 with Composition API
- TypeScript for type safety
- Pinia for state management
- Tailwind CSS for styling
- Chart.js for visualizations
- Axios for HTTP requests
- SSE (EventSource) for real-time updates

**Architecture Pattern:** Feature-based modular structure

```
frontend/src/
├── views/           # Page components (routed)
├── components/      # Reusable UI components
│   ├── ui/          # Generic UI components (Button, Card, etc.)
│   └── layout/      # Layout components (Header, Sidebar)
├── features/        # Feature-specific modules
│   ├── dashboard/
│   └── predictions/
├── stores/          # Pinia stores (state management)
├── composables/     # Vue composition functions
├── lib/             # External service clients (Supabase)
└── router/          # Vue Router configuration
```

### Backend (FastAPI + Python 3.13)

**Technology Stack:**
- FastAPI for async REST API
- Python 3.13 for modern language features
- Pydantic for data validation
- pandas for data manipulation
- LightGBM for machine learning
- CCXT for crypto exchange integration
- Alpaca for stock trading
- Supabase for authentication and database

**Architecture Pattern:** Clean Architecture / Domain-Driven Design

```
backend/
├── api/                  # Application layer
│   ├── routers/          # FastAPI route handlers
│   ├── services/         # Business logic orchestration
│   └── auth.py           # Authentication utilities
├── domain/               # Domain layer (business logic)
│   ├── strategies/       # Trading strategies
│   ├── ml/               # Machine learning models
│   ├── indicators/       # Technical indicators
│   ├── patterns/         # Chart pattern recognition
│   └── config/           # Domain configuration
├── data/                 # Data layer
│   ├── fetchers/         # External data sources
│   ├── storage/          # Data persistence
│   └── utils/            # Data utilities
├── infrastructure/       # Infrastructure layer
│   ├── resource_manager  # CPU/RAM monitoring and queuing
│   ├── api_key_manager   # Encrypted credential storage
│   └── supabase_client   # Database client
└── backtesting/          # Backtesting engine
```

## Design Patterns

### 1. Clean Architecture

**Dependency Rule:** Dependencies point inward
- **API Layer** → **Service Layer** → **Domain Layer** → **Data Layer**
- Domain layer has NO dependencies on infrastructure
- Infrastructure depends on domain interfaces

**Example:**
```python
# Domain layer defines interface
class DataFetcher(ABC):
    @abstractmethod
    def fetch_historical_data(...) -> pd.DataFrame:
        pass

# Infrastructure implements interface
class AlpacaFetcher(DataFetcher):
    def fetch_historical_data(...) -> pd.DataFrame:
        # Implementation using Alpaca API
```

### 2. Strategy Pattern

Trading strategies are plugins that implement a common interface:

```python
class TradingStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        pass

# Implementations
class MLPredictiveStrategy(TradingStrategy):
    ...

class BreakoutScalpingStrategy(TradingStrategy):
    ...
```

Strategies are auto-discovered at runtime via registry pattern.

### 3. Repository Pattern

Data access abstracted through repositories:

```python
# Service layer
backtest_service.get_backtest(backtest_id)

# Repository layer (Supabase)
supabase.table('backtests').select('*').eq('id', backtest_id).execute()
```

### 4. Resource Manager Pattern

Custom task queue with resource awareness:

```python
# Check if resources available
if resource_manager.can_run_task(TaskType.BACKTEST):
    # Run immediately
    run_backtest(...)
else:
    # Queue for later
    task_queue.add_task(backtest_task)
```

### 5. Event-Driven Updates

Server-Sent Events (SSE) for real-time updates:

```python
# Backend broadcasts events
async def task_events():
    while True:
        event = await event_queue.get()
        yield f"data: {json.dumps(event)}\n\n"

# Frontend listens
const eventSource = new EventSource('/api/system/task-events')
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Update UI
}
```

## Security Architecture

### Multi-Layered Security

```
┌─────────────────────────────────────────┐
│ 1. Transport Security (HTTPS)           │
├─────────────────────────────────────────┤
│ 2. Authentication (JWT)                 │
│    - Supabase Auth                      │
│    - Token validation on every request  │
├─────────────────────────────────────────┤
│ 3. Authorization (RLS)                  │
│    - Row Level Security policies        │
│    - User can only see own data         │
│    - Admin role for elevated access     │
├─────────────────────────────────────────┤
│ 4. Encryption at Rest (PGP)             │
│    - API keys encrypted with pgcrypto   │
│    - Encryption key in environment      │
├─────────────────────────────────────────┤
│ 5. Audit Logging                        │
│    - All API key access logged          │
│    - Compliance and forensics           │
└─────────────────────────────────────────┘
```

### Row Level Security (RLS)

Every table with user data has RLS policies:

```sql
-- Example: backtests table
CREATE POLICY "Users can only see own backtests"
  ON backtests
  FOR SELECT
  USING (auth.uid() = user_id);
```

**Benefits:**
- Security enforced at database level
- Cannot be bypassed by application code
- Automatic filtering by user_id

## Data Flow Examples

### Creating a Backtest

```
1. User clicks "Run Backtest" in frontend
2. Frontend sends POST /api/backtests/run with params
3. Backend validates JWT token → extracts user_id
4. Resource Manager checks CPU/RAM availability
   - If available: Run immediately
   - If busy: Queue task
5. Backtest runs in background thread
6. Results saved to database with RLS (user_id = auth.uid())
7. SSE event broadcast to frontend
8. Frontend receives event → updates UI
9. User sees completed backtest in list
```

### Storing API Keys

```
1. User enters API key in Profile page
2. Frontend sends plaintext key via HTTPS POST /api/keys/
3. Backend receives with JWT auth → user_id extracted
4. ApiKeyManager encrypts key using pgcrypto
   encrypt_api_credential(plaintext, ENCRYPTION_KEY)
5. Encrypted key stored in database
6. Plaintext hint (first4...last4) stored for display
7. Audit log records "created" action
8. Frontend refreshes list, shows hint
```

### Real-Time Task Updates

```
1. Backend starts backtest task
2. Emits SSE event: {"type": "task_running", "task": {...}}
3. Frontend EventSource receives event
4. Pinia store updates taskManager state
5. Vue reactivity triggers UI update
6. Status center shows running task with progress
7. When complete, SSE event: {"type": "task_completed"}
8. UI shows success notification
```

## Scalability Considerations

### Current Architecture (Single Server)

- **Suitable for:** 10-100 concurrent users
- **Bottleneck:** Background task queue is in-memory
- **Limitations:**
  - All tasks run on single machine
  - No horizontal scaling

### Future Scaling (Recommendations)

#### 1. Distributed Task Queue (Celery + Redis)

```python
# Replace in-memory queue
from celery import Celery

celery = Celery('trading_bot', broker='redis://localhost:6379')

@celery.task
def run_backtest(user_id, params):
    # Backtest logic
```

**Benefits:**
- Horizontal scaling of workers
- Task persistence across restarts
- Priority queues

#### 2. Database Optimization

Current: Supabase (PostgreSQL)

Scale:
- Read replicas for queries
- Connection pooling (PgBouncer)
- TimescaleDB for time-series data

#### 3. Caching Layer (Redis)

```python
# Cache frequently accessed data
redis.setex(f"user:{user_id}:api_keys", 3600, json.dumps(keys))
```

#### 4. CDN for Frontend

- Static assets served from CDN
- Reduces backend load
- Faster global access

#### 5. Microservices (Future)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  API Gateway │→ │ML Service    │  │Data Service  │
└──────────────┘  └──────────────┘  └──────────────┘
       ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Auth Service  │  │Backtest Srv  │  │Trading Service│
└──────────────┘  └──────────────┘  └──────────────┘
```

## Technology Decisions

### Why FastAPI?

- **Async support**: Native async/await for concurrent requests
- **Type safety**: Pydantic validation
- **Auto docs**: OpenAPI/Swagger UI generated automatically
- **Performance**: Comparable to Node.js, faster than Flask
- **Python ecosystem**: Easy integration with ML libraries

### Why Vue 3?

- **Composition API**: Better code organization than Options API
- **TypeScript**: First-class TypeScript support
- **Reactivity**: Fine-grained reactivity system
- **Small bundle**: Smaller than React
- **Ecosystem**: Pinia, Vue Router, Vite

### Why Supabase?

- **Auth built-in**: JWT authentication out of the box
- **RLS**: Automatic multi-tenant isolation
- **Realtime**: Built-in realtime subscriptions (not using yet)
- **PostgreSQL**: Full SQL database, not NoSQL limitations
- **Open source**: Can self-host if needed

### Why Parquet for Caching?

- **Columnar storage**: 10x smaller than CSV
- **Fast reads**: Optimized for analytics
- **Type preservation**: Data types preserved
- **Pandas integration**: Native pandas support

## Performance Characteristics

### API Response Times (Measured)

- Authentication: 50-100ms
- List backtests: 100-200ms
- Run backtest: 5-60 seconds (background)
- Get predictions: 2-10 seconds (with auto-train)
- List API keys: 50-100ms (PostgREST join optimization)

### Resource Usage (Typical)

- **CPU**: 20-40% during backtest/training
- **RAM**: 500MB-2GB depending on data size
- **Disk**: ~100MB per symbol per year (parquet cache)

### Optimization Techniques Used

1. **Parquet caching**: Avoid re-fetching market data
2. **Model caching**: Reuse trained models until stale
3. **PostgREST joins**: Single query instead of N+1
4. **Background tasks**: Long operations don't block API
5. **SSE instead of polling**: Real-time updates without overhead
6. **Parallel data loading**: Frontend loads providers + keys in parallel

## Monitoring & Observability

### Current Implementation

- **System resources**: CPU/RAM via psutil
- **Task queue**: Queue length and running tasks
- **Audit logs**: API key access tracking
- **Error logging**: Print statements (TODO: structured logging)

### Recommended Additions

1. **Structured logging** (loguru)
   ```python
   logger.info("Backtest started", user_id=user_id, symbol=symbol)
   ```

2. **APM (Application Performance Monitoring)**
   - Sentry for error tracking
   - New Relic for performance monitoring

3. **Metrics** (Prometheus)
   - Request latency histogram
   - Backtest success/failure rate
   - Active user count

4. **Distributed tracing** (Jaeger)
   - Trace request through all services
   - Identify bottlenecks

## Next Steps

- [Feature Documentation](features/) - Detailed docs for each feature
- [API Reference](api/REST_API.md) - Complete API documentation
- [Database Schema](database/SCHEMA.md) - Full database structure
- [Development Guide](development/SETUP.md) - Setup and contribution guide
