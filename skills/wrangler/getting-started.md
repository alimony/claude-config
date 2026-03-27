# Wrangler: Getting Started
Based on Wrangler documentation from developers.cloudflare.com.

## Overview

Wrangler is Cloudflare's CLI for the Developer Platform. It handles creating, developing, testing, and deploying Workers (and related resources like KV, R2, D1, Queues, etc.).

General command syntax:

```
wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]
```

Run via your package manager:

```bash
npx wrangler <COMMAND>     # npm
yarn wrangler <COMMAND>     # yarn
pnpm wrangler <COMMAND>     # pnpm
```

## Installation

### System Requirements

- **Node.js**: Current, Active, or Maintenance LTS versions
- **OS**: macOS 13.5+, Windows 11, or Linux with glibc 2.35+
- A version manager (Volta or nvm) is recommended to avoid permission issues

### Install Locally (Recommended)

Wrangler should be installed locally per-project so the team stays on the same version:

```bash
npm i -D wrangler@latest        # npm
yarn add -D wrangler@latest     # yarn
pnpm add -D wrangler@latest     # pnpm
```

Global installation is **not recommended**. Running `npx wrangler` without a local install will auto-use the latest version.

### Check Version

```bash
npx wrangler --version
```

### Update

Re-run the same install command to update:

```bash
npm i -D wrangler@latest
```

## Authentication

### Login (OAuth)

```bash
npx wrangler login
```

Opens a browser for OAuth authorization with Cloudflare. For containers/remote machines, bind to all interfaces:

```bash
npx wrangler login --callback-host=0.0.0.0
```

### API Token (CI / Non-Interactive)

Set the `CLOUDFLARE_API_TOKEN` environment variable instead of using OAuth:

```bash
export CLOUDFLARE_API_TOKEN="your-api-token"
```

### Verify Authentication

```bash
npx wrangler whoami          # show user and account info
npx wrangler whoami --json   # JSON output
```

### Logout

```bash
npx wrangler logout          # revokes the current OAuth token
```

### Retrieve Current Token

```bash
npx wrangler auth token      # prints current auth credential
```

Token resolution order: `CLOUDFLARE_API_TOKEN` env var > API key/email env vars > OAuth token (auto-refreshed).

## Project Setup

### Create a New Project

```bash
npx wrangler init my-worker
```

This delegates to `create-cloudflare-cli` (C3). It scaffolds a project directory with framework selection and template support.

Skip prompts with `--yes`:

```bash
npx wrangler init my-worker --yes
```

Pull an existing Worker from the dashboard:

```bash
npx wrangler init my-worker --from-dash <WORKER_NAME>
```

### Configuration File

Cloudflare recommends `wrangler.jsonc` for new projects (newer features are increasingly JSON-only). TOML (`wrangler.toml`) is also supported.

Minimal `wrangler.toml`:

```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2026-03-27"
```

Minimal `wrangler.jsonc`:

```jsonc
{
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2026-03-27"
}
```

**Required fields:**

| Field                | Purpose                                      |
|----------------------|----------------------------------------------|
| `name`               | Worker identifier (alphanumeric + dashes, max 255 chars) |
| `main`               | Entry point file path                        |
| `compatibility_date` | Runtime version pinning (`yyyy-mm-dd`)       |

### Environments

Define environment-specific config under `[env.<name>]` sections. Most settings inherit from top-level, but **bindings** (KV, R2, D1) must be redefined per environment.

```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2026-03-27"

[env.staging]
name = "my-worker-staging"
route = "staging.example.com/*"

[env.production]
name = "my-worker-prod"
route = "example.com/*"
```

Deploy to a specific environment:

```bash
npx wrangler deploy --env staging
```

Treat the config file as the source of truth. Dashboard changes will be overwritten on next deploy.

## Core Commands

### Local Development

```bash
npx wrangler dev                     # start dev server on localhost:8787
npx wrangler dev --port 3000         # custom port
npx wrangler dev --remote            # run against remote Cloudflare resources
npx wrangler dev --test-scheduled    # expose /__scheduled for cron testing
```

### Deploy

```bash
npx wrangler deploy                          # deploy to Cloudflare
npx wrangler deploy --dry-run                # compile without deploying
npx wrangler deploy --env production         # deploy specific environment
npx wrangler deploy --minify                 # minify before deploy
npx wrangler deploy --keep-vars              # preserve dashboard env vars
```

### Secrets

```bash
npx wrangler secret put MY_SECRET            # set a secret (prompts for value)
npx wrangler secret list                     # list all secrets
npx wrangler secret delete MY_SECRET         # remove a secret
npx wrangler secret bulk .env                # bulk upload from .env or JSON file
```

### Versioned Deployments

```bash
npx wrangler versions upload                 # create version without deploying
npx wrangler versions deploy --version-id <ID> --percentage 50  # gradual rollout
npx wrangler deployments list                # show recent deployments
npx wrangler rollback <VERSION_ID>           # rollback to a previous version
```

### Monitoring

```bash
npx wrangler tail my-worker                  # stream live logs
npx wrangler tail my-worker --status error   # filter errors only
npx wrangler tail my-worker --search "foo"   # filter by console.log content
```

### Other Useful Commands

```bash
npx wrangler types                   # generate TypeScript types from config
npx wrangler delete                  # delete Worker and associated resources
npx wrangler setup                   # configure project without deploying
npx wrangler docs [SEARCH]           # open Cloudflare docs in browser
npx wrangler complete bash           # generate shell completions (bash/zsh/fish)
npx wrangler telemetry disable       # opt out of anonymous telemetry
```

### Global Flags

| Flag                  | Purpose                            |
|-----------------------|------------------------------------|
| `--help`              | Show help                          |
| `--config / -c`       | Specify config file path           |
| `--cwd`               | Run from a different directory     |
| `--env / -e`          | Target a named environment         |
| `--version / -v`      | Show Wrangler version              |

## Deprecations

### Wrangler v4 (Current)

- **Workers Sites** is deprecated. Migrate to **Workers Static Assets**.
- **`legacy_env`** config property is deprecated. Use Wrangler Environments instead.

### Wrangler v3 Removals (Still Relevant if Upgrading)

Commands renamed or removed:

| Deprecated                     | Replacement                              |
|--------------------------------|------------------------------------------|
| `wrangler publish`             | `wrangler deploy`                        |
| `wrangler pages publish`       | `wrangler pages deploy`                  |
| `wrangler generate`            | `npm create cloudflare@latest`           |
| `wrangler version`             | `wrangler --version`                     |

Removed flags:

| Removed Flag                   | Notes                                    |
|--------------------------------|------------------------------------------|
| `--experimental-local`         | Dev runs locally by default now          |
| `--local`                      | Dev runs locally by default now          |
| `--persist`                    | Data persistence is automatic            |
| `--node-compat`                | Use `nodejs_compat` compatibility flag   |

Removed config properties:

| Removed Property               | Notes                                    |
|--------------------------------|------------------------------------------|
| `usage_model`                  | No longer functional                     |
| `--legacy-assets` / `legacy_assets` | Removed                             |

### Wrangler v2 Removals

These commands no longer exist: `wrangler build`, `wrangler config`, `wrangler preview`, `wrangler subdomain`, `wrangler route`.

Key v2 changes:
- `wrangler.toml` is no longer mandatory (but recommended)
- `main` entry point must be explicit
- `type`, `zone_id`, `build.upload.format` are auto-inferred and deprecated as config fields
- Bare specifiers need relative paths (e.g., `"./some-dep.js"` not `"some-dep.js"`)

## Quick Reference

```bash
# Full setup flow
npm i -D wrangler@latest         # 1. install
npx wrangler login               # 2. authenticate
npx wrangler init my-worker      # 3. scaffold project
cd my-worker
npx wrangler dev                 # 4. develop locally
npx wrangler deploy              # 5. ship it
npx wrangler tail my-worker      # 6. monitor logs
```
