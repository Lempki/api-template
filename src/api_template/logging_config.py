"""Structured JSON logging for every api-* service.

Each record becomes one JSON object per line, which log collectors can parse without guessing.
json.dumps escapes quotes and line breaks in a message, so every line stays valid JSON.
"""

import json
import logging
import logging.config
from typing import Any

from .request_id import current_request_id

__all__ = ["JsonFormatter", "QuietHealthChecks", "configure_logging"]


class JsonFormatter(logging.Formatter):
    """Renders a log record as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Returns the record as one JSON object, with the traceback when there is one."""
        payload: dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # A line written while a request runs names it, so it can be matched with the client's.
        if (request_id := current_request_id()) is not None:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class QuietHealthChecks(logging.Filter):
    """Drops uvicorn's access log lines of successful /health requests.

    Docker asks /health every few seconds, so these lines would bury every other line.
    A health check that fails still logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Returns False for a successful /health request, and True for every other record."""
        # uvicorn logs the client, method, path, HTTP version, and status as the record's args.
        args = record.args
        if not isinstance(args, tuple) or len(args) != 5:
            return True
        path, status = args[2], args[4]
        return not (path == "/health" and isinstance(status, int) and status < 400)


def configure_logging(level: str) -> None:
    """Routes every logger, including uvicorn's, through the JSON formatter.

    Args:
        level: The minimum level, such as "INFO".
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "filters": {"quiet_health": {"()": QuietHealthChecks}},
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "json"}
            },
            "root": {"level": level, "handlers": ["console"]},
            "loggers": {
                # Uvicorn installs its own handlers.
                # Clearing them sends its records to the root handler instead.
                **{
                    name: {"handlers": [], "propagate": True}
                    for name in ("uvicorn", "uvicorn.error")
                },
                "uvicorn.access": {
                    "handlers": [],
                    "propagate": True,
                    "filters": ["quiet_health"],
                },
                # httpx logs every request URL at INFO, and a URL can hold a secret.
                # A Discord webhook URL is one example, because its token is part of the path.
                **{name: {"level": "WARNING"} for name in ("httpx", "httpcore")},
            },
        }
    )
