"""Shared fixtures for the SharePoint MCP tests."""
from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

import server


class _FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}


@pytest.fixture
def fake_graph_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[MagicMock]:
    """Swap the module-level Graph client with a MagicMock for the test body."""
    mock = MagicMock()
    monkeypatch.setattr(server, "client", mock)
    yield mock


@pytest.fixture
def with_bearer(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Patch `get_http_request` so the tools see a bearer-bearing request."""
    token = "test-bearer-token"
    fake = _FakeRequest(headers={"Authorization": f"Bearer {token}"})
    monkeypatch.setattr(server, "get_http_request", lambda: fake)
    yield token
