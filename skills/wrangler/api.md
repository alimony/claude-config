# Wrangler: Programmatic API
Based on Wrangler documentation from developers.cloudflare.com.

## Overview

Wrangler exposes three programmatic APIs for using Cloudflare Workers outside the CLI:

| API | Purpose | Stability |
|-----|---------|-----------|
| `unstable_startWorker` | Run dev server for integration tests | Unstable |
| `unstable_dev` | HTTP server for Worker testing | Deprecated, migrate to `unstable_startWorker` |
| `getPlatformProxy` | Emulate Workers platform bindings in Node.js | Stable |

Use the programmatic API when you need to: run Workers in test suites, access bindings (KV, R2, D1, etc.) from Node.js scripts, or build custom dev tooling around Workers.

## `unstable_startWorker` -- Integration Testing

The recommended way to test Workers programmatically. Starts a dev server and returns an object you can fetch against.

```javascript
import { unstable_startWorker } from "wrangler";

let worker;

// Setup -- do this once (startup takes a few hundred ms)
worker = await unstable_startWorker({ config: "wrangler.json" });

// Make requests
const response = await worker.fetch("http://example.com");
const text = await response.text(); // "Hello world"

// Teardown
await worker.dispose();
```

### Test Framework Pattern (node:test)

```javascript
import { unstable_startWorker } from "wrangler";
import { describe, before, after, test } from "node:test";
import assert from "node:assert";

describe("Worker", () => {
  let worker;

  before(async () => {
    worker = await unstable_startWorker({ config: "wrangler.json" });
  });

  after(async () => {
    await worker.dispose();
  });

  test("responds with hello world", async () => {
    const resp = await worker.fetch("http://example.com");
    assert.strictEqual(await resp.text(), "Hello world");
  });
});
```

### API Surface

- **`unstable_startWorker(options)`** -- returns `Promise<Worker>`
  - `options.config` (string) -- path to wrangler.json/wrangler.toml
- **`worker.fetch(url)`** -- send a request, returns `Promise<Response>`
- **`worker.dispose()`** -- shut down the dev server

## `unstable_dev` -- Legacy Testing API

Deprecated in favor of `unstable_startWorker`. Migrate when possible; Vitest integration is also an alternative.

```javascript
import { unstable_dev } from "wrangler";

const worker = await unstable_dev("src/index.js", {
  experimental: { disableExperimentalWarning: true },
});

const resp = await worker.fetch();
const text = await resp.text();

await worker.stop();
```

### TypeScript Usage

```typescript
import { unstable_dev } from "wrangler";
import type { UnstableDevWorker } from "wrangler";

let worker: UnstableDevWorker;
worker = await unstable_dev("src/index.js", {
  experimental: { disableExperimentalWarning: true },
});
```

### Multi-Worker Testing

When testing service bindings or Worker-to-Worker communication, start child Workers before parents. If you shut down the child Worker prematurely, parent Worker tests will fail.

```javascript
import { unstable_dev } from "wrangler";

let childWorker;
let parentWorker;

// Start child first, then parent
childWorker = await unstable_dev("src/child-worker.js", {
  config: "src/child-wrangler.toml",
  experimental: { disableExperimentalWarning: true },
});
parentWorker = await unstable_dev("src/parent-worker.js", {
  config: "src/parent-wrangler.toml",
  experimental: { disableExperimentalWarning: true },
});

// Test child directly
const childResp = await childWorker.fetch();
// => "Hello World!"

// Test parent (which calls child internally)
const parentResp = await parentWorker.fetch();
// => "Parent worker sees: Hello World!"

// Teardown -- stop parent first, then child
await parentWorker.stop();
await childWorker.stop();
```

### API Surface

- **`unstable_dev(script, options?)`** -- returns `Promise<UnstableDevWorker>`
  - `script` (string) -- path to Worker script, relative to project root
  - `options.config` (string) -- path to wrangler config file
  - `options.experimental.disableExperimentalWarning` (boolean) -- suppress warnings
- **`worker.fetch(url?)`** -- returns `Promise<Response>`
- **`worker.stop()`** -- returns `Promise<void>`

## `getPlatformProxy` -- Bindings in Node.js

Access Workers bindings (KV, R2, D1, Queues, Durable Objects, etc.) directly from Node.js. Runs a local `workerd` process under the hood. Cannot run inside the Workers runtime -- Node.js only.

```javascript
import { getPlatformProxy } from "wrangler";

const { env, cf, ctx, caches, dispose } = await getPlatformProxy();

// Access bindings just like in a Worker
console.log(env.MY_VARIABLE);     // environment variable
await env.MY_KV.get("key");       // KV namespace
await env.MY_R2.get("object");    // R2 bucket
await env.MY_DB.prepare("SELECT * FROM users").all(); // D1

// Clean up when done
await dispose();
```

### Configuration

Bindings are read from your wrangler config. Example:

```jsonc
// wrangler.jsonc
{
  "vars": {
    "MY_VARIABLE": "test"
  },
  "kv_namespaces": [
    { "binding": "MY_KV", "id": "abc123" }
  ]
}
```

### Options

```javascript
const platform = await getPlatformProxy({
  configPath: "./wrangler.jsonc",   // path to config (auto-detected if omitted)
  environment: "staging",           // named environment to use
  persist: true,                    // persist data (default: true, uses wrangler default location)
  // persist: { path: "./my-dir/v3" }  // custom persistence path
  experimental: {
    remoteBindings: true,           // connect to remote (production) bindings
  },
});
```

**Persistence gotcha:** If you use `wrangler dev --persist-to ./my-directory`, set `persist: { path: "./my-directory/v3" }` -- the `persist` option does not automatically add the `v3` subdirectory that wrangler CLI adds.

### TypeScript -- Typed Bindings

`getPlatformProxy` is generic. Pass your `Env` interface for full type safety:

```typescript
interface Env {
  MY_VARIABLE: string;
  MY_KV: KVNamespace;
  MY_DB: D1Database;
}

const { env } = await getPlatformProxy<Env>();
env.MY_VARIABLE; // string
env.MY_KV;       // KVNamespace
```

### Return Object

| Property | Type | Description |
|----------|------|-------------|
| `env` | `Record<string, unknown>` | Proxies to all configured bindings |
| `cf` | `IncomingRequestCfProperties` | Read-only mock of `request.cf` |
| `ctx` | `{ waitUntil, passThroughOnException }` | Mock execution context (functions are no-ops) |
| `caches` | object | Cache API emulation (currently all ops are no-ops) |
| `dispose()` | `() => Promise<void>` | Terminates the underlying `workerd` process |

### Supported Bindings

All of these are accessible via `env`:

- **Environment variables** -- plain values from `[vars]`
- **KV namespaces** -- full local emulation
- **R2 buckets** -- full local emulation
- **D1 databases** -- full local emulation
- **Queues** -- local emulation
- **Service bindings** -- inter-Worker calls
- **Durable Objects** -- requires `script_name` in config (see below)
- **Hyperdrive** -- passthrough values only (connectionString/host not meaningful outside workerd)
- **Workers AI** -- always hits your real Cloudflare account and incurs usage charges, even locally

### Durable Objects Setup

Durable Objects always require `script_name` in your binding config, pointing to the Worker that defines the DO class:

```jsonc
// wrangler.jsonc
{
  "durable_objects": {
    "bindings": [
      {
        "name": "MyDurableObject",
        "class_name": "MyDurableObject",
        "script_name": "external-do-worker"
      }
    ]
  }
}
```

The referenced Worker must export the DO class and a default handler:

```typescript
export class MyDurableObject extends DurableObject {
  // implementation
}
export default {
  fetch() {
    return new Response("Hello, world!");
  },
};
```

When using with Pages or Workers+Assets, pass multiple config files:

```bash
# Pages
npx wrangler pages dev -c path/to/pages/wrangler.jsonc -c path/to/external-do-worker/wrangler.jsonc

# Workers + Assets
npx wrangler dev -c path/to/workers-assets/wrangler.jsonc -c path/to/external-do-worker/wrangler.jsonc
```

## Best Practices

1. **Minimize startup overhead** -- Start Workers in `beforeAll`/`before`, not per-test. Dev server startup takes hundreds of milliseconds.

2. **Always dispose/stop** -- Call `dispose()` or `stop()` in `afterAll`/`after` to terminate the `workerd` process and free resources.

3. **Use `getPlatformProxy` for Node.js tooling** -- When building scripts, seed tools, or custom dev servers that need access to Workers bindings without running a full Worker.

4. **Use `unstable_startWorker` for integration tests** -- When you need to test your actual Worker's HTTP handling end-to-end.

5. **Binding proxies are best-effort emulations** -- They are designed to be close to production but may have slight differences. Always verify critical behavior against the real platform.

6. **Workers AI costs money locally** -- Unlike other bindings which run locally, Workers AI always calls your real Cloudflare account. Be cautious in test loops.

7. **Prefer Vitest integration for new projects** -- Wrangler has a dedicated Vitest integration that may be simpler than using these APIs directly. Consider it as an alternative to `unstable_dev`.
