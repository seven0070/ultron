"""Base model interface (ABC)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from monad.models.metadata import ModelMetadata


class BaseModel(ABC):
    """Abstract model contract — every concrete model implementation adheres to this."""

    metadata: ModelMetadata

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def is_loaded(self) -> bool: ...

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...
