# Monad-Ultron — Build Milestone Tracker

Monad is built in ~120 small, testable milestones. One PR per milestone.

## Phase 1 — Foundation (✅ complete)

| # | Name | Status | Where |
|---|------|--------|-------|
| 001 | Project skeleton | ✅ | (repo root) |
| 002 | Python foundation | ✅ | `pyproject.toml`, `requirements.txt` |
| 003 | Configuration system | ✅ | `monad/config/manager.py` |
| 004 | Logging system | ✅ | `monad/core/logger.py` |
| 005 | CLI framework | ✅ | `monad/ui/cli.py` |
| 006 | Application Manager | ✅ | `monad/core/application.py` |
| 007 | Resource Manager | ✅ | `monad/core/resource_manager.py` |
| 008 | Plugin framework | ✅ | `monad/plugins/manager.py` |
| 009 | DI container | ✅ | `monad/core/container.py` |
| 010 | Environment validator | ✅ | `monad/core/environment.py` |

## Phase 2 — Single-model chat (✅ complete)

| # | Name | Status | Where |
|---|------|--------|-------|
| 011 | Model Management Framework | ✅ | `monad/models/` |
| 012 | Single Model Loader | ✅ | `monad/models/loader.py` |
| 013 | Single-Model Chat Engine | ✅ | `monad/chat/` |
| 014 | Routing Framework | ✅ | `monad/router/` |
| 015 | Inference Provider Framework | ✅ | `monad/inference/` |
| 016 | Prompt & Context Management | ✅ | `monad/prompts/` |

## Phase 3 — Multi-model orchestration

| # | Name | Status |
|---|------|--------|
| **017a** | **Self-Improvement Framework** (Levels 1+2+3) | ✅ **Complete** |
| **017**  | **Multi-model orchestration** (5 strategies + confidence scorer) | ✅ **Complete** |
| **017b** | **llama.cpp perf upgrades** (speculative decoding, KV quant, flash attn) | ✅ **Complete** |
| 018 | Streaming output from orchestrator | ⏳ |
| 019 | Role-specific prompt templates | ⏳ |
| 020 | Adaptive strategy selection (learn from usage) | ⏳ |
| 021 | Multi-model chat CLI (`monad chat --multi`) | ⏳ |
| 022 | Model warm-up & preload | ⏳ |
| 023 | Response caching layer | ⏳ |
| 024 | Fallback / error handling improvements | ⏳ |
| 025 | Concurrent multi-model benchmarks | ⏳ |

## Phase 4 — Memory & retrieval

| # | Name | Status |
|---|------|--------|
| 026 | SQLite schema + migrations | 🚧 stub `memory/stubs.py` |
| 027 | Conversation persistence | ⏳ |
| 028 | Episodic memory | ⏳ |
| 029 | ChromaDB setup | ⏳ |
| 030 | Embedding provider | ⏳ |
| 031 | Vector indexing | ⏳ |
| 032 | Retrieval engine | ⏳ |
| 033 | Memory CLI commands | ⏳ |
| 034 | Memory-augmented chat | ⏳ |
| 035 | Memory pruning / TTL | ⏳ |

## Phase 5 — Tool framework

| # | Name | Status |
|---|------|--------|
| 036 | Tool ABC + registry | 🚧 stub `tools/stubs.py` |
| 037 | Filesystem tool (read) | ⏳ |
| 038 | Filesystem tool (write) | ⏳ |
| 039 | Filesystem tool (delete) | ⏳ |
| 040 | Python execution sandbox | ⏳ |
| 041 | Terminal tool | ⏳ |
| 042 | Git tool | ⏳ |
| 043 | HTTP request tool | ⏳ |
| 044 | PDF reader tool | ⏳ |
| 045 | Browser automation tool | ⏳ |
| 046 | Tool invocation from LLM | ⏳ |
| 047–055 | Tool integrations (JCode, ZeroLang, etc.) | ⏳ |

## Phase 6 — Policy, scheduler, API

| # | Name | Status |
|---|------|--------|
| 056 | Policy gate implementation | 🚧 stub |
| 057 | Approval UI (CLI) | ⏳ |
| 058 | Audit log | ⏳ |
| 059 | FastAPI server | 🚧 stub |
| 060 | REST: /chat, /models, /health | ⏳ |
| 061 | WebSocket streaming | ⏳ |
| 062 | Web dashboard (basic) | ⏳ |
| 063–070 | Scheduler, background jobs | ⏳ |

## Phase 7 — Polish, docs, USB packaging

| # | Name | Status |
|---|------|--------|
| 071 | End-to-end tests | ⏳ |
| 072 | Performance profiling | ⏳ |
| 073 | Memory footprint audit | ⏳ |
| 074 | USB installer polish | 🚧 partial |
| 075 | Portable Python bootstrap | 🚧 partial |
| 076 | Auto-updater | ⏳ |
| 077 | Signed launcher | ⏳ |
| 078–120 | Docs, tutorials, release prep | ⏳ |

## How to add a build

1. Pick the lowest-numbered ⏳ item
2. Open an issue titled `Build #NNN — <name>`
3. Implement — one module or feature only
4. Add pytest tests under `tests/`
5. Update this tracker (⏳ → ✅)
6. PR with title `Build #NNN — <name>`
