# Cognitive Architecture — Planned Addition

> **Status:** 📝 Noted / Pending user input
> **Requested by:** User
> **Date noted:** 2026-07-07
> **Turn context:** After Build #017 (multi-model orchestration) completion

---

## User Request (verbatim)

> "i will add **Cognitive Architecture** to this in this chat just note this down"

---

## What This Means

The user intends to add a **Cognitive Architecture** layer to Monad-Ultron in a future turn of this same chat conversation. They will provide the details (spec, design, requirements) themselves.

Until then:

- ❌ **Do NOT design or implement** the cognitive architecture proactively
- ❌ **Do NOT make assumptions** about what it should include
- ✅ **Wait for the user's spec** before touching this
- ✅ **Reserve conceptual space** in Monad's architecture for it to slot in later
- ✅ **Reference this file** when the user returns to this topic

---

## Where It Will Likely Fit

Based on Monad's current architecture, a Cognitive Architecture layer would most naturally sit **between the Router and the Orchestrator** — as a "thinking" layer that decides *how to think* about a problem before deciding *which models* to use.

```
USER
  ↓
CLI / Dashboard
  ↓
Application Manager
  ↓
Router / Intent Engine                    ← current
  ↓
┌─────────────────────────────────────┐
│  ✨ COGNITIVE ARCHITECTURE (TBD)    │  ← will slot in here
│     • perception                     │
│     • attention                      │
│     • working memory                 │
│     • reasoning / planning           │
│     • metacognition                  │
│     • (user's specific design)       │
└─────────────────────────────────────┘
  ↓
Multi-Model Orchestrator (Build #017)     ← current
  ↓
Response Synthesizer
  ↓
...
```

Anticipated new package (name TBD by user):

```
monad/
├── cognition/         # ← reserved for user's spec
│   ├── __init__.py
│   ├── ...            # (contents TBD)
```

---

## Related Existing Subsystems Worth Knowing About

When the user provides the spec, these existing pieces will likely need to integrate:

| Existing subsystem | How cognition might touch it |
|---|---|
| `monad/router/` | Cognition decides *how* to route, not just *where* |
| `monad/orchestration/` | Cognition picks strategy + model plan |
| `monad/memory/` (stubs) | Working memory ↔ episodic memory |
| `monad/prompts/` | Cognition-driven prompt construction |
| `monad/evolution/` | Metacognition could drive self-improvement |
| `monad/policy/` (stubs) | Cognitive constraints / values |

---

## When the User Returns to This

Ask (only if truly ambiguous) about:
1. **Model of cognition** — SOAR? ACT-R? Global Workspace Theory? Custom?
2. **Scope** — single component or full reasoning loop?
3. **Interaction with orchestration** — replace / wrap / augment?
4. **Persistence** — does cognitive state live in memory_data/?

Otherwise: **just build what they specify**.

---

*This is a placeholder. The user will provide the actual specification in a future message.*
