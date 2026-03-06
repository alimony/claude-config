# Vercel: Project Configuration & Platform
Based on Vercel documentation.

## Core Concepts

### Projects
A project represents a deployed application linked to a single Git repository. Each project has one production deployment and many preview deployments. Multiple projects can share one Git repo (monorepos). Projects group deployments, custom domains, and environment variables.

### Teams & Accounts
- **Hobby** -- free, single user, one login connection per Git provider
- **Pro** -- collaboration, team members, webhooks, advanced features, 14-day free trial
- **Enterprise** -- SAML SSO, advanced security, SLAs, function failover
- Teams are created from the dashboard or API. Team ID is auto-assigned and immutable
- Default team is used for API/CLI requests when no team is specified

### Regions
Vercel operates 126+ PoPs and 20 compute-capable regions. Serverless functions default to `iad1` (Washington, D.C.).

| Code | Location | Code | Location |
|------|----------|------|----------|
| arn1 | Stockholm | iad1 | Washington, D.C. |
| bom1 | Mumbai | icn1 | Seoul |
| cdg1 | Paris | kix1 | Osaka |
| cle1 | Cleveland | lhr1 | London |
| cpt1 | Cape Town | pdx1 | Portland |
| dub1 | Dublin | sfo1 | San Francisco |
| dxb1 | Dubai | sin1 | Singapore |
| fra1 | Frankfurt | syd1 | Sydney |
| gru1 | Sao Paulo | yul1 | Montreal |
| hkg1 | Hong Kong | hnd1 | Tokyo |

Deploy functions in the same region as your database for lowest latency. On outage, traffic auto-reroutes to the next closest region.

### Integrations
Two types available from the Vercel Marketplace:
- **Native integrations** -- two-way connection, billing through Vercel, no separate account needed
- **Connectable accounts** -- link an existing third-party account to your Vercel project

Install via dashboard, CLI (`vercel integration add`), or third-party site.

## Project Settings

Configure from dashboard: Team scope > Project > Settings. Many settings can also be set in `vercel.json`.

### Build & Development Settings

```json
// vercel.json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "installCommand": "pnpm install",
  "outputDirectory": "dist",
  "framework": "nextjs"
}
```

Key settings:
- **Framework preset** -- auto-detected, sets default build/output/dev commands
- **Build command** -- override the framework default
- **Output directory** -- where build output lives (e.g., `dist`, `.next`, `build`)
- **Install command** -- override package manager detection
- **Root directory** -- for monorepos, path to the project within the repo
- **Node.js version** -- set in project settings

### Ignored Build Step
Control when builds run per commit. Options:
- Automatic (every commit), production only, preview only
- Only if changes detected (or in a specific folder)
- Custom bash/node script (exit `1` = build, exit `0` = cancel)
- Nx: `npx nx-ignore <project-name>`

Cancelled builds still count toward deployment quotas.

### Environment Variables
Configured per environment (production, preview, development) from project settings. Supports:
- Shared environment variables (team-level, linked to projects)
- Sensitive environment variables (encrypted, write-only)

### Other Settings
- **Custom domains** -- add per project
- **Deployment protection** -- Vercel Auth, password protection
- **Functions** -- Node.js version, memory, timeout, region
- **Cron Jobs** -- enable/disable from settings, configure in code
- **Webhooks** -- per-project event listeners
- **Drains** -- send logs/traces to external services (Pro/Enterprise)
- **Security** -- attack challenge mode, Git fork protection, deployment retention
- **Skew protection** -- version consistency across deployments

## Package Managers

Vercel auto-detects from lock file. Falls back to npm if no lock file.

| Manager | Lock File | Versions |
|---------|-----------|----------|
| npm | `package-lock.json` | 8, 9, 10 |
| Yarn | `yarn.lock` | 1, 2, 3 |
| pnpm | `pnpm-lock.yaml` | 6, 7, 8, 9, 10 |
| Bun | `bun.lock` / `bun.lockb` | 1 |
| Vlt | `vlt-lock.json` | 0.x |

Version selection uses `lockfileVersion` in the lock file. Corepack is supported -- set `packageManager` in `package.json` to pin exact versions.

Override per-project in dashboard (Settings > General > Build & Development Settings) or per-deployment in `vercel.json`:
```json
{ "installCommand": "pnpm install" }
```

## REST API

Base URL: `https://api.vercel.com`

### Authentication
Use a Bearer token (create from dashboard or API):
```bash
curl https://api.vercel.com/v9/projects \
  -H "Authorization: Bearer $VERCEL_TOKEN"
```

### SDK (@vercel/sdk)
```ts
import { Vercel } from '@vercel/sdk';

const vercel = new Vercel({
  bearerToken: process.env.VERCEL_TOKEN,
});

// Create a team
const team = await vercel.teams.createTeam({
  slug: 'my-team',
  name: 'My Team',
});
```

Key SDK namespaces: `vercel.teams`, `vercel.projects`, `vercel.deployments`, `vercel.domains`, `vercel.envs`.

### Common API Patterns
```bash
# Create a team
curl -X POST https://api.vercel.com/v1/teams \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "team-slug", "name": "Team Name"}'

# Specify team context with ?teamId=
curl "https://api.vercel.com/v9/projects?teamId=team_xxx" \
  -H "Authorization: Bearer $VERCEL_TOKEN"
```

## Webhooks

Available on Pro and Enterprise. Up to 20 custom webhooks per team.

### Setup
1. Team Settings > Webhooks
2. Select events to listen to
3. Choose target projects (all or specific)
4. Enter public endpoint URL
5. Save the secret key for signature verification

### Securing Webhooks
Verify the `x-vercel-signature` header against your webhook secret. For integration webhooks, use the Integration Client Secret.

### Event Types

| Category | Events |
|----------|--------|
| Deployment | `deployment.created`, `.ready`, `.succeeded`, `.error`, `.canceled`, `.promoted`, `.rollback`, `.cleanup` |
| Project | `project.created`, `.removed`, `.renamed` |
| Project Domain | `project.domain-created`, `.domain-deleted`, `.domain-verified` |
| Project Env | `project.env-variable.created`, `.updated`, `.deleted` |
| Domain | `domain.created`, `.renewal`, `.dns-records-changed` |
| Integration | `integration-configuration.removed`, `.permission-upgraded` |
| Marketplace | `marketplace.invoice.created`, `.paid`, `.notpaid`, `.refunded` |
| Alerts | `alerts.triggered` |

### Payload Format
```json
{
  "id": "<eventId>",
  "type": "deployment.created",
  "createdAt": 1705318200000,
  "region": "sfo",
  "payload": {
    "team": { "id": "team_xxx" },
    "deployment": {
      "id": "dpl_xxx",
      "url": "https://example-abc123.vercel.app",
      "name": "my-project"
    },
    "target": "production",
    "project": { "id": "prj_xxx" }
  }
}
```

### Legacy Events (Deprecated)
- `deployment` -> use `deployment.created`
- `deployment-ready` -> use `deployment.succeeded`
- `deployment-prepared` -> use `deployment.ready`

## Production Checklist

Before launching, verify across these categories:

### Operational Excellence
- Environment variables set for all environments (production, preview)
- Build and deploy pipeline tested end-to-end
- Monitoring and alerting configured (Web Analytics, Speed Insights, Logs)
- Team roles and permissions properly assigned
- Deploy hooks and CI/CD integration verified

### Security
- Deployment protection enabled for preview deployments
- Sensitive env vars use encrypted storage
- Git fork protection enabled
- HTTPS enforced on all custom domains
- CSP headers and security headers configured
- API routes validate and sanitize input

### Reliability
- Custom domains configured with proper DNS
- Function regions aligned with database location
- Error handling in serverless functions (timeouts, retries)
- Skew protection enabled for zero-downtime deployments

### Performance
- Static assets cached appropriately
- Images optimized (use `next/image` or equivalent)
- Function cold starts minimized (right region, right size)
- Bundle size audited
- Edge functions used where latency-sensitive

### Cost Optimization
- Unused preview deployments cleaned up (deployment retention policy)
- Function memory and timeout tuned (not over-provisioned)
- Build caching enabled
- Ignored build step configured for monorepos to skip unaffected projects

## Common Pitfalls

- **Wrong region**: Functions default to `iad1`. If your database is in `eu-west-1`, set function region to `dub1` or `cdg1`
- **Lock file mismatch**: Committing wrong lock file (e.g., `package-lock.json` + `pnpm-lock.yaml`) causes unpredictable installs. Keep exactly one lock file
- **Override install command version**: Using `pnpm install` as override defaults to oldest available pnpm (v6). Use Corepack to pin versions instead
- **Cancelled builds count**: Builds cancelled via ignored build step still count toward deployment quotas
- **Webhook env var payloads**: Environment variable webhook events do NOT include actual values
- **Project events scope**: `project.created/removed/renamed` webhooks only fire when integration has access to all team projects
- **`deployment.succeeded` vs `.ready`**: `.succeeded` fires after all checks pass; `.ready` fires when the deployment is built. Use `.ready` if you registered deployment checks
