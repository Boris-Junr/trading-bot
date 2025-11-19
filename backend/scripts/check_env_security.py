#!/usr/bin/env python3
"""
Security audit script for .env file configuration.

Checks for common security issues with environment variable configuration.

Usage:
    python scripts/check_env_security.py
"""

import os
import sys
import re
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_env_file_exists() -> tuple[bool, str]:
    """Check if .env file exists."""
    env_path = Path(__file__).parent.parent / '.env'

    if not env_path.exists():
        return False, "❌ .env file not found. Run: cp .env.example .env"

    return True, "✅ .env file exists"


def check_gitignore() -> tuple[bool, str]:
    """Check if .env is in .gitignore."""
    gitignore_path = Path(__file__).parent.parent.parent / '.gitignore'

    if not gitignore_path.exists():
        return False, "⚠️  .gitignore not found"

    with open(gitignore_path, 'r') as f:
        content = f.read()

    patterns = ['.env', '*.env', '.env.local', '.env.*.local']
    found = any(pattern in content for pattern in patterns)

    if found:
        return True, "✅ .env is in .gitignore"
    else:
        return False, "❌ .env not found in .gitignore!"


def check_git_history() -> tuple[bool, str]:
    """Check if .env was ever committed to git."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'log', '--all', '--full-history', '--', '*/.env'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        if result.stdout.strip():
            return False, "❌ .env file found in git history! Use git filter-repo to remove"
        else:
            return True, "✅ .env not in git history"

    except Exception as e:
        return None, f"⚠️  Could not check git history: {e}"


def check_encryption_key_strength() -> tuple[bool, str]:
    """Check if ENCRYPTION_KEY is strong."""
    env_path = Path(__file__).parent.parent / '.env'

    if not env_path.exists():
        return None, "⚠️  Cannot check - .env file missing"

    with open(env_path, 'r') as f:
        content = f.read()

    # Find ENCRYPTION_KEY
    match = re.search(r'^ENCRYPTION_KEY=(.+)$', content, re.MULTILINE)

    if not match:
        return False, "❌ ENCRYPTION_KEY not set in .env"

    key = match.group(1).strip()

    # Check for placeholder values
    weak_patterns = ['generate_with', 'your_', 'example', 'test', 'password', '12345']
    if any(pattern in key.lower() for pattern in weak_patterns):
        return False, f"❌ ENCRYPTION_KEY appears to be a placeholder: {key[:20]}..."

    # Check length
    if len(key) < 32:
        return False, f"❌ ENCRYPTION_KEY too short: {len(key)} chars (minimum 32)"

    return True, f"✅ ENCRYPTION_KEY is strong ({len(key)} chars)"


def check_file_permissions() -> tuple[bool, str]:
    """Check .env file permissions (Unix only)."""
    if sys.platform == 'win32':
        return None, "⚠️  Permission check skipped (Windows)"

    env_path = Path(__file__).parent.parent / '.env'

    if not env_path.exists():
        return None, "⚠️  Cannot check - .env file missing"

    stat_info = env_path.stat()
    mode = oct(stat_info.st_mode)[-3:]

    if mode == '600':
        return True, f"✅ .env permissions are secure (600)"
    else:
        return False, f"❌ .env permissions too open ({mode}). Run: chmod 600 backend/.env"


def check_backup_files() -> tuple[bool, str]:
    """Check for .env backup files that might be committed."""
    backend_path = Path(__file__).parent.parent
    backup_patterns = ['.env.backup', '.env.old', '.env.bak', '.env~']

    found = []
    for pattern in backup_patterns:
        if (backend_path / pattern).exists():
            found.append(pattern)

    if found:
        return False, f"⚠️  Backup files found: {', '.join(found)} (delete or add to .gitignore)"
    else:
        return True, "✅ No .env backup files found"


def check_example_file() -> tuple[bool, str]:
    """Check if .env.example exists and is up to date."""
    env_path = Path(__file__).parent.parent / '.env'
    example_path = Path(__file__).parent.parent / '.env.example'

    if not example_path.exists():
        return False, "⚠️  .env.example not found (recommended for documentation)"

    if not env_path.exists():
        return None, "⚠️  Cannot compare - .env file missing"

    # Read both files
    with open(env_path, 'r') as f:
        env_keys = set(re.findall(r'^([A-Z_]+)=', f.read(), re.MULTILINE))

    with open(example_path, 'r') as f:
        example_keys = set(re.findall(r'^([A-Z_]+)=', f.read(), re.MULTILINE))

    # Find keys in .env but not in .env.example
    missing = env_keys - example_keys

    if missing:
        return False, f"⚠️  Keys in .env but not in .env.example: {', '.join(missing)}"
    else:
        return True, "✅ .env.example is up to date"


def main():
    """Run all security checks."""
    print()
    print(f"{Colors.BOLD}🔒 ENVIRONMENT SECURITY AUDIT{Colors.RESET}")
    print("=" * 70)
    print()

    checks = [
        ("File Existence", check_env_file_exists),
        ("Gitignore Configuration", check_gitignore),
        ("Git History", check_git_history),
        ("Encryption Key Strength", check_encryption_key_strength),
        ("File Permissions", check_file_permissions),
        ("Backup Files", check_backup_files),
        ("Example File Sync", check_example_file),
    ]

    results = []
    for name, check_func in checks:
        passed, message = check_func()
        results.append((name, passed, message))

        # Color code the output
        if passed is True:
            color = Colors.GREEN
        elif passed is False:
            color = Colors.RED
        else:
            color = Colors.YELLOW

        print(f"{color}{message}{Colors.RESET}")

    print()
    print("=" * 70)

    # Summary
    passed = sum(1 for _, p, _ in results if p is True)
    failed = sum(1 for _, p, _ in results if p is False)
    warnings = sum(1 for _, p, _ in results if p is None)

    print(f"{Colors.BOLD}SUMMARY:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Failed: {failed}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠️  Warnings: {warnings}{Colors.RESET}")
    print()

    if failed > 0:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  Security issues detected! Fix them before deploying.{Colors.RESET}")
        print()
        sys.exit(1)
    elif warnings > 0:
        print(f"{Colors.YELLOW}✓ No critical issues, but review warnings.{Colors.RESET}")
        print()
        sys.exit(0)
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All security checks passed!{Colors.RESET}")
        print()
        sys.exit(0)


if __name__ == '__main__':
    main()
