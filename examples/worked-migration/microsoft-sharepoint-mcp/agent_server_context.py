"""Per-request Sema4.ai platform-context binding for tool handlers.

Thread-files overlay helper. Copied verbatim from the
convert-action-pack skill — no SharePoint-specific logic in here.
"""
from __future__ import annotations

import base64
import contextvars
import json
from typing import Any

from sema4ai_api_client import AuthenticatedClient

_headers_ctx: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "agent_server_headers", default=None
)


def bind_request_headers(headers) -> contextvars.Token:
    """Bind the incoming request headers for the duration of a tool call."""
    normalized = {k.lower(): v for k, v in headers.items()}
    return _headers_ctx.set(normalized)


def reset_request_headers(token: contextvars.Token) -> None:
    _headers_ctx.reset(token)


def _require_headers() -> dict[str, str]:
    headers = _headers_ctx.get()
    if headers is None:
        raise RuntimeError(
            "No request headers bound — call bind_request_headers() first."
        )
    return headers


def current_invocation_data() -> dict[str, Any]:
    """Decode X-Tool-Invocation-Context as a dict. Returns {} if missing/invalid."""
    raw = _require_headers().get("x-tool-invocation-context", "").strip()
    if not raw:
        return {}
    try:
        return json.loads(base64.b64decode(raw).decode("utf-8"))
    except Exception:
        return {}


def current_client_agent_and_thread_id() -> tuple[AuthenticatedClient, str, str]:
    """Build a Sema4.ai Agent Server API client from the current invocation context.

    Returns (client, agent_id, thread_id). Raises RuntimeError if any required
    field is missing.
    """
    ctx = current_invocation_data()
    api_url = ctx.get("agent_server_api_url")
    api_token = ctx.get("agent_server_api_token")
    agent_id = ctx.get("agent_id")
    thread_id = ctx.get("thread_id")

    missing = [
        name
        for name, value in (
            ("agent_server_api_url", api_url),
            ("agent_server_api_token", api_token),
            ("agent_id", agent_id),
            ("thread_id", thread_id),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required platform context fields: {', '.join(missing)}"
        )

    client = AuthenticatedClient(base_url=api_url, token=api_token)
    return client, agent_id, thread_id
