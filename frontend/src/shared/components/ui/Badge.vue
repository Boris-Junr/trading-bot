<template>
  <span :class="badgeClasses">
    <span v-if="dot" class="status-dot" :class="dotColor"></span>
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'neutral'
  dot?: boolean
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  dot: false,
  size: 'md',
})

const badgeClasses = computed(() => {
  const base = 'badge'

  const variantClasses = {
    success: 'badge-success',
    danger: 'badge-danger',
    warning: 'badge-warning',
    info: 'badge-info',
    neutral: 'bg-bg-tertiary text-text-secondary border border-border-default'
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1'
  }

  return [
    base,
    variantClasses[props.variant],
    sizeClasses[props.size]
  ].join(' ')
})

const dotColor = computed(() => {
  return props.variant
})
</script>
