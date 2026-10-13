# Headroom: Compression
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill when you compress large language model (LLM) context with Headroom: JSON tool outputs, source code, images, logs, search results, diffs, and prose. It covers how the pipeline routes content, what each compressor keeps, which thresholds let content pass through unchanged, and how each compressor fails safe.

## Core concepts

- **Routing is automatic.** You call `compress()` or run `headroom proxy`, and Headroom detects the type of each content block. You pass no type hints and need no configuration.
- **The pipeline has two stages.** CacheAligner runs first. It is detector-only and off by default: it reports dynamic-prefix drift (dates, session context) so you can keep the static prefix cacheable, and it never rewrites your messages. ContentRouter runs second and routes each content block to one compressor. Essentially all compression happens in ContentRouter.
- **Headroom preserves structure instead of truncating.** Each compressor keeps what the model needs for its content type and compresses the rest. For JSON it keeps keys, brackets, booleans, nulls, short values, and UUIDs; it compresses long string values and whitespace. For text it keeps high-entropy tokens (IDs, hashes) and headers; it compresses low-information content.
- **Compression fails safe.** A transform that saves nothing or fails passes the original through. Content that matches no compressor goes through a fallback chain, then passes through if no safe saving exists.
- **Savings numbers are directional.** Ratios depend on how redundant and how large the input is, and for Kompress on `target_ratio`. Reproduce them on your own traffic with the harnesses in `benchmarks/`: `compression_benchmark.py`, `bench_transforms.py`, and `text_crusher_quality_eval.py`.

### What `compress()` does, in order

1. **Safety gates** – protected tools, recent turns, frozen cache prefixes, and minimum-size rules decide what may change.
2. **Content detection** – Magika (when available) plus deterministic pattern matching identifies the content type.
3. **Structural compression** – format-specific handlers compact JSON, logs, search results, tables, configuration, HTML, and other recognized structures.
4. **Fallback compression** – Kompress handles eligible text when its runtime is available.
5. **Compress-Cache-Retrieve (CCR) storage in proxy flows** – when CCR is enabled, Headroom keeps the originals of marker-bearing compression for later retrieval. The `--lossless` and `--no-ccr` flags intentionally use different contracts; see [ccr-and-caching](./ccr-and-caching.md).

## Routing quick reference

| Content | Detection signal | Compressor | Typical savings |
| --- | --- | --- | --- |
| JSON arrays | Valid JSON with array elements | SmartCrusher | 26–54% on realistic non-duplicate arrays of 100–10,000 items; far more on repetitive arrays |
| Source code | Syntax patterns, indentation, keywords | CodeAwareCompressor in `headroom proxy`; Kompress in library `compress()` and `HeadroomClient` | Workload-dependent |
| Search results | Several `file:line:content` lines, or `grep -A/-B/-C` context lines | SearchCompressor | 80–95% |
| Build and test logs | Timestamps, log levels, and pytest, npm, or cargo markers | LogCompressor | 85–95% |
| Diffs | Unified diff format (`---`/`+++` and `@@` markers) | DiffCompressor | 60–80% |
| HTML | Tag structure | HTMLExtractor | 70–90% |
| Tables (CSV, TSV, Markdown) | Delimited rows or table syntax | TabularCompressor, which bridges to SmartCrusher | 26–28% on non-duplicate rows |
| Config (YAML, TOML, INI) | Config syntax | ConfigCompressor | 40–70% |
| Human-readable Git status | Branch or detached-HEAD header plus status sections and entries | Lossless passthrough (Python and Rust) | None, by design |
| Plain text | No stronger signal | Kompress | Workload-dependent |
| Anything else | Fallback chain | Kompress, then passthrough | Varies |

Images also take the ContentRouter path when the optional image dependencies are installed – see [Image compression](#image-compression).

### Git status always passes through

Headroom preserves human-readable Git status byte-for-byte, including section labels and paths that contain spaces. Staged, unstaged and untracked paths must stay intact.

- The router checks for Git status before model classification and before selected external or lossy compressors. CSV and wildcard plugins therefore cannot trim status entries.
- Git status also wins over mixed-content splitting. If fenced code or JSON follows a recognized status, Headroom preserves the whole tool result.
- The protection does not cover every `Bash` result. Ordinary prose and build logs still follow their normal routes.
- The recognizer covers only the standard English format (`LC_ALL=C`). Localized status output is not recognized, so run Git with `LC_ALL=C` where an agent reads its status.

## Key APIs

| API | Language | Import | Use it to |
| --- | --- | --- | --- |
| `compress(messages, model=..., config=...)` | Python | `from headroom import compress` | Run the full pipeline on a message list |
| `compress(messages, { model, tokenBudget })` | TypeScript | `import { compress } from "headroom-ai"` | Run the full pipeline on a message list |
| `CompressConfig` | Python | `from headroom import CompressConfig` | Tune the safety gates and the Kompress keep ratio |
| `SmartCrusher`, `SmartCrusherConfig` | Python | `from headroom import SmartCrusher, SmartCrusherConfig` | Compress one JSON string directly |
| `CodeAwareCompressor`, `CodeCompressorConfig`, `DocstringMode` | Python | `from headroom.transforms import ...` | Compress source code directly |
| `ImageCompressor` | Python | `from headroom.image import ImageCompressor` | Compress the images in a message list |
| `SearchCompressor`, `SearchCompressorConfig`, `LogCompressor`, `DiffCompressor` | Python | `from headroom.transforms import ...` | Compress search results, logs, and diffs |
| `TextCrusher` | Python | `from headroom.transforms.text_crusher import TextCrusher` | Extract the relevant parts of long prose |
| `KompressCompressor` | Python | `from headroom.transforms.kompress_compressor import KompressCompressor` | Run the Kompress text fallback directly |
| `detect_content_type`, `ContentType` | Python | `from headroom.transforms import ...` | Build your own routing |
| `headroom proxy`, `--no-code-aware`, `HEADROOM_CODE_AWARE_ENABLED` | Command line, environment | – | Compress traffic without code changes |

## Compress a message list

Pass the message list in the shape you send to the provider. Headroom returns the same shape.

```python
from headroom import compress

messages = [
    {"role": "user", "content": "Summarize the tool output."},
    {"role": "tool", "tool_call_id": "call_1", "content": large_output},
]
result = compress(messages, model="gpt-4o")
print(result.messages)
print(f"Saved {result.tokens_saved} tokens ({result.tokens_saved / result.tokens_before:.0%})")
```

```ts
import { compress } from "headroom-ai";

const result = await compress(messages, { model: "gpt-4o", tokenBudget: 50000 });
console.log(`Before: ${result.tokensBefore} tokens`);
console.log(`After: ${result.tokensAfter} tokens`);
console.log(`Transforms: ${result.transformsApplied.join(", ")}`);
```

| Result field | Python | TypeScript |
| --- | --- | --- |
| Compressed messages | `result.messages` | `result.messages` |
| Tokens saved | `result.tokens_saved` | `result.tokensSaved` |
| Compression ratio | `result.compression_ratio` | `result.compressionRatio` |
| Transforms applied | `result.transforms_applied` | `result.transformsApplied` |
| Tokens before and after | `result.tokens_before`, `result.tokens_after` | `result.tokensBefore`, `result.tokensAfter` |

The TypeScript SDK and the proxy define the compression ratio as tokens after divided by tokens before, so lower is better: `0.23` means a 77% reduction. Some Python examples in the docs print the raw ratio as if it were the saving, so derive the saving from the token counts instead.

In TypeScript, `tokenBudget` is the lever these pages document: SmartCrusher reduces JSON to fit the budget.

### Compress several documents

Put each document in its own message, or call `compress()` once per independent request. The public `compress()` API takes an LLM message list, and separate messages keep the shape you send to the provider.

```python
messages = [
    {"role": "user", "content": "Compare these documents."},
    {"role": "tool", "tool_call_id": "doc_1", "content": first_document},
    {"role": "tool", "tool_call_id": "doc_2", "content": second_document},
]
result = compress(messages, model="gpt-4o")
```

### Configure the pipeline

```python
from headroom import CompressConfig, compress

config = CompressConfig(
    compress_user_messages=True,
    protect_recent=0,
    target_ratio=0.5,             # Kompress keep ratio; structural compressors use their own rules
    min_tokens_to_compress=250,
)
result = compress(messages, model="gpt-4o", config=config)
print(result.transforms_applied)
```

- `target_ratio` steers Kompress only. Structural compressors such as SmartCrusher and LogCompressor apply their own rules, so a lower `target_ratio` does not shrink JSON or logs.
- The other three fields tune the safety gates: which messages may change and how large content must be. These pages show only the example values; see [configuration](./configuration.md) for the defaults.

## SmartCrusher: JSON arrays

SmartCrusher fires automatically when ContentRouter detects a JSON array. It tries two paths in order.

1. **Lossless table fold (default).** If the array is cleanly tabular – a consistent set of keys across items – SmartCrusher re-encodes every item in a compact `csv-schema` form. It keeps the result only if it saves at least 30% of the bytes. No item is dropped.
2. **Scored keep/drop (lossy).** If the fold misses the 30% bar, or the array is not cleanly tabular, SmartCrusher scores every item and targets `max_items_after_crush` items (default 15). In the docs measurement, a 1,000-item array came down to 16 items.

| Item type | Kept on the lossy path |
| --- | --- |
| Error items | 100% – never dropped, because they are critical for debugging |
| First N items | 100% – context and pagination |
| Last N items | 100% – recency |
| Anomalies (more than 2 standard deviations from the mean) | All – unusual values matter |
| Items relevant to the query, scored with Best Matching 25 (BM25) or embeddings | Top K |
| Change points (significant transitions in the data) | Kept while `preserve_change_points=True` (default) |
| Everything else | Sampled, for a statistical representation |

### Call SmartCrusher directly

You don't need to call SmartCrusher for normal traffic, because ContentRouter routes JSON arrays to it. Call it directly when you want fine-grained control over its configuration.

```python
import json
from headroom import SmartCrusher, SmartCrusherConfig

config = SmartCrusherConfig(
    min_tokens_to_crush=200,      # Only compress if > 200 tokens
    max_items_after_crush=15,     # Keep at most 15 items (lossy path only)
    first_fraction=0.3,           # Keep first 30% of items
    last_fraction=0.15,           # Keep last 15% of items
    variance_threshold=2.0,       # Statistical variance threshold
    preserve_change_points=True,  # Keep significant transitions
)
crusher = SmartCrusher(config)

tool_output = json.dumps({"results": items})  # crush() takes a JSON string, not a dict
result = crusher.crush(tool_output, query="find payment failures")
print(result.compressed)  # compressed JSON string
print(result.strategy)    # e.g. "lossless:table(...)" or "smart_sample(1000->15)"
```

`crush()` returns a `CrushResult`. Read `result.strategy` to learn which path ran. These pages show no TypeScript SmartCrusher class. In TypeScript, set `tokenBudget` on `compress()` as shown in [Compress a message list](#compress-a-message-list), or configure SmartCrusher through the proxy or `HeadroomClient`.

### SmartCrusher options

| Option | Default | Meaning |
| --- | --- | --- |
| `min_tokens_to_crush` | `200` | Compress only arrays with more than this many tokens |
| `min_items_to_analyze` | `5` | Minimum items before SmartCrusher analyzes an array |
| `max_items_after_crush` | `15` | Maximum items kept (lossy path only) |
| `first_fraction` | `0.3` | Fraction of items always kept from the start |
| `last_fraction` | `0.15` | Fraction of items always kept from the end |
| `variance_threshold` | `2.0` | Statistical variance threshold for analysis |
| `uniqueness_threshold` | `0.1` | Uniqueness threshold for deduplication |
| `similarity_threshold` | `0.8` | Similarity threshold for grouping |
| `preserve_change_points` | `True` | Keep significant transitions |
| `dedup_identical_items` | `True` | Deduplicate identical items |
| `use_feedback_hints` | `True` | Use TOIN feedback hints for scoring |

Set `with_compaction` on the `SmartCrusher(...)` constructor. The lossless fold runs by default; `SmartCrusher(with_compaction=False)` skips it and forces the keep/drop path.

### When to tune SmartCrusher

Every change that keeps more items costs more tokens. Every change that keeps fewer items risks losing a row the model needs, although errors and anomalies always survive.

- **Pass the user's question as `query`.** Relevance scoring matches items against it, so the rows that answer the question survive.
- **Raise `max_items_after_crush`** when the model needs more than 15 rows to answer, for example to compare many records. The trade-off is more tokens per array.
- **Raise `last_fraction`** for recency-ordered data and **`first_fraction`** for paginated results. The docs keep the last items for recency and the first items for context and pagination.
- **Raise `min_tokens_to_crush`** when small arrays should reach the model untouched. Lower it to compress smaller arrays, which have less to save.
- **Leave `with_compaction` on.** The lossless fold keeps every item when it saves at least 30%. Headroom's own retention-property tests turn it off to exercise the keep/drop path; outside tests, turning it off only removes the chance to keep every item.

## Code compression

CodeAwareCompressor uses tree-sitter to parse source code into an abstract syntax tree (AST). It compresses function bodies and keeps the structure the model needs. Naive truncation cuts a function in half and leaves invalid syntax that confuses the model; CodeAwareCompressor guarantees that its output parses.

- **Always preserved:** import statements, function and method signatures, class definitions, type annotations, and decorators.
- **Compressed:** function bodies, comments, and verbose docstrings (`docstring_mode`: `FULL`, `FIRST_LINE`, or `REMOVE`).

| Tier | Languages | Support |
| --- | --- | --- |
| Tier 1 | Python, JavaScript, TypeScript | Full AST analysis |
| Tier 2 | Go, Rust, Java, C, C++, C#, PHP | Function body compression |

Other languages fall back to Kompress while `fallback_to_kompress=True` (default). The tree-sitter language pack comes with the `code` extra: `pip install "headroom-ai[code]"`. The parsers take about 50 MB, load lazily, and stay cached. Typical results are a 40–70% token reduction in about 10–50 ms per file.

### Routing depends on the entry point

ContentRouter always detects source code. Whether it sends that code to CodeAwareCompressor depends on how you call Headroom.

| Entry point | Where detected code goes | How to change it |
| --- | --- | --- |
| `headroom proxy` | CodeAwareCompressor – `HEADROOM_CODE_AWARE_ENABLED` defaults to on | Disable with `--no-code-aware` or `HEADROOM_CODE_AWARE_ENABLED=0` |
| Library `compress()` and `HeadroomClient` | Kompress – their `ContentRouterConfig` defaults to `enable_code_aware=False` | Build your own pipeline with `ContentRouterConfig(enable_code_aware=True)` |
| `CodeAwareCompressor` called directly | CodeAwareCompressor | Neither setting affects it |

### Compress code directly

```python
from headroom.transforms import CodeAwareCompressor, CodeCompressorConfig

# min_tokens_for_compression defaults to 100; a small snippet needs an
# explicit override or it passes through unmodified.
compressor = CodeAwareCompressor(CodeCompressorConfig(min_tokens_for_compression=10))

result = compressor.compress(code, language="python")
print(result.compressed)
print(f"Compression: {result.compression_ratio:.0%}")  # ~57% in the docs example
print(f"Syntax valid: {result.syntax_valid}")          # True
```

In the docs example, the output keeps the imports, the signature, the docstring's first line, and the start of the body, then marks the rest with `# [6 lines omitted]` and `pass`. It can end with a retrieval marker such as `# [32 tokens compressed. Retrieve more: hash=<cache_key>. Expires in 5m.]`; see [ccr-and-caching](./ccr-and-caching.md) for retrieval.

### Configure CodeAwareCompressor

```python
from headroom.transforms import CodeAwareCompressor, CodeCompressorConfig, DocstringMode

config = CodeCompressorConfig(  # every value shown is the default
    preserve_imports=True,
    preserve_signatures=True,
    preserve_type_annotations=True,
    preserve_decorators=True,
    docstring_mode=DocstringMode.FIRST_LINE,  # FULL, FIRST_LINE, REMOVE
    target_compression_rate=0.2,              # fraction of tokens to keep
    max_body_lines=5,                         # lines kept per function body
    min_tokens_for_compression=100,           # skip smaller content
    language_hint=None,                       # auto-detect when None
    fallback_to_kompress=True,                # Kompress for unsupported languages
)
result = CodeAwareCompressor(config).compress(code)
```

- Raise `target_compression_rate` or `max_body_lines` when the model must reason about implementation details. The trade-off is more tokens per file.
- Use `DocstringMode.FULL` when docstrings carry the intent the model needs. Use `REMOVE` when they repeat the signature.
- Set `language_hint` when you know the language, so detection cannot guess wrong.

### Free parser memory

```python
from headroom.transforms import is_tree_sitter_available
from headroom.transforms.code_compressor import unload_tree_sitter

print(is_tree_sitter_available())  # True when the tree-sitter pack is installed
unload_tree_sitter()               # free the cached parsers when you are done
```

## Image compression

Vision models bill images in tokens: a 1024x1024 image costs about 765 tokens on OpenAI. Headroom's image compressor reads the user's question, picks a technique, and applies it in the form each provider supports. It saves 40–90% of image tokens.

1. **Query analysis** – a fine-tuned MiniLM classifier (`chopratejas/technique-router` on Hugging Face) picks a technique. It reached 93.7% accuracy across 1,157 training examples.
2. **Image analysis** – SigLIP checks image properties: does the image contain text, is it complex, does it have fine details?
3. **Apply compression** – OpenAI gets `detail="low"`, Anthropic images resize to 512px, and Google Gemini images resize to 768px.

| Technique | Savings | Chosen for | Example question |
| --- | --- | --- | --- |
| `full_low` | ~87% | General understanding | "What is this?", "Describe the scene" |
| `preserve` | 0% | Fine details | "Count the whiskers", "Read the serial number" |
| `crop` | 50–90% | A specific region | "What's in the corner?" |
| `transcode` | ~99% | Text extraction | "Read the sign", "Transcribe the document" |

| Provider | Method | Measured example |
| --- | --- | --- |
| OpenAI | Sets the native `detail="low"` parameter | 1024x1024 with `full_low`: 765 to 85 tokens (89%) |
| Anthropic | Python Imaging Library (PIL) resize to 512px | 1024x1024: ~1,398 to ~349 tokens (75%) |
| Google Gemini | Resize to 768px, matching Gemini's 768x768 tiles | 1536x1536: 1,032 tokens (4 tiles) to 258 tokens (1 tile), 75% |

Headroom computes the OpenAI and Anthropic figures from formulas in `headroom/image/tile_optimizer.py`. The Gemini figures describe Google's published tile pricing; Headroom has no Gemini token formula and does not compute or test them.

### Use the proxy

```bash
headroom proxy --port 8787
ANTHROPIC_BASE_URL=http://localhost:8787 claude
```

The proxy compresses images on every request that contains them, as long as the optional image dependencies are installed. The current release has no public proxy command-line toggles for images.

### Use HeadroomClient

```python
from headroom import HeadroomClient, OpenAIProvider
from openai import OpenAI

client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(), default_mode="optimize")
response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [
    {"type": "text", "text": "What animal is this?"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
]}])
# The image is compressed with detail="low"
```

### Use ImageCompressor directly

```python
from headroom.image import ImageCompressor

# use_siglip enables image analysis; device is auto, cuda, cpu, or mps
compressor = ImageCompressor(model_id="chopratejas/technique-router", use_siglip=True, device="cuda")
compressed_messages = compressor.compress(messages, provider="openai")
print(f"Saved {compressor.last_savings:.0f}% tokens")
print(f"Technique: {compressor.last_result.technique.value}")
```

### Image trade-offs

- **Accuracy:** the router is a classifier, not an oracle. A fine-detail question that it misreads gets a low-detail image. Phrase fine-detail questions explicitly ("Read the serial number"), because the wording drives the technique. These pages document no option that forces `preserve`.
- **Fidelity:** every technique except `preserve` trades image fidelity for tokens.
- **Cold start:** the first request downloads the router model; later requests use the cached copy. Download time depends on your network.
- **Footprint:** the router takes about 100 MB as a PyTorch model, or about 32 MB as an Open Neural Network Exchange (ONNX) INT8 model, which is preferred in production. SigLIP image analysis (`use_siglip=True`) needs about 400 MB of graphics processing unit (GPU) memory.
- **Latency:** a resize takes about 5–20 ms (measured median about 9 ms for 1024px to 512px with PIL and LANCZOS).

## Text and log compressors

| Compressor | Input | Keeps | Typical savings |
| --- | --- | --- | --- |
| `SearchCompressor` | grep, ripgrep, and ag output | Exact query matches, BM25-relevant matches, file diversity, first and last matches | 80–95% |
| `LogCompressor` | Build and test logs | Lines with ERROR, FAILED, or Exception; warnings; full stack traces; summary lines; section headers such as `=====` | 85–95% |
| `DiffCompressor` | Unified diffs | Changed lines and enough context to understand them | 60–80% |
| `TextCrusher` | General text, such as documentation and prose | The most relevant sentences verbatim, headers, section markers, document structure | 30–60% |
| `KompressCompressor` | General text fallback | Tokens chosen by learned scoring via ONNX | Highly variable |

LogCompressor drops hundreds of `PASSED` lines, verbose success output, and repeated patterns.

Measured warm speeds, one run each: SearchCompressor ~2.0 ms (1,000 matches, 60 files), LogCompressor ~17 ms (5,000 lines), DiffCompressor ~0.4 ms (30-file diff), TextCrusher ~0.7 ms (10,000 characters). Kompress speed depends on the model.

### Search results

```python
from headroom.transforms import SearchCompressor, SearchCompressorConfig

config = SearchCompressorConfig(
    max_total_matches=30,       # Cap total matches kept across all files
    max_matches_per_file=5,     # Cap matches kept per file (diversity)
    max_files=15,               # Cap number of distinct files kept
    boost_errors=True,          # Prioritize lines that look like errors
    context_keywords=["auth"],  # Extra terms to bias selection toward
)
result = SearchCompressor(config).compress(search_results, context="find process")
print(f"Compressed {result.original_match_count} matches to {result.compressed_match_count}")
print(result.compressed)
```

These are the docs' example values; the page lists no defaults for `SearchCompressorConfig`. Pass `context` so BM25 scoring and exact-match selection know what you searched for.

### Logs and diffs

```python
from headroom.transforms import DiffCompressor, LogCompressor

log_result = LogCompressor().compress(build_output)
print(log_result.compressed)
print(f"Compression ratio: {log_result.compression_ratio:.1%}")

diff_result = DiffCompressor().compress(diff_output)
```

The ~70% diff figure was measured with the default `max_context_lines` and `max_hunks_per_file` limits.

### Prose: Kompress and TextCrusher

```python
from headroom.transforms.kompress_compressor import KompressCompressor
from headroom.transforms.text_crusher import TextCrusher  # own module, not the package root

k = KompressCompressor().compress(long_output)
print(f"Saved: {k.savings_percentage:.1f}%")

t = TextCrusher().compress(long_text, context="authentication")
print(f"{t.original_tokens} -> {t.compressed_tokens} tokens")
```

- ContentRouter sends ordinary prose (`PLAIN_TEXT`) to KompressCompressor.
- TextCrusher runs only when long plain text exceeds Kompress's size gate (`_kompress_max_tokens`). Synchronous ONNX inference on that much text is not safe on the request path, so TextCrusher takes over.
- TextCrusher is extractive: it selects the most relevant input sentences and never rewrites them. Its `target_ratio` defaults to 0.5, which measured about 50% savings on real documentation prose.
- Kompress's `target_ratio` defaults to `None` ("model decides"), which measured only 6–24% on real prose. An explicit `target_ratio=0.5` measured about 40%. Set it through `CompressConfig(target_ratio=0.5)` when you need predictable savings; a lower keep ratio drops more text.
- The first Kompress call after process start pays a one-time model-load cost.
- LLMLingua was removed. Its transform and helper functions are no longer exported; use Kompress and ContentRouter instead.

### Build your own routing

```python
from headroom.transforms import detect_content_type, ContentType, SearchCompressor, LogCompressor

# One file:line:content line is not enough signal; the detector wants several.
content = "src/main.py:42:def process():\nsrc/utils.py:10:def helper():\nsrc/models.py:5:class Foo:"

detection = detect_content_type(content)
if detection.content_type == ContentType.SEARCH_RESULTS:
    result = SearchCompressor().compress(content, context="process")
elif detection.content_type == ContentType.BUILD_OUTPUT:
    result = LogCompressor().compress(content)
elif detection.content_type == ContentType.PLAIN_TEXT:
    from headroom.transforms.text_crusher import TextCrusher
    result = TextCrusher().compress(content, context="process")
```

## Thresholds that let content pass through

| Gate | Default | Effect | Override |
| --- | --- | --- | --- |
| SmartCrusher `min_tokens_to_crush` | `200` | Arrays of 200 tokens or fewer pass through | `SmartCrusherConfig(min_tokens_to_crush=...)` |
| SmartCrusher `min_items_to_analyze` | `5` | Arrays with fewer items are not analyzed | `SmartCrusherConfig(min_items_to_analyze=...)` |
| SmartCrusher lossless fold | 30% byte saving | Below 30%, the keep/drop path runs instead | `SmartCrusher(with_compaction=False)` skips the fold |
| CodeAwareCompressor `min_tokens_for_compression` | `100` | Smaller code passes through unmodified | `CodeCompressorConfig(min_tokens_for_compression=...)` |
| Pipeline `min_tokens_to_compress` | Not on these pages | Minimum-size safety gate | `CompressConfig(min_tokens_to_compress=...)` |
| Kompress size gate `_kompress_max_tokens` | Not on these pages | Longer plain text goes to TextCrusher | Internal; no documented override |

## When not to compress, and how each compressor fails safe

Leave content uncompressed when the model needs exact bytes or every detail. Headroom already does this in several places, so know where it stops.

- **Exact-byte output:** Git status passes through untouched in its standard English format. Other output gets no such protection from the router; the pipeline's safety gates include protected tools – see [troubleshooting-and-limits](./troubleshooting-and-limits.md).
- **Small content:** content under a size gate passes through. Don't lower a gate to squeeze tiny payloads, because the saving is small and a lossy path can still drop detail.
- **Every JSON row matters:** keep `with_compaction` on so the lossless fold can keep every item. In proxy flows, enable CCR so the originals stay retrievable.
- **Fine image detail:** the router picks `preserve` (0% savings) for fine-detail questions.

| Compressor | Fail-safe behavior |
| --- | --- |
| Any transform | A no-saving or failed transform passes the original through |
| ContentRouter fallback | Kompress, then passthrough when no safe saving exists |
| SmartCrusher | Lossless fold first; error items never dropped on the lossy path |
| CodeAwareCompressor | Output always parses; small files pass through; unsupported languages fall back to Kompress |
| Kompress | Runs only when its runtime is available; oversized text goes to TextCrusher |
| Git status | Preserved ahead of plugins, lossy compressors, and mixed-content splitting |
| Image compressor | `preserve` technique keeps the image when details matter |

## Do this, not that

| Do this | Not that | Why |
| --- | --- | --- |
| Let ContentRouter route content | Call individual compressors for normal traffic | The router picks a compressor per content block; direct calls exist for fine-grained control |
| Pass `json.dumps(...)` to `crush()` | Pass a dict | `crush()` takes a JSON string |
| Pass the user's question as `query` or `context` | Compress without it | Relevance scoring matches against it |
| Set Kompress `target_ratio` explicitly | Rely on the `None` default | `None` measured only 6–24% on real prose |
| Import `TextCrusher` from `headroom.transforms.text_crusher` | Import it from `headroom.transforms` | It lives in its own module |
| Use Kompress and ContentRouter for text | Import LLMLingua helpers | LLMLingua was removed |
| Benchmark on your own traffic | Quote the savings ranges as guarantees | Ratios depend heavily on input shape |
| Call `unload_tree_sitter()` in long-lived processes when done | Keep idle parsers loaded | The parsers hold about 50 MB |

## Common pitfalls

- **The lossy-path example misleads.** The docs' 1,000-item array with one error shrinks to about 15 items on the keep/drop path (`with_compaction=False`). With default settings, that mostly identical shape favors the lossless fold, so every item more likely stays. Read `result.strategy`.
- **Small code snippets come back unchanged.** `min_tokens_for_compression` is 100, so a short test snippet passes through. Lower it in `CodeCompressorConfig` to see compression.
- **Proxy and library disagree on code.** The proxy uses CodeAwareCompressor by default; library `compress()` and `HeadroomClient` use Kompress. The same file compresses differently on each path.
- **CacheAligner does not fix caching.** It is off by default and only reports prefix drift; it never rewrites messages.
- **First calls are slow.** Kompress loads its model on the first call after process start, and the image router downloads its model on the first request.
- **A single grep line is not search results.** The detector needs several `file:line:content` lines before it reports `SEARCH_RESULTS`.

## Related skills

- [getting-started](./getting-started.md) – install Headroom and its optional extras before you rely on code or image compression.
- [ccr-and-caching](./ccr-and-caching.md) – retrieve originals behind compression markers, the `--lossless` and `--no-ccr` contracts, and CacheAligner's role in prefix caching.
- [proxy](./proxy.md) – run `headroom proxy`, including `--no-code-aware` and agent wrapping.
- [configuration](./configuration.md) – `CompressConfig` defaults, `ContentRouterConfig`, `HEADROOM_CODE_AWARE_ENABLED`, pipeline extensions, and plugins.
- [sdk-reference](./sdk-reference.md) – full Python and TypeScript signatures for `compress()` and its result objects.
- [framework-integrations](./framework-integrations.md) – `HeadroomClient` and SDK wrappers that run this pipeline.
- [coding-agents](./coding-agents.md) – agents whose search, log, and Git tool outputs this pipeline compresses.
- [observability](./observability.md) – track `tokens_saved` across real traffic and simulate savings.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – safety gates, limitations, and what to check when content is not compressed.
- [architecture-and-security](./architecture-and-security.md) – benchmarks and where the pipeline sits in the architecture.
- [memory](./memory.md) – persistent memory, SharedContext, and failure learning.

## Source pages

- https://docs.headroomlabs.ai/docs/how-compression-works
- https://docs.headroomlabs.ai/docs/smart-crusher
- https://docs.headroomlabs.ai/docs/code-compression
- https://docs.headroomlabs.ai/docs/image-compression
- https://docs.headroomlabs.ai/docs/text-and-logs
