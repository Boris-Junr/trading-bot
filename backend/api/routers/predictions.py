"""
Predictions Router

Endpoints for generating and managing price predictions using ML models.
Includes both synchronous and Server-Sent Events (SSE) streaming endpoints.
"""

import json
import uuid
import asyncio
import traceback
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api import models
from api.services.ml_service import get_ml_service
from infrastructure.resource_manager import (
    get_resource_monitor,
    get_task_queue,
    TaskType
)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# Service initialization (singleton)
ml_service = get_ml_service()


@router.get("/")
async def get_predictions(
    symbol: str,
    timeframe: str,
    auto_train: bool = True,
    force_retrain: bool = False
):
    """
    Get price predictions for a symbol and timeframe.

    This endpoint checks for existing models, trains new ones if needed (based on
    age limits per timeframe), and returns predictions. Training happens synchronously
    if required, so use POST /generate for background execution.

    Args:
        symbol: Trading symbol (e.g., ETH_USDT)
        timeframe: Timeframe (e.g., 1m, 5m, 15m, 1h)
        auto_train: Automatically train model if none exists or is outdated
        force_retrain: Force retraining even if model exists and is fresh

    Returns:
        PredictionData with current price, predictions, and model metadata

    Raises:
        HTTPException: 503 if training required but resources unavailable
        HTTPException: 500 if prediction generation fails
    """
    # Timeframe-based age limits (in days)
    # Shorter timeframes need more frequent retraining due to faster market dynamics
    timeframe_age_limits = {
        '1m': 2,    # 2 days - very short-term, retrain frequently
        '5m': 3,    # 3 days
        '15m': 5,   # 5 days
        '1h': 7,    # 1 week
        '4h': 14,   # 2 weeks
        '1d': 30,   # 1 month - longer-term trends
    }
    max_age_days = timeframe_age_limits.get(timeframe, 7)

    print(f"\n=== Predictions Request: {symbol} {timeframe} ===")
    print(f"Auto-train: {auto_train}, Force retrain: {force_retrain}, Max age: {max_age_days} days")

    # Check for existing model
    models_list = await asyncio.to_thread(ml_service.list_models)
    matching_model = next(
        (m for m in models_list
         if m['symbol'] == symbol and m['timeframe'] == timeframe),
        None
    )

    should_train = force_retrain

    if matching_model:
        trained_at = datetime.fromisoformat(matching_model['trained_at'])
        age_days = (datetime.now() - trained_at).days
        print(f"Found existing model: {matching_model['name']}")
        print(f"Model age: {age_days} days (max: {max_age_days} days)")

        if age_days > max_age_days and auto_train:
            print(f"Model is outdated, will retrain")
            should_train = True
        else:
            print(f"Model is fresh, using existing model")
    else:
        print(f"No existing model found")
        if auto_train:
            print(f"Will train new model")
            should_train = True

    # Train if needed
    if should_train:
        print(f"\n>>> Training model for {symbol} {timeframe}...")

        # Check if resources are available for training
        resource_monitor = get_resource_monitor()
        can_run, reason = resource_monitor.can_run_task(TaskType.MODEL_TRAINING)

        if not can_run:
            # Cannot train now due to insufficient resources
            print(f">>> Insufficient resources for training: {reason}")
            raise HTTPException(
                status_code=503,
                detail=f"Model training required but insufficient resources available: {reason}. Please try again later or use an existing model."
            )

        # Determine appropriate n_steps based on timeframe
        timeframe_to_steps = {
            '1m': 300,   # 5 hours ahead
            '5m': 144,   # 12 hours ahead
            '15m': 96,   # 24 hours ahead
            '1h': 72,    # 3 days ahead
            '4h': 42,    # 1 week ahead
            '1d': 30,    # 1 month ahead
        }
        n_steps = timeframe_to_steps.get(timeframe, 100)

        train_result = await asyncio.to_thread(
            ml_service.train_model,
            symbol=symbol,
            timeframe=timeframe,
            n_steps_ahead=n_steps,
            days_history=30
        )

        if train_result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to train model. Check if historical data is available."
            )

        print(f">>> Training complete! Model saved as: {train_result['name']}")
        print(f">>> Performance - Train R²: {train_result['performance']['train_r2']:.4f}, Val R²: {train_result['performance']['val_r2']:.4f}")

    # Get predictions
    print(f"\n>>> Generating predictions...")
    predictions_data = await asyncio.to_thread(ml_service.get_predictions, symbol, timeframe)

    if predictions_data is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate predictions. Model may not be properly loaded."
        )

    print(f">>> Generated {len(predictions_data['predictions'])} prediction steps")
    print(f"=== Request complete ===\n")

    prediction_steps = [
        models.PredictionStep(**pred)
        for pred in predictions_data['predictions']
    ]

    # Determine model info for response metadata
    if should_train:
        model_name = train_result['name']
        model_age = 0
    elif matching_model:
        model_name = matching_model['name']
        model_age = (datetime.now() - datetime.fromisoformat(matching_model['trained_at'])).days
    else:
        model_name = None
        model_age = None

    return models.PredictionData(
        timestamp=predictions_data['timestamp'],
        current_price=predictions_data['current_price'],
        predictions=prediction_steps,
        smoothness_score=predictions_data['smoothness_score'],
        model_trained=should_train,
        model_name=model_name,
        model_age_days=model_age
    )


@router.post("/generate")
async def generate_predictions_background(symbol: str, timeframe: str, auto_train: bool = True):
    """
    Generate predictions in the background (non-blocking).

    This endpoint queues or immediately starts a prediction task in the background.
    Progress can be monitored via the Status Center using task events SSE stream.

    Args:
        symbol: Trading symbol (e.g., ETH_USDT)
        timeframe: Timeframe (e.g., 1m, 5m, 15m, 1h)
        auto_train: Automatically train model if needed

    Returns:
        Dict with status ("queued" or "running"), prediction_id, and message.
        Use GET /{prediction_id} to check results.

    Raises:
        HTTPException: 500 if prediction task fails to start
    """
    try:
        print(f"\n[Prediction] Starting background prediction for {symbol} {timeframe}")

        # Check if resources are available
        resource_monitor = get_resource_monitor()

        # Check for model training resource needs first
        models_list = await asyncio.to_thread(ml_service.list_models)
        matching_model = next(
            (m for m in models_list
             if m['symbol'] == symbol and m['timeframe'] == timeframe),
            None
        )

        # Determine if training is needed
        timeframe_age_limits = {
            '1m': 2, '5m': 3, '15m': 5, '1h': 7, '4h': 14, '1d': 30,
        }
        max_age_days = timeframe_age_limits.get(timeframe, 7)
        needs_training = False

        if matching_model and auto_train:
            trained_at = datetime.fromisoformat(matching_model['trained_at'])
            age_days = (datetime.now() - trained_at).days
            if age_days > max_age_days:
                needs_training = True
        elif not matching_model and auto_train:
            needs_training = True

        # Always use PREDICTION type from user perspective
        # (Even if training happens internally, it's still a prediction request)
        if needs_training:
            can_run, reason = resource_monitor.can_run_task(TaskType.MODEL_TRAINING)
        else:
            can_run, reason = resource_monitor.can_run_task(TaskType.PREDICTION)
        task_type = TaskType.PREDICTION  # Always use PREDICTION for predictions

        # Generate prediction ID
        prediction_id = str(uuid.uuid4())

        # Create task entry immediately (for status tracking)
        await asyncio.to_thread(
            ml_service.create_prediction_task,
            symbol=symbol,
            timeframe=timeframe,
            prediction_id=prediction_id,
            status='queued' if not can_run else 'running'
        )

        # Define async wrapper for prediction task
        async def run_prediction_task():
            """Wrapper to run prediction and save results"""
            task_queue = get_task_queue()

            async def log(message: str):
                """Helper to log and send to UI"""
                print(message)
                await task_queue.update_task_description(prediction_id, message)

            try:
                # Train if needed
                if needs_training:
                    await log(f"🎯 Preparing to train new model for {symbol} ({timeframe})")
                    await log(f"📊 Gathering 30 days of historical market data...")

                    timeframe_to_steps = {
                        '1m': 300, '5m': 144, '15m': 96,
                        '1h': 72, '4h': 42, '1d': 30,
                    }
                    n_steps = timeframe_to_steps.get(timeframe, 100)

                    # Calculate human-friendly time description
                    if timeframe == '1m':
                        time_desc = "5 hours"
                    elif timeframe == '5m':
                        time_desc = "12 hours"
                    elif timeframe == '15m':
                        time_desc = "1 day"
                    elif timeframe == '1h':
                        time_desc = "3 days"
                    elif timeframe == '4h':
                        time_desc = "1 week"
                    else:
                        time_desc = "1 month"

                    await log(f"🧠 Training AI model to predict {time_desc} into the future...")
                    # Run CPU-intensive training in a thread pool to avoid blocking event loop
                    train_result = await asyncio.to_thread(
                        ml_service.train_model,
                        symbol=symbol,
                        timeframe=timeframe,
                        n_steps_ahead=n_steps,
                        days_history=30
                    )

                    if train_result is None:
                        await log(f"❌ Model training failed - please try again")
                        return

                    await log(f"✅ Model training complete! Ready to generate predictions")
                else:
                    await log(f"♻️ Using existing trained model for {symbol} ({timeframe})")

                # Generate predictions
                await log(f"🔮 Generating future price predictions...")
                # Run CPU-intensive prediction in a thread pool
                predictions_data = await asyncio.to_thread(
                    ml_service.get_predictions,
                    symbol,
                    timeframe
                )

                if predictions_data:
                    await log(f"💾 Saving prediction results to database...")
                    # Save results (run in thread pool)
                    await asyncio.to_thread(
                        ml_service.save_prediction_result,
                        symbol=symbol,
                        timeframe=timeframe,
                        prediction_data=predictions_data,
                        prediction_id=prediction_id
                    )
                    await log(f"✅ Prediction complete! Results are ready to view")
                else:
                    await log(f"❌ Unable to generate predictions - model may need retraining")

            except Exception as e:
                await log(f"❌ Unexpected error: {str(e)}")
                traceback.print_exc()

        if not can_run:
            # Queue the task
            print(f"[Prediction] Insufficient resources: {reason}")
            print(f"[Prediction] Queueing task for later execution")

            task_queue = get_task_queue()
            task_id = await task_queue.enqueue(
                task_type,
                run_prediction_task,
                priority=0,
                task_id=prediction_id  # Use prediction_id as task_id for log streaming
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
                "prediction_id": prediction_id,
                "task_id": task_id,
                "queue_position": queue_position,
                "reason": reason,
                "message": f"Prediction queued. Position in queue: {queue_position}. Check status at /api/predictions/{prediction_id}"
            }

        # Resources available - run immediately in background
        print(f"[Prediction] Resources available, starting background task")

        # Register the task so it appears in Status Center
        task_queue = get_task_queue()
        await task_queue.register_running_task(
            task_type=task_type,
            task_func=run_prediction_task,
            task_id=prediction_id  # Use the same prediction_id for consistency
        )

        # Set initial description
        initial_desc = f"🚀 Starting prediction for {symbol} ({timeframe})..."
        await task_queue.update_task_description(prediction_id, initial_desc)

        return {
            "status": "running",
            "prediction_id": prediction_id,
            "message": f"Prediction started. Check status at /api/predictions/{prediction_id}"
        }

    except Exception as e:
        print(f"[Prediction] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/list")
async def list_predictions():
    """
    Get list of all predictions.

    Returns a list of all generated predictions with metadata including
    symbol, timeframe, timestamp, and status.

    Returns:
        List of prediction metadata dictionaries
    """
    return await asyncio.to_thread(ml_service.list_predictions)


@router.get("/{prediction_id}")
async def get_prediction_by_id(prediction_id: str):
    """
    Get prediction result by ID.

    Retrieves a specific prediction's full results including all prediction
    steps and model information.

    Args:
        prediction_id: Unique prediction identifier

    Returns:
        Complete prediction result data

    Raises:
        HTTPException: 404 if prediction not found
    """
    result = await asyncio.to_thread(ml_service.get_prediction_result, prediction_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return result


@router.get("/stream")
async def stream_predictions(symbol: str, timeframe: str):
    """
    Stream predictions with real-time progress updates via Server-Sent Events.

    This endpoint provides a detailed, step-by-step streaming experience for
    generating predictions, including model checking, training (if needed),
    and prediction generation phases.

    Args:
        symbol: Trading symbol (e.g., ETH_USDT)
        timeframe: Timeframe (e.g., 1m, 5m, 15m, 1h)

    Returns:
        StreamingResponse with real-time prediction progress events

    Events:
        - status: Progress updates for each step (check, fetch, train, predict)
        - complete: Final prediction data
        - error: Error messages if generation fails
    """
    print(f"\n[SSE] Starting prediction stream for {symbol} {timeframe}")

    async def event_generator():
        try:
            # Helper to send SSE events
            def send_event(event_type: str, data: dict):
                event_data = json.dumps(data)
                return f"event: {event_type}\ndata: {event_data}\n\n"

            # Step 1: Check for existing model
            yield send_event("status", {
                "step": "check",
                "status": "in-progress",
                "title": "Checking for model",
                "message": f"Looking for trained model for {symbol} {timeframe}..."
            })
            await asyncio.sleep(0.1)

            models_list = await asyncio.to_thread(ml_service.list_models)
            matching_model = next(
                (m for m in models_list
                 if m['symbol'] == symbol and m['timeframe'] == timeframe),
                None
            )

            yield send_event("status", {"step": "check", "status": "completed"})

            # Step 2: Fetching data
            yield send_event("status", {
                "step": "fetch",
                "status": "in-progress",
                "title": "Fetching market data",
                "message": "Retrieving latest market data..."
            })
            await asyncio.sleep(0.1)
            yield send_event("status", {"step": "fetch", "status": "completed"})

            # Determine if we need to train
            timeframe_age_limits = {
                '1m': 2, '5m': 3, '15m': 5, '1h': 7, '4h': 14, '1d': 30,
            }
            max_age_days = timeframe_age_limits.get(timeframe, 7)

            timeframe_to_steps = {
                '1m': 300, '5m': 144, '15m': 96,
                '1h': 72, '4h': 42, '1d': 30,
            }
            n_steps = timeframe_to_steps.get(timeframe, 100)

            should_train = False

            # Step 3: Model processing
            if matching_model:
                trained_at = datetime.fromisoformat(matching_model['trained_at'])
                age_days = (datetime.now() - trained_at).days

                if age_days > max_age_days:
                    should_train = True
                    yield send_event("status", {
                        "step": "train",
                        "status": "in-progress",
                        "title": "Retraining outdated model",
                        "message": f"Model is {age_days} days old (max: {max_age_days}). Retraining - this may take 2-5 minutes..."
                    })
                else:
                    yield send_event("status", {
                        "step": "train",
                        "status": "in-progress",
                        "title": "Using existing model",
                        "message": f"Found model: {matching_model['name']} ({age_days} days old)"
                    })
                    await asyncio.sleep(0.5)
                    yield send_event("status", {"step": "train", "status": "completed"})
            else:
                should_train = True
                yield send_event("status", {
                    "step": "train",
                    "status": "in-progress",
                    "title": "Training new model",
                    "message": "No existing model found. Training new model - this may take 2-5 minutes..."
                })

            # Train if needed
            if should_train:
                timeframe_to_steps = {
                    '1m': 300, '5m': 144, '15m': 96,
                    '1h': 72, '4h': 42, '1d': 30,
                }
                n_steps = timeframe_to_steps.get(timeframe, 100)

                # Update status: Fetching training data
                yield send_event("status", {
                    "step": "train",
                    "status": "in-progress",
                    "title": "Fetching training data",
                    "message": f"Downloading {30} days of historical data for training..."
                })
                await asyncio.sleep(0.1)  # Allow event to be sent

                # Update status: Training model
                yield send_event("status", {
                    "step": "train",
                    "status": "in-progress",
                    "title": "Training model",
                    "message": "Training LightGBM model - this may take 1-3 minutes..."
                })
                await asyncio.sleep(0.1)  # Allow event to be sent

                # Training happens here
                train_result = await asyncio.to_thread(
                    ml_service.train_model,
                    symbol=symbol,
                    timeframe=timeframe,
                    n_steps_ahead=n_steps,
                    days_history=30
                )

                if train_result is None:
                    yield send_event("error", {
                        "message": "Failed to train model. Check if historical data is available."
                    })
                    return

                yield send_event("status", {
                    "step": "train",
                    "status": "completed",
                    "title": "Model trained successfully",
                    "message": f"Model saved: {train_result['name']} (R²={train_result['performance']['val_r2']:.4f})"
                })
                await asyncio.sleep(0.5)  # Allow user to see completion

            # Step 4: Generate predictions
            yield send_event("status", {
                "step": "predict",
                "status": "in-progress",
                "title": "Updating market data",
                "message": "Fetching latest price data..."
            })
            await asyncio.sleep(0.1)

            yield send_event("status", {
                "step": "predict",
                "status": "in-progress",
                "title": "Generating predictions",
                "message": f"Running autoregressive model for {timeframe_to_steps.get(timeframe, 100)} steps..."
            })
            await asyncio.sleep(0.1)

            predictions_data = await asyncio.to_thread(ml_service.get_predictions, symbol, timeframe)

            if predictions_data is None:
                yield send_event("error", {
                    "message": "Failed to generate predictions. Model may not be properly loaded."
                })
                return

            yield send_event("status", {"step": "predict", "status": "completed"})

            # Send final prediction data
            prediction_steps = [
                {
                    "step": pred["step"],
                    "minutes_ahead": pred["minutes_ahead"],
                    "predicted_open": pred["predicted_open"],
                    "predicted_high": pred["predicted_high"],
                    "predicted_low": pred["predicted_low"],
                    "predicted_close": pred["predicted_close"],
                    "predicted_return": pred["predicted_return"],
                    "confidence": pred.get("confidence"),
                    "timestamp": pred["timestamp"]
                }
                for pred in predictions_data['predictions']
            ]

            # Determine model info
            if should_train and train_result:
                model_name = train_result['name']
                model_age = 0
            elif matching_model:
                model_name = matching_model['name']
                model_age = (datetime.now() - datetime.fromisoformat(matching_model['trained_at'])).days
            else:
                model_name = None
                model_age = None

            yield send_event("complete", {
                "timestamp": predictions_data['timestamp'],
                "current_price": predictions_data['current_price'],
                "predictions": prediction_steps,
                "smoothness_score": predictions_data.get('smoothness_score'),
                "model_trained": should_train,
                "model_name": model_name,
                "model_age_days": model_age,
                "historical_candles": predictions_data.get('historical_candles', [])
            })

        except Exception as e:
            error_msg = f"Error in stream_predictions: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            yield send_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
