/**
 * Async Data Composable
 *
 * Standardizes async data fetching with loading and error states.
 * Eliminates ~250 lines of duplicated try/catch/finally patterns across 8+ files.
 */

import { ref, type Ref } from 'vue'

export interface AsyncDataOptions<T> {
  /**
   * Execute fetch immediately on composable creation
   */
  immediate?: boolean

  /**
   * Custom error message (overrides error.message)
   */
  errorMessage?: string

  /**
   * Callback on successful fetch
   */
  onSuccess?: (data: T) => void

  /**
   * Callback on fetch error
   */
  onError?: (error: Error) => void

  /**
   * Initial data value
   */
  initialData?: T | null
}

export interface AsyncDataReturn<T> {
  /**
   * Fetched data (null until loaded)
   */
  data: Ref<T | null>

  /**
   * Loading state
   */
  loading: Ref<boolean>

  /**
   * Error message (null if no error)
   */
  error: Ref<string | null>

  /**
   * Execute the fetch function
   */
  execute: () => Promise<T | null>

  /**
   * Retry the fetch (alias for execute)
   */
  retry: () => Promise<T | null>

  /**
   * Clear error state
   */
  clearError: () => void

  /**
   * Reset all state to initial values
   */
  reset: () => void
}

/**
 * Standardized async data fetching with loading and error states
 *
 * @template T - Type of data being fetched
 * @param fetchFn - Async function to fetch data
 * @param options - Configuration options
 * @returns Reactive refs and control functions
 *
 * @example
 * ```typescript
 * // Basic usage
 * const { data: backtests, loading, error, execute } = useAsyncData(
 *   () => api.getBacktests()
 * )
 *
 * // With immediate execution
 * const { data, loading, error } = useAsyncData(
 *   () => api.getBacktests(),
 *   { immediate: true }
 * )
 *
 * // With callbacks
 * const { data, loading, error, retry } = useAsyncData(
 *   () => api.getBacktests(),
 *   {
 *     immediate: true,
 *     errorMessage: 'Failed to load backtests',
 *     onSuccess: (data) => console.log('Loaded:', data),
 *     onError: (err) => console.error('Error:', err)
 *   }
 * )
 * ```
 */
export function useAsyncData<T>(
  fetchFn: () => Promise<T>,
  options: AsyncDataOptions<T> = {}
): AsyncDataReturn<T> {
  const data = ref<T | null>(options.initialData ?? null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Execute the fetch function with proper error handling
   */
  async function execute(): Promise<T | null> {
    loading.value = true
    error.value = null

    try {
      const result = await fetchFn()
      data.value = result
      options.onSuccess?.(result)
      return result
    } catch (e: any) {
      const errorMsg = options.errorMessage || e.message || 'An error occurred'
      error.value = errorMsg
      console.error('[useAsyncData] Fetch error:', e)
      options.onError?.(e)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error state
   */
  function clearError(): void {
    error.value = null
  }

  /**
   * Reset all state to initial values
   */
  function reset(): void {
    data.value = options.initialData ?? null
    loading.value = false
    error.value = null
  }

  // Execute immediately if requested
  if (options.immediate) {
    execute()
  }

  return {
    data,
    loading,
    error,
    execute,
    retry: execute,
    clearError,
    reset
  }
}
