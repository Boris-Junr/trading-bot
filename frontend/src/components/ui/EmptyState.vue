<template>
  <Card>
    <div class="empty-state" :class="containerClasses">
      <component :is="icon" class="empty-icon" />
      <h3 class="empty-title">{{ title }}</h3>
      <p class="empty-description">{{ description }}</p>
      <slot name="action">
        <Button v-if="actionText" @click="$emit('action')" :variant="actionVariant">
          {{ actionText }}
        </Button>
      </slot>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import Card from './Card.vue'
import Button from './Button.vue'

/**
 * Empty State Component
 *
 * Standardized empty state display with icon, title, description, and optional action.
 * Eliminates ~200 lines of duplicated empty state markup across 7+ components.
 */

interface Props {
  /**
   * Icon component to display (e.g., DocumentIcon, ChartIcon)
   */
  icon: Component

  /**
   * Main title text
   */
  title: string

  /**
   * Descriptive text explaining the empty state
   */
  description: string

  /**
   * Optional action button text
   */
  actionText?: string

  /**
   * Action button variant
   */
  actionVariant?: 'primary' | 'secondary' | 'danger'

  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * Center content vertically (adds extra padding)
   */
  centered?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  actionVariant: 'primary',
  size: 'md',
  centered: true
})

defineEmits<{
  action: []
}>()

const containerClasses = computed(() => {
  const classes = ['text-center']

  // Size-specific padding
  const sizeClasses = {
    sm: 'py-8',
    md: 'py-12',
    lg: 'py-16'
  }

  classes.push(sizeClasses[props.size])

  return classes.join(' ')
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.empty-title {
  color: var(--text-primary);
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.empty-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  max-width: 28rem;
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

/* Responsive icon size */
@media (max-width: 640px) {
  .empty-icon {
    width: 3rem;
    height: 3rem;
  }

  .empty-title {
    font-size: 1rem;
  }

  .empty-description {
    font-size: 0.8125rem;
  }
}
</style>
