"""
System Resources Router

Endpoints for system resource monitoring and task queue status.
Includes Server-Sent Events (SSE) for real-time task event streaming.
"""

import json
import asyncio
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from infrastructure.resource_manager import get_resource_monitor, get_task_queue

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/resources")
async def get_system_resources():
    """
    Get current system resource availability and queue status.

    Returns combined CPU/RAM resources and task queue status.
    This is the primary endpoint used by the frontend status center.

    Returns:
        Dict with 'resources' (CPU/RAM) and 'queue' (task status) keys
    """
    resource_monitor = get_resource_monitor()
    task_queue = get_task_queue()

    resources = resource_monitor.get_resource_summary()
    queue_status = task_queue.get_queue_status()

    # Log every status check for debugging
    print(f"[API] /api/system/resources polled - Running: {queue_status['running_count']}, Queued: {queue_status['queued_count']}")

    return {
        "resources": resources,
        "queue": queue_status
    }


@router.get("/resources-only")
async def get_system_resources_only():
    """
    Get current system resource availability (CPU/RAM only, no queue status).

    Useful when you only need to check hardware resources without task queue data.

    Returns:
        Dict with 'resources' key containing CPU and RAM availability
    """
    resource_monitor = get_resource_monitor()
    resources = resource_monitor.get_resource_summary()

    return {
        "resources": resources
    }


@router.get("/queue")
async def get_queue_status():
    """
    Get current task queue status.

    Returns information about running and queued tasks without system resources.

    Returns:
        Task queue status with counts and task details
    """
    task_queue = get_task_queue()
    return task_queue.get_queue_status()


@router.get("/task-events")
async def stream_task_events():
    """
    Stream task status change events using Server-Sent Events (SSE).

    This endpoint establishes a persistent connection and streams real-time updates
    about task status changes and system resources.

    Events:
        - initial_state: Sent immediately upon connection with current state
        - task_running: Emitted when a task starts running
        - task_completed: Emitted when a task finishes
        - task_queued: Emitted when a new task is queued
        - heartbeat: Sent every 5 seconds with updated CPU/RAM resources

    Returns:
        StreamingResponse with Server-Sent Events
    """
    async def event_generator():
        task_queue = get_task_queue()
        resource_monitor = get_resource_monitor()
        event_queue = await task_queue.subscribe_to_events()

        try:
            # Send initial state with queue status AND resources
            queue_status = task_queue.get_queue_status()
            resources = resource_monitor.get_resource_summary()
            initial_event = {
                'type': 'initial_state',
                'data': queue_status,
                'resources': resources
            }
            yield f"data: {json.dumps(initial_event)}\n\n"

            # Track last heartbeat time
            last_heartbeat = asyncio.get_event_loop().time()
            heartbeat_interval = 5.0  # Send resource updates every 5 seconds

            # Stream events as they occur (each includes updated resources)
            while True:
                try:
                    # Wait for event with timeout to allow heartbeat
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # No event received, check if it's time for heartbeat
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= heartbeat_interval:
                        # Send heartbeat with current CPU/RAM resources
                        resources = resource_monitor.get_resource_summary()
                        heartbeat_event = {
                            'type': 'heartbeat',
                            'timestamp': datetime.now().isoformat(),
                            'resources': resources
                        }
                        yield f"data: {json.dumps(heartbeat_event)}\n\n"
                        last_heartbeat = current_time

        except asyncio.CancelledError:
            # Client disconnected
            task_queue.unsubscribe_from_events(event_queue)
            print("[SSE] Client disconnected from task events stream")
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
            "Connection": "keep-alive",
        }
    )
