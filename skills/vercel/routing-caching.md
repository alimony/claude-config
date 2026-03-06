# Vercel: Routing, Middleware, Caching & CDN
Based on Vercel documentation.

## CDN Architecture

Vercel's CDN is a globally distributed, framework-aware network (126+ PoPs, 51 countries, 20+ compute regions). Every deployment includes it automatically.

### Request Flow (in order)

1. **Ingress** -- Request hits nearest PoP, routes to nearest Vercel region over private network
2. **Firewall** -- DDoS mitigation, WAF rules, bot management (blocked requests never reach routing)
3. **Routing** -- Redirects, rewrites, headers evaluated before any cache check
4. **Traffic Management** -- Skew protection, rolling releases, microfrontends
5. **Caching** -- CDN cache (regional), then ISR cache (durable, single region), then runtime cache (data inside functions)
6. **Compute** -- Vercel Functions run only if no cache has the content

### Cache Layers (checked in order)

| Layer | What it stores | Where | Durability |
|-------|---------------|-------|------------|
| **CDN cache** | Full HTTP responses (pages, API, static) | Every region, near users | Evicted by TTL or low access |
| **ISR cache** | Pre-rendered pages | Single function region | Up to 31 days, survives deploys |
| **Runtime cache** | Data fetched inside functions (fetch results, DB queries) | Per region | Ephemeral, LRU eviction |
| **Image cache** | Optimized/transformed images | CDN regions | Up to 31 days |

**Request collapsing**: When multiple visitors request the same uncached path simultaneously, Vercel collapses them into one function invocation per region.

---

## Routing

### Routing Order

Requests flow through routing layers in this fixed order:

1. Firewall redirects (emergency, highest priority)
2. Bulk redirects (CSV/JSON uploaded rules)
3. **Project-level routing rules** (dashboard/API, no deploy needed)
4. **Deployment-level routes** (vercel.json, next.config.js, middleware)

### Redirects

Define in `vercel.json` or framework config. Max 2,048 rules, 4,096 chars per source/destination.

```json
// vercel.json
{
  "redirects": [
    { "source": "/old", "destination": "/new", "permanent": true },
    {
      "source": "/:path((?!uk/).*)",
      "has": [{ "type": "header", "key": "x-vercel-ip-country", "value": "GB" }],
      "destination": "/uk/:path*",
      "permanent": false
    }
  ]
}
```

**Status codes**: `307` (temporary, preserves method), `308` (permanent, preserves method), `301`/`302` (may change method to GET). Prefer 307/308 for APIs.

**Next.js**: Use `next.config.js` `redirects()` instead of `vercel.json`.

### Rewrites

Rewrites map a public URL to a different destination without changing the browser URL.

```json
// vercel.json -- internal rewrite
{ "rewrites": [{ "source": "/blog/:slug", "destination": "/posts/:slug" }] }

// External rewrite (reverse proxy)
{ "rewrites": [{ "source": "/api/:path*", "destination": "https://api.example.com/:path*" }] }
```

**Caching external rewrites** -- not cached by default. Enable with:

```json
{
  "headers": [{
    "source": "/api/:path*",
    "headers": [
      { "key": "x-vercel-enable-rewrite-caching", "value": "1" },
      { "key": "CDN-Cache-Control", "value": "max-age=60" }
    ]
  }]
}
```

### Path Matching

- Exact: `/blog`
- Parameters: `/blog/:slug`, `/api/:path*` (wildcard)
- Regex: `/((?!api|_next/static|favicon.ico).*)`
- Named groups: `/products/(?<category>[a-z]+)/(?<id>\\d+)`

### Conditional Matching (`has`/`missing`)

Match on headers, cookies, query params, or host:

```json
{
  "has": [{ "type": "header", "key": "x-vercel-ip-country", "value": "GB" }]
}
```

### Custom Headers

```json
// vercel.json
{
  "headers": [{
    "source": "/api/:path*",
    "headers": [{ "key": "X-Custom", "value": "value" }]
  }]
}
```

### Project-Level Routing Rules

Configured from dashboard/API without deploying. Support redirects, rewrites, status codes, header modification. Run after bulk redirects, before deployment routes. Cannot run middleware.

---

## Routing Middleware

Middleware executes code **before** a request is processed, running globally before the cache. File: `middleware.ts` (or `.js`) at project root (same level as `package.json`).

### Basic Setup

```ts
// middleware.ts
export default function middleware(request: Request) {
  const url = new URL(request.url);
  if (url.pathname === '/old-page') {
    return new Response(null, { status: 302, headers: { Location: '/new-page' } });
  }
  return new Response('Hello from Middleware!');
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
  runtime: 'nodejs', // or 'edge' (default)
};
```

### Config Properties

| Property | Type | Description |
|----------|------|-------------|
| `matcher` | `string \| string[]` | Paths that trigger middleware (preferred over conditionals) |
| `runtime` | `'edge' \| 'nodejs'` | Default: `edge`. For Bun, set `bunVersion` in vercel.json + `runtime: 'nodejs'` |

### Signature

```ts
export default function middleware(request: Request, context: RequestContext) { ... }
```

- `request` -- Standard Web API `Request` (or `NextRequest` in Next.js)
- `context` -- Contains `waitUntil(promise)` to keep function running after response

### Helper Methods (any framework via `@vercel/functions`)

```ts
import { geolocation, ipAddress, rewrite, next } from '@vercel/functions';

// Geolocation
const { country, city, latitude, longitude, region } = geolocation(request);

// IP address
const ip = ipAddress(request);

// Rewrite
return rewrite(new URL('/about-2', request.url));

// Continue chain with modified headers
return next({ headers: { 'x-custom': 'value' } });
```

**Next.js** uses `NextResponse.rewrite()`, `NextResponse.redirect()`, `NextResponse.next()`, and `request.geo` / `request.ip` instead.

### Limits

| Limit | Value |
|-------|-------|
| Max URL length | 14 KB |
| Max request body | 4 MB |
| Max request headers | 64 headers, 16 KB total |

---

## Cache-Control Headers

### Header Priority (highest to lowest)

1. **`Vercel-CDN-Cache-Control`** -- Controls only Vercel's cache. Stripped from response to client.
2. **`CDN-Cache-Control`** -- Controls Vercel + other CDNs. Returned to client.
3. **`Cache-Control`** -- Standard. Used by Vercel, other CDNs, and browser. `s-maxage` stripped before sending to client.

Function response headers override `vercel.json`/`next.config.js` headers for the same route.

### Key Directives

```
Cache-Control: s-maxage=60                              # CDN caches 60s
Cache-Control: s-maxage=1, stale-while-revalidate=59    # Serve stale, revalidate in background
Cache-Control: max-age=604800, stale-if-error=86400     # Serve stale on origin error
Cache-Control: private, max-age=0                       # No CDN caching (per-user content)
Cache-Control: max-age=31536000, immutable              # Hashed static assets
```

### Recommended Settings

| Content | Header | Notes |
|---------|--------|-------|
| Server-rendered (same for all) | `max-age=0, s-maxage=86400` | CDN caches, browser always fresh |
| Semi-static (blogs, products) | `max-age=120, s-maxage=86400` | Short browser cache reduces edge requests |
| Per-user / personalized | `private, max-age=0` | Prevents CDN caching |
| Hashed static assets | `max-age=31536000, immutable` | Frameworks set this automatically |

### Layered Example

```ts
// Different TTLs per layer
return new Response('data', {
  headers: {
    'Cache-Control': 'max-age=10',              // Browser: 10s
    'CDN-Cache-Control': 'max-age=60',          // Other CDNs: 60s
    'Vercel-CDN-Cache-Control': 'max-age=3600', // Vercel: 1hr
  },
});
```

### x-vercel-cache Response Header Values

| Value | Meaning |
|-------|---------|
| `MISS` | Not cached, fetched from origin |
| `HIT` | Served from cache |
| `STALE` | Served stale, revalidating in background |
| `PRERENDER` | Served from static storage (e.g., ISR fallback) |
| `REVALIDATED` | Served from origin after cache deletion (foreground revalidation) |

---

## Incremental Static Regeneration (ISR)

ISR combines static speed with dynamic flexibility: serve cached pages, regenerate in background.

### Framework Setup

| Framework | How to enable |
|-----------|---------------|
| **Next.js App Router** | `export const revalidate = 60` in route segment |
| **Next.js Pages Router** | `return { props: {...}, revalidate: 60 }` from `getStaticProps` |
| **SvelteKit** | `export const config = { isr: { expiration: 60 } }` |
| **Nuxt** | `routeRules: { '/path': { isr: 60 } }` in nuxt.config |

### On-Demand Revalidation

**Next.js App Router**:
```ts
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache';
export async function GET(request: Request) {
  revalidatePath('/blog-posts');
  // or: revalidateTag('blog');
  return Response.json({ revalidated: true });
}
```

**SvelteKit/Nuxt**: Send request with `x-prerender-revalidate: <BYPASS_TOKEN>` header.

### ISR Behavior

- **Durable storage**: Persists 31 days (or until revalidated) in function region
- **Survives deployments**: Cached pages persist across deploys, instant rollbacks
- **300ms global purge**: Revalidation propagates to all CDN regions
- **Request collapsing**: Multiple concurrent misses = one function invocation
- **Failure handling**: On revalidation failure, stale content served with 30s retry TTL

---

## Cache Tags & Purging

### Adding Tags

```ts
// Via response header
headers: { 'Vercel-Cache-Tag': 'product-123,products' }

// Via @vercel/functions
import { addCacheTag } from '@vercel/functions';
addCacheTag('product-123');

// Via Next.js
import { cacheTag } from 'next/cache';
cacheTag('product-123');
```

### Purging Methods

| Method | Use |
|--------|-----|
| `invalidateByTag()` from `@vercel/functions` | Marks stale, background revalidation (recommended) |
| `dangerouslyDeleteByTag()` | Deletes, foreground revalidation (risk of stampede) |
| `revalidateTag()` / `revalidatePath()` (Next.js) | Framework-native invalidation |
| Vercel CLI: `vercel cache invalidate --tag X` | CLI-based purging |
| REST API: `/invalidate-by-tag` | Programmatic purging |
| Dashboard: Settings > Caches | Manual purging (use `*` for entire project) |

**Tag limits**: 256 chars/tag, 128 tags/response, case-sensitive, no commas.

Purging by tag purges all cache layers (CDN, Runtime, Data) together.

---

## Runtime Cache

Regional, ephemeral cache for data inside Vercel Functions. Item size limit: 2MB.

### Any Framework (`@vercel/functions`)

```ts
import { getCache } from '@vercel/functions';

export default {
  async fetch(request) {
    const cache = getCache();
    const value = await cache.get('key');
    if (value) return Response.json(value);

    const data = await fetch('https://api.example.com/data').then(r => r.json());
    await cache.set('key', data, { ttl: 3600, tags: ['my-tag'] });
    return Response.json(data);
  },
};
```

### Next.js 16+ (`use cache: remote`)

```ts
import { cacheLife, cacheTag } from 'next/cache';

async function getData() {
  'use cache: remote'
  cacheTag('my-data')
  cacheLife({ expire: 3600 })
  return fetch('https://api.example.com/data').then(r => r.json());
}
```

Requires `cacheComponents: true` in `next.config.ts`.

### Next.js 14-15 (Data Cache via `fetch`)

```ts
const res = await fetch('https://api.example.com/blog', {
  cache: 'force-cache',
  next: { revalidate: 3600, tags: ['blog'] },
});
```

---

## Vercel Request Headers

| Header | Value |
|--------|-------|
| `x-forwarded-for` / `x-real-ip` | Client IP address |
| `x-vercel-ip-country` | ISO 3166-1 country code (e.g., `US`, `GB`) |
| `x-vercel-ip-country-region` | ISO 3166-2 region (e.g., `CA` for California) |
| `x-vercel-ip-city` | City name (RFC3986-encoded) |
| `x-vercel-ip-continent` | Continent code (`NA`, `EU`, `AS`, etc.) |
| `x-vercel-ip-latitude` | Latitude (e.g., `37.7749`) |
| `x-vercel-ip-longitude` | Longitude (e.g., `-122.4194`) |
| `x-vercel-ip-timezone` | IANA timezone (e.g., `America/Chicago`) |
| `x-vercel-ip-postal-code` | Postal/ZIP code |
| `x-vercel-deployment-url` | Unique deployment URL (`*.vercel.app`) |
| `x-vercel-id` | Region chain and function execution region |

---

## Image Optimization

Vercel transforms images on-demand (resize, compress, convert to WebP/AVIF), caches results on CDN.

### Next.js Setup

```tsx
import Image from 'next/image';
<Image src="/hero.jpg" alt="Hero" width={1920} height={1080} />
```

Configure remote images in `next.config.ts`:

```ts
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'example.com', pathname: '/images/**' },
    ],
  },
};
```

### URL Format

- Next.js: `/_next/image?url={src}&w={width}&q={quality}`
- Other frameworks: `/_vercel/image?url={src}&w={width}&q={quality}`

### Cache Behavior

- Local images: cached up to 31 days, invalidated by content hash change
- Remote images: TTL from upstream `Cache-Control` or `minimumCacheTTL` (default 3600s)
- Image cache persists across deployments
- Purge via `invalidateBySrcImage()` or dashboard

### When NOT to Optimize

- Icons/thumbnails under 10KB
- Animated GIFs
- SVGs
- Frequently changing URLs with tokens

---

## Custom Error Pages

Replace Vercel's default 5xx error pages with branded static pages.

```html
<!-- public/500.html -->
<!doctype html>
<html>
<body>
  <h1>Something went wrong</h1>
  <p>Request ID: ::vercel:REQUEST_ID::</p>
  <p>Error: ::vercel:ERROR_CODE::</p>
</body>
</html>
```

- Must be static files (no SSR)
- `500.html` is the fallback for all 5xx errors
- Add specific pages (e.g., `504.html`) for targeted messaging
- Tokens `::vercel:REQUEST_ID::` and `::vercel:ERROR_CODE::` are replaced at serve time

---

## Common Pitfalls

1. **Middleware runs on every request by default** -- Always set `matcher` to exclude static files (`_next/static`, `_next/image`, `favicon.ico`).
2. **`Cache-Control` without `s-maxage` does nothing for CDN** -- Use `s-maxage` for server-side caching.
3. **`set-cookie` prevents caching** -- Any response with `set-cookie` header is not cached by CDN.
4. **ISR vs Cache-Control** -- ISR provides request collapsing, durable storage, 300ms global purge, instant rollbacks. Plain `Cache-Control` does not.
5. **External rewrites are not cached by default** -- Must add `x-vercel-enable-rewrite-caching: 1` header.
6. **`Vary` header multiplies cache entries** -- Each unique combination of Vary'd header values creates a separate cache entry. Use selectively.
7. **Cache tags are case-sensitive** -- `product` and `Product` are different tags.
8. **`dangerouslyDeleteByTag` can cause cache stampede** -- Prefer `invalidateByTag` (stale-while-revalidate pattern).
9. **Runtime cache is regional and ephemeral** -- Not a replacement for durable storage. Subject to LRU eviction.
10. **`proxy-revalidate` is not supported** on Vercel's CDN.
