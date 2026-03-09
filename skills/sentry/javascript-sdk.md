# Sentry: JavaScript SDK
Based on Sentry documentation (docs.sentry.io).

## SDK Setup

### Browser (Vanilla JS)

```bash
npm install @sentry/browser --save
```

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 1.0,
  tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

### React

```bash
npm install @sentry/react --save
```

```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  sendDefaultPii: true,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 1.0,
  tracePropagationTargets: [/^\//, /^https:\/\/yourserver\.io\/api/],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

### Next.js

Run the wizard (creates config files automatically):

```bash
npx @sentry/wizard@latest -i nextjs
```

Client config (`instrumentation-client.ts`):

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  sendDefaultPii: true,
  tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [Sentry.replayIntegration()],
});
```

Server config (`instrumentation.ts`):

```typescript
import * as Sentry from "@sentry/nextjs";

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./sentry.edge.config");
  }
}

export const onRequestError = Sentry.captureRequestError;
```

Wrap `next.config.ts`:

```typescript
import { withSentryConfig } from "@sentry/nextjs";

export default withSentryConfig(nextConfig, {
  org: "your-org-slug",
  project: "your-project-slug",
  authToken: process.env.SENTRY_AUTH_TOKEN,
  tunnelRoute: "/monitoring",  // Bypasses ad-blockers
  silent: !process.env.CI,
});
```

### Node.js

```bash
npm install @sentry/node --save
```

Create `instrument.js` (must be imported before all other modules):

```javascript
const Sentry = require("@sentry/node");

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  sendDefaultPii: true,
  tracesSampleRate: 1.0,
});
```

CommonJS: `require("./instrument");` at the top of your entry file.
ESM: `node --import ./instrument.mjs app.mjs`

## Configuration Options

### Core Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dsn` | string | — | Where to send events. SDK is disabled if unset |
| `debug` | boolean | false | Print SDK debug info to console |
| `release` | string | — | App version string for regression tracking |
| `environment` | string | `"production"` | Deployment environment name |
| `enabled` | boolean | true | Whether the SDK sends events |
| `tunnel` | string | — | Custom endpoint URL (bypasses ad-blockers) |
| `sendDefaultPii` | boolean | false | Auto-collect IP addresses |
| `maxBreadcrumbs` | number | 100 | Max breadcrumbs before oldest are dropped |
| `attachStacktrace` | boolean | false | Attach stack traces to all messages |
| `normalizeDepth` | number | 3 | Context data normalization depth |
| `sampleRate` | number | 1.0 | Error event sample rate (0.0 to 1.0) |

### Tracing Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `tracesSampleRate` | number | — | Transaction sample rate (0.0 to 1.0) |
| `tracesSampler` | function | — | Dynamic per-transaction sampling function |
| `tracePropagationTargets` | (string\|RegExp)[] | — | Which outgoing requests get trace headers |
| `beforeSendTransaction` | function | — | Modify/drop transactions before sending |
| `beforeSendSpan` | function | — | Modify serialized spans before sending |
| `ignoreTransactions` | (string\|RegExp)[] | [] | Drop transactions matching patterns |

### Replay Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `replaysSessionSampleRate` | number | 0 | Rate for full session recording (0.0 to 1.0) |
| `replaysOnErrorSampleRate` | number | 0 | Rate for error-triggered replays (0.0 to 1.0) |

### Profiling Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `profileSessionSampleRate` | number | — | Percentage of sessions with profiling (0.0 to 1.0) |
| `profileLifecycle` | `"trace"` \| `"manual"` | `"manual"` | Auto-profile with spans or manual control |

### Logs Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enableLogs` | boolean | false | Enable structured log capture |
| `beforeSendLog` | function | — | Filter/modify logs; return null to drop |

### Filtering Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `beforeSend` | function | — | Modify/drop error events before sending |
| `beforeBreadcrumb` | function | — | Modify/drop breadcrumbs; return null to discard |
| `ignoreErrors` | (string\|RegExp)[] | [] | Drop errors matching message patterns |
| `denyUrls` | (string\|RegExp)[] | [] | Drop errors from matching script URLs |
| `allowUrls` | (string\|RegExp)[] | [] | Only keep errors from matching script URLs |

## Sampling

### Uniform Rate

```javascript
Sentry.init({
  tracesSampleRate: 0.2,  // 20% of transactions
  sampleRate: 0.25,       // 25% of errors
});
```

### Dynamic Sampling with tracesSampler

`tracesSampler` takes precedence over `tracesSampleRate`. Return 0-1 (rate), true (100%), or false (0%).

```javascript
Sentry.init({
  tracesSampler: ({ name, attributes, inheritOrSampleWith }) => {
    if (name.includes("healthcheck")) return 0;
    if (name.includes("auth")) return 1;
    if (name.includes("comment")) return 0.01;
    return inheritOrSampleWith(0.5);  // Inherit parent or use 0.5
  },
});
```

Precedence: `tracesSampler` > parent sampling decision > `tracesSampleRate`.

### Filtering Events

```javascript
Sentry.init({
  beforeSend(event) {
    if (event.user) {
      delete event.user.email;  // Strip PII
    }
    return event;  // Return null to drop
  },
  ignoreErrors: [
    "fb_xd_fragment",
    /^Exact Match Message$/,
  ],
  allowUrls: [/https?:\/\/((cdn|www)\.)?example\.com/],
});
```

## Capturing Events

### captureException

```javascript
try {
  riskyOperation();
} catch (err) {
  Sentry.captureException(err);
}
```

### captureMessage

```javascript
Sentry.captureMessage("Something went wrong");
Sentry.captureMessage("Rate limit hit", "warning");
// Levels: "fatal" | "error" | "warning" | "log" | "debug" | "info"
```

### Uncaught Errors

The SDK automatically captures uncaught exceptions and unhandled promise rejections. No manual setup needed.

## Enriching Events

### Tags (Searchable Key-Value Pairs)

```javascript
Sentry.setTag("page_locale", "de-at");
```

Tag keys: max 32 chars, letters/numbers/underscores/periods/colons/dashes.
Tag values: max 200 chars, no newlines.
Tags are indexed and searchable in the Sentry UI.

### Context (Structured Metadata, Not Searchable)

```javascript
Sentry.setContext("character", {
  name: "Mighty Fighter",
  age: 19,
  attack_type: "melee",
});
```

Context data is normalized to `normalizeDepth` levels (default 3). Displayed on issue pages but not filterable.

### Breadcrumbs (Event Trail)

```javascript
Sentry.addBreadcrumb({
  category: "auth",
  message: "Authenticated user " + user.email,
  level: "info",
});
```

Automatic breadcrumbs captured: DOM clicks, key presses, XHR/fetch requests, console calls, location changes.

Filter breadcrumbs:

```javascript
Sentry.init({
  beforeBreadcrumb(breadcrumb, hint) {
    return breadcrumb.category === "ui.click" ? null : breadcrumb;
  },
});
```

### User Identification

```javascript
Sentry.setUser({
  id: "user_123",
  email: "user@example.com",
  username: "john_doe",
  ip_address: "{{ auto }}",  // Auto-detect from connection
});

// Clear user on logout
Sentry.setUser(null);
```

Fields: `id`, `email`, `username`, `ip_address`, plus any custom key-value pairs.

### Scopes

Three scope types: global (all events), isolation (per-request), current (local).

```javascript
// Temporary scope for a single event
Sentry.withScope((scope) => {
  scope.setTag("my-tag", "my value");
  scope.setLevel("warning");
  Sentry.captureException(new Error("scoped error"));
});
// Tag and level do not persist outside the callback
```

Scope priority: global < isolation < current (later overrides earlier).

## React Integration

### Error Boundary (React 18 and below)

```javascript
import * as Sentry from "@sentry/react";

function App() {
  return (
    <Sentry.ErrorBoundary fallback={<p>An error has occurred</p>}>
      <YourAppContent />
    </Sentry.ErrorBoundary>
  );
}
```

### React 19+ Error Handling

```javascript
import { createRoot } from "react-dom/client";

const root = createRoot(container, {
  onUncaughtError: Sentry.reactErrorHandler((error, errorInfo) => {
    console.warn("Uncaught error", error, errorInfo.componentStack);
  }),
  onCaughtError: Sentry.reactErrorHandler(),
  onRecoverableError: Sentry.reactErrorHandler(),
});
```

### React Router v7

```javascript
import React from "react";
import * as Sentry from "@sentry/react";
import {
  useLocation, useNavigationType,
  createRoutesFromChildren, matchRoutes,
} from "react-router";

Sentry.init({
  dsn: "...",
  integrations: [
    Sentry.reactRouterV7BrowserTracingIntegration({
      useEffect: React.useEffect,
      useLocation,
      useNavigationType,
      createRoutesFromChildren,
      matchRoutes,
    }),
  ],
});
```

### Redux Integration

```javascript
const sentryEnhancer = Sentry.createReduxEnhancer();
const store = createStore(rootReducer, compose(sentryEnhancer));
```

## Next.js Integration

### Global Error Page (`app/global-error.tsx`)

```tsx
"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <h1>Something went wrong!</h1>
      </body>
    </html>
  );
}
```

### Auth Token

The wizard creates `.env.sentry-build-plugin` with the auth token. For CI/CD, set the `SENTRY_AUTH_TOKEN` environment variable.

## Tracing

### Browser Tracing Setup

```javascript
Sentry.init({
  integrations: [Sentry.browserTracingIntegration()],
  tracesSampleRate: 1.0,
  tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
});
```

### Custom Spans

**startSpan** (auto-ends when callback completes, recommended):

```javascript
const result = await Sentry.startSpan(
  { name: "fetchUserData", op: "http.client" },
  async () => {
    const res = await fetch("/api/users");
    return res.json();
  },
);
```

**Nested spans:**

```javascript
const result = await Sentry.startSpan(
  { name: "processOrder" },
  async () => {
    const user = await Sentry.startSpan(
      { name: "fetchUser" },
      () => getUser(),
    );
    return Sentry.startSpan(
      { name: "chargePayment" },
      () => charge(user),
    );
  },
);
```

**startSpanManual** (you control when it ends):

```javascript
function middleware(_req, res, next) {
  return Sentry.startSpanManual({ name: "middleware" }, (span) => {
    res.once("finish", () => {
      span.setHttpStatus(res.status);
      span.end();
    });
    return next();
  });
}
```

**startInactiveSpan** (no callback, manual end, not automatically a parent):

```javascript
const span = Sentry.startInactiveSpan({ name: "background-task" });
// ... later
span.end();
```

### Span Options

| Option | Type | Purpose |
|--------|------|---------|
| `name` | string | Span identifier (required) |
| `op` | string | Operation type (e.g. `http.client`, `db.query`) |
| `attributes` | Record | Custom key-value metadata |
| `parentSpan` | Span | Explicitly set parent |
| `onlyIfParent` | boolean | Skip if no parent exists |
| `forceTransaction` | boolean | Display as transaction in UI |

### Span Attributes and Status

```javascript
const span = Sentry.getActiveSpan();
if (span) {
  span.setAttribute("user.tier", "premium");
  span.setAttributes({ cache: "miss", region: "us-east" });
  Sentry.updateSpanName(span, "GET /users/:id");
  span.setStatus({ code: 2 }); // 0=unknown, 1=ok, 2=error
}
```

### Browser Span Hierarchy

By default, all browser spans are flat (children of root). Enable nesting:

```javascript
Sentry.init({
  parentSpanIsAlwaysRootSpan: false,
});
```

## Session Replay

### Setup

```javascript
Sentry.init({
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  integrations: [Sentry.replayIntegration()],
});
```

### Recommended Production Sample Rates

| Traffic | Session Rate | Error Rate |
|---------|-------------|------------|
| High (100k+/day) | 0.01 | 1.0 |
| Medium (10k-100k/day) | 0.1 | 1.0 |
| Low (<10k/day) | 0.25 | 1.0 |

Always keep `replaysOnErrorSampleRate` at 1.0 -- error replays provide the most debugging value.

### Privacy Configuration

By default, all text is masked with `*` and all media is blocked.

```javascript
Sentry.replayIntegration({
  maskAllText: true,       // Default: true
  maskAllInputs: true,     // Default: true
  blockAllMedia: true,     // Default: true
});
```

Target specific elements:

```javascript
Sentry.replayIntegration({
  mask: [".sentry-mask", "[data-sentry-mask]", ".sensitive-class"],
  unmask: [".safe-to-show"],
  block: [".sentry-block", "[data-sentry-block]"],
  unblock: [".safe-media"],
  ignore: [".sentry-ignore"],  // Ignore form input events
});
```

HTML attributes: `data-sentry-mask`, `data-sentry-block`, `data-sentry-ignore`.

### Network Capture (Opt-In)

```javascript
Sentry.replayIntegration({
  networkDetailAllowUrls: [window.location.origin, "api.example.com"],
  networkCaptureBodies: true,
  networkRequestHeaders: ["Cache-Control"],
  networkResponseHeaders: ["Referrer-Policy"],
});
```

### Lazy-Load Replay (Reduce Bundle Size)

```javascript
Sentry.init({ integrations: [] });

// Load later when needed
import("@sentry/browser").then((lazyLoadedSentry) => {
  Sentry.addIntegration(lazyLoadedSentry.replayIntegration());
});
```

### Canvas Recording

```javascript
Sentry.init({
  integrations: [
    Sentry.replayIntegration(),
    Sentry.replayCanvasIntegration(),
  ],
});
```

Warning: No PII scrubbing in canvas recordings.

### CSP Requirements

```
worker-src 'self' blob:
child-src 'self' blob:
```

## Source Maps

### Wizard Setup (Recommended)

```bash
npx @sentry/wizard@latest -i sourcemaps
```

Supports: Webpack, Vite, Rollup, esbuild, TypeScript (tsc).

The wizard configures the build plugin which injects Debug IDs and uploads source maps automatically during build.

### Build Plugin (Manual Configuration)

For Vite (`vite.config.ts`):

```typescript
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig({
  build: { sourcemap: true },
  plugins: [
    sentryVitePlugin({
      org: "your-org",
      project: "your-project",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
});
```

For Webpack (`webpack.config.js`):

```javascript
const { sentryWebpackPlugin } = require("@sentry/webpack-plugin");

module.exports = {
  devtool: "source-map",
  plugins: [
    sentryWebpackPlugin({
      org: "your-org",
      project: "your-project",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
};
```

Source maps are generated only during production builds. They must be uploaded before errors occur for proper stack trace deobfuscation.

## Structured Logging

Requires SDK 9.41.0+. Not supported via loader or CDN scripts.

```javascript
Sentry.init({ dsn: "...", enableLogs: true });

Sentry.logger.trace("Entering function", { fn: "processOrder" });
Sentry.logger.debug("Cache lookup", { key: "user:123" });
Sentry.logger.info("Order created", { orderId: "order_456" });
Sentry.logger.warn("Rate limit approaching", { current: 95, max: 100 });
Sentry.logger.error("Payment failed", { reason: "card_declined" });
Sentry.logger.fatal("Database unavailable", { host: "primary" });
```

### Parameterized Messages

```javascript
Sentry.logger.info(
  Sentry.logger.fmt`User ${userId} purchased ${productName}`,
);
```

### Console Integration

```javascript
Sentry.init({
  integrations: [
    Sentry.consoleLoggingIntegration({ levels: ["log", "warn", "error"] }),
  ],
});
```

### Filter Logs

```javascript
Sentry.init({
  enableLogs: true,
  beforeSendLog: (log) => {
    if (log.level === "debug") return null;  // Drop debug logs
    if (log.attributes?.password) delete log.attributes.password;
    return log;
  },
});
```

## Browser Profiling

Requires Chromium-based browsers (uses JS Self-Profiling API).

### Required HTTP Header

Your server must return: `Document-Policy: js-profiling`

### Setup

```javascript
Sentry.init({
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.browserProfilingIntegration(),
  ],
  tracesSampleRate: 1.0,
  profileSessionSampleRate: 1.0,
});
```

### Manual Profiling

```javascript
Sentry.uiProfiler.startProfiler();
// ... code to profile
Sentry.uiProfiler.stopProfiler();
```

### Trace-Based Profiling

```javascript
Sentry.init({
  profileLifecycle: "trace",  // Auto-profile during active spans
});
```

## Sensitive Data

### SDK-Level Scrubbing (beforeSend)

```javascript
Sentry.init({
  beforeSend(event) {
    if (event.user) {
      delete event.user.email;
    }
    return event;
  },
});
```

### Best Practices

- Send internal IDs instead of emails: `Sentry.setUser({ id: user.id })`
- Hash sensitive values before using as tags
- Use `beforeBreadcrumb` to filter sensitive log data
- Keep `sendDefaultPii: false` (default) unless you need IP collection
- Server-side scrubbing is configurable in Sentry UI without redeployment

### Where Sensitive Data May Appear

- Stack trace local variables
- Breadcrumbs (log statements, DB queries)
- User context (controlled by `sendDefaultPii`)
- HTTP query strings
- Transaction names (URL paths with user IDs)

## Common Pitfalls

### Source Maps Not Working

- Ensure `sourcemap: true` in your build config
- Source maps must be uploaded before errors are captured
- Verify `release` matches between init config and uploaded artifacts
- Use Debug IDs (modern approach) instead of release-based matching

### Bundle Size

- Lazy-load `replayIntegration()` to avoid adding it to the initial bundle
- Use tree shaking: import only what you need from `@sentry/browser`
- The `replayIntegration` adds significant weight; load it asynchronously if page load is critical

### SSR / Next.js Gotchas

- Client and server need separate configs (`instrumentation-client.ts` vs `sentry.server.config.ts`)
- Wrap `next.config.ts` with `withSentryConfig` for source map uploads
- Use `tunnelRoute: "/monitoring"` to bypass ad-blockers
- Set `SENTRY_AUTH_TOKEN` as env var in CI/CD (not committed to repo)
- The `onRequestError` export in `instrumentation.ts` captures server-side request errors

### Node.js Init Order

- `instrument.js` must be imported before all other modules
- CommonJS: `require("./instrument")` at the very top
- ESM: use `node --import ./instrument.mjs`

### Sampling in Production

- Never run `tracesSampleRate: 1.0` in production for high-traffic apps
- Use `tracesSampler` for granular control (drop healthchecks, sample auth at 100%)
- Error sample rate defaults to 1.0; reduce only if volume is excessive
- `replaysSessionSampleRate` of 0.1 is a good starting point for medium traffic

### React 19 Breaking Change

- `ErrorBoundary` component works for React 18 and below
- React 19 requires `reactErrorHandler()` passed to `createRoot` options instead
