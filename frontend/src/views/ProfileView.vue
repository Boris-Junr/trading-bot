<template>
  <div class="profile-view">
    <h1 class="page-title">Profile Settings</h1>

    <!-- User Profile Section -->
    <Card class="mb-6">
      <h2 class="section-title">User Profile</h2>

      <form @submit.prevent="updateProfile" class="profile-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="profile.email"
            type="email"
            disabled
            class="form-input disabled"
          />
          <span class="form-help">Email cannot be changed</span>
        </div>

        <div class="form-group">
          <label for="fullName">Full Name</label>
          <input
            id="fullName"
            v-model="profile.full_name"
            type="text"
            placeholder="Enter your full name"
            class="form-input"
          />
        </div>

        <Button type="submit" :disabled="savingProfile">
          {{ savingProfile ? 'Saving...' : 'Save Profile' }}
        </Button>
      </form>
    </Card>

    <!-- API Keys Section -->
    <Card>
      <h2 class="section-title">API Keys</h2>
      <p class="section-description">Configure your trading platform credentials</p>

      <!-- Loading State -->
      <div v-if="loadingApiKeys" class="loading-container">
        <div class="spinner"></div>
        <p class="loading-text">Loading API keys...</p>
      </div>

      <div v-else class="api-keys-table">
        <!-- Header -->
        <div class="table-header">
          <div class="col-provider">Provider</div>
          <div class="col-env">Environment</div>
          <div class="col-key">API Key</div>
          <div class="col-secret">API Secret</div>
          <div class="col-actions">Actions</div>
        </div>

        <!-- Provider Rows -->
        <div v-for="provider in providers" :key="provider.id" class="provider-section">
          <!-- Paper Trading Row -->
          <div class="table-row" v-if="provider.supports_paper_trading">
            <div class="col-provider">
              <strong>{{ provider.display_name }}</strong>
            </div>
            <div class="col-env">
              <Badge variant="warning">Paper</Badge>
            </div>
            <div class="col-key">
              <input
                v-model="ensureKeyInput(provider.id, 'paper').api_key"
                type="password"
                :placeholder="getKeyHint(provider.id, 'paper', 'api_key') || 'Enter API key'"
                class="form-input-inline"
              />
            </div>
            <div class="col-secret">
              <input
                v-model="ensureKeyInput(provider.id, 'paper').api_secret"
                type="password"
                :placeholder="getKeyHint(provider.id, 'paper', 'api_secret') || 'Enter API secret'"
                class="form-input-inline"
              />
            </div>
            <div class="col-actions">
              <Button
                @click="saveKey(provider.id, 'paper')"
                size="sm"
                :disabled="!hasKeyInput(provider.id, 'paper') || savingKeys[getKeyId(provider.id, 'paper')]"
              >
                {{ savingKeys[getKeyId(provider.id, 'paper')] ? 'Saving...' : 'Save' }}
              </Button>
              <Button
                v-if="hasExistingKey(provider.id, 'paper')"
                @click="deleteKey(provider.id, 'paper')"
                variant="danger"
                size="sm"
                :disabled="deletingKeys[getKeyId(provider.id, 'paper')]"
              >
                {{ deletingKeys[getKeyId(provider.id, 'paper')] ? 'Deleting...' : 'Delete' }}
              </Button>
            </div>
          </div>

          <!-- Live Trading Row -->
          <div class="table-row">
            <div class="col-provider" v-if="!provider.supports_paper_trading">
              <strong>{{ provider.display_name }}</strong>
            </div>
            <div class="col-provider" v-else></div>
            <div class="col-env">
              <Badge variant="danger">Live</Badge>
            </div>
            <div class="col-key">
              <input
                v-model="ensureKeyInput(provider.id, 'live').api_key"
                type="password"
                :placeholder="getKeyHint(provider.id, 'live', 'api_key') || 'Enter API key'"
                class="form-input-inline"
              />
            </div>
            <div class="col-secret">
              <input
                v-model="ensureKeyInput(provider.id, 'live').api_secret"
                type="password"
                :placeholder="getKeyHint(provider.id, 'live', 'api_secret') || 'Enter API secret'"
                class="form-input-inline"
              />
            </div>
            <div class="col-actions">
              <Button
                @click="saveKey(provider.id, 'live')"
                size="sm"
                :disabled="!hasKeyInput(provider.id, 'live') || savingKeys[getKeyId(provider.id, 'live')]"
              >
                {{ savingKeys[getKeyId(provider.id, 'live')] ? 'Saving...' : 'Save' }}
              </Button>
              <Button
                v-if="hasExistingKey(provider.id, 'live')"
                @click="deleteKey(provider.id, 'live')"
                variant="danger"
                size="sm"
                :disabled="deletingKeys[getKeyId(provider.id, 'live')]"
              >
                {{ deletingKeys[getKeyId(provider.id, 'live')] ? 'Deleting...' : 'Delete' }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { supabase } from '../lib/supabase'
import axios from 'axios'
import Card from '../components/ui/Card.vue'
import Button from '../components/ui/Button.vue'
import Badge from '../components/ui/Badge.vue'

const API_BASE_URL = 'http://localhost:8000'

// Profile state
const profile = ref({
  email: '',
  full_name: ''
})
const savingProfile = ref(false)

// API keys state
const apiKeys = ref<any[]>([])
const providers = ref<any[]>([])
const loadingApiKeys = ref(true)
const keyInputs = reactive<Record<string, { api_key: string, api_secret: string }>>({})
const savingKeys = reactive<Record<string, boolean>>({})
const deletingKeys = reactive<Record<string, boolean>>({})

// Helper to generate unique key ID
function getKeyId(providerId: string, environment: string) {
  return `${providerId}_${environment}`
}

// Helper to ensure key input exists
function ensureKeyInput(providerId: string, environment: string) {
  const keyId = getKeyId(providerId, environment)
  if (!keyInputs[keyId]) {
    keyInputs[keyId] = { api_key: '', api_secret: '' }
  }
  return keyInputs[keyId]
}

// Get existing key hint for placeholder
function getKeyHint(providerId: string, environment: string, field: 'api_key' | 'api_secret') {
  const existing = apiKeys.value.find(k =>
    k.provider_id === providerId && k.environment === environment
  )
  return existing ? (field === 'api_key' ? existing.api_key_hint : existing.api_secret_hint) : null
}

// Check if user has entered any input
function hasKeyInput(providerId: string, environment: string) {
  const keyId = getKeyId(providerId, environment)
  return keyInputs[keyId]?.api_key || keyInputs[keyId]?.api_secret
}

// Check if key already exists
function hasExistingKey(providerId: string, environment: string) {
  return apiKeys.value.some(k => k.provider_id === providerId && k.environment === environment)
}

// Initialize key inputs
function initializeKeyInputs() {
  providers.value.forEach(provider => {
    if (provider.supports_paper_trading) {
      keyInputs[getKeyId(provider.id, 'paper')] = { api_key: '', api_secret: '' }
    }
    keyInputs[getKeyId(provider.id, 'live')] = { api_key: '', api_secret: '' }
  })
}

// Load user profile
async function loadProfile() {
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    profile.value.email = user.email || ''

    const { data } = await supabase
      .from('users')
      .select('full_name')
      .eq('id', user.id)
      .single()

    if (data) {
      profile.value.full_name = data.full_name || ''
    }
  } catch (error) {
    console.error('Failed to load profile:', error)
  }
}

// Update user profile
async function updateProfile() {
  savingProfile.value = true
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    await supabase
      .from('users')
      .update({ full_name: profile.value.full_name })
      .eq('id', user.id)

    alert('Profile updated successfully')
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Failed to update profile')
  } finally {
    savingProfile.value = false
  }
}

// Load available providers
async function loadProviders() {
  try {
    const { data } = await supabase
      .from('user_api_key_providers')
      .select('*')
      .eq('is_active', true)
      .order('display_name')

    providers.value = data || []
    initializeKeyInputs()
  } catch (error) {
    console.error('Failed to load providers:', error)
  }
}

// Load user's API keys
async function loadApiKeys() {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) {
      loadingApiKeys.value = false
      return
    }

    const response = await axios.get(`${API_BASE_URL}/api/keys/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })

    apiKeys.value = response.data
  } catch (error) {
    console.error('Failed to load API keys:', error)
  } finally {
    loadingApiKeys.value = false
  }
}

// Save API key
async function saveKey(providerId: string, environment: string) {
  const keyId = getKeyId(providerId, environment)
  const input = keyInputs[keyId]

  if (!input || (!input.api_key && !input.api_secret)) {
    alert('Please enter at least one credential')
    return
  }

  savingKeys[keyId] = true
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) return

    const existing = apiKeys.value.find(k =>
      k.provider_id === providerId && k.environment === environment
    )

    if (existing) {
      // Update existing
      await axios.put(
        `${API_BASE_URL}/api/keys/${existing.id}`,
        {
          provider_id: providerId,
          environment,
          api_key: input?.api_key || undefined,
          api_secret: input?.api_secret || undefined
        },
        { headers: { Authorization: `Bearer ${session.access_token}` } }
      )
    } else {
      // Create new
      if (!input?.api_key || !input?.api_secret) {
        alert('Both API key and secret are required for new credentials')
        savingKeys[keyId] = false
        return
      }

      await axios.post(
        `${API_BASE_URL}/api/keys/`,
        {
          provider_id: providerId,
          environment,
          api_key: input.api_key,
          api_secret: input.api_secret
        },
        { headers: { Authorization: `Bearer ${session.access_token}` } }
      )
    }

    // Clear inputs and reload
    keyInputs[keyId] = { api_key: '', api_secret: '' }
    await loadApiKeys()
    alert('API key saved successfully')
  } catch (error) {
    console.error('Failed to save API key:', error)
    alert('Failed to save API key')
  } finally {
    savingKeys[keyId] = false
  }
}

// Delete API key
async function deleteKey(providerId: string, environment: string) {
  const keyId = getKeyId(providerId, environment)
  const existing = apiKeys.value.find(k =>
    k.provider_id === providerId && k.environment === environment
  )

  if (!existing) return

  if (!confirm(`Delete ${environment} key?`)) return

  deletingKeys[keyId] = true
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) return

    await axios.delete(`${API_BASE_URL}/api/keys/${existing.id}`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })

    await loadApiKeys()
    alert('API key deleted')
  } catch (error) {
    console.error('Failed to delete API key:', error)
    alert('Failed to delete API key')
  } finally {
    deletingKeys[keyId] = false
  }
}

onMounted(async () => {
  // Load profile separately (not blocking)
  loadProfile()

  // Load providers and API keys in parallel for faster initialization
  await Promise.all([
    loadProviders(),
    loadApiKeys()
  ])
})
</script>

<style scoped>
.profile-view {
  width: 100%;
  padding: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 2rem;
  color: var(--text-primary);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: var(--text-muted);
  margin-bottom: 1.5rem;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 1rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.form-input.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-help {
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* API Keys Table */
.api-keys-table {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.table-header {
  display: grid;
  grid-template-columns: 180px 120px 1fr 1fr 180px;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-tertiary);
  border-radius: 0.5rem 0.5rem 0 0;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-color);
}

.provider-section {
  border-bottom: 1px solid var(--border-color);
}

.table-row {
  display: grid;
  grid-template-columns: 180px 120px 1fr 1fr 180px;
  gap: 1rem;
  padding: 1rem;
  align-items: center;
  background: var(--bg-secondary);
}

.table-row:hover {
  background: var(--bg-tertiary);
}

.col-provider,
.col-env,
.col-key,
.col-secret,
.col-actions {
  display: flex;
  align-items: center;
}

.col-actions {
  gap: 0.5rem;
}

.form-input-inline {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: monospace;
}

.form-input-inline:focus {
  outline: none;
  border-color: var(--primary);
}

.form-input-inline::placeholder {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
}
</style>
