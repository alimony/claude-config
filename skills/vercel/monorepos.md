# Vercel: Monorepos & Microfrontends
Based on Vercel documentation.

## Monorepo Setup

### How It Works

Each directory in a monorepo becomes a separate Vercel project. One Git repo can connect to multiple Vercel projects. Every commit triggers deployments for all connected projects (unless skipped).

### Setup via Dashboard

1. **Add New > Project** for each directory you want to deploy.
2. Set the **Root Directory** to the app's subdirectory (e.g., `apps/web`).
3. Configure build settings and deploy.
4. Repeat for each app in the monorepo.

### Setup via CLI

```bash
# From monorepo root (not a subdirectory)
vercel link --repo
```

Subsequent commands like `vercel dev` use the selected project. Run `vercel link` again to switch projects.

### Skipping Unaffected Projects

Vercel automatically skips builds for unchanged projects. A project is "changed" if:
- Its source code changed
- Any internal workspace dependency changed
- A lockfile change impacts its dependencies

**Requirements:**
- GitHub repos only
- Must use npm/yarn/pnpm/bun workspaces
- All packages need unique `name` in `package.json`
- Inter-package dependencies must be explicit in `package.json`

This does **not** consume concurrent build slots (unlike Ignored Build Step).

### Ignored Build Step

Alternative to skipping: cancel builds via the Ignored Build Step project setting. Canceled builds **do** count toward deployment and concurrent build limits.

### Related Projects

Link up to 3 projects in the same repo so preview deployments automatically reference each other (e.g., frontend references correct backend preview URL).

```json
// apps/frontend/vercel.json
{
  "relatedProjects": ["prj_123"]
}
```

Access related project URLs in code:

```ts
import { withRelatedProject } from '@vercel/related-projects';

const apiHost = withRelatedProject({
  projectName: 'my-api-project',
  defaultHost: process.env.API_HOST,
});
```

### Sharing Source Files

Enable **"Include source files outside of the Root Directory in the Build Step"** in Root Directory settings to access shared packages. Enabled by default for projects created after Aug 27, 2020.

### Hosting Multiple Projects Under One Domain

Create a proxy project with `vercel.json` rewrites:

```json
{
  "rewrites": [
    { "source": "/docs/:path*", "destination": "https://docs-project.vercel.app/docs/:path*" },
    { "source": "/:path*", "destination": "https://main-project.vercel.app/:path*" }
  ]
}
```

---

## Turborepo on Vercel

### Quick Setup

Vercel auto-detects Turborepo. `turbo` is globally available during builds — no need to add it as a dependency.

| Setting | Value |
|---------|-------|
| Build Command | `turbo run build` (or just `turbo build` with v1.8+) |
| Root Directory | App location, e.g. `apps/web` |
| Ignored Build Step | `npx turbo-ignore --fallback=HEAD^1` |
| Output Directory | Framework default |

### Environment Variables in turbo.json

**Critical:** Declare env vars that affect build output, or you risk shipping wrong cached builds.

```json
{
  "$schema": "https://turborepo.com/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "env": ["SOME_ENV_VAR"],
      "outputs": ["dist/**"]
    },
    "web#build": {
      "dependsOn": ["^build"],
      "env": ["SOME_OTHER_ENV_VAR"],
      "outputs": [".next/**", "!.next/cache/**"]
    }
  },
  "globalEnv": ["GITHUB_TOKEN"],
  "globalDependencies": ["tsconfig.json"]
}
```

**Tip:** Only declare env vars in app-specific tasks where they are used for higher cache hit rates.

### Build Outputs by Framework

```json
"outputs": [
  ".next/**", "!.next/cache/**",   // Next.js
  ".svelte-kit/**", ".vercel/**",  // SvelteKit
  ".vercel/output/**",             // Build Output API
  "dist/**"                        // Other frameworks
]
```

### Troubleshooting Cache Misses

View the **Run Summary** in the Vercel Dashboard (Turborepo 1.9+): Deployments > select deployment > Run Summary button. Shows task execution times, cache status, and hash inputs with diffs from previous builds.

### Limitation

Next.js with Skew Protection always causes Turborepo cache misses (env var changes per deployment). Use Turborepo 2.4.1+ to avoid missing asset issues.

---

## Remote Caching

### What It Is

Shares Turborepo build artifacts (compiled outputs, test results, logs) across team members and CI/CD. Free on all plans.

| Plan | Upload Limit | Request Limit |
|------|-------------|---------------|
| Hobby | 100 GB/mo | 100/min |
| Pro | 1 TB/mo | 10,000/min |
| Enterprise | 4 TB/mo | 10,000/min |

Artifacts auto-expire after 7 days.

### Enable for Turborepo

```bash
# Authenticate (from monorepo root)
npx turbo login
# For SSO teams:
npx turbo login --sso-team=<team-slug>

# Link to remote cache
npx turbo link
```

Remote caching is **automatic during Vercel builds** — no extra config needed.

### Use from External CI/CD

Set two environment variables:
- `TURBO_TOKEN` — a Vercel Access Token
- `TURBO_TEAM` — your Vercel team slug

### Enable for Nx

Install `@vercel/remote-nx` and configure `nx.json`:

```json
{
  "tasksRunnerOptions": {
    "default": {
      "runner": "@vercel/remote-nx",
      "options": {
        "cacheableOperations": ["build", "test", "lint", "e2e"],
        "cacheDirectory": "/tmp/nx-cache"
      }
    }
  }
}
```

Set `NX_VERCEL_REMOTE_CACHE_TOKEN` and `NX_VERCEL_REMOTE_CACHE_TEAM` env vars (auto-set on Vercel).

### Nx Environment Variable Pitfall

Env vars not defined in a deployment may use stale cached values. Always define all env vars in every deployment. Use `runtimeCacheInputs` to bust cache on env var changes:

```json
"runtimeCacheInputs": ["echo $MY_VERCEL_ENV"]
```

---

## Microfrontends

### When to Use

- Large apps split across independent teams
- Incremental migration from legacy systems
- Need for independent deploy cycles per feature area

Consider simpler alternatives first: monorepos with Turborepo, feature flags, Turbopack.

### Architecture

- **Default app**: Owns `microfrontends.json`, handles routing, serves unmatched paths.
- **Child apps**: Serve specific path prefixes (e.g., `/docs`, `/blog`).
- All apps share a single domain. Routing happens at Vercel's network edge (no extra network hop).

### Setup

1. Create a **Microfrontends Group** in Vercel Dashboard (Settings > Microfrontends).
2. Add `microfrontends.json` to the **default app's root**:

```json
{
  "$schema": "https://openapi.vercel.sh/microfrontends.json",
  "applications": {
    "web": {
      "development": {
        "fallback": "your-production-domain.vercel.app"
      }
    },
    "docs": {
      "routing": [
        { "paths": ["/docs/:path*"] }
      ]
    }
  }
}
```

3. Install `@vercel/microfrontends` in **every** microfrontend app.
4. Configure framework integration:

**Next.js** — wrap `next.config.js` with `withMicrofrontends`:
```js
const { withMicrofrontends } = require('@vercel/microfrontends/next/config');
module.exports = withMicrofrontends(nextConfig);
```

**SvelteKit / Vite** — add the Vite plugin:
```ts
import { microfrontends } from '@vercel/microfrontends/experimental/vite';
export default defineConfig({ plugins: [microfrontends()] });
```

### Path Expressions

| Pattern | Meaning |
|---------|---------|
| `/path` | Exact match |
| `/:slug` | Single segment wildcard |
| `/prefix/:path*` | Zero or more trailing segments |
| `/prefix/:path+` | One or more trailing segments |
| `/:path(a\|b)` | Matches `/a` or `/b` |
| `/:path((?!a\|b).*)` | Any single segment except `/a` or `/b` |

Wildcards (`*`, `+`) must appear at the end. Overlapping paths across microfrontends are not allowed.

### Asset Prefix

`withMicrofrontends` auto-generates a hashed asset prefix (`/vc-ap-<hash>`) so JS/CSS/images route correctly. Override with:

```json
"your-app": {
  "assetPrefix": "marketing-assets",
  "routing": [...]
}
```

Next.js `public/` files must be manually moved under the asset prefix subdirectory.

### Flag-Controlled Routing

Route paths conditionally using feature flags (Next.js only):

```json
{
  "routing": [
    { "flag": "enable-new-dashboard", "paths": ["/new-dashboard"] }
  ]
}
```

Add middleware in the default app:

```ts
import { runMicrofrontendsMiddleware } from '@vercel/microfrontends/next/middleware';

export async function middleware(request) {
  const response = await runMicrofrontendsMiddleware({
    request,
    flagValues: {
      'enable-new-dashboard': async () => someFeatureFlagCheck(),
    },
  });
  if (response) return response;
}

export const config = {
  matcher: ['/.well-known/vercel/microfrontends/client-config', '/new-dashboard'],
};
```

### Local Development

Use the `@vercel/microfrontends` proxy to run one app locally while routing other paths to production.

**With Turborepo (recommended):** Proxy starts automatically with `turbo dev`.

**Without Turborepo:**
```json
{
  "scripts": {
    "dev": "next dev --port $(microfrontends port)",
    "proxy": "microfrontends proxy --local-apps web"
  }
}
```

Visit the proxy URL (default `localhost:3024`), not the app's direct port.

**Polyrepo setup:** Pull config with `vercel microfrontends pull`, or set `VC_MICROFRONTENDS_CONFIG=/path/to/microfrontends.json`.

**Debug locally:** Set `MFE_DEBUG=1` to see routing decisions in console.

### Cross-Zone Navigation (Next.js)

Add `PrefetchCrossZoneLinks` to your layout, then use the optimized Link:

```tsx
import { Link } from '@vercel/microfrontends/next/client';
<Link href="/docs">Docs</Link>
```

### Testing Utilities

```ts
import { validateRouting, validateMiddlewareConfig } from '@vercel/microfrontends/next/testing';

// Validate path routing
validateRouting('./microfrontends.json', {
  marketing: ['/', '/products'],
  docs: ['/docs', '/docs/api'],
});

// Validate middleware config
validateMiddlewareConfig(config, './microfrontends.json');
```

### Debug Headers (Production)

Set cookie `VERCEL_MFE_DEBUG=1` or enable via Vercel Toolbar. Response headers:
- `x-vercel-mfe-app` — which microfrontend handled the request
- `x-vercel-mfe-matched-path` — matched path pattern
- `x-vercel-mfe-response-reason` — internal routing reason

### Fallback Environment

When a microfrontend isn't built for a preview commit, Vercel falls back to:
- **Same Environment** — another deployment in the same environment
- **Production** — the current production deployment
- **Custom Environment** — a named custom environment

Configure in Settings > Microfrontends > Fallback Environment.

---

## Multi-Tenant Apps (Vercel for Platforms)

Serve multiple customers from one codebase with per-tenant domains/subdomains.

### Architecture

- Root domain: `acme.com`
- Tenant subdomains: `tenant1.acme.com`, `tenant2.acme.com`
- Custom domains: `tenantcustomdomain.com`

Vercel handles SSL, DNS routing, and CDN automatically.

### Features

- Unlimited custom domains and subdomains
- Automatic SSL issuance and renewal
- Domain management via REST API or SDK
- Next.js middleware for subdomain routing

### Getting Started

Use the [Platforms Starter Kit](https://vercel.com/templates/next.js/platforms-starter-kit) which includes middleware-based subdomain routing, tenant-specific content, Redis storage, and an admin interface.

### Key Pattern: Middleware Routing

```ts
// middleware.ts — route by subdomain
import { NextRequest, NextResponse } from 'next/server';

export function middleware(req: NextRequest) {
  const hostname = req.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];

  // Rewrite to tenant-specific path
  return NextResponse.rewrite(new URL(`/${subdomain}${req.nextUrl.pathname}`, req.url));
}
```
