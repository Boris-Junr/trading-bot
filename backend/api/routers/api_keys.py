"""
API Keys Router

Endpoints for managing user API keys (Alpaca, Binance, etc.)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import get_current_user_id
from infrastructure.api_key_manager import get_api_key_manager


router = APIRouter(prefix="/api/keys", tags=["api_keys"])


class ApiKeyCreate(BaseModel):
    """Request model for creating API key."""
    provider_id: str
    environment: str
    api_key: str
    api_secret: str
    label: Optional[str] = None


class ApiKeyUpdate(BaseModel):
    """Request model for updating API key."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    label: Optional[str] = None


def create_key_hint(key: str) -> str:
    """Create a hint showing first 4 and last 4 characters."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


@router.get("/")
async def list_api_keys(user_id: str = Depends(get_current_user_id)):
    """
    List user's configured API keys (with hints, not full keys).

    Returns list of API key metadata including masked hints.
    Provider names are already included via PostgREST join.
    """
    mgr = get_api_key_manager()
    keys = mgr.list_user_api_keys(user_id=user_id)
    return keys


@router.post("/")
async def create_api_key(
    data: ApiKeyCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Store user's API credentials.

    The API key and secret are encrypted before storage.
    Only hints (first 4 + last 4 chars) are stored in plaintext.
    """
    mgr = get_api_key_manager()

    try:
        api_key_id = mgr.store_api_key(
            user_id=user_id,
            provider_id=data.provider_id,
            environment=data.environment,
            api_key=data.api_key,
            api_secret=data.api_secret,
            label=data.label,
            api_key_hint=create_key_hint(data.api_key),
            api_secret_hint=create_key_hint(data.api_secret)
        )

        return {
            "id": api_key_id,
            "message": "API key stored successfully"
        }
    except Exception as e:
        print(f"[API] Failed to store API key: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{api_key_id}")
async def update_api_key(
    api_key_id: str,
    data: ApiKeyUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update an existing API key.

    Only provided fields will be updated.
    Leave api_key/api_secret empty to keep current values.
    """
    mgr = get_api_key_manager()

    try:
        # Build update data
        update_data = {}
        if data.api_key:
            update_data['api_key'] = data.api_key
            update_data['api_key_hint'] = create_key_hint(data.api_key)
        if data.api_secret:
            update_data['api_secret'] = data.api_secret
            update_data['api_secret_hint'] = create_key_hint(data.api_secret)
        if data.label is not None:
            update_data['label'] = data.label

        success = mgr.update_api_key(
            user_id=user_id,
            api_key_id=api_key_id,
            **update_data
        )

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        return {"message": "API key updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Failed to update API key: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Deactivate an API key (soft delete).

    The key is marked as inactive but not permanently deleted.
    """
    mgr = get_api_key_manager()

    try:
        success = mgr.deactivate_api_key(user_id=user_id, api_key_id=api_key_id)

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Failed to delete API key: {e}")
        raise HTTPException(status_code=400, detail=str(e))
