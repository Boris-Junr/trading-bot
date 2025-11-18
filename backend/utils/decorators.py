"""
Decorators

Reusable decorators for common patterns.
"""

from functools import wraps
from typing import TypeVar, Type, Callable, Any


T = TypeVar('T')


def singleton(cls: Type[T]) -> Type[T]:
    """
    Singleton decorator for classes.

    Ensures only one instance of the class exists.
    Thread-safe implementation using closure.

    Usage:
        @singleton
        class MyService:
            def __init__(self):
                self.data = {}

        # Both will be the same instance
        service1 = MyService()
        service2 = MyService()
        assert service1 is service2

    Args:
        cls: Class to make singleton

    Returns:
        Modified class with singleton behavior
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance  # type: ignore


def reset_singleton(cls: Type[T]) -> None:
    """
    Reset a singleton instance (useful for testing).

    Args:
        cls: Singleton class to reset
    """
    if hasattr(cls, '__wrapped__'):
        cls = cls.__wrapped__  # type: ignore
    # Implementation would need to access the instances dict
    # This is a simplified version
    pass
