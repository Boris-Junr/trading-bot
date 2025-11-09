<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Sidebar Navigation -->
    <aside class="fixed top-0 left-0 z-40 w-64 h-screen bg-white shadow-lg">
      <div class="h-full px-3 py-4 overflow-y-auto">
        <!-- Logo/Title -->
        <div class="flex items-center mb-6 px-3">
          <h1 class="text-2xl font-bold" style="color: var(--color-primary-600);">Trading Bot</h1>
        </div>

        <!-- Navigation Links -->
        <nav class="space-y-2">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center px-3 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200"
          >
            <span class="text-lg mr-3">{{ item.icon }}</span>
            <span class="font-medium">{{ item.name }}</span>
          </router-link>
        </nav>

        <!-- Footer Info -->
        <div class="absolute bottom-4 left-0 right-0 px-6 text-xs text-gray-500">
          <div>v1.0.0</div>
          <div class="mt-1">{{ connectionStatus }}</div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="ml-64 p-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const navItems = [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Portfolio', path: '/portfolio', icon: '💼' },
  { name: 'Backtests', path: '/backtests', icon: '📈' },
  { name: 'Predictions', path: '/predictions', icon: '🔮' },
  { name: 'Strategies', path: '/strategies', icon: '⚙️' },
  { name: 'Models', path: '/models', icon: '🤖' },
];

const connectionStatus = ref('🟢 Ready');

onMounted(() => {
  console.log('App mounted successfully');
});
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
