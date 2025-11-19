"""
Trading Bot REST API - Main Application

This is the main FastAPI application file. All API endpoints are organized into
separate router modules in the routers/ directory for better maintainability.

Architecture:
- routers/ - Endpoint route handlers organized by domain
- services/ - Business logic layer
- models.py - Request/response models (Pydantic)
- utils.py - Shared utilities (SSE helpers, etc.)
"""
import sys
import io

# Configure UTF-8 encoding for stdout/stderr to support emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[Startup] Loaded .env from: {env_path}")
    print(f"[Startup] TRADING_BOT_DEV_MODE = {os.getenv('TRADING_BOT_DEV_MODE', 'not set')}")
else:
    print(f"[Startup] No .env file found at: {env_path}")

# Import services for singleton initialization
from api.services.data_service import get_data_service
from api.services.ml_service import get_ml_service
from api.services.backtest_service import get_backtest_service
from api.services.portfolio_service import get_portfolio_service
from infrastructure.resource_manager import (
    start_queue_worker,
    stop_queue_worker,
)

# Import all routers
from api.routers import (
    health_router,
    system_router,
    portfolio_router,
    backtests_router,
    predictions_router,
    ml_models_router,
    strategies_router,
    market_router,
)
from api.routers.api_keys import router as api_keys_router

# Initialize FastAPI application
app = FastAPI(
    title="Trading Bot API",
    version="1.0.0",
    description="Automated trading system with ML predictions, backtesting, and portfolio management"
)

# Configure CORS middleware
# Get allowed origins from environment variable, fallback to localhost for development
allowed_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176"
]

# Add production origins from environment variable
if allowed_origins_env:
    production_origins = [origin.strip() for origin in allowed_origins_env.split(',')]
    allowed_origins.extend(production_origins)
    print(f"[Startup] Added production CORS origins: {production_origins}")

print(f"[Startup] Allowed CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singleton services at startup
# These are called once to ensure services are initialized before any requests
data_service = get_data_service()
ml_service = get_ml_service()
backtest_service = get_backtest_service()
portfolio_service = get_portfolio_service()

print("[Startup] All services initialized successfully")


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """
    Start the background queue worker on application startup.

    The queue worker processes background tasks (backtests, predictions, model training)
    when system resources are available.
    """
    print("[API] Starting background queue worker...")
    await start_queue_worker(check_interval=5.0)
    print("[API] Background queue worker started")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Stop the background queue worker on application shutdown.

    Ensures graceful shutdown of background tasks.
    """
    print("[API] Stopping background queue worker...")
    await stop_queue_worker()
    print("[API] Background queue worker stopped")


# Register all routers
# Each router handles a specific domain of the API
app.include_router(health_router)      # Health check endpoints
app.include_router(system_router)      # System resources and task events
app.include_router(portfolio_router)   # Portfolio management
app.include_router(backtests_router)   # Backtest execution and results
app.include_router(predictions_router) # ML predictions
app.include_router(ml_models_router)   # Model training and management
app.include_router(strategies_router)  # Trading strategies
app.include_router(market_router)      # Market data and symbols
app.include_router(api_keys_router)    # User API key management

print("[Startup] All routers registered successfully")
print("[Startup] API endpoints:")
print("  - GET  /api/health")
print("  - GET  /api/system/resources")
print("  - GET  /api/system/task-events (SSE)")
print("  - GET  /api/portfolio")
print("  - GET  /api/backtests")
print("  - POST /api/backtests/run")
print("  - GET  /api/backtests/stream (SSE)")
print("  - GET  /api/predictions")
print("  - POST /api/predictions/generate")
print("  - GET  /api/predictions/stream (SSE)")
print("  - GET  /api/models")
print("  - POST /api/models/train")
print("  - GET  /api/strategies")
print("  - GET  /api/strategies/available")
print("  - GET  /api/market/data")
print("  - GET  /api/market/symbols")


# Development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
