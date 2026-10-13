# Headroom skills

Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0). The documentation site is unversioned; 0.40.0 was the current release on PyPI and npm when the pages were read.
Generated from https://docs.headroomlabs.ai/docs on 2026-10-13.

Headroom is a context-compression layer for large language model (LLM) applications. It compresses tool outputs, logs, database and retrieval results, and files before they reach the model. It ships as a Python package (`headroom-ai`, imported as `headroom`), an npm package (`headroom-ai`), a local proxy server and a `headroom` command-line interface (CLI).

## Key facts at a glance

- **Three ways in:** the proxy (`headroom proxy`, then point the client's base URL at `http://localhost:8787`), the SDK `compress()` call, or a framework or coding-agent integration (`headroom wrap <agent>`).
- **TypeScript needs the proxy.** The TypeScript SDK compresses through the proxy's `POST /v1/compress`; the Python package compresses in-process.
- **Cache mode is the default.** `--mode cache` compresses only the newest delta, so the provider's prompt cache keeps hitting. `--mode token` removes more tokens but rewrites earlier turns.
- **Compression is reversible.** Compress-Cache-Retrieve (CCR) stores each original, and the model fetches it with `headroom_retrieve`. The proxy keeps originals for 30 minutes by default (`HEADROOM_CCR_TTL_SECONDS`).
- **The compression ratio is tokens after ÷ tokens before.** Lower is better, and the saving is `1 - ratio`. Several docs examples print the raw ratio as the saving.
- **Two defaults to know:** an anonymous usage beacon is on (`HEADROOM_BEACON=off` or `DO_NOT_TRACK=1` turns it off), and the proxy refuses a non-loopback bind without `HEADROOM_PROXY_TOKEN` or the `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` acknowledgement.

## Available skills

| Skill | Topics covered | Lines |
|-------|----------------|-------|
| [getting-started](./getting-started.md) | Choosing proxy, SDK, integration or wrap; quickstart in Python and TypeScript; install channels, Python extras, Docker image tags; Docker-native wrapper; persistent installs (`headroom deploy`, `headroom install`); Headroom Enterprise | 499 |
| [compression](./compression.md) | Pipeline and ContentRouter routing; SmartCrusher options; code, image, search, log, diff and text compressors; Kompress and TextCrusher; pass-through thresholds; fail-safe behavior | 502 |
| [ccr-and-caching](./ccr-and-caching.md) | CCR markers, `headroom_retrieve`, store backends and TTL; live-zone context management; byte-stable prefixes and provider prompt caches; CacheAligner; cold-prefix recompaction; agent wake layout and digest routing | 485 |
| [memory](./memory.md) | Persistent memory (`with_memory()`, scopes, `HierarchicalMemory`, supersession, embedders); SharedContext handoffs; failure learning with `headroom learn` | 486 |
| [proxy](./proxy.md) | Starting and tuning the proxy; savings profiles; configuration in depth; Unix sockets; endpoint map and `/v1/compress` (session mode, gateway mode); `headroom wrap` mechanics; Vertex AI and Bedrock; production; corporate networks; local LLM prefill benchmark | 550 |
| [framework-integrations](./framework-integrations.md) | Vercel AI SDK, OpenAI and Anthropic TypeScript SDKs, LangChain and LangGraph, LiteLLM (callback, middleware, guardrail), Agno, Strands, CrewAI, AutoGen; reading metrics per integration | 498 |
| [coding-agents](./coding-agents.md) | Claude Code (VS Code, Vertex AI, Azure AI Foundry), VS Code Copilot, OpenCode and DeepSeek, Grok Build, Codex, Hermes, OpenClaw, agent hooks, MCP tools, Codex recovery; wrap and unwrap | 498 |
| [configuration](./configuration.md) | Precedence; SDK modes versus proxy modes; per-request overrides; custom model limits and pricing; key environment variables; `x-headroom-base-url` routing; cost-aware model routing; pipeline extensions; OAuth2 upstream; filesystem contract | 557 |
| [observability](./observability.md) | `headroom savings` and the savings ledger; `/stats`, `/stats-history`, Prometheus and OpenTelemetry export; SDK metrics; budget alerts; simulation and waste signals; verifying savings | 497 |
| [sdk-reference](./sdk-reference.md) | Python and TypeScript entry points, configuration and result types, providers and token counting, relevance scorers, direct transform use, error hierarchy and what raises versus passes through | 492 |
| [troubleshooting-and-limits](./troubleshooting-and-limits.md) | Symptom → cause → fix table; debugging techniques; Claude Code quirks behind a custom `ANTHROPIC_BASE_URL`; limitations, safety gates, adaptive K, telemetry versus beacon | 499 |
| [architecture-and-security](./architecture-and-security.md) | Request path and pipeline stages; security model (data in flight and at rest, local control surfaces, egress, hardening checklist); benchmarks; runtime rollout channels | 499 |

## Where to start

- New to Headroom: [getting-started](./getting-started.md), then [compression](./compression.md).
- Putting a coding agent behind Headroom: [coding-agents](./coding-agents.md) and [proxy](./proxy.md).
- Adding Headroom to application code: [framework-integrations](./framework-integrations.md) and [sdk-reference](./sdk-reference.md).
- Savings look wrong: [observability](./observability.md), then [troubleshooting-and-limits](./troubleshooting-and-limits.md).
- Security review: [architecture-and-security](./architecture-and-security.md).

## How to use

Reference a specific skill in a project's CLAUDE.md:

    @~/.claude/skills/headroom/proxy.md

Or point at this index to expose the whole set:

    @~/.claude/skills/headroom/index.md

## Coverage

- Documentation pages read (raw MDX source from `/docs/<slug>.mdx`): **57** of the 59 pages in the sitemap
- Pages skipped on purpose: **2** – `releases` and `ci-cd-flows`, which describe Headroom's own release pipeline and matter only to contributors
- Skill files created: **12**
- Total lines (excluding this index): **6,062**
- Pages failed or inaccessible: **0**

## Known documentation issues (reconciled in these skills)

The docs contradict themselves in places. Where a fact mattered, these skills follow the more specific page and, for the items marked below, the headroom-ai 0.40.0 source.

- **Code compression default:** the introduction and the proxy flag table call it off by default. The code-compression page and the 0.40.0 source (`HEADROOM_CODE_AWARE_ENABLED` defaults to `1`) turn it on in `headroom proxy`. Library `compress()` and `HeadroomClient` still send code to Kompress.
- **`headroom_keep_turns` and `headroom_tool_profiles`:** the configuration and API reference pages present them as working per-request overrides. In the 0.40.0 source nothing reads them, as the context-management and errors pages say. Use `CompressConfig.protect_recent` and `--protect-tool-results` instead.
- **Claude on Vertex AI:** the proxy page routes `publisher=anthropic` requests through LiteLLM. The Claude Code on Vertex AI page and the 0.40.0 source forward them directly to the regional Vertex host with the client's own Google token.
- **Compression ratio:** the TypeScript SDK, API reference and proxy define it as tokens after ÷ tokens before. Several Python and metrics examples print it as if it were the saving.
- **CacheAligner:** some pages say it stabilizes prefixes or maximizes cache hits. The cache-optimization and architecture pages say it only reports drift and never rewrites messages; cache mode keeps prefixes stable.
- **`--stateless`:** the proxy page says it stops all filesystem writes. The security-model page says the runtime `proxy.log` is still written.
- **`HEADROOM_TLS_STRICT`:** the proxy page suggests `0` behind TLS-inspecting gateways. The corporate-networks page says the operating system certificate store makes it unnecessary.
- **Version pins:** the errors page, benchmarks and Hermes plugin notes cite 0.37.0 or older releases. The skills say so where a behavior depends on it.
