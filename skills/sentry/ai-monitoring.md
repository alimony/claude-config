# Sentry: AI & Agent Monitoring
Based on Sentry documentation (docs.sentry.io).

## Overview

Sentry provides observability for AI applications: monitoring AI agent workflows, LLM calls, token usage, costs, tool executions, and MCP server operations. It also offers tools that bring Sentry data into AI coding assistants (MCP server, CLI, agent skills).

---

## AI Agent Monitoring

### What It Tracks

| Signal | Description |
|--------|-------------|
| Agent runs | Full execution traces of agent workflows |
| LLM calls | Model invocations with token breakdown |
| Tool calls | Tool execution duration and errors |
| Token usage | Input, output, cached, and reasoning tokens per model |
| Costs | Estimated spend based on token usage and model pricing |
| Errors | Exceptions and failures across the pipeline |
| Agent handoffs | Transitions between agents in multi-agent systems |

### Supported Python Integrations

All auto-enable when the corresponding package is installed.

| Integration | Import | Min SDK Version | Package Version |
|-------------|--------|-----------------|-----------------|
| OpenAI | `sentry_sdk.integrations.openai.OpenAIIntegration` | 2.41.0+ | openai 1.0+ |
| Anthropic | `sentry_sdk.integrations.anthropic.AnthropicIntegration` | — | anthropic 0.16.0+ |
| LangChain | `sentry_sdk.integrations.langchain.LangchainIntegration` | — | langchain 0.1.0+ |
| LangGraph | Auto-enabled | — | — |
| Google Gen AI | Auto-enabled | — | — |
| Hugging Face Hub | Auto-enabled | — | — |
| OpenAI Agents SDK | Auto-enabled | — | — |
| Pydantic AI | Auto-enabled | — | — |
| LiteLLM | Not auto-enabled | — | — |

### Python Setup

```python
import sentry_sdk

sentry_sdk.init(
    dsn="YOUR_DSN",
    send_default_pii=True,           # include prompts/responses
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
    enable_logs=True,
)
```

Integrations activate automatically. To configure explicitly:

```python
from sentry_sdk.integrations.openai import OpenAIIntegration
from sentry_sdk.integrations.anthropic import AnthropicIntegration

sentry_sdk.init(
    dsn="YOUR_DSN",
    send_default_pii=True,
    traces_sample_rate=1.0,
    integrations=[
        OpenAIIntegration(
            include_prompts=True,              # default True; set False to exclude prompts
            tiktoken_encoding_name="cl100k_base",  # for streaming token counts (requires tiktoken)
        ),
        AnthropicIntegration(
            include_prompts=True,
        ),
    ],
)
```

**OpenAI instrumented methods:** `responses.create`, `chat.completions.create`, `embeddings.create`
**Anthropic instrumented methods:** `messages.create` (sync and async)

### Node.js / Vercel AI SDK Setup

Requires Sentry Node SDK 10.6.0+ and `ai` package 3.0.0-6.x.

```javascript
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: "YOUR_DSN",
  tracesSampleRate: 1.0,
  integrations: [
    Sentry.vercelAIIntegration({
      recordInputs: true,   // capture inputs (default: follows sendDefaultPii)
      recordOutputs: true,  // capture outputs (default: follows sendDefaultPii)
    }),
  ],
});
```

Per-call telemetry control:

```javascript
const result = await generateText({
  model: openai("gpt-4o"),
  experimental_telemetry: {
    isEnabled: true,
    functionId: "my-function",
    recordInputs: true,
    recordOutputs: true,
  },
});
```

### Verification

Data appears in the **AI Spans** tab under **Explore > Traces**.
The **AI Agents Dashboard** populates when agent spans are created.

---

## AI Agents Dashboard

Three tabs: **Overview**, **Models**, **Tools**.

### Overview Tab

| Widget | Shows |
|--------|-------|
| Traffic | Agent runs over time, error rates, releases |
| Duration | Response times for agent executions |
| Issues | Recent errors, agent failures, exceptions |
| LLM Calls | Language model generations over time |
| Tokens Used | Token consumption by model |
| Tool Calls | Tool call volume and trends |

A traces table below links to detailed trace views.

### Models Tab

| Widget | Shows |
|--------|-------|
| Model Cost | Estimated cost based on tokens and pricing |
| Tokens Used | Token counts per model |
| Token Types | Input, output, cached, reasoning breakdown |

### Tools Tab

| Widget | Shows |
|--------|-------|
| Tool Calls | Call volume per tool |
| Tool Errors | Error rates per tool |

### Trace Views

- **Abbreviated view** (click a trace): agent invocations, LLM interactions with token breakdown, API calls, agent handoffs, durations, errors.
- **Detailed view**: full prompts, responses (if PII enabled), timing breakdowns, complete error details.

---

## Model Cost Tracking

Costs are estimated from token usage and pricing data from **models.dev** and **OpenRouter**.

### Calculation

```
input cost  = (input_tokens - cached_tokens) * input_rate
            + cached_tokens * cached_rate
            + cache_write_tokens * cache_write_rate

output cost = (output_tokens - reasoning_tokens) * output_rate
            + reasoning_tokens * reasoning_rate

total cost  = input cost + output cost
```

### Required Span Attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `gen_ai.request.model` or `gen_ai.response.model` | Yes | Model name |
| `gen_ai.usage.input_tokens` | Yes | Input token count |
| `gen_ai.usage.output_tokens` | Yes | Output token count |
| `gen_ai.usage.input_tokens.cached` | No | Cached input tokens |
| `gen_ai.usage.input_tokens.cache_write` | No | Cache write tokens |
| `gen_ai.usage.output_tokens.reasoning` | No | Reasoning tokens |

Limitations: excludes non-token charges, unknown models, and non-standard pricing (volume discounts, batch APIs).

---

## Privacy & Data Collection

### PII Settings

| `sendDefaultPii` | Data Collected |
|-------------------|----------------|
| `false` (default) | Metadata only: model names, token counts, tool names, execution times |
| `true` | Full inputs, outputs, prompts, and responses from AI models and tools |

Override per-integration with `include_prompts=False` on individual integrations.

### Server-Side Scrubbing

Sentry auto-scrubs standard PII patterns (credit cards, SSNs, credentials), but these AI span attributes **bypass default scrubbing**:

- `gen_ai.prompt`
- `gen_ai.request.messages`
- `gen_ai.tool.input`
- `gen_ai.tool.output`
- `gen_ai.response.tool_calls`
- `gen_ai.response.text`
- `gen_ai.response.object`

To scrub these, add custom rules in **Settings > Security & Privacy** using:
`$span.data.'<span attribute>'`

---

## MCP Server Monitoring

### What It Tracks

Tool executions, resource access, client connections, transport protocols, errors, and performance across MCP server operations.

### Python Setup

Requires Python SDK 2.43.0+.

```python
import sentry_sdk
from sentry_sdk.integrations.mcp import MCPIntegration
from mcp.server.fastmcp import FastMCP

sentry_sdk.init(
    dsn="YOUR_DSN",
    traces_sample_rate=1.0,
    send_default_pii=True,
    integrations=[MCPIntegration()],
)

mcp = FastMCP("My MCP Server")

@mcp.tool()
async def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

mcp.run()
```

### Node.js Setup

Requires Node SDK 9.46.0+.

```javascript
import * as Sentry from "@sentry/node";
import { McpServer } from "@modelcontextprotocol/sdk";

Sentry.init({
  dsn: "YOUR_DSN",
  tracesSampleRate: 1.0,
});

const server = Sentry.wrapMcpServerWithSentry(
  new McpServer({
    name: "my-mcp-server",
    version: "1.0.0",
  }),
  {
    recordInputs: true,   // default: follows sendDefaultPii
    recordOutputs: true,  // default: follows sendDefaultPii
  }
);
```

### MCP Dashboard

| Widget | Shows |
|--------|-------|
| Traffic | MCP requests over time, error rates, releases |
| Traffic by Client | Connected client types (e.g., cursor-vscode, custom clients) |
| Transport Distribution | Breakdown by protocol (HTTP, SSE, custom) |
| Most Used Tools/Resources/Prompts | Highest-volume MCP components |
| Slowest Tools/Resources/Prompts | Components with elevated response times |
| Most Failing Tools/Resources/Prompts | Components with high error rates |

Detailed tables for **Tools**, **Resources**, and **Prompts** show request volume, error rate, average duration, and P95 latency.

---

## Sentry MCP Server (AI Assistant Integration)

Connect AI coding assistants to Sentry for real-time error analysis. Hosted at `https://mcp.sentry.dev/mcp` with OAuth authentication.

### Setup

```bash
# Claude Code
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# Cursor — add to mcp.json or via Settings > MCP
# VS Code / GitHub Copilot — CMD+Shift+P > "MCP: Add Server"
# Codex
codex mcp add sentry --url https://mcp.sentry.dev/mcp
```

Manual configuration (works in most clients):

```json
{
  "mcpServers": {
    "Sentry": {
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
```

### Available Tools (16+)

Organizations, projects, teams, issues, DSN management, error searching across files and projects, Seer integration for root cause analysis, release management, performance monitoring.

### Example Prompts

- "Tell me about the issues in my project-name"
- "Diagnose issue PROJECT-123 and propose solutions"
- "Use Sentry's Seer to analyze issue PROJECT-456"
- "Check Sentry for errors in components/UserProfile.tsx"
- "Show recent releases for my organization"

### Self-Hosted Setup

Use STDIO transport with a User Auth Token. Required scopes: `org:read`, `project:read`, `project:write`, `team:read`, `team:write`, `event:write`.

```bash
export SENTRY_ACCESS_TOKEN=your-token
export SENTRY_HOST=your-sentry-host
```

---

## Sentry CLI

Natural-language CLI for developers and AI agents.

### Install

```bash
curl https://cli.sentry.dev/install -fsS | bash
# or
npm install -g sentry
# or run directly
npx sentry --help
```

### Authenticate

```bash
sentry auth login          # OAuth device flow (recommended)
sentry auth login --token YOUR_TOKEN  # API token
```

### Key Commands

| Command | Description |
|---------|-------------|
| `sentry issue list` | List all issues |
| `sentry issue explain <short-id>` | AI root cause analysis via Seer |
| `sentry issue plan <short-id>` | Generate remediation steps |
| `sentry project list` | List projects |
| `sentry org list` | List organizations |
| `sentry org list --json \| jq '.[0]'` | JSON output for automation |

---

## Agent Skills

Instruction files that teach AI coding assistants how to set up and use Sentry. Install into your IDE's skills directory.

### Install

```bash
# Single skill
npx skills add getsentry/sentry-for-ai --skill sentry-fix-issues

# All skills
npx skills add getsentry/sentry-for-ai

# CLI skill
npx skills add https://cli.sentry.dev
```

### Skill Directories by IDE

| IDE | User Path | Project Path |
|-----|-----------|--------------|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Codex, Copilot, OpenCode, AmpCode | IDE-specific paths | IDE-specific paths |

### Available Skills

**Setup skills:** React, React Native, Python, Django, Flask, Ruby, Rails, iOS, Next.js, .NET, Go, Svelte, OpenAI/LangChain monitoring, OpenTelemetry exporters.

**Workflow skills:** Error fixing, PR code reviews, alert creation, backlog management.

### dotagents (Package Manager)

Manages `.agents` directories with version locking and team sharing.

```bash
npx @sentry/dotagents init
npx @sentry/dotagents add getsentry/skills --name find-bugs
npx @sentry/dotagents install
```

Skills declared in `agents.toml`, versions locked in `agents.lock`. Skills symlink into IDE-specific directories.
