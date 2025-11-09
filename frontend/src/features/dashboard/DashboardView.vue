<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gradient">Dashboard</h1>
        <p class="mt-1 text-text-secondary">Real-time trading bot performance</p>
      </div>
      <div class="flex items-center gap-3">
        <Badge variant="success" dot>Live</Badge>
        <Button variant="secondary" size="sm">
          <ArrowPathIcon class="w-4 h-4" />
          Refresh
        </Button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Portfolio Value"
        :value="formatCurrency(totalValue)"
        icon="💼"
        variant="primary"
      />
      <StatCard
        label="Daily P&L"
        :value="formatCurrency(dailyPnL)"
        :change="`${dailyPnLPercent >= 0 ? '+' : ''}${dailyPnLPercent.toFixed(2)}%`"
        :variant="dailyPnL >= 0 ? 'success' : 'danger'"
        :trend="dailyPnL >= 0 ? 'up' : 'down'"
      />
      <StatCard
        label="Active Positions"
        :value="positionsCount.toString()"
        icon="📊"
        variant="info"
      />
      <StatCard
        label="Total P&L"
        :value="formatCurrency(totalPnL)"
        :change="`${totalPnLPercent >= 0 ? '+' : ''}${totalPnLPercent.toFixed(2)}%`"
        :variant="totalPnL >= 0 ? 'success' : 'danger'"
        :trend="totalPnL >= 0 ? 'up' : 'down'"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card title="Portfolio Value" :icon="ChartBarIcon">
        <div class="h-64 flex items-center justify-center bg-bg-tertiary rounded-lg border border-border-default">
          <div class="text-center">
            <SparklesIcon class="w-12 h-12 mx-auto text-accent-primary mb-2" />
            <p class="text-text-secondary">Chart visualization coming soon</p>
          </div>
        </div>
      </Card>

      <Card title="Performance Overview" :icon="ChartLineIcon">
        <div class="h-64 flex items-center justify-center bg-bg-tertiary rounded-lg border border-border-default">
          <div class="text-center">
            <SparklesIcon class="w-12 h-12 mx-auto text-accent-secondary mb-2" />
            <p class="text-text-secondary">Performance metrics loading...</p>
          </div>
        </div>
      </Card>
    </div>

    <!-- Recent Activity -->
    <Card title="Active Positions" :icon="BriefcaseIcon">
      <template #actions>
        <Button variant="ghost" size="sm">
          View All
          <ArrowRightIcon class="w-4 h-4" />
        </Button>
      </template>

      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="skeleton h-16"></div>
      </div>

      <div v-else-if="!hasPositions" class="text-center py-12">
        <BriefcaseIcon class="w-16 h-16 mx-auto text-text-muted mb-4" />
        <p class="text-text-secondary">No active positions</p>
        <Button variant="primary" size="sm" class="mt-4">
          Start Trading
        </Button>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(position, index) in portfolio?.positions"
          :key="index"
          class="position-card group"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="position-icon">
                <ChartBarIcon class="w-5 h-5" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-mono font-semibold text-text-primary">
                    {{ position.symbol }}
                  </span>
                  <Badge :variant="position.side === 'long' ? 'success' : 'danger'" size="sm">
                    {{ position.side.toUpperCase() }}
                  </Badge>
                </div>
                <div class="text-sm text-text-secondary mt-0.5">
                  {{ position.quantity }} units @ {{ formatCurrency(position.entry_price) }}
                </div>
              </div>
            </div>

            <div class="text-right">
              <div
                class="font-mono font-semibold text-lg"
                :class="position.pnl >= 0 ? 'positive' : 'negative'"
              >
                {{ position.pnl >= 0 ? '+' : '' }}{{ formatCurrency(position.pnl) }}
              </div>
              <div
                class="text-sm font-medium"
                :class="position.pnl_pct >= 0 ? 'positive' : 'negative'"
              >
                {{ position.pnl_pct >= 0 ? '+' : '' }}{{ position.pnl_pct.toFixed(2) }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Quick Actions -->
    <div class="flex gap-4">
      <Button variant="primary" :icon-left="ChartBarIcon" @click="$router.push('/backtests')">
        Run Backtest
      </Button>
      <Button variant="secondary" :icon-left="SparklesIcon" @click="$router.push('/predictions')">
        View Predictions
      </Button>
      <Button variant="ghost" :icon-left="CogIcon" @click="$router.push('/strategies')">
        Configure Strategy
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import Card from '@/shared/components/ui/Card.vue'
import Button from '@/shared/components/ui/Button.vue'
import Badge from '@/shared/components/ui/Badge.vue'
import StatCard from './components/StatCard.vue'
import {
  ChartBarIcon,
  BriefcaseIcon,
  SparklesIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  CogIcon,
  ChartLineIcon,
} from '@heroicons/vue/24/outline'

const portfolioStore = usePortfolioStore()
const loading = ref(true)

const portfolio = computed(() => portfolioStore.portfolio)
const hasPositions = computed(() => portfolio.value?.positions && portfolio.value.positions.length > 0)

const totalValue = computed(() => portfolio.value?.total_value || 100000)
const dailyPnL = computed(() => portfolio.value?.daily_pnl || 1250.50)
const dailyPnLPercent = computed(() => (dailyPnL.value / totalValue.value) * 100)
const totalPnL = computed(() => portfolio.value?.total_pnl || 5420.75)
const totalPnLPercent = computed(() => (totalPnL.value / (totalValue.value - totalPnL.value)) * 100)
const positionsCount = computed(() => portfolio.value?.positions?.length || 3)

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

onMounted(async () => {
  try {
    await portfolioStore.fetchPortfolio()
  } catch (error) {
    console.error('Error fetching portfolio:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.position-card {
  padding: 1rem;
  border-radius: 0.5rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  transition: all 200ms ease;
}

.position-card:hover {
  border-color: var(--accent-primary);
  background: var(--bg-hover);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);
}

.position-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
}
</style>
