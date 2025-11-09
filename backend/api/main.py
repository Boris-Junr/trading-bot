"""
Trading Bot REST API - Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from api import models
from api.services.data_service import get_data_service
from api.services.ml_service import get_ml_service
from api.services.backtest_service import get_backtest_service
from api.services.portfolio_service import get_portfolio_service

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


# Health Check
@app.get("/api/health")
async def health_check():
    return models.HealthResponse(status="ok", version="1.0.0")


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
    backtests = backtest_service.list_backtests()

    results = []
    for bt in backtests:
        # Handle both direct structure (from run_backtest) and saved structure (from file)
        # Saved backtests have data nested under 'results' key
        bt_data = bt.get('results', bt)

        results.append(models.BacktestResult(
            strategy=bt['strategy'],
            symbol=bt['symbol'],
            start_date=bt['start_date'],
            end_date=bt['end_date'],
            performance=models.Performance(**bt_data['performance']),
            trading=models.TradingStats(**bt_data['trading'])
        ))

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
    bt = backtest_service.get_backtest(backtest_id)

    if bt is None:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return models.BacktestResult(
        strategy=bt['strategy'],
        symbol=bt['symbol'],
        start_date=bt['start_date'],
        end_date=bt['end_date'],
        performance=models.Performance(**bt['performance']),
        trading=models.TradingStats(**bt['trading'])
    )


@app.post("/api/backtests/run")
async def run_backtest(request: models.BacktestRequest):
    """Run a new backtest"""
    try:
        print(f"\n[Backtest] Starting backtest: {request.strategy} on {request.symbol}")
        print(f"[Backtest] Date range: {request.start_date} to {request.end_date}")
        print(f"[Backtest] Params: {request.params}")

        result = backtest_service.run_backtest(
            strategy=request.strategy,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_capital,
            **request.params
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Backtest failed. Check if historical data is available and model exists for this symbol."
            )

        return models.BacktestResult(
            strategy=result['strategy'],
            symbol=result['symbol'],
            start_date=result['start_date'],
            end_date=result['end_date'],
            performance=models.Performance(**result['performance']),
            trading=models.TradingStats(**result['trading'])
        )
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
    models_list = ml_service.list_models()
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

        train_result = ml_service.train_model(
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
    predictions_data = ml_service.get_predictions(symbol, timeframe)

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
async def generate_predictions(symbol: str, timeframe: str, model_path: str):
    """Generate new predictions"""
    predictions_data = ml_service.get_predictions(symbol, timeframe, model_path)

    if predictions_data is None:
        raise HTTPException(status_code=404, detail="Failed to generate predictions")

    prediction_steps = [
        models.PredictionStep(**pred)
        for pred in predictions_data['predictions']
    ]

    return models.PredictionData(
        timestamp=predictions_data['timestamp'],
        current_price=predictions_data['current_price'],
        predictions=prediction_steps,
        smoothness_score=predictions_data['smoothness_score']
    )


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

            models_list = ml_service.list_models()
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
                train_result = ml_service.train_model(
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

            predictions_data = ml_service.get_predictions(symbol, timeframe)

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


# Strategies Endpoints (Still using mock data - would need strategy storage)
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
    models_list = ml_service.list_models()

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
    """Train a new model"""
    result = ml_service.train_model(
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
async def get_symbols(asset_type: str = 'crypto'):
    """
    Get list of available trading symbols

    Args:
        asset_type: 'crypto' or 'stock' (default: 'crypto')

    Returns:
        List of available symbol strings
    """
    symbols = data_service.get_available_symbols(asset_type)
    return {"symbols": symbols, "asset_type": asset_type}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
