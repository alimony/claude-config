# Sentry: Tracing & Performance
Based on Sentry documentation (docs.sentry.io).

## Tracing Concepts

Sentry tracing captures **transactions** (top-level operations like HTTP requests) and **spans** (individual operations within a transaction like DB queries). Together they form a **trace** -- a tree of spans that can cross service boundaries via distributed tracing.

- **Trace**: End-to-end journey across services, identified by a single trace ID.
- **Transaction**: The root span of a trace within one service. Auto-created by framework integrations (e.g., Django request, Express route).
- **Span**: A timed operation within a transaction (e.g., DB query, HTTP call, function execution). Spans have a name, op (operation type), duration, attributes, and status.
- **Head-based sampling**: The originating service decides whether to sample. The decision propagates downstream via headers.

## SDK Setup

### Python

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    send_default_pii=True,
    traces_sample_rate=1.0,  # 0.0 to 1.0 -- capture this fraction of traces
)
```

### JavaScript (Browser)

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  integrations: [Sentry.browserTracingIntegration()],
  tracesSampleRate: 1.0,
  tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
});
```

### Sampling Options

- **`traces_sample_rate` / `tracesSampleRate`**: Uniform rate between 0 and 1.
- **`traces_sampler` / `tracesSampler`**: Function returning 0-1 for context-aware sampling. Takes precedence over the rate if both are set.
- To **disable tracing**, omit both options entirely. Setting rate to 0 still processes traces -- it just discards them.

## Automatic Instrumentation

### Python Auto-Instrumented

| Category | Libraries/Frameworks |
|----------|---------------------|
| Web frameworks (WSGI) | Django, Flask, Pyramid, Falcon, Bottle |
| Web frameworks (ASGI) | FastAPI, Starlette, Quart, Tornado, AIOHTTP |
| Task queues | Celery, Redis Queue (RQ) |
| Database | SQLAlchemy, Django ORM |
| HTTP clients | requests, HTTPX, stdlib |
| Other | Redis, subprocess calls |

Spans are only created within an existing transaction. If your framework is not auto-instrumented, you must create transactions manually.

### JavaScript Auto-Instrumented (Browser)

With `browserTracingIntegration()` enabled:
- Page loads and navigation transitions
- Fetch/XHR network requests
- Long animation frames (main thread blocking)
- Resource loading (scripts, stylesheets, images)

## Custom Instrumentation -- Python

### Context Manager (Recommended)

```python
import sentry_sdk

# Top-level transaction (when no auto-transaction exists)
with sentry_sdk.start_transaction(op="task", name="process-order"):
    # Nested span
    with sentry_sdk.start_span(name="validate-items"):
        validate(order.items)
    with sentry_sdk.start_span(name="charge-payment"):
        charge(order.payment)
```

### Decorator

```python
@sentry_sdk.trace
def process_payment(order):
    ...

# With custom op and attributes (SDK 2.35.0+)
@sentry_sdk.trace(op="payment", name="charge", attributes={"provider": "stripe"})
def charge(payment_info):
    ...
```

When decorating a `@staticmethod` or `@classmethod`, put `@sentry_sdk.trace` **after** (below) the other decorator.

### Manual Start/Finish

```python
span = sentry_sdk.start_span(name="send-email")
send_email(user)
span.finish()  # Must call finish() or span is not sent
```

### Nested Spans

```python
parent = sentry_sdk.start_span(name="import-data")
child = parent.start_child(name="parse-csv")
parse_csv(data)
child.finish()
parent.finish()
```

### Adding Context

```python
span = sentry_sdk.get_current_span()
if span is not None:
    span.set_tag("order_id", order.id)
    span.set_data("item_count", len(order.items))

# Bulk update current span
sentry_sdk.update_current_span(
    op="db.query",
    name="fetch-user",
    attributes={"user_id": user_id},
)
```

Attribute values must be primitive types (`int`, `float`, `bool`, `str`) or homogeneous lists of primitives.

### Centralized Function Tracing

```python
sentry_sdk.init(
    dsn="...",
    functions_to_trace=[
        {"qualified_name": "myapp.services.process_order"},
        {"qualified_name": "myapp.models.User.save"},
    ],
)
```

## Custom Instrumentation -- JavaScript

### startSpan (Recommended)

Auto-finishes when callback completes. Works with sync and async:

```javascript
const result = await Sentry.startSpan(
  { name: "process-order", op: "task" },
  async (span) => {
    span.setAttribute("order.itemCount", 5);
    const res = await processOrder(orderId);
    return res;
  }
);
```

### startSpanManual

For spans whose lifetime does not match a callback:

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

### startInactiveSpan

Creates a span without making it the active parent:

```javascript
const span = Sentry.startInactiveSpan({ name: "background-sync" });
doWork();
span.end();
```

### Span Options

| Option | Type | Purpose |
|--------|------|---------|
| `name` | string | Span identifier (required) |
| `op` | string | Operation category (e.g. `http.client`, `db.query`) |
| `attributes` | Record | Key-value metadata |
| `parentSpan` | Span | Explicit parent (overrides default nesting) |
| `onlyIfParent` | boolean | Skip if no active parent exists |
| `forceTransaction` | boolean | Display as transaction in Sentry UI |

### Adding Attributes and Status

```javascript
const span = Sentry.getActiveSpan();
if (span) {
  span.setAttribute("cache.hit", true);
  span.setAttributes({ "db.rows": 42, "db.table": "users" });
  Sentry.updateSpanName(span, "fetch-users");  // SDK 8.47.0+
  span.setStatus({ code: 1 });  // 0=unknown, 1=ok, 2=error
}
```

### Browser Span Hierarchy

Browsers default to flat hierarchies (all spans are children of root). This prevents misattribution during parallel async operations. Override with `parentSpanIsAlwaysRootSpan: false` in init if you need nesting, but beware of incorrect parent assignment in concurrent code.

## Trace Propagation

Distributed tracing connects spans across services using two HTTP headers:

- **`sentry-trace`**: Contains trace ID, span ID, and sampling decision.
- **`baggage`**: Additional trace metadata (sample rate, environment, etc.).

### How It Works

1. Service A starts a transaction and creates the headers.
2. Outgoing HTTP requests include `sentry-trace` and `baggage`.
3. Service B reads the headers and joins the same trace.
4. The sampling decision from Service A is honored downstream.

### Python

Trace propagation is automatic for supported frameworks (Django, Flask, FastAPI, etc.) on both inbound requests and outbound HTTP calls (requests, HTTPX).

### JavaScript

Control which outbound requests receive trace headers:

```javascript
Sentry.init({
  tracePropagationTargets: [
    "https://api.myapp.com",
    /^\/api\//,  // relative URLs
  ],
});
```

Port numbers matter -- `http://localhost:3000` must be listed explicitly if your backend runs on a specific port. Set to `[]` to disable propagation entirely.

### Server-Rendered Apps

Inject trace context into HTML for the browser SDK to continue the trace:

```html
<meta name="sentry-trace" content="{{sentry_trace}}" />
<meta name="baggage" content="{{baggage}}" />
```

`browserTracingIntegration()` automatically reads these meta tags.

### CORS

Add `sentry-trace` and `baggage` to your CORS allowlist so they are not stripped by proxies, gateways, or firewalls.

## OpenTelemetry Integration

### Using OTel SDK with Sentry (Python)

```bash
pip install "sentry-sdk[opentelemetry]"
```

```python
import sentry_sdk
from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.trace import TracerProvider
from sentry_sdk.integrations.opentelemetry import SentrySpanProcessor, SentryPropagator

sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    instrumenter="otel",  # Disables native Sentry instrumentation
)

provider = TracerProvider()
provider.add_span_processor(SentrySpanProcessor())
trace.set_tracer_provider(provider)
set_global_textmap(SentryPropagator())

# Create spans using OTel API
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my-operation"):
    do_work()
```

Setting `instrumenter="otel"` tells the Sentry SDK to defer to OpenTelemetry for span creation. The first span sent through `SentrySpanProcessor` becomes the transaction.

### OTLP Direct Export

Sentry ingests OpenTelemetry traces and logs via OTLP endpoints directly from OTel SDKs or through the OpenTelemetry Collector. OTLP metrics are not supported. This allows sending traces to Sentry without using the Sentry SDK at all.

Pipeline tools supported: OpenTelemetry Collector, Vector, Fluent Bit.

## Performance Insights UI

Sentry Insights provides performance monitoring across application layers:

- **Frontend**: Web vitals, network request latency
- **Backend**: Database query performance, outbound API calls, cache hit rates, queue monitoring
- **Mobile**: App starts, screen loads, rendering health
- **AI**: LLM/inference operation metrics

### Querying Traces

Use the Trace Explorer with span-based filters:

```
span.op:http.client                    # Filter by operation type
span.duration:>500ms                   # Slow spans
span.description:"GET /api/users"      # Specific operations
transaction:"POST /checkout"           # By transaction name
```

Aggregation functions: `avg(span.duration)`, `p75(span.duration)`, `p90(span.duration)`, `p95(span.duration)`, `max(span.duration)`.

Group by `transaction`, `span.description`, or custom attributes for pattern analysis. Prefer p75/p90/p95 over averages -- averages hide outliers.

### Alerts from Traces

Build a query in Explore > Traces, click "Save As - Alert", choose threshold type (Static, Percent Change, or Anomaly detection), and configure notification routing.

## Profiling (Python)

Profiling samples call stacks to identify hot code paths. Requires tracing to be enabled.

### Continuous Profiling (SDK 2.24.1+)

**Trace lifecycle** -- profiler runs automatically while spans are active:

```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)
```

**Manual lifecycle** -- explicit control:

```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="manual",
)

sentry_sdk.profiler.start_profiler()
# ... code to profile ...
sentry_sdk.profiler.stop_profiler()
```

### Transaction-Based Profiling (SDK 1.18.0+)

Profiles run for the duration of a transaction (max 30 seconds):

```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,  # Relative to traces_sample_rate
)
```

Dynamic sampling with `profiles_sampler`:

```python
from sentry_sdk.types import SamplingContext

def profiles_sampler(ctx: SamplingContext) -> float:
    if ctx.get("transaction_context", {}).get("name") == "important-task":
        return 1.0
    return 0.1

sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profiles_sampler=profiles_sampler,
)
```

## Custom Span Naming Conventions

Use consistent `op` values to enable Sentry's built-in visualizations:

| Category | `op` value | Example attributes |
|----------|-----------|-------------------|
| User actions | `user.action` | `cart.itemCount`, `user.tier` |
| HTTP calls | `http.client` | `http.url`, `http.status_code`, `response.timeMs` |
| Database | `db.query` | `query.type`, `result.rowCount`, `db.table` |
| Queue/jobs | `queue.process` | `job.type`, `job.id`, `queue.name` |
| AI/LLM | `ai.inference` | `ai.model`, `ai.tokens.total` |
| Cache | `cache.get` | `cache.hit`, `cache.key` |

Numeric attributes are automatically queryable with aggregation functions (`sum()`, `avg()`, `p90()`).

### AI Span Templates (Python)

```python
from sentry_sdk.consts import SPANTEMPLATE

@sentry_sdk.trace(template=SPANTEMPLATE.AI_AGENT)
def run_agent(prompt):
    ...
```

Available templates: `AI_AGENT`, `AI_TOOL`, `AI_CHAT`.

## Best Practices

### What to Instrument

- **Business-critical flows**: Checkout, signup, search -- the paths that matter most.
- **Third-party API calls**: External dependencies are often the source of latency.
- **Background jobs**: Queue consumers, cron tasks, data pipelines.
- **Database queries with context**: Auto-instrumentation captures queries, but custom spans let you add _why_ a query matters (business context, row counts, date ranges).

### Sampling Strategy

- Start with `traces_sample_rate=1.0` in development and staging.
- In production, reduce to 0.1-0.2 for high-traffic services. Use `traces_sampler` for granular control (e.g., always sample errors, sample health checks at 0%).
- Profile sampling (`profiles_sample_rate`) is relative to the trace sample rate. If traces are at 0.2 and profiles at 0.5, you profile 10% of all requests.

### Avoiding Overhead

- Do not create spans for trivial operations (simple variable assignments, in-memory lookups).
- Keep attribute values small. Avoid attaching large payloads or PII.
- Use `onlyIfParent` (JS) to skip span creation when there is no active trace.
- In production, lower sample rates to control volume and cost.
- Prefer automatic instrumentation. Custom spans are for business logic and third-party calls that the SDK cannot detect.

### Distributed Tracing Checklist

1. Deploy Sentry SDKs in all services that participate in a trace.
2. Ensure `sentry-trace` and `baggage` headers are not stripped (CORS, proxies, firewalls).
3. Use matching DSNs/projects or ensure the same Sentry organization for cross-project traces.
4. Verify `tracePropagationTargets` (JS) includes all backend origins, including port numbers.
