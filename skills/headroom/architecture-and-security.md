# Headroom: Architecture and security
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill to explain Headroom's request path, answer a security review of the proxy, cite the benchmarks, and control runtime features.

## Core concepts

- **Headroom intercepts, compresses and forwards.** It shrinks the bulky blocks in a request (tool outputs, file reads, logs, search results), sends the smaller request upstream, and returns the provider's response unchanged.
- **Three entry points share one pipeline.** The proxy, the Python and TypeScript `compress()` functions, and the framework integrations all run the same compression pipeline.
- **Every transform fails open.** On any error, a transform returns the content unchanged and the request still goes through.
- **Headroom never drops or reorders messages.** It compresses content in place and leaves the message list intact.
- **Compression is reversible by default.** Compress-Cache-Retrieve (CCR) stores each original so the model can fetch it back.
- **The proxy is a local machine-in-the-middle (MITM).** It reads your agent traffic in plaintext, holds your provider credentials, and trusts the user account it runs as.
- **Runtime rollouts gate behavior, not versions.** A channel decides which features the installed artifact may expose in this process.

## Architecture

### Request path

```text
Your application
  -> Entry point: proxy (FastAPI) | Python compress() | TypeScript compress()
  -> Transform pipeline, in order:
       1. Tool-result interceptor   canary opt-in
       2. CacheAligner              detector only, off by default
       3. ContentRouter             detects content type, routes to one compressor
  -> Backend: direct | LiteLLM | any-llm
  -> Provider: OpenAI, Anthropic, Google, Bedrock and 100+ more
The provider's response returns unchanged.
```

In proxy mode, a FastAPI app runs one handler per provider: Anthropic, OpenAI, Gemini and Bedrock. Each handler runs the same pipeline, then forwards through the selected backend.

| Entry point | How you use it | Code changes |
| --- | --- | --- |
| Proxy mode | Run `headroom proxy` and point your client's base URL at it | The base URL only |
| Software development kit (SDK) mode | Call `compress()` in Python or TypeScript on your messages before you send them, or wrap your client in `HeadroomClient` for per-call optimization and stats | One call or one wrapper |
| Integrations | LangChain, Vercel AI SDK, Agno, Strands, LiteLLM, Model Context Protocol (MCP) adapters | Framework-specific setup |

Pick the proxy when you can't change application code. The trade-off is a local process with its own sensitive routes and files, described under [Security model](#security-model). For SDK signatures, see [sdk-reference](./sdk-reference.md).

### Pipeline stages

1. **Tool-result interceptor (canary opt-in).** Light structural interceptors, such as ast-grep outlining of Read results. It needs the `canary` channel and `--intercept-tool-results`; see [Runtime rollouts](#runtime-rollouts) for the full command.
2. **CacheAligner (off by default).** A detector that reports dynamic-prefix drift, such as dates, universally unique identifiers (UUIDs) and session tokens. It never mutates, moves or rewrites content, and the proxy hard-disables it. It exists for prefix-stability metrics.
3. **ContentRouter.** Does essentially all of the compression.

The context-manager stage of earlier versions is gone. It deleted old turns, by rolling window or intelligent-context scoring, until the request fit the context window. `RollingWindowConfig`, `IntelligentContextConfig` and `ScoringWeights` no longer exist in the Python package. The TypeScript SDK types still export equivalent field names, but those fields are wired to nothing.

### ContentRouter

ContentRouter detects the type of each content block and sends it to exactly one compressor.

| Detected content | Compressor | Typical savings |
| --- | --- | --- |
| JSON arrays (tool outputs) | SmartCrusher | 70–90% |
| Source code | CodeAwareCompressor in the proxy (on by default); Kompress in library `compress()` | 40–70% |
| Search and grep results | SearchCompressor | 80–95% |
| Build and test logs | LogCompressor | 85–95% |
| Diffs | DiffCompressor | 40–80% |
| HTML | HTMLExtractor (trafilatura) | 70–90% |
| CSV, TSV and Markdown tables | TabularCompressor | 60–90% |
| YAML, TOML and INI config | ConfigCompressor | 40–70% |
| Plain text | Kompress; TextCrusher only for long text above Kompress's size gate | 30–60% (TextCrusher) |
| Anything else | Kompress, the machine learning (ML) fallback | Varies |

The architecture page lists code-aware compression as off by default and routes all plain text to TextCrusher. The more specific compression pages, and the 0.40.0 source for the code default, say otherwise, so the table follows them – see [compression](./compression.md). Treat these ranges as typical, not promised. The [benchmarks](#benchmarks) measured 48–49% on JSON search-result arrays and 92% on documentation text, so measure your own traffic before you quote a figure.

To avoid compressing the same content twice, ContentRouter keeps a two-tier cache. A skip set remembers content known not to compress, and a result cache holds earlier compressed output. A time to live (TTL) of 30 minutes bounds both by default.

The heaviest compressors run in a native Rust extension, `headroom._core`, which is built with PyO3 and loaded when the proxy starts. SmartCrusher, the search, log and diff compressors, and content detection are Rust-backed. The Python classes you import are thin, API-compatible shims over them. Kompress, a ModernBERT token compressor, runs separately through Open Neural Network Exchange (ONNX) Runtime, either locally or on a remote endpoint.

### Compression modes and provider caches

The proxy `--mode` flag selects one of two modes:

```bash
headroom proxy --mode cache   # default: compress only the newest delta, forward prior turns byte-faithfully
headroom proxy --mode token   # maximum token removal: may recompress earlier turns
```

- **Use `cache` for coding agents and long multi-turn sessions.** It never invalidates the provider's prefix cache mid-conversation. On multi-turn workloads, that cache is where most of the cost savings come from.
- **Use `token` only when raw token count matters more than cache hits.** You trade cache stability for maximum savings.

| Provider | Cache mechanism | Savings on cached tokens |
| --- | --- | --- |
| Anthropic | `cache_control` on the stable prefix | Up to about 90% |
| OpenAI | Automatic prefix caching | Up to about 50% |
| Google | `CachedContent` API | Up to about 75% |

### CCR and TOIN

CCR is on by default. When ContentRouter compresses a tool output, it stores the original in a hash-indexed local SQLite store, the CCR store. If the model needs the full data, it calls the injected `headroom_retrieve` tool, for example `headroom_retrieve("abc123")`, and gets the original back.

```bash
headroom proxy --no-ccr     # no retrieval markers and no injected headroom_retrieve tool
headroom proxy --lossless   # marker-free, format-native lossless mode
```

The Tool Output Intelligence Network (TOIN) learns over repeated calls which fields carry signal for each tool and which items get retrieved. It feeds that into SmartCrusher's importance scoring. TOIN is local and observation-only: nothing about your tools or traffic is shared across users or sent off the machine. For a new tool type, it starts from statistical heuristics and improves as it observes more calls.

### What Headroom does not rewrite

- **Your prompt text.** Compression targets bulk content blocks, not your instructions.
- **System prompts.** They stay intact by default, so the hottest part of the prefix cache stays stable. A savings profile can opt into compacting them.
- **Most code.** Safety gates protect recent code and code the user asks about, so abstract syntax tree (AST)-based code compression rarely fires – see [troubleshooting-and-limits](./troubleshooting-and-limits.md).
- **Model responses.** They return from the provider unchanged.
- **Short content.** Blocks below the minimum-token threshold pass through, because the overhead would exceed the savings.

## Security model

The security model page aims to support a security review without reading the source. Report vulnerabilities through the project's [SECURITY.md](https://github.com/headroomlabs-ai/headroom/blob/main/SECURITY.md).

### Review answers at a glance

| Question | Answer |
| --- | --- |
| What does the proxy see? | All agent traffic, in plaintext |
| Is the provider connection encrypted? | Yes, with Transport Layer Security (TLS); `HEADROOM_TLS_STRICT=0` relaxes one check narrowly |
| Is anything encrypted at rest? | No; file permissions and the proxy's account protect everything |
| Where do compressed originals go? | The CCR store: plaintext SQLite, 30-minute TTL, lazy purge |
| Are prompts logged? | Not by default; `--log-messages` writes them to the request log |
| What else leaves the host? | The beacon (counters only, on by default), the Python Package Index (PyPI) version check, Hugging Face model downloads, and license calls when a key is set |
| Who can change configuration at runtime? | Any local process running as you, plus peers in `HEADROOM_PROXY_TRUSTED_DASHBOARD_CLIENT_CIDRS` |
| Can a web page reach the sensitive routes? | No; the loopback, `Host:` and `Origin:` gates block remote callers, Domain Name System (DNS) rebinding and cross-site request forgery (CSRF) |
| Can a client redirect requests or credentials? | It can pick a public upstream; Headroom refuses private targets and sends extra headers only to designated hosts |
| Is there an audit trail? | Yes, in `proxy.log`, with changed keys but never values |
| Is it safe on multi-tenant hosts? | No; it is not an isolation boundary |

### Trust model

Headroom runs as a local process under your user account and trusts that account. It sees your full agent traffic in plaintext and holds the provider credentials you give it. Its sensitive HTTP routes accept only loopback callers by default. That protects you from remote and cross-origin attackers, but not from other processes running as you. Headroom is not designed for multi-tenant hosts and is not an isolation boundary between users.

### Data in flight

The proxy terminates your agent's connection, decompresses and parses the body, applies its transforms, and re-sends the request upstream with your credentials. Compression needs inspection, so no mode forwards traffic the proxy cannot read. The proxy sees system prompts, the full conversation, source code sent as context, tool arguments and results, and retrieved chunks, all in plaintext.

The connection to the provider stays on TLS. `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` replace the trust store: set either, and Headroom trusts only those certificate authorities (CAs). `NODE_EXTRA_CA_CERTS` adds roots on top of the system store, as Node.js does. The first one set wins, in that order. For the corporate-network settings `HEADROOM_CERT_STORE` and `HEADROOM_CA_BUNDLE`, see [proxy](./proxy.md).

### Client-selected upstream

The OpenAI-compatible handlers accept an `x-headroom-base-url` request header, so a client can choose where one request goes. This header lets bring-your-own-key (BYOK) gateways, such as LiteLLM, Azure or self-hosted vLLM, reach the dedicated handlers. Two guards bound it:

- **Where it may point.** Headroom resolves the URL and refuses private, loopback, link-local and other non-public addresses. That blocks the confused-deputy case, such as reaching cloud metadata at `169.254.169.254` or private Request for Comments (RFC) 1918 hosts. Headroom unwraps IPv4 addresses embedded in NAT64 (IPv6-to-IPv4 translation) literals before the check. A refused override is not fatal: Headroom logs a warning and sends the request to the configured upstream.
- **What rides along.** The operator's extra-header maps, `ANTHROPIC_TARGET_API_HEADERS` and `OPENAI_TARGET_API_HEADERS`, go only to designated hosts. A designated host is a resolved provider target (`ANTHROPIC_TARGET_API_URL`, `OPENAI_TARGET_API_URL`, or the Gemini, Vertex, Bedrock and Cloud Code equivalents), the default `api.anthropic.com` or `api.openai.com`, or a host in `HEADROOM_UPSTREAM_ALLOWED_HOSTS`. Headroom compares parsed hostnames exactly, so neither `https://api.anthropic.com@evil.example` nor `https://api.anthropic.com.evil.example` matches. Other destinations still get the request without those headers, and Headroom warns once per host.

```bash
# Allow one internal gateway as a client-selected upstream, and send it your extra headers
HEADROOM_ALLOWED_BASE_URLS=https://llm-gateway.internal.example \
HEADROOM_UPSTREAM_ALLOWED_HOSTS=llm-gateway.internal.example \
headroom proxy
```

`HEADROOM_ALLOWED_BASE_URLS` takes comma-separated hosts or URLs. A bare host permits every safe scheme and port on that host. A full URL permits only its exact normalized origin. `HEADROOM_UPSTREAM_RESOLVE_TIMEOUT_S` bounds DNS resolution, 3 seconds by default.

Neither guard authenticates the caller. They stop a client from sending your stored credentials to a host of its choosing. They also stop the proxy from becoming a server-side request forgery (SSRF) pivot into your network. They limit what a request reaches and carries, not who may send it.

### Data at rest

Most state lives in the workspace: `~/.headroom` by default, or `$HEADROOM_WORKSPACE_DIR`. The workspace is not a full inventory. The memory store defaults to a project-local path, and you can move the memory store and the Copilot token independently.

| Item | Path | Sensitive contents | Retention | Permissions |
| --- | --- | --- | --- | --- |
| Copilot OAuth token | `<workspace>/copilot_auth.json` or `$HEADROOM_COPILOT_AUTH_FILE` | GitHub Copilot OAuth refresh token, plaintext JSON | Until you delete it | `0600`, best-effort |
| CCR store | `<workspace>/ccr_store.db` (SQLite) | Pre-compression originals: tool outputs, file contents, retrieved chunks | 30 minutes (`HEADROOM_CCR_TTL_SECONDS`), lazily purged | `0600` |
| Memory store | Project-local by default; see [Memory store paths](#memory-store-paths) | Extracted cross-session memories | Until deleted | Inherits umask |
| Memory exports | `<workspace>/memories/` | Markdown exports of memories | Until deleted | Inherits umask |
| Install ID | `<config dir>/install_id` | Random UUID that identifies the install to the beacon | Until deleted | `0600`, best-effort |
| Savings tracker | `<workspace>/proxy_savings.json` | Aggregate token and cost counters, no prompt content | Until deleted | Inherits umask |
| License cache | `<workspace>/license_cache.json` | Cached license envelope | Per envelope | Inherits umask |
| Settings store | `<workspace>/settings.json` or `$HEADROOM_SETTINGS_PATH` | Dashboard knob values, including the two extra-header maps | Until deleted | `0600`, from `mkstemp` |
| Proxy log | `<workspace>/logs/proxy.log` plus 5 rotations | INFO-level operational log and the admin audit stream | 10 MB × 5 backups | Inherits umask |
| Request log | Opt-in: `--log-file` or `$HEADROOM_LOG_FILE` | Per-request JSON Lines (JSONL); full content with `--log-messages` | Until deleted | Inherits umask |

The config directory is `$HEADROOM_CONFIG_DIR`, else `$HEADROOM_WORKSPACE_DIR/config`, else `~/.headroom/config`. Nothing Headroom writes is encrypted at rest. File permissions and the security of the proxy's account protect all of it.

#### Settings store

The dashboard's settings page persists a curated set of 59 knobs, the settings registry, to `settings.json`. Two knobs are marked secret: the extra-header maps `ANTHROPIC_TARGET_API_HEADERS` and `OPENAI_TARGET_API_HEADERS`. They are free-form JSON header maps merged into forwarded requests, such as `{"Api-Key": "..."}`, and they sit on disk in plaintext. `GET /settings` returns a sentinel instead of the value, but that only masks the display.

- **The file is a second source of environment values.** At command-line interface (CLI) startup and again at app construction, Headroom applies it with `os.environ.setdefault`. Precedence is shell export, then `settings.json`, then the code default. A stored value silently becomes the effective configuration on a host where you assumed the environment was the only input.
- **Its `0600` mode is an implementation property.** `save()` writes atomically with `tempfile.mkstemp` and `os.replace`, and inherits the `0600` from `mkstemp`. There is no explicit `chmod`, so don't treat the mode as a guarantee.

`HEADROOM_TLS_STRICT`, `HEADROOM_BEACON`, `HEADROOM_CCR_BACKEND` and `HEADROOM_OFFLINE` are not in the settings registry, so neither this file nor its routes can set them.

#### Logs

- **`proxy.log` is always on.** A rotating handler (10 MB, 5 backups) is attached when the app starts, before other configuration applies, and no flag suppresses it. It holds INFO-level operational records and the admin audit stream. It gets no explicit mode, so under a common `0002` umask it lands at `0664`: readable by every account on the host.
- **The request log is opt-in.** `--log-file` (`HEADROOM_LOG_FILE`) writes one JSON object per request, with metadata only by default. `--log-messages` (`HEADROOM_LOG_MESSAGES`) adds full request and response content to that file and serves it on the live feed endpoint.
- **`--stateless` does not stop `proxy.log`.** It suppresses the request log by forcing `log_file` to `None`, but `proxy.log` is still written.

```bash
headroom proxy --log-file headroom.jsonl                  # Do: metadata only
headroom proxy --log-file headroom.jsonl --log-messages   # Don't, unless you accept prompts and completions on disk, unencrypted, for as long as the file exists
```

Both log variables are in the settings registry. A caller who reaches the settings routes can turn on full message logging and choose its file.

#### Memory store paths

With `--memory` on and `--memory-db-path` unset, the proxy creates `{cwd}/.headroom/memory.db`, relative to the directory it was launched from. A fleet that runs agents in many repositories therefore creates many databases. `--memory-storage` sets the partitioning:

- `project` (default): one database per resolved workspace, at `<db_path_dir>/memories/projects/<basename>-<hash>/memory.db`.
- `user`: one database per resolved identity.
- `global`: one shared database, the `--memory-db-path` file itself.

`--memory-db-path` (`HEADROOM_MEMORY_DB_PATH`) sets the `global` file and seeds the storage root for `project` mode. Requests can steer scoping with the `x-headroom-project-id` and `x-headroom-cwd` headers.

`x-headroom-user-id` is a partition hint, not an authenticated identity. Headroom honors it only for loopback callers. Any other caller is bound to a hash of `HEADROOM_PROXY_TOKEN`, or else to the server's operating-system user, so a network client cannot select another user's partition. A request with missing peer metadata does not count as loopback, so the check fails closed. Multi-tenant deployments replace the resolver through `set_identity_resolver`; the open-source proxy ships only the single-user default.

```bash
# One known memory file: easier to inventory and delete, but every project shares it
headroom proxy --memory --memory-storage global --memory-db-path ~/.headroom/memory.db
# For an inventory or deletion request, find the project-local stores too
find ~ -type d -name .headroom
```

#### CCR store

With `HEADROOM_CCR_BACKEND` unset or set to `sqlite`, each entry is one JSON row in `ccr_store.db`, with the original in a plaintext `original_content` field. The store survives restarts by design, because the 30-minute TTL assumes worker processes share it. If a tool result held a credential, an internal hostname or a customer record, that value sits in a readable SQLite file for at least the TTL.

- **Expiry is lazy.** A sweep on lookup removes expired rows, and no background timer runs. On an idle proxy, expired content stays on disk until the next access. The TTL bounds retrievability, not residency.
- **The backend can fall back silently.** If SQLite fails to initialize, Headroom logs a warning and uses an in-memory store. Retrieval still works, but no longer survives restarts.

```bash
# Keep originals in process memory only; you lose restart-safety and sharing across worker processes
HEADROOM_CCR_BACKEND=memory headroom proxy --port 8787
```

### Local control surfaces

Besides the provider routes, the proxy exposes sensitive routes: `/admin/*`, `/debug/*`, `/cache/clear`, `/stats/reset`, `/settings*`, `/transformations/feed`, `/v1/feedback*`, `/v1/telemetry*`, `/v1/toin/*`, and the content-bearing `/v1/retrieve*` family. Three gates protect them:

| Gate | Routes | Check | Stops |
| --- | --- | --- | --- |
| `require_loopback`, address | All sensitive routes | The client address is a loopback IP | Remote callers |
| `require_loopback`, host | All sensitive routes | The `Host:` header names loopback | DNS rebinding, where a remote page resolves its hostname to `127.0.0.1` |
| `require_same_origin` | `/admin/runtime-env`, `/cache/clear`, `/stats/reset`, `/settings`, `/settings/apply` | Rejects a foreign `Origin:` header; requests without one, such as curl, pass | CSRF from a page in your browser |

Guarded routes answer 404, not 403, so a scanner cannot tell them from absent routes.

**`POST /admin/runtime-env`** writes only the seven knobs in the hardcoded `RUNTIME_ENV_KNOBS` allowlist and ignores other keys. `headroom wrap` uses this route to hot-sync settings into a running proxy. The knobs cover output shaping (`HEADROOM_OUTPUT_SHAPER`, `HEADROOM_OUTPUT_HOLDOUT`), verbosity steering (`HEADROOM_VERBOSITY_LEVEL`, `HEADROOM_VERBOSITY_AUTOTUNE`) and ast-grep Read interception (`HEADROOM_INTERCEPT_READ_MIN_CHARS`, `HEADROOM_VERIFY_TRUNCATION_ON_DISK`, `HEADROOM_VERIFY_TRUNCATION_MAX_BYTES`). `/admin/upstream` is read-only, and no admin route writes the upstream. That stops a caller from redirecting credential-bearing traffic through the admin surface.

**`POST /settings` and `POST /settings/apply`** are the wider surface, and they belong in the same threat model. `POST /settings` validates against the settings registry and writes to disk. `POST /settings/apply` does the same, then restarts the proxy: a self-restart on service deployments, or it returns the host command under Docker. A caller who reaches these routes can:

- Repoint credential-bearing traffic, because `ANTHROPIC_TARGET_API_URL` and `OPENAI_TARGET_API_URL` are in the registry. The read-only `/admin/upstream` does not prevent this.
- Turn on full message logging to a file path of their choice.
- Write the extra-header maps to disk in plaintext.

Neither the runtime-env allowlist nor the settings registry includes `HEADROOM_TLS_STRICT`, `HEADROOM_BEACON`, `HEADROOM_CCR_BACKEND` or `HEADROOM_OFFLINE`. Headroom reads TLS verification from the process environment at startup only, so no HTTP call can relax it.

**Audit.** Calls to `/admin/*`, `/cache/clear` and `/stats/reset` emit an event with the action, method, path, source IP and status code. `/admin/runtime-env`, `POST /settings` and `POST /settings/apply` also record the changed keys, never the values, so secrets stay out of the log. The audit stream has no file of its own, so it lands in `proxy.log`.

#### Allowlists beyond loopback

Two Classless Inter-Domain Routing (CIDR) allowlists can extend the gates beyond loopback. Both are empty by default. Setting either moves your boundary, so record it in your threat model.

| Variable | Effect |
| --- | --- |
| `HEADROOM_PROXY_TRUSTED_DASHBOARD_CLIENT_CIDRS` | Peers in these ranges reach `/settings`, `/settings/schema`, `/dashboard/settings` and the settings writes without being on loopback. They also see the `/stats` and `/stats-lifetime` fields withheld from other network callers: request IDs, providers, models, errors, project names and backend config. It exists so the settings page works behind a reverse proxy. |
| `HEADROOM_PROXY_TRUSTED_GATEWAY_CIDRS` | Peers in these ranges may supply `X-Forwarded-*` headers, so Headroom uses the forwarded client IP instead of the gateway's. |

A malformed CIDR fails at startup instead of silently emptying the list. Configure both together and point them at infrastructure you control, because a trusted gateway makes the dashboard check run against a client-supplied header.

```bash
# Settings page behind your own reverse proxy at 10.0.0.5
HEADROOM_PROXY_TRUSTED_GATEWAY_CIDRS=10.0.0.5/32 \
HEADROOM_PROXY_TRUSTED_DASHBOARD_CLIENT_CIDRS=10.0.1.0/24 \
headroom proxy
```

#### Residual risk

The gates stop remote and browser-based attackers, not local ones. Any local process running as your user can flip the seven runtime knobs, write the settings and restart the proxy, read `/v1/retrieve*`, and reach the debug routes. There is no token, no mutual TLS (mTLS) and no per-caller authorization: the gates check where a request came from, not who sent it. That is proportionate on a single-user developer machine, the intended deployment. On shared build boxes, multi-user jump hosts, or anywhere untrusted local code runs, don't deploy Headroom without extra isolation.

### Network egress

Besides your configured providers, Headroom may contact these hosts:

| Destination | Purpose | Default | Turn off |
| --- | --- | --- | --- |
| `headroom-beacon.headroom-beacon.workers.dev` | Anonymous session summaries to Headroom Labs | On | `HEADROOM_BEACON=off`, `DO_NOT_TRACK=1` or `HEADROOM_OFFLINE=1` |
| `pypi.org` | Daily version check for update notices | On | `HEADROOM_UPDATE_CHECK=off`; also skipped under `--stateless`, in continuous integration (CI) and in source checkouts |
| `huggingface.co` | Model downloads for the optional ML compression paths | On first use of those features | Pre-provision the model cache, or leave the features off |
| `app.headroomlabs.ai` | License validation and usage reporting | Only with a license key configured | Omit the license key |

**The beacon is the only egress that is on without any action from you** (`BEACON_DEFAULT_ON = True`). It POSTs cumulative snapshots, not deltas, to `https://headroom-beacon.headroom-beacon.workers.dev/v1/logs`, currently a Cloudflare `workers.dev` address.

- **Sent:** counters and identifiers. Session fields are a random ID, sequence number, duration, turn count and final-report flag. Token fields are counts and derived percentages. Compression fields are transform and skip tallies keyed by internal slug, per-strategy event and token counts, aggregate and per-turn latency, passthrough turns and response-cache hits. Context fields are request sources (`proxy` or `mcp`), provider and model names, and failure counts by HTTP status.
- **Also sent:** a random per-install UUID, the Headroom version, operating-system type, processor architecture, and the install mode and detected stack when known.
- **Not sent:** prompts, completions, file contents, tool results and file paths. The install ID is a random UUID, not a machine fingerprint, and deleting `<config dir>/install_id` resets it.

Headroom checks the off switches in this order:

```bash
HEADROOM_OFFLINE=1    # offline mode: disables all egress, the beacon included
DO_NOT_TRACK=1        # the cross-tool convention, honored
HEADROOM_BEACON=off   # false, 0, no, disable and disabled also work
# Don't: HEADROOM_BEACON=of (an unrecognized value keeps the beacon uploading)
```

The beacon fails open while its default stands, so a typo uploads. In configuration management, assert one of the exact off-values. To keep the reports but own them, point `HEADROOM_TELEMETRY_ENDPOINT` at a receiver you control.

`HEADROOM_TELEMETRY` is a separate switch: opt-in, off by default, and fail-closed on unrecognized values. It aggregates stats locally for the in-process collector and the `/stats` and `/v1/telemetry` endpoints, and it sends nothing off the host. Turning it on does not authorize the beacon, and turning it off does not stop the beacon. OpenTelemetry export (`HEADROOM_OTEL_METRICS_*`) is also opt-in and targets a collector you name.

### Governed knobs

These knobs need an explicit policy decision. None of them is in the settings registry or the runtime-env allowlist, so only the process environment sets them.

| Knob | Effect | Policy |
| --- | --- | --- |
| `HEADROOM_TLS_STRICT=0` | Clears only the RFC 5280 strict flag, so Headroom works behind a corporate TLS-inspecting proxy. It does not disable verification wholesale. | Set it deliberately, not by habit, because it still loosens transport security. The corporate-networks page says the operating system (OS) certificate store makes it unnecessary. |
| `HEADROOM_UPDATE_CHECK=off` | Disables the daily PyPI version check | Use it on managed fleets, where your own release process drives upgrades. |

The third governed knob is `HEADROOM_BEACON`, covered under [Network egress](#network-egress). For knobs in the settings registry, the effective value may come from `settings.json` when your shell does not export one. A fleet policy that only inspects exported variables is incomplete for those knobs.

### What `headroom wrap` changes

`headroom wrap` makes persistent changes to your development environment. It injects configuration into agent config files, may edit `CLAUDE.md` or `AGENTS.md`, and can install MCP servers. `headroom unwrap` reverses the wrapping. A full teardown currently takes several commands. Issue [#748](https://github.com/headroomlabs-ai/headroom/issues/748) tracks it and proposes a consolidated `headroom uninstall`, which has not landed. On managed machines, record wrapping as an inventory change. For per-agent commands, see [coding-agents](./coding-agents.md).

### Hardening checklist

Deploy only on single-user machines, because the gates trust every local process running as you. Then work through this list, quickest first:

1. Set `HEADROOM_BEACON=off` (an exact value) or `DO_NOT_TRACK=1`. The beacon is the only egress that is on by default.
2. Set `HEADROOM_UPDATE_CHECK=off` and pin the package version, so your release process drives upgrades.
3. Leave `--log-messages` off. It writes prompts and completions to disk unencrypted.
4. Leave both CIDR allowlists empty unless a reverse proxy needs them. Each one widens the boundary beyond loopback.
5. Check the mode of `proxy.log`. It follows your umask and can be world-readable.
6. Read `settings.json` as well as the environment when you audit configuration, because it sets registry knobs silently.
7. Set `HEADROOM_CCR_BACKEND=memory` if originals must never touch disk. You lose restart-safety and sharing across workers.
8. Pre-provision model assets, so the ML paths never download from `huggingface.co` at runtime.
9. Include project-local `.headroom/` directories in inventories and deletion procedures.

Where fully offline operation is acceptable, `HEADROOM_OFFLINE=1` covers the beacon, update check and model-download items at once.

## Benchmarks

Every number is measured locally and is reproducible. The compression and latency figures come from an Apple M-series CPU, and the headline table names Headroom 0.37.0, not 0.40.0. Latency is the compression pipeline's own overhead, with no large language model (LLM) call involved.

- **Headline:** six scenarios across four content types went from 126,400 to 55,100 tokens (56% saved), with 4.4 ms of total median (p50) overhead.
- **By type:** JSON search-result arrays saved 48–49%, structured logs 53–54%, documentation text 92% and Python source 0%. Code passes through by design to preserve correctness.
- **HTML extraction:** on the Scrapinghub Article Extraction Benchmark (181 pages), F1 is 0.919, precision 0.875 and recall 0.985, at 94.8% compression. Recall matters most for LLM use, because it means nearly all article content survives.
- **Anomaly retention:** a 100-entry JSON log array with one error entry at position 67 went from 4,937 to 3,053 tokens (38.2%), and the error entry survived. SmartCrusher keeps the first and last N items, all anomalies and the statistical distribution.
- **Question answering (QA) accuracy:** no number is published. The test uses a paid LLM judge and runs only when `OPENAI_API_KEY` is set.
- **Latency:** p50 overhead stayed between 0.11 and 1.4 ms for JSON scenarios up to 1,000 items. ContentRouter's detection and routing took 68–99% of pipeline time (mean about 87%) across 14 JSON scenarios.
- **Net effect:** in all 25 compressing scenarios, compression saved more prefill time than it cost, against Claude Sonnet 4.5 at 0.03 ms per token. For 1,000 search results, 1.4 ms of compression saved about 1,464 ms of prefill. Slower, pricier models such as Opus gain more.

```bash
git clone https://github.com/headroomlabs-ai/headroom.git
cd headroom
pip install -e ".[evals,html]"
pytest tests/test_evals/ -v -s
# Latency and compression-ratio tables
python benchmarks/bench_latency.py
python benchmarks/bench_latency.py --scenario json --iterations 10
# QA accuracy preservation: needs OPENAI_API_KEY and makes paid calls
pytest tests/test_evals/test_html_oss_benchmarks.py -k qa_accuracy -v -s
```

Quote your own measurements when you size a deployment, because these come from an older release on one machine type. For local inference, the main gain is often faster prompt processing rather than lower API spend; see the local LLM prefill workflow in [proxy](./proxy.md).

## Runtime rollouts

Runtime rollout answers one question: which behaviors may this already-built artifact expose in this process? It is separate from the release lifecycle, which decides which commit or artifact gets qualified, packaged and published. `HEADROOM_ROLLOUT_CHANNEL=canary` does not install, select or run a canary release.

### Channels

Channels are ordered `stable < beta < canary < dev`.

- `stable` (default): behavior eligible for normal production use.
- `beta`: opt-in behavior backed by automated and limited production evidence.
- `canary`: early dogfood behavior that is still gathering evidence.
- `dev`: local development and maintainer experiments.

Each feature has two separate registry fields: the channel where it is available, and the channel where it is on by default. A feature can be available in `canary` and still stay off until you request it.

### Request, disable and inspect

```bash
# Request a named feature in an allowed channel
HEADROOM_ROLLOUT_CHANNEL=canary \
HEADROOM_FEATURES=tool_result_interceptors \
headroom proxy --intercept-tool-results
# Force it off: explicit disable beats every other input
HEADROOM_DISABLE_FEATURES=tool_result_interceptors headroom proxy
# Check a configuration without starting the proxy; rejects unknown channels and features
HEADROOM_ROLLOUT_CHANNEL=canary headroom rollout status --json
# Inspect the running Python proxy: the rollout object is /stats.rollout
curl http://127.0.0.1:8787/stats
```

The Rust front proxy, when deployed, publishes its own snapshot at `/rollout/status`, so each process's registry and decisions stay independently observable.

### Precedence

Headroom resolves CLI arguments, environment variables and typed configuration once, when it builds the configuration. The proxy and transform pipelines receive an immutable snapshot. Changing the process environment later does not change a running proxy.

| Condition | Result and decision |
| --- | --- |
| Explicit disable | Off, even if defaulted, requested, aliased or unsafe-overridden |
| Requested below its availability channel, unsafe override active | On, `unsafe_override` |
| Requested below its availability channel | Off, `blocked_by_channel` |
| Explicit request in an allowed channel | On, `explicit` |
| Legacy alias enabled in an allowed channel | On, `legacy_alias` |
| Default-enabled in the active channel | On, `default` |
| Otherwise | Off, `not_requested` |

Legacy feature-specific variables are narrow compatibility aliases. They obey channel bounds and explicit disable.

The one exception to the immutable snapshot is `/admin/runtime-env`. Hot-reloading the legacy `HEADROOM_OUTPUT_SHAPER` alias through it replaces the snapshot with a newly resolved one. Channel bounds and `HEADROOM_DISABLE_FEATURES` still win, and `/stats.rollout` shows the new decision. Because these overrides are process-local, the endpoint rejects updates when the built-in server runs multiple workers. In that case, restart the proxy with the environment you want.

### Unsafe override and invalid input

`HEADROOM_UNSAFE_ALLOW_UNSTABLE_FEATURES=1` is a break-glass mechanism. It lets a requested feature cross a channel boundary, but it cannot beat explicit disable. Use it only for debugging and emergency reproduction, never to promote a feature or pass release evidence. While it is active, the snapshot reports `"unsafe_override": true`, `"qualification_eligible": false` and `"qualification_ineligible_reason": "unsafe_rollout_override_active"`.

The Python resolver warns and falls back to `stable` on an unknown channel. It warns about unknown feature names and ignores them (fail closed). `headroom rollout status` and the Rust front proxy's typed parser reject both and list the valid values before startup. Run `headroom rollout status` first, because a channel typo otherwise starts the Python proxy on `stable` with only a warning.

### Status and provenance

The rollout object holds no secrets:

```json
{
  "schema_version": 1, "policy_version": "1", "channel": "stable", "unsafe_override": false,
  "registry_digest": "sha256:...", "snapshot_digest": "sha256:...", "qualification_eligible": true,
  "features": [
    {"name": "tool_result_interceptors", "available_in": "canary", "default_enabled_in": null,
     "requested": false, "disabled": false, "enabled": false, "decision": "not_requested"}
  ]
}
```

- `schema_version` versions the external JSON contract. `policy_version` versions the rollout rules.
- `registry_digest` is SHA-256 over the canonical, ordered feature definitions. `snapshot_digest` identifies the complete effective runtime state. Equivalent configurations produce equal digests, and material policy or decision changes produce different ones.
- The digests are deliberately separate from source, artifact and payload hashes. An external benchmark can compare them between a passthrough arm and a Headroom arm without importing Headroom internals. A mismatch invalidates the comparison.

### Graduation and rollback

A feature moves from canary through beta toward stable only with linked deterministic, integration and benchmark evidence. Bake time counts as evidence, not as qualification by itself. Release qualification follows before a behavior becomes a stable default. Every rollout-managed behavior needs a fast disable path: roll back with `HEADROOM_DISABLE_FEATURES`, or revert the defining change in source.

If you contribute a feature, add a named registry entry and tests for default behavior, explicit request, channel blocking, disable precedence, unsafe behavior, decision reasons and provenance. Don't read rollout variables inside implementation components, so that every decision comes from the resolved snapshot. The Python and Rust registries each list their own runtime's features, but share channel order, precedence, decision reasons, fail-closed input handling and digest semantics.

## Common pitfalls

- **Expecting Headroom to make a request fit the context window.** The dropping stage is gone, and Headroom only compresses in place. The TypeScript rolling-window fields are still exported but wired to nothing.
- **Running `--mode token` on long agent sessions.** Recompressing earlier turns costs provider cache hits, where most multi-turn savings come from.
- **Treating `~/.headroom` as the full inventory.** Memory stores default to project-local `.headroom/` directories.
- **Reading the CCR TTL as a deletion deadline.** Expiry is lazy, so content stays on disk until the next lookup.
- **Missing a silent CCR fallback.** If SQLite fails, originals live in memory only and vanish on restart, so watch for the warning.
- **Expecting `--stateless` to stop all logging.** `proxy.log` is always written.
- **Assuming the upstream can't change because `/admin/upstream` is read-only.** The settings routes can repoint it and restart the proxy.
- **A gateway that never sees traffic.** Headroom refuses a private or loopback `x-headroom-base-url` with only a warning and uses the configured upstream. Add internal gateways to `HEADROOM_ALLOWED_BASE_URLS`.
- **A gateway that receives requests without your configured headers.** Hosts that aren't designated don't get the extra-header maps. Add the host to `HEADROOM_UPSTREAM_ALLOWED_HOSTS`.
- **Turning off `HEADROOM_TELEMETRY` to stop the beacon.** The two switches are independent.
- **Editing the environment of a running proxy.** The snapshot is fixed when the configuration is built, so restart the proxy instead.

## Quick reference

| Task | Command or setting |
| --- | --- |
| Maximize token removal (default is `--mode cache`) | `headroom proxy --mode token` |
| Turn off CCR markers and the retrieval tool | `headroom proxy --no-ccr` |
| Use marker-free lossless compaction | `headroom proxy --lossless` |
| Keep CCR originals off disk | `HEADROOM_CCR_BACKEND=memory` |
| Change the CCR TTL | `HEADROOM_CCR_TTL_SECONDS` |
| Move the workspace, config or settings | `HEADROOM_WORKSPACE_DIR`, `HEADROOM_CONFIG_DIR`, `HEADROOM_SETTINGS_PATH` |
| Stop the beacon | `HEADROOM_BEACON=off` or `DO_NOT_TRACK=1` |
| Run fully offline | `HEADROOM_OFFLINE=1` |
| Stop the update check | `HEADROOM_UPDATE_CHECK=off` |
| Work behind a TLS-inspecting proxy | Trust the corporate root through the OS certificate store or `HEADROOM_CA_BUNDLE` first; `HEADROOM_TLS_STRICT=0` only relaxes strict checks – see [proxy](./proxy.md) |
| Permit an internal client-selected upstream | `HEADROOM_ALLOWED_BASE_URLS` |
| Send extra headers to another host | `HEADROOM_UPSTREAM_ALLOWED_HOSTS` |
| Pick a rollout channel | `HEADROOM_ROLLOUT_CHANNEL` (`stable`, `beta`, `canary` or `dev`) |
| Request or disable features | `HEADROOM_FEATURES`, `HEADROOM_DISABLE_FEATURES` |
| Check rollout configuration | `headroom rollout status --json` |
| See the running rollout state | `curl http://127.0.0.1:8787/stats` (`rollout` object); Rust front proxy: `/rollout/status` |
| Undo agent wrapping | `headroom unwrap`; per-agent usage is in [coding-agents](./coding-agents.md) |

## Related skills

- [compression](./compression.md) – each ContentRouter compressor in depth, including SmartCrusher and the code, text and log compressors.
- [ccr-and-caching](./ccr-and-caching.md) – CCR retrieval, cache optimization, and context management after the dropping stage was removed.
- [proxy](./proxy.md) – all proxy flags, savings profiles, API endpoints, corporate networks and the local LLM prefill workflow.
- [configuration](./configuration.md) – SDK and proxy configuration, environment variables and the filesystem contract behind the data-at-rest table.
- [memory](./memory.md) – the memory feature that creates the project-local stores.
- [observability](./observability.md) – `/stats`, metrics and savings tracking, including local telemetry.
- [coding-agents](./coding-agents.md) – what `headroom wrap` configures for each agent, agent hooks and MCP tools.
- [sdk-reference](./sdk-reference.md) – `compress()` and `HeadroomClient` for SDK mode.
- [framework-integrations](./framework-integrations.md) – the integration entry point for each framework.
- [getting-started](./getting-started.md) – installation and persistent installs, the context for the hardening checklist.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – symptoms, limitations and safety gates.

## Source pages

- https://docs.headroomlabs.ai/docs/architecture
- https://docs.headroomlabs.ai/docs/security-model
- https://docs.headroomlabs.ai/docs/benchmarks
- https://docs.headroomlabs.ai/docs/runtime-rollouts
