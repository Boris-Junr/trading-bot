<template>
  <Card class="system-resources">
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-text-primary">System Resources</h3>
        <Badge :variant="isHealthy ? 'success' : 'warning'" size="sm">
          {{ isHealthy ? 'Healthy' : 'High Usage' }}
        </Badge>
      </div>

      <!-- CPU Usage -->
      <div class="resource-section">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-text-secondary">CPU</span>
          <span class="text-sm text-text-muted">
            {{ availableCores.toFixed(1) }} / {{ totalCores }} cores
          </span>
        </div>

        <div class="resource-bar-container">
          <!-- Background bar -->
          <div class="resource-bar-bg"></div>

          <!-- Buffer threshold indicator -->
          <div
            class="resource-threshold"
            :style="{ left: `${(1 - bufferPercent / 100) * 100}%` }"
          >
            <div class="threshold-line"></div>
            <span class="threshold-label">Buffer</span>
          </div>

          <!-- Usage bar -->
          <div
            class="resource-bar"
            :class="cpuBarClass"
            :style="{ width: `${cpuUsagePercent}%` }"
          >
            <span class="resource-percentage">{{ cpuUsagePercent.toFixed(0) }}%</span>
          </div>
        </div>

        <div class="flex justify-between mt-1 text-xs text-text-muted">
          <span>{{ cpuUsagePercent.toFixed(1) }}% used</span>
          <span>Min: {{ minCores.toFixed(1) }} cores</span>
        </div>
      </div>

      <!-- RAM Usage -->
      <div class="resource-section">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-text-secondary">RAM</span>
          <span class="text-sm text-text-muted">
            {{ availableRAM.toFixed(1) }} / {{ totalRAM.toFixed(1) }} GB
          </span>
        </div>

        <div class="resource-bar-container">
          <!-- Background bar -->
          <div class="resource-bar-bg"></div>

          <!-- Buffer threshold indicator -->
          <div
            class="resource-threshold"
            :style="{ left: `${(1 - bufferPercent / 100) * 100}%` }"
          >
            <div class="threshold-line"></div>
            <span class="threshold-label">Buffer</span>
          </div>

          <!-- Usage bar -->
          <div
            class="resource-bar"
            :class="ramBarClass"
            :style="{ width: `${ramUsagePercent}%` }"
          >
            <span class="resource-percentage">{{ ramUsagePercent.toFixed(0) }}%</span>
          </div>
        </div>

        <div class="flex justify-between mt-1 text-xs text-text-muted">
          <span>{{ ramUsagePercent.toFixed(1) }}% used</span>
          <span>Min: {{ minRAM.toFixed(1) }} GB</span>
        </div>
      </div>

      <!-- Status info -->
      <div v-if="!isHealthy" class="warning-message">
        <svg class="w-4 h-4 text-warning" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>
        <span class="text-sm">High resource usage - new tasks may be queued</span>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Card from './Card.vue'
import Badge from './Badge.vue'

interface Props {
  totalCores: number
  availableCores: number
  totalRAM: number
  availableRAM: number
  minCores: number
  minRAM: number
  bufferPercent: number
}

const props = defineProps<Props>()

// Computed
const cpuUsagePercent = computed(() => {
  if (props.totalCores === 0) return 0
  return ((props.totalCores - props.availableCores) / props.totalCores) * 100
})

const ramUsagePercent = computed(() => {
  if (props.totalRAM === 0) return 0
  return ((props.totalRAM - props.availableRAM) / props.totalRAM) * 100
})

const isHealthy = computed(() => {
  return cpuUsagePercent.value < 80 && ramUsagePercent.value < 80
})

const cpuBarClass = computed(() => {
  const usage = cpuUsagePercent.value
  if (usage >= 90) return 'bg-danger'
  if (usage >= 80) return 'bg-warning'
  return 'bg-success'
})

const ramBarClass = computed(() => {
  const usage = ramUsagePercent.value
  if (usage >= 90) return 'bg-danger'
  if (usage >= 80) return 'bg-warning'
  return 'bg-success'
})
</script>

<style scoped>
.system-resources {
  min-width: 300px;
}

.resource-section {
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  border: 1px solid var(--glass-border);
}

.resource-bar-container {
  position: relative;
  height: 2rem;
  border-radius: 0.375rem;
  overflow: visible;
}

.resource-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--glass-border);
  border-radius: 0.375rem;
}

.resource-bar {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  min-width: 3rem;
}

.bg-success {
  background: linear-gradient(90deg,
    rgba(62, 207, 142, 0.3) 0%,
    rgba(62, 207, 142, 0.5) 100%
  );
  border: 1px solid rgba(62, 207, 142, 0.6);
  box-shadow: 0 0 10px rgba(62, 207, 142, 0.3);
}

.bg-warning {
  background: linear-gradient(90deg,
    rgba(255, 193, 7, 0.3) 0%,
    rgba(255, 193, 7, 0.5) 100%
  );
  border: 1px solid rgba(255, 193, 7, 0.6);
  box-shadow: 0 0 10px rgba(255, 193, 7, 0.3);
}

.bg-danger {
  background: linear-gradient(90deg,
    rgba(239, 68, 68, 0.3) 0%,
    rgba(239, 68, 68, 0.5) 100%
  );
  border: 1px solid rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
}

.resource-percentage {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.resource-threshold {
  position: absolute;
  top: -0.5rem;
  bottom: -0.5rem;
  width: 2px;
  z-index: 10;
  pointer-events: none;
}

.threshold-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 2px;
  background: rgba(255, 193, 7, 0.6);
  border-radius: 1px;
}

.threshold-label {
  position: absolute;
  top: -1.5rem;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.625rem;
  color: rgba(255, 193, 7, 0.9);
  font-weight: 600;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.warning-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 0.375rem;
  color: var(--warning);
}
</style>
