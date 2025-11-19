<template>
  <div class="min-h-screen bg-bg-primary">
    <!-- Show layout only for authenticated routes -->
    <template v-if="isAuthenticatedRoute && !authLoading">
      <!-- Sidebar Navigation -->
      <Sidebar />

      <!-- Main Content -->
      <main class="main-content">
        <!-- Top Header -->
        <Header />

        <!-- Page Content -->
        <div class="page-container">
          <router-view v-slot="{ Component, route }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="route.path" />
            </transition>
          </router-view>
        </div>
      </main>

      <!-- Notification Container (fixed position) -->
      <NotificationContainer />
    </template>

    <!-- Public routes (login/signup) without layout -->
    <template v-else-if="!authLoading">
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.path" />
      </router-view>
    </template>

    <!-- Loading state -->
    <div v-else class="loading-container">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/layout/Sidebar.vue'
import Header from './components/layout/Header.vue'
import NotificationContainer from './components/ui/NotificationContainer.vue'
import { useTaskManagerStore } from './stores/taskManager'
import { useTaskNotifications } from './composables/useTaskNotifications'
import { useAuth } from './composables/useAuth'

const route = useRoute()
const taskManager = useTaskManagerStore()
const { initialize, loading: authLoading } = useAuth()

// Check if current route requires authentication
const isAuthenticatedRoute = computed(() => {
  return route.matched.some((record) => record.meta.requiresAuth)
})

// Enable task notifications
useTaskNotifications()

onMounted(async () => {
  console.log('🚀 Trading Bot - Premium UI loaded')

  // Initialize authentication
  await initialize()
  console.log('🔐 Authentication initialized')

  // Start monitoring system resources and tasks (waits for initial data)
  await taskManager.startMonitoring(2000)
  console.log('📊 Task monitoring started with initial data loaded')
})

onUnmounted(() => {
  // Stop monitoring when app is destroyed
  taskManager.stopMonitoring()
  console.log('📊 Task monitoring stopped')
})
</script>

<style scoped>
.main-content {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
}

.page-container {
  padding: 2rem;
  max-width: 1920px;
  margin: 0 auto;
}

/* Page transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Loading spinner */
.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  gap: 1rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(102, 126, 234, 0.1);
  border-left-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
