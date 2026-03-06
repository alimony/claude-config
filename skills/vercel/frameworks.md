# Vercel: Framework Support
Based on Vercel documentation.

## Core Concepts

### Framework Auto-Detection

Vercel automatically detects your framework from `package.json` dependencies and project structure. Most frameworks deploy with **zero configuration** -- no `vercel.json` needed.

### Build Output API

The Build Output API (`/.vercel/output`) is a file-system-based spec that framework authors use to integrate with Vercel's platform features (Functions, Routing, Caching). You can also use it directly without a framework.

### Platform Features Available to All Frameworks

- **Vercel Functions**: Auto-scaling serverless compute
- **Middleware**: Code that runs before requests, enabling personalization of static content
- **Preview Deployments**: Unique URL per pull request
- **Speed Insights / Web Analytics**: Core Web Vitals and visitor tracking
- **Skew Protection**: Version-locks client and server to prevent mismatches
- **Fluid Compute**: Active CPU billing, concurrency optimization, cold-start prevention (backend frameworks)

---

## Feature Support Matrix

| Feature | Next.js | SvelteKit | Nuxt | TanStack Start | Astro | Remix | React Router | Vite | Backend* |
|---|---|---|---|---|---|---|---|---|---|
| Static Assets | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| SSR | Y | Y | Y | Y | Y | Y | Y | plugin | N/A |
| Streaming SSR | Y | Y | -- | Y | Y | Y | Y | -- | N/A |
| ISR | Y | Y | Y | -- | Y | -- | -- | plugin | N/A |
| Image Optimization | Y | Y | Y | -- | Y | -- | -- | -- | N/A |
| Runtime Cache | Y | -- | -- | -- | -- | -- | -- | -- | N/A |
| OG Image Generation | Y | -- | Y | -- | -- | -- | -- | -- | N/A |
| Skew Protection | Y | Y | -- | -- | Y | -- | -- | -- | N/A |
| Framework Middleware | Y | -- | -- | Y | Y | -- | -- | -- | N/A |
| Output File Tracing | Y | Y | Y | Y | Y | -- | -- | -- | N/A |

*Backend = Express, Hono, Fastify, NestJS, etc. These run as single Vercel Functions with Fluid Compute.

---

## Full-Stack Frameworks

### Next.js

The native Vercel framework. Deepest integration, most features.

**Key Vercel enhancements over self-hosting:**
- ISR pages distributed globally via CDN and persisted to durable storage
- Image Optimization via `next/image` with zero config
- Font Optimization via `next/font` (self-hosted, zero layout shift)
- Middleware runs globally on Edge
- Draft Mode secured behind Vercel team authentication
- Runtime Cache (Next.js exclusive)
- Partial Prerendering (experimental) -- static shell + streamed dynamic holes

**ISR (App Router):**
```ts
// app/example/page.tsx
export default async function Page() {
  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 10 }, // seconds
  });
  // ...
}
```

**ISR (Pages Router):**
```ts
// pages/example/index.tsx
export async function getStaticProps() {
  return { props: { /* ... */ }, revalidate: 10 };
}
```

**Streaming with Suspense:**
```tsx
import { Suspense } from 'react';
export default function Page() {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <AsyncComponent />
    </Suspense>
  );
}
```

**Analytics setup:**
```tsx
// app/layout.tsx (App Router) or pages/_app.tsx (Pages Router)
import { Analytics } from '@vercel/analytics/next';
// Add <Analytics /> to your JSX
```

### SvelteKit

**Adapter setup (recommended over adapter-auto):**
```bash
npm i @sveltejs/adapter-vercel
```

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs20.x', // optional, default
    }),
  },
};
```

**Per-route config (e.g. Edge runtime):**
```js
// +page.server.js
export const config = { runtime: 'edge' };
```

**ISR:**
```js
// route/+page.server.js
export const config = {
  isr: {
    expiration: 60,
    bypassToken: 'SECRET_VALUE', // for on-demand revalidation
  },
};
```

**Image Optimization config:**
```js
// svelte.config.js
adapter({
  images: {
    sizes: [640, 828, 1200, 1920, 3840],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 300,
    domains: ['example-app.vercel.app'],
  },
})
```

**Gotchas:**
- `split: true` splits routes into separate Functions. Usually not needed -- only if hitting size limits or abnormal cold starts.
- Default Function region is `iad1` (Washington D.C.).
- SvelteKit does **not** support URL rewrites from middleware.
- Do **not** use `vercel.json` rewrites with SvelteKit -- SvelteKit cannot access the rewritten URL at runtime.
- Environment variables: use `'$env/static/private'` or `'$env/dynamic/private'` for system env vars (never expose to client).

### Nuxt

**Zero config** -- Nuxt auto-detects Vercel via its Nitro engine.

**Build commands:**
| Command | SSR | SSG | ISR |
|---|---|---|---|
| `nuxt build` (default) | Y | with routeRules | Y |
| `nuxt generate` | -- | Y | -- |

**routeRules (nuxt.config.ts) -- the central config mechanism:**
```ts
export default defineNuxtConfig({
  routeRules: {
    '/**': { isr: 60 },             // ISR: revalidate every 60s
    '/static': { isr: true },        // generate on demand, cache forever
    '/prerendered': { prerender: true }, // static at build time
    '/dynamic': { isr: false },       // always fresh (SSR)
    '/spa': { ssr: false },           // client-side rendering
    '/old/*': { redirect: '/new' },   // redirects
    '/api/*': { headers: { 'x-custom': 'value' } },
  },
});
```

**Use `isr` not `swr`** in routeRules to get Vercel's ISR cache.

**Server middleware** (`/server/middleware/`) -- runs on server, no return statement, modifies `event.context`.
**Route middleware** (`/middleware/`) -- runs in Vue, can redirect/block navigation. Add `.global` suffix for all routes.

**OG images:** Use `nuxt-og-image` package with `defineOgImageComponent`.

**Gotcha:** Legacy Nuxt 2 should only be deployed as static sites (`nuxt generate`). SSR with Nuxt 2 is not recommended on Vercel.

### Remix

**Recommended: Use the Vite plugin with Vercel Preset.**

```ts
// vite.config.ts
import { vitePlugin as remix } from '@remix-run/dev';
import { vercelPreset } from '@vercel/remix/vite';

export default defineConfig({
  plugins: [
    remix({ presets: [vercelPreset()] }),
  ],
});
```

**Import from `@vercel/remix`** instead of `@remix-run/node` for best streaming/Function support:
```tsx
import { defer } from '@vercel/remix';
```

**Cache-Control headers:**
```tsx
export const headers = () => ({
  'Cache-Control': 's-maxage=1, stale-while-revalidate=59',
});
```

**Custom entry.server** -- base off `@vercel/remix`'s `handleRequest`:
```tsx
import { handleRequest } from '@vercel/remix';
// ... export default using handleRequest
```

**Gotchas:**
- Custom `server` file is **not supported** with the Remix Vite plugin on Vercel.
- Vercel supplies a default `entry.server` for streaming. Only customize if needed.
- No ISR or Image Optimization support.

### TanStack Start

Uses **Nitro** for Vercel integration.

```ts
// vite.config.ts
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import { nitro } from 'nitro/vite';

export default defineConfig({
  plugins: [tanstackStart(), nitro(), viteReact()],
});
```

Uses Fluid Compute by default. Minimal Vercel-specific config needed.

### React Router (as framework)

**Install and configure the Vercel Preset:**
```bash
npm i @vercel/react-router
```

```ts
// react-router.config.ts
import { vercelPreset } from '@vercel/react-router/vite';

export default {
  ssr: true,
  presets: [vercelPreset()],
} satisfies Config;
```

The preset enables per-route function config, bundle splitting, and accurate deployment summaries.

**Cache-Control:**
```tsx
export function headers(_) {
  return { 'Cache-Control': 's-maxage=1, stale-while-revalidate=59' };
}
```

**Custom entry.server** -- use `handleRequest` from `@vercel/react-router/entry.server`.

**Custom server entrypoint** (e.g. with Hono for load context):
```ts
// vite.config.ts
build: {
  rollupOptions: isSsrBuild ? { input: './server/app.ts' } : undefined,
},
```

---

## Frontend / Static Frameworks

### Vite (standalone)

Deploys as a static site by default. For SSR or Functions, use community plugins.

**SPA deep-linking fix (`vercel.json`):**
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**Recommended plugins:**
- `vite-plugin-vercel` -- implements Build Output API (SSR, Functions, ISR, SSG)
- `vite-plugin-ssr` -- SSR, Functions, SSG

**Environment variables:** Prefix with `VITE_` to access Vercel system env vars (e.g. `VITE_VERCEL_ENV`).

```js
// vite.config.js
export default defineConfig(() => ({
  define: {
    __APP_ENV__: process.env.VITE_VERCEL_ENV,
  },
}));
```

**When using Vercel CLI**, set the port via env var:
```ts
// vite.config.ts
import vercel from 'vite-plugin-vercel';
export default defineConfig({
  server: { port: process.env.PORT as unknown as number },
  plugins: [vercel()],
});
```

### Other Frontend Frameworks (zero-config)

Angular, Gatsby, Hugo, Jekyll, Eleventy, Vue, VuePress, VitePress, Preact, Docusaurus, Ember, Gridsome, Hexo, Parcel, Stencil, Polymer, Zola, and many more. All deploy with auto-detected build settings.

---

## Backend Frameworks

All backend frameworks deploy as a **single Vercel Function** with **Fluid Compute** by default. They auto-scale based on traffic.

### Common Benefits
- Active CPU pricing (pay only for compute, not I/O wait)
- Instant Rollback, Vercel Firewall, Preview Deployments, Secure Compute
- Rolling releases for gradual rollout

### Entrypoint Detection (Express, Hono, Fastify, NestJS)

All expect one of these file locations:
```
app.{js,ts,mjs,cjs,mts,cts}
index.{js,ts,mjs,cjs,mts,cts}
server.{js,ts,mjs,cjs,mts,cts}
src/app.{js,ts,...}
src/index.{js,ts,...}
src/server.{js,ts,...}
```
NestJS also supports `src/main.{js,ts,...}`.

### Express

```ts
import express from 'express';
const app = express();
app.get('/', (req, res) => res.json({ message: 'Hello' }));
export default app; // or use app.listen(3000)
```

**Gotchas:**
- `express.static()` is **ignored**. Place static files in `public/` directory instead.
- Bundle must fit within 250MB.
- Express swallows errors that can leave Functions in undefined state. Implement robust error handling.

### Hono

```ts
import { Hono } from 'hono';
const app = new Hono();
app.get('/', (c) => c.json({ message: 'Hello' }));
export default app;
```

- Hono middleware (framework-level) works alongside Vercel Routing Middleware.
- `serveStatic()` is **ignored** -- use `public/` directory.
- Supports streaming via `stream()` helper.

### Fastify

```ts
import Fastify from 'fastify';
const fastify = Fastify({ logger: true });
fastify.get('/', async () => ({ hello: 'world' }));
fastify.listen({ port: 3000 });
```

Minimum CLI version: 48.6.0.

### NestJS

```ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();
```

Minimum CLI version: 48.4.0.

### Other Supported Backends

Elysia, FastAPI (Python), Flask (Python), H3, Koa, Nitro, xmcp -- all zero-config.

---

## Serverless Considerations for Backends

- **No WebSockets**: Functions have execution limits. Use a realtime data provider instead of subscribing to events.
- **Database Connections**: Use `attachDatabasePool` from `@vercel/functions` to manage connection pooling.
- **250MB bundle limit**: All Vercel Functions are limited to 250MB after bundling.

---

## Common Patterns

### Adding Web Analytics (any framework)

```bash
npm i @vercel/analytics
```

Then add the `<Analytics />` component (React frameworks) or `inject()` call (SvelteKit) to your root layout.

**SvelteKit example:**
```html
<!-- src/routes/+layout.svelte -->
<script>
  import { dev } from '$app/environment';
  import { inject } from '@vercel/analytics';
  inject({ mode: dev ? 'development' : 'production' });
</script>
```

### Static Assets

For backend frameworks, place files in `public/` -- they are served via CDN. Framework-specific static serving (e.g. `express.static()`, `serveStatic()`) is ignored on Vercel.

### Cache-Control Headers

Use `s-maxage` for CDN caching and `stale-while-revalidate` for background refresh:
```
Cache-Control: s-maxage=1, stale-while-revalidate=59
```

### Local Development

```bash
vercel dev    # runs your app locally with Vercel's runtime
```
