"""PromptBuilder — renders a template with a context."""

from __future__ import annotations

from monad.prompts.context import PromptContext


class PromptBuilder:
    def build(self, template: str, context: PromptContext) -> str:
        vars_ = dict(context.variables)
        vars_.setdefault("system", context.system)
        vars_.setdefault(
            "history",
            "\n".join(f"{h['role'].capitalize()}: {h['content']}" for h in context.history),
        )
        # Fill placeholders defensively — missing keys become empty strings
        class _SafeDict(dict):
            def __missing__(self, k):
                return ""
        return template.format_map(_SafeDict(vars_))
