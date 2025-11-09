// Trading Bot Types

export interface BacktestResult {
  strategy: string;
  symbol: string;
  start_date: string;
  end_date: string;
  performance: Performance;
  trading: TradingStats;
  equity_curve?: EquityPoint[];
  trades?: Trade[];
  daily_performance?: DailyPerformance[];
}

export interface Performance {
  initial_cash: number;
  final_equity: number;
  total_return: number;
  total_pnl: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface TradingStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
}

export interface Trade {
  id: number;
  symbol: string;
  side: 'long' | 'short';
  entry_price: number;
  exit_price: number;
  entry_time: string;
  exit_time: string;
  quantity: number;
  pnl: number;
  return_pct: number;
  duration_minutes: number;
}

export interface DailyPerformance {
  date: string;
  day: number;
  daily_pnl: number;
  daily_return: number;
  cumulative_pnl: number;
  cumulative_return: number;
  equity: number;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
}

export interface HistoricalCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PredictionData {
  timestamp: string;
  current_price: number;
  predictions: PredictionStep[];
  smoothness_score?: number;
  model_trained?: boolean;  // Whether model was trained for this request
  model_name?: string;  // Name of the model used
  model_age_days?: number;  // Age of the model in days
  historical_candles?: HistoricalCandle[];  // Recent OHLC data for candlestick chart
}

export interface PredictionStep {
  step: number;
  minutes_ahead: number;
  timestamp: string;
  predicted_open: number;
  predicted_high: number;
  predicted_low: number;
  predicted_close: number;
  predicted_return: number;
  confidence?: number;
}

export interface ModelInfo {
  name: string;
  type: 'autoregressive' | 'multi-model';
  symbol: string;
  timeframe: string;
  n_steps_ahead: number;
  model_size_kb: number;
  trained_at: string;
  performance: ModelPerformance;
}

export interface ModelPerformance {
  train_r2: number;
  val_r2: number;
  train_rmse: number;
  val_rmse: number;
  test_metrics?: Record<number, StepMetrics>;
}

export interface StepMetrics {
  rmse: number;
  mae: number;
  r2: number;
  mape: number;
}

export interface Strategy {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'backtesting';
  params: Record<string, any>;
  created_at: string;
  last_signal?: Signal;
}

export interface Signal {
  type: 'BUY' | 'SELL' | 'HOLD' | 'CLOSE_LONG' | 'CLOSE_SHORT';
  confidence: number;
  timestamp: string;
  price: number;
  metadata?: Record<string, any>;
}

export interface Portfolio {
  total_value: number;
  cash: number;
  positions: Position[];
  daily_pnl: number;
  daily_pnl_pct: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export interface Position {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  opened_at: string;
}

export interface BacktestScenario {
  strategy: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  params: Record<string, any>;
}
