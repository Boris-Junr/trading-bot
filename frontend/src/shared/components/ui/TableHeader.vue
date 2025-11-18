<template>
  <th
    class="px-4 py-3.5 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider"
    :class="align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : ''"
  >
    <slot />
  </th>
</template>

<script setup lang="ts">
interface Props {
  align?: 'left' | 'center' | 'right'
}

withDefaults(defineProps<Props>(), {
  align: 'left',
})
</script>
