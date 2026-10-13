# Headroom: Reversible compression (CCR) and caching
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill to keep compressed content recoverable, to keep provider prompt caches hitting, and to lay out prompts for agents that wake repeatedly. It covers Compress-Cache-Retrieve (CCR), cache optimization, live-zone-only context management and agent orchestration.

## Core concepts

| Term | Meaning |
| --- | --- |
| Compress-Cache-Retrieve (CCR) | Headroom stores the original of each compressed block. The large language model (LLM) can retrieve it on demand, so compression becomes reversible. |
| CCR store | The local store that holds originals, keyed by hash. The docs also call it the compression store. |
| Marker | Text in the compressed output that carries the hash of the stored original. |
| `headroom_retrieve` | The tool the LLM calls with a `hash` to get an original back. |
| Live zone | The newest content blocks: the latest user message and the latest tool output. Headroom compresses only this zone. |
| Cache hot zone | The system prompt, tool definitions and older turns. Headroom never mutates this zone. |
| Stable prefix | The leading part of the prompt that stays byte-identical across requests. |
| Provider prompt cache | The provider's cache of computed key-value (KV) attention states for a prompt prefix. It hits only on a byte-identical prefix. |
| CacheAligner | An opt-in detector that reports prefix drift. It never rewrites messages. |
| Wake | One run of an agent that is invoked repeatedly with a similar prompt. |

## How the pieces fit

- Compressors such as SmartCrusher and ContentRouter shrink content and write each original to the CCR store.
- Context management decides what gets compressed: only the live zone.
- The proxy injects `headroom_retrieve` and resolves the model's retrieval calls.
- Cache mode and live-zone-only compression keep the cache hot zone byte-identical, so provider prompt caches keep hitting.
- CacheAligner and your own wake measurements show when your prompt assembly breaks the stable prefix.

## How CCR works

CCR lets compressors work aggressively, because the original stays one retrieval away. It lowers the risk of compression; it does not raise the compression ratio. Savings still depend on how redundant your data is.

```text
TOOL OUTPUT (1000 items)
  -> SmartCrusher compresses to 20 items
  -> Original cached with hash=abc123
  -> Retrieval tool injected into context

LLM PROCESSING
  Option A: LLM solves task with 20 items -> Done
  Option B: LLM calls headroom_retrieve(hash=abc123)
            -> Response Handler returns full data automatically
```

| Phase | What happens |
| --- | --- |
| 1. CCR store | The compressor stores the original under a hash and adds a marker to the compressed output. |
| 2. Tool injection | Headroom adds `headroom_retrieve` to the tools your application sends. |
| 3. Response handler | Headroom intercepts the `headroom_retrieve` call and reads the original from the CCR store in around 1 millisecond. It adds the result to the conversation, and the provider request continues automatically. |
| 4. Context tracker | Headroom remembers what it compressed in earlier turns. When a new query looks relevant, such as "auth" against a cached file list, it expands that original before the LLM asks. |

The architecture example shows this marker:

```text
[1000 items compressed to 20. Retrieve more: hash=abc123]
```

The LLM sees this tool next to your own tools:

```json
{
  "name": "headroom_retrieve",
  "description": "Retrieve original uncompressed data from Headroom cache",
  "parameters": {
    "hash": "The hash key from the compression marker"
  }
}
```

| Component | Compresses | CCR behavior |
| --- | --- | --- |
| SmartCrusher | JavaScript Object Notation (JSON) arrays in tool outputs | Stores the original array; the marker includes the hash |
| ContentRouter | Code, logs, search results, text | Stores the original content by strategy |

Because originals stay retrievable, SmartCrusher, LogCompressor, SearchCompressor and Kompress can compress as aggressively as their configuration allows. See [compression](./compression.md) for how each compressor works.

Message-level CCR through `IntelligentContext` is retired, together with the removed `IntelligentContextConfig` class. Tool-output CCR through SmartCrusher and ContentRouter remains fully supported.

## Enable CCR

Pick the path by who should resolve `headroom_retrieve` calls.

| Path | Who resolves `headroom_retrieve` |
| --- | --- |
| `headroom proxy`, Anthropic and OpenAI paths | Headroom, transparently. Your client never sees CCR tool calls. |
| `headroom proxy`, native Gemini, buffered | Headroom, server-side. You receive the model's final response. |
| `headroom proxy`, native Gemini, streaming | Not resolved server-side. Headroom keeps the existing forwarding behavior. |
| `headroom proxy`, native Gemini, `headroom_retrieve` mixed with your own function call | Your client. Headroom preserves both calls instead of resolving the mixed response. |
| Python `HeadroomClient` without the proxy | You. The client embeds markers but injects no tool and intercepts nothing. |

Google's OpenAI-compatible Gemini endpoint can return `finish_reason=MALFORMED_FUNCTION_CALL` on large function-response continuations after CCR retrieval. This separate limitation is tracked in [issue #2041](https://github.com/headroomlabs-ai/headroom/issues/2041).

### Through the proxy

The proxy's request handlers own tool injection and the response handler; the direct Python SDK client does not. Use the proxy when you want the model to retrieve originals on its own.

```bash
headroom proxy                # port 8787 by default; CCR is on
headroom proxy --no-ccr       # disable CCR specifically
headroom proxy --no-optimize  # passthrough baseline for comparison
```

```python
from openai import OpenAI

# Start `headroom proxy` first (defaults to port 8787).
client = OpenAI(base_url="http://127.0.0.1:8787/v1", api_key="local")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
)
```

### TypeScript `compress()`

The TypeScript software development kit (SDK) embeds CCR markers in `result.messages`. Its docs state that CCR is on by default when compressing through the proxy.

```typescript
import { compress } from "headroom-ai";
import type { CCRConfig } from "headroom-ai";

// CCR is enabled by default when compressing through the proxy.
const result = await compress(messages, {
  model: "gpt-4o",
});

// Access compressed messages – CCR markers are embedded automatically
console.log(result.messages);

// CCR configuration options
const ccrConfig: CCRConfig = {
  enabled: true,
  injectTool: true,             // Inject headroom_retrieve tool
  injectRetrievalMarker: true,  // Add retrieval markers to compressed output
  feedbackEnabled: true,        // Learn from retrieval patterns
  storeMaxEntries: 1000,        // Max cached items
  storeTtlSeconds: 3600,        // Cache TTL
};
```

These `CCRConfig` values are the docs' example values, not documented defaults. For instance, `storeTtlSeconds: 3600` differs from the proxy's 1800-second default. The page does not show where you pass a `CCRConfig`, so check [sdk-reference](./sdk-reference.md) first.

### Python SDK without the proxy

`HeadroomClient` integrates directly, with no proxy. It still routes JSON tool outputs through SmartCrusher. It embeds `<<ccr:HASH>>` markers when the compression ratio warrants one. The original is stored and retrievable through `headroom.cache.compression_store`. The client does not inject `headroom_retrieve` and does not intercept the model's retrieval call. To integrate CCR outside the proxy, resolve markers yourself:

```python
from headroom.ccr.marker_resolution import resolve_markers_in_text
```

These pages do not document the function's signature.

## Configure the CCR store and retention

| Setting | Default | Purpose |
| --- | --- | --- |
| `HEADROOM_CCR_TTL_SECONDS` | `1800` (30 minutes) | Time to live (TTL) of proxy CCR originals |
| `HEADROOM_CCR_BACKEND` | `sqlite`: `ccr_store.db` in the workspace directory | Set `memory` for an in-process-only store |
| `headroom.ccr_backend` | – | setuptools entry-point group that resolves other backend names |
| `/v1/retrieve/stats` | – | Proxy endpoint; shows the effective TTL under `store.default_ttl_seconds` |

Set the TTL before you start the proxy, then confirm it:

```bash
HEADROOM_CCR_TTL_SECONDS=7200 headroom proxy

# From another shell; read store.default_ttl_seconds in the response
curl -s http://127.0.0.1:8787/v1/retrieve/stats
```

See [proxy](./proxy.md) for the other proxy endpoints.

Pick the backend by what must survive:

- The SQLite default survives a proxy restart and is shared across the proxy's worker processes.
- `memory` keeps originals inside one process. You give up restart survival and sharing across workers.
- Only `sqlite` and `memory` ship with Headroom. Another backend, such as `redis`, works only if it is installed and registered in the entry-point group.

Know the limits of retention:

- Size the TTL for your longest realistic autonomous run. Raise it above the 30-minute default for long agent runs.
- The TTL is not the only limit. The store also evicts least recently used (LRU) entries once it reaches capacity.

## When an original expires

CCR retrieval depends on the store lifetime and the stored hashes. Plan for expiry instead of assuming originals last forever.

- Assume a stored original can expire before your run finishes.
- When it expires, regenerate the digest or re-read the source content.
- To learn how an original was produced, read the `compression_strategy` metadata on the stored CCR entry. It is the authoritative discriminator.
- Do not infer the producing path from the payload's shape. Shape inference is not the routing authority.

## Context management: live-zone-only compression

Context management runs automatically inside the pipeline. You do not configure a separate stage.

- Headroom never drops messages from the conversation history.
- It does no position-based or score-based context management.
- It compresses only the live zone, type-aware and reversible through CCR.
- It forwards the cache hot zone byte-for-byte. Provider prompt caching stays intact, so cache hit rates stay stable across turns.

```text
Conversation with a large latest tool result
  -> Identify the live zone (newest user message + latest tool output)
  -> Compress the live zone type-aware, cache original in CCR (hash=def456)
  -> Insert marker: "compressed, retrieve: def456"
  -> Older turns, tools, and system prompt are forwarded byte-for-byte
```

| Protection | Effect | Control |
| --- | --- | --- |
| Output buffer reservation | Reserves tokens for the response: `context_budget = model_context_limit - output_buffer_tokens` | Python: `headroom_output_buffer_tokens` per request |
| System message protection | System messages are never dropped | Always applies |
| Turn protection | The last N messages are always preserved | Python `compress()`: `CompressConfig.protect_recent`, default `4` (about the last 2 user/assistant turns) |

The output buffer stops the input from filling the whole context window. Without it, the model could run out of room to answer.

Set per-request overrides in TypeScript:

```typescript
import { compress } from "headroom-ai";

const result = await compress(messages, {
  model: "gpt-4o",
  tokenBudget: 32000,
});

console.log(`Compressed: ${result.tokensBefore} -> ${result.tokensAfter}`);
```

Set per-request overrides in Python:

```python
from headroom import HeadroomClient, OpenAIProvider
from openai import OpenAI

client = HeadroomClient(
    original_client=OpenAI(),
    provider=OpenAIProvider(),
    default_mode="optimize",
)

# Per-request overrides
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    headroom_output_buffer_tokens=8000,  # More room for long responses
)
```

Do not rely on `headroom_keep_turns`. `HeadroomClient.chat.completions.create()` accepts it without an error, but the value never reaches the transform pipeline. Use `CompressConfig.protect_recent` with `compress()` instead.

`IntelligentContextConfig`, `ScoringWeights` and `RollingWindowConfig` are no longer part of Headroom. Remove any code that still uses them.

## Cache optimization: keep the stable prefix byte-identical

Providers reuse cached attention states only for a byte-identical prefix. One changed character at the start of a prompt invalidates the entire provider prompt cache. System prompts often carry such changes: dates, session identifiers and timestamps.

In the proxy, cache mode (`--mode cache`, the default) keeps prefixes stable. It compresses only the newest delta and forwards prior turns byte-faithfully. See [proxy](./proxy.md) for the other savings profiles.

Don't do this:

```python
from datetime import datetime

# The timestamp changes on every request, so the cached prefix never matches.
messages = [
    {"role": "system", "content": f"Now: {datetime.now().isoformat()}\n{RULES}"},
    {"role": "user", "content": question},
]
```

Do this:

```python
from datetime import datetime

# The system prompt keeps the same bytes; volatile data goes last.
messages = [
    {"role": "system", "content": RULES},
    {"role": "user", "content": f"Now: {datetime.now().isoformat()}\n{question}"},
]
```

### CacheAligner reports drift; you fix it

CacheAligner is disabled by default and hard-disabled inside the proxy. When you enable it, it only reports metrics. It never extracts, moves, normalizes, reorders, strips, compresses or rewrites content. These pages do not show how to enable it; check [configuration](./configuration.md).

| Signal | Tells you |
| --- | --- |
| `warnings` | Which parts of the prefix look unstable |
| `cache_metrics.stable_prefix_bytes` | Stable prefix size in bytes |
| `cache_metrics.stable_prefix_tokens_est` | Stable prefix size in estimated tokens |
| `cache_metrics.stable_prefix_hash` | Stable prefix hash, for comparing wakes |
| `cache_metrics.prefix_changed` | Whether the prefix drifted since the previous wake |
| `cache_metrics.previous_hash` | The previous wake's hash, when available |
| `markers` | The emitted `stable_prefix_hash` marker, for downstream observability |

When `warnings` or `prefix_changed` appear, move the volatile content out of the prefix in your own assembly code. CacheAligner is a detector, not a repair pass.

### Provider caching strategies

| Provider | Mechanism | Cached-read discount | Limits | Who owns the layout |
| --- | --- | --- | --- | --- |
| Anthropic | Explicit `cache_control` blocks | 90% off input price | 25% premium on the first write; TTL 5 minutes, extended on hit | Your client or orchestrator places the `cache_control` blocks |
| OpenAI | Automatic prefix caching | 50% off input price | Minimum prefix 1024 tokens | No markers needed; you keep the prefix byte-identical |
| Google | Explicit CachedContent objects | 75% off input price | Minimum cache size 32,768 tokens | Your integration layer owns the CachedContent lifecycle |

For every provider, Headroom surfaces prefix instability and the caller owns the message layout. The exception is the Python `HeadroomClient`: its cache optimizer (`enable_cache_optimizer`, on by default) picks a provider-specific strategy, such as Anthropic `cache_control` breakpoints – see [configuration](./configuration.md).

### Anthropic prefix trackers

Headroom tracks Anthropic prefixes per conversation lineage.

- It keeps a tracker for the longer of two spans. One is the resolved provider cache lifetime plus a 60-second cleanup margin. The other is the configured session cleanup TTL.
- A configured cache lifetime also applies before the first confirmed cache write and when a request omits its TTL.
- A one-hour session does not extend an unrelated five-minute session.
- Headroom discards expired trackers before lookup. A later, longer TTL cannot revive them.
- A retained tracker does not prove that the provider prompt cache is still warm.

### Cold-prefix recompaction

Byte-identical forwarding pays off only while the provider prompt cache is warm. Once a session idles past the provider's cache TTL, that cache is gone. Re-sending the prefix verbatim then gains nothing, so it is the one safe moment to rewrite the prefix.

- The cold-prefix hook detects a lapsed cache. It recompacts the whole prefix with cross-turn dedupe, superseded-read drop and lossless folds. Then it re-caches the smaller result.
- It fires only on a confirmed-cold turn, because a wrong call would bust a warm cache.
- It reads the real TTL. The TTL is exact for Claude Code through its cache-control environment variables, and learned over time for other providers.
- A companion hook covers models that re-send reasoning as plain text every turn, such as Kimi, GLM and DeepSeek. It compresses that reasoning with Kompress on warm turns and drops it on cold turns.
- Both hooks are off by default. The [configuration page](https://docs.headroomlabs.ai/docs/configuration#cold-prefix-hook--reasoning-compaction) documents their flags and when each is safe to enable. See also [configuration](./configuration.md).

## Agent orchestration: structure repeated wakes

Repeated wakes rebuild almost the same expensive prompt. Order each wake so the repeated part stays cacheable.

| Layer | Handling |
| --- | --- |
| Stable instructions, project rules, tool contracts | Byte-identical across wakes. Put them first, as the stable prefix. |
| Current task and other instruction-bearing fields | Verbatim; see digest routing. |
| Wake digest (the volatile per-wake memory digest) | After the stable prefix, in the live zone, where it can change freely. |
| Recent loop state, tool output, child-agent context | Last, outside the stable prefix. |

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8787/v1", api_key="local")

STABLE_PREFIX = "..."  # rules and tool contracts – no dates, identifiers or counters

def wake(digest: str, run_context: str):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": STABLE_PREFIX},  # 1. byte-stable prefix
            {"role": "user", "content": digest},           # 2. wake digest
            {"role": "user", "content": run_context},      # 3. run-specific context
        ],
    )
```

### Digest routing

Route each digest field by how much exact wording it needs at wake time.

| Field | Handling | Why |
| --- | --- | --- |
| Current task | Verbatim | It is instruction-bearing and changes the next action |
| Hard constraints | Verbatim | They are safety and acceptance boundaries |
| Definitions of done | Verbatim | The wording must survive every wake intact |
| Irreversible decisions | Verbatim summary plus retrievable backing detail | The summary stays short; the backing detail stays exact |
| Open threads | Compact summary plus CCR-backed backing detail | The thread shrinks; the source stays recoverable |
| Learnings | Compact summary | They inform the next wake without exact prose |
| File, search and tool outputs | CCR-backed compression | They are large backing detail that should stay retrievable |
| Prose notes | Compact summary; CCR-backed when bulky | The digest stays readable without losing source detail |
| Bulk JSON-like arrays | SmartCrusher or ContentRouter, CCR-backed when needed | Structured blobs usually grow fastest |

Keep the boundary strict. Instruction-bearing fields stay verbatim, or they get a verbatim compact summary plus retrievable backing detail. CCR-backed content is the backing detail, never the instruction itself. The model must see every instruction on every wake, and a CCR original can expire.

### Measure real wakes

Record these for each prompt section before you decide where CCR belongs:

- Section identifier: which section changed or repeated.
- Byte or token estimate: the size before and after curation.
- Digest version: which digest schema you used.
- Cache-hit expectation: whether the section should stay cacheable.
- Compressed size: the compacted payload size.
- Section type: instruction-bearing or safe to compress.

The record separates the stable prefix from the wake digest.

### Choose an integration mode

Choose by where your orchestrator controls message assembly.

| Mode | Use when | Notes |
| --- | --- | --- |
| Proxy | Spawned agents and normal client traffic should pass through a local provider endpoint | Fits `headroom proxy --mode cache` with each client's `base_url` pointed at the proxy |
| Library | Your orchestrator owns message assembly and shapes the digest before launch | Best when the caller decides what goes in the stable prefix and what goes in the wake digest |
| Model Context Protocol (MCP) | Agents need on-demand compression and retrieval tools | Best when `headroom_retrieve` should be available as a tool |
| Proxy plus MCP | You need traffic shaping and tool-level retrieval together | Use when both the provider edge and the agent toolset matter |

### Deploy local-first

- Run one local proxy or MCP process per user session. Do not assume a central proxy.
- Treat the CCR store as local unless your deployment explicitly shares it. The proxy's SQLite default is shared across its own worker processes.
- Size `HEADROOM_CCR_TTL_SECONDS` for the longest realistic autonomous run.
- Assume the store can still expire before the run ends. Then regenerate the digest or re-read the source content.

Local-first deployment keeps the data boundary obvious. The orchestrator can still recover backing detail, and the stable prefix stays small.

## Trade-off: maximum token removal versus cache stability

- Rewriting a warm prefix removes more tokens, but it forfeits the cached-read discount: 90% on Anthropic, 50% on OpenAI, 75% on Google.
- On Anthropic, writing the new prefix to the cache also costs a 25% premium.
- Headroom's defaults favor cache stability. Cache mode compresses only the newest delta. Live-zone compression never touches the cache hot zone. CacheAligner only reports.
- CCR makes aggressive compression of the live zone safe, because the original stays retrievable while the CCR store keeps it.
- The cold-prefix hook rewrites the prefix only when the provider prompt cache is confirmed cold, with no discount left to lose. It is off by default, because a wrong cold call busts a warm cache.

## Anti-patterns that break cache hits

| Don't do this | Do this instead | Why |
| --- | --- | --- |
| Put dates, session identifiers or timestamps in the system prompt | Move them to the wake digest or the latest user message | One changed character at the start invalidates the whole provider prompt cache |
| Rebuild rules and tool contracts each wake with small differences | Build the stable prefix once and reuse the same bytes | Provider prompt caches hit only on a byte-identical prefix |
| Put tool output or child-agent context before the wake digest | Put run-specific context last | The stable prefix stays cacheable |
| Wait for CacheAligner to fix drift | Fix the assembly logic in your caller | CacheAligner detects drift; it never repairs it |
| Rewrite a warm prefix to save tokens | Leave prefix rewrites to the opt-in cold-prefix hook | A wrong call busts a warm provider prompt cache |
| Expect the proxy to place `cache_control` blocks or manage CachedContent objects | Handle them where your client assembles the request, or use the Python `HeadroomClient` cache optimizer | Outside that optimizer, the caller owns the message layout |

## Common pitfalls

- **Expecting the full CCR loop from `HeadroomClient`.** Only the proxy injects `headroom_retrieve` and resolves the call. Route traffic through `headroom proxy`, or resolve markers yourself with `resolve_markers_in_text`.
- **Relying on `headroom_keep_turns`.** It is accepted but has no effect. Use `CompressConfig.protect_recent`.
- **Keeping the default TTL for long runs.** Proxy originals last 1800 seconds unless you set `HEADROOM_CCR_TTL_SECONDS` before the proxy starts.
- **Treating the TTL as a guarantee.** LRU eviction at capacity can remove an original before its TTL ends.
- **Switching to `HEADROOM_CCR_BACKEND=memory` without a reason.** Originals then live in one process, so they neither survive a restart nor reach other workers.
- **Expecting CacheAligner output from the proxy.** CacheAligner is hard-disabled there; cache mode provides prefix stability instead.
- **Assuming your client never sees `headroom_retrieve` on Gemini.** Streaming native Gemini requests and mixed responses reach your client.
- **Hand-parsing marker text.** The format differs by path, for example `[1000 items compressed to 20. Retrieve more: hash=abc123]` versus `<<ccr:HASH>>`. Outside the proxy, use the documented resolver.
- **Reading a retained Anthropic tracker as a warm cache.** Tracker retention does not prove that the provider prompt cache is still warm.
- **Using removed features.** `IntelligentContextConfig`, `ScoringWeights`, `RollingWindowConfig` and message-level CCR are gone.

## Quick reference

| Task | Use |
| --- | --- |
| Get the full CCR loop | Route Anthropic or OpenAI traffic through `headroom proxy` |
| Disable CCR only | `headroom proxy --no-ccr` |
| Measure a passthrough baseline | `headroom proxy --no-optimize` |
| Keep prefixes cache-stable in the proxy | `--mode cache` (the default) |
| Keep originals longer | `HEADROOM_CCR_TTL_SECONDS=7200 headroom proxy` |
| Check the effective TTL | `/v1/retrieve/stats`, field `store.default_ttl_seconds` |
| Use an in-process store | `HEADROOM_CCR_BACKEND=memory` |
| Add a store backend | Register it in the `headroom.ccr_backend` entry-point group |
| Reach stored originals in Python | `headroom.cache.compression_store` |
| Resolve markers outside the proxy (Python) | `headroom.ccr.marker_resolution.resolve_markers_in_text` |
| Configure CCR (TypeScript) | `CCRConfig`: `enabled`, `injectTool`, `injectRetrievalMarker`, `feedbackEnabled`, `storeMaxEntries`, `storeTtlSeconds` |
| Set a token budget (TypeScript) | `compress(messages, { model: "gpt-4o", tokenBudget: 32000 })`, then read `result.tokensBefore` and `result.tokensAfter` |
| Reserve room for the response (Python) | `headroom_output_buffer_tokens` on `client.chat.completions.create()` |
| Protect recent messages (Python) | `CompressConfig.protect_recent`, default `4` |
| Detect prefix drift outside the proxy | CacheAligner `warnings` and `cache_metrics.prefix_changed` |
| Find how an original was produced | `compression_strategy` on the stored CCR entry |
| Give agents a retrieval tool | The MCP integration mode, with `headroom_retrieve` as a tool |

## Related skills

- [getting-started](./getting-started.md) – installation and first run.
- [compression](./compression.md) – SmartCrusher, ContentRouter and the other compressors that write CCR originals.
- [proxy](./proxy.md) – `headroom proxy` options, savings profiles such as `--mode cache`, and the proxy endpoints.
- [configuration](./configuration.md) – SDK and proxy configuration, per-request overrides and environment variables.
- [memory](./memory.md) – persistent memory, SharedContext and failure learning, next to the wake digest described here.
- [coding-agents](./coding-agents.md) – Claude Code and other agents, agent hooks and MCP tools.
- [framework-integrations](./framework-integrations.md) – OpenAI, Anthropic and framework clients pointed at the proxy.
- [sdk-reference](./sdk-reference.md) – Python and TypeScript reference and error handling.
- [observability](./observability.md) – savings tracking and metrics.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – symptoms, limitations and safety gates.
- [architecture-and-security](./architecture-and-security.md) – architecture and security model.

## Source pages

- Reversible Compression (CCR) – https://docs.headroomlabs.ai/docs/ccr
- Cache Optimization – https://docs.headroomlabs.ai/docs/cache-optimization
- Context Management – https://docs.headroomlabs.ai/docs/context-management
- Agent Orchestration – https://docs.headroomlabs.ai/docs/agent-orchestration
