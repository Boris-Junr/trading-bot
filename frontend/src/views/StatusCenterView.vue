<template>
  <div class="status-center-view">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- System Resources Card -->
      <SystemResources
        :totalCores="taskManager.resources?.resources.cpu.total_cores || 0"
        :availableCores="taskManager.resources?.resources.cpu.available_cores || 0"
        :totalRAM="taskManager.resources?.resources.ram.total_gb || 0"
        :availableRAM="taskManager.resources?.resources.ram.available_gb || 0"
        :minCores="taskManager.resources?.resources.cpu.min_threshold_cores || 0"
        :minRAM="taskManager.resources?.resources.ram.min_threshold_gb || 0"
        :bufferPercent="taskManager.resources?.resources.buffer_percent || 5"
      />

      <!-- Resource Summary Stats -->
      <Card>
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-text-primary">Resource Summary</h3>

          <div class="grid grid-cols-2 gap-4">
            <!-- Total Tasks -->
            <div class="stat-item">
              <div class="stat-label">Total Tasks</div>
              <div class="stat-value">{{ totalTasks }}</div>
            </div>

            <!-- Running Tasks -->
            <div class="stat-item">
              <div class="stat-label">Running</div>
              <div class="stat-value text-success">{{ taskManager.runningTasks.length }}</div>
            </div>

            <!-- Queued Tasks -->
            <div class="stat-item">
              <div class="stat-label">Queued</div>
              <div class="stat-value text-warning">{{ taskManager.queuedTasks.length }}</div>
            </div>

            <!-- Completed Tasks -->
            <div class="stat-item">
              <div class="stat-label">Completed</div>
              <div class="stat-value text-text-muted">{{ taskManager.completedTasks.length }}</div>
            </div>
          </div>

          <!-- Resource Capacity -->
          <div class="capacity-info">
            <div class="capacity-item">
              <span class="capacity-label">CPU Capacity</span>
              <Badge :variant="cpuCapacityVariant" size="sm">
                {{ cpuCapacityText }}
              </Badge>
            </div>
            <div class="capacity-item">
              <span class="capacity-label">RAM Capacity</span>
              <Badge :variant="ramCapacityVariant" size="sm">
                {{ ramCapacityText }}
              </Badge>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Task Status -->
    <div class="mb-6">
      <StatusCenter
        :runningTasks="taskManager.runningTasks"
        :queuedTasks="taskManager.queuedTasks"
      />
    </div>

    <!-- Completed Tasks History -->
    <Card v-if="taskManager.completedTasks.length > 0">
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-text-primary">Recent Completed Tasks</h3>
          <Button
            v-if="taskManager.completedTasks.length > 0"
            variant="ghost"
            size="sm"
            @click="taskManager.clearCompletedTasks()"
          >
            Clear All
          </Button>
        </div>

        <div class="completed-tasks-list">
          <div
            v-for="task in recentCompletedTasks"
            :key="task.task_id"
            class="completed-task-item"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <svg class="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <span class="task-type">{{ formatTaskType(task.task_type) }}</span>
                <Badge variant="success" size="xs">Completed</Badge>
              </div>
              <div class="task-time text-xs text-text-muted">
                Completed {{ formatCompletedTime(task.completed_at || task.created_at) }}
              </div>
            </div>
            <div class="task-resources">
              <span class="resource-badge">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clip-rule="evenodd"/>
                </svg>
                {{ task.estimated_cpu_cores?.toFixed(1) }} cores
              </span>
              <span class="resource-badge">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/>
                  <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/>
                  <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"/>
                </svg>
                {{ task.estimated_ram_gb?.toFixed(1) }} GB
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTaskManagerStore } from '@/stores/taskManager'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import SystemResources from '@/components/ui/SystemResources.vue'
import StatusCenter from '@/components/ui/StatusCenter.vue'

const taskManager = useTaskManagerStore()

const totalTasks = computed(() => {
  return taskManager.runningTasks.length +
         taskManager.queuedTasks.length +
         taskManager.completedTasks.length
})

const recentCompletedTasks = computed(() => {
  return taskManager.completedTasks.slice(0, 10)
})

// CPU Capacity
const cpuUsagePercent = computed(() => {
  if (!taskManager.resources) return 0
  return taskManager.resources.resources.cpu.usage_percent || 0
})

const cpuCapacityVariant = computed(() => {
  const usage = cpuUsagePercent.value
  if (usage >= 90) return 'danger'
  if (usage >= 80) return 'warning'
  return 'success'
})

const cpuCapacityText = computed(() => {
  const usage = cpuUsagePercent.value
  if (usage >= 90) return 'Critical'
  if (usage >= 80) return 'High'
  if (usage >= 60) return 'Moderate'
  return 'Available'
})

// RAM Capacity
const ramUsagePercent = computed(() => {
  if (!taskManager.resources) return 0
  return taskManager.resources.resources.ram.usage_percent || 0
})

const ramCapacityVariant = computed(() => {
  const usage = ramUsagePercent.value
  if (usage >= 90) return 'danger'
  if (usage >= 80) return 'warning'
  return 'success'
})

const ramCapacityText = computed(() => {
  const usage = ramUsagePercent.value
  if (usage >= 90) return 'Critical'
  if (usage >= 80) return 'High'
  if (usage >= 60) return 'Moderate'
  return 'Available'
})

function formatTaskType(type: string): string {
  const typeMap: Record<string, string> = {
    'backtest': 'Backtest',
    'model_training': 'Model Training',
    'prediction': 'Prediction'
  }
  return typeMap[type] || type
}

function formatCompletedTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}
</script>

<style scoped>
.status-center-view {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-item {
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  border: 1px solid var(--glass-border);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.capacity-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--glass-border);
}

.capacity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.capacity-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.completed-tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.completed-task-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.375rem;
  border: 1px solid var(--glass-border);
  border-left: 3px solid var(--success);
  transition: all 0.2s ease;
}

.completed-task-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(62, 207, 142, 0.3);
}

.task-type {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.task-resources {
  display: flex;
  gap: 0.75rem;
}

.resource-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
