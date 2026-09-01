# Virtuous CRM+: Integration recipes
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

Reusable patterns for piping an external system into Virtuous CRM+: Stripe, Mailchimp, Constant Contact, peer-to-peer/crowdfunding platforms, auction/event platforms, nightly batch sync, historical-gift backfill, and recurring-donor lifecycle. Every recipe is the *same* Virtuous-side machine with a different adapter on the source side. Learn the machine once; the per-source table tells you what changes.

- API host: `https://api.virtuoussoftware.com`, base path `/api`. Auth: `Authorization: Bearer <token>`, scoped per customer, loaded from a secrets manager.
- Rate limit: **5,000 requests/hour per Virtuous organization** (shared across every credential and integration in that org). Throttle writes conservatively (e.g. ~1,200/hour) so steady-state traffic and the customer's other integrations still fit. See `crm-fundamentals.md` for headers and back-off.

---

## The common pattern: map → dedupe → upsert → verify

Every recipe below is a specialization of one pipeline. Build this once.

```
Source webhook/poll → durable per-customer queue → submitter worker
  → POST to a Virtuous Transaction endpoint (matching decides create vs. merge)
  → Virtuous fires giftCreate/contactUpdate webhook → reconciliation
```

1. **Map.** Translate the source object to a Virtuous object + fields. The Virtuous-side mapping is the durable part of any recipe; source field names drift, so confirm them against the source's current docs.
2. **Dedupe / idempotency.** Carry a stable source identifier so retries and replays never double-write. Two key pairs (see next section): `referenceSource`+`referenceId` for Contacts, `transactionSource`+`transactionId` for Gifts and RecurringGifts. Virtuous's matching algorithm treats these as its highest-priority match signal.
3. **Upsert.** POST to a `*/Transaction` endpoint. You do **not** decide create-vs-update – the matching algorithm merges into an existing record or creates a new one based on the reference/transaction keys, email, name, etc.
4. **Verify.** Reconcile on a schedule: count, sum per project, and donor-side counts. Reconciliation is the safety net for every missed webhook and every gap. It is not optional.

### Shared infrastructure (applies to all recipes)

- **Durable queue, not in-memory.** The webhook receiver verifies the signature, writes the raw event to a queue, and returns `200` immediately. The submitter worker drains the queue out-of-band. Storing the payload verbatim makes replay/reprocessing possible without re-fetching the source.
- **Idempotency at the queue boundary.** Use the source's event ID as the queue primary key with `ON CONFLICT DO NOTHING` to absorb the source's webhook retries.
- **Multi-tenant isolation.** Resolve `customer_id` at queue insertion (map the source's account/list/audience ID → customer). Per-customer credentials, queues, checkpoints, and alerts.
- **Retryable vs. permanent failures.** 5xx / 429 / network → re-queue and retry. 400 / 422 → log and surface for a human; retrying will never succeed.
- **Verify both signatures.** The inbound source signature *and* the Virtuous webhook signature, on every request.

---

## Core identifiers (get these right or you get duplicates)

| Purpose | Fields | Notes |
| --- | --- | --- |
| Contact identity | `referenceSource` + `referenceId` | `referenceSource` = your literal platform name (`"Stripe"`, `"Mailchimp"`). `referenceId` = the source's stable per-donor ID. Highest-priority Contact match signal. |
| Gift idempotency | `transactionSource` + `transactionId` | Stable per-payment source ID. Same pair on a retry resolves to the same Gift – no duplicate. |
| RecurringGift idempotency | `transactionSource` + `transactionId` | `transactionId` = the *schedule's* ID (e.g. `sub_*`), **not** the first payment's ID. |
| Payment → schedule link | `recurringGiftTransactionId` on the Gift | Set to the schedule's `transactionId`. Same value on every payment of the schedule; the payment's own `transactionId` differs each time. |

**Do** pick one source ID per entity and use it for the entire life of the integration. **Don't** mix ID types (e.g. Stripe `ch_*` on some gifts and `pi_*` on others) – that produces duplicate Gifts for the same payment.

## Endpoint quick reference

| Endpoint | Use |
| --- | --- |
| `POST /api/v2/Gift/Transaction` | Create a Gift. Embedded `contact` block gets matched/created automatically. |
| `POST /api/Contact/Transaction` | Create/update a Contact via the matching algorithm. |
| `GET /api/Contact/Find?referenceSource=X&referenceId=Y` (or `?email=`) | Look up a Contact. |
| `PUT /api/Contact/{id}` | Update a Contact – **GET-then-PUT the full record** (PUT replaces, not patches). |
| `GET /api/Gift/{source}/{transactionId}` | Look up a Gift by transaction reference, e.g. `GET /api/Gift/Stripe/pi_123`. |
| `POST /api/Gift/ReversingTransaction` | Refund/reversal. **Never** `DELETE /api/Gift/{id}`. |
| `POST /api/RecurringGift` | Create a recurring schedule (takes `contactId` directly – no embedded matching). |
| `GET /api/RecurringGift/{id}` · `GET /api/RecurringGift/ByContact/{contactId}` | Read a schedule / list a Contact's schedules. |
| `PUT /api/RecurringGift/{id}` | Update a schedule – GET-then-PUT the full record. |
| `PUT /api/RecurringGift/Cancel/{id}` | Cancel a schedule. **Never** update `status: "Cancelled"` via plain PUT. |
| `POST /api/RecurringGift/Query` · `GET /api/RecurringGift/QueryOptions` | Search schedules / list valid filters. |
| `POST /api/Relationship` · `GET /api/Relationship/Types` | Create a donor↔fundraiser link / discover configured types. |
| `POST /api/ContactNote` · `POST /api/ContactNote/Bulk` | Add note(s). |
| `POST /api/Tag/Bulk` | Apply a tag across many Contacts (batch). |
| `POST /api/Event` | Create an Event (galas, 5Ks). |
| `POST /api/Contact/Query` · `POST /api/Gift/Query` | Page through records for reconciliation/backfill. |
| `GET /api/Premium/Query` · `/api/Gift/NonCashGiftTypes` | Discover configured premiums / non-cash gift types. |
| `/api/v2/Pledge/*` | Pledges (commitments not yet paid). |
| `GET /api/Health` | Reachability check (use in nightly prereqs). |

---

## Per-recipe specifics at a glance

| Recipe | Source object → Virtuous | `referenceId` / `transactionId` | Primary endpoint(s) | Signature gotcha |
| --- | --- | --- | --- | --- |
| **Stripe** | Customer→Contact, Charge/PaymentIntent→Gift | `cus_*` / `pi_*` (pick one, prefer PaymentIntent) | `POST /api/v2/Gift/Transaction`, `ReversingTransaction`, `RecurringGift` | Cents→dollars (÷100); off-by-100 is the #1 bug |
| **Mailchimp** | Subscriber→Contact, Audience/Tag→Tag, Group→Custom Field | Subscriber Hash/ID | `POST /api/Contact/Transaction`, `PUT /api/Contact/{id}` | Webhook body is **form-urlencoded**, not JSON; hold `pending` (double opt-in) |
| **Constant Contact** | Contact→Contact, List→Tag | Contact ID (GUID) | `POST /api/Contact/Transaction` | Hybrid webhook+poll; webhook coverage is tier-dependent |
| **Fundraising platform** | Donor→Contact, Fundraiser→Contact/Org, donation→Gift | Platform donor ID / donation ID | `POST /api/Contact/Transaction`, `Gift/Transaction`, `Relationship` | Two Contacts per gift; gross vs. net fee handling |
| **Auction/event** | Order→**many** Gifts | `{order}-{linetype}-{line}` | `POST /api/v2/Gift/Transaction` with `giftPremiums` | One order splits into ticket/auction/cash/sponsorship Gifts; deductible = amount − premiums |
| **Nightly sync** | Any (no webhooks) | source modification timestamp | any write endpoint | Checkpoint on highest *source* timestamp, not wall-clock |
| **Historical import** | Backlog of gifts→Gifts | `platformDonationId` | `POST /api/v2/Gift/Transaction` | Batch label + validation passes + customer sign-off |
| **Recurring updates** | Schedule→RecurringGift, payments→Gifts | schedule ID / payment ID | `POST/PUT /api/RecurringGift*` | Contact must exist first; cancel via `/Cancel/{id}` |

---

## Recipe: Stripe → Virtuous

**Map.** Stripe Customer → Contact; Charge/PaymentIntent → Gift.

| Virtuous field | From Stripe |
| --- | --- |
| `contact.referenceId` | Customer ID `cus_*` |
| `transactionId` | PaymentIntent `pi_*` (recommended) **or** Charge `ch_*` – never both |
| `amount` | `amount / 100` (Stripe stores **cents**; Virtuous expects **dollars**) |
| `giftDate` | `created` epoch → date in the org's timezone |
| `currencyCode` | `currency`, uppercased |
| `giftDesignations[].projectCode` | `metadata.virtuous_project_code` (set when the PaymentIntent is created) |

**Events → actions.** `payment_intent.succeeded` → `POST /api/v2/Gift/Transaction`. `charge.refunded` → `POST /api/Gift/ReversingTransaction`. `charge.dispute.created` → surface/tag. Recurring: `customer.subscription.created` → `POST /api/RecurringGift` (schedule ID `sub_*`); `invoice.paid` → Gift with `recurringGiftTransactionId = invoice.subscription`; `customer.subscription.deleted` → `PUT /api/RecurringGift/Cancel/{id}`.

**Idempotency.** The Stripe *event ID* is the queue anchor (`ON CONFLICT DO NOTHING` covers Stripe's retries). The `transactionId` (PaymentIntent) is the Virtuous-side anchor.

One-time gift submission:

```json
POST /api/v2/Gift/Transaction
{
  "transactionSource": "Stripe",
  "transactionId": "pi_3Q1abcDEF",
  "contact": {
    "referenceId": "cus_Q1abc",
    "type": "Household",
    "firstname": "Jordan", "lastname": "Rivera",
    "emailType": "Home Email", "email": "jordan@example.org",
    "phoneType": "Mobile Phone", "phone": "+15551234567",
    "address": { "address1": "1 Main St", "city": "Austin", "state": "TX", "postal": "78701", "country": "US" }
  },
  "giftDate": "2026-08-31",
  "giftType": "Cash",
  "amount": "500.00",
  "currencyCode": "USD",
  "batch": "Stripe",
  "giftDesignations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "500.00" } ]
}
```

Refund – look up the original Gift, then reverse it:

```json
GET /api/Gift/Stripe/pi_3Q1abcDEF        → { "id": 998877, ... }

POST /api/Gift/ReversingTransaction
{ "reversedGiftId": 998877, "giftDate": "2026-09-02", "notes": "Stripe refund – Refund re_1AbC" }
```

**Gotchas.**
- **Refund race:** `charge.refunded` can arrive before Virtuous's `giftCreate` webhook. On a `404` from the Gift lookup, defer and retry – the original Gift isn't in Virtuous yet.
- **Recurring first payment:** the Gift on `invoice.paid` links to the schedule via `recurringGiftTransactionId`; the schedule itself was created from `customer.subscription.created`.

> **Do** unit-test the cents→dollars conversion – it is the single most common partner bug (every gift recorded at 100× value).
> **Don't** use `DELETE /api/Gift/{id}` for refunds or plain PUT for subscription cancels – use `ReversingTransaction` and `RecurringGift/Cancel/{id}`.

**Reconcile.** Compare Stripe's daily payout charges against Virtuous Gifts by `transactionSource="Stripe"` + `transactionId`. This is the most-requested partner reconciliation – accountants want monthly proof every deposit landed.

---

## Recipe: Mailchimp → Virtuous (and Constant Contact)

Email-platform sync moves **Contacts**, not Gifts. Same Virtuous side for both ESPs; the source adapters differ.

**Map (Mailchimp).** Subscriber → Contact via `POST /api/Contact/Transaction`. `referenceSource: "Mailchimp"`, `referenceId` = Subscriber Hash/ID (stable across email changes). Merge fields `FNAME`/`LNAME`/`PHONE`/`ADDRESS` → Contact fields.

| Mailchimp structure | Virtuous | Notes |
| --- | --- | --- |
| Audience (list) membership | Tag `"Mailchimp: <name>"` | one tag per audience |
| Mailchimp Tag | Tag, prefixed `"MC:"` | prefix keeps them visually distinct from native tags |
| Group | Custom Field | groups are categorical |

**Events → actions.** `subscribe`/`profile` → Contact Transaction. `unsubscribe`/`cleaned` → set `isOptedIn: false` on the email ContactMethod (via GET-then-PUT). `upemail` → update the email ContactMethod's value. `cleaned` → also add a ContactNote with the bounce reason (distinguishes "chose to unsubscribe" from "address is broken").

**Constant Contact differences.** `referenceSource: "Constant Contact"`, `referenceId` = Contact ID (GUID). List membership → Tag prefixed `"CC:"`. Webhook body is JSON and can batch **multiple events per delivery** (iterate the array). Webhook coverage is **tier-dependent** – run a **polling worker** for events not delivered (query `updated_after=<lastPoll>`, hourly is the sane default; respect CC's quota, which partners often share across customers). If the tier has no webhooks, drop to pure polling → a nightly/hourly sync.

**Bidirectional (Virtuous → ESP).** Subscribe to the `contactUpdate` webhook. Only round-trip tags with your ESP prefix (`MC:` / `CC:`); a `"Major Donor"` tag doesn't belong on an email list. Diff current tags against last-known state so you don't re-send every tag on every event.

**Gotchas.**
- **`pending` (double opt-in) is the most-missed state:** the subscriber gave an email but hasn't confirmed. **Hold sync** until a later `subscribe` with `status: subscribed` – creating the Contact early inflates the customer's metrics with unconfirmed signups.
- **Sync loops:** an inbound ESP change fires a `contactUpdate`, which your outbound handler must recognize as ESP-originated and suppress. Store the last ESP-originated update timestamp per Contact and ignore Virtuous events inside a short window after it.
- **Deleted in the ESP:** do **not** delete the Virtuous Contact – donation history is still valuable. Set `isOptedIn: false` + a ContactNote.
- Bulk import on first connection: treat each existing subscriber as a synthetic `subscribe` event; throttle well under the 5,000/hour cap.

> **Do** use `GET`-then-`PUT` for every opt-in/email change – a partial PUT can clear fields you didn't touch.
> **Don't** map ESP lists to tags without confirming with the customer's marketing team – some prefer custom fields for cleaner segmentation.

---

## Recipe: Fundraising platform (P2P / crowdfunding / team) → Virtuous

The distinguishing trait: a donation passes through a **fundraiser**, so there are **three participants** – donor, fundraiser, nonprofit. Record all three plus the relationships.

| Participant | Virtuous representation |
| --- | --- |
| Donor | Contact, `referenceSource: "FundraisingPlatform"`, `referenceId` = platform donor ID |
| Fundraiser | Contact (person) or Organization Contact (team). Often already a supporter/staff/board member |
| Nonprofit | The Virtuous org you write to – constant, no per-gift mapping |

**Contact sync – try harder to match the fundraiser.** Fundraisers usually already exist. Lookup order: (1) `Contact/Find` by platform reference, (2) by email (and back-fill the reference onto the found Contact), (3) create. Tag new fundraisers `"Fundraiser"`. Teams → Organization Contact with `referenceId` prefixed `"team-"` to disambiguate from individuals.

**Gift sync with fundraiser attribution.** `POST /api/v2/Gift/Transaction`, `giftType` usually `"Credit"`. Attach the fundraiser two ways:
- **Pattern A (recommended):** Gift custom fields – `{ "name": "Fundraiser Contact ID", "value": "<id>" }`, plus page URL and platform fee. Unlocks "top fundraisers by dollars" reporting via a Query filter.
- **Pattern B (fallback):** a ContactNote on the donor when the customer has no Gift custom fields.

**Campaign mapping.** Platform Campaign → Virtuous Campaign; Subcampaign/Fund → Virtuous Project (the designation target). Map every campaign at **setup time**, stored in config – never inferred at runtime.

**Relationships (optional).** `POST /api/Relationship` links donor↔fundraiser (e.g. type `"Recruited By"`). The relationship type must already exist – discover via `GET /api/Relationship/Types` and skip gracefully if absent (you can't create types via API). Relationships never expire, so consider also tracking "most recent recruiter" in a custom field.

**Event-tied fundraisers.** 5Ks/walk-a-thons: create a Virtuous `Event`, link a Campaign, designate gifts to the Event's Project, and split the ticket portion out to the auction/event recipe below.

**Gotchas.** Gross vs. net: record the donor's **gross** pledged amount (matches their tax receipt/intent) with the platform fee in a custom field – recommend this over net or two-gift-split. Anonymous donations: still create the Contact (needed for receipting) but tag `"Anonymous Through Fundraiser"`. Pledged-but-unpaid ("I'll give if you hit goal") → Virtuous Pledges (`/api/v2/Pledge/*`), **not** Gifts, until the charge processes.

---

## Recipe: Auction / event platform → Virtuous

The distinctive component is the **order splitter**: one platform order decomposes into *many* Virtuous Gifts, each with its own tax treatment. Composite `transactionId` per line, e.g. `"{order}-ticket-{line}"`, `"{order}-auction-{line}"`.

| Line type | Virtuous shape | Deductible portion |
| --- | --- | --- |
| Ticket | Gift + `giftPremiums` (attendance FMV) | `amount − Σ(premium qty × valuePerItem)` |
| Auction win | Gift + `giftPremiums` (item FMV) | `winningBid − itemFMV` |
| Cash donation | Gift, **no** premiums | full amount |
| Sponsorship (tiered) | Gift + `giftPremiums` (benefits package FMV); tag `"Sponsor"` | `amount − benefitsFMV` |
| Donated auction item (in-kind) | Separate NonCash Gift from the **item donor** | n/a (amount = FMV) |
| Raffle | Not deductible – skip or record with a clear non-deductible designation | – |

Ticket/auction/sponsorship all use the premium mechanism (Virtuous computes the deductible automatically):

```json
POST /api/v2/Gift/Transaction
{
  "transactionSource": "EventPlatform",
  "transactionId": "ord_55-ticket-1",
  "contact": { "referenceId": "att_900" },
  "giftDate": "2026-08-31", "giftType": "Credit", "amount": 500.00,
  "giftDesignations": [ { "projectCode": "GALA-2026", "amountDesignated": 500.00 } ],
  "giftPremiums": [ { "premiumId": 42, "quantity": 2, "valuePerItem": 50.00 } ],
  "customFields": [ { "name": "Event", "value": "2026 Gala" } ]
}
```

Donated item as NonCash:

```json
{ "transactionSource": "EventPlatform", "transactionId": "donated-item-77",
  "contact": { "referenceId": "donor_31" },
  "giftType": "NonCash", "nonCashGiftType": "Auction Item",
  "inKindDescription": "Weekend in Napa", "inKindValue": 1200.00, "amount": 1200.00,
  "giftDesignations": [ { "projectCode": "GALA-2026", "amountDesignated": 1200.00 } ] }
```

**Gotchas.**
- **Premiums must be configured in Virtuous first** ("Gala Ticket", "VIP Reception", each auction item) with their FMVs. Discover IDs via `GET /api/Premium/Query`; discover NonCash types via `/api/Gift/NonCashGiftTypes`. Walk the customer through premium setup at onboarding.
- **Refunds are common** (cancelled tickets, voided wins) → `POST /api/Gift/ReversingTransaction` **per line**; reverse only the affected Gift, don't consolidate an order-level reversal.
- Corporate sponsors → `contactType: "Organization"`, not Household.
- Walk-up/no-email attendees → require some identifier or sync with a `"Walk-up – Needs Review"` tag; don't silently create endless duplicate "John Smith" records.
- Paddle-raise verbal pledges → Pledges (`/api/v2/Pledge/*`), then Gift payments when charged.
- Reconcile the event's total revenue against the sum of Gifts for the event's Project.

---

## Recipe: Nightly (batched) data sync

The fallback when event-driven doesn't fit: **no source webhooks, can't host receivers, tolerant freshness ("yesterday's data today"), constrained source quota, or already-batch-oriented ops.** Nightly is a different tradeoff, not a worse one – but don't pick it just because event-driven "seems hard."

**Four phases** (each boundary is a natural retry point): (1) load checkpoint + confirm prerequisites, (2) read source changes since checkpoint, (3) apply to Virtuous with throttling, (4) persist checkpoint + emit run report.

**Checkpoint on the highest *source-side modification timestamp* processed – not the wall-clock time the last run started.** Wall-clock misses records changed *during* the run; the source timestamp guarantees the next run picks them up. Store `consecutive_failures` and `paused_until` for a circuit breaker.

**Source read shapes:** modification-timestamp filter (`modified_after > checkpoint`, most common) → cursor-based "changes since" → full-snapshot-diff (fallback when the source exposes no timestamps; expensive but works; diff current vs. previous snapshot to derive create/update/delete).

**Apply phase:**
- Throttle ~1,200/hour (a 10,000-change run ≈ 8.3h, fits an overnight window). Pace **per-request**, not per-batch; running flat-out at the 5,000 cap means one 429 stalls the whole run until the limit resets.
- Batch where endpoints allow: `POST /api/Tag/Bulk`, `POST /api/ContactNote/Bulk`. Single-record `Contact/Transaction` and `Gift/Transaction` don't batch.
- Retryable → re-queue for the next nightly run (retries are 24h apart, so a mislabeled-permanent 422 is cheap to catch). Permanent → surface for a human.

**Resumability & safety:** persist progress every ~100 records (or ~30s) so a killed job resumes from the last index. Circuit breaker: after 3 consecutive failures, pause 24h and alert ops – an on-call human clears `paused_until`. This prevents "failing for three weeks, nobody noticed."

**Multi-tenant:** stagger start times across the window (isolates rate-limit budgets), per-customer state/credentials/alerts. **Hybrid:** event-driven for webhook-capable resources, nightly for the rest – share idempotency keys on any resource both pipelines touch. **Monitor:** run completion, duration regressions (the first symptom of trouble), records processed, in-run failure rate (<1% healthy, alert >5%), rate-limit pauses (any non-zero = throttle too aggressive), checkpoint age (<24h).

---

## Recipe: Import historical gifts (bulk backfill)

Same architecture as steady-state sync; what changes is **scale, sequencing, and customer coordination**. Four phases.

**Phase 1 – pre-flight planning (with the customer).**
- **Date window:** everything / from a cutoff (last fiscal year, prior CRM migration) / current fiscal year only. Most want 1–2 fiscal years.
- **Map every Project/Campaign** referenced in the backlog to a current Virtuous `projectCode`. An unmapped project must **fail validation**, never silently fall back to a default (silent fallback hides errors and corrupts analytics).
- **Pick one `giftDate` meaning:** donor-action date (default) vs. settlement date. Don't support both.
- **Batch label** like `Historical-Import-2026-08` on every gift – lets the customer filter the import in the UI and scopes your reconciliation queries.
- **Communicate:** tell the customer a wall of `giftCreate` events will hit their dashboards as the nightly batch processes the import. A surprised customer is the #1 cause of a rollback.

**Phase 2 – two validation passes before submitting anything.** Pass 1 structural: required fields present (`donorPlatformId`, positive `amount`, `giftDate`, `platformDonationId`), project maps to a known code, donor has email or reference. Pass 2 contact resolution: for each donor, `Contact/Find` by reference → by email → none; categorize matched-by-reference (clean) / matched-by-email (import back-fills your reference onto the existing record – confirm the customer wants this) / no-match (will create a Contact). Produce a report and get customer review before loading.

**Phase 3 – the load.**
- Throttle ~1,200/hour (24,000 gifts ≈ 16h minimum), run off-peak in the customer's timezone.
- **Resumable** via a state table keyed on `platform_donation_id` (`pending`→`submitted`→`confirmed`/`failed`/`skipped`), storing the full payload for replay.
- **Idempotency:** `transactionId = platformDonationId`, stable across retries – a lost-in-transit success won't duplicate on retry.

```json
POST /api/v2/Gift/Transaction
{
  "transactionSource": "YourPlatform",
  "transactionId": "donation_2019_44821",
  "contact": { "referenceId": "donor_5561", "type": "Household",
    "firstname": "Sam", "lastname": "Lee", "emailType": "Home Email", "email": "sam@example.org" },
  "giftDate": "2019-11-03",
  "giftType": "Cash",
  "amount": "250.00",
  "currencyCode": "USD",
  "batch": "Historical-Import-2026-08",
  "giftDesignations": [ { "projectCode": "GEN-FUND", "amountDesignated": "250.00" } ]
}
```

**Phase 4 – reconciliation, then sign-off.** Count (submitted vs. Gifts with the batch label). **Sums per Project** (catches merges the count misses – two gifts merging diverges count by one but the sums reveal the dollar impact). Donor-side (distinct import donors vs. new Contacts created in the window; the difference = donors who already existed). Get explicit customer sign-off; keep the import in a holding state – configure receipt/statement workflows to **exclude `Historical-Import-*` batches** until accounting validates the totals.

> **Do** improve the matching signal in Pass 2 – every donor resolved pre-submission is one fewer needs-update item (which for 50,000+ gift imports can be days of the customer's team's work).
> **Don't** deactivate the Virtuous webhook subscription during a pause – you still need `giftCreate` events to confirm gifts already submitted.

---

## Recipe: Sync recurring-donor updates (RecurringGift lifecycle)

The data model: a **RecurringGift** is the *commitment* (frequency, amount, designations, start, status) – **not money**. Each scheduled payment is its own **Gift**, linked back via `recurringGiftTransactionId`. Cancelling a schedule stops future payments; it does **not** delete past Gifts. Unlike Contact merges, the whole lifecycle is API-manageable.

**Create.** `POST /api/RecurringGift` takes `contactId` **directly** – there is no embedded contact matching. So the donor's Contact must exist first:

```json
POST /api/RecurringGift
{
  "transactionSource": "YourPlatform",
  "transactionId": "sub_xyz123",
  "contactId": 4821,
  "startDate": "2026-08-31",
  "amount": 50.00,
  "frequency": "Monthly",
  "automatedPayments": true,
  "trackPayments": true,
  "designations": [ { "projectCode": "MONTHLY-GIVING", "amountDesignated": 50.00 } ]
}
```

Required: `contactId`, `startDate`, `amount`, `frequency`, `designations[]` (amounts must sum to `amount`). Strongly recommended: `transactionSource`+`transactionId` = the **schedule's** ID. Store the returned `id` on your side.

**Contact-first sequencing gotcha.** Because there's no embedded matching, resolve/create the Contact, wait for it to resolve through the nightly batch, *then* create the schedule – so for a brand-new donor the RecurringGift typically appears the **day after** signup. If you need it faster, submit the first payment via `POST /api/v2/Gift/Transaction` (which *does* have embedded matching) and create the schedule once the Contact appears.

**Link each payment.** On every successful charge, `POST /api/v2/Gift/Transaction` with `transactionId` = the specific payment's ID and `recurringGiftTransactionId` = the schedule's `transactionId`. The Gift then shows in the schedule's payment history and the donor's recurring total.

**Update.** GET-then-PUT the **full** record to `PUT /api/RecurringGift/{id}`. On an amount change, distribute proportionally across designations. Common changes: amount, designation array (re-confirm the sum), frequency (some platforms also need `nextExpectedPaymentDate`). A donor's payment-method change needs **no** Virtuous update – payment method lives in your platform.

**Cancel.** `PUT /api/RecurringGift/Cancel/{id}`. **Never** set `status: "Cancelled"` via plain PUT – only the Cancel endpoint sets `cancelDateTimeUtc` and writes the audit log entry. There is **no pause/resume endpoint**: either cancel-and-recreate on resume, or keep pause/resume state on your side and stop submitting payment Gifts during the pause (the schedule looks active but shows a payment gap – discuss with the customer).

**Failed payments.** **Do not submit failed payments as Gifts** – a failed charge is not a gift and inflates totals. Only submit on actual success. If a payment fails permanently and the donor doesn't fix their method, cancel the schedule; surface failures to the customer's team via your own UI/report, not as Virtuous Gifts.

**Reconcile monthly.** Cross-match your active schedules to Virtuous RecurringGifts by `transactionId` (`POST /api/RecurringGift/Query`); flag missing schedules and amount mismatches (>$0.01). The usual drift: a donor changed their amount in your platform but it never propagated – re-push the update.

> **Do** treat the schedule's ID as `transactionId` (not the first payment's ID), so idempotency holds across the schedule's life.
> **Don't** record failed/dunning payments as Gifts, and don't cancel via status-PUT.

---

## Cross-cutting Do / Don't

> **Do**
> - Carry the source's stable ID as `referenceId` / `transactionId` on every write – it's the whole idempotency story.
> - GET-then-PUT full records for any Contact or RecurringGift update (PUT replaces).
> - Throttle to ~1,200/hour and reconcile on a schedule; treat reconciliation as the safety net, not a nicety.
> - Configure Projects, Premiums, Custom Fields, and Relationship Types in Virtuous *before* the integration references them; discover IDs via the relevant Query endpoints.

> **Don't**
> - Mix source ID types for the same entity, or fall back to a default project silently.
> - Delete to reverse a Gift, or status-PUT to cancel a schedule – use `ReversingTransaction` / `RecurringGift/Cancel/{id}`.
> - Create a Contact for a `pending` double-opt-in subscriber, or record a failed recurring payment as a Gift.
> - Assume undocumented enums (`frequency`, gift types) – confirm valid values against the live org before production.

---

## Related skills
- [crm-workflows.md](crm-workflows.md) – the underlying workflows these recipes instantiate (sync external donations, two-way sync, create/update contact, reconcile failed syncs, handle duplicates).
- [crm-concepts.md](crm-concepts.md) – Gifts (premiums, designations, reversals), Contacts, Relationships, statuses/lifecycle states, and IDs.
- [crm-best-practices.md](crm-best-practices.md) – rate limits, throttling headroom, idempotency, and multi-tenant patterns.
- [crm-webhooks.md](crm-webhooks.md) – signature verification, idempotency/safe reprocessing, and the `giftCreate`/`contactUpdate` events these recipes consume.
- [crm-api-giving.md](crm-api-giving.md) – Gift Transaction, ReversingTransaction, RecurringGift, and Pledge endpoint reference.
- [crm-api-contacts.md](crm-api-contacts.md) – Contact Transaction, Contact/Find, ContactNote, Tag, and Relationship endpoint reference.
