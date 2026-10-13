# Headroom: Getting started
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill to pick a way to run Headroom, install it, make a first compressed call and keep the proxy running. Headroom is a context-compression layer for large language model (LLM) applications. It ships as a Python package (`headroom-ai`, imported as `headroom`), a TypeScript software development kit (SDK) on npm (`headroom-ai`), a local proxy server and a `headroom` command-line interface (CLI).

## Core concepts

- Headroom compresses what your agent reads before it reaches the LLM: tool outputs, database results, file reads, retrieval-augmented generation (RAG) results and API responses. The model sees less noise, responds faster and costs less.
- Headroom sits between your agent and the LLM provider: OpenAI, Anthropic, Google, Bedrock, or 100+ providers through LiteLLM.
- Headroom detects each content type and routes it to a matching compressor. The default routes need no configuration.
- Headroom compresses fresh tool output and new turns only. It does not drop conversation history – the score-based history-dropping features IntelligentContext and RollingWindow are retired.
- Nothing is lost. Headroom puts compressed content into the Compress-Cache-Retrieve (CCR) store. The LLM gets a `headroom_retrieve` tool and can fetch the full original when it needs more detail. Compression is aggressive but reversible – see [ccr-and-caching](./ccr-and-caching.md).
- Savings depend on how repetitive the content is. On seeded test data built from real Model Context Protocol (MCP) server output formats, savings range from 21% (code search over 100 results) to 57% (incident debugging). Treat such numbers as a shape, not a promise.

| Content | Compressor | Behavior |
| --- | --- | --- |
| JSON arrays (tool outputs) | SmartCrusher | Keeps errors, anomalies (values outside the normal statistical range) and first and last boundaries. It finds them by statistical analysis of field variance, not keyword matching |
| Source code | CodeAwareCompressor | Abstract syntax tree (AST) aware: keeps signatures, collapses bodies. On by default in `headroom proxy`; library `compress()` and `HeadroomClient` send code to Kompress instead |
| Build and test logs | LogCompressor | Keeps failures and errors, drops passing noise |
| Search results | SearchCompressor | Ranks by relevance, keeps top matches |
| Plain text | Kompress | Removes redundancy with ModernBERT token classification |
| Git diffs | – | Keeps change hunks, drops unchanged context |
| Images | – | A machine learning (ML) router picks the resize and quality trade-off |

The Introduction calls code compression opt-in and disabled by default. The more specific code-compression page says the proxy turns it on by default, so this skill follows that page. The getting-started pages do not name the diff and image compressors. See [compression](./compression.md) for the routing details.

## Choose how to use Headroom

| Way | Code changes | Pick it when | Entry point |
| --- | --- | --- | --- |
| Proxy | None | Your client accepts a base URL and you want zero code changes | `headroom proxy --port 8787` |
| Python `compress()` | One call before each LLM request | You write Python and want per-call control and token counts | `from headroom import compress` |
| TypeScript `compress()` | One call per request, plus a running proxy | You write TypeScript or Node.js | `import { compress } from 'headroom-ai'` |
| Framework integration | Swap in a wrapper or middleware | You use LangChain, Agno, Strands, LiteLLM, the Vercel AI SDK or MCP, or want `withHeadroom` SDK wrapping in TypeScript | [framework-integrations](./framework-integrations.md) |
| Coding-agent wrap | None | You use Claude Code, Codex, Aider, Cursor or OpenClaw | `headroom wrap <tool>` |
| Persistent install | None after setup | You want the proxy to keep running instead of starting it ad hoc | `headroom deploy` |

- The proxy needs no code changes, so you can measure savings on an existing app without touching its code. The trade-off is one more local process that must stay up – a persistent install handles that.
- `compress()` returns a result with token counts for every call, so you see exactly what changed. The trade-off is a call in every request path.
- The core Python package contains `compress()`, so Python needs no proxy. The TypeScript SDK sends messages to the proxy over HTTP, because the compression pipeline runs in Python.
- A framework integration plugs into the abstraction you already use, so you write less glue code.
- `headroom wrap` starts a proxy that lasts for the wrapped session and launches the tool. With a persistent install, the Python-native `wrap` reuses that deployment instead of starting a second proxy.

## Quickstart pattern

The pattern is the same in both languages. Compress the message list, send `result.messages` to your LLM client exactly like the originals, then read the savings from the result.

### Python

```bash
uv tool install --python 3.13 "headroom-ai[all]"   # host-level CLI (proxy, wrap)
pip install "headroom-ai[all]"                      # inside a Python project or virtualenv
```

```python
import json
from headroom import compress
from openai import OpenAI

search_results = json.dumps({"results": [
    {"title": f"Result {i}", "snippet": f"Description {i}", "score": 100 - i}
    for i in range(500)
]})

messages = [
    {"role": "system", "content": "You analyze search results."},
    {"role": "user", "content": "Search for Python tutorials."},
    {"role": "assistant", "content": None, "tool_calls": [{
        "id": "call_1", "type": "function",
        "function": {"name": "search", "arguments": '{"q": "python"}'},
    }]},
    {"role": "tool", "tool_call_id": "call_1", "content": search_results},
    {"role": "user", "content": "What are the top 3 results?"},
]

result = compress(messages, model="gpt-4o")

client = OpenAI()
response = client.chat.completions.create(model="gpt-4o", messages=result.messages)
print(response.choices[0].message.content)

print(f"Tokens: {result.tokens_before} -> {result.tokens_after}")
print(f"Saved:  {result.tokens_saved} ({result.tokens_saved / result.tokens_before:.0%})")
print(f"Transforms: {result.transforms_applied}")  # e.g. ['smart_crusher', 'cache_aligner']
```

### TypeScript

```bash
npm install headroom-ai
uv tool install --python 3.13 "headroom-ai[proxy]"   # or, in a Python project: pip install "headroom-ai[proxy]"
headroom proxy --port 8787                            # keep this running
```

```ts
import { compress } from 'headroom-ai';
import OpenAI from 'openai';

const searchResults = JSON.stringify({
  results: Array.from({ length: 500 }, (_, i) => ({
    title: `Result ${i}`, snippet: `Description ${i}`, score: 100 - i,
  })),
});

const messages = [
  { role: 'system' as const, content: 'You analyze search results.' },
  { role: 'user' as const, content: 'Search for Python tutorials.' },
  { role: 'assistant' as const, content: null, tool_calls: [{
    id: 'call_1', type: 'function' as const,
    function: { name: 'search', arguments: '{"q": "python"}' },
  }] },
  { role: 'tool' as const, tool_call_id: 'call_1', content: searchResults },
  { role: 'user' as const, content: 'What are the top 3 results?' },
];

const result = await compress(messages, { model: 'gpt-4o', baseUrl: 'http://localhost:8787' });

const client = new OpenAI();
const response = await client.chat.completions.create({ model: 'gpt-4o', messages: result.messages });
console.log(response.choices[0].message.content);

// compressionRatio is tokensAfter / tokensBefore, so savings is 1 - ratio.
console.log(`Saved ${result.tokensSaved} tokens (${((1 - result.compressionRatio) * 100).toFixed(0)}%)`);
console.log(`Transforms: ${result.transformsApplied.join(', ')}`);
```

If you omit `baseUrl`, the TypeScript SDK uses `HEADROOM_BASE_URL`, which defaults to `http://localhost:8787`.

### Result fields

| Meaning | Python | TypeScript |
| --- | --- | --- |
| Compressed messages, same format as input | `result.messages` | `result.messages` |
| Tokens before and after | `tokens_before`, `tokens_after` | `tokensBefore`, `tokensAfter` |
| Tokens removed | `tokens_saved` | `tokensSaved` |
| Compression ratio | `compression_ratio` | `compressionRatio` |
| Transforms that ran | `transforms_applied` | `transformsApplied` |
| CCR hashes for retrieval | – | `ccrHashes` |
| Whether compression ran | – | `compressed` |

The getting-started pages show `ccrHashes` and `compressed` for TypeScript only. See [sdk-reference](./sdk-reference.md) for the full result types.

### Read the compression ratio correctly

The docs define the TypeScript `compressionRatio` as `tokensAfter / tokensBefore`. Lower is better, and savings is `1 - compressionRatio`. The getting-started pages do not define the Python `compression_ratio`. The Python examples print it directly as a percentage, and the Quickstart shows "Compression: 90%" for a 45000 to 4500 token run. That number is the savings, not after over before. Derive savings from the token counts so your numbers are right either way.

```python
# Don't: label the raw ratio as savings
print(f"Saved {result.tokens_saved} tokens ({result.compression_ratio:.0%})")

# Do: derive savings from the token counts
print(f"Saved {result.tokens_saved} tokens ({result.tokens_saved / result.tokens_before:.0%})")
```

## Proxy mode (zero code changes)

```bash
headroom proxy --port 8787

ANTHROPIC_BASE_URL=http://localhost:8787 claude        # Claude Code: no /v1 suffix
OPENAI_BASE_URL=http://localhost:8787/v1 your-app      # OpenAI-compatible clients: include /v1

curl http://localhost:8787/stats
# {"requests_total": 42, "tokens_saved_total": 125000, ...}

headroom dashboard            # opens http://localhost:8787/dashboard
headroom dashboard --no-open  # prints the URL without opening a browser
```

- All requests from that client then flow through Headroom.
- If the proxy runs on another port, pass `--port` or set `HEADROOM_PORT`, and change the dashboard URL to match.
- For Claude Code inside VS Code, run `headroom wrap vscode-claude`, reload the VS Code window once and keep the wrapper running while you use the official extension. See [coding-agents](./coding-agents.md).

## Install

### Pick an install channel

| Channel | Use it when | Command |
| --- | --- | --- |
| `uv tool` | You want the `headroom` CLI (`deploy`, `proxy`, `wrap`, `doctor`, `mcp`, `learn` and others) once on your machine, in an isolated app environment | `uv tool install --python 3.13 "headroom-ai[all]"` |
| `pip` | You write Python, or you need the CLI whatever language your app uses | `pip install "headroom-ai[all]"` |
| `npm` | You write TypeScript or Node.js 18+ and want inline `compress()`, `withHeadroom` or Vercel AI SDK middleware | `npm install headroom-ai` (or `pnpm add`, `yarn add`) |
| Docker image | You want the proxy in a container | `docker pull ghcr.io/headroomlabs-ai/headroom:latest` |
| Docker-native wrapper | You want a host `headroom` command without Python or Node.js on the host | See [Docker-native wrapper](#docker-native-wrapper) |
| `pipx` | You already use pipx; prefer `uv tool` if you have uv | `pipx install --python python3.13 "headroom-ai[all]"` |

The docs prefer `uv tool` for a host-level CLI on macOS Apple Silicon and Linux. It keeps Headroom in a dedicated app environment instead of tying it to the current project or shell Python. The TypeScript SDK is a library only: it does not install the `headroom` CLI, which ships with the Python package.

### Python platform rules

- Headroom needs Python 3.10+. Release wheels cover CPython 3.10 through 3.13 on Linux (manylinux_2_28 x86_64 and aarch64), macOS (Apple Silicon and Intel) and Windows x86_64. The Rust extension uses the CPython stable application binary interface (ABI), so these wheels also run on newer supported CPython versions. Optional dependencies may set their own limits.
- Pass `--python 3.13`. On macOS with Homebrew, `python3` may point at an interpreter newer than the wheel set. Install 3.13 with `brew install python@3.13`, or let uv download a managed interpreter.
- On Intel macOS, Open Neural Network Exchange (ONNX) Runtime wheels exist through Python 3.13, with the pre-1.24 runtime. With Python 3.14 and newer there, the `proxy`, `voice`, `relevance` and `image` extras omit their optional ONNX backends. Core compression and the proxy still work, but ML content detection, local ONNX Kompress, embedding relevance and ONNX optical character recognition (OCR) do not. Use Python 3.13 if you need them.
- Rust ML detection needs ONNX Runtime 1.24 or newer, so it stays disabled on Intel macOS even with Python 3.13.
- Other platforms fall back to the source distribution, which needs Rust plus the platform C/C++ toolchain. On Windows, `` error: linker `link.exe` not found `` means the Microsoft Visual C++ (MSVC) toolchain is missing. Install Build Tools for Visual Studio with the "Desktop development with C++" workload, install Rust through rustup with the `stable-x86_64-pc-windows-msvc` toolchain, then open a fresh PowerShell. To avoid the source build, run Headroom in Docker.
- With pipx, an unsupported Python can make pipx resolve an older compatible Headroom release instead of the newest one. Pass `--python python3.13`, and check the interpreter with `pipx list`.

### Verify the install

```bash
headroom --version
python -c "import headroom; print(headroom.__version__)"
node -e "const h = require('headroom-ai'); console.log('headroom-ai loaded')"
uv tool update-shell   # if the shell cannot find headroom after a uv install
```

MCP clients such as Codex do not inherit your interactive shell `PATH`. Configure the absolute path that `command -v headroom` returns:

```toml
[mcp_servers.headroom]
command = "/Users/you/.local/bin/headroom"
args = ["mcp", "serve"]
```

### Python extras

The core package (`pip install headroom-ai`) has no heavy dependencies. It includes `compress()`, SmartCrusher, CacheAligner and live-zone ContentRouter compression. Extras add the rest, and you combine them in one install: `pip install "headroom-ai[proxy,langchain,ml]"`.

`[all]` is the built-in runtime bundle: `proxy,code,ml,memory,relevance,image,reports,otel,evals,voice,html,mcp,spreadsheet`. It is not every integration or backend.

| Extra | Enables | In `[all]` |
| --- | --- | --- |
| `proxy` | Proxy server, HTTP API, MCP runtime, local ONNX Kompress path | Yes |
| `code` | CodeAwareCompressor (tree-sitter AST parsing) | Yes |
| `ml` | PyTorch and Hugging Face Kompress backend and model tooling | Yes |
| `memory` | Persistent memory (sqlite-vec, sentence-transformers); pure-Python default backend, no compiler | Yes |
| `relevance` | fastembed relevance scoring (BAAI/bge-small-en-v1.5, ONNX) | Yes |
| `image` | Image compression (Pillow, ONNX Runtime, OCR) | Yes |
| `mcp` | MCP server tools `headroom_compress`, `headroom_retrieve`, `headroom_stats` | Yes |
| `html` | HTML main-content extraction with trafilatura | Yes |
| `spreadsheet` | `.xlsx` and `.xls` ingestion with openpyxl and xlrd | Yes |
| `reports` | HTML and Markdown reports (Jinja2) | Yes |
| `otel` | OpenTelemetry exporter (OpenTelemetry Protocol, OTLP) | Yes |
| `evals` | Evaluation framework (GSM8K, SQuAD, BFCL benchmarks) | Yes |
| `voice` | Voice and audio support | Yes |
| `proxy-prod` | gunicorn for the proxy on Unix production hosts; install as `"headroom-ai[proxy,proxy-prod]"` | No |
| `sandbox` | Torch-free proxy bundle for constrained environments | No |
| `langchain` | LangChain `HeadroomChatModel` wrapper | No |
| `agno` | Agno `HeadroomAgnoModel` wrapper | No |
| `strands` | Amazon Web Services (AWS) Strands Agents integration | No |
| `autogen` | AutoGen AgentChat integration | No |
| `bedrock` | Native AWS Bedrock credentials and backend | No |
| `anyllm` | any-llm multi-provider backend (Python 3.11+) | No |
| `vector` | Hierarchical Navigable Small World (HNSW) vector backend (hnswlib); needs a C++ toolchain | No |
| `memory-stack` | Qdrant and Neo4j memory backend helpers | No |
| `pytorch-mps` | macOS-only Apple graphics processing unit (GPU) offload for the memory embedder; opt in with `HEADROOM_EMBEDDER_RUNTIME=pytorch_mps` | No |
| `voice-train` | Voice training dependencies | No |

CrewAI needs no extra: `pip install headroom-ai crewai`. Full table: [installation#extras](https://docs.headroomlabs.ai/docs/installation#extras).

### Docker image

Every release publishes images to GitHub Container Registry (GHCR). Run the proxy like this:

```bash
docker run --rm -it \
  -p 127.0.0.1:8787:8787 \
  -e HEADROOM_ALLOW_UNAUTHENTICATED_BIND=1 \
  -v "$PWD:/workspace" \
  -w /workspace \
  ghcr.io/headroomlabs-ai/headroom:latest \
  --host 0.0.0.0 --port 8787
```

The proxy must bind `0.0.0.0` inside the container so the published port can reach it. The proxy refuses to start on a non-loopback bind without `HEADROOM_PROXY_TOKEN`, unless you acknowledge that the runtime already restricts who can reach the port. Here the `127.0.0.1` publication is that restriction, and `HEADROOM_ALLOW_UNAUTHENTICATED_BIND=1` is the acknowledgement. The shorter `docker run` example on the Installation page omits this variable, so add it when you copy that example.

| Tag | Extras | Base | Notes |
| --- | --- | --- | --- |
| `latest` | `proxy,bedrock` | Debian slim | Default; runs as non-root |
| `<version>` | `proxy,bedrock` | Debian slim | Pinned release, built from the same version as the matching Python Package Index (PyPI) and npm release |
| `nonroot` | `proxy,bedrock` | Debian slim | Explicit non-root variant |
| `code`, `code-nonroot` | `proxy,code,bedrock` | Debian slim | Adds tree-sitter for code compression |
| `slim`, `slim-nonroot` | `proxy,bedrock` | Distroless | Minimal image, no shell |
| `code-slim`, `code-slim-nonroot` | `proxy,code,bedrock` | Distroless | Code compression in a minimal image |

Pick a `code` tag when you need code compression, because only those tags include the `code` extra (tree-sitter). A `slim` tag gives a minimal Distroless image; the trade-off is that the image has no shell. To build your own variant, list the targets with `docker buildx bake --list targets`, then run, for example, `docker buildx bake runtime-code-slim-nonroot --set '*.tags=my-registry/headroom:code-slim-nonroot'`.

## Key environment variables

Set these in your shell, a `.env` file or the container environment. A dash means the getting-started pages state no default.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HEADROOM_PORT` | `8787` | Port the proxy listens on |
| `HEADROOM_HOST` | `127.0.0.1` | Host the proxy binds to |
| `HEADROOM_MODE` | `cache` | Default optimization mode: `token` or `cache` |
| `HEADROOM_TELEMETRY` | `off` | `on` records local-only usage stats; nothing is sent externally |
| `HEADROOM_REQUEST_TIMEOUT` | `300` | Request timeout in seconds |
| `HEADROOM_BASE_URL` | `http://localhost:8787` | Proxy URL for the TypeScript SDK |
| `HEADROOM_API_KEY` | none | API key for the TypeScript SDK when the proxy requires auth |
| `HEADROOM_PROXY_TOKEN` | – | Token for deliberate public access to the proxy |
| `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` | – | `1` acknowledges a non-loopback bind that the runtime already restricts |
| `HEADROOM_DOCKER_IMAGE` | – | Custom image for the Docker-native installer |
| `HEADROOM_CONTAINER_RUNTIME` | – | `podman` when `docker` is a Podman wrapper script |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | – | Provider keys when the proxy forwards to OpenAI or Anthropic |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | – | Bedrock backend credentials |
| `GOOGLE_APPLICATION_CREDENTIALS` | – | Vertex AI backend credentials |
| `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION` | – | Vertex AI project and region (LiteLLM-specific) |

- Set `VERTEXAI_PROJECT` explicitly. It is distinct from `GOOGLE_CLOUD_PROJECT`, and without it usage can silently bill your Application Default Credentials (ADC) default quota project. `VERTEXAI_LOCATION` is likewise distinct from `GOOGLE_CLOUD_LOCATION`.
- The Vertex AI backend also needs `google-cloud-aiplatform>=1.38`. No extra and no Docker image includes it – see [proxy](./proxy.md).
- See [configuration](./configuration.md) for every other variable.

## Docker-native wrapper

Use the Docker-native wrapper when you want a host `headroom` command without installing Python or Node.js. Docker becomes the only Headroom runtime dependency on the host. Headroom itself runs in a container, while the wrapper runs the rest of your workflow on the host.

```bash
# Linux
curl -fsSL https://raw.githubusercontent.com/headroomlabs-ai/headroom/main/scripts/install.sh | bash

# macOS: stock /bin/bash is 3.2, so run the installer with a bash 4.3+ from Homebrew
curl -fsSL https://raw.githubusercontent.com/headroomlabs-ai/headroom/main/scripts/install.sh | "$(brew --prefix bash)/bin/bash"
```

```powershell
irm https://raw.githubusercontent.com/headroomlabs-ai/headroom/main/scripts/install.ps1 | iex
```

The installer verifies Docker and pulls `ghcr.io/headroomlabs-ai/headroom:latest`, or `HEADROOM_DOCKER_IMAGE` if you set it. It installs the wrapper into `~/.local/bin` or `~/bin` and adds that directory to `PATH` in your shell startup files. On macOS the wrapper pins the bash you installed with, so later runs stay on a supported shell. The scripts are idempotent: rerun them to refresh the wrapper and image without duplicate shell profile blocks.

### What runs where

| Command | Where it runs |
| --- | --- |
| `headroom proxy`, `headroom learn`, `headroom mcp install`, `headroom memory list` | Inside the container |
| `headroom wrap claude`, `codex`, `aider`, `cursor`, `openclaw`; `headroom unwrap openclaw` | Proxy in the container; the wrapper launches the target CLI on the host |

- The wrapper mounts host state into the container so behavior matches a native install: the project workspace as `/workspace`, plus `~/.headroom`, `~/.claude`, `~/.codex` and `~/.gemini`. Container-side `wrap` preparation writes Headroom config and memory into these mounted host files.
- Port `8787` stays the default, so `http://localhost:8787` works as it does with a native install.
- The wrapper forwards variables with these prefixes into the container: `HEADROOM_`, `ANTHROPIC_`, `OPENAI_`, `GEMINI_`, `AWS_`, `GOOGLE_` and `GOOGLE_CLOUD_`, `AZURE_`, `OTEL_`. Provider auth works without a separate env file.
- OpenClaw stays host-native. The host needs the `openclaw` CLI, and plugin auto-start runs the host `headroom` wrapper from `PATH`. Local plugin source mode (`--plugin-path`) may need host `npm` for build steps.

### Network exposure

The wrapper always publishes the proxy port on loopback and passes `--host 0.0.0.0` inside the container. It sets the `HEADROOM_ALLOW_UNAUTHENTICATED_BIND` acknowledgement itself, only together with the `127.0.0.1` publication, and has no public-publication override. For deliberate public access, publish on an explicit public address and require a token:

```bash
docker run --rm -p 0.0.0.0:8787:8787 \
  -e HEADROOM_PROXY_TOKEN='replace-with-a-secret' \
  ghcr.io/headroomlabs-ai/headroom:latest --host 0.0.0.0 --port 8787
```

Don't pair `-p 0.0.0.0:8787:8787` with `HEADROOM_ALLOW_UNAUTHENTICATED_BIND=1`. The acknowledgement asserts that the runtime restricts who can reach the port, and a public publication breaks that assertion.

### Persistent Docker from the wrapper

```bash
headroom install apply --profile default --preset persistent-docker
headroom install status
headroom install restart
headroom install remove
```

- Supported subcommands: `apply`, `status`, `start`, `stop`, `restart`, `remove`.
- Supported flags: `--profile`, `--port`, `--backend`, `--anyllm-provider`, `--region`, `--mode`, `--memory`, `--no-telemetry`, `--image`.
- Not supported: the `persistent-service` and `persistent-task` presets, and the mutation flags `--scope`, `--providers` and `--target`. Use the Python-native CLI for those.
- The wrapper keeps the profile manifest under `~/.headroom/deploy/<profile>/`, and `/health` reports the deployment metadata.

### Docker Compose

Use the shipped `docker/docker-compose.native.yml` when you prefer Compose over the wrapper's `headroom install` commands. Its `proxy` service uses `restart: unless-stopped`, so `up -d` gives you an always-on proxy at `localhost:8787` with no Python on the host.

```bash
export HEADROOM_HOST_HOME="$HOME"
export HEADROOM_WORKSPACE="$PWD"
docker compose -f docker/docker-compose.native.yml up -d proxy      # omit -d to run in the foreground
docker compose -f docker/docker-compose.native.yml run --rm cli learn   # one-off CLI command
```

```powershell
$env:HEADROOM_HOST_HOME = $HOME
$env:HEADROOM_WORKSPACE = (Get-Location).Path
docker compose -f docker/docker-compose.native.yml up -d proxy
```

Don't confuse two similar variables. `HEADROOM_WORKSPACE` is the host directory that Compose mounts as `/workspace`; it behaves like the working directory of a native run. `HEADROOM_WORKSPACE_DIR` is the Headroom state root inside the container. The shipped compose file sets it to `/tmp/headroom-home/.headroom` for you, so savings, logs and memory land in the mounted `${HOME}/.headroom`.

## Persistent installs

| Mode | What stays running | Entry point | Pick it when |
| --- | --- | --- | --- |
| Turnkey deploy | Docker, a scheduled watchdog or a detached runtime, chosen for this host | `headroom deploy` | You want one command and no runtime decisions |
| Persistent service | Native background service | `headroom install apply --preset persistent-service` | You want an always-running service under the operating-system supervisor |
| Persistent task | Scheduled watchdog plus on-demand runner | `headroom install apply --preset persistent-task` | You want scheduled recovery instead of an always-running service |
| Persistent Docker | Restartable Docker container | `headroom install apply --preset persistent-docker` | You want Docker's restart policy instead of an operating-system supervisor |
| On-demand CLI | Nothing after the command or container exits | `headroom proxy`, or the Docker-native wrapper | You run Headroom ad hoc |
| Wrapped | The proxy, for the length of the tool session | `headroom wrap ...` | You want the proxy only while one tool session runs |

`headroom deploy` picks the most capable restartable runtime it can prove is available. On NVIDIA workstations with Docker GPU support (for example an RTX 4090 host with the NVIDIA container runtime), it uses Docker GPU passthrough. Otherwise it prefers plain Docker, then the host's scheduled watchdog (`launchd`, Task Scheduler or cron). With no supported supervisor, it starts a managed detached Python runtime instead of failing. It also configures detected tools, starts the proxy at `http://127.0.0.1:8787` and stores a deployment profile for later lifecycle commands.

Use the Python-native `headroom install` CLI when you need to force a preset, runtime, scope or provider target:

```bash
headroom deploy                  # turnkey: picks the runtime for this host
headroom install status

headroom install apply --preset persistent-service --providers auto
headroom install apply --preset persistent-task --providers manual --target claude --target codex
headroom install apply --preset persistent-docker --scope user --providers auto
```

### Lifecycle commands

- The subcommands are `apply`, `status`, `start`, `stop`, `restart` and `remove`.
- `apply` creates or updates a named deployment profile and stores its manifest at `~/.headroom/deploy/<profile>/manifest.json`. It applies reversible configuration changes and starts the runtime.
- `status` reports the default backend separately from the Anthropic and OpenAI protocol targets. Each target shows `configured`, `default` or `unknown`. `unknown` means the health response lacked that target's configuration, not that the target is unset. `status` never prints target URLs or credentials.
- `--runtime python` runs `headroom proxy` directly, and `--runtime docker` runs Headroom in Docker with local management. The `persistent-docker` preset always uses Docker.

| Option | Meaning |
| --- | --- |
| `--providers auto` | Detect supported tools on the host and configure the best defaults |
| `--providers all` | Configure all known targets |
| `--providers manual --target <tool>` | Configure only the named tools; repeat `--target` |
| `--scope provider` | Precise, reversible edits to tool config: Claude Code (`env` in `~/.claude/settings.json`), Codex (managed block in `~/.codex/config.toml`), OpenClaw (the `wrap openclaw` flow), OpenCode (managed block in `~/.config/opencode/opencode.json`) |
| `--scope user` | User-level shell or environment surfaces |
| `--scope system` | Machine-wide shell or environment surfaces |

For Copilot, Aider, Cursor and other environment-driven setups, prefer `--scope user` or `--scope system`, because provider scope has no direct adapter for them. For OpenCode, Headroom keeps your original config as `<config filename>.headroom-backup` and `headroom install remove` restores it. If you find a `.jsonc-migration-blocked` marker next to a legacy backup, keep it – it blocks automatic migration of an ambiguous backup. Inspect the legacy bytes before you copy them into your config by hand.

### Health and reuse

Persistent deployments serve the same `/readyz` and `/health` endpoints as ad hoc proxy runs. When the install subsystem launched the proxy, `/health` adds deployment metadata:

```json
{"deployment": {"profile": "default", "preset": "persistent-service", "runtime": "python", "supervisor": "service", "scope": "user"}}
```

The Python-native `headroom wrap` checks for a matching persistent deployment on the requested port before it starts an ephemeral proxy. It tries to recover a stopped or unhealthy deployment first. The Docker-native wrapper does not yet reuse or recover persistent profiles: it starts a fresh proxy container unless you pass `--no-proxy`.

### Claude Code in VS Code

Persistent Claude deployments default to `ENABLE_TOOL_SEARCH=true`, because the standalone `claude` CLI benefits from deferred tool schemas. The Claude Code VS Code extension does not render those deferred-tool blocks through Headroom and can show `unsupported content type`. If your persistent install targets the extension, set `tool_envs.claude.ENABLE_TOOL_SEARCH` to `"false"` in `~/.headroom/deploy/<profile>/manifest.json`, then restart the deployment. Keep it `true` for the standalone CLI.

### Rootless Podman

If `docker` is a Podman wrapper script rather than a symlink, set `HEADROOM_CONTAINER_RUNTIME=podman` for the Python-native `persistent-docker` preset. On Linux, Headroom then runs Podman with `--userns=keep-id` and an explicit `--user` with your user ID (UID) and group ID (GID), so new files stay owned by your host user. Restart the deployment with the updated installer. This prevents new ownership mismatches but does not repair files that an older container created.

## Headroom Enterprise for teams

Open source Headroom targets one developer on one laptop. Headroom Enterprise targets the whole team and adds:

- Savings: tool search for every model, harness tuning and extra compressors. Open source has tool search on Anthropic requests only, on by default.
- Model routing: automatic per-request routing to a cheaper model when quality allows, with a shadow mode that shows the savings first. Open source routing is rule-based and opt-in: set `HEADROOM_MODEL_ROUTER_ENABLED=1` and write rules in `HEADROOM_MODEL_ROUTES` (see [configuration](./configuration.md)).
- Security: detection and stripping of prompt injection and risky tool calls.
- Rollout: managed or in your virtual private cloud (VPC), single sign-on (SSO), central config and org-wide savings.
- Support: dedicated engineers, onboarding and priority response. Open source support runs through GitHub and Discord.

Everything in the open source repository stays under Apache 2.0. To ask about Enterprise, email hello@headroomlabs.ai.

## Best practices and pitfalls

| Do this | Not that | Why |
| --- | --- | --- |
| Start `headroom proxy` before you call the TypeScript SDK | Call TypeScript `compress()` with no proxy running | The SDK sends messages to the proxy over HTTP |
| Install the host CLI with `uv tool install --python 3.13` | Install into whatever `python3` Homebrew gives you | Homebrew's `python3` may be newer than the wheel set, and on Intel macOS, Python 3.14+ loses the optional ONNX features |
| Name integration extras, as in `"headroom-ai[proxy,langchain,ml]"` | Assume `[all]` covers LangChain, Agno, Strands, AutoGen or Bedrock | `[all]` is the runtime bundle, not every integration |
| Use `http://localhost:8787/v1` for `OPENAI_BASE_URL` | Use the same URL form for both providers | The documented `ANTHROPIC_BASE_URL` has no `/v1` suffix |
| Build a pipeline with `ContentRouterConfig(enable_code_aware=True)` when library code must use AST compression | Expect library `compress()` to compress code the way the proxy does | The proxy routes code to CodeAwareCompressor by default; library `compress()` and `HeadroomClient` send it to Kompress – see [compression](./compression.md) |
| Publish locally on `127.0.0.1` with `HEADROOM_ALLOW_UNAUTHENTICATED_BIND=1` | Publish on `0.0.0.0` without `HEADROOM_PROXY_TOKEN` | The acknowledgement holds only when the runtime restricts reach |
| Run one persistent deployment and let `wrap` reuse it | Start a new ad hoc proxy for every session | `wrap` reuses or recovers a matching deployment instead of starting a second proxy |
| Put the absolute `headroom` path in MCP client configs | Rely on `PATH` in clients such as Codex | They do not inherit your interactive shell `PATH` |
| Install `google-cloud-aiplatform>=1.38` yourself for Vertex AI | Expect an extra or image to include it | None of them does |
| Use the torch-free `sandbox` bundle in constrained environments | Install `[all]` or `ml` where PyTorch does not fit | `ml`, which `[all]` includes, adds the PyTorch Kompress backend |

## Quick reference

| Task | Command or endpoint |
| --- | --- |
| Check the CLI | `headroom --version` |
| Start the proxy | `headroom proxy --port 8787` |
| See savings | `curl http://localhost:8787/stats` or `headroom dashboard` |
| Check health and deployment metadata | `/health` and `/readyz` on the proxy port |
| Wrap a coding agent | `headroom wrap claude` (also `codex`, `aider`, `cursor`, `openclaw`, `vscode-claude`) |
| Install a turnkey persistent proxy | `headroom deploy` |
| Manage a persistent install | `headroom install status`, `start`, `stop`, `restart`, `remove` |

## Related skills

- [compression](./compression.md) – how content routing works, each compressor, and how to opt in to code compression.
- [ccr-and-caching](./ccr-and-caching.md) – the CCR store and `headroom_retrieve` behind "nothing is lost", plus CacheAligner and cache optimization.
- [memory](./memory.md) – persistent memory from the `memory` extra and `headroom memory list`.
- [proxy](./proxy.md) – proxy flags, endpoints such as `/stats` and `/health`, token auth, savings profiles and agent wrapping.
- [framework-integrations](./framework-integrations.md) – LangChain, Agno, Strands, CrewAI, AutoGen, LiteLLM, the Vercel AI SDK and `withHeadroom`.
- [coding-agents](./coding-agents.md) – `headroom wrap` for Claude Code, VS Code, Codex, OpenCode and OpenClaw, and the MCP tools.
- [configuration](./configuration.md) – every environment variable, `HEADROOM_MODEL_ROUTES`, and the filesystem contract behind `HEADROOM_WORKSPACE_DIR`.
- [observability](./observability.md) – savings tracking, the dashboard, Prometheus metrics and the `otel` extra.
- [sdk-reference](./sdk-reference.md) – full Python and TypeScript result types and error handling.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – fixes by symptom beyond installation, and safety gates.
- [architecture-and-security](./architecture-and-security.md) – the security model behind the bind and token rules, and benchmarks.

## Source pages

- https://docs.headroomlabs.ai/docs – Introduction
- https://docs.headroomlabs.ai/docs/quickstart – Quickstart
- https://docs.headroomlabs.ai/docs/installation – Installation
- https://docs.headroomlabs.ai/docs/docker-install – Docker-Native Install
- https://docs.headroomlabs.ai/docs/persistent-installs – Persistent Installs
- https://docs.headroomlabs.ai/docs/teams – Headroom for Teams
