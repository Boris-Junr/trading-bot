<template>
  <div
    ref="cardRef"
    class="stat-card group"
    :style="cssVars"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- Animated background glow -->
    <div
      class="stat-glow"
      :style="glowStyle"
    ></div>

    <!-- Content -->
    <div class="relative z-10">
      <!-- Icon or custom header -->
      <div class="flex items-center justify-between mb-3">
        <span v-if="icon" class="text-2xl">{{ icon }}</span>
        <component
          v-else-if="iconComponent"
          :is="iconComponent"
          class="w-6 h-6"
          :class="iconColorClass"
        />
        <div
          v-if="trend"
          class="flex items-center gap-1 text-xs font-medium"
          :class="trend === 'up' ? 'positive' : 'negative'"
        >
          <component :is="trendIcon" class="w-4 h-4" />
        </div>
      </div>

      <!-- Label -->
      <div class="stat-label">{{ label }}</div>

      <!-- Value -->
      <div class="stat-value mt-2">{{ value }}</div>

      <!-- Change/Subtitle -->
      <div v-if="change" class="stat-change mt-2" :class="changeClass">
        {{ change }}
      </div>
    </div>

    <!-- Top border indicator -->
    <div class="stat-border" :class="`border-${variant}`"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/vue/24/solid'

interface Props {
  label: string
  value: string | number
  change?: string
  icon?: string
  iconComponent?: any
  variant?: 'primary' | 'success' | 'danger' | 'info' | 'warning'
  trend?: 'up' | 'down'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
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

  // Percentage position for background glow
  targetX.value = ((event.clientX - rect.left) / rect.width) * 100
  targetY.value = ((event.clientY - rect.top) / rect.height) * 100

  // Exact pixel position for border spotlight
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
    '--border-color': props.variant === 'danger' ? 'rgba(239, 68, 68, 0.6)' :
                      props.variant === 'info' ? 'rgba(59, 130, 246, 0.6)' :
                      props.variant === 'warning' ? 'rgba(251, 191, 36, 0.6)' :
                      'rgba(62, 207, 142, 0.6)'
  }
})

const glowStyle = computed(() => {
  const colors = {
    primary: 'rgba(62, 207, 142, 0.4)',
    success: 'rgba(62, 207, 142, 0.4)',
    danger: 'rgba(239, 68, 68, 0.4)',
    info: 'rgba(59, 130, 246, 0.4)',
    warning: 'rgba(251, 191, 36, 0.4)',
  }

  const x = mouseX.value
  const y = mouseY.value
  const color = colors[props.variant]

  return {
    background: `radial-gradient(circle 70px at ${x}% ${y}%, ${color}, transparent)`
  }
})

const iconColorClass = computed(() => {
  const colors = {
    primary: 'text-accent-primary',
    success: 'text-accent-success',
    danger: 'text-accent-danger',
    info: 'text-accent-info',
    warning: 'text-accent-warning',
  }
  return colors[props.variant]
})

const changeClass = computed(() => {
  if (!props.change) return ''
  if (props.trend === 'up') return 'positive'
  if (props.trend === 'down') return 'negative'
  return 'neutral'
})

const trendIcon = computed(() => {
  return props.trend === 'up' ? ArrowTrendingUpIcon : ArrowTrendingDownIcon
})
</script>

<style scoped>
/* Border spotlight using pseudo-elements */
.stat-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 0.75rem;
  padding: 2px;
  background: radial-gradient(
    70px circle at calc(var(--x, 0) * 1px) calc(var(--y, 0) * 1px),
    var(--border-color, rgba(62, 207, 142, 0.8)),
    transparent
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 300ms ease;
  pointer-events: none;
  filter: blur(10px);
  z-index: 1;
}

.group:hover.stat-card::before {
  opacity: 1;
}

.stat-card::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 0.75rem;
  padding: 1px;
  background: radial-gradient(
    40px circle at calc(var(--x, 0) * 1px) calc(var(--y, 0) * 1px),
    rgba(255, 255, 255, 1),
    transparent
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 300ms ease;
  pointer-events: none;
  z-index: 1;
}

.group:hover.stat-card::after {
  opacity: 1;
}

.stat-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 500ms cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 0.75rem;
  filter: blur(50px);
  pointer-events: none;
  z-index: 0;
}

.group:hover .stat-glow {
  opacity: 1;
}

.stat-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 0.25rem;
  border-radius: 0.75rem 0.75rem 0 0;
  opacity: 0;
  transition: opacity 300ms ease;
}

.group:hover .stat-border {
  opacity: 1;
}

.border-primary {
  background: var(--accent-primary);
}

.border-success {
  background: var(--accent-success);
}

.border-danger {
  background: var(--accent-danger);
}

.border-info {
  background: var(--accent-info);
}

.border-warning {
  background: var(--accent-warning);
}
</style>
