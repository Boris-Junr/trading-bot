import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { BacktestResult, BacktestScenario } from '../types';
import api from '../services/api';

export const useBacktestStore = defineStore('backtest', () => {
  // State
  const backtests = ref<BacktestResult[]>([]);
  const currentBacktest = ref<BacktestResult | null>(null);
  const scenarios = ref<BacktestScenario[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const sortedBacktests = computed(() => {
    return [...backtests.value].sort((a, b) => {
      // Sort by creation date (when the backtest was run), most recent first
      let dateA: number;
      let dateB: number;

      // Try to get created_at, otherwise parse from ID, otherwise fall back to end_date
      if (a.created_at) {
        dateA = new Date(a.created_at).getTime();
      } else if (a.id) {
        // Parse timestamp from ID format: Strategy_Symbol_YYYYMMDD_HHMMSS
        const match = a.id.match(/_(\d{8})_(\d{6})$/);
        if (match && match[1] && match[2]) {
          const dateStr = match[1];
          const timeStr = match[2];
          const year = dateStr.substring(0, 4);
          const month = dateStr.substring(4, 6);
          const day = dateStr.substring(6, 8);
          const hour = timeStr.substring(0, 2);
          const minute = timeStr.substring(2, 4);
          const second = timeStr.substring(4, 6);
          dateA = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`).getTime();
        } else {
          dateA = new Date(a.end_date).getTime();
        }
      } else {
        dateA = new Date(a.end_date).getTime();
      }

      if (b.created_at) {
        dateB = new Date(b.created_at).getTime();
      } else if (b.id) {
        const match = b.id.match(/_(\d{8})_(\d{6})$/);
        if (match && match[1] && match[2]) {
          const dateStr = match[1];
          const timeStr = match[2];
          const year = dateStr.substring(0, 4);
          const month = dateStr.substring(4, 6);
          const day = dateStr.substring(6, 8);
          const hour = timeStr.substring(0, 2);
          const minute = timeStr.substring(2, 4);
          const second = timeStr.substring(4, 6);
          dateB = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`).getTime();
        } else {
          dateB = new Date(b.end_date).getTime();
        }
      } else {
        dateB = new Date(b.end_date).getTime();
      }

      return dateB - dateA; // Larger (more recent) timestamp comes first
    });
  });

  const bestBacktest = computed(() => {
    // Filter out failed backtests before finding the best one
    const successfulBacktests = backtests.value.filter(bt => bt.status !== 'failed' && bt.performance);
    if (successfulBacktests.length === 0) return null;
    return [...successfulBacktests].sort((a, b) =>
      b.performance!.total_return - a.performance!.total_return
    )[0];
  });

  // Actions
  async function fetchBacktests() {
    loading.value = true;
    error.value = null;
    try {
      backtests.value = await api.getBacktests();
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch backtests';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchBacktest(id: string) {
    loading.value = true;
    error.value = null;
    try {
      currentBacktest.value = await api.getBacktest(id);
      return currentBacktest.value;
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch backtest';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function runBacktest(scenario: BacktestScenario) {
    loading.value = true;
    error.value = null;
    try {
      const result = await api.runBacktest(scenario);
      backtests.value.push(result);
      currentBacktest.value = result;
      return result;
    } catch (e: any) {
      error.value = e.message || 'Failed to run backtest';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchScenarios() {
    loading.value = true;
    error.value = null;
    try {
      scenarios.value = await api.getBacktestScenarios();
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch scenarios';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function setCurrentBacktest(backtest: BacktestResult) {
    currentBacktest.value = backtest;
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    backtests,
    currentBacktest,
    scenarios,
    loading,
    error,
    // Getters
    sortedBacktests,
    bestBacktest,
    // Actions
    fetchBacktests,
    fetchBacktest,
    runBacktest,
    fetchScenarios,
    setCurrentBacktest,
    clearError,
  };
});
