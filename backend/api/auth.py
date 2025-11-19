"""
Authentication dependencies for API endpoints.

Verifies Supabase JWT tokens using the Supabase client library.
This approach is more secure and doesn't rely on deprecated JWT secrets.
"""
from fastapi import Header, HTTPException, status
from typing import Optional
from infrastructure.supabase_client import get_client


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and verify user ID from Supabase JWT token using Supabase client.

    This method uses Supabase's built-in token verification which:
    - Works with modern JWT Signing Keys (not deprecated JWT secret)
    - Handles token expiration, revocation, and validation
    - Is maintained and updated by Supabase

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User ID extracted from verified JWT token

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>" format
        parts = authorization.split()
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )

        scheme, token = parts
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Use Supabase client to verify the token
        # This creates a client with the user's token, which automatically validates it
        supabase = get_client(token)

        # Verify token by getting user info
        # This will raise an exception if token is invalid/expired
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract user ID from verified user object
        user_id = user_response.user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user ID",
            )

        return user_id

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other errors (network, Supabase API, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional authentication - returns user ID if token is valid, None otherwise.

    Useful for endpoints that can work with or without authentication.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User ID if token is valid, None otherwise
    """
    if not authorization:
        return None

    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


async def is_admin_user(authorization: Optional[str] = Header(None)) -> bool:
    """
    Check if the authenticated user is an admin by querying the user_role_assignments table.

    Uses the is_user_admin() database function which checks if the user has the 'admin' role
    in the user_role_assignments table.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        True if user is admin, False otherwise
    """
    if not authorization:
        return False

    try:
        # Extract token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return False

        token = parts[1]
        supabase = get_client(token)
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            return False

        user_id = user_response.user.id

        # Query the database function to check if user is admin
        response = supabase.rpc('is_user_admin', {'check_user_id': user_id}).execute()

        # The function returns a boolean
        is_admin = response.data if response.data is not None else False

        return is_admin

    except Exception as e:
        print(f"[Auth] Error checking admin status: {e}")
        import traceback
        traceback.print_exc()
        return False


async def get_current_user_info(authorization: Optional[str] = Header(None)) -> dict:
    """
    Get current user information including ID and admin status.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Dict with user_id and is_admin fields

    Raises:
        HTTPException: If token is missing or invalid
    """
    user_id = await get_current_user_id(authorization)
    is_admin = await is_admin_user(authorization)

    return {
        "user_id": user_id,
        "is_admin": is_admin
    }
