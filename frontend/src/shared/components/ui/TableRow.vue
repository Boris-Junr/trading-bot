<template>
  <tr
    class="border-t border-border-default transition-colors duration-200"
    :class="[
      clickable ? 'cursor-pointer hover:bg-bg-hover' : '',
      highlighted ? 'bg-bg-hover' : ''
    ]"
    @click="handleClick"
  >
    <slot />
  </tr>
</template>

<script setup lang="ts">
interface Props {
  clickable?: boolean
  highlighted?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  clickable: false,
  highlighted: false,
})

const emit = defineEmits<{
  click: []
}>()

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>
