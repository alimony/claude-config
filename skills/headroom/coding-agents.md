# Headroom: Coding agent integrations
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

## Setup at a glance

The wrappers start the local Headroom proxy, so install the proxy extra first: `pip install "headroom-ai[proxy]"`. Run the wrappers from the project directory that should get credit for the savings, because several of them name the project after the current directory.

| Tool | Setup command | How to undo it | Notes |
| --- | --- | --- | --- |
| Claude Code (terminal) | `headroom wrap claude` | No unwrap step documented | Starts or reuses the proxy and launches Claude Code through it. |
| Claude Code on Vertex AI | `export CLAUDE_CODE_USE_VERTEX=1`, then `headroom wrap claude` | As above | Sets `ANTHROPIC_VERTEX_BASE_URL`. Your Google Application Default Credentials (ADC) token passes through. |
| Claude Code on Azure AI Foundry | `export CLAUDE_CODE_USE_FOUNDRY=1` and `ANTHROPIC_FOUNDRY_RESOURCE`, then `headroom wrap claude` | As above | Sets `ANTHROPIC_FOUNDRY_BASE_URL`. Your `api-key` or Entra token passes through. |
| Claude Code extension in Visual Studio Code (VS Code) | `headroom wrap vscode-claude` (add `--1m` for the 1M model selector) | `headroom unwrap vscode-claude` | Edits `env` in `~/.claude/settings.json`. Reload the window once and keep the wrapper running. |
| VS Code Copilot | `headroom copilot-auth login` once, then `headroom wrap vscode` | `headroom unwrap vscode` | Adds a marker-owned block to VS Code user settings. The model picker is unchanged. |
| OpenCode | `headroom wrap opencode` | `headroom unwrap opencode` | Backs up `opencode.json` and registers the Headroom Model Context Protocol (MCP) server. |
| OpenCode with DeepSeek | `headroom wrap opencode --openai-api-url https://api.deepseek.com/v1` | `headroom unwrap opencode` | Without the flag, your DeepSeek key goes to OpenAI and fails with a 401. |
| Grok Build | `headroom wrap grok-build`, then `grok` in a second terminal | `headroom unwrap grok-build` | Edits `[model.grok-build] base_url` in `~/.grok/config.toml`. |
| OpenAI Codex | `headroom wrap codex` | Nothing persists – routing applies only to the launched process | For persistent routing, use `headroom init codex` instead. |
| Cursor | `headroom wrap cursor` | Remove the URL you pasted into Cursor | Prints a base URL for Cursor's model settings. Edits nothing. |
| Aider | `headroom wrap aider` | Not documented | Listed with the other wrappers; no further detail. |
| Hermes Agent | Copy the `headroom_retrieve` plugin and enable it in `~/.hermes/config.yaml` | Reverse the two config edits (no command) | Gives Hermes a native `headroom_retrieve` tool. |
| OpenClaw | `headroom wrap openclaw` | No unwrap documented; set `plugins.slots.contextEngine` to `"legacy"` | Manual install needs `--dangerously-force-unsafe-install`. |
| Agent hooks (Claude Code, GitHub Copilot CLI) | Install the `plugins/headroom-agent-hooks` plugin | Not documented | Runs `headroom init hook ensure` when a session starts. |
| MCP tools (any MCP host) | `headroom mcp install` | `headroom mcp uninstall` | Needs only `headroom-ai[mcp]`; no proxy required. |
| Codex state recovery | `headroom recover codex` | Backups stay in `<target-parent>/.headroom-codex-recovery/` | Close Codex first. |

## Core concepts

- **Endpoint, not model.** The Claude Code and Copilot integrations change where requests go, not which model answers them, so the agent's own model picker keeps working. The exceptions are explicit: `--1m` writes a model setting, and OpenCode gets a `headroom` provider with its own model list.
- **Three integration styles.** A `headroom wrap <agent>` command manages the proxy, the agent's config and the undo step. A native plugin (OpenCode, Hermes, OpenClaw, agent hooks) runs inside the agent. The MCP server offers on-demand tools and needs no proxy.
- **Credentials pass through.** Headroom forwards Claude Code's Anthropic, Google or Azure credentials unchanged and stores none of them. VS Code Copilot is the exception: Headroom does not read VS Code's encrypted token store, so it needs its own GitHub authorization.
- **Fail closed in VS Code.** After you stop the proxy, both VS Code wrappers leave the endpoint in place. Requests then fail instead of silently bypassing Headroom.
- **Retrieval closes the loop.** The proxy replaces bulky content with Compress-Cache-Retrieve (CCR) markers such as `<<ccr:abc123>>`. The agent needs a `headroom_retrieve` tool to fetch the original by hash.

## Shared `headroom wrap` mechanics

### What wrapping changes

Every wrapper starts or reuses the proxy. How it then points the agent at the proxy decides what you must undo:

- **Endpoint variable or flag.** `wrap claude` sets Claude Code's endpoint variable (`ANTHROPIC_BASE_URL`, or `ANTHROPIC_VERTEX_BASE_URL` / `ANTHROPIC_FOUNDRY_BASE_URL` in Vertex or Foundry mode). `wrap codex` passes a `--config` override and writes no file. `wrap cursor` edits nothing and prints a URL.
- **Owned keys with a sidecar.** `wrap vscode-claude` writes two `env` keys (plus `model` with `--1m`) and keeps the prior values in a sidecar next to the settings file.
- **Marker-owned block.** `wrap vscode` adds one marked block to VS Code user settings.
- **File backup.** `wrap opencode` and `wrap grok-build` copy the file to `opencode.json.headroom-backup` or `config.toml.headroom-backup` before the first change.

### Reusing a running proxy

- `wrap` reuses a proxy that is already running instead of starting a second one. That proxy keeps its startup settings, even if you export different values in the calling shell.
- `wrap` warns when an explicit `HEADROOM_MODE`, `HEADROOM_MIN_TOKENS` or `HEADROOM_EXCLUDE_TOOLS` disagrees with the running proxy. Tool exclusions are compared case-insensitively against the effective list, including built-ins and tools protected by `HEADROOM_PROTECT_TOOL_RESULTS`. Older proxies that do not report a setting cannot be compared.
- `wrap` never restarts a shared proxy, because that would interrupt other clients. Restart it yourself with the settings you want, or start a separate instance with `--port`.
- With `--no-proxy`, `wrap` uses the proxy on `--port` and never starts or re-points one. The OpenCode wrapper exits before it touches `opencode.json` if nothing listens there, the listener is not a Headroom proxy, or it forwards to a different upstream.

| Flag | Effect |
| --- | --- |
| `--port <n>` | Proxy port (default 8787). The VS Code wrappers write the same port into settings. |
| `--no-proxy` | Use an existing proxy instead of starting one (OpenCode, Grok Build). |
| `--learn` / `--memory` | Turn on live traffic learning / persistent memory (OpenCode, Grok Build). |
| `--settings-file <path>` / `--no-configure` | Target a specific settings file / print the settings without editing any file (VS Code wrappers). Pass the same `--settings-file` to `unwrap`. |

**Unwrapping.** `headroom unwrap <tool>` exists for `vscode-claude`, `vscode`, `opencode`, `grok-build` and `codex`. OpenCode and Grok Build restore the pre-wrap backup when one exists, and otherwise strip Headroom's marker blocks. The VS Code wrappers edit only their own keys and preserve unrelated settings. Stopping a wrapper with `Ctrl+C` is not an unwrap – see the pitfalls at the end for what stays behind.

### Per-project savings attribution

Several wrappers put a project name, taken from the directory where you run them, into the proxy URL. The proxy records savings with each completed request and credits them to that project. Run the wrapper, and Grok's `grok`, from the project you want credited.

- Claude Code extension: `ANTHROPIC_BASE_URL` becomes `http://127.0.0.1:8787/p/your-project`. It lives in user-level settings, so it stays until you rerun the wrapper elsewhere.
- Copilot: requests go to `http://127.0.0.1:8787/p/<project>/<native Copilot path>`.
- Grok Build: `base_url` takes an optional `/p/<project>` prefix.
- OpenCode native plugin: shell commands that OpenCode runs see `HEADROOM_PROJECT`.

### Manual routing and verification

For clients that read endpoint variables, you can skip `wrap`. The Claude Code extension in VS Code is not one of them: it reads Claude Code's user settings, not the terminal environment, so use `headroom wrap vscode-claude` for it.

```bash
ANTHROPIC_BASE_URL=http://localhost:8787 claude        # Claude Code
OPENAI_BASE_URL=http://localhost:8787/v1 your-client   # any OpenAI-compatible CLI client
```

To verify any integration while the proxy runs, check that `curl http://127.0.0.1:8787/health` reports `"status": "healthy"`. Then watch "Tokens saved" climb on the dashboard at `http://127.0.0.1:8787/dashboard`, or read the `x-headroom-tokens-before`, `x-headroom-tokens-after` and `x-headroom-tokens-saved` response headers. `curl http://127.0.0.1:8787/stats` returns compression statistics.

## Claude Code in VS Code

This section covers Anthropic's official Claude Code extension, not the Claude desktop app. You need VS Code 1.98 or newer, a signed-in extension that already works, and loopback access to `127.0.0.1` from the extension host. Confirm that the extension works before you add Headroom, so you can tell sign-in problems from proxy problems.

```bash
headroom wrap vscode-claude              # configure settings, start the proxy
headroom wrap vscode-claude --1m         # also persist Claude Code's 1M model selector
headroom unwrap vscode-claude            # restore the prior values
```

The wrapper adds two entries under `env` and preserves any prior values for restoration. Headroom does not store or replace your Anthropic credentials.

```json
{ "env": { "ANTHROPIC_BASE_URL": "http://127.0.0.1:8787/p/your-project", "ENABLE_TOOL_SEARCH": "true" } }
```

- `ENABLE_TOOL_SEARCH` keeps Claude Code's on-demand tool loading enabled behind a custom endpoint.
- After the first run, run **Developer: Reload Window** from the Command Palette. Keep the wrapper terminal open for the whole session.
- The settings file is `~/.claude/settings.json` on macOS and Linux, or `%USERPROFILE%\.claude\settings.json` on Windows. Headroom respects `CLAUDE_CONFIG_DIR`, so launch it where that variable matches Claude Code's value.
- `--settings-file /path/to/.claude/settings.json` targets another profile; pass the same option to `unwrap`. `--no-configure` prints the settings without editing a file, and with `--1m` it also prints the resolved `model` and writes neither the settings file nor the sidecar.
- Headroom refuses malformed settings and will not replace a managed value that changed after setup. Inspect the settings file when it reports a conflict.
- For Dev Containers, Secure Shell (SSH) or Windows Subsystem for Linux (WSL), `127.0.0.1` must reach the environment where Claude Code runs. Run Headroom there or forward the port, and pass that environment's settings file with `--settings-file`.
- If `/health` passes but no request reaches the dashboard or proxy log, reload the window and check that the extension host reaches the same `127.0.0.1`.

**1M selector.** `--1m` writes a top-level `model` with one `[1m]` suffix, for example `"model": "claude-opus-5[1m]"`. If no model is selected, Headroom uses `HEADROOM_1M_MODEL`, then a built-in fallback. The sidecar keeps the prior model, and any later run without `--1m` restores it – so pass `--1m` every time you want to keep the selector. Claude Code and Anthropic still decide whether your account gets the 1M tier.

## Claude Code on Vertex AI

Start from Claude Code working on Vertex AI without Headroom. Vertex mode uses your Google login, so you need no `ANTHROPIC_API_KEY`.

```bash
export CLAUDE_CODE_USE_VERTEX=1
export ANTHROPIC_VERTEX_PROJECT_ID=<your-gcp-project>
export CLOUD_ML_REGION=us-east5          # your Vertex region (or "global")
gcloud auth application-default login    # or set GOOGLE_APPLICATION_CREDENTIALS
headroom wrap claude
```

Because it sees `CLAUDE_CODE_USE_VERTEX=1`, the wrapper starts the proxy and points `ANTHROPIC_VERTEX_BASE_URL` at it. It prints `Vertex mode: ANTHROPIC_VERTEX_BASE_URL=http://127.0.0.1:8787` to confirm. Your project, region and Google login stay untouched.

- Claude Code sends its normal `:rawPredict` / `:streamRawPredict` requests. Headroom compresses the messages, keeps the Vertex request shape, and forwards to the regional host derived from each request, so multi-region and `global` both work. Streaming, tool use and prompt caching all work.
- To use a private Vertex gateway, start the proxy with `--vertex-api-url https://your-gateway`.
- Claude Code's server-side auto-mode classifier works only on the native Anthropic-compatible wire path. On the Vertex translation path it stays fail-open, but may fall back to Claude Code's billable client-side classifier.
- No savings: export `CLAUDE_CODE_USE_VERTEX=1` in the same shell before you run the wrapper. A 404: set `CLOUD_ML_REGION` to a region where your Claude model is enabled. Auth errors: Headroom forwards your token as-is, so fix the login that Claude Code uses without Headroom.

### Alternative: Headroom translates to Vertex

Use this only if you cannot set `CLAUDE_CODE_USE_VERTEX`. Claude Code speaks plain Anthropic to Headroom, and Headroom calls Vertex through LiteLLM. The native flow above is recommended, because it reuses your Google auth and has fewer moving parts.

```bash
export HEADROOM_BACKEND=litellm-vertex_ai     # note the _ai suffix
export HEADROOM_REGION=us-east5
export VERTEXAI_PROJECT=<your-gcp-project>
export GOOGLE_APPLICATION_CREDENTIALS=/path/sa.json   # or gcloud ADC
export ANTHROPIC_API_KEY=placeholder          # Claude Code needs *a* key to start
headroom wrap claude --backend litellm-vertex_ai --region us-east5
```

- The proxy page adds two easy-to-miss requirements for this LiteLLM-backed backend. First, install the Vertex SDK with `pip install "headroom-ai[proxy]" "google-cloud-aiplatform>=1.38"`. No Headroom extra or Docker image includes it, and without it the first request fails with `No module named 'vertexai'`.
- Second, set `VERTEXAI_PROJECT` explicitly (the proxy page also sets `VERTEXAI_LOCATION`). If it is unset, requests can silently bill your ADC default quota project instead of the project you intended.

## Claude Code on Azure AI Foundry

Start from Claude Code working on Azure AI Foundry without Headroom. Foundry mode uses your Azure credentials, so you need no `ANTHROPIC_API_KEY`.

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
export ANTHROPIC_FOUNDRY_RESOURCE=<your-azure-resource-name>
headroom wrap claude
```

The wrapper derives the upstream `https://{ANTHROPIC_FOUNDRY_RESOURCE}.services.ai.azure.com/anthropic`, starts the proxy with it, and points `ANTHROPIC_FOUNDRY_BASE_URL` at the proxy. It prints `Foundry mode: ANTHROPIC_FOUNDRY_BASE_URL=http://127.0.0.1:8787/anthropic`, followed by the upstream URL.

- If `ANTHROPIC_FOUNDRY_BASE_URL` already holds the full Azure endpoint, Headroom uses it, and you can skip `ANTHROPIC_FOUNDRY_RESOURCE`.
- Claude Code keeps authenticating with its own `api-key` or Entra bearer token, which Headroom passes through unchanged.
- If the wrapper prints `ANTHROPIC_BASE_URL` instead of "Foundry mode", it did not see `CLAUDE_CODE_USE_FOUNDRY`. The page accepts these variables in the `env` block of `~/.claude/settings.json`, but its troubleshooting asks you to export them in the wrapper's shell, so export them there.
- A 401 means your credentials are not forwarded correctly. Confirm that Claude Code works against Azure AI Foundry directly before you wrap it.
- "Tokens saved" stuck at 0 means content is below the compression threshold or the Rust extension is missing. `pip install "headroom-ai[proxy]"` includes the extension.

## OpenAI Codex

`headroom wrap codex` scopes routing to the Codex process it launches. It passes the proxy URL as a `--config` override and never writes `~/.codex/config.toml`. Codex runs any session with command-line overrides in embedded mode, so it prints "Running without the shared background server".

To keep Codex's shared background server, write the routing into Codex's own config and start `codex` directly:

```bash
headroom init codex     # this project's .codex/config.toml (trusted projects)
headroom init -g codex  # ~/.codex/config.toml, for every project
```

The trade-off: `wrap codex` leaves nothing behind but gives up the shared server, while `init` keeps the shared server but persists until you remove it.

- `headroom unwrap codex` removes the `-g` routing. For a project, delete the `# --- Headroom init provider ---` block from `.codex/config.toml` yourself.
- Unwrap leaves the `SessionStart` hook that `init` adds to Codex's `hooks.json`. That hook keeps starting a proxy at each Codex session until you delete it.
- On Windows, nothing starts the proxy for this routing, so Codex cannot connect while the proxy is down. Use `headroom install apply` for a supervised proxy.

## VS Code Copilot

Headroom sits below Copilot's native model picker. It overrides the Copilot API endpoint, not the model, so the model you pick travels unchanged to GitHub's Copilot API. No "Headroom" model appears in the picker. Headroom does not patch the extension, terminate Transport Layer Security (TLS) or edit Codex configuration.

```bash
headroom copilot-auth login    # one time: open the GitHub device URL and enter the code
headroom copilot-auth status   # should report "logged in"
headroom wrap vscode           # run from the project to credit; keep it running
headroom unwrap vscode         # remove only Headroom's settings block
```

- **Why a separate login.** VS Code keeps its Copilot token in encrypted extension storage, which Headroom deliberately leaves alone. `copilot-auth login` saves a reusable OAuth credential in Headroom's own auth file with user-only permissions. At launch, Headroom exchanges it for a short-lived Copilot API token that stays in the proxy process and never reaches VS Code settings.
- **What `wrap vscode` writes.** A marker-owned block with `github.copilot.advanced.debug.overrideProxyUrl` (inline completions) and `github.copilot.advanced.debug.overrideCapiUrl` (chat). The settings file is JSON with Comments (JSONC), and its comments, formatting, trailing commas and unrelated settings stay byte-for-byte unchanged.
- **What is not routed.** Telemetry, GitHub API calls, MCP, embeddings, model discovery and cloud agents use separate endpoints and bypass Headroom by design.
- **Models.** There is no static Headroom model list, so new Copilot models work without a Headroom release. Newer models may use the OpenAI Responses API; Headroom proxies both it and Chat Completions. An `unsupported_api_for_model` response from `/chat/completions` is not a proxy failure.
- **Enterprise.** GitHub.com Enterprise Cloud normally needs no override. For GitHub Enterprise Server or custom domains, set `GITHUB_COPILOT_ENTERPRISE_URL` or `GITHUB_COPILOT_ENTERPRISE_DOMAIN` before both `copilot-auth login` and `wrap vscode`.

| Platform | Stable VS Code user settings |
| --- | --- |
| macOS | `~/Library/Application Support/Code/User/settings.json` |
| Windows | `%APPDATA%\Code\User\settings.json` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/Code/User/settings.json` |

- For Insiders, VSCodium, portable installs, a custom `--user-data-dir`, a remote extension host or a VS Code profile with its own settings, pass `--settings-file /path/to/User/settings.json` to both `wrap` and `unwrap`. A profile is the likely cause when Headroom records no requests while Copilot keeps working; `wrap vscode` warns about each profile and prints the path to use.
- If Headroom refuses a malformed file, an incomplete marker or an existing unmanaged Copilot override, repair it, or use `--no-configure` and apply the printed settings by hand.
- While the wrapper runs, the `/health` payload should show the Copilot API endpoint as its OpenAI upstream.

## OpenCode

`headroom wrap opencode` starts or reuses the proxy, writes OpenCode config, registers the Headroom MCP tools, and launches OpenCode with the generated config. Pass OpenCode's own arguments after `--`, as in `headroom wrap opencode --port 8787 -- <opencode args>`.

- **Provider.** Writes a `headroom` provider based on `@ai-sdk/openai-compatible` into `opencode.json`, pointing at `http://127.0.0.1:<port>/v1`. The default model is `headroom/claude-sonnet-4-6`; the provider also maps `headroom/claude-opus-4-6`, `headroom/claude-haiku-4-5-20251001`, `headroom/gpt-4o` and `headroom/gpt-4.1`.
- **Runtime config.** Sets `OPENCODE_CONFIG_CONTENT` with the provider, plugin and optional local MCP config. OpenCode merges it with the on-disk config at startup.
- **Other providers.** Leaves `OPENAI_BASE_URL` and `ANTHROPIC_BASE_URL` alone, so providers added with `/connect` keep their own routing.
- **MCP.** Registers `headroom_compress`, `headroom_retrieve` and `headroom_stats` through `headroom mcp serve` (skip with `--no-mcp`), plus optional Serena code graph tools (skip with `--no-serena`).
- **Backup.** Copies `opencode.json` to `opencode.json.headroom-backup` before any change.

OpenCode 2.x connects to a shared background service by default, and a service that was already running never sees Headroom's config. The wrapper therefore adds `--standalone` on 2.x. If you pass `--server <url>`, start that server with Headroom's config too. To confirm what loaded, run `opencode api plugin.list --param directory="$PWD"`; the output should list `headroom`.

- **Unwrap** restores `opencode.json` from the backup when present, otherwise strips marker blocks, and unregisters the Headroom MCP servers. If the provider survives, run `headroom unwrap opencode` again or restore `~/.config/opencode/opencode.json.headroom-backup` by hand.
- **Persistent install.** `headroom install apply --preset persistent-service --scope provider --providers manual --target opencode` writes the provider into `~/.config/opencode/opencode.json` and keeps the proxy on port 8787. The default user scope writes only shell environment config; direct provider config needs `--scope provider`.
- **Failure learning.** `headroom learn --agent opencode --apply` scans past OpenCode sessions and writes corrections to your project's `AGENTS.md`. Set `HEADROOM_OPENCODE_DB` to override the database it reads.

### Native OpenCode plugin

The default export of the `headroom-opencode` npm package is a native plugin for OpenCode 1.x and 2.x. It intercepts provider traffic in-process, adds the `headroom_retrieve` tool, and sets `HEADROOM_ACTIVE`, `HEADROOM_PROXY_URL` and `HEADROOM_PROJECT` for shell commands that OpenCode runs. Choose it for in-process interception. Choose `wrap` when you want the CLI to manage the proxy, config injection, MCP registration, backups and unwrap.

```json
{ "plugin": [["headroom-opencode", { "proxyUrl": "http://127.0.0.1:8787" }]] }
```

- OpenCode 2.x migrates the 1.x `plugin` key. The native 2.x form is `"plugins": [{ "package": "headroom-opencode", "options": { "proxyUrl": "http://127.0.0.1:8787" } }]`.
- Without `proxyUrl`, the plugin reads `HEADROOM_PROXY_URL`, then falls back to `http://127.0.0.1:8787`. Set `HEADROOM_PROXY_URL` when the plugin cannot reach Headroom.
- The plugin routes every external HTTP(S) request through the proxy. Some gateways validate the client and reject the proxy hop. Exclude them with the `excludeHosts` plugin option, or launch with `HEADROOM_OPENCODE_EXCLUDE_HOSTS=opencode.ai,.corp.internal opencode`. An entry matches the host and its subdomains, and excluded requests get no compression or telemetry.

For custom integrations, the package exports config helpers. The default export has `server` for 1.x and `setup` for 2.x, and `HeadroomPlugin` (1.x) and `headroomSetup` (2.x) are exported by name.

```ts
import { buildOpencodeConfigContent, createHeadroomProvider, createHeadroomRetrieveTool } from "headroom-opencode";

const provider = createHeadroomProvider({ proxyPort: 8787 });
const config = buildOpencodeConfigContent({ proxyPort: 8787, defaultModel: "claude-sonnet-4-6" });
const retrieve = createHeadroomRetrieveTool({ proxyBaseUrl: "http://127.0.0.1:8787" });
```

## OpenCode with DeepSeek

DeepSeek's API is OpenAI-compatible, so the proxy can forward OpenCode's traffic to it. Without an explicit upstream, the proxy forwards OpenAI-compatible traffic to `https://api.openai.com/v1`, and OpenAI rejects your DeepSeek key with `401 Incorrect API key provided`.

First, add a `headroom` provider to `~/.config/opencode/opencode.json`. You need it with or without `wrap`: OpenCode offers only the `headroom/<id>` models listed under `provider.headroom.models`, and DeepSeek needs your key in `options.apiKey`. Merge it into any existing file, and keep only one of `opencode.json` and `opencode.jsonc` in a directory, because both together can conflict. Referencing the key from the environment keeps it out of the file.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "headroom/deepseek-v4-pro",
  "provider": {
    "headroom": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Headroom Proxy",
      "options": { "baseURL": "http://127.0.0.1:8787/v1", "apiKey": "{env:DEEPSEEK_API_KEY}" },
      "models": { "deepseek-v4-pro": { "name": "DeepSeek V4 Pro", "limit": { "context": 1000000, "output": 384000 } } }
    }
  },
  "mcp": { "headroom": { "type": "local", "command": ["headroom", "mcp", "serve"], "enabled": true } }
}
```

Then start the proxy with DeepSeek as its upstream:

| Do this | Don't do this |
| --- | --- |
| `headroom wrap opencode --openai-api-url https://api.deepseek.com/v1`, or set `OPENAI_TARGET_API_URL` to that URL before `headroom wrap opencode` | Run a plain `headroom wrap opencode` with a DeepSeek, Together, OpenRouter, Groq or self-hosted gateway key |
| `headroom proxy --port 8787 --openai-api-url https://api.deepseek.com/v1`, then run `opencode` | Expect `wrap` to re-point a proxy that already targets another upstream. Stop it first with `headroom unwrap opencode` |

- A plain `wrap` is safe only when traffic goes to the default upstreams, OpenAI (`api.openai.com`) or Anthropic (`api.anthropic.com`).
- With the flag, `wrap` keeps your `options.apiKey` and `models`, rewrites the provider's `npm`, `name` and `baseURL`, and adds its default `gpt-4o` and `gpt-4.1` ids. Without the flag, it leaves your key and models out, so they never reach OpenAI.
- To let `wrap` reuse a proxy you started, run `headroom wrap opencode --no-proxy --openai-api-url https://api.deepseek.com/v1`. That proxy must already target the same upstream.
- OpenCode validates config models against the proxy's model list. Use only ids that `curl -s http://127.0.0.1:8787/v1/models -H "Authorization: Bearer sk-your-key" | jq '.data[].id'` returns, spelled exactly. Confirm with `/models` in OpenCode.
- The page names `deepseek-flash` and `deepseek-v4-pro` as current, yet its config example uses the retired `deepseek-v4-flash`, which DeepSeek still accepts. `deepseek-chat` and `deepseek-reasoner` are deprecated aliases.
- An "Authentication Fails" or Unauthorized error means `options.apiKey` is missing or wrong. OpenCode must send the key to the proxy, which forwards it to DeepSeek.

### Output shaping

Output shaping makes the model's responses shorter. Turn it on with environment variables when you start the proxy:

```bash
HEADROOM_OUTPUT_SHAPER=1 HEADROOM_VERBOSITY_LEVEL=2 \
headroom proxy --port 8787 --openai-api-url https://api.deepseek.com/v1
```

Levels are cumulative: `1` skips preambles and postambles, `2` also avoids restating code or file content already in context (recommended), `3` also omits rationale unless asked, and `4` is the maximum – fragments, no fluff. The shaper works at once, but `/stats` reports output savings only against a learned baseline. After a few sessions, run `headroom learn --verbosity --apply` to build it.

## Grok Build

```bash
headroom wrap grok-build     # terminal 1: start or reuse the proxy, edit Grok's config
grok                         # terminal 2, from the same project directory
headroom unwrap grok-build   # when you are done
```

- The wrapper writes or updates `[model.grok-build] base_url` in `~/.grok/config.toml` (or `$GROK_HOME/config.toml`), pointing at `http://127.0.0.1:<port>/v1` with an optional `/p/<project>` prefix.
- If that table already exists, Headroom rewrites `base_url` in place, because a duplicate table would make the file invalid.
- Before the first injection, it copies the file to `config.toml.headroom-backup`. Unwrap restores that backup, or strips marker blocks and in-place `base_url` rewrites when no backup exists.
- Flags: `--port` (default 8787), `--no-proxy`, `--learn`, `--memory`. The API key comes from `XAI_API_KEY` (`GROK_CODE_XAI_API_KEY` also works).
- `headroom mcp install` can register the Headroom MCP server for Grok through `GrokRegistrar`. For a persistent install, note the underscore in the target name: `headroom install apply --providers manual --target grok_build`.

## Hermes plugin

Hermes Agent registers its own tools, so unlike Claude Code it does not receive the `headroom_retrieve` MCP tool automatically. Without a retrieval tool, the model re-runs the original command or tries to `cat` a marker such as `ccr:abc123` as a file. The bundled `plugins/hermes` plugin adds a native `headroom_retrieve` tool that calls the proxy's `POST /v1/retrieve` endpoint.

From a checkout of the Headroom repository, copy the plugin:

```bash
mkdir -p ~/.hermes/plugins
cp -r plugins/hermes/headroom_retrieve ~/.hermes/plugins/
```

Enable it in `~/.hermes/config.yaml`, then restart the Hermes gateway or text user interface (TUI), because plugin discovery is cached per process:

```yaml
toolsets:
  - hermes-cli
  - web
  - headroom        # add this

plugins:
  enabled:
    - headroom_retrieve
```

- Once `plugins.enabled` exists, it is an explicit allowlist. List every other user plugin you rely on, because unlisted plugins stay disabled.
- The plugin expects the proxy on `127.0.0.1:8787`. For another address, edit `_PROXY_URL` in the plugin's `__init__.py`. It also needs `httpx`, which Hermes already depends on.
- It accepts `<<ccr:abc123,base64,4.5KB>>`, `ccr:abc123` or `hash=abc123`, and always returns the full original. On an expired hash or an unreachable proxy, it tells the model to re-run the original command instead of retrying blindly.
- You need no proxy change to prevent retrieval loops, because `headroom_retrieve` is a protected built-in in `DEFAULT_EXCLUDE_TOOLS` and `DEFAULT_VERBATIM_EXCLUDE_TOOLS`.
- Consider `HEADROOM_EXCLUDE_TOOLS=read_file`. The built-in defaults protect Claude Code's `Read`, `Grep` and `Edit`, not Hermes's tool names, and file reads are reference data the agent needs verbatim. Configured exclusions merge with the defaults instead of replacing them.
- The page reports testing with headroom 0.22.4 and 0.23.0 on macOS and Linux.

## OpenClaw plugin

The `@headroom-ai/openclaw` plugin brings Headroom compression into OpenClaw.

```bash
headroom wrap openclaw                     # recommended
pip install "headroom-ai[proxy]"           # manual install, step 1
openclaw plugins install --dangerously-force-unsafe-install headroom-ai/openclaw   # step 2
```

OpenClaw treats plugins that can launch processes as unsafe. This plugin declares that capability for its optional proxy auto-start, so the manual install needs `--dangerously-force-unsafe-install` even if you only use a remote proxy. Install selects `headroom` for the `contextEngine` slot. To switch back, set `plugins.slots.contextEngine` to `"legacy"` or another engine id.

| Option | Default | Purpose |
| --- | --- | --- |
| `proxyUrl` | auto-detected | Local or remote proxy. Remote URLs are connect-only: probed at startup, never spawned. |
| `proxyPort` | `8787` | Port for auto-detect and auto-start when `proxyUrl` is unset. |
| `autoStart` | `false` | Start a local `headroom proxy` if none is found. Keep `false` when systemd or another supervisor owns the proxy. |
| `requestTimeoutMs` | `30000` | Cap on one compression call. On timeout, the original uncompressed messages are used. |
| `circuitBreakerThreshold` | `3` | Consecutive `assemble()` errors before all requests bypass the proxy. After `circuitBreakerCooldownMs` (default `60000`), the breaker resets and re-probes `/health`. |
| `routeCodexViaProxy` | `true` | Rewrite the built-in `openai-codex` provider base URL to the proxy, in memory. |
| `gatewayProviderIds` | `[]` | Provider ids to route through the proxy. Accepts the aliases `codex`, `claude`, `copilot` and `gemini`, and overrides the default `openai-codex` list. |

```json
{
  "plugins": { "entries": { "headroom": { "enabled": true, "config": {
    "gatewayProviderIds": ["openai-codex", "anthropic", "github-copilot", "google", "openrouter"]
  } } } }
}
```

- Unlike the VS Code wrappers, the plugin fails open: timeouts and an open circuit breaker send requests uncompressed. The agent keeps working, but those requests earn no savings.
- Gateway rewrites live in memory and never reach `openclaw.json`. Disabling the plugin, clearing `gatewayProviderIds` or restarting without Headroom restores normal routing. For durable provider rewrites, use `headroom wrap openclaw`.
- The proxy keeps its own Codex routing. It still chooses between `api.openai.com` and `chatgpt.com/backend-api/codex/responses` based on ChatGPT auth.
- For a local build, run `npm install`, `npm run build` and `openclaw plugins install --dangerously-force-unsafe-install --link .` inside `plugins/openclaw`. The plugin looks for a launcher on PATH, then the local npm bin, then global npm, then Python.

## Agent hooks plugin

The bundled `plugins/headroom-agent-hooks` plugin keeps Claude Code and GitHub Copilot CLI from starting work against a dead proxy. Each hook runs one hidden helper, `headroom init hook ensure`, with a 15-second timeout. The helper checks for a matching durable `headroom init` deployment and starts it if needed.

- `SessionStart` with matcher `startup|resume`: the deployment is ready before the first turn.
- `PreToolUse` with matcher `Bash|PowerShell`: shell tools always hit a live proxy.

For Claude Code, install it as a plugin from the Headroom repository; it ships a `.claude-plugin/plugin.json` manifest. For Copilot CLI, use Copilot's plugin mechanism with the included `.github/plugin/plugin.json`. Both manifests share `hooks/hooks.json`, so behavior is identical.

## MCP tools

The Headroom MCP server exposes compression, retrieval and stats as tools that any MCP host can call, including Claude Code, Cursor and Codex. It needs no proxy. Install the light extra with `pip install "headroom-ai[mcp]"`, or `[proxy]` if you also run the proxy.

| Tool | Parameters | Returns |
| --- | --- | --- |
| `headroom_compress` | `content` (required) | `compressed`, `hash`, `original_tokens`, `compressed_tokens`, `savings_percent`, `transforms` |
| `headroom_retrieve` | `hash` (required), `query` (optional, searches within the original) | `original_content`, or `results` for a query, plus `source` (`"local"` or `"proxy"`) |
| `headroom_stats` | none | `compressions`, `retrievals`, `tokens_saved`, `savings_percent`, `estimated_cost_saved_usd`, `recent_events`, `sub_agents`, `combined`, `proxy` |

- `headroom_compress` keeps originals in a local `CompressionStore` for 1 hour. Proxy-stored originals expire after 30 minutes; change that with `HEADROOM_CCR_TTL_SECONDS`.
- `headroom_retrieve` checks the local store first, then the proxy's store, so hashes from either source work.
- Sub-agent stats aggregate through the shared file `~/.headroom/session_stats.jsonl`.
- Error messages: "MCP SDK not installed" means the `[mcp]` extra is missing. "Proxy not running" matters only for proxy-backed retrieval. "Entry not found or expired" means the original outlived its expiry window.

### Register with Claude Code

```bash
headroom mcp install                                # one-time registration; --force overwrites an existing entry
headroom mcp install --proxy-url http://host:9000   # custom proxy URL
headroom mcp status                                 # check; headroom mcp uninstall removes it
```

Restart Claude Code and check the tools with `/mcp`. The MCP tools compress only on demand. For automatic compression of all traffic, also run `headroom proxy` and start Claude Code with `ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude`.

### Register with Cursor and other MCP hosts

Point any host that accepts a local stdio server at `headroom mcp serve`. If you run a proxy, pass its URL so retrieval and stats come from the intended instance. Register one entry per proxy when you run several:

```json
{
  "mcpServers": {
    "headroom": { "type": "stdio", "command": "headroom", "args": ["mcp", "serve", "--proxy-url", "http://127.0.0.1:8787"] },
    "headroom-azure": { "type": "stdio", "command": "headroom", "args": ["mcp", "serve", "--proxy-url", "http://127.0.0.1:8788"] }
  }
}
```

| Do this | Don't do this |
| --- | --- |
| Install globally with `uv tool install "headroom-ai[mcp]"` or `pipx install "headroom-ai[mcp]"`, or set `command` to the absolute path from `command -v headroom` (`where headroom` on Windows) | Rely on a virtualenv-only install such as `uv add headroom-ai`. The host cannot find `headroom` and fails with `MCP startup failed: No such file or directory (os error 2)` |
| Run `headroom mcp serve --transport http` for Streamable HTTP (defaults: port `8788`, path `/mcp`) | Assume a running proxy serves MCP at `/mcp`. The proxy serves its own API only |

- For an MCP registry, use the canonical descriptor at `https://github.com/headroomlabs-ai/headroom/blob/main/server.json`. `headroom mcp serve --debug` runs the server in debug mode.
- For user-managed Serena drift, `headroom mcp reconcile` shows the recommendation. Add `--adopt` only when you want Headroom to replace the Serena entry. If an enabled Claude Code plugin bundles Serena, Headroom prints the `claude plugin disable` command instead of editing the plugin.

**MCP alongside the proxy.** The proxy compresses all traffic at the HTTP level before the model sees it, while MCP tools act after the model receives content. They handle different data and do not double-compress.

Claude Code's `/usage` counts MCP calls and results as session context, so a busy workflow can show a large `headroom` share. That share is not a Headroom overhead bill. To shrink it, compare `tokens_saved` from `headroom_stats` with the number of calls, run `/compact` after large MCP-backed steps, and prefer the proxy for routine traffic. Disable the MCP server in proxy-only sessions, and reduce subagent fan-out first, because subagent traffic usually dominates.

## Codex recovery

Older versions of `headroom wrap codex` could run Codex with a temporary `CODEX_HOME` named `headroom-codex-home-*`. Chats and config from those sessions disappeared from normal Codex history after the wrapper exited. Recovery merges the retained state into the durable Codex home without deleting either source. Fixed versions run Codex against the durable home, so new wrapped sessions need no recovery.

Recovery needs a temporary home that still exists, or a pinned copy from an interrupted recovery. Headroom cannot rebuild a deleted temporary home, and it ignores paths pasted into prompts or error messages.

```bash
headroom recover codex                  # close Codex first; discovers retained homes and previews
headroom recover codex \
  --source /path/to/headroom-codex-home-12345 \
  --target "${CODEX_HOME:-$HOME/.codex}"
```

- The target defaults to `$CODEX_HOME`, otherwise `~/.codex`. Confirm that it is the home you normally use.
- Repeat `--source` to merge several homes. Headroom shows the target and every source before it asks. Use `--yes` only in automation where you already reviewed those paths.
- The first interactive `headroom wrap codex` on a fixed version scans `$TMPDIR`, `/tmp`, `/private/tmp`, Python's temporary directory and macOS `/private/var/folders/*/*/T`, then offers recovery. Declining changes nothing.
- With nothing left to recover, the command audits the thread database, rollout files and `history.jsonl`. History-only prompt text cannot rebuild a full transcript.
- Codex's resume picker filters by working directory. Run `codex resume --all` yourself to see every chat; Headroom never launches Codex during recovery.

**Merge rules.**

- JSON Lines (JSONL) indexes such as `history.jsonl` combine without duplicate records, and malformed input goes to quarantine. Session rollouts under `sessions/` and `archived_sessions/` keep the newer file.
- SQLite databases merge only when their schemas and migration checksums are compatible. Primary-key conflicts keep the newer database's rows.
- Thread rows and rollout `session_meta` records that used the old wrapper's localhost `headroom` provider move to the target's active provider. A user-defined remote provider named `headroom` stays.
- `config.toml` merges recursively with newer values winning, and the old wrapper's localhost Headroom routing is removed.
- Other files, including credentials and user settings, keep the newer copy. The target wins modification-time ties, and missing source files never delete target files. Sockets, lock files, SQLite journals and other runtime-only files are recorded but not copied.

Each run keeps an owner-only backup in `<target-parent>/.headroom-codex-recovery/<timestamp-pid>/`, with `source-pinned/`, `target-before/` and `manifest.json`, plus `target-failed/` and `quarantine/` when needed. If parsing, schema validation, integrity checks or writes fail, Headroom renames the failed target to `target-failed/` and restores `target-before/`. Recovery also refuses overlapping source and target paths, symlink traversal in the target, and a source that changes while it is pinned. After a successful run, review `manifest.json`, start Codex, and confirm your chats and settings. Keep the backup until you have verified the history.

## Pitfalls

- **A stopped proxy blocks requests.** Both VS Code wrappers keep the endpoint after `Ctrl+C`, so Claude Code and Copilot requests fail until you rerun the wrapper or unwrap. Keep the wrapper terminal open for the whole session. For Claude Code and GitHub Copilot CLI on a durable `headroom init` deployment, the agent hooks plugin starts that deployment when a session begins.
- **Plugins fail open instead.** OpenClaw sends requests uncompressed on timeouts and circuit-breaker trips. The Hermes plugin tells the model to re-run the command when the proxy is unreachable. Work continues, but without savings.
- **The wrong upstream receives your key.** A plain `headroom wrap opencode` forwards OpenAI-compatible traffic to OpenAI. A third-party key then fails with a 401 from OpenAI, not from your provider.
- **Credential handling.** Headroom passes Anthropic, Google and Azure credentials through and stores none of them. The Vertex alternative sets `ANTHROPIC_API_KEY=placeholder` only so that Claude Code starts. Copilot is the exception: `copilot-auth login` stores an OAuth credential in Headroom's own user-only auth file.
- **Leftover configuration after unwrapping.** `Ctrl+C` is not an unwrap. Pass `unwrap` the same `--settings-file` you passed `wrap`. After `headroom unwrap codex`, the `SessionStart` hook in Codex's `hooks.json` and any project-level `headroom init codex` block remain. OpenClaw keeps `headroom` in the `contextEngine` slot until you change it.
- **Unwrap restores the pre-wrap file.** OpenCode and Grok Build unwrap from the backup taken before the first change, so edits you made to that file while wrapped may be lost. Copy them out before you unwrap.
- **Port collisions.** `headroom mcp serve --transport http` defaults to port 8788, the same port the docs suggest for a second proxy. Give each listener its own port.
- **Remote hosts and profiles.** In Dev Containers, SSH or WSL, `127.0.0.1` must reach Headroom from where the agent runs. VS Code profiles keep their own settings files, so configure each one with `--settings-file`.
- **`headroom` not on PATH.** `uv tool install` puts binaries in `~/.local/bin/`. Run `export PATH="$HOME/.local/bin:$PATH"`.

## Related skills

- [getting-started](./getting-started.md) – installation, persistent installs with `headroom install apply`, and the Docker-native wrapper.
- [proxy](./proxy.md) – proxy CLI options, endpoints such as `/health`, `/stats` and `/v1/retrieve`, and cloud backends, including the `--bedrock-api-url` route for Claude Code with `CLAUDE_CODE_USE_BEDROCK=1`.
- [ccr-and-caching](./ccr-and-caching.md) – how CCR markers, `headroom_retrieve` and the retrieval store work.
- [compression](./compression.md) – what SmartCrusher and the other compressors do to tool output, logs and files.
- [memory](./memory.md) – what `--memory` and `--learn` do, and `headroom learn` failure learning.
- [configuration](./configuration.md) – `HEADROOM_EXCLUDE_TOOLS`, `HEADROOM_CCR_TTL_SECONDS` and the other environment variables.
- [observability](./observability.md) – the dashboard, `/stats` and savings tracking.
- [framework-integrations](./framework-integrations.md) – SDK clients and the LiteLLM callback, which differs from the proxy's `--backend vertex_ai`.
- [sdk-reference](./sdk-reference.md) – Python and TypeScript APIs.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – fixes by symptom and safety gates.
- [architecture-and-security](./architecture-and-security.md) – the security model and runtime rollouts.

## Source pages

- https://docs.headroomlabs.ai/docs/vscode-claude-code
- https://docs.headroomlabs.ai/docs/claude-code-vertex
- https://docs.headroomlabs.ai/docs/claude-code-azure-foundry
- https://docs.headroomlabs.ai/docs/vscode-copilot
- https://docs.headroomlabs.ai/docs/opencode
- https://docs.headroomlabs.ai/docs/opencode-deepseek
- https://docs.headroomlabs.ai/docs/grok-build
- https://docs.headroomlabs.ai/docs/hermes
- https://docs.headroomlabs.ai/docs/openclaw
- https://docs.headroomlabs.ai/docs/agent-hooks
- https://docs.headroomlabs.ai/docs/mcp
- https://docs.headroomlabs.ai/docs/codex-recovery
- https://docs.headroomlabs.ai/docs/proxy (the "Agent wrapping" and "Cloud providers" sections only)
