"""Tests for this service's own routes.

The shared auth, settings, logging, and version behavior is covered by test_shared.py.
"""

import os

from fastapi.testclient import TestClient

SECRET = "test-secret-0123456789"
os.environ["API_SECRET"] = SECRET

from api_template.main import app  # noqa: E402

client = TestClient(app)
AUTH = {"Authorization": f"Bearer {SECRET}"}


def test_echo_requires_a_token() -> None:
    response = client.post("/template/echo", json={"text": "hello"})
    assert response.status_code == 401


def test_echo_with_valid_token() -> None:
    response = client.post("/template/echo", json={"text": "hello"}, headers=AUTH)
    assert response.status_code == 200
    assert response.json() == {"text": "hello"}


def test_echo_missing_body() -> None:
    response = client.post("/template/echo", headers=AUTH)
    assert response.status_code == 422
