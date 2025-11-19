"""
System Resources Router

Endpoints for system resource monitoring and task queue status.
Includes Server-Sent Events (SSE) for real-time task event streaming.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from infrastructure.resource_manager import get_resource_monitor, get_task_queue
from api.auth import get_current_user_id, get_current_user_info, is_admin_user

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/resources")
async def get_system_resources(
    user_id: str = Depends(get_current_user_id),
    authorization: Optional[str] = Header(None)
):
    """
    Get current system resource availability and queue status.

    Returns combined CPU/RAM resources and task queue status.
    This is the primary endpoint used by the frontend status center.

    - Non-admin users: See only their own tasks, no resource metrics
    - Admin users: See all tasks and resource metrics

    Returns:
        Dict with 'resources' (CPU/RAM, admin only), 'queue' (task status), and 'is_admin' flag
    """
    resource_monitor = get_resource_monitor()
    task_queue = get_task_queue()

    # Check if user is admin
    is_admin = await is_admin_user(authorization)

    # Filter queue by user_id for non-admin users
    queue_status = task_queue.get_queue_status(user_id=None if is_admin else user_id)

    # Only log when there's activity
    if queue_status['running_count'] > 0 or queue_status['queued_count'] > 0:
        print(f"[API] /api/system/resources - {'Admin' if is_admin else f'User {user_id[:8]}'}: {queue_status['running_count']} running, {queue_status['queued_count']} queued")

    response = {
        "queue": queue_status,
        "is_admin": is_admin
    }

    # Only include resource metrics for admin users
    if is_admin:
        response["resources"] = resource_monitor.get_resource_summary()

    return response


@router.get("/resources-only")
async def get_system_resources_only(authorization: Optional[str] = Header(None)):
    """
    Get current system resource availability (CPU/RAM only, no queue status).

    Admin-only endpoint for checking hardware resources without task queue data.

    Returns:
        Dict with 'resources' key containing CPU and RAM availability
    """
    # Check if user is admin
    is_admin = await is_admin_user(authorization)

    if not is_admin:
        return {
            "error": "Unauthorized",
            "message": "Only admin users can access resource metrics"
        }

    resource_monitor = get_resource_monitor()
    resources = resource_monitor.get_resource_summary()

    return {
        "resources": resources
    }


@router.get("/queue")
async def get_queue_status(
    user_id: str = Depends(get_current_user_id),
    authorization: Optional[str] = Header(None)
):
    """
    Get current task queue status.

    Returns information about running and queued tasks without system resources.
    Non-admin users see only their own tasks.

    Returns:
        Task queue status with counts and task details
    """
    # Check if user is admin
    is_admin = await is_admin_user(authorization)

    task_queue = get_task_queue()
    # Filter by user_id for non-admin users
    return task_queue.get_queue_status(user_id=None if is_admin else user_id)


@router.get("/task-events")
async def stream_task_events(
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Stream task status change events using Server-Sent Events (SSE).

    This endpoint establishes a persistent connection and streams real-time updates
    about task status changes and system resources.

    - Non-admin users: Receive only events for their own tasks, no resource metrics
    - Admin users: Receive all task events and resource metrics

    Events:
        - initial_state: Sent immediately upon connection with current state
        - task_running: Emitted when a task starts running
        - task_completed: Emitted when a task finishes
        - task_queued: Emitted when a new task is queued
        - heartbeat: Sent every 5 seconds (with resource updates for admins only)

    Args:
        token: JWT token as query parameter (for EventSource compatibility)
        authorization: Authorization header (alternative to token)

    Returns:
        StreamingResponse with Server-Sent Events
    """
    # EventSource doesn't support custom headers, so accept token as query param
    # Construct authorization header from token if provided
    if token and not authorization:
        authorization = f"Bearer {token}"

    # Get user ID from token
    from api.auth import get_current_user_id as _get_user_id
    try:
        user_id = await _get_user_id(authorization)
    except Exception as e:
        print(f"[SSE] Authentication failed: {e}")
        # Return error in SSE format
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Authentication required'})}\n\n"
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"}
        )

    # Check if user is admin
    is_admin = await is_admin_user(authorization)

    async def event_generator():
        task_queue = get_task_queue()
        resource_monitor = get_resource_monitor()
        event_queue = await task_queue.subscribe_to_events()

        try:
            # Send initial state with queue status (filtered for non-admin)
            queue_status = task_queue.get_queue_status(user_id=None if is_admin else user_id)
            initial_event = {
                'type': 'initial_state',
                'data': queue_status,
                'is_admin': is_admin
            }

            # Include resources for admin users only
            if is_admin:
                initial_event['resources'] = resource_monitor.get_resource_summary()

            yield f"data: {json.dumps(initial_event)}\n\n"

            # Track last heartbeat time
            last_heartbeat = asyncio.get_event_loop().time()
            heartbeat_interval = 5.0  # Send updates every 5 seconds

            # Stream events as they occur
            while True:
                try:
                    # Wait for event with timeout to allow heartbeat
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)

                    # Filter events by user_id for non-admin users
                    event_user_id = event.get('data', {}).get('user_id')
                    if not is_admin and event_user_id and event_user_id != user_id:
                        # Skip this event, it's not for this user
                        continue

                    # Remove resources from events for non-admin users
                    if not is_admin and 'resources' in event:
                        del event['resources']

                    yield f"data: {json.dumps(event)}\n\n"

                except asyncio.TimeoutError:
                    # No event received, check if it's time for heartbeat
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= heartbeat_interval:
                        heartbeat_event = {
                            'type': 'heartbeat',
                            'timestamp': datetime.now().isoformat(),
                            'is_admin': is_admin
                        }

                        # Include resource metrics for admin users only
                        if is_admin:
                            heartbeat_event['resources'] = resource_monitor.get_resource_summary()

                        yield f"data: {json.dumps(heartbeat_event)}\n\n"
                        last_heartbeat = current_time

        except asyncio.CancelledError:
            # Client disconnected
            task_queue.unsubscribe_from_events(event_queue)
            print(f"[SSE] {'Admin' if is_admin else f'User {user_id}'} disconnected from task events stream")
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
