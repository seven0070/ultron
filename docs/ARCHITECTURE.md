# Monad-Ultron — Architecture Specification

## Vision

Monad (codename **Ultron**) is a **portable, modular, local AI orchestration operating system**. It is *not* a new language model. It is the "OS" that coordinates multiple open-source LLMs, a memory layer, a policy gate, a tool framework, and a plugin system — all on a USB drive.

## Target Hardware

- **Laptop:** ASUS G615JHR-S5005WS
- **GPU:** RTX 5070 Laptop (8 GB VRAM, CUDA 12.x)
- **Storage:** 128 GB USB drive

## Three-Model Brain

| Model     | Role                                              | Approx. Size (Q4_K_M) |
|-----------|---------------------------------------------------|-----------------------|
| LongCat 2 | Reasoning, planning, final synthesis (controller) | ~5 GB                 |
| GLM-5     | Coding specialist, structured output              | ~5 GB                 |
| Llama 2   | Creative brainstorming, alternatives              | ~4 GB                 |

Plus:
- **JCode** — Code execution harness (plugin)
- **ZeroLang** — Workflow scripting language (plugin)

## System Layers (top → bottom)

```
┌─────────────────────────────────────────────────────┐
│  UI: CLI (Typer+Rich) · Dashboard (FastAPI)         │  ← Build #005, #056+
├─────────────────────────────────────────────────────┤
│  Application Manager (lifecycle, banner, health)     │  ← Build #006
├─────────────────────────────────────────────────────┤
│  Config · DI Container · Plugin Manager              │  ← #003 · #009 · #008
├─────────────────────────────────────────────────────┤
│  Environment Manager (Python/OS/GPU/CUDA validation) │  ← Build #010
├─────────────────────────────────────────────────────┤
│  Resource Manager (paths, USB detection, disk health)│  ← Build #007
├─────────────────────────────────────────────────────┤
│  Prompt Management (templates, context, builder)     │  ← Build #016
├─────────────────────────────────────────────────────┤
│  Router / Intent Engine (classify → strategy)        │  ← Build #014
├─────────────────────────────────────────────────────┤
│  Model Manager · Loader · Runtime                    │  ← #011 · #012
├─────────────────────────────────────────────────────┤
│  Inference Provider (llama.cpp isolated behind ABC)  │  ← Build #015
├─────────────────────────────────────────────────────┤
│  Response Synthesizer (multi-model merge)            │  ← Build #017+
├─────────────────────────────────────────────────────┤
│  Policy Gate (approval-required actions)             │  ← Build #056+
├─────────────────────────────────────────────────────┤
│  Memory & Retrieval (SQLite + ChromaDB)              │  ← Build #026+
├─────────────────────────────────────────────────────┤
│  Tool Framework (FS, Python, Terminal, Browser, Git) │  ← Build #036+
├─────────────────────────────────────────────────────┤
│  Plugins (JCode, ZeroLang, Health, SystemInfo, …)    │  ← Build #008
└─────────────────────────────────────────────────────┘
```

## Directory Layout

```
Monad-Ultron/
├── monad/
│   ├── core/          # application, container, environment, logger, resource_manager
│   ├── config/        # YAML config manager
│   ├── models/        # metadata, registry, manager, loader, interfaces
│   ├── chat/          # chat_engine, conversation
│   ├── router/        # router, classifier, strategy, request, intent
│   ├── inference/     # provider ABC, llama_cpp provider, manager
│   ├── prompts/       # manager, builder, templates, context
│   ├── memory/        # STUBS → SQLite + ChromaDB
│   ├── tools/         # STUBS → FS/Python/Terminal/Browser/Git/PDF/JCode/ZeroLang
│   ├── policy/        # STUBS → approval gate
│   ├── scheduler/     # STUBS → background jobs
│   ├── plugins/       # manager + example plugins
│   ├── api/           # STUBS → FastAPI server
│   ├── ui/            # cli (implemented), dashboard (stub)
│   └── utils/         # path helpers, misc
├── installer/         # USB installer
├── launcher/          # .bat reference launchers
├── docs/              # ARCHITECTURE, INSTALL, USAGE, BUILDS
├── tests/             # pytest suite
├── scripts/           # dev/maintenance
└── config.yaml, models.yaml, run.py
```

## Core Principles

1. **Modular** — every subsystem is swappable
2. **Local-first** — no cloud dependency
3. **Config-driven** — behavior via YAML, not code changes
4. **Provider abstraction** — llama.cpp isolated behind `InferenceProvider`
5. **Approval-gated** — impactful actions need explicit user approval
6. **DI-based** — no hardcoded dependencies
7. **Incremental** — one milestone at a time
8. **Plugin-based** — extend without touching core

## Storage Budget (Q4_K_M quantized)

| Item                | Size        |
|---------------------|-------------|
| LongCat 2 GGUF      | ~5 GB       |
| GLM-5 GGUF          | ~5 GB       |
| Llama 2 GGUF        | ~4 GB       |
| Portable Python + deps | ~4 GB    |
| Source code         | ~50 MB      |
| Memory DB           | ~10 GB grow |
| Workspace           | ~20 GB      |
| Logs / cache        | ~5 GB       |
| **Total**           | **~55 GB**  |
| **Free on 128 GB USB** | **~70 GB** |

## Extensibility

- Add a new inference provider → subclass `InferenceProvider`, register with `InferenceManager`
- Add a new tool → subclass `Tool`, register with `ToolRegistry`
- Add a new plugin → subclass `Plugin`, drop in `monad/plugins/`, list in `config.yaml.plugins.auto_load`
- Add a new model → append entry to `models.yaml`
