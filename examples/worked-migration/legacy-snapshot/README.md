# Legacy snapshot

Key excerpts from `gallery/actions/microsoft-sharepoint/` (v3.1.1), here
for reference while reading the [worked migration narrative](../README.md).
The full pack lives in the Sema4.ai `gallery` repository.

## `package.yaml`

```yaml
name: Microsoft Sharepoint
description: Work with Sharepoint sites, lists and files.
version: 3.1.1
spec-version: v2

dependencies:
  conda-forge:
    - python=3.11.11
    - python-dotenv=1.2.2
    - uv=0.6.11
  pypi:
    - sema4ai-actions=1.6.6
    - pydantic=2.12.5

external-endpoints:
  - name: "Microsoft Graph API"
    description: "Access Sharepoint data from Microsoft Graph API"
    rules:
      - host: "graph.microsoft.com"
        port: 443
```

## Example `@action` — `search_for_site`

From `microsoft_sharepoint/sharepoint_site_action.py`:

```python
@action
def search_for_site(
    search_string: str,
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["Sites.Read.All"]],
    ],
) -> Response[dict]:
    """Search for a Sharepoint site by name or by domain/hostname."""
    headers = build_headers(token)
    if re.match(r"^[a-zA-Z0-9.-]+\.sharepoint\.com$", search_string.strip()):
        hostname = search_string.strip()
        site = send_request("get", f"/sites/{hostname}:/", ..., headers=headers)
        return Response(result={"value": [site]})
    response_json = send_request(
        "get", f"/sites?search={search_string}", ..., headers=headers
    )
    return Response(result=response_json)
```

Three shifts the migration has to address:

1. `OAuth2Secret[...]` becomes a forwarded bearer resolved from the
   `Authorization` header.
2. `Response[T]` wrapper goes away — tools return a typed Pydantic model
   directly.
3. `sema4ai_http` / `send_request` helpers are replaced with `httpx`
   calls inside `sharepoint_client.py`.

## Example thread-file action — `download_sharepoint_file`

From `sharepoint_file_action.py` (abbreviated):

```python
@action(is_consequential=False)
def download_sharepoint_file(
    filelist: FileList,
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["Files.Read"]],
    ],
    site: SiteIdentifier = SiteIdentifier(site_id="", site_name=""),
    attach: bool = False,
) -> Response[list[str]]:
    """Download file(s) from Sharepoint; optionally attach to the thread."""
    headers = build_headers(token)
    for afile in filelist.files:
        ...
        download_r = sema4ai_http.get(download_file_url, headers=headers)
        if attach:
            chat.attach_file_content(name=item_file_name, data=download_r.data)
    ...
```

The `chat.attach_file_content()` call is what triggers the thread-files
overlay in the MCP — the migrated tool wraps its body in
`_bind_request_context()` so the helper can reach the Sema4.ai Agent
Server API.
