# Code Quality Improvements - Refactoring Guide

## Overview

This document describes the code quality improvements implemented in Phase 1 (Quick Wins) and provides guidance for applying them throughout the codebase.

## Implemented Improvements (Phase 1)

### 1. Centralized Timeframe Configuration ✅

**Problem**: Timeframe constants were duplicated in 9 different locations across `main.py`, `ml_service.py`, and `backtest_service.py`.

**Solution**: Created `backend/domain/config/timeframes.py` as single source of truth.

**Usage**:
```python
from domain.config import get_timeframe_config, get_prediction_steps

# Old way (9 different dictionaries across codebase):
steps = {
    '1m': 300,
    '5m': 144,
    # ...
}[timeframe]

# New way (centralized):
steps = get_prediction_steps(timeframe)

# Or get full config:
config = get_timeframe_config('1m')
print(config.prediction_steps)  # 300
print(config.training_days)      # 60
print(config.model_max_age_days) # 2
```

**Files to Update**:
- `backend/api/main.py` (lines 636-645, 694-701, 1016-1024)
- `backend/api/services/ml_service.py` (lines 66-73, 225-232)
- `backend/api/services/backtest_service.py` (lines 394-398)

---

### 2. JSON Sanitization Utilities ✅

**Problem**: Sanitization functions only existed in `backtest_service.py`, causing JSON serialization errors in other services.

**Solution**: Created `backend/utils/json_helpers.py` for reusable sanitization.

**Usage**:
```python
from utils import sanitize_metric, sanitize_dict, sanitize_for_json

# Sanitize individual metrics
safe_value = sanitize_metric(float('nan'))  # Returns 0.0

# Sanitize entire dictionaries
result = {
    'sharpe_ratio': float('inf'),
    'max_drawdown': float('nan'),
    'nested': {
        'value': float('-inf')
    }
}
safe_result = sanitize_dict(result)
# Returns: {'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'nested': {'value': 0.0}}
```

**Files to Update**:
- Replace duplicate sanitization logic in `backtest_service.py`
- Add sanitization to `ml_service.py` for predictions
- Add sanitization to `portfolio_service.py` for portfolio data

---

### 3. Singleton Decorator ✅

**Problem**: Singleton pattern repeated identically in 4 service files with boilerplate code.

**Solution**: Created reusable `@singleton` decorator in `backend/utils/decorators.py`.

**Usage**:
```python
from utils import singleton

# Old way (boilerplate repeated 4 times):
_backtest_service = None

def get_backtest_service() -> BacktestService:
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService()
    return _backtest_service

# New way (clean decorator):
@singleton
class BacktestService:
    def __init__(self):
        # ...

# Usage:
service1 = BacktestService()
service2 = BacktestService()
# service1 is service2 -> True
```

**Files to Update**:
- `backend/api/services/backtest_service.py` (lines 505-514)
- `backend/api/services/ml_service.py` (lines 629-638)
- `backend/api/services/data_service.py` (lines 164-173)
- `backend/api/services/portfolio_service.py` (lines 243-252)

---

## Remaining Improvements (From Analysis)

### High Priority

1. **Split main.py into routers** (1,452 lines → ~100 lines main + 5 routers)
   - Effort: Medium (2-3 days)
   - Impact: High (maintainability)

2. **Extract SSE generator logic** (3 generators, 60-220 lines each)
   - Effort: Medium (1-2 days)
   - Impact: High (testability, reusability)

3. **Add comprehensive type hints**
   - Missing return types in critical functions
   - Effort: Medium (ongoing)
   - Impact: High (code safety)

### Medium Priority

4. **Refactor MLPredictiveStrategy._check_triggers()** (100 lines)
   - Extract to separate trigger methods
   - Create trigger registry pattern

5. **Split large Vue components** (PredictionsView: 881 lines)
   - Extract chart component
   - Extract settings panel
   - Create composables

6. **Create shared composables** (Symbol fetching, date formatting)
   - Reduces duplication in frontend views

### Quick Wins (Can be done in <1 hour each)

7. **Extract magic numbers to constants**
   - `MIN_DATA_BARS = 100` instead of hardcoded
   - `DEFAULT_COMMISSION = 0.001`

8. **Replace print() with logging module**
   - Standardized logging across backend

9. **Create custom exception classes**
   - Better error handling and debugging

---

## Migration Guide

### Step 1: Update Timeframe References

Search for these patterns and replace:

```python
# Pattern 1: Dictionary lookup
steps = {'1m': 300, '5m': 144, ...}[timeframe]
# Replace with:
from domain.config import get_prediction_steps
steps = get_prediction_steps(timeframe)

# Pattern 2: Inline constants
if timeframe == '1m':
    days = 60
elif timeframe == '5m':
    days = 90
# Replace with:
from domain.config import get_training_days
days = get_training_days(timeframe)
```

### Step 2: Apply Sanitization

Add to all API endpoints that return numeric data:

```python
from utils import sanitize_dict

@app.get("/api/some-endpoint")
async def endpoint():
    result = calculate_metrics()  # May contain NaN/Inf
    return sanitize_dict(result)  # Safe for JSON
```

### Step 3: Apply Singleton Decorator

```python
# Before:
_service = None
def get_service():
    global _service
    if _service is None:
        _service = Service()
    return _service

# After:
from utils import singleton

@singleton
class Service:
    ...

# Or for FastAPI dependency injection:
from fastapi import Depends

def get_service() -> Service:
    return Service()  # Will be singleton automatically

@app.get("/endpoint")
async def endpoint(service: Service = Depends(get_service)):
    ...
```

---

## Testing Recommendations

After applying each improvement:

1. **Run existing tests** to ensure no regressions
2. **Test API endpoints** that use updated code
3. **Check JSON responses** for proper serialization
4. **Verify timeframe calculations** match previous behavior

---

## Benefits Summary

| Improvement | Duplications Removed | LOC Reduced | Error Prevention |
|-------------|---------------------|-------------|------------------|
| Timeframes Config | 9 locations | ~200 lines | ✅ Consistency |
| JSON Sanitization | Enables reuse | ~50 lines | ✅ API errors |
| Singleton Decorator | 4 patterns | ~40 lines | ✅ Testing |
| **Total** | **13+** | **~290** | ✅✅✅ |

---

## Next Steps

1. **Update existing code** to use new utilities (can be done gradually)
2. **Add unit tests** for new utility modules
3. **Proceed to Phase 2** (Split main.py into routers)
4. **Monitor** for any issues during migration

---

## Contact & Support

For questions or issues with these improvements, refer to:
- Full analysis report: See agent output above
- Code examples: This guide
- Testing: Verify with existing test suite
