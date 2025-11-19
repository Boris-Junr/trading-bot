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

        <!-- Settings / Profile -->
        <router-link to="/profile" class="header-action-btn" :class="{ 'active': route.name === 'profile' }">
          <Cog6ToothIcon class="w-5 h-5" />
        </router-link>

        <!-- Divider -->
        <div class="header-divider"></div>

        <!-- User Profile Dropdown -->
        <div class="user-profile-container" ref="dropdownRef">
          <div
            class="flex items-center gap-3 cursor-pointer hover:bg-bg-hover rounded-lg px-3 py-2 transition-all"
            @click="toggleDropdown"
          >
            <div class="user-avatar">
              <UserIcon class="w-5 h-5 text-accent-primary" />
            </div>
            <div class="hidden md:block">
              <div class="text-sm font-medium text-text-primary">
                {{ user?.email?.split('@')[0] || 'User' }}
              </div>
              <div class="text-xs text-text-secondary">
                {{ user?.email ? 'Authenticated' : 'Loading...' }}
              </div>
            </div>
            <ChevronDownIcon
              class="w-4 h-4 text-text-muted transition-transform"
              :class="{ 'rotate-180': isDropdownOpen }"
            />
          </div>

          <!-- Dropdown Menu -->
          <div v-if="isDropdownOpen" class="user-dropdown">
            <div class="dropdown-section">
              <div class="dropdown-label">User Information</div>
              <div class="user-info-item">
                <span class="info-label">Email:</span>
                <span class="info-value">{{ user?.email || 'Not available' }}</span>
              </div>
              <div class="user-info-item">
                <span class="info-label">User ID:</span>
                <span class="info-value font-mono text-xs">{{ user?.id || 'Not available' }}</span>
              </div>
            </div>

            <div class="dropdown-divider"></div>

            <button @click="handleLogout" class="dropdown-item danger">
              <ArrowLeftOnRectangleIcon class="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  MagnifyingGlassIcon,
  BellIcon,
  CpuChipIcon,
  Cog6ToothIcon,
  UserIcon,
  ChevronDownIcon,
  ArrowLeftOnRectangleIcon,
} from '@heroicons/vue/24/outline'
import Badge from '../ui/Badge.vue'
import { useTaskManagerStore } from '../../stores/taskManager'
import { useAuth } from '../../composables/useAuth'
import { supabase } from '../../lib/supabase'

const route = useRoute()
const router = useRouter()
const taskManager = useTaskManagerStore()
const { user } = useAuth()
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

// User dropdown
const isDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const handleLogout = async () => {
  try {
    await supabase.auth.signOut()
    closeDropdown()
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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

/* User Profile Dropdown */
.user-profile-container {
  position: relative;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 280px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 0.75rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  z-index: 50;
  animation: dropdownSlide 0.2s ease-out;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-section {
  padding: 1rem;
}

.dropdown-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.user-info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.user-info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.info-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  word-break: break-all;
}

.dropdown-divider {
  height: 1px;
  background: var(--border-default);
  margin: 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.dropdown-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.dropdown-item.danger {
  color: var(--accent-danger);
}

.dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--accent-danger);
}
</style>
