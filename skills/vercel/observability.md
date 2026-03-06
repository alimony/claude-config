# Vercel: Observability & Monitoring
Based on Vercel documentation.

## Overview

Vercel provides a layered observability stack for monitoring infrastructure, application performance, and visitor behavior:

| Tool | Purpose | Plan |
|------|---------|------|
| **Observability** | Infrastructure metrics (functions, edge requests, APIs, middleware) | All plans (limited) |
| **Observability Plus** | Extended retention, granular data, monitoring, notebooks | Pro/Enterprise ($10/mo base) |
| **Web Analytics** | Visitor tracking (pages, referrers, demographics) | All plans |
| **Speed Insights** | Real-user Core Web Vitals performance | All plans |
| **Logs** | Build, runtime, activity, and audit logs | All plans (retention varies) |
| **Drains** | Export logs, traces, analytics, speed insights to external services | Pro/Enterprise |
| **Notebooks** | Save and organize observability queries | Observability Plus |

## Observability

### Tracked Events

Each request to Vercel generates one or more events:

- **Edge Requests** -- cached responses, static assets
- **Vercel Function Invocations** -- serverless function executions
- **External API Requests** -- outbound calls from functions
- **Middleware Invocations** -- routing middleware executions
- **AI Gateway Requests** -- proxied AI model calls

A single user request can generate 1 event (cached) to 6+ events (middleware + function + external APIs + AI gateway).

### Available Insight Sections

| Section | Team | Project | Key Metrics |
|---------|------|---------|-------------|
| Vercel Functions | Y | Y | Invocations, error rate, CPU throttling, latency (Plus) |
| External APIs | Y | Y | Requests, p75 duration, error rate (Plus) |
| Edge Requests | Y | Y | Requests, regions, cache hits, bot breakdown (Plus) |
| Middleware | Y | Y | Invocations, actions, rewrites (Plus) |
| Fast Data Transfer | Y | Y | Data transfer volume, breakdown by path (Plus) |
| Image Optimization | Y | Y | Transformations, bandwidth savings, formats |
| ISR | Y | Y | Revalidations, cache hit ratio, duration (Plus) |
| Blob | Y | - | Downloads, cache, API operations |
| Build Diagnostics | - | Y | Build time, step breakdown |
| AI Gateway | Y | Y | Requests by model, TTFT, token counts, cost |
| Queues | - | Y | Throughput, message age, consumer performance |
| External Rewrites | Y | Y | Rewrite counts, latency (Plus) |

### Observability Plus

Optional upgrade for Pro/Enterprise. Base fee: **$10/month** (prorated). Additional events billed per use.

| Feature | Free | Plus |
|---------|------|------|
| Data retention | Hobby: 12h, Pro: 1d, Enterprise: 3d | **30 days** |
| Runtime log retention | Hobby: 1h, Pro: 1d, Enterprise: 3d | **30 days** (14-day window) |
| Function latency (p75) | No | Yes |
| Breakdown by path | No | Yes |
| External API sorting/filtering | Limited | Full |
| Monitoring access | No | Included |
| Notebooks | No | Yes |

Enable: Dashboard > Observability > Upgrade to Observability Plus.

## Web Analytics

Privacy-friendly visitor analytics. No cookies -- visitors identified by a daily-reset hash.

### Key Metrics
- **Visitors** -- unique visitors (hash-based, resets daily)
- **Page Views** -- total page loads (same visitor counted multiple times)
- **Bounce Rate** -- % of single-page sessions
- **Panels** -- top pages, referrers, countries, OS, browser, device, custom events

Bot traffic is automatically excluded via User-Agent inspection.

### Setup

1. Enable in Dashboard > Project > Analytics > Enable
2. Install the package and add the component:

```bash
npm i @vercel/analytics
```

**Next.js (App Router):**
```tsx
// app/layout.tsx
import { Analytics } from '@vercel/analytics/next';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

**React / Remix:** `import { Analytics } from '@vercel/analytics/react'` (or `/remix`)

**SvelteKit:**
```js
// src/routes/+layout.js
import { injectAnalytics } from '@vercel/analytics/sveltekit';
injectAnalytics({ mode: dev ? 'development' : 'production' });
```

**Vue / Nuxt:** `import { Analytics } from '@vercel/analytics/vue'`

**Astro:** `import Analytics from '@vercel/analytics/astro'` (in head)

**Plain HTML:**
```html
<script>
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
</script>
<script defer src="/_vercel/insights/script.js"></script>
```

3. Deploy and verify `/_vercel/insights/view` requests in browser Network tab.

## Speed Insights

Real-user performance monitoring based on Core Web Vitals. Uses actual visitor data, not lab simulations.

### Core Web Vitals

| Metric | What It Measures | Good Target |
|--------|-----------------|-------------|
| **LCP** (Largest Contentful Paint) | Time until largest visible content renders | <= 2.5s |
| **CLS** (Cumulative Layout Shift) | Visual stability (layout shift fraction) | <= 0.1 |
| **INP** (Interaction to Next Paint) | Responsiveness to user interaction | <= 200ms |
| **FCP** (First Contentful Paint) | Time until first DOM content renders | <= 1.8s |
| **TTFB** (Time to First Byte) | Server response time | < 800ms |
| **FID** (First Input Delay) | Delay before browser responds to first interaction | <= 100ms |
| **TBT** (Total Blocking Time) | Main thread blocking between FCP and TTI | < 800ms |

### Score Interpretation
- **90-100 (green):** Good
- **50-89 (orange):** Needs improvement
- **0-49 (red):** Poor

Default percentile is P75. Dashboard also shows P90, P95, P99. Data points collected: up to 6 per visit (TTFB, FCP on load; FID, LCP on interaction; INP, CLS on leave).

### Setup

1. Enable in Dashboard > Project > Speed Insights > Enable
2. Install and add the component:

```bash
npm i @vercel/speed-insights
```

**Next.js / React / Remix / Vue / Nuxt / Astro:**
```tsx
import { SpeedInsights } from '@vercel/speed-insights/react'; // or /next, /remix, /vue
// Add <SpeedInsights /> to your root layout/component
```

**SvelteKit:**
```js
import { injectSpeedInsights } from '@vercel/speed-insights/sveltekit';
injectSpeedInsights();
```

**Plain HTML:**
```html
<script>
  window.si = window.si || function () { (window.siq = window.siq || []).push(arguments); };
</script>
<script defer src="/_vercel/speed-insights/script.js"></script>
```

3. Deploy and verify `/_vercel/speed-insights/script.js` in page source.

## Logs

### Log Types

| Type | Purpose | Retention |
|------|---------|-----------|
| **Build Logs** | Deployment progress, errors, dependency info | Stored per deployment |
| **Runtime Logs** | Function execution output, searchable | Hobby: 1h, Pro: 1d, Enterprise: 3d (Plus: 30d) |
| **Activity Logs** | Chronological account events (env vars, deploys) | Account-level |
| **Audit Logs** | Who did what and when (Enterprise) | Exportable, 90 days CSV |

### Runtime Log Search
Search and filter runtime logs from Dashboard > Project > Deployments. For longer retention, use Log Drains.

## Debugging Production 500 Errors

### Quick Workflow (CLI)

```bash
# 1. Find 500 errors
vercel logs --environment production --status-code 5xx --since 1h

# 2. Get structured data for filtering
vercel logs --environment production --status-code 500 --json --since 1h \
  | jq '{path: .path, message: .message, timestamp: .timestamp}'

# 3. Search by error message
vercel logs --environment production --query "Cannot read properties" --since 1h --expand

# 4. Narrow time range
vercel logs --environment production --status-code 500 --since 2h --until 1h

# 5. Find specific request
vercel logs --request-id req_xxxxx --expand

# 6. Identify failing deployment
vercel list --prod
vercel inspect <deployment-url>
vercel inspect <deployment-url> --logs  # build logs

# 7. Correlate with code
git log --oneline -10
git show <commit-sha> --stat
```

### Fix and Verify

```bash
# Deploy preview
vercel deploy

# Test the failing route (handles deployment protection)
vercel curl /api/failing-route --deployment <preview-url>

# Check for errors in preview
vercel logs --deployment <preview-deployment-id> --level error

# Ship to production
vercel deploy --prod

# Confirm fix
vercel logs --environment production --status-code 500 --since 5m
```

### Emergency Tools

```bash
# Binary search for regression across deployments
vercel bisect --good <good-url> --bad <bad-url> --path /api/failing-route

# Instant rollback to previous deployment
vercel rollback
vercel rollback status
```

### Common 500 Error Causes
- Unhandled null/undefined from API responses
- Missing environment variables
- Database connection failures
- Type mismatches after dependency updates

## Notebooks

Notebooks organize multiple observability queries into shareable collections. Requires Observability Plus.

- **Personal Notebooks** -- visible only to creator
- **Team Notebooks** -- shared via the Share button, editable by all team members
- Each query has its own filters, time ranges, and aggregations
- Views: line chart, volume chart, table, or big number

Create: Dashboard > Observability > Notebooks > Create Notebook > add queries with the query builder.

## Drains

Forward observability data to external services. Pro and Enterprise only.

### Data Types

| Schema | Format | Integrations |
|--------|--------|-------------|
| `log` (v1) | JSON, NDJSON | Custom endpoint + native integrations (Dash0, etc.) |
| `trace` (v1) | JSON, Protobuf (OTLP/HTTP) | Custom endpoint + native integrations (Braintrust, etc.) |
| `speed_insights` (v1) | JSON, NDJSON | Custom endpoint only |
| `analytics` (v1) | JSON, NDJSON | Custom endpoint only |

### Configuration

1. Dashboard > Team Settings > Drains > Add Drain
2. Choose data type (logs, traces, speed insights, web analytics)
3. Select projects (all or specific)
4. Configure sampling rules (environment, percentage, path prefix)
5. Set destination: custom HTTPS endpoint or native integration

### Sampling Rules
- Rules evaluated top-to-bottom; first match wins, unmatched requests dropped
- Default (no rules): 100% forwarded
- Example: 100% production during launch, then reduce to 10%

### Security
- Verify `x-vercel-signature` header against your secret
- Add custom headers for auth, routing, or identification

### Error Handling
If >80% of deliveries fail or >50 failures in the past hour, Vercel sends a notification email and flags the drain as errored. You can pause, resume, or delete drains from settings.

### Logs and Traces Correlation
When tracing is enabled, logs are automatically enriched with `traceId` and `spanId` fields -- no code changes needed.

## Common Pitfalls

1. **Assuming Observability = full data on free tier.** Latency breakdown, path filtering, and extended retention require Observability Plus.
2. **Not setting up drains for long-term storage.** Default log retention is short (1 hour on Hobby). Use drains to persist data externally.
3. **Ignoring CPU throttling metrics.** Low throttling (<10%) is normal. High throttling causes latency and timeouts -- increase function memory or optimize code.
4. **Forgetting to deploy after enabling analytics.** Web Analytics and Speed Insights add routes (`/_vercel/insights/*`, `/_vercel/speed-insights/*`) that only appear after the next deployment.
5. **Over-draining in production.** Without sampling rules, drains forward 100% of data. Set sampling rates to control volume and cost.
6. **Monitoring sunset.** Monitoring as a standalone product is sunset for Pro plans. Use Observability Plus for equivalent query capabilities.
