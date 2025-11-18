<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-semibold text-text-primary mb-2">
      {{ label }}
      <span v-if="required" class="text-accent-danger ml-0.5">*</span>
    </label>

    <div class="relative">
      <input
        :type="type"
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        class="input-field w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-2.5 text-text-primary text-sm transition-all placeholder:text-text-muted focus:outline-none focus:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed"
        :class="[
          error ? 'border-accent-danger focus:border-accent-danger' : '',
          icon ? 'pl-10' : ''
        ]"
      />

      <div v-if="icon" class="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
        <component :is="icon" class="w-5 h-5" />
      </div>
    </div>

    <p v-if="hint && !error" class="mt-2 text-xs text-text-secondary leading-relaxed">
      {{ hint }}
    </p>

    <p v-if="error" class="mt-2 text-xs text-accent-danger font-medium flex items-center gap-1">
      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
      </svg>
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string | number
  type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'time' | 'datetime-local'
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  icon?: any
}

withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  required: false,
})

defineEmits<{
  'update:modelValue': [value: string | number]
}>()
</script>

<style scoped>
/* No hover effect - only focus changes border to green */
.input-field:focus {
  border-color: var(--accent-primary) !important;
}
</style>
