"""
Build #009 — Dependency Injection container.

Simple, dependency-free service container supporting:
  - singleton registration (one instance, shared)
  - transient registration (new instance every resolve)
  - factory registration (custom construction)
  - circular-dependency detection during resolution
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, TypeVar

from monad.core.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")


class Lifetime(str, Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    FACTORY = "factory"


class ServiceContainerError(Exception):
    """Base error for DI container."""


class ServiceNotRegisteredError(ServiceContainerError):
    pass


class CircularDependencyError(ServiceContainerError):
    pass


class ServiceContainer:
    """Minimal service container.

    Register services by string key (recommended: dotted module path) and
    resolve them lazily. Detects circular dependencies during resolution.
    """

    def __init__(self) -> None:
        self._registrations: dict[str, tuple[Lifetime, Any]] = {}
        self._singletons: dict[str, Any] = {}
        self._resolution_stack: list[str] = []

    # -- registration ---------------------------------------------------------

    def register_singleton(self, key: str, instance_or_cls: Any) -> None:
        """Register a singleton. Pass an instance OR a class (constructed lazily)."""
        self._registrations[key] = (Lifetime.SINGLETON, instance_or_cls)
        # If a pre-built instance was given, cache it immediately
        if not isinstance(instance_or_cls, type):
            self._singletons[key] = instance_or_cls
        log.debug("Registered singleton: {}", key)

    def register_transient(self, key: str, cls: type) -> None:
        """Register a transient service (constructed anew every resolve)."""
        self._registrations[key] = (Lifetime.TRANSIENT, cls)
        log.debug("Registered transient: {}", key)

    def register_factory(self, key: str, factory: Callable[["ServiceContainer"], Any]) -> None:
        """Register a factory function that receives the container."""
        self._registrations[key] = (Lifetime.FACTORY, factory)
        log.debug("Registered factory: {}", key)

    # -- resolution -----------------------------------------------------------

    def resolve(self, key: str) -> Any:
        """Resolve a registered service."""
        if key not in self._registrations:
            raise ServiceNotRegisteredError(f"Service not registered: {key!r}")

        if key in self._resolution_stack:
            chain = " -> ".join(self._resolution_stack + [key])
            raise CircularDependencyError(f"Circular dependency: {chain}")

        lifetime, target = self._registrations[key]

        if lifetime == Lifetime.SINGLETON:
            if key in self._singletons:
                return self._singletons[key]
            self._resolution_stack.append(key)
            try:
                instance = target() if isinstance(target, type) else target
            finally:
                self._resolution_stack.pop()
            self._singletons[key] = instance
            return instance

        if lifetime == Lifetime.TRANSIENT:
            self._resolution_stack.append(key)
            try:
                return target()
            finally:
                self._resolution_stack.pop()

        if lifetime == Lifetime.FACTORY:
            self._resolution_stack.append(key)
            try:
                return target(self)
            finally:
                self._resolution_stack.pop()

        raise ServiceContainerError(f"Unknown lifetime: {lifetime}")

    # -- introspection --------------------------------------------------------

    def is_registered(self, key: str) -> bool:
        return key in self._registrations

    def list_services(self) -> list[tuple[str, str]]:
        """Return [(key, lifetime), ...] for all registered services."""
        return [(k, lt.value) for k, (lt, _) in self._registrations.items()]

    def clear(self) -> None:
        self._registrations.clear()
        self._singletons.clear()
        self._resolution_stack.clear()
