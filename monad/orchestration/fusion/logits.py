"""
FusionLogits — L4 fusion via token-level probability averaging.

Feels like a single unified model to the user.

At each generation step:
  1. Feed the current context to all N loaded models.
  2. Each model returns a logit vector over the shared vocabulary.
  3. Weighted-average the logit vectors (softmax after averaging in log-space).
  4. Sample ONE token from the merged distribution.
  5. Append the sampled token to context for ALL models. Repeat.

Requirements:
  - All models must share the same tokenizer (checked by TokenizerAligner).
  - llama-cpp-python compiled with `logits_all=True` support (default in 2026).

If requirements aren't met, `available_reason()` returns a diagnostic and
callers should fall back to FusionChain.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class LogitsFusionResult:
    text: str
    tokens_generated: int
    latency_ms: float
    models_used: list[str] = field(default_factory=list)
    method: str = "logits_fusion"
    fallback_reason: str = ""


class FusionLogits:
    def __init__(self, provider, model_ids: list[str],
                 weights: dict[str, float] | None = None) -> None:
        """
        provider: LlamaCppProvider
        model_ids: models to fuse (must be loaded)
        weights: {model_id: weight}, defaults to equal weights
        """
        self.provider = provider
        self.model_ids = model_ids
        if weights is None:
            w = 1.0 / max(len(model_ids), 1)
            self.weights = {mid: w for mid in model_ids}
        else:
            total = sum(weights.values()) or 1.0
            self.weights = {mid: w / total for mid, w in weights.items()}

    # -- availability check --------------------------------------------------

    def available_reason(self) -> str:
        """Empty string = available. Non-empty = reason it's NOT available."""
        try:
            import numpy  # noqa: F401
        except ImportError:
            return "numpy not installed (required for logit vector math)"

        loaded = []
        for mid in self.model_ids:
            llm = self.provider._loaded.get(mid) if hasattr(self.provider, "_loaded") else None
            if llm is None:
                return f"model {mid} not loaded"
            if not (hasattr(llm, "eval") or hasattr(llm, "tokenize")):
                return f"model {mid} lacks low-level llama.cpp API"
            loaded.append(llm)

        from monad.orchestration.fusion.aligner import (
            TokenizerAligner, TokenizerCompatibility,
        )
        report = TokenizerAligner(self.provider).check(self.model_ids)
        if report.compatibility == TokenizerCompatibility.DIFFERENT:
            return f"tokenizers differ ({report.reason})"

        return ""

    # -- generation ----------------------------------------------------------

    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7, top_p: float = 0.9,
                 stop_tokens: list[str] | None = None) -> LogitsFusionResult:
        """Generate a single fused output. Falls back to first model on error."""
        reason = self.available_reason()
        if reason:
            log.warning("FusionLogits unavailable: {}", reason)
            return LogitsFusionResult(
                text="", tokens_generated=0, latency_ms=0.0,
                models_used=self.model_ids,
                method="unavailable", fallback_reason=reason,
            )

        try:
            import numpy as np
        except ImportError:
            return LogitsFusionResult(
                text="", tokens_generated=0, latency_ms=0.0,
                fallback_reason="numpy import failed",
            )

        t0 = time.perf_counter()
        llms = [self.provider._loaded[mid] for mid in self.model_ids]
        ws = np.array([self.weights[mid] for mid in self.model_ids], dtype=np.float32)

        # Encode prompt on the first model — tokenizer is shared so tokens are identical
        prompt_tokens = list(llms[0].tokenize(prompt.encode("utf-8"), add_bos=True))
        context = list(prompt_tokens)

        # Reset & prefill each model on the prompt
        for llm in llms:
            try:
                llm.reset()
            except AttributeError:
                pass
            self._eval_tokens(llm, prompt_tokens)

        generated_tokens: list[int] = []
        eos_token = self._eos_token(llms[0])

        for _ in range(max_tokens):
            # Get logits from each model at the current position
            logits_list = []
            for llm in llms:
                lg = self._current_logits(llm)
                if lg is None:
                    log.warning("logits unavailable — aborting fusion")
                    return self._fallback(prompt, max_tokens, temperature, top_p,
                                          t0, "logits unavailable at runtime")
                logits_list.append(np.asarray(lg, dtype=np.float32))

            # Weighted average of logits
            stacked = np.stack(logits_list, axis=0)
            merged = np.tensordot(ws, stacked, axes=(0, 0))

            # Apply temperature + top-p sample
            next_tok = self._sample(merged, temperature=temperature, top_p=top_p, np=np)
            if next_tok == eos_token:
                break

            generated_tokens.append(next_tok)

            # Feed the sampled token back into every model
            for llm in llms:
                self._eval_tokens(llm, [next_tok])

            # Early stop-token detection
            if stop_tokens:
                partial = llms[0].detokenize(generated_tokens).decode("utf-8", errors="replace")
                if any(s and s in partial for s in stop_tokens):
                    break

        text = llms[0].detokenize(generated_tokens).decode("utf-8", errors="replace")
        return LogitsFusionResult(
            text=text,
            tokens_generated=len(generated_tokens),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
            models_used=self.model_ids,
            method="logits_fusion",
        )

    # -- llama.cpp helpers ---------------------------------------------------

    def _eval_tokens(self, llm, tokens: list[int]) -> None:
        """Feed tokens through llama.cpp. Handles both old + new APIs."""
        if not tokens:
            return
        try:
            llm.eval(tokens)                    # older api
            return
        except AttributeError:
            pass
        # Newer llama-cpp-python uses .eval(tokens) but some builds need batching
        try:
            for tok in tokens:
                llm.eval([tok])
        except Exception as e:
            log.debug("eval failed: {}", e)

    def _current_logits(self, llm):
        """Return the raw logits vector for the last processed token."""
        try:
            # llama-cpp-python exposes scores/eval_logits after eval()
            for attr in ("eval_logits", "_scores", "scores"):
                v = getattr(llm, attr, None)
                if v is not None:
                    if callable(v):
                        v = v()
                    # eval_logits is typically list-of-list — take the last
                    if isinstance(v, list) and v and isinstance(v[0], (list, tuple)):
                        return v[-1]
                    return v
        except Exception:
            pass
        return None

    def _eos_token(self, llm) -> int:
        for attr in ("token_eos", "_token_eos"):
            v = getattr(llm, attr, None)
            if callable(v):
                try: return int(v())
                except Exception: pass
            elif v is not None:
                try: return int(v)
                except Exception: pass
        return 2   # llama default

    def _sample(self, logits, temperature: float, top_p: float, np) -> int:
        if temperature <= 0:
            return int(np.argmax(logits))

        logits = logits / max(temperature, 1e-6)
        logits = logits - np.max(logits)
        probs = np.exp(logits)
        probs = probs / probs.sum()

        # top-p (nucleus) sampling
        if 0.0 < top_p < 1.0:
            sorted_idx = np.argsort(-probs)
            sorted_probs = probs[sorted_idx]
            cumsum = np.cumsum(sorted_probs)
            cutoff = int(np.searchsorted(cumsum, top_p) + 1)
            kept = sorted_idx[:cutoff]
            kept_probs = probs[kept] / probs[kept].sum()
            return int(np.random.choice(kept, p=kept_probs))

        return int(np.random.choice(len(probs), p=probs))

    def _fallback(self, prompt, max_tokens, temperature, top_p, t0, reason):
        """Fall back to just the first model."""
        first = self.model_ids[0]
        text = self.provider.generate(first, prompt, max_tokens=max_tokens,
                                       temperature=temperature, top_p=top_p)
        return LogitsFusionResult(
            text=text, tokens_generated=len(text.split()),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
            models_used=[first], method="fallback_single",
            fallback_reason=reason,
        )
