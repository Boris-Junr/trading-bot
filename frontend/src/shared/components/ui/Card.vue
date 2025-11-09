<template>
  <div :class="cardClasses">
    <!-- Header -->
    <div v-if="title || $slots.header" class="card-header">
      <slot name="header">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <component v-if="icon" :is="icon" class="w-5 h-5 text-accent-primary" />
            <h3 class="text-lg font-semibold">{{ title }}</h3>
          </div>
          <div v-if="$slots.actions" class="flex items-center gap-2">
            <slot name="actions" />
          </div>
        </div>
      </slot>
    </div>

    <!-- Content -->
    <div :class="contentClasses">
      <slot />
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-border-default">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title?: string
  icon?: any
  padding?: boolean
  hoverable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  padding: true,
  hoverable: false,
})

const cardClasses = computed(() => {
  const base = 'card'
  const hover = props.hoverable ? 'cursor-pointer hover:border-accent-primary hover:shadow-glow-primary' : ''
  return [base, hover].filter(Boolean).join(' ')
})

const contentClasses = computed(() => {
  return props.padding ? '' : '-mx-6 -my-4'
})
</script>
