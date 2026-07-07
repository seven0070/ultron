"""PromptManager — central access to templates + builder."""

from __future__ import annotations

from monad.prompts.builder import PromptBuilder
from monad.prompts.context import PromptContext
from monad.prompts.templates import TEMPLATES


class PromptManager:
    def __init__(self) -> None:
        self._templates: dict[str, str] = dict(TEMPLATES)
        self._builder = PromptBuilder()

    def add_template(self, name: str, text: str) -> None:
        self._templates[name] = text

    def get_template(self, name: str) -> str:
        if name not in self._templates:
            raise KeyError(f"No such prompt template: {name}")
        return self._templates[name]

    def render(self, template_name: str, context: PromptContext) -> str:
        tpl = self.get_template(template_name)
        return self._builder.build(tpl, context)

    def list_templates(self) -> list[str]:
        return sorted(self._templates)
