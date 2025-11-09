import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: 'Dashboard' },
    },
    {
      path: '/backtests',
      name: 'backtests',
      component: () => import('../views/BacktestsView.vue'),
      meta: { title: 'Backtests' },
    },
    {
      path: '/backtests/:id',
      name: 'backtest-detail',
      component: () => import('../views/BacktestDetailView.vue'),
      meta: { title: 'Backtest Details' },
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: () => import('../views/PredictionsView.vue'),
      meta: { title: 'ML Predictions' },
    },
    {
      path: '/strategies',
      name: 'strategies',
      component: () => import('../views/StrategiesView.vue'),
      meta: { title: 'Strategies' },
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      component: () => import('../views/PortfolioView.vue'),
      meta: { title: 'Portfolio' },
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/ModelsView.vue'),
      meta: { title: 'ML Models' },
    },
  ],
});

// Navigation guard to update page title
router.beforeEach((to, _from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - Trading Bot` : 'Trading Bot';
  next();
});

export default router;
