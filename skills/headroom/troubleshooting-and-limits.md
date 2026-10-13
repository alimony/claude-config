# Headroom: Troubleshooting and limitations
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

## Symptoms, causes and fixes

Find your symptom, apply the fix, then read the matching section below for the reasoning and the trade-offs.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `headroom proxy` fails or hangs | Port 8787 is in use, or the `[proxy]` extra is missing | Check with `lsof -i :8787`, start with `--port 8788`, or `pip install "headroom-ai[proxy]"` |
| `curl: (7) Failed to connect to localhost port 8787` | The proxy is not running, or it started on another port | `curl http://localhost:8787/health`, then `ps aux \| grep headroom` |
| Some requests fail with 502 or 503 | The real error is in the proxy log; common suspects are a missing application programming interface (API) key and a failing provider API | Run with `--log-file` and `--log-messages`, confirm the key is set, then call the provider API directly |
| Windows 11 24H2+: every request stalls, or the first detection takes about 5 seconds and compression quality drops | Without `ORT_DYLIB_PATH`, Windows loads its own Windows Machine Learning (ML) copy of `onnxruntime.dll`, which deadlocks | Confirm the `Pinned ORT_DYLIB_PATH` startup line; otherwise `pip install onnxruntime` or set `ORT_DYLIB_PATH` |
| `stats['session']['tokens_saved_total']` is 0 | Client mode is `audit`, no tool outputs, tool outputs under 200 tokens, or incompressible data | Switch to `optimize`, lower `min_tokens_to_crush`, and accept passthrough for code and grep results |
| TypeScript `compress()` reports 0 `tokensSaved` | The proxy was started with `--no-optimize`, or one of the causes above | Restart the proxy without `--no-optimize` |
| Dashboard "Tokens Saved" reads about 0, but spend is flat or lower | The default `coding` savings profile runs the proxy in cache mode | Read the Prefix Cache Impact panel and the Compression vs Cache tile |
| Model answers miss facts that were in tool outputs | SmartCrusher keeps too few items (`max_items_after_crush`, default 15) | Raise `max_items_after_crush`, or disable SmartCrusher |
| Requests are slow | Embedding-based relevance scoring, small payloads, or transforms you do not need | Use the `bm25` tier, raise `min_tokens_to_crush`, and turn CacheAligner off if you enabled it |
| `pipx` keeps an old release, or `No matching distribution found` | The pipx environment uses a Python that has no Headroom wheels yet | `pipx install --python python3.13 "headroom-ai[all]"` |
| `RuntimeError: Unsupported compiler -- at least C++11 support is needed!` | No C++ build tools | Install `build-essential` (Debian, Docker) or the Xcode command line tools (macOS) |
| `ModuleNotFoundError: No module named 'headroom'` | Headroom is installed in another environment | `pip show headroom-ai`, activate the virtual environment, `pip install --upgrade headroom-ai` |
| An optional feature fails on a missing module | Its extra is not installed | Install `[proxy]`, `[relevance]`, `[code]` or `[all]` |
| Windows Defender blocks `sg.exe` from `ast-grep-cli` 0.44.1 | A flagged release that Headroom's dependency pin excludes | `uv cache clean` and reinstall, or run the proxy in Docker |
| uv: `src does not appear to be a Python project`, or `Unknown wheel data type: .DS_Store` | Corrupt or stale entries in the uv cache | `uv cache clean`, then reinstall |
| OpenAI invalid key, or Anthropic authentication error | The key is not set, or not passed to the provider client | Read the key from the environment and pass `api_key=` |
| Unknown model warnings | A custom or fine-tuned model has no known context limit | Pass `model_context_limits` to `HeadroomClient` |
| `validate_setup()` returns `"ok": False` | Missing key, unwritable storage path, or invalid mode | See [Validate the setup](#validate-the-setup) |
| Claude Code `/context all` shows tens of thousands more tool tokens | A custom `ANTHROPIC_BASE_URL` turns off Claude Code's deferred tool loading | `headroom wrap claude`, or set `ENABLE_TOOL_SEARCH=true` |
| Claude Code in Visual Studio Code (VS Code) shows `unsupported content type` | The extension cannot render deferred-tool blocks | Set `ENABLE_TOOL_SEARCH=false` for that target and restart the Headroom deployment |
| `Remote Control is only available when using Claude via api.anthropic.com` | Claude Code checks the `ANTHROPIC_BASE_URL` host before any request | Start Claude without `ANTHROPIC_BASE_URL` for those sessions |
| claude.ai server-managed settings do not apply | Claude Code skips the settings fetch for any non-default host | Ship the policy as endpoint-managed settings |

## Core concepts

- **Fail open.** Every compressor returns the original content unchanged when it cannot compress safely. It logs the error at WARNING level instead of raising it. The trade-off: a compression failure never breaks your request, but it stays silent until you read the logs.
- **Two kinds of mode.** The Python software development kit (SDK) client runs in `audit` mode (observe only) or `optimize` mode (compress). The proxy compresses in `cache` mode by default and in `token` mode with `--mode token`. Starting the proxy with `--no-optimize` turns its optimization off. If you pass a proxy mode such as `token` to the client, `validate_setup()` reports `Invalid mode`.
- **Cache mode versus token mode.** Cache mode freezes the provider prefix and compresses only the newest turn delta, so the provider prefix cache keeps hitting. Token mode maximizes visible compression but rewrites prior turns, which can reduce prefix-cache hits. The default `coding` savings profile uses cache mode.
- **Size gates.** The content router skips messages under 50 tokens by default. SmartCrusher, the JavaScript Object Notation (JSON) array compressor, skips content under 200 tokens (`min_tokens_to_crush`) and arrays under 5 items (`min_items_to_analyze`). Small payloads pass through because the overhead would exceed the savings.
- **Client-side gates.** With a custom `ANTHROPIC_BASE_URL`, Claude Code changes its own behavior before any request reaches Headroom. Proxy-side changes cannot reverse these decisions, and only client-side settings sometimes can.

## Debugging techniques

Work from the quickest check to the most involved one.

### Check the proxy is up

```bash
curl http://localhost:8787/health   # does the proxy answer?
ps aux | grep headroom              # did it start on another port?
lsof -i :8787                       # does another process hold the port?
headroom proxy --port 8788          # start on a free port instead

# Still failing, or 502/503 errors: log requests to a file
headroom proxy --log-file ~/.headroom/logs/proxy.jsonl --log-messages
```

### Validate the setup

`validate_setup()` reports provider, storage and config problems as separate entries.

```python
result = client.validate_setup()
print(result)
# {"provider": {"ok": False, "error": "No API key"}}             -> set OPENAI_API_KEY or pass api_key to OpenAI()
# {"storage": {"ok": False, "error": "unable to open database"}} -> check path permissions; use :memory: for testing
# {"config": {"ok": False, "error": "Invalid mode"}}             -> use "audit" or "optimize" only

# In tests, in-memory storage keeps file permissions from breaking them
client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(), store_url="sqlite:///:memory:")
```

### Turn on Python logs

Compressors never raise errors, so the log is where you see why content passed through.

```python
import logging
# Everything, with logger names
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# Or only Headroom (a handler must still exist, for example from basicConfig())
logging.getLogger("headroom").setLevel(logging.DEBUG)
```

### Read the session stats

```python
stats = client.get_stats()
print(stats["config"]["mode"])                       # should be "optimize"
print(stats["transforms"]["smart_crusher_enabled"])  # is SmartCrusher on?
print(stats["session"]["tokens_saved_total"])        # 0 means nothing was saved
```

### Simulate the transforms

`simulate()` shows which transforms would apply and what the optimized messages look like. Use it to measure your own traffic instead of trusting published figures. See [observability](./observability.md) for more on simulation.

```python
import json
plan = client.chat.completions.simulate(model="gpt-4o", messages=messages)
print(f"Tokens: {plan.tokens_before} -> {plan.tokens_after}")
print(f"Transforms: {plan.transforms}")
print(f"Waste signals: {plan.waste_signals}")
print(json.dumps(plan.messages_optimized, indent=2))
```

### Test one transform in isolation

Isolate SmartCrusher when you suspect the transform rather than your setup. `Tokenizer` has no zero-argument form, because it wraps a provider-specific token counter.

```python
import json
from headroom import SmartCrusher, Tokenizer, OpenAIProvider
from headroom.config import SmartCrusherConfig

crusher = SmartCrusher(SmartCrusherConfig())
tokenizer = Tokenizer(OpenAIProvider().get_token_counter("gpt-4o"), "gpt-4o")
messages = [{"role": "tool", "content": json.dumps({"items": list(range(100))}), "tool_call_id": "1"}]

result = crusher.apply(messages, tokenizer)
print(f"Tokens: {result.tokens_before} -> {result.tokens_after}")
```

### Other signals to read

- **Claude Code:** run `/context all` in a fresh session, before you send a message, to see whether tool schemas are deferred.
- **Proxy log:** when Claude Code tool deferral is off, the proxy prints a one-time hint that names the fix.
- **Windows startup log:** look for `Pinned ORT_DYLIB_PATH to bundled ONNX Runtime`.
- **Dashboard:** in cache mode, read the Prefix Cache Impact panel and the Compression vs Cache tile, not only "Tokens Saved".

### Report a bug

When you file an issue at [github.com/headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom/issues), include your Headroom version (`pip show headroom-ai`), Python version, provider, debug log output and minimal reproduction code.

## Fixes in detail

The `HeadroomConfig` snippets below show only the fields to change. See [configuration](./configuration.md) for how to apply a config to your client.

### No token savings

Fix the mode first, then the threshold. Code and grep results pass through by design, and data with high uniqueness does not compress, so neither shows savings.

```python
# 1. Compress instead of observe ("audit" modifies nothing)
client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(), default_mode="optimize")

# 2. Or override per request
response = client.chat.completions.create(model="gpt-4o", messages=messages, headroom_mode="optimize")

# 3. Let smaller tool outputs reach SmartCrusher
config = HeadroomConfig()
config.smart_crusher.min_tokens_to_crush = 100  # default 200
```

Trade-off: a lower threshold compresses more tool outputs, but on small payloads the overhead can exceed the savings.

In TypeScript, `compress()` reports savings in camelCase fields. Make sure the proxy runs in optimize mode – the default, unless someone started it with `--no-optimize`.

```ts
import { compress } from 'headroom-ai';

const result = await compress(messages, { model: 'gpt-4o' });
console.log(`Saved: ${result.tokensSaved} tokens`);
console.log(`Compressed: ${result.compressed}`);
```

### Dashboard reads about 0 tokens saved

Since 0.31.0, the default `coding` savings profile runs the proxy in cache mode. Cache mode compresses only the newest turn delta, so the savings shift to cheaper prefix-cache reads. The "Tokens Saved" tile counts only compression, so it understates cache-mode savings. On a short prompt, the tile can read about 0 while your cost still drops.

To compare against visible compression, run token mode for a diagnostic session. Savings profiles are covered in [proxy](./proxy.md).

```bash
headroom proxy --mode token                       # token mode for one run
HEADROOM_SAVINGS_PROFILE=balanced headroom proxy  # token-mode profile, ~70% target
HEADROOM_SAVINGS_PROFILE=agent-90 headroom proxy  # token-mode profile, ~90% target
```

Do not keep token mode permanently to raise the headline number. Token mode rewrites prior turns, so compression goes up while cache-read savings go down. For long coding sessions, preserving the prefix cache usually wins overall.

### Compression too aggressive

SmartCrusher always keeps errors, anomalies and change points (see [Adaptive K](#adaptive-k-what-smartcrusher-always-keeps)). If the model misses ordinary items, keep more of them, or turn SmartCrusher off:

```python
config = HeadroomConfig()
config.smart_crusher.max_items_after_crush = 50  # 1. keep more items (default 15)
config.smart_crusher.enabled = False             # 2. or disable SmartCrusher entirely
```

Trade-off: each retained item costs tokens. Disabling SmartCrusher gives up JSON array compression, the primary use case.

Do not reach for `headroom_tool_profiles={...}` on `client.chat.completions.create()`. The troubleshooting page states that in 0.37.0 the argument is accepted but never read, and no transform in the 0.40.0 source reads it either, so it changes nothing. The per-tool `CompressionProfile` has only `bias`, `min_k` and `max_k`. It has no `skip_compression` key, and a plain dict there would raise `AttributeError` if anything read it.

### High latency

Measure first, then cut the work you do not need:

```python
import logging, time
logging.basicConfig(level=logging.DEBUG)
start = time.time()
response = client.chat.completions.create(...)
print(f"Total time: {time.time() - start:.2f}s")

config = HeadroomConfig()
config.smart_crusher.relevance.tier = "bm25"    # faster than embeddings
config.smart_crusher.min_tokens_to_crush = 500  # skip small payloads
config.cache_aligner.enabled = False            # disable transforms you do not need
```

Each change has a cost. BM25 (Best Matching 25) gives up embedding-based relevance scoring. A higher threshold leaves more tool outputs uncompressed. The troubleshooting page warns that disabling CacheAligner can lower prefix cache hit rates. The more specific cache-optimization page says CacheAligner is off by default and only reports prefix drift, so turning it off costs you only those reports – see [ccr-and-caching](./ccr-and-caching.md).

Do not look for a rolling-window setting. The stage that dropped messages from history was retired, and `HeadroomConfig` has no `rolling_window` field.

### Windows: ML content detection hangs

The Rust core loads Open Neural Network Exchange (ONNX) Runtime dynamically. Without `ORT_DYLIB_PATH`, Windows 11 24H2+ resolves `onnxruntime.dll` to `C:\Windows\System32\onnxruntime.dll`, the Windows ML component (1.17.x). That copy deadlocks session start instead of returning an error. As a result, every proxied request can stall (historically `Optimization failed: TimeoutError`). Alternatively, the first detection in each process takes about 5 seconds, and detection drops to the non-ML fallback tiers, which lowers compression quality. The log may show `magika ONNX session init timed out`.

Headroom pins `ORT_DYLIB_PATH` at import time to the dynamic-link library (DLL) in the `onnxruntime` pip package, which `headroom-ai[proxy]` includes. Confirm the pin in the startup log: `Pinned ORT_DYLIB_PATH to bundled ONNX Runtime: ...\onnxruntime\capi\onnxruntime.dll`. A library install without `onnxruntime` skips the pin. Install the package, or point the variable at any modern ONNX Runtime:

```powershell
pip install onnxruntime                              # enables the automatic pin
$env:ORT_DYLIB_PATH = "C:\path\to\onnxruntime.dll"   # or point at any modern ONNX Runtime yourself
```

`HEADROOM_MAGIKA_INIT_TIMEOUT_SECS` (default `5`) caps the session start as a safety net. On timeout, detection falls back to the non-ML tiers for the rest of the process lifetime. You avoid the hang, but compression quality stays lower until the process restarts.

### Installation problems

```bash
# pipx picked an old release: name a supported interpreter
pipx list
pipx install --python python3.13 "headroom-ai[all]"
# C++11 compiler missing
apt-get install -y build-essential && pip install headroom-ai   # Linux, Debian-based, Docker
xcode-select --install && pip install headroom-ai              # macOS
# Installed in the wrong environment
pip show headroom-ai
source venv/bin/activate
pip install --upgrade headroom-ai
# Corrupt or stale uv cache (also the first fix for the Defender block below)
uv cache clean                  # or one package: uv cache clean litellm
uv tool install "headroom-ai[all]"
```

pipx resolves packages inside its own virtual environment. If that Python has no Headroom wheels yet, pip may skip newer releases and pick the newest build it can use. Uninstall first, or reinstall with the supported interpreter. To pin a release, append `==<version>` to the package name in the same command.

When you build a Docker image, install `build-essential`, install Headroom and purge the build tools in one `RUN` layer, so the tools do not stay in the image. The optional extras are `[proxy]` for the proxy server, `[relevance]` for embedding-based relevance scoring, `[code]` for tree-sitter code compression and `[all]` for everything.

**Windows Defender blocks `sg.exe`.** The install fails on the `ast-grep-cli` 0.44.1 wheel with `Threat: Trojan:Win64/Lazy!MTB`. Because `ast-grep` is a base dependency, the `[proxy]` extra fails too. Headroom uses `ast-grep` only for optional abstract syntax tree (AST) outlining of Read output, and it runs normally without it.

The page is inconsistent about this release: one section calls the detection a false positive, and another calls 0.44.1 a compromised supply-chain build. Headroom's pin (`ast-grep-cli>=0.30.0,!=0.44.1`) excludes the release, so clear the uv cache and reinstall to let the resolver pick a release the pin allows. If that fails, run the proxy in Docker (`ghcr.io/headroomlabs-ai/headroom`; see [getting-started](./getting-started.md)), which installs no local wheel. The page also lists restoring `sg.exe` from quarantine and, as a last resort, a temporary Defender exclusion scoped to the uv tools directory. Given the supply-chain warning, avoid both for 0.44.1, and never disable Defender wholesale.

### Provider problems

Fail fast on a missing key instead of letting the provider reject the request:

```python
import os
from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
client = HeadroomClient(original_client=OpenAI(api_key=api_key), provider=OpenAIProvider())
```

For Anthropic, use the same pattern with `Anthropic(api_key=api_key)` from `anthropic` and `AnthropicProvider()`.

To rule out the proxy on a 502 or 503, check that the key is set, then call the provider directly. Avoid `echo $OPENAI_API_KEY`, because it prints the secret to the terminal and into any captured session log.

```bash
test -n "$OPENAI_API_KEY" && echo "OPENAI_API_KEY is set"   # or ANTHROPIC_API_KEY
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

For custom or fine-tuned models, declare the context limit to stop unknown model warnings:

```python
client = HeadroomClient(original_client=OpenAI(), provider=OpenAIProvider(),
                        model_context_limits={"ft:gpt-4o-2024-08-06:my-org::abc123": 128000, "my-custom-model": 32000})
```

## Claude Code through a custom `ANTHROPIC_BASE_URL`

Pointing Claude Code at Headroom through `ANTHROPIC_BASE_URL` triggers three client-side behaviors. Claude Code decides each one before any request reaches the proxy. For Claude Code setup itself, see [coding-agents](./coding-agents.md).

### Larger context window: keep tool search on

Claude Code normally defers most tool schemas behind its server-side Tool Search Tool. It sends tool names and loads full schemas on demand, but only when it believes it talks to `api.anthropic.com` directly. With a custom host, it loads every schema eagerly. In `/context all`, the "System tools" and "MCP tools" lines then grow by tens of thousands of tokens before your first message (MCP is the Model Context Protocol). No proxy header can reverse this, but `ENABLE_TOOL_SEARCH` can:

```bash
headroom wrap claude                       # sets ENABLE_TOOL_SEARCH=true for you
headroom wrap claude --tool-search auto    # true (default) = always defer; auto or auto:N = defer only
                                           # when tool definitions exceed N% of the budget; false = off
ENABLE_TOOL_SEARCH=true ANTHROPIC_BASE_URL=http://localhost:8787 claude   # running claude yourself
```

The proxy forwards `tool_reference` blocks, so deferral works end to end – streaming and non-streaming, subscription and API-key auth. Verify with `/context all` in a fresh session, before you send a message ([issue #746](https://github.com/headroomlabs-ai/headroom/issues/746) has the full analysis):

| Section | Eager (no `ENABLE_TOOL_SEARCH`) | Deferred (`ENABLE_TOOL_SEARCH=true`) |
| --- | --- | --- |
| System tools | Fully materialized | Deferred subset |
| MCP tools | Every tool shows a token cost | `(loaded on-demand)`, 0 tokens |

**VS Code exception.** The Claude Code VS Code extension does not render the deferred-tool content blocks. Tool results show as `unsupported content type`, while the standalone `claude` command works. For that target, set `ENABLE_TOOL_SEARCH=false` and restart the Headroom deployment ([issue #2028](https://github.com/headroomlabs-ai/headroom/issues/2028)). The trade-off is the larger context window inside VS Code.

### Remote Control unavailable

The Remote Control menu is missing, and `/remote-control` reports `Remote Control is only available when using Claude via api.anthropic.com`. Claude Code v2.1.196 and later compares the `ANTHROPIC_BASE_URL` host against `api.anthropic.com` exactly, so a loopback address fails. Remote Control also ignores `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL`, the flag that re-enables the 1M context window and on-demand tool loading. Headroom restores some features server-side, for example `--1m` restores the `context-1m` beta header. It cannot do that here, because Remote Control eligibility and its bridge connection both live in the client.

Start sessions that need Remote Control without `ANTHROPIC_BASE_URL`, and use Headroom for the rest:

```bash
env -u ANTHROPIC_BASE_URL claude   # needs Remote Control: make sure the variable is unset
headroom wrap claude               # everything else: through Headroom
```

Do not set `ANTHROPIC_UNIX_SOCKET` as a workaround. It passes the host check, but the variable is reserved for `claude ssh`, so Claude Code classifies the session as API-key auth. Remote Control requires claude.ai subscription auth, so the variable opens one gate and closes the other. On Claude Code 2.1.198 with `headroom proxy --uds`, requests fail with `Could not resolve authentication method` even after a subscription login.

The only candidate route left is a man-in-the-middle front end set through `HTTPS_PROXY`, with a locally generated certificate authority trusted through `NODE_EXTRA_CA_CERTS`. It is tracked in [issue #1779](https://github.com/headroomlabs-ai/headroom/issues/1779), and the page gives no ready setup for it. The upstream request to allow loopback proxies is [anthropics/claude-code#76653](https://github.com/anthropics/claude-code/issues/76653). `headroom proxy --uds` stays useful as a transport, and `ENABLE_TOOL_SEARCH` can stay on.

### Server-managed settings unavailable

Settings pushed from **Admin Settings > Claude Code > Managed settings** in the claude.ai console do not apply through Headroom. Claude Code skips the server-managed settings fetch when `ANTHROPIC_BASE_URL` names any non-default host, so the request never reaches Headroom. Anthropic keeps this boundary on purpose, because a proxy in the path could otherwise forge org policy. Headroom has no fix ([issue #3074](https://github.com/headroomlabs-ai/headroom/issues/3074)).

Deploy the same policy as endpoint-managed settings instead: a mobile device management (MDM) profile, the Windows registry, or a local `managed-settings.json`. Claude Code reads those from local disk at startup, so proxying does not affect them. The local file lives in `/Library/Application Support/ClaudeCode/` on macOS, `/etc/claude-code/` on Linux and `C:\Program Files\ClaudeCode\` on Windows.

If the local file does not take effect, the cause is the path, the permissions or the JSON syntax – not Headroom. Debug it from Claude Code's own log:

```bash
claude --debug-file <path>   # then search the log for "Remote settings"
```

## Limitations

### When Headroom helps and when it does not

Each figure is a directional, single-sample measurement taken with `compress()` on a synthetic payload of that shape. Treat none of them as a guarantee, and measure your own traffic with `client.chat.completions.simulate()`. To reproduce figures of this kind exactly, run `uv run python benchmarks/index_proof_table.py --seed 20260902` from a checkout of the Headroom repository.

| Content | Compression (single sample) | Latency impact |
| --- | --- | --- |
| JSON arrays of dicts (search results, API responses, database rows) – the primary use case | About 52% (200 items) | Net win on Sonnet and Opus |
| JSON arrays of strings (file paths, log lines, tags) | About 95% (300 items) | Net win |
| JSON arrays of numbers (metrics, time series) | About 97% (500 items) | Net win |
| Mixed-type JSON arrays | About 45% (200 items) | Net win |
| Structured logs as JSON | Varies widely with duplication | Net win |
| Multi-turn agent conversations | Not independently measured | Break-even to net win |
| Plain text (documentation, articles) | Needs the optional `kompress` ML text path | Adds latency; cost savings only |
| Code | Passthrough | Minimal overhead |
| Retrieval-augmented generation (RAG) document contexts | Passthrough | Minimal overhead |

Headroom adds the most value to long agent sessions with accumulated tool outputs, JSON-heavy workflows, build and test output, and multi-tool agents, where repeated tool results compound the savings. It adds little to short conversational exchanges, where overhead can exceed savings. It also adds little to code-only sessions, because code passes through, and to single-turn requests with no accumulated context.

### What passes through unchanged

- **Short messages** under the content router minimum: 50 tokens by default, set anywhere from 10 to 250 by savings profiles. The page calls this setting both `min_tokens_to_compress` and `min_tokens`.
- **Source code**, to preserve correctness.
- **grep and search results**, which are already compact.
- **System prompts**, to keep the prefix cache compatible.
- **Images**, which the limitations page counts at a fixed cost of about 1,600 tokens. The [compression](./compression.md) skill covers image compression, so check it before you rely on this.

### Code mostly passes through, on purpose

The limitations page treats code as passthrough. The compression pages add that the proxy routes code to the AST-aware compressor by default and library `compress()` sends it to Kompress – see [compression](./compression.md). Either way, the AST-aware CodeCompressor (tree-sitter; Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Perl, C# and PHP) sits behind three safety gates, so it rarely fires on real traffic:

1. **Size.** Messages under the content router minimum (50 tokens by default) and blocks under `min_chars_for_block_compression` (500 characters) are skipped. Both are counted in tokens or characters, never words.
2. **Recent code** (`protect_recent_code=4`). Code in the last 4 messages is never compressed.
3. **Analysis intent** (`protect_analysis_context=True`). If the latest user message contains keywords like "analyze", "review", "explain", "fix" or "debug", all code in the conversation is protected.

Users fetch code to work with it, and compressing function bodies removes exactly what they need. Headroom never drops messages from the history or strips function bodies. For aggressive code compression, set `protect_analysis_context=False` in `ContentRouterConfig` (content routing is covered in [compression](./compression.md)). The trade-off is the risk the default prevents: the model can lose code it needs.

```python
# Needs headroom-ai[code] for tree-sitter
router_config = ContentRouterConfig(protect_analysis_context=False)
```

### JSON compression constraints

| Compressed | How |
| --- | --- |
| Arrays of dicts | Statistical analysis with adaptive K |
| Arrays of strings | Deduplication, adaptive sampling and error preservation |
| Arrays of numbers | Statistical summary that keeps outliers and change points |
| Mixed-type arrays | Grouped by type, and each group compressed on its own |
| Nested objects | Recursed into, and arrays inside compressed, up to depth 5 |

These pass through untouched: arrays under 5 items (`min_items_to_analyze`), content under 200 tokens (`min_tokens_to_crush`), bool-only arrays and JSON objects without array values. Malformed JSON also passes through, silently and with no error. If one JSON tool shows no savings, check that its output parses with `json.loads()`.

Edge cases: `NaN` and `Infinity` are filtered out before statistics are computed. Arrays nested deeper than 5 levels are not examined. Mixed-type groups smaller than `min_items_to_analyze` stay as they are.

### Safety gates: every compressor fails open

- Invalid JSON passes through, and no error is raised.
- An AST parse failure falls back to the original content.
- Compression that would make the output larger returns the original.
- A missing optional dependency (tree-sitter) causes a passthrough with a warning log.
- Errors are logged at WARNING level and never propagated to the caller.

LLMLingua is not part of Headroom, so ignore older guides that install the `[llmlingua]` extra – it was removed. Text compression goes through the Kompress (ModernBERT ONNX) path, which fails open like every other compressor.

### Adaptive K: what SmartCrusher always keeps

SmartCrusher sizes its sample (K) from the data instead of using a fixed number. The Kneedle algorithm on bigram coverage curves finds where more items stop adding information. SimHash fingerprints detect near-duplicates, and zlib validation checks that the subset captures the full set's diversity. K is split 30% from the array start, 15% from the end and 55% for importance-scored items. These items are always kept, even beyond the K budget:

- Error items containing "error", "exception", "failed" or "critical", in all array types
- Numeric anomalies more than 2 standard deviations from the mean
- String-length anomalies more than 2 standard deviations from the mean length
- Change points, where running values shift suddenly

Failures and outliers therefore survive compression. When answers miss ordinary items, raise `max_items_after_crush`. To keep more anomalies, lower `variance_threshold`.

### Tuning parameters

| Parameter | Default | Effect |
| --- | --- | --- |
| `min_items_to_analyze` | 5 | Arrays below this pass through |
| `min_tokens_to_crush` | 200 | Content below this passes through |
| `max_items_after_crush` | 15 | Upper bound on retained items |
| `variance_threshold` | 2.0 | Standard deviations for anomaly detection; lower keeps more |
| `protect_analysis_context` | True | Protects code when the user asks about it |
| `protect_recent_code` | 4 | Messages from the end in which code is protected |
| `skip_user_messages` | True | Never compresses user messages |
| `toin_confidence_threshold` | 0.3 | Minimum Tool Output Intelligence Network (TOIN) confidence to apply hints |

### Provider interactions

- The limitations page says CacheAligner maximizes Anthropic and OpenAI prefix cache hit rates. The cache-optimization page says it only reports prefix drift, while cache mode keeps prefixes stable. See [ccr-and-caching](./ccr-and-caching.md).
- Token counting uses tiktoken for OpenAI and a calibrated estimate for Anthropic, so treat Anthropic counts as estimates.
- Compression works with all providers, with no provider-specific limitations.
- Compressed content stays valid JSON, so downstream tools and parsers work unchanged.

### TOIN cold start

TOIN learns compression patterns from usage. A new tool type has no learned patterns, so compression falls back to statistical heuristics. Hints with confidence below `toin_confidence_threshold` (0.3) are ignored. Patterns build up as the tool is used repeatedly. Cross-session learning needs persistence through `TelemetryConfig.storage_path`, and without it learned patterns do not carry over between sessions.

### Telemetry and the upload beacon

Headroom has two independent switches with different defaults:

| Variable | Default | What it does |
| --- | --- | --- |
| `HEADROOM_TELEMETRY` | Off (opt in) | Aggregates compression stats locally for the in-process collector and the `/stats` endpoint. Never leaves the machine. |
| `HEADROOM_BEACON` | On (opt out) | Uploads an anonymous summary: token totals, compression ratios, skip reasons, provider and model identifiers, failure counts, operating system and architecture. Never prompts, completions, code or file paths. |

To stop the upload, use one of the documented values exactly, or run offline:

```bash
export HEADROOM_BEACON=off   # or: export DO_NOT_TRACK=1
```

Do not guess other spellings. `is_beacon_enabled()` fails open, so an unrecognized value uploads rather than staying silent. Turning on local `/stats` does not start an upload, because the two switches are separate by design. The full beacon field list is in [proxy](./proxy.md).

## Environment variables at a glance

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENABLE_TOOL_SEARCH` | Set to `true` by `headroom wrap claude` | Keeps Claude Code tool schemas deferred through the proxy |
| `HEADROOM_SAVINGS_PROFILE` | `coding` (cache mode) | `balanced` (about 70% target) and `agent-90` (about 90% target) run token mode |
| `HEADROOM_MAGIKA_INIT_TIMEOUT_SECS` | `5` | Caps the start of ML content detection |
| `ORT_DYLIB_PATH` | Pinned at import to the bundled ONNX Runtime | Points Headroom at a modern ONNX Runtime on Windows |
| `HEADROOM_TELEMETRY` | Off | Local stats for the collector and `/stats` |
| `HEADROOM_BEACON` | On | `off` stops the anonymous upload |
| `DO_NOT_TRACK` | Unset | `1` stops the anonymous upload |

## Do and don't

| Do | Don't | Why |
| --- | --- | --- |
| Set `default_mode="optimize"` or `headroom_mode="optimize"` | Leave the client in `audit` and expect savings | `audit` observes and modifies nothing |
| Judge cache-mode savings on the Prefix Cache Impact panel | Switch to token mode for good to raise "Tokens Saved" | Token mode rewrites prior turns and can cost prefix-cache hits |
| Raise `max_items_after_crush` when facts go missing | Pass `headroom_tool_profiles` | The argument is accepted but ignored |
| Measure your traffic with `simulate()` | Quote the single-sample percentages as guarantees | Each comes from one synthetic payload |
| Keep `ENABLE_TOOL_SEARCH=true` for the `claude` command | Keep it on for the VS Code extension | The extension shows `unsupported content type` |
| Start Remote Control sessions without `ANTHROPIC_BASE_URL` | Set `ANTHROPIC_UNIX_SOCKET` | It switches the session to API-key auth |
| Ship org policy as endpoint-managed settings | Expect server-managed settings through any proxy | Claude Code skips the fetch for non-default hosts |
| Clear the uv cache or use Docker when Defender flags `sg.exe` | Restore `sg.exe` from quarantine or disable Defender | One section of the page calls 0.44.1 a compromised supply-chain build |
| Use `sqlite:///:memory:` storage in tests | Point tests at a path you cannot write | `validate_setup()` reports `unable to open database` |
| Use exactly `HEADROOM_BEACON=off` or `DO_NOT_TRACK=1` | Invent other values | Unrecognized values upload |

## Related skills

- [getting-started](./getting-started.md) – installation, the Docker-native wrapper and persistent installs.
- [proxy](./proxy.md) – proxy command-line options, savings profiles, API endpoints and agent wrapping.
- [configuration](./configuration.md) – applying `HeadroomConfig`, per-request overrides, environment variables and model limits.
- [compression](./compression.md) – content routing, SmartCrusher, and the code, image, text and log compressors.
- [ccr-and-caching](./ccr-and-caching.md) – Compress-Cache-Retrieve (CCR), cache optimization and context management.
- [coding-agents](./coding-agents.md) – Claude Code setups (VS Code, Vertex AI, Azure AI Foundry) and other coding agents.
- [observability](./observability.md) – savings tracking, metrics, Prometheus and simulation.
- [sdk-reference](./sdk-reference.md) – Python and TypeScript API reference and error handling.
- [framework-integrations](./framework-integrations.md) – OpenAI SDK, Anthropic SDK, LangChain and other framework wrappers.
- [architecture-and-security](./architecture-and-security.md) – architecture, security model and benchmarks.

## Source pages

- https://docs.headroomlabs.ai/docs/troubleshooting
- https://docs.headroomlabs.ai/docs/limitations
