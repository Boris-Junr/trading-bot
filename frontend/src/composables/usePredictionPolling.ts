/**
 * Prediction Polling Composable
 *
 * Handles background task polling for prediction generation.
 * Manages loading states, progress tracking, and error handling.
 */

import { ref, type Ref } from 'vue'
import type { PredictionData } from '@/types'

export interface LoadingStep {
  name: string
  label: string
  status: 'pending' | 'in-progress' | 'completed'
}

export interface LoadingStatus {
  title: string
  message: string
}

export interface UsePredictionPollingOptions {
  /**
   * Polling interval in milliseconds (default: 2000)
   */
  pollInterval?: number

  /**
   * Maximum number of polling attempts (default: 150)
   */
  maxAttempts?: number

  /**
   * Callback when prediction completes
   */
  onComplete?: (data: PredictionData) => void

  /**
   * Callback when prediction fails
   */
  onError?: (error: string) => void
}

export interface UsePredictionPollingReturn {
  /**
   * Whether prediction is currently loading
   */
  loading: Ref<boolean>

  /**
   * Error message (null if no error)
   */
  error: Ref<string | null>

  /**
   * Current loading status
   */
  loadingStatus: Ref<LoadingStatus>

  /**
   * Loading steps with progress
   */
  loadingSteps: Ref<LoadingStep[]>

  /**
   * Start prediction generation and poll for results
   */
  generatePrediction: (symbol: string, timeframe: string, autoTrain?: boolean) => Promise<PredictionData | null>

  /**
   * Clear error state
   */
  clearError: () => void

  /**
   * Reset all state
   */
  reset: () => void
}

const DEFAULT_STEPS: LoadingStep[] = [
  { name: 'check', label: 'Checking for existing model', status: 'pending' },
  { name: 'fetch', label: 'Fetching market data', status: 'pending' },
  { name: 'train', label: 'Processing model', status: 'pending' },
  { name: 'predict', label: 'Generating predictions', status: 'pending' }
]

/**
 * Composable for polling prediction tasks
 */
export function usePredictionPolling(
  options: UsePredictionPollingOptions = {}
): UsePredictionPollingReturn {
  const {
    pollInterval = 2000,
    maxAttempts = 150,
    onComplete,
    onError
  } = options

  const loading = ref(false)
  const error = ref<string | null>(null)
  const loadingStatus = ref<LoadingStatus>({
    title: 'Loading...',
    message: ''
  })
  const loadingSteps = ref<LoadingStep[]>(JSON.parse(JSON.stringify(DEFAULT_STEPS)))

  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

  /**
   * Update a specific loading step status
   */
  function updateLoadingStep(stepName: string, status: 'pending' | 'in-progress' | 'completed') {
    const step = loadingSteps.value.find(s => s.name === stepName)
    if (step) {
      step.status = status
    }
  }

  /**
   * Reset all loading steps to pending
   */
  function resetLoadingSteps() {
    loadingSteps.value = JSON.parse(JSON.stringify(DEFAULT_STEPS))
  }

  /**
   * Clear error state
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset all state
   */
  function reset() {
    loading.value = false
    error.value = null
    loadingStatus.value = { title: 'Loading...', message: '' }
    resetLoadingSteps()
  }

  /**
   * Poll for prediction completion
   */
  async function pollResult(predictionId: string): Promise<PredictionData | null> {
    let attempts = 0

    while (attempts < maxAttempts) {
      attempts++

      try {
        const statusResponse = await fetch(`${baseURL}/predictions/${predictionId}`)

        if (!statusResponse.ok) {
          throw new Error(`Failed to check prediction status: ${statusResponse.statusText}`)
        }

        const statusData = await statusResponse.json()

        if (statusData.status === 'queued') {
          loadingStatus.value = {
            title: 'Queued',
            message: 'Waiting for resources...'
          }
          await new Promise(resolve => setTimeout(resolve, pollInterval))
          continue
        }

        if (statusData.status === 'running') {
          // Update loading steps based on attempts
          if (attempts < 5) {
            updateLoadingStep('fetch', 'in-progress')
            loadingStatus.value = {
              title: 'Fetching data',
              message: 'Loading market data...'
            }
          } else if (attempts < 15) {
            updateLoadingStep('fetch', 'completed')
            updateLoadingStep('train', 'in-progress')
            loadingStatus.value = {
              title: 'Checking model',
              message: 'Preparing model...'
            }
          } else {
            updateLoadingStep('train', 'completed')
            updateLoadingStep('predict', 'in-progress')
            loadingStatus.value = {
              title: 'Generating predictions',
              message: 'Running ML model...'
            }
          }

          await new Promise(resolve => setTimeout(resolve, pollInterval))
          continue
        }

        if (statusData.status === 'completed' && statusData.result) {
          // Success!
          updateLoadingStep('fetch', 'completed')
          updateLoadingStep('train', 'completed')
          updateLoadingStep('predict', 'completed')

          return statusData.result
        }

        throw new Error('Prediction failed or returned invalid data')
      } catch (err: any) {
        throw err
      }
    }

    throw new Error('Prediction timed out after 5 minutes')
  }

  /**
   * Generate prediction and poll for results
   */
  async function generatePrediction(
    symbol: string,
    timeframe: string,
    autoTrain: boolean = true
  ): Promise<PredictionData | null> {
    loading.value = true
    error.value = null
    resetLoadingSteps()

    try {
      // Step 1: Start the background prediction
      loadingStatus.value = {
        title: 'Initializing',
        message: 'Starting prediction task...'
      }
      updateLoadingStep('check', 'in-progress')

      const normalizedSymbol = symbol.replace('/', '_')
      const startResponse = await fetch(
        `${baseURL}/predictions/generate?symbol=${normalizedSymbol}&timeframe=${timeframe}&auto_train=${autoTrain}`,
        { method: 'POST' }
      )

      if (!startResponse.ok) {
        throw new Error(`Failed to start prediction: ${startResponse.statusText}`)
      }

      const startData = await startResponse.json()
      const predictionId = startData.prediction_id

      if (startData.status === 'queued') {
        loadingStatus.value = {
          title: 'Queued',
          message: `Task queued at position ${startData.queue_position}. Waiting for resources...`
        }
      } else {
        loadingStatus.value = {
          title: 'Running',
          message: 'Prediction task is running in background...'
        }
      }

      updateLoadingStep('check', 'completed')
      updateLoadingStep('fetch', 'in-progress')

      // Step 2: Poll for completion
      const result = await pollResult(predictionId)

      loading.value = false

      if (result && onComplete) {
        onComplete(result)
      }

      return result
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to generate prediction'
      error.value = errorMessage
      loading.value = false

      if (onError) {
        onError(errorMessage)
      }

      return null
    }
  }

  return {
    loading,
    error,
    loadingStatus,
    loadingSteps,
    generatePrediction,
    clearError,
    reset
  }
}
