<template>
  <div class="space-y-8">
    <!-- Recent Predictions -->
    <RecentPredictionsList
      :predictions="recentPredictions"
      @select="loadPrediction"
    />

    <!-- Controls -->
    <PredictionControls
      v-model:symbol="selectedSymbol"
      v-model:timeframe="selectedTimeframe"
      :symbols="symbols"
      :loading-symbols="loadingSymbols"
      :is-generating="loading"
      @generate="handleGeneratePrediction"
    />

    <!-- Loading State with Progress -->
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
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Prediction Results -->
    <PredictionResultsCard v-else-if="predictionData" :data="predictionData" />

    <!-- Empty State -->
    <EmptyState
      v-else
      :icon="SparklesIcon"
      title="No Predictions Yet"
      description="Select symbol and timeframe, then click Generate Prediction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PredictionData } from '@/types'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import { useSymbols } from '@/composables/useSymbols'
import { usePredictionPolling } from '@/composables/usePredictionPolling'
import Card from '@/components/ui/Card.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PredictionControls from '@/features/predictions/components/PredictionControls.vue'
import PredictionResultsCard from '@/features/predictions/components/PredictionResultsCard.vue'
import RecentPredictionsList from '@/features/predictions/components/RecentPredictionsList.vue'

// Selected parameters
const selectedSymbol = ref('ETH/USDT')
const selectedTimeframe = ref('1m')
const predictionData = ref<PredictionData | null>(null)
const recentPredictions = ref<any[]>([])

// Symbols
const { symbols, loading: loadingSymbols, fetch: fetchSymbols } = useSymbols('all')

// Prediction polling
const {
  loading,
  error,
  loadingStatus,
  loadingSteps,
  generatePrediction,
  clearError
} = usePredictionPolling({
  onComplete: async (data) => {
    predictionData.value = data
    await loadRecentPredictions()
  }
})

/**
 * Handle generate prediction button click
 */
async function handleGeneratePrediction() {
  clearError()
  await generatePrediction(selectedSymbol.value, selectedTimeframe.value, true)
}

/**
 * Load recent predictions from API
 */
async function loadRecentPredictions() {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  try {
    const response = await fetch(`${baseURL}/predictions/list`)
    if (response.ok) {
      const predictions = await response.json()
      recentPredictions.value = predictions.slice(0, 10)
    }
  } catch (err) {
    console.error('Failed to load recent predictions:', err)
  }
}

/**
 * Load a specific prediction by ID
 */
async function loadPrediction(predictionId: string) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  try {
    clearError()
    loading.value = true

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

// Load initial data
onMounted(async () => {
  await Promise.all([loadRecentPredictions(), fetchSymbols()])
})
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
</style>
