"""
Monad Cognitive Architecture (Phase 5 delivery).

A layered cognitive architecture that slots in between Router and Orchestrator:

    Router (intent)
        ↓
    ┌─────────────────────────────────────┐
    │        COGNITIVE ARCHITECTURE       │
    │  Layer 1: Perception                │
    │  Layer 2: Memory (Cognee)           │
    │  Layer 3: Learning                  │
    │  Layer 4: Reasoning                 │
    │  Layer 5: Executive                 │
    │  Layer 6: 83 Organs                 │
    │  Layer 7: Self-Model                │
    │  Layer 8: Adaptation                │
    │  Layer 9: Action                    │
    └─────────────────────────────────────┘
        ↓
    Multi-Model Orchestrator
"""

from monad.cognition.core import Monad, MonadConfig
from monad.cognition.organs import (
    Organ, OrganCategory, OrganRegistry, register_all,
)

__all__ = [
    "Monad", "MonadConfig",
    "Organ", "OrganCategory", "OrganRegistry", "register_all",
]

__version__ = "0.2.0"    # cognitive layer version (repo is 0.3.x)
