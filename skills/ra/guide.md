# Resident Advisor GraphQL: Usage guide
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18). Not an official, documented API. Fields can change without notice.

## Endpoint and etiquette

- `POST https://ra.co/graphql`, `Content-Type: application/json`, body `{"query": "...", "variables": {...}}`.
- Send a browser-like `User-Agent`. Introspection is enabled, so the schema is discoverable.
- Public read queries work without authentication. `Ticketing_*`, `Embeddable_*`, payment, guestlist, presale, HelpScout and every `Mutation` need credentials. Do not call them without the account owner's authorisation.
- This is a private API. Check RA's terms before automated or bulk use, cache results, and keep request rates low.
- GraphQL validation errors return HTTP 200 with an `errors` array. Check `errors`, not the status code.

## Conventions

- IDs are strings (`"34"`), even where filters take integers (`areas: {eq: 34}`).
- Dates are ISO strings without timezone in responses (`2026-10-20T00:00:00.000`). Send UTC ISO strings in filters.
- `contentUrl` is a path on ra.co: `/events/<id>`, `/clubs/<id>`. Artists use slug URLs (`/dj/<slug>`).
- `search` returns `searchType` `VENUE` for `IndexType.CLUB`.
- Find an Area id with `areas(searchTerm:)`. Berlin is `34`.

## Verified examples

Find an area:

```graphql
{ areas(searchTerm: "Berlin") { id name urlName country { urlCode } } }
```

Event listings for an area and date range (the main listing query behind ra.co/events):

```graphql
query($f: FilterInputDtoInput, $o: FilterOptionsInputDtoInput) {
  eventListings(filters: $f, filterOptions: $o, page: 1, pageSize: 20,
                sort: { listingDate: { order: ASCENDING } }) {
    totalResults
    data { id listingDate event { id title date startTime contentUrl venue { id name } artists { id name } } }
  }
}
# variables
{ "f": { "areas": { "eq": 34 },
         "listingDate": { "gte": "2026-10-20T00:00:00.000Z", "lte": "2026-10-27T00:00:00.000Z" } },
  "o": { "genre": true } }
```

Search (indices: `EVENT ARTIST CLUB PROMOTER LABEL AREA NEWS REVIEW FEATURE PODCAST EXCHANGE`):

```graphql
{ search(searchTerm: "Berghain", limit: 5, indices: [CLUB]) { id value contentUrl searchType } }
```

Venue by id:

```graphql
{ venue(id: 5031) { id name address capacity area { name } } }
```

## Pitfalls

- `IndexType` has `CLUB`, not `VENUE`. `VENUE` is only a `GlobalSearchType` result value.
- `artist(slug:)` returned `null` for guessed slugs. Get the id or slug from `search(indices:[ARTIST])` or `event.artists` first.
- `eventsListing` is deprecated. Use `eventListings`.
- `events(type:)` is required (`EventQueryType`). It returned an empty list for `LATEST` and `FROMDATE` in tests; prefer `eventListings`.
- Request only the fields you need. `Event`, `Artist` and `Venue` are large types.
- Do not hard-code field lists from memory. Check `types-public.md` or run introspection again.

## Files

| File | Content |
|---|---|
| [queries.md](./queries.md) | All 97 root query fields with arguments |
| [mutations.md](./mutations.md) | All 115 mutations (authenticated) |
| [types-public.md](./types-public.md) | Public object types (Event, Artist, Venue, Area, Label, Promoter, News, Search, listings) |
| [types-ticketing.md](./types-ticketing.md) | Ticketing, payment, guestlist, presale, embeddable, admin types |
| [inputs.md](./inputs.md) | Input types, including listing filters |
| [enums.md](./enums.md) | Enums and unions |

## Refresh the schema

```bash
curl -s -H 'Content-Type: application/json' -A 'Mozilla/5.0' https://ra.co/graphql \
  -d '{"query":"{ __schema { types { name kind } } }"}'
```
