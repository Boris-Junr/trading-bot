"""
Backtests Router

Endpoints for running and managing backtests.
Includes Server-Sent Events (SSE) for real-time backtest streaming.
"""

import json
import uuid
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api import models
from api.services.backtest_service import get_backtest_service
from infrastructure.resource_manager import (
    get_resource_monitor,
    get_task_queue,
    TaskType
)

router = APIRouter(prefix="/api/backtests", tags=["backtests"])

# Service initialization (singleton)
backtest_service = get_backtest_service()


@router.get("/")
async def get_backtests():
    """
    Get list of all backtest results.

    Returns both successful and failed backtests. Failed backtests include error
    information, while successful backtests include full performance metrics.

    Returns:
        List of backtest results with status indicators
    """
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


@router.get("/{backtest_id}")
async def get_backtest(backtest_id: str):
    """
    Get detailed backtest results by ID.

    Args:
        backtest_id: Unique backtest identifier

    Returns:
        Full backtest results including performance, trading stats, trades, and charts

    Raises:
        HTTPException: 404 if backtest not found
    """
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


@router.get("/stream")
async def stream_backtest(
    strategy: str,
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    params: str = "{}"
):
    """
    Stream backtest execution with real-time progress updates via Server-Sent Events.

    NOTE: This endpoint is currently not used by the frontend. The /run endpoint with
    background execution and Status Center monitoring is used instead.

    Args:
        strategy: Strategy name (e.g., MLPredictive)
        symbol: Trading pair (e.g., BTC_USDT)
        start_date: ISO format start date
        end_date: ISO format end date
        initial_capital: Starting cash amount
        params: JSON string of strategy parameters

    Returns:
        StreamingResponse with real-time backtest progress events
    """
    print(f"\n[SSE Backtest] Starting backtest stream for {symbol} {strategy}")

    # Parse params JSON string
    params_dict = json.loads(params)

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


@router.post("/run")
async def run_backtest(request: models.BacktestRequest):
    """
    Run a new backtest in background with task queuing and resource management.

    This endpoint queues the backtest if resources are unavailable, or runs it
    immediately in the background. Progress can be monitored via the Status Center
    using the task events SSE stream.

    Args:
        request: Backtest configuration including strategy, symbol, dates, and parameters

    Returns:
        Dict with status ("queued" or "running"), backtest_id, and descriptive message

    Raises:
        HTTPException: 500 if backtest fails to start
    """
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
                    results_dir = Path(__file__).parent.parent.parent / 'output' / 'backtests'
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
                traceback.print_exc()
                # Save failed backtest result
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
                results_dir = Path(__file__).parent.parent.parent / 'output' / 'backtests'
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
        print(f"[Backtest] Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")
