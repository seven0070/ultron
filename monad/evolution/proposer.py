"""
PatchProposer — asks the LLMs to draft a code change.

Uses GLM-5 (coding specialist) to draft the patch, LongCat 2 (reasoning) to
review the intent, Llama 2 (creative) optionally for brainstorming alternatives.

Falls back to stub-mode when no models are loaded — returns a template diff
the user can hand-edit. This makes the framework testable end-to-end today.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from monad.core.logger import get_logger
from monad.evolution.evolvable import EvolutionZone, is_path_allowed

log = get_logger(__name__)


@dataclass
class PatchProposal:
    goal: str
    zone: EvolutionZone
    target_path: str
    original_content: str
    proposed_content: str
    rationale: str = ""
    model_used: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def diff(self) -> str:
        import difflib
        return "".join(difflib.unified_diff(
            self.original_content.splitlines(keepends=True),
            self.proposed_content.splitlines(keepends=True),
            fromfile=f"a/{self.target_path}",
            tofile=f"b/{self.target_path}",
        ))


class PatchProposer:
    """Draft a patch for an evolvable file."""

    def __init__(self, root: Path, inference_manager=None, model_manager=None) -> None:
        self.root = Path(root)
        self.inference = inference_manager
        self.models = model_manager

    def propose(
        self,
        goal: str,
        zone: EvolutionZone,
        target_path: str,
        preferred_model: str = "glm5",
    ) -> PatchProposal:
        """
        Draft a patch. Refuses if target is outside allowed zones.
        """
        allowed, reason = is_path_allowed(target_path)
        if not allowed:
            raise PermissionError(f"Cannot modify {target_path}: {reason}")

        target_full = (self.root / target_path).resolve()
        # ensure target stays inside root
        try:
            target_full.relative_to(self.root)
        except ValueError:
            raise PermissionError(f"Target path escapes Monad root: {target_path}")

        original = target_full.read_text(encoding="utf-8") if target_full.exists() else ""
        proposed, rationale, model_used, warnings = self._draft(
            goal, target_path, original, preferred_model
        )

        return PatchProposal(
            goal=goal,
            zone=zone,
            target_path=target_path,
            original_content=original,
            proposed_content=proposed,
            rationale=rationale,
            model_used=model_used,
            warnings=warnings,
        )

    def _draft(
        self, goal: str, target_path: str, original: str, preferred_model: str
    ) -> tuple[str, str, str, list[str]]:
        """
        Try LLM-based drafting. Fall back to a stub template if models unavailable.
        Returns (proposed_content, rationale, model_used, warnings).
        """
        try:
            provider = self.inference.get_default_provider() if self.inference else None
            meta = self.models.get(preferred_model) if self.models else None
            if not (provider and meta and meta.local_path
                    and provider.is_loaded(preferred_model)):
                raise RuntimeError("no live model available")

            prompt = self._build_prompt(goal, target_path, original)
            reply = provider.generate(
                preferred_model, prompt,
                max_tokens=2048, temperature=0.2, top_p=0.9,
            )
            proposed, rationale = self._extract_code_and_rationale(reply, original)
            return proposed, rationale, preferred_model, []

        except Exception as e:
            log.info("PatchProposer falling back to stub: {}", e)
            stub_marker = (
                f"\n\n# TODO(monad-evolution): {goal}\n"
                f"# Auto-drafted stub — no live model was available. "
                f"Edit this file manually or re-run when a model is loaded.\n"
            )
            proposed = (original or "") + stub_marker
            return (
                proposed,
                f"Stub proposal — LLM unavailable ({e}). Marker inserted for manual edit.",
                "stub",
                ["no_llm_available"],
            )

    def _build_prompt(self, goal: str, target_path: str, original: str) -> str:
        preview = original if len(original) < 4000 else original[:4000] + "\n# … (truncated)\n"
        return (
            "You are an expert Python engineer working on the Monad-Ultron project.\n"
            "Your job: apply a small, focused change to ONE file.\n\n"
            f"GOAL:\n{goal}\n\n"
            f"TARGET FILE: {target_path}\n\n"
            "CURRENT FILE CONTENT (may be empty for a new file):\n"
            "```python\n" + preview + "\n```\n\n"
            "OUTPUT FORMAT (strict):\n"
            "```python\n"
            "# full new file content here — no ellipses, no partial code\n"
            "```\n\n"
            "RATIONALE:\n"
            "<one paragraph explaining what you changed and why>\n"
        )

    def _extract_code_and_rationale(self, reply: str, fallback: str) -> tuple[str, str]:
        """Pull ```python...``` block + trailing rationale out of LLM reply."""
        code = fallback
        rationale = ""
        if "```" in reply:
            parts = reply.split("```")
            for i, block in enumerate(parts):
                if i % 2 == 1:  # inside a fence
                    body = block
                    if body.lower().startswith("python\n"):
                        body = body.split("\n", 1)[1] if "\n" in body else ""
                    code = body
                    break
            # rationale = text after the last fence
            after = parts[-1].strip()
            if after and not after.startswith("`"):
                rationale = after
        else:
            rationale = reply.strip()
        return code.rstrip() + "\n", rationale or "(no rationale provided)"
