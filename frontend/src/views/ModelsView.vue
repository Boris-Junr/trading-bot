<template>
  <div>
    <!-- Loading State -->
    <LoadingSpinner v-if="loading" />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Models List -->
    <div v-else class="space-y-6">
      <!-- Empty State -->
      <EmptyState
        v-if="models.length === 0"
        :icon="CpuChipIcon"
        title="No Models Trained Yet"
        description="Train your first ML model for price prediction"
        action-text="Train Your First Model"
        @action="showTrainModal = true"
      >
        <template #action>
          <Button @click="showTrainModal = true" variant="primary">
            Train Your First Model
          </Button>
        </template>
      </EmptyState>

      <!-- Model Cards -->
      <Card v-for="model in models" :key="model.name">
        <div class="flex justify-between items-start mb-4">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-lg font-semibold text-text-primary">{{ model.name }}</h3>
              <Badge variant="success" size="sm">{{ model.type.toUpperCase() }}</Badge>
            </div>
            <p class="text-sm text-text-secondary">{{ formatModelDescription(model) }}</p>
          </div>
        </div>

        <!-- Model Details Grid -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <div>
            <div class="text-xs text-text-muted mb-1">Symbol</div>
            <div class="text-sm font-semibold text-text-primary">{{ model.symbol }}</div>
          </div>
          <div>
            <div class="text-xs text-text-muted mb-1">Timeframe</div>
            <div class="text-sm font-semibold text-text-primary">{{ model.timeframe }}</div>
          </div>
          <div>
            <div class="text-xs text-text-muted mb-1">Prediction Steps</div>
            <div class="text-sm font-semibold text-text-primary">{{ model.n_steps_ahead }}</div>
          </div>
          <div>
            <div class="text-xs text-text-muted mb-1">Model Size</div>
            <div class="text-sm font-semibold text-text-primary">{{ formatNumber(model.model_size_kb, 1) }} KB</div>
          </div>
          <div>
            <div class="text-xs text-text-muted mb-1">Trained</div>
            <div class="text-sm font-semibold text-text-primary">{{ formatDate(model.trained_at) }}</div>
          </div>
        </div>

        <!-- Performance Metrics -->
        <div class="pt-4 border-t border-border-default">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div class="text-xs text-text-muted mb-1">Train R²</div>
              <div class="text-lg font-bold font-mono text-text-primary">{{ formatNumber(model.performance.train_r2, 3) }}</div>
            </div>
            <div>
              <div class="text-xs text-text-muted mb-1">Val R²</div>
              <div class="text-lg font-bold font-mono text-text-primary">{{ formatNumber(model.performance.val_r2, 3) }}</div>
            </div>
            <div>
              <div class="text-xs text-text-muted mb-1">Train RMSE</div>
              <div class="text-lg font-bold font-mono text-text-primary">{{ formatNumber(model.performance.train_rmse, 2) }}</div>
            </div>
            <div>
              <div class="text-xs text-text-muted mb-1">Val RMSE</div>
              <div class="text-lg font-bold font-mono text-text-primary">{{ formatNumber(model.performance.val_rmse, 2) }}</div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="mt-4 flex gap-2">
          <Button variant="secondary" size="sm">View Details</Button>
          <Button variant="secondary" size="sm">Test Model</Button>
          <Button variant="secondary" size="sm">Export</Button>
        </div>
      </Card>
    </div>

    <!-- Train Model Modal -->
    <Modal
      v-model="showTrainModal"
      title="Train New Model"
      subtitle="Configure and train a new ML model for price prediction"
      size="md"
    >
      <div class="space-y-5">
        <Select v-model="newModel.symbol" label="Trading Symbol" :disabled="loadingSymbols">
          <option v-for="symbol in availableSymbols" :key="symbol" :value="symbol.replace('/', '_')">
            {{ symbol }}
          </option>
        </Select>

        <Select v-model="newModel.timeframe" label="Timeframe">
          <option value="1m">1 minute</option>
          <option value="5m">5 minutes</option>
          <option value="15m">15 minutes</option>
          <option value="1h">1 hour</option>
        </Select>

        <Input
          v-model="newModel.n_steps_ahead"
          type="number"
          label="Prediction Steps"
          hint="Number of future steps to predict"
        />

        <Input
          v-model="newModel.days_history"
          type="number"
          label="Training Days"
          hint="Number of days of historical data to use for training"
        />
      </div>

      <template #footer>
        <Button @click="showTrainModal = false" variant="secondary">
          Cancel
        </Button>
        <Button @click="trainModel" :disabled="training" variant="primary" class="flex-1">
          {{ training ? 'Training...' : 'Start Training' }}
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { ModelInfo } from '../types'
import api from '../services/api'
import { useFormatters } from '@/composables/useFormatters'
import { useSymbols } from '@/composables/useSymbols'
import { CpuChipIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Modal from '@/components/ui/Modal.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

// Initialize composables
const { formatDate, formatNumber } = useFormatters()
const { symbols: availableSymbols, loading: loadingSymbols, fetch: fetchSymbols } = useSymbols('all')

const showTrainModal = ref(false)
const models = ref<ModelInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const training = ref(false)

const newModel = ref({
  symbol: 'ETH_USDT',
  timeframe: '1m',
  n_steps_ahead: 300,
  days_history: 30,
})

onMounted(async () => {
  await Promise.all([fetchModels(), fetchSymbols()])
})

async function fetchModels() {
  loading.value = true
  error.value = null
  try {
    models.value = await api.getModels()
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch models'
    console.error('Failed to fetch models:', e)
  } finally {
    loading.value = false
  }
}

async function trainModel() {
  training.value = true
  try {
    await api.trainModel(newModel.value)
    showTrainModal.value = false
    await fetchModels()
  } catch (e) {
    console.error('Failed to train model:', e)
  } finally {
    training.value = false
  }
}

function formatModelDescription(model: ModelInfo): string {
  return `${model.type} model for ${model.symbol} price prediction (${model.timeframe} timeframe)`
}
</script>

<style scoped>
</style>
