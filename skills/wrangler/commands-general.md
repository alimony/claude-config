# Wrangler: General Commands
Based on Wrangler documentation from developers.cloudflare.com.

## Core Concepts

Wrangler's general commands cover the full lifecycle of a Cloudflare Worker: create, develop locally, deploy, manage secrets, monitor logs, control versions, and roll back. Key mental model:

- **Version** = a snapshot of your Worker code + config (not yet serving traffic)
- **Deployment** = a version (or split of versions) actively serving production traffic
- `wrangler deploy` creates a version AND deploys it in one step
- `wrangler versions upload` + `wrangler versions deploy` splits those steps apart (needed for gradual rollouts)

---

## Quick Reference

| Task | Command |
|------|---------|
| Start local dev server | `wrangler dev` |
| Deploy to production | `wrangler deploy` |
| Set a secret | `wrangler secret put KEY` |
| Bulk-load secrets | `wrangler secret bulk secrets.json` |
| Stream live logs | `wrangler tail` |
| Check current auth | `wrangler whoami` |
| Generate TS types | `wrangler types` |
| Roll back a deploy | `wrangler rollback [VERSION_ID]` |
| Delete a Worker | `wrangler delete` |
| Upload without deploying | `wrangler versions upload` |
| Gradual rollout | `wrangler versions deploy <v1>@90% <v2>@10%` |
| Check deploy status | `wrangler deployments status` |
| Profile startup perf | `wrangler check startup` |

---

## Local Development (`wrangler dev`)

### Basic Usage

```bash
# Uses main from wrangler.toml
wrangler dev

# Explicit entry point
wrangler dev src/index.ts

# Custom port
wrangler dev --port 3000

# Test cron triggers locally
wrangler dev --test-scheduled
# Then hit: curl http://localhost:8787/__scheduled
```

### Important Flags

| Flag | Purpose |
|------|---------|
| `--remote` | Use real Cloudflare resources instead of local simulation |
| `--port <n>` | Listen on a specific port (default: 8787) |
| `--local-protocol https` | Serve over HTTPS locally |
| `--persist-to <dir>` | Where to store local KV/D1/R2 data between restarts |
| `--var key:value` | Inject variables without touching wrangler.toml |
| `--env <name>` | Use a specific environment config |
| `--no-bundle` | Skip esbuild bundling (use your own build pipeline) |
| `--test-scheduled` | Expose `/__scheduled` endpoint for cron testing |
| `--config/-c` | Config file(s); pass multiple for multi-worker dev sessions |

### Injecting Variables and Defines

```bash
# Runtime variables (accessible via env.*)
wrangler dev --var "git_hash:'$(git rev-parse HEAD)'" "debug:true"

# Build-time replacements (like #define in C)
wrangler dev --define "GIT_HASH:'$(git rev-parse HEAD)'"
```

### Do This / Don't Do This

```bash
# DO: Use --persist-to for stable local data across restarts
wrangler dev --persist-to .wrangler/state

# DON'T: Rely on --remote for everyday development
# Local mode is faster and doesn't consume API calls

# DO: Use --test-scheduled to verify cron handlers
wrangler dev --test-scheduled

# DON'T: Forget that --latest defaults to true
# Pin --compatibility-date in production configs instead
```

---

## Deploying (`wrangler deploy`)

### Basic Usage

```bash
# Deploy using wrangler.toml config
wrangler deploy

# Deploy a specific entry point
wrangler deploy src/index.ts

# Deploy to a named environment
wrangler deploy --env staging

# Dry run (compile only, do not upload)
wrangler deploy --dry-run
```

### Important Flags

| Flag | Purpose |
|------|---------|
| `--dry-run` | Compile and validate without deploying |
| `--keep-vars` | Preserve variables set via dashboard (don't overwrite) |
| `--env <name>` | Target a specific environment |
| `--minify` | Minify output before uploading |
| `--tag <str>` | Tag the version (useful for gradual rollouts) |
| `--message <str>` | Human-readable deployment message |
| `--strict` | Defensive mode; prevents risky deployments |
| `--triggers/--schedule` | Set cron triggers inline |
| `--routes/--route` | Set routes inline |

### Auto-Detection

When no `wrangler.toml` exists, `wrangler deploy` auto-detects your framework (Next.js, Remix, etc.) and configures the project automatically. Use `wrangler setup` to do the configuration step without deploying.

### CI/CD Pattern

```bash
# Authenticate via environment variable
export CLOUDFLARE_API_TOKEN="your-api-token"

# Deploy with a version message
wrangler deploy --message "deploy: $(git rev-parse --short HEAD)"

# Keep dashboard-set secrets intact
wrangler deploy --keep-vars
```

---

## Secrets Management (`wrangler secret`)

### Critical Distinction

| Command | Effect |
|---------|--------|
| `wrangler secret put` | Creates secret AND immediately deploys a new version |
| `wrangler versions secret put` | Creates secret in a new version WITHOUT deploying |

Choose `wrangler versions secret` when you need to control exactly when secrets go live.

### Common Patterns

```bash
# Interactive prompt for value
wrangler secret put API_KEY

# Pipe a value (useful for multiline keys)
echo "sk-live-abc123" | wrangler secret put STRIPE_KEY

# Pipe a multiline private key
echo "-----BEGIN PRIVATE KEY-----\nM...==\n-----END PRIVATE KEY-----\n" | wrangler secret put PRIVATE_KEY

# Bulk upload from JSON
wrangler secret bulk secrets.json
# secrets.json format:
# { "API_KEY": "value1", "DB_PASSWORD": "value2" }

# Bulk upload also supports .env format
wrangler secret bulk .env

# List all secrets (names only, values are never exposed)
wrangler secret list

# Delete a secret
wrangler secret delete OLD_KEY
```

### Do This / Don't Do This

```bash
# DO: Use `secret bulk` for setting multiple secrets at once (one deployment)
wrangler secret bulk secrets.json

# DON'T: Run `secret put` in a loop -- each call triggers a separate deployment
# Bad:
for key in KEY1 KEY2 KEY3; do wrangler secret put $key; done

# DO: Use `versions secret put` when you need deployment control
wrangler versions secret put API_KEY --message "rotate API key"

# DON'T: Put secrets in --var flags or wrangler.toml -- they're not encrypted
```

---

## Versions and Gradual Rollouts

Requires wrangler >= 3.40.0. Before 3.73.0, add `--x-versions` flag.

### Upload Without Deploying

```bash
wrangler versions upload --tag "v2.1.0" --message "new caching layer"
```

### Gradual Rollout

```bash
# Interactive (prompts for percentages)
wrangler versions deploy

# Non-interactive: send 10% to new version, 90% stays on old
wrangler versions deploy \
  095f00a7-23a7-43b7-a227-e4c97cab5f22@10% \
  1a88955c-2fbd-4a72-9d9b-3ba1e59842f2@90% \
  -y
```

### Inspect Versions

```bash
# List recent versions
wrangler versions list

# View specific version details
wrangler versions view <VERSION_ID>

# Check what's currently deployed
wrangler deployments status

# List deployment history
wrangler deployments list
```

---

## Rolling Back

```bash
# Roll back to previous version (interactive confirmation)
wrangler rollback

# Roll back to a specific version
wrangler rollback <VERSION_ID>

# Skip confirmation prompt
wrangler rollback <VERSION_ID> --message "reverting bad deploy"
```

**Warning:** Rollback immediately creates a new deployment and becomes the active version across ALL routes and domains. There is no "undo rollback" -- you'd need to deploy the desired version again.

---

## Live Logging (`wrangler tail`)

```bash
# Basic tail
wrangler tail my-worker

# Pretty-print logs
wrangler tail my-worker --format pretty

# Only show errors
wrangler tail my-worker --status error

# Filter to specific HTTP method
wrangler tail my-worker --method POST

# Filter by text in console.log output
wrangler tail my-worker --search "database timeout"

# Filter by your own IP
wrangler tail my-worker --ip self

# Tail a specific version
wrangler tail my-worker --version-id <VERSION_ID>

# Sample 10% of requests (high-traffic workers)
wrangler tail my-worker --sampling-rate 0.1
```

**Gotcha:** High-traffic Workers may enter sampling mode automatically, dropping some log messages. Use `--sampling-rate` proactively to control this.

---

## Authentication

### Login Methods

```bash
# Browser-based OAuth (default)
wrangler login

# Check who you're logged in as
wrangler whoami

# Get current token (for scripts)
wrangler auth token

# Get token as JSON with type info
wrangler auth token --json

# Logout (invalidates OAuth token)
wrangler logout
```

### CI/CD Authentication (No Browser)

```bash
# Preferred: API token (scoped permissions)
export CLOUDFLARE_API_TOKEN="your-token"

# Alternative: Global API key (full account access -- avoid if possible)
export CLOUDFLARE_API_KEY="your-key"
export CLOUDFLARE_EMAIL="your-email"
```

**Auth precedence:** `CLOUDFLARE_API_TOKEN` > `CLOUDFLARE_API_KEY`+`CLOUDFLARE_EMAIL` > OAuth from `wrangler login`.

### Docker / Remote Machine Login

```bash
# In a container, bind the callback port
docker run -p 8976:8976 your-image
npx wrangler login --callback-host=0.0.0.0

# Custom callback port
docker run -p 8976:9000 your-image
npx wrangler login --callback-host=0.0.0.0 --callback-port=9000
```

On remote machines without a browser, copy the URL printed by `wrangler login` and open it in a local browser.

---

## TypeScript Types (`wrangler types`)

```bash
# Generate types from wrangler.toml bindings
wrangler types

# Output to a custom path (must be .d.ts)
wrangler types ./src/env.d.ts

# Generate for a specific environment only
wrangler types --env production

# Check if types are up-to-date (useful in CI)
wrangler types --check

# Multi-worker: include service binding types from another worker
wrangler types -c wrangler.toml -c ../other-worker/wrangler.toml
```

This generates an `Env` interface reflecting your KV namespaces, D1 databases, R2 buckets, secrets, and vars. With `--strict-vars`, plain string vars become literal/union types.

---

## Triggers (Experimental)

When using `versions upload` (instead of `deploy`), route/cron changes need a separate step:

```bash
# Apply route and cron trigger changes
wrangler triggers deploy

# Preview only
wrangler triggers deploy --dry-run
```

---

## Startup Performance Profiling

```bash
# Profile your Worker's startup
wrangler check startup

# Profile a specific bundle file
wrangler check startup --worker dist/index.js
```

The generated CPU profile can be imported into Chrome DevTools (Performance tab) or opened in VS Code. Note: this measures performance on YOUR machine, not on Cloudflare's infrastructure -- use it for relative comparisons.

When a deployment fails with a startup time error, Wrangler automatically generates a CPU profile.

---

## Shell Completions

```bash
# Bash
wrangler complete bash >> ~/.bashrc && source ~/.bashrc

# Zsh
wrangler complete zsh >> ~/.zshrc && source ~/.zshrc

# Fish
wrangler complete fish >> ~/.config/fish/config.fish && source ~/.config/fish/config.fish
```

---

## Global Flags (All Commands)

| Flag | Purpose |
|------|---------|
| `--config/-c <path>` | Wrangler config file (repeatable for multi-worker) |
| `--env/-e <name>` | Target environment |
| `--cwd <dir>` | Run as if started from this directory |
| `--env-file <path>` | Load .env file (repeatable; later overrides earlier) |
| `--help` | Show help |
| `--version` | Show wrangler version |

---

## Common Pitfalls

1. **`secret put` triggers a deployment.** If you need to set 5 secrets, use `secret bulk` to avoid 5 separate deployments.

2. **`--latest` defaults to true in dev.** Your local environment may use a newer runtime than production. Always set `compatibility_date` in `wrangler.toml` for reproducibility.

3. **`--from-dash` is a one-time snapshot.** After `wrangler init --from-dash`, changes in the Cloudflare dashboard will NOT sync back to your local project.

4. **Rollback is immediate and global.** It affects all routes/domains instantly. There is no gradual rollback -- use `versions deploy` with percentage splits for safer rollbacks.

5. **`--keep-vars` matters in CI.** Without it, `wrangler deploy` may overwrite variables set through the dashboard.

6. **Version commands need wrangler >= 3.40.0.** Before 3.73.0, you also need the `--x-versions` flag.

7. **Tail sampling.** High-traffic Workers will drop some log messages. Use `--sampling-rate` to control the rate yourself.

8. **`wrangler types --check` in CI.** Add this to your CI pipeline to catch stale type definitions before they cause runtime errors.
