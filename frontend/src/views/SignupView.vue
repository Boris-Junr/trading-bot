<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- Logo/Brand -->
      <div class="brand-section">
        <div class="brand-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </div>
        <h1 class="brand-title">Create Account</h1>
        <p class="brand-subtitle">Get started with Trading Bot</p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSignup" class="auth-form">
        <div class="form-group">
          <label for="fullName">Full Name</label>
          <input
            id="fullName"
            v-model="fullName"
            type="text"
            placeholder="John Doe"
            :disabled="loading"
            autocomplete="name"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="your@email.com"
            :disabled="loading"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="Create a password (min. 6 characters)"
            minlength="6"
            :disabled="loading"
            autocomplete="new-password"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your password"
            :disabled="loading"
            autocomplete="new-password"
          />
        </div>

        <div v-if="error" class="error-message">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <span>{{ error }}</span>
        </div>

        <div v-if="success" class="success-message">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ success }}</span>
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="!loading">Create Account</span>
          <span v-else class="loading-spinner">
            <svg class="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Creating account...
          </span>
        </button>
      </form>

      <!-- Divider -->
      <div class="divider">
        <span>Already have an account?</span>
      </div>

      <!-- Sign in link -->
      <router-link to="/login" class="btn-secondary">
        Sign in instead
      </router-link>
    </div>

    <!-- Background decoration -->
    <div class="bg-decoration">
      <div class="decoration-circle circle-1"></div>
      <div class="decoration-circle circle-2"></div>
      <div class="decoration-circle circle-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { signUp } = useAuth()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

const handleSignup = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  // Validate passwords match
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    loading.value = false
    return
  }

  // Validate password length
  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    loading.value = false
    return
  }

  try {
    await signUp(email.value, password.value, fullName.value)
    success.value = 'Account created successfully! Redirecting...'
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err: any) {
    error.value = err.message || 'Failed to create account'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg-primary);
  padding: 2rem;
  overflow: hidden;
}

.auth-card {
  position: relative;
  z-index: 10;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  padding: 3rem 2.5rem;
  border-radius: 1rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 420px;
  backdrop-filter: blur(10px);
}

/* Brand Section */
.brand-section {
  text-align: center;
  margin-bottom: 2.5rem;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-primary-dim));
  border-radius: 1rem;
  color: white;
  margin-bottom: 1.5rem;
}

.brand-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.brand-subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9375rem;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

label {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--text-primary);
}

input {
  padding: 0.875rem 1rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

input::placeholder {
  color: var(--text-muted);
}

input:focus {
  outline: none;
  border-color: var(--accent-primary);
  background: var(--bg-secondary);
}

input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Buttons */
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-primary-dim));
  color: white;
  border: none;
  border-radius: 0.625rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-top: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(62, 207, 142, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-spinner svg {
  width: 1.25rem;
  height: 1.25rem;
}

.btn-secondary {
  display: block;
  padding: 0.875rem 1.5rem;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  font-weight: 600;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

/* Messages */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--accent-danger);
  border-radius: 0.625rem;
  font-size: 0.875rem;
}

.error-message svg {
  flex-shrink: 0;
}

.success-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: rgba(62, 207, 142, 0.1);
  border: 1px solid rgba(62, 207, 142, 0.2);
  color: var(--accent-success);
  border-radius: 0.625rem;
  font-size: 0.875rem;
}

.success-message svg {
  flex-shrink: 0;
}

/* Divider */
.divider {
  margin: 2rem 0 1.5rem 0;
  text-align: center;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-default);
}

.divider span {
  position: relative;
  display: inline-block;
  padding: 0 1rem;
  background: var(--bg-secondary);
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* Background Decoration */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(62, 207, 142, 0.08) 0%, transparent 70%);
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -150px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float 25s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Responsive */
@media (max-width: 640px) {
  .auth-container {
    padding: 1rem;
  }

  .auth-card {
    padding: 2rem 1.5rem;
  }

  .brand-title {
    font-size: 1.75rem;
  }

  .auth-form {
    gap: 1rem;
  }
}
</style>
