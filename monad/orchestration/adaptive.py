"""
Build #020 — Adaptive strategy selection.

Monad remembers which orchestration strategy worked best for which intent,
learns from real outcomes, and gradually shifts its AUTO choices to whatever
actually performs best on YOUR usage patterns.

Backend: SQLite table of (intent, strategy, outcome, latency, confidence).
Selection: Thompson-sampling-lite over per-intent success rates.
"""

from __future__ import annotations

import json
import random
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class StrategyStats:
    strategy: str
    intent: str
    trials: int = 0
    successes: int = 0
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    last_used: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.trials == 0:
            return 0.5  # neutral prior
        return self.successes / self.trials

    @property
    def sample_score(self) -> float:
        """Beta-distribution posterior sample (Thompson sampling)."""
        alpha = 1 + self.successes
        beta = 1 + max(0, self.trials - self.successes)
        return random.betavariate(alpha, beta)


class AdaptiveRouter:
    """Learns strategy → intent mapping from real usage."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS adaptive_stats (
        intent      TEXT NOT NULL,
        strategy    TEXT NOT NULL,
        trials      INTEGER NOT NULL DEFAULT 0,
        successes   INTEGER NOT NULL DEFAULT 0,
        latency_sum REAL NOT NULL DEFAULT 0,
        conf_sum    REAL NOT NULL DEFAULT 0,
        last_used   REAL NOT NULL DEFAULT 0,
        PRIMARY KEY (intent, strategy)
    );
    """

    KNOWN_STRATEGIES = (
        "domain_routing", "cascade", "mixture_of_agents",
        "verification", "ensemble",
    )

    def __init__(self, db_path: str | Path | None = None,
                 exploration: float = 0.15) -> None:
        """
        db_path: SQLite for persistence. None = in-memory only.
        exploration: probability of trying a random strategy (epsilon-greedy floor).
        """
        self.exploration = exploration
        self._conn = sqlite3.connect(str(db_path) if db_path else ":memory:",
                                      check_same_thread=False)
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    # -- selection ------------------------------------------------------------

    def select(self, intent: str, allowed: list[str] | None = None,
               default: str = "domain_routing") -> str:
        """Pick a strategy for this intent using Thompson sampling."""
        candidates = list(allowed or self.KNOWN_STRATEGIES)
        if not candidates:
            return default

        # Cold start / exploration
        if random.random() < self.exploration:
            choice = random.choice(candidates)
            log.debug("adaptive: explore → {}", choice)
            return choice

        # Sample one score per candidate from its beta posterior
        best, best_score = default, -1.0
        for s in candidates:
            stats = self._load(intent, s)
            score = stats.sample_score
            if score > best_score:
                best_score = score
                best = s
        log.debug("adaptive: exploit intent={} → {} (score={:.3f})",
                  intent, best, best_score)
        return best

    # -- feedback -------------------------------------------------------------

    def record(self, intent: str, strategy: str, success: bool,
               latency_ms: float, confidence: float = 0.5) -> None:
        """Record an outcome. success=True → increments the strategy's tally."""
        now = time.time()
        cur = self._conn.execute(
            "SELECT trials,successes,latency_sum,conf_sum FROM adaptive_stats "
            "WHERE intent=? AND strategy=?", (intent, strategy),
        )
        row = cur.fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO adaptive_stats "
                "(intent,strategy,trials,successes,latency_sum,conf_sum,last_used) "
                "VALUES (?,?,?,?,?,?,?)",
                (intent, strategy, 1, int(success), latency_ms, confidence, now),
            )
        else:
            trials, succ, lat_sum, conf_sum = row
            self._conn.execute(
                "UPDATE adaptive_stats SET trials=?,successes=?,latency_sum=?,"
                "conf_sum=?,last_used=? WHERE intent=? AND strategy=?",
                (trials + 1, succ + int(success),
                 lat_sum + latency_ms, conf_sum + confidence, now,
                 intent, strategy),
            )
        self._conn.commit()

    # -- introspection --------------------------------------------------------

    def _load(self, intent: str, strategy: str) -> StrategyStats:
        cur = self._conn.execute(
            "SELECT trials,successes,latency_sum,conf_sum,last_used "
            "FROM adaptive_stats WHERE intent=? AND strategy=?",
            (intent, strategy),
        )
        row = cur.fetchone()
        if row is None:
            return StrategyStats(strategy=strategy, intent=intent)
        trials, succ, lat_sum, conf_sum, last_used = row
        return StrategyStats(
            strategy=strategy, intent=intent, trials=trials, successes=succ,
            avg_latency_ms=(lat_sum / trials) if trials else 0.0,
            avg_confidence=(conf_sum / trials) if trials else 0.0,
            last_used=last_used,
        )

    def stats(self, intent: str | None = None) -> list[StrategyStats]:
        if intent is None:
            cur = self._conn.execute("SELECT DISTINCT intent FROM adaptive_stats")
            intents = [r[0] for r in cur.fetchall()]
        else:
            intents = [intent]
        out = []
        for i in intents:
            for s in self.KNOWN_STRATEGIES:
                out.append(self._load(i, s))
        return [s for s in out if s.trials > 0]

    def close(self) -> None:
        self._conn.close()
