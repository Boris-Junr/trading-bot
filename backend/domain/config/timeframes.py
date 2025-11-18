"""
Centralized timeframe configuration for ML models and predictions.

This module eliminates duplication of timeframe-related constants across the codebase.
Previously scattered across 9 different locations in main.py, ml_service.py, and backtest_service.py.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class TimeframeConfig:
    """Configuration for a specific timeframe."""

    prediction_steps: int  # Number of steps ahead to predict
    training_days: int  # Days of historical data for training
    model_max_age_days: int  # Maximum age before model needs retraining

    @property
    def description(self) -> str:
        """Human-readable description of the timeframe configuration."""
        return (
            f"{self.prediction_steps} steps ahead, "
            f"{self.training_days} days training data, "
            f"max age {self.model_max_age_days} days"
        )


# Centralized timeframe configurations
# Single source of truth for all timeframe-related constants
TIMEFRAME_CONFIGS: Dict[str, TimeframeConfig] = {
    '1m': TimeframeConfig(
        prediction_steps=300,  # 5 hours ahead
        training_days=60,      # 2 months of training data
        model_max_age_days=2   # Retrain after 2 days
    ),
    '5m': TimeframeConfig(
        prediction_steps=144,  # 12 hours ahead
        training_days=90,      # 3 months of training data
        model_max_age_days=3   # Retrain after 3 days
    ),
    '15m': TimeframeConfig(
        prediction_steps=96,   # 24 hours ahead
        training_days=120,     # 4 months of training data
        model_max_age_days=5   # Retrain after 5 days
    ),
    '1h': TimeframeConfig(
        prediction_steps=72,   # 3 days ahead
        training_days=180,     # 6 months of training data
        model_max_age_days=7   # Retrain after 1 week
    ),
    '4h': TimeframeConfig(
        prediction_steps=42,   # 1 week ahead
        training_days=365,     # 1 year of training data
        model_max_age_days=14  # Retrain after 2 weeks
    ),
    '1d': TimeframeConfig(
        prediction_steps=30,   # 1 month ahead
        training_days=730,     # 2 years of training data
        model_max_age_days=30  # Retrain after 1 month
    ),
}


def get_timeframe_config(timeframe: str) -> TimeframeConfig:
    """
    Get configuration for a specific timeframe.

    Args:
        timeframe: Timeframe identifier (e.g., '1m', '5m', '1h', '1d')

    Returns:
        TimeframeConfig object with prediction steps, training days, and max age

    Raises:
        ValueError: If timeframe is not recognized
    """
    if timeframe not in TIMEFRAME_CONFIGS:
        raise ValueError(
            f"Unknown timeframe: {timeframe}. "
            f"Supported: {', '.join(TIMEFRAME_CONFIGS.keys())}"
        )
    return TIMEFRAME_CONFIGS[timeframe]


def get_prediction_steps(timeframe: str) -> int:
    """Get number of prediction steps for a timeframe."""
    return get_timeframe_config(timeframe).prediction_steps


def get_training_days(timeframe: str) -> int:
    """Get number of training days for a timeframe."""
    return get_timeframe_config(timeframe).training_days


def get_max_age_days(timeframe: str) -> int:
    """Get maximum model age in days for a timeframe."""
    return get_timeframe_config(timeframe).model_max_age_days


# Legacy support: Direct dictionaries for backward compatibility
# These can be removed once all references are updated
PREDICTION_STEPS_BY_TIMEFRAME = {
    tf: config.prediction_steps
    for tf, config in TIMEFRAME_CONFIGS.items()
}

TRAINING_DAYS_BY_TIMEFRAME = {
    tf: config.training_days
    for tf, config in TIMEFRAME_CONFIGS.items()
}

MAX_AGE_DAYS_BY_TIMEFRAME = {
    tf: config.model_max_age_days
    for tf, config in TIMEFRAME_CONFIGS.items()
}
