# TMDB API Skills

Based on The Movie Database (TMDB) API v3 documentation.
Generated from https://developer.themoviedb.org/docs/getting-started on 2026-08-24.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [getting-started](./getting-started.md) | Base URL, request shape, pagination envelope, the 500-page cap, error codes, rate limits, JSONP, attribution, client libraries | 481 |
| [authentication](./authentication.md) | API key vs v4 bearer token, the three-step user login flow, session IDs, v4 token conversion, guest sessions, secret handling | 472 |
| [images-and-configuration](./images-and-configuration.md) | Building an image URL, size buckets per image type, caching `/configuration`, `include_image_language`, picking the best image | 428 |
| [localization](./localization.md) | The `language` and `region` parameters, fallback behaviour, translation endpoints, alternative titles, region-specific certifications | 388 |
| [append-to-response](./append-to-response.md) | The `append_to_response` parameter, valid sub-requests per parent, the 20-item limit, the season/episode shorthand | 400 |
| [movies](./movies.md) | Every movie endpoint, the details response shape, credits, images, videos, external IDs, release dates, recommendations vs similar | 499 |
| [tv-series](./tv-series.md) | Every TV series endpoint, `credits` vs `aggregate_credits`, episode groups, content ratings, the series details shape | 506 |
| [tv-seasons-and-episodes](./tv-seasons-and-episodes.md) | The season and episode URL hierarchy, ordinals vs IDs, season 0 specials, stills, guest stars, alternate orderings | 463 |
| [people-and-credits](./people-and-credits.md) | Person details, gender codes, movie/TV/combined credits, resolving a `credit_id`, tagged images, filmography patterns | 504 |
| [search-and-find](./search-and-find.md) | The Search vs Discover vs Find decision, all 7 search endpoints, `search/multi`, external-ID lookup, the search-then-details workflow | 497 |
| [discover](./discover.md) | The complete filter reference for both Discover endpoints, AND/OR/NOT syntax, `.gte`/`.lte` ranges, every `sort_by` value, worked recipes | 518 |
| [trending-and-popular](./trending-and-popular.md) | The popularity model, trending time windows, every curated list, and the Discover equivalent of each | 407 |
| [user-account-and-ratings](./user-account-and-ratings.md) | Account details, favorites, watchlist, posting and deleting ratings, account states, guest-session ratings, the write envelope | 500 |
| [lists](./lists.md) | The v3 vs v4 lists decision, the full v3 list lifecycle, list membership, destructive operations | 444 |
| [entities](./entities.md) | Collections, companies, networks, keywords, genres, certifications, reviews, and the name-to-ID lookup pattern | 499 |
| [watch-providers](./watch-providers.md) | The JustWatch attribution rules, provider lists, per-title availability, `display_priority`, the Discover provider filters | 437 |
| [changes-and-exports](./changes-and-exports.md) | Daily ID exports, the change lists, per-item change logs, and a complete local-mirror sync architecture | 450 |

## Where to Start

- Build your first request: [getting-started](./getting-started.md), then [authentication](./authentication.md).
- Look something up by name: [search-and-find](./search-and-find.md).
- Build a filtered browse page: [discover](./discover.md).
- Cut your request count: [append-to-response](./append-to-response.md).
- Show a poster: [images-and-configuration](./images-and-configuration.md).
- Mirror TMDB locally: [changes-and-exports](./changes-and-exports.md).

## How to Use

Reference an individual skill in your project's CLAUDE.md:

    @~/.claude/skills/tmdb/discover.md

Or reference this index to see all available skills:

    @~/.claude/skills/tmdb/index.md

## Coverage

- Documentation pages read: 177 (20 guides, 157 API reference)
- Skill files created: 17
- Total lines: 7893
- Pages failed: 0

Every page was read from its official `.md` source, which embeds the full OpenAPI 3.1 definition for each endpoint.

## Known Documentation Defects

The agents found these problems in the source documentation. Each skill file records the correct behaviour.

- Two reference pages carry swapped content: `alternative-names-copy` documents the network **images** endpoint, and `details-copy` documents the network **alternative names** endpoint.
- `lists-copy` is the `/tv/{series_id}/lists` endpoint, not a list-management endpoint.
- The `tv-episode-changes-by-id` prose describes `start_date` and `end_date`, but its OpenAPI block lists only `episode_id`.
- The `account_states` examples use `id: 550`, which is a movie ID, on TV endpoints.
- The image-languages guide shows both `en,null` and `en-US,null`, but states that regional variants do not work for images. Use `en,null`.
- The guest-session scope differs between the guide and the reference page. Plan for ratings only.
- `movie-recommendations` embeds an empty response example.
- The episode-group `type` integers have no published legend.
