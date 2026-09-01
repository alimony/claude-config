# Virtuous CRM+: Webhooks
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

Webhooks push real-time notifications to a URL you control when records change in a nonprofit's Virtuous organization (new Gifts, updated Contacts, deleted Projects). They are the recommended pattern for any partner integration that reacts to change – use them instead of polling.

- Host: `https://api.virtuoussoftware.com`, base path `/api`.
- Auth for subscription management: `Authorization: Bearer YOUR_API_TOKEN`.
- Deliveries are `POST` with `Content-Type: application/json` to your `payloadUrl`.

## Why webhooks over polling

| Dimension | Webhook | Poll |
| --- | --- | --- |
| Freshness | Delivers within seconds | Runs on your interval (minutes/hours) |
| Cost | Deliveries do **not** count against your hourly rate limit | Every scan counts, even when nothing changed |
| Completeness | Fires for changes from any source (your integration, other integrations, manual UI edits, nightly batch) | Only sees changes before your last query timestamp |

> **Do** use webhooks as the primary change signal, and use Query endpoints with `modifiedDateTimeUtc` filters only as a reconciliation backstop.
> **Don't** poll as the primary mechanism – it is slower, spends rate-limit budget, and misses concurrent edits.

## The flow

1. **Subscribe** – `POST /api/Webhook` with a payload URL and the event toggles you want. Response returns the subscription `id` and echoes the `secret`.
2. **Receive** – Virtuous `POST`s the event payload to your `payloadUrl` when a subscribed event occurs.
3. **Verify and process** – verify the request signature, then handle the event.
4. **Acknowledge** – return any `2xx`. Non-`2xx` (or timeout) triggers retries.

---

## Event types

CRM+ exposes **15 event toggles** on the subscription object, spanning six resource families. Each is independently switchable; subscribe only to what you process.

> **Confirmed vs unconfirmed:** the OpenAPI spec confirms the *set* of event types (the boolean toggle fields) but does **not** publish a payload schema for any individual event. Payload highlights below reflect the related resource schemas and typical webhook patterns – confirm exact shapes with Virtuous engineering before building production handlers.

| Event | Toggle field | Fires when | Payload highlights |
| --- | --- | --- | --- |
| Contact created | `contactCreate` | New Contact via UI, `POST /api/Contact`, or a Contact/Gift Transaction batch that matched nothing | Full Contact record (id, name, contactType, ContactIndividuals, addresses, contact methods, tags, custom fields) |
| Contact updated | `contactUpdate` | Existing Contact changes: manual edit, `PUT /api/Contact/{id}`, Transaction merge, archive/unarchive | Full updated Contact record (no changed-fields diff – compare against your stored copy) |
| Gift created | `giftCreate` | New Gift via `POST /api/Gift`, Gift Transaction batch, manual entry, recurring payment, or pledge payment | Gift record with designations, premiums, contact reference; `transactionSource` + `transactionId` if it came from a Transaction |
| Gift updated | `giftUpdate` | Existing Gift changes: designation reallocation, batch reassignment, manual correction | Full updated Gift record |
| Gift deleted | `giftDelete` | Gift permanently removed (rare; usually manual admin action) | Identifies the deleted Gift only; no post-deletion record |
| Project created | `projectCreate` | New Project via UI or `POST /api/Project` | Full Project record |
| Project updated | `projectUpdate` | Existing Project changes: lifecycle flags (`isActive`, `isPublic`, `isAvailableOnline`, `isTaxDeductible`), balance, name/code | Full updated Project record |
| Project deleted | `projectDelete` | Project permanently removed (uncommon; usually archived instead) | Identifies the deleted Project only |
| Form submission | `formSubmission` | Donor/constituent submits a Virtuous-hosted form | Submitted field values plus any Contact/Gift created or matched; shape varies per org's form config |
| Contact note created | `contactNoteCreate` | Note added to a Contact | ContactNote record attached to a Contact |
| Contact note updated | `contactNoteUpdate` | Existing note edited | Updated ContactNote record |
| Contact note deleted | `contactNoteDelete` | Note removed from a Contact | Identifies the deleted note |
| Event created | `eventCreate` | New program/calendar Event (gala, conference, volunteer day) | Full Event record (a Virtuous *Event* record, not the webhook event) |
| Event updated | `eventUpdate` | Existing program Event changes | Updated Event record |
| Event deleted | `eventDelete` | Program Event removed | Identifies the deleted Event |

**Reasonable starting subscription** for a donor-sync integration: `contactCreate`, `contactUpdate`, `giftCreate`, `giftUpdate`, plus `projectUpdate` to keep a cached Project list current. Add `giftDelete` / `projectDelete` only if you soft-delete on your side. Add ContactNote and Event families only if you use them. Skip `formSubmission` unless your integration is form-aware.

> **Don't** subscribe to events you do not process – it loads your endpoint and muddies log analysis. Start minimal and add toggles as needs emerge.

---

## Registering and managing subscriptions

A subscription says (a) where to deliver and (b) which events. You provide the `secret`; Virtuous does not generate it.

### Create

```bash
curl -X POST https://api.virtuoussoftware.com/api/Webhook \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payloadUrl": "https://your-integration.example.com/virtuous/webhook",
    "secret": "your-randomly-generated-secret",
    "contactCreate": true,
    "contactUpdate": true,
    "giftCreate": true,
    "giftUpdate": true,
    "active": true
  }'
```

A successful response echoes the full subscription record, including `id` (store it) and every toggle field. Omitted toggles default to `false`.

### Management endpoints

| Endpoint | Use |
| --- | --- |
| `GET /api/Webhook/{webhookId}` | Retrieve one subscription by ID |
| `POST /api/Webhook` | Create a subscription |
| `PUT /api/Webhook/{webhookId}` | Update: change payload URL, rotate secret, or modify event toggles |
| `PUT /api/Webhook/{webhookId}/Active?active=true` (or `false`) | Toggle the `active` flag in one call |
| `DELETE /api/Webhook/{webhookId}` | Permanently delete the subscription |

> **There is no "list all subscriptions" endpoint** in the CRM+ spec. Persist the `id` returned from `POST /api/Webhook` in your own database at creation time – that is the only reliable way to find your subscriptions later.

**Updating toggles:** `PUT` replaces the record, so send the *full* set of fields you want retained – payload URL, secret, and every event toggle. A `GET`-then-`PUT` pattern avoids silently disabling toggles you previously enabled.

**Rotating the secret:** generate a new value and `PUT` it. The new secret takes effect on the next delivery. During the rotation window your verifier must accept both old and new secrets, because in-flight deliveries may still carry the old signature. The safe pattern: keep a list of valid current-and-recent secrets, accept a signature matching any of them, and drop the old one once no old-signed deliveries are still arriving.

### Subscription fields

Non-toggle fields: `id` (integer, primary key), `payloadUrl` (string, HTTPS URL accepting `POST` + JSON), `secret` (string, you supply it; store it in a secrets manager), and `active` (boolean; `true` delivers, `false` drops events without queuing). The remaining 15 fields are the event toggles from the [event table](#event-types) above; all default to `false` when omitted.

**Generate the secret** with a cryptographically secure random source of at least 32 bytes, for example `crypto.randomBytes(32).toString('base64')` (Node), and store it in a secrets manager. Treat it like an API key; never commit it.

### Endpoint requirements

| Requirement | Why |
| --- | --- |
| HTTPS only, public CA cert | Virtuous does not deliver to plain HTTP |
| Accept `POST` + JSON body | All deliveries are `POST` with `Content-Type: application/json` |
| Return `2xx` on success | Any `2xx` (`200`/`204`) acknowledges; non-`2xx` triggers retries |
| Respond fast | Acknowledge inside the timeout window; defer heavy work to a queue |
| Idempotent processing | Retries redeliver the same event; the same payload twice must produce one result |

> **Unconfirmed:** the exact delivery timeout is not in the OpenAPI spec. Assume the industry-standard 10–30 seconds and size your endpoint to acknowledge well inside it.

---

## Payload envelope

Every delivery is a `POST` with a JSON body that identifies the event, the affected resource, and the change. Exact field names are **not published**; treat the shape below as "expect something equivalent," not literal keys.

```json
{
  "eventType": "contact.created",
  "eventId": "evt_abc123",
  "timestamp": "2024-12-15T14:30:00Z",
  "organizationId": 67890,
  "data": { "id": 4821, "...": "the full resource record" }
}
```

What is reliable regardless of exact names:

- **The event type is identifiable from the payload itself** – route by inspecting the body, not just the request shape.
- **A unique event identifier is present** – use it as the idempotency key.
- **A timestamp is present** – use it for ordering when out-of-order delivery is possible.
- **The affected resource is embedded** – you rarely need a follow-up `GET`, which matters because a per-event `GET` would spend rate-limit budget.

---

## Signature verification

Verify **every** incoming request before processing. Without it, anyone who learns your `payloadUrl` can post fake events (fraudulent gifts, unauthorized contact edits, manipulated reporting).

A valid signature proves **authenticity** (only a holder of the `secret` could produce it) and **integrity** (it is computed over the body, so any tampering invalidates it). It does **not** prove **freshness** (a replayed request still verifies – see replay protection) or **authorization** (whether you should act on the event is business logic).

> **Unconfirmed:** the exact scheme (header name, algorithm, signed-string format) is **not documented** in the spec. The pattern below is the industry standard CRM+ is presumed to follow: HMAC-SHA256 (hash-based message authentication code) over the raw request body, hex-encoded, delivered in a request header. Confirm with Virtuous engineering and adjust the header constant and body format before production.

### The algorithm, step by step

1. Virtuous computes `signature = HMAC-SHA256(secret, raw_request_body)` at delivery time.
2. It sends the signature in a request header, presumed `X-Virtuous-Signature`.
3. Your receiver reads the **raw** body (before any JSON parse), computes the same HMAC with your stored secret, and compares the two in **constant time**.
4. Match → accept. Mismatch → reject with `401 Unauthorized`.

Two non-obvious requirements:

- **Use the raw body bytes.** Parsing JSON then re-serializing changes whitespace, key order, and number formatting, all of which break the signature.
- **Compare in constant time.** A naive `===` short-circuits on the first differing byte and leaks timing that lets an attacker iterate toward a valid signature. Use `crypto.timingSafeEqual` (Node) or `hmac.compare_digest` (Python).

### Verifier (Node.js)

```javascript
import crypto from 'crypto';

// Header name is presumed; confirm and update once published.
const SIGNATURE_HEADER = 'x-virtuous-signature';

export function verifyVirtuousSignature(rawBody, headers, secret) {
  const received = headers[SIGNATURE_HEADER];
  if (!received) return false;

  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)              // rawBody is a Buffer, not parsed JSON
    .digest('hex');

  const a = Buffer.from(expected, 'hex');
  const b = Buffer.from(received, 'hex');
  if (a.length !== b.length) return false;   // timingSafeEqual requires equal length
  return crypto.timingSafeEqual(a, b);
}
```

### Receiver (Express) – capture the raw body

```javascript
import express from 'express';
import { verifyVirtuousSignature } from './signature-verification.js';

const app = express();

app.post(
  '/virtuous/webhook',
  // Capture raw bytes for verification. Do NOT use express.json() here –
  // it parses and discards the raw body, breaking the signature.
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const secret = process.env.VIRTUOUS_WEBHOOK_SECRET;
    if (!verifyVirtuousSignature(req.body, req.headers, secret)) {
      // Log context to investigate – but never the raw body, secret, or signature.
      console.warn('Webhook signature verification failed', { ip: req.ip });
      return res.status(401).send('Invalid signature');
    }

    const event = JSON.parse(req.body.toString('utf8'));
    res.status(200).send('OK');        // acknowledge first
    await enqueueForProcessing(event); // then hand off to a durable queue
  }
);

app.listen(3000);
```

Python is the same shape: `hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()` compared with `hmac.compare_digest(expected, received)`.

> **Do** load the secret from a secrets manager, run verification before any processing, and alert on sustained `401`s (a strong signal of attack or misconfiguration).
> **Don't** hardcode the secret, log the raw body/secret/signature, or verify against re-serialized JSON.

**Expected, legitimate failures:** a **secret rotation in flight** (accept old and new secrets during the window), or **a proxy that modified the body** (some load balancers and web application firewalls re-encode bodies; configure the proxy to pass the body through unmodified).

### Replay protection (verification alone does not cover it)

A captured request replays with a valid signature. Two complementary defenses:

**1. Timestamp window** – reject events older than a short window (for example, five minutes). Only meaningful if the timestamp is **inside the signed body**; a timestamp in an unsigned header can be rewritten.

```javascript
const MAX_AGE_SECONDS = 5 * 60;
function isFresh(event) {
  if (!event.timestamp) return false;
  return (Date.now() - new Date(event.timestamp).getTime()) / 1000 < MAX_AGE_SECONDS;
}
```

**2. Event-ID idempotency** – track processed event IDs and drop repeats. This is the same mechanism you need for retries (next section), so it is the primary defense; keep records for at least your replay window (24 hours is a reasonable minimum).

---

## Idempotency and safe processing

**Assume every event is delivered at least twice** over the life of your integration, even on a healthy system. Duplicates are normal, not exceptional.

Four causes:

| Cause | What happens |
| --- | --- |
| Retry after timeout | You processed the event but responded too slowly; Virtuous retries |
| Network glitch | Your `2xx` is lost in transit; Virtuous never sees it and retries |
| Crash mid-acknowledgement | You processed, then crashed before responding |
| Replay / accidental re-delivery | A captured delivery is replayed by an attacker or a misbehaving proxy |

### Why a plain database write is not enough

Idempotency via database uniqueness works for "make the row look like this" operations and **fails** for "do this thing once" operations:

| Operation | Idempotent via DB uniqueness alone? |
| --- | --- |
| Upsert by Virtuous ID (`INSERT ... ON CONFLICT DO UPDATE`) | Yes |
| Insert with auto-generated ID | No – each delivery makes a new row |
| Increment a counter | No – each delivery increments |
| Send an email / charge a card / call a downstream API | No – each delivery repeats the side effect |
| Append to an audit log | No – each delivery appends |

Most real integrations have at least one "do this once" side effect, so they need an explicit idempotency key.

### The idempotency-key pattern (three states)

Track each event ID through **unclaimed → claimed → completed**. Two states ("seen"/"unseen") race under concurrent delivery: both copies see "unseen" and both run. Three states let the first delivery atomically claim, so the second skips.

```javascript
async function processWebhookEvent(event) {
  const claim = await idempotencyStore.claim(event.eventId); // atomic compare-and-set
  if (claim.alreadyProcessed) {
    console.info('Skipping duplicate', { eventId: event.eventId });
    return;
  }
  try {
    await handleEvent(event);                    // includes side effects
    await idempotencyStore.complete(event.eventId);
  } catch (err) {
    await idempotencyStore.release(event.eventId); // let a retry try again
    throw err;
  }
}
```

Backing stores that support an atomic claim:

```javascript
// Redis: SET NX returns null if the key already exists (already claimed).
const result = await redis.set(`idem:${eventId}`, 'claimed', 'NX', 'EX', 86400);
const alreadyProcessed = result === null;

// PostgreSQL: zero rows affected means it was already claimed.
// INSERT INTO webhook_events (event_id, status, claimed_at)
//   VALUES ($1, 'claimed', NOW()) ON CONFLICT (event_id) DO NOTHING;
```

A relational table is the simplest and most observable choice. Redis is faster but needs careful TTL (time-to-live) management. A managed queue's built-in dedup (for example, AWS SQS FIFO `MessageDeduplicationId`) is convenient but its window is short (5 minutes on SQS), too short to catch late retries.

**Retention:** keep idempotency records for at least the maximum retry window. Default to 30 days; 7 days is defensible for very high volume if you have good observability on retry-driven duplicates.

### Process asynchronously

The handler's only synchronous job is to verify and enqueue. Everything else runs in a background worker. This isolates your acknowledgement latency from slow downstream dependencies, so transient slowness does not turn into timeouts and retries.

> **Do** enqueue onto a **durable** queue (SQS, Google Cloud Tasks, Pub/Sub, Redis Streams with persistence) before acknowledging.
> **Don't** rely on an in-memory queue (`setImmediate`, an in-process pool) – if the process crashes between acknowledging and processing, the event is lost and your `2xx` was a lie.

### Side-effect ordering – use one atomic mechanism

Splitting "do the side effect" and "mark complete" across two awaits is unsafe in either order: crash between them and you either repeat the side effect or skip it forever. Fix it by committing the side-effect *intent* atomically with completion.

```javascript
// ❌ crash between these repeats the email
await sendThankYouEmail(event.contact);
await idempotencyStore.complete(event.eventId);
```

**Option A – transactional outbox.** Mark complete and record the side-effect intent in the same transaction; a separate worker drains the outbox with its own idempotency.

```javascript
await db.transaction(async (tx) => {
  await tx.complete(event.eventId);
  await tx.outbox.insert({ type: 'send_email', contactId: event.data.id, template: 'thank_you' });
});
```

**Option B – idempotency keys on downstream APIs.** Derive a key from the event ID plus side-effect type (`${eventId}-email`, `${eventId}-stripe-charge`) and let the downstream service (Stripe, SendGrid, Twilio) dedup.

For multiple side effects per event, prefer the outbox.

### Out-of-order deliveries

Retries can deliver events out of chronological order. For state updates, order by the **payload timestamp**, not receipt time: compare the event's `modifiedDateTimeUtc` against your stored copy and skip stale updates.

```javascript
async function handleContactUpdated(event) {
  const stored = await db.contacts.find({ virtuousId: event.data.id });
  if (stored && new Date(stored.modifiedDateTimeUtc) >= new Date(event.data.modifiedDateTimeUtc)) {
    return; // stored record is newer – skip
  }
  await db.contacts.upsert({ virtuousId: event.data.id, ...event.data });
}
```

This is naturally idempotent for state updates but does **not** cover side effects – pair it with the idempotency-key store, do not use it as a replacement.

### Cross-source duplicates (partner-specific)

If you both submit Transactions and subscribe to webhooks, your own `POST /api/v2/Gift/Transaction` eventually fires a `giftCreate` back to you. Match on the `transactionSource` / `transactionId` pair you sent, and update your existing row instead of inserting a second gift.

```javascript
async function handleGiftCreated(event) {
  if (event.data.transactionSource === 'YourPlatform') {
    await db.gifts.update(
      { transactionId: event.data.transactionId },
      { virtuousGiftId: event.data.id, status: 'confirmed' }
    );
    return;
  }
  await db.gifts.insert({ /* created elsewhere – capture as new */ });
}
```

The `giftCreate` event is also the canonical signal that your submitted Gift Transaction succeeded.

---

## Retry behavior

When a delivery fails (non-`2xx`, timeout, unreachable), Virtuous retries. Retries are your safety net for transient failures, at the cost of duplicate deliveries and a finite attempt count.

| Endpoint result | Retried? |
| --- | --- |
| `2xx` (`200`, `201`, `202`, `204`) | No – delivery succeeded |
| `4xx` (`400`, `401`, `403`, `404`) | Yes – even though a `4xx` rarely resolves on retry |
| `5xx` (`500`, `502`, `503`, `504`) | Yes – typically transient |
| Connection refused / unreachable | Yes |
| Timeout before responding | Yes – treated as a failed delivery |
| Invalid HTTPS certificate | Sometimes retried, sometimes rejected outright |

> **Unconfirmed:** the exact retry schedule, maximum attempts, delivery timeout, and final-failure handling are **not documented** in the spec. Assume the industry norm: exponential backoff with a cap, early retries minutes apart and later ones hours apart, continuing for at least several hours before giving up. Design to survive either an aggressive or a sparse schedule.

### What status code to return

- **Success:** return `2xx` (usually `200` or `204`) as soon as you have verified and durably enqueued.
- **Events you intentionally skip** (unhandled type, a customer you no longer service, a form you do not track): return `2xx` and log the decision. A `4xx` here just triggers retries that keep failing – wasted load on both sides.

```javascript
const handlers = {
  'contact.created': handleContactCreated,
  'gift.created': handleGiftCreated,
  // ...
};
async function processEvent(event) {
  const handler = handlers[event.eventType];
  if (!handler) {
    console.info('Skipping unhandled type', { eventType: event.eventType, eventId: event.eventId });
    return; // no retry needed – we chose not to handle it
  }
  await handler(event);
}
```

### Avoid duplicate side effects

Retries *will* redeliver events. The idempotency-key store from the previous section is what keeps a retry from double-counting a gift or sending a second email. There is no way to opt out of retries, so idempotency is mandatory, not optional.

### Inactive subscriptions drop events (not a retry scenario)

Deactivating (`.../Active?active=false`) or deleting a subscription drops events that occur while it is inactive – they are **not** queued for later. This is different from a failing endpoint.

> **Do** leave the subscription **active** during a temporary endpoint outage and let retries catch up when you recover.
> **Don't** deactivate during an outage – that bypasses the retry mechanism and loses events permanently.

### Final failure and reconciliation

After the maximum retries, Virtuous stops and does not redeliver later. Because final-failure handling is undocumented, implement a **polled reconciliation** safety net regardless: after any extended outage, run a Query with `modifiedDateTimeUtc > outage_start_time` for each subscribed resource type and process the results as if they arrived by webhook.

### Monitor

Track two metrics: **endpoint response time (p95)** – rising latency predicts timeout-driven retries, so alert as it approaches the timeout; and **non-`2xx` rate** – rising errors predict failed deliveries, so alert above a small baseline. Distinguish "healthy but slow" (fix with capacity) from "failing" (fix with debugging/rollback) – the remediation differs.

---

## Local testing

Webhooks need a public HTTPS URL, but your laptop is not addressable. Three components solve it: a tunnel, a Seeded Sandbox subscription, and your local handler.

> **Do** subscribe your local machine **only against a Seeded Sandbox**. Request one from your Virtuous partner contact if you do not have one.
> **Don't** point a tunnel at a production customer organization – that leaks donor data into your local logs.

### 1. Start a tunnel

`ngrok` is the common choice (mature, free tier, built-in inspector). Cloudflare Tunnel gives stable URLs that persist across restarts; `localtunnel` is simpler but less reliable.

```bash
brew install ngrok
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
ngrok http 3000     # prints a public URL like https://abc123.ngrok-free.app
```

The ngrok inspector at `http://localhost:4040` shows every request through the tunnel, with view/replay/inspect. It is the most useful tool in the kit. Free-tier URLs randomize on restart, so re-point the subscription each time.

### 2. Subscribe against the sandbox

Reuse the `POST /api/Webhook` call from [Create](#create) with three changes: a `SANDBOX_API_TOKEN`, the tunnel URL as `payloadUrl` (`https://abc123.ngrok-free.app/virtuous/webhook`), and a throwaway `secret` (for example `local-dev-secret`). Save the returned `id` for cleanup.

### 3. Trigger events

- **Direct endpoints fire synchronously:** `POST /api/Contact` and `POST /api/Gift` trigger `contactCreate` / `giftCreate` immediately; edit a record to fire an update event. Use these for fast feedback.
- **Transactions fire on the nightly batch:** `POST /api/Contact/Transaction` and Gift Transactions do **not** deliver their webhook immediately.

### 4. Capture fixtures and replay

Save a real delivery (raw body plus headers) from the inspector as a fixture, then replay it in unit tests against the exact bytes Virtuous sent – the most reliable way to validate verification and parsing.

```javascript
test('handles contact.created from a real fixture', async () => {
  const fx = JSON.parse(fs.readFileSync('test/fixtures/contact-created.json'));
  const rawBody = Buffer.from(fx.body, 'utf8');
  expect(verifyVirtuousSignature(rawBody, fx.headers, 'local-dev-secret')).toBe(true);
  await processWebhookEvent(JSON.parse(rawBody.toString('utf8')));
  // assert side effects
});
```

The inspector's **Replay** button re-sends a captured delivery. Use it to:

- **Test idempotency** – replay twice; observable state and side-effect count must match a single delivery (assert the email/downstream-call count is 1, not 2).
- **Iterate on code** – change the handler and replay without re-triggering in Virtuous.
- **Observe failure paths** – return `500` on replay and watch the retry from a live subscription.

### Cleanup and CI

```bash
curl -X DELETE https://api.virtuoussoftware.com/api/Webhook/{webhookId} \
  -H "Authorization: Bearer SANDBOX_API_TOKEN"
# or keep it but stop deliveries:
curl -X PUT "https://api.virtuoussoftware.com/api/Webhook/{webhookId}/Active?active=false" \
  -H "Authorization: Bearer SANDBOX_API_TOKEN"
```

For CI, run **fixture-replay tests** (no network to Virtuous needed) as the default. Add a **staging environment with a persistent tunnel** (Cloudflare Tunnel) and a permanently subscribed sandbox only for high-risk integrations (financial reconciliation, donor communication) where end-to-end confidence matters.

---

## Production checklist

- Signature verification runs on **every** request before processing, over the **raw** body, using a constant-time compare.
- The secret is loaded from a secrets manager – never hardcoded or logged; secret rotation accepts multiple valid secrets during the window.
- The endpoint is HTTPS-only with a public CA certificate; failed signatures are logged with context but never the body/secret/signature.
- Replay protection is in place (event-ID idempotency, plus a timestamp window if the timestamp is signed).
- The handler acknowledges fast, enqueues to a durable queue, and processes async.
- Every side effect is guarded by an idempotency key or a transactional outbox.
- A polled reconciliation job backstops missed events after outages.

---

## Related skills

- [crm-fundamentals.md](crm-fundamentals.md) – core resources (Contact, Gift, Project), auth, and API basics referenced by webhook payloads.
- [crm-workflows.md](crm-workflows.md) – end-to-end patterns including reconcile-failed-syncs, the polled backstop for missed deliveries.
- [crm-best-practices.md](crm-best-practices.md) – rate limits, error handling, and the polling-vs-webhooks trade-off.
- [crm-api-system.md](crm-api-system.md) – environments (Seeded Sandbox), base URLs, and authentication tokens.
- [crm-recipes.md](crm-recipes.md) – copy-paste integration recipes, including Transaction submission that pairs with `giftCreate` confirmation.
