"""Smoke test — import the server, list tools, assert the expected registry."""
from __future__ import annotations

import server


EXPECTED_TOOLS = {
    "search_for_site",
    "get_sharepoint_site",
    "get_all_sharepoint_sites",
    "get_sharepoint_lists",
    "create_sharepoint_list",
    "add_sharepoint_list_item",
    "update_sharepoint_list_item",
    "delete_sharepoint_list_item",
    "get_sharepoint_list_items",
    "search_sharepoint_files",
    "download_sharepoint_file",
    "upload_file_to_sharepoint",
}


def _registered_tool_names() -> set[str]:
    # Internal API — fragile across fastmcp versions. If this breaks, check
    # the current fastmcp tool-registry accessor and adjust.
    return {tool.name for tool in server.mcp._tool_manager._tools.values()}


def test_all_expected_tools_registered() -> None:
    names = _registered_tool_names()
    missing = EXPECTED_TOOLS - names
    extra = names - EXPECTED_TOOLS
    assert not missing, f"Missing tools: {missing}"
    assert not extra, f"Unexpected tools: {extra}"


def test_tool_count() -> None:
    assert len(_registered_tool_names()) == 12
