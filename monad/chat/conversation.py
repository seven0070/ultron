"""Conversation session — holds message history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationSession:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    max_history: int = 20

    def add(self, role: Role, content: str) -> None:
        self.messages.append(Message(role, content))
        if len(self.messages) > self.max_history:
            # Preserve system message if present
            head = [m for m in self.messages[:1] if m.role == "system"]
            self.messages = head + self.messages[-(self.max_history - len(head)):]

    def clear(self, keep_system: bool = True) -> None:
        if keep_system:
            self.messages = [m for m in self.messages if m.role == "system"]
        else:
            self.messages.clear()

    def to_prompt(self) -> str:
        parts = []
        for m in self.messages:
            if m.role == "system":
                parts.append(f"[SYSTEM]\n{m.content}\n")
            elif m.role == "user":
                parts.append(f"[USER]\n{m.content}\n")
            else:
                parts.append(f"[ASSISTANT]\n{m.content}\n")
        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)
