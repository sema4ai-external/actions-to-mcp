"""Thread-file upload / download helpers — wraps sema4ai-api-client.

Thread-files overlay helper. Copied verbatim from the
convert-action-pack skill — no SharePoint-specific logic in here.
"""
from __future__ import annotations

from agent_server_context import current_client_agent_and_thread_id


def attach_file_content(name: str, data: bytes, content_type: str) -> list[dict]:
    """Upload bytes as a thread file. Returns the Agent Server's file descriptor list."""
    client, agent_id, thread_id = current_client_agent_and_thread_id()
    response = client.threads.attach_file(
        agent_id=agent_id,
        thread_id=thread_id,
        file_name=name,
        file_bytes=data,
        content_type=content_type,
    )
    response.raise_for_status()
    return response.parsed or []


def get_file_content(file_ref: str) -> bytes:
    """Download a thread file by reference."""
    client, agent_id, thread_id = current_client_agent_and_thread_id()
    response = client.threads.download_file(
        agent_id=agent_id,
        thread_id=thread_id,
        file_reference=file_ref,
    )
    response.raise_for_status()
    return response.content
