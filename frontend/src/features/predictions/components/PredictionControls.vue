<template>
  <Card title="Prediction Settings" :icon="CogIcon">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Select
        v-model="localSymbol"
        label="Symbol"
        :disabled="loadingSymbols"
        :key="`symbols-${symbols.length}`"
      >
        <option v-for="symbol in symbols" :key="symbol" :value="symbol">
          {{ symbol }}
        </option>
      </Select>

      <Select v-model="localTimeframe" label="Timeframe">
        <option value="1m">1 Minute</option>
        <option value="5m">5 Minutes</option>
        <option value="15m">15 Minutes</option>
        <option value="1h">1 Hour</option>
      </Select>

      <div class="flex items-end">
        <Button @click="handleGenerate" :disabled="isGenerating" variant="primary" class="w-full">
          {{ isGenerating ? 'Loading...' : 'Generate Prediction' }}
        </Button>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CogIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Select from '@/components/ui/Select.vue'

/**
 * Prediction Controls Component
 *
 * Provides symbol and timeframe selection with generate prediction button.
 * Handles form state and validation.
 */

interface Props {
  /**
   * Currently selected symbol
   */
  symbol: string

  /**
   * Currently selected timeframe
   */
  timeframe: string

  /**
   * Available symbols for selection
   */
  symbols: string[]

  /**
   * Loading state for symbols
   */
  loadingSymbols?: boolean

  /**
   * Whether prediction generation is in progress
   */
  isGenerating?: boolean
}

interface Emits {
  (e: 'update:symbol', value: string): void
  (e: 'update:timeframe', value: string): void
  (e: 'generate'): void
}

const props = withDefaults(defineProps<Props>(), {
  loadingSymbols: false,
  isGenerating: false
})

const emit = defineEmits<Emits>()

// Local reactive values for v-model
const localSymbol = ref(props.symbol)
const localTimeframe = ref(props.timeframe)

// Watch for external prop changes
watch(() => props.symbol, (newValue) => {
  localSymbol.value = newValue
})

watch(() => props.timeframe, (newValue) => {
  localTimeframe.value = newValue
})

// Emit changes to parent
watch(localSymbol, (newValue) => {
  emit('update:symbol', newValue)
})

watch(localTimeframe, (newValue) => {
  emit('update:timeframe', newValue)
})

function handleGenerate() {
  emit('generate')
}
</script>
