<template>
  <div
    ref="cardRef"
    :class="cardClasses"
    :style="cssVars"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- Animated background glow -->
    <div class="card-glow" :style="glowStyle"></div>

    <!-- Header -->
    <div v-if="title || $slots.header" class="card-header relative z-10">
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
    <div :class="contentClasses" class="relative z-10">
      <slot />
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-border-default relative z-10">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'

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

// Mouse tracking for glow effect with inertia
const cardRef = ref<HTMLElement | null>(null)
const targetX = ref(50)
const targetY = ref(50)
const mouseX = ref(50)
const mouseY = ref(50)
const prevX = ref(50)
const prevY = ref(50)
const velocityX = ref(0)
const velocityY = ref(0)

// Exact pixel position for border spotlight
const mousePixelX = ref(0)
const mousePixelY = ref(0)

let animationFrame: number | null = null

const lerp = (start: number, end: number, factor: number) => {
  return start + (end - start) * factor
}

const animate = () => {
  // Store previous position
  prevX.value = mouseX.value
  prevY.value = mouseY.value

  // Smooth interpolation with inertia
  mouseX.value = lerp(mouseX.value, targetX.value, 0.12)
  mouseY.value = lerp(mouseY.value, targetY.value, 0.12)

  // Calculate velocity for bubble deformation
  velocityX.value = mouseX.value - prevX.value
  velocityY.value = mouseY.value - prevY.value

  // Continue animation if not close enough to target
  const dx = Math.abs(targetX.value - mouseX.value)
  const dy = Math.abs(targetY.value - mouseY.value)

  if (dx > 0.1 || dy > 0.1) {
    animationFrame = requestAnimationFrame(animate)
  } else {
    animationFrame = null
    // Reset velocity when stopped
    velocityX.value = 0
    velocityY.value = 0
  }
}

const handleMouseMove = (event: MouseEvent) => {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()

  // Percentage position for background glow (with inertia)
  targetX.value = ((event.clientX - rect.left) / rect.width) * 100
  targetY.value = ((event.clientY - rect.top) / rect.height) * 100

  // Exact pixel position for border spotlight (no inertia - instant update)
  mousePixelX.value = event.clientX - rect.left
  mousePixelY.value = event.clientY - rect.top

  // Always ensure animation is running
  if (animationFrame === null) {
    animationFrame = requestAnimationFrame(animate)
  }
}

const handleMouseLeave = () => {
  // Don't reset position - let opacity handle the fade out
}

onBeforeUnmount(() => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
})

const cssVars = computed(() => {
  return {
    '--x': mousePixelX.value,
    '--y': mousePixelY.value,
  }
})

const glowStyle = computed(() => {
  const x = mouseX.value
  const y = mouseY.value

  return {
    background: `radial-gradient(circle 80px at ${x}% ${y}%, rgba(62, 207, 142, 0.4), transparent)`
  }
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
