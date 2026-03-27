# Wrangler: Configuration
Based on Wrangler documentation from developers.cloudflare.com.

## File Format

Wrangler supports TOML (`wrangler.toml`) and JSON (`wrangler.jsonc` / `wrangler.json`). Cloudflare recommends JSON for new projects -- some newer features are JSON-only. This guide uses TOML examples since most existing projects use it.

## Minimum Viable Config

Three keys are required to deploy:

```toml
name = "my-worker"               # Alphanumeric + dashes, max 63 chars on workers.dev
main = "./src/index.ts"          # Entry point (optional for assets-only Workers)
compatibility_date = "2025-09-01" # Runtime version (yyyy-mm-dd)
```

---

## Core Structure

### Inheritable Keys (top-level, overridable per environment)

| Key | Type | Purpose |
|-----|------|---------|
| `name` | string | Worker name |
| `main` | string | Entry point |
| `compatibility_date` | string | Runtime version |
| `compatibility_flags` | string[] | Feature flags (e.g. `["nodejs_compat_v2"]`) |
| `account_id` | string | Cloudflare account ID |
| `workers_dev` | boolean | Deploy to `*.workers.dev` subdomain |
| `route` / `routes` | string/object[] | Custom domain routing |
| `logpush` | boolean | Enable Workers Trace Events |
| `minify` | boolean | Minify bundle |
| `no_bundle` | boolean | Skip bundling |
| `tsconfig` | string | Path to tsconfig.json |
| `upload_source_maps` | boolean | Upload source maps on deploy |
| `preview_urls` | boolean | Enable preview URLs |

### Non-Inheritable Keys (must be redefined per environment)

| Key | Purpose |
|-----|---------|
| `vars` | Environment variables |
| `define` | Build-time string substitutions |
| `kv_namespaces` | KV bindings |
| `r2_buckets` | R2 bindings |
| `d1_databases` | D1 bindings |
| `durable_objects` | Durable Object bindings |
| `services` | Service bindings |
| `queues` | Queue producer/consumer bindings |
| `workflows` | Workflow bindings |
| `hyperdrive` | Postgres connection bindings |
| `ai` | Workers AI binding |
| `secrets` | Secret declarations |
| `analytics_engine_datasets` | Analytics bindings |
| `send_email` | Email routing bindings |
| `browser` | Browser Rendering binding |
| `mtls_certificates` | mTLS certificate bindings |

### Top-Level Only (never inherited, never overridden)

| Key | Purpose |
|-----|---------|
| `keep_vars` | Preserve dashboard-set variables on deploy |
| `migrations` | Durable Object class migrations |
| `send_metrics` | Usage data reporting |
| `site` | **Deprecated** -- use Static Assets |

---

## Environments

Environments create separate Worker instances named `<worker-name>-<env-name>`.

### Basic Structure

```toml
name = "my-worker"
main = "./src/index.ts"
compatibility_date = "2025-09-01"

[vars]
ENVIRONMENT = "development"

[env.staging]
route = "staging.example.com/*"

[env.staging.vars]
ENVIRONMENT = "staging"

[env.production]
routes = ["example.com/foo/*", "example.com/bar/*"]

[env.production.vars]
ENVIRONMENT = "production"
```

### Deployment

```bash
npx wrangler deploy              # Deploys "my-worker" (top-level)
npx wrangler deploy --env staging    # Deploys "my-worker-staging"
npx wrangler deploy -e production    # Deploys "my-worker-production"

# Or use the environment variable (CLI flag takes precedence)
CLOUDFLARE_ENV=staging npx wrangler deploy
```

### Inheritance Rules

**Do this** -- redefine bindings in each environment:
```toml
name = "my-worker"

[[kv_namespaces]]
binding = "CACHE"
id = "dev-namespace-id"

[[env.production.kv_namespaces]]
binding = "CACHE"
id = "prod-namespace-id"
```

**Don't do this** -- assume bindings inherit:
```toml
name = "my-worker"

[[kv_namespaces]]
binding = "CACHE"
id = "dev-namespace-id"

[env.production]
# WRONG: CACHE binding is NOT inherited here
# Production will have NO KV bindings
```

Key rules:
- Inheritable keys (name, compatibility_date, etc.) flow down to environments automatically
- Non-inheritable keys (vars, all bindings) must be explicitly set in each environment
- Routes are non-inheritable -- each environment needs its own route config
- Secrets are non-inheritable and must be set per environment

### Workers.dev vs Custom Domains

```toml
name = "my-worker"
route = "example.com/*"       # Top-level uses custom domain

[env.staging]
workers_dev = true             # Staging uses workers.dev subdomain
# Deploys to: my-worker-staging.<subdomain>.workers.dev
```

### Service Bindings Across Environments

When binding to another Worker's environment, target the full deployed name:

```toml
# worker-b's config
[[services]]
binding = "WORKER_A"
service = "worker-a"           # Top-level targets worker-a

[[env.staging.services]]
binding = "WORKER_A"
service = "worker-a-staging"   # Staging targets worker-a-staging
```

### Environment Name Warning

SSL certificates are public record. Avoid sensitive information in environment names (e.g., don't use names like `acquisition-target-corp` or `migration-to-aws`).

---

## Routing

```toml
# Single route
route = "example.com/*"

# Multiple routes
routes = ["example.com/api/*", "example.com/app/*"]

# Route with zone
[[routes]]
pattern = "shop.example.com/*"
zone_name = "example.com"

# Custom domain (Cloudflare manages DNS)
[[routes]]
pattern = "shop.example.com"
custom_domain = true
```

---

## Bindings

### KV Namespaces

```toml
[[kv_namespaces]]
binding = "MY_KV"
id = "abc123"
preview_id = "def456"          # Required for `wrangler dev --remote`
```

Auto-provisioned (ID created on first deploy):
```toml
[[kv_namespaces]]
binding = "MY_KV"
```

### R2 Buckets

```toml
[[r2_buckets]]
binding = "BUCKET"
bucket_name = "my-bucket"
jurisdiction = "eu"            # Optional: jurisdictional restriction
preview_bucket_name = "dev-bucket"
```

### D1 Databases

```toml
[[d1_databases]]
binding = "DB"
database_name = "my-db"
database_id = "abc123"
preview_database_id = "def456"
migrations_dir = "migrations"
```

### Durable Objects

```toml
[durable_objects]
bindings = [
  { name = "COUNTER", class_name = "Counter" }
]

# External Durable Object (from another Worker)
[[durable_objects.bindings]]
name = "EXTERNAL_DO"
class_name = "ExternalClass"
script_name = "other-worker"
environment = "production"
```

Migrations (required when adding/renaming/deleting DO classes):
```toml
[[migrations]]
tag = "v1"
new_sqlite_classes = ["Counter"]

[[migrations]]
tag = "v2"
renamed_classes = [{ from = "Counter", to = "PageCounter" }]
deleted_classes = ["OldClass"]
```

### Service Bindings

```toml
[[services]]
binding = "AUTH"
service = "auth-worker"
entrypoint = "handleAuth"      # Optional named entrypoint
```

### Queues

```toml
[[queues.producers]]
binding = "QUEUE"
queue = "my-queue"
delivery_delay = 60            # Seconds before delivery

[[queues.consumers]]
queue = "my-queue"
max_batch_size = 10
max_batch_timeout = 30
max_retries = 10
dead_letter_queue = "my-queue-dlq"
max_concurrency = 5
```

### Other Bindings

```toml
# Hyperdrive (Postgres) -- requires compatibility_flags = ["nodejs_compat_v2"]
[[hyperdrive]]
binding = "DB"
id = "<HYPERDRIVE_CONFIG_ID>"

# Workers AI -- one per project, incurs charges even in local dev
[ai]
binding = "AI"
```

---

## Variables and Secrets

### Plain Variables (in config)

```toml
[vars]
API_HOST = "example.com"
MAX_RETRIES = "3"

# Structured values
[vars.SERVICE_CONFIG]
URL = "https://api.example.com"
ID = 123
```

**Do not put sensitive values in `vars`** -- use secrets instead.

### Secrets (local development)

Create `.dev.vars` or `.env` in project root (not both):

```
SECRET_KEY=my-secret-value
API_TOKEN=eyJhbGci...
```

Per-environment secrets use suffixed files:
- `.dev.vars.staging` / `.dev.vars.production`
- `.env.staging` / `.env.production`

`.env` file precedence (highest to lowest):
1. `.env.<env>.local`
2. `.env.local`
3. `.env.<env>`
4. `.env`

**Always add these to `.gitignore`:**
```
.dev.vars*
.env*
```

### Secrets (production)

```bash
npx wrangler secret put API_KEY
npx wrangler secret put API_KEY --env production
```

### Declaring Required Secrets

```toml
[secrets]
required = ["API_KEY", "DB_PASSWORD"]
```

This restricts loaded keys to only those listed and warns about missing ones.

### Controlling .env Loading

```bash
# Disable .env loading entirely
CLOUDFLARE_LOAD_DEV_VARS_FROM_DOT_ENV=false npx wrangler dev

# Include all process env vars in Worker
CLOUDFLARE_INCLUDE_PROCESS_ENV=true npx wrangler dev
```

---

## Static Assets

```toml
[assets]
directory = "./public"
binding = "ASSETS"                          # Optional: access in Worker code
html_handling = "auto-trailing-slash"       # Options: force-trailing-slash, drop-trailing-slash, none
not_found_handling = "404-page"             # Options: single-page-application, none

# Run Worker code first for these routes (assets as fallback)
run_worker_first = ["/api/*", "!/api/docs/*"]
```

---

## Build Configuration

```toml
[build]
command = "npm run build"
cwd = "build_cwd"
watch_dir = "build_watch_dir"    # String or array of directories

no_bundle = false                # Skip Wrangler's bundling
find_additional_modules = true   # Auto-discover modules
base_dir = "src"                 # Base directory for module resolution
preserve_file_names = false      # false = content hash prefix on filenames
minify = false
keep_names = true                # Preserve function/class names (esbuild)

# Module rules
[[rules]]
type = "Text"                    # ESModule, CommonJS, CompiledWasm, Text, Data
globs = ["**/*.md"]
fallthrough = true               # Allow multiple rules per file type

# Module aliasing
[alias]
"node-fetch" = "./fetch-polyfill"
"fs" = "./fs-polyfill"
```

---

## Performance, Observability, Crons, and Local Dev

```toml
[limits]
cpu_ms = 300000                  # Max 5 minutes (Standard Usage Model only)
subrequests = 10000              # Free: 50, Paid: up to 10,000,000

[placement]
mode = "smart"                   # Auto-place near backend services
# OR: region = "aws:us-east-1" | host = "db.example.com:5432"

[observability]
enabled = true
head_sampling_rate = 0.1         # 0 to 1, default 1 (100%)

[triggers]
crons = ["*/5 * * * *", "0 0 * * *"]   # Empty array disables all crons

[dev]
ip = "localhost"                 # Bind address
port = 8787                      # Default port
local_protocol = "http"          # http or https
upstream_protocol = "https"
host = "example.com"             # Forward destination
```

---

## System Environment Variables

### Authentication

| Variable | Purpose |
|----------|---------|
| `CLOUDFLARE_ACCOUNT_ID` | Account ID |
| `CLOUDFLARE_API_TOKEN` | API token (recommended for CI/CD) |
| `CLOUDFLARE_API_KEY` | Legacy API key (use with EMAIL) |
| `CLOUDFLARE_EMAIL` | Account email (use with API_KEY) |
| `CLOUDFLARE_ACCESS_CLIENT_ID` | Access Service Token client ID |
| `CLOUDFLARE_ACCESS_CLIENT_SECRET` | Access Service Token secret |

### Runtime, Logging, and Local Dev

| Variable | Purpose | Values |
|----------|---------|--------|
| `CLOUDFLARE_ENV` | Select environment | Any env name; `--env` flag takes precedence |
| `CLOUDFLARE_API_BASE_URL` | Custom API endpoint | Default: `https://api.cloudflare.com/client/v4` |
| `WRANGLER_LOG` | Log level | `none`, `error`, `warn`, `info`, `log`, `debug` |
| `WRANGLER_LOG_PATH` | Log output path | File (`.log` suffix) or directory |
| `WRANGLER_SEND_METRICS` | Telemetry opt-out | `true` / `false` |
| `FORCE_COLOR` | Disable color | Set to `0` |
| `WRANGLER_HTTPS_KEY_PATH` | Custom HTTPS key for `wrangler dev` | File path |
| `WRANGLER_HTTPS_CERT_PATH` | Custom HTTPS cert for `wrangler dev` | File path |
| `DOCKER_HOST` | Container engine socket | Socket path |
| `CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_<BINDING>` | Local DB connection | Postgres URI |

### Deprecated Variables (do not use)

`CF_ACCOUNT_ID`, `CF_API_TOKEN`, `CF_API_KEY`, `CF_EMAIL`, `CF_API_BASE_URL` -- use `CLOUDFLARE_*` equivalents.

### Example `.env` for CI/CD

```
CLOUDFLARE_ACCOUNT_ID=abc123
CLOUDFLARE_API_TOKEN=your-api-token
WRANGLER_LOG=error
WRANGLER_SEND_METRICS=false
```

---

## Common Patterns

### Multi-Environment Production Setup

```toml
name = "my-app"
main = "./src/index.ts"
compatibility_date = "2025-09-01"
compatibility_flags = ["nodejs_compat_v2"]
workers_dev = true

[vars]
ENVIRONMENT = "development"

[[kv_namespaces]]
binding = "CACHE"
id = "dev-kv-id"

# --- Staging ---
[env.staging]
workers_dev = true

[env.staging.vars]
ENVIRONMENT = "staging"

[[env.staging.kv_namespaces]]
binding = "CACHE"
id = "staging-kv-id"

# --- Production ---
[env.production]
workers_dev = false
routes = ["api.example.com/*"]

[env.production.vars]
ENVIRONMENT = "production"

[[env.production.kv_namespaces]]
binding = "CACHE"
id = "prod-kv-id"
```

### Source of Truth Best Practices

- **Config file is authoritative**: Wrangler overwrites dashboard settings on deploy
- **Keep dashboard vars**: Set `keep_vars = true` if you manage some vars via dashboard
- **Disable route management**: Remove `route`/`routes` keys and set `workers_dev = false` if routes are managed elsewhere
- **Source maps in production**: Set `upload_source_maps = true` for better error traces
- **Auto-provisioning for prototypes**: Omit resource IDs for KV/D1/R2 during early development; Wrangler creates them on deploy

---

## Quick Troubleshooting

| Symptom | Likely Cause |
|---------|-------------|
| Bindings missing in staging/production | Non-inheritable keys not redefined in `[env.X]` |
| `wrangler dev --remote` fails on KV/D1 | Missing `preview_id` / `preview_database_id` |
| Secrets not loading locally | Using both `.dev.vars` and `.env` (pick one) |
| Env-specific secrets not loading | `.dev.vars.<env>` requires ALL secrets (no merge with base `.dev.vars`) |
| Dashboard vars disappearing on deploy | Missing `keep_vars = true` |
| Wrong environment deploying | `--env` flag overrides `CLOUDFLARE_ENV`; check both |
| `CF_*` variables not working | Deprecated; switch to `CLOUDFLARE_*` prefix |
