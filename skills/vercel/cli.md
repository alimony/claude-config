# Vercel: CLI Reference
Based on Vercel documentation.

## Installation & Authentication

```bash
npm i vercel        # or pnpm/yarn/bun
vercel --version    # verify installation
vercel login        # interactive login
vercel login --github  # login via GitHub
vercel whoami       # check current user
vercel switch       # switch team scope
```

**CI/CD authentication:** Create a token at vercel.com/account/tokens, then pass `--token <TOKEN>` to any command. Never use `vercel login` in CI.

## Core Concepts

### Project Linking

Running `vercel` in a directory for the first time prompts you to link to an existing project or create a new one. This creates a `.vercel/` directory containing org and project IDs.

```bash
vercel link                      # interactive linking
vercel link --yes --project foo  # non-interactive
vercel link --repo               # link all projects in a monorepo (requires Git integration)
```

- `.vercel/` is auto-added to `.gitignore`
- To unlink: delete the `.vercel/` directory
- Framework is auto-detected with default build/dev/output settings

**Project resolution precedence (highest to lowest):**
1. `--project` flag (name or ID)
2. `VERCEL_PROJECT_ID` env var
3. `.vercel/project.json` from linking

For CI/CD, set `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` as env vars to skip interactive linking.

### Deployment Workflow

```
vercel pull          # fetch env vars + project settings
vercel build         # local build (optional)
vercel deploy        # preview deployment
vercel deploy --prod # production deployment
```

**stdout is always the deployment URL** -- pipe it for scripting:
```bash
vercel deploy > deployment-url.txt
```

## Global Options

| Flag | Short | Description |
|------|-------|-------------|
| `--cwd <path>` | | Working directory |
| `--debug` | `-d` | Verbose output |
| `--token <token>` | `-t` | Auth token (for CI/CD) |
| `--scope <slug>` | `-S` | Execute under a specific scope |
| `--team <slug-or-id>` | `-T` | Specify team |
| `--project <name-or-id>` | | Specify project |
| `--local-config <path>` | `-A` | Path to vercel.json |
| `--global-config <path>` | `-Q` | Path to global config dir |
| `--no-color` | | Disable color/emoji (respects NO_COLOR=1) |
| `--help` | `-h` | Show help |
| `--version` | `-v` | Show version |
| `--yes` | | Skip confirmation prompts (use defaults) |

## Key Commands

### deploy (default command)

`vercel` and `vercel deploy` are equivalent. Deploys from source or prebuilt output.

```bash
vercel                              # preview deploy
vercel --prod                       # production deploy
vercel --prod --skip-domain         # prod deploy without domain assignment (staged)
vercel deploy --prebuilt            # deploy pre-built .vercel/output
vercel deploy --prebuilt --archive=tgz  # compress before upload (for large projects)
```

| Flag | Short | Description |
|------|-------|-------------|
| `--prod` | | Deploy to production |
| `--skip-domain` | | Skip auto domain assignment (use with `--prod`) |
| `--prebuilt` | | Deploy from `.vercel/output` |
| `--archive=tgz` | | Compress before upload |
| `--force` | `-f` | Skip build cache |
| `--with-cache` | | Retain build cache when using `--force` |
| `--no-wait` | | Exit without waiting for deploy to finish |
| `--env KEY=val` | `-e` | Runtime env var |
| `--build-env KEY=val` | `-b` | Build-time env var |
| `--logs` | `-l` | Print build logs |
| `--meta KEY=val` | `-m` | Add deployment metadata |
| `--target <env>` | | Target environment (production/preview/custom) |
| `--regions <region>` | | Function region |
| `--public` | | Make source public at `/_src` |
| `--yes` | | Skip setup prompts |

**Prebuilt caveats:** `--prebuilt` disables Skew Protection and System Environment Variables at build time. Do not use if your framework depends on these.

### dev

Replicate the Vercel deployment environment locally. **Not recommended if your framework's dev command already supports all needed features** (e.g., `next dev`).

```bash
vercel dev                # start local dev server
vercel dev --listen 5005  # custom port
vercel dev --yes          # skip setup prompts
```

### build

Build locally; output goes to `.vercel/output` (Build Output API format). Run `vercel pull` first to get latest env vars and settings.

```bash
vercel build              # preview build
vercel build --prod       # production build
vercel build --target=staging  # custom environment build
vercel build --output ./custom-dir  # custom output directory
```

### pull

Fetch env vars and project settings to `.vercel/` for offline use with `vercel build` and `vercel dev`. **Only needed if using those commands.**

```bash
vercel pull                            # development env vars
vercel pull --environment=preview      # preview env vars
vercel pull --environment=production   # production env vars
vercel pull --environment=preview --git-branch=feature-x
```

### env

Manage environment variables on the Vercel platform.

```bash
# List
vercel env ls [environment] [gitbranch]

# Add
vercel env add NAME [environment] [gitbranch]
vercel env add SECRET production --sensitive   # mark as sensitive
cat file.txt | vercel env add NAME production  # value from stdin

# Update
vercel env update NAME [environment] [gitbranch]

# Remove
vercel env rm NAME [environment] --yes

# Pull to .env file
vercel env pull                          # -> .env.local (development)
vercel env pull .env.preview --environment=preview
vercel env pull --environment=preview --git-branch=feature-x

# Run command with env vars (no file written)
vercel env run -- next dev
vercel env run -e production -- next build
vercel env run -e preview --git-branch feature-x -- npm test
```

Key flags: `--sensitive`, `--force` (overwrite without prompt), `--yes`.

**`vercel env pull` vs `vercel pull`:** Use `vercel pull` when working with `vercel build`/`vercel dev` (stores in `.vercel/`). Use `vercel env pull` to export to a `.env` file for framework dev commands.

### logs

View request logs or stream live runtime logs.

```bash
vercel logs                                  # last 24h for linked project
vercel logs --follow                         # stream live logs (up to 5 min)
vercel logs --follow --deployment dpl_xxx    # stream specific deployment
vercel logs --level error --since 1h         # filter by level and time
vercel logs --status-code 5xx --environment production
vercel logs --json | jq '.message'           # JSON output for piping
vercel logs --query "timeout" --expand       # full-text search, expanded
```

| Flag | Short | Description |
|------|-------|-------------|
| `--follow` | `-f` | Stream live logs |
| `--deployment` | `-d` | Filter by deployment |
| `--level` | | error, warning, info, fatal |
| `--status-code` | | e.g. 500, 4xx, 5xx |
| `--source` | | serverless, edge-function, edge-middleware, static |
| `--environment` | | production, preview |
| `--since` / `--until` | | Time range (1h, 30m, ISO 8601) |
| `--branch` | `-b` | Filter by git branch |
| `--query` | `-q` | Full-text search |
| `--json` | `-j` | JSON Lines output |
| `--expand` | `-x` | Show full log messages |
| `--limit` | `-n` | Max entries (default 100) |

### inspect

Retrieve deployment info or build logs.

```bash
vercel inspect <deployment-id-or-url>
vercel inspect <url> --logs             # show build logs
vercel inspect <url> --logs --wait      # wait for build, then show logs
vercel inspect <url> --wait --timeout=5m
```

### promote & rollback

**promote:** Assign production domains to an existing deployment.
```bash
vercel promote <deployment-id-or-url>          # promote to production
vercel promote status [project]                # check promotion status
vercel promote <url> --timeout=5m
```

**rollback:** Revert production to a previous deployment.
```bash
vercel rollback [deployment-id-or-url]         # rollback production
vercel rollback status [project]               # check rollback status
```

Hobby plan: can only rollback to the immediately previous production deployment.
To undo a rollback: use `vercel promote`.

### alias

Assign custom domains to deployments. Prefer `vercel promote` / `vercel rollback` for production domain management.

```bash
vercel alias set <deployment-url> <custom-domain>
vercel alias rm <custom-domain>
vercel alias ls [--limit 100]
```

### domains

Manage domains under the current scope.

```bash
vercel domains ls [--limit 100]
vercel domains inspect <domain>
vercel domains add <domain> [project] [--force]
vercel domains rm <domain> [--yes]
vercel domains buy <domain>
vercel domains move <domain> <scope-name>
vercel domains transfer-in <domain>
```

### bisect

Binary search through deployments to find when a bug was introduced (like `git bisect` but for deployments). Both good and bad deployments must be production deployments.

```bash
vercel bisect                                   # interactive
vercel bisect --good <url> --bad <url>          # specify endpoints
vercel bisect --good <url> --bad <url> --path /blog  # check specific path
vercel bisect --run ./test.sh                   # automated (exit 0=good, non-0=bad, 125=skip)
vercel bisect --open                            # auto-open URLs in browser
```

### blob

Interact with Vercel Blob storage. Authenticates via `BLOB_READ_WRITE_TOKEN` from env file or `--rw-token`.

```bash
vercel blob list [--prefix images/ --limit 100]
vercel blob put <file> [--pathname assets/hero.jpg] [--access private]
vercel blob get <url-or-pathname> [--output ./local.jpg]
vercel blob del <url-or-pathname>
vercel blob copy <from-url> <to-pathname>
vercel blob create-store <name> [--access public --region iad1]
vercel blob delete-store <store-id>
```

Key flags: `--add-random-suffix`, `--content-type`, `--cache-control-max-age`, `--allow-overwrite`, `--multipart` (default true).

### flags

Manage Vercel Flags (feature flags) from the CLI.

```bash
vercel flags list [--state active|archived]
vercel flags add <slug> [--kind boolean|string|number] [--description "..."]
vercel flags inspect <flag>
vercel flags enable <flag> --environment production
vercel flags disable <flag> -e production --variant off
vercel flags archive <flag> --yes
vercel flags rm <flag> --yes              # must be archived first

# SDK keys
vercel flags sdk-keys ls
vercel flags sdk-keys add --type server --environment production
vercel flags sdk-keys rm <hash-key>
```

## CI/CD Patterns

### Basic preview + production pipeline

```bash
# Install CLI
npm i -g vercel

# Pull env vars and settings (non-interactive)
vercel pull --yes --environment=preview --token=$VERCEL_TOKEN

# Deploy preview
DEPLOY_URL=$(vercel deploy --yes --token=$VERCEL_TOKEN)

# Run tests against preview
curl -f "$DEPLOY_URL/api/health"

# Promote to production
vercel deploy --prod --yes --token=$VERCEL_TOKEN
```

### Prebuilt deployment (keeps source private)

```bash
vercel pull --yes --environment=production --token=$VERCEL_TOKEN
vercel build --prod
vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
```

### Staged production deployment

```bash
# Deploy to production without assigning domains
vercel --prod --skip-domain --token=$VERCEL_TOKEN

# Run smoke tests against the deployment URL...

# When ready, promote
vercel promote $DEPLOY_URL --token=$VERCEL_TOKEN
```

### Custom domain alias in CI

```bash
vercel deploy > deployment-url.txt 2>error.txt
code=$?
if [ $code -eq 0 ]; then
    vercel alias $(cat deployment-url.txt) preview.example.com
else
    echo "Deploy failed: $(cat error.txt)"
    exit 1
fi
```

## Common Pitfalls

- **Forgetting `vercel pull` before `vercel build`:** Build will use stale or missing env vars and settings. Always pull first.
- **Using `--prebuilt` when you need Skew Protection:** Prebuilt deployments do not get a deployment ID at build time, so Skew Protection and System Environment Variables will not work.
- **`vercel env pull` vs `vercel pull`:** They write to different locations. `env pull` writes to `.env` files for framework dev commands. `pull` writes to `.vercel/` for `vercel build`/`vercel dev`.
- **Interactive prompts in CI:** Always use `--yes` and `--token` in non-interactive environments. Set `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` to skip linking prompts.
- **Alias URL resolution in bisect:** If using an alias URL for `--good`/`--bad`, it resolves to the current alias target, which may differ after a promote/rollback.
- **`--archive` can slow deploys:** While it avoids file count limits, it disables per-file caching. Only use for projects with thousands of files.
- **Hobby plan rollback limitation:** Can only roll back to the immediately previous production deployment, not arbitrary past deployments.
- **`--skip-domain` overrides project settings:** It overrides the "Auto-assign Custom Production Domains" setting regardless of dashboard configuration.
- **`--` separator for `env run`:** Required to separate Vercel flags from the command: `vercel env run -e preview -- npm test`.
