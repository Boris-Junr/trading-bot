<template>
  <aside class="sidebar fixed top-0 left-0 z-40 h-screen transition-transform">
    <div class="h-full flex flex-col bg-bg-secondary border-r border-border-default backdrop-blur-glass">
      <!-- Terminal Header -->
      <div class="p-6 border-b border-border-default">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-3 h-3 rounded-full bg-accent-danger"></div>
          <div class="w-3 h-3 rounded-full bg-accent-warning"></div>
          <div class="w-3 h-3 rounded-full bg-accent-success"></div>
        </div>
        <div class="flex items-center gap-2 font-mono text-sm">
          <span class="text-accent-success">$</span>
          <span class="text-gradient font-bold text-lg">trading-bot</span>
        </div>
        <div class="mt-2 flex items-center gap-2 text-xs">
          <div class="status-dot success animate-pulse-glow"></div>
          <span class="text-text-secondary">Connected</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-hide">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          v-slot="{ isActive }"
          custom
        >
          <a
            :href="item.path"
            @click.prevent="$router.push(item.path)"
            :class="[
              'nav-item group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all',
              isActive
                ? 'bg-accent-primary/10 text-accent-primary border-l-2 border-accent-primary'
                : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'w-5 h-5 transition-colors',
                isActive ? 'text-accent-primary' : 'text-text-muted group-hover:text-accent-primary'
              ]"
            />
            <span class="font-medium">{{ item.label }}</span>
            <ChevronRightIcon
              v-if="isActive"
              class="w-4 h-4 ml-auto text-accent-primary"
            />
          </a>
        </router-link>
      </nav>

      <!-- Footer -->
      <div class="p-4 border-t border-border-default">
        <div class="text-xs text-text-muted space-y-1">
          <div class="flex items-center justify-between">
            <span>Version</span>
            <span class="font-mono text-accent-primary">v1.0.0</span>
          </div>
          <div class="flex items-center justify-between">
            <span>Uptime</span>
            <span class="font-mono">{{ uptime }}</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  ChartBarIcon,
  BriefcaseIcon,
  ChartPieIcon,
  SparklesIcon,
  CogIcon,
  CpuChipIcon,
  ChevronRightIcon,
} from '@heroicons/vue/24/outline'

const navItems = [
  { label: 'Dashboard', path: '/', icon: ChartBarIcon },
  { label: 'Portfolio', path: '/portfolio', icon: BriefcaseIcon },
  { label: 'Backtests', path: '/backtests', icon: ChartPieIcon },
  { label: 'Predictions', path: '/predictions', icon: SparklesIcon },
  { label: 'Strategies', path: '/strategies', icon: CogIcon },
  { label: 'Models', path: '/models', icon: CpuChipIcon },
]

const uptime = ref('00:00:00')

onMounted(() => {
  // Simple uptime counter (for demo)
  const startTime = Date.now()
  setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const hours = Math.floor(elapsed / 3600).toString().padStart(2, '0')
    const minutes = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0')
    const seconds = (elapsed % 60).toString().padStart(2, '0')
    uptime.value = `${hours}:${minutes}:${seconds}`
  }, 1000)
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
}

.nav-item {
  position: relative;
}
</style>
