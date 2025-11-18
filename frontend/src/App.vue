<template>
  <div class="min-h-screen bg-bg-primary">
    <!-- Sidebar Navigation -->
    <Sidebar />

    <!-- Main Content -->
    <main class="main-content">
      <!-- Top Header -->
      <Header />

      <!-- Page Content -->
      <div class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- Notification Container (fixed position) -->
    <NotificationContainer />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import Sidebar from './shared/components/layout/Sidebar.vue'
import Header from './shared/components/layout/Header.vue'
import NotificationContainer from './shared/components/ui/NotificationContainer.vue'
import { useTaskManagerStore } from './stores/taskManager'
import { useTaskNotifications } from './composables/useTaskNotifications'

const taskManager = useTaskManagerStore()

// Enable task notifications
useTaskNotifications()

onMounted(async () => {
  console.log('🚀 Trading Bot - Premium UI loaded')

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
</style>
