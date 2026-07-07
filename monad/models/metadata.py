"""Model metadata + status enum."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ModelStatus(str, Enum):
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    DOWNLOADED = "downloaded"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class ModelMetadata:
    id: str
    role: str
    format: str
    filename: str
    url: str = ""
    size_gb: float = 0.0
    sha256: str = ""
    context: int = 4096
    gpu_layers: int = -1
    description: str = ""
    status: ModelStatus = ModelStatus.REGISTERED
    local_path: str = ""
    extra: dict = field(default_factory=dict)
