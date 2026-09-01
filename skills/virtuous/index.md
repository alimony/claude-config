# Virtuous CRM+ skills

Based on Virtuous CRM+ documentation and the `virtuous-crm-openapi-spec-2026.yaml` OpenAPI spec (version 2026).
Generated from https://docs.virtuous.org/crm/overview on 2026-08-31.

Virtuous is a nonprofit CRM and fundraising platform. These skills cover the **CRM+ REST API** for partner integrations: contacts, giving, campaigns/projects/events, webhooks, and the supporting endpoints. The docs site also hosts separate products (Raise, Volunteer, Momentum, Analytics) that are out of scope here.

## Key facts at a glance

- **API host:** `https://api.virtuoussoftware.com`, base path `/api` (the auth token endpoint is `POST /Token`, at the root, not under `/api`).
- **Auth:** `Authorization: Bearer <token>` on every request. Tokens come from an API key or the OAuth password grant. Some reference-lookup endpoints are HMAC-auth only. See `crm-fundamentals.md`.
- **Golden rule for writes:** prefer the **Transaction (import-pipeline) endpoints** (`POST /api/Contact/Transaction`, `POST /api/v2/Gift/Transaction`). They run Virtuous's matching algorithm and are dedupe-safe; raw `POST /api/Contact` and `POST /api/Gift` do not deduplicate.
- **Idempotency keys:** `referenceSource` + `referenceId` (Contacts), `transactionSource` + `transactionId` (Gifts and RecurringGifts). Carry a stable source ID on every write.
- **Rate limit:** 5,000 requests/hour, per Virtuous organization (shared across all credentials in that org).

## Available skills

| Skill | Topics covered | Lines |
|-------|----------------|-------|
| [crm-fundamentals](./crm-fundamentals.md) | Authentication (OAuth token, API keys, HMAC, 2FA), base URLs and environments, rate limits and headers, error handling, first authenticated call | 400 |
| [crm-concepts](./crm-concepts.md) | Data model: Contact / Individual / Method / Address hierarchy, Gifts vs Transactions, funds/campaigns/designations/projects, reference IDs vs Virtuous IDs, custom fields and collections, statuses and lifecycle | 437 |
| [crm-workflows](./crm-workflows.md) | Create/update a contact, record a donation, query contacts by filter, query donations by date range, handle duplicates, one-way and two-way sync, reconcile failed syncs | 459 |
| [crm-recipes](./crm-recipes.md) | Source-specific integrations: Stripe, Mailchimp, Constant Contact, P2P/crowdfunding, auction/event platforms, nightly batch sync, historical-gift backfill, recurring-donor lifecycle | 376 |
| [crm-webhooks](./crm-webhooks.md) | Event types, subscription management, signature verification, idempotency and safe processing, retry behavior, local testing | 509 |
| [crm-best-practices](./crm-best-practices.md) | Performance, data modeling, error recovery, security and credential management, sync architecture, versioning and backward compatibility | 437 |
| [crm-api-contacts](./crm-api-contacts.md) | Endpoint reference (91 ops): Contact, ContactIndividual, ContactMethod, ContactAddress, ContactNote, ContactTag, Tag, ContactReference, Relationship, OrganizationGroup, Tribute | 520 |
| [crm-api-giving](./crm-api-giving.md) | Endpoint reference (73 ops): Gift, Gift Transaction, RecurringGift, Pledge, PlannedGift, GiftAsk, GiftDesignation, Premium, Grant | 591 |
| [crm-api-campaigns-events](./crm-api-campaigns-events.md) | Endpoint reference (69 ops): Campaign, Communication, Segment, Project (+ notes/roles/expenses), Event, EventAttendee | 526 |
| [crm-api-system](./crm-api-system.md) | Endpoint reference (59 ops): Token, Organization, Permission, Webhook, Task, Email/EmailList, Search, plus deprecated Reminder and cross-product Volunteer endpoints | 440 |

## How to use

The guide skills (fundamentals, concepts, workflows, recipes, webhooks, best-practices) teach how to build integrations properly. The four `crm-api-*` skills are endpoint references synthesized directly from the 2026 OpenAPI spec, each with a complete method/path/purpose table plus deep dives on the important calls.

Reference a specific skill in a project's CLAUDE.md:

    @~/.claude/skills/virtuous/crm-workflows.md

Or point at this index to expose the whole set:

    @~/.claude/skills/virtuous/index.md

## Coverage

- Guide pages read (full markdown): **44**
- API operations documented from the 2026 OpenAPI spec: **292** (across 237 paths)
- Skill files created: **10**
- Total lines (excluding this index): **4,695**
- Pages failed or inaccessible: **0**

## Known documentation issues (reconciled in these skills)

The upstream docs and spec contain a few genuine inconsistencies. These skills resolve them as follows, but confirm against a live org before production:

- **Rate limit:** the authoritative pages and the `X-RateLimit-Limit: 5000` header say 5,000/hour; two pages (`error-handling`, `first-api-call`) show a stale 1,500/1499 figure. These skills use **5,000/hour**.
- **Spec field typing:** the OpenAPI spec types nearly every field (booleans, integers, dates, money) as `string`, while the live API accepts natural types. Send native types; treat auto-generated SDKs with caution.
- **Webhook event names:** most docs use camelCase (`giftCreate`, `contactUpdate`); one page uses dotted (`gift.created`). Verify the canonical form per event; `crm-webhooks.md` standardizes on the 15 subscription toggle fields.
- **Webhook signature scheme:** the exact header, algorithm, and signed-string format are not published in the spec. `crm-webhooks.md` documents an HMAC-SHA256 approach as presumed and flags it for confirmation.
- **Versioning:** most endpoints are under `/api`, but the Gift Transaction endpoint is `POST /api/v2/Gift/Transaction` and Pledges are under `/api/v2/Pledge/*`.
