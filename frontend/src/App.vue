<template>
  <div class="min-h-screen bg-bg-primary">
    <!-- Sidebar Navigation -->
    <Sidebar />

    <!-- Main Content -->
    <main class="main-content">
      <div class="container-padding py-8">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './shared/components/layout/Sidebar.vue'

onMounted(() => {
  console.log('🚀 Trading Bot - Modern UI loaded')
})
</script>

<style scoped>
.main-content {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
}

/* Page transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
