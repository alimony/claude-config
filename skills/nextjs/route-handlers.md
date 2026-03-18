# Next.js: Route Handlers & API
Based on Next.js documentation (App Router).

Generated from nextjs.org/docs on 2026-03-18. Next.js 16.1.7.

## Route Handlers (`route.ts`)

Define custom API endpoints using Web Request/Response APIs. Place `route.ts` (or `.js`) files inside the `app` directory.

```ts
// app/api/route.ts
export async function GET(request: Request) {
  return Response.json({ message: 'Hello World' })
}
```

**Key rules:**
- Cannot coexist with `page.ts` at the same route segment (`app/page.ts` + `app/route.ts` = conflict)
- Can be nested anywhere in `app` (`app/api/users/route.ts` is fine alongside `app/page.ts`)
- Do not participate in layouts or client-side navigation
- Each `route.ts` takes over all HTTP verbs for that route

### Supported HTTP Methods

`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`. Unsupported methods return 405.

If `OPTIONS` is not defined, Next.js auto-implements it with the correct `Allow` header.

```ts
// app/api/route.ts
export async function GET(request: Request) {}
export async function POST(request: Request) {}
export async function PUT(request: Request) {}
export async function PATCH(request: Request) {}
export async function DELETE(request: Request) {}
export async function HEAD(request: Request) {}
export async function OPTIONS(request: Request) {}
```

### Parameters

**`request`** (optional) -- a `NextRequest` (extends Web `Request`):

```ts
import type { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const url = request.nextUrl
  const searchParams = request.nextUrl.searchParams
  const query = searchParams.get('query') // /api/search?query=hello -> "hello"
}
```

**`context`** (optional) -- contains `params` (a Promise) for dynamic routes:

```ts
// app/dashboard/[team]/route.ts
export async function GET(
  request: Request,
  { params }: { params: Promise<{ team: string }> }
) {
  const { team } = await params
  return Response.json({ team })
}
```

| Route                            | URL            | `params`                            |
|----------------------------------|----------------|-------------------------------------|
| `app/dashboard/[team]/route.ts`  | `/dashboard/1` | `Promise<{ team: '1' }>`           |
| `app/shop/[tag]/[item]/route.ts` | `/shop/1/2`    | `Promise<{ tag: '1', item: '2' }>` |
| `app/blog/[...slug]/route.ts`    | `/blog/1/2`    | `Promise<{ slug: ['1', '2'] }>`    |

**`RouteContext` helper** -- globally available after type generation (`next dev`/`next build`/`next typegen`):

```ts
// app/users/[id]/route.ts
import type { NextRequest } from 'next/server'

export async function GET(_req: NextRequest, ctx: RouteContext<'/users/[id]'>) {
  const { id } = await ctx.params
  return Response.json({ id })
}
```

### Request Body

```ts
// JSON
export async function POST(request: Request) {
  const body = await request.json()
  return Response.json({ received: body })
}

// FormData
export async function POST(request: Request) {
  const formData = await request.formData()
  const name = formData.get('name')
  const email = formData.get('email')
  return Response.json({ name, email })
}

// Raw text (webhooks)
export async function POST(request: Request) {
  const text = await request.text()
  // verify signature, process payload...
  return new Response('OK', { status: 200 })
}
```

### Caching

Route Handlers are **not cached by default** (changed in v15). Only `GET` can be cached. Other methods are never cached.

**Opt into caching** with `force-static`:

```ts
export const dynamic = 'force-static'

export async function GET() {
  const res = await fetch('https://api.example.com/data')
  const data = await res.json()
  return Response.json({ data })
}
```

**Revalidation** with time-based ISR:

```ts
export const revalidate = 60 // revalidate every 60 seconds

export async function GET() {
  const data = await fetch('https://api.vercel.app/blog')
  const posts = await data.json()
  return Response.json(posts)
}
```

**What makes a GET handler dynamic** (prevents prerendering):
- Accessing `request` object properties (`req.url`, `request.headers`, `request.cookies`)
- Calling `cookies()`, `headers()`, `connection()`
- Network requests, database queries, async filesystem operations
- Non-deterministic operations like `Math.random()`, `Date.now()`

**With `use cache`** (Cache Components enabled): extract cached logic into helper functions, not directly in the handler body.

```ts
import { cacheLife } from 'next/cache'

export async function GET() {
  const products = await getProducts()
  return Response.json(products)
}

async function getProducts() {
  'use cache'
  cacheLife('hours')
  return await db.query('SELECT * FROM products')
}
```

## NextRequest

Extends the Web `Request` API. Import from `next/server`.

### `cookies`

```ts
request.cookies.get('token')       // { name, value, Path }
request.cookies.getAll()           // all cookies
request.cookies.getAll('name')     // all cookies with name
request.cookies.has('token')       // boolean
request.cookies.set('key', 'val')  // set cookie
request.cookies.delete('key')      // delete cookie
request.cookies.clear()            // remove all
```

### `nextUrl`

Extended `URL` object with Next.js-specific properties:

```ts
request.nextUrl.pathname       // "/api/users"
request.nextUrl.searchParams   // URLSearchParams object
request.nextUrl.basePath       // base path from config
request.nextUrl.buildId        // build identifier (string | undefined)
```

Note: `ip` and `geo` were removed in v15.

## NextResponse

Extends the Web `Response` API. Import from `next/server`.

### Static Methods

**`NextResponse.json(body, init?)`** -- return JSON:

```ts
import { NextResponse } from 'next/server'
return NextResponse.json({ error: 'Not found' }, { status: 404 })
```

**`NextResponse.redirect(url, status?)`** -- redirect:

```ts
return NextResponse.redirect(new URL('/login', request.url))

// With query params
const loginUrl = new URL('/login', request.url)
loginUrl.searchParams.set('from', request.nextUrl.pathname)
return NextResponse.redirect(loginUrl)
```

**`NextResponse.rewrite(url)`** -- proxy to URL while preserving original URL in browser:

```ts
// Browser shows /about, server renders /about-2
return NextResponse.rewrite(new URL('/about-2', request.url))
```

**`NextResponse.next(init?)`** -- continue to next handler (used in Proxy/Middleware):

```ts
// Pass through with modified request headers
const newHeaders = new Headers(request.headers)
newHeaders.set('x-version', '123')
return NextResponse.next({
  request: { headers: newHeaders },  // forwarded upstream, not to client
})
```

Warning: `NextResponse.next({ headers })` (without `request:`) sends headers to the **client** -- generally avoid this pattern as it can break streaming and Server Actions.

### Response Cookies

```ts
const response = NextResponse.next()
response.cookies.set('theme', 'dark')
response.cookies.set({ name: 'theme', value: 'dark', path: '/' })
response.cookies.get('theme')        // { name, value, Path }
response.cookies.getAll()
response.cookies.has('theme')        // boolean
response.cookies.delete('theme')
return response
```

### Headers & Cookies via `next/headers`

Alternative to `NextRequest`/`NextResponse` -- works in Route Handlers and Server Components:

```ts
import { cookies, headers } from 'next/headers'

export async function GET() {
  const cookieStore = await cookies()
  const token = cookieStore.get('token')

  const headersList = await headers()
  const referer = headersList.get('referer')

  return Response.json({ token: token?.value, referer })
}
```

Note: `headers()` returns a read-only `Headers` instance. To set response headers, return a new `Response`.

## Proxy (`proxy.ts`) -- formerly Middleware

Runs server-side code **before** a request is completed. Renamed from `middleware.ts` in Next.js 16.

**Convention:** single `proxy.ts` at project root (or inside `src/`), same level as `app/` or `pages/`.

```ts
// proxy.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/old-blog')) {
    return NextResponse.redirect(new URL('/blog', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/old-blog/:path*', '/dashboard/:path*'],
}
```

Export as named `proxy` or `default` export. Only one proxy file per project.

**Migrate from middleware:** `npx @next/codemod@canary middleware-to-proxy .`

### Matcher

Controls which paths trigger the proxy:

```ts
// Single path
export const config = { matcher: '/about/:path*' }

// Multiple paths
export const config = { matcher: ['/about/:path*', '/dashboard/:path*'] }

// Regex negative lookahead -- exclude static assets
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)'],
}

// Advanced: has/missing conditions
export const config = {
  matcher: [{
    source: '/api/:path*',
    has: [{ type: 'header', key: 'Authorization', value: 'Bearer Token' }],
    missing: [{ type: 'cookie', key: 'session', value: 'active' }],
  }],
}
```

Matcher values must be constants (statically analyzed at build time).

### Execution Order

1. `headers` from `next.config.js`
2. `redirects` from `next.config.js`
3. Proxy (rewrites, redirects, etc.)
4. `beforeFiles` rewrites from `next.config.js`
5. Filesystem routes (`public/`, `_next/static/`, pages, app)
6. `afterFiles` rewrites
7. Dynamic routes
8. `fallback` rewrites

### `waitUntil` for Background Work

```ts
import { NextResponse } from 'next/server'
import type { NextFetchEvent, NextRequest } from 'next/server'

export function proxy(req: NextRequest, event: NextFetchEvent) {
  event.waitUntil(
    fetch('https://analytics.example.com', {
      method: 'POST',
      body: JSON.stringify({ pathname: req.nextUrl.pathname }),
    })
  )
  return NextResponse.next()
}
```

### Limitations

- Cannot use `fetch` with `cache`, `next.revalidate`, or `next.tags` options
- Not intended for slow data fetching or full session management
- Defaults to Node.js runtime; `runtime` config option is not available in proxy files
- For simple redirects, prefer `redirects` in `next.config.ts`

## Edge Runtime

Opt in per route with `export const runtime = 'edge'`. Default is `'nodejs'`.

```ts
// app/api/route.ts
export const runtime = 'edge'

export async function GET() {
  return Response.json({ runtime: 'edge' })
}
```

**When to use Edge:**
- Need lowest latency (runs closer to user)
- Simple request/response transformations
- Lightweight compute without Node.js dependencies

**Limitations:**
- No native Node.js APIs (no `fs`, no `path`, etc.)
- No `require()` -- must use ES Modules
- `node_modules` work only if they use ES Modules and no native Node.js APIs
- No ISR support
- No `eval()` or `new Function(evalString)`
- `revalidate` config not available with `runtime = 'edge'`
- Not supported with Cache Components (`use cache`)

**Supported APIs:** Web standard APIs (fetch, Request, Response, Headers, URL, crypto, TextEncoder/Decoder, ReadableStream, WritableStream, etc.), plus `process.env` and `AsyncLocalStorage`.

**Allow dynamic code evaluation** for specific files:

```ts
// proxy.ts
export const config = {
  unstable_allowDynamic: ['/lib/utilities.js', '**/node_modules/function-bind/**'],
}
```

## Route Segment Config

Exported constants that configure route behavior. Work in pages, layouts, and route handlers.

```ts
export const dynamic = 'auto'           // 'auto' | 'force-dynamic' | 'error' | 'force-static'
export const dynamicParams = true        // true | false
export const revalidate = false          // false | 0 | number (seconds)
export const fetchCache = 'auto'         // 'auto' | 'default-cache' | 'only-cache' | 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'
export const runtime = 'nodejs'          // 'nodejs' | 'edge'
export const preferredRegion = 'auto'    // 'auto' | 'global' | 'home' | string | string[]
export const maxDuration = 5             // seconds (platform-dependent)
```

**`dynamic`:**
- `'auto'` -- default, cache what can be cached
- `'force-dynamic'` -- always render at request time (like `getServerSideProps`)
- `'error'` -- force static, error if Dynamic APIs are used (like `getStaticProps`)
- `'force-static'` -- force static, `cookies()`/`headers()` return empty values

**`revalidate`:**
- `false` -- cache indefinitely (default)
- `0` -- always dynamic
- `number` -- revalidate every N seconds
- The lowest `revalidate` across layouts/pages in a route wins
- Must be a static literal (`revalidate = 600` works, `revalidate = 60 * 10` does not)

**`dynamicParams`:**
- `true` (default) -- dynamic segments not in `generateStaticParams` render on demand
- `false` -- unmatched segments return 404

Note: these options are disabled when `cacheComponents` is enabled in `next.config.ts`, and may be deprecated in favor of `use cache`.

## Common Patterns

### CORS

```ts
// app/api/route.ts
export async function GET(request: Request) {
  return new Response('OK', {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}
```

For project-wide CORS, use the proxy with a matcher on `/api/:path*`.

### Streaming

With Vercel AI SDK:

```ts
// app/api/chat/route.ts
import { openai } from '@ai-sdk/openai'
import { StreamingTextResponse, streamText } from 'ai'

export async function POST(req: Request) {
  const { messages } = await req.json()
  const result = await streamText({ model: openai('gpt-4-turbo'), messages })
  return new StreamingTextResponse(result.toAIStream())
}
```

With raw Web APIs:

```ts
export async function GET() {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(encoder.encode('chunk 1\n'))
      await new Promise((r) => setTimeout(r, 100))
      controller.enqueue(encoder.encode('chunk 2\n'))
      controller.close()
    },
  })
  return new Response(stream)
}
```

### Webhooks

```ts
export async function POST(request: Request) {
  try {
    const text = await request.text()
    // Verify signature, process payload
  } catch (error) {
    return new Response(`Webhook error: ${error.message}`, { status: 400 })
  }
  return new Response('Success', { status: 200 })
}
```

### Redirects

```ts
import { redirect } from 'next/navigation'

export async function GET(request: Request) {
  redirect('https://nextjs.org/')
}
```

### Non-UI Responses (RSS, XML)

```ts
// app/rss.xml/route.ts
export async function GET() {
  return new Response(`<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>My Blog</title>
    <link>https://example.com</link>
  </channel>
</rss>`, {
    headers: { 'Content-Type': 'text/xml' },
  })
}
```

### Auth Guard in Proxy

```ts
// proxy.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const token = request.cookies.get('session')?.value
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*'],
}
```
