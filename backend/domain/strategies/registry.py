"""
Strategy Registry - Auto-discovery of trading strategies

Automatically discovers and registers all strategy implementations.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, List, Optional
from .base import Strategy


class StrategyRegistry:
    """
    Registry for auto-discovering and managing trading strategies.

    Strategies are automatically discovered from the implementations folder.
    Each strategy must inherit from the Strategy base class and implement
    the get_metadata() class method.
    """

    def __init__(self):
        """Initialize the registry."""
        self._strategies: Dict[str, Type[Strategy]] = {}
        self._discover_strategies()

    def _discover_strategies(self):
        """Automatically discover all strategy classes in the implementations folder."""
        implementations_dir = Path(__file__).parent / 'implementations'

        if not implementations_dir.exists():
            print(f"[StrategyRegistry] Implementations directory not found: {implementations_dir}")
            return

        # Find all Python files in implementations folder (excluding __init__.py)
        strategy_files = [
            f for f in implementations_dir.glob('*.py')
            if f.name not in ('__init__.py', '__pycache__')
        ]

        for strategy_file in strategy_files:
            module_name = f"domain.strategies.implementations.{strategy_file.stem}"

            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Find all classes that inherit from Strategy
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a Strategy subclass (but not Strategy itself)
                    if (issubclass(obj, Strategy) and
                        obj is not Strategy and
                        hasattr(obj, 'get_metadata')):

                        # Get strategy metadata
                        try:
                            metadata = obj.get_metadata()
                            strategy_name = metadata.get('name')

                            if strategy_name:
                                self._strategies[strategy_name] = obj
                                print(f"[StrategyRegistry] Registered: {strategy_name} ({obj.__name__})")
                            else:
                                print(f"[StrategyRegistry] Skipping {obj.__name__}: No 'name' in metadata")

                        except Exception as e:
                            print(f"[StrategyRegistry] Error getting metadata for {obj.__name__}: {e}")

            except Exception as e:
                print(f"[StrategyRegistry] Error loading module {module_name}: {e}")

        print(f"[StrategyRegistry] Total strategies registered: {len(self._strategies)}")

    def get_strategy_class(self, name: str) -> Optional[Type[Strategy]]:
        """
        Get a strategy class by name.

        Args:
            name: Strategy name (e.g., 'MLPredictive', 'BreakoutScalping')

        Returns:
            Strategy class or None if not found
        """
        return self._strategies.get(name)

    def get_all_strategies(self) -> Dict[str, Type[Strategy]]:
        """
        Get all registered strategies.

        Returns:
            Dictionary mapping strategy names to strategy classes
        """
        return self._strategies.copy()

    def get_available_strategies_metadata(self) -> List[dict]:
        """
        Get metadata for all available strategies.

        Returns:
            List of strategy metadata dictionaries for API consumption
        """
        metadata_list = []

        for name, strategy_class in self._strategies.items():
            try:
                metadata = strategy_class.get_metadata()

                # Format for API
                api_metadata = {
                    'value': metadata.get('name'),
                    'label': metadata.get('label'),
                    'description': metadata.get('description'),
                    'requires_model': metadata.get('requires_model', False),
                    'parameters': metadata.get('parameters', {}),
                    'category': metadata.get('category', 'general'),
                }

                metadata_list.append(api_metadata)

            except Exception as e:
                print(f"[StrategyRegistry] Error getting metadata for {name}: {e}")

        return metadata_list

    def create_strategy(self, name: str, **params) -> Optional[Strategy]:
        """
        Create a strategy instance by name.

        Args:
            name: Strategy name
            **params: Strategy-specific parameters

        Returns:
            Strategy instance or None if strategy not found
        """
        strategy_class = self.get_strategy_class(name)

        if strategy_class is None:
            print(f"[StrategyRegistry] Strategy not found: {name}")
            return None

        try:
            return strategy_class(**params)
        except Exception as e:
            print(f"[StrategyRegistry] Error creating strategy {name}: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global registry instance
_registry = None


def get_strategy_registry() -> StrategyRegistry:
    """Get or create the global strategy registry."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry
