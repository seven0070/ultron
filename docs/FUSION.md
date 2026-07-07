# LLM Fusion — Making Multiple Models Answer as One

Monad's Fusion layer takes the pool of loaded LLMs and produces **one unified answer**. Not one model calling another — one output the user perceives as coming from a single mind.

There are five theoretical levels of "fusion." We deliberately implement only what actually works on your hardware.

## 📊 The Five Levels

| Level | Name | What it means | Monad? |
|---|---|---|---|
| L1 | Text aggregation | Models answer separately → one merges (Mixture-of-Agents) | ✅ Already in Build #017 |
| L2 | **Sequential refinement** | Model A drafts → B refines → C polishes | ✅ **`FusionChain`** |
| L3 | **Token voting** | Every K tokens, all models vote on the next chunk | ✅ **`FusionEnsembleTokens`** |
| L4 | **Logit-level fusion** | Merge raw probability distributions per token, sample once | ✅ **`FusionLogits`** |
| L5 | Weight-level merge | Actually average model weights | ❌ Impossible across families |

**L5 is impossible** across Qwen ≠ DeepSeek ≠ Llama (different architectures, tokenizers, training). We don't pretend otherwise.

## 🎯 How to Use It

```bash
# AUTO mode — Monad picks the best available fusion for your models
monad fuse "explain quantum entanglement in simple terms"

# Force a specific mode
monad fuse "write a python function to reverse a string" --mode chain
monad fuse "who wrote Hamlet?" --mode ensemble
monad fuse "any question" --mode logits            # falls back if unavailable

# See the trace
monad fuse "your question" --trace
```

## 🧬 The Three Working Modes

### FusionChain (L2) — Sequential Refinement ⭐ *works with any models*

Each model has a role: **Draft → Refine → Polish**.
The user sees one final answer, but 3 models shaped it.

```
Your question
    ↓
Qwen 7B  (DRAFT)   →  first attempt, comprehensive
    ↓
DeepSeek (REFINE)  →  precision pass, fixes errors, tightens logic
    ↓
Llama 3B (POLISH)  →  clarity + structure for the final version
    ↓
ONE FINAL ANSWER  (single, coherent, unified)
```

**Pros:** Works with any tokenizers. Any model combo. Deterministic.
**Cons:** Slower than single model (~3×). Errors from Draft can propagate.

### FusionEnsembleTokens (L3) — Chunk Voting

Every N tokens, all models generate their next chunk in parallel. The longest common prefix wins.

```
Prompt: "The capital of France is"

  Chunk 1:
    A: "The capital of France is Paris."
    B: "The capital of France is Paris, established as..."
    C: "The capital of France is Paris and has been..."
  Longest common prefix: "The capital of France is Paris"
  → All models advanced past this
  → Loop continues
```

**Pros:** Doesn't need shared tokenizer. Catches divergence early.
**Cons:** Only useful when models substantially agree.

### FusionLogits (L4) — True Token-Level Merge ⭐ *deepest fusion*

At each token, all models return raw logit vectors. We take a weighted average, sample **once**, and feed the same token to every model.

```
At each generation step:
  Qwen logits:      [-2.1, -0.5, 0.3, ...]   over 32000 vocab
  DeepSeek logits:  [-1.8, -0.4, 0.5, ...]
  Llama logits:     [-2.3, -0.6, 0.2, ...]
                       ↓  weighted average
  Merged logits:    [-2.07, -0.5, 0.33, ...]
                       ↓  temp + top-p sample
  Next token: chosen ONCE
                       ↓  fed to all 3 models
  Continue...
```

**Pros:** Truly single output stream. Statistically fused, not just text-mixed.
**Cons:** Requires shared tokenizer (Qwen ≠ DeepSeek ≠ Llama → falls back). Requires numpy. Slower per token.

**When does L4 work?** When all pool models are from the same family — e.g. three Qwen fine-tunes, or Llama 3.2 + Llama 3.1 + Llama 3 Guard. If tokenizers differ, Monad transparently falls back to FusionChain and tells you why.

## 🤖 AUTO Mode Decision Tree

```
Is numpy installed AND all pool models share a tokenizer?
    ├─ YES → LOGITS   (deepest possible)
    └─ NO  → Are there 2+ models loaded?
             ├─ YES → ENSEMBLE  (token voting)
             └─ NO  → CHAIN     (single-model draft)
```

## ⚙️ Weights (LOGITS mode only)

You can bias the fusion toward a specific model:

```python
from monad.orchestration import FusionOrchestrator, FusionMode

fuser.fuse(
    "your question",
    mode=FusionMode.LOGITS,
    weights={"longcat2": 0.5, "glm5": 0.3, "llama2": 0.2},
)
```

Default is equal weight.

## 🚫 What Fusion Is NOT

- ❌ **Not** actual weight merging. Physically impossible across architectures.
- ❌ **Not** a new super-model. Latency is worse, not better.
- ❌ **Not** infallible. If all 3 models are wrong about the same thing, fusion is wrong too.

## 🧪 Verified Behavior

- ✅ `FusionChain` always works (any models, any tokenizers)
- ✅ `FusionEnsembleTokens` works with 2+ models
- ✅ `FusionLogits` works when tokenizers match, falls back gracefully otherwise
- ✅ `FusionOrchestrator.AUTO` picks the best available mode transparently
- ✅ 15 unit tests covering all three modes + fallbacks + trace details

## 📚 Design Sources

- Text-level MoA: Wang et al., *Mixture-of-Agents Enhances Large Language Model Capabilities*, 2024
- Logit-averaging ensembles: Jiang et al., *LLM-Blender: Ensembling Large Language Models*, ACL 2023
- Token voting / speculative-decoding-adjacent: Miao et al., *SpecInfer*, 2024
- Why weight merging fails cross-family: TIES / Model Soups literature (works only within same base)
