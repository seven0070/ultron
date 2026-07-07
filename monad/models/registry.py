"""Model registry — thin in-memory store keyed by id."""

from __future__ import annotations

from monad.models.metadata import ModelMetadata


class ModelRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, ModelMetadata] = {}

    def register(self, meta: ModelMetadata) -> None:
        self._by_id[meta.id] = meta

    def get(self, model_id: str) -> ModelMetadata | None:
        return self._by_id.get(model_id)

    def all(self) -> list[ModelMetadata]:
        return list(self._by_id.values())

    def by_role(self, role: str) -> list[ModelMetadata]:
        return [m for m in self._by_id.values() if m.role == role]

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, model_id: str) -> bool:
        return model_id in self._by_id
