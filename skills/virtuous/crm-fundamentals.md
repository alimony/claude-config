# Virtuous CRM+: API fundamentals
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

The CRM+ API is the server-to-server integration surface for the Virtuous Responsive Fundraising platform. Use it to read and write Contacts, Gifts, recurring giving, Campaigns, and Designations on behalf of a nonprofit customer. This skill covers the fundamentals every integration needs before touching a resource endpoint: authentication, environments, rate limits, and error handling.

## API at a glance

| Property | Value |
| --- | --- |
| Base URL | `https://api.virtuoussoftware.com` |
| Base path | `/api` (appended to the base URL, e.g. `/api/Contact/4821`) |
| Protocol | HTTPS only. Plain HTTP requests fail. |
| Auth | API Key or OAuth 2.0 Bearer token in the `Authorization` header |
| Request/response format | `application/json` (error bodies too, mostly – see Error handling) |
| Rate limit | 5,000 requests per hour, per Virtuous organization |
| Token endpoint | `POST https://api.virtuoussoftware.com/Token` (OAuth only) |
| Sandbox | No separate host. Isolation is per organization. Request a Seeded Sandbox org. |

Authenticated endpoints do not support cross-origin (browser) requests. Call the API from a server-side environment only, and never embed credentials in client-side code.

## Authentication

Every request carries a Bearer token in the `Authorization` header. Two token types exist, and the header format is identical for both:

```text
Authorization: Bearer YOUR_API_TOKEN
```

### Choose a method

| Method | Best for | Token lifetime |
| --- | --- | --- |
| **API Key** | Partner integrations, automated syncs, background jobs, service accounts | 15 years (static) |
| **OAuth token** | User-delegated access – the integration acts as a specific Virtuous user | 15 days access token / 365 days refresh token |

Use an API Key for almost every partner integration. Reach for OAuth only when the integration must act as a specific signed-in user (for example, an interactive admin tool). API Keys survive personnel changes; OAuth credentials are revoked when the underlying user leaves the nonprofit.

### API Keys

Create a key in the Virtuous UI (administrator permission required): **Settings → All Settings → Connectivity → API Keys → Create an API Key**. Give it a descriptive name (usually the integration name) and pick a permission group. After saving, the key is stored in the UI and can be revealed or copied later from the key's edit view (eye icon to show, copy icon to copy).

- **One key per nonprofit customer.** A key is generated inside a specific Virtuous organization and grants access only to that organization's data. There is no header or query parameter that switches organization at request time. A multi-customer integration stores one key per customer and selects the right key per call.
- **Permission group is attached to the key.** Two keys in the same organization can have different access levels. A `403` usually means the key's permission group lacks the resource you called.

### OAuth: password grant

Request a token with a `POST` to the `/Token` endpoint using the `password` grant type. URL-encode the email and password so special characters survive.

```bash
curl -X POST https://api.virtuoussoftware.com/Token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=YOUR_EMAIL&password=YOUR_PASSWORD"
```

Successful response:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3599,
  "refresh_token": "zyx987...",
  "userName": "developer@example.org",
  "twoFactorEnabled": "False",
  ".issued": "Thu, 10 Feb 2022 22:27:19 GMT",
  ".expires": "Sat, 25 Feb 2022 22:27:19 GMT"
}
```

Use the `access_token` value as your Bearer token. `expires_in` is the access-token session window in seconds (roughly one hour here); the OAuth credential's full effective lifetime is 15 days.

> **Do / Don't:** Send the `/Token` body as `application/x-www-form-urlencoded`. Do NOT send it as `multipart/form-data` – several HTTP clients and the Postman collection default to that and the request fails. If you cannot get a token, check the `Content-Type` first.

### OAuth: refresh a token

When the access token expires, exchange the refresh token for a new one instead of re-prompting the user. Refresh tokens last 365 days.

```bash
curl -X POST https://api.virtuoussoftware.com/Token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=YOUR_REFRESH_TOKEN"
```

Virtuous may rotate the refresh token on each refresh, so store BOTH the new `access_token` and the new `refresh_token` from the response every time.

### OAuth: two-factor accounts

If the account has 2FA enabled, the first token request returns `202 Accepted`, signalling that a verification code is required. The user receives a code by SMS. Resubmit the same request with an added `otp` field:

```bash
curl -X POST https://api.virtuoussoftware.com/Token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=YOUR_EMAIL&password=YOUR_PASSWORD&otp=YOUR_OTP"
```

### HMAC-only endpoints

A small number of endpoints require HMAC authentication instead of a Bearer token – most notably `GET /api/Contact/ByReference/{referenceId}`, used to look up Contacts by an external reference ID. HMAC uses a different credential and signing mechanism. The spec flags these endpoints only with the note "HMAC Auth only" and gives no signing instructions. If you get a `401` on an HMAC-marked endpoint, contact Virtuous support for HMAC credentials before relying on it.

### Send the Bearer token

```bash
curl https://api.virtuoussoftware.com/api/Contact/4821 \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

Get the header shape exactly right – these are the most common `401` causes:

- Header name is `Authorization`; scheme is `Bearer` followed by a single space, then the token.
- No quotes around the token, no `=` or `:`, no URL-encoding. `Bearer "abc123"` and `Bearer  abc123` (two spaces) both return `401`.
- Values pasted from a secrets manager often carry surrounding quotes or trailing whitespace. Trim them.
- Include `Content-Type: application/json` on `POST`, `PUT`, and `PATCH`. It is optional on `GET` (no body).

### Credential security

> **Do:** Store every customer's key in a secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault, Doppler, 1Password). Use a separate key per customer. Rotate immediately on any suspected exposure. Redact the `Authorization` header in all HTTP logs.

> **Don't:** Commit a key to source control, put one in client-side JavaScript, pool one key across customers, or log a key anywhere – even in test. A single leaked key is a compromise and requires rotation.

## Base URLs and environments

There is one production host, no staging URL, and no version prefix in the base path. Reach an endpoint by appending its path to the base URL:

```text
GET https://api.virtuoussoftware.com/api/Contact/4821
```

A few resources are versioned in place with a `/v2/` path segment (for example `GET /api/v2/Pledge/{pledgeId}`). The host is unchanged; only that resource path carries the version.

### There is no test host – use a Seeded Sandbox

Every key connects to the same host. Isolation lives at the **organization** level: a key resolves to exactly one Virtuous organization, and a valid key writes to that organization's live data with no automatic rollback. A `POST /api/Gift` against a production nonprofit creates a real gift.

Virtuous provisions a **Seeded Sandbox** – a dedicated organization pre-loaded with representative Contacts, Gifts, Campaigns, and Designations. Its name typically ends with `(Sandbox)`. Request one from your Virtuous partner manager.

- Generate the sandbox's key inside the sandbox organization; treat it as fully independent from any production key.
- Verify write paths against the sandbox before pointing them at customer data.
- The sandbox is shared across your team and mutable until refreshed. Namespace test data (prefix Contact names or external reference IDs with a developer initial) to avoid collisions.

### Verify which organization a credential belongs to

Call `GET /api/Organization/Current` when onboarding any key. It is the fastest way to catch a misconfigured credential before it writes to the wrong organization.

```json
{
  "organizationUserId": 67890,
  "organizationName": "The Human Fund",
  "organizationTimeZone": "US/Arizona",
  "organizationCulture": "en-US",
  "currentUserTimeZone": "US/Arizona",
  "isAdministrator": true,
  "isEnabled": true
}
```

Store `organizationUserId` and `organizationName` alongside the key in your tenant config and compare them on each onboarding refresh to detect a customer rotating a key into a different organization. Also capture `organizationTimeZone`: Virtuous dates are stored in the organization's time zone, not UTC, so you need it to interpret date fields elsewhere. `isEnabled: false` means the organization is disabled (usually billing or administrative); treat it as a soft failure and surface a clear error rather than retrying.

### Multi-organization OAuth users

An OAuth user (for example a consultant) may belong to several organizations. API-Key integrations never switch – the key is bound to one organization.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/Organization` | List every organization the current user belongs to |
| `GET /api/Organization/Current` | Read the active organization for this session |
| `PUT /api/Organization/Switch` | Change the active organization by `organizationUserId` |

### Cross-product base URLs

Tokens are NOT interchangeable across products. Store a separate credential per product.

| Product | Base URL |
| --- | --- |
| CRM+ | `https://api.virtuoussoftware.com` |
| Raise | `https://prod-api.raisedonors.com` |
| Volunteer (VOMO) | `https://api.vomo.org/v1` |

## Make your first authenticated call

`GET /api/Organization/Current` is the canonical "is my credential working" check – no path params, no query, no body.

```bash
curl -i https://api.virtuoussoftware.com/api/Organization/Current \
  -H "Authorization: Bearer $VIRTUOUS_API_TOKEN"
```

The `-i` flag prints response headers so you can see the status and rate-limit headers. A `200 OK` whose `organizationName` matches the account you created the key in means you are ready to make real calls. Export the token first (`export VIRTUOUS_API_TOKEN="..."`); never paste a key into a shared terminal, notebook, or chat tool.

The workhorse read is the Contact query, which returns the standard pagination envelope:

```bash
curl -X POST https://api.virtuoussoftware.com/api/Contact/Query \
  -H "Authorization: Bearer $VIRTUOUS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "groups": [], "sortBy": "lastName", "descending": false, "skip": 0, "take": 10 }'
```

```json
{ "list": [ { "id": 4821, "name": "Wayne, Bruce" } ], "total": 4823, "skip": 0, "take": 10 }
```

`list` holds this page; `total` is the count across all pages. Advance by incrementing `skip` by `take`. `groups: []` returns all Contacts – it takes a structured filter object, not a free-text string. Discover available filter fields and operators with `GET /api/Contact/QueryOptions`.

## Rate limits

The limit is **5,000 requests per hour**, enforced per **Virtuous organization** – not per key or per token. Every credential issued inside an organization draws from the same hourly bucket, and so does every other integration the nonprofit runs. Budget your integration well below 5,000/hour to leave headroom for the customer's other callers. Each customer is a separate organization with its own independent budget, which is what makes a multi-customer integration viable.

### Rate-limit headers

Every response carries these. Read `X-RateLimit-Remaining` on each response and slow down as it approaches zero rather than waiting for a `429`.

| Header | Meaning |
| --- | --- |
| `X-RateLimit-Limit` | Total requests for the window (always `5000`) |
| `X-RateLimit-Remaining` | Requests left in the current window (whole-organization figure) |
| `X-RateLimit-Reset` | Unix timestamp (seconds) when the window resets to 5,000 |

### When you hit the limit

Exceeding the budget returns `429 Too Many Requests` with a `Retry-After` header (seconds to wait) and a JSON body:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 847
X-RateLimit-Remaining: 0

{ "error": { "code": "RATE_LIMITED", "message": "You have exceeded the request rate limit. Retry after 847 seconds.", "details": [] } }
```

The spec does not declare `429` on individual endpoints, but it can occur on ANY request. Handle it everywhere. Respect `Retry-After`, then add exponential backoff with jitter so parallel workers do not retry in lockstep:

```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 5) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${process.env.VIRTUOUS_API_TOKEN}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status !== 429) {
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      return await response.json();
    }
    if (attempt === maxRetries) throw new Error('Max retries reached.');

    const header = response.headers.get('Retry-After');
    const baseMs = header ? parseInt(header, 10) * 1000 : Math.min(1000 * 2 ** attempt, 60000);
    const jitter = baseMs * (0.8 + Math.random() * 0.4); // ±20%
    await new Promise((r) => setTimeout(r, jitter));
  }
}
```

### Stay within the limit

- **Use bulk and query endpoints.** `POST /api/Contact/Query`, `POST /api/Gift/Query`, `POST /api/Gift/Bulk` return or write many records per request. Never call `GET /api/Contact/{id}` in a loop. A single query with `take=1000` returns up to 1,000 records, so a paginated loop can pull ~1.5 million records/hour.
- **Use webhooks for change detection.** Webhook deliveries do NOT count against the limit. Polling burns the budget fast.
- **Do not poll more than once per minute** for any resource. For near-real-time updates, use webhooks.
- **Spread large batch jobs across the hour** rather than bursting, leaving room for webhook and UI-triggered traffic on the shared bucket.
- Adding a second key inside the same organization does NOT expand the budget – both keys share it. For a legitimate high-volume need (such as an initial historical migration), route the customer to Virtuous support for a per-organization exception.

## Error handling

Status code tells you the category; the body carries machine-readable codes and human-readable messages. The canonical shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request body contains invalid values.",
    "details": [
      { "field": "amount", "code": "MUST_BE_POSITIVE", "message": "Gift amount must be greater than zero." },
      { "field": "giftDate", "code": "REQUIRED", "message": "Gift date is required." }
    ]
  }
}
```

- `error.code` – `SCREAMING_SNAKE_CASE`, safe for `switch` statements.
- `error.message` – human-readable, safe to log, never contains stack traces.
- `error.details[]` – one entry per failing field (`field`, `code`, `message`); an empty `[]` means the error applies to the whole request. Surface `details[].message` to end users; branch on `details[].code`.

> **Gotcha – the body is not always JSON.** The API is still migrating to this shape. Some endpoints (notably `401`) return plain text such as `Authorization has been denied for this request.` Always inspect `response.status` FIRST, then attempt to parse. The spec does not document `401`, `403`, `422`, `429`, or `500` on individual endpoints, yet they all occur – handle them defensively everywhere.

### Status codes

| Status | Code | Meaning | Common cause |
| --- | --- | --- | --- |
| `400` | `BAD_REQUEST` | Malformed request | Invalid JSON, missing header, unparseable body |
| `401` | `UNAUTHENTICATED` | Auth failed | Missing header, expired OAuth token, revoked key |
| `403` | `FORBIDDEN` | Authorization failed | Valid credential, permission group lacks the resource |
| `404` | `NOT_FOUND` | Resource not found | The ID in the path matches no record |
| `409` | `CONFLICT` | State conflict | Duplicate record, uniqueness violation |
| `422` | `VALIDATION_FAILED` | Semantic validation failed | Valid JSON but a value breaks a business rule |
| `429` | `RATE_LIMITED` | Rate limit exceeded | Over the hourly budget – see Rate limits |
| `500` | `INTERNAL_ERROR` | Server error | Virtuous-side fault, not caused by your request |
| `503` | `SERVICE_UNAVAILABLE` | Temporary outage | Retry after the `Retry-After` header |

> **`404` is not "no matches".** A missing specific resource is `404`. An empty search on a list/query endpoint returns `200` with `"list": []` and `"total": 0`. Do not treat `404` as "no records found".

### Handle a validation error

```bash
RESPONSE=$(curl -s -o /tmp/body.json -w "%{http_code}" \
  -X POST https://api.virtuoussoftware.com/api/Gift \
  -H "Authorization: Bearer $VIRTUOUS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"contactId": 4821, "amount": -50}')

if [ "$RESPONSE" -ge 400 ]; then echo "Error $RESPONSE:"; cat /tmp/body.json; fi
```

A defensive client inspects status before parsing, falls back on plain text, and branches on the actionable codes:

```javascript
async function callCrmApi(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${process.env.VIRTUOUS_API_TOKEN}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json')
    ? await response.json()
    : { error: { code: 'UNKNOWN', message: await response.text() } };

  if (!response.ok) {
    const error = body?.error || {};
    switch (response.status) {
      case 401: throw new Error('Authentication failed – check your API token.');
      case 403: throw new Error('Permission denied for this resource.');
      case 422: {
        const fields = (error.details || []).map((d) => `${d.field}: ${d.message}`).join(', ');
        throw new Error(`Validation failed: ${fields}`);
      }
      case 429: throw new Error(`Rate limited – retry after ${response.headers.get('Retry-After') || '60'}s`);
      default: throw new Error(`API error ${response.status}: ${error.message}`);
    }
  }
  return body;
}
```

### Retry or not

| Category | Status codes | Retry? | Notes |
| --- | --- | --- | --- |
| Transient | `429`, `500`, `502`, `503`, `504` | Yes, with backoff | Respect `Retry-After` on `429` and `503` |
| Authentication | `401` | Only after refreshing | OAuth: one refresh + one retry. API Key: do not retry – the key is revoked. |
| Authorization | `403` | No | Same credential fails again; fix the permission group |
| Client error | `400`, `404`, `409`, `422` | No | The request must change; an identical retry gives an identical error |

### Cross-API note

CRM+ uses the `error.code` / `error.message` / `error.details[]` envelope. Raise uses an RFC 7807 shape (`title` / `status` / `detail`, field errors in a flat `errors` map). Detect the shape by checking whether the response root has `error` (CRM+) or `title` (Raise).

## Common pitfalls

- **Token expiry.** OAuth access tokens last only ~15 days; refresh before they lapse, and store the rotated refresh token each time. API Keys last 15 years but can be revoked in the UI at any time – a sudden `401` on a previously working key usually means revocation.
- **Wrong host on `404`.** The base URL is `api.virtuoussoftware.com`, not `www.` or `app.`. Paths begin with `/api/` and are case-sensitive. Substitute path params (`/api/Contact/4821`, not `/api/Contact/{contactId}`).
- **Writing to live data.** Any valid key writes to real records with no rollback. Verify with `GET /api/Organization/Current` and check for `(Sandbox)` before running write paths.
- **Prefer transaction endpoints for imports.** `POST /api/Contact/Transaction` and `POST /api/GiftTransaction` run Virtuous's nightly contact-matching and deduplication. They are safer than `POST /api/Contact` or `POST /api/Gift` directly, which skip matching and can create duplicates.
- **Shared rate budget.** Remaining capacity is org-wide, so another integration can exhaust the bucket. Read `X-RateLimit-Remaining`, not just your own request count.
- **Documentation inconsistency on the limit.** The authoritative limit is 5,000/hour (overview, rate-limits page, and the `X-RateLimit-Limit: 5000` header). The error-handling table's mention of "1,500 requests" and a `X-RateLimit-Remaining: 1499` sample elsewhere are stale doc figures – trust 5,000.
- **Debugging.** Use `curl -v` to confirm what is actually on the wire (a client library may drop or add a header). If `GET /api/Organization/Current` returns `200`, the credential is fine and the problem is the specific endpoint. Always read the error body.

## Quick reference

| Need | Do this |
| --- | --- |
| Auth for a service account | API Key in `Authorization: Bearer` |
| Auth as a specific user | OAuth password grant at `POST /Token`, `x-www-form-urlencoded` |
| Refresh OAuth | `grant_type=refresh_token`; save both new tokens |
| 2FA account | First call returns `202`; resubmit with `otp` |
| Confirm a credential | `GET /api/Organization/Current` |
| Fetch many records | `POST /api/Contact/Query` / `/api/Gift/Query`, `take` up to 1000, page with `skip` |
| Import Contacts/Gifts safely | `POST /api/Contact/Transaction`, `POST /api/GiftTransaction` |
| Avoid polling | Subscribe to webhooks (free of the rate limit) |
| Handle `429` | Respect `Retry-After`, back off with jitter |
| Handle `422` | Read `error.details[]`, fix fields, do not retry blind |

## Related skills

- `crm-concepts.md` – the Contact, Gift, and Designation data model these fundamentals sit on top of.
- `crm-workflows.md` – end-to-end recipes (create a contact, sync donations, reconcile failed syncs) built on transaction endpoints.
- `crm-best-practices.md` – performance, pagination, and multi-tenant patterns that extend the rate-limit guidance here.
- `crm-webhooks.md` – real-time change events that replace polling and do not count against the rate limit.
- `crm-api-contacts.md` – Contact, ContactIndividual, and address endpoints, including `Contact/Query` and transaction imports.
- `crm-api-giving.md` – Gift, recurring giving, pledge, and designation endpoints.
- `crm-api-campaigns-events.md` – campaign and event resource endpoints.
- `crm-api-system.md` – organization, query-options, and other system endpoints used for onboarding and credential verification.
