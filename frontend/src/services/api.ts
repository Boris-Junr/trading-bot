import axios, { type AxiosInstance } from 'axios';
import type {
  BacktestResult,
  BacktestScenario,
  PredictionData,
  ModelInfo,
  Strategy,
  Portfolio,
} from '../types';
import { supabase } from '@/lib/supabase';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Add Supabase auth token if available
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          config.headers.Authorization = `Bearer ${session.access_token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - sign out and redirect
          await supabase.auth.signOut();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Backtest endpoints
  async getBacktests(): Promise<BacktestResult[]> {
    const response = await this.client.get('/backtests');
    return response.data;
  }

  async getBacktest(id: string): Promise<BacktestResult> {
    const response = await this.client.get(`/backtests/${id}`);
    return response.data;
  }

  async runBacktest(scenario: BacktestScenario): Promise<BacktestResult> {
    const response = await this.client.post('/backtests/run', scenario, {
      timeout: 300000  // 5 minutes timeout for backtests
    });
    return response.data;
  }

  async getBacktestScenarios(): Promise<BacktestScenario[]> {
    const response = await this.client.get('/backtests/scenarios');
    return response.data;
  }

  // Prediction endpoints
  async getPredictions(symbol: string, timeframe: string): Promise<PredictionData> {
    const response = await this.client.get('/predictions', {
      params: { symbol, timeframe },
    });
    return response.data;
  }

  async generatePredictions(
    symbol: string,
    timeframe: string,
    autoTrain: boolean = true
  ): Promise<any> {
    const response = await this.client.post('/predictions/generate', null, {
      params: { symbol, timeframe, auto_train: autoTrain },
    });
    return response.data;
  }

  async listPredictions(): Promise<any[]> {
    const response = await this.client.get('/predictions/list');
    return response.data;
  }

  async getPredictionById(predictionId: string): Promise<any> {
    const response = await this.client.get(`/predictions/${predictionId}`);
    return response.data;
  }

  // Model endpoints
  async getModels(): Promise<ModelInfo[]> {
    const response = await this.client.get('/models');
    return response.data;
  }

  async getModel(name: string): Promise<ModelInfo> {
    const response = await this.client.get(`/models/${name}`);
    return response.data;
  }

  async trainModel(config: {
    symbol: string;
    timeframe: string;
    n_steps_ahead: number;
    days_history: number;
  }): Promise<ModelInfo> {
    const response = await this.client.post('/models/train', config);
    return response.data;
  }

  // Strategy endpoints
  async getStrategies(): Promise<Strategy[]> {
    const response = await this.client.get('/strategies');
    return response.data;
  }

  async getStrategy(id: string): Promise<Strategy> {
    const response = await this.client.get(`/strategies/${id}`);
    return response.data;
  }

  async createStrategy(strategy: Partial<Strategy>): Promise<Strategy> {
    const response = await this.client.post('/strategies', strategy);
    return response.data;
  }

  async updateStrategy(id: string, strategy: Partial<Strategy>): Promise<Strategy> {
    const response = await this.client.put(`/strategies/${id}`, strategy);
    return response.data;
  }

  async deleteStrategy(id: string): Promise<void> {
    await this.client.delete(`/strategies/${id}`);
  }

  async activateStrategy(id: string): Promise<Strategy> {
    const response = await this.client.post(`/strategies/${id}/activate`);
    return response.data;
  }

  async deactivateStrategy(id: string): Promise<Strategy> {
    const response = await this.client.post(`/strategies/${id}/deactivate`);
    return response.data;
  }

  // Portfolio endpoints
  async getPortfolio(): Promise<Portfolio> {
    const response = await this.client.get('/portfolio');
    return response.data;
  }

  async getPortfolioHistory(days: number = 30): Promise<any[]> {
    const response = await this.client.get('/portfolio/history', {
      params: { days },
    });
    return response.data;
  }

  // Market data endpoints
  async getMarketData(
    symbol: string,
    timeframe: string,
    start?: string,
    end?: string
  ): Promise<any[]> {
    const response = await this.client.get('/market/data', {
      params: { symbol, timeframe, start, end },
    });
    return response.data;
  }

  async getSymbols(assetType: string = 'all'): Promise<string[]> {
    const response = await this.client.get('/market/symbols', {
      params: { asset_type: assetType },
    });
    return response.data.symbols;
  }

  // Health check
  async health(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const api = new ApiService();
export default api;
