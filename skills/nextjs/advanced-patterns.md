# Next.js: Advanced Patterns
Based on Next.js documentation (App Router).

## Internationalization (i18n)

### Routing strategy

Nest all routes under `app/[lang]/` so the locale is a dynamic segment. Use middleware (or `proxy.js`) to detect the user's preferred locale from the `Accept-Language` header and redirect to the correct sub-path.

```js
// proxy.js
import { NextResponse } from "next/server";
import { match } from "@formatjs/intl-localematcher";
import Negotiator from "negotiator";

const locales = ["en-US", "nl-NL", "nl"];
const defaultLocale = "en-US";

function getLocale(request) {
  const headers = { "accept-language": request.headers.get("accept-language") };
  const languages = new Negotiator({ headers }).languages();
  return match(languages, locales, defaultLocale);
}

export function proxy(request) {
  const { pathname } = request.nextUrl;
  const hasLocale = locales.some(
    (l) => pathname.startsWith(`/${l}/`) || pathname === `/${l}`
  );
  if (hasLocale) return;

  const locale = getLocale(request);
  request.nextUrl.pathname = `/${locale}${pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = { matcher: ["/((?!_next).*)"] };
```

### Translation dictionaries

Load JSON dictionaries per locale in Server Components. The dictionary files stay out of the client bundle.

```ts
// app/[lang]/dictionaries.ts
import "server-only";

const dictionaries = {
  en: () => import("./dictionaries/en.json").then((m) => m.default),
  nl: () => import("./dictionaries/nl.json").then((m) => m.default),
};

export type Locale = keyof typeof dictionaries;
export const hasLocale = (l: string): l is Locale => l in dictionaries;
export const getDictionary = async (l: Locale) => dictionaries[l]();
```

```tsx
// app/[lang]/page.tsx
import { notFound } from "next/navigation";
import { getDictionary, hasLocale } from "./dictionaries";

export default async function Page({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const dict = await getDictionary(lang);
  return <button>{dict.products.cart}</button>;
}
```

### Static generation for locales

```tsx
// app/[lang]/layout.tsx
export async function generateStaticParams() {
  return [{ lang: "en-US" }, { lang: "de" }];
}

export default async function RootLayout({ children, params }: LayoutProps<"/[lang]">) {
  return <html lang={(await params).lang}><body>{children}</body></html>;
}
```

Libraries: `next-intl`, `next-international`, `lingui`, `paraglide-next`.

---

## Multi-Zones (Micro-Frontends)

Multiple independent Next.js apps served under one domain. Each "zone" owns a set of URL paths. Navigation within a zone is a soft navigation; crossing zones triggers a hard navigation (full page load).

### Zone configuration

Each non-default zone needs `assetPrefix` to avoid static file conflicts:

```js
// next.config.js (blog zone)
const nextConfig = {
  assetPrefix: "/blog-static",
};
```

### Routing requests

The primary app uses `rewrites` to forward paths to other zones:

```js
// next.config.js (main app)
async rewrites() {
  return [
    { source: "/blog",       destination: `${process.env.BLOG_DOMAIN}/blog` },
    { source: "/blog/:path+", destination: `${process.env.BLOG_DOMAIN}/blog/:path+` },
    { source: "/blog-static/:path+", destination: `${process.env.BLOG_DOMAIN}/blog-static/:path+` },
  ];
}
```

### Key rules

- Use `<a>` tags (not `<Link>`) for cross-zone navigation.
- Set `serverActions.allowedOrigins` in each zone's config when using Server Actions.
- Feature flags help coordinate releases across zones.
- Share code via a monorepo or private npm packages.

---

## Instrumentation

`instrumentation.ts` runs once when a new Next.js server instance starts, before it handles requests.

```ts
// instrumentation.ts (project root or src/)
import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({ serviceName: "next-app" });
}
```

### Runtime-specific imports

`register` runs in both Node.js and Edge runtimes. Conditionally import runtime-specific code:

```ts
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./instrumentation-node");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    await import("./instrumentation-edge");
  }
}
```

---

## OpenTelemetry

Next.js auto-instruments spans for incoming requests, route rendering, fetch calls, API handlers, and metadata generation.

### Quick setup with @vercel/otel

```bash
npm install @vercel/otel @opentelemetry/sdk-logs @opentelemetry/api-logs @opentelemetry/instrumentation
```

```ts
// instrumentation.ts
import { registerOTel } from "@vercel/otel";
export function register() {
  registerOTel({ serviceName: "next-app" });
}
```

### Manual setup (Node.js only)

```ts
// instrumentation.node.ts
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { SimpleSpanProcessor } from "@opentelemetry/sdk-trace-node";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: resourceFromAttributes({ [ATTR_SERVICE_NAME]: "next-app" }),
  spanProcessor: new SimpleSpanProcessor(new OTLPTraceExporter()),
});
sdk.start();
```

### Custom spans

```ts
import { trace } from "@opentelemetry/api";

export async function fetchGithubStars() {
  return await trace.getTracer("nextjs-example").startActiveSpan("fetchGithubStars", async (span) => {
    try { return await getValue(); }
    finally { span.end(); }
  });
}
```

### Default span types

| Span | Type |
|------|------|
| `[method] [route]` | Root request span |
| `render route (app) [route]` | App Router render |
| `fetch [method] [url]` | Fetch in app code |
| `executing api route (app) [route]` | Route Handler execution |
| `generateMetadata [page]` | Metadata generation |

Set `NEXT_OTEL_VERBOSE=1` to emit all spans. Set `NEXT_OTEL_FETCH_DISABLED=1` to suppress fetch spans.

---

## Lazy Loading

Reduces initial JS by deferring Client Components and libraries until needed. Server Components are automatically code-split.

### next/dynamic

Composite of `React.lazy()` + `Suspense`:

```jsx
"use client";
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("../components/Chart"));
const ClientOnly = dynamic(() => import("../components/Map"), { ssr: false });
const WithLoader = dynamic(() => import("../components/Editor"), {
  loading: () => <p>Loading...</p>,
});
```

### Named exports

```jsx
const Hello = dynamic(() => import("../components/hello").then((mod) => mod.Hello));
```

### Dynamic library import

```jsx
"use client";
import { useState } from "react";

export default function Search() {
  const [results, setResults] = useState();
  return (
    <input onChange={async (e) => {
      const Fuse = (await import("fuse.js")).default;
      setResults(new Fuse(names).search(e.currentTarget.value));
    }} />
  );
}
```

### Rules

- `ssr: false` only works in Client Components.
- Dynamically importing a Server Component lazy-loads its Client Component children, not the Server Component itself.

---

## MDX

### Setup

```bash
npm install @next/mdx @mdx-js/loader @mdx-js/react @types/mdx
```

```js
// next.config.mjs
import createMDX from "@next/mdx";

const nextConfig = { pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"] };
const withMDX = createMDX({ /* options: { remarkPlugins, rehypePlugins } */ });
export default withMDX(nextConfig);
```

### Required: mdx-components.tsx

```tsx
// mdx-components.tsx (project root)
import type { MDXComponents } from "mdx/types";

export function useMDXComponents(): MDXComponents {
  return {
    h1: ({ children }) => <h1 className="text-4xl font-bold">{children}</h1>,
  };
}
```

### Usage patterns

1. **File-based routing**: Place `page.mdx` directly in `app/` routes.
2. **Import**: Import `.mdx` files as React components in `page.tsx`.
3. **Dynamic**: Use `await import(\`@/content/${slug}.mdx\`)` with `generateStaticParams`.

### Frontmatter via exports

```mdx
export const metadata = { author: "Jane" };

# My Post
```

```tsx
import Post, { metadata } from "@/content/post.mdx";
```

### Plugins (Turbopack compatible)

```js
const withMDX = createMDX({
  options: {
    remarkPlugins: ["remark-gfm", ["remark-toc", { heading: "Contents" }]],
    rehypePlugins: ["rehype-slug"],
  },
});
```

### Experimental Rust MDX compiler

```js
module.exports = withMDX({ experimental: { mdxRs: true } });
```

---

## Draft Mode

Preview unpublished CMS content without rebuilding. Sets a cookie that switches pages from static to dynamic rendering.

### Enable via Route Handler

```ts
// app/api/draft/route.ts
import { draftMode } from "next/headers";
import { redirect } from "next/navigation";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const secret = searchParams.get("secret");
  const slug = searchParams.get("slug");

  if (secret !== process.env.DRAFT_SECRET || !slug) {
    return new Response("Invalid token", { status: 401 });
  }

  const draft = await draftMode();
  draft.enable();
  redirect(slug);
}
```

### Consume in pages

```tsx
import { draftMode } from "next/headers";

export default async function Page() {
  const { isEnabled } = await draftMode();
  const url = isEnabled ? "https://draft.cms.com" : "https://published.cms.com";
  const data = await (await fetch(url)).json();
  return <h1>{data.title}</h1>;
}
```

---

## Analytics & Web Vitals

### useReportWebVitals

```tsx
// app/_components/web-vitals.tsx
"use client";
import { useReportWebVitals } from "next/web-vitals";

export function WebVitals() {
  useReportWebVitals((metric) => {
    // metric.name: TTFB, FCP, LCP, FID, CLS, INP
    const body = JSON.stringify(metric);
    if (navigator.sendBeacon) navigator.sendBeacon("/analytics", body);
    else fetch("/analytics", { body, method: "POST", keepalive: true });
  });
}
```

Include `<WebVitals />` in root layout. The component must be `"use client"`.

### Client instrumentation

`instrumentation-client.js` runs before frontend code starts. Ideal for global error tracking or analytics init:

```js
// instrumentation-client.js
window.addEventListener("error", (event) => reportError(event.error));
```

---

## Package Bundling

### Bundle analysis

Turbopack: `npx next experimental-analyze` (v16.1+, interactive UI with import tracing).
Webpack: `ANALYZE=true npm run build` (with `@next/bundle-analyzer`).

### optimizePackageImports

Auto-resolves only used exports from large libraries (icon libraries, etc.):

```js
// next.config.js
module.exports = {
  experimental: {
    optimizePackageImports: ["lucide-react", "@heroicons/react"],
  },
};
```

Many popular libraries are optimized automatically by Next.js.

### serverExternalPackages

Opt specific packages out of server-side bundling (resolved at runtime from `node_modules`):

```js
module.exports = { serverExternalPackages: ["sharp"] };
```

### transpilePackages

Transpile packages that ship untranspiled source (monorepo packages, ESM-only deps):

```js
module.exports = { transpilePackages: ["@acme/ui", "lodash-es"] };
```

### Move heavy rendering to Server Components

If a library only transforms data into static HTML (syntax highlighting, charts, markdown), render it in a Server Component so the library never enters the client bundle.

---

## Third-Party Libraries (@next/third-parties)

Optimized loading wrappers for common third-party scripts.

```bash
npm install @next/third-parties@latest
```

### Google Tag Manager

```tsx
import { GoogleTagManager } from "@next/third-parties/google";
// In root layout:
<GoogleTagManager gtmId="GTM-XYZ" />

// Send events:
import { sendGTMEvent } from "@next/third-parties/google";
sendGTMEvent({ event: "buttonClicked", value: "xyz" });
```

### Google Analytics

```tsx
import { GoogleAnalytics } from "@next/third-parties/google";
<GoogleAnalytics gaId="G-XYZ" />

import { sendGAEvent } from "@next/third-parties/google";
sendGAEvent("event", "buttonClicked", { value: "xyz" });
```

### Google Maps Embed

```tsx
import { GoogleMapsEmbed } from "@next/third-parties/google";
<GoogleMapsEmbed apiKey="XYZ" height={200} width="100%" mode="place" q="Brooklyn+Bridge,New+York,NY" />
```

### YouTube Embed

Uses `lite-youtube-embed` for fast loading:

```tsx
import { YouTubeEmbed } from "@next/third-parties/google";
<YouTubeEmbed videoid="ogfYd705cRs" height={400} params="controls=0" />
```

---

## AI Agents & MCP

### AGENTS.md

Next.js 16+ bundles version-matched docs at `node_modules/next/dist/docs/`. `create-next-app` generates `AGENTS.md` to direct AI coding agents to these docs instead of stale training data.

### MCP (Model Context Protocol)

Next.js 16+ exposes `/_next/mcp` in dev. Install `next-devtools-mcp` for agent access:

```json
// .mcp.json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    }
  }
}
```

**Capabilities** provided to agents:
- `get_errors`: Build, runtime, and type errors from dev server.
- `get_logs`: Development log file path.
- `get_page_metadata`: Routes, components, rendering info per page.
- `get_project_metadata`: Project structure, config, dev server URL.
- `get_server_action_by_id`: Source file and function name for a Server Action.
- Next.js knowledge base queries, migration/upgrade tools, Playwright browser testing integration.

---

## Backend for Frontend

### Route Handlers

Public HTTP endpoints in `app/**/route.ts`. Support all HTTP methods, any content type.

```ts
// app/api/route.ts
export async function POST(request: Request) {
  try {
    const data = await request.json();
    // process...
    return Response.json({ ok: true });
  } catch {
    return new Response("Error", { status: 500 });
  }
}
```

### Content negotiation

Serve different content types from the same URL using rewrites with header matching:

```js
// next.config.js
async rewrites() {
  return [{
    source: "/docs/:slug*",
    destination: "/docs/md/:slug*",
    has: [{ type: "header", key: "accept", value: "(.*)text/markdown(.*)" }],
  }];
}
```

### Proxy pattern

Use `proxy.js` (one per project) for request interception: authentication, redirects, rewrites.

### Webhooks

Route Handlers work well for receiving webhook events (CMS revalidation, auth callbacks).

### Key caveats

- Do not fetch Route Handlers from Server Components (extra HTTP round trip). Access data sources directly.
- Server Actions are queued/sequential; use Route Handlers for data fetching.
- In `export` mode, only `GET` handlers with `dynamic = "force-static"` are supported.

---

## Custom Server

Programmatically start Next.js from a Node.js HTTP server. Only use when the built-in router cannot meet requirements.

```ts
// server.ts
import { createServer } from "http";
import next from "next";

const app = next({ dev: process.env.NODE_ENV !== "production" });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer((req, res) => handle(req, res)).listen(3000);
});
```

**Trade-offs**: Loses Automatic Static Optimization. Not compatible with standalone output mode. The file is not processed by the Next.js compiler.

---

## Architecture

### Next.js Compiler (SWC)

Rust-based compiler using SWC. 17x faster than Babel, default since v12. Handles transpilation and minification (replaced Terser in v13).

**Supported transforms** (via `next.config.js`):

| Feature | Config key |
|---------|-----------|
| Styled Components | `compiler.styledComponents` |
| Emotion | `compiler.emotion` |
| Relay | `compiler.relay` |
| Remove `data-test` props | `compiler.reactRemoveProperties` |
| Remove `console.*` | `compiler.removeConsole` |
| Define build-time variables | `compiler.define` / `compiler.defineServer` |
| Legacy decorators | `tsconfig.json` `experimentalDecorators` |
| JSX import source | `tsconfig.json` `jsxImportSource` |
| Jest | `next/jest` auto-config |
| Module transpilation | `transpilePackages` |
| Build lifecycle hooks | `compiler.runAfterProductionCompile` |

Falls back to Babel if a `.babelrc` is present.

### Fast Refresh

Hot module reloading for React components. Preserves state for function components and hooks.

**Behavior**:
- Editing a file with only React exports: updates that component only.
- Editing a shared module: re-runs it and all importers.
- Editing a file imported outside the React tree: full reload.

**Tips**:
- Add `// @refresh reset` to force remount on every edit.
- State is not preserved for class components or anonymous default exports.
- Hooks with dependencies always re-run during Fast Refresh.

### Accessibility

Built-in features:
- **Route announcer**: Announces page changes to screen readers on client-side transitions (reads `document.title`, then `<h1>`, then pathname).
- **ESLint a11y**: `eslint-plugin-jsx-a11y` included by default (aria-props, role-has-required-aria-props, etc.).
