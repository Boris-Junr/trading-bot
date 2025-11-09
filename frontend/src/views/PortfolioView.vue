<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900">Portfolio</h1>
      <p class="mt-2 text-gray-600">Detailed view of your positions and performance</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-gray-500">Loading portfolio...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Portfolio Content -->
    <div v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="stat-card">
          <div class="stat-label">Total Portfolio Value</div>
          <div class="stat-value">${{ formatNumber(totalValue) }}</div>
          <div class="text-xs text-gray-500 mt-2">Cash: ${{ formatNumber(portfolio?.cash || 0) }}</div>
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

        <div class="stat-card">
          <div class="stat-label">Daily P&L</div>
          <div class="stat-value" :class="dailyPnL >= 0 ? 'positive' : 'negative'">
            {{ dailyPnL >= 0 ? '+' : '' }}${{ formatNumber(dailyPnL) }}
          </div>
          <div class="text-xs mt-2" :class="dailyPnL >= 0 ? 'positive' : 'negative'">
            {{ dailyPnLPercent >= 0 ? '+' : '' }}{{ dailyPnLPercent.toFixed(2) }}%
          </div>
        </div>
      </div>

      <!-- Positions Table -->
      <div class="card mb-8">
        <div class="flex justify-between items-center mb-6">
          <h2 class="card-header">Active Positions</h2>
          <Button @click="refreshPortfolio" variant="secondary" size="sm">
            Refresh
          </Button>
        </div>

        <div v-if="!hasPositions" class="text-center py-8 text-gray-500">
          No active positions
        </div>

        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Quantity</th>
                <th>Entry Price</th>
                <th>Current Price</th>
                <th>P&L</th>
                <th>P&L %</th>
                <th>Opened</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(position, index) in portfolio?.positions" :key="index">
                <td class="font-medium text-gray-900">{{ position.symbol }}</td>
                <td>
                  <span
                    class="px-2 py-1 text-xs font-medium rounded"
                    :class="position.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  >
                    {{ position.side.toUpperCase() }}
                  </span>
                </td>
                <td>{{ position.quantity }}</td>
                <td>${{ position.entry_price.toFixed(2) }}</td>
                <td>${{ position.current_price.toFixed(2) }}</td>
                <td :class="position.pnl >= 0 ? 'positive' : 'negative'">
                  {{ position.pnl >= 0 ? '+' : '' }}${{ formatNumber(position.pnl) }}
                </td>
                <td :class="position.pnl_pct >= 0 ? 'positive' : 'negative'">
                  {{ position.pnl_pct >= 0 ? '+' : '' }}{{ position.pnl_pct.toFixed(2) }}%
                </td>
                <td class="text-gray-600">{{ formatDate(position.opened_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Portfolio History Chart -->
      <div class="card">
        <h2 class="card-header">Portfolio Value History (30 Days)</h2>
        <div class="h-64">
          <canvas ref="historyChartCanvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { usePortfolioStore } from '../stores/portfolio';
import { storeToRefs } from 'pinia';
import { useChart } from '../composables/useChart';
import api from '../services/api';
import Button from '@/shared/components/ui/Button.vue';

const portfolioStore = usePortfolioStore();
const {
  portfolio,
  loading,
  error,
  totalValue,
  totalPnL,
  totalPnLPercent,
  dailyPnL,
  dailyPnLPercent,
  hasPositions,
} = storeToRefs(portfolioStore);

const historyChartCanvas = ref<HTMLCanvasElement | null>(null);
const { createChart } = useChart(historyChartCanvas);

onMounted(async () => {
  await refreshPortfolio();
  await loadHistory();
});

async function refreshPortfolio() {
  try {
    await portfolioStore.fetchPortfolio();
  } catch (e) {
    console.error('Failed to fetch portfolio:', e);
  }
}

async function loadHistory() {
  try {
    const history = await api.getPortfolioHistory(30);
    await nextTick();
    createHistoryChart(history);
  } catch (e) {
    console.error('Failed to fetch portfolio history:', e);
  }
}

function createHistoryChart(history: any[]) {
  if (!historyChartCanvas.value || !history.length) return;

  const labels = history.map(h => new Date(h.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
  const values = history.map(h => h.total_value);

  createChart({
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Portfolio Value',
          data: values,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0,  // Straight lines for discrete time points
          pointRadius: 2,
          pointHoverRadius: 5,
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
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              return `Value: $${context.parsed.y.toLocaleString()}`;
            },
          },
        },
      },
      scales: {
        x: {
          display: true,
          grid: {
            display: false,
          },
        },
        y: {
          display: true,
          ticks: {
            callback: (value) => `$${value.toLocaleString()}`,
          },
        },
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false,
      },
    },
  });
}

function formatNumber(value: number): string {
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>
