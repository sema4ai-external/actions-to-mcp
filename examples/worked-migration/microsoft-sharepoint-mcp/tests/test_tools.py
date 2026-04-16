"""Representative tool tests — one per category (read, mutation, missing-auth, thread-file)."""
from __future__ import annotations

import pytest

import server


def test_search_for_site_resolves_bearer_and_calls_client(
    fake_graph_client, with_bearer
) -> None:
    fake_graph_client.search_for_site.return_value = {
        "value": [{"id": "site-1", "name": "Contoso"}]
    }
    result = server.search_for_site("Contoso")
    fake_graph_client.search_for_site.assert_called_once_with(with_bearer, "Contoso")
    assert result.value == [{"id": "site-1", "name": "Contoso"}]


def test_create_sharepoint_list_is_mutating(fake_graph_client, with_bearer) -> None:
    fake_graph_client.create_list.return_value = {
        "id": "list-1",
        "displayName": "Projects",
    }
    result = server.create_sharepoint_list(
        site=server.SiteIdentifier(site_id="site-1"),
        sharepoint_list=server.SharepointList(display_name="Projects"),
    )
    assert result.list["id"] == "list-1"


def test_missing_bearer_raises(monkeypatch, fake_graph_client) -> None:
    class _NoAuthRequest:
        headers: dict[str, str] = {}

    monkeypatch.setattr(server, "get_http_request", lambda: _NoAuthRequest())
    with pytest.raises(ValueError, match="Missing OAuth token"):
        server.search_for_site("Contoso")


def test_download_sharepoint_file_attaches_when_requested(
    fake_graph_client, with_bearer, monkeypatch
) -> None:
    fake_graph_client.download_file.return_value = (b"hello", "report.pdf")
    attached: list[dict] = []

    def fake_attach(*, name: str, data: bytes, content_type: str) -> list:
        attached.append({"name": name, "data": data, "content_type": content_type})
        return []

    monkeypatch.setattr(server, "attach_file_content", fake_attach)

    class _NoopCtx:
        def __enter__(self) -> "_NoopCtx":
            return self

        def __exit__(self, *args: object) -> bool:
            return False

    monkeypatch.setattr(server, "_bind_request_context", lambda: _NoopCtx())

    result = server.download_sharepoint_file(
        filelist=server.FileList(
            files=[server.File(file_id="f1", name="report.pdf")]
        ),
        attach=True,
    )
    assert result.files == ["report.pdf"]
    assert attached and attached[0]["name"] == "report.pdf"
