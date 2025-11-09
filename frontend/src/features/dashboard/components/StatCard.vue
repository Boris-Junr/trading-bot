<template>
  <div class="stat-card group">
    <!-- Animated background glow -->
    <div class="stat-glow" :class="`glow-${variant}`"></div>

    <!-- Content -->
    <div class="relative z-10">
      <!-- Icon or custom header -->
      <div class="flex items-center justify-between mb-3">
        <span v-if="icon" class="text-2xl">{{ icon }}</span>
        <component
          v-else-if="iconComponent"
          :is="iconComponent"
          class="w-6 h-6"
          :class="iconColorClass"
        />
        <div
          v-if="trend"
          class="flex items-center gap-1 text-xs font-medium"
          :class="trend === 'up' ? 'positive' : 'negative'"
        >
          <component :is="trendIcon" class="w-4 h-4" />
        </div>
      </div>

      <!-- Label -->
      <div class="stat-label">{{ label }}</div>

      <!-- Value -->
      <div class="stat-value mt-2">{{ value }}</div>

      <!-- Change/Subtitle -->
      <div v-if="change" class="stat-change mt-2" :class="changeClass">
        {{ change }}
      </div>
    </div>

    <!-- Top border indicator -->
    <div class="stat-border" :class="`border-${variant}`"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/vue/24/solid'

interface Props {
  label: string
  value: string | number
  change?: string
  icon?: string
  iconComponent?: any
  variant?: 'primary' | 'success' | 'danger' | 'info' | 'warning'
  trend?: 'up' | 'down'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
})

const iconColorClass = computed(() => {
  const colors = {
    primary: 'text-accent-primary',
    success: 'text-accent-success',
    danger: 'text-accent-danger',
    info: 'text-accent-info',
    warning: 'text-accent-warning',
  }
  return colors[props.variant]
})

const changeClass = computed(() => {
  if (!props.change) return ''
  if (props.trend === 'up') return 'positive'
  if (props.trend === 'down') return 'negative'
  return 'neutral'
})

const trendIcon = computed(() => {
  return props.trend === 'up' ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
})
</script>

<style scoped>
.stat-glow {
  @apply absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300;
  @apply rounded-xl blur-xl;
}

.glow-primary {
  background: radial-gradient(circle at 50% 0%, var(--accent-primary) 0%, transparent 70%);
}

.glow-success {
  background: radial-gradient(circle at 50% 0%, var(--accent-success) 0%, transparent 70%);
}

.glow-danger {
  background: radial-gradient(circle at 50% 0%, var(--accent-danger) 0%, transparent 70%);
}

.glow-info {
  background: radial-gradient(circle at 50% 0%, var(--accent-info) 0%, transparent 70%);
}

.glow-warning {
  background: radial-gradient(circle at 50% 0%, var(--accent-warning) 0%, transparent 70%);
}

.stat-border {
  @apply absolute top-0 left-0 right-0 h-1 rounded-t-xl opacity-0 group-hover:opacity-100;
  @apply transition-opacity duration-300;
}

.border-primary {
  @apply bg-accent-primary;
}

.border-success {
  @apply bg-accent-success;
}

.border-danger {
  @apply bg-accent-danger;
}

.border-info {
  @apply bg-accent-info;
}

.border-warning {
  @apply bg-accent-warning;
}
</style>
