"""Pydantic input/output models for the Microsoft SharePoint MCP.

Mirrors the shapes from the legacy Sema4.ai action pack's
`microsoft_sharepoint/models.py`. Preserving the field names lets the
Sema4.ai agent reuse its existing knowledge of the schemas.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SiteIdentifier(BaseModel):
    """Reference to a SharePoint site.

    Provide at least one of `site_id` or `site_name`. If `site_name` is one
    of "me", "my site", or "mysite", the Graph `/me/` endpoint is used
    instead of a specific site.
    """

    site_id: str = Field(default="", description="Full SharePoint site ID.")
    site_name: str = Field(default="", description="Site display name or special alias.")


class SharepointList(BaseModel):
    display_name: str = Field(description="Display name of the list.")
    description: str = Field(default="", description="Optional list description.")
    template: str = Field(default="genericList", description="Graph list template.")


class ListItem(BaseModel):
    fields: dict[str, Any] = Field(description="Field values keyed by column name.")


class SharepointListItem(BaseModel):
    item_id: str = Field(description="ID of the list item to operate on.")
    fields: dict[str, Any] = Field(
        default_factory=dict, description="Updated field values."
    )


class File(BaseModel):
    file_id: str = Field(default="", description="Graph item ID for the file.")
    name: str = Field(default="", description="Display name.")
    file: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw file payload returned by Graph (kept for compatibility with legacy callers).",
    )


class FileList(BaseModel):
    files: list[File] = Field(description="One or more files to operate on.")


# --- Tool output models ---


class SearchSitesOutput(BaseModel):
    value: list[dict[str, Any]]


class GetSiteOutput(BaseModel):
    site: dict[str, Any]


class GetListsOutput(BaseModel):
    value: list[dict[str, Any]]


class CreateListOutput(BaseModel):
    list: dict[str, Any]


class ListItemOutput(BaseModel):
    item: dict[str, Any]


class DeleteItemOutput(BaseModel):
    deleted_item_id: str


class GetListItemsOutput(BaseModel):
    value: list[dict[str, Any]]


class SearchFilesOutput(BaseModel):
    files: list[dict[str, Any]]


class DownloadFilesOutput(BaseModel):
    files: list[str] = Field(description="Names of the files that were downloaded.")


class UploadFileOutput(BaseModel):
    file: dict[str, Any]
