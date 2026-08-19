# Letterboxd API: Films, Collections and Contributors
Based on Letterboxd API v0 documentation.

## Scope

This file covers film discovery, single film lookups, film reference data, film collections, and contributors (directors, cast, crew and studios). All endpoints start with `https://api.letterboxd.com/api/v0/`.

Read `overview.md` first for the authentication and cursor rules. Read `me.md` for the modern write endpoints. Read `search.md` for text search.

## Deprecation status – read this first

Letterboxd moved films into a wider "production" model. A production is a `Film`, a `Show`, a `Season` or an `Episode` (see `ProductionType`). Almost every single-film endpoint now points to a `/production/{id}` equivalent. The old paths still work and the docs still describe them in full.

| Deprecated path | Replacement |
|---|---|
| `GET /film/{id}` | `GET /production/{id}` |
| `GET /film/{id}/availability` | `GET /production/{id}/availability` |
| `GET /film/{id}/statistics` | `GET /production/{id}/statistics` |
| `GET /film/{id}/me` | `GET /production/{id}/me` |
| `GET /film/{id}/members` | `GET /production/{id}/members` |
| `GET /film/{id}/friends` | `GET /production/{id}/friends` |
| `GET /film/{id}/member/{member}` | `GET /production/{id}/member/{member}` |
| `PATCH /film/{id}/me` | `PATCH /me/watch/{id}`, `/me/like/{id}`, `/me/rate/{id}`, `/me/watchlist/{id}` |
| `POST /film/{id}/report` | `POST /production/{id}/report` |
| `GET /films/autocomplete` | `GET /search?input={input}&searchMethod=Autocomplete&include=FilmSearchItem` |

`GET /films`, `GET /film-collection/{id}`, `GET /film-collections` and all `/contributor/...` endpoints are NOT deprecated. Build on those.

The `/production/...` endpoints are not described in this documentation set. The parameter and response shapes below still apply, because the replacements copy them.

## Endpoint quick reference

| Endpoint | Scopes | Status | Returns |
|---|---|---|---|
| `GET /films` | oauth2 (optional) | current | `FilmsResponse` |
| `GET /films/genres` | oauth2 (optional) | current | `GenresResponse` |
| `GET /films/languages` | oauth2 (optional) | current | `LanguagesResponse` |
| `GET /films/countries` | oauth2 (optional) | current | `CountriesResponse` |
| `GET /films/film-services` | oauth2 (optional) | current | `FilmServicesResponse` |
| `GET /films/availability-types` | none | current | `AvailabilityTypesResponse` |
| `GET /films/autocomplete` | oauth2 (optional) | DEPRECATED | `FilmsAutocompleteResponse` |
| `GET /film/{id}` | oauth2 (optional) | DEPRECATED | `Film` |
| `GET /film/{id}/availability` | oauth2 (optional) | **FIRST PARTY**, DEPRECATED | `ProductionAvailabilityResponse` |
| `GET /film/{id}/statistics` | oauth2 (optional) | DEPRECATED | `FilmStatistics` |
| `GET /film/{id}/me` | `user` | DEPRECATED | `ProductionRelationship` |
| `GET /film/{id}/members` | oauth2 (optional) | DEPRECATED | `MemberFilmRelationshipsResponse` |
| `GET /film/{id}/friends` | `user` | DEPRECATED | `FriendFilmRelationshipsResponse` |
| `GET /film/{id}/member/{member}` | oauth2 (optional) | DEPRECATED | `MemberFilmRelationship` |
| `PATCH /film/{id}/me` | `user`, `content:modify` | DEPRECATED | `FilmRelationshipUpdateResponse` |
| `POST /film/{id}/report` | `user`, `content:modify` | DEPRECATED | `204 No Content` |
| `GET /film-collection/{id}` | oauth2 (optional) | current | `FilmCollection` |
| `GET /film-collections` | oauth2 (optional) | current | `FilmCollectionsResponse` |
| `GET /contributor/{id}` | oauth2 (optional) | current | `Contributor` |
| `GET /contributor/{id}/contributions` | oauth2 (optional) | current | `FilmContributionsResponse` |
| `GET /contributor/{id}/hunt-items` | oauth2 (optional) | current | `HuntItems` (**FIRST PARTY** data) |
| `GET /contributor/{id}/me` | oauth2, member token | current | `ContributorRelationship` |

"oauth2 (optional)" means the endpoint accepts an unauthenticated token. A member token adds the member relationship data to the response.

## GET /films – the discovery endpoint

`GET /films` is the main film query endpoint. It applies filters, applies a sort order, and returns one page of `FilmSummary` objects plus a `next` cursor. Almost every "find films that ..." task uses this endpoint.

The response also carries the film relationships for the signed-in member and for the member in the `member` parameter.

### Pagination and page size

| Parameter | Type | Notes |
|---|---|---|
| `cursor` | string | The pagination cursor. Send the `next` value from the previous response. |
| `perPage` | int32 | Default `20`, maximum `100`. |
| `countItems` | boolean | Set to `true` to fill `itemCount` with the total match count, not the page count. |
| `excludeMemberFilmRelationships` | boolean | Set to `true` to drop the `relationships` array. Use it to make the response small. |

Do not build page numbers. Follow the `next` cursor until the response omits it. The API stops all cursor pagination at 100,000 objects.

### Identity and content filters

| Parameter | Type | Notes |
|---|---|---|
| `filmId` | string[] | Up to 100 IDs. Accepts a LID, a TMDB ID with the `tmdb:` prefix, or an IMDB ID with the `imdb:` prefix. Repeat the parameter per value: `filmId=b8wK&filmId=imdb:tt1396484`. |
| `genre` | string | The LID of one genre. Get the LID from `/films/genres`. |
| `includeGenre` | string[] | Up to 100 genre LIDs. A film must match ALL of them. |
| `excludeGenre` | string[] | Up to 100 genre LIDs. A film must match NONE of them. |
| `country` | string | The ISO 3166-1 code of the production country. |
| `language` | string | The ISO 639-1 code of a spoken language. |
| `decade` | int32 | The first year of the decade. The value must end in `0`, for example `1980`. |
| `year` | int32 | One release year, for example `1994`. |

Use `filmId` to fetch many known films in one request. Do not call `GET /film/{id}` in a loop.

### First-party taxonomy filters

Third-party clients must not send these four parameters. Letterboxd restricts them for licence reasons.

| Parameter | Type | Notes |
|---|---|---|
| `similarTo` | string | **FIRST PARTY** The LID of a film. Returns films similar to it. |
| `theme` | string | **FIRST PARTY** A theme code. |
| `minigenre` | string | **FIRST PARTY** A minigenre code. |
| `nanogenre` | string | **FIRST PARTY** A nanogenre code. |

Each of these four makes `sort=BestMatch` valid. Without one of them, `BestMatch` fails.

### Availability filters

| Parameter | Type | Notes |
|---|---|---|
| `service` | string | The ID of one service. Get the ID from `/films/film-services`. |
| `availabilityType` | string[] | Availability type keys. Get the keys from `/films/availability-types`. |
| `exclusive` | boolean | `true` limits results to films on one service only. |
| `unavailable` | boolean | `true` limits results to films on no service. |
| `includeOwned` | boolean | `true` also returns films that the member owns. |
| `negate` | boolean | `true` inverts the current service filters. |

The service list changes with the member. Some services, and the "My Services" options, need a paying member. An unauthenticated token gets a shorter list.

### Member relationship filters

| Parameter | Type | Notes |
|---|---|---|
| `member` | string | The LID of the member to filter on, or to sort by. |
| `memberRelationship` | `FilmMemberRelationship` | Needs `member`. Default `Watched`. |
| `includeFriends` | `IncludeFriends` | Needs `member`. `None` (default), `Only`, `All`. |
| `memberMinRating` | number | `0.5` to `5.0` in steps of `0.5`. |
| `memberMaxRating` | number | `0.5` to `5.0` in steps of `0.5`. |

`FilmMemberRelationship` values: `Ignore`, `Watched`, `NotWatched`, `Liked`, `NotLiked`, `Rated`, `NotRated`, `InWatchlist`, `NotInWatchlist`, `Favorited`.

Use `memberRelationship=Ignore` when you want the member only for a `sort=MemberRating*` order. `Ignore` removes the relationship filter but keeps the member context.

### Tag filters

| Parameter | Type | Notes |
|---|---|---|
| `tagCode` | string | One tag code. |
| `includeTags` | string[] | Tag codes. A film must have ALL of them. |
| `excludeTags` | string[] | Tag codes. A film must have NONE of them. |
| `tagger` | string | The member LID that owns the tags. Needs `tagCode` or `includeTags`. |
| `includeTaggerFriends` | `IncludeFriends` | Needs `tagger`. `None` (default), `Only`, `All`. |
| `tag` | string | **DEPRECATED** Use `tagCode`. |

### The `where` parameter

`where` accepts one or more `FilmWhereClause` values. Repeat the parameter for each value. The API combines the values with AND: `where=Watched&where=Released`.

| Group | Values (each also has a `Not` form) |
|---|---|
| Release and format | `Released`, `FeatureLength` |
| Watch state | `Watched`, `WatchedFromWatchlist` (no `Not` form), `Rewatched`, `InWatchlist` |
| Diary and text | `Logged`, `Reviewed` |
| Opinion | `Rated`, `Liked` |
| Ownership and notes | `Owned`, `AddedPrivateNote` |
| Custom art | `Customised`, `CustomisedBackdrop` |
| Content type | `Fiction`, `Film`, `TV` (no `Not` forms) |

The relationship clauses apply to the signed-in member, not to the `member` parameter. Use `member` plus `memberRelationship` to filter on a different member. The documentation does not say this in words, so test both against your token.

### Sort orders

`sort` defaults to `FilmPopularity`. That value measures all-time activity for the film.

| Sort value | Condition |
|---|---|
| `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` | none |
| `FilmPopularityWithFriends` and the three period variants | signed-in member only |
| `FilmName` | none |
| `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst` | none |
| `DateLatestFirst`, `DateEarliestFirst` | needs `member` with `memberRelationship` of `Watched`, `Liked`, `Rated` or `InWatchlist` |
| `AverageRatingHighToLow`, `AverageRatingLowToHigh` | none |
| `RatingHighToLow`, `RatingLowToHigh` | **DEPRECATED** Use the `AverageRating*` values. |
| `MemberRatingHighToLow`, `MemberRatingLowToHigh` | needs `member` and `includeFriends=None` |
| `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh` | signed-in member only |
| `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked` | signed-in member only |
| `FilmDurationShortestFirst`, `FilmDurationLongestFirst` | none |
| `BestMatch` | needs `similarTo`, `theme`, `minigenre` or `nanogenre` |

`DateLatestFirst` sorts by the date of the relationship, not by the release date. It answers "what did this member watch most recently".

### Worked examples

```http
# 1. All films a member has not watched, best rated first.
GET /films?member={memberLID}&memberRelationship=NotWatched&sort=AverageRatingHighToLow&perPage=100

# 2. The highest rated horror films of the 1980s.
#    Resolve {horrorLID} once from GET /films/genres and keep it in the cache.
GET /films?genre={horrorLID}&decade=1980&sort=AverageRatingHighToLow&perPage=50&countItems=true

# 3. The member's watchlist, most recently added first.
GET /films?member={memberLID}&memberRelationship=InWatchlist&sort=DateLatestFirst

# 4. Films on the member's watchlist that one service carries now.
#    Take {streamKey} from GET /films/availability-types. Do not guess the key.
GET /films?member={memberLID}&memberRelationship=InWatchlist&service={serviceId}&availabilityType={streamKey}

# 5. Japanese-language films of 1994 that the signed-in member has not logged.
GET /films?language=ja&year=1994&where=NotLogged&where=Released&sort=FilmPopularity

# 6. The member's own ratings, high to low. Note memberRelationship=Ignore.
GET /films?member={memberLID}&memberRelationship=Ignore&includeFriends=None&sort=MemberRatingHighToLow

# 7. Documentaries the member rated 4.0 or higher.
GET /films?member={memberLID}&memberRelationship=Rated&includeGenre={documentaryLID}&memberMinRating=4.0

# 8. What the member and the member's friends watched, popular with friends first.
GET /films?member={memberLID}&memberRelationship=Watched&includeFriends=All&sort=FilmPopularityWithFriends

# 9. Fetch a batch of known films. One request, not three.
GET /films?filmId=b8wK&filmId=tmdb:11&filmId=imdb:tt1396484&excludeMemberFilmRelationships=true

# 10. Crime films that are not thrillers, longest first.
GET /films?includeGenre={crimeLID}&excludeGenre={thrillerLID}&sort=FilmDurationLongestFirst

# 11. The same request as number 2, in full.
curl -s -H "Authorization: Bearer $LB_TOKEN" \
  "https://api.letterboxd.com/api/v0/films?genre=$HORROR_LID&decade=1980&sort=AverageRatingHighToLow&perPage=50"
```

### The response

`FilmsResponse` holds `next`, `items` (an array of `FilmSummary`) and `itemCount`. `itemCount` stays empty unless you send `countItems=true`.

Each `FilmSummary` carries a `relationships` array of `MemberFilmRelationship`. That array holds the signed-in member and the `member` parameter member. Send `excludeMemberFilmRelationships=true` when you do not need it, because it makes each page much smaller.

A `400` reports a bad parameter combination, for example a sort order without its required parameter. The specification also lists `403` and `404`, because `/films` shares an error contract with the list endpoints.

## GET /film/{id} – Film against FilmSummary

**DEPRECATED.** Use `GET /production/{id}`.

| Parameter | In | Notes |
|---|---|---|
| `id` | path | The film LID, or a TMDB ID with the `tmdb:` prefix, for example `tmdb:11`. |
| `member` | query | The LID of a member. The response then honors that member's custom poster settings. |

`Film` extends `Production`. `FilmSummary` is the smaller object that every list endpoint returns.

| Data | Where |
|---|---|
| `id`, `name`, `fullDisplayName`, `sortingName`, `link`, `releaseYear`, `runTime`, `rating`, `adult`, `poster`, `genres`, `topFilmsPosition`, `filmCollectionId` | both |
| `directors`, `contextualPoster`, `relationships` | `FilmSummary` only |
| `releaseDate`, `description`, `tagline`, `trailer`, `backdrop`, `backdropFocalPoint`, `primaryLanguage`, `inVideoStore`, `recentStories` | `Film` only |
| `countries`, `languages`, `productionLanguage`, `releases`, `themes`, `minigenres`, `nanogenres`, `similarProductions` | `Film` only, **FIRST PARTY** |
| `originalName`, `alternativeNames`, `posterPickerUrl`, `backdropPickerUrl` | both, **FIRST PARTY** |

Plan the round trips with this table. A poster grid needs `FilmSummary` only, so one `/films` call is enough. A film detail page needs `description`, `tagline`, `trailer` and `backdrop`, so it needs `GET /film/{id}`. Note that `FilmSummary` gives `directors` but the full `Film` does not, so a detail page still needs one `/films?filmId=` call or one contributions call.

Do not call `GET /film/{id}` in a loop over a result page. Use `GET /films?filmId=...` with up to 100 IDs instead.

`Film.contributions` is deprecated. Use `GET /contributor/{id}/contributions`, or the production contributions endpoint, for cast and crew. `trailer` is a `FilmTrailer`, and `FilmTrailerType` has one value only: `youtube`.

## GET /films/autocomplete

**DEPRECATED.** Use `GET /search?input={input}&searchMethod=Autocomplete&include=FilmSearchItem`.

| Parameter | Notes |
|---|---|
| `input` | Required. A word, a partial word or a phrase. |
| `perPage` | Default `20`, maximum `100`. |
| `adult` | Default `false`. |
| `excludeMemberFilmRelationships` | Set to `true` for a smaller response. |

The endpoint returns `FilmsAutocompleteResponse` with up to 100 `FilmSummary` items in relevance order. It has no cursor.

Use this endpoint, or the `Autocomplete` search method, for a search box that suggests titles while the user types. Use `/search` for a full search page, because `/search` also returns members, lists, reviews, tags and stories. New code must use `/search`.

## Reference-data endpoints

These five endpoints supply the valid identifiers for the `/films` filters. Fetch them at start-up and keep them in a cache. Do not write the identifiers into the source code, because Letterboxd can change them.

| Endpoint | Item shape | Order | Feeds |
|---|---|---|---|
| `GET /films/genres` | `Genre { id, name }` | alphabetical | `genre`, `includeGenre`, `excludeGenre` |
| `GET /films/languages` | `Language { code, name }` | alphabetical | `language` (ISO 639-1) |
| `GET /films/countries` | `Country { code, name, flagUrl }` | alphabetical | `country` (ISO 3166-1) |
| `GET /films/film-services` | `Service { id, name, icon, largeIcon }` | logical | `service` |
| `GET /films/availability-types` | `AvailabilityType { key, label }` | alphabetical | `availabilityType` |

The genre `id` is a LID, not the genre name. `/films?genre=horror` fails. Map the name to the LID with the `/films/genres` response. `/films/film-services` needs the member token, because the result changes with the member's subscription and region, so refresh that cache per member. `/films/availability-types` needs no authentication.

## GET /film/{id}/availability

**FIRST PARTY. DEPRECATED.** Use `GET /production/{id}/availability`.

Third-party clients cannot call this endpoint, because Letterboxd restricts the streaming data by licence. A third-party client can still filter on availability through `/films?service=...`, but it cannot read the per-film store list. The response is `ProductionAvailabilityResponse` with an `items` array of `ProductionAvailability`, in order of preference:

| Field | Notes |
|---|---|
| `displayName` | The service name. Use it. The old `service` enum is deprecated. |
| `serviceCode`, `id` | The service code, and the production ID on that service. |
| `country` | The regional store, as an ISO 3166-1 alpha-3 code. Not every service supports every country. |
| `types` | One or more of `rent`, `cinema`, `buy`, `stream`. |
| `url`, `icon`, `largeIcon` | The URL of the film on that service, and the service artwork. |
| `classification`, `classificationAdvisoryText` | The age rating and its advisory text. |
| `inMemberLibrary` | `true` if the item is in the member's library. |

The API assumes the USA store when the member has set no preferred store for a service.

## GET /film/{id}/statistics

**DEPRECATED.** Use `GET /production/{id}/statistics`.

| Parameter | Notes |
|---|---|
| `id` | path. The film LID. |
| `member` | query. Return statistics for the members that this member follows. |

`FilmStatistics` holds `film` (a `FilmIdentifier`), `rating` (the weighted average from `0.5` to `5.0`), `counts` and `ratingsHistogram`. The `rating` field stays empty until the film has enough ratings, so test for it before you print it. `counts` holds `watches`, `likes`, `ratings`, `fans`, `lists` and `reviews`, and `fans` counts the members with the film in their four favorites.

Each `RatingsHistogramBar` has three fields. They are `rating` (the increment from `0.5` to `5.0`), `count` (the number of ratings there) and `normalizedWeight` (`0.0` to `1.0`). Draw the histogram with `normalizedWeight` as the bar height. The tallest bar always returns `1.0`, unless the film has no ratings. Do not divide `count` by the maximum yourself.

## Member relationships to a film

| Endpoint | Answers |
|---|---|
| `GET /film/{id}/me` | What is my relationship with this film? |
| `GET /film/{id}/member/{member}` | What is one named member's relationship with this film? |
| `GET /film/{id}/members` | Which members have this relationship with this film? |
| `GET /film/{id}/friends` | Which of my friends watched this film? |

`GET /film/{id}/me` needs the `user` scope and returns a `ProductionRelationship`. Its `type` field holds a `ProductionType` (`Film`, `Show`, `Season` or `Episode`), and `productionId` and `memberId` hold the two LIDs. The object also holds `watched`, `whenWatched`, `liked`, `whenLiked`, `favorited`, `owned`, `inWatchlist`, `whenAddedToWatchlist`, `whenCompletedInWatchlist`, `rating`, `derivedRating`, `rewatched`, `privacyPolicy`, and the LID arrays `reviews`, `diaryEntries` and `drafts`. It also carries `privateNote`, `customPoster` and `backdrop`, but only for your own relationship.

`GET /film/{id}/member/{member}` returns a `MemberFilmRelationship`, a schema that is deprecated in favour of the identical `MemberProductionRelationship`. `GET /film/{id}/members` is cursored and returns `MemberFilmRelationshipsResponse`.

| Parameter | Notes |
|---|---|
| `cursor`, `perPage` | Default `20`, maximum `100`. |
| `filmRelationship` | A `FilmMemberRelationship`. Default `Watched`. |
| `member` + `memberRelationship` | Limit the result to members that follow, or are followed by, that member. |
| `sort` | A `MembersSort`. Default `Date`. |

`sort=Date` changes meaning with `filmRelationship`. With `Watched` it puts the most recent watchers first. With `Liked` it puts the most recent likes first. With `InWatchlist` it puts the most recent watchlist additions first.

`GET /film/{id}/friends` needs the `user` scope. It returns `FriendFilmRelationshipsResponse`: a cursored list of `MemberFilmViewingRelationship` items (each with the member, the relationship and the log entry), plus `watchCount` and `watchListCount`.

Warning: `watchCount` and `watchListCount` return `-1` when the member has too many friends to count. Test for `-1` before you show the number.

## PATCH /film/{id}/me – write the member state

**DEPRECATED.** Use the four single-purpose endpoints in `me.md`: `PATCH /me/watch/{id}`, `PATCH /me/like/{id}`, `PATCH /me/rate/{id}` and `PATCH /me/watchlist/{id}`. Prefer them in new code, because each one takes one field. Scopes: `user` and `content:modify`.

The body is a `FilmRelationshipUpdateRequest`. Send only the fields that change.

```json
{ "watched": true, "liked": true, "rating": 4.5, "inWatchlist": false }
```

| Field | Rules |
|---|---|
| `watched` | `true` also removes the film from the watchlist. |
| `liked` | A simple boolean. |
| `rating` | `0.5` to `5.0` in steps of `0.5`, or `null` to remove the rating. A rating forces `watched` to `true`. |
| `inWatchlist` | `true` adds the film. `false` removes it. |

The API ignores a field that breaks a business rule. It does not fail the request. Always read the `messages` array in the `FilmRelationshipUpdateResponse`, and show each message to the user. The message codes are `InvalidRatingValue` and `UnableToRemoveWatch`. You cannot set `watched` to `false` while a rating, a review or a diary entry exists for that member. Delete that activity first.

The response holds `data` (the new `ProductionRelationship`) and `messages`. Use `data` to refresh the interface. Do not send a second GET. Send the header `X-HTTP-Method-Override: PATCH` on a POST if your client cannot send PATCH.

## POST /film/{id}/report

**DEPRECATED.** Use `POST /production/{id}/report`. Scopes: `user` and `content:modify`.

The body is a `ReportProductionRequest`:

```json
{ "reason": "Duplicate", "message": "This is the same film as b8wK." }
```

`reason` accepts `Duplicate`, `NotAFilm`, `Image` or `Other`. The `message` field is required for all four reasons. A success returns `204` with no body.

## Film collections

A film collection is Letterboxd's group for a series, for example a trilogy. `FilmSummary.filmCollectionId` gives the LID of the collection that holds the film. Neither endpoint is deprecated.

### GET /film-collection/{id}

The response is a `FilmCollection` with `id`, `name`, `filmCount`, `films` (an array of `FilmSummary`) and `links`. The endpoint has no cursor and no `perPage`, so it returns the whole collection. It accepts the same filter set as `/films`. That set holds `filmId`, `genre`, `includeGenre`, `excludeGenre`, `country`, `language`, `decade`, `year`, the six availability parameters, `where`, the four member parameters and the tag parameters. It also accepts the **FIRST PARTY** `similarTo`, `theme`, `minigenre` and `nanogenre`.

The `sort` enum is smaller than the `/films` one. It drops `DateLatestFirst`, `DateEarliestFirst`, `BestMatch`, `AuthenticatedMemberBasedOnLiked` and `AuthenticatedMemberRelatedToLiked`. It keeps `FilmName`, the `ReleaseDate*` pair, the `AverageRating*` pair, the `MemberRating*` pair, the `AuthenticatedMemberRating*` pair, the `FilmDuration*` pair and the `FilmPopularity*` family.

```http
# Show one collection in release order, with the member's relationship data.
GET /film-collection/{collectionLID}?sort=ReleaseDateEarliestFirst&member={memberLID}&memberRelationship=Ignore
```

### GET /film-collections

A cursored window over all film collections. It returns `FilmCollectionsResponse` with `next`, `items` and `itemCount`.

| Parameter | Notes |
|---|---|
| `cursor`, `perPage` | Default `20`, maximum `100`. |
| `genre`, `includeGenre`, `excludeGenre` | Match a collection that contains such films. |
| `decade`, `year` | Match a collection with a film from that decade or year. |
| `upcoming` | `true` limits the result to collections with an upcoming film. |
| `minFilmCount` | The smallest collection size to return. |
| `previewHowMany` | The number of preview films per collection. Keep it low, for example `5`. |
| `countItems` | `true` fills `itemCount`. |
| `sort` | Default `FilmCollectionPopularity`. |

The `sort` values are `FilmCollectionName`, `FilmCollectionSizeLargestFirst`, `FilmCollectionSizeSmallestFirst`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `FilmCollectionPopularity`, `FilmCollectionPopularityThisWeek`, `FilmCollectionPopularityThisMonth` and `FilmCollectionPopularityThisYear`.

```http
# Popular series with at least three films, and four preview posters each.
GET /film-collections?minFilmCount=3&previewHowMany=4&sort=FilmCollectionPopularityThisMonth
```

Always send `previewHowMany`. Without it each collection returns its full `films` array, and a page of 20 collections becomes very large.

## Contributors

A contributor is a director, an actor, a crew member or a studio.

### GET /contributor/{id}

`id` accepts a contributor LID or a TMDB ID with the `tmdb:` prefix, for example `tmdb:3`.

The response is a `Contributor` with `id`, `name`, `tmdbid`, `bio`, `poster` (16:9), `links` and `statistics`. `statistics.contributions` is an array of `ContributionStatistics`, and each entry gives a `type` and a `filmCount`.

Use `statistics.contributions` to build the section list on a contributor page. It tells you which contribution types exist, and how many films each type has, before you fetch any film. The `contributorPosterPickerUrl` field is **FIRST PARTY**.

### GET /contributor/{id}/contributions

A cursored window over the films for a contributor. `id` must be a LID here. The response is `FilmContributionsResponse`.

| Field | Notes |
|---|---|
| `items` | An array of `FilmContribution`: `type`, `film` (`FilmSummary`), `characterName`, `containsSpoilers`. |
| `metadata` | An array of `FilmContributorMetadata`: the `type`, plus `totalFilmCount` and `filteredFilmCount`. |
| `relationships` | An array of `FilmContributorMemberRelationship`: the member, and the watch and like counts per contribution type. |
| `next`, `itemCount` | The cursor and the count. |

`characterName` appears only when `type` is `Actor`. `containsSpoilers` is `true` when the role itself gives away the plot. Hide such a role behind a spoiler control.

The endpoint accepts the whole `/films` filter set, plus `type` (one `ContributionType`, which limits the result to that role) and `excludeMemberFilmRelationships`. The `sort` enum adds `Billing`, which is the credit order for a cast list. It has no `Date*` values, no `BestMatch` and no `*WithFriends` values. It keeps `FilmName`, the `ReleaseDate*` pair, the `AverageRating*` pair, the deprecated `Rating*` pair, the `MemberRating*` pair, the `AuthenticatedMemberRating*` pair, the `FilmDuration*` pair and `FilmPopularity*`. The default is `FilmPopularity`.

```http
# The full filmography as a director, newest first.
GET /contributor/{contributorLID}/contributions?type=Director&sort=ReleaseDateLatestFirst

# The cast credits in billing order.
GET /contributor/{contributorLID}/contributions?type=Actor&sort=Billing&perPage=100

# Which films by this director has the member not seen yet?
GET /contributor/{contributorLID}/contributions?type=Director&member={memberLID}&memberRelationship=NotWatched
```

### ContributionType

| Group | Values |
|---|---|
| Direction | `Director`, `CoDirector`, `AssistantDirector`, `AdditionalDirecting` |
| Cast | `Actor` (the only type with `characterName`), `Casting` |
| Writing | `Writer`, `OriginalWriter`, `Story`, `Creator` |
| Production | `Producer`, `ExecutiveProducer`, `Studio` |
| Camera and light | `Cinematography`, `CameraOperator`, `AdditionalPhotography`, `Lighting` |
| Art | `ProductionDesign`, `ArtDirection`, `SetDecoration`, `TitleDesign` |
| Post and effects | `Editor`, `SpecialEffects`, `VisualEffects` |
| Music and sound | `Composer`, `Songs`, `Sound` |
| Performance craft | `Stunts`, `Choreography` |
| Wardrobe | `Costumes`, `MakeUp`, `Hairstyling` |

`Studio` is a contributor type. A studio therefore has a `/contributor/{id}` page like a person.

### GET /contributor/{id}/hunt-items

Returns `HuntItems` with a `huntItems` array of `TreasureHuntItem`. Each item has `locationHint`, `name`, `image`, `found`, `itemId`, `nonce`, `token` and `actionUrl`. The `huntItems` field is marked **FIRST PARTY**, so expect an empty array on a third-party token. The `nonce` and `token` values feed `POST /me/collect-item`.

### GET /contributor/{id}/me

Returns a `ContributorRelationship`. The object holds one field: `customPoster`, the member's own custom poster for the contributor, or `null`. Call it only when you must show a custom contributor poster.

## Pitfalls

1. **The 100,000-object cap.** Cursor pagination stops at 100,000 objects. Letterboxd sets the cap to stop a full copy of the dataset. Narrow the filters when you need deep data. Do not write a program that reads every film.
2. **First-party parameters and endpoints are closed.** The parameters `similarTo`, `theme`, `minigenre` and `nanogenre` are first party, and so is `GET /film/{id}/availability`. A third-party key cannot use them. First-party fields, such as `countries`, `languages`, `releases` and `themes`, stay empty on a third-party token. Do not treat an empty first-party field as a data fault.
3. **A genre needs a LID, a country and a language need a code.** `genre` takes an opaque LID from `/films/genres`. `country` takes an ISO 3166-1 code. `language` takes an ISO 639-1 code. `ProductionAvailability.country` uses ISO 3166-1 alpha-3, which is a different code set. Do not mix them.
4. **A LID is not a slug.** The URL slug `letterboxd.com/film/parasite-2019/` is not a LID. Make a HEAD request to the web page and read the `x-letterboxd-identifier` header, or read the path of the `boxd.it` share URL. Both give the LID.
5. **Summary against full schema.** A list endpoint returns `FilmSummary`. `FilmSummary` has no `description`, no `tagline`, no `trailer`, no `backdrop` and no `releaseDate`. Fetch the full `Film` only for a detail view.
6. **A sort order can fail the request.** A `MemberRating*` sort without `member`, or a `BestMatch` sort without a taxonomy filter, returns `400`. Validate the combination before you send it.
7. **`rating` can be absent.** `FilmSummary.rating` and `FilmStatistics.rating` appear only after the film gets enough ratings. Handle the empty value.
8. **`-1` means "not counted".** `watchCount` and `watchListCount` on the friends endpoint return `-1` for a member with many friends.
9. **The API does not report an ignored PATCH field.** A `PATCH /film/{id}/me` request returns `200` even when it applies nothing. Read `messages` every time.
10. **`memberRelationship` defaults to `Watched`.** A `member` parameter without `memberRelationship` limits the result to watched films, and gives no warning. Send `memberRelationship=Ignore` when you want the member only for the sort order.
11. **Deprecated paths still work, but plan the move.** Every `/film/{id}...` path has a `/production/{id}...` replacement. Keep the film path in one place in your client, so one change moves the whole application.
12. **Do not write reference data into the source code.** Genre LIDs, service IDs and availability-type keys come from the API. Cache the service list per member, because a paying member sees more services.

## Relationships

| File | Use it for |
|---|---|
| `overview.md` | The base URL, the LID concept, the authentication, the cursor rules and the 100,000-object cap. |
| `me.md` | `PATCH /me/watch/{id}`, `/me/like/{id}`, `/me/rate/{id}`, `/me/watchlist/{id}` – the modern replacements for `PATCH /film/{id}/me`. Also the tag endpoints behind `tagCode`, and `POST /me/collect-item` for hunt items. |
| `log-entries.md` | Diary entries and reviews. `ProductionRelationship.diaryEntries` and `.reviews` hold the LIDs that those endpoints take. |
| `search.md` | `GET /search`, the replacement for `/films/autocomplete`, and the `FilmSearchItem` and `ContributorSearchItem` types. |
| `schemas-entities.md` | The full field lists for `Film`, `FilmSummary`, `Production`, `FilmCollection`, `Contributor`, `FilmStatistics`, `RatingsHistogramBar` and `ProductionAvailability`. |
| `schemas-enums.md` | The complete value lists for `FilmWhereClause`, `FilmMemberRelationship`, `ContributionType`, `ProductionType`, `FilmTrailerType`, `IncludeFriends` and `MembersSort`. |
| `lists.md` | Lists of films. `FilmStatisticsCounts.lists` counts them. |
| `members.md` | Member profiles, friends and the member LIDs that the `member` parameter takes. |
