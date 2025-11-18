<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="spinner"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-accent-danger/10 border border-accent-danger/20 rounded-xl text-accent-danger text-sm mb-8">
      {{ error }}
    </div>

    <!-- Strategies Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Empty State -->
      <div v-if="strategies.length === 0" class="col-span-2">
        <Card>
          <div class="text-center py-12">
            <CogIcon class="w-16 h-16 mx-auto text-text-muted mb-4" />
            <p class="text-text-primary font-medium mb-2">No Strategies Configured</p>
            <p class="text-text-secondary text-sm mb-6">Create your first trading strategy to get started</p>
            <Button @click="showCreateModal = true" variant="primary">
              Create Your First Strategy
            </Button>
          </div>
        </Card>
      </div>

      <!-- Strategy Cards -->
      <Card v-for="strategy in strategies" :key="strategy.id">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-lg font-semibold text-text-primary">{{ strategy.name }}</h3>
            <p class="text-sm text-text-secondary mt-1">{{ strategy.type }} strategy</p>
          </div>
          <Badge :variant="strategy.status === 'active' ? 'success' : 'secondary'" size="sm">
            {{ strategy.status.toUpperCase() }}
          </Badge>
        </div>

        <div class="space-y-3 mb-4">
          <div v-for="(value, key) in strategy.params" :key="key" class="flex justify-between text-sm">
            <span class="text-text-secondary">{{ formatParamKey(key) }}</span>
            <span class="font-medium text-text-primary">{{ formatParamValue(value) }}</span>
          </div>
        </div>

        <div class="flex gap-2">
          <Button variant="secondary" size="sm" class="flex-1">Edit</Button>
          <Button
            v-if="strategy.status === 'active'"
            @click="deactivate(strategy.id)"
            variant="secondary"
            size="sm"
            class="flex-1"
          >
            Deactivate
          </Button>
          <Button
            v-else
            @click="activate(strategy.id)"
            variant="primary"
            size="sm"
            class="flex-1"
          >
            Activate
          </Button>
        </div>
      </Card>

      <!-- Add New Placeholder -->
      <div
        v-if="strategies.length > 0"
        @click="showCreateModal = true"
        class="card border-2 border-dashed border-border-default hover:border-accent-primary cursor-pointer transition-all duration-200 flex items-center justify-center min-h-[200px]"
      >
        <div class="text-center py-8">
          <PlusIcon class="w-12 h-12 mx-auto text-text-muted mb-3" />
          <p class="text-text-primary font-medium">Create New Strategy</p>
        </div>
      </div>
    </div>

    <!-- Create Strategy Modal -->
    <Modal
      v-model="showCreateModal"
      title="Create New Strategy"
      subtitle="Configure a new trading strategy for your portfolio"
      size="md"
    >
      <div class="space-y-5">
        <Select v-model="newStrategy.type" label="Strategy Type">
          <option value="MLPredictive">ML Predictive</option>
          <option value="RSI">RSI</option>
          <option value="MACD">MACD</option>
          <option value="MovingAverage">Moving Average Crossover</option>
        </Select>

        <Input
          v-model="newStrategy.name"
          label="Strategy Name"
          placeholder="e.g., My ML Strategy"
        />

        <Textarea
          v-model="newStrategy.description"
          label="Description"
          placeholder="Describe your strategy..."
          :rows="4"
        />
      </div>

      <template #footer>
        <Button @click="showCreateModal = false" variant="secondary">
          Cancel
        </Button>
        <Button variant="primary" class="flex-1">
          Create Strategy
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Strategy } from '../types'
import api from '../services/api'
import { CogIcon, PlusIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Modal from '@/components/ui/Modal.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import Textarea from '@/components/ui/Textarea.vue'

const showCreateModal = ref(false)
const strategies = ref<Strategy[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const newStrategy = ref({
  type: 'MLPredictive',
  name: '',
  description: '',
})

onMounted(async () => {
  await fetchStrategies()
})

async function fetchStrategies() {
  loading.value = true
  error.value = null
  try {
    strategies.value = await api.getStrategies()
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch strategies'
    console.error('Failed to fetch strategies:', e)
  } finally {
    loading.value = false
  }
}

async function activate(id: string) {
  try {
    await api.activateStrategy(id)
    await fetchStrategies()
  } catch (e) {
    console.error('Failed to activate strategy:', e)
  }
}

async function deactivate(id: string) {
  try {
    await api.deactivateStrategy(id)
    await fetchStrategies()
  } catch (e) {
    console.error('Failed to deactivate strategy:', e)
  }
}

function formatParamKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatParamValue(value: any): string {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  return String(value)
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
