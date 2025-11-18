<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-xl text-accent-danger text-sm">
      {{ error }}
    </div>

    <!-- Portfolio Content -->
    <div v-else class="space-y-8">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          label="Total Portfolio Value"
          :value="formatCurrency(totalValue)"
          icon="💼"
          variant="primary"
        />

        <StatCard
          label="Total P&L"
          :value="formatCurrency(totalPnL)"
          :change="`${totalPnLPercent >= 0 ? '+' : ''}${totalPnLPercent.toFixed(2)}%`"
          :variant="totalPnL >= 0 ? 'success' : 'danger'"
          :trend="totalPnL >= 0 ? 'up' : 'down'"
        />

        <StatCard
          label="Daily P&L"
          :value="formatCurrency(dailyPnL)"
          :change="`${dailyPnLPercent >= 0 ? '+' : ''}${dailyPnLPercent.toFixed(2)}%`"
          :variant="dailyPnL >= 0 ? 'success' : 'danger'"
          :trend="dailyPnL >= 0 ? 'up' : 'down'"
        />
      </div>

      <!-- Positions Table -->
      <Card title="Active Positions" :icon="BriefcaseIcon">
        <template #actions>
          <Button @click="refreshPortfolio" variant="secondary" size="sm">
            Refresh
          </Button>
        </template>

        <div v-if="!hasPositions" class="text-center py-12">
          <BriefcaseIcon class="w-16 h-16 mx-auto text-text-muted mb-4" />
          <p class="text-text-secondary">No active positions</p>
        </div>

        <Table v-else>
          <template #header>
            <TableHeader>Symbol</TableHeader>
            <TableHeader>Side</TableHeader>
            <TableHeader align="right">Quantity</TableHeader>
            <TableHeader align="right">Entry Price</TableHeader>
            <TableHeader align="right">Current Price</TableHeader>
            <TableHeader align="right">P&L</TableHeader>
            <TableHeader align="right">P&L %</TableHeader>
            <TableHeader>Opened</TableHeader>
          </template>

          <TableRow v-for="(position, index) in portfolio?.positions" :key="index">
            <TableCell bold>{{ position.symbol }}</TableCell>
            <TableCell>
              <Badge :variant="position.side === 'long' ? 'success' : 'danger'" size="sm">
                {{ position.side.toUpperCase() }}
              </Badge>
            </TableCell>
            <TableCell align="right" mono>{{ position.quantity }}</TableCell>
            <TableCell align="right" mono>${{ position.entry_price.toFixed(2) }}</TableCell>
            <TableCell align="right" mono>${{ position.current_price.toFixed(2) }}</TableCell>
            <TableCell align="right" mono :class="position.pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'">
              {{ position.pnl >= 0 ? '+' : '' }}${{ formatNumber(position.pnl) }}
            </TableCell>
            <TableCell align="right" mono :class="position.pnl_pct >= 0 ? 'text-accent-success' : 'text-accent-danger'">
              {{ position.pnl_pct >= 0 ? '+' : '' }}{{ (position.pnl_pct * 100).toFixed(2) }}%
            </TableCell>
            <TableCell>{{ formatDate(position.opened_at) }}</TableCell>
          </TableRow>
        </Table>
      </Card>

      <!-- Portfolio History Chart -->
      <Card title="Portfolio Value History (30 Days)" :icon="ChartBarIcon">
        <div class="h-64">
          <canvas ref="historyChartCanvas"></canvas>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import { storeToRefs } from 'pinia'
import { useChart } from '../composables/useChart'
import api from '../services/api'
import { BriefcaseIcon, ChartBarIcon } from '@heroicons/vue/24/outline'
import Card from '@/shared/components/ui/Card.vue'
import Button from '@/shared/components/ui/Button.vue'
import Badge from '@/shared/components/ui/Badge.vue'
import StatCard from '@/features/dashboard/components/StatCard.vue'
import Table from '@/shared/components/ui/Table.vue'
import TableHeader from '@/shared/components/ui/TableHeader.vue'
import TableRow from '@/shared/components/ui/TableRow.vue'
import TableCell from '@/shared/components/ui/TableCell.vue'

const portfolioStore = usePortfolioStore()
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
} = storeToRefs(portfolioStore)

const historyChartCanvas = ref<HTMLCanvasElement | null>(null)
const { createChart } = useChart(historyChartCanvas)

onMounted(async () => {
  await refreshPortfolio()
  await loadHistory()
})

async function refreshPortfolio() {
  try {
    await portfolioStore.fetchPortfolio()
  } catch (e) {
    console.error('Failed to fetch portfolio:', e)
  }
}

async function loadHistory() {
  try {
    const history = await api.getPortfolioHistory(30)
    await nextTick()
    createHistoryChart(history)
  } catch (e) {
    console.error('Failed to fetch portfolio history:', e)
  }
}

function createHistoryChart(history: any[]) {
  if (!historyChartCanvas.value || !history.length) return

  const labels = history.map(h => new Date(h.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
  const values = history.map(h => h.total_value)

  createChart({
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Portfolio Value',
          data: values,
          borderColor: 'rgb(62, 207, 142)',
          backgroundColor: 'rgba(62, 207, 142, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
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
              return `Value: $${context.parsed.y.toLocaleString()}`
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
  })
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatNumber(value: number): string {
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
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
