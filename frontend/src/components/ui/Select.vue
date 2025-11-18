<template>
  <div class="w-full" ref="selectRef">
    <label v-if="label" class="block text-sm font-semibold text-text-primary mb-2">
      {{ label }}
      <span v-if="required" class="text-accent-danger ml-0.5">*</span>
    </label>

    <div class="relative">
      <button
        type="button"
        @click="toggleDropdown"
        :disabled="disabled"
        class="select-button w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-2.5 text-text-primary text-sm transition-all focus:outline-none focus:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-left flex items-center justify-between"
        :class="[
          error ? 'border-accent-danger focus:border-accent-danger' : '',
          isOpen ? 'border-accent-primary' : ''
        ]"
      >
        <span :class="selectedLabel ? 'text-text-primary' : 'text-text-muted'">
          {{ selectedLabel || placeholder || 'Select an option' }}
        </span>
        <ChevronDownIcon
          class="w-5 h-5 text-text-muted transition-transform"
          :class="isOpen ? 'rotate-180' : ''"
        />
      </button>

      <!-- Custom Dropdown with Teleport to avoid overflow clipping -->
      <Teleport to="body">
        <div
          v-if="isOpen"
          v-motion
          :initial="{ opacity: 0, y: -12, scale: 0.95 }"
          :enter="{
            opacity: 1,
            y: 0,
            scale: 1,
            transition: {
              type: 'spring',
              stiffness: 400,
              damping: 28,
              mass: 0.4
            }
          }"
          :leave="{
            opacity: 0,
            y: -8,
            scale: 0.98,
            transition: { duration: 150, ease: 'easeOut' }
          }"
          ref="dropdownRef"
          class="dropdown-menu fixed z-50"
          :style="dropdownStyle"
        >
          <div class="dropdown-content">
            <div
              v-for="option in options"
              :key="option.value"
              @click="selectOption(option)"
              class="dropdown-item"
              :class="{
                'dropdown-item-selected': option.value === modelValue,
                'dropdown-item-disabled': option.disabled
              }"
            >
              <span>{{ option.label }}</span>
              <CheckIcon v-if="option.value === modelValue" class="w-4 h-4 text-accent-primary" />
            </div>
          </div>
        </div>
      </Teleport>
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
import { ref, computed, onMounted, onBeforeUnmount, onUpdated, useSlots, nextTick } from 'vue'
import { ChevronDownIcon, CheckIcon } from '@heroicons/vue/24/outline'

interface Props {
  modelValue: string | number
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
}

interface Option {
  value: string | number
  label: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const slots = useSlots()
const selectRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const options = ref<Option[]>([])
const dropdownStyle = ref({})

// Parse options from slot on mount
onMounted(() => {
  parseOptions()
})

// Only re-parse options when the slot content actually changes
// Using a watcher would be better here, but we keep onUpdated with safeguard
let lastOptionsCount = 0
onUpdated(() => {
  // Use nextTick to ensure DOM is fully updated before parsing
  nextTick(() => {
    const defaultSlot = slots.default?.()
    const currentCount = defaultSlot?.length || 0

    // Only re-parse if the number of slot children changed
    if (currentCount !== lastOptionsCount) {
      lastOptionsCount = currentCount
      parseOptions()
    }
  })
})

const parseOptions = () => {
  const defaultSlot = slots.default?.()
  if (!defaultSlot) return

  const parsedOptions: Option[] = []

  defaultSlot.forEach((vnode: any) => {
    // Handle both direct option elements and fragments
    if (vnode.type === 'option') {
      const value = vnode.props?.value ?? vnode.children
      const label = typeof vnode.children === 'string' ? vnode.children : vnode.children?.[0] ?? value
      const disabled = vnode.props?.disabled !== undefined

      parsedOptions.push({ value, label, disabled })
    } else if (vnode.type === Symbol.for('v-fgt')) {
      // Handle fragment (v-for, v-if creates fragments)
      const children = vnode.children as any[]
      children?.forEach((child: any) => {
        if (child.type === 'option') {
          const value = child.props?.value ?? child.children
          const label = typeof child.children === 'string' ? child.children : child.children?.[0] ?? value
          const disabled = child.props?.disabled !== undefined

          parsedOptions.push({ value, label, disabled })
        }
      })
    }
  })

  options.value = parsedOptions
}

const selectedLabel = computed(() => {
  const selected = options.value.find(opt => opt.value === props.modelValue)
  return selected?.label || ''
})

const updateDropdownPosition = () => {
  if (!selectRef.value) return
  const rect = selectRef.value.getBoundingClientRect()
  dropdownStyle.value = {
    top: `${rect.bottom + 8}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

const toggleDropdown = async () => {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
    if (isOpen.value) {
      await nextTick()
      updateDropdownPosition()
    }
  }
}

const selectOption = (option: Option) => {
  if (!option.disabled) {
    emit('update:modelValue', option.value)
    isOpen.value = false
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node

  // Check if click is outside both the select button AND the dropdown menu
  const isOutsideSelect = selectRef.value && !selectRef.value.contains(target)
  const isOutsideDropdown = dropdownRef.value && !dropdownRef.value.contains(target)

  if (isOutsideSelect && isOutsideDropdown) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', updateDropdownPosition, true)
  window.addEventListener('resize', updateDropdownPosition)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
})
</script>

<style scoped>
/* No hover effect - only focus/open changes border to green */
.select-button:focus {
  border-color: var(--accent-primary) !important;
}

/* Dropdown Menu */
.dropdown-menu {
  max-height: 16rem;
  overflow: hidden;
}

.dropdown-content {
  background: #232323;
  border: 2px solid var(--accent-primary);
  border-radius: 0.75rem;
  overflow-y: auto;
  max-height: 16rem;
  opacity: 1;
}

/* Custom scrollbar for dropdown */
.dropdown-content::-webkit-scrollbar {
  width: 6px;
}

.dropdown-content::-webkit-scrollbar-track {
  background: #161616;
}

.dropdown-content::-webkit-scrollbar-thumb {
  background: #2a2a2a;
  border-radius: 3px;
}

.dropdown-content::-webkit-scrollbar-thumb:hover {
  background: #6e7681;
}

/* Dropdown Items */
.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-primary);
  font-size: 0.875rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: #232323;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover:not(.dropdown-item-disabled) {
  background: #2a2a2a;
  color: var(--accent-primary);
}

.dropdown-item-selected {
  background: #161616;
  color: var(--accent-primary);
  font-weight: 500;
}

.dropdown-item-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
