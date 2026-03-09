# Sentry: Data Management & Security
Based on Sentry documentation (docs.sentry.io).

## Data Collected by Default

### Python SDK

**Always collected:**
- Request URLs (full URL of outgoing/incoming HTTP requests)
- Request query strings
- Request bodies (JSON and form; raw bodies and file uploads excluded; controlled by `max_request_body_size`, default `"medium"`)
- Source code context (snapshot around error origin)
- Stack trace local variables (names and values)
- SQL queries (sanitized/parameterized only; actual parameters omitted)

**Opt-in (`send_default_pii=True`):**
- HTTP headers (sensitive headers filtered by default)
- Cookies (session ID and CSRF tokens removed by default)
- Logged-in user info (email, user ID, username)
- User IP addresses
- LLM inputs/responses (AI integrations)

**Can be disabled:**
- Source context: `include_source_context=False`
- Local variables: `include_local_variables=False`
- Request bodies: `max_request_body_size="never"`

### JavaScript SDK

**Always collected:**
- HTTP response/request headers
- Full request URLs and query strings (server-side scrubbing applied for `apiKey`, `token`, etc.)
- Request/response body size only (via `content-length`), not content
- Browser, OS, device info (from User-Agent)
- Referrer URL
- Console logs as breadcrumbs (may contain sensitive data)
- Session Replay (text, images, and user input masked by default)

**Opt-in (`sendDefaultPii: true`):**
- Cookies (`Cookie` and `Set-Cookie` headers)
- User IP address and inferred location
- Logged-in user info (email, user ID, username)

**Not collected by default:**
- Request/response body content
- Local variables in stack traces
- User information or cookies

## Sensitive Data Handling (SDK-Side)

### Python SDK

**EventScrubber** — automatic denylist-based scrubbing:

```python
import sentry_sdk
from sentry_sdk.scrubber import EventScrubber, DEFAULT_DENYLIST, DEFAULT_PII_DENYLIST

sentry_sdk.init(
    dsn="...",
    send_default_pii=False,
    event_scrubber=EventScrubber(),  # uses default denylists
)
```

Add custom fields to the denylist:

```python
sentry_sdk.init(
    send_default_pii=False,
    event_scrubber=EventScrubber(
        denylist=DEFAULT_DENYLIST + ["my_sensitive_var"],
        pii_denylist=DEFAULT_PII_DENYLIST + ["my_private_var"],
        recursive=True,  # scrub nested structures
    ),
)
```

**before_send** — modify or drop events before transmission:

```python
def before_send(event, hint):
    # Drop events from admin pages
    if event.get("request", {}).get("url", "").startswith("/admin"):
        return None
    # Remove sensitive data
    if "user" in event:
        event["user"].pop("email", None)
    return event

sentry_sdk.init(dsn="...", before_send=before_send)
```

**before_send_transaction** — same as above but for transaction events.

**before_breadcrumb** — filter sensitive data from breadcrumbs before attachment.

**Best practices:**

```python
# Hash confidential data instead of sending plaintext
sentry_sdk.set_tag("birthday", checksum_or_hash("08/12/1990"))

# Use internal identifiers, not emails
sentry_sdk.set_user({"id": user.id})
```

### JavaScript SDK

**beforeSend** — scrub events before they leave the browser:

```javascript
Sentry.init({
  dsn: "...",
  beforeSend(event) {
    if (event.user) {
      delete event.user.email;
    }
    return event;
  },
});
```

**beforeBreadcrumb** — filter breadcrumbs containing sensitive data.

**Client-side filtering (InboundFilters integration):**

```javascript
Sentry.init({
  dsn: "...",
  ignoreErrors: ["ResizeObserver loop", /^NetworkError/],
  denyUrls: [/extensions\//i, /^chrome:\/\//i],
  allowUrls: [/https?:\/\/yourapp\.com/],
  ignoreTransactions: ["GET /healthcheck"],
});
```

**Best practices:**

```javascript
// Hash confidential data
Sentry.setTag("birthday", checksumOrHash("08/12/1990"));

// Use internal identifiers
Sentry.setUser({ id: user.id });
```

### Areas to Watch for Sensitive Data

- **Stack locals** — variable values in stack traces
- **Breadcrumbs** — log statements, database queries, console output
- **HTTP context** — query strings, request URLs
- **Transaction names** — URLs containing user IDs (e.g., `/users/1234/details`)
- **HTTP spans** — query strings and fragments in span attributes

## Server-Side Data Scrubbing

### Default Scrubbing (Enabled by Default)

Configure at **Settings > Security & Privacy** (org-level) or **Settings > Projects > [Project] > Security & Privacy** (project-level).

Sentry automatically redacts:
- **Credit card-like values** (basic regex detection)
- **Sensitive field names** — any field whose key contains: `password`, `secret`, `passwd`, `api_key`, `apikey`, `auth`, `credentials`, `mysql_pwd`, `privatekey`, `private_key`, `token`, `bearer`
- **Custom sensitive fields** — additional entries you configure under "Additional Sensitive Fields"
- **Entire objects** are set to null when sensitive data is detected (not just the matching field)

**Safe Fields** — exclude specific fields from scrubbing using path selectors and wildcards. Note: Safe Fields cannot prevent scrubbing in breadcrumbs.

**IP address storage** — can be disabled separately for PII compliance.

### Advanced Data Scrubbing Rules

Rules have three parts: **Method**, **Data Type**, and **Source** (selector).

**Methods:**
| Method | Behavior |
|--------|----------|
| Remove | Set to `null`, remove field, or replace with empty string |
| Mask | Replace all characters with `*` |
| Hash | Replace with a hashed value |
| Replace | Swap with `[Filtered]` (or custom placeholder) |

**Built-in data types:** Credit Card Numbers, Password Fields, IP Addresses (v4/v6), IMEI Numbers, Email Addresses, UUIDs, PEM Keys, Auth in URLs, US SSNs, Usernames in Filepaths, MAC Addresses, Anything.

**Custom regex:** `[Replace] [Regex Matches: \d{3}-\d{3}-\d{4}] from [extra.**]`

Use `(?i)` for case-insensitive matching. Wrap in `()` to replace only the first capture group.

**Source selectors:**

```
$error.value          # exception message
$message              # top-level log message
extra.'My Value'      # specific Additional Data key
extra.**              # everything in Additional Data
$http.headers.x-token # specific HTTP header
$user.ip_address      # user IP
$frame.vars.foo       # stack trace variable
tags.server_name      # tag value
**                    # all default PII fields
```

**Wildcards:** `**` matches all subpaths; `*` matches a single level.

**Boolean logic:** `foo && !extra.foo` (AND), `foo || bar` (OR), `!foo` (NOT).

**Examples:**

```
[Mask] [Credit Card Numbers] from [$string]
[Remove] [Password Fields] from [extra.**]
[Hash] [IP Addresses] from [$user.ip_address]
[Replace] [Regex Matches: \d{3}-\d{3}-\d{4}] from [extra.**]
[Remove] [Anything] from [exception.values.*.value]
```

Advanced rules take precedence over default scrubbing settings. Rules apply only to new events going forward.

## Data Storage Location

### Regions

| Region | Location | API Domain |
|--------|----------|------------|
| US | Iowa, USA | `us.sentry.io` |
| EU | Frankfurt, Germany | `de.sentry.io` |

Region is chosen at organization creation and **cannot be changed** afterward. The only option is creating a new organization.

### What Is Stored Where

**In your selected region:** Error events, transactions, profiles, session replays, releases, debug symbols, source maps.

**Always in US:** User accounts, organization settings, access tokens, audit logs, project metadata, DSN keys, integration metadata.

**Both regions:** Uptime checks (replicated globally).

### Multi-Organization

Each organization operates independently with separate subscriptions, usage tracking, and user management.

## Security

### DSN (Data Source Name)

The DSN is a public identifier for your project. It is safe to expose in client-side code. The DSN alone only allows sending new events; it cannot read existing data, modify settings, or access other projects.

### IP Ranges

**Inbound (dashboard, API, ingestion):**
- `sentry.io` / `us.sentry.io`: `35.186.247.156/32`
- `de.sentry.io`: `34.36.122.224/32`, `34.36.87.148/32`
- Ingestion (org subdomains): `34.120.195.249/32`, `34.120.62.213/32`, `34.160.81.0/32`, `34.102.210.18/32`

**Outbound (webhooks, integrations):**
- US: `35.184.238.160/32`, `104.155.159.182/32`, `104.155.149.19/32`, `130.211.230.102/32`
- EU: `34.141.31.19/32`, `34.141.4.162/32`, `35.234.78.236/32`

Allowlist outbound IPs if your firewall blocks Sentry webhooks or source map fetching.

## Quotas & Rate Limiting

### What Counts Toward Quota

Events count if they: pass validation (valid DSN, project, parseable), are not blocked by spike protection, have not triggered rate limits, are not filtered by inbound filters or SDK filtering, and do not exceed size limits.

**Delete & Discard** (Business/Enterprise): future matching events do not count. Resolved/ignored issues still count.

### Spike Protection

Automatically drops events when volume exceeds a baseline threshold. Enable per-project at **Settings > Spike Protection**.

### Rate Limits

**Per-project:** Configure at **[Project] > Settings > SDK Setup > Client Keys (DSN)**. Set maximum events per time window (e.g., 500 events/minute).

**Organization-level:** Manage at **Settings > Security & Privacy** (attachments).

### SDK-Side Volume Control

```python
# Python: sample rate (0.0 to 1.0)
sentry_sdk.init(
    dsn="...",
    sample_rate=0.5,           # send 50% of error events
    traces_sample_rate=0.1,    # send 10% of transactions
)
```

```javascript
// JavaScript: sample rate
Sentry.init({
  dsn: "...",
  sampleRate: 0.5,
  tracesSampleRate: 0.1,
});
```

Note: sample rate is static; changing it requires redeployment.

### Inbound Filters (No Code Changes)

Configure at **[Project] > Settings > Inbound Filters**:
- Common browser extension errors
- Localhost events
- Legacy browser errors
- Web crawlers/bots
- Specific IP addresses or subnets
- Specific releases (Business/Enterprise)
- Error message patterns (Business/Enterprise)

Filtered events do not count toward quota.

### Managing Quota (Easiest to Hardest)

1. Enable spike protection
2. Adjust quotas in **Settings > Subscription**
3. Apply per-project rate limits
4. Review and discard repeated noisy events
5. Configure inbound filters (no deploy needed)
6. Set SDK sample rates (requires deploy)
7. Implement `beforeSend` / `before_send` callbacks (requires deploy)
8. Fine-tune SDK configuration

## Best Practices

### Minimize Data Exposure

- Keep `send_default_pii` / `sendDefaultPii` **disabled** unless you need user-identifying data.
- Use `before_send` / `beforeSend` to strip sensitive fields before they leave the client.
- Hash or tokenize PII (birthdays, phone numbers) rather than sending plaintext.
- Set user context with internal IDs, not emails: `set_user({"id": user.id})`.
- Disable local variables (`include_local_variables=False`) if stack traces might contain secrets.
- Set `max_request_body_size="never"` if request bodies contain sensitive payloads.

### Server-Side Defense in Depth

- Keep default server-side scrubbing **enabled**.
- Add domain-specific sensitive field names to "Additional Sensitive Fields."
- Write advanced scrubbing rules for known PII patterns (SSNs, phone numbers, custom IDs).
- Use the **Hash** method when you need to correlate scrubbed values across events without exposing the original.

### Quota Hygiene

- Enable spike protection on all projects.
- Use inbound filters to drop noise (browser extensions, bots, legacy browsers) before it hits quota.
- Set per-project rate limits as a safety ceiling, not a throttle.
- Use `beforeSend` to drop events you will never investigate (health checks, known noise).
- Review the Usage Stats page regularly; sort by project to find volume outliers.
- Use **Delete & Discard** for recurring irrelevant issues (Business/Enterprise).

### Region & Compliance

- Choose EU region (`de.sentry.io`) at org creation if GDPR requires EU data residency.
- Be aware that account metadata (user accounts, org settings, audit logs) is always stored in the US regardless of region choice.
- Use region-specific API domains (`us.sentry.io` or `de.sentry.io`) for API calls.
