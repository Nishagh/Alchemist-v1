"""
Global Narrative Framework - Python Implementation

A comprehensive system for giving AI agents persistent identity, memory, and 
evolutionary narrative capabilities.
"""

__version__ = "2.0.0"
__author__ = "Alchemist Platform"

from .core.identity_schema import AgentIdentity
from .core.narrative_tracker import NarrativeTracker

__all__ = [
    "AgentIdentity",
    "NarrativeTracker"
]