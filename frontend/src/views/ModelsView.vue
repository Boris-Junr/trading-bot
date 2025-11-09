<template>
  <div>
    <!-- Header -->
    <div class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">ML Models</h1>
        <p class="mt-2 text-gray-600">Manage and train machine learning models</p>
      </div>
      <button @click="showTrainModal = true" class="btn-primary">
        Train New Model
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-gray-500">Loading models...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200 mb-8">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Models List -->
    <div v-else class="grid grid-cols-1 gap-6">
      <div v-if="models.length === 0" class="card text-center py-12">
        <p class="text-gray-500">No models trained yet</p>
        <button @click="showTrainModal = true" class="btn-primary mt-4">
          Train Your First Model
        </button>
      </div>

      <!-- Model Cards -->
      <div v-for="model in models" :key="model.name" class="card">
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-lg font-semibold text-gray-900">{{ model.name }}</h3>
              <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">{{ model.type.toUpperCase() }}</span>
            </div>
            <p class="text-sm text-gray-600 mb-4">{{ formatModelDescription(model) }}</p>

            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div class="text-xs text-gray-500">Symbol</div>
                <div class="text-sm font-medium">{{ model.symbol }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Timeframe</div>
                <div class="text-sm font-medium">{{ model.timeframe }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Prediction Steps</div>
                <div class="text-sm font-medium">{{ model.n_steps_ahead }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Model Size</div>
                <div class="text-sm font-medium">{{ model.model_size_kb.toFixed(1) }} KB</div>
              </div>
              <div>
                <div class="text-xs text-gray-500">Trained</div>
                <div class="text-sm font-medium">{{ formatDate(model.trained_at) }}</div>
              </div>
            </div>

            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div class="text-xs text-gray-500">Train R²</div>
                  <div class="text-lg font-semibold text-gray-900">{{ model.performance.train_r2.toFixed(3) }}</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Val R²</div>
                  <div class="text-lg font-semibold text-gray-900">{{ model.performance.val_r2.toFixed(3) }}</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Train RMSE</div>
                  <div class="text-lg font-semibold text-gray-900">{{ model.performance.train_rmse.toFixed(2) }}</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Val RMSE</div>
                  <div class="text-lg font-semibold text-gray-900">{{ model.performance.val_rmse.toFixed(2) }}</div>
                </div>
              </div>
            </div>

            <div class="mt-4 flex gap-2">
              <button class="btn-secondary text-sm">View Details</button>
              <button class="btn-secondary text-sm">Test Model</button>
              <button class="btn-secondary text-sm">Export</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Train Model Modal -->
    <div
      v-if="showTrainModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showTrainModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-gray-900">Train New Model</h2>
            <button @click="showTrainModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
              <input
                v-model="newModel.symbol"
                type="text"
                placeholder="e.g., ETH_USDT"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
              <select v-model="newModel.timeframe" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="1m">1 minute</option>
                <option value="5m">5 minutes</option>
                <option value="15m">15 minutes</option>
                <option value="1h">1 hour</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Prediction Steps</label>
              <input
                v-model.number="newModel.n_steps_ahead"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Training Days</label>
              <input
                v-model.number="newModel.days_history"
                type="number"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <p class="text-xs text-gray-500 mt-1">Number of days of historical data to use for training</p>
            </div>
          </div>

          <div class="mt-6 flex gap-3">
            <button @click="trainModel" :disabled="training" class="btn-primary flex-1">
              {{ training ? 'Training...' : 'Start Training' }}
            </button>
            <button @click="showTrainModal = false" class="btn-secondary">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { ModelInfo } from '../types';
import api from '../services/api';

const showTrainModal = ref(false);
const models = ref<ModelInfo[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const training = ref(false);

const newModel = ref({
  symbol: 'ETH_USDT',
  timeframe: '1m',
  n_steps_ahead: 300,
  days_history: 30,
});

onMounted(async () => {
  await fetchModels();
});

async function fetchModels() {
  loading.value = true;
  error.value = null;
  try {
    models.value = await api.getModels();
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch models';
    console.error('Failed to fetch models:', e);
  } finally {
    loading.value = false;
  }
}

async function trainModel() {
  training.value = true;
  try {
    await api.trainModel(newModel.value);
    showTrainModal.value = false;
    await fetchModels();
  } catch (e) {
    console.error('Failed to train model:', e);
  } finally {
    training.value = false;
  }
}

function formatModelDescription(model: ModelInfo): string {
  return `${model.type} model for ${model.symbol} price prediction (${model.timeframe} timeframe)`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
</script>
