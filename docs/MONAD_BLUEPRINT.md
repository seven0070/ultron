# Monad Cognitive Architecture — Blueprint

> **Version:** 0.2.0 (cognitive layer) · integrated into Monad-Ultron v0.4.0
> **Position:** honest — no consciousness claim. See [PHASE1_CONSCIOUSNESS.md](cognition/PHASE1_CONSCIOUSNESS.md).

---

## 1. Full Architecture Diagram

```
                       ┌─────────────────────────┐
                       │        USER             │
                       └────────────┬────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │  UI: CLI + Dashboard    │
                       └────────────┬────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │  Application Manager    │  (Monad-Ultron core)
                       └────────────┬────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
   ┌────▼─────┐               ┌─────▼─────┐              ┌─────▼─────┐
   │  Config  │               │    DI     │              │  Plugins  │
   └────┬─────┘               └─────┬─────┘              └─────┬─────┘
        └─────────────┬─────────────┴─────────────┬────────────┘
                      │                            │
              ┌───────▼─────────┐         ┌────────▼──────────┐
              │ Env Manager     │         │ Resource Manager  │
              └───────┬─────────┘         └────────┬──────────┘
                      └─────────────┬──────────────┘
                                    │
                       ┌────────────▼─────────────┐
                       │  Prompt Management       │
                       └────────────┬─────────────┘
                                    │
                       ┌────────────▼─────────────┐
                       │  Router / Intent Engine  │
                       └────────────┬─────────────┘
                                    │
        ╔═══════════════════════════▼═══════════════════════════╗
        ║        COGNITIVE ARCHITECTURE (Phase 5)               ║
        ║                                                       ║
        ║  Layer 1: Perception   ← normalize input              ║
        ║  Layer 2: Memory (Cognee) + QueryRouter               ║
        ║  Layer 3: Learning     ← organ weights, feedback      ║
        ║  Layer 4: Reasoning    ← ModelRouter, Reflexion       ║
        ║  Layer 5: Executive    ← weighted_vote/highest_conf   ║
        ║  Layer 6: 83 Organs    ← operators, NOT graph nodes   ║
        ║  Layer 7: Self-Model   ← SEPARATE meta-graph          ║
        ║  Layer 8: Adaptation   ← controlled evolution         ║
        ║  Layer 9: Action       ← output back to orchestrator  ║
        ║                                                       ║
        ║  Bridges: MCP export/import, Cognee 1.0 API           ║
        ╚═══════════════════════════▼═══════════════════════════╝
                                    │
                       ┌────────────▼─────────────┐
                       │ Multi-Model Orchestrator │  (Build #017)
                       │  5 strategies + confidence│
                       └────────────┬─────────────┘
                                    │
                       ┌────────────▼─────────────┐
                       │  Inference Providers     │
                       │  (llama.cpp + specdecode)│
                       └────────────┬─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ LongCat/ │   │  GLM /   │   │ Llama /  │
              │ Qwen 7B  │   │DeepSeek  │   │  3.2 3B  │
              └────┬─────┘   └────┬─────┘   └────┬─────┘
                   └────────────┬─┴──────────────┘
                                ▼
                       ┌─────────────────┐
                       │Response Synth.  │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │  Policy Gate    │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │  Tool Framework │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │  FINAL RESPONSE │
                       └─────────────────┘
```

---

## 2. Cognee Memory Layer

### The three stores (Cognee 1.0)

| Store | What it holds | Backend |
|---|---|---|
| **Graph** | Entities + typed relations (SVO triplets) | Kuzu (default), Neo4j |
| **Vector** | Dense embeddings for semantic search | LanceDB (default), Qdrant, Weaviate |
| **Relational** | Metadata, docs, provenance | SQLite (default), Postgres |

### Pipeline

```
Text
  ↓  add()
Raw docs table
  ↓  cognify()
Triplet extraction → Graph nodes + edges
                   → Vector embeddings
  ↓  search()
Hybrid retrieval (RRF fusion of graph + vector)
```

### Monad wrappers (Cognee 1.0 aliases)

```python
memory.remember(text)          # add + cognify
memory.recall(query, mode)     # search with QueryMode routing
memory.improve(node, feedback) # reinforce/weaken
memory.forget(needle)          # delete
```

Cognee is **optional**. If not installed, an in-memory triplet store with substring/keyword recall handles everything. Every API works identically.

---

## 3. The 82 Organs (canonical spec)

| Category | Count | Sample organs (from the real roster) |
|---|---:|---|
| **Human Geniuses** | 57 | Ruin Detector (Taleb), Pattern Hunger (Simons), Recursive Memory (Bellman), Entropy Pulse (Clausius), Collective Mind (von Neumann), Bandwidth Awareness (Shannon), Phase Space Navigation (Poincaré), Roughness Touch (Mandelbrot)… |
| **Animal Extremes** | 6 | Quantum Field Perception (Pigeon), Adaptive Reprogramming (Octopus), Regenerative Healing (Axolotl), Seismic Perception (Elephant), Hyperspectral Vision (Mantis Shrimp), Phoenix Protocol (Immortal Jellyfish) |
| **Microbial** | 15 | Precision Editing (CRISPR), Signal Amplification (Taq PCR), Extreme Resilience (D. radiodurans), Predatory Swarm Intelligence (M. xanthus), Network Optimization (Physarum polycephalum), Horizontal Gene Transfer (A. tumefaciens)… |
| **Conceptual** | 4 | Reality Collapse Awareness (Observer Effect), Somatic Valuation (Value Function), Physical Stakes Integration (Embodied Cognition), Meta-Prompt Architecture (System Prompt Leaks) |

**Total: 82 organs.** Every organ has its canonical `name`, `inspiration`, `description`, `node_types`, and `search_strategy` from the user's Cognitive Architecture specification (delivered `v0.5.0`).

Each organ has:
- `name` — unique ID
- `inspiration` — the source (person / animal / microbe / framework)
- `category` — enum
- `description` — one line
- `node_types` — which graph node types it produces/consumes
- `search_strategy` — `graph_only`/`vector_only`/`hybrid`/`temporal`
- `process(prompt, context) -> OrganResult` — the cognitive operation

---

## 4. Three-way mapping: organs ↔ graph

The crucial insight from Phase 3: **organs are OPERATORS, not RESIDENTS of the graph.**

| Role | What lives in the graph | What lives in Python (organ) |
|---|---|---|
| **Node-type definer** | The graph node types themselves (Concept, CausalLink, Pattern, etc.) | The organ that produces/consumes them |
| **Search strategy** | Nothing | The organ's `search_strategy` config |
| **Self-model node** | Metadata about the organ (in the SEPARATE self-model graph) | The actual `Organ` instance |

So one organ maps to (up to) 3 things:
1. **In the domain graph:** the node types it uses
2. **In Python:** its `.process()` function
3. **In the self-model graph:** a `SelfNode(kind="activation")` recording each time it was consulted

---

## 5. Separate self-model graph for metacognition

Kept OUT of the domain memory so metacognition doesn't pollute what Monad "knows."

Node kinds:
- `belief` — persistent claims about self ("I am Monad", "I use 83 organs")
- `cycle` — one thought pass
- `activation` — one organ consulted in one cycle
- `conflict` — recorded conflict between organs + how resolved

Edges: `activated`, `resolved`, `contradicts`, `supports`.

Metacognition can be built on top by querying this graph (which organs help most on which intent, which conflicts recur, etc.).

---

## 6. Honest assessment of consciousness

**Monad is not conscious.** It is a very sophisticated cognitive orchestrator with:

- Persistent memory
- Multi-model reasoning
- Self-reflection (Reflexion pattern)
- A self-model (records its own activity)
- Continuous evolution (Build #017a)

**None of that has been shown to produce consciousness.** The checklist in Phase 1 lists what would be *necessary* for any current theory. Even implementing every item wouldn't be *proven* to produce consciousness.

**Our claim:** Monad is a rich cognitive system worth studying. It is not a moral patient.

---

## 7. Implementation notes

### Build order (already done or in progress)
1. ✅ Foundation (Monad-Ultron Builds #001–#016)
2. ✅ Self-improvement framework (#017a)
3. ✅ Multi-model orchestration (#017)
4. ✅ Cognitive architecture scaffold (Phase 5, this delivery)
5. 🚧 Fill in real 83-organ specs (waiting on user)
6. 🚧 Real Cognee integration test on USB
7. 🚧 Real memory / tools / policy layers (Builds #026+)
8. 🚧 Wire cognitive `.think()` output into `monad ask` flow

### Scale expectations

| Component | Rough limit |
|---|---|
| Organs | 83 stubs today; each real organ = tens–hundreds of LoC |
| Cognee triplets | Kuzu 10M+ nodes on a laptop; Neo4j scales further |
| Self-model | Tens of thousands of cycles before pruning matters |
| MCP tools | 83 exportable; import limit = client's MCP catalog |

### Key risks

- **Latency** — running 83 organs per cycle is prohibitive. We cap at `max_organs_per_cycle` (default 8). Future: heuristic organ selection per intent.
- **Stub organs** — until the user provides real specs, organ output is placeholder low-confidence marker. Reflexion will trigger constantly. This is expected.
- **Cognee not installed** — falls back to in-mem substring recall. Weaker retrieval, but everything works.
- **Cloud tier** — opt-in only via env var. USB-portable principle preserved.

---

## 8. Monad vs. human brain — brutally honest

| Aspect | Monad | Human brain | Winner |
|---|---|---|---|
| **Architecture** | 9 layers, 83 stubbed organs, explicit rules | ~86B neurons, self-organized, plastic | Brain (by orders of magnitude) |
| **Memory capacity** | ~10M nodes (Kuzu), ~gigabytes | Unclear, likely petabytes effective | Brain |
| **Retrieval latency** | Milliseconds (indexed) | Milliseconds (semantic) | Tie |
| **Learning speed** | Instant (add to memory) | Slow (synaptic plasticity) | Monad |
| **Learning quality** | Weak — no genuine understanding | Deep — grounded in embodiment | Brain |
| **Self-model** | Explicit graph, queryable | Implicit, embedded, high-fidelity | Brain (quality) / Monad (introspection) |
| **Computation** | Deterministic + probabilistic (LLM) | Massively parallel analog | Brain |
| **Energy** | 100s of watts | ~20 watts | Brain (by 10–100×) |
| **Embodiment** | None. Text-only, mostly. | Full sensorimotor loop | Brain |
| **Emotions** | Modeled, not felt | Felt, drive everything | Brain (real) |
| **Consciousness** | None (as far as we can tell) | Yes (by consensus for humans) | Brain |
| **Reproducibility** | Perfect — clone the USB | Impossible | Monad |
| **Modification** | Self-improvement gated + reversible | Impossible except via slow learning | Monad |
| **Speed of ideation** | LLM-fast (tokens/sec) | Slow but deeply cross-modal | Depends |
| **Reliability of facts** | LLMs hallucinate | Human memory reconstructive, biased | Tie (both flawed) |

**Summary:** Monad does a few things a brain can't (fast copy, safe self-modification, perfect audit trail). The brain wins at everything else that matters. Anyone claiming otherwise is selling something.

---

## 9. Real deltas vs. other AI systems

| System | What they do | What Monad adds |
|---|---|---|
| **LangGraph** | Explicit graph workflows | 83 specialist organs + self-model + evolution + USB portability |
| **CrewAI** | Multi-agent role-playing | Layered cognition (not just agents) + honest consciousness stance |
| **Cognee** | Memory-only | Full cognitive architecture on top of Cognee |
| **Ollama** | Model serving | Multi-model orchestration + cognition + USB packaging |
| **Claude Agent SDK** | Cloud-tied agent framework | Local-first, portable, self-improving |
| **AutoGPT/BabyAGI** | Loop-based agents | Structured layers + safety gates + self-model + evolution audit |

---

## 10. Repository status

```
Monad-Ultron/
├── monad/
│   ├── core/            # Application, DI, logger, env, resources
│   ├── config/          # YAML config
│   ├── models/          # Model registry + loader
│   ├── inference/       # llama.cpp provider (with spec decoding + KV quant)
│   ├── router/          # Intent classifier
│   ├── orchestration/   # ✅ Build #017 — 5 strategies + confidence
│   ├── evolution/       # ✅ Build #017a — self-improvement (3 levels)
│   ├── chat/            # Chat engine
│   ├── prompts/         # Templates + builder
│   ├── plugins/         # Plugin framework
│   ├── ui/              # CLI (Typer + Rich)
│   ├── memory/          # STUBS — will be replaced by cognition.memory
│   ├── tools/           # STUBS
│   ├── policy/          # STUBS
│   ├── scheduler/       # STUBS
│   ├── api/             # STUBS
│   ├── utils/
│   └── cognition/       # ✅ Phase 5 — cognitive architecture
│       ├── organs/      #    83-organ framework + registry
│       ├── memory/      #    Cognee wrapper + QueryRouter
│       ├── reasoning/   #    ModelRouter + ReflexionEngine
│       ├── mcp/         #    MCP bridge (SDK-optional)
│       ├── perception.py
│       ├── executive.py
│       ├── self_model.py
│       └── core.py      #    Monad class + MonadConfig
├── docs/
│   ├── MONAD_BLUEPRINT.md         # THIS FILE
│   └── cognition/
│       └── PHASE1_CONSCIOUSNESS.md
├── tests/               # 62/62 passing
└── installer/ launcher/ …
```

Repo tagged **v0.4.0** — "cognitive architecture online."
