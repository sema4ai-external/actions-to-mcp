"""Microsoft Graph client used by the SharePoint MCP tools.

Replaces the legacy `sema4ai_http` + `send_request` helpers. Every method
takes the bearer token explicitly so tool code can fail fast with a clear
error when the token is missing.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

from models import (
    File,
    ListItem,
    SharepointList,
    SharepointListItem,
    SiteIdentifier,
)

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
SPECIAL_SITE_ALIASES = {"me", "my site", "mysite"}


class SharepointGraphClient:
    """Thin synchronous Graph API client."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self._http = http_client or httpx.Client(base_url=GRAPH_ROOT, timeout=30.0)

    # --- Helpers ---

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _resolve_site_path(self, site: SiteIdentifier | None) -> str:
        """Return the Graph URL prefix for a site-scoped request."""
        if site is None or (not site.site_id and not site.site_name):
            return "/me"
        if site.site_name.lower() in SPECIAL_SITE_ALIASES:
            return "/me"
        if site.site_id:
            return f"/sites/{site.site_id}"
        raise ValueError(
            f"Cannot resolve site from name alone: {site.site_name!r}. "
            "Call search_for_site() first to get the site_id."
        )

    # --- Sites ---

    def search_for_site(self, token: str, search_string: str) -> dict[str, Any]:
        if re.match(r"^[a-zA-Z0-9.-]+\.sharepoint\.com$", search_string.strip()):
            resp = self._http.get(
                f"/sites/{search_string.strip()}:/", headers=self._headers(token)
            )
            if resp.status_code == 404:
                return {"value": []}
            resp.raise_for_status()
            return {"value": [resp.json()]}
        resp = self._http.get(
            "/sites", params={"search": search_string}, headers=self._headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def get_site(self, token: str, site: SiteIdentifier) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        resp = self._http.get(path, headers=self._headers(token))
        resp.raise_for_status()
        return resp.json()

    def get_all_sites(self, token: str) -> dict[str, Any]:
        resp = self._http.get(
            "/sites", params={"search": "*"}, headers=self._headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    # --- Lists ---

    def get_lists(self, token: str, site: SiteIdentifier) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        resp = self._http.get(f"{path}/lists", headers=self._headers(token))
        resp.raise_for_status()
        return resp.json()

    def create_list(
        self, token: str, site: SiteIdentifier, sharepoint_list: SharepointList
    ) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        payload = {
            "displayName": sharepoint_list.display_name,
            "description": sharepoint_list.description,
            "list": {"template": sharepoint_list.template},
        }
        resp = self._http.post(
            f"{path}/lists", json=payload, headers=self._headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def add_list_item(
        self,
        token: str,
        site: SiteIdentifier,
        list_id: str,
        item: ListItem,
    ) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        resp = self._http.post(
            f"{path}/lists/{list_id}/items",
            json={"fields": item.fields},
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return resp.json()

    def update_list_item(
        self,
        token: str,
        site: SiteIdentifier,
        list_id: str,
        item: SharepointListItem,
    ) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        resp = self._http.patch(
            f"{path}/lists/{list_id}/items/{item.item_id}/fields",
            json=item.fields,
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return resp.json()

    def delete_list_item(
        self,
        token: str,
        site: SiteIdentifier,
        list_id: str,
        item_id: str,
    ) -> str:
        path = self._resolve_site_path(site)
        resp = self._http.delete(
            f"{path}/lists/{list_id}/items/{item_id}",
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return item_id

    def get_list_items(
        self,
        token: str,
        site: SiteIdentifier,
        list_id: str,
        top: int = 100,
    ) -> dict[str, Any]:
        path = self._resolve_site_path(site)
        resp = self._http.get(
            f"{path}/lists/{list_id}/items",
            params={"$top": top, "$expand": "fields"},
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return resp.json()

    # --- Files ---

    def search_files(
        self, token: str, site: SiteIdentifier, search_text: str
    ) -> list[dict[str, Any]]:
        path = self._resolve_site_path(site)
        resp = self._http.get(
            f"{path}/drive/root/search(q='{search_text}')",
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return resp.json().get("value", [])

    def download_file(
        self, token: str, site: SiteIdentifier | None, file: File
    ) -> tuple[bytes, str]:
        file_id = file.file_id or file.file.get("id", "")
        name = file.name or file.file.get("name", file_id)
        if not file_id:
            raise ValueError("File must have file_id set to download by ID.")
        if site is not None and site.site_id:
            url = f"/sites/{site.site_id}/drive/items/{file_id}/content"
        else:
            url = f"/me/drive/items/{file_id}/content"
        resp = self._http.get(url, headers=self._headers(token))
        resp.raise_for_status()
        return resp.content, name

    def upload_file(
        self,
        token: str,
        site: SiteIdentifier | None,
        filename: str,
        data: bytes,
    ) -> dict[str, Any]:
        if site is not None and site.site_id:
            url = f"/sites/{site.site_id}/drive/root:/{filename}:/content"
        else:
            url = f"/me/drive/root:/{filename}:/content"
        headers = self._headers(token) | {"Content-Type": "application/octet-stream"}
        resp = self._http.put(url, content=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
