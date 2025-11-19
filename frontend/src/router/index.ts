import { createRouter, createWebHistory } from 'vue-router';
import { supabase } from '@/lib/supabase';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: {
        title: 'Login',
        description: 'Sign in to your account',
        requiresAuth: false
      },
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/SignupView.vue'),
      meta: {
        title: 'Sign Up',
        description: 'Create a new account',
        requiresAuth: false
      },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../features/dashboard/DashboardView.vue'),
      meta: {
        title: 'Dashboard',
        description: 'Real-time overview of your trading performance',
        requiresAuth: true
      },
    },
    {
      path: '/backtests',
      name: 'backtests',
      component: () => import('../views/BacktestsView.vue'),
      meta: {
        title: 'Backtests',
        description: 'Test strategies on historical data',
        requiresAuth: true
      },
    },
    {
      path: '/backtests/:id',
      name: 'backtest-detail',
      component: () => import('../views/BacktestDetailView.vue'),
      meta: {
        title: 'Backtest Details',
        description: 'Detailed backtest results and metrics',
        requiresAuth: true
      },
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: () => import('../views/PredictionsView.vue'),
      meta: {
        title: 'ML Predictions',
        description: 'Price predictions from machine learning models',
        requiresAuth: true
      },
    },
    {
      path: '/strategies',
      name: 'strategies',
      component: () => import('../views/StrategiesView.vue'),
      meta: {
        title: 'Strategies',
        description: 'Manage and configure your trading strategies',
        requiresAuth: true
      },
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      component: () => import('../views/PortfolioView.vue'),
      meta: {
        title: 'Portfolio',
        description: 'Detailed view of your positions and performance',
        requiresAuth: true
      },
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/ModelsView.vue'),
      meta: {
        title: 'ML Models',
        description: 'Manage and train machine learning models',
        requiresAuth: true
      },
    },
    {
      path: '/status',
      name: 'status',
      component: () => import('../views/StatusCenterView.vue'),
      meta: {
        title: 'System Status',
        description: 'Monitor system resources and task queue',
        requiresAuth: true
      },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: {
        title: 'Profile',
        description: 'Manage your account and API keys',
        requiresAuth: true
      },
    },
  ],
});

// Navigation guard for authentication and page title
router.beforeEach(async (to, _from, next) => {
  // Update page title
  document.title = to.meta.title ? `${to.meta.title} - Trading Bot` : 'Trading Bot';

  // Check if route requires authentication
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

  if (requiresAuth) {
    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      // Redirect to login if not authenticated
      next({ name: 'login', query: { redirect: to.fullPath } });
    } else {
      next();
    }
  } else {
    // Public route - allow access
    // If user is already logged in and trying to access login/signup, redirect to dashboard
    if ((to.name === 'login' || to.name === 'signup')) {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        next({ name: 'dashboard' });
        return;
      }
    }
    next();
  }
});

export default router;
