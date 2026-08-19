# Letterboxd API: Enum Reference
Based on Letterboxd API v0 documentation.

Every enum value is a literal string. Copy it exactly. The API compares enum values with case sensitivity. A wrong value returns HTTP 400 with an `ErrorResponse` body.

## How to send an enum value

| Situation | Format | Example |
|---|---|---|
| Single-value query parameter | `name=Value` | `?sort=FilmPopularity` |
| Array query parameter (exploded form style) | Repeat the key once per value | `?where=Watched&where=Released` |
| Enum in a JSON request or response body | A JSON string | `{"commentPolicy": "Friends"}` |

Never send a comma-separated list. The API uses exploded form style for every array parameter. All values use ASCII letters only, so no percent-encoding applies.

## Index: enum to endpoint and parameter

| Enum | Endpoint and parameter | Purpose |
|---|---|---|
| `AccountStatus` | Response field `accountStatus` on `Member`, `MemberAccount`, `MemberSummary` | Reports if the account is live or memorialized. |
| `ActivityFilter` | `GET /member/{id}/activity` → `include`, `exclude` | Selects the activity types that the feed returns. |
| `ActivityType` | Response field `type` on an activity item | Reports the type of a returned activity item. |
| `CommentPolicy` | `POST /lists`, `PATCH /list/{id}`, `PATCH /log-entry/{id}`, `PATCH /me` → `commentPolicy`; response field `commentPolicy` | Sets who can post a comment on the content. |
| `CommentsSort` | `GET /list/{id}/comments`, `GET /log-entry/{id}/comments`, `GET /story/{id}/comments` → `sort` | Orders a comment thread. |
| `CommentSubscriptionState` | Response field `subscriptionState` on `ListRelationship`, `ReviewRelationship`, `StoryRelationship` | Reports the notification state of the member for a thread. |
| `CommentThreadState` | Response field `commentThreadState` on the same three objects | Reports if the authenticated member can post a comment. |
| `CommentType` | Response field `type` on `Comment` | Reports the parent object type of a comment. |
| `ContributionType` | `GET /contributor/{id}/contributions` → `type`; `GET /search` → `contributionType`; response field `type` on `FilmContribution` | Names a cast or crew role. |
| `FeaturedContentType` | `GET /featured-content` → `include`; response field `type` | Selects the kind of editorial content. |
| `FilmMemberRelationship` | `GET /films`, `GET /list/{id}/entries`, `GET /member/{id}/watchlist`, `GET /contributor/{id}/contributions`, `GET /film-collection/{id}` → `memberRelationship`; `GET /members` and `GET /film/{id}/members` → `filmRelationship`; `GET /log-entries` → `filmMemberRelationship` | Filters by the link between a member and a film. |
| `FilmTrailerType` | Response field `type` on `FilmTrailer` | Names the trailer host. |
| `FilmWhereClause` | `GET /films`, `GET /list/{id}/entries`, `GET /member/{id}/watchlist`, `GET /contributor/{id}/contributions`, `GET /film-collection/{id}` → `where` | Filters a film list. |
| `IncludeFriends` | The same five film endpoints plus `GET /lists` and `GET /log-entries` → `includeFriends`, `includeTaggerFriends` | Extends a member filter to the friends of the member. |
| `ListMemberRelationship` | `GET /lists` → `memberRelationship`; `GET /members` → `listRelationship` | Filters by the link between a member and a list. |
| `ListWhereClause` | `GET /lists` → `where` | Filters a list of lists. |
| `LogEntryWhereClause` | `GET /log-entries` → `where` | Filters diary entries and reviews. |
| `MemberRelationships` | `GET /members`, `GET /film/{id}/members`, `GET /review/{id}/members` → `memberRelationship` | Filters by the follow link between two members. |
| `MembersSort` | The same three member endpoints → `sort` | Orders a member list. |
| `MemberStatus` | Response field `memberStatus` on `Member`, `MemberSummary` | Reports the account type, such as Pro or Patron. |
| `PosterMode` | `PATCH /me` → `posterMode`; response fields `posterMode`, `posterModeOptions` | Controls if the member sees custom posters. |
| `PrivacyPolicy` | `GET /log-entries` → `privacyPolicy`; `PATCH /log-entry/{id}` and `PATCH /me` → `privacyPolicy`; response field `privacyPolicy` | Sets or filters who can see the content. |
| `ProductionType` | Response field `type` on `ProductionRelationship` | Reports the production kind, such as a film or an episode. |
| `ReviewMemberRelationship` | `GET /log-entries` → `memberRelationship` | Filters by the link between a member and a review. |
| `SearchResultType` | `GET /search` → `include` | Limits a search to result types. |
| `SharePolicy` | `POST /lists`, `PATCH /list/{id}` → `sharePolicy`; response field `sharePolicy` | Sets who can access a list. |
| `StoryMemberRelationship` | `GET /stories` → `memberRelationship`; `GET /members` → `storyRelationship` | Filters by the link between a member and a story. |

First-party note: the source marks no individual enum value as first party. It marks whole parameters as first party. `sort=BestMatch` needs one of the first-party parameters `similarTo`, `theme`, `minigenre` or `nanogenre`, so a third-party client cannot use `BestMatch`.

# 1. Where-clause enums

`where` is always an array. Repeat the key to send more than one value.

| Endpoint | Combination rule | Source wording |
|---|---|---|
| `GET /films` → `where` | AND | "Specify one or more values to limit the list of films accordingly." |
| `GET /log-entries` → `where` | AND | "Specify one or more values to limit the returned log entries accordingly." |
| `GET /lists` → `where` | AND | Each value is described as a limit on the returned lists. |
| `GET /member/{id}/activity` → `where` | AND. The source states this rule. | "If multiple values are supplied, only activity matching all terms will be returned." |

The source states the AND rule only for the activity endpoint. The other endpoints use the same "limit ... accordingly" wording, so treat them as AND. The API gives no OR operator. For an OR result, send two requests and merge the responses in your client.

## 1.1 FilmWhereClause

Use with `GET /films`, `GET /list/{id}/entries`, `GET /member/{id}/watchlist`, `GET /contributor/{id}/contributions` and `GET /film-collection/{id}`. Each member-state value applies to the authenticated member. To apply it to another member, add `member` and `memberRelationship`.

| Group | Values | Meaning |
|---|---|---|
| Release status | `Released` / `NotReleased` | The film has, or has not, a release date in the past. |
| Content type | `Fiction` | Exclude documentaries. |
| Content type | `Film` | Exclude TV shows. |
| Content type | `TV` | Return TV shows only. |
| Length | `FeatureLength` / `NotFeatureLength` | The film is, or is not, feature length. |
| Watchlist | `InWatchlist` / `NotInWatchlist` | The film is, or is not, in the watchlist. |
| Watchlist | `WatchedFromWatchlist` | The member watched the film after they added it to the watchlist. |
| Watched | `Watched` / `NotWatched` | The member did, or did not, mark the film as watched. |
| Logged | `Logged` / `NotLogged` | The member has, or has not, a log entry for the film. |
| Logged | `Rewatched` / `NotRewatched` | The member did, or did not, mark a diary entry as a rewatch. |
| Review | `Reviewed` / `NotReviewed` | The member did, or did not, write a review. |
| Rating | `Rated` / `NotRated` | The member did, or did not, rate the film. Add `memberMinRating` and `memberMaxRating` for a range. |
| Like | `Liked` / `NotLiked` | The member did, or did not, like the film. |
| Ownership | `Owned` / `NotOwned` | The member does, or does not, own the film. |
| Custom art | `Customised` / `NotCustomised` | The member did, or did not, set a custom poster. Note the British spelling. |
| Custom art | `CustomisedBackdrop` / `NotCustomisedBackdrop` | The member did, or did not, set a custom backdrop. |
| Private note | `AddedPrivateNote` / `NotAddedPrivateNote` | The member did, or did not, add a private note. |

Warning: `FilmWhereClause` uses `Customised` with an "s". `ListWhereClause` uses `Customized` with a "z". Do not swap them.

Worked query. It returns released feature films that the member watched but did not rate, and it excludes documentaries. The four `where` values combine with AND.

```
/films?member=abc1&memberRelationship=Watched&includeFriends=None&where=Released&where=FeatureLength&where=Fiction&where=NotRated&sort=ReleaseDateLatestFirst&perPage=50
```

## 1.2 LogEntryWhereClause

Use with `GET /log-entries` → `where`. `Released`, `NotReleased`, `FeatureLength` and `NotFeatureLength` describe the film, not the log entry.

| Group | Values | Meaning |
|---|---|---|
| Entry kind | `HasDiaryDate` | Return only entries that appear in the diary of a member. |
| Entry kind | `HasReview` | Return only entries that contain a review. |
| Entry kind | `NoDrafts` | Exclude draft log entries. |
| Review content | `Clean` | Exclude reviews that contain profane language. |
| Review content | `NoSpoilers` | Exclude reviews that the owner marked as a spoiler. |
| Film release | `Released` / `NotReleased` | The film has, or has not, a release date in the past. |
| Film length | `FeatureLength` / `NotFeatureLength` | The film is, or is not, feature length. |
| Film type | `Fiction` | Exclude log entries of documentaries. |
| Film type | `Film` | Exclude log entries of TV shows. |
| Film type | `TV` | Return log entries of TV shows only. |
| Watchlist | `InWatchlist` / `NotInWatchlist` | The film is, or is not, in the watchlist of the authenticated member. |
| Watched | `Watched` / `NotWatched` | The authenticated member did, or did not, watch the film. |
| Logged | `Logged` / `NotLogged` | The member has, or has not, a log entry for the film. |
| Logged | `Rewatched` / `NotRewatched` | The member did, or did not, mark a rewatch. |
| Review | `Reviewed` / `NotReviewed` | The member did, or did not, review the film. |
| Rating | `Rated` / `NotRated` | The entry has, or has not, a rating. Add `minRating` and `maxRating` for a range. |
| Like | `Liked` / `NotLiked` | The member did, or did not, like the film. |
| Ownership | `Owned` / `NotOwned` | The member does, or does not, own the film. |
| Custom art | `Customised` / `NotCustomised` | The member did, or did not, set a custom poster. |
| Custom art | `CustomisedBackdrop` / `NotCustomisedBackdrop` | The member did, or did not, set a custom backdrop. |
| Private note | `AddedPrivateNote` / `NotAddedPrivateNote` | The member did, or did not, add a private note. |

To apply the member-state values to another member, add `member` and `filmMemberRelationship`.

Worked query. It returns popular reviews for one film and removes drafts, profanity and spoilers.

```
/log-entries?film=b8wK&where=HasReview&where=Clean&where=NoSpoilers&where=NoDrafts&sort=ReviewPopularityThisWeek&perPage=20
```

Implied values: `sort=ReviewPopularity*` implies `where=HasReview`. `sort=Date` implies `where=HasDiaryDate`. `memberRelationship=Liked` also implies `where=HasReview`.

Warning: you may combine `filter=NoDuplicateMembers` only with the `where` values `HasDiaryDate`, `HasReview`, `Clean` and `NoSpoilers`. Any other `where` value returns a 400.

## 1.3 ListWhereClause

Use with `GET /lists` → `where`.

| Group | Value | Meaning |
|---|---|---|
| Content | `Clean` | Return lists that contain no profane language. |
| Publication | `Published` | Return the public lists of the member. |
| Publication | `NotPublished` | Return the lists of the authenticated member that are not public. |
| Publication | `NotPublishedOrShared` | The source gives no description. Treat it as lists that are neither published nor shared. |
| Sharing | `SharedAnyone` | The source gives no description. Treat it as lists shared with anyone. |
| Sharing | `SharedFriends` | The source gives no description. Treat it as lists shared with friends. |
| Member link | `Owned` | The source gives no description. Treat it as lists that the member owns. |
| Custom art | `Customized` | The source gives no description. Treat it as lists with custom art. Note the American spelling. |

The API never returns the private lists of another member. `where=NotPublished` needs the token of the owner. A different token returns HTTP 403.

```
/lists?member=abc1&memberRelationship=Owner&includeFriends=None&where=Published&where=Clean&sort=WhenPublishedLatestFirst&perPage=20
```

# 2. Sort enums

## 2.1 Default sort per endpoint

| Endpoint | Default `sort` |
|---|---|
| `GET /films` | `FilmPopularity` |
| `GET /list/{id}/entries` | `ListRanking` |
| `GET /member/{id}/watchlist` | `Added` |
| `GET /contributor/{id}/contributions` | `FilmPopularity` |
| `GET /film-collection/{id}` | `FilmPopularity` |
| `GET /lists` | `Date` |
| `GET /log-entries` | `WhenAdded`. With `where=HasDiaryDate` the default is `Date`. |
| `GET /stories` | `WhenUpdatedLatestFirst` |
| `GET /members`, `GET /film/{id}/members`, `GET /review/{id}/members` | `Date` |
| The three comment endpoints | `Date` |

## 2.2 Film-list sort: complete value list per endpoint

Each endpoint accepts only its own list. Copy the row for the endpoint that you call.

| Endpoint | Complete `sort` values |
|---|---|
| `GET /films` | `FilmName`, `DateLatestFirst`, `DateEarliestFirst`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `RatingHighToLow`, `RatingLowToHigh`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst`, `BestMatch`, `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear`, `FilmPopularityWithFriends`, `FilmPopularityWithFriendsThisWeek`, `FilmPopularityWithFriendsThisMonth`, `FilmPopularityWithFriendsThisYear` |
| `GET /list/{id}/entries` | `ListRanking`, `WhenAddedToList`, `WhenAddedToListEarliestFirst`, `Shuffle`, `FilmName`, `OwnerRatingHighToLow`, `OwnerRatingLowToHigh`, `OwnerDiaryLatestFirst`, `OwnerDiaryEarliestFirst`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `AuthenticatedMemberDiaryLatestFirst`, `AuthenticatedMemberDiaryEarliestFirst`, `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `MemberDiaryLatestFirst`, `MemberDiaryEarliestFirst`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `RatingHighToLow`, `RatingLowToHigh`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst`, `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` |
| `GET /member/{id}/watchlist` | `Added`, `DateLatestFirst`, `DateEarliestFirst`, `Shuffle`, `FilmName`, `OwnerRatingHighToLow`, `OwnerRatingLowToHigh`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst`, `FilmPopularity`, `RatingHighToLow`, `RatingLowToHigh`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` |
| `GET /contributor/{id}/contributions` | `Billing`, `FilmName`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `RatingHighToLow`, `RatingLowToHigh`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst`, `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` |
| `GET /film-collection/{id}` | `FilmName`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst`, `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear`, `FilmPopularityWithFriends`, `FilmPopularityWithFriendsThisWeek`, `FilmPopularityWithFriendsThisMonth`, `FilmPopularityWithFriendsThisYear` |

Meanings and constraints:

| Value or family | Meaning | Constraint |
|---|---|---|
| `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` | Count of the activity that the film received, all time or over a period. | The three period values are DEPRECATED on `GET /list/{id}/entries` and `GET /member/{id}/watchlist`. The source states that they never worked there. |
| `FilmPopularityWithFriends`, plus the `ThisWeek`, `ThisMonth` and `ThisYear` variants | Popularity among the friends of the signed-in member. | Sign in as a member. |
| `FilmName` | Alphabetical by film title. | – |
| `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst` | By the release date of the film. | – |
| `FilmDurationShortestFirst`, `FilmDurationLongestFirst` | By the runtime of the film. | – |
| `AverageRatingHighToLow`, `AverageRatingLowToHigh` | By the average member rating. | – |
| `RatingHighToLow`, `RatingLowToHigh` | The old average rating sort. | DEPRECATED. Use the `AverageRating*` values. |
| `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh` | By the rating of the signed-in member. | Sign in as a member. |
| `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked` | A recommendation from the films that the signed-in member liked. | Sign in as a member. |
| `MemberRatingHighToLow`, `MemberRatingLowToHigh` | By the rating of the member in the `member` parameter. | Send `member` and `includeFriends=None`. |
| `OwnerRatingHighToLow`, `OwnerRatingLowToHigh` | By the rating of the list owner or the watchlist owner. | – |
| `OwnerDiaryLatestFirst`, `OwnerDiaryEarliestFirst` | By the diary date of the list owner. | – |
| `AuthenticatedMemberDiaryLatestFirst`, `AuthenticatedMemberDiaryEarliestFirst` | By the diary date of the signed-in member. | Sign in as a member. |
| `MemberDiaryLatestFirst`, `MemberDiaryEarliestFirst` | By the diary date of the member in the `member` parameter. | Send `member`. |
| `DateLatestFirst`, `DateEarliestFirst` | By the date of the member relationship event. | On `GET /films`, send `member` and a `memberRelationship` of `Watched`, `Liked`, `Rated` or `InWatchlist`. |
| `ListRanking` | The order that the list owner set. | – |
| `WhenAddedToList`, `WhenAddedToListEarliestFirst` | By the time that the film entered the list. | – |
| `Added` | Most recent watchlist addition first. | – |
| `Shuffle` | A random order. | – |
| `Billing` | The credit order of a contributor. | – |
| `BestMatch` | Relevance order for a similarity search. | Send `similarTo`, `theme`, `minigenre` or `nanogenre`. All four are first party. |

## 2.3 Lists sort (`GET /lists`)

| Values | Meaning |
|---|---|
| `Date` | Default. Lists created or updated most recently appear first. |
| `WhenLiked` | By the time of the like. |
| `WhenPublishedLatestFirst` / `WhenPublishedEarliestFirst` | By the publication time. |
| `WhenCreatedLatestFirst` / `WhenCreatedEarliestFirst` | By the creation time. |
| `WhenAccessedLatestFirst` / `WhenAccessedEarliestFirst` | By the time of the last view. |
| `ListName` | Alphabetical by list name. |
| `ListPopularity`, `ListPopularityThisWeek`, `ListPopularityThisMonth`, `ListPopularityThisYear` | List popularity, all time or over a period. |
| `ListPopularityWithFriends`, `ListPopularityWithFriendsThisWeek`, `ListPopularityWithFriendsThisMonth`, `ListPopularityWithFriendsThisYear` | Popularity among the friends of the signed-in member. Sign in as a member. |

`filter=NoDuplicateMembers` works only with `Date`, `WhenPublishedLatestFirst` and `WhenCreatedLatestFirst`.

## 2.4 Log entry sort (`GET /log-entries`)

| Values | Meaning |
|---|---|
| `WhenAdded` | Default. By the creation date of the log entry. |
| `Date` | By the diary date. Implies `where=HasDiaryDate`. |
| `DiaryCount` | By the number of diary entries. |
| `ReviewCount` | By the number of reviews. |
| `WhenLiked` | By the time of the like. |
| `EntryRatingHighToLow` / `EntryRatingLowToHigh` | By the rating on the log entry. |
| `RatingHighToLow` / `RatingLowToHigh` | DEPRECATED. Use the `EntryRating*` values. |
| `AuthenticatedMemberRatingHighToLow` / `AuthenticatedMemberRatingLowToHigh` | By the rating of the signed-in member. |
| `MemberRatingHighToLow` / `MemberRatingLowToHigh` | By the rating of the member in `member`. Send `includeFriends=None`. |
| `AverageRatingHighToLow` / `AverageRatingLowToHigh` | By the average film rating. |
| `ReleaseDateLatestFirst` / `ReleaseDateEarliestFirst` | By the release date of the film. |
| `FilmName` | Alphabetical by film title. |
| `FilmDurationShortestFirst` / `FilmDurationLongestFirst` | By the runtime of the film. |
| `ReviewPopularity`, `ReviewPopularityThisWeek`, `ReviewPopularityThisMonth`, `ReviewPopularityThisYear` | Reviews with more likes and comments first. Implies `where=HasReview`. |
| `ReviewPopularityWithFriends`, `ReviewPopularityWithFriendsThisWeek`, `ReviewPopularityWithFriendsThisMonth`, `ReviewPopularityWithFriendsThisYear` | The same measure among friends. Sign in as a member. |
| `FilmPopularity`, `FilmPopularityThisWeek`, `FilmPopularityThisMonth`, `FilmPopularityThisYear` | Reviews for films with more combined activity first. |
| `FilmPopularityWithFriends`, `FilmPopularityWithFriendsThisWeek`, `FilmPopularityWithFriendsThisMonth`, `FilmPopularityWithFriendsThisYear` | The same measure among friends. Sign in as a member. |

With a `film` parameter, only `WhenAdded`, `Date`, `EntryRating*` and `ReviewPopularity*` apply. Do not send `film` with `FilmName`, `ReleaseDate*`, `FilmDuration*` or any `FilmPopularity*` value.

## 2.5 Stories sort (`GET /stories`)

| Values | Meaning |
|---|---|
| `WhenUpdatedLatestFirst` / `WhenUpdatedEarliestFirst` | By the update time. The first value is the default. |
| `WhenPublishedLatestFirst` / `WhenPublishedEarliestFirst` | By the publication time. |
| `WhenCreatedLatestFirst` / `WhenCreatedEarliestFirst` | By the creation time. |
| `StoryTitle` | Alphabetical by story title. |
| `PinnedFirst` | Pinned stories first. |
| `WhenLiked` | By the time of the like. |

## 2.6 MembersSort

Default: `Date` on `GET /members`, `GET /film/{id}/members` and `GET /review/{id}/members`.

| Values | Meaning |
|---|---|
| `Date` | Context sensitive. Read the table below. |
| `Name` | Alphabetical by member name. |
| `MemberPopularity`, `MemberPopularityThisWeek`, `MemberPopularityThisMonth`, `MemberPopularityThisYear` | Member popularity, all time or over a period. |
| `MemberPopularityWithFriends`, `MemberPopularityWithFriendsThisWeek`, `MemberPopularityWithFriendsThisMonth`, `MemberPopularityWithFriendsThisYear` | Popularity among the friends of the member. Sign in as a member. |

The meaning of `Date` changes with the other parameters:

| Other parameters | Order that `Date` gives |
|---|---|
| `review=...` | Members who liked the review most recently appear first. |
| `list=...` | Members who liked the list most recently appear first. |
| `film=...` with `filmRelationship=Watched` | Members who watched the film most recently appear first. |
| `film=...` with `filmRelationship=Liked` | Members who liked the film most recently appear first. |
| `film=...` with `filmRelationship=InWatchlist` | Members who added the film to the watchlist most recently appear first. |
| `member=...` with `memberRelationship=IsFollowing` | Most recently followed members appear first. |
| `member=...` with `memberRelationship=IsFollowedBy` | Most recent followers appear first. |
| None of the above | Members who joined the site most recently appear first. |

## 2.7 CommentsSort

Default: `Date`. Use with `GET /list/{id}/comments`, `GET /log-entry/{id}/comments` and `GET /story/{id}/comments`.

| Value | Meaning |
|---|---|
| `Date` | Oldest comment first. This is the default. |
| `DateLatestFirst` | Newest comment first. |
| `Updates` | Newest content first. It returns the most recently posted or edited comments. |

With `Updates`, also send `includeDeletions=true`. The paged result then stays consistent after a comment deletion.

# 3. Relationship enums

A relationship enum has two jobs. As a request filter it limits the returned rows. As a response value it appears only where a schema field declares it. Every relationship enum in this API is a filter only. The API reports the actual state with boolean fields.

| Enum | Filter parameter | Response object that reports the same state |
|---|---|---|
| `FilmMemberRelationship` | `memberRelationship`, `filmRelationship`, `filmMemberRelationship` | `ProductionRelationship` with `watched`, `liked`, `rated`, `owned`, `inWatchlist`, `favorited` |
| `ListMemberRelationship` | `memberRelationship` on `GET /lists`; `listRelationship` on `GET /members` | `ListRelationship` with `liked` and `subscribed` |
| `ReviewMemberRelationship` | `memberRelationship` on `GET /log-entries` | `ReviewRelationship` with `liked` and `subscribed` |
| `StoryMemberRelationship` | `memberRelationship` on `GET /stories`; `storyRelationship` on `GET /members` | `StoryRelationship` with `liked` and `subscribed` |
| `MemberRelationships` | `memberRelationship` on `GET /members` | `MemberRelationship` with `following`, `followedBy`, `blocking`, `blockedBy`, `closeFriend`, `closeFriendedBy` |

## 3.1 FilmMemberRelationship

Default: `Watched` on every endpoint that names a default. Always send `member` with it.

| Values | Meaning |
|---|---|
| `Ignore` | Apply no relationship filter. Use it when you send `member` only for a `sort=MemberRating*` value. |
| `Watched` / `NotWatched` | The member did, or did not, watch the film. |
| `Liked` / `NotLiked` | The member did, or did not, like the film. |
| `Rated` / `NotRated` | The member did, or did not, rate the film. |
| `InWatchlist` / `NotInWatchlist` | The film is, or is not, in the watchlist of the member. |
| `Favorited` | The film is one of the four favorites of the member. |

On `GET /members`, `filmRelationship=InWatchlist` also needs a `member` value.

## 3.2 The other relationship enums

| Enum | Value | Meaning |
|---|---|---|
| `ListMemberRelationship` | `Owner` | The member owns the list. Default on `GET /lists`. |
| `ListMemberRelationship` | `Liked` | The member liked the list. Default on `GET /members` → `listRelationship`. |
| `ListMemberRelationship` | `Accessed` | The member viewed the shared list. It needs the token of the list owner, or the API returns 403. |
| `ReviewMemberRelationship` | `Ignore` | Apply no relationship filter. |
| `ReviewMemberRelationship` | `Owner` | The member created the log entry. |
| `ReviewMemberRelationship` | `Liked` | The member liked the review. This implies `where=HasReview`. |
| `StoryMemberRelationship` | `Owner` | The member owns the story. Default on `GET /stories`. |
| `StoryMemberRelationship` | `Liked` | The member liked the story. Default on `GET /members` → `storyRelationship`. |
| `MemberRelationships` | `IsFollowing` | Return the members that the `member` follows. This is the default. |
| `MemberRelationships` | `IsFollowedBy` | Return the members that follow the `member`. |
| `MemberRelationships` | `HasBlocked` | The `member` blocked these members. The endpoint documentation does not describe this value. |
| `MemberRelationships` | `HasCloseFriended` | The `member` added these members as close friends. The endpoint documentation does not describe this value. |

`ReviewMemberRelationship` has no default. Send `member` with every relationship parameter.

# 4. Policy and state enums

| Enum | Value | Meaning |
|---|---|---|
| `CommentPolicy` | `Anyone` | Any member can post a comment. |
| `CommentPolicy` | `Friends` | Only the members that the owner follows can post a comment. |
| `CommentPolicy` | `You` | Only the content owner can post a comment. |
| `PrivacyPolicy` | `Anyone` | Any member can see the content. |
| `PrivacyPolicy` | `Friends` | Only the members that the owner follows can see the content. |
| `PrivacyPolicy` | `You` | Only the owner can see the content. |
| `PrivacyPolicy` | `Draft` | The content is a draft. |
| `SharePolicy` | `Anyone` | Any member can access the list. |
| `SharePolicy` | `Friends` | Only the members that the owner follows can access the list. |
| `SharePolicy` | `You` | Only the owner can access the list. |
| `PosterMode` | `All` | Show every custom poster. |
| `PosterMode` | `Theirs` | Show the custom posters of other members. |
| `PosterMode` | `Yours` | Show your own custom posters only. |
| `PosterMode` | `None` | Show no custom poster. |
| `IncludeFriends` | `None` | Use the member only. This is the default everywhere. |
| `IncludeFriends` | `All` | Use the member and their friends. |
| `IncludeFriends` | `Only` | Use the friends of the member only. |
| `CommentSubscriptionState` | `Subscribed` | The member gets comment notifications. Default for the owner. |
| `CommentSubscriptionState` | `NotSubscribed` | The member gets no notification and never unsubscribed. Default for other members. |
| `CommentSubscriptionState` | `Unsubscribed` | The member unsubscribed on purpose. A new comment will not resubscribe them. |
| `CommentThreadState` | `CanComment` | The member can post a comment. Every other value blocks a comment. |
| `CommentThreadState` | `Banned` | The community managers stopped the member from comments. |
| `CommentThreadState` | `Blocked` | The owner blocked the member. |
| `CommentThreadState` | `BlockedThem` | The member blocked the owner. |
| `CommentThreadState` | `Closed` | The owner closed the thread. |
| `CommentThreadState` | `FriendsOnly` | The owner accepts comments only from members they follow. |
| `CommentThreadState` | `Moderated` | The community managers removed the content. This applies to reviews only. |
| `CommentThreadState` | `NotCommentable` | The thread accepts no comment. |
| `CommentThreadState` | `NotValidated` | The owner did not validate their email address. |

`You` in `CommentPolicy`, `PrivacyPolicy` and `SharePolicy` means the content owner, not the reader. To learn if the signed-in member can post a comment, read `commentThreadState`.

Warning: `PATCH /me` supports only `Anyone`, `Friends` and `You` for `commentPolicy` and `privacyPolicy`. Do not send `Draft` there. `PATCH /me` also names only `All`, `Yours` and `None` for `posterMode`. Read `posterModeOptions` from `GET /me` first, because the allowed options change with the account type.

Warning: `CommentSubscriptionState` is a response value only. To change the state, send the boolean field `subscribed` to `PATCH /me/subscribe/{id}` or to a relationship update request. Never send the enum value.

Warning: `sort=MemberRating*` needs one member, so send `includeFriends=None` with it.

# 5. Type and status enums

| Enum | Value | Meaning |
|---|---|---|
| `AccountStatus` | `Active` | The account is live. |
| `AccountStatus` | `Memorialized` | The account is a memorial for a member who died. |
| `MemberStatus` | `Crew` | A member of the Letterboxd team. |
| `MemberStatus` | `Alum` | A past member of the Letterboxd team. |
| `MemberStatus` | `Hq` | An official Letterboxd account. |
| `MemberStatus` | `Patron` | A Patron subscriber. |
| `MemberStatus` | `Pro` | A Pro subscriber. |
| `MemberStatus` | `Member` | A free account. |
| `CommentType` | `ListComment`, `ReviewComment`, `StoryComment` | The parent object of the comment. |
| `ProductionType` | `Film`, `Show`, `Season`, `Episode` | The kind of the production. |
| `FilmTrailerType` | `youtube` | The only value. Note the lower case. |
| `FeaturedContentType` | `FeaturedTrailer`, `FeaturedLink` | The kind of editorial content. |
| `SearchResultType` | `ContributorSearchItem`, `FilmSearchItem`, `ListSearchItem`, `MemberSearchItem`, `ReviewSearchItem` | Search result types, part one. |
| `SearchResultType` | `TagSearchItem`, `StorySearchItem`, `ArticleSearchItem`, `PodcastSearchItem`, `ShowSearchItem` | Search result types, part two. |

`GET /search` defaults to every `SearchResultType`. Its `searchMethod` parameter is a separate inline enum with the values `FullText`, `Autocomplete` and `NamesAndKeywords`. The default is `FullText`.

# 6. ActivityFilter and ActivityType

`ActivityFilter` is the request filter on `GET /member/{id}/activity` → `include`. The `exclude` parameter is DEPRECATED. Letterboxd supports both parameters for paying members only. `ActivityType` is the response field `type`. Both enums hold the same 22 values.

| Group | Values |
|---|---|
| Reviews | `ReviewActivity`, `ReviewCommentActivity`, `ReviewLikeActivity`, `ReviewResponseActivity` |
| Lists | `ListActivity`, `ListCommentActivity`, `ListLikeActivity` |
| Stories | `StoryActivity`, `StoryCommentActivity`, `StoryLikeActivity` |
| Films | `DiaryEntryActivity`, `FilmRatingActivity`, `FilmWatchActivity`, `FilmLikeActivity`, `WatchlistActivity` |
| Productions | `ProductionLikeActivity`, `ProductionWatchActivity`, `ProductionRatingActivity`, `ProductionWatchlistActivity` |
| Members | `FollowActivity` |
| Groups of actions | `CombinedPersonActivity`, `CombinedIncomingActivity` |

Defaults with no `include` and no `exclude`: with `where=OwnActivity` the feed holds every type except `FilmLikeActivity` and `FilmWatchActivity`. In every other case the feed also drops `FilmRatingActivity` and `FollowActivity`.

The `where` parameter of the activity endpoint is a separate inline enum. Its values are `OwnActivity`, `NotOwnActivity`, `IncomingActivity` and `NotIncomingActivity`. Multiple values combine with AND.

# 7. ContributionType

Use with `GET /contributor/{id}/contributions` → `type` and `GET /search` → `contributionType`. On `GET /search` this parameter implies `include=ContributorSearchItem`.

| Values | Values | Values | Values |
|---|---|---|---|
| `Director` | `CoDirector` | `Actor` | `Producer` |
| `Writer` | `OriginalWriter` | `Story` | `Casting` |
| `Editor` | `Cinematography` | `AssistantDirector` | `AdditionalDirecting` |
| `ExecutiveProducer` | `Lighting` | `CameraOperator` | `AdditionalPhotography` |
| `ProductionDesign` | `ArtDirection` | `SetDecoration` | `SpecialEffects` |
| `VisualEffects` | `TitleDesign` | `Stunts` | `Choreography` |
| `Composer` | `Songs` | `Sound` | `Costumes` |
| `Creator` | `MakeUp` | `Hairstyling` | `Studio` |

Watch the spelling. The API uses `MakeUp` with a capital U. It uses `Cinematography` and `ProductionDesign` as one word each.

# 8. Common 400 errors

| Mistake | Bad value | Correct value |
|---|---|---|
| You guess a value that the enum does not hold. | `where=Unwatched` | `where=NotWatched` |
| You use a display label from the website. | `sort=Popular this week` | `sort=FilmPopularityThisWeek` |
| You change the case. | `sort=filmpopularity` | `sort=FilmPopularity` |
| You use the wrong spelling variant on `GET /films`. | `where=Customized` | `where=Customised` |
| You use the wrong spelling variant on `GET /lists`. | `where=Customised` | `where=Customized` |
| You send a comma-separated array. | `where=Watched,Released` | `where=Watched&where=Released` |
| You send a sort value from another endpoint. | `sort=ListRanking` on `GET /films` | `sort=FilmPopularity` |
| You use a member sort without the member. | `sort=MemberRatingHighToLow` alone | Add `member=<LID>` and `includeFriends=None`. |
| You use a relationship without the member. | `memberRelationship=Liked` alone | Add `member=<LID>`. |
| You use a first-party sort. | `sort=BestMatch` from a third-party client | Use another sort value. |
| You use a friends value with no user token. | `sort=FilmPopularityWithFriends` | Sign the member in first. |
| You send an enum where the API wants a boolean. | `{"subscriptionState": "Subscribed"}` | `{"subscribed": true}` |
| You send `Draft` to the member settings. | `PATCH /me` with `privacyPolicy=Draft` | Use `Anyone`, `Friends` or `You`. |
| You mix `NoDuplicateMembers` with a blocked filter. | `filter=NoDuplicateMembers&where=Released` | Use `HasDiaryDate`, `HasReview`, `Clean` or `NoSpoilers` only. |
| You send a deprecated sort value. | `sort=RatingHighToLow` | `sort=AverageRatingHighToLow` on film lists, `sort=EntryRatingHighToLow` on log entries. |

Read the `ErrorResponse` body. It names the parameter that failed. Check that parameter against the index table at the top of this file.

# 9. Relationships

| Topic | File |
|---|---|
| Entity schemas that hold these enums as fields | `schemas-entities.md` |
| Film queries, film services and genres | The films topic skill file |
| List queries and list entry queries | The lists topic skill file |
| Diary entry and review queries | The log entries topic skill file |
| Member, activity, watchlist and search endpoints | The members topic skill file |
| OAuth scopes and the first-party limits | `authentication.md` |
