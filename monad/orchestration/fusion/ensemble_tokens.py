"""
FusionEnsembleTokens — L3 fusion via periodic token-level voting.

Middle ground between L2 (chain) and L4 (logits fusion):
  - Every K tokens, each model generates its next chunk in parallel.
  - The chunks are compared; majority vote (by longest common prefix) wins.
  - All models are advanced past the agreed prefix and continue.

Practical benefits:
  - Doesn't need same tokenizer (compares detokenized text).
  - Catches divergence early (unlike FusionChain, where divergence is only visible
    at the end).
  - Faster than L4 because we don't merge every single token.

Cost: N * (tokens/K) forward passes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class EnsembleTokensResult:
    text: str
    latency_ms: float
    models_used: list[str] = field(default_factory=list)
    votes_per_step: list[dict] = field(default_factory=list)
    method: str = "ensemble_tokens"


class FusionEnsembleTokens:
    def __init__(self, executor, model_ids: list[str],
                 chunk_tokens: int = 32) -> None:
        self.executor = executor
        self.model_ids = model_ids
        self.chunk_tokens = chunk_tokens

    def generate(self, prompt: str, max_tokens: int = 512,
                 temperature: float = 0.6, top_p: float = 0.9) -> EnsembleTokensResult:
        t0 = time.perf_counter()
        context = prompt
        total_generated_chars = 0
        votes_log: list[dict] = []

        # Rough char budget from max_tokens
        char_budget = max_tokens * 4

        while total_generated_chars < char_budget:
            # Ask every model for the next chunk in parallel
            proposals = self.executor.run(
                self.model_ids, context,
                max_tokens=self.chunk_tokens,
                temperature=temperature, top_p=top_p,
            )
            texts = [(r.model_id, r.text) for r in proposals if r.ok]
            if not texts:
                break

            # Longest common prefix among all proposals
            prefix = _longest_common_prefix([t for _, t in texts])
            if not prefix.strip():
                # No consensus — take the highest-confidence proposal's first chunk
                best = max(proposals, key=lambda r: (r.confidence.score if r.confidence else 0.0,
                                                     len(r.text)))
                prefix = best.text[:self.chunk_tokens * 4]

            votes_log.append({
                "step": len(votes_log) + 1,
                "prefix_chars": len(prefix),
                "proposals": {mid: len(t) for mid, t in texts},
            })

            context += prefix
            total_generated_chars += len(prefix)

            # Stop if any model produced an EOS-like signal (empty or terminal)
            if len(prefix.strip()) < 4:
                break

        generated = context[len(prompt):]
        return EnsembleTokensResult(
            text=generated,
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
            models_used=self.model_ids,
            votes_per_step=votes_log,
        )


def _longest_common_prefix(texts: list[str]) -> str:
    if not texts:
        return ""
    if len(texts) == 1:
        return texts[0]
    ref = texts[0]
    i = 0
    while i < len(ref) and all(i < len(t) and t[i] == ref[i] for t in texts):
        i += 1
    return ref[:i]
