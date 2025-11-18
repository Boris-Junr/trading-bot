import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../features/dashboard/DashboardView.vue'),
      meta: {
        title: 'Dashboard',
        description: 'Real-time overview of your trading performance'
      },
    },
    {
      path: '/backtests',
      name: 'backtests',
      component: () => import('../views/BacktestsView.vue'),
      meta: {
        title: 'Backtests',
        description: 'Test strategies on historical data'
      },
    },
    {
      path: '/backtests/:id',
      name: 'backtest-detail',
      component: () => import('../views/BacktestDetailView.vue'),
      meta: {
        title: 'Backtest Details',
        description: 'Detailed backtest results and metrics'
      },
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: () => import('../views/PredictionsView.vue'),
      meta: {
        title: 'ML Predictions',
        description: 'Price predictions from machine learning models'
      },
    },
    {
      path: '/strategies',
      name: 'strategies',
      component: () => import('../views/StrategiesView.vue'),
      meta: {
        title: 'Strategies',
        description: 'Manage and configure your trading strategies'
      },
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      component: () => import('../views/PortfolioView.vue'),
      meta: {
        title: 'Portfolio',
        description: 'Detailed view of your positions and performance'
      },
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/ModelsView.vue'),
      meta: {
        title: 'ML Models',
        description: 'Manage and train machine learning models'
      },
    },
    {
      path: '/status',
      name: 'status',
      component: () => import('../views/StatusCenterView.vue'),
      meta: {
        title: 'System Status',
        description: 'Monitor system resources and task queue'
      },
    },
  ],
});

// Navigation guard to update page title
router.beforeEach((to, _from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - Trading Bot` : 'Trading Bot';
  next();
});

export default router;
