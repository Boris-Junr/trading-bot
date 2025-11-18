"""
Trading Bot REST API - Main Application
"""
import sys
import io

# Configure UTF-8 encoding for stdout/stderr to support emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import asyncio
import os
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[Startup] Loaded .env from: {env_path}")
    print(f"[Startup] TRADING_BOT_DEV_MODE = {os.getenv('TRADING_BOT_DEV_MODE', 'not set')}")
else:
    print(f"[Startup] No .env file found at: {env_path}")

from api import models
from api.services.data_service import get_data_service
from api.services.ml_service import get_ml_service
from api.services.backtest_service import get_backtest_service
from api.services.portfolio_service import get_portfolio_service
from infrastructure.resource_manager import (
    get_resource_monitor,
    get_task_queue,
    start_queue_worker,
    stop_queue_worker,
    TaskType
)

app = FastAPI(title="Trading Bot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_service = get_data_service()
ml_service = get_ml_service()
backtest_service = get_backtest_service()
portfolio_service = get_portfolio_service()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start the background queue worker on application startup."""
    print("[API] Starting background queue worker...")
    await start_queue_worker(check_interval=5.0)


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background queue worker on application shutdown."""
    print("[API] Stopping background queue worker...")
    await stop_queue_worker()


# Health Check
@app.get("/api/health")
async def health_check():
    return models.HealthResponse(status="ok", version="1.0.0")


# System Resources Endpoint
@app.get("/api/system/resources")
async def get_system_resources():
    """Get current system resource availability and queue status."""
    resource_monitor = get_resource_monitor()
    task_queue = get_task_queue()

    resources = resource_monitor.get_resource_summary()
    queue_status = task_queue.get_queue_status()

    # Log every status check for debugging
    print(f"[API] /api/system/resources polled - Running: {queue_status['running_count']}, Queued: {queue_status['queued_count']}")

    return {
        "resources": resources,
        "queue": queue_status
    }


# Resources Only Endpoint (CPU/RAM without queue status)
@app.get("/api/system/resources-only")
async def get_system_resources_only():
    """Get current system resource availability (CPU/RAM only, no queue status)."""
    resource_monitor = get_resource_monitor()
    resources = resource_monitor.get_resource_summary()

    return {
        "resources": resources
    }


# Queue Status Endpoint
@app.get("/api/system/queue")
async def get_queue_status():
    """Get current task queue status."""
    task_queue = get_task_queue()
    return task_queue.get_queue_status()


#Task Events Stream (SSE)
@app.get("/api/system/task-events")
async def stream_task_events():
    """
    Stream task status change events using Server-Sent Events (SSE).

    Events:
    - task_running: Task started running
    - task_completed: Task finished
    - task_queued: Task added to queue
    """
    async def event_generator():
        task_queue = get_task_queue()
        resource_monitor = get_resource_monitor()
        event_queue = await task_queue.subscribe_to_events()

        try:
            # Send initial state with queue status AND resources
            queue_status = task_queue.get_queue_status()
            resources = resource_monitor.get_resource_summary()
            initial_event = {
                'type': 'initial_state',
                'data': queue_status,
                'resources': resources
            }
            yield f"data: {json.dumps(initial_event)}\n\n"

            # Track last heartbeat time
            last_heartbeat = asyncio.get_event_loop().time()
            heartbeat_interval = 5.0  # Send resource updates every 5 seconds

            # Stream events as they occur (each includes updated resources)
            while True:
                try:
                    # Wait for event with timeout to allow heartbeat
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # No event received, check if it's time for heartbeat
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= heartbeat_interval:
                        # Send heartbeat with current CPU/RAM resources
                        resources = resource_monitor.get_resource_summary()
                        heartbeat_event = {
                            'type': 'heartbeat',
                            'timestamp': datetime.now().isoformat(),
                            'resources': resources
                        }
                        yield f"data: {json.dumps(heartbeat_event)}\n\n"
                        last_heartbeat = current_time

        except asyncio.CancelledError:
            # Client disconnected
            task_queue.unsubscribe_from_events(event_queue)
            print("[SSE] Client disconnected from task events stream")
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
            "Connection": "keep-alive",
        }
    )


# Portfolio Endpoints
@app.get("/api/portfolio", response_model=models.Portfolio)
async def get_portfolio():
    """Get current portfolio state"""
    portfolio_data = portfolio_service.get_portfolio()

    # Convert to API models
    positions = [
        models.Position(**pos)
        for pos in portfolio_data.get('positions', [])
    ]

    return models.Portfolio(
        total_value=portfolio_data['total_value'],
        cash=portfolio_data['cash'],
        positions=positions,
        daily_pnl=portfolio_data['daily_pnl'],
        daily_pnl_pct=portfolio_data['daily_pnl_pct'],
        total_pnl=portfolio_data['total_pnl'],
        total_pnl_pct=portfolio_data['total_pnl_pct']
    )


@app.get("/api/portfolio/history")
async def get_portfolio_history(days: int = 30):
    """Get portfolio value history"""
    return portfolio_service.get_history(days)


# Backtest Endpoints
@app.get("/api/backtests")
async def get_backtests():
    """Get list of all backtest results"""
    backtests = await asyncio.to_thread(backtest_service.list_backtests)

    results = []
    for bt in backtests:
        # Check if this is a failed backtest
        if bt.get('status') == 'failed':
            # Return failed backtest with minimal info
            results.append({
                'id': bt['id'],
                'status': 'failed',
                'strategy': bt['strategy'],
                'symbol': bt['symbol'],
                'start_date': bt['start_date'],
                'end_date': bt['end_date'],
                'error': bt.get('error', 'Unknown error'),
                'created_at': bt.get('created_at')
            })
            continue

        # Handle successful backtests
        # Handle both direct structure (from run_backtest) and saved structure (from file)
        # Saved backtests have data nested under 'results' key
        bt_data = bt.get('results', bt)

        result = models.BacktestResult(
            strategy=bt['strategy'],
            symbol=bt['symbol'],
            start_date=bt['start_date'],
            end_date=bt['end_date'],
            performance=models.Performance(**bt_data['performance']),
            trading=models.TradingStats(**bt_data['trading'])
        )
        # Add the id, status, and created_at fields to the result
        result_dict = result.model_dump()
        result_dict['id'] = bt['id']
        result_dict['status'] = bt.get('status', 'success')
        result_dict['created_at'] = bt.get('created_at')
        results.append(result_dict)

    return results


@app.get("/api/backtests/stream")
async def stream_backtest(
    strategy: str,
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    params: str = "{}"
):
    """Stream backtest execution with real-time progress updates via Server-Sent Events"""
    print(f"\n[SSE Backtest] Starting backtest stream for {symbol} {strategy}")

    # Parse params JSON string
    import json as json_lib
    params_dict = json_lib.loads(params)

    async def event_generator():
        try:
            def send_event(event_type: str, data: dict):
                event_data = json.dumps(data)
                return f"event: {event_type}\ndata: {event_data}\n\n"

            # Check if resources are available
            resource_monitor = get_resource_monitor()
            can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

            if not can_run:
                # Queue the task instead of running immediately
                print(f"[SSE Backtest] Insufficient resources: {reason}")
                yield send_event("queued", {
                    "message": f"Task queued due to insufficient resources: {reason}",
                    "reason": reason
                })

                task_queue = get_task_queue()
                task_id = await task_queue.enqueue(
                    TaskType.BACKTEST,
                    backtest_service.run_backtest,
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_cash=initial_capital,
                    **params_dict
                )

                # Get queue position
                queue_status = task_queue.get_queue_status()
                queue_position = None
                for i, task in enumerate(queue_status['queued_tasks'], 1):
                    if task['task_id'] == task_id:
                        queue_position = i
                        break

                yield send_event("queue_position", {
                    "task_id": task_id,
                    "position": queue_position,
                    "message": f"Your task is queued at position {queue_position}"
                })
                return

            print(f"[SSE Backtest] Resources available, proceeding with backtest")

            # Step 1: Fetching historical data
            print(f"[SSE] Step 1: Fetching historical data for {symbol}")
            yield send_event("status", {
                "step": "fetch",
                "status": "in-progress",
                "title": "Fetching historical data",
                "message": f"Downloading data for {symbol} from {start_date} to {end_date}..."
            })
            await asyncio.sleep(0.1)
            print(f"[SSE] Step 1 complete")

            # Step 2: Loading/training model
            print(f"[SSE] Step 2: Preparing model")
            yield send_event("status", {
                "step": "model",
                "status": "in-progress",
                "title": "Preparing model",
                "message": "Checking for existing model or training new one..."
            })
            await asyncio.sleep(0.1)
            print(f"[SSE] Step 2 complete")

            # Step 3: Running backtest
            print(f"[SSE] Step 3: Running backtest - calling backtest_service.run_backtest()")
            yield send_event("status", {
                "step": "backtest",
                "status": "in-progress",
                "title": "Running backtest",
                "message": "Executing strategy on historical data..."
            })
            await asyncio.sleep(0.1)

            # Execute backtest in thread pool to avoid blocking the event loop
            print(f"[SSE] Executing backtest with params: strategy={strategy}, symbol={symbol}, dates={start_date} to {end_date}, cash={initial_capital}")
            print(f"[SSE] Strategy params: {params_dict}")

            # Run the synchronous backtest in a thread pool to avoid blocking
            executor = ThreadPoolExecutor(max_workers=1)
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                executor,
                lambda: backtest_service.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_cash=initial_capital,
                    **params_dict
                )
            )
            print(f"[SSE] Backtest execution completed, result={'success' if result else 'failed'}")

            if result is None:
                yield send_event("error", {
                    "message": "Backtest failed. Check if historical data is available and model exists for this symbol."
                })
                return

            yield send_event("status", {"step": "backtest", "status": "completed"})

            # Step 4: Analyzing results
            yield send_event("status", {
                "step": "analyze",
                "status": "in-progress",
                "title": "Analyzing results",
                "message": "Calculating performance metrics..."
            })
            await asyncio.sleep(0.5)
            yield send_event("status", {"step": "analyze", "status": "completed"})

            # Send final results
            yield send_event("complete", {
                "id": result.get('id'),
                "strategy": result['strategy'],
                "symbol": result['symbol'],
                "start_date": result['start_date'],
                "end_date": result['end_date'],
                "performance": result['performance'],
                "trading": result['trading']
            })

        except Exception as e:
            import traceback
            error_msg = f"Error in stream_backtest: {str(e)}"
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


@app.get("/api/backtests/{backtest_id}")
async def get_backtest(backtest_id: str):
    """Get detailed backtest results"""
    bt = await asyncio.to_thread(backtest_service.get_backtest, backtest_id)

    if bt is None:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Handle both direct structure (from run_backtest) and saved structure (from file)
    # Saved backtests have data nested under 'results' key
    bt_data = bt.get('results', bt)

    return models.BacktestResult(
        strategy=bt['strategy'],
        symbol=bt['symbol'],
        start_date=bt['start_date'],
        end_date=bt['end_date'],
        performance=models.Performance(**bt_data['performance']),
        trading=models.TradingStats(**bt_data['trading'])
    )


@app.post("/api/backtests/run")
async def run_backtest(request: models.BacktestRequest):
    """Run a new backtest in background with real-time log streaming"""
    try:
        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())

        print(f"\n[Backtest-{backtest_id}] Starting backtest: {request.strategy} on {request.symbol}")
        print(f"[Backtest-{backtest_id}] Date range: {request.start_date} to {request.end_date}")

        # Check if resources are available
        resource_monitor = get_resource_monitor()
        task_queue = get_task_queue()
        can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

        # Task type for queuing
        task_type = TaskType.BACKTEST

        # Define async wrapper for backtest task with log streaming
        async def run_backtest_task():
            """Wrapper to run backtest and stream logs"""
            task_queue = get_task_queue()

            async def log(message: str):
                """Helper to log and send to UI"""
                print(message)
                await task_queue.update_task_description(backtest_id, message)

            try:
                # Calculate date range
                from datetime import datetime
                start = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
                days = (end - start).days

                await log(f"🎯 Preparing to backtest {request.strategy} strategy on {request.symbol}")
                await log(f"📅 Testing {days} days of historical data ({request.start_date[:10]} to {request.end_date[:10]})")
                await log(f"💰 Starting with ${request.initial_capital:,.2f} initial capital")

                await log(f"🔄 Running backtest simulation...")

                # Run CPU-intensive backtest in a thread pool
                result = await asyncio.to_thread(
                    backtest_service.run_backtest,
                    strategy=request.strategy,
                    symbol=request.symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    initial_cash=request.initial_capital,
                    **request.params
                )

                if result is None:
                    await log(f"❌ Backtest failed - unable to execute simulation")
                    # Save failed backtest result
                    import json
                    from datetime import datetime
                    from pathlib import Path
                    failed_result = {
                        'id': backtest_id,
                        'status': 'failed',
                        'strategy': request.strategy,
                        'symbol': request.symbol,
                        'start_date': request.start_date,
                        'end_date': request.end_date,
                        'initial_capital': request.initial_capital,
                        'created_at': datetime.now().isoformat(),
                        'error': 'Backtest execution failed'
                    }
                    results_dir = Path(__file__).parent.parent / 'output' / 'backtests'
                    result_file = results_dir / f"{backtest_id}.json"
                    with open(result_file, 'w') as f:
                        json.dump(failed_result, f, indent=2)
                    return

                # Extract key metrics for display
                result_id = result.get('id', backtest_id)
                total_return = result['performance']['total_return']
                sharpe = result['performance']['sharpe_ratio']
                max_dd = result['performance']['max_drawdown']
                total_trades = result['trading']['total_trades']

                await log(f"✅ Backtest complete!")
                await log(f"📊 Return: {total_return:+.2%} | Sharpe: {sharpe:.2f} | Max DD: {max_dd:.2%} | Trades: {total_trades}")
                await log(f"💾 Results saved automatically with ID: {result_id}")

            except Exception as e:
                await log(f"❌ Unexpected error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Save failed backtest result
                import json
                from datetime import datetime
                from pathlib import Path
                failed_result = {
                    'id': backtest_id,
                    'status': 'failed',
                    'strategy': request.strategy,
                    'symbol': request.symbol,
                    'start_date': request.start_date,
                    'end_date': request.end_date,
                    'initial_capital': request.initial_capital,
                    'created_at': datetime.now().isoformat(),
                    'error': str(e)
                }
                results_dir = Path(__file__).parent.parent / 'output' / 'backtests'
                result_file = results_dir / f"{backtest_id}.json"
                with open(result_file, 'w') as f:
                    json.dump(failed_result, f, indent=2)

        if not can_run:
            # Queue the task
            print(f"[Backtest-{backtest_id}] Insufficient resources: {reason}")
            print(f"[Backtest-{backtest_id}] Queueing task for later execution")

            task_id = await task_queue.enqueue(
                task_type,
                run_backtest_task,
                priority=0,
                task_id=backtest_id  # Use backtest_id as task_id for log streaming
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
                "backtest_id": backtest_id,
                "task_id": task_id,
                "queue_position": queue_position,
                "message": f"Backtest queued. Position in queue: {queue_position}"
            }

        # Resources available - run immediately in background
        print(f"[Backtest-{backtest_id}] Resources available, starting background task")

        # Register the task so it appears in Status Center
        await task_queue.register_running_task(
            task_type=task_type,
            task_func=run_backtest_task,
            task_id=backtest_id
        )

        # Set initial description
        initial_desc = f"🚀 Starting backtest for {request.symbol}..."
        await task_queue.update_task_description(backtest_id, initial_desc)

        return {
            "status": "running",
            "backtest_id": backtest_id,
            "message": f"Backtest started in background. Check Status Center for progress."
        }

    except Exception as e:
        import traceback
        print(f"[Backtest] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


# Predictions Endpoints
@app.get("/api/predictions")
async def get_predictions(
    symbol: str,
    timeframe: str,
    auto_train: bool = True,
    force_retrain: bool = False
):
    """
    Get price predictions

    Args:
        symbol: Trading symbol (e.g., ETH_USDT)
        timeframe: Timeframe (e.g., 1m, 5m, 15m, 1h)
        auto_train: Automatically train model if none exists or is outdated
        force_retrain: Force retraining even if model exists and is fresh
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


@app.post("/api/predictions/generate")
async def generate_predictions_background(symbol: str, timeframe: str, auto_train: bool = True):
    """
    Generate predictions in the background (non-blocking)

    Returns a task ID immediately. Use GET /api/predictions/{task_id} to check status/results.
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
        import uuid
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
                import traceback
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
        import traceback
        print(f"[Prediction] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/api/predictions/list")
async def list_predictions():
    """Get list of all predictions"""
    return await asyncio.to_thread(ml_service.list_predictions)


@app.get("/api/predictions/{prediction_id}")
async def get_prediction_by_id(prediction_id: str):
    """Get prediction result by ID"""
    result = await asyncio.to_thread(ml_service.get_prediction_result, prediction_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return result


@app.get("/api/predictions/stream")
async def stream_predictions(symbol: str, timeframe: str):
    """Stream predictions with real-time progress updates via Server-Sent Events"""
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
            import traceback
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


# Strategies Endpoints (Using auto-discovery registry)
@app.get("/api/strategies/available")
async def get_available_strategies():
    """Get list of available strategy types for backtesting (auto-discovered)"""
    from domain.strategies.registry import get_strategy_registry

    registry = get_strategy_registry()
    return registry.get_available_strategies_metadata()


@app.get("/api/strategies")
async def get_strategies():
    """Get all trading strategies"""
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


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get strategy details"""
    strategies = await get_strategies()
    for strategy in strategies:
        if strategy.id == strategy_id:
            return strategy
    raise HTTPException(status_code=404, detail="Strategy not found")


@app.post("/api/strategies")
async def create_strategy(request: models.CreateStrategyRequest):
    """Create a new strategy"""
    return models.Strategy(
        id=f"{request.type.lower()}-{datetime.now().timestamp()}",
        name=request.name,
        type=request.type,
        status="inactive",
        params=request.params,
        created_at=datetime.now().isoformat()
    )


@app.put("/api/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: models.CreateStrategyRequest):
    """Update a strategy"""
    return models.Strategy(
        id=strategy_id,
        name=request.name,
        type=request.type,
        status="inactive",
        params=request.params,
        created_at=datetime.now().isoformat()
    )


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """Delete a strategy"""
    return {"message": "Strategy deleted"}


@app.post("/api/strategies/{strategy_id}/activate")
async def activate_strategy(strategy_id: str):
    """Activate a strategy"""
    strategy = await get_strategy(strategy_id)
    strategy.status = "active"
    return strategy


@app.post("/api/strategies/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: str):
    """Deactivate a strategy"""
    strategy = await get_strategy(strategy_id)
    strategy.status = "inactive"
    return strategy


# Models Endpoints
@app.get("/api/models")
async def get_models():
    """Get all trained models"""
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


@app.get("/api/models/{model_name}")
async def get_model(model_name: str):
    """Get model details"""
    model_list = await get_models()
    for model in model_list:
        if model.name == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@app.post("/api/models/train")
async def train_model(request: models.TrainModelRequest):
    """Train a new model (with resource checking and queuing)"""
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


# Market Data Endpoints
@app.get("/api/market/data")
async def get_market_data(
    symbol: str,
    timeframe: str,
    start: str = None,
    end: str = None
):
    """Get historical market data"""
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None

    candles = data_service.get_market_data(
        symbol=symbol,
        timeframe=timeframe,
        start=start_dt,
        end=end_dt
    )

    return candles


@app.get("/api/market/symbols")
async def get_symbols(asset_type: str = 'all'):
    """
    Get list of available trading symbols from global trading pairs configuration

    Args:
        asset_type: 'crypto', 'forex', 'indices', or 'all' (default: 'all')

    Returns:
        List of allowed symbol strings from trading pairs config
    """
    from domain.config import (
        get_pairs_by_type,
        ALLOWED_SYMBOLS,
        AssetType
    )

    # If requesting all symbols, return everything
    if asset_type == 'all':
        return {"symbols": list(ALLOWED_SYMBOLS), "asset_type": asset_type}

    # Map request to AssetType enum
    asset_type_map = {
        'crypto': AssetType.CRYPTO,
        'forex': AssetType.FOREX,
        'indices': AssetType.INDICES
    }

    if asset_type not in asset_type_map:
        # Fallback to all symbols if invalid asset_type
        return {"symbols": list(ALLOWED_SYMBOLS), "asset_type": 'all'}

    # Get pairs for specific asset type
    pairs = get_pairs_by_type(asset_type_map[asset_type])
    symbols = [pair.symbol for pair in pairs]

    return {"symbols": symbols, "asset_type": asset_type}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
