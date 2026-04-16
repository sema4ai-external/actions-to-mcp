# Azure Container Apps

Azure Container Apps is Microsoft's serverless container platform —
the Azure-native equivalent of Cloud Run.

## Container

Standard Linux image (same `Dockerfile` shape as
[Cloud Run](cloud-run.md), with the port adjusted for Container Apps'
convention — typically 8080).

Publish to Azure Container Registry:

```bash
az acr build --registry mcpregistry --image mcp-my-service:latest .
```

## Deploy

```bash
az containerapp up \
  --name my-mcp \
  --resource-group my-rg \
  --environment my-env \
  --image mcpregistry.azurecr.io/mcp-my-service:latest \
  --target-port 8080 \
  --ingress external \
  --env-vars MCP_HTTP_PORT=8080
```

Key flags:

- **`--ingress external`** — expose the MCP to the internet.
- **`--target-port`** — the port your MCP listens on inside the
  container.
- **Session affinity** — enable via `az containerapp ingress
  sticky-sessions set` after create. Required for streamable-HTTP
  sessions.

## Secrets

```bash
az containerapp secret set \
  --name my-mcp \
  --resource-group my-rg \
  --secrets my-api-key=supersecret

az containerapp update \
  --name my-mcp \
  --resource-group my-rg \
  --set-env-vars MY_SERVICE_API_KEY=secretref:my-api-key
```

Secrets attach as env vars via `secretref:`. Your MCP reads them
normally via `os.environ`.

## Register with Sema4.ai

Get the FQDN:

```bash
az containerapp show --name my-mcp --resource-group my-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

Register `https://<fqdn>/mcp` on your Sema4.ai agent — see
[registering with a Sema4.ai agent](../03-framework-and-setup.md#registering-with-a-sema4ai-agent).

## Tips

- **Log Analytics** workspace attached to the Container Apps
  environment captures stdout.
- **Application Insights** for request-level tracing — wire it up
  via OpenTelemetry if you want deep instrumentation.
- **Scale to zero** cuts cost but adds cold-start latency. Disable
  for latency-sensitive MCPs.
