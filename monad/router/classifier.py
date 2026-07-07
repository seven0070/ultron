"""Rules-based intent classifier."""

from __future__ import annotations

import re

from monad.router.intent import Intent

_CODING_KWS = re.compile(
    r"\b(code|function|class|debug|error|traceback|python|javascript|c\+\+|"
    r"typescript|golang|rust|regex|sql|api|refactor|implement|algorithm)\b",
    re.IGNORECASE,
)
_CREATIVE_KWS = re.compile(
    r"\b(story|poem|write|imagine|creative|brainstorm|idea|character|"
    r"lyric|song|scene)\b",
    re.IGNORECASE,
)
_ANALYSIS_KWS = re.compile(
    r"\b(analyz|compare|evaluate|assess|pros and cons|breakdown|critique)\b",
    re.IGNORECASE,
)
_SUMMARIZE_KWS = re.compile(
    r"\b(summari[sz]e|tl;?dr|shorten|abstract|key points)\b",
    re.IGNORECASE,
)
_QUESTION_KWS = re.compile(r"\b(what|why|how|when|where|who|which)\b\s.*\?", re.IGNORECASE)


class IntentClassifier:
    def classify(self, text: str) -> Intent:
        t = text.strip()
        if not t:
            return Intent.UNKNOWN
        if _CODING_KWS.search(t):
            return Intent.CODING
        if _CREATIVE_KWS.search(t):
            return Intent.CREATIVE
        if _SUMMARIZE_KWS.search(t):
            return Intent.SUMMARIZATION
        if _ANALYSIS_KWS.search(t):
            return Intent.ANALYSIS
        if _QUESTION_KWS.search(t) or t.endswith("?"):
            return Intent.QUESTION
        return Intent.GENERAL_CHAT
