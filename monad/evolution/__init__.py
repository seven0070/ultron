"""
Build #017a — Self-Improvement Framework.

Gives Monad the ability to safely improve itself:
  Level 1: self-update  (pull new versions from git)
  Level 2: self-extend  (write & load new plugins/tools)
  Level 3: self-debug   (diagnose crashes, propose patches, test, rollback)

Level 4 (unsupervised recursive rewriting of core) is DELIBERATELY UNSUPPORTED.
Every change flows through PolicyGate for user approval.
"""

from monad.evolution.evolvable import Evolvable, EvolutionZone
from monad.evolution.log import EvolutionLog, EvolutionRecord, ChangeType, Outcome
from monad.evolution.proposer import PatchProposer, PatchProposal
from monad.evolution.sandbox import SandboxRunner, SandboxResult
from monad.evolution.rollback import RollbackManager
from monad.evolution.manager import EvolutionManager
from monad.evolution.updater import SelfUpdater

__all__ = [
    "Evolvable", "EvolutionZone",
    "EvolutionLog", "EvolutionRecord", "ChangeType", "Outcome",
    "PatchProposer", "PatchProposal",
    "SandboxRunner", "SandboxResult",
    "RollbackManager",
    "EvolutionManager",
    "SelfUpdater",
]
