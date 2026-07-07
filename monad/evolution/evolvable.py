"""
Evolvable — declares which parts of Monad may be self-modified.

The framework REFUSES to touch anything outside the declared zones. This is
the safety boundary that prevents Level 4 (unsupervised core rewriting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EvolutionZone(str, Enum):
    """Categories of files Monad is allowed to touch when self-improving."""
    PLUGINS = "plugins"       # monad/plugins/*.py (new plugins, plugin patches)
    TOOLS = "tools"           # monad/tools/*.py (new tools only — not the framework)
    PROMPTS = "prompts"       # monad/prompts/templates.py + custom template files
    CONFIGS = "configs"       # config.yaml, models.yaml (limited keys)
    WORKSPACE = "workspace"   # workspace/ — freely writable, not code
    MEMORY = "memory_data"    # memory_data/ — freely writable, not code


# =============================================================================
# THE SAFETY LIST — what Monad may modify, in what way.
# =============================================================================
# path_glob:    files (or patterns) allowed
# max_lines:    hard cap on file size to prevent runaway growth
# require_test: True = patch must pass tests before apply (recommended)
# core:         True = special-case, tighter approval flow
# =============================================================================

@dataclass
class EvolutionPolicy:
    zone: EvolutionZone
    path_globs: list[str] = field(default_factory=list)
    max_lines: int = 500
    require_test: bool = True
    core: bool = False


DEFAULT_POLICIES: dict[EvolutionZone, EvolutionPolicy] = {
    EvolutionZone.PLUGINS: EvolutionPolicy(
        zone=EvolutionZone.PLUGINS,
        path_globs=["monad/plugins/*.py"],
        max_lines=400,
        require_test=True,
    ),
    EvolutionZone.TOOLS: EvolutionPolicy(
        zone=EvolutionZone.TOOLS,
        path_globs=["monad/tools/impl/*.py"],   # new tools live in impl/
        max_lines=400,
        require_test=True,
    ),
    EvolutionZone.PROMPTS: EvolutionPolicy(
        zone=EvolutionZone.PROMPTS,
        path_globs=["monad/prompts/custom/*.txt", "monad/prompts/custom/*.j2"],
        max_lines=200,
        require_test=False,
    ),
    EvolutionZone.CONFIGS: EvolutionPolicy(
        zone=EvolutionZone.CONFIGS,
        path_globs=["config.yaml", "models.yaml"],
        max_lines=500,
        require_test=False,
        core=True,   # config changes touch app root — tighter approval
    ),
    EvolutionZone.WORKSPACE: EvolutionPolicy(
        zone=EvolutionZone.WORKSPACE,
        path_globs=["workspace/**/*"],
        max_lines=10_000,
        require_test=False,
    ),
    EvolutionZone.MEMORY: EvolutionPolicy(
        zone=EvolutionZone.MEMORY,
        path_globs=["memory_data/**/*"],
        max_lines=100_000,
        require_test=False,
    ),
}


# Paths that are ALWAYS forbidden — never modifiable by Monad itself.
FORBIDDEN_PATHS: list[str] = [
    "monad/core/**",           # application manager, DI, logger, resources, env
    "monad/evolution/**",      # THE FRAMEWORK ITSELF — can't rewrite its own safety
    "monad/policy/**",         # can't rewrite the gate that gates it
    "monad/inference/**",      # provider abstraction — too critical
    "monad/models/**",         # model manager — too critical
    "monad/router/**",         # can't change how requests are routed
    "monad/config/manager.py", # config *loader* is off-limits (values are ok)
    "installer/**",
    "launcher/**",
    ".git/**",
    "python_portable/**",
    "*.gguf", "*.safetensors", "*.bin",
]


class Evolvable:
    """Marker mixin for objects that participate in self-improvement."""
    evolution_zone: EvolutionZone | None = None
    evolvable: bool = False


def is_path_allowed(path: str | Path) -> tuple[bool, str]:
    """
    Return (allowed, reason). Checks:
      1. Not in FORBIDDEN_PATHS
      2. Matches an allowed zone glob
    """
    import fnmatch
    p = str(path).replace("\\", "/")

    for forbidden in FORBIDDEN_PATHS:
        if fnmatch.fnmatch(p, forbidden):
            return False, f"forbidden path: matches {forbidden!r}"

    for policy in DEFAULT_POLICIES.values():
        for glob in policy.path_globs:
            if fnmatch.fnmatch(p, glob):
                return True, f"allowed via {policy.zone.value}"

    return False, "no matching evolution zone"
