"""
Build #013 — Chat engine.

Wraps prompts + inference + conversation history. Falls back to a stub reply
if no model is loaded (so the CLI is testable even without GGUFs).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from monad.chat.conversation import ConversationSession
from monad.core.logger import get_logger

if TYPE_CHECKING:
    from rich.console import Console

    from monad.core.application import MonadApplication

log = get_logger(__name__)


class ChatEngine:
    def __init__(self, app: "MonadApplication") -> None:
        self.app = app
        cfg = app.config.get("chat", {}) if app.config else {}
        self.max_history = int(cfg.get("max_history", 20))
        self.temperature = float(cfg.get("temperature", 0.7))
        self.top_p = float(cfg.get("top_p", 0.9))
        self.max_tokens = int(cfg.get("max_tokens", 2048))
        self.session = ConversationSession(
            session_id=str(uuid.uuid4())[:8],
            max_history=self.max_history,
        )
        self.session.add(
            "system",
            "You are Monad-Ultron, a portable local AI assistant. Be concise and helpful.",
        )
        self.current_model_id: str | None = (
            app.config.get("runtime.default_model") if app.config else None
        )

    # -- generation -----------------------------------------------------------

    def send(self, user_text: str) -> str:
        self.session.add("user", user_text)
        try:
            reply = self._generate()
        except Exception as e:
            log.error("Generation failed: {}", e)
            reply = f"[Model not available yet — stub reply]\nYou said: {user_text}"
        self.session.add("assistant", reply)
        return reply

    def _generate(self) -> str:
        """Try to generate via inference provider; raise if not possible."""
        try:
            from monad.inference import InferenceManager, LlamaCppProvider
            from monad.models import ModelManager
        except Exception as e:
            raise RuntimeError(f"Inference stack unavailable: {e}") from e

        mm = ModelManager()
        if len(mm.list_models()) == 0:
            from pathlib import Path
            mm.load_registry(Path.cwd() / "models.yaml", Path.cwd() / "models")

        if not self.current_model_id:
            raise RuntimeError("No default model configured")

        meta = mm.get(self.current_model_id)
        if not meta.local_path:
            raise RuntimeError(
                f"Model file for {self.current_model_id} not downloaded yet. "
                f"Run: python installer/download_models.py"
            )

        im = InferenceManager()
        if "llama_cpp" not in im.list():
            im.register(LlamaCppProvider(), default=True)
        provider = im.get_default_provider()
        if not provider.is_loaded(self.current_model_id):
            provider.load_model(meta)

        prompt = self.session.to_prompt()
        return provider.generate(
            self.current_model_id,
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
        )

    # -- CLI loop -------------------------------------------------------------

    def run_cli(self, console: "Console") -> None:
        while True:
            try:
                user = console.input("[bold cyan]you>[/bold cyan] ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]bye![/dim]")
                return

            if not user:
                continue
            if user in ("/exit", "/quit"):
                console.print("[dim]bye![/dim]")
                return
            if user == "/help":
                console.print("Commands: /help /clear /status /model <id> /exit")
                continue
            if user == "/clear":
                self.session.clear()
                console.print("[green]session cleared[/green]")
                continue
            if user == "/status":
                console.print({
                    "session": self.session.session_id,
                    "messages": len(self.session.messages),
                    "model": self.current_model_id,
                })
                continue
            if user.startswith("/model "):
                new_id = user.split(" ", 1)[1].strip()
                self.current_model_id = new_id
                console.print(f"[green]model set to {new_id}[/green]")
                continue

            reply = self.send(user)
            console.print(f"[bold magenta]monad>[/bold magenta] {reply}\n")
