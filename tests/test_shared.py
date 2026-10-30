"""Tests for the modules every service shares: auth, settings, logging, and version.

The package and project names come from pyproject.toml.
That keeps this file identical in every service.
"""

import importlib
import json
import logging
import os
import sys
import tomllib
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

SECRET = "test-secret-0123456789"
os.environ["API_SECRET"] = SECRET

_PYPROJECT = tomllib.loads(
    (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
)
PACKAGE: str = _PYPROJECT["tool"]["dev-standards"]["template"]["package"]
PROJECT: str = _PYPROJECT["project"]["name"]

auth = importlib.import_module(f"{PACKAGE}.auth")
config = importlib.import_module(f"{PACKAGE}.config")
logging_config = importlib.import_module(f"{PACKAGE}.logging_config")
main = importlib.import_module(f"{PACKAGE}.main")
service = importlib.import_module(f"{PACKAGE}.service")

# A minimal app with one protected route tests the auth dependency without any service's routes.
_protected = FastAPI()


@_protected.get("/protected", dependencies=[Depends(auth.require_auth)])
async def _protected_route() -> dict[str, bool]:
    return {"ok": True}


protected_client = TestClient(_protected)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong"},
        {"Authorization": f"Bearer {SECRET}x"},
        {"Authorization": f"Basic {SECRET}"},
    ],
    ids=["missing", "wrong", "longer", "wrong-scheme"],
)
def test_auth_rejects_missing_or_wrong_tokens_with_401(headers: dict[str, str]) -> None:
    response = protected_client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_auth_accepts_the_secret() -> None:
    response = protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {SECRET}"}
    )
    assert response.status_code == 200


def test_health_reports_service_and_version() -> None:
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == PROJECT
    assert response.json()["version"] == main.VERSION


def test_version_comes_from_package_metadata() -> None:
    assert (
        main.VERSION
        == service.service_version(PROJECT)
        == _PYPROJECT["project"]["version"]
    )
    assert service.service_version("not-an-installed-project") == "0.0.0"


@pytest.mark.parametrize("secret", ["changeme", "your-secret-here", "short"])
def test_weak_secrets_are_refused(secret: str) -> None:
    with pytest.raises(ValidationError, match="API_SECRET"):
        config.Settings(api_secret=secret)


def test_rejected_secret_is_not_echoed_in_the_error() -> None:
    with pytest.raises(ValidationError) as error:
        config.Settings(api_secret="real-but-short")
    assert "real-but-short" not in str(error.value)


def test_secret_is_never_printed() -> None:
    settings = config.Settings(api_secret=SECRET)
    assert SECRET not in repr(settings)
    assert SECRET not in str(settings.model_dump())


def test_unknown_log_level_is_refused() -> None:
    with pytest.raises(ValidationError):
        config.Settings(api_secret=SECRET, log_level="LOUD")


def test_json_log_lines_stay_valid_with_quotes() -> None:
    record = logging.LogRecord(
        "svc", logging.INFO, __file__, 1, 'He said "hi"', None, None
    )
    line = json.loads(logging_config.JsonFormatter().format(record))
    assert (line["message"], line["level"], line["logger"]) == (
        'He said "hi"',
        "INFO",
        "svc",
    )


def test_request_urls_from_http_clients_are_not_logged() -> None:
    logging_config.configure_logging("DEBUG")
    try:
        for name in ("httpx", "httpcore"):
            assert not logging.getLogger(name).isEnabledFor(logging.INFO)
    finally:
        logging_config.configure_logging("INFO")


def access_record(path: str, status: int) -> logging.LogRecord:
    """Builds the record that uvicorn logs for a request."""
    return logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1:5000", "GET", path, "1.1", status),
        None,
    )


@pytest.mark.parametrize(
    ("path", "status", "logged"),
    [
        ("/health", 200, False),
        # A failing health check is worth seeing.
        ("/health", 503, True),
        ("/media/info", 200, True),
        ("/health?verbose=1", 200, True),
    ],
)
def test_successful_health_checks_stay_out_of_the_access_log(
    path: str, status: int, logged: bool
) -> None:
    logging_config.configure_logging("INFO")
    access = logging.getLogger("uvicorn.access")

    # A logger's filter returns the record that passes, or False.
    assert bool(access.filter(access_record(path, status))) is logged


def test_json_log_lines_include_exceptions() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.getLogger("svc").makeRecord(
            "svc", logging.ERROR, __file__, 1, "Failed.", None, sys.exc_info()
        )
    line = json.loads(logging_config.JsonFormatter().format(record))
    assert "ValueError: boom" in line["exception"]
