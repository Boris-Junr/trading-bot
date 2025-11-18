import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  timestamp: Date
}

export const useNotificationStore = defineStore('notifications', () => {
  // State
  const notifications = ref<Notification[]>([])
  const maxNotifications = 5

  // Actions
  function addNotification(
    type: Notification['type'],
    title: string,
    message: string,
    duration: number = 5000
  ): string {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    const notification: Notification = {
      id,
      type,
      title,
      message,
      duration,
      timestamp: new Date()
    }

    notifications.value.unshift(notification)

    // Keep only max notifications
    if (notifications.value.length > maxNotifications) {
      notifications.value = notifications.value.slice(0, maxNotifications)
    }

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }

    return id
  }

  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function clearAll() {
    notifications.value = []
  }

  // Convenience methods
  function success(title: string, message: string, duration?: number) {
    return addNotification('success', title, message, duration)
  }

  function error(title: string, message: string, duration?: number) {
    return addNotification('error', title, message, duration)
  }

  function warning(title: string, message: string, duration?: number) {
    return addNotification('warning', title, message, duration)
  }

  function info(title: string, message: string, duration?: number) {
    return addNotification('info', title, message, duration)
  }

  return {
    // State
    notifications,

    // Actions
    addNotification,
    removeNotification,
    clearAll,
    success,
    error,
    warning,
    info
  }
})
