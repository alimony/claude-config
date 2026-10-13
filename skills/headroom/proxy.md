# Headroom: Proxy server
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

The Headroom proxy is a standalone HTTP server that compresses large language model (LLM) traffic on its way to the provider. You point a client's base URL at the proxy, and Headroom compresses each request before it forwards it upstream. This skill covers running and tuning the proxy, the compression-only API, agent wrapping, cloud backends, production deployment, corporate networks and local-model benchmarks.

## Core concepts

- **Optimized and passthrough modes.** The proxy compresses by default (optimized mode). `--no-optimize` turns it into a transparent forwarder (passthrough mode), so the token counts before and after match. Use passthrough mode for baselines.
- **ContentRouter.** The proxy routes text, logs, JSON, code, images and tool outputs through the enabled compressors. Where it applies, it leaves reversible Compress-Cache-Retrieve (CCR) markers, so the model can recover originals with the `headroom_retrieve` tool.
- **Cache mode and token mode.** `--mode cache` (the default) freezes prior turns and compresses only the newest delta, so the provider's prefix cache stays valid. `--mode token` maximizes removal and may rewrite prior turns, which changes the cached prefix. Prefer cache mode for long agent sessions: on Anthropic a cache read is about 90% cheaper than fresh input, so a cache miss can cost more than the compression saves.
- **Savings profiles.** `HEADROOM_SAVINGS_PROFILE` seeds the whole compression posture at startup. The default profile is `coding`.
- **Three configuration layers.** Environment variables override the savings profile, and command-line interface (CLI) flags override both. Nearly every flag has a `HEADROOM_*` twin for Docker, systemd and CI.
- **Loopback by default.** The proxy binds `127.0.0.1:8787`. A non-loopback bind needs `HEADROOM_PROXY_TOKEN` or the explicit `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` acknowledgement, or the proxy refuses to start.

## Start the proxy

```bash
# Basic usage
headroom proxy

# With logging and budget
headroom proxy \
  --log-file /var/log/headroom.jsonl \
  --budget 100.0

# Deliberate public access, with the existing token protocol
HEADROOM_PROXY_TOKEN='replace-with-a-secret' headroom proxy --host 0.0.0.0 --port 8080

# Health check: returns status, optimize, and stats (total_requests, tokens_saved, savings_percent)
curl http://localhost:8787/health
```

Core flags that later sections do not cover (run `headroom proxy --help`, or see https://docs.headroomlabs.ai/docs/proxy, for the full list):

| Flag | Default | Use it to |
| --- | --- | --- |
| `--host`, `--port` | `127.0.0.1`, `8787` | Set the bind address. |
| `--uds PATH` | none | Serve on a Unix domain socket instead of TCP. |
| `--no-optimize` | `false` | Run in passthrough mode. |
| `--no-cache` | `false` | Turn off semantic caching. |
| `--openai-api-url`, `--anthropic-api-url`, `--gemini-api-url` | provider defaults | Forward to a custom upstream. |
| `--provider-name` | detected from `--openai-api-url` | Rename the OpenAI-compatible upstream on the dashboard (for example `OpenRouter`). Routing and pricing are unaffected. |
| `--backend` | `anthropic` | Pick `anthropic`, `bedrock`, `openrouter`, `anyllm` or `litellm-<provider>`; see [Cloud providers](#cloud-providers) for `vertex_ai` and `azure`. |
| `--memory`, `--learn` | `false` | Turn on persistent memory. `--learn` adds live traffic learning, implies `--memory`, and persists a pattern after `--min-evidence` observations (default `5`). |
| `--codex-wire-debug` | `false` | Write local Codex wire snapshots and matching proxy log traces. |

`--memory` interacts with cache mode. In `--mode cache`, the proxy skips automatic memory context injection for Anthropic `/v1/messages` to keep the prefix stable, while OpenAI chat, OpenAI Responses and Gemini append memory to the live-zone tail. Use `--mode token` when you need automatic memory context on the Anthropic path.

## Point clients at the proxy

| Client speaks | Set | Value |
| --- | --- | --- |
| Anthropic Messages API (for example Claude Code) | `ANTHROPIC_BASE_URL` | `http://localhost:8787` – no `/v1` |
| OpenAI-compatible API | `OPENAI_BASE_URL` | `http://localhost:8787/v1` |
| Bedrock InvokeModel (needs `--bedrock-api-url`) | `AWS_ENDPOINT_URL_BEDROCK_RUNTIME` | `http://127.0.0.1:8787` |
| Native Vertex REST | the client's endpoint setting | the proxy URL |

```bash
# Claude Code
ANTHROPIC_BASE_URL=http://localhost:8787 claude

# Any OpenAI-compatible CLI client that reads OPENAI_BASE_URL
OPENAI_BASE_URL=http://localhost:8787/v1 your-client
```

When the proxy has a proxy token, non-loopback callers send it as `Authorization: Bearer <token>` or `X-Headroom-Proxy-Token: <token>`. Headroom strips it before forwarding. A client that also sends a provider credential should use `X-Headroom-Proxy-Token` and keep `Authorization` for the provider.

To change where the proxy forwards, use the upstream flags above or these variables:

```bash
# Route OpenAI passthrough requests to a custom endpoint
export OPENAI_TARGET_API_URL=https://custom.openai.endpoint.com
# Route Anthropic passthrough requests to a custom endpoint
export ANTHROPIC_TARGET_API_URL=https://litellm.company.internal
# Compress Bedrock InvokeModel traffic, forwarding to a re-signing gateway
export BEDROCK_TARGET_API_URL=http://127.0.0.1:4000
```

Custom paths that fall through to the catch-all handler are not compressed by default. Set `HEADROOM_COMPRESS_PASSTHROUGH=1` to compress them too, when the body is OpenAI Responses-shaped and the path ends in `/responses`.

## Choose a savings profile

| Profile | Target savings | Mode | Behavior | Pick it for |
| --- | --- | --- | --- | --- |
| `coding` (default) | about 50%, emergent | `cache` | Compresses only the newest delta, with about zero prefix-cache busts. Compresses user messages, keeps system prompts, never lossy-compresses file reads. Lossless first with lossy fallback; tool search and cross-turn dedup on. | Coding agents, especially on Anthropic. `headroom wrap` uses it. |
| `balanced` | about 70% | `token` | 30% keep-ratio on the standard lossless pipeline, structural compaction, protects 4 recent turns. | Safe general-purpose moderate compression. |
| `agent-90` | about 90% | `token` | Forces Kompress with a `0.10` keep-ratio, skips the lossless path, compresses user and system messages. | Non-coding, cost-sensitive or high-volume workloads. |
| `general` | about 60%, emergent | `token` | No turn protection; leaves user and system messages uncompressed; standard lossless pipeline. | Non-coding chat with little code in context. |

`coding` sets `protect_recent=0` on purpose. In cache mode the delta already is the newest turn, so a turn-count guard would block the only thing cache mode compresses. File reads stay byte-exact through `protect_reads=True` instead.

```bash
# Aggressive profile; state the mode explicitly on a direct launch
HEADROOM_SAVINGS_PROFILE=agent-90 headroom proxy --mode token

# Start from a profile and override single knobs
HEADROOM_SAVINGS_PROFILE=coding HEADROOM_FORCE_KOMPRESS=1 headroom proxy
HEADROOM_SAVINGS_PROFILE=balanced HEADROOM_TARGET_RATIO=0.15 headroom proxy
```

- **Profile defaults fill only unset variables.** That is why the overrides above work.
- **Mode precedence.** For a direct `headroom proxy` launch, the mode comes from `--mode`, then `HEADROOM_MODE`, then the `cache` default. The profile does not supply a mode fallback after startup; wrapped launches may seed `HEADROOM_MODE`. Pass `--mode token` or `HEADROOM_MODE=token` with a token-mode profile, so the mode is never in doubt.
- **Typos fail quietly.** An unknown profile name logs a warning and falls back to `coding`, and the proxy still starts. Check the startup log after you change the profile.
- **Use the environment variable.** It is the setting that `headroom wrap` passes on to the proxy it launches.
- **Custom profiles** are `AgentSavingsProfile` dataclasses in `headroom/agent_savings.py`, which also lists every knob of the built-in profiles.

## Configure the proxy in depth

Three layers set proxy behavior, each overriding the one before: savings profile, `HEADROOM_*` environment variables, CLI flags. Most deployments pick a profile and touch few of the knobs below; unless noted, each is off or unset by default. For programmatic deployment, pass a whole proxy config as JSON in `HEADROOM_PROXY_CONFIG_JSON`, or point `HEADROOM_CONFIG_DIR` and `HEADROOM_WORKSPACE_DIR` at custom roots.

### Compression tuning

| Flag / variable | Default | Effect |
| --- | --- | --- |
| `--mode` / `HEADROOM_MODE` | `cache` | `cache` compresses only the newest delta; `token` maximizes removal. |
| `--target-ratio` / `HEADROOM_TARGET_RATIO` | unset | Keep-ratio for machine learning (ML) text compression; lower is more aggressive, for example `0.10`. |
| `HEADROOM_MIN_TOKENS` | `500` | Minimum block size before a tool output is compressed. |
| `HEADROOM_COMPRESS_USER_MESSAGES` | profile | Compress text in user messages. `coding` turns it on; `0` keeps user text verbatim. Anthropic `tool_result` blocks compress either way. |
| `HEADROOM_COMPRESS_SYSTEM_MESSAGES` | unset | Compress system prompts. Leave it off to keep the hottest cache prefix stable. |
| `HEADROOM_PROTECT_RECENT` | profile | Never compress the N most recent turns. |
| `--protect-tool-results` / `HEADROOM_PROTECT_TOOL_RESULTS` | empty | Comma-separated tool names whose output is never lossy-compressed. |
| `--compressor` (repeatable) / `HEADROOM_COMPRESSORS` | all | Restrict to `smart_crusher`, `kompress`, `code_aware`, `search`, `log`, `tabular`, `config`, `html`, `image`. |
| `--code-aware` / `--no-code-aware` / `HEADROOM_CODE_AWARE_ENABLED` | on | Abstract syntax tree (AST) code compression; needs `headroom-ai[code]` and does nothing without it. The proxy page and `--help` say "disabled", but the code-compression page and the 0.40.0 source default it to on. |

```bash
headroom proxy --compressor smart_crusher --compressor log       # only these two compressors
HEADROOM_PROTECT_TOOL_RESULTS=<tool_a>,<tool_b> headroom proxy  # never lossy-compress these tools
```

`HEADROOM_COMPRESS_PASSTHROUGH`, `HEADROOM_COMPRESS_USER_MESSAGES` and `HEADROOM_FORCE_KOMPRESS_ALL` have no `headroom proxy` flag. Set them as environment variables, or use the direct module entry point `python -m headroom.proxy.server`, which accepts `--compress-passthrough`, `--compress-user-messages` and `--force-kompress-all`.

### Kompress (ML compression)

Kompress is the ModernBERT/ONNX (Open Neural Network Exchange) compressor that ContentRouter falls back to for prose and unstructured text. It scores tokens for retention – classification, not generation – and runs in-process by default, so budget CPU and memory for it.

| Flag / variable | Default | Effect |
| --- | --- | --- |
| `--disable-kompress` / `HEADROOM_DISABLE_KOMPRESS` | `false` | Turn off ML compression and keep the structural compressors. |
| `--disable-kompress-anthropic`, `--disable-kompress-openai` | inherit | Per-provider override. |
| `HEADROOM_FORCE_KOMPRESS_ALL` | `false` | Route all content through Kompress, bypassing per-type selection. |
| `HEADROOM_KOMPRESS_ENDPOINT`, `HEADROOM_KOMPRESS_ENDPOINT_TOKEN` | none | Offload inference to a remote `/compress` endpoint (for example a Modal deployment), with a bearer token. |
| `HEADROOM_KOMPRESS_BACKEND` | `auto` | `auto`, `onnx_cpu`, `onnx_coreml`, `pytorch` or `pytorch_mps`. |

A remote Kompress endpoint is real egress: content goes out for inference, although the CCR store stays proxy-local and originals never persist off the machine. The endpoint points outbound and is unrelated to the proxy's inbound `/v1/compress` route.

### Reversible compression and file reads

By default Headroom stores originals so the model can recover them through `headroom_retrieve`. Coding agents re-read the same files, so the proxy also retires stale reads without busting the prefix cache.

| Flag / variable | Default | Effect |
| --- | --- | --- |
| `--no-ccr` / `HEADROOM_NO_CCR` | CCR on | Remove retrieval markers and the injected `headroom_retrieve` tool. |
| `--lossless` / `HEADROOM_LOSSLESS` | `false` | Format-native lossless compaction only: no CCR marker, no retrieval tool. |
| `--no-ccr-proactive-expansion` | expansion on | Stop re-expanding compressed content when the model appears to need it. |
| `--no-read-lifecycle` | lifecycle on | Stop replacing stale or superseded file reads with CCR markers. |
| `--read-maturation` / `HEADROOM_READ_MATURATION` | `false` | Beta. Keep fresh file reads verbatim while in use and compress them once the file quiesces (`--read-maturation-quiesce-turns`, default `5`), unless the provider cache already holds them. Needs `HEADROOM_ROLLOUT_CHANNEL=beta` or `dev`. |
| `--intercept-tool-results` | `false` | Canary tool-result interceptors such as ast-grep Read outlining. Needs `HEADROOM_ROLLOUT_CHANNEL=canary` or `dev`. |

### Reliability and performance

| Flag / variable | Default | Effect |
| --- | --- | --- |
| `--request-timeout-seconds` / `HEADROOM_REQUEST_TIMEOUT` | `300` | Upstream request timeout in seconds. |
| `--connect-timeout-seconds` | `10` | Upstream connect timeout in seconds. |
| `--retry-max-attempts` | `3` | Retries on transient upstream failure. |
| `--limit-concurrency` | `1000` | Concurrent connections before Uvicorn returns 503. |
| `--max-connections`, `--max-keepalive` | `500`, `100` | Upstream HTTP connection and keep-alive limits. |
| `--rpm`, `--tpm` | `60`, unlimited | Requests- and tokens-per-minute limits; `--no-rate-limit` turns them off. |
| `--budget`, `--budget-period` | none, `daily` | Spend cap in US dollars per period; over-budget requests get 429. |
| `--workers` / `HEADROOM_WORKERS` | `1` | Uvicorn worker processes. |
| `--embedding-server` / `HEADROOM_EMBEDDING_SERVER` | off | Share one ONNX embedder across workers, saving about 600 MB of resident memory. |
| `--compression-max-workers` / `HEADROOM_COMPRESSION_MAX_WORKERS` | CPU count | Bound the CPU-bound compression thread pool. |

### Tool search and model routing

- `HEADROOM_TOOL_SEARCH` (server side) defers Model Context Protocol (MCP) and system tool schemas behind a `search_tools` tool, so large schemas do not ride in every request. It is on by default for Anthropic requests that carry enough tools; set `HEADROOM_TOOL_SEARCH=0` to opt out.
- `ENABLE_TOOL_SEARCH` (client side) keeps Claude Code's own deferred tool loading active behind a custom base URL. `headroom wrap` sets it automatically, so remember it when you set `ANTHROPIC_BASE_URL` by hand.
- Cost-aware model routing rewrites the upstream model per request, for example to send small tool-free calls to a cheaper model. It is opt-in through `HEADROOM_MODEL_ROUTER_ENABLED` and `HEADROOM_MODEL_ROUTES`.

### Logs and observability

| Flag / variable | Default | Effect |
| --- | --- | --- |
| `--telemetry` / `HEADROOM_TELEMETRY` | off | Local-only usage stats for your `/stats`, `/metrics` and dashboard. Nothing leaves the machine. |
| `--log-file` / `HEADROOM_LOG_FILE` | none | JSON Lines (JSONL) request and response log. |
| `--log-messages` | `false` | Add full message bodies to the log. |
| `HEADROOM_LOG_LEVEL` | `warning` | Uvicorn log level. Raise it to `info` for the per-request access log when you diagnose a deployed proxy. |
| `HEADROOM_LOG_PAYLOAD_PREVIEW` | `off` | Add up to 4 KB of each retrieved CCR payload to `headroom_retrieve` lines in the runtime log. |
| `HEADROOM_OTEL_METRICS_ENABLED`, `HEADROOM_LANGFUSE_ENABLED` | `false` | Export OpenTelemetry metrics (`HEADROOM_OTEL_METRICS_ENDPOINT`, …) or Langfuse traces (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`). |

The runtime log is `~/.headroom/logs/proxy-<port>.log`. Treat every log as sensitive while `--log-messages`, `--codex-wire-debug` or `HEADROOM_LOG_PAYLOAD_PREVIEW` is on: payloads are verbatim tool output and can carry source code, customer data or credentials that the redactor misses. Never share a log captured with payload preview on.

- **Linux and macOS:** every log file and rotated backup is `0600`, and Headroom refuses to log through a symlinked path. A log shipper that runs as another user cannot read the runtime log, so run it as the same user or copy the file with a privileged job.
- **Windows:** Headroom cannot restrict the log, which inherits the directory's access control list. Keep `%USERPROFILE%\.headroom` and your `--log-file` path off shared volumes.

### Security and networking

| Variable | Default | Effect |
| --- | --- | --- |
| `HEADROOM_PROXY_TOKEN` | none | Require a token from non-loopback callers. It also gates `/stats-history`, `/quota`, `/subscription-window` and `/metrics`, which otherwise answer only loopback callers and trusted Classless Inter-Domain Routing (CIDR) ranges. |
| `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` | `false` | Accept a non-loopback bind with no token. Set it only when the runtime already limits reachability, such as a container published on `127.0.0.1`. |
| `HEADROOM_COMPRESS_ALLOW_REMOTE` | `false` | Let non-loopback callers reach `POST /v1/compress` and `POST /v1/usage`. |
| `HEADROOM_OFFLINE` | `false` | Air-gap mode: refuse every connection Headroom itself starts, such as telemetry, update checks, model and tokenizer downloads, remote Kompress, and OpenTelemetry and Langfuse export. Forwarding your requests to your configured upstream still works. |
| `--stateless` / `HEADROOM_STATELESS` | `false` | Keep runtime state in memory; memory and the request log are off. The security-model page adds that the runtime `proxy.log` is still written. |
| `HEADROOM_LICENSE`, `HEADROOM_USAGE_REPORTING` | unset, `false` | License token. `HEADROOM_USAGE_REPORTING=1` lets the proxy validate it and post aggregate usage counts, never content. |
| `HEADROOM_CERT_STORE`, `HEADROOM_CA_BUNDLE`, `HEADROOM_TLS_STRICT` | see below | Upstream Transport Layer Security (TLS) trust; see [Run behind a corporate network](#run-behind-a-corporate-network). |

The bind check exists because, without a token, `/v1/*` would relay upstream with the operator's credentials for every peer that can reach the port.

- **Do:** `HEADROOM_PROXY_TOKEN='replace-with-a-secret' headroom proxy --host 0.0.0.0 --port 8080`.
- **Don't:** set `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` on a host that other machines can reach. Every peer that reaches the port can then relay requests on your provider credentials.

## Serve on a Unix socket

```bash
headroom proxy --uds ~/.headroom/run/proxy.sock
curl --unix-socket ~/.headroom/run/proxy.sock http://localhost/health
```

`--uds` changes only the transport; request handling is identical. Prefer it over a loopback port when you want no port to collide with or expose, because filesystem permissions then govern access. It also suits containers and systemd units that share a socket through a bind mount or runtime directory.

- **The parent directory's mode is the access-control boundary**, because a socket carries no credentials. Headroom creates a missing parent as `0700`. It leaves an existing parent's permissions alone, but refuses to start if that directory is writable by other users and not sticky. A sticky directory such as `/tmp` is accepted, because others cannot unlink or rename your entry.
- **Startup checks.** Headroom removes a stale socket left by a crashed process. It refuses to start when something still listens on the path (two proxies would split traffic), when the path exists and is not a socket (likely a typo pointing at real data), or when the path exceeds `sun_path`: 108 bytes on Linux, 104 on macOS and the BSDs. Keep the path short, because an overlong path fails inside `bind()` with an error that names nothing.
- **Portable Operating System Interface (POSIX) only.** On Windows the command exits with an error that tells you to use `--port`.
- **No Remote Control.** A socket does not re-enable Claude Code's Remote Control. `ANTHROPIC_UNIX_SOCKET` passes that feature's host check, but Claude Code then treats the session as API-key auth, which fails a separate subscription-auth requirement.

## API endpoints

The full request, response and error tables are at https://docs.headroomlabs.ai/docs/proxy.

| Category | Endpoints | Notes |
| --- | --- | --- |
| Health and stats | `GET /health`, `GET /stats`, `GET /stats-history`, `GET /metrics`, `/dashboard` | `/stats` adds durable `persistent_savings` from `~/.headroom/proxy_savings.json` (override with `HEADROOM_SAVINGS_PATH`). `/stats-history` holds hourly to monthly rollups for the dashboard, for example `?format=csv&series=weekly`. `/metrics` is Prometheus format. |
| Anthropic | `POST /v1/messages` | Compresses, forwards, returns the response. |
| OpenAI | `POST /v1/chat/completions`, `POST /v1/responses` | The Responses route compresses `input` where applicable. |
| Codex | `POST /v1/codex/responses`, `POST /backend-api/responses`, `POST /backend-api/codex/responses`; Live voice WebSockets on `/v1/live`, `/v1/codex/live`, `/backend-api/live`, `/backend-api/codex/live` | Aliases of the Responses handler. Live voice frames pass through untransformed; `HEADROOM_CODEX_LIVE_WS_PATH` corrects the backend suffix. |
| Cloud Code Assist | `POST /v1internal:streamGenerateContent`, `POST /v1/v1internal:streamGenerateContent` | Google Cloud Code Assist and Antigravity clients (`google-gemini-cli`, `google-antigravity`). |
| Native Vertex | `/{api_version}/projects/{project}/locations/{location}/publishers/{publisher}/models/{model}:generateContent`, plus `:streamGenerateContent`, `:countTokens`, `:rawPredict`, `:streamRawPredict` | Always registered. |
| Bedrock InvokeModel | `/model/{id}/invoke`, `/model/{id}/invoke-with-response-stream` | Registered only with `--bedrock-api-url`. |
| Compression only | `POST /v1/compress`, `POST /v1/compress/response`, `POST /v1/usage` | Loopback-only by default. |

For lifetime savings in Prometheus, use `headroom_persistent_savings_tokens_saved_total`, which matches `/stats.persistent_savings`. `headroom_tokens_saved_total` counts only the current proxy process.

### Compress without a completion: `POST /v1/compress`

This route compresses messages and returns them without any completion request to a provider: no generation and no provider API key. The TypeScript SDK, LiteLLM's `headroom` guardrail and API-gateway sidecars use it. It still runs local ML – Kompress and the Magika content classifier – so budget CPU and memory for a sidecar.

```bash
curl -s http://localhost:8787/v1/compress -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "..."}], "model": "claude-sonnet-4-6"}'
```

| Request field | Notes |
| --- | --- |
| `messages` (required) | OpenAI shape or Anthropic content blocks. No format conversion: you get back the shape you sent, with block types, `tool_use_id`s and order preserved. |
| `model` (required) | The real model name, including gateway prefixes such as `bedrock/anthropic.claude-3-5-sonnet` or `vertex_ai/claude-sonnet-4@20250514`. It selects the tokenizer and context limit. |
| `token_budget` | Overrides the model's context limit. |
| `config` | `mode`, `frozen_message_count`, `session_id`, `compress_user_messages` (default `false`), `target_ratio`, `protect_recent`, `protect_analysis_context`. |
| `gateway` | Switches on gateway mode. |

Leave `config.mode` unset for forward-only callers: the default is marker-free and writes nothing to the CCR store. Use `ccr` only if you also inject `headroom_retrieve` and can reach `/v1/retrieve` (itself loopback-only); otherwise the markers are dangling pointers. `lossy_inline` (alias `lossless_then_lossy`) runs the lossless fold first and then compresses the remainder, still marker-free.

The response carries `messages`, `tokens_before`, `tokens_after`, `tokens_saved`, `compression_ratio`, `transforms_applied`, `transforms_summary`, `ccr_hashes` and, in session mode, `session`. `compression_ratio` is `tokens_after / tokens_before`, so lower is better: `0.23` means a 77% reduction.

- **Remote callers get `404`, not `403`.** Both the client IP and the `Host:` header must be loopback; Docker and Podman host-gateway requests with a loopback `Host:` header count. A gateway in another pod sees what looks like a missing route until you set `HEADROOM_COMPRESS_ALLOW_REMOTE=1`. The proxy token still applies.
- **`system` and `tools` are ignored outside gateway mode.** You get a `200` without a warning, and neither field comes back. Carry both yourself and send them upstream unchanged. Tool-schema compaction, tool-search deferral and output steering need gateway mode.
- **Timeouts fail open without a session.** You get `200` with your original messages, zeroed metrics, `compression_skipped: true` and `skip_reason: "compression_timeout"`. Check `compression_skipped` when you need to know whether compression ran.
- `x-headroom-bypass: true` skips compression and echoes the messages with zeroed metrics.
- Errors: `400` `invalid_request`, `401` for a missing or wrong proxy token, `404` for a remote caller, `503` `compression_error`, and `503` `compression_timeout` in session mode. Requests appear under `provider="compress"` in `/stats` and `/metrics`.

### Keep the prefix cache across turns

Without session state, `/v1/compress` is not safe for an agent loop. The provider caches the bytes you forwarded, and those differ from your originals once compressed. If you recompress the pristine conversation each turn, the leading messages come back different, and you pay for compression and a cache miss. A `200` with a positive `tokens_saved` hides this, so watch your provider's cache-read tokens.

**Option 1 – keep the state yourself.** Pass `config.frozen_message_count` (how many leading messages the provider already cached), and send back your previous output, not the originals. The frozen count pins whatever you hand it.

```python
import requests

proxy = "http://localhost:8787"
# Keep what you FORWARDED, not what you started with.
forwarded: list[dict] = []

def next_turn(new_messages: list[dict]) -> list[dict]:
    body = {
        "messages": forwarded + new_messages,
        "model": "claude-sonnet-4-6",
        # Everything already forwarded is already cached upstream – pin it.
        "config": {"frozen_message_count": len(forwarded)},
    }
    result = requests.post(f"{proxy}/v1/compress", json=body).json()
    forwarded[:] = result["messages"]   # becomes next turn's frozen prefix
    return forwarded
```

**Option 2 – session mode.** Pass `config.session_id` (non-empty, at most 256 characters) and resend the raw conversation each turn. Headroom returns every message it returned before byte for byte, and compresses only the new tail. A larger explicit `frozen_message_count` still wins.

```json
{ "messages": [{ "role": "user", "content": "..." }], "model": "claude-sonnet-4-6", "config": { "session_id": "conv-8f1c" } }
```

- Forward the returned messages verbatim, because they are what the next turn replays.
- `compress_user_messages` is refused with `400`, because user-message rewrites are not byte-replayable.
- Timeouts and busy sessions return `503` (`compression_timeout`) instead of failing open; retry the turn. A concurrent turn that waits more than 10 seconds for the session lock gets the same `503`.
- State is in-process. The replay cache lives for `HEADROOM_COMPRESSION_CACHE_TTL_SECONDS` of idle time (default `3900`, floor `600`). With several workers or replicas, hash the upstream on the session id so that each session stays on one process, or replay silently misses.
- `HEADROOM_COMPRESS_SESSION_FROM_HEADER=1` lets the `x-headroom-session-id` header stand in for `config.session_id`. It is off by default because gateways often stamp one value on all traffic, and Claude Code subagents share a value, which would blend conversations.
- Optionally post the provider's `usage` block to `POST /v1/usage` for cache-hit attribution and savings accounting, for example `{ "session_id": "conv-8f1c", "usage": { "cache_read_input_tokens": 11800, "cache_creation_input_tokens": 400 } }`. It is telemetry only, so skipping it costs attribution, never correctness.

`protect_recent` is no substitute for either option: it guards the newest messages, while the cache sits at the oldest.

### Gateway mode

An API gateway that owns routing (Kong, LiteLLM, a custom sidecar) never shows Headroom the provider's response. Gateway mode splits one model turn into two calls, so that transforms that need the response can run only when the gateway can re-drive the provider ("no shrink without reload").

1. **Request half.** Add a top-level `gateway` object to `POST /v1/compress` (`{}` uses every default). Every top-level field other than `messages`, `model`, `token_budget`, `config` and `gateway` passes through into the returned `body`, and `tools` is compacted deterministically, so identical tools stay byte-identical across turns. Forward `body` as-is, and set the returned `headers` on the provider request (today only `anthropic-beta`).
2. **Response half.** When `obligations` is non-empty, post `turn_id`, `status`, `usage`, `round` and, for a `redrive` obligation after a successful call, the full provider `response` to `POST /v1/compress/response`. The answer is `done` (forward its `response`, or the provider response you hold when it is `null`) or `redrive` (send its `request` to the provider exactly as given and post the result back).

Declare capabilities in the `gateway` block. `can_redrive` (default `false`) means the gateway can call the provider again with a request Headroom hands it; send `false` for streaming requests. `can_relay_response` (default `false`) promises status and usage after every turn. `session_affinity` (default `true`) pins the session to one replica; `false` disables re-driving. `request_headers` passes client headers, of which only `anthropic-beta` is read.

Pending turns expire after `HEADROOM_GATEWAY_TURN_TTL_SECONDS` (default `120`), and a turn re-drives at most `HEADROOM_GATEWAY_MAX_REDRIVES` times (default `8`). Hook failures end the turn with `done`, never an error. With `config.mode: "ccr"` and `can_redrive`, Headroom injects `headroom_retrieve` and answers the model's retrieval calls itself. Tool-search deferral on this path needs the licensed headroom-tool-search extension (`HEADROOM_PROXY_EXTENSIONS=tool_search`). The Kong Gateway 3.9 plugin [kong-plugin-headroom](https://github.com/headroomlabs-ai/kong-plugin-headroom) implements both halves. `HEADROOM_GATEWAY_CONTRACT=0` removes the contract, after which a `gateway` block is ignored.

## Wrap an agent

```bash
headroom wrap claude          # Claude Code
headroom wrap vscode-claude   # Claude Code extension in VS Code: configures settings, then starts the proxy
headroom wrap codex           # OpenAI Codex
headroom wrap aider           # Aider
headroom wrap cursor          # starts the proxy and prints settings to paste into Cursor
headroom wrap grok-build      # updates ~/.grok/config.toml and starts the proxy
headroom wrap antigravity     # starts the proxy and prints Antigravity setup instructions
```

- `wrap` routes the agent through the local proxy with the `coding` profile. It passes `HEADROOM_SAVINGS_PROFILE` to the proxy it starts, and may seed `HEADROOM_MODE`.
- **`wrap` can reuse a running proxy, settings and all.** Exporting different values in your shell does not change that proxy's startup-only settings. `wrap` warns when an explicit `HEADROOM_MODE`, `HEADROOM_MIN_TOKENS` or `HEADROOM_EXCLUDE_TOOLS` disagrees with the running proxy, but it never restarts a shared proxy or interrupts its clients. Restart the proxy with the settings you want, or pass `--port` for a separate instance.
- For the processes it launches, `wrap` adds `127.0.0.1,localhost,::1` to `NO_PROXY`. For Claude Code, it also sets `ENABLE_TOOL_SEARCH`.
- `wrap` registers [Serena](https://github.com/oraios/serena) as the code-memory MCP server, which runs on demand through `uvx` and indexes the project locally. For Claude Code the entry has `local` scope, so a Serena that cannot start does not break sessions in unrelated projects. Pass `--code-memory none` to skip it, or `--code-memory-scope user` (`HEADROOM_CODE_MEMORY_SCOPE=user`) to register it machine-wide. The next `wrap` or `unwrap` removes the retired `tokensave` entry.
- Apps that read their own settings get configuration help instead of an environment. Paste the printed base URL into Cursor's or Antigravity's model settings. Grok Build gets `[model.grok-build] base_url` in `~/.grok/config.toml`. The VS Code extension needs a VS Code reload after the first run and a wrapper that keeps running.
- `headroom wrap codex` passes the proxy URL as a `--config` override and never writes `~/.codex/config.toml`, so Codex runs in embedded mode without its shared background server. For persistent routing that keeps the shared server, run `headroom init codex` (this project's `.codex/config.toml`) or `headroom init -g codex` (every project). `headroom unwrap codex` removes the `-g` routing; for a project, delete the `# --- Headroom init provider ---` block. Unwrap leaves the `SessionStart` hook in Codex's `hooks.json`, which still starts a proxy. On Windows nothing starts the proxy for persistent routing, so use `headroom install apply` for a supervised proxy.

## Cloud providers

```bash
headroom proxy --backend bedrock --region us-east-1        # AWS Bedrock
headroom proxy --backend vertex_ai --region us-central1    # Google Vertex AI
headroom proxy --backend azure                              # Azure OpenAI
OPENROUTER_API_KEY=sk-or-... headroom proxy --backend openrouter   # OpenRouter (400+ models)
```

### Vertex AI

`--backend vertex_ai` delegates to LiteLLM, which brings two requirements that are easy to miss:

```bash
pip install "headroom-ai[proxy]" "google-cloud-aiplatform>=1.38"
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json  # or use Application Default Credentials
export VERTEXAI_PROJECT=<your-gcp-project>
export VERTEXAI_LOCATION=us-central1
headroom proxy --backend vertex_ai --region us-central1
```

- No Headroom extra or Docker image variant includes `google-cloud-aiplatform`. Without it, the first request fails with `No module named 'vertexai'`.
- LiteLLM reads `VERTEXAI_PROJECT` and `VERTEXAI_LOCATION`, not `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`. If `VERTEXAI_PROJECT` is unset, requests can silently resolve against your Application Default Credentials (ADC) quota project and bill a different project. Set it even when `GOOGLE_CLOUD_PROJECT` is exported.
- This backend runs Headroom as a proxy that calls Vertex through LiteLLM. It is not the LiteLLM callback integration, which adds Headroom inside your own LiteLLM app.

The native Vertex routes in the endpoint table need no backend flag. `publisher=google` (Gemini) requests get Headroom's full Gemini optimization handler. `publisher=anthropic` (Claude on Vertex) requests go through the Anthropic Messages handler and on to the regional Vertex host with the client's own Google token, so they need neither `google-cloud-aiplatform` nor `VERTEXAI_PROJECT`. The proxy page says they take the LiteLLM-Vertex path instead, but the Claude Code on Vertex AI page and the 0.40.0 source both show the direct path. A client that speaks native Vertex REST can point its endpoint at the proxy; `headroom wrap claude` uses this in Vertex mode – see [coding-agents](./coding-agents.md).

### Bedrock

| Your client sends | Use | Headroom then |
| --- | --- | --- |
| Anthropic `/v1/messages` | `--backend bedrock` | Re-signs the request and sends it to Amazon Web Services (AWS). |
| Bedrock `POST /model/{id}/invoke`, for example Claude Code with `CLAUDE_CODE_USE_BEDROCK=1` | `--bedrock-api-url` or `BEDROCK_TARGET_API_URL` | Compresses with the `/v1/messages` pipeline and forwards to a local re-signing gateway (LiteLLM, LocalStack, a corporate Bedrock proxy). |

```bash
headroom proxy --bedrock-api-url http://127.0.0.1:4000
# then point the client's Bedrock endpoint at Headroom:
AWS_ENDPOINT_URL_BEDROCK_RUNTIME=http://127.0.0.1:8787 your-bedrock-client
```

Never point `--bedrock-api-url` at raw AWS. Rewriting the body invalidates the caller's AWS Signature Version 4 (SigV4) signature, which covers a hash of the body, so AWS rejects the request with 403. For direct-to-AWS compression, use `--backend bedrock`, which re-signs.

## Deploy to production

```bash
pip install gunicorn

gunicorn "headroom.proxy.server:create_app()" \
  --workers 4 \
  --bind 0.0.0.0:8787 \
  --worker-class uvicorn.workers.UvicornWorker
# Callers must send `Authorization: Bearer replace-with-a-secret` or
# `X-Headroom-Proxy-Token: replace-with-a-secret`.
```

`headroom.proxy.server` has no module-level `app` object. It exposes a `create_app(config: ProxyConfig | None = None) -> FastAPI` factory, so the gunicorn import string must call it.

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install "headroom-ai[proxy]" \
    && apt-get purge -y build-essential && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
EXPOSE 8787
CMD ["headroom", "proxy", "--host", "0.0.0.0", "--port", "8787"]
```

```bash
docker run --rm -p 127.0.0.1:8787:8787 \
  -e HEADROOM_PROXY_TOKEN='replace-with-a-secret' \
  headroom-proxy
```

- `build-essential` is needed at install time because `headroom-ai` includes `hnswlib`, a C++ extension compiled from source. The Dockerfile purges it afterwards to keep the image slim.
- The container binds `0.0.0.0`, so it needs `HEADROOM_PROXY_TOKEN`, or `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` when the published port is loopback-only. Publish on `127.0.0.1` unless you mean to expose the port; for network access, use an intentional address and keep the token.
- In a container the operating system (OS) certificate store usually lacks a corporate root, so mount the root and set `HEADROOM_CA_BUNDLE`.
- With several workers, add `--embedding-server` to share one embedder. Pin each `/v1/compress` session or gateway turn to one process or replica, because that state is in-process.
- Use `--stateless` to keep runtime state off disk. It still writes the runtime `proxy.log`, so it does not stop every disk write – see [architecture-and-security](./architecture-and-security.md).
- Key environment variables: `HEADROOM_HOST`, `HEADROOM_PORT`, `HEADROOM_PROXY_TOKEN`, `HEADROOM_BUDGET`, `HEADROOM_WORKERS`, `HEADROOM_SAVINGS_PROFILE`, `HEADROOM_MODE`, `HEADROOM_LOG_LEVEL` and `HEADROOM_SAVINGS_PATH`.

**Telemetry and the usage beacon.** Local telemetry (`--telemetry`) is off by default and never leaves the machine. Separately, an anonymous usage beacon is on by default. When a session goes idle, it posts about 2 KB of counters and identifiers (token totals, compression ratios, skip reasons, provider names, model ids, failure counts) to a Headroom Labs collector. It never sends prompts, completions, code, file paths, file contents or environment variables, and its install id is a random UUID. Turn it off with `HEADROOM_BEACON=off`, `DO_NOT_TRACK=1` or `HEADROOM_OFFLINE=1`; the last one also turns off update checks and license reporting.

## Run behind a corporate network

Many companies route laptop traffic through a gateway that inspects TLS, such as Zscaler or Netskope. The gateway re-signs each HTTPS connection with the company's root certificate, which IT installs in the OS certificate store. Headroom trusts that same store (macOS Keychain, the Windows certificate store, the Linux system bundle) plus the public roots bundled with Python, so a managed machine usually needs no configuration.

```bash
headroom doctor --network
headroom doctor --network --network-url https://your-gateway.example.com/v1/models   # also test a custom upstream
```

For each endpoint, the check prints who signed the presented certificate (for example `Zscaler Intermediate Root CA`), whether Headroom trusts it, and whether a gateway block page came back instead of the service. If anything fails, the last row is a short request that you can send to IT as-is.

### Fix an untrusted certificate

The error names the host and the issuer, for example a certificate for `api.anthropic.com` issued by Zscaler. Pick one fix:

1. Ask IT to deploy the corporate root to the OS certificate store, for example with Zscaler Client Connector ("Install Zscaler SSL Certificate") or a mobile device management (MDM) profile. Nothing else changes.
2. Export the corporate root as a Privacy-Enhanced Mail (PEM) file and set `HEADROOM_CA_BUNDLE=/path/to/company-root.pem`. If you already set `NODE_EXTRA_CA_CERTS` for Claude Code, Headroom picks that up too.
3. Ask IT to exempt the provider domains from inspection.

| Do | Don't |
| --- | --- |
| Add the corporate root through the OS certificate store or `HEADROOM_CA_BUNDLE`; both add to the trusted set. | Turn certificate checking off. Headroom has no switch for that, on purpose. |
| Use `SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` only with a complete bundle. | Point them at the corporate root alone: they replace every other trust source. |
| Ask IT to trust the corporate root. | Ask IT to exempt `python` as a process: that exempts every Python program on the machine. |

| Variable | Default | Effect |
| --- | --- | --- |
| `HEADROOM_CERT_STORE` | `system,bundled` | Trusted roots: `system` is the OS certificate store, `bundled` is certifi's public roots. `bundled` alone restores the old public-roots-only behavior. Mirrors Claude Code's `CLAUDE_CODE_CERT_STORE`. |
| `HEADROOM_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` | unset | Extra PEM roots, added to the above. |
| `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` | unset | Replace every other source. |
| `HEADROOM_TLS_STRICT` | strict | `0` relaxes OpenSSL's Request for Comments (RFC) 5280 strict checks on the bundled path. Not needed with the OS certificate store. |

The trust policy covers the proxy's HTTP and WebSocket upstreams, GitHub Copilot sign-in, and model and tokenizer downloads from Python. The Rust proxy binary `headroom-proxy` (used in the Docker image) trusts Mozilla's roots plus the OS certificate store, and adds `HEADROOM_CA_BUNDLE` or `NODE_EXTRA_CA_CERTS` for HTTP upstreams. One gap remains: the embedding model that the Rust core downloads for relevance scoring trusts Mozilla's roots only. Behind inspection that download fails and Headroom falls back to BM25 scoring; set `HF_ENDPOINT` or pre-populate the cache to keep embeddings.

### Explicit HTTP proxies and PAC files

If the company sets `HTTPS_PROXY` or a proxy auto-config (PAC) file, Headroom's upstream calls go through that proxy. The agent's calls to Headroom must not, because they target `127.0.0.1`, which the corporate proxy cannot reach. `headroom wrap` handles this for the processes it launches. If you start the agent yourself, run:

```bash
export NO_PROXY="$NO_PROXY,127.0.0.1,localhost,::1"
```

Python does not evaluate PAC files, so export the proxy that the PAC file resolves to as `HTTPS_PROXY`.

When only provider traffic should go through a proxy, use `headroom proxy --http-proxy http://proxy.internal:8080` or `HEADROOM_HTTP_PROXY`; HTTPS provider APIs go through it with CONNECT. Don't set process-wide `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` or `NO_PROXY` for that purpose, because Headroom passes them into tool executions and unrelated tool traffic ends up proxied.

### What to ask IT for

| Domain | Used for | Required |
| --- | --- | --- |
| `api.anthropic.com` | Claude, Claude Code | yes, for Anthropic |
| `api.openai.com`, `chatgpt.com` | OpenAI API, Codex | yes, for OpenAI and Codex |
| `api.githubcopilot.com`, `api.github.com` | GitHub Copilot | for Copilot |
| `huggingface.co`, `cdn-lfs.hf.co`, `cas-bridge.xethub.hf.co` | Compression models, downloaded once | recommended |
| `openaipublic.blob.core.windows.net` | Tokenizer vocabulary, downloaded once | recommended |

- Deploy the inspection root to the OS certificate store. That is enough for Headroom; no per-app certificate work is needed.
- Do not route these domains to "Caution" or "Isolate". An API client cannot click through an interstitial page, so it receives HTML where it expects JSON.
- If streams stall or arrive in bursts, exempt the provider domains from inspection or data loss prevention (DLP) buffering. Some gateways buffer server-sent events while they inspect them.
- Anthropic tenant restrictions need inspection of `api.anthropic.com` to stay on. That works with Headroom as long as the corporate root is trusted.

If `huggingface.co` stays blocked, Headroom degrades instead of failing: it uses rule-based compression without the compression model, and estimates token counts without the tokenizer vocabulary. To keep ML compression, point Headroom at an internal Hugging Face mirror such as Artifactory or Nexus, or pre-populate `~/.cache/huggingface` from a machine with access:

```bash
export HF_ENDPOINT=https://artifactory.example.com/api/huggingface/huggingface
```

## Benchmark local LLM prefill

Local models do not charge per token, but they still process every prompt token during prefill, and long coding-agent sessions on Apple Silicon often bottleneck there rather than on generation. Headroom reduces how much prompt the local server processes. Measure it as an A/B comparison on the dashboard, against a local OpenAI-compatible server on `http://127.0.0.1:8000`: MLX/OMLX, vLLM, LM Studio, Ollama's OpenAI-compatible endpoint, or any server that accepts `/v1/chat/completions` or `/v1/responses`.

```bash
# 1. Baseline in passthrough mode
headroom proxy --port 8787 --openai-api-url http://127.0.0.1:8000 --no-optimize

# Point the agent at Headroom, not at the local server
export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
export OPENAI_API_KEY=local

# Watch the session (or open http://127.0.0.1:8787/dashboard)
headroom dashboard --port 8787 --no-open

# 2. Reset the task. 3. Optimized run: the same command without --no-optimize
headroom proxy --port 8787 --openai-api-url http://127.0.0.1:8000

# Optional separate condition: traffic learning (implies memory)
headroom proxy --port 8787 --openai-api-url http://127.0.0.1:8000 --learn
```

- Pick a realistic task. A coding-agent refactor works well, because it produces repeated file reads, tool results, lint and test output, and a growing context. In passthrough mode the before and after counts match; record them as the baseline.
- Reset between runs: revert the first run's changes (a clean git worktree is the easiest reset point), start a fresh agent session, and keep the model, server, prompt and unrelated flags the same. Do not compare a cold first run with a warmed second run. Compare passthrough, optimized and optimized-with-learning runs independently, with the dashboard token counts as the primary measurement.
- The savings percentage is the prompt-token reduction sent to the local model. It does not make the prefill kernel faster; it gives the kernel less prompt to process. For hosted APIs, fewer input tokens mean lower cost and latency; for local models, they mean less prefill work and lower memory pressure.
- Long agent sessions gain more than short chat turns, because repeated file reads, tool outputs and logs are compressible. Expect smaller savings on short natural-language turns.
- Report the local server, model and quantization, hardware, agent or client, task, baseline and optimized token totals, the savings percentage, and flags such as `--learn` or `--memory`.

## Quick troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| The proxy refuses to start on `--host 0.0.0.0` | No proxy token | Set `HEADROOM_PROXY_TOKEN`, or `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` behind a loopback-only publish. |
| A gateway gets `404` from `/v1/compress` | Loopback-only route | Set `HEADROOM_COMPRESS_ALLOW_REMOTE=1` and keep the token. |
| Cache reads drop after you add `/v1/compress` | Pristine originals recompressed each turn | Use `frozen_message_count` with your forwarded output, or `config.session_id`. |
| `wrap` ignores your new settings | It reused a running proxy | Restart that proxy, or `wrap` with `--port`. |
| A token-mode profile still behaves like cache mode | Unknown name fell back to `coding`, or no explicit mode | Check the startup warning, and pass `--mode token`. |
| TLS error naming Zscaler or another issuer | Corporate root not trusted | Use the OS certificate store or `HEADROOM_CA_BUNDLE`; run `headroom doctor --network`. |
| The agent cannot reach Headroom behind a corporate proxy | Loopback calls go to the corporate proxy | Add `127.0.0.1,localhost,::1` to `NO_PROXY`. |
| Bedrock returns 403 | `--bedrock-api-url` points at raw AWS | Point it at a re-signing gateway, or use `--backend bedrock`. |
| Vertex bills the wrong project | `VERTEXAI_PROJECT` unset | Set `VERTEXAI_PROJECT` and `VERTEXAI_LOCATION`. |

## Related skills

- [getting-started](./getting-started.md) – installation, the Docker-native wrapper, and persistent installs such as a supervised proxy.
- [compression](./compression.md) – what ContentRouter, SmartCrusher, Kompress and the other compressors do with the traffic the proxy routes.
- [ccr-and-caching](./ccr-and-caching.md) – reversible compression, `headroom_retrieve`, and the prefix-cache optimization behind cache mode.
- [memory](./memory.md) – what `--memory` and `--learn` store and inject.
- [framework-integrations](./framework-integrations.md) – SDK and framework clients that point at the proxy or call `/v1/compress`, including the LiteLLM integration.
- [coding-agents](./coding-agents.md) – each `headroom wrap` target in depth, Claude Code on Vertex AI, MCP tools and Codex recovery.
- [configuration](./configuration.md) – the full environment-variable reference, cost-aware model routing, pipeline extensions and the filesystem contract.
- [observability](./observability.md) – `/stats`, `/metrics`, Prometheus, Grafana and the dashboard.
- [sdk-reference](./sdk-reference.md) – Python and TypeScript APIs, including the TypeScript SDK that calls `/v1/compress`.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – fixes by symptom, including why the Unix socket route does not restore Remote Control.
- [architecture-and-security](./architecture-and-security.md) – the security model and rollout channels (`HEADROOM_ROLLOUT_CHANNEL`).

## Source pages

- https://docs.headroomlabs.ai/docs/proxy
- https://docs.headroomlabs.ai/docs/corporate-networks
- https://docs.headroomlabs.ai/docs/local-llm-prefill
