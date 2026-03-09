# Sentry: Python SDK
Based on Sentry documentation (docs.sentry.io).

## Installation

```bash
pip install "sentry-sdk"
```

## SDK Setup

### Basic Python

Initialize early in application lifecycle, before any other imports that might raise errors:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    environment="production",
    release="myapp@1.0.0",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
    send_default_pii=True,
    enable_logs=True,
)
```

### Django

In `settings.py` -- no explicit integration import needed for basic setup:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    traces_sample_rate=1.0,
    send_default_pii=True,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
    enable_logs=True,
)
```

Auto-instruments: middleware, signals, DB queries, Redis commands, cache operations.
Attaches user data from `django.contrib.auth` when `send_default_pii=True`.

Advanced `DjangoIntegration` options:

```python
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[
        DjangoIntegration(
            transaction_style="url",        # "url" or "endpoint" (function name)
            middleware_spans=True,           # track middleware performance
            signals_spans=True,             # track signal receivers
            cache_spans=True,               # monitor cache hit/miss
        ),
    ],
)
```

### Celery

Initialize in both the worker process and the application process.

Worker-side setup (non-Django):

```python
from celery import signals
import sentry_sdk

@signals.celeryd_init.connect
def init_sentry(**_kwargs):
    sentry_sdk.init(
        dsn="...",
        traces_sample_rate=1.0,
    )
```

When using Django with `config_from_object`, the `settings.py` init covers both app and worker.

`CeleryIntegration` options:

```python
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[
        CeleryIntegration(
            propagate_traces=True,          # link task errors to callers
            monitor_beat_tasks=False,       # auto-instrument Beat tasks as crons
            exclude_beat_tasks=["payment-check-.*"],  # regex patterns to skip
        ),
    ],
)
```

Override trace propagation per-task (does not work with `.delay()`):

```python
my_task.apply_async(
    args=("param",),
    headers={"sentry-propagate-traces": False},
)
```

### FastAPI

Auto-activates when `fastapi` is installed:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    send_default_pii=True,
    enable_logs=True,
)
```

Advanced options:

```python
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[
        StarletteIntegration(transaction_style="url"),
        FastApiIntegration(
            transaction_style="url",                  # "url" or "endpoint"
            failed_request_status_codes={*range(500, 600)},
            middleware_spans=False,
            http_methods_to_capture=("GET", "POST"),
        ),
    ],
)
```

### Flask

Auto-activates when `flask` is installed:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    send_default_pii=True,
    enable_logs=True,
)
```

Advanced options:

```python
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[
        FlaskIntegration(
            transaction_style="url",                      # "url" or "endpoint"
            http_methods_to_capture=("GET", "POST"),
        ),
    ],
)
```

### Async Programs

For async applications, call init inside an async function:

```python
import asyncio
import sentry_sdk

async def main():
    sentry_sdk.init(dsn="...")

asyncio.run(main())
```

## Key Configuration Options

### Common init() Parameters

| Option | Type | Default | Description |
|---|---|---|---|
| `dsn` | `str` | `None` | Where to send events |
| `debug` | `bool` | `False` | Enable SDK debug output |
| `release` | `str` | `None` | App version (e.g. `"myapp@1.0.0"`) |
| `environment` | `str` | `"production"` | Deployment environment |
| `sample_rate` | `float` | `1.0` | Error event sample rate (0.0-1.0) |
| `traces_sample_rate` | `float` | `None` | Transaction sample rate (0.0-1.0) |
| `traces_sampler` | `function` | `None` | Dynamic transaction sampling function |
| `profiles_sample_rate` | `float` | `None` | Profile sample rate (0.0-1.0) |
| `profile_session_sample_rate` | `float` | `None` | Session profiling rate (0.0-1.0) |
| `profile_lifecycle` | `str` | `"manual"` | `"trace"` (auto) or `"manual"` |
| `send_default_pii` | `bool` | `None` | Capture request headers, IPs, user info |
| `max_breadcrumbs` | `int` | `100` | Max breadcrumbs to keep |
| `attach_stacktrace` | `bool` | `False` | Attach stack traces to messages |
| `include_local_variables` | `bool` | `True` | Capture local vars in stack frames |
| `ignore_errors` | `list` | `[]` | Exception class names to never report |
| `enable_logs` | `bool` | `False` | Enable Sentry structured logging |
| `before_send` | `function` | `None` | Modify/drop error events before sending |
| `before_send_transaction` | `function` | `None` | Modify/drop transaction events |
| `before_breadcrumb` | `function` | `None` | Modify/drop breadcrumbs |
| `before_send_log` | `function` | `None` | Modify/drop log entries |
| `event_scrubber` | `EventScrubber` | `None` | Scrub sensitive data from events |
| `integrations` | `list` | `[]` | Additional integrations |
| `disabled_integrations` | `list` | `[]` | Explicitly disabled integrations |
| `server_name` | `str` | `None` | Server identifier |
| `in_app_include` | `list[str]` | `[]` | Module prefixes belonging to your app |
| `in_app_exclude` | `list[str]` | `[]` | Module prefixes to exclude |
| `shutdown_timeout` | `int` | `2` | Seconds to wait before shutdown |
| `transport_queue_size` | `int` | `100` | Event queue capacity |
| `max_request_body_size` | `str` | `"medium"` | Request body capture size |
| `trace_propagation_targets` | `list` | `[".*"]` | URL patterns for trace header propagation |
| `functions_to_trace` | `list` | `[]` | Functions to auto-instrument |

### Environment

```python
sentry_sdk.init(environment="staging")
```

Falls back to `SENTRY_ENVIRONMENT` env var, then defaults to `"production"`.
Names are case-sensitive, max 64 chars, no newlines/spaces/slashes.

### Release

```python
sentry_sdk.init(release="myapp@1.0.0")
```

Auto-detected from `SENTRY_RELEASE` env var, git SHA, or hosting provider vars
(`HEROKU_SLUG_COMMIT`, `SOURCE_VERSION`, `CIRCLE_SHA1`, etc.).

## Sampling

### Uniform Sampling

```python
sentry_sdk.init(
    traces_sample_rate=0.2,   # 20% of transactions
    sample_rate=1.0,          # 100% of errors (default)
)
```

### Dynamic Transaction Sampling

```python
def traces_sampler(sampling_context):
    if sampling_context.get("parent_sampled") is not None:
        return float(sampling_context["parent_sampled"])
    return 0.1

sentry_sdk.init(traces_sampler=traces_sampler)
```

Precedence: explicit `sampled` param > `traces_sampler` > parent decision > `traces_sample_rate`.

### Dynamic Error Sampling

```python
def error_sampler(event, hint):
    if hint.get("exc_info", [None])[0] == MyNoisyException:
        return 0.01
    return 1.0

sentry_sdk.init(error_sampler=error_sampler)
```

## Capturing Events

### Capture Exceptions

```python
import sentry_sdk

try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

Or without arguments to capture from `sys.exc_info()`:

```python
try:
    risky_operation()
except Exception:
    sentry_sdk.capture_exception()
```

### Capture Messages

```python
sentry_sdk.capture_message("Something noteworthy happened")
```

## Filtering Events

### before_send (Error Events)

Return `None` to drop the event:

```python
def before_send(event, hint):
    exc_info = hint.get("exc_info")
    if exc_info and exc_info[0] == ZeroDivisionError:
        return None
    return event

sentry_sdk.init(before_send=before_send)
```

### before_send_transaction (Transaction Events)

```python
from urllib.parse import urlparse

def filter_transactions(event, hint):
    url = event.get("request", {}).get("url", "")
    if urlparse(url).path == "/healthcheck":
        return None
    return event

sentry_sdk.init(before_send_transaction=filter_transactions)
```

### ignore_errors

```python
sentry_sdk.init(ignore_errors=[KeyboardInterrupt, ConnectionError])
```

## Enriching Events

### Tags (Searchable, Indexed)

```python
sentry_sdk.set_tag("payment.provider", "stripe")
sentry_sdk.set_tags({"page.locale": "de-at", "page.type": "article"})
```

Keys: max 32 chars, alphanumeric plus `_`, `.`, `:`, `-`.
Values: max 200 chars, no newlines. Tags are searchable in the Sentry UI.

### Context (Structured, Not Searchable)

```python
sentry_sdk.set_context("order", {
    "id": "ord_12345",
    "amount": 99.99,
    "currency": "USD",
})
```

Do not use `type` as a key (reserved). For searchable data, use tags instead.

### User Identification

```python
sentry_sdk.set_user({
    "id": "user_123",
    "email": "jane@example.com",
    "username": "jane",
    "ip_address": "{{auto}}",
})

# Clear user data
sentry_sdk.set_user(None)
```

At least one field required. IP collection requires `send_default_pii=True`.

### Breadcrumbs

Automatically captured: HTTP requests, log entries, DB queries, Redis commands.

Manual breadcrumbs:

```python
sentry_sdk.add_breadcrumb(
    category="auth",
    message=f"Authenticated user {user.email}",
    level="info",
)
```

Filter breadcrumbs:

```python
def before_breadcrumb(crumb, hint):
    if crumb["category"] == "noisy.logger":
        return None
    return crumb

sentry_sdk.init(before_breadcrumb=before_breadcrumb)
```

### Attachments

```python
scope = sentry_sdk.get_current_scope()
scope.add_attachment(bytes=b"file content", filename="debug.txt")
scope.add_attachment(path="/path/to/file.log")
```

Max: 40MB compressed request, 200MB uncompressed per event. Retained 30 days.

### Scopes

Three scope levels merge when sending events (global -> isolation -> current):

- **Global scope**: app-wide data (release, environment)
- **Isolation scope**: per-request data (user, tags) -- managed by framework integrations
- **Current scope**: per-span data

```python
with sentry_sdk.new_scope() as scope:
    scope.set_tag("my-tag", "my-value")
    try:
        risky_operation()
    except Exception as e:
        sentry_sdk.capture_exception(e)
# tag is gone outside the with block
```

Important: inside `new_scope()`, call methods on the yielded scope object, not top-level
`sentry_sdk.set_tag()` which may target a different scope.

## Tracing

### Enabling

```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
)
```

### Custom Spans

Context manager:

```python
with sentry_sdk.start_span(name="process-order") as span:
    span.set_data("order_id", order.id)
    process(order)
```

Decorator:

```python
@sentry_sdk.trace
def process_order(order):
    ...
```

Decorator with parameters (v2.35.0+):

```python
@sentry_sdk.trace(op="db", name="fetch-user", attributes={"user_id": 42})
def fetch_user(user_id):
    ...
```

Manual span (must call `finish()`):

```python
span = sentry_sdk.start_span(name="compute")
result = compute()
span.finish()
```

### Nested Spans

```python
parent = sentry_sdk.start_span(name="parent-op")
child = parent.start_child(name="child-op")
do_work()
child.finish()
parent.finish()
```

### Accessing Active Span

```python
span = sentry_sdk.get_current_span()          # current span or None
txn = sentry_sdk.get_current_scope().transaction  # active transaction name
```

### Updating Current Span

```python
sentry_sdk.update_current_span(
    op="updated-op",
    name="Updated Name",
    attributes={"key": "value"},
)
```

### Centralized Function Tracing

```python
sentry_sdk.init(
    dsn="...",
    functions_to_trace=[
        {"qualified_name": "myapp.services.payment.charge"},
        {"qualified_name": "myapp.utils.validate"},
    ],
)
```

## Structured Logs

Requires SDK v2.35.0+. Enable with `enable_logs=True`.

```python
from sentry_sdk import logger as sentry_logger

sentry_logger.trace("Starting connection to {database}", database="users")
sentry_logger.debug("Cache miss for user {user_id}", user_id=123)
sentry_logger.info("Updated global cache")
sentry_logger.warning("Rate limit for {endpoint}", endpoint="/api/results/")
sentry_logger.error("Payment failed. Order: {order_id}", order_id="or_123")
sentry_logger.fatal("DB {database} pool exhausted", database="users")
```

With extra attributes:

```python
sentry_logger.error(
    "Payment processing failed",
    attributes={
        "payment.provider": "stripe",
        "payment.currency": "USD",
        "user.tier": "premium",
    },
)
```

Filter logs:

```python
def before_log(log, _hint):
    if log["severity_text"] == "info":
        return None
    return log

sentry_sdk.init(enable_logs=True, before_send_log=before_log)
```

## Profiling

### Continuous Profiling (Trace Mode)

Profiler runs while spans are active:

```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)
```

### Manual Profiling

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

## Cron Monitoring

### Decorator

```python
from sentry_sdk.crons import monitor

@monitor(monitor_slug="daily-cleanup")
def daily_cleanup():
    ...
```

Also works as a context manager:

```python
with monitor(monitor_slug="daily-cleanup"):
    run_cleanup()
```

### Celery Beat Auto-Instrumentation

```python
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="...",
    integrations=[
        CeleryIntegration(monitor_beat_tasks=True),
    ],
)
```

### Manual Check-Ins

```python
from sentry_sdk.crons import capture_checkin
from sentry_sdk.crons.consts import MonitorStatus

check_in_id = capture_checkin(
    monitor_slug="daily-cleanup",
    status=MonitorStatus.IN_PROGRESS,
)

try:
    run_cleanup()
    capture_checkin(
        monitor_slug="daily-cleanup",
        check_in_id=check_in_id,
        status=MonitorStatus.OK,
    )
except Exception:
    capture_checkin(
        monitor_slug="daily-cleanup",
        check_in_id=check_in_id,
        status=MonitorStatus.ERROR,
    )
    raise
```

Rate limit: 6 check-ins per minute per monitor-environment combination.

## Sensitive Data

### EventScrubber

Default scrubber filters passwords, tokens, sessions, cookies, CSRF tokens:

```python
from sentry_sdk.scrubber import EventScrubber, DEFAULT_DENYLIST

sentry_sdk.init(
    send_default_pii=False,
    event_scrubber=EventScrubber(
        denylist=DEFAULT_DENYLIST + ["my_secret_field"],
    ),
)
```

### Scrubbing with before_send

```python
def before_send(event, hint):
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        event["request"]["headers"] = {
            k: v for k, v in event["request"]["headers"].items()
            if k.lower() not in ("authorization", "cookie")
        }
    return event

sentry_sdk.init(before_send=before_send)
```

### Safe User Identification

```python
sentry_sdk.set_user({"id": user.id})  # ID only, no email/username
sentry_sdk.set_tag("birthday", hashlib.sha256(b"08/12/1990").hexdigest())
```

Watch for sensitive data in: stack locals, breadcrumbs, user context, request params,
transaction names containing URLs, HTTP span query strings.

## Testing with Sentry

### Disabling in Tests

Set `dsn` to `None` or omit `sentry_sdk.init()` entirely. The SDK is a no-op without a DSN.

### Intercepting Events in Tests

Use the `transport` option to capture events locally:

```python
class EventCaptureTransport(sentry_sdk.transport.Transport):
    def __init__(self, options):
        self.events = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.type == "event":
                self.events.append(item.payload.json)

transport = EventCaptureTransport(None)
sentry_sdk.init(dsn="https://key@sentry.io/1", transport=transport)

# ... run code that triggers errors ...
assert len(transport.events) == 1
```

### Django Test Override

```python
from django.test import override_settings, TestCase

class MyTest(TestCase):
    @override_settings(SENTRY_DSN=None)
    def test_something(self):
        ...
```

## Common Pitfalls

1. **Late initialization.** Call `sentry_sdk.init()` as early as possible. Errors raised
   before init are not captured.

2. **Celery worker init.** The SDK must be initialized in the worker process, not just
   the module where tasks are defined. Use the `celeryd_init` signal for non-Django setups.

3. **100% sample rate in production.** Set `traces_sample_rate` to a low value (0.01-0.2)
   in high-throughput environments. Use `traces_sampler` for granular control.

4. **Swallowed exceptions.** `capture_exception()` only works inside an `except` block
   or with an explicit exception argument. Silent `except: pass` blocks hide errors from
   Sentry too.

5. **Scope confusion with new_scope.** Inside `with sentry_sdk.new_scope() as scope:`,
   use `scope.set_tag()` -- not the top-level `sentry_sdk.set_tag()` which may target a
   different scope.

6. **Blocking shutdown.** The SDK sends events asynchronously. If your process exits
   immediately, events may be lost. The default `shutdown_timeout` is 2 seconds.
   For CLI scripts, call `sentry_sdk.flush()` before exiting.

7. **send_default_pii defaults to off.** User IPs, request headers, and cookies are not
   sent unless you explicitly set `send_default_pii=True`.

8. **Tags vs context.** Tags are indexed and searchable (use for filtering). Context is
   structured but not searchable (use for debugging detail). Do not put large payloads
   in either -- there is a 200-char limit on tag values and a payload size cap on context.

9. **before_send does not cover transactions.** Use `before_send_transaction` to filter
   transaction events. `before_send` only applies to error events.

10. **Cron rate limits.** Max 6 check-ins per minute per monitor-environment. Exceeding
    this causes missed check-ins and false alerts.
