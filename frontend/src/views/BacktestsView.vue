<template>
  <div>
    <!-- Header -->
    <div class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Backtests</h1>
        <p class="mt-2 text-gray-600">Test your strategies on historical data</p>
      </div>
      <button
        @click="showRunModal = true"
        :disabled="loadingModels"
        class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ loadingModels ? 'Loading...' : 'Run New Backtest' }}
      </button>
    </div>

    <!-- No Models Info -->
    <div v-if="!hasModels && !loadingModels" class="card bg-blue-50 border border-blue-200 mb-8">
      <div class="flex items-start">
        <svg class="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <div>
          <h3 class="font-semibold text-blue-900">No trained models found</h3>
          <p class="text-sm text-blue-700 mt-1">
            No pre-trained models detected. When you run a backtest, a model will be automatically trained for your selected symbol and timeframe (this may take 2-5 minutes).
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-gray-500">Loading backtests...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Backtests List -->
    <div v-else>
      <div v-if="sortedBacktests.length === 0" class="card text-center py-12">
        <p class="text-gray-500">No backtests run yet</p>
        <button
          @click="showRunModal = true"
          class="btn-primary mt-4"
        >
          Run Your First Backtest
        </button>
        <p v-if="!hasModels" class="text-sm text-gray-500 mt-4">
          A model will be automatically trained when you run your first backtest
        </p>
      </div>

      <div v-else class="grid grid-cols-1 gap-6">
        <div
          v-for="backtest in sortedBacktests"
          :key="backtest.end_date + backtest.strategy"
          class="card hover:shadow-lg transition-shadow cursor-pointer"
          @click="goToDetail(backtest)"
        >
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-lg font-semibold text-gray-900">{{ backtest.strategy }}</h3>
                <span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                  {{ backtest.symbol }}
                </span>
              </div>
              <p class="text-sm text-gray-600 mb-4">
                {{ formatDate(backtest.start_date) }} - {{ formatDate(backtest.end_date) }}
              </p>

              <!-- Performance Metrics Grid -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div class="text-xs text-gray-500">Total Return</div>
                  <div
                    class="text-lg font-semibold"
                    :class="backtest.performance.total_return >= 0 ? 'positive' : 'negative'"
                  >
                    {{ backtest.performance.total_return >= 0 ? '+' : '' }}{{ (backtest.performance.total_return * 100).toFixed(2) }}%
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Total P&L</div>
                  <div
                    class="text-lg font-semibold"
                    :class="backtest.performance.total_pnl >= 0 ? 'positive' : 'negative'"
                  >
                    {{ backtest.performance.total_pnl >= 0 ? '+' : '' }}${{ formatNumber(backtest.performance.total_pnl) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Sharpe Ratio</div>
                  <div class="text-lg font-semibold text-gray-900">
                    {{ backtest.performance.sharpe_ratio.toFixed(2) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Win Rate</div>
                  <div class="text-lg font-semibold text-gray-900">
                    {{ (backtest.trading.win_rate * 100).toFixed(1) }}%
                  </div>
                </div>
              </div>
            </div>
            <div class="ml-4">
              <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Run Backtest Modal -->
    <div
      v-if="showRunModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showRunModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-gray-900">Run New Backtest</h2>
            <button @click="showRunModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Strategy</label>
              <select v-model="newBacktest.strategy" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="MLPredictive">ML Predictive Strategy</option>
              </select>
              <p class="text-xs text-gray-500 mt-1">More strategies coming soon (RSI, MACD, etc.)</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
              <select v-model="newBacktest.symbol" class="w-full px-3 py-2 border border-gray-300 rounded-lg" :disabled="loadingSymbols">
                <option v-if="loadingSymbols" value="">Loading symbols...</option>
                <option v-else v-for="symbol in availableSymbols" :key="symbol" :value="symbol">
                  {{ symbol }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                <span v-if="hasModels && modelsSymbols.includes(newBacktest.symbol)">
                  ✓ Model available for {{ newBacktest.symbol }}
                </span>
                <span v-else>
                  Model will be trained automatically (2-5 minutes)
                </span>
              </p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  v-model="newBacktest.start_date"
                  type="date"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  v-model="newBacktest.end_date"
                  type="date"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Initial Capital ($)</label>
              <input
                v-model.number="newBacktest.initial_capital"
                type="number"
                step="100"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <!-- Progress indicator -->
          <div v-if="running" class="mt-6 space-y-4">
            <!-- Status message -->
            <div v-if="backtestStatus.title" class="p-4 bg-blue-50 rounded-lg">
              <div class="font-medium text-blue-900">{{ backtestStatus.title }}</div>
              <div class="text-sm text-blue-700 mt-1">{{ backtestStatus.message }}</div>
            </div>

            <!-- Progress steps -->
            <div class="space-y-2">
              <div
                v-for="step in backtestSteps"
                :key="step.name"
                class="flex items-center gap-3"
              >
                <div class="flex-shrink-0">
                  <svg v-if="step.status === 'completed'" class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  <svg v-else-if="step.status === 'in-progress'" class="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <span
                  class="text-sm"
                  :class="{
                    'text-green-600 font-medium': step.status === 'completed',
                    'text-blue-600 font-medium': step.status === 'in-progress',
                    'text-gray-500': step.status === 'pending'
                  }"
                >
                  {{ step.label }}
                </span>
              </div>
            </div>
          </div>

          <div class="mt-6 flex gap-3">
            <button @click="runBacktest" :disabled="running" class="btn-primary flex-1">
              {{ running ? 'Running...' : 'Run Backtest' }}
            </button>
            <button @click="showRunModal = false" :disabled="running" class="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useBacktestStore } from '../stores/backtest';
import { storeToRefs } from 'pinia';
import type { BacktestResult, ModelInfo } from '../types';
import api from '../services/api';

const router = useRouter();
const backtestStore = useBacktestStore();
const { backtests, loading, error, sortedBacktests } = storeToRefs(backtestStore);

const showRunModal = ref(false);
const running = ref(false);
const availableModels = ref<ModelInfo[]>([]);
const loadingModels = ref(false);
const availableSymbols = ref<string[]>([]);
const loadingSymbols = ref(false);

const newBacktest = ref({
  strategy: 'MLPredictive',
  symbol: '',
  start_date: '',
  end_date: '',
  initial_capital: 10000,
});

// Get symbols with trained models
const modelsSymbols = computed(() => {
  const symbols = new Set(availableModels.value.map(m => m.symbol));
  return Array.from(symbols);
});

const hasModels = computed(() => availableModels.value.length > 0);

onMounted(async () => {
  // Set default dates (last 30 days)
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  newBacktest.value.end_date = end.toISOString().split('T')[0];
  newBacktest.value.start_date = start.toISOString().split('T')[0];

  // Fetch available symbols and models in parallel
  await Promise.all([
    fetchSymbols(),
    fetchModels()
  ]);

  // Set default symbol to first available symbol
  if (availableSymbols.value.length > 0) {
    newBacktest.value.symbol = availableSymbols.value[0];
  }

  await backtestStore.fetchBacktests();
});

async function fetchSymbols() {
  loadingSymbols.value = true;
  try {
    availableSymbols.value = await api.getSymbols('crypto');
  } catch (e) {
    console.error('Failed to fetch symbols:', e);
    // Fallback to default list if API fails
    availableSymbols.value = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'];
  } finally {
    loadingSymbols.value = false;
  }
}

async function fetchModels() {
  loadingModels.value = true;
  try {
    availableModels.value = await api.getModels();
  } catch (e) {
    console.error('Failed to fetch models:', e);
  } finally {
    loadingModels.value = false;
  }
}

const backtestStatus = ref({ title: '', message: '' });
const backtestSteps = ref([
  { name: 'fetch', label: 'Fetch Data', status: 'pending' },
  { name: 'model', label: 'Prepare Model', status: 'pending' },
  { name: 'backtest', label: 'Run Backtest', status: 'pending' },
  { name: 'analyze', label: 'Analyze Results', status: 'pending' },
]);

function updateBacktestStep(stepName: string, status: 'pending' | 'in-progress' | 'completed') {
  const step = backtestSteps.value.find(s => s.name === stepName);
  if (step) {
    step.status = status;
  }
}

function resetBacktestSteps() {
  backtestSteps.value.forEach(step => step.status = 'pending');
  backtestStatus.value = { title: '', message: '' };
}

async function runBacktest() {
  // Validate inputs
  if (!newBacktest.value.symbol) {
    alert('Please select a symbol');
    return;
  }

  if (!newBacktest.value.start_date || !newBacktest.value.end_date) {
    alert('Please select start and end dates');
    return;
  }

  running.value = true;
  resetBacktestSteps();

  // Use Server-Sent Events to get real-time progress updates
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

  const params = new URLSearchParams({
    strategy: newBacktest.value.strategy,
    symbol: newBacktest.value.symbol,
    start_date: newBacktest.value.start_date,
    end_date: newBacktest.value.end_date,
    initial_capital: newBacktest.value.initial_capital.toString(),
    params: JSON.stringify({
      timeframe: '1m',
      min_predicted_return: 0.002,
      confidence_threshold: 0.6,
      prediction_window: 60,
      risk_per_trade: 0.02
    })
  });

  const url = `${baseURL}/backtests/stream?${params.toString()}`;

  const eventSource = new EventSource(url);

  eventSource.addEventListener('status', (event: any) => {
    const data = JSON.parse(event.data);

    // Update status message
    if (data.title || data.message) {
      backtestStatus.value = {
        title: data.title || backtestStatus.value.title,
        message: data.message || backtestStatus.value.message
      };
    }

    // Update step status
    updateBacktestStep(data.step, data.status);
  });

  eventSource.addEventListener('complete', async (event: any) => {
    const data = JSON.parse(event.data);
    eventSource.close();
    running.value = false;
    showRunModal.value = false;

    // Refresh the backtests list
    await backtestStore.fetchBacktests();
  });

  eventSource.addEventListener('error', (event: any) => {
    try {
      const data = JSON.parse(event.data);
      alert(`Failed to run backtest: ${data.message}`);
    } catch {
      alert('Failed to run backtest: Connection error');
    }
    eventSource.close();
    running.value = false;
  });

  eventSource.onerror = () => {
    alert('Connection to server lost');
    eventSource.close();
    running.value = false;
  };
}

function goToDetail(backtest: BacktestResult) {
  // For now, we'll use a simple ID (could be improved with actual IDs from backend)
  const id = btoa(`${backtest.strategy}-${backtest.end_date}`);
  router.push(`/backtests/${id}`);
}

function formatNumber(value: number): string {
  return Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
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
