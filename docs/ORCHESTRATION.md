# Monad Multi-Model Orchestration (Build #017)

## The Big Idea

Instead of asking one model everything, Monad routes each request through the **right strategy for the job**, coordinating multiple models when it helps and using just one when it doesn't.

## The 5 Strategies

| Strategy | When Monad picks it | How it works |
|---------|--------------------|--------------|
| **domain_routing** | General chat, creative, summarization | Intent classifier → route to the specialist model. Fastest, cheapest. |
| **cascade** | Questions, unknown intent | Try the cheap/fast model. If confidence is low, escalate to the strong model. |
| **mixture_of_agents** | Analysis, open-ended reasoning | All 3 models answer in parallel. A 4th "aggregator" LLM merges into one better answer. |
| **verification** | Coding tasks | Proposer writes; a different model verifies/rewrites. Catches bugs. |
| **ensemble** | Short factual QA | All models answer. Majority vote wins. Best when models should agree. |

You can force any strategy with `--strategy`, or let Monad auto-pick per intent.

## Auto-selection table

| Intent | Strategy chosen |
|--------|-----------------|
| coding | verification |
| creative | domain_routing |
| analysis | mixture_of_agents |
| summarization | domain_routing |
| question | cascade |
| general_chat | domain_routing |
| unknown | cascade |

## CLI Usage

```bash
# Auto strategy (recommended)
monad ask "write a python function to reverse a string"
monad ask "analyze the pros and cons of nuclear energy"
monad ask "what's the capital of France?"

# See the full trace (which models, what confidence, escalations, timing)
monad ask "your question" --trace

# Force a strategy
monad ask "your question" --strategy mixture_of_agents
monad ask "your question" --strategy ensemble
monad ask "your question" --strategy cascade

# List strategies
monad strategies
```

## The Confidence Scorer

Cascade & synthesis need to know how "good" an answer is. We use cheap heuristics (no extra model calls):

| Signal | Weight | What it catches |
|--------|-------|-----------------|
| Length reasonable | 0.20 | Too-short or truncated answers |
| No hedging | 0.25 | "I'm not sure", "I don't know", "as an AI" |
| No refusal | 0.20 | "I can't help with that" |
| Low repetition | 0.20 | Common local-model failure: looping |
| Complete format | 0.15 | Unclosed code fences, trailing "…" |

Score is 0.0–1.0. Cascade's default escalation threshold is 0.55.

## Performance Optimizations (integrated into LlamaCppProvider)

Based on 2026 llama.cpp best practices:

- **Speculative decoding** — pair each big model with a tiny "draft" model → **1.5–3× decode speedup**
- **KV cache quantization** (`type_k=q8_0`, `type_v=q8_0`) — **~75% VRAM reduction** for context
- **Flash Attention** (`flash_attn=true`) — memory bandwidth boost
- **Batch/ubatch tuning** — per-model in `models.yaml` `extra:` section
- **Version-safe kwargs** — provider auto-drops kwargs the installed `llama-cpp-python` doesn't recognize

## Configuration

`config.yaml`:
```yaml
orchestration:
  enabled: true
  default_strategy: "auto"     # or force one strategy
  max_workers: 3               # parallel proposer threads
  model_pool:
    reasoning: "longcat2"
    coding: "glm5"
    creative: "llama2"
  cascade_threshold: 0.55
```

`models.yaml` (`extra:` section per model):
```yaml
- id: "longcat2"
  # …
  extra:
    draft_model: "qwen2.5-draft"   # speculative decoding partner
    cache_type_k: "q8_0"           # KV quant
    cache_type_v: "q8_0"
    flash_attn: true
    batch_size: 512
```

## Design Sources

- **Velsof**, *Multi-LLM Orchestration in 2026: 7 Battle-Tested Patterns*
- **SLM-MUX (ICLR 2026)**: crucial finding — discussion-based orchestration **fails** with small models. That's why our default is selection-based (domain_routing / cascade), not debate.
- **vucense.com**, *Speculative Decoding Explained: 2× faster local LLMs*
- **llama.cpp discussion #10466**, speculative decoding on consumer GPUs
- **Braincuber**, *Multi-Token Prediction in llama.cpp: 2.4× faster inference*

## What's Next

Build #017 lays the *strategy* framework. Follow-ups:

- **#018** — Response synthesizer improvements (chain-of-thought merging)
- **#019** — Model-specific prompt templates per role
- **#020** — Adaptive strategy selection (learn which strategy works best per user)
- **#021** — Streaming output (token-by-token from proposers + aggregator)
- **#022** — Multi-model chat mode (`monad chat --multi`)
