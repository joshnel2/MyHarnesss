"""
Harness Core Module

The Harness is an AI-native system that acts as an extension of the Fulcrum's intelligence.
It loads context, executes tasks, validates outputs, and maintains a learning loop through Shadow Mode.
"""

from .harness import Harness

__all__ = ["Harness"]
__version__ = "1.0.0"
