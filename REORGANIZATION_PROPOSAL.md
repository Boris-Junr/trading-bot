# Backend Reorganization Proposal

## Current State Analysis

### Folder Structure

```
backend/
├── analysis/           # ML models, indicators, patterns
│   ├── indicators/     # Technical indicators (momentum, trend, volatility)
│   ├── models/         # ML predictors
│   │   ├── features/   # Feature engineering
│   │   ├── predictors/ # Autoregressive, Multi-OHLC
│   │   └── saved/      # ❌ Duplicate model storage
│   └── patterns/       # Chart patterns (reversal, continuation, triangles)
│
├── api/               # FastAPI application
│   ├── routers/       # API endpoints
│   └── services/      # ⚠️ LARGE FILES (400+ lines)
│
├── backtesting/       # Backtest engine
│   └── scenarios/     # JSON configs
│
├── config/            # Settings
├── data/              # Data fetching & storage
│   ├── fetchers/      # Alpaca, YFinance, CCXT
│   ├── portfolio/     # Portfolio classes
│   ├── storage/       # Cache, adapters
│   └── utils/         # Normalizers, detectors
│
├── strategies/        # Trading strategies
│   └── implementations/
│
├── tests/             # Unit & E2E tests
│   ├── e2e/
│   └── unit/
│
├── data_cache/        # Parquet cache (runtime)
├── models/            # ❌ Duplicate model storage
├── output/            # Backtest results (runtime)
└── *.py              # ⚠️ Root-level scripts (clutter)
```

---

## Issues Identified

### 1. **DUPLICATE MODEL STORAGE** ❌
**Problem**: Models stored in TWO locations
- `backend/models/` (used by backtesting)
- `backend/analysis/models/saved/` (legacy?)

**Impact**:
- Confusion about which is the source of truth
- Wasted disk space
- Potential version conflicts

**Recommendation**: **Keep only `backend/models/`** (top-level, clear purpose)

---

### 2. **OVERSIZED SERVICE FILES** ⚠️
**Problem**: `api/services/backtest_service.py` is **460 lines**
- Violates single responsibility principle
- Hard to navigate and test
- Mixes concerns: validation, training, execution, saving

**Example**:
```python
# backtest_service.py does TOO MUCH:
- Run backtests
- Train models
- Validate model metadata
- Save results
- List/retrieve results
- Sanitize JSON
```

**Recommendation**: **Split into focused modules** (see refactoring section)

---

### 3. **ROOT-LEVEL SCRIPT CLUTTER** ⚠️
**Problem**: Scripts in `backend/` root:
```
analyze_optimization.py
run_backtest.py
test_backtest.py
test_pagination.py
test_training_period.py
```

**Impact**:
- Harder to find actual application code
- Unclear which scripts are utilities vs tests

**Recommendation**: **Move to organized locations**

---

### 4. **UNCLEAR SEPARATION** ⚠️
**Problem**: `data/portfolio/` is isolated
- Portfolio classes are in `data/` (data layer)
- But used by backtesting (application layer)
- Not intuitive

**Recommendation**: **Move to `backtesting/portfolio/`** (belongs to backtesting domain)

---

### 5. **__init__.py NECESSITY?** ❓

**Answer**: **YES, but can be simplified**

#### Why `__init__.py` exists:
1. **Makes directories Python packages** (allows imports)
2. **Controls namespace** (what gets exported)
3. **Backwards compatibility** (Python 2 requirement, still convention)

#### Current state:
Most are **empty** or just have docstrings. This is **fine and recommended**.

#### What you CAN do:
```python
# Option 1: Keep empty (RECOMMENDED for most)
# __init__.py
""

# Option 2: Export convenience imports
# strategies/__init__.py
from .base import BaseStrategy
from .implementations import MLPredictiveStrategy

__all__ = ['BaseStrategy', 'MLPredictiveStrategy']
```

**Recommendation**: **Keep all __init__.py** (standard practice), most can stay empty

---

## Proposed Reorganization

### Target Structure

```
backend/
├── core/                    # NEW: Core domain logic
│   ├── models/              # Data models, DTOs
│   ├── exceptions/          # Custom exceptions
│   └── types/               # Type definitions
│
├── domain/                  # NEW: Business logic
│   ├── indicators/          # Move from analysis/
│   ├── patterns/            # Move from analysis/
│   ├── ml/                  # Move from analysis/models/
│   │   ├── features/
│   │   ├── predictors/
│   │   └── training/        # NEW: Split out training logic
│   └── strategies/          # Move from root strategies/
│
├── backtesting/             # Keep, add portfolio
│   ├── engine.py
│   ├── portfolio/           # Move from data/portfolio/
│   ├── scenarios/
│   └── reporting/           # NEW: CSV logger, metrics
│
├── data/                    # Data access layer only
│   ├── fetchers/
│   ├── storage/
│   └── cache/               # Rename data_cache → data/cache
│
├── api/                     # API layer
│   ├── routers/
│   ├── services/            # ⚠️ TO REFACTOR
│   │   ├── backtest/        # NEW: Split service
│   │   │   ├── runner.py
│   │   │   ├── validator.py
│   │   │   └── storage.py
│   │   ├── data.py
│   │   ├── ml.py
│   │   └── portfolio.py
│   └── models.py            # API DTOs
│
├── infrastructure/          # NEW: Cross-cutting concerns
│   ├── config/              # Move from config/
│   ├── logging/             # NEW: Centralized logging
│   └── monitoring/          # NEW: Metrics, health checks
│
├── scripts/                 # NEW: Utility scripts
│   ├── train_model.py       # Move from analysis/models/
│   ├── analyze_optimization.py
│   └── run_backtest.py
│
├── tests/                   # Keep structure
│   ├── unit/
│   ├── integration/         # Rename from e2e
│   └── fixtures/            # NEW: Shared test data
│
├── runtime/                 # NEW: Runtime artifacts (gitignored)
│   ├── models/              # Trained ML models
│   ├── cache/               # Data cache
│   └── output/              # Backtest results
│
└── requirements.txt
```

---

## Refactoring Opportunities

### 1. **Split `backtest_service.py` (460 lines)**

#### Current Monolith:
```python
class BacktestService:
    def run_backtest(...)        # Orchestration
    def _create_strategy(...)    # Strategy factory
    def _validate_model(...)     # Validation
    def _train_model(...)        # ML training
    def _save_results(...)       # Persistence
    def list_backtests(...)      # Retrieval
    def get_backtest(...)        # Retrieval
```

#### Proposed Split:

**File 1: `api/services/backtest/runner.py`** (~150 lines)
```python
class BacktestRunner:
    """Orchestrates backtest execution"""
    def run(self, config: BacktestConfig) -> BacktestResult:
        strategy = self.strategy_factory.create(...)
        engine = BacktestEngine(...)
        return engine.run(data, strategy)
```

**File 2: `api/services/backtest/validator.py`** (~100 lines)
```python
class ModelValidator:
    """Validates models for backtesting"""
    def validate_for_backtest(self, model_path, backtest_date):
        metadata = self.load_metadata(model_path)
        return self.check_overlap(metadata, backtest_date)
```

**File 3: `api/services/backtest/storage.py`** (~120 lines)
```python
class BacktestStorage:
    """Handles persistence of backtest results"""
    def save(self, result: BacktestResult) -> str
    def list_all(self) -> List[BacktestSummary]
    def get_by_id(self, id: str) -> BacktestResult
```

**File 4: `api/services/backtest/trainer.py`** (~90 lines)
```python
class ModelTrainer:
    """Trains ML models for backtesting"""
    def train_for_backtest(self, symbol, timeframe, end_date):
        data = self.fetch_training_data(...)
        model = self.train(data)
        self.save_with_metadata(model, ...)
```

---

### 2. **Extract Configuration**

**Problem**: Settings scattered across files

**Solution**: Centralized config with Pydantic

```python
# infrastructure/config/settings.py
from pydantic_settings import BaseSettings

class DataSettings(BaseSettings):
    cache_dir: Path = Path("runtime/cache")
    alpaca_api_key: str
    alpaca_secret: str

class MLSettings(BaseSettings):
    models_dir: Path = Path("runtime/models")
    default_n_steps: int = 300

class BacktestSettings(BaseSettings):
    output_dir: Path = Path("runtime/output")
    default_commission: float = 0.001

class Settings(BaseSettings):
    data: DataSettings
    ml: MLSettings
    backtest: BacktestSettings

    class Config:
        env_file = ".env"
```

---

### 3. **Add Dependency Injection**

**Problem**: Services create dependencies directly (hard to test)

**Current**:
```python
class BacktestService:
    def __init__(self):
        self.fetcher = HistoricalDataFetcher()  # ❌ Hardcoded
```

**Better**:
```python
class BacktestRunner:
    def __init__(
        self,
        fetcher: IDataFetcher,           # Interface
        validator: IModelValidator,
        trainer: IModelTrainer,
        storage: IBacktestStorage
    ):
        self.fetcher = fetcher
        # ...
```

**Benefits**:
- Easy to mock in tests
- Swap implementations (e.g., test data fetcher)
- Clear dependencies

---

### 4. **Standardize Error Handling**

**Create custom exceptions**:

```python
# core/exceptions.py
class TradingBotException(Exception):
    """Base exception"""

class DataFetchError(TradingBotException):
    """Failed to fetch data"""

class ModelTrainingError(TradingBotException):
    """Failed to train model"""

class DataLeakageError(TradingBotException):
    """Backtest/training data overlap detected"""

class InsufficientDataError(TradingBotException):
    """Not enough data for operation"""
```

**Usage**:
```python
if len(df) < min_required:
    raise InsufficientDataError(
        f"Need {min_required} bars, got {len(df)}"
    )
```

---

### 5. **Add Logging Infrastructure**

**Problem**: Print statements everywhere

**Solution**: Structured logging

```python
# infrastructure/logging/setup.py
import logging
from rich.logging import RichHandler

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

# Usage in modules
logger = logging.getLogger(__name__)
logger.info("Starting backtest", extra={
    "symbol": symbol,
    "period": f"{start} to {end}",
    "strategy": strategy_name
})
```

---

## Migration Plan

### Phase 1: Low-Risk Cleanup (Week 1)
1. ✅ Delete `analysis/models/saved/` (keep only `models/`)
2. ✅ Move root scripts to `scripts/`
3. ✅ Rename `data_cache/` → `runtime/cache/`
4. ✅ Add `runtime/` to `.gitignore`
5. ✅ Move `data/portfolio/` → `backtesting/portfolio/`

### Phase 2: Service Refactoring (Week 2)
1. Create `api/services/backtest/` directory
2. Split `backtest_service.py` into 4 files
3. Add interfaces/protocols for dependencies
4. Update routers to use new services
5. Run tests to verify

### Phase 3: Core Reorganization (Week 3)
1. Create `core/` and `domain/` directories
2. Move `analysis/*` → `domain/`
3. Create `infrastructure/` directory
4. Move `config/` → `infrastructure/config/`
5. Update all imports

### Phase 4: Enhancements (Week 4)
1. Add centralized exception handling
2. Add structured logging
3. Add dependency injection container
4. Add health check endpoints
5. Update documentation

---

## About `__init__.py` Files

### Do You Need Them?

**Short answer**: **Yes, keep them**

**Long answer**:

1. **Python 3.3+** made them optional for "namespace packages"
2. **BUT**: Having them is still best practice because:
   - Makes intent clear (this IS a package)
   - Allows explicit exports
   - Better IDE support
   - Standard convention

### What Should Be In Them?

**Most cases: Empty or minimal**

```python
# api/__init__.py
""  # Empty is fine

# or with docstring
"""
API layer for the trading bot.
Handles HTTP endpoints and request/response formatting.
"""
```

**Package root: Export key items**

```python
# strategies/__init__.py
from .base import BaseStrategy, Signal, SignalType
from .implementations import MLPredictiveStrategy

__all__ = [
    'BaseStrategy',
    'Signal',
    'SignalType',
    'MLPredictiveStrategy'
]
```

**Allows clean imports**:
```python
# Instead of:
from strategies.base import BaseStrategy
from strategies.implementations.ml_predictive_strategy import MLPredictiveStrategy

# Users can do:
from strategies import BaseStrategy, MLPredictiveStrategy
```

### Recommendation:
✅ **Keep all `__init__.py` files**
✅ **Most can be empty** (or just have docstrings)
✅ **Add exports only in package roots** (like `strategies/`, `api/`)

---

## Summary of Recommendations

### Immediate Actions (Do Now):
1. ✅ **Commit current state** (DONE)
2. ✅ **Delete duplicate model storage** (`analysis/models/saved/`)
3. ✅ **Move scripts to `scripts/` directory**
4. ✅ **Add `runtime/` to `.gitignore`**
5. ✅ **Keep all `__init__.py` files** (standard practice)

### High Priority (This Week):
1. 🔄 **Split `backtest_service.py`** into focused modules
2. 🔄 **Move `data/portfolio/` → `backtesting/portfolio/`**
3. 🔄 **Centralize configuration** with Pydantic

### Medium Priority (Next 2 Weeks):
1. ⏳ **Reorganize into `core/`, `domain/`, `infrastructure/`**
2. ⏳ **Add dependency injection**
3. ⏳ **Add structured logging**
4. ⏳ **Custom exception hierarchy**

### Low Priority (Future):
1. 📋 **Add health check endpoints**
2. 📋 **Add monitoring/metrics**
3. 📋 **Generate API documentation**
4. 📋 **Add performance profiling**

---

## Questions for You

Before proceeding with reorganization:

1. **Duplicate models**: Can I delete `backend/analysis/models/saved/` entirely?
2. **Breaking changes**: Are you OK with import path changes (will need to update code)?
3. **Timeline**: Prefer incremental (safer) or big-bang (faster) migration?
4. **Priority**: Which issues bother you most? (I'll tackle those first)

---

## Conclusion

The current codebase is **functional but messy**. The proposed reorganization will:

✅ **Improve maintainability** (smaller, focused files)
✅ **Enhance testability** (dependency injection)
✅ **Reduce confusion** (clear structure, no duplicates)
✅ **Enable scaling** (modular architecture)

**Recommendation**: Start with **Phase 1** (low-risk cleanup) and get that working, then proceed incrementally.

**Note**: All `__init__.py` files should stay - they're Python convention and don't hurt.
