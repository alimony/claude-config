# Sentry: Enriching Events
Based on Sentry documentation (docs.sentry.io).

## Tags

Tags are indexed key-value string pairs that power filtering, search, and tag-distribution maps in the Sentry UI.

### Python

```python
import sentry_sdk

# Single tag
sentry_sdk.set_tag("page.locale", "de-at")

# Multiple tags
sentry_sdk.set_tags({"page.locale": "de-at", "page.type": "article"})
```

### JavaScript

```javascript
import * as Sentry from "@sentry/browser";

Sentry.setTag("page_locale", "de-at");
```

### Tag naming rules

- **Keys**: Max 32 characters. Letters, numbers, underscores, periods, colons, dashes only.
- **Values**: Max 200 characters. No newlines.

### Do this / Don't do this

```python
# Do: use your own namespace for custom tags
sentry_sdk.set_tag("myapp.plan", "enterprise")

# Don't: overwrite Sentry's automatic tags (browser, os, etc.)
sentry_sdk.set_tag("browser", "custom-value")  # breaks built-in filtering
```

Tags are bound to the isolation scope -- all subsequent events in that scope inherit them. Sentry automatically indexes tag frequency, last occurrence, and distinct counts.

---

## Breadcrumbs

Breadcrumbs create a trail of events leading up to an issue. They are not events themselves -- they attach to the next captured event.

### Manual breadcrumbs

**Python:**

```python
import sentry_sdk

sentry_sdk.add_breadcrumb(
    category="auth",
    message="Authenticated user %s" % user.email,
    level="info",
)
```

**JavaScript:**

```javascript
import * as Sentry from "@sentry/browser";

Sentry.addBreadcrumb({
  category: "auth",
  message: "Authenticated user " + user.email,
  level: "info",
});
```

### Breadcrumb fields

| Field | Description |
|-------|-------------|
| `type` | Breadcrumb type (default, http, navigation, etc.) |
| `category` | Dot-separated string for grouping (e.g. `auth`, `ui.click`) |
| `message` | Human-readable message |
| `level` | `fatal`, `error`, `warning`, `info`, `debug` |
| `timestamp` | Defaults to current time |
| `data` | Dict/object of supplementary key-value pairs |

### Automatic breadcrumbs

**Python SDK auto-captures:** HTTP requests (web frameworks), logging module output, database queries, Redis commands, subprocess (Popen) calls, Apache Spark events.

**JavaScript SDK auto-captures:** DOM clicks, keyboard input, XHR/fetch requests, console calls, navigation/history changes.

### Filtering breadcrumbs

**Python:**

```python
from sentry_sdk.types import Breadcrumb, BreadcrumbHint

def before_breadcrumb(crumb: Breadcrumb, hint: BreadcrumbHint) -> Breadcrumb | None:
    if crumb["category"] == "a.spammy.Logger":
        return None
    return crumb

sentry_sdk.init(
    # ...
    before_breadcrumb=before_breadcrumb,
)
```

**JavaScript:**

```javascript
Sentry.init({
  beforeBreadcrumb(breadcrumb, hint) {
    return breadcrumb.category === "ui.click" ? null : breadcrumb;
  },
});
```

Return `None`/`null` to drop the breadcrumb entirely.

---

## Context

Contexts attach arbitrary structured data to events. Unlike tags, contexts are **not searchable** -- use tags when you need filtering.

### Python

```python
import sentry_sdk

sentry_sdk.set_context("character", {
    "name": "Mighty Fighter",
    "age": 19,
    "attack_type": "melee",
})
```

### JavaScript

```javascript
Sentry.setContext("character", {
  name: "Mighty Fighter",
  age: 19,
  attack_type: "melee",
});
```

### Rules

- Context names are unrestricted strings.
- All keys are allowed inside a context **except** `type` (reserved by Sentry).
- Nested data is normalized to 3 levels deep by default.
- Avoid sending large data blobs -- exceeding payload limits triggers HTTP 413.
- Pass `null` as the context value to clear a previously set context.

### Do this / Don't do this

```python
# Do: attach focused, relevant data
sentry_sdk.set_context("order", {"id": order.id, "total": order.total})

# Don't: dump entire application state
sentry_sdk.set_context("state", app.get_full_state())  # risks 413 errors
```

**Note:** `set_extra()` is deprecated. Use `set_context()` instead.

---

## Scopes

Scopes hold data (tags, contexts, breadcrumbs, user) that gets merged into every event captured within that scope.

### Three scope types

| Scope | Purpose | Access |
|-------|---------|--------|
| **Global** | App-wide data (release, environment) | `sentry_sdk.get_global_scope()` / `Sentry.getGlobalScope()` |
| **Isolation** | Per-request data (user, tags) | `sentry_sdk.set_tag()` / `Sentry.setTag()` (top-level APIs target this) |
| **Current** | Per-span or narrowly scoped data | `new_scope()` / `withScope()` |

**Merge order:** Global -> Isolation -> Current. Later scopes override earlier ones for conflicting keys.

### Python -- new_scope

```python
import sentry_sdk

with sentry_sdk.new_scope() as scope:
    scope.set_tag("my-tag", "my value")
    try:
        raise RuntimeError("scoped error")
    except Exception:
        sentry_sdk.capture_exception()

# Tag "my-tag" does NOT apply to events outside the with block
```

Inside `new_scope`, call methods on the yielded `scope` object directly -- do not use top-level APIs like `sentry_sdk.set_tag()` (those target the isolation scope, not the new scope).

### JavaScript -- withScope

```javascript
Sentry.withScope((scope) => {
  scope.setTag("my-tag", "my value");
  scope.setLevel("warning");
  Sentry.captureException(new Error("scoped error"));
});

// Tag "my-tag" does NOT apply to events outside the callback
```

### JavaScript -- scope precedence

```javascript
Sentry.getGlobalScope().setExtras({ shared: "global", global: "data" });
Sentry.getIsolationScope().setExtras({ shared: "isolation", isolation: "data" });
Sentry.getCurrentScope().setExtras({ shared: "current", current: "data" });

Sentry.captureException(new Error("test"));
// Merged result: { shared: "current", global: "data", isolation: "data", current: "data" }
```

---

## User Identification

Identifying users lets Sentry track how many users are affected by each issue and enables user-specific filtering.

### Python

```python
import sentry_sdk

sentry_sdk.set_user({"email": "jane.doe@example.com"})

# Clear the user (e.g. on logout)
sentry_sdk.set_user(None)
```

### JavaScript

```javascript
Sentry.setUser({ id: "42", email: "jane.doe@example.com" });

// Clear the user
Sentry.setUser(null);
```

### Standard user fields

| Field | Description |
|-------|-------------|
| `id` | Your internal user identifier |
| `username` | Display-friendly name |
| `email` | Enables Gravatar and notifications |
| `ip_address` | Identifies unauthenticated users |

At least one field is required. You can add arbitrary extra key-value pairs beyond these.

### IP address behavior

- Set `ip_address` to `"{{auto}}"` to infer from the connection to Sentry's servers.
- Enable `send_default_pii=True` (Python) / `sendDefaultPii: true` (JS) for automatic IP extraction from HTTP requests.
- Set to `None`/`null` or use project Security & Privacy settings to disable IP storage.

---

## Event Processors

Event processors modify or drop events before they are sent to Sentry.

### before_send (runs last, guaranteed)

**Python:**

```python
import sentry_sdk
from sentry_sdk.types import Event, Hint

def before_send(event: Event, hint: Hint) -> Event | None:
    if "exc_info" in hint:
        exc = hint["exc_info"][1]
        if isinstance(exc, SomeIgnoredException):
            return None  # drop the event
    event["tags"]["custom"] = "value"
    return event

sentry_sdk.init(
    dsn="...",
    before_send=before_send,
)
```

**JavaScript:**

```javascript
Sentry.init({
  dsn: "...",
  beforeSend(event, hint) {
    const error = hint.originalException;
    if (error?.message?.match(/ignore this/i)) {
      return null; // drop the event
    }
    return event;
  },
});
```

Return `None`/`null` to drop the event entirely.

### Custom event processors on scope

**Python:**

```python
import sentry_sdk

def my_processor(event, hint):
    event["tags"]["foo"] = "42"
    return event

# Global -- applies to all events
sentry_sdk.get_global_scope().add_event_processor(my_processor)

# Scoped -- applies only within new_scope
with sentry_sdk.new_scope() as scope:
    scope.add_event_processor(my_processor)
    sentry_sdk.capture_message("processed")
```

### Execution order

- `add_event_processor` (global or scoped): runs in **undetermined order**.
- `before_send` / `before_send_transaction`: **guaranteed to run last**.

---

## Attachments

Attachments let you store additional files (logs, config dumps, screenshots) alongside events.

### Python

```python
import sentry_sdk

scope = sentry_sdk.get_current_scope()

# From bytes
scope.add_attachment(bytes=b"Hello World!", filename="attachment.txt")

# From file path
scope.add_attachment(path="/path/to/file.txt")
```

### Parameters for add_attachment

| Parameter | Description |
|-----------|-------------|
| `bytes` | Raw data or callable returning bytes |
| `path` | File path on disk |
| `filename` | Display name in Sentry (inferred from `path` if omitted) |
| `content_type` | MIME type (auto-detected if omitted) |
| `add_to_transactions` | Include with transaction events (default `False`) |

Provide either `bytes` or `path`, not both.

### Modifying attachments via event processor

```python
from sentry_sdk.scope import add_global_event_processor
from sentry_sdk.attachments import Attachment

@add_global_event_processor
def processor(event, hint):
    hint["attachments"] = [Attachment(bytes=b"data", filename="debug.txt")]
    return event
```

### Limits

- Max 40 MB compressed per request.
- Max 200 MB uncompressed per event.
- Attachments are stored for 30 days.
- All attachments on a scope are sent with every non-transaction event in that scope.

---

## Fingerprinting

Fingerprints control how Sentry groups events into issues. Events with the same fingerprint array are grouped together.

### Basic: group by request properties

```python
import sentry_sdk

def make_request(method, path, options):
    try:
        return session.request(method, path, **options)
    except RequestError as err:
        with sentry_sdk.new_scope() as scope:
            scope.fingerprint = [method, path, str(err.status_code)]
            sentry_sdk.capture_exception(err)
```

### Using {{ default }} to extend default grouping

```python
import sentry_sdk
from sentry_sdk.types import Event, Hint

class CustomRPCError(Exception):
    function = None
    error_code = None

def before_send(event: Event, hint: Hint):
    if "exc_info" not in hint:
        return event
    exc = hint["exc_info"][1]
    if isinstance(exc, CustomRPCError):
        event["fingerprint"] = [
            "{{ default }}",       # keep Sentry's automatic grouping
            str(exc.function),     # plus custom dimensions
            str(exc.error_code),
        ]
    return event

sentry_sdk.init(before_send=before_send)
```

### Aggressive grouping (collapse all into one issue)

```python
def before_send(event, hint):
    if "exc_info" not in hint:
        return event
    exc = hint["exc_info"][1]
    if isinstance(exc, DatabaseConnectionError):
        event["fingerprint"] = ["database-connection-error"]
    return event
```

### Do this / Don't do this

```python
# Do: use {{ default }} to add dimensions to Sentry's grouping
event["fingerprint"] = ["{{ default }}", str(error_code)]

# Don't: use highly variable values that create one issue per event
event["fingerprint"] = [str(request_id)]  # unique per request = ungrouped noise
```

- `{{ default }}` keeps Sentry's built-in grouping and adds your custom dimensions.
- Omitting `{{ default }}` completely replaces automatic grouping.
- Fingerprints are string arrays of unrestricted length.

---

## Transaction Names

Transaction names group performance data in Sentry's Insights product and annotate error events with their point of failure.

### Python

```python
import sentry_sdk

scope = sentry_sdk.get_current_scope()
scope.set_transaction_name("UserListView")
```

### Good transaction names

Transaction names should have **low cardinality** while still uniquely identifying the code path:

```python
# Do: parameterized route
scope.set_transaction_name("GET /api/{version}/users/")

# Do: class-based view name
scope.set_transaction_name("UserListView")

# Do: task path
scope.set_transaction_name("myapp.tasks.renew_all_subscriptions")

# Don't: include variable values like user IDs
scope.set_transaction_name(f"GET /api/users/{user_id}")  # too many unique values
```

Most framework integrations set transaction names automatically. Use `set_transaction_name()` only when you need to override the default.
