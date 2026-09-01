# Virtuous CRM+ API: Giving endpoints
Based on Virtuous CRM+ OpenAPI spec (2026), retrieved 2026-08-31.

All giving endpoints live under the host `https://api.virtuoussoftware.com` with the base path `/api`, and every request needs a Bearer token (`Authorization: Bearer YOUR_API_TOKEN`) unless a note says otherwise. See `crm-fundamentals.md` for auth, rate limits, and the shared query/paging model. The single most important distinction in this domain is between a **Gift record** (the stored donation on a contact) and a **Gift Transaction** (a payload you push through the import and matching pipeline that becomes a Gift after a nightly batch). Prefer the Transaction path for anything coming from an external system, because it dedupes contacts, matches recurring gifts and pledges, and gives you idempotency for free; see `crm-concepts.md` for the full model.

## How this domain is organised

This reference groups 73 operations across nine resources:

| Resource | Ops | What it holds |
| --- | --- | --- |
| Gift | 18 | The donation records, plus the Transaction import pipeline and reversals |
| GiftAsk | 8 | Solicitations for a specific amount, usually tied to a project and fundraiser |
| GiftDesignation | 2 | Query-only view of gifts split out per project |
| Grant | 10 | Grants you are pursuing or have been awarded |
| PlannedGift | 8 | Bequests, trusts, and other future commitments |
| Pledge | 8 | Commitments to give a set amount over several payments |
| Premium | 10 | Donor thank-you items with inventory (books, tickets, shirts) |
| RecurringGift | 8 | Ongoing giving schedules |
| RecurringGiftPayment | 1 | The expected/fulfilled payments behind a schedule |

### Shared conventions

- **Paging.** List and Query endpoints take `skip` and `take` query parameters. The documented max `take` for Query endpoints is 1,000. Page by incrementing `skip`.
- **Queries.** Every Query endpoint (`POST .../Query`) takes a body of `{ groups, sortBy, descending }`. Call the matching `GET .../QueryOptions` endpoint first to discover the valid parameters, operators, and values before you build `groups` and their conditions.
- **Updates are full-model replacements.** For every `PUT` here, excluding a property removes its value. Send the entire model even when you change one field. The one exception is `PATCH /api/Gift`, which is a true patch (send only what changes).
- **Field typing.** The spec types almost every field as `string`, including amounts, dates, and boolean flags. The live API accepts and returns natural types, so send numbers for amounts, ISO 8601 strings for dates, and booleans for flags. See the field-typing warning in `crm-concepts.md`.

---

## Quick reference

Every endpoint in the domain, grouped by resource.

### Gift

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v2/Gift/Transaction` | Create one gift through the import/matching pipeline (recommended) |
| POST | `/api/v2/Gift/Transactions` | Bulk-create gifts through the import pipeline (recommended) |
| POST | `/api/Gift` | Create a gift directly on a known contact (not recommended) |
| POST | `/api/Gift/Bulk` | Create up to 100 gifts directly on known contacts (not recommended) |
| PATCH | `/api/Gift` | Bulk-update gifts with patch semantics (send only changed fields) |
| PUT | `/api/Gift/{giftId}` | Update one gift (full model required) |
| DELETE | `/api/Gift/{giftId}` | Delete a gift and its designations (cannot be undone) |
| GET | `/api/Gift/{giftId}` | Get one full gift by Virtuous id |
| GET | `/api/Gift/{transactionSource}/{transactionId}` | Get a gift by external source + id pair |
| GET | `/api/Gift/ByContact/{contactId}` | List gifts credited to a contact (paged, sortable) |
| GET | `/api/Gift/ByReference/{referenceId}` | List gifts by external reference id (HMAC auth only) |
| GET | `/api/Gift/Passthrough/ByContact/{contactId}` | List gifts that passed through a contact (DAF, employer match) |
| POST | `/api/Gift/Query` | Query gifts, abbreviated form (paged) |
| POST | `/api/Gift/Query/FullGift` | Query gifts, full detail (slower) |
| GET | `/api/Gift/QueryOptions` | Get valid fields, operators, values for gift queries |
| POST | `/api/Gift/ReversingTransaction` | Create a reversing transaction to offset a gift (refunds) |
| GET | `/api/Gift/CustomFields` | List enabled gift custom fields |
| GET | `/api/Gift/NonCashGiftTypes` | List configurable non-cash gift types |

### GiftAsk

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/GiftAsk` | Create a gift ask (solicitation) on a contact |
| GET | `/api/GiftAsk/{giftAskId}` | Get one gift ask |
| PUT | `/api/GiftAsk/{giftAskId}` | Update a gift ask (full model required) |
| GET | `/api/GiftAsk/{giftAskId}/Gifts` | List gifts applied to a gift ask |
| GET | `/api/GiftAsk/ByContact/{contactId}` | List gift asks for a contact (paged) |
| POST | `/api/GiftAsk/Query` | Query gift asks (paged) |
| GET | `/api/GiftAsk/QueryOptions` | Get valid fields, operators, values for gift ask queries |
| GET | `/api/GiftAsk/CustomFields` | List enabled gift ask custom fields |

### GiftDesignation

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/GiftDesignation/Query` | Query gifts split out per designation (one row per project) |
| GET | `/api/GiftDesignation/QueryOptions` | Get valid fields, operators, values for designation queries |

### Grant

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Grant` | Create a grant record |
| GET | `/api/Grant/{grantId}` | Get one grant |
| PUT | `/api/Grant/{grantId}` | Update a grant (full model required) |
| DELETE | `/api/Grant/{grantId}` | Delete a grant (applied gifts stay on contacts) |
| GET | `/api/Grant/{grantId}/Gifts` | List gifts applied to a grant |
| GET | `/api/Grant/ByContact/{contactId}` | List grants for a contact (paged) |
| GET | `/api/Grant/ByReference/{referenceId}` | Get a grant by external reference id |
| POST | `/api/Grant/Query` | Query grants (paged) |
| GET | `/api/Grant/QueryOptions` | Get valid fields, operators, values for grant queries |
| GET | `/api/Grant/CustomFields` | List enabled grant custom fields |

### PlannedGift

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/PlannedGift` | Create a planned gift (bequest, trust) on a contact |
| GET | `/api/PlannedGift/{plannedGiftId}` | Get one planned gift |
| PUT | `/api/PlannedGift/{plannedGiftId}` | Update a planned gift (full model required) |
| GET | `/api/PlannedGift/{plannedGiftId}/Gifts` | List gifts applied to a planned gift |
| GET | `/api/PlannedGift/ByContact/{contactId}` | List planned gifts for a contact (paged) |
| POST | `/api/PlannedGift/Query` | Query planned gifts (paged) |
| GET | `/api/PlannedGift/QueryOptions` | Get valid fields, operators, values for planned gift queries |
| GET | `/api/PlannedGift/CustomFields` | List enabled planned gift custom fields |

### Pledge

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v2/Pledge` | Create a pledge with a payment schedule |
| GET | `/api/v2/Pledge/{pledgeId}` | Get one pledge |
| PUT | `/api/v2/Pledge/{pledgeId}` | Update a pledge (full model required) |
| PUT | `/api/v2/Pledge/WriteOff/{pledgeId}` | Write off a pledge's unpaid balance |
| GET | `/api/v2/Pledge/ByContact/{contactId}` | List pledges for a contact (paged, sortable) |
| POST | `/api/v2/Pledge/Query` | Query pledges (paged) |
| GET | `/api/v2/Pledge/QueryOptions` | Get valid fields, operators, values for pledge queries |
| GET | `/api/v2/Pledge/CustomFields` | List enabled pledge custom fields |

### Premium

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Premium` | Create a premium (donor thank-you item) |
| GET | `/api/Premium/{premiumId}` | Get one premium |
| PUT | `/api/Premium/{premiumId}` | Update a premium (full model required) |
| GET | `/api/Premium/Code/{premiumCode}` | Get a premium by its unique code |
| PUT | `/api/Premium/Increment/{premiumId}` | Increase premium inventory (positive number) |
| PUT | `/api/Premium/Decrement/{premiumId}` | Decrease premium inventory (negative number) |
| POST | `/api/Premium/Search` | Search premiums by name or code (paged) |
| POST | `/api/Premium/Query` | Query premiums (paged) |
| GET | `/api/Premium/QueryOptions` | Get valid fields, operators, values for premium queries |
| GET | `/api/Premium/CustomFields` | List enabled premium custom fields |

### RecurringGift

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/RecurringGift` | Create a recurring gift schedule on a contact |
| GET | `/api/RecurringGift/{recurringGiftId}` | Get one recurring gift |
| PUT | `/api/RecurringGift/{recurringGiftId}` | Update a recurring gift (full model required) |
| PUT | `/api/RecurringGift/Cancel/{recurringGiftId}` | Cancel a recurring gift (keeps recorded payments) |
| GET | `/api/RecurringGift/ByContact/{contactId}` | List recurring gifts for a contact (paged, sortable) |
| POST | `/api/RecurringGift/Query` | Query recurring gifts (paged) |
| GET | `/api/RecurringGift/QueryOptions` | Get valid fields, operators, values for recurring gift queries |
| GET | `/api/RecurringGift/CustomFields` | List enabled recurring gift custom fields |

### RecurringGiftPayment

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/RecurringGiftPayment/{recurringGiftId}` | List expected/fulfilled payments for a recurring gift (paged) |

---

## Creating gifts: Transaction vs direct create

There are two ways to get a gift into Virtuous. Use the first unless you have a specific reason not to.

### Recommended: POST /api/v2/Gift/Transaction

This is the recommended way to create a gift. The payload goes into a holding state, and a nightly batch runs Virtuous's matching algorithms for contacts, recurring gifts, pledges, and designations. Note the `v2` path segment. This endpoint accepts **HMAC or OAuth** auth per the spec; standard Bearer API-key auth also works in practice.

Key body fields (from the spec):

| Field | Notes |
| --- | --- |
| `transactionSource` | Your platform name, e.g. `"Stripe"`. Half of the idempotency key. |
| `transactionId` | Your unique id for this donation. The other half of the idempotency key. |
| `contact` | Embedded contact block; the matching algorithm runs against it. See `crm-api-contacts.md`. |
| `giftDate` | Date of the gift. |
| `giftType` | `Cash`, `EFT`, `Stock`, etc. Call `GET /api/Gift/NonCashGiftTypes` for the non-cash subset. |
| `amount` | Gift amount. Must equal the sum of designation amounts. |
| `currencyCode`, `exchangeRate` | Multi-currency support. |
| `frequency` | Set for recurring-schedule payments. |
| `recurringGiftTransactionId`, `recurringGiftTransactionUpdate` | Link this payment to an existing recurring schedule. |
| `pledgeFrequency`, `pledgeTransactionId`, `pledgeExpectedFullfillmentDate` | Link this payment to a pledge. (`Fullfillment` is spelled that way in the spec.) |
| `batch`, `notes`, `segment`, `mediaOutlet` | Bookkeeping and attribution. |
| `receiptDate`, `receiptSegment` | Receipting. |
| `cashAccountingCode`, `isTaxDeductible`, `isPrivate` | Accounting and visibility. |
| `tribute`, `tributeDedication` | In-honor-of / in-memory-of details. |
| `checkNumber`, `creditCardType` | Payment instrument details. |
| `nonCashGiftTypeId`, `nonCashGiftType`, `nonCashGiftDescription` | In-kind gift details. |
| `stockTickerSymbol`, `stockNumberOfShares`, `iraCustodian` | Stock and IRA gift details. |
| `submissionUrl` | Source URL for the gift. |
| `designations` | Array; how the amount is split across projects (see below). |

```bash
curl -X POST https://api.virtuoussoftware.com/api/v2/Gift/Transaction \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transactionSource": "YourPlatform",
    "transactionId": "donation-9421",
    "contact": {
      "referenceId": "donor-abc123",
      "name": "Bruce Wayne",
      "type": "Household",
      "firstname": "Bruce",
      "lastname": "Wayne",
      "emailType": "Home Email",
      "email": "bruce@wayne.example",
      "phoneType": "Mobile Phone",
      "phone": "555-0100",
      "address": {
        "address1": "1007 Mountain Drive",
        "city": "Gotham",
        "state": "NJ",
        "postal": "07001",
        "country": "US"
      }
    },
    "giftDate": "2024-12-15",
    "giftType": "Cash",
    "amount": "500.00",
    "currencyCode": "USD",
    "batch": "Year-End-2024",
    "designations": [
      { "projectCode": "CLEAN-WATER", "amountDesignated": "500.00" }
    ]
  }'
```

The endpoint returns `200 OK` to confirm the payload was accepted into the holding state. It does **not** return a created gift id, because the gift does not exist yet. Detect the outcome with webhooks (`Gift Created`) or by polling `GET /api/Gift/{transactionSource}/{transactionId}`. See `crm-concepts.md` for the matching, needs-update, and webhook details.

> Ambiguity to verify: the spec digest names the array `designations`, but the published concept-page cURL example names it `giftDesignations`. The example above follows the digest field name. Confirm against a live call if a submission's designations do not attach.

### Recommended for volume: POST /api/v2/Gift/Transactions

Submits a batch of gift transactions through the same import process, each matched by the same algorithms. This is the recommended way to load many gifts at once. HMAC or OAuth auth valid.

| Field | Notes |
| --- | --- |
| `transactionSource` | Platform name applied to the batch. |
| `transactions` | Array of gift transaction objects (same shape as the single endpoint). |
| `createImport` | Whether to create a visible import record. |
| `importName` | Name for the import in the Virtuous UI. |
| `batch`, `batchTotal` | Batch label and expected control total. |
| `defaultGiftDate`, `defaultGiftType` | Defaults applied to transactions that omit them. |

```json
POST /api/v2/Gift/Transactions
{
  "transactionSource": "YourPlatform",
  "createImport": true,
  "importName": "Nightly Stripe sync 2024-12-15",
  "batch": "Year-End-2024",
  "batchTotal": "1000.00",
  "defaultGiftDate": "2024-12-15",
  "defaultGiftType": "Cash",
  "transactions": [
    { "transactionId": "donation-9421", "amount": "500.00", "contact": { "referenceId": "donor-abc123" },
      "designations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "500.00" } ] },
    { "transactionId": "donation-9422", "amount": "500.00", "contact": { "referenceId": "donor-def456" },
      "designations": [ { "projectCode": "EDU", "amountDesignated": "500.00" } ] }
  ]
}
```

### Not recommended: POST /api/Gift and POST /api/Gift/Bulk

These create a gift (or up to 100 gifts) **directly** on a contact record. The spec labels both **"not recommended"** and warns that Virtuous does not support cleaning up data caused by creating gifts incorrectly this way. Use them only when you have already verified the exact `contactId` and you need a synchronous result. Prefer the Transaction endpoints for anything else.

Key body fields include `contactId`, `giftType`, `giftDate`, `amount`, `transactionSource`, `transactionId`, `batch`, `segmentId`, `receiptSegmentId`, `mediaOutletId`, `notes`, `isPrivate`, `receiptDate`, `contactIndividualId`, `contactPassthroughId`, `cashAccountingCode`, `state`, `isTaxDeductible`, `giftAskId`, `passthroughGiftAskId`, `grantId`, `contactMembershipId`, `currencyCode`, `exchangeRate`, `checkNumber`, `creditCardType`, and the non-cash / stock / crypto fields (`cryptocoinType`, `transactionHash`, `coinAmount`, `tickerSymbol`, `numberOfShares`, `iraCustodian`, `stockSoldForCash`, and more).

```json
POST /api/Gift
{
  "contactId": 4821,
  "giftType": "Cash",
  "giftDate": "2024-12-15",
  "amount": 500.00,
  "transactionSource": "YourPlatform",
  "transactionId": "donation-9421",
  "isTaxDeductible": true
}
```

`POST /api/Gift/Bulk` takes an array of the same objects (max 100).

---

## Reading gifts

| Goal | Endpoint |
| --- | --- |
| One gift by Virtuous id | `GET /api/Gift/{giftId}` |
| One gift by your ids | `GET /api/Gift/{transactionSource}/{transactionId}` |
| All gifts for a contact | `GET /api/Gift/ByContact/{contactId}` |
| Gifts that passed through a contact (DAF, match) | `GET /api/Gift/Passthrough/ByContact/{contactId}` |
| Gifts recorded against an external reference id | `GET /api/Gift/ByReference/{referenceId}` (HMAC auth only) |
| Filtered / paged retrieval | `POST /api/Gift/Query` |
| Filtered retrieval with full detail | `POST /api/Gift/Query/FullGift` |

`GET /api/Gift/{giftId}` returns the full record, including designations, premiums, tribute, payment details, and the credited contact. The `ByContact`, `ByReference`, and `Passthrough/ByContact` list endpoints support `skip`/`take`; `ByContact` and `Passthrough/ByContact` also sort by `Id`, `Amount`, `GiftDate`, `ReceiptDate`, and `Batch` via `sortBy` + `descending`.

`GET /api/Gift/ByReference/{referenceId}` also accepts `excludeReferenceOriginatedGifts` to filter out gifts that originated from that reference. It is **HMAC auth only**.

### Querying gifts

Call `GET /api/Gift/QueryOptions` first to learn the valid parameters, operators, and values, then build `groups`. Each group carries a list of conditions; use `skip`/`take` to page. Sortable fields are `Id`, `Amount`, `GiftDate`, `ReceiptDate`, and `Batch`.

```json
POST /api/Gift/Query?skip=0&take=100
{
  "groups": [
    {
      "conditions": [
        { "parameter": "Gift Date", "operator": "GreaterThanOrEqual", "value": "2024-12-01" },
        { "parameter": "Gift Date", "operator": "LessThanOrEqual",   "value": "2024-12-31" }
      ]
    }
  ],
  "sortBy": "GiftDate",
  "descending": true
}
```

The exact `parameter` names, `operator` values, and value formats come from the QueryOptions response, so treat the keys above as illustrative and confirm them there. Use `POST /api/Gift/Query` for speed; reach for `POST /api/Gift/Query/FullGift` only when you need every designation, premium, and pledge linkage, since it is slower.

---

## Updating and deleting gifts

### PUT /api/Gift/{giftId} – full replacement

Update one gift. Excluding a property removes its value, so send the whole model. `GiftDate` uses only the date portion of the value to set the UTC date, with no timezone conversion, so pass a plain date. Body fields mirror the create fields plus stock-sale details (`dateStockWasSold`, `stockSaleAmount`) and `nonCashGiftTypeId`.

### PATCH /api/Gift – bulk patch

Use this whenever more than one gift changes. Unlike the `PUT`, this is a true patch: send only the gift id and the fields you are changing. The body is an array of objects with `id`, plus any of `receiptDateUtc`, `segmentId`, `notes`, and `customFields`.

```json
PATCH /api/Gift
[
  { "id": 78421, "receiptDateUtc": "2024-12-20T00:00:00Z" },
  { "id": 78422, "receiptDateUtc": "2024-12-20T00:00:00Z", "notes": "Receipted in year-end run" }
]
```

### DELETE /api/Gift/{giftId} – rarely what you want

Deletes the gift and its designations. This cannot be undone and it changes the contact's giving history and totals. **Do not use it for refunds or returned payments** – use a reversing transaction instead (next section).

---

## Refunds and reversals

To offset a gift (a refund, a returned check, a chargeback), create a reversing transaction rather than deleting the gift. The original gift stays on the record for audit purposes, and the reversal is a separate offsetting record that negates the amount and its splits.

```json
POST /api/Gift/ReversingTransaction
{
  "giftDate": "2025-01-05",
  "reversedGiftId": 78421,
  "notes": "Stripe refund re:ch_3PXyz123"
}
```

| Field | Notes |
| --- | --- |
| `reversedGiftId` | The gift being negated. |
| `giftDate` | Date of the reversal. |
| `notes` | Free-text reason. |

---

## Gift designations

A designation allocates part or all of a gift's amount to a project. A gift always has at least one designation, and the designation amounts must sum to the gift's `amount` (the API enforces this at creation). Within a gift transaction, reference a project by `projectId`, `projectCode`, or `externalAccountingCode`, and set `amountDesignated` for each split.

```json
"designations": [
  { "projectCode": "CLEAN-WATER", "amountDesignated": "300.00" },
  { "projectId": 412,            "amountDesignated": "200.00" }
]
```

Two query-only endpoints let you report on gifts broken out per designation, so a gift split across three projects returns three rows:

- `POST /api/GiftDesignation/Query` – sortable by `Id`, `Amount`, `GiftDate`, `ReceiptDate`, `Batch`; paged with `skip`/`take`.
- `GET /api/GiftDesignation/QueryOptions` – the valid parameters, operators, and values for that query.

Projects and campaigns themselves live in the campaigns/events domain; see `crm-api-campaigns-events.md`. Campaigns are read-only through the API.

---

## Recurring gifts

A recurring gift is a schedule; each successful payment becomes a Gift with `recurringGiftTransactionId` set to the schedule. Manage the schedule with these endpoints, and read the payments behind it with `RecurringGiftPayment`.

### Create – POST /api/RecurringGift

| Field | Notes |
| --- | --- |
| `contactId` | The donor. |
| `startDate`, `frequency`, `amount` | The core schedule. |
| `nextExpectedPaymentDate`, `anticipatedEndDate` | Schedule horizon. |
| `automatedPayments` | Set when an external processor collects payments. |
| `trackPayments` | Set so Virtuous expects a payment each period and surfaces missed ones. |
| `thankYouDate`, `segmentId`, `isPrivate` | Stewardship and attribution. |
| `designations` | Array of project splits (inherited by each payment gift). |
| `customFields` | Array of custom field values. |

```json
POST /api/RecurringGift
{
  "contactId": 4821,
  "startDate": "2025-01-01",
  "frequency": "Monthly",
  "amount": 50.00,
  "nextExpectedPaymentDate": "2025-01-01",
  "automatedPayments": true,
  "trackPayments": true,
  "designations": [ { "projectCode": "CLEAN-WATER", "amountDesignated": "50.00" } ]
}
```

### Update – PUT /api/RecurringGift/{recurringGiftId}

Full-model replacement; same fields as create minus `contactId`.

### Cancel – PUT /api/RecurringGift/Cancel/{recurringGiftId}

Cancels the schedule so no further payments are expected. Payments already recorded are kept.

```json
PUT /api/RecurringGift/Cancel/{recurringGiftId}
{
  "cancelReason": "Donor request",
  "categoryId": 3
}
```

`cancelReason` records why; `categoryId` groups the cancellation for reporting.

### Read

- `GET /api/RecurringGift/{recurringGiftId}` – one schedule with its designations, status, and next expected payment date.
- `GET /api/RecurringGift/ByContact/{contactId}` – a contact's schedules (paged, sortable).
- `POST /api/RecurringGift/Query` + `GET /api/RecurringGift/QueryOptions` – filtered retrieval.
- `GET /api/RecurringGiftPayment/{recurringGiftId}` – the expected payments, each with the gift that fulfilled it or the date it was dismissed if never collected (paged).

> Recurring vs one-time: create the schedule once with `POST /api/RecurringGift` (or let a gift transaction match one via `recurringGiftTransactionId`). Do **not** create a fresh schedule per payment. Individual payments arrive as ordinary gifts linked back to the schedule.

---

## Pledges

A pledge is a commitment to give a set amount, usually over several payments. Note the `v2` path segment on all pledge endpoints. Each payment toward a pledge becomes a Gift with `pledgeTransactionId` set to the pledge.

### Create – POST /api/v2/Pledge

| Field | Notes |
| --- | --- |
| `contactId` | The donor. |
| `amountPledged` | Total committed. |
| `frequency`, `pledgeDate`, `expectedFulfillmentDate` | Schedule and target completion. |
| `payments` | Array defining the expected payment schedule. |
| `giftAskId` | The ask this pledge answers, if any. |
| `segmentId`, `projectId`, `isPrivate` | Attribution and visibility. |
| `customFields` | Array of custom field values. |

```json
POST /api/v2/Pledge
{
  "contactId": 4821,
  "amountPledged": 10000.00,
  "frequency": "Annual",
  "pledgeDate": "2025-01-01",
  "expectedFulfillmentDate": "2028-12-31",
  "projectId": 311,
  "payments": [
    { "amount": 2500.00, "date": "2025-01-01" },
    { "amount": 2500.00, "date": "2026-01-01" },
    { "amount": 2500.00, "date": "2027-01-01" },
    { "amount": 2500.00, "date": "2028-01-01" }
  ]
}
```

> The `payments` array items carry the schedule; the spec digest does not enumerate their sub-fields, so confirm the exact keys against a live call or the fuller schema. The `amount`/`date` shape above is illustrative.

### Update – PUT /api/v2/Pledge/{pledgeId}

Full-model replacement; fields match create minus `contactId`.

### Write off – PUT /api/v2/Pledge/WriteOff/{pledgeId}

Writes off the unpaid balance so it no longer counts as expected revenue. Payments already applied are kept. Send a `reason`.

```json
PUT /api/v2/Pledge/WriteOff/{pledgeId}
{ "reason": "Donor unable to complete pledge" }
```

### Read

- `GET /api/v2/Pledge/{pledgeId}` – one pledge with amount, frequency, expected payments, and amount paid so far.
- `GET /api/v2/Pledge/ByContact/{contactId}` – a contact's pledges (paged, sortable).
- `POST /api/v2/Pledge/Query` + `GET /api/v2/Pledge/QueryOptions` – filtered retrieval.

---

## Premiums

A premium is a donor thank-you item (a book, an event ticket, a shirt) with tracked inventory. Assign premiums to gifts by `premiumId` when recording the gift.

### Create – POST /api/Premium

| Field | Notes |
| --- | --- |
| `name` | Display name. |
| `code` | Must be unique. |
| `price` | What a donor pays. |
| `fairMarketValue` | Amount that reduces the tax-deductible portion of a gift. |
| `cost` | What the item costs you. |
| `description` | Free text. |
| `inventoryCount` | Quantity on hand; adjust later with Increment/Decrement. |
| `isActive` | Whether the premium is available. |
| `customFields` | Array of custom field values. |

`PUT /api/Premium/{premiumId}` replaces the full model with the same fields.

### Inventory

Adjust stock without a full update:

- `PUT /api/Premium/Increment/{premiumId}?incrementor=N` – `incrementor` defaults to `1` and MUST be positive.
- `PUT /api/Premium/Decrement/{premiumId}?decrementor=-N` – `decrementor` defaults to `-1` and MUST be negative.

### Find and read

- `GET /api/Premium/{premiumId}` – one premium by id.
- `GET /api/Premium/Code/{premiumCode}` – one premium by its unique code (useful when your system tracks premiums by code).
- `POST /api/Premium/Search` – full or partial match on name or code; body `{ "search": "..." }`, paged with `skip`/`take`.
- `POST /api/Premium/Query` + `GET /api/Premium/QueryOptions` – structured filtered retrieval.

```json
POST /api/Premium/Search?skip=0&take=25
{ "search": "annual report" }
```

---

## Gift asks, planned gifts, and grants

These three resources follow the same CRUD-plus-query shape. Each has `Create`, `Get`, `Update` (full-model `PUT`), a `ByContact` list, a `Query` + `QueryOptions` pair, `CustomFields`, and a `.../Gifts` sub-list showing the gifts applied so you can compare committed against received.

### GiftAsk – POST /api/GiftAsk

Records a solicitation for a specific amount, usually tied to a project and fundraiser. Set `declined` when the ask was turned down, and `expectedFulfillmentDate` to track when you expect the gift.

Body: `contactId`, `askAmount`, `askDate`, `expectedFulfillmentDate`, `notes`, `askType`, `frequency`, `declined`, `projectId`, `segmentId`, `assignedUserId`, `secondaryAssignedUserId`, `status`, `customFields`. Read applied gifts with `GET /api/GiftAsk/{giftAskId}/Gifts`.

### PlannedGift – POST /api/PlannedGift

Records a future commitment such as a bequest or a trust. Use `anticipatedAmount` and `anticipatedStartDate` for what you expect, and `currentValue` for what the commitment is worth today.

Body: `contactId`, `plannedGiftDate`, `plannedGiftType`, `frequency`, `anticipatedAmount`, `anticipatedStartDate`, `numberOfOccurrences`, `currentValue`, `contactIndividualId`, `assignedUserId`, `projectId`, `segmentId`, `thankYouDate`, `customFields`. Read realised gifts with `GET /api/PlannedGift/{plannedGiftId}/Gifts`.

### Grant – POST /api/Grant

Records a grant you are pursuing or have been awarded. Track it through submission and award with `status` and the date fields, set `referenceId` to your own identifier, and set `projectId` to the project the funding supports. Grants also support `GET /api/Grant/ByReference/{referenceId}` and `DELETE /api/Grant/{grantId}` (applied gifts stay on their contacts).

Body: `ownerId`, `title`, `grantingOrganizationId`, `description`, `referenceId`, `receivingOrganizationId`, `projectId`, `dueDate`, `totalAnticipatedAmount`, `status`, `submissionDate`, `anticipatedAwardDate`, `pointOfContactName`, `pointOfContactEmail`, `pointOfContactPhone`, `website`, `awardedGrant`, `awardedAmount`, `awardedDate`, `awardTerms`, `grantType`, `customFields`. Read applied gifts with `GET /api/Grant/{grantId}/Gifts`.

---

## Gotchas

- **Prefer the Transaction/import path over raw gift creation.** `POST /api/v2/Gift/Transaction` and `.../Transactions` run Virtuous's matching (contact dedupe, recurring, pledge, designation) and are the recommended path. `POST /api/Gift` and `/api/Gift/Bulk` are labelled "not recommended" and skip matching; the spec warns Virtuous will not clean up the resulting mess. Use direct create only with a verified `contactId` and a real need for synchronous results.
- **The Transaction endpoint is asynchronous.** A `200 OK` means "accepted into holding", not "gift created". No gift id comes back. Detect the real gift with the `Gift Created` webhook or `GET /api/Gift/{transactionSource}/{transactionId}`. Some gifts land in the "needs update" bucket for manual resolution and never appear in queries; build reconciliation to tolerate that. See `crm-concepts.md`.
- **Reference ids give you idempotency.** Set `transactionSource` + `transactionId` on every gift transaction. Re-submitting the same pair is recognised as a duplicate and does not create a second gift, which makes retries safe. Use stable ids from your platform (a Stripe charge id, your donation id), not fresh UUIDs per retry.
- **Designation amounts must sum to the gift amount.** The API enforces `sum(amountDesignated) == amount` at creation. A single-project gift still needs one designation for the full amount. Reference projects by `projectId`, `projectCode`, or `externalAccountingCode`.
- **Designation field-name ambiguity.** The spec digest names the gift-transaction array `designations`; the published concept-page example names it `giftDesignations`. Verify against a live call if splits do not attach.
- **Recurring vs one-time.** Create a schedule once; each payment is a separate gift linked by `recurringGiftTransactionId`. Do not create a new schedule per payment. Same idea for pledges via `pledgeTransactionId`.
- **Refund with a reversal, not a delete.** `POST /api/Gift/ReversingTransaction` preserves the audit trail. `DELETE /api/Gift/{giftId}` erases history and totals and cannot be undone.
- **`PUT` replaces; `PATCH /api/Gift` patches.** Every `PUT` here needs the full model – omitting a field clears it. Only the bulk `PATCH /api/Gift` accepts a partial payload.
- **`GiftDate` has no timezone conversion.** On `PUT /api/Gift/{giftId}` it uses only the date portion to set the UTC date. Pass a plain date to avoid off-by-one-day shifts.
- **Two endpoints are auth-restricted.** `GET /api/Gift/ByReference/{referenceId}` is HMAC auth only. The `v2` Gift Transaction endpoints accept HMAC or OAuth (Bearer works in practice).
- **`v2` paths are inconsistent.** Gift Transactions and all Pledge endpoints sit under `/api/v2/...`; everything else uses `/api/...`. This is a known spec quirk; the paths above are correct as written.
- **Spec types everything as `string`.** Send natural types anyway (numbers, ISO dates, booleans). SDK generators that read the spec literally will produce wrong types.

## Related skills

- `crm-fundamentals.md` – auth (Bearer, HMAC, OAuth), rate limits, paging, and the shared query model.
- `crm-concepts.md` – the Gift resource, the Transaction/import pipeline, matching, the needs-update bucket, and webhooks.
- `crm-workflows.md` – end-to-end recipes such as creating a donation and querying donations by date range.
- `crm-recipes.md` – full integration recipes (for example, Stripe gift events flowing into Virtuous).
- `crm-api-contacts.md` – the embedded contact block used inside a gift transaction, and contact reads/writes.
- `crm-api-campaigns-events.md` – projects and campaigns that designations point to (campaigns are read-only through the API).
