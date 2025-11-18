"""
API Utilities

Shared helper functions for API endpoints, particularly for Server-Sent Events (SSE).
"""

import json
from typing import Callable, Any
from fastapi.responses import StreamingResponse


def sse_response(generator: Callable) -> StreamingResponse:
    """
    Create a StreamingResponse configured for Server-Sent Events.
    
    Args:
        generator: Async generator function that yields SSE events
        
    Returns:
        StreamingResponse configured for SSE with proper headers
        
    Example:
        ```python
        async def event_generator():
            yield format_sse_event("message", {"data": "hello"})
            
        @router.get("/stream")
        async def stream():
            return sse_response(event_generator())
        ```
    """
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


def format_sse_event(event_type: str, data: Any) -> str:
    """
    Format data as a Server-Sent Event.
    
    Args:
        event_type: Type of event (e.g., "message", "heartbeat", "error")
        data: Data to send (will be JSON-encoded)
        
    Returns:
        Formatted SSE event string
        
    Example:
        >>> format_sse_event("update", {"progress": 50})
        'event: update\ndata: {"progress": 50}\n\n'
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def format_sse_heartbeat() -> str:
    """
    Create a heartbeat event for SSE connections.
    
    Heartbeats keep the connection alive and help detect disconnections.
    
    Returns:
        Formatted heartbeat SSE event
    """
    return ": heartbeat\n\n"
