<template>
  <div class="space-y-6">
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <StatCard
        label="Current Price"
        :value="formatCurrency(data.current_price)"
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
        :value="formatPercent(finalPrediction.changePercent)"
        :change="`Target: ${formatCurrency(finalPrediction.price)}`"
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
          <TableCell align="right" mono>{{ formatCurrency(prediction.predicted_open) }}</TableCell>
          <TableCell align="right" mono>{{ formatCurrency(prediction.predicted_high) }}</TableCell>
          <TableCell align="right" mono>{{ formatCurrency(prediction.predicted_low) }}</TableCell>
          <TableCell align="right" mono>{{ formatCurrency(prediction.predicted_close) }}</TableCell>
          <TableCell align="right" mono :class="prediction.predicted_return >= 0 ? 'text-accent-success' : 'text-accent-danger'">
            {{ formatPercent(prediction.predicted_return * 100, 3) }}
          </TableCell>
          <TableCell align="right" mono>{{ formatPercent((prediction.confidence ?? 0) * 100, 1, false) }}</TableCell>
        </TableRow>
      </Table>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { PredictionData } from '@/types'
import { useChart } from '@/composables/useChart'
import { useFormatters } from '@/composables/useFormatters'
import { ChartBarIcon, TableCellsIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import StatCard from '@/features/dashboard/components/StatCard.vue'
import Table from '@/components/ui/Table.vue'
import TableHeader from '@/components/ui/TableHeader.vue'
import TableRow from '@/components/ui/TableRow.vue'
import TableCell from '@/components/ui/TableCell.vue'

/**
 * Prediction Results Card Component
 *
 * Displays prediction results including summary stats, chart, and detailed table.
 * Can be reused for both current and historical predictions.
 */

interface Props {
  /**
   * Prediction data to display
   */
  data: PredictionData
}

const props = defineProps<Props>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const { createChart } = useChart(chartCanvas)
const { formatCurrency, formatPercent } = useFormatters()

// Watch for data changes and update chart
watch(() => props.data, async (newData) => {
  if (newData) {
    await nextTick()
    updateChart(newData)
  }
}, { immediate: true })

/**
 * Update chart with prediction data
 */
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
            label: (context: any) => {
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
          ticks: { callback: (value: any) => `$${value}` },
        },
      },
      interaction: { mode: 'index', intersect: false },
    },
  } as any)
}

/**
 * First 20 predictions for table display
 */
const displayedPredictions = computed(() => {
  return props.data.predictions.slice(0, 20)
})

/**
 * Final prediction summary (last prediction)
 */
const finalPrediction = computed(() => {
  if (!props.data || props.data.predictions.length === 0) {
    return { price: 0, change: 0, changePercent: 0 }
  }
  const lastPrediction = props.data.predictions[props.data.predictions.length - 1]
  if (!lastPrediction) {
    return { price: 0, change: 0, changePercent: 0 }
  }
  const change = lastPrediction.predicted_close - props.data.current_price
  const changePercent = (change / props.data.current_price) * 100
  return { price: lastPrediction.predicted_close, change, changePercent }
})
</script>
