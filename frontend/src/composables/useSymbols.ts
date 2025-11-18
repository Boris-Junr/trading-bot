/**
 * Symbols Composable
 *
 * Centralized symbol fetching with caching and fallback support.
 * Eliminates ~80 lines of duplicated symbol loading across BacktestsView,
 * PredictionsView, and ModelsView.
 */

import { ref, type Ref } from 'vue'
import { api } from '@/services/api'

export type AssetType = 'all' | 'crypto' | 'forex' | 'indices'

export interface UseSymbolsReturn {
  /**
   * Available trading symbols
   */
  symbols: Ref<string[]>

  /**
   * Loading state
   */
  loading: Ref<boolean>

  /**
   * Error message (null if no error)
   */
  error: Ref<string | null>

  /**
   * Fetch symbols from API
   */
  fetch: () => Promise<void>

  /**
   * Refresh symbols (alias for fetch)
   */
  refresh: () => Promise<void>

  /**
   * Clear error state
   */
  clearError: () => void
}

/**
 * Fallback symbols when API is unavailable
 */
const FALLBACK_SYMBOLS: Record<AssetType, string[]> = {
  crypto: [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'ADA/USDT',
    'DOT/USDT',
    'MATIC/USDT',
    'DOGE/USDT'
  ],
  forex: [
    'EUR/USD',
    'GBP/USD',
    'USD/JPY',
    'AUD/USD',
    'USD/CAD'
  ],
  indices: [
    'SPY',
    'QQQ',
    'DIA',
    'NAS100',
    'US30',
    'GER40'
  ],
  all: [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'ADA/USDT',
    'DOT/USDT',
    'MATIC/USDT',
    'DOGE/USDT',
    'EUR/USD',
    'GBP/USD',
    'USD/JPY',
    'AUD/USD',
    'USD/CAD',
    'SPY',
    'QQQ',
    'DIA',
    'NAS100',
    'US30',
    'GER40'
  ]
}

/**
 * Simple in-memory cache for symbols
 */
const symbolsCache: Record<AssetType, { data: string[]; timestamp: number } | null> = {
  all: null,
  crypto: null,
  forex: null,
  indices: null
}

const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

/**
 * Centralized symbol fetching with caching and fallback
 *
 * @param assetType - Type of assets to fetch (default: 'all')
 * @param options - Configuration options
 * @returns Reactive refs and control functions
 *
 * @example
 * ```typescript
 * // Basic usage
 * const { symbols, loading, fetch } = useSymbols('crypto')
 * await fetch()
 *
 * // With immediate fetch
 * const { symbols, loading, error } = useSymbols('all', { immediate: true })
 *
 * // Refresh symbols
 * const { symbols, refresh } = useSymbols()
 * await refresh()
 * ```
 */
export function useSymbols(
  assetType: AssetType = 'all',
  options: { immediate?: boolean; useCache?: boolean } = {}
): UseSymbolsReturn {
  const symbols = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const { immediate = false, useCache = true } = options

  /**
   * Check if cached data is still valid
   */
  function isCacheValid(): boolean {
    if (!useCache) return false

    const cached = symbolsCache[assetType]
    if (!cached) return false

    const now = Date.now()
    return now - cached.timestamp < CACHE_TTL
  }

  /**
   * Fetch symbols from API with caching and fallback
   */
  async function fetch(): Promise<void> {
    // Check cache first
    if (isCacheValid()) {
      const cached = symbolsCache[assetType]!
      symbols.value = cached.data
      console.log(`[useSymbols] Using cached symbols for ${assetType}`)
      return
    }

    loading.value = true
    error.value = null

    try {
      console.log(`[useSymbols] Fetching symbols for ${assetType}`)
      const data = await api.getSymbols(assetType)
      symbols.value = data

      // Update cache
      symbolsCache[assetType] = {
        data,
        timestamp: Date.now()
      }
    } catch (e: any) {
      console.error('[useSymbols] Failed to fetch symbols:', e)
      error.value = e.message || 'Failed to fetch symbols'

      // Use fallback symbols
      symbols.value = FALLBACK_SYMBOLS[assetType] || FALLBACK_SYMBOLS.all
      console.log(`[useSymbols] Using fallback symbols for ${assetType}`)
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

  // Fetch immediately if requested
  if (immediate) {
    fetch()
  }

  return {
    symbols,
    loading,
    error,
    fetch,
    refresh: fetch,
    clearError
  }
}

/**
 * Clear all cached symbols
 */
export function clearSymbolsCache(): void {
  symbolsCache.all = null
  symbolsCache.crypto = null
  symbolsCache.forex = null
  symbolsCache.indices = null
}
