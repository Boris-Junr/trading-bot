<template>
  <div>
    <!-- Loading State -->
    <LoadingSpinner v-if="loading" />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

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
          :change="formatPercent(totalPnLPercent)"
          :variant="totalPnL >= 0 ? 'success' : 'danger'"
          :trend="totalPnL >= 0 ? 'up' : 'down'"
        />

        <StatCard
          label="Daily P&L"
          :value="formatCurrency(dailyPnL)"
          :change="formatPercent(dailyPnLPercent)"
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

        <EmptyState
          v-if="!hasPositions"
          :icon="BriefcaseIcon"
          title="No Active Positions"
          description="You don't have any open positions at the moment. Start trading to see your portfolio here."
        />

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
            <TableCell align="right" mono>{{ formatNumber(position.quantity, 8) }}</TableCell>
            <TableCell align="right" mono>{{ formatCurrency(position.entry_price) }}</TableCell>
            <TableCell align="right" mono>{{ formatCurrency(position.current_price) }}</TableCell>
            <TableCell align="right" mono :class="position.pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'">
              {{ formatCurrency(position.pnl) }}
            </TableCell>
            <TableCell align="right" mono :class="position.pnl_pct >= 0 ? 'text-accent-success' : 'text-accent-danger'">
              {{ formatPercent(position.pnl_pct * 100) }}
            </TableCell>
            <TableCell>{{ formatDate(position.opened_at, 'long') }}</TableCell>
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
import { useFormatters } from '@/composables/useFormatters'
import api from '../services/api'
import { BriefcaseIcon, ChartBarIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatCard from '@/features/dashboard/components/StatCard.vue'
import Table from '@/components/ui/Table.vue'
import TableHeader from '@/components/ui/TableHeader.vue'
import TableRow from '@/components/ui/TableRow.vue'
import TableCell from '@/components/ui/TableCell.vue'

const { formatDate, formatCurrency, formatNumber, formatPercent } = useFormatters()

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
            label: (context: any) => {
              return `Value: ${formatCurrency(context.parsed.y ?? 0)}`
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
            callback: (value) => formatCurrency(value as number),
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
</script>
