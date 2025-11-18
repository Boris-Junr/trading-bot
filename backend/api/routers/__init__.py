"""
API Routers

Exports all router modules for registration in main.py.
"""

from .health import router as health_router
from .system import router as system_router
from .portfolio import router as portfolio_router
from .backtests import router as backtests_router
from .predictions import router as predictions_router
from .ml_models import router as ml_models_router
from .strategies import router as strategies_router
from .market import router as market_router

__all__ = [
    'health_router',
    'system_router',
    'portfolio_router',
    'backtests_router',
    'predictions_router',
    'ml_models_router',
    'strategies_router',
    'market_router',
]
