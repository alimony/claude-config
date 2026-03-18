# Next.js: Deployment & Production
Based on Next.js documentation (App Router).

## Deployment Options Overview

| Option | Feature Support | Use Case |
|--------|----------------|----------|
| Node.js server (`next start`) | All | Full-featured apps |
| Docker container | All | Containerized infra, Kubernetes |
| Static export (`output: 'export'`) | Limited | Static hosting, CDNs, SPAs |
| Adapters | Platform-specific | Cloudflare, Netlify, AWS Amplify, etc. |

## Node.js Server

Standard deployment — build and start:

```json
{
  "scripts": {
    "build": "next build",
    "start": "next start"
  }
}
```

```bash
npm run build && npm run start
```

Supports all Next.js features. Use a reverse proxy (nginx) in front for security (malformed requests, rate limiting, payload limits).

## Standalone Output (Docker / Containers)

`output: 'standalone'` creates a self-contained folder with only the files needed to run, without installing all `node_modules`. Uses `@vercel/nft` to trace dependencies.

```js
// next.config.js
module.exports = {
  output: 'standalone',
}
```

After `next build`, the `.next/standalone` folder contains a minimal `server.js`. Copy static assets manually:

```bash
cp -r public .next/standalone/
cp -r .next/static .next/standalone/.next/
node .next/standalone/server.js
```

Set `PORT` and `HOSTNAME` env vars to control the listen address:

```bash
PORT=8080 HOSTNAME=0.0.0.0 node .next/standalone/server.js
```

### Dockerfile Pattern

```dockerfile
FROM node:22-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

### Monorepo Tracing

Set `outputFileTracingRoot` to include files outside the project directory:

```js
// packages/web-app/next.config.js
const path = require('path')
module.exports = {
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname, '../../'),
}
```

Include/exclude specific files in traces:

```js
module.exports = {
  outputFileTracingIncludes: {
    '/*': ['node_modules/sharp/**/*'],
    '/api/another': ['./necessary-folder/**/*'],
  },
  outputFileTracingExcludes: {
    '/api/hello': ['./un-necessary-folder/**/*'],
  },
}
```

## Static Export

Generates plain HTML/CSS/JS into an `out` folder. No Node.js server required.

```js
// next.config.js
module.exports = {
  output: 'export',
  // trailingSlash: true,    // /about -> /about/index.html
  // distDir: 'dist',        // change output dir from 'out'
}
```

Server Components run at build time (like traditional SSG). Client Components work normally. Route Handlers support GET only (rendered to static files at build).

### Image Optimization with Static Export

Use a custom image loader since the built-in optimizer requires a server:

```js
// next.config.js
module.exports = {
  output: 'export',
  images: { loader: 'custom', loaderFile: './my-loader.ts' },
}
```

```ts
// my-loader.ts
export default function cloudinaryLoader({ src, width, quality }: {
  src: string; width: number; quality?: number
}) {
  const params = ['f_auto', 'c_limit', `w_${width}`, `q_${quality || 'auto'}`]
  return `https://res.cloudinary.com/demo/image/upload/${params.join(',')}${src}`
}
```

### Nginx Config for Static Export

```nginx
server {
  listen 80;
  server_name acme.com;
  root /var/www/out;

  location / {
    try_files $uri $uri.html $uri/ =404;
  }
  error_page 404 /404.html;
  location = /404.html { internal; }
}
```

### Unsupported with Static Export

- Dynamic routes without `generateStaticParams()`
- Route Handlers that read the request
- Cookies, Headers, Rewrites, Redirects
- Middleware/Proxy
- ISR (Incremental Static Regeneration)
- Default image optimizer
- Draft Mode, Server Actions, Intercepting Routes

## Single-Page Application (SPA) Mode

Next.js supports strict SPAs with client-side rendering. Use `output: 'export'` for a static SPA with per-route HTML files (better than a single `index.html`).

### Data Fetching in SPAs

Hoist data fetching to a Server Component layout, pass the Promise (not awaited) to a context provider, and unwrap with `use()` in Client Components:

```tsx
// app/layout.tsx
import { UserProvider } from './user-provider'
import { getUser } from './user'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  let userPromise = getUser() // do NOT await
  return (
    <html lang="en">
      <body>
        <UserProvider userPromise={userPromise}>{children}</UserProvider>
      </body>
    </html>
  )
}
```

```tsx
// app/profile.tsx
'use client'
import { use } from 'react'
import { useUser } from './user-provider'

export function Profile() {
  const { userPromise } = useUser()
  const user = use(userPromise) // suspends until resolved
  return '...'
}
```

### Browser-Only Components

Disable SSR prerendering for components that need `window`/`document`:

```tsx
import dynamic from 'next/dynamic'
const ClientOnly = dynamic(() => import('./component'), { ssr: false })
```

### Shallow Routing

Use `window.history.pushState` / `replaceState` for URL state without full navigation — integrates with `usePathname` and `useSearchParams`.

## Production Checklist

### Automatic Optimizations (no config needed)

- Server Components (zero client JS by default)
- Automatic code-splitting per route
- Prefetching when `<Link>` enters viewport
- Static rendering at build time (when no dynamic APIs used)

### During Development

- Use `<Link>` for client-side navigation, layouts for shared UI
- Place `'use client'` boundaries as low in the tree as possible
- Wrap dynamic APIs (`cookies`, `searchParams`) in `<Suspense>`
- Fetch data in Server Components; use Route Handlers only from Client Components
- Use `next/image`, `next/font`, `next/script` for automatic optimization
- Add `app/global-error.tsx` and `app/global-not-found.tsx`

### Security

- Prefix client-exposed env vars with `NEXT_PUBLIC_` only when needed
- Use data tainting to prevent sensitive data reaching the client
- Add Content Security Policy headers
- Keep `.env.*` in `.gitignore`

### SEO & Metadata

- Use the Metadata API for titles, descriptions, OG images
- Generate `sitemap.xml` and `robots.txt` via file conventions
- Add `useReportWebVitals` for Core Web Vitals analytics

### Before Production

```bash
next build   # catch build errors
next start   # test in production mode locally
```

- Run Lighthouse in incognito
- Analyze bundles with `@next/bundle-analyzer`

## Self-Hosting Configuration

### Environment Variables

Server-only by default. Use `NEXT_PUBLIC_` prefix to inline into client bundle at build time. For runtime server env vars, use dynamic rendering:

```tsx
import { connection } from 'next/server'

export default async function Page() {
  await connection() // opts into dynamic rendering
  const value = process.env.MY_VALUE // read at runtime
}
```

### Caching & ISR

Works automatically on filesystem. For multi-instance deployments, use a custom cache handler:

```js
// next.config.js
module.exports = {
  cacheHandler: require.resolve('./cache-handler.js'),
  cacheMaxMemorySize: 0, // disable in-memory cache
}
```

```js
// cache-handler.js — replace Map with Redis/S3/etc.
const cache = new Map()
module.exports = class CacheHandler {
  async get(key) { return cache.get(key) }
  async set(key, data, ctx) {
    cache.set(key, { value: data, lastModified: Date.now(), tags: ctx.tags })
  }
  async revalidateTag(tags) {
    tags = [tags].flat()
    for (let [key, value] of cache) {
      if (value.tags.some((tag) => tags.includes(tag))) cache.delete(key)
    }
  }
}
```

### Streaming with Nginx

Disable proxy buffering for SSR streaming:

```js
// next.config.js
module.exports = {
  async headers() {
    return [{
      source: '/:path*{/}?',
      headers: [{ key: 'X-Accel-Buffering', value: 'no' }],
    }]
  },
}
```

### Multi-Server / Rolling Deployments

**Encryption key** — all instances must share the same key for Server Functions:

```bash
NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=<base64-encoded-32-byte-key> next build
```

**Deployment ID** — detects version skew during rolling deploys, triggers hard navigation on mismatch:

```js
module.exports = { deploymentId: process.env.DEPLOYMENT_VERSION }
```

**Build ID** — use a consistent ID across containers:

```js
module.exports = {
  generateBuildId: async () => process.env.GIT_HASH,
}
```

## CI Build Caching

Cache `.next/cache` between builds. Without it, every build starts cold.

### GitHub Actions

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ${{ github.workspace }}/.next/cache
    key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
    restore-keys: |
      ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
```

### GitLab CI

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .next/cache/
```

### CircleCI

```yaml
steps:
  - save_cache:
      key: dependency-cache-{{ checksum "yarn.lock" }}
      paths:
        - ./node_modules
        - ./.next/cache
```

### Other Providers

- **Vercel**: automatic, no config needed
- **Netlify**: use `@netlify/plugin-nextjs`
- **AWS CodeBuild**: add `.next/cache/**/*` to `cache.paths` in `buildspec.yml`
- **Bitbucket**: define `nextcache: .next/cache` in `definitions.caches`
- **Azure Pipelines**: use `Cache@2` task with key `next | $(Agent.OS) | yarn.lock`
- **Heroku**: add `"cacheDirectories": [".next/cache"]` to `package.json`

## Memory Optimization

### Strategies

1. **Reduce dependencies** — audit with `@next/bundle-analyzer`
2. **Webpack memory optimization**:
   ```js
   // next.config.js
   module.exports = { experimental: { webpackMemoryOptimizations: true } }
   ```
3. **Debug memory during build**:
   ```bash
   next build --experimental-debug-memory-usage
   ```
4. **Heap profiling**:
   ```bash
   node --heap-prof node_modules/next/dist/bin/next build
   ```
5. **Disable webpack cache** if memory-constrained (trades speed for memory):
   ```js
   webpack: (config, { dev }) => {
     if (config.cache && !dev) config.cache = Object.freeze({ type: 'memory' })
     return config
   }
   ```
6. **Skip TypeScript checking in build** (run separately in CI):
   ```js
   module.exports = { typescript: { ignoreBuildErrors: true } }
   ```
7. **Disable source maps**:
   ```js
   module.exports = {
     productionBrowserSourceMaps: false,
     experimental: { serverSourceMaps: false },
   }
   ```
8. **Disable entry preloading** (reduces initial memory, same eventual footprint):
   ```js
   module.exports = { experimental: { preloadEntriesOnStart: false } }
   ```

## Progressive Web App (PWA)

### 1. Web App Manifest

```ts
// app/manifest.ts
import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'My App',
    short_name: 'App',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#000000',
    icons: [
      { src: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
  }
}
```

### 2. Service Worker

Place `public/sw.js` to handle push events and notification clicks:

```js
// public/sw.js
self.addEventListener('push', function (event) {
  if (event.data) {
    const data = event.data.json()
    event.waitUntil(
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: data.icon || '/icon.png',
      })
    )
  }
})

self.addEventListener('notificationclick', function (event) {
  event.notification.close()
  event.waitUntil(clients.openWindow('/'))
})
```

### 3. Push Notifications

Use the `web-push` library with VAPID keys:

```bash
npm install -g web-push
web-push generate-vapid-keys
```

```env
NEXT_PUBLIC_VAPID_PUBLIC_KEY=your_public_key
VAPID_PRIVATE_KEY=your_private_key
```

Server Action to send notifications:

```ts
'use server'
import webpush from 'web-push'

webpush.setVapidDetails(
  'mailto:you@example.com',
  process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!,
  process.env.VAPID_PRIVATE_KEY!
)

export async function sendNotification(subscription: PushSubscription, message: string) {
  await webpush.sendNotification(
    subscription,
    JSON.stringify({ title: 'Notification', body: message, icon: '/icon.png' })
  )
}
```

### 4. Security Headers for PWA

```js
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
      {
        source: '/sw.js',
        headers: [
          { key: 'Content-Type', value: 'application/javascript; charset=utf-8' },
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'" },
        ],
      },
    ]
  },
}
```

### 5. Offline Support

Use [Serwist](https://github.com/serwist/serwist) for offline caching with Next.js. Requires webpack config.

## Public & Static Pages

### Cache Components with `'use cache'`

Mark shared data components as cacheable to keep pages prerenderable:

```tsx
async function ProductList() {
  'use cache'
  const products = await db.product.findMany()
  return <List items={products} />
}
```

### Partial Prerendering

Mix static and dynamic content on one page. Wrap dynamic parts in `<Suspense>`:

```tsx
import { Suspense } from 'react'

export default async function Page() {
  return (
    <>
      <Suspense fallback={<PromotionSkeleton />}>
        <PromotionContent />  {/* dynamic, streamed */}
      </Suspense>
      <Header />              {/* static */}
      <ProductList />         {/* cached */}
    </>
  )
}
```

Build output confirms partial prerendering:

```
Route (app)      Revalidate  Expire
┌ ◐ /products    15m         1y
◐  (Partial Prerender)  static HTML with dynamic server-streamed content
```

### CDN Behavior

- Dynamic APIs accessed: `Cache-Control: private` (not CDN-cacheable)
- Fully static/prerendered: `Cache-Control: public` (CDN-cacheable)
- Immutable assets (hashed filenames): `public, max-age=31536000, immutable`
- Use `assetPrefix` to serve static assets from a CDN domain

## Platform Adapters

For platforms that don't run standard Node.js, use adapters:

- Cloudflare Workers
- AWS Amplify
- Netlify
- Firebase App Hosting
- Deno Deploy
- Vercel (native support)

A Deployment Adapters API is in development for custom platform support.
