"""
Utilities Module

Shared utility functions used across the backend.
"""

from .json_helpers import sanitize_metric, sanitize_dict, sanitize_for_json
from .decorators import singleton

__all__ = [
    # JSON helpers
    'sanitize_metric',
    'sanitize_dict',
    'sanitize_for_json',
    # Decorators
    'singleton',
]
