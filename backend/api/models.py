"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# Portfolio Models
class Position(BaseModel):
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    opened_at: str


class Portfolio(BaseModel):
    total_value: float
    cash: float
    positions: List[Position]
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float


# Backtest Models
class Performance(BaseModel):
    initial_cash: float
    final_equity: float
    total_return: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float


class TradingStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float


class BacktestResult(BaseModel):
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    performance: Performance
    trading: TradingStats


class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    params: dict = {}


# Prediction Models
class PredictionStep(BaseModel):
    step: int
    minutes_ahead: int
    timestamp: str
    predicted_open: float
    predicted_high: float
    predicted_low: float
    predicted_close: float
    predicted_return: float
    confidence: Optional[float] = None


class HistoricalCandle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PredictionData(BaseModel):
    timestamp: str
    current_price: float
    predictions: List[PredictionStep]
    smoothness_score: Optional[float] = None
    model_trained: Optional[bool] = None  # Whether model was trained for this request
    model_name: Optional[str] = None  # Name of the model used
    model_age_days: Optional[int] = None  # Age of the model in days
    historical_candles: Optional[List[HistoricalCandle]] = None  # Recent OHLC data for candlestick chart


# Strategy Models
class Strategy(BaseModel):
    id: str
    name: str
    type: str
    status: str  # 'active' | 'inactive' | 'backtesting'
    params: Dict[str, Any]
    created_at: str
    last_signal: Optional[Dict[str, Any]] = None


class CreateStrategyRequest(BaseModel):
    name: str
    type: str
    params: Dict[str, Any]


# Model Models
class ModelPerformance(BaseModel):
    train_r2: float
    val_r2: float
    train_rmse: float
    val_rmse: float


class ModelInfo(BaseModel):
    name: str
    type: str  # 'autoregressive' | 'multi-model'
    symbol: str
    timeframe: str
    n_steps_ahead: int
    model_size_kb: float
    trained_at: str
    performance: ModelPerformance


class TrainModelRequest(BaseModel):
    symbol: str
    timeframe: str
    n_steps_ahead: int
    days_history: int


# Health Check
class HealthResponse(BaseModel):
    status: str
    version: str
