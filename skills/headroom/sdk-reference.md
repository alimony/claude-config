# Headroom: SDK reference
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

This skill covers the Headroom software development kits (SDKs): the Python package `headroom-ai`, imported as `headroom`, and the npm package `headroom-ai`. It maps their application programming interface (API) and their error handling. It lists the options you use most; for every configuration option, load [configuration](./configuration.md).

## Quick reference

A dash (–) means the API reference documents no equivalent in that language.

| Task | Python (`headroom`) | TypeScript (`headroom-ai`) |
| --- | --- | --- |
| Compress, then call the model | `client.chat.completions.create(...)` on a `HeadroomClient` | `await compress(messages, { model })`, then send `result.messages` |
| Preview savings without a model call | `client.chat.completions.simulate(...)` | – |
| Create a client | `HeadroomClient(original_client=..., provider=...)` | `new HeadroomClient({ baseUrl, apiKey, ... })` |
| Top-level configuration | `HeadroomConfig(smart_crusher=..., cache_aligner=...)` | `HeadroomConfig` type |
| Compression result | `SimulationResult` (preview) | `CompressResult` |
| Token-counting provider | `OpenAIProvider`, `AnthropicProvider`, `GoogleProvider` (from `headroom.providers`) | – |
| Count tokens | `Tokenizer(counter, model)`, `count_tokens_text(text, counter)` | – |
| Relevance scoring | `create_scorer()`, `BM25Scorer`, `EmbeddingScorer`, `HybridScorer` | `RelevanceScorerConfig` via `SmartCrusherConfig.relevance` |
| Run a transform yourself | `SmartCrusher`, `CacheAligner`, `TransformPipeline` | – |
| Stats and stored metrics | `get_stats()`, `get_metrics()`, `get_summary()`, `generate_report()` | – |
| Check setup at startup | `client.validate_setup()` | – |
| Catch any Headroom error | `except HeadroomError` | `e instanceof HeadroomError` |
| Convert a proxy error response | – | `mapProxyError(status, type, message)` |

## Core concepts

- **`HeadroomClient` is a different object in each language.** In Python, it wraps your OpenAI or Anthropic client, runs the transform pipeline and makes the model call. In TypeScript, it holds the connection settings for the Headroom proxy.
- **TypeScript compresses through the proxy.** `compress()` sends messages to the Headroom proxy and returns compressed messages for your own large language model (LLM) client. The proxy must be running (`headroom proxy`).
- **Headroom never drops messages.** It compresses only the newest content blocks – the latest user message and the latest tool result. The cache hot zone – system prompt, tools and older turns – stays untouched.
- **Compression fails safe.** If a transform fails, the original content passes through unchanged, so a compression problem does not break your model call. An invalid mode, a broken metrics database and TypeScript proxy errors still raise – see [What raises and what passes through](#what-raises-and-what-passes-through).
- **This reference documents `compress()` for TypeScript only.** For other Python compression entry points, see [compression](./compression.md) and [getting-started](./getting-started.md).

## Entry points

### TypeScript: `compress()`

`compress(messages, options)` compresses messages through the Headroom proxy and resolves to a `CompressResult`.

| Option | Type | Purpose |
| --- | --- | --- |
| `model` | `string` | Model name for token counting and context limits |
| `tokenBudget` | `number` | Compress to fit within this many tokens |
| `fallback` | `boolean` | Return the original messages on failure instead of throwing |
| `retries` | `number` | Retry attempts on failure |
| `timeout` | `number` | Request timeout in milliseconds |
| `baseUrl` | `string` | Address of the Headroom proxy |
| `apiKey` | `string` | API key for authentication |
| `client` | `HeadroomClientInterface` | Pre-configured client instance to use |
| `hooks` | `CompressionHooks` | Hooks for pre- and post-processing |

```ts
import { compress } from 'headroom-ai';

const result = await compress(messages, {
  model: 'gpt-4o', baseUrl: 'http://localhost:8787', timeout: 15_000,
  fallback: true, retries: 2, tokenBudget: 100_000,
});
if (!result.compressed) console.warn('Sending uncompressed messages');
// Pass result.messages to your LLM client.
```

Choose one failure strategy for each call site:

- **`fallback: true`** keeps requests flowing, because a failure returns the original messages. The trade-off: a proxy outage can go unnoticed, so check `result.compressed`, which says whether compression was actually applied.
- **Typed catches** tell you exactly what failed, at the cost of handling each error yourself. See [Catch errors in TypeScript](#catch-errors-in-typescript).

### TypeScript: `HeadroomClient`

The constructor takes the five connection options that `compress()` also accepts: `baseUrl`, `apiKey`, `timeout`, `fallback` and `retries`. Build it once and pass it through the `client` option, so connection settings live in one place.

```ts
import { compress, HeadroomClient } from 'headroom-ai';

const client = new HeadroomClient({ baseUrl: 'http://localhost:8787', apiKey: 'your-api-key', timeout: 30_000, fallback: true, retries: 2 });
const result = await compress(messages, { model: 'gpt-4o', client });
```

The reference shows no `chat.completions.create()` in TypeScript. `compress()` does the compression, and your own LLM client makes the call.

### Python: `HeadroomClient`

The Python client wraps your existing OpenAI or Anthropic client. It supplies each model's context limit from the provider, so you do not pass limits per call.

| Parameter | Default | Purpose |
| --- | --- | --- |
| `original_client` | required | The `OpenAI` or `Anthropic` client to wrap |
| `provider` | required | Token-counting provider, such as `OpenAIProvider()` |
| `default_mode` | `"audit"` | `"audit"` or `"optimize"` |
| `config` | default config | `HeadroomConfig` with `smart_crusher` and `cache_aligner` settings |
| `store_url` | `None` | Address of the metrics database |
| `enable_cache_optimizer` | `True` | Provider-specific cache optimization |
| `enable_semantic_cache` | `False` | Query-level semantic caching |
| `model_context_limits` | `{}` | Per-model context-limit overrides (`dict[str, int]`) |

```python
from headroom import HeadroomClient, OpenAIProvider, HeadroomConfig, SmartCrusherConfig, CacheAlignerConfig
from openai import OpenAI

config = HeadroomConfig(
    smart_crusher=SmartCrusherConfig(min_tokens_to_crush=100),
    cache_aligner=CacheAlignerConfig(enabled=True),
)
client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(), default_mode="optimize", config=config)
```

The default mode is `"audit"`, not `"optimize"`. The reference example sets `"optimize"` explicitly. Check [configuration](./configuration.md) for what each mode does before you rely on the default.

### Python: `chat.completions.create()`

`create()` accepts every standard OpenAI or Anthropic parameter, plus these per-request overrides:

| Override | Default | Purpose |
| --- | --- | --- |
| `headroom_mode` | client default | `"audit"`, `"optimize"` or `"simulate"` for this request |
| `headroom_query` | `None` | Query for relevance scoring |
| `headroom_keep_turns` | `2` | Documented as "keep the last N turns uncompressed", but accepted and ignored – see below |
| `headroom_output_buffer_tokens` | `4000` | Tokens reserved for the model's output |

```python
response = client.chat.completions.create(
    model="gpt-4o", messages=[...], headroom_mode="optimize", headroom_output_buffer_tokens=8000,
)
```

A larger `headroom_output_buffer_tokens` leaves more room for the answer, but less for input.

Don't rely on `headroom_keep_turns`. The context-management page says the client accepts it without forwarding it to the transform pipeline, and the 0.40.0 source confirms that it is never used. For turn protection, call `compress()` with `CompressConfig(protect_recent=...)` – see [ccr-and-caching](./ccr-and-caching.md).

`headroom_tool_profiles` is accepted but not wired through `TransformPipeline.apply()`, so it changes nothing (documented for 0.37.0). To compress tool outputs less aggressively, tune SmartCrusher instead:

```python
# Don't: pass headroom_tool_profiles – it is accepted but ignored
# Do: keep more items after compression (default 15), or set enabled = False to skip SmartCrusher
config = HeadroomConfig()
config.smart_crusher.max_items_after_crush = 100
```

### Python: `chat.completions.simulate()`

`simulate()` previews the optimization without making an API call. Use it to measure savings and spot waste before you change a live workload. The trade-off: it says nothing about answer quality, because no model runs.

```python
plan = client.chat.completions.simulate(model="gpt-4o", messages=[...])

print(f"Tokens: {plan.tokens_before} -> {plan.tokens_after}")
print(f"Savings: {plan.tokens_saved/plan.tokens_before*100:.1f}%")
print(f"Transforms: {plan.transforms}")
```

It returns a `SimulationResult` – see [Result types](#result-types).

## Configuration types

Python passes most defaults to the `HeadroomClient` constructor. TypeScript groups them in the `HeadroomConfig` type.

| Setting | Python | TypeScript `HeadroomConfig` |
| --- | --- | --- |
| Default mode | `HeadroomClient(default_mode=...)` | `defaultMode` |
| Metrics database | `HeadroomClient(store_url=...)` | `storeUrl` |
| Context-limit overrides | `HeadroomClient(model_context_limits=...)` | `modelContextLimits` |
| SmartCrusher | `HeadroomConfig.smart_crusher` | `smartCrusher` |
| Cache aligner | `HeadroomConfig.cache_aligner` | `cacheAligner` |
| Cache optimizer | `HeadroomClient(enable_cache_optimizer=...)` | `cacheOptimizer` |
| Compress-Cache-Retrieve (CCR) | – | `ccr` |
| Prefix freeze, content routing, diff artifacts | – | `prefixFreeze`, `contentRouterEnabled`, `generateDiffArtifact` |

The reference lists the TypeScript `HeadroomConfig` type but shows no `compress()` or `HeadroomClient` option that accepts it. Do not guess an option name – check [configuration](./configuration.md).

In Python, pass sub-configurations as keyword arguments, as in the client example. You can also set attributes on a default `HeadroomConfig()`, as in the `headroom_tool_profiles` fix above. The options you change most:

| Python | TypeScript | Python default | Effect |
| --- | --- | --- | --- |
| `smart_crusher.min_tokens_to_crush` | `smartCrusher.minTokensToCrush` | `200` | Minimum tokens before compression applies |
| `smart_crusher.min_items_to_analyze` | `smartCrusher.minItemsToAnalyze` | `5` | Minimum items before analysis |
| `smart_crusher.max_items_after_crush` | `smartCrusher.maxItemsAfterCrush` | `15` | Maximum items kept after compression |
| `smart_crusher.first_fraction` / `last_fraction` | `firstFraction` / `lastFraction` | `0.3` / `0.15` | Share of items kept from the start and the end |
| `cache_aligner.enabled` | `cacheAligner.enabled` | `False` | Cache alignment stays off until you enable it |

Do not confuse the cache aligner with the cache optimizer: `enable_cache_optimizer` defaults to `True`, while the cache aligner defaults to off. [ccr-and-caching](./ccr-and-caching.md) explains what each one does. For the remaining thresholds and the dynamic-content detection settings, see [configuration](./configuration.md) or the [API reference](https://docs.headroomlabs.ai/docs/api-reference#configuration).

### Retired context-management classes

Context management now runs inside the transform pipeline. `RollingWindowConfig`, `IntelligentContextConfig` and `ScoringWeights` are gone from the Python package, so `from headroom import RollingWindowConfig` fails. `HeadroomConfig` has no `rolling_window` either. Reserve output room per request with `headroom_output_buffer_tokens`. For turn protection, use `CompressConfig.protect_recent` with `compress()`, because `headroom_keep_turns` has no effect.

The TypeScript `HeadroomConfig` type still exports the equivalent legacy field names. They are wired to nothing, so setting them has no effect.

## Result types

### `CompressResult` (TypeScript)

| Field | Type | Meaning |
| --- | --- | --- |
| `messages` | `any[]` | Compressed messages, in the same format as the input |
| `tokensBefore` | `number` | Token count before compression |
| `tokensAfter` | `number` | Token count after compression |
| `tokensSaved` | `number` | Tokens removed by compression |
| `compressionRatio` | `number` | `tokensAfter` divided by `tokensBefore` |
| `transformsApplied` | `string[]` | Names of the transforms that were applied |
| `ccrHashes` | `string[]` | CCR hashes – see [ccr-and-caching](./ccr-and-caching.md) |
| `compressed` | `boolean` | Whether compression was actually applied |

`compressionRatio` is after divided by before, so a lower value means more compression. A ratio of 0.25 means the compressed messages use a quarter of the original tokens.

```ts
// Don't: compressionRatio is the share that remains, not the share saved
console.log(`Saved ${result.compressionRatio * 100}%`);

// Do: compute the saving from tokensSaved
console.log(`Saved ${((result.tokensSaved / result.tokensBefore) * 100).toFixed(1)}%`);
```

### `SimulationResult` (Python)

`simulate()` returns `tokens_before`, `tokens_after`, `tokens_saved`, `transforms` (names of the transforms applied) and `waste_signals`.

`waste_signals` counts tokens per waste type, such as oversized JavaScript Object Notation (JSON) blocks and HyperText Markup Language (HTML) noise. It is a plain `dict[str, int]`, not an object with attributes.

| Key | Tokens from |
| --- | --- |
| `json_bloat` | JSON blocks over 500 tokens |
| `html_noise` | HTML tags and comments |
| `base64` | Base64-encoded blobs |
| `whitespace` | Repeated whitespace |
| `dynamic_date` | Dynamic dates in the system prompt |
| `repetition` | Repeated content |
| `reread` | Tool results served again after they already appeared |
| `reread_compressed` | The part of `reread` whose first serve was already compressed away |

```python
# Don't: plan.waste_signals.json_bloat – attribute access fails on a dict
for signal, tokens in plan.waste_signals.items():  # Do: read it as a dict
    print(f"{signal}: {tokens} tokens")
```

### `RequestMetrics` (Python)

`RequestMetrics` describes one processed request: `request_id`, `timestamp`, `model`, `tokens_input_before`, `tokens_input_after`, `tokens_output` and `transforms_applied`. It stores no cost. Compute cost on demand with the provider's `estimate_cost()`, shown in [Providers and token counting](#providers-and-token-counting).

### Same idea, different names

| Concept | `SimulationResult` | `RequestMetrics` | `CompressResult` (TypeScript) |
| --- | --- | --- | --- |
| Tokens before | `tokens_before` | `tokens_input_before` | `tokensBefore` |
| Tokens after | `tokens_after` | `tokens_input_after` | `tokensAfter` |
| Tokens saved | `tokens_saved` | – | `tokensSaved` |
| Transforms | `transforms` | `transforms_applied` | `transformsApplied` |

### Stats and stored metrics (Python)

| Call | Returns | Reads the metrics database |
| --- | --- | --- |
| `client.get_stats()` | Dict with `session`, `config` and `transforms` keys | No – current session only |
| `client.get_metrics(start_time=datetime.utcnow() - timedelta(hours=1), limit=100)` | Stored metrics | Yes |
| `client.get_summary()` | Dict with `total_requests`, `total_tokens_before`, `total_tokens_after`, `total_tokens_saved`, `avg_tokens_saved`, `avg_cache_alignment`, `audit_count` and `optimize_count` | Yes |
| `generate_report(store_url="sqlite:///headroom.db", format="html", period="day")` | HTML or Markdown report | Yes |

Use `get_stats()` for frequent checks, because it runs no database query. Import `generate_report` from `headroom`. Storage calls can raise driver errors – see [Catch errors in Python](#catch-errors-in-python). For dashboards and Prometheus, see [observability](./observability.md).

## Providers and token counting

A provider supplies token counting, context limits and cost estimates for one model family. The Python `HeadroomClient` requires one.

```python
from headroom import OpenAIProvider, AnthropicProvider, Tokenizer, count_tokens_text
from headroom.providers import GoogleProvider
from anthropic import Anthropic

provider = OpenAIProvider()
counter = provider.get_token_counter("gpt-4o")
tokens = counter.count_text("Hello, world!")
limit = provider.get_context_limit("gpt-4o")  # 128000
cost = provider.estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o")

tokens = count_tokens_text("Hello, world!", counter)  # one-off count
tokenizer = Tokenizer(counter, "gpt-4o")  # reusable; CacheAligner.apply() takes one
tokens = tokenizer.count_messages(messages)

anthropic_provider = AnthropicProvider(client=Anthropic())
tokens = anthropic_provider.get_token_counter("claude-3-5-sonnet-latest").count_messages(messages)

google_provider = GoogleProvider()
```

`AnthropicProvider` takes an `Anthropic` client because it counts tokens through the Anthropic API. You get accurate counts in exchange for an API round trip. `count_tokens_messages` is exported as well, but the reference never shows how to call it, so use `Tokenizer.count_messages()`.

Unknown models do not raise. `get_context_limit()` falls back to a default limit and logs a one-time `WARNING` that names the fallback. Your calls keep working, but the budget may not match the real model. Set the limit explicitly in one of these places:

- `model_context_limits` on the Python `HeadroomClient`, such as `model_context_limits={"unknown-model-xyz": 128_000}`, or `modelContextLimits` in the TypeScript `HeadroomConfig`
- the `HEADROOM_MODEL_LIMITS` environment variable
- the file `~/.headroom/models.json`

The formats of the environment variable and the file are in [configuration](./configuration.md).

## Relevance scoring

Relevance scoring ranks items against a query. Pass the query per request with `headroom_query`, or as `query=` when you call `SmartCrusher.crush()` yourself.

| Scorer | Strength | Trade-off |
| --- | --- | --- |
| `BM25Scorer` | Fast keyword-based scoring, zero dependencies | Matches keywords, not meaning |
| `EmbeddingScorer` | Semantic similarity | Needs the `headroom-ai[relevance]` extra |
| `HybridScorer` | Combines BM25 and embeddings | You tune the mix with `alpha` |
| `create_scorer()` | Picks the best available scorer | Less control over the tier |

```python
from headroom import create_scorer, BM25Scorer, EmbeddingScorer, HybridScorer, embedding_available

scorer = create_scorer()                          # best available scorer
scorer = create_scorer(tier="hybrid", alpha=0.7)  # explicit tier
scores = BM25Scorer().score_batch(["item 1", "item 2"], "search query")
if embedding_available():  # guard: needs headroom-ai[relevance]
    scores = EmbeddingScorer(model_name="BAAI/bge-small-en-v1.5").score_batch(items, query)
scorer = HybridScorer(alpha=0.5)  # 50% BM25, 50% embedding
```

`RelevanceScorerConfig` expresses the same choices as configuration. The Python defaults are `tier="hybrid"`, `bm25_k1=1.5`, `bm25_b=0.75`, `embedding_model="all-MiniLM-L6-v2"`, `hybrid_alpha=0.5`, `adaptive_alpha=True` and `relevance_threshold=0.25`. For `hybrid_alpha`, 0 means pure embedding and 1 means pure BM25. `relevance_threshold` is the minimum score an item needs to stay. TypeScript uses camelCase names, such as `hybridAlpha` and `relevanceThreshold`, and attaches the config through `SmartCrusherConfig.relevance`.

## Run transforms directly

Call a transform yourself when you want to compress content outside a chat call. The trade-off: you supply the inputs yourself. `CacheAligner` needs a `Tokenizer`. `TransformPipeline` needs a `model_limit`, which `HeadroomClient` otherwise takes from the provider's context limits.

```python
import json
from headroom import SmartCrusher, CacheAligner, TransformPipeline, Tokenizer, OpenAIProvider

result = SmartCrusher().crush(content=json.dumps({"results": [...]}), query="user query")

provider = OpenAIProvider()
tokenizer = Tokenizer(provider.get_token_counter("gpt-4o"), "gpt-4o")
result = CacheAligner().apply(messages, tokenizer)

pipeline = TransformPipeline(transforms=[SmartCrusher(), CacheAligner()])
result = pipeline.apply(messages, "gpt-4o", model_limit=128_000)  # Do: pass model_limit
# Don't: pipeline.apply(messages, "gpt-4o") – direct pipeline use requires model_limit
```

How SmartCrusher chooses what to keep is in [compression](./compression.md).

## TypeScript message types

The TypeScript SDK uses the standard OpenAI message format, with `SystemMessage`, `UserMessage`, `AssistantMessage` and `ToolMessage` variants. Message fields keep snake_case names, unlike the camelCase SDK options.

| Field | Type | Notes |
| --- | --- | --- |
| `role` | `"system" \| "user" \| "assistant" \| "tool"` | Sender role |
| `content` | `string \| ContentPart[] \| null` | `null` for tool-calling assistant messages |
| `tool_calls` | `ToolCall[]` | Assistant messages only |
| `tool_call_id` | `string` | Tool messages only – the tool call this message answers |

## Error handling

The errors page pins several of these behaviors to version 0.37.0, while 0.40.0 was current when the docs were fetched. Re-check them if your code depends on a particular exception being raised or not raised.

### Error hierarchy

Every Headroom error extends `HeadroomError` in both languages.

| Class | Languages | Meaning |
| --- | --- | --- |
| `HeadroomError` | Both | Base class |
| `HeadroomConnectionError` | TypeScript | Cannot reach the proxy |
| `HeadroomAuthError` | TypeScript | Status 401 from the proxy |
| `HeadroomCompressError` | TypeScript | Compression failed; has `statusCode` and `errorType` |
| `CompressionError` | Python | Compression failed (exported, not raised) |
| `ConfigurationError`, `ProviderError`, `StorageError` | Both | Invalid configuration, provider issues, storage failures |
| `TokenizationError`, `CacheError`, `ValidationError`, `TransformError` | Both | Failures in token counting, cache operations, validation and transform execution |

The compression error has a different name in each language: Python `CompressionError`, TypeScript `HeadroomCompressError`.

### What raises and what passes through

| Situation | Language | What happens |
| --- | --- | --- |
| A transform fails, for example on malformed JSON in a tool message | Python | Original content passes through unchanged; no exception |
| SmartCrusher cannot preserve protected rows | Python | Original, uncompressed content passes through; `WARNING` logged |
| Unknown model name | Python | Default context limit and a one-time `WARNING`; no `ProviderError` |
| `headroom_tool_profiles` passed | Python | Accepted and ignored |
| Invalid `default_mode` string | Python | `ValueError` from the `HeadroomMode` enum |
| Broken metrics database in `get_metrics()` or `get_summary()` | Python | The driver's own exception, such as `sqlite3.OperationalError` |
| Proxy unreachable | TypeScript | `HeadroomConnectionError` |
| Proxy returns an error response | TypeScript | Class chosen by status and error type – see the mapping below |
| Any `compress()` failure with `fallback: true` | TypeScript | Original messages returned instead of an exception |

Several Python classes are exported but not raised. Nothing raises `CompressionError`, and there is no strict mode that would. Nothing raises `ProviderError` either – an unknown model falls back to a default limit instead. `get_metrics()` and `get_summary()` do not wrap storage failures in `StorageError`. `HeadroomClient` does not raise `ConfigurationError`.

### Catch errors in TypeScript

```ts
import { compress, HeadroomConnectionError, HeadroomAuthError, HeadroomCompressError, HeadroomError } from 'headroom-ai';

try {
  const result = await compress(messages, { model: 'gpt-4o' });
} catch (e) {
  if (e instanceof HeadroomConnectionError) console.error('Is the proxy running? Start with: headroom proxy');
  else if (e instanceof HeadroomAuthError) console.error('Auth failed:', e.message);
  else if (e instanceof HeadroomCompressError) console.error(`Compress failed (${e.statusCode}):`, e.message);
  else if (e instanceof HeadroomError) console.error('Headroom error:', e.message, e.details);
  else throw e; // not a Headroom error, so do not swallow it
}
```

Check subclasses before `HeadroomError`. Every class extends it, so a base-class check placed first matches everything and hides the specific cause. Every error carries `details` (`Record<string, any> | undefined`), and `HeadroomCompressError` adds `statusCode` and `errorType`.

### Map proxy errors to classes

The TypeScript SDK maps proxy error responses to classes automatically:

| Status | Proxy error type | TypeScript class |
| --- | --- | --- |
| 401 | – | `HeadroomAuthError` |
| 4xx or 5xx | `configuration_error`, `provider_error`, `storage_error`, `tokenization_error`, `cache_error`, `validation_error` or `transform_error` | The matching class: `ConfigurationError`, `ProviderError`, `StorageError`, `TokenizationError`, `CacheError`, `ValidationError` or `TransformError` |
| 4xx or 5xx | Any other type | `HeadroomCompressError` |

When you handle a raw proxy error response yourself, convert it with `mapProxyError()`:

```ts
import { mapProxyError } from 'headroom-ai';

const error = mapProxyError(400, 'configuration_error', 'Invalid mode'); // a ConfigurationError instance
```

### Catch errors in Python

Catch what the code actually raises today, not what the class names suggest. An `except ConfigurationError` around the constructor and an `except StorageError` around metrics calls never run for the common failures.

```python
try:
    client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(), default_mode="optimize")
except ValueError as e:  # an invalid mode raises ValueError, not ConfigurationError
    raise SystemExit(f"Invalid mode: {e}")

check = client.validate_setup()
if not check["valid"]:
    for key in ("provider", "storage", "config", "cache_optimizer"):
        if not check[key]["ok"]:
            print(f"  - {key}: {check[key]['error']}")

try:
    metrics = client.get_metrics()
except Exception:  # driver errors such as sqlite3.OperationalError are not wrapped in StorageError
    metrics = []  # continue without historical metrics
```

Keep `except Exception` around storage calls only. Everywhere else, catch specific classes, because a broad catch hides real bugs. Catching `HeadroomError` does not help around storage calls, since the driver's exception is not a Headroom class. When you do catch a `HeadroomError`, read `e.details` – a dict that may include `field`, `provider`, `model` and `original_error`.

### Log safe fallbacks

Turn on `WARNING` logging to see fallbacks that otherwise stay silent. Transforms catch their own failures and return the original content, so the log is where you notice that compression was skipped.

```python
import logging
logging.basicConfig(level=logging.WARNING)
# WARNING:headroom.transforms.smart_crusher:SmartCrusher audit_safe: 1 protected row(s) could not be
# preserved through compression (...). Failing closed: returning original uncompressed.
```

The errors page calls this behavior failing open, while the SmartCrusher log line calls it failing closed. Both mean the original, uncompressed content goes through.

## Best practices

1. **Validate at startup.** Call `client.validate_setup()` once when your app starts. Provider, storage, configuration and cache-optimizer problems then surface before the first request. The cost is one extra call at boot.
2. **Log at `WARNING` level.** Safe fallbacks and unknown-model defaults are silent otherwise. You accept some extra log lines in exchange.
3. **Catch specific exceptions.** A broad catch hides real bugs. Make one exception: storage calls, where driver errors arrive unwrapped.
4. **Preview before you optimize.** `simulate()` shows savings and waste signals without an API call. It cannot judge answer quality, so still review model output after you switch modes.
5. **Set context limits for models Headroom does not know.** The default limit keeps calls working, but the real limit may differ.

## Common pitfalls

- **The default mode is `"audit"`.** Set `default_mode` or `headroom_mode` explicitly, and check [configuration](./configuration.md) for what each mode does.
- **Cache alignment is off by default.** Set `cache_aligner.enabled = True`. `enable_cache_optimizer` is a separate setting.
- **Some settings look live but are not.** `headroom_tool_profiles` and `headroom_keep_turns` are ignored, the TypeScript legacy context fields are wired to nothing, and `RollingWindowConfig` no longer imports.
- **Result fields are easy to misread.** `compressionRatio` is after divided by before, `waste_signals` is a dict, and the transform list has three names: `transforms`, `transforms_applied` and `transformsApplied`.
- **Direct use needs extra inputs.** `TransformPipeline.apply()` needs `model_limit`. `EmbeddingScorer` needs the `headroom-ai[relevance]` extra, so guard it with `embedding_available()`.
- **TypeScript needs a running proxy.** `HeadroomConnectionError` means the SDK cannot reach it; start it with `headroom proxy`.
- **TypeScript messages use snake_case** (`tool_calls`, `tool_call_id`), while SDK options use camelCase (`tokenBudget`).

## Related skills

- [configuration](./configuration.md) – every SDK and proxy option, per-request overrides, environment variables and model limits.
- [compression](./compression.md) – the compression pipeline, content routing and how SmartCrusher decides what to keep.
- [ccr-and-caching](./ccr-and-caching.md) – CCR hashes, the cache aligner and optimizer, and context management.
- [proxy](./proxy.md) – the proxy that TypeScript `compress()` calls, its options and its endpoints.
- [observability](./observability.md) – savings tracking, metrics, Prometheus and simulation.
- [framework-integrations](./framework-integrations.md) – Headroom with the OpenAI, Anthropic and Vercel AI SDKs, LangChain and other frameworks.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – fixes by symptom, such as compression that is too aggressive, plus safety gates.
- [getting-started](./getting-started.md) – installation, including optional extras.

## Source pages

- https://docs.headroomlabs.ai/docs/api-reference
- https://docs.headroomlabs.ai/docs/errors
