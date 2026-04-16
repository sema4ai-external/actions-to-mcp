# Cloud Run

Google Cloud Run is the simplest target — serverless containers with
built-in HTTPS, session affinity, and secret integration.

## Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY . .
RUN uv sync --frozen

ENV MCP_HTTP_PORT=8080
EXPOSE 8080

CMD ["uv", "run", "python", "server.py"]
```

Cloud Run expects the container to listen on the port given by the
`PORT` env var (8080 by default). Either hard-code `8080` as shown or
read `PORT` in `server.py`.

## Deploy

```bash
gcloud run deploy my-mcp \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --session-affinity \
  --set-secrets=MY_SERVICE_API_KEY=my-service-api-key:latest
```

Key flags:

- **`--session-affinity`** — required for streamable-HTTP MCP
  sessions. Without it, Cloud Run load-balances every request and
  your session breaks.
- **`--allow-unauthenticated`** — Cloud Run's native auth is
  orthogonal to your MCP's auth. Your MCP handles auth itself
  (forwarded bearer, API key, etc.); leave Cloud Run open.
- **`--set-secrets`** — Cloud Run mounts Secret Manager values as env
  vars. Use this for anything your MCP reads via `os.environ`.

## Register with Sema4.ai

The deploy output includes a URL like `https://my-mcp-xxxx.run.app`.
Register `https://my-mcp-xxxx.run.app/mcp` on your Sema4.ai agent —
see [registering with a Sema4.ai agent](../03-framework-and-setup.md#registering-with-a-sema4ai-agent).

## Tips

- **Min instances ≥ 1** if cold-start latency bothers your agent.
  Costs money; weigh against per-call latency.
- **Cloud Logging** captures stdout; your MCP's `print()` or
  `logging.info()` calls land there.
- **Shared nginx sidecar** — if you need an auth gatekeeper in front
  of the MCP (e.g. a shared `X-Sema4ai-Auth` infra-auth header), run
  nginx as a sidecar and have it forward to the Python server. This
  is the pattern Sema4.ai uses for its own internal MCPs.
