# Vercel: Deployments, Builds & Environments
Based on Vercel documentation.

## Core Concepts

### Deployment Model
A **deployment** is the result of a successful build. Each deployment gets a unique URL. Vercel has three default environments:

| Environment | Trigger | CLI Command |
|-------------|---------|-------------|
| **Production** | Push/merge to production branch (usually `main`) | `vercel --prod` |
| **Preview** | Push to any non-production branch, or open a PR | `vercel` |
| **Development** | Local machine | `vercel dev` |

**Custom Environments** (Pro/Enterprise): Create additional targets like `staging` or `qa` with their own env vars and domains. Pro gets 1 custom env per project, Enterprise gets 12.

### Deployment Methods
1. **Git push** -- most common. Connect GitHub/GitLab/Bitbucket/Azure DevOps. Each commit triggers a build.
2. **Vercel CLI** -- `vercel` (preview) or `vercel --prod` (production).
3. **Deploy Hooks** -- HTTP POST to a unique URL triggers a deployment from a specific branch. No auth needed (URL is the secret).
4. **REST API** -- Upload files via SHA, then POST to create deployment. For custom/multi-tenant workflows.

### Generated URLs

| URL Type | Format | Use Case |
|----------|--------|----------|
| Commit URL | `<project>-<hash>-<scope>.vercel.app` | Permanent link to a specific commit's deployment |
| Branch URL | `<project>-git-<branch>-<scope>.vercel.app` | Always points to latest commit on branch |
| CLI URL | `<project>-<scope>.vercel.app` | Latest CLI deployment |

URLs are truncated if >63 characters before `.vercel.app`. Project names resembling domains get shortened for anti-phishing protection.

**Preview Deployment Suffix** (Pro add-on, Enterprise default): Replace `vercel.app` with a custom domain. Requires Vercel nameservers.

---

## Builds

### Build Process
Vercel auto-detects your framework and sets Build Command, Install Command, and Output Directory. Shallow clone (`git clone --depth=10`) is used by default.

### Build Configuration

```json
// vercel.json overrides for a specific deployment
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install",
  "framework": "nextjs"
}
```

Override via Dashboard: Project Settings > Build and Deployment.

**Skip build step** for static sites: Set Framework Preset to "Other", leave Build Command empty.

**Root Directory**: For monorepos, set the subdirectory containing your app. Code cannot access files outside this directory.

### Build Resources

| Machine Type | vCPUs | Memory | Disk |
|-------------|-------|--------|------|
| Standard | 4 | 8 GB | 23 GB |
| Enhanced | 8 | 16 GB | 56 GB |
| Turbo | 30 | 60 GB | 64 GB |

- Build timeout: **45 minutes** max.
- Build cache: up to **1 GB**, retained for 1 month.
- Turbo machines are default for new Pro projects.

### Build Concurrency
- Each plan has concurrent build slot limits. Queued builds on the same branch auto-cancel older ones and deploy only the latest.
- **Prioritize Production Builds**: Enable to jump production builds ahead of queued preview builds (default for projects created after Dec 2024).
- **On-Demand Concurrent Builds** (Pro/Enterprise): Skip the queue entirely. Configurable per-project or per-team.
- **Force build**: Use "Start Building Now" button in dashboard for individual queued deployments.

### Monorepo Optimization
- **Skip unaffected projects**: Vercel auto-detects if a project's files changed and skips deployment if not. Does not occupy build slots.
- **Ignored Build Step**: Custom script that cancels builds. Still counts toward concurrency limits.

---

## Environment Variables

### Basics
- Key-value pairs, encrypted at rest. Max **64 KB total** per deployment (all vars combined). Edge Functions/Middleware limited to **5 KB per variable**.
- Changes only apply to **new deployments** -- you must redeploy after changing env vars.
- Can be set at **project level** or **team level** (shared across all projects).

### Per-Environment Variables

```bash
# CLI: Add to specific environment
vercel env add DATABASE_URL production
vercel env add DATABASE_URL preview
vercel env add DATABASE_URL development

# Add to a custom environment
vercel env add MY_KEY staging

# Branch-specific preview variable (overrides default preview var)
vercel env add DATABASE_URL preview feature-branch

# Sensitive variable (value hidden after creation, production/preview only)
vercel env add API_SECRET production --sensitive

# Pull env vars locally
vercel env pull                          # development vars -> .env.local
vercel pull --environment=production     # production vars
vercel pull --environment=preview --git-branch=feature-branch

# List and audit
vercel env ls production
vercel env ls preview

# Remove
vercel env rm DATABASE_URL production

# Run command with specific env
vercel env run -e preview -- npm test
```

### Sensitive Environment Variables
- Values are non-readable once created (write-only).
- Only available in production and preview (not development).
- Team owners can enforce a policy requiring all new vars to be sensitive.

### System Environment Variables
Enable via Project Settings > Environment Variables > "Automatically expose System Environment Variables".

Key variables:

| Variable | Available At | Description |
|----------|-------------|-------------|
| `VERCEL_ENV` | Build + Runtime | `production`, `preview`, or `development` |
| `VERCEL_URL` | Build + Runtime | Deployment URL (no `https://` prefix) |
| `VERCEL_BRANCH_URL` | Build + Runtime | Git branch URL |
| `VERCEL_PROJECT_PRODUCTION_URL` | Build + Runtime | Shortest production domain (set even in preview) |
| `VERCEL_GIT_COMMIT_REF` | Build + Runtime | Git branch name |
| `VERCEL_GIT_COMMIT_SHA` | Build + Runtime | Git commit SHA |
| `VERCEL_GIT_PREVIOUS_SHA` | Build only | SHA of last successful deployment for branch |
| `VERCEL_DEPLOYMENT_ID` | Build + Runtime | Unique deployment ID (used by Skew Protection) |
| `VERCEL_REGION` | Runtime only | Region ID where function is running |

### Reserved Variable Names (Cannot Use)
`AWS_SECRET_KEY`, `AWS_EXECUTION_ENV`, `AWS_LAMBDA_*`, `NOW_REGION`, `TZ`, `LAMBDA_TASK_ROOT`, `LAMBDA_RUNTIME_DIR`.

### Private npm Packages
Set `NPM_TOKEN` or `NPM_RC` as environment variables for private registry auth.

---

## Git Integration

### Setup
Import a repo from the Vercel dashboard ("New Project"). Vercel auto-deploys on every push.

### Production Branch
Selected in order: `main` > `master` > Bitbucket production branch > repo default. Customizable in Project Settings > Environments > Production > Branch Tracking.

### PR Workflow
1. Push to non-production branch or open PR.
2. Vercel creates preview deployment, posts comment on PR with preview URL.
3. Merge to production branch triggers production deployment.

### GitHub-Specific Features
- **Auto job cancellation**: If a build is running when a new push arrives on the same branch, queued builds are canceled except the latest. Disable with `github.autoJobCancellation: false` in `vercel.json`.
- **Deployment status events**: `repository_dispatch` events (`vercel.deployment.ready`, `vercel.deployment.success`, `vercel.deployment.error`, etc.) trigger GitHub Actions.
- **Fork protection**: PRs from forks require authorization before deploying (protects env vars).
- **Silence bot comments**: Project Settings > Git > toggle off comments.

### GitHub Actions (for GHES or custom CI/CD)

```bash
# In your GitHub Action:
npm install --global vercel@latest
vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}
vercel build
vercel deploy --prebuilt
```

---

## Promoting & Rolling Back

### Production Deployment States
- **Staged**: Built for production but no domain auto-assigned (requires manual promote).
- **Promoted**: Has been manually promoted from staging.
- **Current**: Actively serving production traffic.

### Instant Rollback
Reassigns domains to a previous deployment **without rebuilding**. Takes effect within seconds.

```bash
# Roll back to previous deployment
vercel rollback

# Roll back to specific deployment (Pro/Enterprise)
vercel rollback <deployment-url>

# Check status
vercel rollback status
```

**Key behaviors after rollback:**
- Auto-assignment of production domains is turned off. New pushes to main will NOT go live.
- Environment variables are NOT updated -- uses the rolled-back deployment's original build.
- Cron jobs revert to the rolled-back deployment's state.
- To restore normal flow: `vercel promote <deployment-url>` or use "Undo Rollback" in dashboard.

**Eligible deployments**: Only those previously aliased to a production domain. Hobby plan: previous deployment only. Pro/Enterprise: any eligible deployment.

### Promote Preview to Production
Triggers a **complete rebuild** with production environment variables.

### Staged Production (No Auto-Assign)
1. Disable "Auto-assign Custom Production Domains" in Project Settings > Environments > Production > Branch Tracking.
2. Push to main -- builds but does not serve traffic.
3. Manually promote when ready: `vercel promote <deployment-url>`.

### Bisect (Find Bad Deployment)

```bash
# Interactive
vercel bisect --good <good-url> --bad <bad-url>

# Automated with test script (exit 0=good, non-zero=bad, 125=skip)
vercel bisect --good <good-url> --bad <bad-url> --run ./test.sh
```

---

## Rolling Releases (Pro/Enterprise)

Gradually shift traffic from old to new deployment through configurable stages.

### Configuration

```bash
vercel rolling-release configure --cfg '{
  "enabled": true,
  "advancementType": "automatic",
  "stages": [
    {"targetPercentage": 10, "duration": 5},
    {"targetPercentage": 50, "duration": 10},
    {"targetPercentage": 100}
  ]
}'
```

### Workflow

```bash
vercel deploy --prod                                    # Triggers rolling release
vercel rolling-release start --dpl <deployment-url>     # Begin traffic shift
vercel rolling-release fetch                            # Check status
vercel rolling-release approve --dpl <url> --currentStageIndex 0  # Manual advance
vercel rolling-release complete --dpl <url>             # Finalize at 100%
vercel rolling-release abort --dpl <url>                # Revert on errors
```

### How It Works
- Users are assigned to buckets via cookie (based on IP for consistency across incognito).
- A 0% stage serves no traffic by default but can be forced with `?vcrrForceCanary=true`.
- An active rolling release must be completed or aborted before starting a new one.

**Always enable Skew Protection with Rolling Releases** -- ensures each user's backend API calls match the deployment they loaded.

---

## Skew Protection

Prevents version skew between client and server during deployments. Uses deployment ID to route API requests to the matching backend version.

### Enable
Projects Settings > Advanced > Skew Protection (enabled by default for new projects using supported frameworks).

**Supported frameworks** (zero-config): Next.js 14.1.4+, SvelteKit 5.2.0+, Qwik 1.5.3+, Astro 9.0.0+ (with `skewProtection: true`).

### Manual Implementation (Other Frameworks)
Add `VERCEL_DEPLOYMENT_ID` to requests via one of:

```ts
// Option 1: Query string
const query = process.env.VERCEL_SKEW_PROTECTION_ENABLED === '1'
  ? `?dpl=${process.env.VERCEL_DEPLOYMENT_ID}`
  : '';
const res = await fetch(`/api/data${query}`);

// Option 2: Header
const headers = process.env.VERCEL_SKEW_PROTECTION_ENABLED === '1'
  ? { 'x-deployment-id': process.env.VERCEL_DEPLOYMENT_ID }
  : {};
const res = await fetch('/api/data', { headers });

// Option 3: Cookie (__vdpl)
```

### Custom Threshold
Set on a specific deployment to invalidate all older clients, forcing them to the fixed version.

---

## Deploy Hooks

Trigger deployments via HTTP POST without authentication (URL is the secret).

```bash
# Create in Project Settings > Git > Deploy Hooks
# Trigger:
curl -X POST https://api.vercel.com/v1/integrations/deploy/prj_.../tKybBxqhQs

# Without build cache:
curl -X POST "https://api.vercel.com/v1/integrations/deploy/prj_.../tKybBxqhQs?buildCache=false"
```

- Requires connected Git repository.
- Multiple requests for the same version cancel previous builds.
- Limits: 5 per project (Hobby/Pro), 10 per project (Enterprise).
- Treat the URL as a secret. Revoke and recreate if compromised.

---

## Build Logs

- Generated at build time, stored indefinitely, truncated at **4 MB**.
- Access via dashboard (Build Logs button) or append `/_logs` to any deployment URL.
- Click timestamps to link to specific lines (`#L6`) or ranges (`Shift+click` for `#L6-L9`).
- Export to external systems with **Log Drains**.
- `/_src` and `/_logs` paths require Vercel authentication by default.

---

## Common Pitfalls

1. **Env vars not applied**: Changes only take effect on new deployments. Always redeploy after updating env vars.
2. **Preview vs Production env vars**: Promoting a preview deployment to production triggers a rebuild with **production** env vars, not the preview ones used originally.
3. **Instant Rollback disables auto-deploy**: After rollback, pushes to main do NOT auto-promote. You must explicitly promote or undo the rollback.
4. **Instant Rollback uses stale config**: Rolled-back deployments use their original env vars and build config, not current settings.
5. **Branch-specific vars override all preview vars**: A branch-specific preview variable overrides the default preview variable of the same name. You do not need to duplicate all preview vars per branch.
6. **Build timeout**: 45 minutes max. Optimize with build caching and larger machines.
7. **Rolling releases without Skew Protection**: Users may see inconsistent client/server behavior. Always enable both together.
8. **Deploy Hook security**: The URL has no auth -- anyone with the URL can trigger deployments. Treat it like a password.
9. **Private Git submodules fail**: Only public HTTP submodules work. Use private npm packages instead for private repos.
10. **Edge Function env var limit**: 5 KB per variable (vs 64 KB for Node.js functions).

---

## Quick Reference: CLI Commands

```bash
# Deploy
vercel                          # Preview deployment
vercel --prod                   # Production deployment
vercel deploy --target=staging  # Custom environment

# Environment
vercel link                     # Link local dir to project
vercel env pull                 # Pull dev env vars to .env.local
vercel pull --environment=production  # Pull production vars
vercel env add KEY production   # Add env var
vercel env ls production        # List env vars
vercel env rm KEY production    # Remove env var

# Inspect & Debug
vercel list --prod              # List production deployments
vercel inspect <url>            # Deployment metadata
vercel inspect <url> --logs     # Build logs
vercel logs --environment production --level error --since 5m
vercel curl /api/health --deployment <url>

# Promote & Rollback
vercel promote <url>            # Promote to production
vercel promote status           # Check promotion progress
vercel rollback                 # Instant rollback to previous
vercel rollback <url>           # Rollback to specific deployment
vercel bisect --good <url> --bad <url>  # Find bad deployment

# Rolling Releases
vercel rolling-release configure --cfg '...'
vercel rolling-release start --dpl <url>
vercel rolling-release fetch
vercel rolling-release abort --dpl <url>
```
