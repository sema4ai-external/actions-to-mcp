"""Microsoft SharePoint MCP server.

Migrated from the Sema4.ai action pack at
`gallery/actions/microsoft-sharepoint/`. See `../README.md` for the
commit-by-commit narrative.

Auth: OAuth forwarded bearer. The Sema4.ai agent performs the OAuth dance
upstream and forwards `Authorization: Bearer …` with each tool call.

Two tools use the thread-files overlay to upload/download files through
the Sema4.ai Agent Server API — they wrap their bodies in
`_bind_request_context()`.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import fastmcp
from fastmcp.server.dependencies import get_http_request
from mcp.types import ToolAnnotations

from agent_server_context import bind_request_headers, reset_request_headers
from agent_server_helper import attach_file_content, get_file_content
from models import (
    CreateListOutput,
    DeleteItemOutput,
    DownloadFilesOutput,
    File,
    FileList,
    GetListItemsOutput,
    GetListsOutput,
    GetSiteOutput,
    ListItem,
    ListItemOutput,
    SearchFilesOutput,
    SearchSitesOutput,
    SharepointList,
    SharepointListItem,
    SiteIdentifier,
    UploadFileOutput,
)
from sharepoint_client import SharepointGraphClient

mcp = fastmcp.FastMCP("Microsoft SharePoint")
client = SharepointGraphClient()


# ---------------------------------------------------------------------------
# Auth and request-context helpers
# ---------------------------------------------------------------------------

def _require_bearer() -> str:
    """Resolve the forwarded OAuth bearer token from the Authorization header."""
    request = get_http_request()
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    raise ValueError(
        "Missing OAuth token — the Sema4.ai agent must forward Authorization: Bearer …"
    )


@contextmanager
def _bind_request_context() -> Iterator[None]:
    """Bind the current HTTP request's headers so thread-file helpers can read them."""
    request = get_http_request()
    if request is None:
        raise RuntimeError("No HTTP request context available")
    token = bind_request_headers(request.headers)
    try:
        yield
    finally:
        reset_request_headers(token)


READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
MUTATE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


# ---------------------------------------------------------------------------
# Site tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=READ)
def search_for_site(search_string: str) -> SearchSitesOutput:
    """Search for a SharePoint site by name or by hostname (e.g. 'contoso.sharepoint.com')."""
    token = _require_bearer()
    return SearchSitesOutput(**client.search_for_site(token, search_string))


@mcp.tool(annotations=READ)
def get_sharepoint_site(site: SiteIdentifier | None = None) -> GetSiteOutput:
    """Get a SharePoint site by ID, or the user's default site when `site` is omitted."""
    token = _require_bearer()
    return GetSiteOutput(site=client.get_site(token, site or SiteIdentifier()))


@mcp.tool(annotations=READ)
def get_all_sharepoint_sites() -> SearchSitesOutput:
    """List every SharePoint site the authenticated user can see."""
    token = _require_bearer()
    return SearchSitesOutput(**client.get_all_sites(token))


# ---------------------------------------------------------------------------
# List tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=READ)
def get_sharepoint_lists(site: SiteIdentifier | None = None) -> GetListsOutput:
    """Get all lists on a SharePoint site (defaults to the authenticated user's own site)."""
    token = _require_bearer()
    return GetListsOutput(**client.get_lists(token, site or SiteIdentifier()))


@mcp.tool(annotations=MUTATE)
def create_sharepoint_list(
    site: SiteIdentifier,
    sharepoint_list: SharepointList,
) -> CreateListOutput:
    """Create a new SharePoint list on the given site."""
    token = _require_bearer()
    return CreateListOutput(list=client.create_list(token, site, sharepoint_list))


@mcp.tool(annotations=MUTATE)
def add_sharepoint_list_item(
    site: SiteIdentifier,
    list_id: str,
    new_item: ListItem,
) -> ListItemOutput:
    """Add a new item to a SharePoint list."""
    token = _require_bearer()
    return ListItemOutput(item=client.add_list_item(token, site, list_id, new_item))


@mcp.tool(annotations=MUTATE)
def update_sharepoint_list_item(
    site: SiteIdentifier,
    list_id: str,
    update_item: SharepointListItem,
) -> ListItemOutput:
    """Update fields on a SharePoint list item."""
    token = _require_bearer()
    return ListItemOutput(
        item=client.update_list_item(token, site, list_id, update_item)
    )


@mcp.tool(annotations=MUTATE)
def delete_sharepoint_list_item(
    site: SiteIdentifier,
    list_id: str,
    item_id: str,
) -> DeleteItemOutput:
    """Delete a SharePoint list item by ID."""
    token = _require_bearer()
    deleted = client.delete_list_item(token, site, list_id, item_id)
    return DeleteItemOutput(deleted_item_id=deleted)


@mcp.tool(annotations=READ)
def get_sharepoint_list_items(
    site: SiteIdentifier,
    list_id: str,
    top: int = 100,
) -> GetListItemsOutput:
    """Return items in a SharePoint list. `top` caps the result count."""
    token = _require_bearer()
    return GetListItemsOutput(
        **client.get_list_items(token, site, list_id, top=top)
    )


# ---------------------------------------------------------------------------
# File tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=READ)
def search_sharepoint_files(
    search_text: str,
    site: SiteIdentifier | None = None,
) -> SearchFilesOutput:
    """Search for files on SharePoint by text match."""
    token = _require_bearer()
    return SearchFilesOutput(
        files=client.search_files(token, site or SiteIdentifier(), search_text)
    )


@mcp.tool(annotations=READ)
def download_sharepoint_file(
    filelist: FileList,
    site: SiteIdentifier | None = None,
    attach: bool = False,
) -> DownloadFilesOutput:
    """Download one or more files from SharePoint.

    When `attach` is true, each downloaded file is uploaded to the current
    Sema4.ai thread via the Agent Server API — this is what lets the agent
    use the file downstream.
    """
    token = _require_bearer()
    results: list[str] = []
    with _bind_request_context():
        for file in filelist.files:
            content, name = client.download_file(token, site, file)
            if attach:
                attach_file_content(
                    name=name,
                    data=content,
                    content_type="application/octet-stream",
                )
            results.append(name)
    return DownloadFilesOutput(files=results)


@mcp.tool(annotations=MUTATE)
def upload_file_to_sharepoint(
    filename: str,
    site: SiteIdentifier | None = None,
) -> UploadFileOutput:
    """Upload a thread-attached file to SharePoint as `filename`.

    The file must already be attached to the current thread — this tool
    pulls its bytes from the Sema4.ai Agent Server and writes them to the
    site's drive.
    """
    token = _require_bearer()
    with _bind_request_context():
        data = get_file_content(filename)
        uploaded = client.upload_file(token, site, filename, data)
    return UploadFileOutput(file=uploaded)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("MCP_HTTP_PORT", "8067"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
