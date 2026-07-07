"""Tests for Build #016 — PromptManager."""

from monad.prompts import PromptContext, PromptManager


def test_render_chat_template():
    pm = PromptManager()
    ctx = PromptContext(system="You are helpful.", variables={"user": "Hi"})
    out = pm.render("chat", ctx)
    assert "Hi" in out
    assert "You are helpful." in out


def test_missing_variable_is_empty():
    pm = PromptManager()
    ctx = PromptContext(variables={})
    out = pm.render("coding", ctx)
    assert "expert software engineer" in out.lower()


def test_list_templates():
    pm = PromptManager()
    templates = pm.list_templates()
    assert "chat" in templates
    assert "coding" in templates
    assert "creative" in templates
