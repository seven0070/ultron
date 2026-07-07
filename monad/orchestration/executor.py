"""
ParallelExecutor — runs multiple models concurrently and collects results.

Uses ThreadPoolExecutor because llama.cpp inference releases the GIL and is
I/O-bound relative to Python. For CPU-only inference or single-GPU with one
model at a time, results still come back sequentially — but the caller code
doesn't need to change.

Each result is a ProposerResult carrying model id, text, latency, tokens,
error state, and (optionally) a ConfidenceReport.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from monad.core.logger import get_logger

if TYPE_CHECKING:
    from monad.orchestration.confidence import ConfidenceReport

log = get_logger(__name__)


@dataclass
class ProposerResult:
    model_id: str
    text: str = ""
    latency_ms: float = 0.0
    tokens: int = 0
    error: str = ""
    confidence: "ConfidenceReport | None" = None
    metadata: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.text.strip())


class ParallelExecutor:
    def __init__(self, inference_manager, model_manager, max_workers: int = 3) -> None:
        self.inference = inference_manager
        self.models = model_manager
        self.max_workers = max_workers

    def run(
        self,
        model_ids: list[str],
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        scorer=None,
    ) -> list[ProposerResult]:
        """Execute prompt against N models in parallel; return all results."""
        results: list[ProposerResult] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(model_ids))) as pool:
            futures = {
                pool.submit(
                    self._run_one, mid, prompt, max_tokens, temperature, top_p, stop, scorer
                ): mid
                for mid in model_ids
            }
            for fut in as_completed(futures):
                results.append(fut.result())
        # Preserve caller order
        order = {mid: i for i, mid in enumerate(model_ids)}
        results.sort(key=lambda r: order.get(r.model_id, 999))
        return results

    def run_one(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
        scorer=None,
    ) -> ProposerResult:
        return self._run_one(model_id, prompt, max_tokens, temperature, top_p, stop, scorer)

    # -- internal -------------------------------------------------------------

    def _run_one(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: list[str] | None,
        scorer,
    ) -> ProposerResult:
        t0 = time.perf_counter()
        try:
            meta = self.models.get(model_id)
            provider = self.inference.get_default_provider()
            if not provider.is_loaded(model_id):
                if not meta.local_path:
                    raise RuntimeError(
                        f"Model {model_id} has no local file — run "
                        f"`python installer/download_models.py`"
                    )
                provider.load_model(meta)
            text = provider.generate(
                model_id, prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
            )
            latency = (time.perf_counter() - t0) * 1000
            result = ProposerResult(
                model_id=model_id,
                text=text,
                latency_ms=round(latency, 1),
                tokens=len(text.split()),  # rough estimate
            )
            if scorer is not None:
                result.confidence = scorer.score(text, requested_max_tokens=max_tokens)
            return result
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000
            log.warning("Model {} failed: {}", model_id, e)
            return ProposerResult(
                model_id=model_id,
                error=str(e),
                latency_ms=round(latency, 1),
            )
