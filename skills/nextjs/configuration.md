# Next.js: Configuration
Based on Next.js documentation (App Router).

## next.config.js / next.config.ts

The config file lives at the project root (next to `package.json`). Supports `.js`, `.mjs`, `.ts`, and `.mts` extensions.

### File Format

**JavaScript (CommonJS):**
```js
// next.config.js
// @ts-check
/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
}
module.exports = nextConfig
```

**ESM:**
```js
// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {}
export default nextConfig
```

**TypeScript (recommended):**
```ts
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* config options here */
}
export default nextConfig
```

### Function and Async Config

Config can be a function receiving `phase` and `defaultConfig`. Useful for per-environment settings:

```js
const { PHASE_DEVELOPMENT_SERVER } = require('next/constants')

module.exports = (phase, { defaultConfig }) => {
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    return { /* dev-only config */ }
  }
  return { /* production config */ }
}
```

Async functions supported since v12.1.0 -- use `module.exports = async (phase) => { ... }`.

---

## Environment Variables

### .env Files

Next.js loads `.env*` files into `process.env` automatically. Files must be in the project root (not `/src`).

**Load order** (first match wins):
1. `process.env` (already set)
2. `.env.$(NODE_ENV).local`
3. `.env.local` (skipped when `NODE_ENV=test`)
4. `.env.$(NODE_ENV)`
5. `.env`

Supports multiline values and variable expansion with `$`:
```bash
# .env
TWITTER_USER=nextjs
TWITTER_URL=https://x.com/$TWITTER_USER
# Escape literal $: use \$
```

### NEXT_PUBLIC_ Prefix

Variables without prefix are **server-only**. To expose to the browser, prefix with `NEXT_PUBLIC_`:

```bash
# .env
DB_PASSWORD=secret          # server only
NEXT_PUBLIC_API_URL=https://api.example.com  # available in browser
```

`NEXT_PUBLIC_` values are **inlined at build time** -- they will not update after build. Dynamic lookups like `process.env[varName]` will not be inlined.

### Runtime Environment Variables

Server Components using dynamic APIs (`cookies()`, `headers()`, `connection()`) read `process.env` at runtime:

```tsx
import { connection } from 'next/server'

export default async function Page() {
  await connection()
  const value = process.env.MY_VALUE  // evaluated at runtime
  // ...
}
```

### Test Environment

`.env.test` is loaded when `NODE_ENV=test`. `.env.local` is NOT loaded during tests to ensure consistent results.

### Loading Outside Next.js Runtime

Use `@next/env` for ORMs, test runners, or scripts:

```ts
import { loadEnvConfig } from '@next/env'
loadEnvConfig(process.cwd())
```

---

## Key Configuration Options

### output

Controls build output format:

| Value | Description |
|-------|-------------|
| (default) | Standard Node.js server output |
| `'standalone'` | Creates self-contained folder with minimal `server.js` |
| `'export'` | Static HTML export (no server required) |

**Standalone** is ideal for Docker deployments -- copies only required files and `node_modules`:

```js
module.exports = { output: 'standalone' }
```

After `next build`, deploy `.next/standalone`. Copy static assets manually:
```bash
cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/
node .next/standalone/server.js
```

For monorepos, set `outputFileTracingRoot` to include files outside project directory:
```js
const path = require('path')
module.exports = {
  outputFileTracingRoot: path.join(__dirname, '../../'),
}
```

### images

Configure the `next/image` optimization API:

```js
module.exports = {
  images: {
    // Allow external images (required for remote sources)
    remotePatterns: [
      new URL('https://example.com/images/**'),
      // or object form:
      {
        protocol: 'https',
        hostname: '**.example.com',
        pathname: '/account123/**',
        search: '',
      },
    ],

    // Restrict local image paths
    localPatterns: [{ pathname: '/assets/images/**', search: '' }],

    // Custom image loader (for CDN providers)
    loader: 'custom',
    loaderFile: './my/image/loader.js',

    // Image sizes for srcset generation
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840], // default
    imageSizes: [32, 48, 64, 96, 128, 256, 384],                 // default

    // Allowed quality values (required in v16+)
    qualities: [75],  // default

    // Output formats
    formats: ['image/webp'],  // default; add 'image/avif' for AVIF

    // Cache TTL in seconds
    minimumCacheTTL: 14400,  // default: 4 hours

    // SVG handling (off by default for security)
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",

    // Disable all optimization
    unoptimized: true,
  },
}
```

### redirects

Async function returning redirect rules. Checked before the filesystem:

```js
module.exports = {
  async redirects() {
    return [
      {
        source: '/old-blog/:slug',
        destination: '/blog/:slug',
        permanent: true,   // 308 (permanent) vs 307 (temporary)
      },
    ]
  },
}
```

Path matching uses `path-to-regexp`: `:param` (single segment), `:param*` (zero+), `:param+` (one+), `:param?` (optional), `:param(\\d+)` (regex).

Supports `has`/`missing` conditions for header, cookie, query, or host matching:
```js
{
  source: '/:path*',
  has: [{ type: 'header', key: 'x-redirect-me' }],
  missing: [{ type: 'cookie', key: 'session' }],
  destination: '/login',
  permanent: false,
}
```

### rewrites

URL proxy -- serves content from destination while keeping the original URL. Same path matching and `has`/`missing` syntax as redirects. Can return an array or phased object:

```js
module.exports = {
  async rewrites() {
    return {
      beforeFiles: [],   // checked before pages/public files
      afterFiles: [],    // checked after pages but before dynamic routes
      fallback: [        // checked after all routes (ideal for migration)
        { source: '/:path*', destination: 'https://old-site.com/:path*' },
      ],
    }
  },
}
```

### headers

Add custom HTTP headers to responses:

```js
module.exports = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
        ],
      },
    ]
  },
}
```

Common security headers to set: `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`.

### basePath

Deploy under a sub-path. `next/link` and `next/router` automatically prepend it:

```js
module.exports = { basePath: '/docs' }
```

`/about` becomes `/docs/about`. Set at build time, cannot change without rebuild. Note: `next/image` `src` must include the basePath manually.

### assetPrefix

Serve static assets (`/_next/static/`) from a CDN:

```js
module.exports = {
  assetPrefix: isDev ? undefined : 'https://cdn.mydomain.com',
}
```

Only affects `/_next/static` files. Does not affect `/public` folder -- prefix those manually.

### trailingSlash

```js
module.exports = { trailingSlash: true }
```

When `true`, `/about` redirects to `/about/`. Default is `false` (opposite behavior). Exceptions: file URLs and `.well-known/` paths.

### serverActions

```js
module.exports = {
  experimental: {
    serverActions: {
      allowedOrigins: ['my-proxy.com', '*.my-proxy.com'],  // CSRF protection
      bodySizeLimit: '2mb',  // default: 1MB
    },
  },
}
```

### serverExternalPackages

Opt packages out of Server Components bundling to use native Node.js `require`:

```js
module.exports = {
  serverExternalPackages: ['@acme/ui'],
}
```

Many packages are auto-externalized: `@prisma/client`, `sharp`, `mongodb`, `pg`, `pino`, `canvas`, `bcrypt`, `puppeteer`, `playwright`, and more.

### transpilePackages

Transpile and bundle packages from `node_modules` or monorepo workspaces:

```js
module.exports = {
  transpilePackages: ['@acme/ui', 'lodash-es'],
}
```

### optimizePackageImports

Tree-shake barrel exports for faster builds. Many libraries are optimized by default (`lucide-react`, `date-fns`, `lodash-es`, `@mui/material`, `@heroicons/react/*`, `recharts`, `react-icons/*`, etc.):

```js
module.exports = {
  experimental: {
    optimizePackageImports: ['my-large-package'],
  },
}
```

### reactCompiler

Auto-optimize component rendering, reducing need for `useMemo`/`useCallback`:

```js
// Install: npm install -D babel-plugin-react-compiler
module.exports = { reactCompiler: true }
```

Opt-in mode with `compilationMode: 'annotation'` -- annotate components with `'use memo'` directive.

### cacheLife

Define custom cache profiles for `'use cache'` directive:

```js
module.exports = {
  cacheComponents: true,
  cacheLife: {
    blog: {
      stale: 3600,       // 1 hour client staleness
      revalidate: 900,   // 15 min server revalidation
      expire: 86400,     // 1 day max
    },
  },
}
```

Use in code: `cacheLife('blog')` inside a `'use cache'` function.

### cacheHandlers

Custom cache storage for `'use cache'` directives (Redis, Memcached, etc.). Handler must implement `get()`, `set()`, `refreshTags()`, `getExpiration()`, `updateTags()`:

```js
module.exports = {
  cacheHandlers: {
    default: require.resolve('./cache-handlers/default.js'),
    remote: require.resolve('./cache-handlers/redis.js'),
  },
}
```

### turbopack

Configure the Turbopack bundler (default in development):

```js
module.exports = {
  turbopack: {
    // Webpack loader compatibility
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
    // Module aliases
    resolveAlias: {
      underscore: 'lodash',
    },
    // File extensions to resolve
    resolveExtensions: ['.mdx', '.tsx', '.ts', '.jsx', '.js', '.mjs', '.json'],
  },
}
```

Built-in support for CSS, PostCSS, Sass, modern JS -- no loaders needed for those. Tested loaders: `@svgr/webpack`, `yaml-loader`, `raw-loader`, `sass-loader`, `babel-loader`, `graphql-tag/loader`.

### webpack

Custom webpack config (not covered by semver):

```js
module.exports = {
  webpack: (config, { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }) => {
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    })
    return config  // must return modified config
  },
}
```

The function runs three times: server (Node.js runtime), server (Edge runtime), and client. Use `isServer` and `nextRuntime` (`"edge"` | `"nodejs"` | `undefined`) to distinguish.

---

## TypeScript

### Automatic Setup

Create a `.ts`/`.tsx` file and run `next dev` -- Next.js auto-installs dependencies and creates `tsconfig.json`.

### Key Features

- **next.config.ts**: Full TypeScript support for config files
- **IDE Plugin**: Validates segment config, `'use client'` directive, hooks usage. Enable via "TypeScript: Select TypeScript Version" > "Use Workspace Version" in VS Code
- **Route-aware types**: `PageProps`, `LayoutProps`, `RouteContext` generated during dev/build
- **Typed routes**: Enable `typedRoutes: true` for compile-time link validation
- **Typed env**: Enable `experimental.typedEnv: true` for env variable IntelliSense
- **Incremental type checking**: Enable `incremental: true` in `tsconfig.json` for faster checks
- **next-env.d.ts**: Auto-generated type declarations (add to `.gitignore`)

### Custom tsconfig Path

```ts
// next.config.ts
const nextConfig: NextConfig = {
  typescript: {
    tsconfigPath: 'tsconfig.build.json',
  },
}
```

### Ignore Build Errors (not recommended)

```ts
const nextConfig: NextConfig = { typescript: { ignoreBuildErrors: true } }
```

### Type Generation Without Full Build

```bash
next typegen && tsc --noEmit  # CI type checking without full build
```

---

## ESLint

### Setup (Flat Config)

Next.js 16+ uses standard ESLint CLI (removed `next lint`).

```bash
npm i -D eslint eslint-config-next
```

```js
// eslint.config.mjs
import { defineConfig, globalIgnores } from 'eslint/config'
import nextVitals from 'eslint-config-next/core-web-vitals'

export default defineConfig([
  ...nextVitals,
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts']),
])
```

### Configurations

| Config | Description |
|--------|-------------|
| `eslint-config-next` | Base Next.js + React + React Hooks rules |
| `eslint-config-next/core-web-vitals` | Base + Core Web Vitals rules as errors |
| `eslint-config-next/typescript` | TypeScript-specific rules from `typescript-eslint` |

### With TypeScript and Prettier

```js
// eslint.config.mjs
import nextVitals from 'eslint-config-next/core-web-vitals'
import nextTs from 'eslint-config-next/typescript'
import prettier from 'eslint-config-prettier/flat'

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  prettier,
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts']),
])
```

### Customization

Disable rules: `{ rules: { '@next/next/no-img-element': 'off' } }`. Monorepo root: `{ settings: { next: { rootDir: 'packages/my-app/' } } }`.

---

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `next dev` | Start development server (HMR, error reporting) |
| `next build` | Create optimized production build |
| `next start` | Start production server (requires `next build` first) |
| `next info` | Print system info for bug reports |
| `next typegen` | Generate TypeScript route definitions |
| `next upgrade` | Upgrade Next.js to latest version |
| `next experimental-analyze` | Analyze bundle output with Turbopack |
| `next telemetry` | Enable/disable anonymous telemetry |

### next dev

```bash
next dev [directory] [options]
  -p, --port <port>       # Port (default: 3000, env: PORT)
  -H, --hostname <host>   # Hostname (default: 0.0.0.0)
  --turbopack             # Use Turbopack (default in v16+)
  --webpack               # Use Webpack instead of Turbopack
  --experimental-https    # Enable HTTPS with self-signed cert
```

### next build

```bash
next build [directory] [options]
  --turbopack             # Use Turbopack (default)
  --webpack               # Use Webpack
  -d, --debug             # Verbose output (shows rewrites, redirects, headers)
  --profile               # Enable React production profiling
  --no-lint               # Skip linting
  --debug-prerender       # Debug prerender errors
  --debug-build-paths=<p> # Build only specific routes (glob patterns)
```

Build output symbols: `○` Static (prerendered), `f` Dynamic (server-rendered on demand).

### next start

```bash
next start [directory] [options]
  -p, --port <port>             # Port (default: 3000)
  -H, --hostname <hostname>     # Hostname (default: 0.0.0.0)
  --keepAliveTimeout <ms>       # Keep-alive timeout for proxies
```

### create-next-app

```bash
npx create-next-app@latest [project-name] [options]
  --ts / --js             # TypeScript (default) or JavaScript
  --tailwind              # Include Tailwind CSS (default)
  --eslint / --biome      # Linter choice
  --app                   # App Router (default)
  --src-dir               # Use src/ directory
  --turbopack / --webpack # Bundler choice
  --import-alias <alias>  # Import alias (default: "@/*")
  --empty                 # Empty project
  --example <name|url>    # Bootstrap from example
  --use-npm/pnpm/yarn/bun # Package manager
  --skip-install          # Skip installing dependencies
  --yes                   # Use defaults for all prompts
```

---

## Quick Reference: All Config Options

| Option | Description |
|--------|-------------|
| `assetPrefix` | CDN prefix for static assets (`/_next/static/`) |
| `basePath` | Sub-path prefix for entire application |
| `cacheHandlers` | Custom cache storage for `'use cache'` directives |
| `cacheLife` | Cache profile definitions (stale, revalidate, expire) |
| `compress` | Enable gzip compression (default: true) |
| `crossOrigin` | crossOrigin attribute on script tags |
| `devIndicators` | Configure dev mode on-screen indicator |
| `distDir` | Custom build output directory (default: `.next`) |
| `env` | Build-time environment variables (legacy, prefer `.env` files) |
| `generateBuildId` | Custom build identifier |
| `headers()` | Custom HTTP response headers |
| `images` | Image optimization configuration |
| `logging` | Dev mode fetch logging configuration |
| `optimizePackageImports` | Tree-shake barrel exports |
| `output` | Build output mode: default, `'standalone'`, `'export'` |
| `pageExtensions` | Custom file extensions for pages |
| `poweredByHeader` | Disable `x-powered-by` header (default: true) |
| `productionBrowserSourceMaps` | Enable source maps in production |
| `reactCompiler` | Enable React Compiler for auto-memoization |
| `reactStrictMode` | Enable React Strict Mode |
| `redirects()` | URL redirect rules |
| `rewrites()` | URL rewrite/proxy rules |
| `sassOptions` | Sass compiler options |
| `serverActions` | Server Actions config (allowedOrigins, bodySizeLimit) |
| `serverExternalPackages` | Packages excluded from server bundling |
| `trailingSlash` | Enforce trailing slashes on URLs |
| `transpilePackages` | Transpile packages from node_modules |
| `turbopack` | Turbopack-specific config (rules, aliases, extensions) |
| `typescript` | TypeScript build config (ignoreBuildErrors, tsconfigPath) |
| `webpack()` | Custom webpack configuration function |

### Routing Priority Order

1. `headers` checked/applied
2. `redirects` checked/applied
3. Proxy middleware
4. `beforeFiles` rewrites
5. Static files (`public/`, `_next/static/`, non-dynamic pages)
6. `afterFiles` rewrites
7. `fallback` rewrites (before 404)
