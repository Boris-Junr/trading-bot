<template>
  <div class="dashboard-container">
    <!-- Stats Grid -->
    <div class="stats-grid">
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
    <div class="charts-grid">
      <Card title="Portfolio Value" :icon="ChartBarIcon">
        <div class="chart-placeholder">
          <div class="placeholder-content">
            <div class="placeholder-icon">
              <ChartBarIcon class="w-8 h-8" />
            </div>
            <p class="placeholder-text">Chart visualization coming soon</p>
          </div>
        </div>
      </Card>

      <Card title="Performance Overview" :icon="ChartPieIcon">
        <div class="chart-placeholder">
          <div class="placeholder-content">
            <div class="placeholder-icon">
              <ChartPieIcon class="w-8 h-8" />
            </div>
            <p class="placeholder-text">Performance metrics loading...</p>
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
          class="position-card group relative"
          @mousemove="(e) => handleCardMouseMove(e, index)"
          @mouseleave="handleCardMouseLeave"
        >
          <!-- Animated background glow -->
          <div
            class="card-glow"
            :style="cardGlowStyles[index]"
          ></div>

          <div class="flex items-center justify-between relative z-10">
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

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import StatCard from './components/StatCard.vue'
import {
  ChartBarIcon,
  BriefcaseIcon,
  ArrowRightIcon,
  ChartPieIcon,
} from '@heroicons/vue/24/outline'

const portfolioStore = usePortfolioStore()
const loading = ref(true)

const portfolio = computed(() => portfolioStore.portfolio)
const hasPositions = computed(() => portfolio.value?.positions && portfolio.value.positions.length > 0)

// Mouse tracking for card glow effects
const cardGlowStyles = reactive<Record<number, { background: string }>>({})

const handleCardMouseMove = (event: MouseEvent, index: number) => {
  const card = event.currentTarget as HTMLElement
  const rect = card.getBoundingClientRect()
  const mouseX = ((event.clientX - rect.left) / rect.width) * 100
  const mouseY = ((event.clientY - rect.top) / rect.height) * 100

  cardGlowStyles[index] = {
    background: `radial-gradient(circle at ${mouseX}% ${mouseY}%, var(--accent-primary) 0%, transparent 35%)`
  }
}

const handleCardMouseLeave = () => {
  // Don't reset position - let opacity handle the fade out
}

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
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.chart-placeholder {
  height: 20rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: 0.75rem;
  border: 1px solid var(--border-default);
}

.placeholder-content {
  text-align: center;
}

.placeholder-icon {
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1rem;
  border-radius: 0.75rem;
  background: rgba(62, 207, 142, 0.08);
  border: 1px solid rgba(62, 207, 142, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
}

.placeholder-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.position-card {
  padding: 1.25rem;
  border-radius: 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  transition: all var(--transition-base);
  overflow: hidden;
}

.position-card:hover {
  border-color: var(--accent-primary);
  background: var(--bg-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.card-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 300ms ease;
  border-radius: 0.75rem;
  filter: blur(0.3rem);
  pointer-events: none;
}

.position-card:hover .card-glow {
  opacity: 1;
}

.position-icon {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.75rem;
  background: rgba(62, 207, 142, 0.1);
  border: 1px solid rgba(62, 207, 142, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
  transition: all var(--transition-base);
}

.position-card:hover .position-icon {
  background: rgba(62, 207, 142, 0.15);
  border-color: rgba(62, 207, 142, 0.4);
  transform: scale(1.05);
}
</style>
