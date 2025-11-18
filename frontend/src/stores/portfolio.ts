import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Portfolio } from '../types';
import api from '../services/api';

export const usePortfolioStore = defineStore('portfolio', () => {
  // State
  const portfolio = ref<Portfolio | null>(null);
  const history = ref<any[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const totalValue = computed(() => portfolio.value?.total_value || 0);
  const totalPnL = computed(() => portfolio.value?.total_pnl || 0);
  const totalPnLPercent = computed(() => (portfolio.value?.total_pnl_pct || 0) * 100);
  const dailyPnL = computed(() => portfolio.value?.daily_pnl || 0);
  const dailyPnLPercent = computed(() => (portfolio.value?.daily_pnl_pct || 0) * 100);

  const hasPositions = computed(() =>
    portfolio.value?.positions && portfolio.value.positions.length > 0
  );

  const positionsCount = computed(() => portfolio.value?.positions?.length || 0);

  // Actions
  async function fetchPortfolio() {
    loading.value = true;
    error.value = null;
    try {
      portfolio.value = await api.getPortfolio();
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch portfolio';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchHistory(days: number = 30) {
    loading.value = true;
    error.value = null;
    try {
      history.value = await api.getPortfolioHistory(days);
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch portfolio history';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    portfolio,
    history,
    loading,
    error,
    // Getters
    totalValue,
    totalPnL,
    totalPnLPercent,
    dailyPnL,
    dailyPnLPercent,
    hasPositions,
    positionsCount,
    // Actions
    fetchPortfolio,
    fetchHistory,
    clearError,
  };
});
