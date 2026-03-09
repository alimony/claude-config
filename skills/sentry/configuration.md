# Sentry: Configuration
Based on Sentry documentation (docs.sentry.io).

## Quick-Reference: SDK Init Options

### Common Options (Python / JavaScript)

| Option (Python) | Option (JS) | Type | Default | Description |
|---|---|---|---|---|
| `dsn` | `dsn` | `str` | — | Where to send events. Required. |
| `debug` | `debug` | `bool` | `False` | Print SDK diagnostic info |
| `release` | `release` | `str` | auto-detected | App version for regression tracking |
| `environment` | `environment` | `str` | `"production"` | Deployment context (production, staging, etc.) |
| `sample_rate` | `sampleRate` | `float` | `1.0` | Error event sample rate (0.0-1.0) |
| `error_sampler` | — | `func` | `None` | Dynamic per-error sampling function (Python only) |
| `max_breadcrumbs` | `maxBreadcrumbs` | `int` | `100` | Max breadcrumbs per event |
| `attach_stacktrace` | `attachStacktrace` | `bool` | `False` | Auto-attach stack traces to messages |
| `send_default_pii` | `sendDefaultPii` | `bool` | `False` | Collect PII (IP addresses, user data) |
| `traces_sample_rate` | `tracesSampleRate` | `float` | `None` | Transaction sample rate (0.0-1.0) |
| `traces_sampler` | `tracesSampler` | `func` | `None` | Dynamic transaction sampling function |
| `profiles_sample_rate` | `profilesSampleRate` | `float` | `None` | Profile sample rate (0.0-1.0) |
| `before_send` | `beforeSend` | `func` | `None` | Modify/drop error events before sending |
| `before_send_transaction` | `beforeSendTransaction` | `func` | `None` | Modify/drop transaction events before sending |
| `before_breadcrumb` | `beforeBreadcrumb` | `func` | `None` | Modify/drop breadcrumbs |
| `ignore_errors` | `ignoreErrors` | `list` | `[]` | Exception classes (Py) or message patterns (JS) to ignore |
| `integrations` | `integrations` | `list` | `[]` | Additional integrations to enable |
| `default_integrations` | `defaultIntegrations` | `bool` | `True` | Enable built-in integrations |
| `send_client_reports` | `sendClientReports` | `bool` | `True` | Send client outcome reports |
| `enable_logs` | `enableLogs` | `bool` | `False` | Enable Sentry structured logs |
| `trace_propagation_targets` | `tracePropagationTargets` | `list` | `['.*']` (Py) | URLs to propagate tracing headers to |
| `auto_session_tracking` | — | `bool` | `True` | Auto-record sessions (Python) |
| `max_value_length` | `maxValueLength` | `int` | `100000` (Py) | Truncate string values beyond this length |
| `shutdown_timeout` | — | `int` | `2` | Seconds to wait for drain on shutdown (Python) |

### JavaScript-Only Options

| Option | Type | Default | Description |
|---|---|---|---|
| `tunnel` | `string` | — | Custom endpoint URL to bypass ad-blockers |
| `normalizeDepth` | `number` | `3` | Context data tree depth limit |
| `normalizeMaxBreadth` | `number` | `1000` | Max properties per object when normalizing |
| `enabled` | `boolean` | `true` | Whether SDK sends events at all |
| `denyUrls` | `Array<string\|RegExp>` | `[]` | Block errors from these script URLs |
| `allowUrls` | `Array<string\|RegExp>` | `[]` | Only report errors from these script URLs |
| `ignoreTransactions` | `Array<string\|RegExp>` | `[]` | Filter transactions by name pattern |
| `ignoreSpans` | `Array<string\|RegExp\|Object>` | `[]` | Filter spans by name/operation |
| `replaysSessionSampleRate` | `number` | — | Session replay sample rate |
| `replaysOnErrorSampleRate` | `number` | — | Error-triggered replay sample rate |
| `beforeSendSpan` | `Function` | — | Modify (not drop) span objects |
| `enhanceFetchErrorMessages` | `string\|false` | `'always'` | Append hostname to fetch errors |

### Python-Only Options

| Option | Type | Default | Description |
|---|---|---|---|
| `include_source_context` | `bool` | `True` | Include source code around errors |
| `include_local_variables` | `bool` | `True` | Capture local variable snapshots |
| `add_full_stack` | `bool` | `False` | Include all frames from execution start |
| `server_name` | `str` | `None` | Server identifier sent with events |
| `project_root` | `str` | `os.getcwd()` | Root directory for in-app frame detection |
| `in_app_include` | `list[str]` | `[]` | Module prefixes that belong to your app |
| `in_app_exclude` | `list[str]` | `[]` | Module prefixes that do not belong to your app |
| `event_scrubber` | `EventScrubber` | `None` | Strips cookies, sessions, passwords |
| `max_request_body_size` | `str` | `"medium"` | Capture HTTP body: `"never"`, `"small"`, `"medium"`, `"always"` |
| `profile_lifecycle` | `str` | `"manual"` | `"manual"` or `"trace"` |
| `functions_to_trace` | `list[str]` | `[]` | Functions to auto-instrument |
| `enable_db_query_source` | `bool` | `True` | Tag DB queries with source location |
| `enable_backpressure_handling` | `bool` | `True` | Health-check monitor thread |

## Sampling

### Error Sampling

Set a static rate or use a dynamic function.

```python
# Python - static
sentry_sdk.init(sample_rate=0.25)  # send 25% of errors

# Python - dynamic (error_sampler takes precedence over sample_rate)
def error_sampler(event, hint):
    exc = hint.get("exc_info", [None])[0]
    if exc == MyIgnoredException:
        return 0        # drop entirely
    if exc == MyException:
        return 0.5      # 50% chance
    return 1.0          # send all others

sentry_sdk.init(error_sampler=error_sampler)
```

```javascript
// JavaScript - static only
Sentry.init({ sampleRate: 0.25 });
```

### Transaction Sampling

Either set a uniform rate or provide a sampler function. You must configure one of these to enable tracing -- no transactions are sent by default.

```python
# Python - uniform rate
sentry_sdk.init(traces_sample_rate=0.2)  # ~20% of transactions

# Python - dynamic sampler
def traces_sampler(sampling_context):
    name = sampling_context.get("transaction_context", {}).get("name", "")
    if "healthcheck" in name:
        return 0          # drop health checks
    if "auth" in name:
        return 1.0        # always sample auth
    return 0.1            # 10% for everything else

sentry_sdk.init(traces_sampler=traces_sampler)
```

```javascript
// JavaScript - uniform rate
Sentry.init({ tracesSampleRate: 0.5 });

// JavaScript - dynamic sampler
Sentry.init({
  tracesSampler: ({ name, attributes, inheritOrSampleWith }) => {
    if (name.includes("healthcheck")) return 0;
    if (name.includes("auth")) return 1;
    return inheritOrSampleWith(0.5); // inherit parent or use 0.5
  },
});
```

### Sampling Precedence (Highest to Lowest)

1. `traces_sampler` / `tracesSampler` function decision
2. Parent sampling decision (propagated in distributed traces)
3. `traces_sample_rate` / `tracesSampleRate` static value

Sampling decisions propagate to child spans and downstream services. Respect parent decisions to keep distributed traces complete.

### Profile Sampling

```python
sentry_sdk.init(
    traces_sample_rate=1.0,
    profiles_sample_rate=0.1,        # 10% of traced transactions get profiled
    profile_lifecycle="trace",       # or "manual"
)
```

```javascript
Sentry.init({
  tracesSampleRate: 1.0,
  profileSessionSampleRate: 0.1,     // 10% of sessions profiled
  profileLifecycle: "trace",         // or "manual"
});
```

## Filtering

### before_send / beforeSend (Error Events)

Modify the event, strip data, or return `None`/`null` to drop it entirely.

```python
# Python
from sentry_sdk.types import Event, Hint

def before_send(event: Event, hint: Hint) -> Event | None:
    if hint.get("exc_info", [None])[0] == ZeroDivisionError:
        return None  # drop
    if event.get("user"):
        del event["user"]["email"]  # strip PII
    return event

sentry_sdk.init(before_send=before_send)
```

```javascript
// JavaScript
Sentry.init({
  beforeSend(event, hint) {
    if (hint.originalException instanceof UninterestingError) return null;
    if (event.user) delete event.user.email;
    return event;
  },
});
```

### before_send_transaction / beforeSendTransaction (Transactions)

```python
# Python - drop health-check transactions
from urllib.parse import urlparse

def filter_transactions(event, hint):
    url = event.get("request", {}).get("url", "")
    if urlparse(url).path == "/healthcheck":
        return None
    return event

sentry_sdk.init(before_send_transaction=filter_transactions)
```

```javascript
// JavaScript
Sentry.init({
  beforeSendTransaction(event) {
    if (event.transaction === "/unimportant/route") return null;
    return event;
  },
});
```

### ignore_errors / ignoreErrors

```python
# Python - list of exception class names (strings)
sentry_sdk.init(ignore_errors=["ConnectionError", "TimeoutError"])
```

```javascript
// JavaScript - strings (partial match) and regex (exact match)
Sentry.init({
  ignoreErrors: [
    "fb_xd_fragment",
    /^Exact Match Message$/,
  ],
});
```

### allowUrls / denyUrls (JavaScript Only)

Filter errors by the URL of the originating script.

```javascript
Sentry.init({
  allowUrls: [/https?:\/\/((cdn|www)\.)?example\.com/],
  denyUrls: [/extensions\//i, /^chrome:\/\//i],
});
```

### ignoreTransactions / ignoreSpans (JavaScript Only)

```javascript
Sentry.init({
  ignoreTransactions: ["partial/match", /^Exact Transaction Name$/],
  ignoreSpans: [{ name: /healthcheck/, op: "http.client" }],
});
```

### Third-Party Error Filtering (JavaScript Only)

Requires `@sentry/bundler-plugin`. Marks your bundles with an app key and filters errors from third-party frames.

```javascript
Sentry.init({
  integrations: [
    Sentry.thirdPartyErrorFilterIntegration({
      filterKeys: ["my-app-key"],
      behaviour: "drop-error-if-exclusively-contains-third-party-frames",
    }),
  ],
});
```

Behaviour options: `drop-error-if-contains-third-party-frames`, `drop-error-if-exclusively-contains-third-party-frames`, `apply-tag-if-contains-third-party-frames`, `apply-tag-if-exclusively-contains-third-party-frames`.

### Hints

Hints provide context for filtering decisions in `before_send` / `beforeSend`:
- `exc_info` (Python) / `originalException` (JS): the original exception
- `syntheticException`: artificially created for string errors
- `event_id`: unique event identifier

For breadcrumbs, hints contain the original data source (DOM element, XHR object, log record).

## Environments

Set via init or the `SENTRY_ENVIRONMENT` env var. Falls back to `"production"`.

```python
sentry_sdk.init(environment="staging")
```

```javascript
Sentry.init({ environment: "staging" });
```

**Constraints:** case-sensitive, max 64 chars, no newlines/spaces/slashes, cannot be `"None"`. Environments cannot be deleted once created (only hidden).

## Releases

Tag events with your app version for regression tracking and release health.

```python
sentry_sdk.init(release="myapp@1.0.0")
```

```javascript
Sentry.init({ release: "myapp@1.0.0" });
```

**Auto-detection order (Python):** `SENTRY_RELEASE` env var, Git commit SHA, hosting provider vars (`HEROKU_SLUG_COMMIT`, `SOURCE_VERSION`, `CODEBUILD_RESOLVED_SOURCE_VERSION`, `CIRCLE_SHA1`, `GAE_DEPLOYMENT_ID`).

**Naming rules:** no newlines/tabs/slashes/backslashes, not `.` or `..` or space only, max 200 chars.

Release health tracks user adoption, crash rates, and session data.

## Draining (Flushing Events Before Shutdown)

The SDK sends events asynchronously. Ensure pending events are delivered before shutdown.

```python
# Automatic: SDK drains on exit via AtexitIntegration (default)
# Configure timeout:
sentry_sdk.init(shutdown_timeout=5)

# Manual drain (disables the client afterward):
client = sentry_sdk.get_client()
client.close(timeout=2.0)

# Flush without disabling (keeps client alive):
sentry_sdk.flush(timeout=2.0)
```

Set `shutdown_timeout=0` or disable `AtexitIntegration` to turn off automatic draining.

## Dynamic Sampling (Server-Side)

Server-side sampling runs after events reach Sentry, adjusting rates without redeployment. Applies to spans and transactions only -- not errors.

**How it works:** Sentry analyzes incoming traffic volume and applies sampling rules. Low-volume projects get higher rates; high-volume projects get reduced rates.

**Automatic priorities (enabled by default):**
- Prioritized: latest releases, dev environments (`*debug*`, `*dev*`, `*local*`, `*qa*`, `*test*`), low-volume projects/transactions
- Deprioritized: health checks (`*healthcheck*`, `*/ping`, `*/health`)

**Distributed traces:** The sample rate of the originating project applies to all projects in the trace.

**Recommended approach:** Send 100% of events from the SDK (`traces_sample_rate=1.0`) when feasible and let dynamic sampling optimize server-side. This gives Sentry maximum visibility to make intelligent decisions.

**Custom sample rates** (Enterprise): Adjust per-project rates in the Sentry UI without SDK changes.

## Quotas and Rate Limiting

Sentry charges by data volume (errors, transactions, spans, replays, profiles, logs, attachments).

### Volume Management Strategies (Easiest to Hardest)

1. **Spike Protection** -- Automatic; drops excess traffic during anomalies. Enable per-project or org-wide in Settings > Spike Protection.
2. **Quota Adjustment** -- Increase/decrease limits in subscription settings.
3. **Rate Limiting** -- Per-project error limits via Project > Settings > Client Keys (DSN). Org-level attachment limits via Settings > Security & Privacy.
4. **Inbound Filters** -- Server-side filtering rules in Sentry UI (no code changes).
5. **SDK Sample Rate** -- `sample_rate` / `traces_sample_rate` to reduce volume at source.
6. **SDK Filtering** -- `before_send` / `before_send_transaction` callbacks.
7. **SDK Configuration** -- `ignore_errors`, `deny_urls`, `allow_urls`, etc.

### What Counts Toward Quota

Events count unless stopped by: spike protection, exceeded quota, rate limits, inbound filters, SDK sampling, SDK filtering, or size limit violations.

**Note:** Events for issues marked "Ignore" still consume quota. Only true filtering (dropping before acceptance) saves quota.

### Monitoring Usage

- All members: Stats > Usage tab
- Owners/Billing: Settings > Subscription (downloadable project breakdowns)
