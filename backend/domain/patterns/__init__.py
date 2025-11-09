"""
Chart pattern recognition module.

Identifies common technical analysis patterns:
- Triangles: Ascending, Descending, Symmetrical
- Continuation: Flags, Pennants
- Reversal: Head & Shoulders, Double Top/Bottom
"""
from .triangles import TrianglePatterns
from .continuation import FlagPattern, PennantPattern
from .reversal import HeadAndShoulders, DoubleTops

__all__ = [
    'TrianglePatterns',
    'FlagPattern',
    'PennantPattern',
    'HeadAndShoulders',
    'DoubleTops',
]
