"""
ML Models for Price Prediction

This module contains machine learning models for predicting future prices.
Uses autoregressive gradient boosting for smooth, coherent price curve predictions.
"""

from .predictors.autoregressive_predictor import AutoregressivePricePredictor
from .predictors.multi_ohlc_predictor import MultiOHLCPredictor

__all__ = [
    'AutoregressivePricePredictor',
    'MultiOHLCPredictor',
]
