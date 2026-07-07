"""Intent enum."""

from enum import Enum


class Intent(str, Enum):
    GENERAL_CHAT = "general_chat"
    CODING = "coding"
    CREATIVE = "creative"
    QUESTION = "question"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    UNKNOWN = "unknown"
