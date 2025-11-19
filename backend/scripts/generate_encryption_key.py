#!/usr/bin/env python3
"""
Generate a cryptographically secure encryption key.

This script helps you create a strong encryption key and provides
instructions for secure storage.

Usage:
    python scripts/generate_encryption_key.py
"""

import secrets
import string
import os
import sys


def generate_secure_key(length: int = 43) -> str:
    """
    Generate a cryptographically secure random key.

    Args:
        length: Key length (default 43 chars for 256-bit base64)

    Returns:
        Secure random key string
    """
    # Use base64-like character set (alphanumeric + +/)
    alphabet = string.ascii_letters + string.digits + '+/'
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return key


def print_security_instructions(key: str):
    """Print the key and security instructions."""
    print("=" * 70)
    print("[*] ENCRYPTION KEY GENERATED")
    print("=" * 70)
    print()
    print("Your new encryption key:")
    print()
    print(f"  {key}")
    print()
    print("=" * 70)
    print("[*] SETUP INSTRUCTIONS")
    print("=" * 70)
    print()
    print("1. Add to your .env file:")
    print(f"   ENCRYPTION_KEY={key}")
    print()
    print("2. SECURITY CHECKLIST:")
    print("   [x] Never commit .env to git (.gitignore should block it)")
    print("   [x] Use different keys for dev/staging/production")
    print("   [x] Store production key in secrets manager (AWS/Azure/Vault)")
    print("   [x] Restrict .env file permissions: chmod 600 .env")
    print("   [x] Rotate key every 90 days in production")
    print()
    print("3. Verify .env is not in git history:")
    print('   git log --all --full-history -- "*/.env"')
    print("   (Should return empty)")
    print()
    print("4. Set file permissions (Linux/Mac):")
    print("   chmod 600 backend/.env")
    print("   chown $(whoami):$(whoami) backend/.env")
    print()
    print("=" * 70)
    print("[!] PRODUCTION DEPLOYMENT")
    print("=" * 70)
    print()
    print("For production, use a secrets manager instead of .env:")
    print()
    print("AWS Secrets Manager:")
    print(f'  aws secretsmanager create-secret \\')
    print(f'    --name trading-bot/encryption-key \\')
    print(f'    --secret-string "{key}"')
    print()
    print("Azure Key Vault:")
    print(f'  az keyvault secret set \\')
    print(f'    --vault-name trading-bot-vault \\')
    print(f'    --name encryption-key \\')
    print(f'    --value "{key}"')
    print()
    print("HashiCorp Vault:")
    print(f'  vault kv put secret/trading-bot/encryption-key \\')
    print(f'    value="{key}"')
    print()
    print("=" * 70)


def check_env_file_permissions():
    """Check if .env file has secure permissions."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

    if not os.path.exists(env_path):
        return

    # Check permissions (Unix only)
    if sys.platform != 'win32':
        stat_info = os.stat(env_path)
        mode = oct(stat_info.st_mode)[-3:]

        if mode != '600':
            print("[!] WARNING: .env file has insecure permissions!")
            print(f"   Current: {mode}")
            print("   Run: chmod 600 backend/.env")
            print()


def main():
    """Main entry point."""
    print()
    print("Generating cryptographically secure encryption key...")
    print()

    key = generate_secure_key()
    print_security_instructions(key)
    check_env_file_permissions()

    print("[+] Done! Copy the key to your .env file.")
    print()


if __name__ == '__main__':
    main()
