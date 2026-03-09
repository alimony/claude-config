# Sentry: Fundamentals
Based on Sentry documentation (docs.sentry.io).

## Core Concepts

### What Sentry Is

Sentry is a developer-first error tracking and performance monitoring platform. It captures errors, traces performance, records session replays, collects logs, and tracks metrics — all connected through distributed tracing.

### Key Terms

| Term | Definition |
|------|-----------|
| **DSN** (Data Source Name) | Connection string that tells the SDK where to send events. Associates data with the correct project. Found in project settings. |
| **Event** | A single data payload sent to Sentry (error, transaction, etc.). |
| **Issue** | A group of similar events deduplicated by fingerprint. One issue may contain thousands of events. |
| **Transaction** | A single instance of a service being called, representing a unit of work (e.g., a page load or API request). Contains spans. |
| **Span** | A timed operation within a transaction. Spans nest to form a trace tree. |
| **Trace** | The full journey of a request across services. Composed of transactions and spans linked by a trace ID. |
| **Scope** | Holds contextual data (user, tags, breadcrumbs) attached to events. Scopes can be global or local. |
| **Breadcrumb** | A timestamped log of actions leading up to an event (clicks, navigations, console logs). |
| **Release** | A version of your deployed code. Links errors to commits and enables regression detection. |
| **Environment** | A label (production, staging, dev) for organizing issues, releases, and user feedback. |
| **Fingerprint** | The rule used to group events into issues. Sentry auto-generates fingerprints but they can be customized. |
| **Envelope** | The transport format wrapping one or more items (events, attachments, sessions) sent to Sentry. |
| **Sample Rate** | Controls what percentage of data is captured and sent. Reduces volume and cost. Applies to traces, replays, logs, etc. |
| **Extrapolation** | Sentry's method to provide accurate aggregate metrics from sampled data, so dashboards remain reliable even at low sample rates. |

### Data Flow

```
Your App (SDK) --> Envelope --> Sentry Relay --> Ingest Pipeline --> Storage
                                    |
                            Filtering / Sampling
                            Rate Limiting
                            PII Scrubbing
```

1. The SDK captures an event (error, transaction, log, etc.)
2. Events are packaged into envelopes and sent to your DSN endpoint
3. Sentry Relay receives, filters, scrubs PII, applies rate limits
4. Data enters the ingest pipeline for processing and storage
5. Issues are created/updated, alerts evaluated, dashboards refreshed

### Data Management

- **Inbound Filters** — Server-side rules to drop events before they count against quota (filter browser extensions, legacy browsers, specific error messages)
- **Size Limits** — Events and attachments have maximum size constraints; oversized payloads are rejected
- **Issue Grouping** — Events are grouped into issues via fingerprinting algorithms; customize with fingerprint rules or SDK-side `beforeSend`

## Error Monitoring

### Capturing Errors

SDKs automatically capture unhandled exceptions. For handled exceptions, capture explicitly:

```javascript
try {
  await processOrder(order);
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      order_id: order.id,
      payment_method: order.paymentMethod,
    },
    level: "error",
  });
}
```

### Error Severity Levels

`fatal` > `error` > `warning` > `info` > `debug`

Use the appropriate level — not everything is an `error`.

### Adding Context

**Set user globally** so every event includes identity:

```javascript
Sentry.setUser({ id: user.id, email: user.email });
```

**Tags** — Searchable key-value pairs for high-cardinality data (IDs, regions, feature flags). Set via `Sentry.setTag()` or inline on `captureException`.

**Breadcrumbs** — Automatic trail of user actions before the error. SDKs capture console logs, clicks, navigations, and network requests by default.

### Noise Reduction

- Use `ignoreErrors` to suppress known non-actionable errors (browser extensions, third-party scripts)
- Use `beforeSend` hook to filter or modify events before transmission
- Set up inbound filters in project settings for server-side filtering

### Recommended Issue Views

| View | How to Find It |
|------|---------------|
| High-volume issues | Sort by event count — catches widespread bugs and infinite loops |
| New issues after deploy | Filter `firstRelease:v1.2.3` — catches regressions |
| Environment-specific | Filter by environment — spots config problems |
| High user impact | Sort by unique users, not event count |
| User-reported issues | Enable User Feedback Widget — captures user-submitted reports |

## Tracing & Performance

### Automatic Instrumentation

With `browserTracingIntegration()`, Sentry auto-captures:
- Page loads and navigation
- Fetch/XHR requests
- Long animation frames
- Resource loading

Backend SDKs auto-instrument HTTP handlers, database queries, and framework operations.

### Custom Spans

Add spans where auto-instrumentation misses business logic:

```javascript
Sentry.startSpan(
  { name: "checkout.process", op: "user.action" },
  async (span) => {
    span.setAttribute("cart.itemCount", cart.items.length);
    span.setAttribute("user.tier", user.subscriptionTier);
    await processCheckout(cart);
  },
);
```

Numeric attributes become queryable metrics (`sum()`, `avg()`, `p90()`) in Trace Explorer.

### Span Operation Conventions

| Use Case | `op` Value | Key Attributes |
|----------|-----------|----------------|
| User interactions | `user.action` | cart.itemCount, user.tier |
| External APIs | `http.client` | http.url, http.status_code, response.timeMs |
| Database queries | `db.query` | query.type, query.dateRange, result.rowCount |
| Background jobs | `queue.process` | job.type, job.id, queue.name, job.status |
| AI/LLM operations | `ai.inference` | ai.model, ai.feature, ai.tokens.total |

### Key Performance Queries

| What to Find | Query | Metric | Threshold |
|--------------|-------|--------|-----------|
| Slow page loads | `span.op:pageload` | `p90(span.duration)` | > 3s |
| Slow APIs | `span.op:http.client` | `avg(span.duration)` | > 1s avg or > 2s p95 |
| UI jank | `span.op:ui.long-animation-frame` | `span.duration` | > 200ms |
| SPA navigation | `span.op:navigation` | `p90(span.duration)` | > 1s |
| Heavy resources | `span.op:resource.script` | `avg(span.duration)` | > 1s |

**Always use p75/p90/p95 instead of averages** — averages hide outliers.

### Every Error Is Trace-Connected

Every error in Sentry is automatically linked to its trace, so you can navigate from an error to the full execution context (what API calls happened, what queries ran, how long each took).

## Structured Logging

### Log Levels

`trace` > `debug` > `info` > `warn` (`warning` in Python) > `error` > `fatal`

Use verbose levels (debug, trace) in development. Filter to info+ in production.

### Emitting Logs

```javascript
Sentry.logger.info("Order completed", {
  orderId: "order_123",
  userId: user.id,
  amount: 149.99,
  paymentMethod: "stripe",
});
```

Logs are automatically trace-connected — each includes a trace ID linking to the full trace view.

### What to Log

1. **Authentication events** — login success/failure, MFA, OAuth errors
2. **Payment processing** — attempts, failures, gateway responses
3. **External API / async operations** — webhooks, third-party responses, durations
4. **Background jobs** — execution, failures, retries (outside normal request context)
5. **Feature flags / config changes** — flag evaluations, config updates after deploys

### Production Best Practice

Consolidate related data into single structured log entries rather than many small logs. Use `beforeSendLog` to filter verbose levels in production.

### Log Drains

For environments without SDK access, use log drains from Vercel, Cloudflare Workers, Heroku, Supabase, or forwarding via OpenTelemetry Collector, Vector, Fluent Bit.

## Metrics

### Metric Types

| Type | Method | Use For |
|------|--------|---------|
| Counter | `Sentry.metrics.count()` | Events that happen (orders, clicks, errors) |
| Gauge | `Sentry.metrics.gauge()` | Current state (queue depth, connections) |
| Distribution | `Sentry.metrics.distribution()` | Values that vary (latency, sizes, amounts) |

### Emitting Metrics

```javascript
// Counter
Sentry.metrics.count("checkout.failed", 1, {
  attributes: { user_tier: "premium", failure_reason: "payment_declined" },
});

// Gauge
Sentry.metrics.gauge("queue.depth", await queue.size(), {
  attributes: { queue_name: "notifications" },
});

// Distribution
Sentry.metrics.distribution("api.latency", responseTimeMs, {
  unit: "millisecond",
  attributes: { endpoint: "/api/orders" },
});
```

### High-Value Metric Patterns

1. **Business events** — checkouts, conversions, signups (counters)
2. **Application health** — success/failure rates for operations (counters)
3. **Resource utilization** — pool sizes, queue depths, polled ~30s (gauges)
4. **Latency & performance** — response times using p90/p95/p99 (distributions)
5. **Business values** — order totals, file sizes, batch counts (distributions)

All metrics are trace-connected — drill from metric spikes into underlying traces.

## Session Replay

### What It Captures

- User interactions (clicks, navigation, form inputs)
- Network activity (API calls, response codes, timing)
- Console output (warnings, errors, debug messages)
- URL changes and route transitions

### Privacy

**All text content, user input, and images are masked by default.** Selectively unmask specific elements with the `data-sentry-unmask` attribute. Keep form inputs masked.

### Key Use Cases

- **Error root cause** — see what the user did before the crash
- **Bug reproduction** — exact interaction sequence for reported issues
- **Click quality** — detect rage clicks (repeated futile clicks) and dead clicks (non-functional elements)
- **Performance analysis** — identify slow interactions and delayed visual feedback

### Useful Replay Filters

- `count_errors:>0` — sessions with errors
- `count_rage_clicks:>0` — frustrated users
- `user.email:jane@example.com` — specific user sessions

## Search Syntax

### Query Structure

```
key:value key:value "raw search text"
```

Each `key:value` pair is a token. Raw text at the end searches event titles/messages using CONTAINS matching.

### Operators

| Operator | Example |
|----------|---------|
| Exact match | `browser:Chrome` |
| Negation | `!browser:Chrome` |
| Greater/less than | `event.timestamp:>2024-01-01` |
| Duration comparison | `transaction.duration:>5s` |
| Wildcards | `browser:"Safari 11*"` |
| Multiple values (OR) | `browser:[Chrome, Opera]` |
| Logical OR | `browser:Chrome OR browser:Opera` |
| Grouping | `x AND (y OR z)` |

`AND` has higher precedence than `OR`. Use parentheses for complex queries.

### Reserved Keywords

- `is:resolved`, `is:unresolved`, `is:ignored` — issue state
- `assigned:me`, `assigned:team-slug` — assignment
- `firstRelease:VERSION` — first seen in release

### Page Filters

Project, environment, and date range filters persist during navigation and apply across views.

## OpenTelemetry (OTLP)

Sentry accepts OpenTelemetry traces and logs via OTLP endpoints (open beta). Metrics are not yet supported.

### Ingestion Methods

1. **Direct export** — OTel SDKs send directly to Sentry
2. **Forwarding** — Route through OTel Collector, Vector, or Fluent Bit (use Sentry Exporter for multi-project routing)
3. **Log/trace drains** — Managed platforms (Vercel, Cloudflare, Heroku)

### Combining Sentry SDK + OTel

- Frontend-to-backend: use `propagateTraceparent` to link frontend traces with OTel-instrumented backends
- Same service: OTLP Integration shares trace context between Sentry and OTel within one service

## Onboarding Checklist

1. **Create project, enable tracing + replay** — get the DSN
2. **Upload source maps / debug symbols** — readable stack traces are essential
3. **Set environment and release** — `environment: "production"`, `release: "v1.2.3"`
4. **Connect source control** (GitHub) — suspect commits, stack trace links, code owners
5. **Connect messaging** (Slack/Discord) — severity-based alerts, resolve from chat
6. **Connect issue tracker** (Jira/Linear) — sync issue statuses, flag regressions
7. **Set auto-resolve to 2 weeks** — recommended for optimal issue and regression tracking
8. **Configure sample rates** — balance data volume with cost
9. **Set up alerts** — don't rely on checking the dashboard manually
10. **Customize dashboards and saved searches** — tailor to your application's needs

