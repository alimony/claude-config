# Vercel: Functions & Compute
Based on Vercel documentation.

## Core Concepts

### What Are Vercel Functions?

Server-side code that runs without managing servers. They scale automatically, handle concurrent requests via fluid compute, and scale to zero when idle. Functions are created by placing files in the `/api` directory (or framework-specific locations like `app/api/` in Next.js App Router).

### Fluid Compute

The default execution model (enabled by default since April 2025). Key benefits:

- **Optimized concurrency**: Multiple requests share a single function instance, reducing cold starts and cost
- **Active CPU billing**: You pay only for CPU time your code actively uses, not I/O wait time
- **Background processing**: Use `waitUntil()` to run tasks after the response is sent
- **Bytecode caching**: Node.js 20+ functions get cached bytecode for faster cold starts (production only)
- **Error isolation**: Uncaught exceptions in one request do not crash other concurrent requests on the same instance
- **SIGTERM handling**: Functions receive SIGTERM before shutdown with 500ms cleanup window

Enable/disable in dashboard (Settings > Functions > Fluid Compute) or `vercel.json`:

```json
{ "fluid": true }
```

### Runtimes Comparison

| Runtime | Best For | Isolation | Max Bundle |
|---------|----------|-----------|------------|
| **Node.js** | General purpose, full Node.js API | microVM | 250 MB |
| **Bun** | CPU-bound tasks, zero-config TS | microVM | 250 MB |
| **Python** | FastAPI, Django, Flask, ML | microVM | 500 MB |
| **Go** | High-performance HTTP handlers | microVM | 250 MB |
| **Edge** | Low-latency, global execution | V8 isolate | 1-4 MB |

**Vercel recommends Node.js over Edge** for most use cases. Edge has limited API support (no filesystem, no native Node.js modules, no `eval`/`new Function`).

## Function Signatures

### Recommended: `fetch` Web Standard (Node.js/Bun)

```ts
// api/hello.ts — works with Hono, ElysiaJS, H3, etc.
export default {
  async fetch(request: Request) {
    const url = new URL(request.url);
    const name = url.searchParams.get('name') || 'World';
    return Response.json({ message: `Hello ${name}!` });
  },
};
```

### Named HTTP Method Exports

```ts
// api/users.ts
export async function GET(request: Request) {
  return Response.json({ users: [] });
}

export async function POST(request: Request) {
  const body = await request.json();
  return Response.json({ created: true }, { status: 201 });
}
```

### Next.js App Router (Route Handlers)

```ts
// app/api/hello/route.ts
export const maxDuration = 30;

export async function GET(request: Request) {
  return new Response('Hello from Vercel!');
}
```

### Python

```python
# api/index.py — BaseHTTPRequestHandler style
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write('{"hello": "world"}'.encode('utf-8'))
```

```python
# api/index.py — WSGI/ASGI (FastAPI, Flask, Django)
# Export an `app` variable instead of `handler`
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/index")
def root():
    return {"hello": "world"}
```

### Go

```go
// api/index.go
package handler

import (
  "fmt"
  "net/http"
)

func Handler(w http.ResponseWriter, r *http.Request) {
  fmt.Fprintf(w, `{"hello": "world"}`)
}
```

## Configuration

### Duration, Memory, and Region Limits

| Setting | Hobby | Pro | Enterprise |
|---------|-------|-----|------------|
| **Default duration** | 300s | 300s | 300s |
| **Max duration** | 300s | 800s | 800s |
| **Memory/CPU** | 2 GB / 1 vCPU (fixed) | 2-4 GB / 1-2 vCPU | Same as Pro |
| **Regions** | 1 | Up to 3 | Unlimited |
| **Concurrency** | Up to 30,000 | Up to 30,000 | 100,000+ |
| **Request/response body** | 4.5 MB | 4.5 MB | 4.5 MB |
| **File descriptors** | 1,024 shared | 1,024 shared | 1,024 shared |
| **Functions per deploy** | 12 (no framework) | Unlimited | Unlimited |

### Setting Duration

In function code (Next.js App Router, SvelteKit, Astro, Nuxt, Remix):

```ts
// app/api/long-task/route.ts
export const maxDuration = 60; // seconds
```

In `vercel.json` (all runtimes):

```json
{
  "functions": {
    "api/heavy.js": { "maxDuration": 60 },
    "api/*.py": { "maxDuration": 30 }
  }
}
```

### Setting Regions

Default region: `iad1` (Washington, D.C.). Always deploy functions near your data source.

```json
{
  "regions": ["sfo1"],
  "functionFailoverRegions": ["pdx1"],
  "functions": {
    "api/eu-data.js": {
      "regions": ["cdg1"],
      "functionFailoverRegions": ["lhr1"]
    }
  }
}
```

For Next.js App Router, set region in code:

```ts
export const preferredRegion = ['iad1', 'hnd1'];
```

For Edge runtime, also export the runtime:

```ts
export const runtime = 'edge';
export const preferredRegion = ['iad1', 'hnd1'];
```

## Key APIs: `@vercel/functions`

```bash
npm i @vercel/functions
```

### `waitUntil()` -- Background Tasks

Runs work after the response is sent. The promise shares the function's timeout.

```ts
import { waitUntil } from '@vercel/functions';

export default {
  fetch(request: Request) {
    waitUntil(
      fetch('https://analytics.example.com/log', {
        method: 'POST',
        body: JSON.stringify({ url: request.url }),
      })
    );
    return new Response('OK');
  },
};
```

For **Next.js 15.1+**, use the built-in `after()` from `next/server` instead:

```ts
import { after } from 'next/server';

export async function GET(request: Request) {
  const response = new Response('Hello');
  after(async () => {
    await fetch('https://analytics.example.com/log');
  });
  return response;
}
```

### `geolocation()` and `ipAddress()`

```ts
import { geolocation, ipAddress } from '@vercel/functions';

export default {
  fetch(request: Request) {
    const geo = geolocation(request);
    // { city, country, flag, countryRegion, region, latitude, longitude, postalCode }
    const ip = ipAddress(request);
    return Response.json({ geo, ip });
  },
};
```

### `attachDatabasePool()` -- Connection Management

Critical for fluid compute. Ensures idle pool clients are released before functions suspend.

```ts
import { Pool } from 'pg';
import { attachDatabasePool } from '@vercel/functions';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
attachDatabasePool(pool); // Call once after creating the pool

export default {
  async fetch() {
    const client = await pool.connect();
    try {
      const result = await client.query('SELECT NOW()');
      return Response.json(result.rows[0]);
    } finally {
      client.release();
    }
  },
};
```

Supports: pg, mysql2, mariadb, mongodb, ioredis, cassandra-driver.

### `getCache()` -- Runtime Cache

```ts
import { getCache } from '@vercel/functions';

export default {
  async fetch(request: Request) {
    const cache = getCache();
    const cached = await cache.get('my-key');
    if (cached) return Response.json(cached);

    const data = await fetchExpensiveData();
    await cache.set('my-key', data, { ttl: 3600, tags: ['my-tag'] });
    return Response.json(data);
  },
};
```

Invalidate by tag (propagates globally in ~300ms):

```ts
await getCache().expireTag('my-tag');
```

Cache limits: max 2 MB per item, 128 tags per item, 256 bytes per tag.

### Cache Tag Invalidation (CDN)

```ts
import { invalidateByTag, addCacheTag } from '@vercel/functions';

// Tag a response
await addCacheTag('product-123,products');

// Later, invalidate (background revalidation)
await invalidateByTag('product-123');
```

### `getEnv()` -- System Environment Variables

```ts
import { getEnv } from '@vercel/functions';
const { VERCEL_REGION } = getEnv();
```

## Streaming

Use the Vercel AI SDK (`ai` package) for streaming AI responses:

```ts
import { streamText } from 'ai';

export async function POST(request: Request) {
  const { messages } = await request.json();
  const response = streamText({
    model: 'openai/gpt-4o-mini',
    messages,
  });
  return response.toTextStreamResponse();
}
```

Streaming is supported on Node.js, Bun, and Python runtimes. Edge runtime must begin sending a response within 25 seconds but can stream for up to 300 seconds.

## Cron Jobs

Configure in `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/daily-cleanup",
      "schedule": "0 5 * * *"
    }
  ]
}
```

Cron expression format: `minute hour day-of-month month day-of-week` (always UTC). Validate with [crontab.guru](https://crontab.guru/).

Key constraints:
- **Hobby**: Max 2 cron jobs, daily frequency only
- **Pro**: Up to 40 cron jobs
- Cron requests are HTTP GET with user agent `vercel-cron/1.0`
- No alternative names (`MON`, `JAN`) -- use numbers only
- Cannot set both day-of-month and day-of-week simultaneously

Secure your cron endpoint:

```ts
export function GET(request: Request) {
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }
  // ... do work
  return Response.json({ success: true });
}
```

## Request Cancellation

Enable per-route in `vercel.json`, then use `AbortController`:

```json
{
  "functions": {
    "api/*": { "supportsCancellation": true }
  }
}
```

```ts
export async function GET(request: Request) {
  const controller = new AbortController();
  request.signal.addEventListener('abort', () => controller.abort());

  const response = await fetch('https://backend.example.com', {
    signal: controller.signal,
  });
  return new Response(response.body);
}
```

Put must-complete work in `waitUntil()` when cancellation is enabled.

## OG Image Generation

Use `@vercel/og` (included in Next.js App Router as `next/og`) to generate social card images:

```tsx
// app/api/og/route.tsx
import { ImageResponse } from 'next/og'; // or '@vercel/og' outside Next.js

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get('title') || 'Hello';

  return new ImageResponse(
    (
      <div style={{
        fontSize: 60, background: 'white', width: '100%', height: '100%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {title}
      </div>
    ),
    { width: 1200, height: 630 },
  );
}
```

Key constraints:
- Only flexbox layout (`display: flex`) supported -- no CSS grid
- Font formats: `ttf`, `otf`, `woff` only
- Max bundle: 500 KB (including fonts/images)
- Cached by default with `max-age=31536000`
- Add `/api/og/*` to `Allow` in `robots.txt` so social crawlers can fetch images

## Vercel Sandbox

Ephemeral Linux microVMs for running untrusted code (AI agents, user submissions, playgrounds).

```ts
import { Sandbox } from '@vercel/sandbox';

const sandbox = await Sandbox.create({ runtime: 'node24' });
const result = await sandbox.runCommand('node', ['-e', 'console.log("hi")']);
console.log(await result.stdout()); // "hi"
await sandbox.stop();
```

Key features:
- Millisecond startup, Firecracker microVM isolation
- Runtimes: `node24`, `node22`, `python3.13`
- Snapshotting: save state to skip setup on future runs
- Network policies: `allow-all`, `deny-all`, or custom domain allowlists with credential brokering
- File I/O: `writeFiles()`, `readFile()`, `mkDir()`
- Public URLs via `sandbox.domain(port)` for exposed ports
- Default timeout: 5 min (extendable to 45 min Hobby, 5 hrs Pro/Enterprise)
- Auth: Vercel OIDC tokens (recommended) or access tokens

## Pricing (Fluid Compute)

| Metric | How It Works |
|--------|-------------|
| **Active CPU** | Billed per CPU-hour. Only actual code execution counts; I/O wait is free |
| **Provisioned Memory** | Billed per GB-hour for entire instance lifetime (including I/O wait) |
| **Invocations** | Per request. First 1M included on Hobby and Pro |

Regional pricing varies. Example (Sao Paulo, 4 GB function, 1 request):
- 4s active CPU + 10s instance alive = ~$0.00045 per invocation

## Common Pitfalls

1. **Functions far from data**: Default region is `iad1`. If your DB is in EU, set `regions: ["cdg1"]` to avoid cross-continent latency.
2. **Missing `attachDatabasePool()`**: Without it, connection pools leak across suspensions in fluid compute. Always call it after creating a pool.
3. **Edge runtime limitations**: No filesystem, no native Node.js modules, no `eval`. Vercel recommends migrating from Edge to Node.js.
4. **4.5 MB body limit**: Both request and response bodies are capped. Use presigned URLs or streaming for large payloads.
5. **Cron idempotency**: Events may be delivered more than once. Design handlers to be safe on re-execution.
6. **Archiving cold starts**: Functions archived after 2 weeks (production) or 48 hours (preview) get an extra ~1s cold start on first invocation.
7. **File descriptors**: Only 1,024 shared across concurrent executions. Use connection pooling and close resources promptly.
8. **Python bundle size**: No automatic tree-shaking. Use `excludeFiles` in `vercel.json` to stay under the 500 MB limit.
9. **`waitUntil` timeout**: Promises passed to `waitUntil()` share the function's `maxDuration`. They are cancelled if the function times out.
10. **SIGTERM cleanup window**: Only 500ms after receiving SIGTERM. Keep cleanup logic minimal.

## Settings Precedence

When multiple configurations exist, the order of priority (highest first):

1. **Function code** (`export const maxDuration = ...`)
2. **`vercel.json`** (`functions` property)
3. **Dashboard** settings
4. **Fluid compute defaults**
