"""Registry of inference providers."""

from __future__ import annotations

from monad.core.logger import get_logger
from monad.inference.interfaces import InferenceProvider

log = get_logger(__name__)


class InferenceManager:
    def __init__(self) -> None:
        self._providers: dict[str, InferenceProvider] = {}
        self._default: str | None = None

    def register(self, provider: InferenceProvider, default: bool = False) -> None:
        self._providers[provider.name] = provider
        if default or self._default is None:
            self._default = provider.name
        log.debug("Registered inference provider: {} (default={})", provider.name, default)

    def get(self, name: str) -> InferenceProvider:
        if name not in self._providers:
            raise KeyError(f"No such inference provider: {name}")
        return self._providers[name]

    def get_default_provider(self) -> InferenceProvider:
        if self._default is None:
            raise RuntimeError("No inference provider registered")
        return self._providers[self._default]

    def list(self) -> list[str]:
        return list(self._providers)
