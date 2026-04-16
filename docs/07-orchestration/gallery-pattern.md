# Multi-MCP gateway

Hosting multiple migrated MCPs behind a single endpoint — one
container, one domain, path-based routing. Useful when you're
migrating several action packs and don't want a separate Cloud Run
service per MCP.

Sema4.ai uses this pattern internally to host its public MCP gallery;
it's documented here as a template you can adapt.

## Architecture

```
                     ┌───────────────────────────────────────┐
 https://gw/mcp/a  ─▶│ nginx reverse proxy, port 8080         │
 https://gw/mcp/b  ─▶│   /mcp/a → localhost:8001              │
 https://gw/mcp/c  ─▶│   /mcp/b → localhost:8002              │
                     │   /mcp/c → localhost:8003              │
                     │                                         │
                     │ MCP A (python server.py, port 8001)    │
                     │ MCP B (python server.py, port 8002)    │
                     │ MCP C (python server.py, port 8003)    │
                     └───────────────────────────────────────┘
```

One container. Each MCP gets its own venv and reserved internal port.
nginx routes on path prefix. A small entrypoint script launches every
MCP process and finally nginx.

## Key pieces

- **Per-MCP directory** — one subdir per MCP, each with its own
  `pyproject.toml`, `server.py`, and dependencies.
- **Reserved internal ports** — assign each MCP a unique port (e.g.
  8001, 8002, 8003 …). Document in one place so nothing collides.
- **Per-MCP metadata file** (`gallery.json` or similar) — name,
  description, OAuth config, path prefix. Useful for generating a
  combined manifest.
- **Shared Dockerfile** — multi-stage. Install uv, then loop over the
  per-MCP dirs running `uv sync` with isolated venvs, then copy the
  nginx config.
- **nginx config** — one `location` block per MCP, `proxy_pass` to
  `http://127.0.0.1:<port>/`.
- **Entrypoint script** — starts each Python process in the
  background, waits for readiness, launches nginx in the foreground.
- **Health endpoint** — a TCP-probe script that checks every internal
  port is serving.

## Per-MCP registration on the Sema4.ai agent

Each MCP is registered independently on the agent, with its own URL:

- `https://gateway.example.com/mcp/sharepoint/mcp`
- `https://gateway.example.com/mcp/slack/mcp`
- `https://gateway.example.com/mcp/linear/mcp`

The agent treats them as separate servers. The gateway pattern is
about hosting convenience, not about exposing one combined interface.

## Tips

- **Don't share Python processes** — even if two MCPs use fastmcp,
  keep them in separate venvs and separate processes. Easier to
  debug, easier to restart, no dependency conflicts.
- **Reserve port ranges by provider** (8001–8019 for Google,
  8020–8039 for Microsoft, etc.) so adding an MCP doesn't force port
  reshuffling.
- **Generate the nginx config + entrypoint dynamically** if you have
  many MCPs — a small Python script that reads per-MCP metadata and
  writes both beats hand-maintaining them in sync.

## Deploy

This container is just a container — deploy to any of the single-MCP
targets: [Cloud Run](cloud-run.md), [Bedrock AgentCore](bedrock-agentcore.md),
or [Azure Container Apps](azure-container-apps.md). Pick based on
your team's cloud preference.
