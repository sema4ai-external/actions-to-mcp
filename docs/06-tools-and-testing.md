# Tools and testing

Two sides of the same coin: designing tools the Sema4.ai agent can
use correctly, and verifying they do what the legacy action did. Code
patterns for both live in the
[SharePoint worked example](../examples/worked-migration/) and the
[`convert-action-pack`](../.claude/skills/convert-action-pack/SKILL.md)
skill — this page is the reference.

## Tool design

In MCP, tool names and descriptions *are* the contract the Sema4.ai
agent reads to pick a tool. In actions they were mostly metadata.
Small wording changes move an agent from "I know what to do" to "I
don't understand this tool".

### Naming

- **Verb + object, snake_case**: `create_invoice`, not `process` or
  `invoice_create`.
- **Stable.** Renames invalidate every agent configuration. Keep old
  names as deprecated aliases for a release if you must rename.
- **Specific.** `send_slack_message` beats `send_message` — generic
  names collide with other MCPs on the same agent.
- **Match the vendor's vocabulary** unless it fights the rules above.

### Descriptions

Docstring first line = what the tool does. Second paragraph = when to
use it (especially if several tools are similar).

```python
@mcp.tool(annotations=READ)
def search_for_site(search_string: str) -> SearchSitesOutput:
    """Search for a SharePoint site by name or hostname.

    Use this when you have a human-readable name or a full hostname
    like "contoso.sharepoint.com" and need the site's ID for
    subsequent calls.
    """
```

Don't describe implementation; don't echo the parameter list; do
call out side effects.

### Annotations

`ToolAnnotations` drives agent behavior:

- `readOnlyHint=True` — agent may retry freely, cache, call
  speculatively.
- `destructiveHint=True` — agent may prompt the user before calling.

The two are independent. Legacy `is_consequential` is a starting
point, not a rule — verify against actual behavior.

### Parameters and returns

- **One Pydantic input model** for 3+ arguments; scalars otherwise.
- **`Field(description=…)` on every field** — those are the parameter
  docs the agent reads.
- **Match legacy field names.** Agents already know them; renaming
  costs re-learning.
- **Typed output models, not `dict`.** Stable shapes only. Drop
  `Response[T]` wrappers.

### Errors

`ValueError` for bad input, upstream HTTP errors for vendor failures,
`RuntimeError` for unexpected state. Don't reinvent `ActionError`.
Name the problem, not the internals. Don't leak credentials or
context.

### Pagination, granularity, consistency

- Cap with a `top: int = 100` parameter; return a cursor if the
  legacy action paginated; trim payloads to fields the agent actually
  needs.
- One round trip per tool. Split a tool that does two independent
  things; don't atomize to the point where common operations need
  five chained calls. Default to the legacy granularity.
- Keep parameter ordering, return-shape conventions, and error
  patterns uniform across the server. Agents learn server patterns
  fast when they're consistent.

## Testing

Three layers, all in `tests/`. The
[SharePoint suite](../examples/worked-migration/microsoft-sharepoint-mcp/tests/)
shows concrete examples.

| Layer | Catches | When |
| --- | --- | --- |
| Smoke | Registration, import errors, wiring. | First, before tool logic. |
| Tool | Auth resolution, response shapes, errors. | Per tool (or tool category). |
| Parity | Semantic equivalence vs the legacy action. | Once server compiles. |

### Smoke

Import the server, list tools, assert the expected set. One test,
catches most scaffolding bugs. See
[`test_smoke.py`](../examples/worked-migration/microsoft-sharepoint-mcp/tests/test_smoke.py).

### Tool

One test per category (read / mutation / thread-file), not per tool.
Mock the vendor client; verify auth resolution, parameter mapping,
response shape. Keep the bar low — thin wrappers don't need their
vendor client tested through them. See
[`test_tools.py`](../examples/worked-migration/microsoft-sharepoint-mcp/tests/test_tools.py).

### Context

Only when the server uses the thread-files overlay. Cover valid /
missing / malformed / partially-filled header cases. See
[`test_context.py`](../examples/worked-migration/microsoft-sharepoint-mcp/tests/test_context.py).

### Parity

Three approaches, in order of cost:

1. **Shape diff via MCP Inspector.** Call each tool; compare output
   field-by-field to the legacy action's return. Claude Code can
   drive this.
2. **Side-by-side runs.** Fire legacy and MCP against the same
   vendor with the same credentials and inputs; `diff` the outputs.
   Strongest signal short of full-loop.
3. **Full-loop via ngrok + a Sema4.ai agent.** Definitive. See
   [migration workflow](04-migration-workflow.md) step 5.

### Parity checklist

- [ ] Every legacy `@action` → MCP tool with same name (or
      documented rename).
- [ ] Every legacy `@query` → SDM Verified Query.
- [ ] Tool annotations match actual behavior.
- [ ] Pydantic input schemas preserve legacy field names.
- [ ] Return shapes match (minus `Response[T]`).
- [ ] Auth failures → clear `ValueError`, not 500s.
- [ ] Thread-file flows round-trip in the ngrok full-loop.
- [ ] Tool descriptions pick the right tool on plain-language prompts.
- [ ] Parity report in the PR explains intentional deltas.

### What not to test

- Sema4.ai Agent Server internals — use the ngrok full-loop; mocks
  drift.
- fastmcp internals.
- 100% coverage of vendor wrappers.
- Scope enforcement per tool (see
  [scope consolidation](05-sema4-patterns.md#oauth-scope-consolidation)).

## See also

- [Sema4.ai patterns](05-sema4-patterns.md) — auth, context, files.
- [Migration workflow](04-migration-workflow.md) — how test layers
  fit into the end-to-end loop.
