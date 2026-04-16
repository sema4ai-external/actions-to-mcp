# Orchestration

How to host your migrated MCP. Three cloud-specific walk-throughs plus
a pattern for bundling multiple MCPs behind one endpoint.

| Target | Best for | File |
| --- | --- | --- |
| **Google Cloud Run** | Teams already on GCP; simplest setup. | [cloud-run.md](cloud-run.md) |
| **AWS Bedrock AgentCore** | AWS-first stacks, especially integrating with Bedrock-hosted models. | [bedrock-agentcore.md](bedrock-agentcore.md) |
| **Azure Container Apps** | Azure-first stacks. | [azure-container-apps.md](azure-container-apps.md) |
| **Multi-MCP gateway** | Hosting several migrated MCPs behind one URL. | [gallery-pattern.md](gallery-pattern.md) |

Pick one. The MCP itself is the same in every case — what differs is
the container image's base, ingress config, and how secrets arrive.

Every target needs:

- **Streamable-HTTP transport** (remote-only — Sema4.ai doesn't
  support stdio).
- **Session affinity** on the load balancer (MCP sessions are
  stateful per connection).
- **Secrets wiring** — platform-native secret managers for anything
  your MCP reads via `os.environ`.
- **A health endpoint** if the platform expects one (all three below
  do).
