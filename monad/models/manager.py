"""
Model manager — orchestrates registry, filesystem checks, load/unload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from monad.core.logger import get_logger
from monad.models.exceptions import ModelFileMissingError, ModelNotFoundError
from monad.models.metadata import ModelMetadata, ModelStatus
from monad.models.registry import ModelRegistry

log = get_logger(__name__)


class ModelManager:
    """Loads model registry from YAML and manages lifecycle metadata."""

    _instance: "ModelManager | None" = None

    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.registry = ModelRegistry()
        self.models_dir: Path = Path("models")
        self._initialized = True

    def load_registry(self, models_yaml: str | Path, models_dir: Path | None = None) -> None:
        path = Path(models_yaml)
        if not path.exists():
            log.warning("models.yaml not found at {} — registry will be empty", path)
            return
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        entries: Iterable[dict] = data.get("models", [])
        for e in entries:
            meta = ModelMetadata(
                id=e["id"],
                role=e.get("role", "general"),
                format=e.get("format", "gguf"),
                filename=e.get("filename", ""),
                url=e.get("url", ""),
                size_gb=float(e.get("size_gb", 0)),
                sha256=e.get("sha256", ""),
                context=int(e.get("context", 4096)),
                gpu_layers=int(e.get("gpu_layers", -1)),
                description=e.get("description", ""),
            )
            self.registry.register(meta)

        if models_dir:
            self.models_dir = Path(models_dir)

        self._refresh_download_status()
        log.info("Loaded {} model(s) from registry", len(self.registry))

    def _refresh_download_status(self) -> None:
        for meta in self.registry.all():
            local = self.models_dir / meta.id / meta.filename
            if local.exists():
                meta.status = ModelStatus.DOWNLOADED
                meta.local_path = str(local)

    def list_models(self) -> list[ModelMetadata]:
        return self.registry.all()

    def get(self, model_id: str) -> ModelMetadata:
        meta = self.registry.get(model_id)
        if meta is None:
            raise ModelNotFoundError(model_id)
        return meta

    def validate(self, model_id: str) -> bool:
        meta = self.get(model_id)
        local = self.models_dir / meta.id / meta.filename
        if not local.exists():
            raise ModelFileMissingError(f"{model_id}: missing {local}")
        return True
