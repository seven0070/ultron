"""Provider ABC — all inference backends implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from monad.models.metadata import ModelMetadata


class InferenceProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    def load_model(self, meta: ModelMetadata) -> None: ...

    @abstractmethod
    def unload_model(self, meta: ModelMetadata) -> None: ...

    @abstractmethod
    def is_loaded(self, model_id: str) -> bool: ...

    @abstractmethod
    def generate(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> str: ...

    def stream(
        self,
        model_id: str,
        prompt: str,
        **kwargs,
    ) -> Iterator[str]:
        """Default: fall back to single-shot generate. Providers can override."""
        yield self.generate(model_id, prompt, **kwargs)
