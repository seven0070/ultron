"""
llama.cpp provider. This is the ONLY place in Monad that imports llama_cpp.
Guarded imports so the rest of Monad works even without llama-cpp-python installed.
"""

from __future__ import annotations

from typing import Any

from monad.core.logger import get_logger
from monad.inference.interfaces import InferenceProvider
from monad.models.metadata import ModelMetadata

log = get_logger(__name__)


class LlamaCppProvider(InferenceProvider):
    name = "llama_cpp"

    def __init__(self) -> None:
        self._loaded: dict[str, Any] = {}
        self._llama_cls = None

    def _ensure_llama(self):
        if self._llama_cls is not None:
            return
        try:
            from llama_cpp import Llama  # type: ignore
            self._llama_cls = Llama
        except ImportError as e:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Install with: pip install llama-cpp-python"
            ) from e

    def load_model(self, meta: ModelMetadata) -> None:
        if meta.id in self._loaded:
            return
        self._ensure_llama()
        if not meta.local_path:
            raise FileNotFoundError(f"Model {meta.id} has no local_path — download it first")
        log.info("Loading {} via llama.cpp (ctx={}, gpu_layers={})",
                 meta.id, meta.context, meta.gpu_layers)
        self._loaded[meta.id] = self._llama_cls(
            model_path=meta.local_path,
            n_ctx=meta.context,
            n_gpu_layers=meta.gpu_layers,
            verbose=False,
        )

    def unload_model(self, meta: ModelMetadata) -> None:
        self._loaded.pop(meta.id, None)

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._loaded

    def generate(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> str:
        if model_id not in self._loaded:
            raise RuntimeError(f"Model not loaded: {model_id}")
        llm = self._loaded[model_id]
        out = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )
        return out["choices"][0]["text"]
