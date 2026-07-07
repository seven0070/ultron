"""
STUB FastAPI server. Full implementation lands in Build #056+.

Once fastapi is installed, this module will expose:
  GET  /health
  POST /chat
  GET  /models
  POST /models/{id}/load
  ...
"""

from __future__ import annotations


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError as e:
        raise RuntimeError("fastapi not installed — pip install 'monad-ultron[api]'") from e

    app = FastAPI(title="Monad-Ultron API", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
