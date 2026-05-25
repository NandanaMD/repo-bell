from __future__ import annotations

import logging
import threading
from typing import Any, Callable

try:
    from flask import Flask, Response, request
    from werkzeug.serving import make_server
except ModuleNotFoundError:
    Flask = None  # type: ignore[assignment]
    Response = Any  # type: ignore[assignment]
    request = None  # type: ignore[assignment]
    make_server = None  # type: ignore[assignment]

from app.github.event_factory import webhook_payload_to_events
from app.github.models import GitHubEvent
from app.webhook.signature import is_valid_signature

logger = logging.getLogger(__name__)

WebhookCallback = Callable[[GitHubEvent], None]


class WebhookServer:
    def __init__(self, port: int, secret: str, on_event: WebhookCallback) -> None:
        if Flask is None:
            raise RuntimeError(
                "Webhook mode requires Flask. Install dependencies with 'pip install -r requirements.txt' "
                "or switch mode to polling."
            )

        self._port = port
        self._secret = secret
        self._on_event = on_event
        self._server = None
        self._thread: threading.Thread | None = None
        self._app = Flask("RepoBellWebhook")
        self._register_routes()

    def _register_routes(self) -> None:
        @self._app.post("/webhook")
        def webhook() -> tuple[Response, int] | Response:
            delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
            event_name = request.headers.get("X-GitHub-Event", "")
            signature = request.headers.get("X-Hub-Signature-256", "")
            payload_raw = request.get_data(cache=False)

            if not is_valid_signature(self._secret, payload_raw, signature):
                logger.warning("Webhook signature validation failed for delivery %s", delivery_id)
                return Response("signature mismatch", status=401)

            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                return Response("invalid payload", status=400)

            events = webhook_payload_to_events(event_name, delivery_id, payload)
            for event in events:
                self._on_event(event)

            return Response("ok", status=200)

        @self._app.get("/health")
        def health() -> tuple[Response, int]:
            return Response("ok", status=200), 200

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        if make_server is None:
            raise RuntimeError("Werkzeug server is unavailable. Install Flask dependencies.")

        self._server = make_server("0.0.0.0", self._port, self._app)
        self._thread = threading.Thread(target=self._server.serve_forever, name="webhook-server", daemon=True)
        self._thread.start()
        logger.info("Webhook server started on port %s", self._port)

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("Webhook server stopped")
