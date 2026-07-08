# Monad Web App — Landing Page + Chat UI

You no longer need the terminal to use Monad. The `webapp/` directory is a full **Next.js 15 + Tailwind + Framer Motion** app with:

- 🎨 **Landing page** at `/` — hero, features, architecture, CTAs
- 💬 **Chat interface** at `/chat` — sidebar + right rail + streaming messages
- 🧠 **Natural-language commands** — say *"integrate this repo"*, *"learn this"*, *"evolve"*, etc.
- 🔗 **Real backend wiring** — every action hits a real FastAPI endpoint

## Quick Start

### Windows (one click, after one-time setup)

```
launcher\start-webapp.bat
```

Double-click. It will:
1. Start the Python backend (`monad serve` on port 8765)
2. Start the Next.js app (port 3000)
3. Open your browser to `http://127.0.0.1:3000`

On first run it will also `npm install` inside `webapp/` (~1 minute).

### Linux / macOS

```bash
./launcher/start-webapp.sh
```

### Manual (two terminals)

```bash
# Terminal 1
monad serve

# Terminal 2
cd webapp
npm install         # first time only
npm run dev
```

Then open http://127.0.0.1:3000.

## What you can type

The chat auto-parses commands. **No slashes needed** — Monad detects intent:

| Say this | What happens |
|---|---|
| *any question* | Routes through the multi-model orchestrator |
| `fuse: <question>` | All models fuse into ONE unified answer |
| `fuse chain: <q>` | Force draft→refine→polish mode |
| `fuse logits: <q>` | Force token-level logit fusion |
| `learn this: <text>` | Ingest into memory (chunked + embedded) |
| `learn: <url>` | Fetch URL (SSRF-protected), ingest content |
| `integrate https://github.com/foo/bar` | Fetch README, analyze, suggest next steps |
| `evolve: add a plugin that <goal>` | Draft a code change (approval-gated) |
| `evolve: <goal> into monad/plugins/foo.py` | Target a specific file |
| `remember: <fact>` | Pin something to memory |
| `recall <query>` | Hybrid RRF retrieval from memory |
| `run tool filesystem op=list path=.` | Invoke a Monad tool |
| `/help` | Show all commands |
| `/cog <question>` | Force cognition pre-pass (all 82 organs) |

Toggle **Cognition** or **Fusion** in the chat header to make them default-on for every query.

## Architecture

```
┌────────────────────────────────┐
│  Browser  (localhost:3000)     │
└────────────┬───────────────────┘
             │
             ▼  next.config.mjs rewrite
┌────────────────────────────────┐
│  Next.js webapp                │
│  ├─ /app/page.tsx    Landing   │
│  ├─ /app/chat/       Chat UI   │
│  ├─ /components/               │
│  └─ /lib/{api,commands}.ts     │
└────────────┬───────────────────┘
             │  /api/monad/* → :8765
             ▼
┌────────────────────────────────┐
│  FastAPI  (localhost:8765)     │
│  monad/api/server.py           │
│  ├─ POST /ask     orchestrator │
│  ├─ POST /fuse    multi-model  │
│  ├─ POST /learn   ingest       │
│  ├─ POST /evolve/propose       │
│  ├─ POST /memory/{remember,recall} │
│  ├─ POST /tools/{id}           │
│  └─ GET  /{info,organs,tools}  │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│  Monad-Ultron Python core      │
│  cognition · orchestration ·   │
│  memory · tools · policy       │
└────────────────────────────────┘
```

## Files

```
webapp/
├── app/
│   ├── page.tsx              landing page
│   ├── chat/page.tsx         chat page
│   ├── layout.tsx            root layout
│   └── globals.css           tailwind + monad palette
├── components/
│   ├── chat/
│   │   ├── ChatPanel.tsx     main chat surface + dispatcher
│   │   ├── MessageBubble.tsx markdown + syntax highlight
│   │   └── QuickActions.tsx  starter prompts
│   ├── layout/
│   │   ├── Sidebar.tsx       sessions + status
│   │   └── RightRail.tsx     organs / tools / evolution
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       └── Badge.tsx
├── lib/
│   ├── api.ts                fetch wrapper
│   ├── commands.ts           natural-language parser
│   └── utils.ts              tailwind cn()
├── preview.html              static visual preview (no build)
├── package.json
├── next.config.mjs
├── tailwind.config.ts
└── tsconfig.json
```

## Preview without installing anything

Open `webapp/preview.html` in any browser (or in the workspace preview) to see what the landing page looks like — no `npm install` needed.

The real Next.js version has:
- Framer Motion animations (fade-in on scroll, orb pulse)
- Client-side routing (`/` → `/chat`)
- Live backend integration in the chat page
- Dark-mode-only design (matches Monad's aesthetic)

## Customization

**Colors** — `webapp/tailwind.config.ts` under `theme.extend.colors`. Monad ships with a "deep space + neon" palette; swap for your brand.

**Commands** — Add a new intent in `webapp/lib/commands.ts` (`parseCommand`) and handle it in `ChatPanel.tsx` (`dispatch`).

**Backend endpoint** — Set `NEXT_PUBLIC_MONAD_API` in `webapp/.env.local` if your FastAPI isn't on `:8765`.

## Deploy

The webapp is a standard Next.js app — deploys anywhere:

- **Vercel**: `npx vercel` in `webapp/`
- **Docker**: `next build && next start`
- **Static**: `next build && next export` (loses server actions, keeps everything else)

For a truly portable USB deploy: run both processes locally and point the browser at `localhost`. That's what `start-webapp.bat` does.
