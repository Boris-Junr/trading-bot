<template>
  <aside class="sidebar fixed top-0 left-0 z-40 h-screen transition-transform">
    <div class="h-full flex flex-col bg-bg-secondary border-r border-border-default">
      <!-- Brand Header -->
      <div class="brand-header">
        <div class="brand-logo">
          <div class="logo-icon">
            <ChartBarSquareIcon class="w-6 h-6" />
          </div>
          <div class="brand-text">
            <div class="brand-name">TradingBot</div>
            <div class="brand-tagline">AI-Powered</div>
          </div>
        </div>
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span class="status-text">Live</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-6 space-y-1 overflow-y-auto scrollbar-hide">
        <div class="nav-section">
          <div class="nav-section-title">Overview</div>
          <router-link
            v-for="item in primaryNav"
            :key="item.path"
            :to="item.path"
            v-slot="{ isActive }"
            custom
          >
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              :class="[
                'nav-item',
                isActive ? 'nav-item-active' : 'nav-item-inactive'
              ]"
            >
              <div class="nav-item-content">
                <component :is="item.icon" class="nav-item-icon" />
                <span class="nav-item-label">{{ item.label }}</span>
              </div>
              <div v-if="item.badge" class="nav-badge">{{ item.badge }}</div>
            </a>
          </router-link>
        </div>

        <div class="nav-section mt-6">
          <div class="nav-section-title">Trading</div>
          <router-link
            v-for="item in tradingNav"
            :key="item.path"
            :to="item.path"
            v-slot="{ isActive }"
            custom
          >
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              :class="[
                'nav-item',
                isActive ? 'nav-item-active' : 'nav-item-inactive'
              ]"
            >
              <div class="nav-item-content">
                <component :is="item.icon" class="nav-item-icon" />
                <span class="nav-item-label">{{ item.label }}</span>
              </div>
            </a>
          </router-link>
        </div>
      </nav>

      <!-- Footer -->
      <div class="sidebar-footer">
        <div class="footer-stat">
          <div class="footer-stat-label">Version</div>
          <div class="footer-stat-value">Open Beta</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  ChartBarSquareIcon,
  ChartBarIcon,
  BriefcaseIcon,
  ChartPieIcon,
  SparklesIcon,
  CogIcon,
  CpuChipIcon,
} from '@heroicons/vue/24/outline'

const primaryNav = [
  { label: 'Dashboard', path: '/', icon: ChartBarIcon },
  { label: 'Portfolio', path: '/portfolio', icon: BriefcaseIcon, badge: '3' },
]

const tradingNav = [
  { label: 'Backtests', path: '/backtests', icon: ChartPieIcon },
  { label: 'Predictions', path: '/predictions', icon: SparklesIcon },
  { label: 'Strategies', path: '/strategies', icon: CogIcon },
  { label: 'Models', path: '/models', icon: CpuChipIcon },
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
}

/* Brand Header */
.brand-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-default);
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.logo-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.625rem;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-primary-dim));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-inverse);
  box-shadow: 0 4px 12px rgba(62, 207, 142, 0.2);
}

.brand-text {
  flex: 1;
}

.brand-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.brand-tagline {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(62, 207, 142, 0.08);
  border: 1px solid rgba(62, 207, 142, 0.15);
  border-radius: 0.5rem;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--accent-primary);
  box-shadow: 0 0 8px var(--accent-primary);
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent-primary);
}

/* Navigation */
.nav-section-title {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0 0.75rem;
  margin-bottom: 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  border-radius: 0.625rem;
  transition: all var(--transition-fast);
  cursor: pointer;
  margin-bottom: 0.25rem;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.nav-item-icon {
  width: 1.25rem;
  height: 1.25rem;
  transition: all var(--transition-fast);
}

.nav-item-label {
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-item-inactive {
  color: var(--text-secondary);
}

.nav-item-inactive:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}

.nav-item-inactive:hover .nav-item-icon {
  color: var(--accent-primary);
  transform: translateX(2px);
}

.nav-item-active {
  background: rgba(62, 207, 142, 0.12);
  color: var(--accent-primary);
  border: 1px solid rgba(62, 207, 142, 0.2);
}

.nav-item-active .nav-item-icon {
  color: var(--accent-primary);
}

.nav-badge {
  padding: 0.125rem 0.5rem;
  background: var(--accent-primary);
  color: var(--text-inverse);
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: 9999px;
  min-width: 1.25rem;
  text-align: center;
}

/* Footer */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-default);
  background: var(--bg-tertiary);
}

.footer-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
}

.footer-stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.footer-stat-value {
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-secondary);
}

.footer-divider {
  height: 1px;
  background: var(--border-default);
  margin: 0.25rem 0;
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
