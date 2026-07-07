"""
ReflexionEngine — generate → reflect → research → revise loop.

Based on the Reflexion pattern (Shinn et al. 2023, updated for 2026 agent
frameworks). Given a low-confidence draft, the engine:

    1. Generates a critique of the draft
    2. Optionally queries memory for missing info
    3. Produces a revised answer

Fully functional without an LLM (heuristic critique + revision); if an LLM is
provided via `llm_generate`, it uses the LLM for higher-quality critique.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ReflexionTrace:
    original: str
    critique: str = ""
    research_queries: list[str] = field(default_factory=list)
    research_hits: list[str] = field(default_factory=list)
    revised: str = ""


class ReflexionEngine:
    """
    llm_generate: optional callable (prompt: str) -> str
    memory:       optional MemoryLayer for the "research" step
    """

    def __init__(self, llm_generate: Callable[[str], str] | None = None,
                 memory=None) -> None:
        self.llm_generate = llm_generate
        self.memory = memory

    # -- public API -----------------------------------------------------------

    def reflect_and_revise(
        self,
        prompt: str,
        draft: str,
        organ_results: list | None = None,
    ) -> str:
        trace = self.reflect_and_revise_traced(prompt, draft, organ_results)
        return trace.revised or draft

    def reflect_and_revise_traced(
        self,
        prompt: str,
        draft: str,
        organ_results: list | None = None,
    ) -> ReflexionTrace:
        trace = ReflexionTrace(original=draft)

        # 1. Critique
        trace.critique = self._critique(prompt, draft)

        # 2. Research (optional, memory-based)
        if self.memory is not None:
            queries = self._research_queries(prompt, trace.critique)
            trace.research_queries = queries
            hits = []
            for q in queries[:3]:
                for r in self.memory.recall(q, top_k=2):
                    hits.append(r.get("text", ""))
            trace.research_hits = hits

        # 3. Revise
        trace.revised = self._revise(prompt, draft, trace)
        return trace

    # -- internals ------------------------------------------------------------

    def _critique(self, prompt: str, draft: str) -> str:
        if self.llm_generate is not None:
            try:
                p = (
                    "You are a strict reviewer. Read the QUESTION and the DRAFT ANSWER. "
                    "List concrete flaws (missing info, unclear steps, factual errors). "
                    "Be terse.\n\n"
                    f"QUESTION:\n{prompt}\n\nDRAFT:\n{draft}\n\nCRITIQUE:"
                )
                return self.llm_generate(p).strip()
            except Exception:
                pass
        # Heuristic critique
        issues = []
        d = draft.strip()
        if len(d) < 40:
            issues.append("answer is too short")
        if d.lower().startswith(("i don't know", "i'm not sure", "i cannot")):
            issues.append("answer expresses uncertainty/refusal")
        if d.count("```") % 2 != 0:
            issues.append("code fence not closed")
        if not issues:
            issues.append("no obvious flaws by heuristic; consider verifying facts")
        return "; ".join(issues)

    def _research_queries(self, prompt: str, critique: str) -> list[str]:
        # Cheap: pull nouns from critique + top nouns from prompt
        tokens = [w.strip(".,;:") for w in (prompt + " " + critique).split()
                  if len(w) > 3 and w[0].isupper()]
        seen, out = set(), []
        for t in tokens:
            if t.lower() not in seen:
                seen.add(t.lower())
                out.append(t)
        return out[:5]

    def _revise(self, prompt: str, draft: str, trace: ReflexionTrace) -> str:
        if self.llm_generate is not None:
            try:
                extra = "\n".join(trace.research_hits[:5])
                p = (
                    "You are the reviser. Rewrite the DRAFT to address every point in the "
                    "CRITIQUE, using RESEARCH if helpful. Output only the revised answer.\n\n"
                    f"QUESTION:\n{prompt}\n\nDRAFT:\n{draft}\n\n"
                    f"CRITIQUE:\n{trace.critique}\n\nRESEARCH:\n{extra}\n\nREVISED:"
                )
                return self.llm_generate(p).strip()
            except Exception:
                pass
        # Heuristic revision — append acknowledgment + research hits
        parts = [draft.strip()]
        if trace.research_hits:
            parts.append("\n\n(Additional context from memory:")
            for h in trace.research_hits[:3]:
                parts.append(f"  • {h[:200]}")
            parts.append(")")
        else:
            parts.append(
                f"\n\n(Note: reviewer identified — {trace.critique}. "
                "Consider treating this answer as tentative.)"
            )
        return "\n".join(parts)
