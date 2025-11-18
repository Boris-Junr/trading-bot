<template>
  <div :class="alertClasses">
    <svg v-if="showIcon" class="error-icon" fill="currentColor" viewBox="0 0 20 20">
      <path
        fill-rule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
        clip-rule="evenodd"
      />
    </svg>
    <div class="error-content">
      <h4 v-if="title" class="error-title">{{ title }}</h4>
      <p class="error-message">{{ message }}</p>
    </div>
    <button v-if="dismissable" @click="$emit('dismiss')" class="error-dismiss" type="button">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * Error Alert Component
 *
 * Standardized error display component with optional title and dismiss button.
 * Eliminates 150+ lines of duplicated error styling across 7+ components.
 */

interface Props {
  /**
   * Main error message (required)
   */
  message: string

  /**
   * Optional title for the error
   */
  title?: string

  /**
   * Error severity variant
   * - danger: Red error (default)
   * - warning: Yellow warning
   * - info: Blue information
   */
  variant?: 'danger' | 'warning' | 'info'

  /**
   * Show error icon
   */
  showIcon?: boolean

  /**
   * Show dismiss button
   */
  dismissable?: boolean

  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'danger',
  showIcon: true,
  dismissable: false,
  size: 'md'
})

defineEmits<{
  dismiss: []
}>()

const alertClasses = computed(() => {
  const baseClasses = ['error-alert', 'flex', 'items-start', 'gap-3', 'rounded-xl', 'border']

  // Variant-specific classes
  const variantClasses = {
    danger: ['bg-accent-danger/10', 'border-accent-danger/20', 'text-accent-danger'],
    warning: ['bg-yellow-500/10', 'border-yellow-500/20', 'text-yellow-600'],
    info: ['bg-blue-500/10', 'border-blue-500/20', 'text-blue-600']
  }

  // Size-specific classes
  const sizeClasses = {
    sm: ['p-3', 'text-xs'],
    md: ['p-4', 'text-sm'],
    lg: ['p-5', 'text-base']
  }

  return [...baseClasses, ...variantClasses[props.variant], ...sizeClasses[props.size]].join(' ')
})
</script>

<style scoped>
.error-icon {
  flex-shrink: 0;
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.125rem;
}

.error-content {
  flex: 1;
}

.error-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.error-message {
  opacity: 0.9;
}

.error-dismiss {
  flex-shrink: 0;
  padding: 0.25rem;
  border-radius: 0.375rem;
  transition: background-color 0.15s ease;
}

.error-dismiss:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.error-dismiss:focus {
  outline: none;
  box-shadow: 0 0 0 2px currentColor;
}
</style>
