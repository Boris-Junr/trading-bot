/**
 * Formatting Composable
 *
 * Centralized formatting utilities for dates, currency, numbers, and percentages.
 * Eliminates duplication across 5+ components with consistent formatting.
 */

export function useFormatters() {
  /**
   * Format date with multiple output options
   *
   * @param dateString - ISO date string or Date object
   * @param format - Output format: 'short' | 'long' | 'relative'
   * @returns Formatted date string
   *
   * @example
   * formatDate('2024-01-15', 'short') // "Jan 15, 2024"
   * formatDate('2024-01-15', 'long') // "January 15, 2024, 3:30 PM"
   * formatDate('2024-01-15', 'relative') // "2d ago"
   */
  function formatDate(
    dateString: string | Date,
    format: 'short' | 'long' | 'relative' = 'short'
  ): string {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString

    if (format === 'relative') {
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffSecs = Math.floor(diffMs / 1000)
      const diffMins = Math.floor(diffSecs / 60)
      const diffHours = Math.floor(diffMins / 60)
      const diffDays = Math.floor(diffHours / 24)

      if (diffSecs < 60) return 'just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
      if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
      return `${Math.floor(diffDays / 365)}y ago`
    }

    if (format === 'long') {
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // Default: short format
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  /**
   * Format number as currency (USD)
   *
   * @param value - Numeric value
   * @param decimals - Number of decimal places (default: 2)
   * @returns Formatted currency string
   *
   * @example
   * formatCurrency(1234.567) // "$1,234.57"
   * formatCurrency(1234.567, 0) // "$1,235"
   */
  function formatCurrency(value: number, decimals: number = 2): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value)
  }

  /**
   * Format number with thousand separators
   *
   * @param value - Numeric value
   * @param decimals - Number of decimal places (default: 2)
   * @returns Formatted number string
   *
   * @example
   * formatNumber(1234.567) // "1,234.57"
   * formatNumber(1234.567, 0) // "1,235"
   */
  function formatNumber(value: number, decimals: number = 2): string {
    return Math.abs(value).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  /**
   * Format number as percentage
   *
   * @param value - Numeric value (e.g., 12.34 for 12.34%)
   * @param decimals - Number of decimal places (default: 2)
   * @param includeSign - Include + sign for positive values (default: true)
   * @returns Formatted percentage string
   *
   * @example
   * formatPercent(12.34) // "+12.34%"
   * formatPercent(-5.67) // "-5.67%"
   * formatPercent(12.34, 1, false) // "12.3%"
   */
  function formatPercent(
    value: number,
    decimals: number = 2,
    includeSign: boolean = true
  ): string {
    const formatted = `${Math.abs(value).toFixed(decimals)}%`

    if (!includeSign) return formatted

    return value >= 0 ? `+${formatted}` : `-${formatted}`
  }

  /**
   * Format number in compact notation (K, M, B)
   *
   * @param value - Numeric value
   * @param decimals - Number of decimal places (default: 1)
   * @returns Compact formatted string
   *
   * @example
   * formatCompact(1234) // "1.2K"
   * formatCompact(1234567) // "1.2M"
   * formatCompact(1234567890) // "1.2B"
   */
  function formatCompact(value: number, decimals: number = 1): string {
    const absValue = Math.abs(value)
    const sign = value < 0 ? '-' : ''

    if (absValue >= 1e9) {
      return `${sign}${(absValue / 1e9).toFixed(decimals)}B`
    }
    if (absValue >= 1e6) {
      return `${sign}${(absValue / 1e6).toFixed(decimals)}M`
    }
    if (absValue >= 1e3) {
      return `${sign}${(absValue / 1e3).toFixed(decimals)}K`
    }

    return `${sign}${absValue.toFixed(decimals)}`
  }

  /**
   * Format task type for display
   *
   * @param type - Task type string (e.g., 'backtest', 'model_training')
   * @returns Human-readable task type
   *
   * @example
   * formatTaskType('backtest') // "Backtest"
   * formatTaskType('model_training') // "Model Training"
   */
  function formatTaskType(type: string): string {
    const typeMap: Record<string, string> = {
      'backtest': 'Backtest',
      'model_training': 'Model Training',
      'prediction': 'Prediction',
      'data_fetch': 'Data Fetch'
    }
    return typeMap[type] || type
  }

  return {
    formatDate,
    formatCurrency,
    formatNumber,
    formatPercent,
    formatCompact,
    formatTaskType
  }
}
