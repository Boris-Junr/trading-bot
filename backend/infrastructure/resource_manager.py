"""
Resource Manager - Monitor system resources and manage task queuing.

Provides dynamic resource monitoring (CPU cores, RAM) and intelligent task
queuing based on actual hardware availability rather than hard limits.
"""

import psutil
import asyncio
import uuid
import os
from typing import Dict, Optional, Tuple, Callable, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import deque
import json


class TaskType(Enum):
    """Types of tasks with different resource requirements."""
    BACKTEST = "backtest"
    MODEL_TRAINING = "model_training"
    PREDICTION = "prediction"


@dataclass
class ResourceRequirements:
    """Resource requirements for a task."""
    cpu_cores: float  # Number of CPU cores needed
    ram_gb: float     # GB of RAM needed


@dataclass
class SystemResources:
    """Current system resource availability."""
    total_cpu_cores: int
    available_cpu_cores: float
    total_ram_gb: float
    available_ram_gb: float
    cpu_percent: float
    ram_percent: float


# Resource requirements per task type (realistic estimates based on actual usage)
TASK_RESOURCE_REQUIREMENTS: Dict[TaskType, ResourceRequirements] = {
    TaskType.BACKTEST: ResourceRequirements(cpu_cores=1.0, ram_gb=0.5),      # Typical backtests use <500MB
    TaskType.MODEL_TRAINING: ResourceRequirements(cpu_cores=2.0, ram_gb=1.5), # Gradient boosting typically 1-2GB
    TaskType.PREDICTION: ResourceRequirements(cpu_cores=0.5, ram_gb=0.3),     # Lightweight inference
}


class ResourceMonitor:
    """
    Monitor system resources (CPU cores, RAM).

    Uses absolute values (cores, GB) instead of percentages for
    hardware-independent resource management.
    """

    def __init__(self, buffer_percent: float = 0.20):
        """
        Initialize resource monitor.

        Args:
            buffer_percent: Percentage of total resources to keep as buffer (default 20%)
        """
        # Check for development mode (less strict resource requirements)
        is_dev_mode = os.getenv('TRADING_BOT_DEV_MODE', 'false').lower() == 'true'

        if is_dev_mode:
            # Development mode: Only 5% buffer (very lenient)
            self.buffer_percent = 0.05
            self.consumption_factor = 0.50  # Only assume 50% consumption in dev mode
            print("=" * 80)
            print("[ResourceMonitor] DEVELOPMENT MODE ENABLED")
            print("[ResourceMonitor] Buffer: 5% (vs 20% production)")
            print("[ResourceMonitor] Consumption factor: 50% (vs 80% production)")
            print("=" * 80)
        else:
            self.buffer_percent = buffer_percent
            self.consumption_factor = 0.80  # Assume 80% consumption in production

        self.total_cpu_cores = psutil.cpu_count(logical=True)
        self.total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)

        # Calculate minimum thresholds
        self.min_cpu_cores = self.total_cpu_cores * self.buffer_percent
        self.min_ram_gb = self.total_ram_gb * self.buffer_percent

        print(f"[ResourceMonitor] Total resources: {self.total_cpu_cores} cores, {self.total_ram_gb:.2f} GB RAM")
        print(f"[ResourceMonitor] Minimum thresholds: {self.min_cpu_cores:.2f} cores, {self.min_ram_gb:.2f} GB RAM")
        print(f"[ResourceMonitor] Consumption factor: {self.consumption_factor * 100:.0f}%")

    def get_current_resources(self) -> SystemResources:
        """
        Get current system resource availability.

        Returns:
            SystemResources object with current availability
        """
        # CPU availability
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # Available cores = total cores * (1 - cpu_percent/100)
        available_cpu_cores = self.total_cpu_cores * (1 - cpu_percent / 100)

        # RAM availability
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        available_ram_gb = mem.available / (1024 ** 3)

        return SystemResources(
            total_cpu_cores=self.total_cpu_cores,
            available_cpu_cores=available_cpu_cores,
            total_ram_gb=self.total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_percent=cpu_percent,
            ram_percent=ram_percent
        )

    def can_run_task(self, task_type: TaskType, consumption_factor: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if a task can run without dropping resources below minimum thresholds.

        Uses predictive check: estimates consumption based on task type
        to see if it would drop available resources below buffer thresholds.

        Args:
            task_type: Type of task to check
            consumption_factor: Factor of estimated consumption (uses instance default if None)

        Returns:
            Tuple of (can_run: bool, reason: str)
        """
        # Use instance consumption factor if not provided
        if consumption_factor is None:
            consumption_factor = self.consumption_factor

        resources = self.get_current_resources()
        requirements = TASK_RESOURCE_REQUIREMENTS[task_type]

        # Calculate predicted consumption
        predicted_cpu_consumption = requirements.cpu_cores * consumption_factor
        predicted_ram_consumption = requirements.ram_gb * consumption_factor

        # Predict available resources after starting this task
        predicted_cpu_available = resources.available_cpu_cores - predicted_cpu_consumption
        predicted_ram_available = resources.available_ram_gb - predicted_ram_consumption

        # Check if predicted availability would be above minimum thresholds
        cpu_ok = predicted_cpu_available >= self.min_cpu_cores
        ram_ok = predicted_ram_available >= self.min_ram_gb

        # Detailed logging for debugging
        print(f"\n[ResourceCheck] Task: {task_type.value}")
        print(f"[ResourceCheck] Current available: {resources.available_cpu_cores:.2f} cores, {resources.available_ram_gb:.2f} GB RAM")
        print(f"[ResourceCheck] Task requires: {requirements.cpu_cores:.2f} cores, {requirements.ram_gb:.2f} GB RAM")
        print(f"[ResourceCheck] Predicted consumption ({consumption_factor*100:.0f}%): {predicted_cpu_consumption:.2f} cores, {predicted_ram_consumption:.2f} GB RAM")
        print(f"[ResourceCheck] After task starts: {predicted_cpu_available:.2f} cores, {predicted_ram_available:.2f} GB RAM")
        print(f"[ResourceCheck] Minimum thresholds: {self.min_cpu_cores:.2f} cores, {self.min_ram_gb:.2f} GB RAM")
        print(f"[ResourceCheck] CPU OK: {cpu_ok}, RAM OK: {ram_ok}")

        if not cpu_ok:
            reason = (
                f"Insufficient CPU: need {predicted_cpu_consumption:.2f}, "
                f"available {resources.available_cpu_cores:.2f}, "
                f"would leave {predicted_cpu_available:.2f} (min: {self.min_cpu_cores:.2f})"
            )
            print(f"[ResourceCheck] BLOCKED: {reason}\n")
            return (False, reason)

        if not ram_ok:
            reason = (
                f"Insufficient RAM: need {predicted_ram_consumption:.2f}GB, "
                f"available {resources.available_ram_gb:.2f}GB, "
                f"would leave {predicted_ram_available:.2f}GB (min: {self.min_ram_gb:.2f}GB)"
            )
            print(f"[ResourceCheck] BLOCKED: {reason}\n")
            return (False, reason)

        reason = (
            f"Can run: {predicted_cpu_available:.2f} cores and "
            f"{predicted_ram_available:.2f}GB RAM will remain"
        )
        print(f"[ResourceCheck] APPROVED: {reason}\n")
        return (True, reason)

    def get_resource_summary(self) -> Dict[str, any]:
        """Get a summary of current resources for API responses."""
        resources = self.get_current_resources()
        return {
            "cpu": {
                "total_cores": resources.total_cpu_cores,
                "available_cores": round(resources.available_cpu_cores, 2),
                "usage_percent": round(resources.cpu_percent, 1),
                "min_threshold_cores": round(self.min_cpu_cores, 2)
            },
            "ram": {
                "total_gb": round(resources.total_ram_gb, 2),
                "available_gb": round(resources.available_ram_gb, 2),
                "usage_percent": round(resources.ram_percent, 1),
                "min_threshold_gb": round(self.min_ram_gb, 2)
            },
            "buffer_percent": self.buffer_percent * 100
        }


# Global resource monitor instance
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get or create the global resource monitor instance."""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor(buffer_percent=0.20)
    return _resource_monitor


@dataclass
class QueuedTask:
    """A task waiting in the queue."""
    task_id: str
    task_type: TaskType
    task_func: Callable  # The actual async function to execute
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: int = 0  # Higher priority runs first
    queued_at: datetime = field(default_factory=datetime.now)
    estimated_cpu_cores: float = 0.0
    estimated_ram_gb: float = 0.0
    description: str = ""  # Current status/log message

    def __post_init__(self):
        """Set estimated resources based on task type."""
        requirements = TASK_RESOURCE_REQUIREMENTS[self.task_type]
        self.estimated_cpu_cores = requirements.cpu_cores
        self.estimated_ram_gb = requirements.ram_gb


class TaskQueue:
    """
    Priority queue for tasks with resource-based execution control.

    Tasks are queued when resources are insufficient and automatically
    executed when resources become available.
    """

    def __init__(self, resource_monitor: ResourceMonitor):
        """
        Initialize task queue.

        Args:
            resource_monitor: ResourceMonitor instance to check availability
        """
        self.resource_monitor = resource_monitor
        self.queue: deque[QueuedTask] = deque()
        self.running_tasks: Dict[str, QueuedTask] = {}
        self._lock = asyncio.Lock()

        # Event streaming for real-time updates
        self._event_subscribers: List[asyncio.Queue] = []

    async def enqueue(
        self,
        task_type: TaskType,
        task_func: Callable,
        *args,
        priority: int = 0,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add a task to the queue.

        Args:
            task_type: Type of task
            task_func: Async function to execute
            *args: Positional arguments for task_func
            priority: Priority level (higher = runs sooner)
            task_id: Optional custom task ID (generated if not provided)
            **kwargs: Keyword arguments for task_func

        Returns:
            task_id: Unique identifier for the queued task
        """
        async with self._lock:
            if task_id is None:
                task_id = str(uuid.uuid4())
            queued_task = QueuedTask(
                task_id=task_id,
                task_type=task_type,
                task_func=task_func,
                args=args,
                kwargs=kwargs,
                priority=priority
            )

            # Insert based on priority (higher priority first)
            inserted = False
            for i, existing_task in enumerate(self.queue):
                if priority > existing_task.priority:
                    self.queue.insert(i, queued_task)
                    inserted = True
                    break

            if not inserted:
                self.queue.append(queued_task)

            # Emit task_queued event
            await self._emit_event("task_queued", {
                "task_id": task_id,
                "task_type": task_type.value,
                "estimated_cpu_cores": queued_task.estimated_cpu_cores,
                "estimated_ram_gb": queued_task.estimated_ram_gb,
                "queue_position": len(self.queue),
                "description": queued_task.description
            })

            return task_id

    async def try_execute_next(self) -> Optional[str]:
        """
        Try to execute the next task in queue if resources are available.

        Returns:
            task_id if a task was started, None otherwise
        """
        async with self._lock:
            if not self.queue:
                return None

            # Check if we can run the next task
            next_task = self.queue[0]
            can_run, reason = self.resource_monitor.can_run_task(next_task.task_type)

            if not can_run:
                return None

            # Remove from queue and start execution
            task = self.queue.popleft()
            self.running_tasks[task.task_id] = task

            # Execute task in background
            asyncio.create_task(self._execute_task(task))

            return task.task_id

    async def _execute_task(self, task: QueuedTask):
        """
        Execute a queued task and remove it from running_tasks when done.

        Args:
            task: The task to execute
        """
        print(f"[TaskQueue] ▶️  Executing task: {task.task_id} ({task.task_type.value})")
        success = False
        try:
            # Execute the task function
            await task.task_func(*task.args, **task.kwargs)
            print(f"[TaskQueue] Task completed: {task.task_id}")
            success = True
        except Exception as e:
            print(f"[TaskQueue] Task failed: {task.task_id} - {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Remove from running tasks
            async with self._lock:
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
                    print(f"[TaskQueue] 🧹 Removed completed task: {task.task_id}")
                    print(f"[TaskQueue] Remaining running tasks: {len(self.running_tasks)}")

                    # Emit task_completed event
                    await self._emit_event("task_completed", {
                        "task_id": task.task_id,
                        "task_type": task.task_type.value,
                        "success": success
                    })

    async def register_running_task(
        self,
        task_type: TaskType,
        task_func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Register a task as running (for tasks that start immediately without queueing).

        Args:
            task_type: Type of task
            task_func: Async function being executed
            *args: Positional arguments
            task_id: Optional task ID (generates new one if not provided)
            **kwargs: Keyword arguments

        Returns:
            task_id: Task identifier
        """
        async with self._lock:
            if task_id is None:
                task_id = str(uuid.uuid4())

            queued_task = QueuedTask(
                task_id=task_id,
                task_type=task_type,
                task_func=task_func,
                args=args,
                kwargs=kwargs,
                priority=0
            )

            self.running_tasks[task_id] = queued_task

            print(f"[TaskQueue] Registered running task: {task_id} ({task_type.value})")
            print(f"[TaskQueue] Total running tasks: {len(self.running_tasks)}")

            # Emit task_running event
            await self._emit_event("task_running", {
                "task_id": task_id,
                "task_type": task_type.value,
                "estimated_cpu_cores": queued_task.estimated_cpu_cores,
                "estimated_ram_gb": queued_task.estimated_ram_gb
            })

            # Execute task and ensure cleanup
            asyncio.create_task(self._execute_task(queued_task))

            return task_id

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        print(f"[TaskQueue] get_queue_status() called - running_tasks dict has {len(self.running_tasks)} items")

        running_tasks_list = [
            {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "estimated_cpu_cores": task.estimated_cpu_cores,
                "estimated_ram_gb": task.estimated_ram_gb,
                "description": task.description
            }
            for task in self.running_tasks.values()
        ]

        status = {
            "queued_count": len(self.queue),
            "running_count": len(self.running_tasks),
            "queued_tasks": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "priority": task.priority,
                    "queued_at": task.queued_at.isoformat(),
                    "estimated_cpu_cores": task.estimated_cpu_cores,
                    "estimated_ram_gb": task.estimated_ram_gb,
                    "queue_position": i + 1,
                    "description": task.description
                }
                for i, task in enumerate(self.queue)
            ],
            "running_tasks": running_tasks_list
        }

        if len(running_tasks_list) > 0:
            print(f"[TaskQueue] Returning {len(running_tasks_list)} running tasks")
            print(f"[TaskQueue] Running task IDs: {[t['task_id'] for t in running_tasks_list]}")
        else:
            print(f"[TaskQueue] No running tasks to return")

        return status

    def get_task_position(self, task_id: str) -> Optional[int]:
        """
        Get the queue position of a task.

        Returns:
            Position (1-indexed) or None if not in queue
        """
        for i, task in enumerate(self.queue):
            if task.task_id == task_id:
                return i + 1
        return None

    async def subscribe_to_events(self) -> asyncio.Queue:
        """
        Subscribe to task status change events.

        Returns:
            Queue that will receive event dictionaries
        """
        event_queue = asyncio.Queue()
        self._event_subscribers.append(event_queue)
        print(f"[TaskQueue] New event subscriber added (total: {len(self._event_subscribers)})")
        return event_queue

    def unsubscribe_from_events(self, event_queue: asyncio.Queue):
        """
        Unsubscribe from task status change events.

        Args:
            event_queue: The queue to remove from subscribers
        """
        if event_queue in self._event_subscribers:
            self._event_subscribers.remove(event_queue)
            print(f"[TaskQueue] Event subscriber removed (remaining: {len(self._event_subscribers)})")

    async def update_task_description(self, task_id: str, description: str):
        """
        Update the description of a running task and emit an event.

        Args:
            task_id: ID of the task to update
            description: New description message
        """
        async with self._lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                # Update the description field on the task object
                task.description = description
                # Emit description update event
                await self._emit_event("task_description_update", {
                    "task_id": task_id,
                    "task_type": task.task_type.value,
                    "description": description
                })
                print(f"[TaskQueue] Updated task {task_id} description: {description}")

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to all subscribers.

        Args:
            event_type: Type of event (task_queued, task_running, task_completed)
            data: Event data
        """
        # Include current CPU/RAM stats with every event
        resources = self.resource_monitor.get_resource_summary()

        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "resources": resources  # Include CPU/RAM stats
        }

        # Send to all subscribers (non-blocking)
        for subscriber in self._event_subscribers[:]:  # Copy list to avoid modification during iteration
            try:
                subscriber.put_nowait(event)
            except asyncio.QueueFull:
                # If queue is full, skip this subscriber
                print(f"[TaskQueue] WARNING: Event queue full for subscriber, skipping")
            except Exception as e:
                print(f"[TaskQueue] WARNING: Error emitting event to subscriber: {e}")


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get or create the global task queue instance."""
    global _task_queue
    if _task_queue is None:
        resource_monitor = get_resource_monitor()
        _task_queue = TaskQueue(resource_monitor)
    return _task_queue


# Background worker
_worker_task: Optional[asyncio.Task] = None
_worker_running = False


async def queue_worker(check_interval: float = 5.0):
    """
    Background worker that periodically checks if queued tasks can run.

    Args:
        check_interval: Seconds between queue checks (default 5.0)
    """
    global _worker_running
    _worker_running = True
    task_queue = get_task_queue()

    print(f"[QueueWorker] Started, checking every {check_interval}s")

    while _worker_running:
        try:
            # Check queue status
            queue_status = task_queue.get_queue_status()
            queued_count = queue_status['queued_count']
            running_count = queue_status['running_count']

            if queued_count > 0:
                print(f"\n[QueueWorker] Queue check: {queued_count} queued, {running_count} running")

            # Try to execute next task in queue
            task_id = await task_queue.try_execute_next()
            if task_id:
                print(f"[QueueWorker] Started task {task_id} from queue\n")
            elif queued_count > 0:
                print(f"[QueueWorker] Tasks queued but resources insufficient\n")

            # Wait before next check
            await asyncio.sleep(check_interval)
        except Exception as e:
            print(f"[QueueWorker] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(check_interval)


async def start_queue_worker(check_interval: float = 5.0):
    """
    Start the background queue worker.

    Args:
        check_interval: Seconds between queue checks (default 5.0)
    """
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(queue_worker(check_interval))
        print("[QueueWorker] Started")


async def stop_queue_worker():
    """Stop the background queue worker."""
    global _worker_running, _worker_task
    _worker_running = False
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
        print("[QueueWorker] Stopped")
