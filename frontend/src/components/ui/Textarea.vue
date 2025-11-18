<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-semibold text-text-primary mb-2">
      {{ label }}
      <span v-if="required" class="text-accent-danger ml-0.5">*</span>
    </label>

    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      class="textarea-field w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-3 text-text-primary text-sm transition-all placeholder:text-text-muted focus:outline-none focus:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed resize-y"
      :class="error ? 'border-accent-danger focus:border-accent-danger' : ''"
    />

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
  modelValue: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  rows?: number
}

withDefaults(defineProps<Props>(), {
  disabled: false,
  required: false,
  rows: 4,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
/* No hover effect - only focus changes border to green */
.textarea-field:focus {
  border-color: var(--accent-primary) !important;
}

/* Custom scrollbar for textarea */
.textarea-field::-webkit-scrollbar {
  width: 6px;
}

.textarea-field::-webkit-scrollbar-track {
  background: transparent;
}

.textarea-field::-webkit-scrollbar-thumb {
  background: var(--bg-hover);
  border-radius: 3px;
}

.textarea-field::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
