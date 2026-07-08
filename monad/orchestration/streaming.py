"""
Build #018 — Streaming output.

Turns any orchestration result into an iterator of text chunks so the UI can
display tokens as they arrive (like ChatGPT/Gemini).

Two modes:
  - real_stream(model_id, prompt, ...)   uses the provider's stream() if available
  - fake_stream(text, chunk_size=6)       chunks a completed string for a
                                          typewriter effect (used when a strategy
                                          can only produce a full response)

The FastAPI /ask and /fuse endpoints can wrap either mode in a
Server-Sent-Events response for the webapp.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Iterator


@dataclass
class StreamChunk:
    text: str                          # incremental delta (not cumulative)
    index: int                         # 0-based chunk index
    done: bool = False
    metadata: dict = None              # populated only on the FINAL chunk


class StreamingResponse:
    """
    Iterable of StreamChunk objects. Also exposes a `.text` property that
    returns the full accumulated text after consumption.
    """
    def __init__(self, source: Iterator[StreamChunk]) -> None:
        self._source = source
        self._buffer: list[str] = []
        self._done = False

    def __iter__(self) -> Iterator[StreamChunk]:
        for chunk in self._source:
            self._buffer.append(chunk.text)
            if chunk.done:
                self._done = True
            yield chunk

    @property
    def text(self) -> str:
        return "".join(self._buffer)

    @property
    def done(self) -> bool:
        return self._done

    def to_sse(self) -> Iterator[str]:
        """Server-Sent Events format for FastAPI streaming responses."""
        import json
        for chunk in self:
            payload = {"text": chunk.text, "index": chunk.index, "done": chunk.done}
            if chunk.metadata:
                payload["metadata"] = chunk.metadata
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def real_stream(
    provider,
    model_id: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.9,
    metadata_final: dict | None = None,
) -> StreamingResponse:
    """
    Use provider.stream() if available; otherwise fall back to a single-chunk
    response (which still fits the SSE format).
    """
    def _gen() -> Iterator[StreamChunk]:
        i = 0
        try:
            for piece in provider.stream(
                model_id, prompt, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p,
            ):
                if not piece:
                    continue
                yield StreamChunk(text=piece, index=i)
                i += 1
        except Exception as e:
            yield StreamChunk(text=f"[stream error: {e}]", index=i)
            i += 1
        yield StreamChunk(text="", index=i, done=True, metadata=metadata_final)
    return StreamingResponse(_gen())


def fake_stream(
    text: str,
    chunk_size: int = 6,
    delay_s: float = 0.02,
    metadata_final: dict | None = None,
) -> StreamingResponse:
    """
    Chunk a completed string for a typewriter effect.
    Used when a strategy (chain, ensemble, MoA) only produces a full text.
    """
    def _gen() -> Iterator[StreamChunk]:
        i = 0
        for offset in range(0, len(text), chunk_size):
            piece = text[offset:offset + chunk_size]
            yield StreamChunk(text=piece, index=i)
            i += 1
            if delay_s > 0:
                time.sleep(delay_s)
        yield StreamChunk(text="", index=i, done=True, metadata=metadata_final)
    return StreamingResponse(_gen())


def wrap_callable_as_stream(
    fn: Callable[[], Any],
    chunk_size: int = 8,
    delay_s: float = 0.015,
) -> StreamingResponse:
    """Run a blocking generator and stream its final text out chunk-by-chunk."""
    result = fn()
    text = result if isinstance(result, str) else str(result)
    return fake_stream(text, chunk_size=chunk_size, delay_s=delay_s,
                       metadata_final={"source": "wrap_callable"})
