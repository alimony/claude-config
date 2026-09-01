# Virtuous CRM+: Common workflows
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

How-to workflows for partner integrations against the CRM+ REST API: create/update contacts, record donations, query by filters and date range, handle duplicates, and build sync pipelines that reconcile cleanly.

## Orientation

- Base URL: `https://api.virtuoussoftware.com`; base path `/api`. Auth on every request: `Authorization: Bearer YOUR_API_TOKEN`.
- During partner development, use the customer's Seeded Sandbox, not production.
- The golden rule: **prefer the Transaction (import-pipeline) endpoints for writes.** They run Virtuous's matching algorithm and are dedupe-safe. Raw `POST /api/Contact` and `POST /api/Gift` do not deduplicate at all.
- Transaction writes are **asynchronous**. They return `200 OK` with no ID; the real record is created by the nightly batch and announced via a webhook. Direct writes are synchronous and return the record with its `id` (as `200`, not `201`).
- Version gotcha: the Gift Transaction endpoint is `POST /api/v2/Gift/Transaction` (note `v2`). The Contact Transaction endpoint is `POST /api/Contact/Transaction` (no `v2`). Everything else is under `/api`.
- Field-typing gotcha: the spec types many fields (booleans, integers, dates, money) as `string`. The live API accepts the natural types. Send `true`/`false`, numbers, and ISO 8601 strings – not `"true"` or `"123"`. Auto-generated SDKs that read the spec literally are the usual cause of type-mismatch bugs. For money, send a fixed-2 string (e.g. `"500.00"`) to dodge float representation issues.
- Rate limit: 5,000 requests/hour per Virtuous organization (one customer = one bucket, shared across every credential in that org). Back off on `429` per the `Retry-After` header. See `crm-fundamentals.md` for the headers and back-off details.

## Quick reference: which endpoint for each task

| Task | Method + endpoint |
| --- | --- |
| Create contact, dedupe-safe (default) | `POST /api/Contact/Transaction` |
| Create contact, synchronous (you know it's new) | `POST /api/Contact` |
| Look up contact before create | `GET /api/Contact/Find?email=` or `?referenceSource=&referenceId=` |
| Fetch contact by your external reference | `GET /api/Contact/{referenceSource}/{referenceId}` |
| Read one contact by Virtuous ID | `GET /api/Contact/{contactId}` |
| Update a contact | `GET` then `PUT /api/Contact/{contactId}` |
| Update one address / individual | `PUT /api/ContactAddress/{id}` · `PUT /api/ContactIndividual/{id}` |
| Archive / unarchive contact | `PUT /api/Contact/Archive/{id}` · `PUT /api/Contact/Unarchive/{id}` |
| Query contacts by filter | `POST /api/Contact/Query` (full records: `.../Query/FullContact`) |
| Discover contact filter parameters | `GET /api/Contact/QueryOptions` |
| Create gift, dedupe-safe (default) | `POST /api/v2/Gift/Transaction` |
| Create gift, synchronous (have `contactId`) | `POST /api/Gift` |
| Fetch gift by your external reference | `GET /api/Gift/{transactionSource}/{transactionId}` |
| Read one gift by Virtuous ID | `GET /api/Gift/{giftId}` |
| Query gifts by filter/date | `POST /api/Gift/Query` (full records: `.../Query/FullGift`) |
| Discover gift filter parameters | `GET /api/Gift/QueryOptions` |
| Reverse a duplicate gift | `POST /api/Gift/ReversingTransaction` |
| Delete a gift (rare, destroys audit trail) | `DELETE /api/Gift/{giftId}` |
| List valid non-cash subtypes | `GET /api/Gift/NonCashGiftTypes` |
| Validate project / campaign names | `GET /api/Project/Query` · `POST /api/Campaign/Query` |
| Subscribe to events | `POST /api/Webhook` |
| Deactivate a webhook subscription | `PUT /api/Webhook/{id}/Active?active=false` |

## The foundational pattern: idempotent create-or-update by external reference

Everything below depends on carrying **your own stable identifier** on every record. This is the single most important habit.

- Contacts use `referenceSource` + `referenceId` (in the Transaction payload) or `contactReferences: [{ source, id }]` (in the direct-create payload). Both name the same thing.
- Gifts use `transactionSource` + `transactionId`.

These pairs are the idempotency key and the reconciliation join key. With them you can look a record up later, match an inbound webhook to a pending submission, and let the matching algorithm resolve to the right existing record instead of creating a duplicate.

**Do** use a stable value from the source event: your donation row's primary key, the Stripe charge ID, the Eventbrite registration ID.
**Don't** generate the identifier at submission time (a fresh `crypto.randomUUID()` per attempt). On retry, Virtuous sees a new key and creates a duplicate.

```javascript
// ❌ Wrong – new key each attempt → duplicates on retry
{ transactionSource: 'YourPlatform', transactionId: crypto.randomUUID() }
// ✅ Right – stable key from the donation event
{ transactionSource: 'YourPlatform', transactionId: donation.id }
```

The lookup-by-reference endpoints (`GET /api/Contact/{referenceSource}/{referenceId}`, `GET /api/Gift/{transactionSource}/{transactionId}`) return `404` while a Transaction is still in the holding state and `200` with the record once the batch resolves it. This is the backbone of every reconciliation loop.

---

## Workflow 1: Create a contact

**Right sequence:** look up first, then submit a Transaction, then confirm asynchronously.

### Step 1 – pre-create lookup (avoid duplicates)

```bash
# By your reference (strongest signal)
curl "https://api.virtuoussoftware.com/api/Contact/Find?referenceSource=YourPlatform&referenceId=donor-bw-001" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
# Or by email
curl "https://api.virtuoussoftware.com/api/Contact/Find?email=bruce%40wayne.example" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

`200` returns the existing contact (reuse it; capture its `id`). `404` means no match. `Find` does **exact** matching only – no fuzzy name/address matching. For fuzzy dedupe, fall back to `POST /api/Contact/Query` with name + postal filters and treat results as human-review suggestions, not auto-merge candidates.

### Step 2 – submit the Contact Transaction (dedupe-safe path)

```bash
curl -X POST https://api.virtuoussoftware.com/api/Contact/Transaction \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "referenceSource": "YourPlatform", "referenceId": "donor-bw-001",
    "contactType": "Household",
    "firstName": "Bruce", "lastName": "Wayne",
    "emailType": "Home Email", "email": "bruce@wayne.example",
    "phoneType": "Mobile Phone", "phone": "555-0100",
    "address1": "1007 Mountain Drive", "city": "Gotham", "state": "NJ",
    "postal": "07001", "country": "US",
    "originSegmentCode": "INTEGRATION-IMPORT", "tags": "New Donor"
  }'
```

Returns `200 OK` with **no body and no ID** – the record is in the holding state. The nightly batch either creates a new contact or merges the data into a matching existing one. Include the strongest signals you have; the matcher weighs them in priority order: external reference, email, phone, name + address. `contactType` is `Household`, `Organization`, or `Foundation` (defaults to `Household`; be explicit).

### Step 3 – confirm the outcome

- **Preferred: webhooks.** Subscribe to `contactCreate` and `contactUpdate` via `POST /api/Webhook`. `contactCreate` fires for a new record; `contactUpdate` fires when the Transaction merged into an existing one. Both payloads carry the full contact plus `contactReferences[]` containing your `referenceSource`/`referenceId` – match on that pair, capture the Virtuous `id`, store it.
- **Fallback: poll** `GET /api/Contact/{referenceSource}/{referenceId}` on a slow cadence (hours, not seconds – the batch runs overnight). Polling burns rate-limit budget; use webhooks unless you can't.

### Direct create – only when you need a synchronous ID

Use `POST /api/Contact` for interactive tools that must return an ID immediately. Note the **different, nested payload shape** (individuals and methods as arrays, reference as `contactReferences`):

```bash
curl -X POST https://api.virtuoussoftware.com/api/Contact \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "contactType": "Household", "name": "Wayne, Bruce",
    "contactIndividuals": [{
      "firstName": "Bruce", "lastName": "Wayne", "isPrimary": true,
      "contactMethods": [
        { "type": "Home Email", "value": "bruce@wayne.example", "isPrimary": true, "isOptedIn": true },
        { "type": "Mobile Phone", "value": "555-0100", "isPrimary": true }
      ]
    }],
    "address": { "address1": "1007 Mountain Drive", "city": "Gotham", "state": "NJ", "postal": "07001", "country": "US", "isPrimary": true },
    "contactReferences": [{ "source": "YourPlatform", "id": "donor-bw-001" }]
  }'
```

Returns `200 OK` with the created contact and its `id`.

> Do / Don't
> - **Do** run `GET /api/Contact/Find` before every direct create and proceed only on `404`.
> - **Don't** call `POST /api/Contact` blind. It creates a second record unconditionally when the donor already exists, leaving duplicates that only an admin can merge.

---

## Workflow 2: Update a contact

The safe pattern is **`GET`-then-`PUT` the complete record** – always, regardless of what the API appears to do.

The spec declares `PUT` as full replacement (omitted fields cleared to null); the live API usually behaves as PATCH (omitted fields preserved). Because the two disagree, sending the full record is the only approach correct under both. It costs one extra request.

```javascript
async function updateContactSafely(contactId, changes) {
  const base = 'https://api.virtuoussoftware.com';
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const current = await fetch(`${base}/api/Contact/${contactId}`, { headers }).then(r => r.json());
  const updated = { ...current, ...changes };          // apply changes onto the full record
  return fetch(`${base}/api/Contact/${contactId}`, {
    method: 'PUT', headers, body: JSON.stringify(updated),
  }).then(r => r.json());
}
```

> Do / Don't
> - **Do** send the whole record you just read, with your edits merged in.
> - **Don't** send a "partial" body with only the changed fields. If the API is full-replacement, you silently null out everything you omitted.

**Sub-resource edits** avoid touching sibling array items – use them for one-item changes:

| Sub-resource | Endpoint |
| --- | --- |
| Address | `PUT /api/ContactAddress/{contactAddressId}` |
| Individual | `PUT /api/ContactIndividual/{contactIndividualId}` |
| Contact method | via its parent ContactIndividual (no standalone endpoint) |

Same `GET`-then-`PUT` discipline applies to each. When editing a nested item inside the parent record instead, map the array and replace only the target item – never rebuild the array wholesale.

- **Primary email / phone** live on a ContactIndividual's `contactMethods`. Edit the existing primary's `value`, or add a new method with `isPrimary: true` and clear the old one's flag.
- **Mark deceased:** set `isDeceased: true` on the individual, then suppress their contact methods downstream.
- **Custom fields / extra references:** modify the `customFields` or `contactReferences` array, then `PUT` the full record.
- **Archive:** use `PUT /api/Contact/Archive/{id}` and `PUT /api/Contact/Unarchive/{id}` – do not set `isArchived` via `PUT`.

**Field typing on update:** send booleans, integers, and ISO dates as native types even though the spec says `string`. **Concurrency:** there is no `ETag`/`If-Match`; last write wins. If concurrent writers are a real risk, read `modifiedDateTimeUtc` before your `GET`-then-`PUT` and compare it on the response to detect an interleaved write. **Persist the response**, not your input – the server may normalize values (trimmed whitespace, canonical state codes). Errors: `409 Conflict` signals a unique-constraint clash (e.g. the email is already on another contact) – reconcile the duplicate before retrying.

---

## Workflow 3: Create a donation (gift)

**Right sequence:** identify the donor, validate the project code, submit a Gift Transaction, confirm asynchronously.

The Transaction endpoint bundles four things you would otherwise hand-code: contact matching, designation resolution by `projectCode`, recurring-gift linkage, and pledge-payment linkage.

```bash
curl -X POST https://api.virtuoussoftware.com/api/v2/Gift/Transaction \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "transactionSource": "YourPlatform", "transactionId": "donation-9421",
    "contact": {
      "referenceId": "donor-bw-001", "type": "Household",
      "firstname": "Bruce", "lastname": "Wayne",
      "emailType": "Home Email", "email": "bruce@wayne.example",
      "phoneType": "Mobile Phone", "phone": "555-0100",
      "address": { "address1": "1007 Mountain Drive", "city": "Gotham", "state": "NJ", "postal": "07001", "country": "US" }
    },
    "giftDate": "2024-12-15", "giftType": "Cash",
    "amount": "500.00", "currencyCode": "USD", "batch": "Year-End-2024",
    "giftDesignations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "500.00" } ]
  }'
```

Returns `200 OK` with no Gift ID – resolved by the nightly batch. Embedded `contact` data drives contact matching and creates the donor if none matches.

**Required / strongly recommended fields:** `transactionSource` + `transactionId` (idempotency key), `contact.referenceId` (strongest match signal), `giftDate` (ISO 8601), `giftType`, `amount`, at least one `giftDesignations[]` entry. `currencyCode` defaults to the org currency; set it explicitly.

**Designations must balance.** The sum of `amountDesignated` must equal `amount`, validated synchronously – a mismatch is rejected with `400`.

```json
// ✅ sums to amount            // ❌ rejected: 300 ≠ 500
{ "amount": "500.00", "giftDesignations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "300.00" }, { "projectCode": "EDUCATION", "amountDesignated": "200.00" } ] }
{ "amount": "500.00", "giftDesignations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "300.00" } ] }
```

**Confirm the outcome** exactly as with contacts: subscribe to the `giftCreate` webhook (match by `transactionSource` + `transactionId`, capture `gift.id`), or poll `GET /api/Gift/{transactionSource}/{transactionId}` as a fallback.

### Gift-type variations

- **Recurring payment:** add `recurringGiftTransactionId` – the matcher links the gift to the existing schedule.
- **Pledge payment:** add `pledgeTransactionId`.
- **Non-cash (in-kind):** `giftType: "NonCash"` plus `nonCashGiftType`, `inKindDescription`, `inKindValue`. Discover valid subtypes via `GET /api/Gift/NonCashGiftTypes`.
- **Stock:** `giftType: "Stock"` plus `stockTickerSymbol`, `stockNumberOfShares`; `amount` is fair market value on the gift date.

### Direct create – only with a verified `contactId`

```bash
curl -X POST https://api.virtuoussoftware.com/api/Gift \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{ "contactId": 4821, "giftType": "Cash", "giftDate": "2024-12-15", "amount": 500.00,
        "currencyCode": "USD", "transactionSource": "YourPlatform", "transactionId": "donation-9421",
        "giftDesignations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": 500.00 } ] }'
```

Returns `200 OK` with the Gift and its `id`.

> Do / Don't
> - **Do** default to `POST /api/v2/Gift/Transaction` for all gift import.
> - **Don't** reach for `POST /api/Gift` casually. It requires a known `contactId` and bypasses contact matching **and** recurring/pledge linkage – set `recurringGiftTransactionId` / `pledgeTransactionId` yourself when needed.

---

## Workflow 4: Query contacts by filters

`POST /api/Contact/Query` retrieves by criteria. First discover valid parameters with `GET /api/Contact/QueryOptions` (cache at startup, refresh daily at most) – parameter names, including custom-field-derived ones, vary per organization and are case-sensitive.

**Filter shape:** `groups[].conditions[]`, each condition `{ parameter, operator, value }`. Conditions within one group combine with AND. Page with `skip`/`take`; `take` max is 1000. Loop while `skip < total`.

### Incremental sync by modification date (the common case)

```javascript
async function pullModifiedContacts(lastSyncTimestamp) {
  const out = []; let skip = 0, take = 1000, total = null, highest = lastSyncTimestamp;
  do {
    const page = await fetch('https://api.virtuoussoftware.com/api/Contact/Query', {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        groups: [{ conditions: [{ parameter: 'Last Modified Date', operator: 'Is After', value: lastSyncTimestamp }] }],
        sortBy: 'last modified date', descending: false,     // oldest first → resumable
        includeArchived: true,                               // else archives look "missing"
        skip, take,
      }),
    }).then(r => r.json());
    if (total === null) total = page.total;
    for (const c of page.list) { out.push(c); if (c.modifiedDateTimeUtc > highest) highest = c.modifiedDateTimeUtc; }
    skip += take;
  } while (skip < total);
  return { contacts: out, nextSyncTimestamp: highest };     // floor = highest seen, NOT wall clock
}
```

Three things this gets right: sort by modification date **ascending** so an interrupted run resumes from the highest fully-processed timestamp; carry forward the **highest `modifiedDateTimeUtc` observed** (not the wall-clock start time – that would drop records changed mid-run); and `includeArchived: true`, because archiving bumps `modifiedDateTimeUtc` but archived records are excluded from default queries.

### Targeted retrieval and bulk export

- **By tag / custom field / attribute:** e.g. `{ parameter: 'Tag', operator: 'Is', value: 'Major Donor' }`, or combine `Contact Type` + `State`.
- **Bulk export:** empty `groups: []` returns every contact; set `includeArchived: true` and `sortBy: 'id'` (immutable → stable). For very large exports, use an **ID cursor** (`Contact Id`/`Greater Than`/last id) instead of large `skip` values – high `skip` degrades server-side, cursoring keeps each query bounded and resumable.

**Response:** `POST /api/Contact/Query` returns an abbreviated shape (`id`, `name`, `contactType`, `email`, `phone`, `address`, `contactViewUrl`). For full records either `GET /api/Contact/{id}` per item (small subsets) or `POST /api/Contact/Query/FullContact` (whole set, meaningfully slower – use only when needed).

**Cadence:** webhooks are the preferred change signal; run this query as a slower reconciliation backstop (hourly for most partners, 5-10 min near-real-time, daily for warehouses). Use `take=1000` for bulk, `take=25-50` for interactive UIs. Filter aggressively – filtering server-side beats discarding client-side. Assert loop progress to avoid burning the hourly budget on a runaway paginator.

---

## Workflow 5: Query donations by date range

`POST /api/Gift/Query` mirrors Contact Query with its own `GET /api/Gift/QueryOptions`. Gift parameters typically include `Gift Date`, `Receipt Date`, `Gift Type`, `Amount`, `Batch`, `Project`, `Campaign`, `Segment`. Indexed sort fields: `Id`, `Amount`, `GiftDate`, `ReceiptDate`, `Batch`.

### Date-window query

```bash
curl -X POST https://api.virtuoussoftware.com/api/Gift/Query \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{ "groups": [{ "conditions": [
          { "parameter": "Gift Date", "operator": "Between", "value": "2024-12-01", "secondaryValue": "2024-12-31" } ] }],
        "sortBy": "GiftDate", "descending": false, "skip": 0, "take": 1000 }'
```

`Between` uses `value` + `secondaryValue` as inclusive bounds. Other date operators: `Is After`, `Is Before`, `Is On`, `Is After Or On`.

**Pick the right date field.** `giftDate` = when the donor gave; `receiptDate` = when the org processed/receipted it (differs for backdated or mailed gifts). Use `giftDate` for donor analytics and year-end reports; use `receiptDate` for accounting/tax reconciliation. Ask the customer which field aligns with their accounting period – mismatching it produces a discrepancy every close.

**Other patterns:** incremental sync filters `Last Modified Date`/`Is After` but still sorts by `GiftDate` (indexed; `Last Modified Date` may not be). Project/campaign reporting filters `Project`/`Is` or `Campaign`/`Is` by **name** (a gift links to a campaign indirectly through its designations' projects; the filter resolves this server-side). Major-gift dashboards filter `Amount`/`Greater Than Or Equal To` and sort `Amount` descending.

**Response** is abbreviated (`id`, `contactId`, `giftType`, `giftDate`, `amount`, `segment`, `batch`, `giftUrl`). `transactionSource`/`transactionId` and designations appear only in `POST /api/Gift/Query/FullGift` (or per-gift `GET /api/Gift/{giftId}`) – you need those for reconciliation joins.

**Reconciliation join:** query the window, then for each Virtuous gift look up your record by `transactionSource` + `transactionId` and bucket into matched / Virtuous-only (manual entry or another integration) / partner-only (a sync failure → Workflow 9). Date formats: `YYYY-MM-DD` for `Gift Date`/`Receipt Date`, `YYYY-MM-DDTHH:MM:SSZ` for `Last Modified Date`. An unknown `Project`/`Campaign` name returns `400`, not an empty set – validate names against `GET /api/Project/Query` and `POST /api/Campaign/Query` first.

---

## Workflow 6: Handle duplicate records

Duplicates arise from insufficient matching signal, direct create without a lookup, an unstable `transactionId`, or concurrent writes from multiple sources. Contacts and gifts have **different resolution surfaces.**

| Duplicate | Resolution | API support |
| --- | --- | --- |
| Two contacts, same donor | Merge in the Virtuous UI (admin) | **No merge endpoint.** Detect via `mergedIntoContactId`; you cannot merge programmatically. |
| Two gifts, same donation | Reversing transaction | `POST /api/Gift/ReversingTransaction` is API-accessible. |

### Contacts – detect and hand off

1. **Prevent** with the Workflow 1 pre-create lookup.
2. **Detect** with a scheduled reconciliation query (e.g. pull recently-modified contacts, group by normalized email/name+postal, surface groups of size > 1).
3. **Post-merge remap:** when an admin merges, the merged-away record carries `mergedIntoContactId` pointing at the survivor, and a `contactUpdate` webhook fires. On seeing it, repoint your stored `virtuous_contact_id` to the survivor **and remap every other stored reference** (donations, lists, logs) – orphaned references look valid until something dereferences a merged-away ID.

```javascript
async function handleContactUpdated(event) {
  const c = event.data;
  if (c.mergedIntoContactId) {
    await db.partnerContacts.update(
      { virtuousContactId: c.id },
      { virtuousContactId: c.mergedIntoContactId, mergedFrom: c.id, mergedAt: new Date() });
  }
}
```

Your role is bounded: detect, surface to the customer (link via `contactViewUrl`, state clearly the merge happens in Virtuous), wait, remap. High-volume partners keep a "pending merge" queue the customer works through.

### Gifts – reverse, don't delete

Detect by the unique reference (`GET /api/Gift/{transactionSource}/{transactionId}`) or by querying `Contact Id` + `Amount` + `Gift Date`/`Is On`. Resolve with a **reversing transaction** that offsets the duplicate while preserving the audit trail (original stays, reversal cancels it, net contribution zero):

```bash
curl -X POST https://api.virtuoussoftware.com/api/Gift/ReversingTransaction \
  -H "Authorization: Bearer YOUR_API_TOKEN" -H "Content-Type: application/json" \
  -d '{ "reversedGiftId": 78422, "giftDate": "2024-12-16",
        "notes": "Reversing duplicate of Gift 78421 (Stripe ch_3PXyz123)" }'
```

Exact body fields vary by org configuration – confirm against the schema before production. `DELETE /api/Gift/{giftId}` exists but erases the gift from the audit trail; use it only for a very recent duplicate not yet visible in any receipt, report, or accounting export, and only with the customer's sign-off. Otherwise reverse.

**Prevention beats both:** always use Transaction endpoints, include as many matching signals as you capture, keep `transactionId` stable, and wrap any unavoidable direct create in your own `Find` lookup.

---

## Workflow 7: Sync external donations into Virtuous (one-way pipeline)

The production architecture has four decoupled parts, each on its own schedule: **outbound queue → submitter worker → webhook receiver → reconciliation poller.**

**Capture into a durable queue** off your hot path. Key it by your stable donation ID (dedupe at insert with `INSERT ... ON CONFLICT DO NOTHING`), store the full Transaction payload as JSON for replay, and track explicit state (`pending → submitted → confirmed`, or `failed` / `needs_review`). A queued-but-unsubmitted donation is recoverable; a donation lost to a synchronous call against a down API is gone.

**Submitter worker** – the only component that calls `POST /api/v2/Gift/Transaction`. It transitions state on success only and classifies failures:

```javascript
if (response.ok) {                                   // 2xx: accepted into holding state
  await setStatus(donation, 'submitted');
} else if (response.status === 429) {                // rate limited: stop, honor Retry-After, retry next run
  return pauseFor(parseInt(response.headers.get('Retry-After') || '60', 10));
} else if (response.status >= 500) {                 // server error: transient → leave 'pending', retry
  await recordRetryableError(donation, response.status);
} else {                                             // 4xx: malformed, won't fix itself → 'failed' for humans
  await setStatus(donation, 'failed', await response.text());
}
```

Key discipline: **stable `transactionSource`/`transactionId` from the stored payload** (never regenerated), **state advances only on `2xx`**, and **4xx vs 5xx differentiation** (4xx is permanent → `failed`; 5xx and network errors are transient → stay `pending`). Run one worker per customer; use `FOR UPDATE SKIP LOCKED` so a customer's queue is drained by at most one worker at a time.

**Webhook receiver** – handle `giftCreate`, ignore events whose `transactionSource` isn't yours, match by `transactionId`, and be idempotent on the `confirmed` status (duplicate deliveries will happen and must be no-ops). The donor's `contactId` rides along in the `giftCreate` payload, so you only need `contactCreate` if you track contacts independently.

**Reconciliation poller** – the essential safety net. For records `submitted` longer than a safe window (24 h > nightly-batch + webhook delay), look up `GET /api/Gift/{transactionSource}/{transactionId}`: `200` → mark `confirmed` (a webhook was lost); `404` → mark `needs_review` (likely the needs-update bucket). Without this, a single dropped webhook becomes a permanent silent inconsistency.

**Initial historical load** flows through the same pipeline: bulk-insert history as `pending`, throttle the submitter to a conservative rate well under the 5,000/hour cap (e.g. ~1,500/hour, so a 24,000-gift backfill takes ~16 h – run it overnight), let the receiver confirm, then reconcile counts. Coordinate with the customer: a large backfill produces a matching wave of `giftCreate` webhooks and UI changes they should expect.

**Multi-tenant:** per-customer credentials, queues, workers, webhook subscriptions, and reconciliation – scoped by `customer_id`. **Monitor:** queue depth (`pending`), `submitted → confirmed` latency, `failed` count, `needs_review` count, and `giftCreate` arrival rate; alert on sustained anomalies.

---

## Workflow 8: Build a two-way sync

Add a return direction (Virtuous → your platform) on top of Workflow 7. The defining risk is **sync loops:** your write triggers a webhook, your handler treats it as new and writes it back, which triggers another webhook. Two defenses work together.

1. **Source identification.** Every write carries your `transactionSource`/`referenceSource`. In the webhook handler, check it first – if the event came from your own write, just capture the Virtuous ID and stop; only ingest events that originated elsewhere (manual entry, another integration, the Virtuous UI).

```javascript
async function handleGiftCreated(event) {
  const gift = event.data;
  if (gift.transactionSource === 'YourPlatform') {          // our own write echoing back
    await db.partnerGifts.update({ transactionId: gift.transactionId }, { virtuousGiftId: gift.id, status: 'confirmed' });
    return;
  }
  await ingestVirtuousOriginatedGift(gift);                 // genuinely external → ingest
}
```

2. **Per-record sync state.** Track `sync_state` (`in_sync` · `partner_pending` · `virtuous_pending` · `conflict`), plus `virtuous_modified_at`, `partner_modified_at`, `last_sync_at`. Setting `virtuous_pending` when applying an inbound change opens a cooldown during which outbound submission for that record is suppressed – this breaks delayed loops even when applying the inbound change re-triggers your own update logic.

**State transitions:** partner write `in_sync → partner_pending`, confirmed by webhook `→ in_sync`; inbound webhook `in_sync → virtuous_pending`, cooldown elapsed `→ in_sync`; ambiguous resolution `→ conflict`, resolved manually `→ in_sync`.

**Inbound handler** routes by event type (`contact.created/updated`, `gift.created/updated`, `gift.deleted`), finds the local record by your `contactReference` or by `virtuous_contact_id`, checks `mergedIntoContactId` (remap and return if set), then applies the change with `sync_state: virtuous_pending`. Run **Query-based reconciliation** (Workflow 4/5, every 4-12 h) as a backstop through the same handler for events lost to outages or subscription downtime.

**Source-of-truth** for fields both sides edit – pick per integration:
- **Most-recent-wins:** compare `modifiedDateTimeUtc`; simple but exposed to clock skew.
- **Per-field ownership:** document which side owns each field; outbound writes touch only your fields, inbound only Virtuous's. Eliminates conflicts for those fields.
- **Virtuous-as-canonical:** safest default for shared fields – the nonprofit's staff are the authoritative editors; your platform mirrors and writes back only on explicit request.

**Initial reconciliation** at first connect: bulk-export both sides, cross-match by reference/email, set matched pairs `in_sync`, create missing local records, submit Transactions for records only you hold. **Pausing a customer:** deactivate the webhook via `PUT /api/Webhook/{id}/Active?active=false` and stop the workers – but note events during an inactive subscription are **dropped, not queued**, so run a fresh reconciliation on reactivation.

---

## Workflow 9: Reconcile failed syncs

The safety net under Workflows 7 and 8. Four failure categories, each with its own detection and resolution.

| Category | Symptom | Detection | Resolution |
| --- | --- | --- | --- |
| **Stuck transaction** | Accepted, but no record and no webhook | `submitted` > 24 h, then `GET /api/Gift/{src}/{id}` returns `200` | Mark `confirmed` (webhook was lost); note recovery path |
| **Needs-update bucket** | Contact matching failed; awaits manual pick | `404` from the same lookup at 72+ h | Mark `needs_review`; surface to customer to resolve in Virtuous Imports |
| **Missed webhook** | Record exists in Virtuous, absent locally | Query `Last Modified Date`/`Is After`, diff against your DB | Apply via the idempotent inbound handler |
| **Drift** | Same record, different field values | Field-by-field compare of paired records | Apply the source-of-truth rule; if ambiguous, mark `conflict` |

**Stuck vs needs-update** look identical during lookup (both `404` early). The distinguisher is time: past the batch window a stuck transaction usually resolves on a later reconciliation pass, whereas a needs-update transaction sits until an admin picks a contact, creates one, or discards it. The API exposes **no endpoint to query the needs-update bucket** – detection is by inference (a transaction that should have resolved but can't be found by its reference). When the admin resolves it, the normal `giftCreate` webhook fires and your standard handler captures it. A growing `needs_review` count means your Transactions carry too little matching signal.

**Missed-webhook reconciliation** depends on an **idempotent inbound handler** – applying the same change twice (once via the late webhook, once via reconciliation) must produce identical state. Test this explicitly by replaying an event twice. **Drift detection** costs one API call per paired record, so run it weekly/monthly over a recent subset, not the whole database.

**Operationalize it:** a daily per-customer run (stuck → needs-update → missed-webhook → report) plus a weekly drift pass; a reconciliation report tracking `pending`, `submitted > 24 h`, `needs_review`, `failed`, `conflict`, latency, and recovered count; and an append-only `virtuous_reconciliation_log` (category, record ids, resolution, details) for diagnosing regressions and answering compliance questions. Escalate by class: auto-recovered → log only; needs-review → customer queue; a spike in `failed` or broad drift → engineering alert. Most reconciliation should be operational, not engineering.

**"Where's my record?" runbook:** find your record and its reference → look it up in Virtuous by external reference → if `404` and `submitted` < 48 h, wait (still in batch); if older, suspect needs-update and surface to the customer → if present in Virtuous but missing locally, apply through the inbound handler → if field values disagree, apply the source-of-truth rule or mark `conflict`.

---

## Cross-cutting error handling

| Status | Meaning | Action |
| --- | --- | --- |
| `400` | Malformed JSON, missing/invalid field, unbalanced designations, unknown `projectCode`/`giftType`, unknown Project/Campaign filter name, `take > 1000` | Inspect body; fix request; validate names/codes; check spec-vs-live field types |
| `401` | Invalid/expired token | Refresh the credential |
| `403` | Insufficient key permissions | Check the key's permission group |
| `404` | Record not found (or merged/deleted); reference still in holding state | Confirm the ID; for references, poll or reconcile |
| `409` | Unique-constraint clash (e.g. email already on another contact) | Reconcile the duplicate, then retry |
| `422` | Validation failed | Read `error.details[]` for field-level messages |
| `429` | Rate limit exceeded (5,000/hr per org) | Back off per `Retry-After`; stop draining |

## Related skills

- `crm-fundamentals.md` – getting started, authentication, base URLs, environments.
- `crm-concepts.md` – the data model: Contacts, Gifts, Transactions and the needs-update bucket, relationships and IDs.
- `crm-recipes.md` – complete end-to-end integration recipes (e.g. Stripe to Virtuous).
- `crm-best-practices.md` – rate limits, pagination, error handling, and idempotency in depth.
- `crm-api-contacts.md` – Contact endpoint reference (Find, Query, sub-resources, archive).
- `crm-api-giving.md` – Gift endpoint reference (Transaction, Query, reversing transactions, gift types).
- `crm-webhooks.md` – subscription management, event types, signature verification, safe reprocessing.
