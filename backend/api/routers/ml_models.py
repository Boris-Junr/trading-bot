"""
ML Models Router

Endpoints for managing and training machine learning models.
Includes model listing, details, and training with resource management.
"""

import asyncio
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException
from api import models
from api.services.ml_service import get_ml_service
from infrastructure.resource_manager import (
    get_resource_monitor,
    get_task_queue,
    TaskType
)

router = APIRouter(prefix="/api/models", tags=["models"])

# Service initialization (singleton)
ml_service = get_ml_service()


@router.get("/")
async def get_models():
    """
    Get all trained models.

    Returns a list of all trained ML models with metadata including symbol,
    timeframe, prediction steps, model size, training timestamp, and performance metrics.

    Returns:
        List[ModelInfo]: List of model information objects
    """
    models_list = await asyncio.to_thread(ml_service.list_models)

    return [
        models.ModelInfo(
            name=m['name'],
            type=m['type'],
            symbol=m['symbol'],
            timeframe=m['timeframe'],
            n_steps_ahead=m['n_steps_ahead'],
            model_size_kb=m['model_size_kb'],
            trained_at=m['trained_at'],
            performance=models.ModelPerformance(**m['performance'])
        )
        for m in models_list
    ]


@router.get("/{model_name}")
async def get_model(model_name: str):
    """
    Get model details by name.

    Retrieves detailed information about a specific trained model including
    all metadata and performance metrics.

    Args:
        model_name: Name of the model (e.g., ETH_USDT_1m_300steps_multi_ohlc)

    Returns:
        ModelInfo: Complete model information

    Raises:
        HTTPException: 404 if model not found
    """
    model_list = await get_models()
    for model in model_list:
        if model.name == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("/train")
async def train_model(request: models.TrainModelRequest):
    """
    Train a new ML model with resource checking and queuing.

    This endpoint checks resource availability and either queues the training task
    or executes it immediately. Training is CPU/RAM intensive and can take several
    minutes depending on data volume and model complexity.

    Args:
        request: Training configuration including symbol, timeframe, prediction steps,
                and historical data days

    Returns:
        Dict with status and model info. If queued, returns queue position.
        If running immediately, returns ModelInfo upon completion.

    Raises:
        HTTPException: 500 if training fails
    """
    print(f"\n[ModelTraining] Training model for {request.symbol} {request.timeframe}")

    # Check if resources are available
    resource_monitor = get_resource_monitor()
    can_run, reason = resource_monitor.can_run_task(TaskType.MODEL_TRAINING)

    if not can_run:
        # Queue the task instead of running immediately
        print(f"[ModelTraining] Insufficient resources: {reason}")
        print(f"[ModelTraining] Queueing task for later execution")

        task_queue = get_task_queue()
        task_id = await task_queue.enqueue(
            TaskType.MODEL_TRAINING,
            ml_service.train_model,
            symbol=request.symbol,
            timeframe=request.timeframe,
            n_steps_ahead=request.n_steps_ahead,
            days_history=request.days_history
        )

        # Get queue position
        queue_status = task_queue.get_queue_status()
        queue_position = None
        for i, task in enumerate(queue_status['queued_tasks'], 1):
            if task['task_id'] == task_id:
                queue_position = i
                break

        return {
            "status": "queued",
            "task_id": task_id,
            "queue_position": queue_position,
            "reason": reason,
            "message": f"Model training queued due to insufficient resources. Position in queue: {queue_position}"
        }

    # Resources available - train model immediately
    print(f"[ModelTraining] Resources available, training model")
    result = await asyncio.to_thread(
        ml_service.train_model,
        symbol=request.symbol,
        timeframe=request.timeframe,
        n_steps_ahead=request.n_steps_ahead,
        days_history=request.days_history
    )

    if result is None:
        raise HTTPException(status_code=500, detail="Training failed")

    return models.ModelInfo(
        name=result['name'],
        type=result['type'],
        symbol=result['symbol'],
        timeframe=result['timeframe'],
        n_steps_ahead=result['n_steps_ahead'],
        model_size_kb=result['model_size_kb'],
        trained_at=result['trained_at'],
        performance=models.ModelPerformance(**result['performance'])
    )
