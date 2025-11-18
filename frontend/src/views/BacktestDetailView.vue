<template>
  <div>
    <!-- Back Button -->
    <div class="mb-8">
      <Button @click="$router.back()" variant="secondary" size="sm" class="mb-4">
        <ArrowLeftIcon class="w-4 h-4 mr-2" />
        Back to Backtests
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-xl text-accent-danger text-sm mb-8">
      {{ error }}
    </div>

    <!-- Backtest Content -->
    <div v-else-if="backtest" class="space-y-8">
      <!-- Performance Summary -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total Return"
          :value="`${backtest.performance.total_return >= 0 ? '+' : ''}${(backtest.performance.total_return * 100).toFixed(2)}%`"
          :change="`$${backtest.performance.total_pnl.toFixed(2)} profit`"
          :variant="backtest.performance.total_return >= 0 ? 'success' : 'danger'"
        />

        <StatCard
          label="Sharpe Ratio"
          :value="backtest.performance.sharpe_ratio.toFixed(2)"
          change="Risk-adjusted return"
          variant="primary"
        />

        <StatCard
          label="Max Drawdown"
          :value="`${(backtest.performance.max_drawdown * 100).toFixed(1)}%`"
          change="Largest decline"
          variant="danger"
        />

        <StatCard
          label="Win Rate"
          :value="`${(backtest.trading.win_rate * 100).toFixed(1)}%`"
          :change="`${backtest.trading.winning_trades} of ${backtest.trading.total_trades} trades`"
          variant="success"
        />
      </div>

      <!-- Strategy Info -->
      <Card title="Strategy Information">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div class="text-sm text-text-secondary mb-1">Strategy</div>
            <div class="font-medium text-text-primary">{{ backtest.strategy }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Symbol</div>
            <div class="font-medium text-text-primary">{{ backtest.symbol }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Period</div>
            <div class="font-medium text-text-primary">{{ formatDate(backtest.start_date) }} - {{ formatDate(backtest.end_date) }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Initial Capital</div>
            <div class="font-medium text-text-primary">${{ backtest.performance.initial_cash.toLocaleString() }}</div>
          </div>
        </div>
      </Card>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Equity Curve" :icon="ChartBarIcon">
          <div class="h-64">
            <canvas ref="equityChartCanvas"></canvas>
          </div>
        </Card>

        <Card title="Returns Distribution" :icon="ChartBarIcon">
          <div class="h-64">
            <canvas ref="returnsChartCanvas"></canvas>
          </div>
        </Card>
      </div>

      <!-- Trading Metrics -->
      <Card title="Trading Metrics">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <div>
            <div class="text-sm text-text-secondary mb-1">Total Trades</div>
            <div class="text-xl font-semibold text-text-primary">{{ backtest.trading.total_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Winning Trades</div>
            <div class="text-xl font-semibold text-accent-success">{{ backtest.trading.winning_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Losing Trades</div>
            <div class="text-xl font-semibold text-accent-danger">{{ backtest.trading.losing_trades }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Avg Win</div>
            <div class="text-xl font-semibold text-accent-success">${{ backtest.trading.avg_win.toFixed(2) }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Avg Loss</div>
            <div class="text-xl font-semibold text-accent-danger">${{ backtest.trading.avg_loss.toFixed(2) }}</div>
          </div>
          <div>
            <div class="text-sm text-text-secondary mb-1">Profit Factor</div>
            <div class="text-xl font-semibold text-text-primary">{{ backtest.trading.profit_factor.toFixed(2) }}</div>
          </div>
        </div>
      </Card>

      <!-- Recent Trades -->
      <Card title="Recent Trades">
        <div class="text-center py-8 text-text-muted">
          Trade details will be available when connected to full backtest engine
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import type { BacktestResult } from '../types'
import api from '../services/api'
import { useChart } from '../composables/useChart'
import { ChartBarIcon, ArrowLeftIcon } from '@heroicons/vue/24/outline'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import StatCard from '@/features/dashboard/components/StatCard.vue'

const route = useRoute()
const backtest = ref<BacktestResult | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const equityChartCanvas = ref<HTMLCanvasElement | null>(null)
const returnsChartCanvas = ref<HTMLCanvasElement | null>(null)

const { createChart: createEquityChart } = useChart(equityChartCanvas)
const { createChart: createReturnsChart } = useChart(returnsChartCanvas)

onMounted(async () => {
  await fetchBacktest()
})

watch(backtest, async (newBacktest) => {
  if (newBacktest) {
    await nextTick()
    createCharts(newBacktest)
  }
})

async function fetchBacktest() {
  loading.value = true
  error.value = null
  try {
    const id = route.params.id as string
    backtest.value = await api.getBacktest(id)
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch backtest details'
    console.error('Failed to fetch backtest:', e)
  } finally {
    loading.value = false
  }
}

function createCharts(bt: BacktestResult) {
  // Create mock equity curve data (in real app, this would come from backtest results)
  const days = 30
  const equityData = []
  let equity = bt.performance.initial_cash

  for (let i = 0; i <= days; i++) {
    // Simulate equity growth
    const dailyReturn = (Math.random() - 0.45) * 100 // Slight upward bias
    equity += dailyReturn
    equityData.push(equity)
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
          borderColor: 'rgb(62, 207, 142)',
          backgroundColor: 'rgba(62, 207, 142, 0.1)',
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
  })

  // Returns Distribution (histogram)
  const returns = []
  for (let i = 0; i < 50; i++) {
    returns.push((Math.random() - 0.5) * 10) // Random returns between -5% and 5%
  }

  // Create histogram bins
  const bins = 15
  const min = Math.min(...returns)
  const max = Math.max(...returns)
  const binSize = (max - min) / bins
  const binCounts = new Array(bins).fill(0)

  returns.forEach(ret => {
    const binIndex = Math.min(Math.floor((ret - min) / binSize), bins - 1)
    binCounts[binIndex]++
  })

  createReturnsChart({
    type: 'line',
    data: {
      labels: Array.from({ length: bins }, (_, i) => `${(min + i * binSize).toFixed(1)}%`),
      datasets: [
        {
          label: 'Frequency',
          data: binCounts,
          borderColor: 'rgb(62, 207, 142)',
          backgroundColor: 'rgba(62, 207, 142, 0.5)',
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
  })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>

<style scoped>
.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid var(--border-default);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
