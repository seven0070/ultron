# Monad Self-Improvement Framework

## Philosophy

Monad can improve itself — but **safely**, and **always with your approval**.

We support three levels; **Level 4 is deliberately not supported**.

| Level | What | Status |
|-------|------|--------|
| **1 — Self-update** | Pull new versions of Monad from your git remote | ✅ Implemented |
| **2 — Self-extend** | Write new plugins/tools/prompts and load them | ✅ Framework ready |
| **3 — Self-debug** | Diagnose errors, propose patches to existing plugins/tools | ✅ Framework ready |
| **4 — Recursive self-rewriting** | Modify its own core, unsupervised | 🚫 **Refused by design** |

## The Safety Model

### 1. Zones — what CAN be modified

Only files matching an `EvolutionZone` glob can be touched:

| Zone | Path glob | Purpose |
|------|-----------|---------|
| `plugins`  | `monad/plugins/*.py`         | New/patched plugins |
| `tools`    | `monad/tools/impl/*.py`      | New user-defined tools |
| `prompts`  | `monad/prompts/custom/*.txt` | Custom prompt templates |
| `configs`  | `config.yaml`, `models.yaml` | Runtime config (limited) |
| `workspace`| `workspace/**`               | User data files |
| `memory`   | `memory_data/**`             | Learned memory |

### 2. Forbidden Paths — what NEVER changes

The framework refuses to touch:
- `monad/core/**` — application manager, DI, logger, environment, resources
- `monad/evolution/**` — **the framework itself** (can't rewrite its own safety)
- `monad/policy/**` — the gate that gates it
- `monad/inference/**`, `monad/models/**`, `monad/router/**`
- `monad/config/manager.py` — the loader (values in yaml are ok)
- `.git/**`, `installer/**`, `launcher/**`, `python_portable/**`, model files

### 3. The Loop — 6 checked stages

```
    ┌─────────────────────────────────────────────────┐
    │  1. PROPOSE          PatchProposer + LLMs       │
    │     ↓                                            │
    │  2. VALIDATE ZONE    is_path_allowed()          │
    │     ↓                                            │
    │  3. SANDBOX TEST     SandboxRunner (pytest)     │
    │     ↓                                            │
    │  4. APPROVAL         PolicyGate.check()         │
    │     ↓                                            │
    │  5. BACKUP + APPLY   RollbackManager.backup()   │
    │     ↓                                            │
    │  6. LOG              EvolutionLog (SQLite)      │
    └─────────────────────────────────────────────────┘
```

Any stage can veto. Nothing bypasses.

### 4. Every change is reversible

Before applying, `RollbackManager` snapshots the old file to
`memory_data/evolution_backups/<record_id>/`. One command restores:

```
monad evolve rollback evo-20260707-143025-abc123
```

### 5. Everything is journaled

`memory_data/evolution.db` (SQLite) has one row per proposal, approval,
apply, and rollback. Full audit trail. Queryable:

```
monad evolve history --limit 50
```

## CLI Commands

| Command | What it does |
|---------|--------------|
| `monad update`                          | Level 1 — pull latest from git |
| `monad update --check`                  | Level 1 — just check, don't pull |
| `monad evolve propose "<goal>" -t <file>` | Draft a change (does not apply) |
| `monad evolve apply <record_id>`         | Test + approve + apply |
| `monad evolve apply <id> --skip-tests`   | Skip sandbox tests (dangerous) |
| `monad evolve rollback <record_id>`      | Undo an applied change |
| `monad evolve history`                   | See what's been changed |

## Example: Monad adds itself a new plugin

```bash
# 1. Ask Monad to create a new plugin
monad evolve propose "add a plugin that reports GPU temperature" \
    --target monad/plugins/gpu_temp.py \
    --zone plugins

# Output:
# ✎ Proposal evo-20260707-143025-a1b2c3
#   Model:     glm5
#   Rationale: Creates a Plugin subclass that reads NVIDIA GPU temp via nvidia-smi.
#   Diff preview: (first 40 lines shown)
#
# To apply: monad evolve apply evo-20260707-143025-a1b2c3

# 2. Apply — runs sandbox tests + asks approval
monad evolve apply evo-20260707-143025-a1b2c3

# 3. If something goes wrong, roll back
monad evolve rollback evo-20260707-143025-a1b2c3
```

## Why NOT Level 4

Full recursive self-improvement (Monad rewriting its own core, unsupervised) sounds cool but:

1. **No reliable success signal.** How does Monad *know* its rewrite is better? Tests only cover known cases.
2. **Silent corruption.** One bad rewrite of `application.py` bricks the whole system with no rollback.
3. **Nobody has shipped it.** Even the biggest AI labs don't run production systems this way.
4. **Contradicts the point.** The whole architecture is *approval-gated*. Unsupervised rewriting bypasses your consent.

If you ever want to explore Level 4, do it in a **git branch** of Monad — not in the running system. The framework will refuse to write to `monad/core/**` no matter what you ask it to do.

## Extending the Framework

To allow a new zone (say, allow Monad to edit its own README):

1. Add a value to `EvolutionZone` in `monad/evolution/evolvable.py`
2. Add a `DEFAULT_POLICIES` entry with the path glob + `max_lines` cap
3. **Do not remove `FORBIDDEN_PATHS` entries** — those are the safety floor.

Every change to the zone list itself should be reviewed by a human. That's why `monad/evolution/**` is forbidden even to Monad.
