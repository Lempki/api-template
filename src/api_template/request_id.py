"""Request IDs, which tie a client's log lines to this service's lines about the same request.

A client sends an ID in the X-Request-ID header, and the service makes one up when it gets none.
Every log line written while the request runs carries the ID, and the response sends it back.
"""

import re
import uuid
from contextvars import ContextVar

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

__all__ = ["HEADER", "RequestIdMiddleware", "current_request_id"]

HEADER = "X-Request-ID"

# A client's ID ends up in every log line, so only short IDs of plain characters are kept.
# Anything else is replaced by a new ID, which keeps the log free of what a client typed.
_VALID_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    """Returns the ID of the request that runs now, or None outside a request."""
    return _request_id.get()


class RequestIdMiddleware:
    """Gives each HTTP request an ID for its log lines and returns it in the response.

    It is plain ASGI middleware rather than Starlette's BaseHTTPMiddleware.
    uvicorn writes its access line inside the send call, which then still sees the ID.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Runs the request with its ID set, and adds the ID to the response's headers."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        given = Headers(scope=scope).get(HEADER)
        request_id = (
            given if given and _VALID_ID.fullmatch(given) else uuid.uuid4().hex[:12]
        )

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).append(HEADER, request_id)
            await send(message)

        token = _request_id.set(request_id)
        try:
            await self.app(scope, receive, send_with_id)
        finally:
            _request_id.reset(token)
