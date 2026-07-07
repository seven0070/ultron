"""
QueryRouter — route a query to the right retrieval mode.

Modes (from user spec):
    graph_only     — pure knowledge-graph traversal (structured entities/relations)
    vector_only    — pure semantic similarity (concepts, feelings)
    hybrid         — RRF fusion of graph + vector
    temporal       — time-anchored retrieval (recent events, history)
    feeling_lucky  — best-guess single-shot for casual queries
"""

from __future__ import annotations

import re
from enum import Enum


class QueryMode(str, Enum):
    GRAPH_ONLY = "graph_only"
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
    TEMPORAL = "temporal"
    FEELING_LUCKY = "feeling_lucky"


_GRAPHY = re.compile(
    r"\b(who|what is|which|between|related to|linked|connection|"
    r"relationship|caused by|causes|is a|type of)\b",
    re.IGNORECASE,
)
_VECTORY = re.compile(
    r"\b(similar|like|feels|resembles|about|regarding|concerning|explain|"
    r"describe|meaning|imagine)\b",
    re.IGNORECASE,
)
_TEMPORAL = re.compile(
    r"\b(when|before|after|during|history|timeline|recent|latest|yesterday|"
    r"today|last (week|month|year)|20\d\d)\b",
    re.IGNORECASE,
)
_LUCKY = re.compile(r"^\s*(hey|yo|hi|hmm|quick|just)\b", re.IGNORECASE)


class QueryRouter:
    """Heuristic router — cheap, no model calls."""

    def route(self, query: str) -> QueryMode:
        q = query.strip()
        if not q:
            return QueryMode.FEELING_LUCKY
        if _LUCKY.search(q) and len(q) < 40:
            return QueryMode.FEELING_LUCKY
        if _TEMPORAL.search(q):
            return QueryMode.TEMPORAL
        graphy = bool(_GRAPHY.search(q))
        vectory = bool(_VECTORY.search(q))
        if graphy and not vectory:
            return QueryMode.GRAPH_ONLY
        if vectory and not graphy:
            return QueryMode.VECTOR_ONLY
        return QueryMode.HYBRID
