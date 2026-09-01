# Virtuous CRM+: Best practices
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

Production integration guidance for the CRM+ REST API. Host `https://api.virtuoussoftware.com`, base path `/api`. Auth is `Authorization: Bearer <token>`. This file is a checklist, not a tutorial – pair it with the sibling skills listed at the end.

## The two hard constraints

Almost every decision below traces back to one of these. Design against them from day one.

| Constraint | Implication |
| --- | --- |
| 5,000 requests/hour, per Virtuous organization | Every call counts. Sustained throughput above this needs an engineering exception. Treat it as a hard ceiling. The budget is **per customer org**, not per partner – with N customers you have N × 5,000/hour. |
| Transactions resolve asynchronously | Contact Transactions and Gift Transactions submit fast but resolve on the nightly batch. Submission is quick; resolution is not synchronous. Never block waiting for resolution. |

---

## 1. API performance

### Do / Don't

| Do | Don't |
| --- | --- |
| Use webhooks for change detection wherever Virtuous publishes the event. | Don't poll as the primary signal – every poll burns rate budget even when nothing changed. |
| Keep polling only as a reconciliation backstop (daily, not every 15 min). | Don't run `POST /api/Contact/Query` on a tight loop for freshness. |
| Request the abbreviated shape (`POST /api/Contact/Query`) for list/sync/export scans. | Don't call `POST /api/Contact/Query/FullContact` over a whole result set – it is meaningfully slower and costs hundreds of extra requests. |
| Set `take: 1000` (the cap) for bulk reads. | Don't accept the default `take` (as low as 25) for sync – 100K records becomes 4,000 requests instead of 100. |
| Push filters into the request body (`groups[].conditions[]`). | Don't over-fetch and filter client-side – wastes requests and bandwidth. |
| Cache stable reference data (see table below). | Don't cache specific Contacts/Gifts, query results, or webhook subscription details. |
| Pace dispatch with a rate limiter even when running concurrently. | Don't fire N requests concurrently with no throttle – 4 concurrent at 200 ms/req is ~72,000 req/hour, far over the ceiling. |
| Reuse HTTP connections (keep-alive, a pooled client / `Session()`). | Don't create a new client per request. |
| Acknowledge webhooks fast and queue the work. | Don't do heavy processing inside the webhook handler – timeouts trigger duplicate deliveries. |
| Check for a batch endpoint before looping a single-record one. | Don't loop `POST` per record when `POST /api/Tag/Bulk` or `POST /api/ContactNote/Bulk` exists. |

### Abbreviated scan + targeted full fetch

Cheap broad query, then fetch full detail only for the subset that needs it – together cheaper than a `FullContact` query over the whole set.

```javascript
const all = await pageThrough('/api/Contact/Query', {
  groups: [{ conditions: [{ parameter: 'Last Modified Date', operator: 'Is After', value: lastSync }] }],
  take: 1000,
});
for (const c of all.filter(needsFullDetail)) {
  const full = await get(`/api/Contact/${c.id}`);   // targeted, small subset only
  await process(full);
}
```

### Pagination: skip/take vs ID-cursor

| Strategy | Use when | Watch out |
| --- | --- | --- |
| `skip`/`take` | Small–medium sets (tens of thousands). Simple, the default. | Server-side query degrades at high `skip` (`skip=50000` is slow). Offsets shift under concurrent inserts – you re-process or miss rows. |
| ID-cursor | Very large or unstable sets, resumable exports. | Slightly more verbose; requires an indexed ID filter on Query. |

```javascript
let cursorId = 0;
while (true) {
  const page = await query({
    groups: [{ conditions: [{ parameter: 'Contact Id', operator: 'Greater Than', value: String(cursorId) }] }],
    sortBy: 'id', descending: false, skip: 0, take: 1000,
  });
  if (page.list.length === 0) break;
  process(page.list);
  cursorId = page.list.at(-1).id;   // bounded per query, stable under inserts, resumable
}
```

### Reference cache TTLs

| Cache (1 day unless noted) | Not cacheable |
| --- | --- |
| QueryOptions per resource type | Specific Contacts or Gifts (go stale fast) |
| Project list and codes | Query results (filter-dependent, complex invalidation) |
| Campaign list, Premium list | Webhook subscription details |
| Gift/Contact custom-field metadata | |
| RelationshipTypes (1 week – almost never changes) | |

Scope the cache per customer – different orgs have different Projects, Campaigns, and fields.

### Token bucket for steady-state pacing

Size below the ceiling (20% headroom) so cache refreshes don't spill into 429s. Bounded concurrency (4–8) controls burst; the bucket controls sustained rate.

```javascript
// 1,200 req/hour = 0.333/sec, capacity 20 for modest bursts
const bucket = new TokenBucket(20, 1200 / 3600);
async function limited(...args) { await bucket.acquire(); return fetch(...args); }
```

### Monitor these

`X-Rate-Limit-Remaining` trending to zero, any non-zero 429 count (throttle misconfigured), average and p95 latency, queue depth. Well-behaved integrations sit far below the ceiling – if you brush it routinely the cause is usually too-frequent polling, broad queries, or missing caching, not the limit itself.

---

## 2. Data modeling

### Contact type – choose at creation

`contactType` is `Household`, `Organization`, or `Foundation`. Changing it later is operationally awkward.

| Signal in source data | contactType |
| --- | --- |
| `business_name` populated, no individual first/last name | `Organization` |
| IRS Form 990 / Schedule I / grant-tracking conventions | `Foundation` |
| Everything else (default) | `Household` |

Ambiguous (sole proprietor giving from a business name with a personal email)? Default to `Household` and tag `Business-Donor` for staff to review.

### External reference – the most important modeling decision

Every match, dedup, and reconciliation depends on `referenceSource` + `referenceId`.

| Rule | Detail |
| --- | --- |
| `referenceSource` is fixed per integration | Same value (`Stripe`, `Mailchimp`, your platform name) for every write. Never vary by customer or environment. |
| `referenceId` is the source's stable primary key | Stripe Customer ID, your User ID. **Stable = survives every other field changing.** |
| The pair is unique across all your writes | One donor → exactly one (`source`, `id`) pair in Virtuous. |

Not stable: email, phone, name, address (donors change all of these). Stable: Stripe Customer ID, a real primary-key User ID.

> **Do not** use the donation's order ID as the Contact `referenceId` – the same donor giving twice then creates two Contacts. Use the donor's stable ID for the Contact reference; use the order/charge ID for the Gift `transactionId`.

No stable ID in the source? Generate a UUID once and persist it, or hash the most stable subset (`lowercase(email) + lowercase(lastName)`) for read-only sources.

### Project codes – the API primary key for designations

| Do | Don't |
| --- | --- |
| Use upper-case alphanumeric + hyphens (`CLEAN-WATER`, `GEN-FUND`). | Don't use cryptic codes (`P-2024-0317`) – they frustrate customer reporting. |
| Reuse year-agnostic codes (`GEN-FUND`). | Don't embed the year unless the Project is genuinely year-specific (`MARATHON-2024`). |
| Cache the destination→code mapping; validate against `GET /api/Project/Query` at startup and after customer changes. | Don't hardcode codes without validation. |

Split a Gift across `giftDesignations[]` only when the donor specifies multiple destinations, the source records multi-project intent, or customer policy allocates portions. Don't split as a workaround for a missing designation – flag it for staff.

### Tags vs custom fields

| Use a tag | Use a custom field |
| --- | --- |
| Value is boolean ("in segment X or not"). | Value is structured (date, number, dropdown, text). |
| Many records share it; you filter by it. | Value varies per record. |
| Owned by marketing/segmentation. | Owned by operations/finance. |
| Short, stable value list. | List changes often or is unbounded. |

Prefix integration-written tags so staff can tell them apart: `MC:`, `CC:`, `Stripe:`, `Auto:`. No prefix = customer-managed.

### Capture, don't infer

Store what your platform owns; query what Virtuous owns. Don't re-derive giving totals – Virtuous already computes `lifeToDateGiving`.

| Your platform owns | Virtuous owns |
| --- | --- |
| Identity on your platform (Stripe Customer ID, User ID) | Contact ID (identity inside Virtuous) |
| Donation event metadata (charge ID, payment method) | The Gift, designations, premiums, tax-deductible status |
| Your tags/lists/segments | The Contact's tags in Virtuous |
| Your calculated metrics | Giving totals, modification timestamps |

For mixed reports ("Gold-list donors who gave > $1,000"), pull the giving totals from Virtuous on demand rather than syncing and risking staleness.

### More modeling rules

- **Document per-field ownership** in a multi-integration environment. Outbound writes touch only fields you own; inbound handlers apply only fields the source owns. Otherwise two integrations overwrite each other.
- **Audit metadata → custom fields, not notes.** `Integration Source`, `Integration Version`, `First Synced At`, `Source Event ID` are queryable and don't clutter the Notes view. Reserve ContactNotes for human-readable content.
- **Relationships sparingly.** Only create ones you genuinely own, and only types configured in Virtuous (`GET /api/Relationship/Types`). When in doubt use a custom field and let staff formalize it.
- **Plan for reporting:** consistent tag/custom-field spelling (`Major Donor` ≠ `major_donor`), predictable Project codes, and a stable `originSegmentCode` (`STRIPE-DONATION`, `MAILCHIMP-SIGNUP`) for acquisition-channel splits. Confirm preferred values at onboarding.

---

## 3. Error recovery

### Classify first – three categories

| Category | Symptom | Recovery |
| --- | --- | --- |
| Transient | Network blip, brief platform hiccup, rate-limit spike | Retry with backoff |
| Persistent-recoverable | Expired credential, sustained rate limiting | Pause and alert – needs a human |
| Permanent | Malformed request, missing field, deleted resource | Stop and surface – never resolves on retry |

The common failure is treating all three alike. Retrying a permanent failure only adds noise; stopping on a transient one loses data.

### Status → category

| Status | Category |
| --- | --- |
| `400`, `403`, `422` | Permanent (malformed / permissions / validation) |
| `401` | Persistent-recoverable (credential – refresh needed) |
| `404` | Transient for 3–5 attempts over ~30 s (post-create indexing lag), then permanent |
| `409` | `concurrent_modification` = transient (GET-then-PUT); unique-constraint violation = permanent |
| `429` | Transient – honor `Retry-After` |
| `5xx`, network (ECONNREFUSED/ETIMEDOUT) | Transient |

### Exponential backoff with jitter

Quick first retry, longer later ones, jitter to avoid synchronized thundering herds, and a max-attempt bound. Don't retry `permanent` or `persistent_recoverable`.

```javascript
async function retryWithBackoff(fn, { maxAttempts = 5, baseDelayMs = 1000, maxDelayMs = 60000, jitter = 0.5 } = {}) {
  for (let attempt = 1; ; attempt++) {
    try { return await fn(); }
    catch (err) {
      const cat = classifyError(err.status, err.body, attempt);
      if (cat !== 'transient' || attempt === maxAttempts) throw err;   // permanent/persistent → escalate
      const delay = Math.min(baseDelayMs * 2 ** (attempt - 1), maxDelayMs);
      await sleep(delay + delay * jitter * Math.random());
    }
  }
}
```

For 429 specifically, prefer the `Retry-After` header – the server knows exactly when the window resets. For background work, raise `maxAttempts`/`maxDelayMs` for a longer budget.

### Idempotency is the precondition for safe retries

| Write | Idempotent when |
| --- | --- |
| `POST /api/v2/Gift/Transaction` | carries stable `transactionSource` + `transactionId` |
| `POST /api/Contact/Transaction` | carries stable `referenceSource` + `referenceId` |
| `POST /api/Contact` (direct) | **never** – each call creates a new Contact |
| `PUT /api/Contact/{id}` | always (same body → same state) |

Use stable, deterministic keys – never random per-attempt UUIDs. For non-idempotent writes, after a timeout/reset **check whether it actually completed before retrying**:

```javascript
catch (err) {
  if (err.code === 'ETIMEDOUT' || err.code === 'ECONNRESET') {
    const existing = await findContactByReference(donor.referenceSource, donor.referenceId);
    if (existing) return existing;   // it succeeded server-side; don't create a duplicate
  }
  throw err;
}
```

### Dead-letter queue

Route permanent + persistent-recoverable failures to a DLQ (customer_id, operation_type, original_payload, status_code, attempt_count, resolution). It gives visibility, replay (re-submit the original payload after a fix), and audit. Offer **replay as-is / fix-and-replay / discard** in an admin UI. Review the DLQ on a daily/weekly cadence and alert on depth growth – an ignored DLQ silently accumulates.

### Circuit breaker

Stop hammering a failing downstream so it can recover. States: **closed** (pass through, count failures) → **open** (fail fast for a cool-down) → **half-open** (one test request) → closed on success. One breaker **per logical downstream** – a failing Virtuous endpoint must not block your Mailchimp sync. Tune by traffic: high-traffic → higher threshold (~20), shorter open (30 s); low-traffic → lower threshold (~5), longer open (5 min).

### Reconciliation is the safety net

Retries handle transient failures, DLQs handle permanent ones, but some failures leave inconsistent state with **no error** (a timed-out write that actually succeeded, an exhausted webhook retry). Periodically compare partner-side vs Virtuous-side state and surface discrepancies. **Assume your retry logic is imperfect and design reconciliation that doesn't depend on it being correct.**

### Observability

- **Structured logs** with customer_id, record id, `X-Request-Id` (lets Virtuous correlate their logs), status_code, attempt.
- **Metrics per category:** `...failures{category="transient"}` (expected > 0, don't page), `persistent_recoverable` (should be near zero – alert), `permanent` (investigate), `dead_letter_queue_depth`, `circuit_breaker_state`.
- **Baseline** the normal failure rate per category; 0.5% transient may be fine, a jump to 5% is not. Test failure paths in staging (inject network loss, mock 429s, send malformed payloads).

---

## 4. Security and credential management

### Store secrets correctly

| Do | Don't |
| --- | --- |
| Use a dedicated secrets manager (AWS/GCP/Azure), self-hosted Vault, or an encrypted DB column with a rotated KMS key. | Env vars in deployment manifests (visible to deployers, logged, not auditable). |
| Scope keys: `virtuous/{env}/{customer_id}/api_token`. | `.env` files in source control (in git history forever). |
| Per-customer access scoping; no human read access in production; audit-log every read. | Plaintext DB columns or hardcoded secrets. |

### Rotation

API tokens: every 90 days (high-sensitivity) to 6–12 months (lower). Flow: generate new in Virtuous → store alongside old ("pending") → cut over reads → validate a live call → retire and revoke old. Build this in from the start.

### Webhook secrets

The **integration generates** these (you supply `secret` in `POST /api/Webhook`). Use ≥ 32 bytes of CSPRNG entropy and **never reuse a secret across customers**. Store at `virtuous/{env}/{customer_id}/webhook_secret`. Rotation needs a window where the verifier accepts both old and new.

```javascript
crypto.randomBytes(32).toString('base64');   // per-customer webhook secret
```

### OAuth / source-platform credentials

| Credential | Handling |
| --- | --- |
| Refresh token (long-lived) | Protect like an API token – secrets manager. Persist a rotated refresh token if the flow returns a new one. |
| Access token (short-lived) | Cache in memory or short-TTL Redis keyed to its expiry. **Don't** write it to the secrets manager – churny and wasteful. |

A revoked grant (`invalid_grant` / `unauthorized`) is a customer-side event, not a bug: **pause that customer's sync and notify them in your UI** – don't retry.

### Network and PII

- **TLS everywhere** with a valid public-CA cert; reject invalid certs and plain HTTP (don't override the runtime default).
- **Egress IP allowlisting:** run behind a stable-IP NAT, document the IPs, notify customers before they change.
- **Harden the webhook receiver:** HTTPS-only, edge rate limiting, WAF, signature verification on every request, reject unexpected Content-Type and oversize bodies.
- **Don't log PII.** Reference donors by Contact ID / your user ID, never name/email. **Don't log request bodies in error paths** – they contain donor PII; log status, message, request id instead. Scrub PII from error responses you return to customers' developers.

### Retention

| Data | Retention |
| --- | --- |
| Active sync state | Indefinite while customer active |
| Dead-letter entries | 90 days after resolution, then archive |
| Reconciliation logs | 1 year, then archive |
| Worker logs with identifiers | 30 days hot, 1 year cold |
| Webhook delivery captures | 30 days |

Delete old rotated credentials from the secrets manager – don't just mark them inactive.

### Onboarding / offboarding

- **Onboarding:** receive the token through your UI (not email), validate with a low-impact call before storing, store under the scoped path, create the webhook subscription with a fresh secret, run initial reconciliation, confirm in the UI.
- **Offboarding:** stop syncing → `DELETE /api/Webhook/{webhookId}` → revoke the API token → delete all customer secrets → delete/anonymize customer data per retention + GDPR/CCPA → confirm to the customer. **Deletion is the step most integrations get wrong** – stale sync rows, DLQ entries, and logs linger. Have a documented, tested deletion process.

### Least privilege

Request only the permissions the integration uses (e.g. write Gifts + read Contacts), not "all access" – a narrower compromised token is less damaging. Document the required permission set in your setup docs. (The exact CRM+ permission groups are an admin-side concern; walk through them with the customer's admin at onboarding.)

### Incident response

- **Suspected token compromise:** rotate immediately (cheap even if unconfirmed) → audit recent writes → check secrets-manager access logs for unexpected accessors → report transparently to the customer.
- **Webhook signature failures spike:** either a forgery attempt or a rotation problem – alert and investigate quickly.

---

## 5. Sync architecture

### Building blocks

Source event capture (webhook / poller / CDC) → outbound queue → submitter → Virtuous; plus an inbound event handler and a state store. Every recipe is an assembly of these five.

### Patterns

| Pattern | Use when |
| --- | --- |
| 1. One-way push, event-driven | Source has webhooks; near-real-time needed. The default for payment processors / fundraising platforms / ESPs. |
| 2. One-way push, polled | Source has no webhooks (or a tier the customer lacks); hourly/daily freshness is fine. Hybrid = webhooks for some events, polling for the rest, into one queue. |
| 3. One-way pull, Virtuous → partner | Partner is a reporting tool / BI / warehouse; Virtuous is source of truth. |
| 4. Two-way sync | Data lives in both systems and must stay consistent. |
| 5. Bulk load + steady-state | New customer with historical data: import "everything before today", then sync "everything after". |

**Two-way sync's hardest problem is the sync loop:** a write on one side fires a webhook that writes the other side that fires a webhook back. Defense = source identification (`transactionSource`/`referenceSource` mark records you wrote) + per-record sync state, so the inbound handler distinguishes "from us" vs "from elsewhere". Roll out behind a feature flag, processing only "from elsewhere" first, and watch request volume on both sides.

**Pattern 5: share the queue** between the one-time bulk loader and the steady-state capture. The submitter drains both, so the same idempotency, throttling, and monitoring cover both. Don't build separate bulk-only and steady-state-only paths – they drift on edge cases.

### State: checkpoints and per-record status

Incremental sync tracks a high-water mark (watermark) per customer, resource, and direction:

```sql
CREATE TABLE sync_checkpoints (
  customer_id TEXT, resource_type TEXT,          -- 'contact' | 'gift'
  direction TEXT,                                -- 'inbound' | 'outbound'
  last_processed_timestamp TIMESTAMPTZ,
  last_processed_id TEXT,
  PRIMARY KEY (customer_id, resource_type, direction)
);
```

Next run queries `Last Modified Date Is After <last_processed_timestamp>`, then advances the watermark. Per-record status (`pending`/`submitted`/`confirmed`/`failed`, plus `virtuous_id`, `partner_modified_at`, `virtuous_modified_at`) enables idempotency, reconciliation, and audit.

### Multi-tenant isolation

Scope by `customer_id` on every axis: credentials, queues (a busy customer must not starve others), workers, state, and **rate-limit budget (per-customer-org – they don't share)**, and alerting. Per-customer workers/cron slots give clean blast-radius isolation. A single multi-tenant worker processing one customer at a time is fine for 10–20 customers; go per-customer for larger scale.

### Anti-patterns

| Anti-pattern | Why it fails | Fix |
| --- | --- | --- |
| Synchronous write inside the source webhook handler | If Virtuous is slow, the source's delivery times out and retries – duplicate processing. | Capture into a queue and ack immediately. |
| One global rate limiter | Rate limit is per-customer-org; a global limiter under-uses N × 5,000/hour and lets one customer's burst starve others. | Per-customer limiters. |
| No state, re-run the whole sync on interruption | Re-processes everything; without idempotency keys that's mass duplication. | Checkpoint + per-record state. |
| Retry forever | Permanent failures never resolve – consumes resources, hides the problem. | Bound retries, surface to humans. |

### Evolving between patterns

- **Polled → event-driven:** add the webhook receiver feeding the same queue, run both in parallel a week or two to confirm parity, then demote polling to a daily backstop (keep or retire depending on the source's webhook reliability).
- **One-way → two-way:** subscribe to Virtuous webhooks, migrate to per-record sync state *first*, implement source identification, roll out "from elsewhere" only, then full inbound – behind a flag, watching for loops.
- **Single → multi-tenant:** add `customer_id` everywhere, make workers customer-aware, move credentials to a secrets manager. The second customer surfaces the bugs (hardcoded values that were customer-specific, shared state that should have been scoped).

---

## 6. Versioning and backward compatibility

CRM+ uses **partial versioning**: most endpoints are unversioned `/api/…` (effectively v1); a subset is `/api/v2/…`. There is no `/api/v1/` prefix.

### What is on `/v2/` today

| Family | Endpoints |
| --- | --- |
| Gift Transaction submission | `POST /api/v2/Gift/Transaction` (single), `POST /api/v2/Gift/Transactions` (batch) |
| Pledge management (entire family) | `POST /api/v2/Pledge`, `GET /api/v2/Pledge/{id}`, `GET /api/v2/Pledge/ByContact/{contactId}`, `POST /api/v2/Pledge/Query`, `GET /api/v2/Pledge/QueryOptions`, `GET /api/v2/Pledge/CustomFields`, `PUT /api/v2/Pledge/WriteOff/{id}` |

**Prefer the `/v2/` variant when it exists.** There's no documented reason to call `/api/Gift/Transaction` (non-v2) for a new integration. Contact, Project, RecurringGift, Webhook, and most Query endpoints remain unversioned.

### Spec vs live field typing – a real, current mismatch

The OpenAPI spec types many fields as `string` that the live API accepts and returns as native types.

| Spec says `string` for | Live accepts | Live returns |
| --- | --- | --- |
| booleans (`isPrivate`) | `true`/`false` and `"true"`/`"false"` | native `true`/`false` |
| integers (`anniversaryYear`) | `2010` and `"2010"` | native `2010` |
| dates (`birthDate`) | ISO 8601 `"1972-02-19"` | ISO 8601 string |
| amounts | `500.00` or `"500.00"` | sometimes native, sometimes string |

Send native types in requests; parse defensively in responses (coerce `"true"`→`true`, `parseFloat` string amounts). **Don't trust auto-generated SDKs that strictly enforce the spec types** – they send string booleans and reject native responses.

### Backward-compatibility assumptions

| Safe to assume stable | May change without notice | Ambiguous – code defensively |
| --- | --- | --- |
| Existing endpoint paths | New fields in responses | New required field on an existing body (treat as breaking) |
| Existing request/response field names | New optional request fields | Status code change (audit found a `200` where spec implies `201`) |
| Envelope shape (`list`/`total`, `error.details[]`) | New webhook event types | Field type on the wire (string↔number – happens routinely) |
| Auth mechanism (Bearer, header name) | New enum values, changed error text, new endpoints, perf | |

### Defensive coding checklist

- Endpoint URLs are constants in **one** place (a base-path map per endpoint family), never hardcoded throughout – a future version bump is then one edit.
- Access response fields by name with defaults; don't strict-destructure or `.strict()`-validate (breaks on added fields).
- Parsers handle both native and string forms of booleans, integers, amounts, and dates.
- Webhook handlers switch on **known** event types and ignore unknown ones.
- Don't hardcode enum lists for client-side validation – let the API reject invalid values.
- Retry logic branches by status class (`2xx`/`4xx`/`5xx`) with explicit cases for `401`/`404`/`409`/`422`/`429`.
- Log or metric-count `Sunset` and `Deprecation` response headers – they aggregate into the next migration's work list.
- Review any spec-generated SDK before adopting it.

### Migrating a deprecated endpoint

Watch for a `Sunset` header (removal date), `Deprecation: true`, a spec `deprecated: true`, or a changelog/support announcement. Then: read the new endpoint's docs → implement behind a feature flag alongside the old path → verify parity on the **Seeded Sandbox** → migrate customers gradually with per-customer flags (roll back on issues) → delete the old path once everyone is migrated.

---

## Related skills

- [crm-fundamentals.md](crm-fundamentals.md) – auth, base URLs, rate limits, pagination mechanics.
- [crm-concepts.md](crm-concepts.md) – Contacts, Gifts, Projects/designations, custom fields, transactions, field typing.
- [crm-workflows.md](crm-workflows.md) – two-way sync, reconcile failed syncs, handle duplicate records, query by filters.
- [crm-webhooks.md](crm-webhooks.md) – webhook subscription, signature verification, idempotency, secret rotation.
- [crm-recipes.md](crm-recipes.md) – nightly data sync, import historical gifts, Stripe/Mailchimp/Constant Contact integrations.
- [crm-api-contacts.md](crm-api-contacts.md) – Contact and Contact Transaction endpoint reference.
- [crm-api-giving.md](crm-api-giving.md) – Gift, Gift Transaction (v2), RecurringGift, and Pledge (v2) endpoint reference.
