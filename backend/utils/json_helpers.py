"""
JSON Helpers

Utilities for handling JSON serialization issues like NaN, Inf, and None values.

Previously duplicated in backtest_service.py. Now centralized for reuse across all services.
"""

import math
from typing import Any, Dict, List, Union


def sanitize_metric(value: Union[int, float, None]) -> float:
    """
    Convert NaN and Inf values to 0.0 for JSON compliance.

    Args:
        value: Numeric value that may contain NaN or Inf

    Returns:
        Sanitized float value (NaN/Inf -> 0.0)

    Examples:
        >>> sanitize_metric(float('nan'))
        0.0
        >>> sanitize_metric(float('inf'))
        0.0
        >>> sanitize_metric(42.5)
        42.5
    """
    if value is None:
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary for JSON serialization.

    Handles:
    - NaN and Inf in numeric values
    - Nested dictionaries
    - Lists of values

    Args:
        data: Dictionary that may contain non-JSON-compliant values

    Returns:
        Sanitized dictionary safe for JSON serialization

    Examples:
        >>> sanitize_dict({'a': float('nan'), 'b': {'c': float('inf')}})
        {'a': 0.0, 'b': {'c': 0.0}}
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item) if isinstance(item, dict) else sanitize_metric(item) if isinstance(item, (int, float)) else item
                for item in value
            ]
        elif isinstance(value, (int, float)):
            result[key] = sanitize_metric(value)
        else:
            result[key] = value
    return result


def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize any object for JSON serialization.

    Handles dictionaries, lists, and primitive types.

    Args:
        obj: Object to sanitize

    Returns:
        Sanitized object safe for JSON serialization
    """
    if isinstance(obj, dict):
        return sanitize_dict(obj)
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (int, float)):
        return sanitize_metric(obj)
    else:
        return obj
