<template>
  <div>
    <!-- Header with Back Button -->
    <div class="mb-8">
      <button @click="$router.back()" class="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Back to Backtests
      </button>
      <h1 class="text-3xl font-bold text-gray-900">Backtest Details</h1>
      <p class="mt-2 text-gray-600">Detailed analysis of backtest performance</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-gray-500">Loading backtest details...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200 mb-8">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Backtest Content -->
    <div v-else-if="backtest">
      <!-- Performance Summary -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="stat-card">
          <div class="stat-label">Total Return</div>
          <div class="stat-value" :class="backtest.performance.total_return >= 0 ? 'positive' : 'negative'">
            {{ backtest.performance.total_return >= 0 ? '+' : '' }}{{ (backtest.performance.total_return * 100).toFixed(2) }}%
          </div>
          <div class="text-xs text-gray-500 mt-2">${{ backtest.performance.total_pnl.toFixed(2) }} profit</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Sharpe Ratio</div>
          <div class="stat-value">{{ backtest.performance.sharpe_ratio.toFixed(2) }}</div>
          <div class="text-xs text-gray-500 mt-2">Risk-adjusted return</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Max Drawdown</div>
          <div class="stat-value negative">{{ (backtest.performance.max_drawdown * 100).toFixed(1) }}%</div>
          <div class="text-xs text-gray-500 mt-2">Largest decline</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Win Rate</div>
          <div class="stat-value">{{ (backtest.trading.win_rate * 100).toFixed(1) }}%</div>
          <div class="text-xs text-gray-500 mt-2">{{ backtest.trading.winning_trades }} of {{ backtest.trading.total_trades }} trades</div>
        </div>
      </div>

      <!-- Strategy Info -->
      <div class="card mb-8">
        <h2 class="card-header">Strategy Information</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div class="text-sm text-gray-600">Strategy</div>
            <div class="font-medium">{{ backtest.strategy }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Symbol</div>
            <div class="font-medium">{{ backtest.symbol }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Period</div>
            <div class="font-medium">{{ formatDate(backtest.start_date) }} - {{ formatDate(backtest.end_date) }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Initial Capital</div>
            <div class="font-medium">${{ backtest.performance.initial_cash.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div class="card">
          <h3 class="card-header">Equity Curve</h3>
          <div class="h-64">
            <canvas ref="equityChartCanvas"></canvas>
          </div>
        </div>

        <div class="card">
          <h3 class="card-header">Returns Distribution</h3>
          <div class="h-64">
            <canvas ref="returnsChartCanvas"></canvas>
          </div>
        </div>
      </div>

      <!-- Trading Metrics -->
      <div class="card mb-8">
        <h2 class="card-header">Trading Metrics</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <div>
            <div class="text-sm text-gray-600">Total Trades</div>
            <div class="text-xl font-semibold">{{ backtest.trading.total_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Winning Trades</div>
            <div class="text-xl font-semibold positive">{{ backtest.trading.winning_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Losing Trades</div>
            <div class="text-xl font-semibold negative">{{ backtest.trading.losing_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Avg Win</div>
            <div class="text-xl font-semibold positive">${{ backtest.trading.avg_win.toFixed(2) }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Avg Loss</div>
            <div class="text-xl font-semibold negative">${{ backtest.trading.avg_loss.toFixed(2) }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-600">Profit Factor</div>
            <div class="text-xl font-semibold">{{ backtest.trading.profit_factor.toFixed(2) }}</div>
          </div>
        </div>
      </div>

      <!-- Recent Trades -->
      <div class="card">
        <h2 class="card-header">Recent Trades</h2>
        <div class="text-center py-8 text-gray-500">
          Trade details will be available when connected to full backtest engine
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import type { BacktestResult } from '../types';
import api from '../services/api';
import { useChart } from '../composables/useChart';
import Button from '@/shared/components/ui/Button.vue';

const route = useRoute();
const backtest = ref<BacktestResult | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const equityChartCanvas = ref<HTMLCanvasElement | null>(null);
const returnsChartCanvas = ref<HTMLCanvasElement | null>(null);

const { createChart: createEquityChart } = useChart(equityChartCanvas);
const { createChart: createReturnsChart } = useChart(returnsChartCanvas);

onMounted(async () => {
  await fetchBacktest();
});

watch(backtest, async (newBacktest) => {
  if (newBacktest) {
    await nextTick();
    createCharts(newBacktest);
  }
});

async function fetchBacktest() {
  loading.value = true;
  error.value = null;
  try {
    const id = route.params.id as string;
    backtest.value = await api.getBacktest(id);
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch backtest details';
    console.error('Failed to fetch backtest:', e);
  } finally {
    loading.value = false;
  }
}

function createCharts(bt: BacktestResult) {
  // Create mock equity curve data (in real app, this would come from backtest results)
  const days = 30;
  const equityData = [];
  let equity = bt.performance.initial_cash;

  for (let i = 0; i <= days; i++) {
    // Simulate equity growth
    const dailyReturn = (Math.random() - 0.45) * 100; // Slight upward bias
    equity += dailyReturn;
    equityData.push(equity);
  }

  // Equity Curve
  createEquityChart({
    type: 'line',
    data: {
      labels: Array.from({ length: days + 1 }, (_, i) => `Day ${i}`),
      datasets: [
        {
          label: 'Portfolio Value',
          data: equityData,
          borderColor: 'rgb(37, 99, 235)',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0,  // Straight lines for discrete time points
          pointRadius: 1,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (context) => `Value: $${context.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          display: true,
          ticks: {
            maxTicksLimit: 10,
          },
        },
        y: {
          display: true,
          ticks: {
            callback: (value) => `$${value.toLocaleString()}`,
          },
        },
      },
    },
  });

  // Returns Distribution (histogram)
  const returns = [];
  for (let i = 0; i < 50; i++) {
    returns.push((Math.random() - 0.5) * 10); // Random returns between -5% and 5%
  }

  // Create histogram bins
  const bins = 15;
  const min = Math.min(...returns);
  const max = Math.max(...returns);
  const binSize = (max - min) / bins;
  const binCounts = new Array(bins).fill(0);

  returns.forEach(ret => {
    const binIndex = Math.min(Math.floor((ret - min) / binSize), bins - 1);
    binCounts[binIndex]++;
  });

  createReturnsChart({
    type: 'line',
    data: {
      labels: Array.from({ length: bins }, (_, i) => `${(min + i * binSize).toFixed(1)}%`),
      datasets: [
        {
          label: 'Frequency',
          data: binCounts,
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.5)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Return %',
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Frequency',
          },
          ticks: {
            stepSize: 1,
          },
        },
      },
    },
  });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
</script>
