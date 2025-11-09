"""
Technical analysis module.

Combines technical indicators and pattern recognition for comprehensive
market analysis.

Submodules:
- indicators: Technical indicators (SMA, RSI, MACD, Bollinger Bands, etc.)
- patterns: Chart pattern recognition (triangles, flags, head & shoulders, etc.)
"""
from .indicators import SMA, EMA, MACD, RSI, Stochastic, BollingerBands, ATR
from .patterns import TrianglePatterns, FlagPattern, PennantPattern, HeadAndShoulders, DoubleTops

__all__ = [
    # Indicators
    'SMA',
    'EMA',
    'MACD',
    'RSI',
    'Stochastic',
    'BollingerBands',
    'ATR',
    # Patterns
    'TrianglePatterns',
    'FlagPattern',
    'PennantPattern',
    'HeadAndShoulders',
    'DoubleTops',
]
