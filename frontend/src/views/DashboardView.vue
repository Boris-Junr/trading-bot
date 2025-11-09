<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
      <p class="mt-2 text-gray-600">Overview of your trading bot performance</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="stat-card">
        <div class="stat-label">Total Value</div>
        <div class="stat-value">${{ formatNumber(totalValue) }}</div>
        <div class="text-xs text-gray-500 mt-2">Portfolio</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Daily P&L</div>
        <div class="stat-value" :class="dailyPnL >= 0 ? 'positive' : 'negative'">
          {{ dailyPnL >= 0 ? '+' : '' }}${{ formatNumber(dailyPnL) }}
        </div>
        <div class="text-xs mt-2" :class="dailyPnL >= 0 ? 'positive' : 'negative'">
          {{ dailyPnLPercent >= 0 ? '+' : '' }}{{ dailyPnLPercent.toFixed(2) }}%
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Active Positions</div>
        <div class="stat-value">{{ positionsCount }}</div>
        <div class="text-xs text-gray-500 mt-2">Open trades</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Total P&L</div>
        <div class="stat-value" :class="totalPnL >= 0 ? 'positive' : 'negative'">
          {{ totalPnL >= 0 ? '+' : '' }}${{ formatNumber(totalPnL) }}
        </div>
        <div class="text-xs mt-2" :class="totalPnL >= 0 ? 'positive' : 'negative'">
          {{ totalPnLPercent >= 0 ? '+' : '' }}{{ totalPnLPercent.toFixed(2) }}%
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Portfolio Chart Placeholder -->
      <div class="card">
        <h3 class="card-header">Portfolio Value</h3>
        <div class="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
          <p class="text-gray-400">Chart will be displayed here</p>
        </div>
      </div>

      <!-- Performance Chart Placeholder -->
      <div class="card">
        <h3 class="card-header">Daily Performance</h3>
        <div class="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
          <p class="text-gray-400">Chart will be displayed here</p>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="card">
      <h3 class="card-header">Recent Activity</h3>
      <div class="space-y-4">
        <div v-if="loading" class="text-center py-8 text-gray-500">
          Loading...
        </div>
        <div v-else-if="!hasPositions" class="text-center py-8 text-gray-500">
          No active positions
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(position, index) in portfolio?.positions"
            :key="index"
            class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
          >
            <div>
              <div class="font-medium text-gray-900">{{ position.symbol }}</div>
              <div class="text-sm text-gray-600">
                {{ position.side.toUpperCase() }} · {{ position.quantity }} units
              </div>
            </div>
            <div class="text-right">
              <div class="font-medium" :class="position.pnl >= 0 ? 'positive' : 'negative'">
                {{ position.pnl >= 0 ? '+' : '' }}${{ formatNumber(position.pnl) }}
              </div>
              <div class="text-sm" :class="position.pnl_pct >= 0 ? 'positive' : 'negative'">
                {{ position.pnl_pct >= 0 ? '+' : '' }}{{ position.pnl_pct.toFixed(2) }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="mt-8 flex gap-4">
      <router-link to="/backtests" class="btn-primary">
        Run Backtest
      </router-link>
      <router-link to="/predictions" class="btn-secondary">
        View Predictions
      </router-link>
      <router-link to="/strategies" class="btn-secondary">
        Manage Strategies
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { usePortfolioStore } from '../stores/portfolio';
import { storeToRefs } from 'pinia';

const portfolioStore = usePortfolioStore();
const {
  portfolio,
  loading,
  totalValue,
  totalPnL,
  totalPnLPercent,
  dailyPnL,
  dailyPnLPercent,
  hasPositions,
  positionsCount,
} = storeToRefs(portfolioStore);

onMounted(async () => {
  try {
    await portfolioStore.fetchPortfolio();
  } catch (error) {
    console.error('Failed to fetch portfolio:', error);
  }
});

function formatNumber(value: number): string {
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
</script>
