<template>
  <div class="space-y-8">
    <!-- Recent Predictions (Collapsable) -->
    <div v-if="recentPredictions.length > 0" class="collapsable-section">
      <div class="collapsable-header" @click="isRecentCollapsed = !isRecentCollapsed">
        <div class="collapsable-title">
          <ClockIcon class="header-icon" />
          <h3>Recent predictions</h3>
          <span class="prediction-count">{{ recentPredictions.length }}</span>
        </div>
        <svg
          class="chevron-icon"
          :class="{ 'chevron-expanded': !isRecentCollapsed }"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
      </div>
      <transition name="collapse">
        <div v-show="!isRecentCollapsed" class="collapsable-content">
          <div class="prediction-list">
        <div
          v-for="pred in recentPredictions"
          :key="pred.id"
          class="prediction-item"
          @click="loadPrediction(pred.id)"
        >
          <!-- Status Indicator -->
          <div class="prediction-status-indicator" :class="{
            'status-completed': pred.status === 'completed',
            'status-running': pred.status === 'running',
            'status-queued': pred.status === 'queued'
          }"></div>

          <!-- Main Content -->
          <div class="prediction-content">
            <div class="prediction-header">
              <div class="prediction-title">
                <span class="prediction-symbol">{{ pred.symbol }}</span>
                <span class="prediction-timeframe">{{ pred.timeframe }}</span>
              </div>
              <div class="prediction-status" :class="{
                'status-badge-completed': pred.status === 'completed',
                'status-badge-running': pred.status === 'running',
                'status-badge-queued': pred.status === 'queued'
              }">
                <svg v-if="pred.status === 'completed'" class="status-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <svg v-else-if="pred.status === 'running'" class="status-icon status-icon-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="status-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                </svg>
                <span class="status-text">{{ pred.status }}</span>
              </div>
            </div>

            <!-- Metadata -->
            <div class="prediction-meta">
              <div class="meta-item">
                <svg class="meta-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                </svg>
                <span>{{ formatDate(pred.created_at) }}</span>
              </div>
              <div v-if="pred.current_price" class="meta-item">
                <svg class="meta-icon" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"/>
                </svg>
                <span>${{ pred.current_price.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- Chevron -->
          <div class="prediction-chevron">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>
        </div>
      </transition>
    </div>

    <!-- Controls -->
    <Card title="Prediction Settings" :icon="CogIcon">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Select
          v-model="selectedSymbol"
          label="Symbol"
          :disabled="loadingSymbols"
          :key="`symbols-${availableSymbols.length}`"
        >
          <option v-for="symbol in availableSymbols" :key="symbol" :value="symbol">
            {{ symbol }}
          </option>
        </Select>

        <Select v-model="selectedTimeframe" label="Timeframe">
          <option value="1m">1 Minute</option>
          <option value="5m">5 Minutes</option>
          <option value="15m">15 Minutes</option>
          <option value="1h">1 Hour</option>
        </Select>

        <div class="flex items-end">
          <Button @click="fetchPredictions" :disabled="loading" variant="primary" class="w-full">
            {{ loading ? 'Loading...' : 'Generate Prediction' }}
          </Button>
        </div>
      </div>
    </Card>

    <!-- Loading State -->
    <Card v-if="loading">
      <div class="flex flex-col items-center py-12 space-y-6">
        <!-- Spinner -->
        <div class="spinner"></div>

        <!-- Status Messages -->
        <div class="text-center space-y-2">
          <div class="text-lg font-semibold text-text-primary">{{ loadingStatus.title }}</div>
          <div class="text-sm text-text-secondary">{{ loadingStatus.message }}</div>

          <!-- Progress Steps -->
          <div class="mt-6 space-y-2">
            <div v-for="step in loadingSteps" :key="step.name" class="flex items-center justify-center space-x-2 text-sm">
              <div class="flex items-center space-x-2">
                <!-- Completed -->
                <svg v-if="step.status === 'completed'" class="w-5 h-5 text-accent-success" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <!-- In Progress -->
                <div v-else-if="step.status === 'in-progress'" class="spinner-sm"></div>
                <!-- Pending -->
                <div v-else class="w-5 h-5 border-2 border-border-default rounded-full"></div>

                <span :class="{
                  'text-accent-success font-medium': step.status === 'completed',
                  'text-accent-primary font-medium': step.status === 'in-progress',
                  'text-text-muted': step.status === 'pending'
                }">
                  {{ step.label }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-xl text-accent-danger text-sm">
      {{ error }}
    </div>

    <!-- Predictions Content -->
    <template v-else-if="predictionData">
      <!-- Current Price -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          label="Current Price"
          :value="`$${predictionData.current_price.toFixed(2)}`"
          icon="💰"
          variant="primary"
        />

        <StatCard
          label="Predicted Direction"
          :value="finalPrediction.change >= 0 ? 'BULLISH' : 'BEARISH'"
          :variant="finalPrediction.change >= 0 ? 'success' : 'danger'"
          :trend="finalPrediction.change >= 0 ? 'up' : 'down'"
        />

        <StatCard
          label="Expected Change"
          :value="`${finalPrediction.changePercent >= 0 ? '+' : ''}${finalPrediction.changePercent.toFixed(2)}%`"
          :change="`Target: $${finalPrediction.price.toFixed(2)}`"
          :variant="finalPrediction.changePercent >= 0 ? 'success' : 'danger'"
        />
      </div>

      <!-- Prediction Chart -->
      <Card title="Price Prediction" :icon="ChartBarIcon">
        <div class="h-96">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </Card>

      <!-- Predictions Table -->
      <Card title="Step-by-Step Predictions" :icon="TableCellsIcon">
        <p class="text-sm text-text-secondary mb-4">Showing first 20 predictions</p>
        <Table>
          <template #header>
            <TableHeader>Time Ahead</TableHeader>
            <TableHeader align="right">Open</TableHeader>
            <TableHeader align="right">High</TableHeader>
            <TableHeader align="right">Low</TableHeader>
            <TableHeader align="right">Close</TableHeader>
            <TableHeader align="right">Change</TableHeader>
            <TableHeader align="right">Confidence</TableHeader>
          </template>

          <TableRow v-for="prediction in displayedPredictions" :key="prediction.step">
            <TableCell>+{{ prediction.minutes_ahead }} min</TableCell>
            <TableCell align="right" mono>${{ prediction.predicted_open.toFixed(2) }}</TableCell>
            <TableCell align="right" mono>${{ prediction.predicted_high.toFixed(2) }}</TableCell>
            <TableCell align="right" mono>${{ prediction.predicted_low.toFixed(2) }}</TableCell>
            <TableCell align="right" mono>${{ prediction.predicted_close.toFixed(2) }}</TableCell>
            <TableCell align="right" mono :class="prediction.predicted_return >= 0 ? 'text-accent-success' : 'text-accent-danger'">
              {{ prediction.predicted_return >= 0 ? '+' : '' }}{{ (prediction.predicted_return * 100).toFixed(3) }}%
            </TableCell>
            <TableCell align="right" mono>{{ (prediction.confidence * 100).toFixed(1) }}%</TableCell>
          </TableRow>
        </Table>
      </Card>
    </template>

    <!-- No Data State -->
    <Card v-else>
      <div class="text-center py-12">
        <SparklesIcon class="w-16 h-16 mx-auto text-text-muted mb-4" />
        <p class="text-text-primary font-medium mb-2">No Predictions Yet</p>
        <p class="text-text-secondary text-sm">Select symbol and timeframe, then click "Generate Prediction"</p>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { PredictionData } from '../types'
import api from '../services/api'
import { useChart } from '../composables/useChart'
import { ChartBarIcon, SparklesIcon, CogIcon, TableCellsIcon, ClockIcon } from '@heroicons/vue/24/outline'
import Card from '@/shared/components/ui/Card.vue'
import Button from '@/shared/components/ui/Button.vue'
import Select from '@/shared/components/ui/Select.vue'
import StatCard from '@/features/dashboard/components/StatCard.vue'
import Table from '@/shared/components/ui/Table.vue'
import TableHeader from '@/shared/components/ui/TableHeader.vue'
import TableRow from '@/shared/components/ui/TableRow.vue'
import TableCell from '@/shared/components/ui/TableCell.vue'

const selectedSymbol = ref('ETH/USDT')
const selectedTimeframe = ref('1m')
const predictionData = ref<PredictionData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const chartCanvas = ref<HTMLCanvasElement | null>(null)
const recentPredictions = ref<any[]>([])
const isRecentCollapsed = ref(true) // Collapsed by default
const availableSymbols = ref<string[]>([])
const loadingSymbols = ref(false)

const loadingStatus = ref({
  title: 'Loading...',
  message: ''
})

const loadingSteps = ref([
  { name: 'check', label: 'Checking for existing model', status: 'pending' },
  { name: 'fetch', label: 'Fetching market data', status: 'pending' },
  { name: 'train', label: 'Processing model', status: 'pending' },
  { name: 'predict', label: 'Generating predictions', status: 'pending' }
])

const { createChart } = useChart(chartCanvas)

watch(predictionData, async (newData) => {
  if (newData) {
    await nextTick()
    updateChart(newData)
  }
})

function updateLoadingStep(stepName: string, status: 'pending' | 'in-progress' | 'completed') {
  const step = loadingSteps.value.find(s => s.name === stepName)
  if (step) {
    step.status = status
  }
}

function resetLoadingSteps() {
  loadingSteps.value.forEach(step => step.status = 'pending')
}

async function fetchPredictions() {
  loading.value = true
  error.value = null
  resetLoadingSteps()

  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  try {
    // Step 1: Start the background prediction
    loadingStatus.value = {
      title: 'Initializing',
      message: 'Starting prediction task...'
    }
    updateLoadingStep('check', 'in-progress')

    const startResponse = await fetch(
      `${baseURL}/predictions/generate?symbol=${selectedSymbol.value.replace('/', '_')}&timeframe=${selectedTimeframe.value}&auto_train=true`,
      { method: 'POST' }
    )

    if (!startResponse.ok) {
      throw new Error(`Failed to start prediction: ${startResponse.statusText}`)
    }

    const startData = await startResponse.json()
    const predictionId = startData.prediction_id

    if (startData.status === 'queued') {
      loadingStatus.value = {
        title: 'Queued',
        message: `Task queued at position ${startData.queue_position}. Waiting for resources...`
      }
    } else {
      loadingStatus.value = {
        title: 'Running',
        message: 'Prediction task is running in background...'
      }
    }

    updateLoadingStep('check', 'completed')
    updateLoadingStep('fetch', 'in-progress')

    // Step 2: Poll for completion
    const pollInterval = 2000 // Poll every 2 seconds
    const maxAttempts = 150 // 5 minutes max
    let attempts = 0

    const pollResult = async (): Promise<void> => {
      attempts++

      if (attempts > maxAttempts) {
        throw new Error('Prediction timed out after 5 minutes')
      }

      const statusResponse = await fetch(`${baseURL}/predictions/${predictionId}`)

      if (!statusResponse.ok) {
        throw new Error(`Failed to check prediction status: ${statusResponse.statusText}`)
      }

      const statusData = await statusResponse.json()

      if (statusData.status === 'queued') {
        loadingStatus.value = {
          title: 'Queued',
          message: 'Waiting for resources...'
        }
        await new Promise(resolve => setTimeout(resolve, pollInterval))
        return pollResult()
      } else if (statusData.status === 'running') {
        // Update loading steps based on attempts
        if (attempts < 5) {
          updateLoadingStep('fetch', 'in-progress')
          loadingStatus.value = {
            title: 'Fetching data',
            message: 'Loading market data...'
          }
        } else if (attempts < 15) {
          updateLoadingStep('fetch', 'completed')
          updateLoadingStep('train', 'in-progress')
          loadingStatus.value = {
            title: 'Checking model',
            message: 'Preparing model...'
          }
        } else {
          updateLoadingStep('train', 'completed')
          updateLoadingStep('predict', 'in-progress')
          loadingStatus.value = {
            title: 'Generating predictions',
            message: 'Running ML model...'
          }
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval))
        return pollResult()
      } else if (statusData.status === 'completed' && statusData.result) {
        // Success!
        updateLoadingStep('fetch', 'completed')
        updateLoadingStep('train', 'completed')
        updateLoadingStep('predict', 'completed')

        predictionData.value = statusData.result
        loading.value = false

        // Reload recent predictions list
        await loadRecentPredictions()
      } else {
        throw new Error('Prediction failed or returned invalid data')
      }
    }

    await pollResult()

  } catch (err: any) {
    error.value = err.message || 'Failed to fetch predictions'
    loading.value = false
  }
}

function updateChart(data: PredictionData) {
  if (!chartCanvas.value) return

  const allPredictions = data.predictions
  let sampleRate = 1
  if (allPredictions.length > 200) sampleRate = 2
  else if (allPredictions.length > 150) sampleRate = 3

  const predictions = allPredictions.filter((_, i) => i % sampleRate === 0)

  const candlestickData = predictions.map(pred => ({
    x: new Date(pred.timestamp).getTime(),
    o: pred.predicted_open,
    h: pred.predicted_high,
    l: pred.predicted_low,
    c: pred.predicted_close,
  }))

  const allHighs = allPredictions.map(p => p.predicted_high)
  const allLows = allPredictions.map(p => p.predicted_low)
  const absoluteHigh = Math.max(...allHighs)
  const absoluteLow = Math.min(...allLows)
  const priceRange = absoluteHigh - absoluteLow
  const padding = priceRange * 0.15

  const roundingFactor = priceRange > 100 ? 10 : priceRange > 10 ? 1 : 0.5
  const yMin = Math.floor((absoluteLow - padding) / roundingFactor) * roundingFactor
  const yMax = Math.ceil((absoluteHigh + padding) / roundingFactor) * roundingFactor

  createChart({
    type: 'candlestick',
    data: {
      datasets: [
        {
          label: 'Predicted Price',
          data: candlestickData,
          type: 'candlestick',
          color: {
            up: 'rgb(62, 207, 142)',
            down: 'rgb(192, 57, 43)',
            unchanged: 'rgb(156, 163, 175)',
          },
          borderColor: {
            up: 'rgb(62, 207, 142)',
            down: 'rgb(192, 57, 43)',
            unchanged: 'rgb(156, 163, 175)',
          },
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top' },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              const point = context.raw as any
              return [
                `Open: $${point.o.toFixed(2)}`,
                `High: $${point.h.toFixed(2)}`,
                `Low: $${point.l.toFixed(2)}`,
                `Close: $${point.c.toFixed(2)}`,
              ]
            },
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'minute',
            displayFormats: { minute: 'HH:mm', hour: 'HH:mm' },
          },
          title: { display: true, text: 'Time' },
        },
        y: {
          min: yMin,
          max: yMax,
          title: { display: true, text: 'Predicted Price (USD)' },
          ticks: { callback: (value) => `$${value}` },
        },
      },
      interaction: { mode: 'index', intersect: false },
    },
  } as any)
}

const displayedPredictions = computed(() => {
  if (!predictionData.value) return []
  return predictionData.value.predictions.slice(0, 20)
})

const finalPrediction = computed(() => {
  if (!predictionData.value || predictionData.value.predictions.length === 0) {
    return { price: 0, change: 0, changePercent: 0 }
  }
  const lastPrediction = predictionData.value.predictions[predictionData.value.predictions.length - 1]
  const change = lastPrediction.predicted_close - predictionData.value.current_price
  const changePercent = (change / predictionData.value.current_price) * 100
  return { price: lastPrediction.predicted_close, change, changePercent }
})

// Fetch available symbols
async function fetchSymbols() {
  loadingSymbols.value = true
  try {
    availableSymbols.value = await api.getSymbols('all')
  } catch (e) {
    console.error('Failed to fetch symbols:', e)
    // Fallback to common symbols if API fails
    availableSymbols.value = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT', 'EUR/USD', 'GBP/USD', 'NAS100']
  } finally {
    loadingSymbols.value = false
  }
}

// Load recent predictions on mount
onMounted(async () => {
  await Promise.all([loadRecentPredictions(), fetchSymbols()])
})

async function loadRecentPredictions() {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  try {
    const response = await fetch(`${baseURL}/predictions/list`)
    if (response.ok) {
      const predictions = await response.json()
      recentPredictions.value = predictions.slice(0, 10) // Show last 10
    }
  } catch (err) {
    console.error('Failed to load recent predictions:', err)
  }
}

async function loadPrediction(predictionId: string) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  try {
    loading.value = true
    error.value = null

    const response = await fetch(`${baseURL}/predictions/${predictionId}`)

    if (!response.ok) {
      throw new Error('Failed to load prediction')
    }

    const data = await response.json()

    if (data.status === 'completed' && data.result) {
      predictionData.value = data.result
      // Update symbols/timeframe to match loaded prediction
      selectedSymbol.value = data.symbol.replace('_', '/')
      selectedTimeframe.value = data.timeframe
    } else if (data.status === 'running' || data.status === 'queued') {
      error.value = `Prediction is still ${data.status}. Please wait...`
    } else {
      error.value = 'Prediction has no results yet'
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load prediction'
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString()
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

/* Recent Predictions List Styles */
.prediction-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 500px;
  overflow-y: auto;
}

.prediction-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  border: 1px solid var(--glass-border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.prediction-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(62, 207, 142, 0.3);
  transform: translateX(4px);
}

/* Status Indicator (left border) */
.prediction-status-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 0.5rem 0 0 0.5rem;
}

.status-completed {
  background: var(--accent-success);
}

.status-running {
  background: var(--accent-warning);
}

.status-queued {
  background: var(--text-muted);
}

/* Content Area */
.prediction-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-left: 0.5rem;
}

.prediction-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.prediction-title {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.prediction-symbol {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.prediction-timeframe {
  font-size: 0.75rem;
  color: var(--text-muted);
  padding: 0.125rem 0.375rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.25rem;
}

/* Status Badge */
.prediction-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge-completed {
  background: rgba(62, 207, 142, 0.15);
  color: var(--accent-success);
}

.status-badge-running {
  background: rgba(255, 193, 7, 0.15);
  color: var(--accent-warning);
}

.status-badge-queued {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}

.status-icon {
  width: 1rem;
  height: 1rem;
}

.status-icon-spin {
  animation: spin 1s linear infinite;
}

.status-text {
  line-height: 1;
}

/* Metadata */
.prediction-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.meta-icon {
  width: 0.875rem;
  height: 0.875rem;
  opacity: 0.7;
}

/* Chevron */
.prediction-chevron {
  display: flex;
  align-items: center;
  color: var(--text-muted);
  opacity: 0.5;
  transition: all 0.2s ease;
}

.prediction-chevron svg {
  width: 1.25rem;
  height: 1.25rem;
}

.prediction-item:hover .prediction-chevron {
  opacity: 1;
  color: var(--accent-success);
  transform: translateX(4px);
}

/* Collapsable Section Styles */
.collapsable-section {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.collapsable-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.collapsable-header:hover {
  background: rgba(62, 207, 142, 0.05);
}

.collapsable-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--accent-success);
}

.collapsable-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.prediction-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.75rem;
  padding: 0 0.5rem;
  background: rgba(62, 207, 142, 0.15);
  color: var(--accent-success);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
}

.chevron-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}

.chevron-expanded {
  transform: rotate(180deg);
}

.collapsable-content {
  padding: 0 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid var(--glass-border);
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 600px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
