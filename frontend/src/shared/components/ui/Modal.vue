<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      v-motion
      :initial="{ opacity: 0 }"
      :enter="{ opacity: 1, transition: { duration: 250, ease: 'easeOut' } }"
      :leave="{ opacity: 0, transition: { duration: 200, ease: 'easeIn' } }"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      style="background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px);"
      @click.self="handleClose"
    >
      <div
        v-if="modelValue"
        v-motion
        :initial="{ opacity: 0, scale: 0.95, y: 20 }"
        :enter="{
          opacity: 1,
          scale: 1,
          y: 0,
          transition: {
            type: 'spring',
            stiffness: 300,
            damping: 24,
            mass: 0.5
          }
        }"
        :leave="{
          opacity: 0,
          scale: 0.98,
          y: -10,
          transition: { duration: 200, ease: 'easeIn' }
        }"
        class="modal-card w-full overflow-hidden"
        :class="sizeClass"
        @click.stop
      >
        <!-- Header -->
        <div class="modal-header relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <h2 class="text-xl font-bold text-text-primary">{{ title }}</h2>
              <p v-if="subtitle" class="mt-1 text-sm text-text-secondary">{{ subtitle }}</p>
            </div>
            <button
              @click="handleClose"
              v-motion
              :initial="{ scale: 1 }"
              :hovered="{ scale: 1.05 }"
              :tapped="{ scale: 0.95 }"
              class="w-9 h-9 flex items-center justify-center rounded-lg text-text-muted hover:bg-bg-hover hover:text-text-primary transition-colors ml-4"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Body -->
        <div class="modal-body relative z-10">
          <slot />
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="modal-footer relative z-10">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/outline'

interface Props {
  modelValue: boolean
  title: string
  subtitle?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  closeOnOutsideClick?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  closeOnOutsideClick: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const sizeClass = {
  sm: 'max-w-md',
  md: 'max-w-xl',
  lg: 'max-w-3xl',
  xl: 'max-w-5xl',
}[props.size]

const handleClose = () => {
  if (props.closeOnOutsideClick) {
    emit('update:modelValue', false)
  }
}
</script>

<style scoped>
/* Modal card - matches Card component styling */
.modal-card {
  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  transition: all var(--transition-base);
  max-height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
}

.modal-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--glow-primary);
}

.modal-header {
  flex-shrink: 0;
  padding: 1.75rem 2rem;
  border-bottom: 1px solid var(--border-default);
  background: linear-gradient(to bottom, rgba(35, 35, 35, 0.5), transparent);
}

.modal-body {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  min-height: 0;
}

/* Custom scrollbar for modal body */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--bg-hover);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

.modal-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--border-default);
  background: linear-gradient(to top, rgba(35, 35, 35, 0.5), transparent);
}
</style>
