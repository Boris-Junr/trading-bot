<template>
  <div>
    <!-- Header -->
    <div class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Trading Strategies</h1>
        <p class="mt-2 text-gray-600">Manage and configure your trading strategies</p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary">
        Create Strategy
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="text-gray-500">Loading strategies...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card bg-red-50 border border-red-200 mb-8">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Strategies Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-if="strategies.length === 0" class="col-span-2 card text-center py-12">
        <p class="text-gray-500">No strategies configured yet</p>
        <button @click="showCreateModal = true" class="btn-primary mt-4">
          Create Your First Strategy
        </button>
      </div>

      <!-- Strategy Cards -->
      <div v-for="strategy in strategies" :key="strategy.id" class="card">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{{ strategy.name }}</h3>
            <p class="text-sm text-gray-600 mt-1">{{ strategy.type }} strategy</p>
          </div>
          <span
            class="px-3 py-1 text-xs font-medium rounded-full"
            :class="strategy.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'"
          >
            {{ strategy.status.toUpperCase() }}
          </span>
        </div>

        <div class="space-y-3 mb-4">
          <div v-for="(value, key) in strategy.params" :key="key" class="flex justify-between text-sm">
            <span class="text-gray-600">{{ formatParamKey(key) }}</span>
            <span class="font-medium text-xs">{{ formatParamValue(value) }}</span>
          </div>
        </div>

        <div class="flex gap-2">
          <button class="btn-secondary flex-1 text-sm">Edit</button>
          <button
            v-if="strategy.status === 'active'"
            @click="deactivate(strategy.id)"
            class="btn-secondary flex-1 text-sm"
          >
            Deactivate
          </button>
          <button
            v-else
            @click="activate(strategy.id)"
            class="btn-primary flex-1 text-sm"
          >
            Activate
          </button>
        </div>
      </div>

      <!-- Add New Placeholder -->
      <div class="card border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:border-gray-400 transition-colors" @click="showCreateModal = true">
        <div class="text-center py-8">
          <svg class="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
          </svg>
          <p class="text-gray-600 font-medium">Create New Strategy</p>
        </div>
      </div>
    </div>

    <!-- Create Strategy Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-gray-900">Create New Strategy</h2>
            <button @click="showCreateModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Strategy Type</label>
              <select class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option>ML Predictive</option>
                <option>RSI</option>
                <option>MACD</option>
                <option>Moving Average Crossover</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Strategy Name</label>
              <input
                type="text"
                placeholder="My Strategy"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                placeholder="Describe your strategy..."
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg"
              ></textarea>
            </div>
          </div>

          <div class="mt-6 flex gap-3">
            <button class="btn-primary flex-1">Create Strategy</button>
            <button @click="showCreateModal = false" class="btn-secondary">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { Strategy } from '../types';
import api from '../services/api';

const showCreateModal = ref(false);
const strategies = ref<Strategy[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  await fetchStrategies();
});

async function fetchStrategies() {
  loading.value = true;
  error.value = null;
  try {
    strategies.value = await api.getStrategies();
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch strategies';
    console.error('Failed to fetch strategies:', e);
  } finally {
    loading.value = false;
  }
}

async function activate(id: string) {
  try {
    await api.activateStrategy(id);
    await fetchStrategies();
  } catch (e) {
    console.error('Failed to activate strategy:', e);
  }
}

async function deactivate(id: string) {
  try {
    await api.deactivateStrategy(id);
    await fetchStrategies();
  } catch (e) {
    console.error('Failed to deactivate strategy:', e);
  }
}

function formatParamKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatParamValue(value: any): string {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  return String(value);
}
</script>
