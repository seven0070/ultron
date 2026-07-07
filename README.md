# 🧠 Monad-Ultron

> **Portable, modular, local AI orchestration platform that runs from a USB drive.**

Monad (codename: *Ultron*) is **not** a new language model. It is an **orchestration operating system** that coordinates multiple open-source LLMs — routing, reasoning, coding, and creative work across specialized models — all running locally on your machine, from a USB drive.

Plug the USB into any compatible Windows PC, double-click `monad.bat`, and you have a full local AI workstation.

---

## ✨ Features

- 🔌 **Fully portable** — Python, dependencies, models, and code all live on the USB
- 🧩 **Modular architecture** — Every subsystem is swappable via dependency injection
- 🤖 **Multi-model brain** — LongCat 2 (reasoning) + GLM-5 (code) + Llama 2 (creative)
- 🛠️ **Tool framework** — Filesystem, Python sandbox, Git, terminal, browser, PDFs
- 🧠 **Local memory** — SQLite + ChromaDB vector store, no cloud
- 🔒 **Approval-gated** — All impactful actions require your explicit approval
- 🔧 **Plugin-based** — Extend without touching core (JCode, ZeroLang, and more)
- 📴 **Offline-first** — Once installed, needs zero internet

---

## 🎯 Target Hardware

- **Laptop:** ASUS G615JHR-S5005WS (or any Windows 11 PC with an NVIDIA GPU)
- **GPU:** RTX 5070 Laptop (or any CUDA 12.x GPU with ≥ 8 GB VRAM)
- **USB:** 128 GB minimum, USB 3.2 recommended for speed

---

## 🚀 Quick Start

### Option A — One-click installer (recommended)

1. **Plug your 128 GB USB drive into your desktop.**
2. **Download this repo** and extract it anywhere on your desktop.
3. **Double-click** `installer/install_to_usb.bat`.
4. The installer will:
   - Detect your USB drive (asks you to confirm)
   - Copy the Monad codebase to the USB
   - Download portable Python 3.12 (~30 MB) to the USB
   - Create a virtual environment on the USB
   - Install all Python dependencies on the USB
   - Download the 3 GGUF models (~15 GB) to `USB:/models/`
   - Create the launcher `monad.bat` at the USB root
5. **Eject and plug the USB into your laptop.**
6. **Double-click `monad.bat`** on the USB. Done. 🎉

### Option B — Manual copy

1. Copy the entire `Monad-Ultron/` folder to your USB drive.
2. Follow [`docs/INSTALL.md`](docs/INSTALL.md) for manual Python + model setup.

---

## 🏗️ Architecture

```
USER
  │
  ▼
┌──────────────────┐
│ CLI / Dashboard  │
└────────┬─────────┘
         ▼
  Application Manager
         │
 ┌───────┼───────┐
 ▼       ▼       ▼
Config  DI    Plugins
 └───────┼───────┘
         ▼
  Environment Manager
         ▼
   Resource Manager
         ▼
  Prompt Management
         ▼
  Router / Intent Engine
         │
 ┌───────┼───────┐
 ▼       ▼       ▼
LongCat GLM-5  Llama-2
(reason) (code) (creative)
 └───────┼───────┘
         ▼
 Response Synthesizer
         ▼
   Policy Gate
         ▼
Memory & Retrieval
         ▼
  Tool Framework
 ┌────┬────┬────┬────┐
 ▼    ▼    ▼    ▼    ▼
FS  Python Browser Term Git
         │
     ┌───┴───┐
     ▼       ▼
   JCode  ZeroLang
         │
         ▼
   Final Response
```

Full spec: see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📂 Repository Layout

```
Monad-Ultron/
├── monad/                  # Core Python package
│   ├── core/               # App manager, DI container, logger, env, resources
│   ├── config/             # YAML configuration system
│   ├── models/             # Model manager, loader, runtime, registry
│   ├── chat/               # Conversation engine
│   ├── router/             # Intent classifier & routing strategies
│   ├── inference/          # LLM provider abstraction (llama.cpp, etc.)
│   ├── prompts/            # Prompt templates & context builder
│   ├── memory/             # SQLite + ChromaDB memory layer (stubs)
│   ├── tools/              # Tool framework (stubs)
│   ├── policy/             # Approval gate (stubs)
│   ├── scheduler/          # Background jobs (stubs)
│   ├── plugins/            # Plugin manager + example plugins
│   ├── api/                # FastAPI server (stubs)
│   ├── ui/                 # CLI (Typer + Rich)
│   └── utils/              # Shared utilities
├── installer/              # Windows installer scripts
├── launcher/               # USB launcher (.bat files)
├── docs/                   # ARCHITECTURE, INSTALL, USAGE, BUILDS
├── tests/                  # Unit tests
├── scripts/                # Dev/maintenance scripts
├── config.yaml             # Main runtime config
├── models.yaml             # Model download manifest
├── requirements.txt
├── pyproject.toml
├── LICENSE                 # MIT
├── run.py                  # Main entry point
└── README.md               # (this file)
```

---

## 🛣️ Build Roadmap

Monad is being built in **~120 small, testable milestones**.

| Phase | Milestones | Status |
|-------|-----------|--------|
| Foundation (project setup, config, logging, CLI) | #001–#010 | ✅ Complete |
| Model framework & single-model chat | #011–#013 | ✅ Complete |
| Routing, inference, prompts | #014–#016 | ✅ Complete |
| **Self-improvement framework** (self-update, self-extend, self-debug) | **#017a** | ✅ **Complete** |
| **Multi-model orchestration** (5 strategies + confidence scoring) | **#017** | ✅ **Complete** |
| **llama.cpp perf upgrades** (speculative decoding, KV quant, flash attn) | **#017b** | ✅ **Complete** |
| **Cognitive architecture** (9 layers, 82 canonical organs, Cognee, MCP) | **Phases 1-6** | ✅ **Complete** |
| **Real memory layer** (SQLite + ChromaDB + RRF hybrid retrieval) | **#026** | ✅ **Complete** |
| **Tool framework** (Filesystem, Python sandbox, Terminal, HTTP) | **#036–#039** | ✅ **Complete** |
| **Real policy gate** (allow/deny/prompt + SQLite audit) | **#056** | ✅ **Complete** |
| **Cognition→Orchestrator wiring** (`monad ask --cognition`) | **#017f** | ✅ **Complete** |
| **FastAPI + HTML dashboard** (`monad serve`) | **#059** | ✅ **Complete** |
| **Background scheduler** (periodic + one-shot jobs) | **#070** | ✅ **Complete** |
| Streaming, adaptive routing, caching | #018–#025 | 🚧 Stubs |
| Memory & retrieval | #026–#035 | 🚧 Stubs |
| Tool framework | #036–#055 | 🚧 Stubs |
| Policy, scheduler, API, dashboard | #056–#080 | 🚧 Stubs |
| USB packaging, tests, docs | #081–#120 | 🚧 Partial |

Detailed tracker: [`docs/BUILDS.md`](docs/BUILDS.md).

---

## 🔧 For Developers

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/Monad-Ultron.git
cd Monad-Ultron

# Create venv
python -m venv .venv
.venv\Scripts\activate    # Windows
# or: source .venv/bin/activate  # Linux/Mac

# Install
pip install -e .

# Run
python run.py
# or
monad --help
```

---

## 🤝 Contributing

Monad is built one small milestone at a time. See [`docs/BUILDS.md`](docs/BUILDS.md) for the build queue. Each PR should implement exactly one milestone.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 🙋 Support

- Read the docs in `docs/`
- Run `python run.py doctor` for diagnostics
- Open an issue on GitHub

---

> ⚠️ **Note on GitHub username:** All URLs in this repo currently use `YOUR_USERNAME` as a placeholder. Before pushing to GitHub, run:
> ```bash
> # Windows PowerShell
> Get-ChildItem -Recurse -File | ForEach-Object { (Get-Content $_.FullName -Raw) -replace 'YOUR_USERNAME', 'your-actual-username' | Set-Content $_.FullName }
> ```
> Then push with `git remote add origin https://github.com/your-actual-username/Monad-Ultron.git && git push -u origin main`.
