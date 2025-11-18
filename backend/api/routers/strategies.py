"""
Strategies Router

Endpoints for managing trading strategies (CRUD operations).
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from domain.strategies.registry import get_strategy_registry
from api import models

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("/available")
async def get_available_strategies():
    """
    Get list of available strategy types for backtesting (auto-discovered).

    This endpoint uses the strategy registry to automatically discover all
    strategies that have been registered in the system.

    Returns:
        List of strategy metadata including name, description, and parameters
    """
    registry = get_strategy_registry()
    return registry.get_available_strategies_metadata()


@router.get("/")
async def get_strategies():
    """
    Get all trading strategies.

    TODO: Replace mock data with real database/persistence layer.

    Returns:
        List of configured strategies
    """
    return [
        models.Strategy(
            id="ml-pred-1",
            name="ML Predictive Strategy",
            type="MLPredictive",
            status="active",
            params={
                "symbols": ["ETH_USDT", "BTC_USDT"],
                "timeframe": "1m",
                "model_path": "ETH_USDT_1m_300steps_autoregressive",
                "position_size": 0.1
            },
            created_at=datetime.now().isoformat()
        ),
        models.Strategy(
            id="rsi-1",
            name="RSI Strategy",
            type="RSI",
            status="inactive",
            params={
                "symbols": ["ETH_USDT"],
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70
            },
            created_at=datetime.now().isoformat()
        )
    ]


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """
    Get strategy details by ID.

    Args:
        strategy_id: Unique strategy identifier

    Returns:
        Strategy details

    Raises:
        HTTPException: 404 if strategy not found
    """
    strategies = await get_strategies()
    for strategy in strategies:
        if strategy.id == strategy_id:
            return strategy
    raise HTTPException(status_code=404, detail="Strategy not found")


@router.post("/")
async def create_strategy(request: models.CreateStrategyRequest):
    """
    Create a new strategy.

    TODO: Persist to database instead of returning mock data.

    Args:
        request: Strategy creation request with name, type, and parameters

    Returns:
        Created strategy with generated ID
    """
    return models.Strategy(
        id=f"{request.type.lower()}-{datetime.now().timestamp()}",
        name=request.name,
        type=request.type,
        status="inactive",
        params=request.params,
        created_at=datetime.now().isoformat()
    )


@router.put("/{strategy_id}")
async def update_strategy(strategy_id: str, request: models.CreateStrategyRequest):
    """
    Update an existing strategy.

    TODO: Persist changes to database.

    Args:
        strategy_id: Unique strategy identifier
        request: Updated strategy configuration

    Returns:
        Updated strategy
    """
    return models.Strategy(
        id=strategy_id,
        name=request.name,
        type=request.type,
        status="inactive",
        params=request.params,
        created_at=datetime.now().isoformat()
    )


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """
    Delete a strategy.

    TODO: Delete from database.

    Args:
        strategy_id: Unique strategy identifier

    Returns:
        Success message
    """
    return {"message": "Strategy deleted"}


@router.post("/{strategy_id}/activate")
async def activate_strategy(strategy_id: str):
    """
    Activate a strategy for live trading.

    Args:
        strategy_id: Unique strategy identifier

    Returns:
        Activated strategy

    Raises:
        HTTPException: 404 if strategy not found
    """
    strategy = await get_strategy(strategy_id)
    strategy.status = "active"
    return strategy


@router.post("/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: str):
    """
    Deactivate a strategy.

    Args:
        strategy_id: Unique strategy identifier

    Returns:
        Deactivated strategy

    Raises:
        HTTPException: 404 if strategy not found
    """
    strategy = await get_strategy(strategy_id)
    strategy.status = "inactive"
    return strategy
