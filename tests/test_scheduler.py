"""Tests for Build #070 — real Scheduler."""

from __future__ import annotations

import time

from monad.scheduler import Job, JobStatus, Scheduler


def test_one_shot_job_runs():
    ran = []
    s = Scheduler()
    s.add(Job(id="j1", func=lambda: ran.append(1)))
    s.start()
    time.sleep(0.2)
    s.stop()
    assert ran == [1]
    assert s.get("j1").status == JobStatus.DONE
    assert s.get("j1").run_count == 1


def test_periodic_job_runs_multiple_times():
    ran = []
    s = Scheduler()
    s.add(Job(id="tick", func=lambda: ran.append(time.time()), interval_s=0.05))
    s.start()
    time.sleep(0.35)
    s.stop()
    assert len(ran) >= 3


def test_failed_job_records_error():
    def boom():
        raise ValueError("boom")
    s = Scheduler()
    s.add(Job(id="boom", func=boom))
    s.start()
    time.sleep(0.2)
    s.stop()
    j = s.get("boom")
    assert j.status == JobStatus.FAILED
    assert "boom" in j.last_error


def test_remove_cancels():
    s = Scheduler()
    s.add(Job(id="x", func=lambda: None, interval_s=1.0), delay_s=10.0)
    assert s.remove("x") is True
    assert s.get("x") is None


def test_start_stop_idempotent():
    s = Scheduler()
    s.start()
    s.start()   # no-op
    assert s.running
    s.stop()
    s.stop()    # no-op
    assert not s.running


def test_disabled_job_does_not_run():
    ran = []
    s = Scheduler()
    j = Job(id="disabled", func=lambda: ran.append(1), enabled=False)
    s.add(j)
    s.start()
    time.sleep(0.15)
    s.stop()
    assert ran == []


def test_args_and_kwargs():
    got = []
    s = Scheduler()
    s.add(Job(id="args", func=lambda a, b: got.append((a, b)),
              args=(1,), kwargs={"b": 2}))
    s.start()
    time.sleep(0.15)
    s.stop()
    assert got == [(1, 2)]
