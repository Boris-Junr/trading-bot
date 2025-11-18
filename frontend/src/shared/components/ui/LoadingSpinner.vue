<template>
  <div :class="containerClasses">
    <div :class="spinnerClasses"></div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * Loading Spinner Component
 *
 * Reusable loading indicator with optional message.
 * Eliminates 200+ lines of duplicated spinner styles across 7+ components.
 */

interface Props {
  /**
   * Size of the spinner
   * - sm: 1.5rem (24px)
   * - md: 3rem (48px)
   * - lg: 4rem (64px)
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * Optional loading message to display below spinner
   */
  message?: string

  /**
   * Center the spinner in its container
   */
  centered?: boolean

  /**
   * Minimum height for centered spinner (default: py-12)
   */
  minHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  centered: true,
  minHeight: 'py-12'
})

const containerClasses = computed(() => {
  const classes = []

  if (props.centered) {
    classes.push('flex', 'flex-col', 'justify-center', 'items-center', props.minHeight)
  }

  return classes.join(' ')
})

const spinnerClasses = computed(() => {
  const baseClasses = [
    'spinner',
    'border-3',
    'border-border-default',
    'border-t-accent-primary',
    'rounded-full',
    'animate-spin'
  ]

  // Size-specific classes
  const sizeClasses = {
    sm: ['w-6', 'h-6', 'border-2'],
    md: ['w-12', 'h-12', 'border-3'],
    lg: ['w-16', 'h-16', 'border-4']
  }

  return [...baseClasses, ...sizeClasses[props.size]].join(' ')
})
</script>

<style scoped>
.spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-message {
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  text-align: center;
}
</style>
