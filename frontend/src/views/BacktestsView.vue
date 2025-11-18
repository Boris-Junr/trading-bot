<template>
  <div>
    <!-- No Models Info -->
    <div
      v-if="!hasModels && !loadingModels"
      class="premium-alert mb-6"
    >
      <div class="alert-icon">
        <InformationCircleIcon class="w-6 h-6" />
      </div>
      <div class="alert-content">
        <h3 class="alert-title">No trained models found</h3>
        <p class="alert-text">
          No pre-trained models detected. When you run a backtest, a model will be automatically trained for your selected symbol and timeframe.
        </p>
        <div class="alert-meta">
          <ClockIcon class="w-4 h-4" />
          <span>Training typically takes 2-5 minutes</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-xl text-accent-danger text-sm">
      {{ error }}
    </div>

    <!-- Backtests List -->
    <div v-else>
      <Card v-if="sortedBacktests.length === 0">
        <div class="text-center py-12">
          <ChartPieIcon class="w-16 h-16 mx-auto text-text-muted mb-4" />
          <p class="text-text-primary font-medium mb-2">No Backtests Run Yet</p>
          <p class="text-text-secondary text-sm mb-6">Run your first backtest to test your trading strategies</p>
          <Button @click="showRunModal = true" variant="primary">
            Run Your First Backtest
          </Button>
          <p v-if="!hasModels" class="text-sm text-text-muted mt-4">
            A model will be automatically trained when you run your first backtest
          </p>
        </div>
      </Card>

      <div v-else>
        <!-- Header with New Backtest button -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-text-primary">Backtest Results</h2>
            <p class="text-sm text-text-secondary mt-1">View and analyze your strategy backtests</p>
          </div>
          <Button @click="showRunModal = true" variant="primary">
            New Backtest
          </Button>
        </div>

        <!-- Backtests Grid -->
        <div class="grid grid-cols-1 gap-6">
          <Card
            v-for="backtest in sortedBacktests"
            :key="backtest.end_date + backtest.strategy"
            :hoverable="backtest.status !== 'failed'"
            @click="backtest.status !== 'failed' ? goToDetail(backtest) : null"
            :class="{ 'cursor-not-allowed opacity-80': backtest.status === 'failed' }"
          >
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-lg font-semibold text-text-primary">{{ backtest.strategy }}</h3>
                <Badge variant="primary" size="sm">{{ backtest.symbol }}</Badge>
                <Badge v-if="backtest.status === 'failed'" variant="danger" size="sm">FAILED</Badge>
              </div>
              <p class="text-sm text-text-secondary mb-4">
                {{ formatDate(backtest.start_date) }} - {{ formatDate(backtest.end_date) }}
              </p>

              <!-- Failed Backtest Error -->
              <div v-if="backtest.status === 'failed'" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-lg">
                <div class="text-sm text-accent-danger">
                  ❌ {{ backtest.error || 'Backtest execution failed' }}
                </div>
              </div>

              <!-- Performance Metrics Grid (for successful backtests) -->
              <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div class="text-xs text-text-muted mb-1">Total Return</div>
                  <div
                    class="text-lg font-semibold font-mono"
                    :class="backtest.performance.total_return >= 0 ? 'text-accent-success' : 'text-accent-danger'"
                  >
                    {{ backtest.performance.total_return >= 0 ? '+' : '' }}{{ (backtest.performance.total_return * 100).toFixed(2) }}%
                  </div>
                </div>
                <div>
                  <div class="text-xs text-text-muted mb-1">Total P&L</div>
                  <div
                    class="text-lg font-semibold font-mono"
                    :class="backtest.performance.total_pnl >= 0 ? 'text-accent-success' : 'text-accent-danger'"
                  >
                    {{ backtest.performance.total_pnl >= 0 ? '+' : '' }}${{ formatNumber(backtest.performance.total_pnl) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-text-muted mb-1">Sharpe Ratio</div>
                  <div class="text-lg font-semibold font-mono text-text-primary">
                    {{ backtest.performance.sharpe_ratio.toFixed(2) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-text-muted mb-1">Win Rate</div>
                  <div class="text-lg font-semibold font-mono text-text-primary">
                    {{ (backtest.trading.win_rate * 100).toFixed(1) }}%
                  </div>
                </div>
              </div>
            </div>
            <div class="ml-4">
              <ChevronRightIcon class="w-6 h-6 text-text-muted" />
            </div>
          </div>
        </Card>
        </div>
      </div>
    </div>

    <!-- Run Backtest Modal -->
    <Modal
      v-model="showRunModal"
      title="Run New Backtest"
      subtitle="Test your trading strategy against historical market data"
      size="lg"
      :close-on-outside-click="!running"
    >
      <div class="space-y-5">
        <Select
          v-model="newBacktest.strategy"
          label="Strategy"
          :disabled="loadingStrategies"
          :hint="loadingStrategies ? 'Loading strategies...' : 'Select a trading strategy to backtest'"
        >
          <option
            v-for="strategy in availableStrategies"
            :key="strategy.value"
            :value="strategy.value"
          >
            {{ strategy.label }}
          </option>
        </Select>

        <Select
          v-model="newBacktest.symbol"
          label="Trading Symbol"
          :disabled="loadingSymbols"
          :hint="hasModels && modelsSymbols.includes(newBacktest.symbol) ? `✓ Model available for ${newBacktest.symbol}` : 'Model will be trained automatically (2-5 minutes)'"
        >
          <option v-for="symbol in availableSymbols" :key="symbol" :value="symbol">
            {{ symbol }}
          </option>
        </Select>

        <div class="grid grid-cols-2 gap-4">
          <Input
            v-model="newBacktest.start_date"
            type="date"
            label="Start Date"
          />
          <Input
            v-model="newBacktest.end_date"
            type="date"
            label="End Date"
          />
        </div>

        <Input
          v-model="newBacktest.initial_capital"
          type="number"
          label="Initial Capital ($)"
          placeholder="10000"
        />
      </div>

      <!-- Progress indicator -->
      <div v-if="running" class="mt-6 space-y-4">
        <!-- Status message -->
      </div>

      <template #footer>
        <Button @click="showRunModal = false" :disabled="running" variant="secondary">
          Cancel
        </Button>
        <Button @click="runBacktest" :disabled="running" variant="primary" class="flex-1">
          {{ running ? 'Running...' : 'Run Backtest' }}
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBacktestStore } from '../stores/backtest'
import { storeToRefs } from 'pinia'
import type { BacktestResult, ModelInfo } from '../types'
import api from '../services/api'
import { InformationCircleIcon, ClockIcon, ChartPieIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
import Card from '@/shared/components/ui/Card.vue'
import Button from '@/shared/components/ui/Button.vue'
import Badge from '@/shared/components/ui/Badge.vue'
import Modal from '@/shared/components/ui/Modal.vue'
import Input from '@/shared/components/ui/Input.vue'
import Select from '@/shared/components/ui/Select.vue'

const router = useRouter()
const backtestStore = useBacktestStore()
const { backtests, loading, error, sortedBacktests } = storeToRefs(backtestStore)

const showRunModal = ref(false)
const running = ref(false)
const availableModels = ref<ModelInfo[]>([])
const loadingModels = ref(false)
const availableSymbols = ref<string[]>([])
const loadingSymbols = ref(false)
const availableStrategies = ref<Array<{value: string, label: string, description: string, requires_model: boolean}>>([
  { value: 'MLPredictive', label: 'ML Predictive Strategy', description: 'Uses ML predictions', requires_model: true },
  { value: 'BreakoutScalping', label: 'Breakout Scalping Strategy', description: 'Range breakout strategy', requires_model: false }
])
const loadingStrategies = ref(false)

const newBacktest = ref({
  strategy: 'MLPredictive',
  symbol: '',
  start_date: '',
  end_date: '',
  initial_capital: 10000,
})

// Get symbols with trained models
const modelsSymbols = computed(() => {
  const symbols = new Set(availableModels.value.map(m => m.symbol))
  return Array.from(symbols)
})

const hasModels = computed(() => availableModels.value.length > 0)

onMounted(async () => {
  // Set default dates (last 30 days)
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  newBacktest.value.end_date = end.toISOString().split('T')[0]
  newBacktest.value.start_date = start.toISOString().split('T')[0]

  // Fetch available symbols, models, and strategies in parallel
  await Promise.all([
    fetchSymbols(),
    fetchModels(),
    fetchStrategies()
  ])

  // Set default symbol to first available symbol
  if (availableSymbols.value.length > 0) {
    newBacktest.value.symbol = availableSymbols.value[0]
  }

  // Set default strategy to first available strategy
  if (availableStrategies.value.length > 0) {
    newBacktest.value.strategy = availableStrategies.value[0].value
  }

  await backtestStore.fetchBacktests()
})

async function fetchSymbols() {
  loadingSymbols.value = true
  try {
    // Fetch all allowed symbols from global trading pairs configuration
    availableSymbols.value = await api.getSymbols('all')
  } catch (e) {
    console.error('Failed to fetch symbols:', e)
    // Fallback to high-volatility pairs from config
    availableSymbols.value = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDT', 'SOL/USDT', 'EUR/USD', 'NAS100']
  } finally {
    loadingSymbols.value = false
  }
}

async function fetchModels() {
  loadingModels.value = true
  try {
    availableModels.value = await api.getModels()
  } catch (e) {
    console.error('Failed to fetch models:', e)
  } finally {
    loadingModels.value = false
  }
}

async function fetchStrategies() {
  loadingStrategies.value = true
  try {
    const response = await fetch('http://localhost:8000/api/strategies/available')
    if (response.ok) {
      availableStrategies.value = await response.json()
    } else {
      throw new Error(`API returned ${response.status}`)
    }
  } catch (e) {
    console.error('Failed to fetch strategies:', e)
    // Fallback to default list if API fails
    availableStrategies.value = [
      { value: 'MLPredictive', label: 'ML Predictive Strategy', description: 'Uses ML predictions', requires_model: true },
      { value: 'BreakoutScalping', label: 'Breakout Scalping Strategy', description: 'Range breakout strategy', requires_model: false }
    ]
  } finally {
    loadingStrategies.value = false
  }
}

async function runBacktest() {
  // Validate inputs
  if (!newBacktest.value.symbol) {
    alert('Please select a symbol')
    return
  }

  if (!newBacktest.value.start_date || !newBacktest.value.end_date) {
    alert('Please select start and end dates')
    return
  }

  running.value = true

  // Use new background execution endpoint
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  try {
    const response = await fetch(`${baseURL}/backtests/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy: newBacktest.value.strategy,
        symbol: newBacktest.value.symbol,
        start_date: newBacktest.value.start_date,
        end_date: newBacktest.value.end_date,
        initial_capital: newBacktest.value.initial_capital,
        params: {
          timeframe: '1m',
          min_predicted_return: 0.002,
          confidence_threshold: 0.6,
          prediction_window: 60,
          risk_per_trade: 0.02
        }
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to start backtest')
    }

    // Close modal immediately - backtest runs in background
    running.value = false
    showRunModal.value = false

    // Refresh the backtests list after a short delay
    setTimeout(() => backtestStore.fetchBacktests(), 1000)

  } catch (error: any) {
    alert(`Failed to run backtest: ${error.message}`)
    running.value = false
  }
}

function goToDetail(backtest: BacktestResult) {
  // Use the actual ID from the backend
  const id = backtest.id || btoa(`${backtest.strategy}-${backtest.end_date}`)
  router.push(`/backtests/${id}`)
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
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>

<style scoped>
.premium-alert {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(62, 207, 142, 0.05);
  border: 1px solid rgba(62, 207, 142, 0.15);
  border-radius: 0.75rem;
  backdrop-filter: blur(10px);
}

.alert-icon {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(62, 207, 142, 0.12);
  border: 1px solid rgba(62, 207, 142, 0.25);
  border-radius: 0.625rem;
  color: var(--accent-primary);
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alert-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.alert-text {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0;
}

.alert-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  color: var(--accent-primary);
  font-weight: 500;
}

.alert-meta svg {
  flex-shrink: 0;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid var(--border-default);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-sm {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid var(--border-default);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
