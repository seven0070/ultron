"""Tests for Build #009 — ServiceContainer."""

import pytest

from monad.core.container import (
    CircularDependencyError,
    ServiceContainer,
    ServiceNotRegisteredError,
)


class Foo:
    pass


def test_singleton_instance():
    c = ServiceContainer()
    foo = Foo()
    c.register_singleton("foo", foo)
    assert c.resolve("foo") is foo
    assert c.resolve("foo") is foo


def test_singleton_lazy_class():
    c = ServiceContainer()
    c.register_singleton("foo", Foo)
    a = c.resolve("foo")
    b = c.resolve("foo")
    assert a is b
    assert isinstance(a, Foo)


def test_transient():
    c = ServiceContainer()
    c.register_transient("foo", Foo)
    assert c.resolve("foo") is not c.resolve("foo")


def test_factory():
    c = ServiceContainer()
    c.register_factory("bar", lambda _: {"count": 42})
    assert c.resolve("bar") == {"count": 42}


def test_not_registered():
    c = ServiceContainer()
    with pytest.raises(ServiceNotRegisteredError):
        c.resolve("missing")


def test_circular():
    c = ServiceContainer()
    c.register_factory("a", lambda cc: cc.resolve("b"))
    c.register_factory("b", lambda cc: cc.resolve("a"))
    with pytest.raises(CircularDependencyError):
        c.resolve("a")
