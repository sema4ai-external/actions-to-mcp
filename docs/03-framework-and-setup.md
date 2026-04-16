# Framework and setup

Recommendations, not mandates. Pick what fits — but know why these are the
defaults across Sema4.ai's own MCP work.

## Framework: fastmcp

We recommend **[fastmcp](https://github.com/jlowin/fastmcp)** (≥ 2.3).

Why:

- Minimal surface — `FastMCP("name")` + `@mcp.tool()` covers most of what an
  action pack does.
- Built-in HTTP request access (`fastmcp.server.dependencies.get_http_request`) —
  you need this to read the Sema4.ai context header and forwarded auth.
- Built-in `JWTVerifier` for OAuth resource-server patterns.
- Used by both Sema4.ai's hosted MCP gallery and our internal servers, so
  the patterns in this guide map 1:1 to production code.

Other frameworks — the official `mcp` SDK, or low-level Starlette with a
hand-rolled MCP layer — work too, but require more glue. Start with fastmcp.
Drop to the lower level only if you hit a real constraint.

## Python and packaging

- **Python 3.12+** — matches fastmcp and `sema4ai-api-client` baselines.
- **uv** for environment and dependency management. `uv sync` to install,
  `uv add <pkg>` to add, commit `uv.lock`.
- **One MCP = one project** — flat `server.py` entry point, one
  `pyproject.toml`, one `uv.lock`.
- **Project name**: `mcp-{service}` (e.g. `mcp-microsoft-sharepoint`) — avoids
  collisions with vendor SDK packages on PyPI.

Minimum `pyproject.toml`:

```toml
[project]
name = "mcp-my-service"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.3",
    "pydantic>=2",
]
```

## Layout

Keep it flat. Per-MCP:

```
my-mcp/
├── server.py          entry point — binds port, runs mcp.run()
├── pyproject.toml
├── uv.lock
├── models.py          optional — Pydantic models for complex tools
├── client.py          optional — vendor API client
└── tests/
    ├── conftest.py
    ├── test_smoke.py  imports server, lists tools, asserts names
    └── test_tools.py  exercises each tool with mocked deps
```

Avoid a `src/` layout or `create_app()` / `run_http()` wrappers unless you
need them. Extra indirection makes migrations harder to review.

## Minimum `server.py`

```python
import fastmcp

mcp = fastmcp.FastMCP("my-service")


@mcp.tool()
def ping() -> str:
    """Return pong."""
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8067)
```

The MCP endpoint path is `/mcp` by default. Port 8067 is a Sema4.ai
convention (matching `internal-mcps` and the hosted gallery); any port
works locally — only your deployment's ingress port matters to Sema4.ai.

## Coding agent: Claude Code

This guide assumes you're doing the migration from a coding agent, and the
skills and walkthroughs are built for **[Claude Code](https://docs.claude.com/en/docs/claude-code)**.
With Claude Code installed, you can run the `convert-action-pack` skill
on your action packs directly.

If you prefer Cursor, Windsurf, or another MCP-aware agent, the skill
content is plain markdown — import it as a rule, prompt, or custom
instruction. The walkthroughs assume Claude Code, but the generated MCP
code is agent-agnostic.

## MCP Inspector — the parity check loop

Install **MCP Inspector** for tool-by-tool verification:

```bash
npx @modelcontextprotocol/inspector
```

Point it at your running server (e.g. `http://localhost:8067/mcp`) to
invoke each tool directly, inspect descriptions, and check annotations.
This is the fastest way to spot-check that your MCP behaves like the
action it's replacing.

## Local dev loop

One terminal:

```bash
cd my-mcp
uv sync
uv run python server.py
# → http://localhost:8067/mcp
```

For fast local checks, point **MCP Inspector** at the URL (see above).
Re-run `python server.py` after each change — short migrations don't need
hot reload; add `uvicorn --reload` only if you're building something
substantial.

### Testing against Sema4.ai in the loop

Local tool invocation only gets you so far — context headers, auth
forwarding, and streamable-HTTP behavior all depend on the Sema4.ai
platform being in the call path. Expose your local server with **ngrok**
and register the tunnel URL as a remote MCP on your Sema4.ai agent:

```bash
ngrok http 8067
# → https://<subdomain>.ngrok.app
```

Register `https://<subdomain>.ngrok.app/mcp` on your Sema4.ai agent as an
MCP server. The agent now calls your local code through Sema4.ai's cloud
— exactly the same path as production, but you still get edit-and-restart
iteration speed. This is the fastest way to catch issues that only surface
when the Sema4.ai platform is in the loop.

## Registering with a Sema4.ai agent

Once your MCP is reachable — via ngrok for development or a deployed
URL for production — register it on your Sema4.ai agent. The agent
needs a public URL ending in `/mcp` and auth configuration matching
your server's pattern (forwarded bearer for OAuth, an API-key header,
or none). For OAuth, register the *union* of scopes every tool in the
MCP can need — per-tool scopes collapse to a single grant at the OAuth
client, see [scope consolidation](05-sema4-patterns.md#oauth-scope-consolidation).
Common gotchas: the `Authorization` header can be stripped by some
ingress controllers, streamable-HTTP needs session affinity on load
balancers, and `/mcp` vs `/mcp/` trailing-slash behavior varies. For
the exact click-path in Studio / Control Room, follow the Sema4.ai
product docs — that UI evolves.

## What's next

- [Migration workflow](04-migration-workflow.md) — step-by-step with the
  `convert-action-pack` skill.
- [Sema4.ai patterns](05-sema4-patterns.md) — context headers, auth,
  thread files.
