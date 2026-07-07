"""
ConfidenceScorer — heuristic scoring for model outputs.

We can't rely on logprobs (llama.cpp exposes them but not uniformly), so we
combine several cheap signals:

  - length reasonableness    (too short or truncated at max_tokens = suspicious)
  - hedge/uncertainty markers ("I'm not sure", "I don't know", "as an AI")
  - refusal markers          ("I can't help with that")
  - repetition ratio         (looping is a common local-model failure mode)
  - format completeness      (unclosed code fences, trailing "…")

Returns 0.0–1.0. Used by Cascade (escalate if <threshold) and by Verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEDGE_RE = re.compile(
    r"\b(i(?:'m| am) not sure|i don't know|i'm unable|i cannot|as an ai|"
    r"i apologi[sz]e|i don't have (?:the )?ability|no clear answer|"
    r"insufficient information)\b",
    re.IGNORECASE,
)
_REFUSAL_RE = re.compile(
    r"\b(i can(?:'|no)t (?:help|assist|do that|comply)|i won't|"
    r"i must decline|against my (?:guidelines|policy))\b",
    re.IGNORECASE,
)
_TRAIL_ELLIPSIS = re.compile(r"(?:\.{3,}|…)\s*$")


@dataclass
class ConfidenceReport:
    score: float
    length_ok: bool
    no_hedging: bool
    no_refusal: bool
    low_repetition: bool
    complete_format: bool
    reasons: list[str]


class ConfidenceScorer:
    """Cheap, transparent scoring — no extra model calls."""

    def __init__(
        self,
        min_chars: int = 20,
        max_chars_soft: int = 8000,
        repetition_threshold: float = 0.35,
    ) -> None:
        self.min_chars = min_chars
        self.max_chars_soft = max_chars_soft
        self.repetition_threshold = repetition_threshold

    def score(self, text: str, requested_max_tokens: int | None = None) -> ConfidenceReport:
        reasons: list[str] = []
        text_stripped = (text or "").strip()

        length_ok = len(text_stripped) >= self.min_chars
        if not length_ok:
            reasons.append(f"too short ({len(text_stripped)} chars)")

        no_hedging = not bool(_HEDGE_RE.search(text_stripped))
        if not no_hedging:
            reasons.append("contains hedge/uncertainty phrases")

        no_refusal = not bool(_REFUSAL_RE.search(text_stripped))
        if not no_refusal:
            reasons.append("model refused")

        rep = self._repetition_ratio(text_stripped)
        low_repetition = rep < self.repetition_threshold
        if not low_repetition:
            reasons.append(f"repetitive output (ratio={rep:.2f})")

        complete_format = self._format_complete(text_stripped)
        if not complete_format:
            reasons.append("output appears truncated (open fence or trailing …)")

        # Weighted score
        score = 0.0
        score += 0.20 if length_ok else 0.0
        score += 0.25 if no_hedging else 0.0
        score += 0.20 if no_refusal else 0.0
        score += 0.20 if low_repetition else 0.0
        score += 0.15 if complete_format else 0.0

        return ConfidenceReport(
            score=round(score, 3),
            length_ok=length_ok,
            no_hedging=no_hedging,
            no_refusal=no_refusal,
            low_repetition=low_repetition,
            complete_format=complete_format,
            reasons=reasons,
        )

    # -- internals ------------------------------------------------------------

    def _repetition_ratio(self, text: str) -> float:
        """Fraction of 4-grams that repeat. High = looping."""
        tokens = text.split()
        if len(tokens) < 12:
            return 0.0
        grams = [" ".join(tokens[i : i + 4]) for i in range(len(tokens) - 3)]
        if not grams:
            return 0.0
        unique = len(set(grams))
        return 1.0 - (unique / len(grams))

    def _format_complete(self, text: str) -> bool:
        # Unbalanced code fences?
        if text.count("```") % 2 != 0:
            return False
        # Trailing ellipsis?
        if _TRAIL_ELLIPSIS.search(text):
            return False
        return True
