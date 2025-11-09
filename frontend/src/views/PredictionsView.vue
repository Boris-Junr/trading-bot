<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900">ML Predictions</h1>
      <p class="mt-2 text-gray-600">Price predictions from machine learning models</p>
    </div>

    <!-- Controls -->
    <div class="card mb-8">
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
          <select v-model="selectedSymbol" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            <option value="ETH_USDT">ETH_USDT</option>
            <option value="BTC_USDT">BTC_USDT</option>
            <option value="SOL_USDT">SOL_USDT</option>
          </select>
        </div>

        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
          <select v-model="selectedTimeframe" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
          </select>
        </div>

        <div class="flex items-end">
          <Button @click="fetchPredictions" :disabled="loading" variant="primary">
            {{ loading ? 'Loading...' : 'Generate Prediction' }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card py-12">
      <div class="flex flex-col items-center space-y-4">
        <!-- Spinner -->
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>

        <!-- Status Messages -->
        <div class="text-center space-y-2">
          <div class="text-lg font-medium text-gray-900">{{ loadingStatus.title }}</div>
          <div class="text-sm text-gray-600">{{ loadingStatus.message }}</div>

          <!-- Progress Steps -->
          <div class="mt-6 space-y-2">
            <div v-for="step in loadingSteps" :key="step.name"
                 class="flex items-center justify-center space-x-2 text-sm">
              <div class="flex items-center space-x-2">
                <!-- Completed -->
                <svg v-if="step.status === 'completed'" class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <!-- In Progress -->
                <div v-else-if="step.status === 'in-progress'" class="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <!-- Pending -->
                <div v-else class="w-5 h-5 border-2 border-gray-300 rounded-full"></div>

                <span :class="step.status === 'completed' ? 'text-green-600 font-medium' :
                              step.status === 'in-progress' ? 'text-blue-600 font-medium' :
                              'text-gray-400'">
                  {{ step.label }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200 mb-8">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Predictions Content -->
    <div v-else-if="predictionData">
      <!-- Current Price -->
      <div class="card mb-8">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-gray-600">Current Price</div>
            <div class="text-3xl font-bold text-gray-900">${{ predictionData.current_price.toFixed(2) }}</div>
            <div class="text-sm text-gray-500 mt-1">{{ selectedSymbol }}</div>
          </div>
          <div class="text-right">
            <div class="text-sm text-gray-600">Last Updated</div>
            <div class="text-lg font-medium">{{ formatTime(predictionData.timestamp) }}</div>
            <div class="text-xs text-gray-500 mt-1">Smoothness: {{ (predictionData.smoothness_score * 100).toFixed(1) }}%</div>
          </div>
        </div>
      </div>

      <!-- Prediction Chart -->
      <div class="card mb-8">
        <h2 class="card-header">Price Prediction (Next {{ Math.floor(predictionData.predictions.length / 60) }} Hours)</h2>
        <div class="h-96">
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>

      <!-- Prediction Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="stat-card">
          <div class="stat-label">Predicted Direction</div>
          <div class="stat-value" :class="finalPrediction.change >= 0 ? 'positive' : 'negative'">
            {{ finalPrediction.change >= 0 ? 'BULLISH' : 'BEARISH' }}
          </div>
          <div class="text-xs text-gray-500 mt-2">Next {{ predictionData.predictions.length }} steps</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Expected Change</div>
          <div class="stat-value" :class="finalPrediction.changePercent >= 0 ? 'positive' : 'negative'">
            {{ finalPrediction.changePercent >= 0 ? '+' : '' }}{{ finalPrediction.changePercent.toFixed(2) }}%
          </div>
          <div class="text-xs text-gray-500 mt-2">${{ finalPrediction.price.toFixed(2) }} target</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Avg Confidence</div>
          <div class="stat-value">{{ (avgConfidence * 100).toFixed(1) }}%</div>
          <div class="text-xs text-gray-500 mt-2">Model certainty</div>
        </div>
      </div>

      <!-- Predictions Table -->
      <div class="card">
        <h2 class="card-header">Step-by-Step Predictions (Showing first 20)</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Time Ahead</th>
                <th>Open</th>
                <th>High</th>
                <th>Low</th>
                <th>Close</th>
                <th>Change</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="prediction in displayedPredictions" :key="prediction.step">
                <td>+{{ prediction.minutes_ahead }} min</td>
                <td>${{ prediction.predicted_open.toFixed(2) }}</td>
                <td>${{ prediction.predicted_high.toFixed(2) }}</td>
                <td>${{ prediction.predicted_low.toFixed(2) }}</td>
                <td>${{ prediction.predicted_close.toFixed(2) }}</td>
                <td :class="prediction.predicted_return >= 0 ? 'positive' : 'negative'">
                  {{ prediction.predicted_return >= 0 ? '+' : '' }}{{ (prediction.predicted_return * 100).toFixed(3) }}%
                </td>
                <td>{{ (prediction.confidence * 100).toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="card text-center py-12">
      <p class="text-gray-500">Select symbol and timeframe, then click "Generate Prediction"</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import type { PredictionData } from '../types';
import api from '../services/api';
import { useChart } from '../composables/useChart';
import Button from '@/shared/components/ui/Button.vue';

const selectedSymbol = ref('ETH_USDT');
const selectedTimeframe = ref('1m');
const predictionData = ref<PredictionData | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const chartCanvas = ref<HTMLCanvasElement | null>(null);

const loadingStatus = ref({
  title: 'Loading...',
  message: ''
});

const loadingSteps = ref([
  { name: 'check', label: 'Checking for existing model', status: 'pending' },
  { name: 'fetch', label: 'Fetching market data', status: 'pending' },
  { name: 'train', label: 'Processing model', status: 'pending' },
  { name: 'predict', label: 'Generating predictions', status: 'pending' }
]);

const { createChart } = useChart(chartCanvas);

watch(predictionData, async (newData) => {
  if (newData) {
    await nextTick();
    updateChart(newData);
  }
});

function updateLoadingStep(stepName: string, status: 'pending' | 'in-progress' | 'completed') {
  const step = loadingSteps.value.find(s => s.name === stepName);
  if (step) {
    step.status = status;
  }
}

function resetLoadingSteps() {
  loadingSteps.value.forEach(step => step.status = 'pending');
}

async function fetchPredictions() {
  loading.value = true;
  error.value = null;
  resetLoadingSteps();

  // Use Server-Sent Events to get real-time progress updates from backend
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
  const url = `${baseURL}/predictions/stream?symbol=${selectedSymbol.value}&timeframe=${selectedTimeframe.value}`;

  const eventSource = new EventSource(url);

  eventSource.addEventListener('status', (event) => {
    const data = JSON.parse(event.data);

    // Update loading status if we have title/message
    if (data.title || data.message) {
      loadingStatus.value = {
        title: data.title || loadingStatus.value.title,
        message: data.message || loadingStatus.value.message
      };
    }

    // Update step status
    updateLoadingStep(data.step, data.status);
  });

  eventSource.addEventListener('complete', (event) => {
    const data = JSON.parse(event.data);
    predictionData.value = data;
    eventSource.close();
    loading.value = false;
  });

  eventSource.addEventListener('error', (event) => {
    const data = JSON.parse(event.data);
    error.value = data.message || 'Failed to fetch predictions';
    eventSource.close();
    loading.value = false;
  });

  eventSource.onerror = () => {
    error.value = 'Connection to server lost';
    eventSource.close();
    loading.value = false;
  };
}

function updateChart(data: PredictionData) {
  if (!chartCanvas.value) return;

  // Sample predictions for better chart performance while showing more detail
  // Show more points than before: every 2nd point when > 200, every 3rd when > 150
  const allPredictions = data.predictions;
  let sampleRate = 1;
  if (allPredictions.length > 200) {
    sampleRate = 2;
  } else if (allPredictions.length > 150) {
    sampleRate = 3;
  }

  const predictions = allPredictions.filter((_, i) => i % sampleRate === 0);

  // Prepare predicted candlestick data from OHLC predictions
  const candlestickData = predictions.map(pred => ({
    x: new Date(pred.timestamp).getTime(),
    o: pred.predicted_open,
    h: pred.predicted_high,
    l: pred.predicted_low,
    c: pred.predicted_close,
  }));

  // Calculate min/max for y-axis with padding based on actual highs and lows
  const allHighs = allPredictions.map(p => p.predicted_high);
  const allLows = allPredictions.map(p => p.predicted_low);
  const absoluteHigh = Math.max(...allHighs);
  const absoluteLow = Math.min(...allLows);

  // Add 15% padding to the range for better visualization
  const priceRange = absoluteHigh - absoluteLow;
  const padding = priceRange * 0.15;

  // Calculate padded values
  const paddedMin = absoluteLow - padding;
  const paddedMax = absoluteHigh + padding;

  // Round to nice values for cleaner axis
  // Round down min to nearest 0.5 or 1 depending on price range
  const roundingFactor = priceRange > 100 ? 10 : priceRange > 10 ? 1 : 0.5;
  const yMin = Math.floor(paddedMin / roundingFactor) * roundingFactor;
  const yMax = Math.ceil(paddedMax / roundingFactor) * roundingFactor;

  // Create chart configuration
  createChart({
    type: 'candlestick',
    data: {
      datasets: [
        {
          label: 'Predicted Price',
          data: candlestickData,
          type: 'candlestick',
          color: {
            up: 'rgb(34, 197, 94)',
            down: 'rgb(239, 68, 68)',
            unchanged: 'rgb(156, 163, 175)',
          },
          borderColor: {
            up: 'rgb(34, 197, 94)',
            down: 'rgb(239, 68, 68)',
            unchanged: 'rgb(156, 163, 175)',
          },
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              const point = context.raw as any;
              return [
                `Open: $${point.o.toFixed(2)}`,
                `High: $${point.h.toFixed(2)}`,
                `Low: $${point.l.toFixed(2)}`,
                `Close: $${point.c.toFixed(2)}`,
              ];
            },
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'minute',
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
            },
          },
          title: {
            display: true,
            text: 'Time',
          },
        },
        y: {
          min: yMin,
          max: yMax,
          title: {
            display: true,
            text: 'Predicted Price (USD)',
          },
          ticks: {
            callback: (value) => `$${value}`,
          },
        },
      },
      interaction: {
        mode: 'index',
        intersect: false,
      },
    },
  } as any);
}

const displayedPredictions = computed(() => {
  if (!predictionData.value) return [];
  return predictionData.value.predictions.slice(0, 20);
});

const finalPrediction = computed(() => {
  if (!predictionData.value || predictionData.value.predictions.length === 0) {
    return { price: 0, change: 0, changePercent: 0 };
  }
  const lastPrediction = predictionData.value.predictions[predictionData.value.predictions.length - 1];
  const change = lastPrediction.predicted_close - predictionData.value.current_price;
  const changePercent = (change / predictionData.value.current_price) * 100;
  return {
    price: lastPrediction.predicted_close,
    change,
    changePercent
  };
});

const avgConfidence = computed(() => {
  if (!predictionData.value || predictionData.value.predictions.length === 0) return 0;
  const sum = predictionData.value.predictions.reduce((acc, p) => acc + p.confidence, 0);
  return sum / predictionData.value.predictions.length;
});

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}
</script>
