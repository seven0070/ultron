"""
ResponseSynthesizer — merge N proposer outputs into one answer.

Modes:
  - "best"      : pick highest-confidence result (fast, no extra LLM call)
  - "aggregate" : ask the aggregator model to synthesize (Mixture-of-Agents style)
  - "vote"      : text-similarity majority vote (best for factual QA)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from monad.core.logger import get_logger
from monad.orchestration.executor import ParallelExecutor, ProposerResult

log = get_logger(__name__)


SynthesisMode = Literal["best", "aggregate", "vote"]


@dataclass
class SynthesisResult:
    text: str
    mode: SynthesisMode
    picked_model: str = ""
    aggregator_model: str = ""
    votes: dict = None
    latency_ms: float = 0.0


class ResponseSynthesizer:
    def __init__(self, executor: ParallelExecutor) -> None:
        self.executor = executor

    def synthesize(
        self,
        results: list[ProposerResult],
        mode: SynthesisMode = "best",
        aggregator_model: str = "",
        original_prompt: str = "",
    ) -> SynthesisResult:
        good = [r for r in results if r.ok]
        if not good:
            errs = "; ".join(f"{r.model_id}: {r.error}" for r in results)
            return SynthesisResult(text=f"[all proposers failed: {errs}]", mode=mode)

        if mode == "best":
            return self._pick_best(good)
        if mode == "vote":
            return self._vote(good)
        if mode == "aggregate":
            return self._aggregate(good, aggregator_model, original_prompt)
        return self._pick_best(good)

    # -- best -----------------------------------------------------------------

    def _pick_best(self, results: list[ProposerResult]) -> SynthesisResult:
        # If confidence scores present, pick the max; else pick the longest.
        with_conf = [r for r in results if r.confidence is not None]
        if with_conf:
            best = max(with_conf, key=lambda r: r.confidence.score)
        else:
            best = max(results, key=lambda r: len(r.text))
        return SynthesisResult(
            text=best.text,
            mode="best",
            picked_model=best.model_id,
            latency_ms=best.latency_ms,
        )

    # -- vote -----------------------------------------------------------------

    def _vote(self, results: list[ProposerResult]) -> SynthesisResult:
        """
        Loose vote: normalize each answer to a canonical form, count.
        Best for factual QA where the "right answer" is a short phrase.
        """
        def canon(s: str) -> str:
            return " ".join(s.strip().lower().split())[:200]

        buckets: dict[str, list[ProposerResult]] = {}
        for r in results:
            buckets.setdefault(canon(r.text), []).append(r)

        counts = Counter({k: len(v) for k, v in buckets.items()})
        winning_key, _ = counts.most_common(1)[0]
        winning_bucket = buckets[winning_key]
        # Pick the highest-confidence representative from the winning bucket
        rep = max(
            winning_bucket,
            key=lambda r: (r.confidence.score if r.confidence else 0.0, len(r.text)),
        )
        return SynthesisResult(
            text=rep.text,
            mode="vote",
            picked_model=rep.model_id,
            votes={k[:60]: v for k, v in counts.items()},
            latency_ms=sum(r.latency_ms for r in results) / len(results),
        )

    # -- aggregate ------------------------------------------------------------

    def _aggregate(
        self, results: list[ProposerResult], aggregator_model: str, original_prompt: str
    ) -> SynthesisResult:
        if not aggregator_model:
            log.warning("aggregate mode requested but no aggregator_model — using best")
            return self._pick_best(results)

        rendered = "\n\n".join(
            f"--- Proposal from {r.model_id} "
            f"(conf={r.confidence.score if r.confidence else 'n/a'}) ---\n{r.text}"
            for r in results
        )
        agg_prompt = (
            "You are the Aggregator. Multiple assistants have proposed answers to a user's "
            "question. Read all proposals critically, discard errors, keep the strongest ideas, "
            "and produce ONE final answer that is more complete and correct than any single "
            "proposal. Do not mention the proposers or your own role.\n\n"
            f"USER QUESTION:\n{original_prompt}\n\n"
            f"PROPOSALS:\n{rendered}\n\n"
            "FINAL ANSWER:"
        )
        merged = self.executor.run_one(
            aggregator_model, agg_prompt, max_tokens=1200, temperature=0.4,
        )
        if not merged.ok:
            log.warning("Aggregator {} failed: {} — falling back to best",
                        aggregator_model, merged.error)
            return self._pick_best(results)
        return SynthesisResult(
            text=merged.text,
            mode="aggregate",
            aggregator_model=aggregator_model,
            latency_ms=sum(r.latency_ms for r in results) + merged.latency_ms,
        )
