<template>
  <div>
    <!-- Loading State -->
    <LoadingSpinner v-if="loading" />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Predictions List -->
    <div v-else>
      <EmptyState
        v-if="sortedPredictions.length === 0"
        :icon="SparklesIcon"
        title="No Predictions Yet"
        description="Generate your first prediction to see market forecasts"
        action-text="Generate Your First Prediction"
        @action="showGenerateModal = true"
      >
        <template #action>
          <Button @click="showGenerateModal = true" variant="primary">
            Generate Your First Prediction
          </Button>
        </template>
      </EmptyState>

      <div v-else>
        <!-- Header with New Prediction button -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-text-primary">Predictions</h2>
            <p class="text-sm text-text-secondary mt-1">View market price predictions and forecasts</p>
          </div>
          <Button @click="showGenerateModal = true" variant="primary">
            New Prediction
          </Button>
        </div>

        <!-- Predictions Grid -->
        <div class="grid grid-cols-1 gap-6">
          <Card
            v-for="prediction in sortedPredictions"
            :key="prediction.id"
            :hoverable="prediction.status === 'completed'"
            @click="prediction.status === 'completed' ? viewPrediction(prediction) : null"
            :class="{ 'cursor-not-allowed opacity-80': prediction.status !== 'completed' }"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="text-lg font-semibold text-text-primary">{{ prediction.symbol }}</h3>
                  <Badge variant="info" size="sm">{{ prediction.timeframe }}</Badge>
                  <Badge
                    :variant="getStatusVariant(prediction.status)"
                    size="sm"
                  >
                    {{ prediction.status.toUpperCase() }}
                  </Badge>
                </div>
                <p class="text-sm text-text-secondary mb-4">
                  {{ formatDate(prediction.created_at) }}
                </p>

                <!-- Failed Prediction Error -->
                <div v-if="prediction.status === 'failed'" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-lg">
                  <div class="text-sm text-accent-danger">
                    {{ prediction.error || 'Prediction generation failed' }}
                  </div>
                </div>

                <!-- Running/Queued Status -->
                <div v-else-if="prediction.status === 'running' || prediction.status === 'queued'" class="p-4 bg-accent-warning/10 border border-accent-warning/20 rounded-lg">
                  <div class="text-sm text-accent-warning flex items-center gap-2">
                    <div class="spinner-sm"></div>
                    <span>{{ prediction.status === 'running' ? 'Generating prediction...' : 'Waiting in queue...' }}</span>
                  </div>
                </div>

                <!-- Completed Prediction Info -->
                <div v-else-if="prediction.status === 'completed'">
                  <!-- Prediction Range -->
                  <div v-if="prediction.prediction_start && prediction.prediction_end" class="mb-3 p-2 bg-accent-primary/10 border border-accent-primary/20 rounded">
                    <div class="text-xs text-text-muted mb-1">Prediction Range</div>
                    <div class="text-sm text-text-secondary">
                      {{ formatDate(prediction.prediction_start) }} → {{ formatDate(prediction.prediction_end) }}
                    </div>
                  </div>

                  <!-- Stats Grid -->
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div class="text-xs text-text-muted mb-1">Current Price</div>
                      <div class="text-lg font-semibold font-mono text-text-primary">
                        {{ prediction.current_price ? `$${formatNumber(prediction.current_price)}` : 'N/A' }}
                      </div>
                    </div>
                    <div>
                      <div class="text-xs text-text-muted mb-1">Direction</div>
                      <div class="text-lg font-semibold flex items-center gap-2">
                        <span v-if="prediction.direction === 'bullish'" class="text-accent-success">↗ Bullish</span>
                        <span v-else-if="prediction.direction === 'bearish'" class="text-accent-danger">↘ Bearish</span>
                        <span v-else class="text-text-muted">→ Neutral</span>
                      </div>
                    </div>
                    <div>
                      <div class="text-xs text-text-muted mb-1">Max Expected Change</div>
                      <div
                        class="text-lg font-semibold font-mono"
                        :class="(prediction.max_expected_change || 0) >= 0 ? 'text-accent-success' : 'text-accent-danger'"
                      >
                        {{ (prediction.max_expected_change || 0) >= 0 ? '+' : '' }}{{ ((prediction.max_expected_change || 0) * 100).toFixed(2) }}%
                      </div>
                    </div>
                    <div>
                      <div class="text-xs text-text-muted mb-1">Created</div>
                      <div class="text-sm text-text-secondary">
                        {{ formatDate(prediction.created_at) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="prediction.status === 'completed'" class="ml-4">
                <ChevronRightIcon class="w-6 h-6 text-text-muted" />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <!-- Generate Prediction Modal -->
    <Modal
      v-model="showGenerateModal"
      title="Generate New Prediction"
      subtitle="Get AI-powered price predictions for any trading pair"
      size="lg"
      :close-on-outside-click="!generating"
    >
      <div class="space-y-5">
        <Select
          v-model="newPrediction.symbol"
          label="Trading Symbol"
          :disabled="loadingSymbols"
          :hint="loadingSymbols ? 'Loading symbols...' : 'Select a trading pair to predict'"
        >
          <option v-for="symbol in availableSymbols" :key="symbol" :value="symbol">
            {{ symbol }}
          </option>
        </Select>

        <Select
          v-model="newPrediction.timeframe"
          label="Timeframe"
          hint="Select the prediction timeframe"
        >
          <option value="1m">1 Minute</option>
          <option value="5m">5 Minutes</option>
          <option value="15m">15 Minutes</option>
          <option value="1h">1 Hour</option>
        </Select>
      </div>

      <!-- Progress indicator -->
      <div v-if="generating" class="mt-6 space-y-4">
        <!-- Status message -->
      </div>

      <template #footer>
        <Button @click="showGenerateModal = false" :disabled="generating" variant="secondary">
          Cancel
        </Button>
        <Button @click="generatePrediction" :disabled="generating" variant="primary" class="flex-1">
          {{ generating ? 'Generating...' : 'Generate Prediction' }}
        </Button>
      </template>
    </Modal>

    <!-- View Prediction Modal -->
    <Modal
      v-model="showViewModal"
      title="Prediction Details"
      :subtitle="`${viewingPrediction?.symbol || ''} - ${viewingPrediction?.timeframe || ''}`"
      size="xl"
    >
      <PredictionResultsCard v-if="predictionData" :data="predictionData" />
      <LoadingSpinner v-else-if="loadingPredictionData" />
      <ErrorAlert v-else-if="viewError" :message="viewError" />

      <template #footer>
        <Button @click="showViewModal = false" variant="secondary" class="flex-1">
          Close
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import type { PredictionListItem, PredictionData } from '@/types'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { SparklesIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
import { useFormatters } from '@/composables/useFormatters'
import { useSymbols } from '@/composables/useSymbols'
import { useTaskManagerStore } from '@/stores/taskManager'
import { useAuth } from '@/composables/useAuth'
import api from '@/services/api'
import { supabase } from '@/lib/supabase'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Modal from '@/components/ui/Modal.vue'
import Select from '@/components/ui/Select.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PredictionResultsCard from '@/features/predictions/components/PredictionResultsCard.vue'

// Formatters
const { formatDate, formatNumber } = useFormatters()

// Auth
const { user } = useAuth()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const predictions = ref<PredictionListItem[]>([])
const showGenerateModal = ref(false)
const showViewModal = ref(false)
const generating = ref(false)
const viewingPrediction = ref<PredictionListItem | null>(null)
const predictionData = ref<PredictionData | null>(null)
const loadingPredictionData = ref(false)
const viewError = ref<string | null>(null)

// Real-time subscription
let realtimeChannel: RealtimeChannel | null = null

// Symbols
const { symbols: availableSymbols, loading: loadingSymbols, fetch: fetchSymbols } = useSymbols('all')

// Task manager for watching prediction completions
const taskManager = useTaskManagerStore()

// New prediction form
const newPrediction = ref({
  symbol: '',
  timeframe: '1m'
})

// Computed
const sortedPredictions = computed(() => {
  return [...predictions.value].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

/**
 * Load predictions directly from Supabase (much faster than going through backend API)
 */
async function loadPredictions() {
  loading.value = true
  error.value = null

  try {
    if (!user.value) {
      console.log('No authenticated user, skipping predictions fetch')
      predictions.value = []
      return
    }

    // Fetch directly from Supabase including result for summary data
    const { data, error: fetchError } = await supabase
      .from('predictions')
      .select('id, symbol, timeframe, created_at, status, result')
      .eq('user_id', user.value.id)
      .order('created_at', { ascending: false })

    if (fetchError) throw fetchError

    predictions.value = (data || []).map(pred => {
      const result = pred.result || {}
      const preds = result.predictions || []

      // Calculate direction and max expected change from predictions
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral'
      let maxExpectedChange = 0
      let predictionStart = null
      let predictionEnd = null

      if (preds.length > 0) {
        // Get first prediction's direction (short-term)
        const firstReturn = preds[0]?.predicted_return || 0
        direction = firstReturn > 0.001 ? 'bullish' : firstReturn < -0.001 ? 'bearish' : 'neutral'

        // Find max absolute return across all predictions
        const returns = preds.map((p: any) => p.predicted_return || 0)
        const maxReturn = Math.max(...returns)
        const minReturn = Math.min(...returns)
        maxExpectedChange = Math.abs(maxReturn) > Math.abs(minReturn) ? maxReturn : minReturn

        // Get prediction range timestamps
        predictionStart = preds[0]?.timestamp || null
        predictionEnd = preds[preds.length - 1]?.timestamp || null
      }

      return {
        id: pred.id,
        symbol: pred.symbol,
        timeframe: pred.timeframe,
        created_at: pred.created_at,
        status: pred.status || 'completed',
        current_price: result.current_price,
        direction,
        max_expected_change: maxExpectedChange,
        prediction_start: predictionStart,
        prediction_end: predictionEnd
      }
    })
  } catch (err: any) {
    error.value = err.message || 'Failed to load predictions'
  } finally {
    loading.value = false
  }
}

/**
 * Generate a new prediction
 */
async function generatePrediction() {
  if (!newPrediction.value.symbol) {
    alert('Please select a symbol')
    return
  }

  generating.value = true

  try {
    const data = await api.generatePredictions(
      newPrediction.value.symbol,
      newPrediction.value.timeframe,
      true // auto_train
    )

    // Close modal immediately - prediction runs in background
    generating.value = false
    showGenerateModal.value = false

    // Refresh the predictions list after a short delay
    setTimeout(() => loadPredictions(), 1000)

  } catch (error: any) {
    alert(`Failed to generate prediction: ${error.message}`)
    generating.value = false
  }
}

/**
 * View prediction details
 */
async function viewPrediction(prediction: PredictionListItem) {
  viewingPrediction.value = prediction
  showViewModal.value = true
  loadingPredictionData.value = true
  viewError.value = null
  predictionData.value = null

  try {
    const data = await api.getPredictionById(prediction.id)

    if (data.status === 'completed' && data.result) {
      predictionData.value = data.result
    } else {
      viewError.value = 'Prediction has no results yet'
    }
  } catch (err: any) {
    viewError.value = err.message || 'Failed to load prediction details'
  } finally {
    loadingPredictionData.value = false
  }
}

/**
 * Get badge variant for status
 */
function getStatusVariant(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const variantMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    completed: 'success',
    running: 'warning',
    queued: 'info',
    failed: 'danger'
  }
  return variantMap[status] || 'info'
}

// Watch for prediction task completions and refresh list
watch(
  () => taskManager.completedTasks,
  (completedTasks) => {
    // Check if any prediction tasks completed
    const hasPredictionCompleted = completedTasks.some(task => task.task_type === 'prediction')
    if (hasPredictionCompleted) {
      loadPredictions()
    }
  },
  { deep: true }
)

// Initialize
onMounted(async () => {
  // Load predictions and symbols in parallel
  await Promise.all([loadPredictions(), fetchSymbols()])

  // Set default symbol
  if (availableSymbols.value.length > 0) {
    newPrediction.value.symbol = availableSymbols.value[0] ?? ''
  }

  // Set up real-time subscription for predictions
  setupRealtimeSubscription()
})

onUnmounted(() => {
  // Clean up real-time subscription
  if (realtimeChannel) {
    console.log('Unsubscribing from real-time prediction updates')
    supabase.removeChannel(realtimeChannel)
    realtimeChannel = null
  }
})

/**
 * Set up real-time subscription for predictions
 */
function setupRealtimeSubscription() {
  if (!user.value) return

  console.log('Setting up real-time subscription for predictions')

  realtimeChannel = supabase
    .channel('predictions_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'predictions',
        filter: `user_id=eq.${user.value.id}`
      },
      (payload) => {
        console.log('Prediction change detected:', payload)

        if (payload.eventType === 'INSERT') {
          // New prediction added
          const newPrediction = {
            id: payload.new.id,
            symbol: payload.new.symbol,
            timeframe: payload.new.timeframe,
            created_at: payload.new.created_at,
            status: payload.new.status || 'running',
            current_price: payload.new.result?.current_price
          }
          predictions.value.unshift(newPrediction)
        } else if (payload.eventType === 'UPDATE') {
          // Prediction updated (e.g., status changed from running to completed)
          const index = predictions.value.findIndex(p => p.id === payload.new.id)
          if (index !== -1) {
            predictions.value[index] = {
              ...predictions.value[index],
              status: payload.new.status,
              current_price: payload.new.result?.current_price
            }
          }
        } else if (payload.eventType === 'DELETE') {
          // Prediction deleted
          predictions.value = predictions.value.filter(p => p.id !== payload.old.id)
        }
      }
    )
    .subscribe()
}
</script>

<style scoped>
.spinner {
  width: 2rem;
  height: 2rem;
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
