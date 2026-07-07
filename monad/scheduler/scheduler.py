"""
Scheduler — thread-based background job runner.

Purpose:
  - Run periodic tasks (health checks, memory pruning, evolution checks)
  - Run one-shot delayed tasks
  - Report status + last error for each job

Stdlib-only: threading + heapq priority queue. No apscheduler dependency —
keeps Monad USB-portable.
"""

from __future__ import annotations

import heapq
import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from monad.core.logger import get_logger

log = get_logger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class _ScheduledRun:
    when: float
    seq: int
    job_id: str = field(compare=False)


@dataclass
class Job:
    id: str
    func: Callable
    interval_s: float | None = None      # None = one-shot
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    last_run_at: float = 0.0
    last_error: str = ""
    run_count: int = 0
    enabled: bool = True


class Scheduler:
    """Thread-based background scheduler. Safe to start/stop multiple times."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: list[_ScheduledRun] = []           # heap
        self._seq: int = 0
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False

    # -- job management -------------------------------------------------------

    def add(self, job: Job, delay_s: float = 0.0) -> None:
        """Register a job. If interval_s is set it will re-schedule itself."""
        with self._lock:
            self._jobs[job.id] = job
            self._schedule_run(job.id, when=time.time() + max(0.0, delay_s))
        self._wake.set()
        log.debug("Scheduler: added job {} (interval={}s)", job.id, job.interval_s)

    def remove(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.pop(job_id, None)
            if j:
                j.status = JobStatus.CANCELLED
        return j is not None

    def list(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    # -- lifecycle ------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="MonadScheduler",
                                        daemon=True)
        self._thread.start()
        log.info("Scheduler started (jobs={})", len(self._jobs))

    def stop(self, timeout: float = 5.0) -> None:
        if not self._running:
            return
        self._running = False
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None
        log.info("Scheduler stopped.")

    @property
    def running(self) -> bool:
        return self._running

    # -- run loop -------------------------------------------------------------

    def _loop(self) -> None:
        while self._running:
            next_run = self._pop_ready()
            if next_run is None:
                # Nothing due — wait until either wake() or next scheduled time
                wait = self._peek_wait()
                self._wake.wait(timeout=wait)
                self._wake.clear()
                continue
            self._execute(next_run.job_id)

    def _pop_ready(self) -> _ScheduledRun | None:
        now = time.time()
        with self._lock:
            if self._queue and self._queue[0].when <= now:
                return heapq.heappop(self._queue)
        return None

    def _peek_wait(self) -> float:
        with self._lock:
            if not self._queue:
                return 1.0                       # idle wake for stop() responsiveness
            return max(0.01, self._queue[0].when - time.time())

    def _schedule_run(self, job_id: str, when: float) -> None:
        self._seq += 1
        heapq.heappush(self._queue, _ScheduledRun(when=when, seq=self._seq, job_id=job_id))

    def _execute(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or not job.enabled:
                return
            job.status = JobStatus.RUNNING

        try:
            job.func(*job.args, **job.kwargs)
            job.status = JobStatus.DONE
            job.last_error = ""
        except Exception as e:  # noqa: BLE001
            job.status = JobStatus.FAILED
            job.last_error = f"{type(e).__name__}: {e}"
            log.warning("Scheduler job {} failed: {}\n{}", job_id, e,
                        traceback.format_exc(limit=3))
        finally:
            job.last_run_at = time.time()
            job.run_count += 1

        # Reschedule if periodic
        if job.interval_s and job.enabled and self._running:
            with self._lock:
                self._schedule_run(job_id, when=time.time() + job.interval_s)
            self._wake.set()
