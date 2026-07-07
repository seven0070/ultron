"""
TokenizerAligner — detects whether models share a tokenizer.

Token-level and logit-level fusion require a shared vocabulary. If tokenizers
differ, the safe path is to fall back to text-level fusion (FusionChain).

We do a probe: encode a fixed test string on each model and compare the token
sequences. If they match, tokenizers are compatible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenizerCompatibility(str, Enum):
    IDENTICAL = "identical"     # exact same tokenizer — safe for logits fusion
    COMPATIBLE = "compatible"   # same vocab size, small differences (rare)
    DIFFERENT = "different"     # different vocabs — logits fusion impossible


@dataclass
class AlignmentReport:
    compatibility: TokenizerCompatibility
    model_ids: list[str]
    vocab_sizes: dict[str, int]
    reason: str = ""


class TokenizerAligner:
    """Cheap probe — no extra model calls needed at inference time."""

    PROBE_STRINGS = [
        "The quick brown fox jumps over the lazy dog.",
        "def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)",
        "Émoji test: 🧠 🚀 café naïve",
    ]

    def __init__(self, provider) -> None:
        """provider must be a loaded LlamaCppProvider (or duck-compatible)."""
        self.provider = provider

    def check(self, model_ids: list[str]) -> AlignmentReport:
        """Return an AlignmentReport for a list of loaded model IDs."""
        if len(model_ids) < 2:
            return AlignmentReport(
                compatibility=TokenizerCompatibility.IDENTICAL,
                model_ids=model_ids,
                vocab_sizes={},
                reason="single model — trivially compatible",
            )

        vocab_sizes: dict[str, int] = {}
        token_signatures: dict[str, tuple] = {}

        for mid in model_ids:
            llm = self._get_llama_instance(mid)
            if llm is None:
                return AlignmentReport(
                    compatibility=TokenizerCompatibility.DIFFERENT,
                    model_ids=model_ids, vocab_sizes={},
                    reason=f"model {mid} not loaded",
                )
            vocab_sizes[mid] = self._vocab_size(llm)

            sigs = []
            for probe in self.PROBE_STRINGS:
                toks = self._tokenize(llm, probe)
                sigs.append(tuple(toks))
            token_signatures[mid] = tuple(sigs)

        # All vocab sizes match AND all token sequences match?
        first_sig = next(iter(token_signatures.values()))
        first_vocab = next(iter(vocab_sizes.values()))

        if all(s == first_sig for s in token_signatures.values()):
            return AlignmentReport(
                compatibility=TokenizerCompatibility.IDENTICAL,
                model_ids=model_ids, vocab_sizes=vocab_sizes,
                reason="all models produced identical token sequences on probes",
            )

        if all(v == first_vocab for v in vocab_sizes.values()):
            return AlignmentReport(
                compatibility=TokenizerCompatibility.COMPATIBLE,
                model_ids=model_ids, vocab_sizes=vocab_sizes,
                reason=f"same vocab size ({first_vocab}) but different tokenization",
            )

        return AlignmentReport(
            compatibility=TokenizerCompatibility.DIFFERENT,
            model_ids=model_ids, vocab_sizes=vocab_sizes,
            reason=f"vocab sizes differ: {vocab_sizes}",
        )

    # -- llama.cpp introspection helpers -------------------------------------

    def _get_llama_instance(self, model_id: str):
        try:
            return self.provider._loaded.get(model_id)
        except Exception:
            return None

    def _vocab_size(self, llm) -> int:
        for attr in ("n_vocab", "vocab_size"):
            v = getattr(llm, attr, None)
            if callable(v):
                try:
                    return int(v())
                except Exception:
                    pass
            elif v is not None:
                return int(v)
        try:
            return len(llm.tokenize(b" ", add_bos=False))  # crude fallback
        except Exception:
            return -1

    def _tokenize(self, llm, text: str) -> list[int]:
        try:
            return list(llm.tokenize(text.encode("utf-8"), add_bos=False))
        except Exception:
            return []
