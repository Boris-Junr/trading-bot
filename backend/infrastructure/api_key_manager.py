"""
API Key Manager

Securely manages user API keys for trading platforms (Alpaca, Binance, etc.)
Handles encryption/decryption using the encryption key from environment variables.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from infrastructure.supabase_client import get_admin_client


@dataclass
class ApiKeyCredentials:
    """Decrypted API credentials for use in trading operations."""
    api_key: str
    api_secret: str
    provider: str
    environment: str  # 'paper' or 'live'
    additional_config: Dict[str, Any]


class ApiKeyManager:
    """
    Manages encrypted API keys for users.

    Security Features:
    - Keys encrypted at rest using PGP symmetric encryption
    - Encryption key stored in environment variable (never in code/database)
    - RLS policies ensure users can only access their own keys
    - Audit logging for all key access
    - Keys never logged or exposed in plaintext
    """

    def __init__(self):
        """Initialize the API Key Manager."""
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable must be set! "
                "Generate a strong key: openssl rand -base64 32"
            )

        # Validate encryption key strength
        if len(self.encryption_key) < 32:
            raise ValueError(
                "ENCRYPTION_KEY must be at least 32 characters (256 bits). "
                "Generate a strong key: openssl rand -base64 32"
            )

        # Warn if key looks like default/example value
        weak_patterns = ['test', 'example', 'generate_with', 'password', '12345']
        if any(pattern in self.encryption_key.lower() for pattern in weak_patterns):
            raise ValueError(
                "ENCRYPTION_KEY appears to be a placeholder or weak key! "
                "Generate a cryptographically secure key: openssl rand -base64 32"
            )

    def store_api_key(
        self,
        user_id: str,
        provider_id: str,
        environment: str,
        api_key: str,
        api_secret: str,
        label: Optional[str] = None,
        api_key_hint: Optional[str] = None,
        api_secret_hint: Optional[str] = None,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store encrypted API credentials for a user.

        Args:
            user_id: User's UUID
            provider_id: Provider UUID from user_api_key_providers table
            environment: 'paper' or 'live'
            api_key: Plain API key (will be encrypted)
            api_secret: Plain API secret (will be encrypted)
            label: Optional user-friendly label
            api_key_hint: Plaintext hint (e.g., "PK12...xyz9")
            api_secret_hint: Plaintext hint (e.g., "sk12...xyz9")
            additional_config: Optional provider-specific config

        Returns:
            api_key_id: UUID of the stored credential

        Raises:
            Exception: If storage fails
        """
        supabase = get_admin_client()

        # Encrypt credentials using database function
        encrypted_key = supabase.rpc(
            'encrypt_api_credential',
            {'plaintext': api_key, 'encryption_key': self.encryption_key}
        ).execute()

        encrypted_secret = supabase.rpc(
            'encrypt_api_credential',
            {'plaintext': api_secret, 'encryption_key': self.encryption_key}
        ).execute()

        # Store encrypted credentials
        result = supabase.table('user_api_keys').insert({
            'user_id': user_id,
            'provider_id': provider_id,
            'environment': environment,
            'api_key_encrypted': encrypted_key.data,
            'api_secret_encrypted': encrypted_secret.data,
            'api_key_hint': api_key_hint,
            'api_secret_hint': api_secret_hint,
            'label': label,
            'additional_config': additional_config or {}
        }).execute()

        api_key_id = result.data[0]['id']

        # Log the action
        self._log_audit(user_id, api_key_id, 'created')

        print(f"[ApiKeyManager] Stored API key {api_key_id} for user {user_id[:8]}")
        return api_key_id

    def get_api_credentials(
        self,
        user_id: str,
        provider_id: str,
        environment: str = 'paper',
        label: Optional[str] = None
    ) -> Optional[ApiKeyCredentials]:
        """
        Retrieve and decrypt API credentials for a user.

        Args:
            user_id: User's UUID
            provider_id: Provider UUID
            environment: 'paper' or 'live'
            label: Optional specific label to retrieve

        Returns:
            ApiKeyCredentials with decrypted keys, or None if not found

        Raises:
            Exception: If decryption fails
        """
        supabase = get_admin_client()

        # Query for the API key
        query = supabase.table('user_api_keys').select('*, user_api_key_providers(name)').eq('user_id', user_id).eq('provider_id', provider_id).eq('environment', environment)

        if label:
            query = query.eq('label', label)

        result = query.execute()

        if not result.data:
            print(f"[ApiKeyManager] No API key found for user {user_id[:8]}")
            return None

        key_record = result.data[0]
        provider_name = key_record.get('user_api_key_providers', {}).get('name', 'unknown')

        # Decrypt credentials using database function
        try:
            decrypted_key = supabase.rpc(
                'decrypt_api_credential',
                {
                    'ciphertext': key_record['api_key_encrypted'],
                    'encryption_key': self.encryption_key
                }
            ).execute()

            decrypted_secret = supabase.rpc(
                'decrypt_api_credential',
                {
                    'ciphertext': key_record['api_secret_encrypted'],
                    'encryption_key': self.encryption_key
                }
            ).execute()

            credentials = ApiKeyCredentials(
                api_key=decrypted_key.data,
                api_secret=decrypted_secret.data,
                provider=provider_name,
                environment=key_record['environment'],
                additional_config=key_record.get('additional_config', {})
            )

            # Update last_used_at
            supabase.table('user_api_keys').update({
                'last_used_at': datetime.now().isoformat()
            }).eq('id', key_record['id']).execute()

            # Log the usage
            self._log_audit(user_id, key_record['id'], 'used')

            print(f"[ApiKeyManager] Retrieved {provider_name} {key_record['environment']} key for user {user_id[:8]}")
            return credentials

        except Exception as e:
            print(f"[ApiKeyManager] Failed to decrypt key: {e}")
            self._log_audit(user_id, key_record['id'], 'failed', {'error': str(e)})
            raise

    def list_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all API keys for a user (without decrypting).

        Args:
            user_id: User's UUID

        Returns:
            List of API key metadata (no sensitive data, includes hints)
        """
        supabase = get_admin_client()

        # Use PostgREST foreign key traversal to join with providers in one query
        result = supabase.table('user_api_keys').select(
            'id, provider_id, environment, label, last_used_at, created_at, api_key_hint, api_secret_hint, user_api_key_providers(display_name)'
        ).eq('user_id', user_id).order('created_at', desc=True).execute()

        # Flatten the nested provider data
        for key in result.data:
            if key.get('user_api_key_providers'):
                key['provider_display_name'] = key['user_api_key_providers']['display_name']
                del key['user_api_key_providers']

        return result.data

    def deactivate_api_key(self, user_id: str, api_key_id: str) -> bool:
        """
        Delete an API key (hard delete).

        Args:
            user_id: User's UUID
            api_key_id: API key ID to delete

        Returns:
            True if successful
        """
        supabase = get_admin_client()

        # Log before deletion
        self._log_audit(user_id, api_key_id, 'deleted')

        # Hard delete the record
        result = supabase.table('user_api_keys').delete().eq('id', api_key_id).eq('user_id', user_id).execute()

        if result.data:
            print(f"[ApiKeyManager] Permanently deleted key {api_key_id} for user {user_id[:8]}")
            return True

        return False

    def update_api_key(
        self,
        user_id: str,
        api_key_id: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_key_hint: Optional[str] = None,
        api_secret_hint: Optional[str] = None,
        label: Optional[str] = None,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing API key.

        Args:
            user_id: User's UUID
            api_key_id: API key ID to update
            api_key: New API key (optional)
            api_secret: New API secret (optional)
            api_key_hint: New API key hint (optional)
            api_secret_hint: New API secret hint (optional)
            label: New label (optional)
            additional_config: New config (optional)

        Returns:
            True if successful
        """
        supabase = get_admin_client()

        update_data = {}

        # Encrypt new credentials if provided
        if api_key:
            encrypted_key = supabase.rpc(
                'encrypt_api_credential',
                {'plaintext': api_key, 'encryption_key': self.encryption_key}
            ).execute()
            update_data['api_key_encrypted'] = encrypted_key.data
            if api_key_hint:
                update_data['api_key_hint'] = api_key_hint

        if api_secret:
            encrypted_secret = supabase.rpc(
                'encrypt_api_credential',
                {'plaintext': api_secret, 'encryption_key': self.encryption_key}
            ).execute()
            update_data['api_secret_encrypted'] = encrypted_secret.data
            if api_secret_hint:
                update_data['api_secret_hint'] = api_secret_hint

        if label is not None:
            update_data['label'] = label

        if additional_config is not None:
            update_data['additional_config'] = additional_config

        if not update_data:
            return False

        result = supabase.table('user_api_keys').update(
            update_data
        ).eq('id', api_key_id).eq('user_id', user_id).execute()

        if result.data:
            self._log_audit(user_id, api_key_id, 'updated', {'fields': list(update_data.keys())})
            print(f"[ApiKeyManager] Updated key {api_key_id} for user {user_id[:8]}")
            return True

        return False

    def _log_audit(
        self,
        user_id: str,
        api_key_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log API key access for audit trail.

        Args:
            user_id: User's UUID
            api_key_id: API key ID
            action: Action performed ('created', 'used', 'updated', 'deleted', 'failed')
            details: Optional additional details
        """
        try:
            supabase = get_admin_client()
            supabase.table('api_key_audit_log').insert({
                'user_id': user_id,
                'api_key_id': api_key_id,
                'action': action,
                'details': details or {}
            }).execute()
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            print(f"[ApiKeyManager] Audit logging failed: {e}")


# Singleton instance
_api_key_manager: Optional[ApiKeyManager] = None


def get_api_key_manager() -> ApiKeyManager:
    """Get the singleton ApiKeyManager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = ApiKeyManager()
    return _api_key_manager
