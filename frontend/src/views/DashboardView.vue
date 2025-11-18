<template>
  <div class="space-y-8">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        label="Total Value"
        :value="`$${formatNumber(totalValue)}`"
        change="Portfolio"
        variant="primary"
      />

      <StatCard
        label="Daily P&L"
        :value="`${dailyPnL >= 0 ? '+' : ''}$${formatNumber(dailyPnL)}`"
        :change="`${dailyPnLPercent >= 0 ? '+' : ''}${dailyPnLPercent.toFixed(2)}%`"
        :variant="dailyPnL >= 0 ? 'success' : 'danger'"
      />

      <StatCard
        label="Active Positions"
        :value="positionsCount.toString()"
        change="Open trades"
        variant="primary"
      />

      <StatCard
        label="Total P&L"
        :value="`${totalPnL >= 0 ? '+' : ''}$${formatNumber(totalPnL)}`"
        :change="`${totalPnLPercent >= 0 ? '+' : ''}${totalPnLPercent.toFixed(2)}%`"
        :variant="totalPnL >= 0 ? 'success' : 'danger'"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card title="Portfolio Value" :icon="ChartBarIcon">
        <div class="h-64 flex items-center justify-center bg-bg-tertiary rounded-lg">
          <p class="text-text-muted">Chart will be displayed here</p>
        </div>
      </Card>

      <Card title="Daily Performance" :icon="ChartBarIcon">
        <div class="h-64 flex items-center justify-center bg-bg-tertiary rounded-lg">
          <p class="text-text-muted">Chart will be displayed here</p>
        </div>
      </Card>
    </div>

    <!-- Recent Activity -->
    <Card title="Recent Activity" :icon="ClockIcon">
      <div class="space-y-4">
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="spinner"></div>
        </div>
        <div v-else-if="!hasPositions" class="text-center py-8 text-text-muted">
          No active positions
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(position, index) in portfolio?.positions"
            :key="index"
            class="flex items-center justify-between p-4 bg-bg-tertiary rounded-lg border border-border-default hover:border-accent-primary transition-all"
          >
            <div>
              <div class="font-medium text-text-primary">{{ position.symbol }}</div>
              <div class="text-sm text-text-secondary">
                {{ position.side.toUpperCase() }} · {{ position.quantity }} units
              </div>
            </div>
            <div class="text-right">
              <div class="font-medium" :class="position.pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'">
                {{ position.pnl >= 0 ? '+' : '' }}${{ formatNumber(position.pnl) }}
              </div>
              <div class="text-sm" :class="position.pnl_pct >= 0 ? 'text-accent-success' : 'text-accent-danger'">
                {{ position.pnl_pct >= 0 ? '+' : '' }}{{ position.pnl_pct.toFixed(2) }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Quick Actions -->
    <div class="flex flex-wrap gap-4">
      <Button @click="$router.push('/backtests')" variant="primary">
        Run Backtest
      </Button>
      <Button @click="$router.push('/predictions')" variant="secondary">
        View Predictions
      </Button>
      <Button @click="$router.push('/strategies')" variant="secondary">
        Manage Strategies
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import { storeToRefs } from 'pinia'
import { ChartBarIcon, ClockIcon } from '@heroicons/vue/24/outline'
import StatCard from '@/features/dashboard/components/StatCard.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const portfolioStore = usePortfolioStore()
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
} = storeToRefs(portfolioStore)

onMounted(async () => {
  try {
    await portfolioStore.fetchPortfolio()
  } catch (error) {
    console.error('Failed to fetch portfolio:', error)
  }
})

function formatNumber(value: number): string {
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
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
