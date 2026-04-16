"""Tests for agent_server_context — the thread-files overlay context parser."""
from __future__ import annotations

import base64
import json

import pytest

from agent_server_context import (
    bind_request_headers,
    current_client_agent_and_thread_id,
    current_invocation_data,
    reset_request_headers,
)


def _encoded_context(**fields: str) -> str:
    return base64.b64encode(json.dumps(fields).encode("utf-8")).decode("ascii")


def test_current_invocation_data_returns_dict_from_valid_header() -> None:
    headers = {
        "X-Tool-Invocation-Context": _encoded_context(
            agent_id="abc",
            thread_id="123",
            agent_server_api_url="https://agent-server.example.com",
            agent_server_api_token="tok",
        )
    }
    token = bind_request_headers(headers)
    try:
        data = current_invocation_data()
        assert data["agent_id"] == "abc"
        assert data["thread_id"] == "123"
    finally:
        reset_request_headers(token)


def test_current_invocation_data_empty_when_missing() -> None:
    token = bind_request_headers({})
    try:
        assert current_invocation_data() == {}
    finally:
        reset_request_headers(token)


def test_current_invocation_data_empty_on_malformed_base64() -> None:
    token = bind_request_headers({"X-Tool-Invocation-Context": "not-base64!@#"})
    try:
        assert current_invocation_data() == {}
    finally:
        reset_request_headers(token)


def test_missing_required_fields_raises() -> None:
    headers = {
        "X-Tool-Invocation-Context": _encoded_context(
            agent_id="abc",
            thread_id="123",
            # agent_server_api_url + token intentionally missing
        )
    }
    token = bind_request_headers(headers)
    try:
        with pytest.raises(RuntimeError, match="Missing required platform context"):
            current_client_agent_and_thread_id()
    finally:
        reset_request_headers(token)
