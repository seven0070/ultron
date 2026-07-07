"""
Build #012 — Model loader.

Bridges ModelManager (metadata) → InferenceProvider (actual inference).
"""

from __future__ import annotations

from monad.core.logger import get_logger
from monad.inference import InferenceManager
from monad.models.manager import ModelManager
from monad.models.metadata import ModelStatus

log = get_logger(__name__)


class ModelLoader:
    def __init__(self, manager: ModelManager, inference: InferenceManager) -> None:
        self.manager = manager
        self.inference = inference

    def load(self, model_id: str) -> None:
        meta = self.manager.get(model_id)
        self.manager.validate(model_id)
        provider = self.inference.get_default_provider()
        provider.load_model(meta)
        meta.status = ModelStatus.LOADED
        log.success("Model loaded: {}", model_id)

    def unload(self, model_id: str) -> None:
        meta = self.manager.get(model_id)
        provider = self.inference.get_default_provider()
        provider.unload_model(meta)
        meta.status = ModelStatus.DOWNLOADED
        log.info("Model unloaded: {}", model_id)
