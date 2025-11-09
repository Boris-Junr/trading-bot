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
    return [...backtests.value].sort((a, b) =>
      new Date(b.end_date).getTime() - new Date(a.end_date).getTime()
    );
  });

  const bestBacktest = computed(() => {
    if (backtests.value.length === 0) return null;
    return [...backtests.value].sort((a, b) =>
      b.performance.total_return - a.performance.total_return
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
