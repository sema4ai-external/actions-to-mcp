# AWS Bedrock AgentCore

AgentCore is AWS's managed runtime for agent-adjacent services,
including MCPs. It's the natural choice when your MCP sits alongside
Bedrock-hosted models and other AWS services.

This page covers the MCP-side shape. For current AgentCore console /
CLI steps, follow the AWS docs — they evolve.

## Container shape

Build a standard Linux container (same `Dockerfile` shape as the
[Cloud Run](cloud-run.md) page, minus the Cloud Run-specific port
convention). Publish to ECR.

Key requirements for AgentCore:

- **Listen on the port AgentCore expects** (configurable via env
  var on the runtime config).
- **Serve streamable-HTTP on a known path** (`/mcp`).
- **Handle `X-Tool-Invocation-Context` and `Authorization`** as
  described in [sema4-patterns](../05-sema4-patterns.md) — AgentCore
  doesn't touch these; they pass through.

## Auth

Two orthogonal layers:

- **AgentCore-level auth** — AWS IAM policies on who can invoke the
  runtime. Configure per your security model.
- **MCP-level auth** — `Authorization: Bearer` or `X-Api-Key` from
  the Sema4.ai agent, forwarded through AgentCore to your MCP.

IAM controls who can invoke; your MCP's own auth determines what the
invoker can do inside.

## Secrets

Use AWS Secrets Manager. Mount into the container as env vars via
AgentCore's runtime config. Your MCP reads them the same way it does
on any platform.

## Scaling and sessions

AgentCore handles autoscaling. Ensure your runtime config enables
session affinity so streamable-HTTP sessions survive across requests
— check the current AgentCore docs for the exact knob.

## Register with Sema4.ai

AgentCore gives you an invoke endpoint URL. Register it (with `/mcp`
suffix) on your Sema4.ai agent — see
[registering with a Sema4.ai agent](../03-framework-and-setup.md#registering-with-a-sema4ai-agent).

## Tips

- **CloudWatch Logs** captures container stdout. Your MCP's logs land
  there automatically.
- **AWS X-Ray** can trace requests if you instrument the MCP — see
  [observability](../08-observability.md).
- **VPC access** — if the MCP calls services in a private VPC (e.g. a
  data warehouse), configure the AgentCore runtime's VPC attachment.
