# monad.cognition — Cognitive Architecture

The user's prompt asked for the cognitive architecture at `/home/user/monad/`.
Because Monad-Ultron already exists as the parent project with 4,200+ lines of
foundation code, we integrated the cognitive layer INTO it as this package
(`monad.cognition`) rather than build a competing repo.

The full package is importable as:

```python
from monad.cognition import Monad, MonadConfig

m = Monad(MonadConfig())
cycle = m.think("your prompt here")
print(cycle.output)
```

## CLI

```bash
python run.py cognition info
python run.py cognition organs
python run.py cognition organs --category human_genius
python run.py cognition think "what is intelligence?" -v
```

## Package layout

```
monad/cognition/
├── core.py                   # Monad + MonadConfig (top-level orchestrator)
├── perception.py             # Layer 1
├── memory/                   # Layer 2 — Cognee wrapper + QueryRouter
│   ├── store.py
│   └── query_router.py
├── reasoning/                # Layer 4 — ModelRouter + Reflexion
│   ├── model_router.py
│   └── reflexion.py
├── executive.py              # Layer 5 — weighted vote / highest conf
├── organs/                   # Layer 6 — 83 organs
│   ├── base.py               # Organ ABC + OrganResult
│   ├── stub.py               # Generic stub
│   ├── registry.py           # OrganRegistry
│   ├── human_geniuses.py     # 58 stubs
│   ├── animal_extremes.py    # 6 stubs
│   ├── microbial.py          # 15 stubs
│   └── conceptual.py         # 4 stubs
├── self_model.py             # Layer 7 — SEPARATE meta-graph
├── mcp/                      # MCP bridge
│   └── bridge.py
└── README.md                 # THIS FILE
```

See `docs/MONAD_BLUEPRINT.md` for the full architectural spec, and
`docs/cognition/PHASE1_CONSCIOUSNESS.md` for the honest consciousness stance.
