# Headroom: Configuration
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill when you configure the Headroom software development kit (SDK) or the proxy and its command-line interface (CLI), override settings per request, describe custom models, extend the request pipeline, relocate files on disk, or authenticate to an OAuth2-protected upstream.

## Core concepts

- **Two separate mode axes.** SDK modes (`audit`, `optimize`, `simulate`) decide whether the SDK changes a request. The proxy `--mode` (`cache`, `token`) trades compression against prefix-cache stability. Neither accepts the other's values.
- **Two filesystem roots.** `HEADROOM_CONFIG_DIR` holds configuration you write. `HEADROOM_WORKSPACE_DIR` holds state that Headroom writes.
- **Model metadata lookup.** Headroom resolves context limits and prices from your configuration, a built-in table, and the installed LiteLLM model database. Configure only the models it cannot look up.
- **Two extension seams.** `headroom.pipeline_extension` entry points hook lifecycle events in both the SDK and the proxy. `headroom.proxy_extension` entry points, such as `headroom-oauth2`, plug into the proxy.
- **Opt-in extras.** Cost-aware model routing, reasoning compaction, cold-prefix recompaction, and cache time to live (TTL) learning are off by default. The base proxy behaves the same until you opt in.

## Configuration precedence

You configure Headroom in four layers. Each later layer overrides the earlier ones:

1. Default values
2. Environment variables
3. SDK constructor arguments
4. Per-request overrides

Some resources have their own resolution chain. In each chain, the first match wins.

| Resource | Resolution order |
| --- | --- |
| On-disk paths (savings ledger, TOIN telemetry, subscription state) | explicit argument → per-resource env var → path derived from the canonical root → default |
| `models.json` (Python providers) | `${HEADROOM_CONFIG_DIR}/models.json` → `${HEADROOM_WORKSPACE_DIR}/models.json` (legacy) |
| Context limits | your configuration and the built-in table, merged (exact match, then partial or prefix match) → LiteLLM `max_input_tokens` → pattern inference → generic default |
| Pricing | your configuration → LiteLLM → built-in table → pattern inference → generic default |
| Model for `headroom wrap claude --1m` | `--model` or `ANTHROPIC_MODEL` → `HEADROOM_1M_MODEL` → built-in default `claude-opus-5` |
| Rollout features | `HEADROOM_DISABLE_FEATURES` wins over every enable path |

## SDK modes versus proxy mode

| Axis | Values | Set with |
| --- | --- | --- |
| SDK mode | `audit` observes and logs without changes (monitoring, baselines). `optimize` applies safe, deterministic transforms (production). `simulate` returns the plan without an API call (testing, cost estimates). | `HeadroomClient(default_mode=...)`, or `headroom_mode=...` per request |
| Proxy mode | `cache` (default) freezes prior turns so the provider prefix cache is never busted. `token` maximizes visible per-request compression at the cost of cache stability. The configuration page says to prefer `cache` unless you are diagnosing compression numbers; the token-mode savings profiles in [proxy](./proxy.md) target non-coding workloads. | `headroom proxy --mode`, or `HEADROOM_MODE` |

```bash
headroom proxy --mode cache      # do this: cache stability is where agent-workload savings come from
headroom proxy --mode optimize   # don't do this: the proxy does not accept audit, optimize, or simulate
```

## SDK configuration

```python
from headroom import HeadroomClient, OpenAIProvider
from openai import OpenAI

client = HeadroomClient(
    original_client=OpenAI(),
    provider=OpenAIProvider(),
    default_mode="optimize",        # "audit" observes only
    enable_cache_optimizer=True,    # provider-specific cache optimization
    enable_semantic_cache=False,    # query-level semantic caching
    model_context_limits={"gpt-4o": 128000, "gpt-4o-mini": 128000},
    # store_url="sqlite:////absolute/path/to/headroom.db",  # defaults to a temp directory
)
```

```typescript
import { HeadroomClient } from 'headroom-ai';

const client = new HeadroomClient(); // reads HEADROOM_BASE_URL and HEADROOM_API_KEY

const explicit = new HeadroomClient({
  baseUrl: 'http://localhost:8787', apiKey: 'your-api-key', timeout: 30_000, fallback: true, retries: 2,
});
```

- The Python client wraps your provider client (`original_client`) and takes a provider object. The TypeScript client talks to a Headroom proxy at `baseUrl`, which defaults to `http://localhost:8787` through `HEADROOM_BASE_URL`. `HEADROOM_API_KEY` is an optional key for authenticated Headroom endpoints.
- `store_url` defaults to a temp directory. Set an absolute SQLite URL (four slashes) when you want the database at a known path.

## Per-request overrides

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    headroom_mode="audit",               # override default_mode for this request
    headroom_output_buffer_tokens=8000,  # reserve more tokens for output
)
```

```typescript
import { compress } from 'headroom-ai';

const result = await compress(messages, { model: 'gpt-4o', tokenBudget: 100_000, timeout: 15_000 });
```

The configuration page also shows `headroom_keep_turns` and `headroom_tool_profiles` as per-request overrides. Don't rely on either. The context-management and errors pages say the client accepts them without effect, and in the 0.40.0 source no transform reads them. For turn protection, use `CompressConfig.protect_recent` with `compress()`. To keep one tool's output intact in the proxy, use `--protect-tool-results` – see [proxy](./proxy.md).

### Context window management

Context management is automatic: the pipeline compresses only the live zone. You reserve room for the answer per request with `headroom_output_buffer_tokens`. Don't import `RollingWindowConfig`, `IntelligentContextConfig`, or `ScoringWeights`, because these classes are no longer part of Headroom.

## SmartCrusher and CacheAligner

The configuration page shows how to build `SmartCrusherConfig` and `CacheAlignerConfig`, not how to attach them to a client. See [compression](./compression.md) and [ccr-and-caching](./ccr-and-caching.md) for the components themselves.

`SmartCrusherConfig` tunes JSON compression. The docs show these values as an example and do not mark them as defaults.

```python
from headroom.transforms import SmartCrusherConfig

config = SmartCrusherConfig(
    max_items_after_crush=15,  # maximum items to keep after compression
    min_tokens_to_crush=200,   # minimum tokens before compression applies
    first_fraction=0.3,        # fraction of items always kept from the start
    last_fraction=0.15,        # fraction of items always kept from the end
    variance_threshold=2.0,    # variance threshold for statistical analysis
)
```

`CacheAlignerConfig` configures CacheAligner, which detects dynamic content in the prompt prefix. The configuration page calls this prefix stabilization, but the more specific cache-optimization page says CacheAligner only reports drift and never rewrites messages – see [ccr-and-caching](./ccr-and-caching.md). `date_patterns` take effect only with `use_dynamic_detector=False`, which replaces the built-in dynamic-content detector with your regexes.

```python
from headroom import CacheAlignerConfig

config = CacheAlignerConfig(
    enabled=True,
    use_dynamic_detector=False,  # activates date_patterns
    date_patterns=[r"Today is \w+ \d+, \d{4}", r"Current time: .*"],
)
```

## Provider-specific settings

Provider classes configure token counting and context or pricing overrides, not caching. `enable_cache_optimizer` on `HeadroomClient` picks the cache strategy from the provider you pass: Anthropic `cache_control` breakpoints, OpenAI prefix stabilization, or Google `CachedContent`.

```python
from anthropic import Anthropic
from headroom import AnthropicProvider, OpenAIProvider
from headroom.providers import GoogleProvider

openai_provider = OpenAIProvider(context_limits={"gpt-4o": 128000})
anthropic_provider = AnthropicProvider(client=Anthropic())  # optional client: accurate counts via the Token Count API
google_provider = GoogleProvider()  # estimation; a configured google.generativeai module enables countTokens
```

## Custom model configuration

Configure only models Headroom cannot look up: fine-tunes, private deployments, and gateway aliases. Public models resolve from LiteLLM, so pinning one means you maintain a number that would otherwise stay current on its own.

```json
{
  "anthropic": {
    "context_limits": {"claude-4-opus-20250301": 200000, "claude-custom-finetune": 128000},
    "pricing": {"claude-4-opus-20250301": {"input": 15.00, "output": 75.00, "cached_input": 1.50}}
  },
  "openai": {
    "context_limits": {"ft:gpt-4o:my-org": 128000, "my-private-deployment": 200000},
    "pricing": {"my-private-deployment": [5.00, 15.00]}
  }
}
```

- Save it as `${HEADROOM_CONFIG_DIR}/models.json` (default `~/.headroom/config/models.json`). To override the content, set `HEADROOM_MODEL_LIMITS` to a JSON string or a file path.
- The legacy `~/.headroom/models.json` still works, because the Python providers fall back to `${HEADROOM_WORKSPACE_DIR}/models.json`. Put new files in the config root.
- A pricing entry is an object with `input`, `output`, and `cached_input` keys, or a two-number array such as `[5.00, 15.00]`. In code, set limits with `model_context_limits` on `HeadroomClient` or `context_limits` on `OpenAIProvider`.

### How Headroom resolves limits and prices

- **Source.** Headroom reads the installed LiteLLM model database (`litellm.model_cost`). The data ships with the LiteLLM package, so it is as current as your LiteLLM version. Upgrade LiteLLM to refresh it. No lookup makes a network call.
- **Deliberate asymmetry.** For limits, the built-in table outranks LiteLLM, because LiteLLM reports a model's maximum capability while Headroom needs its effective default. Example: LiteLLM reports 1,000,000 for `claude-sonnet-4-20250514`, but that window is an opt-in beta, so the built-in 200,000 is the safe assumption. Pricing has no such split, so LiteLLM beats the built-in table there. Your own configuration beats LiteLLM in both chains.
- **Input budget, not total window.** Limits mean `max_input_tokens`: `gpt-5` resolves to 272K input, not the 400K total (272K in + 128K out).
- **Gateway names.** LiteLLM also resolves `azure/...`, `bedrock/...`, `vertex_ai/...`, and `groq/...` names, which the built-in tables never covered.
- **No LiteLLM.** The LiteLLM dependency is gated `python_version < '3.14'`. The built-in tables cover installs where LiteLLM is unavailable.

Models that neither the tables nor LiteLLM match fall through to pattern inference. The most specific prefix wins, so `gpt-4.1` is not treated as `gpt-4`, which would mean an 8K limit and legacy pricing.

| Pattern | Inferred settings |
| --- | --- |
| `*opus*`, `*sonnet*`, `*haiku*` | 200K context, matching tier pricing |
| `gpt-4o*` | 128K context, GPT-4o pricing |
| `gpt-4.1*` | ~1M context, GPT-4.1 pricing |
| `gpt-5*` | 272K input, GPT-5 pricing |
| `o1*`, `o3*`, `o4*` | 200K context, reasoning model pricing |

## Validation

Validate your configuration at startup, so a broken provider, storage, or cache setup surfaces before the first real request.

```python
result = client.validate_setup()

if not result["valid"]:
    print("Configuration issues:")
    for check in ("provider", "storage", "config", "cache_optimizer"):
        if result[check]["error"]:
            print(f"  - {check}: {result[check]['error']}")
```

## Proxy configuration

```bash
headroom proxy --port 8787 --host 127.0.0.1 --mode cache --budget 10.00 --log-file headroom.jsonl
headroom proxy --no-optimize              # disable optimization (passthrough mode)
headroom proxy --no-cache                 # disable semantic caching
headroom proxy --memory                   # enable memory
headroom proxy --learn --min-evidence 3   # enable live learning
```

`--budget` sets a daily limit in US dollars. See [proxy](./proxy.md) for every CLI flag and endpoint.

### Environment variables you need most

The full table is at https://docs.headroomlabs.ai/docs/configuration. Rows that say "Rust proxy" apply to the Rust transparent proxy, not the Python proxy.

| Variable | Default | Purpose |
| --- | --- | --- |
| **Server and networking** | | |
| `HEADROOM_HOST` / `HEADROOM_PORT` | `127.0.0.1` / `8787` | Proxy bind host and port |
| `HEADROOM_MODE` | `cache` | `token` or `cache` |
| `HEADROOM_WORKERS` | `1` | Uvicorn worker count |
| `HEADROOM_LIMIT_CONCURRENCY` | `1000` | Concurrent connections before the proxy returns 503 |
| `HEADROOM_MAX_CONNECTIONS` / `HEADROOM_MAX_KEEPALIVE` / `HEADROOM_KEEPALIVE_EXPIRY` | `500` / `100` / `90` | Maximum upstream connections, maximum keep-alive connections, and seconds an idle keep-alive connection stays open |
| `HEADROOM_REQUEST_TIMEOUT` | `300` | Request timeout in seconds |
| `HEADROOM_HTTP_PROXY` | – | HTTP proxy for upstream provider requests only (HTTPS provider APIs use CONNECT) |
| `HEADROOM_BUDGET` | – | Daily budget limit in US dollars |
| **Storage, state, and telemetry** | | |
| `HEADROOM_CONFIG_DIR` / `HEADROOM_WORKSPACE_DIR` | `~/.headroom/config` / `~/.headroom` | Config root (read-mostly) and state root (read-write) |
| `HEADROOM_SAVINGS_PATH`, `HEADROOM_TOIN_PATH`, `HEADROOM_SUBSCRIPTION_STATE_PATH` | derived from the workspace root | Per-file overrides that always win when set |
| `HEADROOM_MODEL_LIMITS` | – | Custom model config (JSON string or file path) |
| `HEADROOM_STATELESS` | `false` | `true` disables filesystem writes, except the runtime `proxy.log` |
| `HEADROOM_TELEMETRY` | `off` | `on` records local-only usage stats for your own `/stats` and dashboard. Nothing is sent externally. |
| **Compression and machine learning (ML) runtimes** | | |
| `HEADROOM_LOSSLESS_COMPACTION` | `1` | `0` disables the byte-reversible lossless folds and keeps the rest of the pipeline. Read per request, so `/admin/runtime-env` hot-sync applies without a restart. |
| `HEADROOM_LIVE_ZONE_DISABLE_ARMS` | – | Rust proxy: comma-separated content types whose compression arm becomes a no-op, for example `source_code,plain_text`. Read once per process. Unknown names are logged and ignored. |
| `HEADROOM_MEMORY_INJECTION_MODE` | `live_zone_tail` | `live_zone_tail` or `disabled`. The retired `system_prompt` value raises. |
| `HEADROOM_KOMPRESS_BACKEND` | `auto` | `auto` tries ONNX on the CPU, then PyTorch. Also `onnx`/`onnx_cpu`, `onnx_coreml`, `pytorch`, `pytorch_mps`. |
| `HEADROOM_KOMPRESS_ENDPOINT` / `HEADROOM_KOMPRESS_ENDPOINT_TOKEN` | – | Offload Kompress to a remote endpoint instead of the local ONNX model |
| `ORT_DYLIB_PATH` | auto-pinned | ONNX Runtime library for the Rust core. Set it to override the pin made at `import headroom`. |
| **Cache stability and header hygiene** | | |
| `HEADROOM_BETA_HEADER_STICKY` / `HEADROOM_PROXY_BETA_HEADER_STICKY` | `enabled` | Re-inject beta tokens within a session (Python proxy / Rust proxy). The Rust flag needs `HEADROOM_PROXY_COMPRESSION=1`. |
| `HEADROOM_STRIP_INTERNAL_HEADERS` / `HEADROOM_PROXY_STRIP_INTERNAL_HEADERS` | `enabled` | Strip `x-headroom-*` request headers before forwarding (Python proxy / Rust proxy) |
| `HEADROOM_PROXY_PYTHON_FORWARDER_MODE` | `byte_faithful` | Forwards the original bytes when no transform changed the body, which keeps Anthropic prompt-cache hits intact |
| `HEADROOM_UPSTREAM_ALLOWED_HOSTS` | – | Extra hosts that may receive configured secret headers |
| `HEADROOM_ALLOWED_BASE_URLS` | – | Client-chosen upstreams admitted by name through an outbound proxy |

`disabled` for the strip flags and `legacy_json_kwarg` for the forwarder mode are explicit operator opt-ins for diagnostics or emergency rollback. They are not fallbacks.

```bash
export HEADROOM_HTTP_PROXY="http://<proxy-host>:<port>"   # do this: provider requests only
export HTTPS_PROXY="http://<proxy-host>:<port>"           # don't do this for provider-only proxying
```

Prefer `HEADROOM_HTTP_PROXY`, because Headroom passes the process-wide `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY` through to tool executions. The first three also make the proxy refuse `x-headroom-base-url` requests that would route through them (see below).

### Internal request headers

| Header | Effect |
| --- | --- |
| `x-headroom-base-url` | Routes this request to another upstream base |
| `x-headroom-session-id` | Sets the session key for beta header tracking |
| `x-headroom-bypass: true` or `x-headroom-mode: passthrough` | Byte-faithful passthrough, which model routing skips |
| `x-headroom-user-id` | Memory user-id resolution |

By default, the proxy strips `x-headroom-*` request headers before forwarding, to stop fingerprinting and leakage. It still reads them on the inbound side.

## Per-request routing

| Need | Use |
| --- | --- |
| The client picks a different upstream base for one request | `x-headroom-base-url` header |
| An extension picks the model for one request | `request.state.headroom_route` |
| Rules move small requests to a cheaper model | `HEADROOM_MODEL_ROUTER_ENABLED` and `HEADROOM_MODEL_ROUTES` |
| The upstream rejects payloads that follow the spec | A `PRE_SEND` pipeline extension, plus the header if the base also varies |

### Upstream override with `x-headroom-base-url`

The header lets one Headroom instance send different models to different upstream bases, instead of one global `OPENAI_API_URL` or `OPENAI_TARGET_API_URL` per proxy process. The OpenAI-compatible routes (`/v1/chat/completions`, `/v1/responses`), the Anthropic Messages route (`POST /v1/messages`), and the generic passthrough route honor it. The proxy forwards to the header value plus the original request path, so pass the base only. An empty or whitespace-only value is ignored.

```bash
# Anthropic Messages gateway (OpenCode Zen): forwarded to https://opencode.ai/zen/go/v1/messages
curl http://127.0.0.1:8787/v1/messages \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-headroom-base-url: https://opencode.ai/zen/go" \
  -H "x-api-key: <gateway-api-key>" \
  -d '{"model":"glm-5.2","max_tokens":16,"messages":[{"role":"user","content":"hi"}]}'
```

**Secret headers go only to designated hosts.** `OPENAI_TARGET_API_HEADERS` and `ANTHROPIC_TARGET_API_HEADERS` hold operator secrets, and the client chooses the header value. So the proxy attaches those headers only for a configured provider target (`ANTHROPIC_TARGET_API_URL`, `OPENAI_TARGET_API_URL`, and the Gemini, Vertex, and Cloud Code equivalents) or a host in `HEADROOM_UPSTREAM_ALLOWED_HOSTS`. Other upstreams still receive the request, without those headers, and the proxy logs `upstream_extra_headers_withheld host=<host>` once per host. To send your headers to a gateway, list its host: `export HEADROOM_UPSTREAM_ALLOWED_HOSTS="gateway.internal,api.example-gateway.ai"`. Matching is exact on the parsed hostname, with no wildcards. So `api.anthropic.com.evil.example` and `https://api.anthropic.com@evil.example` do not match `api.anthropic.com`.

**Outbound proxies block client-chosen upstreams.** The proxy resolves the hostname, rejects non-public addresses, and dials the address it validated, which defeats Domain Name System (DNS) rebinding. An outbound HTTP or SOCKS proxy (`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`) resolves the name itself, so Headroom refuses an `x-headroom-base-url` request that would go through one. Operator-configured provider URLs are unaffected. To admit a destination anyway, name it in `HEADROOM_ALLOWED_BASE_URLS`. The trade-off: this also turns off the resolve-and-pin check for that destination.

### Extension-chosen model with `request.state.headroom_route`

Use this when an extension, not the caller, picks the model for a turn, such as a router that picks a cheaper model.

```python
from types import SimpleNamespace

# middleware or an extension holding the request
request.state.headroom_route = SimpleNamespace(
    model="moonshot/kimi-k2",   # required
    provider="moonshot",        # optional; inferred from the model id if absent
    reason="cheaper at this prefix length",
)
```

- **Absent means unchanged.** Missing or malformed advice, an unknown provider, or a backend that fails to build leaves the request on its original path. A routing preference never takes traffic down.
- **Duck-typed.** The extension does not import Headroom to publish advice.
- **Native versus foreign.** For a native provider (`anthropic`), rewrite `body["model"]` yourself. A foreign provider goes through a `LiteLLMBackend` built for it, and Headroom writes the model id. Backends are built once per provider and cached, and a provider that fails to build is not retried per request.
- **Routes.** Honored on `/v1/messages` and `/v1/chat/completions`, streaming and non-streaming, but not on the Responses API. The contract lives in `headroom/proxy/route_advice.py`, and `routemegood` is the reference consumer.

### Cost-aware model routing

The router rewrites the upstream model per request, for example sending small, tool-free requests to a cheaper model. Set `HEADROOM_MODEL_ROUTER_ENABLED` to `1`, `true`, `yes`, `on`, or `enabled`, and declare ordered rules in `HEADROOM_MODEL_ROUTES`. The first rule whose conditions all match wins, and every decision is logged with a reason.

| Rule field | Meaning |
| --- | --- |
| `to_model` | Required. Target model when the rule matches. |
| `max_input_tokens` / `min_input_tokens` | Estimated input size at or below / at or above this |
| `max_output_tokens` | Request `max_tokens` at or below this. A request without `max_tokens` does not match. |
| `require_no_tools` | Match only requests that declare no tools |
| `from_models` | Restrict to these source models. Omit for any model. |
| `name` | Label in the decision log |

```bash
export HEADROOM_MODEL_ROUTER_ENABLED=1
export HEADROOM_MODEL_ROUTES='[
  {"name": "small-no-tools", "max_input_tokens": 4000, "require_no_tools": true,
   "from_models": ["claude-sonnet-4-6"], "to_model": "claude-haiku-4-5"}
]'
```

- Combine `max_input_tokens` with `max_output_tokens` to downshift only turns that are cheap on both sides. A tiny prompt that asks for a long answer stays on the original model.
- Input size is a fast, tokenizer-free estimate over messages, tools, and the top-level `system` prompt. It is meant for tier selection, not exact accounting.
- A malformed rule fails open: Headroom skips it, never widens it, and applies the remaining rules. Byte-faithful passthrough requests are never model-rewritten. Routing currently applies on the Anthropic `/v1/messages` path.

## Cache stability settings

### Session beta header tracking

The proxy keeps a per-session union of `anthropic-beta` and `OpenAI-Beta` tokens in `SessionBetaTracker`. The session key comes from the `x-headroom-session-id` header, or else from `md5(model + system_prompt[:500])[:16]`.

- **Why.** Clients such as Claude Code and Codex CLI can drop a beta token between turns. The beta header is part of the prefix-cache key, so a dropped token busts the cache mid-conversation. The tracker re-injects tokens seen earlier in the session.
- **Trade-off.** After the proxy sees a token in a session, it keeps sending it for the rest of that session. Removing the token on the client does not stop it.

```bash
export HEADROOM_BETA_HEADER_STICKY=disabled   # forward the client's anthropic-beta value verbatim
```

Disabling sticky mode can lower prefix-cache hit rates for clients that drop and re-add beta tokens. Any value other than `enabled` or `disabled` raises at request time. The Rust proxy keys sessions per conversation, so parallel conversations never inherit each other's tokens.

### Cold-prefix hook and reasoning compaction

These flags target tokens that agent harnesses re-send every turn. All are off by default.

| Goal | Set | Notes |
| --- | --- | --- |
| Shrink Kimi, GLM, or DeepSeek reasoning re-sent each turn | `HEADROOM_THINKING_COMPACT=1`, plus `HEADROOM_KOMPRESS_ENDPOINT` for the best ratio | Warm turns compress reasoning with Kompress, cold turns drop it. No-op for Claude, Codex, and OpenAI, whose reasoning is an encrypted handle. `HEADROOM_THINKING_COMPACT_KEEP_LAST` (default `1`) leaves the latest turns intact. |
| Recompact a dead-cache prefix instead of re-sending it whole | `HEADROOM_COLD_RECOMPACT=1`, plus `HEADROOM_DEDUPE=1` | Fires only when the cache has lapsed. Works in `cache` and `token` mode. |
| Learn each provider's real cache TTL | `HEADROOM_CACHE_TTL_LEARN=1`, then run `headroom-cache-ttl` periodically | Observation-only. Respects `HEADROOM_STATELESS`. The log is size-bounded. |

A wrong "cold" verdict recompacts a warm prefix and busts the cache, so the TTL must be right. For Claude Code, Headroom reads the TTL exactly from `cache_control.ttl` and from `ENABLE_PROMPT_CACHING_1H`, `FORCE_PROMPT_CACHING_5M`, and `DISABLE_PROMPT_CACHING` (plus `DISABLE_PROMPT_CACHING_<FAMILY>`). With caching disabled, every turn is a free recompaction candidate. Kimi, OpenAI, and Codex expose no TTL, so detection uses a conservative default until the learner has data.

```bash
headroom-cache-ttl            # reads cache_ttl_observations.jsonl, writes cache_ttl_learned.json
headroom-cache-ttl --dry-run  # print the estimate table without writing
```

- Run the estimator from cron or launchd. It runs out-of-process by design, so it never touches the request path. The proxy picks up a rewritten table by modification time, without a restart.
- It writes the upper end of each bounded interval, because overestimating a TTL only skips a recompaction, while underestimating busts a warm cache. It never pools estimates across models.
- Keep `HEADROOM_THINKING_COMPACT` a deliberate choice: it rewrites reasoning the model actively uses and depends on Kompress, so it costs quality and latency. Keep `HEADROOM_COLD_RECOMPACT` opt-in for Kimi and OpenAI until the learner has data. `HEADROOM_CACHE_TTL_LEARN` is the safest of the three to turn on.

### Claude 1M context window

`headroom wrap claude --1m` selects a `[1m]`-suffixed model id, so Claude Code sends the `context-1m` beta header. Set `HEADROOM_1M_MODEL` to target a model without pinning `ANTHROPIC_MODEL` globally, so the default can follow a new Opus generation without a code change.

```bash
export HEADROOM_1M_MODEL=claude-opus-5            # accepted with or without the [1m] suffix
headroom wrap claude --1m
headroom wrap vscode-claude --1m                  # VS Code: writes Claude Code's model setting, reversibly
headroom wrap vscode-claude --no-configure --1m   # print the setting without writing either file
headroom unwrap vscode-claude                     # restore the model and proxy environment values
```

For the VS Code extension, use `headroom wrap vscode-claude --1m` instead of `ANTHROPIC_MODEL`, because the extension uses its own persisted `model` setting. Running the wrap command without `--1m` restores a model that Headroom managed. Headroom's local tests prove settings persistence and restoration, not a 1M window on your account: Claude Code and Anthropic own model support and account eligibility.

## Pipeline extensions

A pipeline extension hooks lifecycle events without forking Headroom. It can mutate `messages`, `tools`, `headers`, or `metadata` in place. The SDK client and the proxy dispatch the same events, so one extension covers both deployments.

| Stage | When |
| --- | --- |
| `SETUP`, `PRE_START`, `POST_START`, then `INPUT_RECEIVED` | Process and pipeline startup, then raw request accepted |
| `INPUT_CACHED`, `INPUT_ROUTED`, `INPUT_COMPRESSED`, `INPUT_REMEMBERED` | Cache, routing, compression, and memory stages |
| `PRE_SEND` | Last hook before the request goes upstream |
| `POST_SEND`, `RESPONSE_RECEIVED` | After forwarding and on response |
| `OUTCOME_OBSERVED` | Read-only `OutcomeSnapshot` (tokens, stop reason, transforms applied) after the response is processed |

Normalize at `PRE_SEND`. Compression and caching are done by then, so what you write into `event.messages` is exactly what the provider receives. At earlier stages, those steps have not run yet.

Example: an OpenAI-compatible gateway returns `400 "Message content is null"` for assistant messages that carry `content: null` with `tool_calls`. The OpenAI spec produces that shape, and the provider's workaround is `content: ""`.

```python
# my_headroom_ext/normalize.py
from headroom.pipeline import PipelineEvent, PipelineStage


class NullContentNormalizer:
    """Rewrite `content: null` + tool_calls to `content: ""` before send."""

    def on_pipeline_event(self, event: PipelineEvent) -> PipelineEvent | None:
        if event.stage is not PipelineStage.PRE_SEND or not event.messages:
            return None
        for message in event.messages:
            if (
                message.get("role") == "assistant"
                and message.get("content") is None
                and message.get("tool_calls")
            ):
                message["content"] = ""
        return None  # mutated in place; returning None keeps the event
```

```toml
# pyproject.toml of your extension package
[project.entry-points."headroom.pipeline_extension"]
null-content-normalizer = "my_headroom_ext.normalize:NullContentNormalizer"
```

Install the package into the same environment as Headroom (`pip install my-headroom-ext`). Headroom loads entry points on startup.

- An extension is an object with `on_pipeline_event(event)`, or a class that Headroom instantiates with no arguments. Return `None` after mutating in place, or return a replacement `PipelineEvent`. Returning the same `event` also works.
- Extensions fail open: Headroom catches and logs an exception, and the request proceeds unmodified. If the upstream still rejects requests, check the logs for a failing extension.
- `discover_pipeline_extensions=False` turns off discovery, and `pipeline_extensions=[...]` passes explicit instances. Both SDK `HeadroomConfig` and proxy `ProxyConfig` expose these fields.

## OAuth2 upstream authentication

Enterprise gateways (Azure AD / Entra, Okta, Auth0, Keycloak, Cognito) often protect OpenAI-compatible endpoints with an OAuth2 client-credentials flow. The `headroom-oauth2` extension mints a bearer token from your token endpoint, then caches and refreshes it (single-flight). It injects `Authorization: Bearer <token>` on each upstream request. It hard-codes no vendor and plugs into the `headroom.proxy_extension` entry point, so it stays out-of-tree and opt-in.

```bash
pip install headroom-oauth2
export HEADROOM_OAUTH2_TOKEN_URL="https://<identity-provider>/<token-path>"
export HEADROOM_OAUTH2_CLIENT_ID="<client-id>"
export HEADROOM_OAUTH2_CLIENT_SECRET="<client-secret>"
headroom proxy --backend litellm-openai --proxy-extension oauth2
```

| Variable | Meaning |
| --- | --- |
| `HEADROOM_OAUTH2_TOKEN_URL` | Token endpoint (client-credentials grant). The extension is a no-op unless this is set. |
| `HEADROOM_OAUTH2_CLIENT_ID` / `HEADROOM_OAUTH2_CLIENT_SECRET` | Credentials |
| `HEADROOM_OAUTH2_SCOPES` / `HEADROOM_OAUTH2_AUDIENCE` | Space- or comma-separated scopes, and an optional audience |
| `HEADROOM_OAUTH2_GRANT_TYPE` | Default `client_credentials` |
| `HEADROOM_OAUTH2_AUTH_STYLE` | `post` (form credentials) or `basic` (HTTP Basic) |
| `HEADROOM_OAUTH2_HEADERS` | Static upstream headers, `K=V,K2=V2` |
| `HEADROOM_OAUTH2_ALLOW_INSECURE` | `1` allows a non-HTTPS token URL |

- **Backends.** The bearer token reaches the upstream only for OpenAI-compatible or passthrough LiteLLM providers. `bedrock`, `vertex`, and `sagemaker` authenticate from the environment and ignore it, and the extension logs a warning at startup there.
- **Transport.** The token URL must use HTTPS. Loopback HTTP is allowed for tests.
- **Corporate networks.** Headroom mints tokens with the Python standard library (`urllib`) and the system certificate store. A corporate-injected certificate authority (CA) is trusted, so the extension works behind Secure Sockets Layer (SSL) inspection, where stacks with bundled roots fail.

## Filesystem contract

| Root | Default | Holds | Access |
| --- | --- | --- | --- |
| `HEADROOM_CONFIG_DIR` | `~/.headroom/config` | Model catalogs, plugin settings | Read-mostly |
| `HEADROOM_WORKSPACE_DIR` | `~/.headroom` | Savings, logs, memory database, telemetry, caches | Read-write |

The Python proxy, the CLI, and the npm SDK all recognize both roots. The roots are additive: every per-resource variable keeps its old semantics. An explicit argument falls through when it is `None` or empty, and an env var falls through when it is unset or blank. For example, `HEADROOM_WORKSPACE_DIR=/mnt/state` puts savings at `/mnt/state/proxy_savings.json`, but `HEADROOM_SAVINGS_PATH=/custom/savings.json` always wins, even when the workspace root is set. With neither set, savings go to `~/.headroom/proxy_savings.json`.

| Resource | Default path | Override |
| --- | --- | --- |
| Proxy savings ledger | `${WORKSPACE_DIR}/proxy_savings.json` | `HEADROOM_SAVINGS_PATH` |
| TOIN telemetry | `${WORKSPACE_DIR}/toin.json` | `HEADROOM_TOIN_PATH` |
| Subscription tracker state | `${WORKSPACE_DIR}/subscription_state.json` | `HEADROOM_SUBSCRIPTION_STATE_PATH` |
| Memory SQLite database | `${WORKSPACE_DIR}/memory.db` | CLI `--memory-db-path` |
| Native memory directory | `${WORKSPACE_DIR}/memories/` | `MemoryConfig.native_memory_dir` |
| Proxy logs and HTTP 400 debug dumps | `${WORKSPACE_DIR}/logs/`, `${WORKSPACE_DIR}/logs/debug_400/` | – |
| Models catalog | `${CONFIG_DIR}/models.json` | `HEADROOM_MODEL_LIMITS` (content override) |
| Plugin settings | `${CONFIG_DIR}/plugins/<name>/...` | – |

The workspace root also holds deployment profiles in `deploy/`, plus `license_cache.json`, `session_stats.jsonl`, `sync_state.json`, `bridge_state.json`, and `.beacon_lock_<port>`. Legacy per-resource variables take a raw string, with no tilde expansion and no path-separator normalization, so pass absolute paths to them.

**Project-scoped `.headroom/` directories.** Some code paths deliberately resolve `.headroom/` relative to the current working directory and ignore `HEADROOM_WORKSPACE_DIR`, so that project memory lives in the project directory. These are the memory database defaults in `headroom/proxy/server.py` and `headroom/memory/mcp_server.py`, and the memory and hook artifacts of `headroom/cli/wrap.py`. For one central memory store, pass `--memory-db-path <path>` or set the path through the plugin API.

### Docker

| Variable | Scope | Meaning |
| --- | --- | --- |
| `HEADROOM_WORKSPACE` | Host side | Directory bind-mounted into the container as `/workspace`, like the working directory in native runs. Used by `docker-compose.native.yml`. |
| `HEADROOM_WORKSPACE_DIR` | Inside the container | State root. Resolves to `/tmp/headroom-home/.headroom` in the official image, which bind-mounts to `${HOME}/.headroom` on the host. |

The official bootstrap (the compose file, `scripts/install.sh`, and the Python `install` command) sets `HEADROOM_WORKSPACE_DIR` and `HEADROOM_CONFIG_DIR` inside the container for you. Don't set `HEADROOM_WORKSPACE` to move state, because it chooses the mounted project directory, not the state root.

### Plugin directories

```python
from headroom import paths

cfg_dir = paths.plugin_config_dir("my-plugin")       # ~/.headroom/config/plugins/my-plugin
state_dir = paths.plugin_workspace_dir("my-plugin")  # ~/.headroom/plugins/my-plugin
cfg_dir.mkdir(parents=True, exist_ok=True)
(cfg_dir / "settings.json").write_text("{}")
```

```typescript
import { pluginConfigDir, pluginWorkspaceDir } from "@headroom/sdk";

const cfgDir = pluginConfigDir("my-plugin");
const stateDir = pluginWorkspaceDir("my-plugin");
```

The helpers reject names that contain `/` or `\`, to keep the namespace flat. The filesystem page imports the TypeScript helpers from `@headroom/sdk`, while the other TypeScript examples import from `headroom-ai`. Check which name your installed package exposes.

## Runtime rollout channels

Rollout channels control which behaviors an installed artifact may expose. They do not select a package or a released version.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HEADROOM_ROLLOUT_CHANNEL` | `stable` | `stable`, `beta`, `canary`, or `dev` |
| `HEADROOM_FEATURES` | unset | Comma-separated features to request |
| `HEADROOM_DISABLE_FEATURES` | unset | Comma-separated features to force off. Wins over every enable path. |
| `HEADROOM_UNSAFE_ALLOW_UNSTABLE_FEATURES` | unset | Break-glass override for emergency mitigation only |

See [architecture-and-security](./architecture-and-security.md) for rollout policy and provenance.

## Common pitfalls

- **Wrong mode axis.** `audit`, `optimize`, and `simulate` are SDK modes. The proxy accepts only `cache` and `token`.
- **Duplicated paths.** `x-headroom-base-url` takes a base. The proxy appends the original path, such as `/v1/messages`.
- **Missing gateway secrets.** If your configured headers do not reach a gateway, look for `upstream_extra_headers_withheld` and add the exact host to `HEADROOM_UPSTREAM_ALLOWED_HOSTS`.
- **Refused overrides behind a corporate proxy.** Global `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY` makes the proxy refuse `x-headroom-base-url` requests, unless the destination is in `HEADROOM_ALLOWED_BASE_URLS`.
- **Beta tokens that will not go away.** Sticky tracking re-injects them for the whole session. Set `HEADROOM_BETA_HEADER_STICKY=disabled` if you must drop one.
- **Rust proxy flags with no effect.** `HEADROOM_PROXY_BETA_HEADER_STICKY` needs `HEADROOM_PROXY_COMPRESSION=1`. Without it, the Rust proxy is a strict byte-pipe and warns at startup.
- **Silent extension failures.** A crashing pipeline extension is logged and skipped, so the upstream gets the unmodified request.
- **Memory outside the workspace.** Project-scoped memory paths ignore `HEADROOM_WORKSPACE_DIR`. Pass `--memory-db-path` for a central store.
- **OAuth2 on the wrong backend.** `bedrock`, `vertex`, and `sagemaker` ignore the injected bearer token.

## Related skills

- [getting-started](./getting-started.md) – installation, the Docker-native wrapper, and persistent installs.
- [compression](./compression.md) – SmartCrusher, Kompress, and the content routing that the compression variables tune.
- [ccr-and-caching](./ccr-and-caching.md) – CacheAligner, cache optimization, and automatic context management.
- [memory](./memory.md) – persistent memory, which `--memory`, the memory database paths, and `HEADROOM_MEMORY_INJECTION_MODE` configure.
- [proxy](./proxy.md) – every proxy CLI flag, savings profiles, endpoints, and corporate networks.
- [framework-integrations](./framework-integrations.md) – using the SDK and proxy from LiteLLM, LangChain, and other frameworks.
- [coding-agents](./coding-agents.md) – `headroom wrap` for Claude Code and VS Code, and Codex recovery. If Codex history disappeared after an older wrapper, read Codex recovery before wrapping Codex again.
- [observability](./observability.md) – savings tracking, `/stats`, and metrics.
- [sdk-reference](./sdk-reference.md) – the full Python and TypeScript API, including `HeadroomClient` and `compress`.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – symptoms such as Windows ML content detection hangs that `ORT_DYLIB_PATH` affects.
- [architecture-and-security](./architecture-and-security.md) – runtime rollouts in full and the security model.

## Source pages

- https://docs.headroomlabs.ai/docs/configuration
- https://docs.headroomlabs.ai/docs/filesystem-contract
- https://docs.headroomlabs.ai/docs/pipeline-extensions
- https://docs.headroomlabs.ai/docs/oauth2-upstream
