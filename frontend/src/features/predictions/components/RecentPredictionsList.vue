<template>
  <div v-if="predictions.length > 0" class="collapsable-section">
    <div class="collapsable-header" @click="isCollapsed = !isCollapsed">
      <div class="collapsable-title">
        <ClockIcon class="header-icon" />
        <h3>Recent predictions</h3>
        <span class="prediction-count">{{ predictions.length }}</span>
      </div>
      <svg
        class="chevron-icon"
        :class="{ 'chevron-expanded': !isCollapsed }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </div>
    <transition name="collapse">
      <div v-show="!isCollapsed" class="collapsable-content">
        <div class="prediction-list">
          <div
            v-for="pred in predictions"
            :key="pred.id"
            class="prediction-item"
            @click="$emit('select', pred.id)"
          >
            <!-- Status Indicator -->
            <div class="prediction-status-indicator" :class="getStatusIndicatorClass(pred.status)"></div>

            <!-- Main Content -->
            <div class="prediction-content">
              <div class="prediction-header">
                <div class="prediction-title">
                  <span class="prediction-symbol">{{ pred.symbol }}</span>
                  <span class="prediction-timeframe">{{ pred.timeframe }}</span>
                </div>
                <div class="prediction-status" :class="getStatusBadgeClass(pred.status)">
                  <component :is="getStatusIcon(pred.status)" class="status-icon" :class="{ 'status-icon-spin': pred.status === 'running' }" />
                  <span class="status-text">{{ pred.status }}</span>
                </div>
              </div>

              <!-- Metadata -->
              <div class="prediction-meta">
                <div class="meta-item">
                  <svg class="meta-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                  </svg>
                  <span>{{ formatDate(pred.created_at, 'relative') }}</span>
                </div>
                <div v-if="pred.current_price" class="meta-item">
                  <svg class="meta-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"/>
                  </svg>
                  <span>{{ formatCurrency(pred.current_price) }}</span>
                </div>
              </div>
            </div>

            <!-- Chevron -->
            <div class="prediction-chevron">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue'
import { ClockIcon } from '@heroicons/vue/24/outline'
import { useFormatters } from '@/composables/useFormatters'

/**
 * Recent Predictions List Component
 *
 * Displays a collapsible list of recent predictions with status indicators.
 * Emits select event when user clicks on a prediction.
 */

interface PredictionListItem {
  id: string
  symbol: string
  timeframe: string
  status: 'completed' | 'running' | 'queued'
  created_at: string
  current_price?: number
}

interface Props {
  /**
   * List of recent predictions
   */
  predictions: PredictionListItem[]

  /**
   * Whether the list is initially collapsed
   */
  initiallyCollapsed?: boolean
}

interface Emits {
  (e: 'select', predictionId: string): void
}

const props = withDefaults(defineProps<Props>(), {
  initiallyCollapsed: true
})

const emit = defineEmits<Emits>()

const { formatDate, formatCurrency } = useFormatters()
const isCollapsed = ref(props.initiallyCollapsed)

/**
 * Get CSS class for status indicator (left border)
 */
function getStatusIndicatorClass(status: string): string {
  const classMap: Record<string, string> = {
    completed: 'status-completed',
    running: 'status-running',
    queued: 'status-queued'
  }
  return classMap[status] || 'status-queued'
}

/**
 * Get CSS class for status badge
 */
function getStatusBadgeClass(status: string): string {
  const classMap: Record<string, string> = {
    completed: 'status-badge-completed',
    running: 'status-badge-running',
    queued: 'status-badge-queued'
  }
  return classMap[status] || 'status-badge-queued'
}

/**
 * Get status icon component
 */
function getStatusIcon(status: string) {
  if (status === 'completed') {
    return h('svg', {
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        'd': 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
        'clip-rule': 'evenodd'
      })
    ])
  } else if (status === 'running') {
    return h('svg', {
      fill: 'none',
      viewBox: '0 0 24 24'
    }, [
      h('circle', {
        class: 'opacity-25',
        cx: '12',
        cy: '12',
        r: '10',
        stroke: 'currentColor',
        'stroke-width': '4'
      }),
      h('path', {
        class: 'opacity-75',
        fill: 'currentColor',
        d: 'M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
      })
    ])
  } else {
    return h('svg', {
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        'd': 'M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z',
        'clip-rule': 'evenodd'
      })
    ])
  }
}
</script>

<style scoped>
/* Recent Predictions List Styles */
.prediction-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 500px;
  overflow-y: auto;
}

.prediction-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
  border: 1px solid var(--glass-border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.prediction-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(62, 207, 142, 0.3);
  transform: translateX(4px);
}

/* Status Indicator (left border) */
.prediction-status-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 0.5rem 0 0 0.5rem;
}

.status-completed {
  background: var(--accent-success);
}

.status-running {
  background: var(--accent-warning);
}

.status-queued {
  background: var(--text-muted);
}

/* Content Area */
.prediction-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-left: 0.5rem;
}

.prediction-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.prediction-title {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.prediction-symbol {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.prediction-timeframe {
  font-size: 0.75rem;
  color: var(--text-muted);
  padding: 0.125rem 0.375rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.25rem;
}

/* Status Badge */
.prediction-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge-completed {
  background: rgba(62, 207, 142, 0.15);
  color: var(--accent-success);
}

.status-badge-running {
  background: rgba(255, 193, 7, 0.15);
  color: var(--accent-warning);
}

.status-badge-queued {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
}

.status-icon {
  width: 1rem;
  height: 1rem;
}

.status-icon-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-text {
  line-height: 1;
}

/* Metadata */
.prediction-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.meta-icon {
  width: 0.875rem;
  height: 0.875rem;
  opacity: 0.7;
}

/* Chevron */
.prediction-chevron {
  display: flex;
  align-items: center;
  color: var(--text-muted);
  opacity: 0.5;
  transition: all 0.2s ease;
}

.prediction-chevron svg {
  width: 1.25rem;
  height: 1.25rem;
}

.prediction-item:hover .prediction-chevron {
  opacity: 1;
  color: var(--accent-success);
  transform: translateX(4px);
}

/* Collapsable Section Styles */
.collapsable-section {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.collapsable-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.collapsable-header:hover {
  background: rgba(62, 207, 142, 0.05);
}

.collapsable-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--accent-success);
}

.collapsable-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.prediction-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.75rem;
  padding: 0 0.5rem;
  background: rgba(62, 207, 142, 0.15);
  color: var(--accent-success);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
}

.chevron-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}

.chevron-expanded {
  transform: rotate(180deg);
}

.collapsable-content {
  padding: 0 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid var(--glass-border);
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 600px;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
