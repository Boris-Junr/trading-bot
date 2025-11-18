<template>
  <header class="top-header">
    <div class="header-content">
      <!-- Left: Page Title & Description -->
      <div>
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-text-primary">{{ pageTitle }}</h1>
          <Badge v-if="env" variant="success" size="sm">{{ env }}</Badge>
        </div>
        <p v-if="pageDescription" class="mt-1 text-sm text-text-secondary">{{ pageDescription }}</p>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-3">
        <!-- Search -->
        <button class="header-action-btn">
          <MagnifyingGlassIcon class="w-5 h-5" />
        </button>

        <!-- System Status (link to status page) -->
        <router-link to="/status" class="header-action-btn relative" :class="{ 'active': route.name === 'status' }">
          <CpuChipIcon class="w-5 h-5" />
          <span v-if="hasActiveTasks" class="notification-badge">{{ activeTasksCount }}</span>
        </router-link>

        <!-- Notifications -->
        <button class="header-action-btn relative">
          <BellIcon class="w-5 h-5" />
        </button>

        <!-- Settings -->
        <button class="header-action-btn">
          <Cog6ToothIcon class="w-5 h-5" />
        </button>

        <!-- Divider -->
        <div class="header-divider"></div>

        <!-- User Profile -->
        <div class="flex items-center gap-3 cursor-pointer hover:bg-bg-hover rounded-lg px-3 py-2 transition-all">
          <div class="user-avatar">
            <UserIcon class="w-5 h-5 text-accent-primary" />
          </div>
          <div class="hidden md:block">
            <div class="text-sm font-medium text-text-primary">Trading Bot</div>
            <div class="text-xs text-text-secondary">Pro Plan</div>
          </div>
          <ChevronDownIcon class="w-4 h-4 text-text-muted" />
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  MagnifyingGlassIcon,
  BellIcon,
  CpuChipIcon,
  Cog6ToothIcon,
  UserIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'
import Badge from '../ui/Badge.vue'
import { useTaskManagerStore } from '@/stores/taskManager'

const route = useRoute()
const taskManager = useTaskManagerStore()
const env = import.meta.env.MODE === 'development' ? 'DEV' : 'LIVE'

const pageTitle = computed(() => (route.meta.title as string) || 'Trading Bot')
const pageDescription = computed(() => route.meta.description as string | undefined)

// Active tasks count for badge
const hasActiveTasks = computed(() => {
  return taskManager.hasQueuedTasks || taskManager.hasRunningTasks
})

const activeTasksCount = computed(() => {
  return taskManager.queuedTasks.length + taskManager.runningTasks.length
})
</script>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-default);
  backdrop-filter: blur(12px);
  background: rgba(28, 28, 28, 0.8);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  max-width: 100%;
}

.header-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.header-action-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  background: var(--accent-danger);
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--bg-primary);
}

.header-divider {
  width: 1px;
  height: 2rem;
  background: var(--border-default);
}

.user-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-primary-dim));
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--bg-tertiary);
}

/* Active state for router-link */
.header-action-btn.active {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
</style>
