"""Routing strategies — decide which model handles a request."""

from __future__ import annotations

from abc import ABC, abstractmethod

from monad.router.intent import Intent


class RoutingStrategy(ABC):
    @abstractmethod
    def choose_model(self, intent: Intent) -> str: ...


class SingleModelStrategy(RoutingStrategy):
    """Always route to one configured model (used until multi-model orchestration lands)."""

    def __init__(self, default_model_id: str) -> None:
        self.default_model_id = default_model_id

    def choose_model(self, intent: Intent) -> str:
        return self.default_model_id


class RoleBasedStrategy(RoutingStrategy):
    """(Build #017+) Intent → role → model."""

    ROLE_MAP: dict[Intent, str] = {
        Intent.CODING: "coding",
        Intent.CREATIVE: "creative",
        Intent.ANALYSIS: "reasoning",
        Intent.SUMMARIZATION: "reasoning",
        Intent.QUESTION: "reasoning",
        Intent.GENERAL_CHAT: "reasoning",
        Intent.UNKNOWN: "reasoning",
    }

    def __init__(self, role_to_model: dict[str, str]) -> None:
        self.role_to_model = role_to_model

    def choose_model(self, intent: Intent) -> str:
        role = self.ROLE_MAP.get(intent, "reasoning")
        return self.role_to_model.get(role, next(iter(self.role_to_model.values())))
