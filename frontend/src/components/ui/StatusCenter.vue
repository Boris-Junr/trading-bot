<template>
  <Card class="status-center">
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-text-primary">Task Status</h3>
        <div class="flex items-center gap-2">
          <Badge variant="primary" size="sm">
            {{ runningTasks.length }} Running
          </Badge>
          <Badge v-if="queuedTasks.length > 0" variant="warning" size="sm">
            {{ queuedTasks.length }} Queued
          </Badge>
        </div>
      </div>

      <!-- Running Tasks -->
      <div v-if="runningTasks.length > 0" class="task-group">
        <div class="task-group-header">
          <svg class="w-4 h-4 text-success animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          <span class="text-sm font-medium text-text-secondary">Running</span>
        </div>

        <div class="task-list">
          <div
            v-for="task in runningTasks"
            :key="task.task_id"
            class="task-item running"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="task-type">{{ formatTaskType(task.task_type) }}</span>
                <Badge variant="success" size="xs">Running</Badge>
              </div>
              <div v-if="task.description" class="task-description">
                {{ task.description }}
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
            <div class="task-progress">
              <div class="progress-spinner"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Queued Tasks -->
      <div v-if="queuedTasks.length > 0" class="task-group">
        <div class="task-group-header">
          <svg class="w-4 h-4 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <span class="text-sm font-medium text-text-secondary">Queued</span>
        </div>

        <div class="task-list">
          <div
            v-for="task in queuedTasks"
            :key="task.task_id"
            class="task-item queued"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="task-type">{{ formatTaskType(task.task_type) }}</span>
                <Badge variant="warning" size="xs">
                  #{{ task.queue_position }} in queue
                </Badge>
              </div>
              <div v-if="task.description" class="task-description">
                {{ task.description }}
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
            <div class="queue-position">
              <span class="position-number">#{{ task.queue_position }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="runningTasks.length === 0 && queuedTasks.length === 0" class="empty-state">
        <svg class="w-12 h-12 text-text-muted opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="text-sm text-text-muted">No active tasks</p>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Card from './Card.vue'
import Badge from './Badge.vue'
import type { Task } from '@/types'

interface Props {
  runningTasks: Task[]
  queuedTasks: Task[]
}

const props = defineProps<Props>()

function formatTaskType(type: string): string {
  const typeMap: Record<string, string> = {
    'backtest': 'Backtest',
    'model_training': 'Model Training',
    'prediction': 'Prediction'
  }
  return typeMap[type] || type
}
</script>

<style scoped>
.status-center {
  min-width: 350px;
}

.task-group {
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  border: 1px solid var(--glass-border);
}

.task-group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--glass-border);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.375rem;
  border: 1px solid var(--glass-border);
  transition: all 0.2s ease;
}

.task-item:hover {
  background: rgba(0, 0, 0, 0.4);
  border-color: rgba(62, 207, 142, 0.3);
}

.task-item.running {
  border-left: 3px solid var(--success);
}

.task-item.queued {
  border-left: 3px solid var(--warning);
}

.task-type {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.task-description {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  font-style: italic;
}

.task-resources {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.resource-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.task-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
}

.progress-spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid rgba(62, 207, 142, 0.2);
  border-top-color: var(--success);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.queue-position {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 0.375rem;
}

.position-number {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--warning);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 0.5rem;
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
