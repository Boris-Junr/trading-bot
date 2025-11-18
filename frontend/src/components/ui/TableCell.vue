<template>
  <td
    class="px-4 py-4 text-text-primary"
    :class="[
      align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : '',
      bold ? 'font-semibold' : '',
      mono ? 'font-mono' : ''
    ]"
  >
    <slot />
  </td>
</template>

<script setup lang="ts">
interface Props {
  align?: 'left' | 'center' | 'right'
  bold?: boolean
  mono?: boolean
}

withDefaults(defineProps<Props>(), {
  align: 'left',
  bold: false,
  mono: false,
})
</script>
