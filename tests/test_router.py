"""Tests for Build #014 — Router + IntentClassifier."""

from monad.router import IntentClassifier, Router, SingleModelStrategy
from monad.router.intent import Intent
from monad.router.request import Request


def test_coding_intent():
    c = IntentClassifier()
    assert c.classify("Write a python function to reverse a string") == Intent.CODING


def test_creative_intent():
    c = IntentClassifier()
    assert c.classify("Write a short story about a dragon") == Intent.CREATIVE


def test_question_intent():
    c = IntentClassifier()
    assert c.classify("What is the capital of France?") == Intent.QUESTION


def test_router_returns_response():
    r = Router(IntentClassifier(), SingleModelStrategy("longcat2"))
    resp = r.route(Request(text="Hello there"))
    assert resp.model_id == "longcat2"
    assert isinstance(resp.intent, Intent)
