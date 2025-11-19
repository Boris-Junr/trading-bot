import { watch } from 'vue'
import { useTaskManagerStore } from '@/stores/taskManager'
import { useNotificationStore } from '@/stores/notifications'
import type { Task } from '@/types'

export function useTaskNotifications() {
  const taskManager = useTaskManagerStore()
  const notifications = useNotificationStore()

  // Track previous task states
  const previousStates = new Map<string, Task['status']>()

  // Watch all tasks by combining all computed arrays
  // This ensures we catch tasks transitioning between states
  watch(
    () => [
      ...taskManager.queuedTasks,
      ...taskManager.runningTasks,
      ...taskManager.completedTasks,
      ...taskManager.failedTasks
    ],
    (allTasks) => {
      allTasks.forEach((task) => {
        const taskId = task.task_id
        const previousStatus = previousStates.get(taskId)
        const currentStatus = task.status

        // Skip if status hasn't changed
        if (previousStatus === currentStatus) {
          return
        }

        // Update tracked state
        previousStates.set(taskId, currentStatus)

        // Create notifications based on state transitions
        const taskTypeName = formatTaskType(task.task_type)

        // Task queued (only show if it's new or transitioning to queued)
        if (currentStatus === 'queued' && !previousStatus) {
          notifications.warning(
            'Task Queued',
            `${taskTypeName} queued at position #${task.queue_position || '?'}`,
            4000
          )
        }

        // Task started running (show for any transition to running)
        if (currentStatus === 'running' && previousStatus !== 'running' && previousStatus !== 'completed' && previousStatus !== 'failed') {
          notifications.info(
            'Task Started',
            `${taskTypeName} is now running`,
            3000
          )
        }

        // Task completed (show for any transition to completed from active states)
        if (currentStatus === 'completed' && (previousStatus === 'running' || previousStatus === 'queued' || !previousStatus)) {
          notifications.success(
            'Task Completed',
            `${taskTypeName} finished successfully`,
            5000
          )
        }

        // Task failed (show for any transition to failed)
        if (currentStatus === 'failed' && previousStatus !== 'failed') {
          notifications.error(
            'Task Failed',
            task.error || `${taskTypeName} failed to complete`,
            8000
          )
        }
      })

      // Clean up tracking for removed tasks
      const currentTaskIds = new Set(allTasks.map(t => t.task_id))
      previousStates.forEach((_, taskId) => {
        if (!currentTaskIds.has(taskId)) {
          previousStates.delete(taskId)
        }
      })
    },
    { deep: true }
  )

  function formatTaskType(type: string): string {
    const typeMap: Record<string, string> = {
      'backtest': 'Backtest',
      'model_training': 'Model Training',
      'prediction': 'Prediction'
    }
    return typeMap[type] || type
  }

  return {
    // Empty return - this composable works via side effects (watchers)
  }
}
