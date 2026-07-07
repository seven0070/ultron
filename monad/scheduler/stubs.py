"""STUB scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Job:
    id: str
    func: Callable
    interval_s: float = 60.0


class Scheduler:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def add(self, job: Job) -> None:
        self._jobs[job.id] = job

    def list(self) -> list[Job]:
        return list(self._jobs.values())

    def start(self) -> None:
        # STUB: real implementation will use asyncio / apscheduler
        pass

    def stop(self) -> None:
        pass
