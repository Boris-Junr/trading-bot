"""
Health Check Router

Simple health check endpoint to verify API is running.
"""

from fastapi import APIRouter
from api import models

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Check if the API is running"""
    return models.HealthResponse(status="ok", version="1.0.0")
