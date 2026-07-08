# Monad Web App

Landing page + chat UI for [Monad-Ultron](../README.md).

Built with **Next.js 15**, **Tailwind CSS**, **Framer Motion**, and **shadcn-style components**.

## 🚀 One-time setup

You need **Node.js 20+** and **Python 3.12+** (which you already have for Monad itself).

```bash
cd webapp
npm install       # first time only, ~1 minute
```

## ✨ Run it

**Two processes** run side by side:

```bash
# Terminal 1 — the Monad backend (Python)
cd ..            # from repo root
monad serve      # starts FastAPI on http://127.0.0.1:8765

# Terminal 2 — the web app (Next.js)
cd webapp
npm run dev      # starts UI on http://127.0.0.1:3000
```

Then open **http://127.0.0.1:3000** and click **Launch Monad**.

## 🖱 One-click launcher (Windows)

From the repo root, double-click:

```
launcher\start-webapp.bat
```

It runs both processes and opens your browser.

## 🎨 What you get

| Route | What |
|---|---|
| `/` | Landing page — hero, features, architecture diagram |
| `/chat` | Chat UI with sidebar (sessions, status) + right rail (organs, tools, evolution) |

## 💬 Natural-language commands

The chat auto-parses these — no need to memorize CLI syntax:

| You type | What happens |
|---|---|
| *any question* | Routes through the multi-model orchestrator |
| `fuse: <question>` | All models fuse into one answer |
| `learn this: <text/paste>` | Ingested into SQLite + vector memory |
| `learn: <url>` | HTTP-fetched (SSRF-protected), chunked, embedded |
| `integrate https://github.com/...` | Fetches README, stores reference, suggests next steps |
| `evolve: <goal>` | Drafts a code change (approval-gated) |
| `remember: <fact>` | Pins to memory |
| `recall <query>` | Hybrid RRF retrieval |
| `run tool <id>` | Invokes a Monad tool through the policy gate |
| `/help` | Full command list |

Toggle **Cognition** in the header to add the 82-organ pre-pass. Toggle **Fusion** to route every prompt through multi-model fusion.

## 🧬 Architecture

```
Browser (http://localhost:3000)
       │
       ▼
Next.js webapp (this dir)
       │  fetch /api/monad/*
       ▼  (proxied by next.config.mjs)
FastAPI backend (http://localhost:8765)
       │
       ▼
Monad-Ultron Python core
   ├── orchestration/  ← /ask, /fuse
   ├── cognition/      ← 82 organs pre-pass
   ├── memory/         ← /memory/remember, /recall
   ├── tools/          ← /tools, /tools/{id}
   ├── evolution/      ← /evolve/propose, /evolve/history
   └── policy/         ← every mutating action gated
```

## 🛠 Configuration

`webapp/.env.local` (optional):

```env
NEXT_PUBLIC_MONAD_API=http://127.0.0.1:8765
```

Default is `http://127.0.0.1:8765` which matches `monad serve`.

## 📦 Building for production

```bash
cd webapp
npm run build
npm run start
```

For a truly portable deploy (single binary), consider bundling with `next export` for a static HTML/JS drop that talks to your local FastAPI.
