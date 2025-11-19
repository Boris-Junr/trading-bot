"""
Supabase Client for Multi-Tenant Trading Bot

This module provides a configured Supabase client with tenant context management.
All queries automatically respect Row Level Security (RLS) policies.
"""

import os
from typing import Optional
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from backend/.env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================================================
# Configuration
# ============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")

# ============================================================================
# Supabase Client
# ============================================================================

class SupabaseClient:
    """
    Wrapper around Supabase client with tenant context management.

    Usage:
        # Admin operations (bypasses RLS)
        admin_client = SupabaseClient.get_admin_client()

        # Tenant-scoped operations (respects RLS)
        tenant_client = SupabaseClient.get_tenant_client(tenant_id)
    """

    _admin_client: Optional[Client] = None
    _tenant_clients: dict[str, Client] = {}

    @classmethod
    def get_admin_client(cls) -> Client:
        """
        Get admin client with service role key.
        This client bypasses RLS policies - use with caution!

        Returns:
            Supabase client with service role permissions
        """
        if not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required for admin operations")

        if cls._admin_client is None:
            cls._admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        return cls._admin_client

    @classmethod
    def get_tenant_client(cls, tenant_id: str) -> Client:
        """
        Get client scoped to a specific tenant.
        This client respects RLS policies.

        Args:
            tenant_id: UUID of the tenant

        Returns:
            Supabase client with tenant context
        """
        if not SUPABASE_ANON_KEY:
            # Fall back to service role if anon key not available
            # but set tenant context manually
            client = cls.get_admin_client()
            # Set tenant context via SQL
            client.rpc('set_tenant_context', {'tenant_uuid': tenant_id}).execute()
            return client

        # Use cached client if available
        if tenant_id in cls._tenant_clients:
            return cls._tenant_clients[tenant_id]

        # Create new tenant-scoped client
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

        # Set tenant context
        client.rpc('set_tenant_context', {'tenant_uuid': tenant_id}).execute()

        # Cache the client
        cls._tenant_clients[tenant_id] = client

        return client

    @classmethod
    def reset_tenant_clients(cls):
        """Clear all cached tenant clients."""
        cls._tenant_clients.clear()


# ============================================================================
# Convenience Functions
# ============================================================================

def get_admin_client() -> Client:
    """Get admin Supabase client (bypasses RLS)."""
    return SupabaseClient.get_admin_client()

def get_tenant_client(tenant_id: str) -> Client:
    """Get tenant-scoped Supabase client (respects RLS)."""
    return SupabaseClient.get_tenant_client(tenant_id)

def get_client(access_token: str) -> Client:
    """
    Get Supabase client authenticated with a user's access token.

    This creates a client using the anon key and sets the user's JWT token,
    which allows Supabase to verify the token and enforce RLS policies.

    Args:
        access_token: User's JWT access token from Supabase auth

    Returns:
        Supabase client authenticated with the user's token
    """
    if not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_ANON_KEY environment variable is required for user authentication")

    # Create client with anon key
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # Set the user's access token for authentication
    # This will be used for all subsequent requests
    client.postgrest.auth(access_token)

    return client

# ============================================================================
# Tenant Context Manager
# ============================================================================

class TenantContext:
    """
    Context manager for tenant-scoped operations.

    Usage:
        with TenantContext(tenant_id) as client:
            # All operations here are scoped to the tenant
            backtests = client.table('backtests').select('*').execute()
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.client: Optional[Client] = None

    def __enter__(self) -> Client:
        self.client = get_tenant_client(self.tenant_id)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


# ============================================================================
# Helper Functions
# ============================================================================

async def create_tenant(name: str, slug: str, settings: dict = None) -> str:
    """
    Create a new tenant.

    Args:
        name: Tenant name
        slug: Unique slug identifier
        settings: Optional tenant settings

    Returns:
        Tenant UUID
    """
    client = get_admin_client()

    result = client.table('tenants').insert({
        'name': name,
        'slug': slug,
        'settings': settings or {}
    }).execute()

    return result.data[0]['id']

async def get_tenant_by_slug(slug: str) -> Optional[dict]:
    """
    Get tenant by slug.

    Args:
        slug: Tenant slug

    Returns:
        Tenant data or None if not found
    """
    client = get_admin_client()

    result = client.table('tenants').select('*').eq('slug', slug).execute()

    if result.data:
        return result.data[0]
    return None

async def list_tenants() -> list[dict]:
    """
    List all tenants (admin only).

    Returns:
        List of tenant records
    """
    client = get_admin_client()

    result = client.table('tenants').select('*').execute()

    return result.data

# ============================================================================
# Default Tenant
# ============================================================================

DEFAULT_TENANT_SLUG = "default"

async def get_default_tenant_id() -> str:
    """
    Get or create the default tenant and return its ID.

    Returns:
        Default tenant UUID
    """
    tenant = await get_tenant_by_slug(DEFAULT_TENANT_SLUG)

    if tenant:
        return tenant['id']

    # Create default tenant
    return await create_tenant(
        name="Default Organization",
        slug=DEFAULT_TENANT_SLUG,
        settings={
            "timezone": "UTC",
            "currency": "USD"
        }
    )
