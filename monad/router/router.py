"""Main Router — classify → strategy → model."""

from __future__ import annotations

from monad.core.logger import get_logger
from monad.router.classifier import IntentClassifier
from monad.router.request import Request, Response
from monad.router.strategy import RoutingStrategy

log = get_logger(__name__)


class Router:
    def __init__(self, classifier: IntentClassifier, strategy: RoutingStrategy) -> None:
        self.classifier = classifier
        self.strategy = strategy

    def route(self, request: Request) -> Response:
        intent = self.classifier.classify(request.text)
        model_id = self.strategy.choose_model(intent)
        log.debug("Routed: intent={} -> model={}", intent.value, model_id)
        return Response(text="", intent=intent, model_id=model_id)
