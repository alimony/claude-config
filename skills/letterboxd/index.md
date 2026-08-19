# Letterboxd API Skills

Based on Letterboxd API v0 documentation.
Generated from https://api-docs.letterboxd.com on 2026-08-19.

The API base URL is `https://api.letterboxd.com/api/v0/`. The documentation is one single page, so the sections below map to that page, not to separate URLs.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [overview](./overview.md) | Base URL, LIDs, cursor pagination, the 100,000 object cap, errors, images, the First Party rule | 335 |
| [authentication](./authentication.md) | OAuth2 flow choice, `/auth/token`, scopes, OIDC, refresh, revocation, `/auth/*` endpoints | 397 |
| [films](./films.md) | `GET /films` filters and sorts, film collections, contributors, availability, statistics | 500 |
| [log-entries](./log-entries.md) | Diary entries, reviews, ratings, `POST`/`PATCH` bodies, the log entry data model | 450 |
| [lists](./lists.md) | List queries, creation, the `entries` edit-command model, delete against forget, policies | 480 |
| [members](./members.md) | Member lookup, activity feed, watchlist, tags, follow and block, statistics | 496 |
| [me](./me.md) | `GET`/`PATCH /me`, watch, rate, like, watchlist, subscribe, favourites, tags | 408 |
| [search](./search.md) | `GET /search`, the polymorphic result dispatch, autocomplete, news, featured content | 320 |
| [stories-and-comments](./stories-and-comments.md) | Stories, the cross-cutting comment model, the two-step report pattern | 424 |
| [schemas-entities](./schemas-entities.md) | Naming conventions, core entity fields, polymorphic types, request bodies, full schema index | 892 |
| [schemas-enums](./schemas-enums.md) | All 27 enums with all 246 literal values, mapped to the parameters that accept them | 472 |

## Start Here

Read [overview](./overview.md) and [authentication](./authentication.md) first. They carry the rules that apply to every other file: how to get a token, which flow you are allowed to use, how to page through results, and how a LID works.

## Two Restrictions To Know Before You Design A Feature

The API blocks third-party clients in two different ways. Do not confuse them.

| Mechanism | Where it appears | Effect |
|---|---|---|
| The `client:firstparty` **scope** | The Security row of 5 endpoints | Your token cannot call the endpoint at all |
| The **FIRST PARTY** documentation marker | 1 endpoint, 20 query parameters, 28 schema fields | The parameter is refused, or the field is absent from the response |

The 5 endpoints that need the `client:firstparty` scope are `GET /auth/get-upload-url`, `POST /me/register-push-notifications`, `POST /me/deregister-push-notifications`, `POST /me/validation-request` and `PATCH /me/favorite-productions`.

The 20 marked parameters are `similarTo`, `theme`, `minigenre` and `nanogenre` on `GET /films`, `GET /film-collection/{id}`, `GET /list/{id}/entries`, `GET /member/{id}/watchlist` and `GET /contributor/{id}/contributions`.

52 of the 102 endpoints need no scope at all. Those endpoints work with a Client Credentials token, so you can build a read-only application without a member login. See [overview](./overview.md) for the full table.

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/letterboxd/films.md

Or reference this index to see all available skills:

    @~/.claude/skills/letterboxd/index.md

## Coverage

- Documentation read: the complete single-page reference (222,400 characters, 8,113 lines after conversion)
- Endpoint groups covered: 13 of 13
- Operations covered: 102 of 102
- Schemas covered: 217 (190 objects, 27 enums)
- Skill files created: 11
- Total lines: 5,174
- Pages failed: 0

## Verification Notes

- All 246 enum literal values were checked against the source. None are missing.
- Every endpoint scope requirement was extracted from the Security row of each operation, not inferred.
- All JSON and Python code blocks parse.
- The docs sit behind Cloudflare, so the page was read through a browser and cross-checked against an archived copy. Every one of the 115 section anchors matched.

## Known Gaps In The Official Documentation

These are gaps in Letterboxd's own reference, not gaps in these skills. Each file states the gap where it applies.

- The `/production/...` endpoints are missing. Many `/film/...` endpoints are marked deprecated and point at `/production/...`, but no such endpoint group is documented.
- The concrete subtypes of `AbstractActivity`, `AbstractSearchItem` and `FeaturedContentItem` are not documented. The discriminator value tables are empty, so the payload field names are unverified.
- The token response schema is not published. Only `expires_in` is named.
- `/auth/authorize` has no endpoint entry, so its query parameters come from the OAuth2 standard.
- No general rate limit, no `Retry-After` and no `401` status are documented anywhere.
- The behaviour at the 100,000 object pagination cap is not stated.
