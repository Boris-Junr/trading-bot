# System Monitoring & Resource Management

Real-time system resource monitoring, intelligent task queuing, and background job execution with CPU/RAM tracking, automatic task scheduling, and Server-Sent Events for live updates.

## Overview

The system monitoring infrastructure provides:
- Dynamic CPU and RAM resource monitoring
- Intelligent task queue with priority-based execution
- Automatic resource-based task scheduling
- Real-time task status updates via Server-Sent Events (SSE)
- Background task execution with progress tracking
- Development mode with relaxed resource constraints
- Multi-user support with admin/non-admin views

## Architecture

```
User Request (Frontend)
    ↓ POST /api/backtests/run (or predictions, model training)
Backend API (FastAPI)
    ↓
Resource Monitor
    ├─ Check available CPU cores
    ├─ Check available RAM
    └─ Predict resource consumption
        ↓
    Can run task?
        ├─→ NO: Queue task (TaskQueue)
        │       ├─ Add to priority queue
        │       ├─ Emit task_queued event (SSE)
        │       └─ Wait for resources
        │           ↓
        │       Queue Worker (background)
        │           └─ Check every 5 seconds
        │               └─ Execute when resources available
        │
        └─→ YES: Run immediately
                ├─ Register as running task
                ├─ Emit task_running event (SSE)
                ├─ Execute in thread pool
                └─ Emit task_completed event (SSE)
                    ↓
Frontend (Vue 3 + Pinia)
    ├─ SSE connection (/api/system/task-events)
    ├─ Real-time task updates
    ├─ Real-time CPU/RAM metrics (admin only)
    └─ Status Center UI
```

## Backend Implementation

### Files

- **[backend/infrastructure/resource_manager.py](../../backend/infrastructure/resource_manager.py)** - Resource monitoring and task queue
- **[backend/api/routers/system.py](../../backend/api/routers/system.py)** - System monitoring API endpoints
- **[backend/api/routers/backtests.py](../../backend/api/routers/backtests.py:296-468)** - Backtest endpoint with task queuing
- **[backend/api/routers/predictions.py](../../backend/api/routers/predictions.py)** - Prediction endpoint with task queuing

### Core Components

#### 1. Resource Monitor

Monitors system CPU cores and RAM availability with intelligent resource prediction.

**Initialization:**
```python
from infrastructure.resource_manager import get_resource_monitor, TaskType

resource_monitor = get_resource_monitor()
```

**Resource Requirements by Task Type:**
```python
TASK_RESOURCE_REQUIREMENTS = {
    TaskType.BACKTEST: ResourceRequirements(cpu_cores=1.0, ram_gb=0.5),
    TaskType.MODEL_TRAINING: ResourceRequirements(cpu_cores=2.0, ram_gb=1.5),
    TaskType.PREDICTION: ResourceRequirements(cpu_cores=0.5, ram_gb=0.3),
}
```

**Check if Resources Available:**
```python
can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

if not can_run:
    print(f"Cannot run: {reason}")
    # Example: "Insufficient RAM: need 0.5GB, available 0.3GB, would leave 0.1GB (min: 0.2GB)"
```

**How It Works:**
1. Measures current CPU usage (via `psutil.cpu_percent()`)
2. Calculates available cores: `total_cores × (1 - cpu_percent/100)`
3. Measures available RAM (via `psutil.virtual_memory().available`)
4. Predicts resource consumption (assumes 80% of requirements in production, 50% in dev mode)
5. Checks if predicted available resources stay above minimum thresholds (20% buffer in production, 5% in dev mode)

**Example Log Output:**
```
[ResourceMonitor] Total resources: 8 cores, 16.00 GB RAM
[ResourceMonitor] Minimum thresholds: 1.60 cores, 3.20 GB RAM
[ResourceMonitor] Consumption factor: 80%

[ResourceCheck] Task: backtest
[ResourceCheck] Current available: 6.40 cores, 12.50 GB RAM
[ResourceCheck] Task requires: 1.00 cores, 0.50 GB RAM
[ResourceCheck] Predicted consumption (80%): 0.80 cores, 0.40 GB RAM
[ResourceCheck] After task starts: 5.60 cores, 12.10 GB RAM
[ResourceCheck] Minimum thresholds: 1.60 cores, 3.20 GB RAM
[ResourceCheck] CPU OK: True, RAM OK: True
[ResourceCheck] APPROVED: Can run: 5.60 cores and 12.10GB RAM will remain
```

**Development Mode:**

Set environment variable to enable lenient resource checks:
```bash
export TRADING_BOT_DEV_MODE=true
```

Development mode uses:
- 5% buffer (vs 20% production)
- 50% consumption factor (vs 80% production)
- Allows more tasks to run concurrently on limited hardware

#### 2. Task Queue

Priority-based task queue with automatic execution when resources become available.

**Enqueue a Task:**
```python
from infrastructure.resource_manager import get_task_queue, TaskType

task_queue = get_task_queue()

# Define async task function
async def my_backtest_task():
    # CPU-intensive work
    result = await asyncio.to_thread(
        backtest_service.run_backtest,
        strategy='MLPredictive',
        symbol='BTC_USDT',
        start_date='2024-01-01',
        end_date='2024-01-31',
        initial_cash=10000.0
    )
    return result

# Queue task
task_id = await task_queue.enqueue(
    TaskType.BACKTEST,
    my_backtest_task,
    priority=0,              # Higher priority = runs sooner
    user_id='user_123'       # Optional: for multi-user filtering
)

print(f"Task queued: {task_id}")
```

**Register Immediately Running Task:**

For tasks that start immediately (without queueing):
```python
# Register task so it appears in Status Center
await task_queue.register_running_task(
    task_type=TaskType.BACKTEST,
    task_func=my_backtest_task,
    task_id='my-custom-id',
    user_id='user_123'
)
```

**Update Task Description (Live Progress):**
```python
# Send progress updates to frontend
await task_queue.update_task_description(
    task_id='my-custom-id',
    description='📊 Backtesting day 15 of 30...'
)
```

**Background Queue Worker:**

Automatically started on application startup:
```python
from infrastructure.resource_manager import start_queue_worker

# Start worker that checks every 5 seconds
await start_queue_worker(check_interval=5.0)
```

The worker:
- Runs continuously in the background
- Checks queue every 5 seconds
- Executes next task if resources are available
- Emits SSE events on task state changes

**Task Lifecycle:**

```
Task Created
    ↓
enqueue() → task_queued event (SSE)
    ↓
Queue Worker checks resources
    ├─→ Resources insufficient → Stay in queue
    └─→ Resources available → Execute
            ↓
        task_running event (SSE)
            ↓
        Execute task function
            ↓
        task_completed event (SSE)
```

#### 3. Server-Sent Events (SSE)

Real-time task updates streamed to frontend via SSE.

**Event Types:**

| Event | Description | Payload |
|-------|-------------|---------|
| `initial_state` | Sent on connection | Current queue + running tasks |
| `task_queued` | Task added to queue | `task_id`, `task_type`, `queue_position`, `estimated_cpu_cores`, `estimated_ram_gb` |
| `task_running` | Task started execution | `task_id`, `task_type`, `estimated_cpu_cores`, `estimated_ram_gb` |
| `task_completed` | Task finished | `task_id`, `task_type`, `success` |
| `task_description_update` | Progress update | `task_id`, `description` |
| `heartbeat` | Periodic health check (every 5s) | Current resources (CPU/RAM) - admin only |

**All events include:**
- `timestamp`: ISO format timestamp
- `resources`: Current CPU/RAM stats (admin users only)

**Example Event Stream:**
```javascript
// Initial state
data: {"type":"initial_state","data":{"queued_count":0,"running_count":1,"queued_tasks":[],"running_tasks":[...]}}

// Task queued
data: {"type":"task_queued","data":{"task_id":"abc-123","task_type":"backtest","queue_position":1}}

// Task started
data: {"type":"task_running","data":{"task_id":"abc-123","task_type":"backtest"}}

// Progress update
data: {"type":"task_description_update","data":{"task_id":"abc-123","description":"📊 Backtesting day 15 of 30..."}}

// Task completed
data: {"type":"task_completed","data":{"task_id":"abc-123","task_type":"backtest","success":true}}

// Heartbeat (every 5 seconds)
data: {"type":"heartbeat","resources":{"cpu":{"total_cores":8,"available_cores":6.4,"usage_percent":20.0},"ram":{"total_gb":16.0,"available_gb":12.5,"usage_percent":21.9}}}
```

### API Endpoints

#### GET /api/system/resources

Get current system resources and task queue status.

**Authorization:** Required (JWT)

**Response:**
```json
{
  "resources": {                     // Admin users only
    "cpu": {
      "total_cores": 8,
      "available_cores": 6.4,
      "usage_percent": 20.0,
      "min_threshold_cores": 1.6
    },
    "ram": {
      "total_gb": 16.0,
      "available_gb": 12.5,
      "usage_percent": 21.9,
      "min_threshold_gb": 3.2
    },
    "buffer_percent": 20.0
  },
  "queue": {
    "queued_count": 1,
    "running_count": 2,
    "queued_tasks": [
      {
        "task_id": "abc-123",
        "task_type": "backtest",
        "priority": 0,
        "queue_position": 1,
        "estimated_cpu_cores": 1.0,
        "estimated_ram_gb": 0.5,
        "queued_at": "2024-01-15T10:30:00",
        "description": "",
        "user_id": "user-123"          // Non-admin: only own tasks
      }
    ],
    "running_tasks": [
      {
        "task_id": "def-456",
        "task_type": "prediction",
        "estimated_cpu_cores": 0.5,
        "estimated_ram_gb": 0.3,
        "description": "Generating predictions for ETH_USDT...",
        "user_id": "user-123"
      }
    ]
  },
  "is_admin": false
}
```

**Usage:**
```python
# Frontend (axios)
const response = await axios.get('/api/system/resources', {
  headers: { Authorization: `Bearer ${token}` }
})
```

#### GET /api/system/queue

Get task queue status only (no resource metrics).

**Authorization:** Required (JWT)

**Response:**
```json
{
  "queued_count": 1,
  "running_count": 2,
  "queued_tasks": [...],
  "running_tasks": [...]
}
```

#### GET /api/system/task-events

Establish SSE connection for real-time task updates.

**Authorization:** Required (JWT via query param or header)

**Query Parameters:**
- `token` (optional): JWT token (for EventSource compatibility, since EventSource doesn't support custom headers)

**Headers:**
- `Authorization` (optional): Bearer token (alternative to query param)

**Usage:**
```javascript
// Frontend (EventSource)
const token = await getAuthToken()
const eventSource = new EventSource(`/api/system/task-events?token=${token}`)

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('Event:', data.type, data)

  if (data.type === 'task_completed') {
    console.log('Task finished:', data.data.task_id)
  }
}

eventSource.onerror = (error) => {
  console.error('SSE connection error:', error)
}
```

**Admin vs Non-Admin:**

| Feature | Non-Admin Users | Admin Users |
|---------|----------------|-------------|
| Task visibility | Own tasks only | All tasks (system-wide) |
| Resource metrics | ❌ Not included | ✅ CPU/RAM stats in all events |
| Heartbeat events | ✅ Received (no resources) | ✅ Received with resources |
| Queue filtering | Filtered by user_id | Unfiltered (all users) |

## Frontend Implementation

### Files

- **[frontend/src/stores/taskManager.ts](../../frontend/src/stores/taskManager.ts)** - Pinia store for task management
- **[frontend/src/views/StatusCenterView.vue](../../frontend/src/views/StatusCenterView.vue)** - Status Center page
- **[frontend/src/components/ui/StatusCenter.vue](../../frontend/src/components/ui/StatusCenter.vue)** - Task status component
- **[frontend/src/components/ui/SystemResources.vue](../../frontend/src/components/ui/SystemResources.vue)** - Resource metrics component (admin only)

### Task Manager Store

Manages task state and SSE connection.

**Initialize Monitoring:**
```typescript
import { useTaskManagerStore } from '@/stores/taskManager'

const taskManager = useTaskManagerStore()

// Start monitoring (establishes SSE connection)
await taskManager.startMonitoring()
```

**Access Task Data:**
```typescript
// Running tasks
console.log('Running:', taskManager.runningTasks)
// [{ task_id: 'abc-123', task_type: 'backtest', status: 'running', ... }]

// Queued tasks
console.log('Queued:', taskManager.queuedTasks)
// [{ task_id: 'def-456', task_type: 'prediction', status: 'queued', queue_position: 1, ... }]

// Completed tasks
console.log('Completed:', taskManager.completedTasks)
// [{ task_id: 'ghi-789', task_type: 'backtest', status: 'completed', completed_at: '...', ... }]

// System resources (admin only)
console.log('CPU Usage:', taskManager.cpuUsagePercent)  // 25.3
console.log('RAM Usage:', taskManager.ramUsagePercent)  // 18.7
console.log('Admin?', taskManager.isAdmin)              // true/false
```

**Manually Update Tasks:**
```typescript
// Add task
taskManager.addTask({
  task_id: 'my-task-123',
  task_type: 'backtest',
  status: 'running',
  created_at: new Date().toISOString(),
  estimated_cpu_cores: 1.0,
  estimated_ram_gb: 0.5
})

// Update task
taskManager.updateTask('my-task-123', {
  status: 'completed',
  completed_at: new Date().toISOString()
})

// Remove task
taskManager.removeTask('my-task-123')

// Clear completed tasks
taskManager.clearCompletedTasks()
```

**Stop Monitoring:**
```typescript
// Close SSE connection and stop polling
taskManager.stopMonitoring()
```

### Status Center UI

**StatusCenterView.vue** displays:

**For Admin Users:**
1. **System Resources Card** - CPU/RAM metrics with usage bars
2. **Resource Summary Stats** - Total/running/queued/completed task counts
3. **Task Status** - Live running and queued tasks
4. **Recent Completed Tasks** - Last 10 completed tasks with timestamps

**For Non-Admin Users:**
1. **My Tasks Summary** - Personal task counts (running/queued/completed)
2. **Task Status** - Only your running and queued tasks
3. **Recent Completed Tasks** - Your completed tasks only

**Components:**

```vue
<template>
  <StatusCenterView>
    <!-- Admin: System Resources -->
    <SystemResources
      v-if="taskManager.isAdmin"
      :totalCores="8"
      :availableCores="6.4"
      :totalRAM="16.0"
      :availableRAM="12.5"
      :minCores="1.6"
      :minRAM="3.2"
      :bufferPercent="20"
    />

    <!-- Task Status (all users) -->
    <StatusCenter
      :runningTasks="taskManager.runningTasks"
      :queuedTasks="taskManager.queuedTasks"
    />
  </StatusCenterView>
</template>
```

**Task Display:**

Running tasks show:
- Task type (Backtest, Model Training, Prediction)
- Status badge (Running)
- Progress description (if available)
- Estimated CPU cores and RAM
- Animated spinner

Queued tasks show:
- Task type
- Queue position badge (#1 in queue)
- Description (if available)
- Estimated resources
- Position number indicator

Completed tasks show:
- Task type
- Completion badge
- Relative completion time ("5m ago", "2h ago")
- Resources used

## Usage Examples

### Example 1: Run Backtest with Automatic Queuing

**Backend (backtests.py:296-468):**
```python
@router.post("/run")
async def run_backtest(request: BacktestRequest, user_id: str = Depends(get_current_user_id)):
    backtest_id = str(uuid.uuid4())

    # Check resources
    resource_monitor = get_resource_monitor()
    task_queue = get_task_queue()
    can_run, reason = resource_monitor.can_run_task(TaskType.BACKTEST)

    async def run_backtest_task():
        await task_queue.update_task_description(backtest_id, "🎯 Preparing backtest...")

        result = await asyncio.to_thread(
            backtest_service.run_backtest,
            strategy=request.strategy,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_capital,
            user_id=user_id
        )

        await task_queue.update_task_description(backtest_id, f"✅ Backtest complete! Return: {result['performance']['total_return']:+.2%}")

    if not can_run:
        # Queue task
        task_id = await task_queue.enqueue(
            TaskType.BACKTEST,
            run_backtest_task,
            priority=0,
            task_id=backtest_id,
            user_id=user_id
        )

        return {
            "status": "queued",
            "backtest_id": backtest_id,
            "message": "Backtest queued. Check Status Center for progress."
        }

    # Run immediately
    await task_queue.register_running_task(
        task_type=TaskType.BACKTEST,
        task_func=run_backtest_task,
        task_id=backtest_id,
        user_id=user_id
    )

    return {
        "status": "running",
        "backtest_id": backtest_id,
        "message": "Backtest started. Check Status Center for progress."
    }
```

**Frontend:**
```typescript
// Run backtest
const response = await api.runBacktest({
  strategy: 'MLPredictive',
  symbol: 'BTC_USDT',
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  initial_capital: 10000,
  params: {}
})

console.log(response.status)  // "running" or "queued"
console.log(response.message) // "Backtest started. Check Status Center for progress."

// Task automatically appears in Status Center via SSE
```

### Example 2: Monitor System Resources (Admin Only)

```typescript
import { useTaskManagerStore } from '@/stores/taskManager'

const taskManager = useTaskManagerStore()

// Start monitoring
await taskManager.startMonitoring()

// Check if user is admin
if (taskManager.isAdmin) {
  // Access resource metrics
  console.log('CPU Usage:', taskManager.cpuUsagePercent, '%')
  console.log('Available Cores:', taskManager.availableCpuCores)
  console.log('RAM Usage:', taskManager.ramUsagePercent, '%')
  console.log('Available RAM:', taskManager.availableRamGB, 'GB')

  // Watch for high usage
  watch(() => taskManager.cpuUsagePercent, (usage) => {
    if (usage > 90) {
      console.warn('⚠️ High CPU usage:', usage, '%')
    }
  })
}
```

### Example 3: Custom Task with Progress Updates

```python
async def my_custom_task():
    task_queue = get_task_queue()
    task_id = str(uuid.uuid4())

    await task_queue.update_task_description(task_id, "🚀 Starting custom task...")
    await asyncio.sleep(2)

    await task_queue.update_task_description(task_id, "📊 Processing data (50%)...")
    # Do work
    await asyncio.sleep(2)

    await task_queue.update_task_description(task_id, "✅ Custom task complete!")

# Register and run
await task_queue.register_running_task(
    task_type=TaskType.BACKTEST,  # Or custom type
    task_func=my_custom_task,
    task_id='custom-123',
    user_id='user-123'
)
```

Frontend sees live updates in Status Center:
```
🚀 Starting custom task...
  ↓ (2 seconds later)
📊 Processing data (50%)...
  ↓ (2 seconds later)
✅ Custom task complete!
  ↓
Task moves to "Completed" section
```

## Performance Considerations

### Resource Thresholds

**Production (default):**
- Buffer: 20% of total resources reserved
- Consumption factor: 80% (assumes tasks use 80% of estimated resources)
- Example (8-core, 16GB machine):
  - Minimum: 1.6 cores, 3.2GB RAM must remain free
  - Backtest estimated: 1.0 cores, 0.5GB RAM
  - Actual consumption predicted: 0.8 cores, 0.4GB RAM
  - Allows ~6 backtests concurrently before queueing

**Development mode (`TRADING_BOT_DEV_MODE=true`):**
- Buffer: 5% of total resources
- Consumption factor: 50% (more lenient)
- Example (8-core, 16GB machine):
  - Minimum: 0.4 cores, 0.8GB RAM must remain free
  - Allows many more concurrent tasks (good for testing on laptops)

### SSE vs Polling

**SSE (default):**
- Real-time updates with sub-second latency
- No polling overhead
- Auto-reconnects on connection loss
- Heartbeat every 5 seconds keeps connection alive

**Polling (fallback):**
- Activated only if SSE connection permanently fails
- Polls every 2 seconds
- Higher latency and server load
- Used as last resort

### Task Cleanup

Completed tasks remain in memory until:
- User manually clears via "Clear All" button
- Page is refreshed (tasks re-loaded from server)
- User logs out

**Best Practice:**
```typescript
// Periodically clear old completed tasks
setInterval(() => {
  const taskManager = useTaskManagerStore()
  const oldThreshold = Date.now() - 3600000  // 1 hour ago

  taskManager.completedTasks.forEach(task => {
    if (new Date(task.completed_at).getTime() < oldThreshold) {
      taskManager.removeTask(task.task_id)
    }
  })
}, 600000)  // Clean up every 10 minutes
```

## Troubleshooting

### Tasks Not Appearing in Status Center

**Check SSE connection:**
```typescript
const taskManager = useTaskManagerStore()
console.log('Monitoring:', taskManager.isMonitoring)  // Should be true
```

**Check browser console for SSE errors:**
```
[TaskManager] ❌ SSE connection error: ...
[TaskManager] EventSource readyState: 2 (CLOSED)
```

**Solution:** Check CORS configuration, ensure token is valid, check server logs.

### Tasks Stuck in Queue

**Check resource availability:**
```bash
# View system resources
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/system/resources

# Check queue status
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/system/queue
```

**Common causes:**
1. Other tasks consuming resources
2. System under heavy load (>80% CPU/RAM)
3. Queue worker not running (check server logs for `[QueueWorker] Started`)

**Solution:** Wait for tasks to complete, or enable development mode for more lenient resource checks.

### SSE Connection Dropping

**Symptoms:**
```
[TaskManager] ⚠️ SSE permanently closed, falling back to polling mode
```

**Common causes:**
1. Nginx/proxy buffering SSE responses
2. Firewall blocking persistent connections
3. Network instability

**Solutions:**

**Nginx configuration:**
```nginx
location /api/system/task-events {
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

**Increase timeout:**
```python
# In system.py
return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=3600"  # 1 hour
    }
)
```

## Security

### Admin vs Non-Admin Access

**Authorization Check:**
```python
from api.auth import is_admin_user

is_admin = await is_admin_user(authorization_header)

if is_admin:
    # Show all tasks, include resource metrics
    queue_status = task_queue.get_queue_status(user_id=None)
else:
    # Show only user's tasks, no resource metrics
    queue_status = task_queue.get_queue_status(user_id=current_user_id)
```

**Admin privileges:**
- See all users' tasks (system-wide)
- View CPU/RAM resource metrics
- View resource consumption in SSE events

**Non-admin users:**
- See only their own tasks
- No resource metrics (CPU/RAM stats hidden)
- SSE events filtered to their `user_id` only

### Token Authentication

**SSE with EventSource:**

Since `EventSource` doesn't support custom headers, tokens are passed as query parameters:
```javascript
const eventSource = new EventSource(`/api/system/task-events?token=${jwt_token}`)
```

**Token validation:**
```python
# Backend extracts token from query param
if token and not authorization:
    authorization = f"Bearer {token}"

# Validate
user_id = await get_current_user_id(authorization)
```

**Security note:** Tokens in URLs can be logged by proxies/servers. Consider:
1. Using short-lived tokens (15-30 min expiry)
2. Rotating tokens frequently
3. Using secure WebSockets instead (future enhancement)

## Related Documentation

- [Backtesting System](03-BACKTESTING.md) - Uses task queue for background execution
- [ML & Predictions](02-ML-PREDICTIONS.md) - Uses task queue for model training and predictions
- [Authentication & Authorization](01-AUTH.md) - Admin user management
