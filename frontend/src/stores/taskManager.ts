import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, ResourceSummary } from '@/types'
import axios from 'axios'
import { supabase } from '@/lib/supabase'

const API_BASE_URL = 'http://localhost:8000'

export const useTaskManagerStore = defineStore('taskManager', () => {
  // State
  const tasks = ref<Map<string, Task>>(new Map())
  const resources = ref<ResourceSummary | null>(null)
  const isMonitoring = ref(false)
  const pollingInterval = ref<number | null>(null)
  const isAdmin = ref(false)

  // Computed
  const queuedTasks = computed(() => {
    return Array.from(tasks.value.values())
      .filter(task => task.status === 'queued')
      .sort((a, b) => (a.queue_position || 0) - (b.queue_position || 0))
  })

  const runningTasks = computed(() => {
    return Array.from(tasks.value.values())
      .filter(task => task.status === 'running')
  })

  const completedTasks = computed(() => {
    return Array.from(tasks.value.values())
      .filter(task => task.status === 'completed')
      .sort((a, b) => {
        const timeA = new Date(a.completed_at || a.created_at).getTime()
        const timeB = new Date(b.completed_at || b.created_at).getTime()
        return timeB - timeA
      })
  })

  const failedTasks = computed(() => {
    return Array.from(tasks.value.values())
      .filter(task => task.status === 'failed')
  })

  const hasQueuedTasks = computed(() => queuedTasks.value.length > 0)
  const hasRunningTasks = computed(() => runningTasks.value.length > 0)

  const cpuUsagePercent = computed(() => {
    if (!resources.value) return 0
    return resources.value.resources.cpu.usage_percent || 0
  })

  const ramUsagePercent = computed(() => {
    if (!resources.value) return 0
    return resources.value.resources.ram.usage_percent || 0
  })

  const availableCpuCores = computed(() => {
    if (!resources.value) return 0
    return resources.value.resources.cpu.available_cores
  })

  const availableRamGB = computed(() => {
    if (!resources.value) return 0
    return resources.value.resources.ram.available_gb
  })

  // Actions
  async function fetchResources() {
    try {
      // Get auth token
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        console.error('[TaskManager] No auth token available')
        return
      }

      const response = await axios.get<ResourceSummary>(`${API_BASE_URL}/api/system/resources`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      })
      resources.value = response.data

      // Update admin status if included in response
      if (typeof response.data.is_admin === 'boolean') {
        isAdmin.value = response.data.is_admin
      }

      // Debug logging
      console.log('[TaskManager] Fetched resources:', {
        running: response.data.queue?.running_count || 0,
        queued: response.data.queue?.queued_count || 0,
        running_tasks: response.data.queue?.running_tasks || []
      })

      // Update task information from queue status
      if (response.data.queue) {
        // Update queued tasks
        response.data.queue.queued_tasks.forEach(queuedTask => {
          const existingTask = tasks.value.get(queuedTask.task_id)
          if (existingTask) {
            existingTask.status = 'queued'
            existingTask.queue_position = queuedTask.queue_position
            existingTask.estimated_cpu_cores = queuedTask.estimated_cpu_cores
            existingTask.estimated_ram_gb = queuedTask.estimated_ram_gb
          } else {
            // Create new task entry
            tasks.value.set(queuedTask.task_id, {
              task_id: queuedTask.task_id,
              task_type: queuedTask.task_type as 'backtest' | 'model_training' | 'prediction',
              status: 'queued',
              created_at: queuedTask.queued_at,
              queue_position: queuedTask.queue_position,
              estimated_cpu_cores: queuedTask.estimated_cpu_cores,
              estimated_ram_gb: queuedTask.estimated_ram_gb
            })
          }
        })

        // Update running tasks
        response.data.queue.running_tasks.forEach(runningTask => {
          console.log('[TaskManager] Processing running task:', runningTask.task_id, runningTask.task_type)
          const existingTask = tasks.value.get(runningTask.task_id)
          if (existingTask) {
            console.log('[TaskManager] Updating existing task to running:', runningTask.task_id)
            existingTask.status = 'running'
            existingTask.queue_position = undefined
            existingTask.estimated_cpu_cores = runningTask.estimated_cpu_cores
            existingTask.estimated_ram_gb = runningTask.estimated_ram_gb
          } else {
            console.log('[TaskManager] Creating new running task entry:', runningTask.task_id)
            // Create new task entry
            tasks.value.set(runningTask.task_id, {
              task_id: runningTask.task_id,
              task_type: runningTask.task_type as 'backtest' | 'model_training' | 'prediction',
              status: 'running',
              created_at: new Date().toISOString(),
              started_at: new Date().toISOString(),
              estimated_cpu_cores: runningTask.estimated_cpu_cores,
              estimated_ram_gb: runningTask.estimated_ram_gb
            })
          }
        })

        // Remove tasks that are no longer in queue or running
        const activeTaskIds = new Set([
          ...response.data.queue.queued_tasks.map(t => t.task_id),
          ...response.data.queue.running_tasks.map(t => t.task_id)
        ])

        // Mark tasks as completed if they were running/queued but are no longer active
        tasks.value.forEach((task, taskId) => {
          if ((task.status === 'queued' || task.status === 'running') && !activeTaskIds.has(taskId)) {
            task.status = 'completed'
            task.completed_at = new Date().toISOString()
            task.queue_position = undefined
          }
        })
      }
    } catch (error) {
      console.error('[TaskManager] Failed to fetch resources:', error)
    }
  }

  function addTask(task: Task) {
    tasks.value.set(task.task_id, task)
  }

  function updateTask(taskId: string, updates: Partial<Task>) {
    const task = tasks.value.get(taskId)
    if (task) {
      Object.assign(task, updates)
    }
  }

  function removeTask(taskId: string) {
    tasks.value.delete(taskId)
  }

  function clearCompletedTasks() {
    tasks.value.forEach((task, taskId) => {
      if (task.status === 'completed') {
        tasks.value.delete(taskId)
      }
    })
  }

  function clearAllTasks() {
    tasks.value.clear()
  }

  async function startMonitoring(intervalMs: number = 2000) {
    if (isMonitoring.value) return

    isMonitoring.value = true

    // Fetch initial data immediately and WAIT for it to complete
    console.log('[TaskManager] Fetching initial resources...')
    await fetchResources().catch(err => console.error('[TaskManager] Failed to fetch initial resources:', err))
    console.log('[TaskManager] Initial resources loaded')

    // Set up SSE for real-time task updates (includes CPU/RAM via heartbeat)
    // Get auth token for SSE connection
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) {
      console.error('[TaskManager] No auth token available for SSE')
      return
    }

    // EventSource doesn't support custom headers, so pass token as query parameter
    const sseUrl = `${API_BASE_URL}/api/system/task-events?token=${session.access_token}`
    console.log('[TaskManager] 🔌 Attempting SSE connection to:', sseUrl)
    const eventSource = new EventSource(sseUrl)

    eventSource.onopen = () => {
      console.log('[TaskManager] ✅ SSE connection established successfully!')
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('[TaskManager] Received SSE event:', data.type, data)

        // Update admin status if included
        if (typeof data.is_admin === 'boolean') {
          isAdmin.value = data.is_admin
        }

        // Update resources from event (only for admin users)
        if (data.resources) {
          if (resources.value) {
            resources.value.resources = data.resources
          } else {
            resources.value = { resources: data.resources, queue: { queued_count: 0, running_count: 0, queued_tasks: [], running_tasks: [] }, is_admin: false }
          }
        }

        // Handle event type
        if (data.type === 'initial_state') {
          // Initial queue status
          processQueueStatus(data.data)
        } else if (data.type === 'heartbeat') {
          // Periodic resource update (CPU/RAM stats refreshed every 5s)
          // Resources already updated above, nothing else to do
        } else if (data.type === 'task_running') {
          // Task started running
          handleTaskRunning(data.data)
        } else if (data.type === 'task_completed') {
          // Task completed
          handleTaskCompleted(data.data)
        } else if (data.type === 'task_queued') {
          // Task queued
          handleTaskQueued(data.data)
        } else if (data.type === 'task_description_update') {
          // Task description updated
          handleTaskDescriptionUpdate(data.data)
        }
      } catch (error) {
        console.error('[TaskManager] Error processing SSE event:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('[TaskManager] ❌ SSE connection error:', error)
      console.error('[TaskManager] EventSource readyState:', eventSource.readyState, '(0=CONNECTING, 1=OPEN, 2=CLOSED)')
      console.error('[TaskManager] EventSource url:', eventSource.url)

      // Only fallback to polling if connection is permanently closed
      // readyState 0 = CONNECTING (initial connection or reconnecting)
      // readyState 1 = OPEN (connected)
      // readyState 2 = CLOSED (permanently failed)
      if (eventSource.readyState === 2 && !pollingInterval.value) {
        console.warn('[TaskManager] ⚠️  SSE permanently closed, falling back to polling mode')
        pollingInterval.value = window.setInterval(() => {
          fetchResources()
        }, intervalMs)
      } else if (eventSource.readyState === 0) {
        console.log('[TaskManager] 🔄 SSE is connecting/reconnecting, waiting...')
      }
    }

    // Store event source for cleanup
    ;(window as any).__taskEventSource = eventSource

    console.log('[TaskManager] Started monitoring with SSE (fully event-driven, no polling)')
  }

  function handleTaskRunning(taskData: any) {
    console.log('[TaskManager] Task started running:', taskData.task_id)
    const task = tasks.value.get(taskData.task_id)
    if (task) {
      task.status = 'running'
      task.queue_position = undefined
      if (taskData.description) {
        task.description = taskData.description
      }
    } else {
      tasks.value.set(taskData.task_id, {
        task_id: taskData.task_id,
        task_type: taskData.task_type as 'backtest' | 'model_training' | 'prediction',
        status: 'running',
        description: taskData.description,
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        estimated_cpu_cores: taskData.estimated_cpu_cores,
        estimated_ram_gb: taskData.estimated_ram_gb
      })
    }
  }

  function handleTaskCompleted(taskData: any) {
    console.log('[TaskManager] Task completed:', taskData.task_id)
    const task = tasks.value.get(taskData.task_id)
    if (task) {
      task.status = 'completed'
      task.completed_at = new Date().toISOString()
      task.queue_position = undefined
    }
  }

  function handleTaskQueued(taskData: any) {
    console.log('[TaskManager] Task queued:', taskData.task_id)
    tasks.value.set(taskData.task_id, {
      task_id: taskData.task_id,
      task_type: taskData.task_type as 'backtest' | 'model_training' | 'prediction',
      status: 'queued',
      description: taskData.description,
      created_at: new Date().toISOString(),
      queue_position: taskData.queue_position,
      estimated_cpu_cores: taskData.estimated_cpu_cores,
      estimated_ram_gb: taskData.estimated_ram_gb
    })
  }

  function handleTaskDescriptionUpdate(taskData: any) {
    console.log('[TaskManager] Task description updated:', taskData.task_id, taskData.description)
    const task = tasks.value.get(taskData.task_id)
    if (task) {
      task.description = taskData.description
    }
  }

  function processQueueStatus(queueData: any) {
    // Update queued tasks
    queueData.queued_tasks?.forEach((queuedTask: any) => {
      const existingTask = tasks.value.get(queuedTask.task_id)
      if (existingTask) {
        existingTask.status = 'queued'
        existingTask.queue_position = queuedTask.queue_position
      } else {
        tasks.value.set(queuedTask.task_id, {
          task_id: queuedTask.task_id,
          task_type: queuedTask.task_type as 'backtest' | 'model_training' | 'prediction',
          status: 'queued',
          created_at: queuedTask.queued_at,
          queue_position: queuedTask.queue_position,
          estimated_cpu_cores: queuedTask.estimated_cpu_cores,
          estimated_ram_gb: queuedTask.estimated_ram_gb
        })
      }
    })

    // Update running tasks
    queueData.running_tasks?.forEach((runningTask: any) => {
      const existingTask = tasks.value.get(runningTask.task_id)
      if (existingTask) {
        existingTask.status = 'running'
        existingTask.queue_position = undefined
        // Keep existing description if present
        if (runningTask.description) {
          existingTask.description = runningTask.description
        }
      } else {
        // Set default description for running tasks on initial load
        const defaultDescription = runningTask.description || "Processing..."
        tasks.value.set(runningTask.task_id, {
          task_id: runningTask.task_id,
          task_type: runningTask.task_type as 'backtest' | 'model_training' | 'prediction',
          status: 'running',
          description: defaultDescription,
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          estimated_cpu_cores: runningTask.estimated_cpu_cores,
          estimated_ram_gb: runningTask.estimated_ram_gb
        })
      }
    })
  }

  function stopMonitoring() {
    if (!isMonitoring.value) return

    isMonitoring.value = false

    // Close SSE connection
    const eventSource = (window as any).__taskEventSource
    if (eventSource) {
      eventSource.close()
      ;(window as any).__taskEventSource = null
      console.log('[TaskManager] Closed SSE connection')
    }

    // Stop polling
    if (pollingInterval.value !== null) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }

    console.log('[TaskManager] Stopped monitoring')
  }

  return {
    // State
    tasks,
    resources,
    isMonitoring,
    isAdmin,

    // Computed
    queuedTasks,
    runningTasks,
    completedTasks,
    failedTasks,
    hasQueuedTasks,
    hasRunningTasks,
    cpuUsagePercent,
    ramUsagePercent,
    availableCpuCores,
    availableRamGB,

    // Actions
    fetchResources,
    addTask,
    updateTask,
    removeTask,
    clearCompletedTasks,
    clearAllTasks,
    startMonitoring,
    stopMonitoring
  }
})
