# Virtuous CRM+: Data model & core concepts
Based on Virtuous CRM+ documentation (API spec 2026), retrieved 2026-08-31.

This skill teaches the CRM+ data model so you model donor and giving data correctly against the REST API at `https://api.virtuoussoftware.com` (base path `/api`). Read it before writing any code that creates or reads Contacts or Gifts. The single most common integration mistake is misplacing person-level fields on the Contact record; the [Contact hierarchy](#the-contact-hierarchy) section fixes that.

## The core resources

CRM+ exposes a small set of first-class resources. Almost every integration works on the spine **Contact → Gift → Project**: donors, their giving, and what that giving funds.

| Resource | Represents | Notes |
| --- | --- | --- |
| **Contact** | A household, organization, or foundation | The record a donor "belongs to". Not a person. |
| **ContactIndividual** | A person inside a Contact | Holds names, birth date, gender. Many per Contact. |
| **ContactAddress** | A postal address on a Contact | Many per Contact; one is primary. |
| **ContactMethod** | An email or phone | Lives on a ContactIndividual, not on the Contact. |
| **Gift** | A single posted donation | Belongs to one Contact; allocated via designations. |
| **GiftDesignation** | An allocation of a Gift to a Project | A Gift has one or more; amounts sum to the Gift amount. |
| **Project** | A fundable purpose ("fund" elsewhere) | The money destination. Referenced, rarely created by partners. |
| **Campaign** | A time-bound fundraising effort | Groups Projects. Read-only through the API. |
| **Segment** | A grouping of Contacts | For outreach targeting and reporting. |
| **RecurringGift** | An ongoing donation schedule | Each successful payment becomes a Gift. |
| **Pledge** | A commitment to give over time | Each payment toward it becomes a Gift. |
| **Relationship** | A connection between two Contacts | Spouse, employer, etc. Distinct from household structure. |
| **Webhook** | A subscription to record-change events | Replaces polling for incremental sync and async outcomes. |

Key relationships to internalize:

- **A Contact is not a person.** People are ContactIndividuals inside the Contact.
- **A Gift can fund multiple Projects.** Each split is a separate GiftDesignation; a Gift always has at least one.
- **Campaigns are context, not a destination.** Money flows to Projects through designations. A Gift inherits its Campaign from the Project it funds.
- **RecurringGifts and Pledges generate Gifts.** The schedule or commitment is one record; each payment is a separate Gift linked back to it.

***

## The Contact hierarchy

A Contact represents a **household or organization**, never a single person. The people, addresses, and contact methods are separate sub-resources hanging off the Contact. Putting person-level or email data directly on the Contact is the number-one partner mistake.

### What lives where

| Field / data | Correct home | Wrong home (common mistake) |
| --- | --- | --- |
| `contactType`, `name` (display name of the household/org) | **Contact** | – |
| `firstName`, `lastName`, `birthDate`, `gender`, `title`, `isPrimary`, `isSecondary`, `isDeceased` | **ContactIndividual** | Contact |
| Email address, phone number (`type` + `value` + `isPrimary` + `isOptedIn`) | **ContactMethod** (on a ContactIndividual) | Contact or ContactIndividual as a bare string |
| `address1`, `address2`, `city`, `state`, `postal`, `country`, seasonal date ranges | **ContactAddress** | ContactIndividual |
| `tags`, `customFields`, `contactReferences` | **Contact** | – |

Cardinality: a Contact has **many** ContactIndividuals and **many** ContactAddresses. Each ContactIndividual has **many** ContactMethods. The Contact's primary address is also surfaced as a top-level `address` object for convenience, but it is a ContactAddress with its own `id`.

### A realistic Contact

This household has two people (a primary and a secondary spouse), each with their own email and phone, plus a shared address, tags, one custom field, and external references:

```json
{
  "id": 4821,
  "contactType": "Household",
  "name": "Wayne, Bruce",
  "isPrivate": false,
  "isArchived": false,
  "contactIndividuals": [
    {
      "id": 9012,
      "firstName": "Bruce",
      "lastName": "Wayne",
      "isPrimary": true,
      "isSecondary": false,
      "isDeceased": false,
      "contactMethods": [
        { "id": 31001, "type": "Home Email", "value": "bruce@wayne.example", "isPrimary": true, "isOptedIn": true },
        { "id": 31002, "type": "Mobile Phone", "value": "555-0100", "isPrimary": true }
      ]
    },
    {
      "id": 9013,
      "firstName": "Selina",
      "lastName": "Wayne",
      "isPrimary": false,
      "isSecondary": true,
      "contactMethods": [
        { "id": 31003, "type": "Home Email", "value": "selina@wayne.example", "isPrimary": true, "isOptedIn": false }
      ]
    }
  ],
  "address": {
    "id": 51001,
    "label": "Home",
    "address1": "1007 Mountain Drive",
    "city": "Gotham",
    "state": "NJ",
    "postal": "07001",
    "country": "US",
    "isPrimary": true
  },
  "tags": ["Major Donor", "Board Member"],
  "customFields": [
    { "name": "wealthScore", "value": "850", "displayName": "Wealth Score" }
  ],
  "contactReferences": [
    { "source": "Stripe", "id": "cus_abc123" },
    { "source": "YourPlatform", "id": "donor-bw-001" }
  ],
  "createDateTimeUtc": "2024-01-15T09:23:00Z",
  "modifiedDateTimeUtc": "2024-12-15T14:30:00Z"
}
```

> **Do**
> - Put names and person attributes on ContactIndividual; put email/phone on ContactMethod.
> - Mark the primary donor `isPrimary: true`; if a spouse is captured, mark them `isSecondary: true`. Downstream features (joint giving, household receipts) depend on this.
> - Set `isOptedIn` per ContactMethod to carry consent.

> **Don't**
> - Don't send `firstName`/`lastName` or an `email` string on the Contact resource.
> - Don't invent `contactType` values. The spec types the field as `string` and does not enumerate valid values. Call `GET /api/Contact/Types` and cache the result; common values are `Household`, `Organization`, `Foundation`, but the enum is per-organization.
> - Don't assume field types from the spec: it declares nearly every field (including `isPrimary`, month/day integers) as `string`. The live API accepts and returns natural types (`boolean`, `integer`, `number`). Send natural types; loosen strict schema validators.

***

## Gifts vs Transactions: two ways to write, one that reads

CRM+ gives you **two architecturally different ways** to create Contacts and Gifts from an external system. The choice matters more than any single field: it decides whether you produce duplicates and how soon records appear.

Be precise about the vocabulary, because "Transaction" does not mean "a Gift":

- A **Gift** is the authoritative, posted donation record. It has a numeric `id`, shows in the donor's giving history, and returns from gift queries.
- A **Gift Transaction** is an *import payload in a holding state*. It is **not yet a Gift**. A nightly batch converts it into a Gift (matching the donor, resolving designations, associating recurring/pledge links). Some transactions never become gifts – they land in the "needs update" bucket for manual resolution. The same holds for Contact vs Contact Transaction.

### Pattern 1 – Transaction (recommended for partners)

| Endpoint | Imports |
| --- | --- |
| `POST /api/Contact/Transaction` | One Contact (donor data with no gift). Note: **no** version segment. |
| `POST /api/v2/Gift/Transaction` | One Gift, optionally with an embedded contact block. |
| `POST /api/v2/Gift/Transactions` | A batch of Gifts (plural), same semantics. |

The Gift Transaction endpoints use the `v2` path segment; the Contact Transaction endpoint does not. This inconsistency is a known spec issue; the paths above are stable.

The pipeline is **asynchronous**:

1. The API accepts the payload into a **holding state** (visible in the Virtuous UI under Imports) and returns `200 OK`. It does **not** return a Gift `id` – no Gift exists yet.
2. A **nightly batch** runs the matching algorithm against existing records.
3. **On match:** incoming Contact data merges into the existing Contact; a Gift associates with the matched Contact.
4. **On no match:** a new record is created – or, for a Gift the algorithm cannot confidently place, the transaction moves to the **needs-update** bucket for an administrator to resolve.
5. **Webhooks fire** (`Contact Created`, `Contact Updated`, `Gift Created`) when the real record exists.

How matching decides (most reliable first):

| Signal | Matches when |
| --- | --- |
| External reference (`referenceSource` + `referenceId`) | An existing Contact carries the same `(source, id)` in `contactReferences`. Highest priority. |
| Email | The email exists on an existing ContactIndividual's ContactMethods. |
| Phone | The phone exists on an existing ContactIndividual's ContactMethods. |
| Name + address | First/last name plus matching city/state/postal. Fuzzy fallback. |

For a Gift Transaction the batch also resolves designations (by `projectCode`, `externalAccountingCode`, or `projectId`) and associates the Gift with an existing RecurringGift or Pledge when `recurringGiftTransactionId` / `pledgeTransactionId` is supplied.

### Pattern 2 – Direct create

| Endpoint | Behavior |
| --- | --- |
| `POST /api/Contact` | Creates a Contact synchronously. **No matching, no dedup.** |
| `POST /api/Gift` | Creates a Gift synchronously. |

Direct create bypasses the pipeline: the record appears immediately with exactly the fields you sent. Use it only when you already hold a verified Virtuous ID (for example, adding a Note or a correction to a known Contact), for interactive admin tools that need instant confirmation, or for a pre-deduplicated one-time historical load.

> **Do**
> - Default new partner integrations to the Transaction endpoints. Virtuous recommends this in the spec itself; it moves matching into Virtuous and removes a whole class of duplicate bugs.
> - Detect outcomes with webhooks, correlating on your `(transactionSource, transactionId)` pair. Don't poll "did my transaction become a Gift yet" – the batch runs overnight.
> - Include every identifying field you have (reference id, email, phone, full address) to raise the auto-match rate and keep gifts out of needs-update.
> - Tolerate the gap: assume some submitted gifts stay pending or land in needs-update. When a customer reports a missing gift, check there first via `GET /api/Gift/{transactionSource}/{transactionId}`.

> **Don't**
> - Don't call `POST /api/Contact` for general donor sync without your own matching – it silently creates duplicates. If you must use it, first check `GET /api/Contact/{referenceSource}/{referenceId}`, `GET /api/Contact/Find`, then `POST /api/Contact/Query`.
> - Don't treat status codes as creation signals: direct create returns `200 OK` (not `201`), with no `Location` header. The new `id` is in the response body.

***

## Gifts

A Gift is one transfer of value from a donor to the organization. It belongs to exactly one Contact (`contactId`) and is allocated to one or more Projects through `giftDesignations`.

```json
{
  "id": 78421,
  "contactId": 4821,
  "giftType": "Cash",
  "giftDate": "2024-12-15",
  "amount": 500.00,
  "currencyCode": "USD",
  "batch": "Year-End-2024",
  "transactionSource": "Stripe",
  "transactionId": "ch_3PXyz123",
  "recurringGiftTransactionId": null,
  "pledgeTransactionId": null,
  "giftDesignations": [
    { "id": 91002, "projectId": 311, "project": "Clean Water Initiative", "amountDesignated": 300.00 },
    { "id": 91003, "projectId": 412, "project": "Education Programs", "amountDesignated": 200.00 }
  ]
}
```

### Gift types

The `giftType` field is typed as `string` in the spec and not enumerated. Commonly used values:

| Type | Meaning |
| --- | --- |
| `Cash` | Monetary gift (cash, check, card, ACH). Default for most online giving. |
| `EFT` | Electronic funds transfer – bank transfer, ACH, wire. (EFT = electronic funds transfer.) |
| `Credit` | Credit-card gifts tracked separately from other cash. |
| `Stock` | Securities, recorded at fair market value on the gift date. |
| `NonCash` | In-kind goods or services. Use `nonCashGiftType`, `inKindDescription`, `inKindValue`. |
| `Other` | Anything that doesn't fit. |

Discover the non-cash subset with `GET /api/Gift/NonCashGiftTypes`; confirm the full enabled list with the organization's administrator.

### Linkage to recurring gifts and pledges

A Gift can be standalone or a payment on a longer arrangement. Set the linkage **at gift-creation time** – creating an orphan Gift does not retroactively associate it.

- **RecurringGift payment:** set `recurringGiftTransactionId` to the schedule's id. The Gift inherits the schedule's designations by default.
- **Pledge payment:** set `pledgeTransactionId` to the pledge's id. The amount records against the pledge balance.

### Premiums

A `GiftPremium` is a donor-recognition item (a shirt, a book, an event ticket) tracked on the Gift so it can be fulfilled and the tax-deductible portion computed. Assign by `premiumId`; the catalog comes from `GET /api/Premium`.

### Reversals and refunds

Never `DELETE` a Gift for a refund. Post an offsetting record with `POST /api/Gift/ReversingTransaction`. The original Gift stays on file for audit; the reversing transaction offsets it. This is the correct path for a downstream refund event (for example, a Stripe refund).

### Reading Gifts

| Endpoint | Use |
| --- | --- |
| `GET /api/Gift/{giftId}` | One Gift by Virtuous id. |
| `GET /api/Gift/{transactionSource}/{transactionId}` | One Gift by your platform's ids. Cleanest for sync; no need to store the Virtuous id. |
| `GET /api/Gift/ByContact/{contactId}` | All Gifts for a Contact. |
| `POST /api/Gift/Query` | Filtered, paginated retrieval (incremental sync, export). |
| `POST /api/Gift/Query/FullGift` | Same, but with full designations, premiums, and pledge links. Slower; use only when needed. |

> **Field typing warning:** the spec types most Gift fields as `string`, including `amount`, `giftDate`, and `exchangeRate`. Send natural types (number, ISO 8601 date, boolean); responses come back with correct types. SDK generators that read the spec literally will mistype these.

***

## Funds, Campaigns, Designations, Projects

If you come from Raiser's Edge, DonorPerfect, or Salesforce NPSP, a "fund" is a **Project** in Virtuous. Every endpoint and field uses `Project`.

| Elsewhere | Virtuous |
| --- | --- |
| Fund | Project |
| Fund designation / gift allocation | GiftDesignation |
| Appeal / Campaign | Campaign |

### The three-layer allocation model

A gift's money flows: **Gift → GiftDesignation → Project**, with the Project grouped under a **Campaign**.

- **Project** answers "what does this gift fund?" – a specific program or purpose. This is where the money lands.
- **GiftDesignation** answers "how much goes to that purpose?" – the split. A Gift has at least one; all `amountDesignated` values must sum to the Gift `amount`. The API rejects a mismatch with `400`, and rejects a Gift with no designations at all.
- **Campaign** answers "what fundraising effort is this part of?" – time-bound reporting context. A Gift is associated with a Campaign *indirectly*, through the Project it funds. There is no direct Gift→Campaign field.

Single-Project gift (the common case): one designation for the full amount. Split gift: multiple designations summing to the total.

```json
{
  "amount": 500.00,
  "giftDesignations": [
    { "projectCode": "CLEAN-WATER", "amountDesignated": 300.00 },
    { "projectCode": "EDUCATION",   "amountDesignated": 200.00 }
  ]
}
```

### Identifying a Project

Three fields can reference a Project. For partners, **`projectCode` is usually the right anchor** – human-readable, configurable to match your platform's identifier, and stable across migrations.

| Field | Use |
| --- | --- |
| `id` (integer) | Virtuous internal id, unique within the organization. |
| `projectCode` (string) | The org's short code, e.g. `"CLEAN-WATER"`. Accepted directly in a designation. |
| `externalAccountingCode` (string) | The GL (general ledger) account code. Use as the bridge for accounting reconciliation. |

Read Projects with `GET /api/Project/{projectId}`, `GET /api/Project/Code/{projectCode}`, or `POST /api/Project/Query` (filter `isActive: true` and `isPublic: true` to get the set safe to designate to). `GET /api/Project/{projectId}/Balance` returns giving totals. Sub-projects roll up to a parent via `parentId`; designate to the most specific sub-project and Virtuous handles the rollup.

### Campaigns are read-only

The API exposes `GET /api/Campaign/{campaignId}`, `POST /api/Campaign/Query`, and `GET /api/Campaign/QueryOptions` – but **no** create, update, or delete. Partners cannot create Campaigns programmatically. If your integration needs one, direct the nonprofit administrator to create it in the Virtuous UI, then reference its Projects in your gift submissions. Campaigns use `campaignId` as their primary key and a single `isArchived` flag.

### Segments

A **Segment** groups *Contacts* (Major Donors, Lapsed Givers) for outreach and attribution – it answers "who", not "what" or "when". Unlike Campaigns, Segments are writable (`POST`/`PUT /api/Segment`). A Gift can carry a `segment` / `segmentCode` for attribution.

***

## Reference IDs vs Virtuous IDs

Getting identifiers right is what keeps an integration free of duplicates and lets you correlate external records to Virtuous records.

### Primary and foreign keys

Every resource has a numeric `id` primary key, assigned at creation, immutable. Campaign is the one exception – its key is `campaignId`. A foreign key to another resource is named `{resource}Id`: a Gift references its Contact via `contactId`; a designation references its Project via `projectId`. Any field ending in `Id` (other than `id` itself) is a foreign key.

> **IDs are per-organization, not global.** A Contact with `id: 4821` in one nonprofit's instance is unrelated to `id: 4821` in another's. A partner serving multiple nonprofits **must** scope every stored Virtuous id by customer: store `(customerId, resourceType, virtuousId)`, never a bare `virtuousId`. A single global index across customers causes silent data mix-ups.

### External references – the bridge to your system

External references let your platform's identifiers travel with the Virtuous record, so you often need not store the Virtuous id at all. **This is the correct mechanism to correlate external records and prevent duplicates.**

**Contacts** carry an *array* of references (one per integrated system):

```json
{ "contactReferences": [
    { "source": "Stripe", "id": "cus_abc123" },
    { "source": "YourPlatform", "id": "donor-bw-001" }
] }
```

Set them on creation with `referenceSource` + `referenceId` (in the Contact body or the embedded contact block of a Gift Transaction). The Transaction matcher treats this as the highest-priority signal. Look a Contact up by reference with:

| Endpoint | Auth |
| --- | --- |
| `GET /api/Contact/{referenceSource}/{referenceId}` | Standard Bearer token. Recommended. |
| `GET /api/Contact/ByReference/{referenceId}` | HMAC only (HMAC = hash-based message authentication code). Older single-segment path; contact Virtuous support for credentials. |

**Gifts** carry a *single* pair (a gift has at most one external reference), `transactionSource` + `transactionId`. It serves two jobs:

- **Idempotency.** Re-submitting a Gift Transaction with the same pair is recognized as a duplicate and does not create a second Gift. Safe to retry after a network failure.
- **Lookup.** `GET /api/Gift/{transactionSource}/{transactionId}` retrieves the Gift (or the still-pending transaction) by your ids.

> **Do**
> - Set `referenceSource`/`referenceId` on every Contact and `transactionSource`/`transactionId` on every Gift you submit. One extra field buys bullet-proof idempotency and a clean lookup path back.
> - Pick one stable `source` string for your integration and use it everywhere (`"Stripe"`, `"YourPlatformName"`). Use a sub-context like `"Acme/Donations"` vs `"Acme/Events"` when one platform sends multiple streams.
> - Use stable source ids (a Stripe charge id, your internal donation id).

> **Don't**
> - Don't generate a fresh UUID per retry for `transactionId` – it defeats idempotency and creates duplicates.
> - Don't use generic sources like `"API"` or `"Import"` – they make reconciliation across integrations impossible.

### The Relationship resource

A **Relationship** models an explicit connection between *two separate Contacts* (spouse, parent, employer) – distinct from the ContactIndividual grouping inside one household Contact. Fields: `contactId` + `contactIndividualId` (the owning side), `relatedContactId` + `relatedContactIndividualId` (the other side), `relationshipType`, `notes`. Standard CRUD lives under `/api/Relationship`; list a Contact's relationships with `GET /api/Relationship/ByContact/{contactId}`. Discover valid types with `GET /api/Relationship/Types` and don't hardcode them. Most straightforward donor syncs (one donor = one Contact) never touch Relationships; they matter for wealth-screening, corporate-giving, and family-giving integrations.

***

## Custom fields and custom collections

Custom fields are the supported extension point for organization-specific data (wealth scores, communication preferences, partner identifiers). **Configuration is per-organization and per-resource** – every nonprofit customer may have a different set, so never hardcode field names.

### Discover, then read/write

Each resource has its own discovery endpoint returning the configured fields: `GET /api/Contact/CustomFields`, and siblings for `ContactIndividual`, `ContactNote`, `Gift`, `GiftAsk`, `RecurringGift`, `Project`, `PlannedGift`, `Premium`, `Event`, `EventAttendee`, `Grant`, `VolunteerOpportunity` (and `GET /api/v2/Pledge/CustomFields`). Cache the result at setup, re-fetch daily; don't fetch per record read.

```json
[
  { "name": "wealthScore", "displayName": "Wealth Score", "dataType": "Number", "options": [] },
  { "name": "preferredContactMethod", "displayName": "Preferred Contact Method", "dataType": "Dropdown", "options": ["Email", "Phone", "Mail", "Text Message"] }
]
```

Values appear on a record as a `customFields` array of `{ name, value, displayName }`. Reference by `name` (the internal name), never `displayName`.

### Wire formats

The spec types every value as `string` regardless of `dataType`. Serialize on write per this table; parse on read using the `dataType` from discovery:

| `dataType` | Write format |
| --- | --- |
| `Text` | The string, e.g. `"Major Donor"`. |
| `Number` | String digits, e.g. `"850"`. |
| `Date` | ISO 8601 date, e.g. `"2024-12-15"`. |
| `Boolean` | The string `"true"` or `"false"`. |
| `Dropdown` | Exactly one string from the field's `options` (case-sensitive). |

Writing rules: include only the fields you want to set (omitted fields are unchanged, matching PUT-as-PATCH behavior). Sending `{ "name": "x", "value": "" }` **clears** the field; omitting it leaves it alone. Treat an unknown field name as a warning and continue – a customer may have renamed or removed it – rather than failing the whole sync.

### Custom collections – multi-instance data

When a Contact needs *repeating* sub-records (for example, multiple board memberships each with a role and start date), use **Custom Collections**. Discover with `GET /api/Contact/CustomCollections` or `GET /api/ContactIndividual/CustomCollections`. Instances appear as a `customCollections` array; each has `customCollectionId`, `customCollectionName`, a unique `collectionInstanceId`, and a `fields` array of name/value pairs. Create an instance with `POST /api/Contact/{contactId}/Collection/{customCollectionId}`; update or delete by `collectionInstanceId`. Most integrations only need standard custom fields; collections are configured in close coordination with the nonprofit's Virtuous administrator.

***

## Statuses and lifecycle

CRM+ has **no single status model**. Contacts and Projects use boolean flags, RecurringGifts and Pledges use an explicit `status` string, and Gifts have no status at all. Read lifecycle flags on every record you process and check them against the operation you are about to perform: queries exclude some states by default, and writes to the wrong state are rejected.

| Resource | Lifecycle expressed by | Watch out for |
| --- | --- | --- |
| **Contact** | `isPrivate`, `isArchived` (on ContactIndividual: `isDeceased`) | Archived Contacts are excluded from `POST /api/Contact/Query` unless you send `"includeArchived": true`. A private Contact may return `403` or be filtered for restricted credentials. |
| **Project** | `isActive`, `isPublic`, `isAvailableOnline`, `isTaxDeductible` | Designating a gift to an inactive Project fails with `400`/`422`. Present only `isActive: true` + `isPublic: true` Projects for mapping. |
| **Campaign** | `isArchived` | Read-only; no API archive endpoint. Still gettable by `campaignId` after its end date. |
| **RecurringGift** | `status` string + `cancelDateTimeUtc` | Common values `Active`, `Paused`, `Cancelled`, `Failed` (not enumerated in spec – treat unknowns defensively). |
| **Pledge** | `status` string + `payments[]` | Common values `Active`, `Written Off`, `Completed`. |
| **Gift** | No status field | State lives in related records (see below). |

### State transitions use dedicated endpoints

These are transitions, not deletions – data is preserved for audit:

- **Archive/unarchive a Contact:** `PUT /api/Contact/Archive/{contactId}` and `PUT /api/Contact/Unarchive/{contactId}`. Prefer these over `DELETE`.
- **Cancel a RecurringGift:** `PUT /api/RecurringGift/Cancel/{id}`. **Permanent** – sets `status: Cancelled` and `cancelDateTimeUtc`; there is no uncancel. To resume giving, create a new schedule with `POST /api/RecurringGift`.
- **Write off a Pledge:** `PUT /api/v2/Pledge/WriteOff/{id}`. Preserves the commitment and payment history with `status: Written Off`.

### Gift "state" without a status field

| Concept | How it is expressed |
| --- | --- |
| Original gift | A standard Gift record. |
| Refund / reversal | A separate Gift via `POST /api/Gift/ReversingTransaction`; the original stays. |
| Pledge payment | A Gift with `pledgeTransactionId` set. |
| Recurring payment | A Gift with `recurringGiftTransactionId` set. |
| Pending | Not yet a Gift – a holding-state Transaction until the nightly batch runs. |

Gifts are immutable once posted; there is no archived-Gift state.

### Deceased individuals

`isDeceased` is on the **ContactIndividual**, not the Contact. Read it per-individual when iterating a household, and suppress that individual's emails and phones from outbound communications. The household Contact stays active while other living individuals remain.

### Incremental sync anchor

Every resource carries `createDateTimeUtc` and `modifiedDateTimeUtc` (UTC, ISO 8601). `modifiedDateTimeUtc` updates on any change, **including lifecycle transitions** – so one query filtered by `modifiedDateTimeUtc > {last_run}` catches content edits, archives, and status changes alike. On each run, store the maximum `modifiedDateTimeUtc` from the response as the next run's floor, and include archived records when reconciling so an archived Contact isn't mistaken for a deletion.

***

## Related skills

- `crm-fundamentals.md` – authentication, environments, rate limits, and getting started with the CRM+ API.
- `crm-workflows.md` – end-to-end recipes (create a Contact, record a donation, sync external gifts, build a two-way sync).
- `crm-api-contacts.md` – the Contact, ContactIndividual, address, and relationship endpoints in detail.
- `crm-api-giving.md` – the Gift, GiftDesignation, RecurringGift, and Pledge endpoints in detail.
- `crm-api-campaigns-events.md` – Campaign, Project, Segment, and Event endpoints.
- `crm-best-practices.md` – deduplication, idempotency, reconciliation, and webhook-driven sync patterns.
