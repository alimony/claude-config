# Letterboxd API: Members
Based on Letterboxd API v0 documentation.

Every path below is relative to `https://api.letterboxd.com/api/v0`. Send `Authorization: Bearer TOKEN` with every request. URL encode all query parameters.

The examples use these shell variables.

```bash
API=https://api.letterboxd.com/api/v0
TOKEN=<access-token>
MEMBER=<member-LID>
```

## Endpoint quick reference

| Method and path | Purpose | Token | Response |
|---|---|---|---|
| `GET /member/{id}` | Full profile of one member | client | `Member` |
| `GET /members` | Search and filter members, cursored | client | `MembersResponse` (`MemberSummary[]`) |
| `GET /member/{id}/activity` | Activity feed, cursored | client (member for network activity) | `ActivityResponse` (`AbstractActivity[]`) |
| `GET /member/{id}/watchlist` | The member's watchlist, cursored | client | `FilmsResponse` |
| `GET /member/{id}/statistics` | Counts and rating histogram | client | `MemberStatistics` |
| `GET /member/{id}/me` | Your relationship with a member | member (`user`) | `MemberRelationship` |
| `PATCH /member/{id}/me` | Follow, block or add a Close Friend | member (`user`, `content:modify`) | `MemberRelationshipUpdateResponse` |
| `GET /member/{id}/list-tags-2` | The member's list tags | client | `MemberTagsResponse` |
| `GET /member/{id}/log-entry-tags` | The member's diary and review tags | client | `MemberTagsResponse` |
| `GET /member/{id}/list-tags`, `.../review-tags`, `.../review-tags-2` | **DEPRECATED** – see the Tags section | client | `TagsResponse`, `MemberTagsResponse` |
| `GET /members/pronouns` | The pronoun options | client | `PronounsResponse` |
| `GET /member/report-reasons` | Reasons for a member report | client | `ReportReasonMetadataResponse` |
| `POST /member/{id}/report` | Report a member | member (`user`, `content:modify`) | `204` |
| `POST /members/register` | Create an account | client | `Member` (`201`) |

A "client" token comes from the Client Credentials flow. A "member" token comes from the Authorization Code flow. See authentication.md.

## Restricted items in this group

| Item | Restriction |
|---|---|
| `similarTo`, `theme`, `minigenre`, `nanogenre` on `/member/{id}/watchlist` | **FIRST PARTY** – Letterboxd apps only |
| `Member.backdropPickerUrl` | **FIRST PARTY** – Letterboxd apps only |
| `include` and `exclude` on `/member/{id}/activity`, `Member.pinnedFilmLists`, `Member.pinnedReviews`, `MemberStatistics.yearsInReview` | Paying members only |
| `Member.backdrop`, `Member.backdropFocalPoint` | Returned for Patron members only |
| `Member.featuredList`, `Member.teamMembers`, `Member.orgType` | Returned for HQ members only |
| `sort=MemberPopularityWithFriends*` on `/members` | Member token only |
| `listRelationship=Accessed` on `/members` | The list owner only |

Licensing restrictions keep the First Party items with the Letterboxd apps. Do not send these parameters from a third-party client, and do not depend on these fields.

## GET /member/{id} – one member

`GET /member/{id}` returns a `Member`. The path takes the member LID, not the username.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/member/$MEMBER"
```

Responses: `200` with a `Member`, or `404` if no member matches the LID, or if the member opted out of the API.

### Member compared to MemberSummary

`MemberSummary` is the small form. It appears in every list response, in `AbstractActivity.member`, in comments and in log entries. `Member` is the full profile. It comes only from `GET /member/{id}`, from `MemberAccount.member` and from `POST /members/register`.

| Fields | `MemberSummary` | `Member` |
|---|---|---|
| `id`, `username`, `givenName`, `familyName`, `displayName`, `shortName`, `pronoun`, `avatar`, `memberStatus`, `accountStatus`, `hideAdsInContent`, `canPublishStories` | Yes | Yes |
| `bio`, `bioLbml`, `location`, `website`, `twitterUsername`, `favoriteProductions`, `pinnedFilmLists`, `pinnedReviews`, `backdrop`, `backdropFocalPoint`, `privateWatchlist`, `links`, `featuredList`, `teamMembers`, `orgType` | No | Yes |

`displayName` and `shortName` are never empty. Use `displayName` in a header. Use `shortName` in body text.

- Do this: render a list of members from the `MemberSummary` objects that the list endpoint returns.
- Do not do this: call `GET /member/{id}` for each row of a list. The extra fields are rarely needed, and the calls count against your rate limit.

`memberStatus` is one of `Crew`, `Alum`, `Hq`, `Patron`, `Pro`, `Member`. `Patron` and `Pro` are paid tiers. `Hq` marks an organisation account. `accountStatus` is `Active` or `Memorialized`. Hide the follow control for a `Memorialized` account.

## GET /members – search and filter members

`GET /members` is a cursored window over members. Each filter selects a different population. Use one filter group per request.

| Parameter | Type | Notes |
|---|---|---|
| `cursor`, `perPage` | string, int32 | The pagination cursor. `perPage` defaults to `20`, maximum `100`. |
| `sort` | `MembersSort` | Default `Date`. |
| `member` | string | A member LID. Returns the members who follow, or are followed by, this member. |
| `memberRelationship` | `MemberRelationships` | Use with `member`. Default `IsFollowing`. |
| `list` | string | A list LID. Returns the members who like the list. |
| `listRelationship` | `ListMemberRelationship` | Use with `list`. Default `Liked`. `Accessed` needs the list owner. |
| `review` | string | A review LID. Returns the members who like the review. |
| `story` | string | A story LID. Returns the members who like the story. |
| `storyRelationship` | `StoryMemberRelationship` | Use with `story`. Default `Liked`. |
| `film` | string | **DEPRECATED** A film LID. |
| `filmRelationship` | `FilmMemberRelationship` | **DEPRECATED** Use with `film`. Default `Watched`. |
| `filmMinRating`, `filmMaxRating` | number | **DEPRECATED** `0.5` to `5.0`, in steps of `0.5`. |

### MemberRelationships

| Value | Result for `member=X` |
|---|---|
| `IsFollowing` | The members that X follows. This is the default. |
| `IsFollowedBy` | The members that follow X – the followers of X. |
| `HasBlocked` | The members that X blocks. The reference does not document this value on `/members`. Expect it to work only for your own LID. |
| `HasCloseFriended` | The Close Friends of X. The same restriction applies. |

### MembersSort

| Value | Meaning |
|---|---|
| `Date` | Default. The meaning depends on the filter – see below. |
| `Name` | Alphabetical by display name. |
| `MemberPopularity` | All-time popularity. |
| `MemberPopularityThisWeek`, `...ThisMonth`, `...ThisYear` | Popularity in the period. |
| `MemberPopularityWithFriends` and its `ThisWeek`, `ThisMonth` and `ThisYear` forms | Popularity among the friends of the authenticated member. Needs a member token. |

`sort=Date` follows the filter. With `review` or `list`, the members who liked the content most recently appear first. With `film`, the members who watched, liked or watchlisted the film first appear at the top. With `member` and `IsFollowing`, the most recently followed members appear first. With `member` and `IsFollowedBy`, the most recent followers appear first. Without a filter, the members who joined the site most recently appear first.

### Worked example – the followers of a member

```bash
curl -s -G "$API/members" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "member=$MEMBER" \
  --data-urlencode "memberRelationship=IsFollowedBy" \
  --data "perPage=100"
```

Swap `IsFollowedBy` for `IsFollowing` to get the members that this member follows.

### Worked example – page through all followers

```bash
cursor=""
while : ; do
  page=$(curl -s -G "$API/members" -H "Authorization: Bearer $TOKEN" \
    --data-urlencode "member=$MEMBER" --data-urlencode "memberRelationship=IsFollowedBy" \
    --data "perPage=100" ${cursor:+--data-urlencode "cursor=$cursor"})
  echo "$page" | jq -r '.items[].username'
  cursor=$(echo "$page" | jq -r '.next // empty')
  [ -z "$cursor" ] && break   # Stop when the API returns no next cursor.
done
```

### Worked example – the members who liked a film

The `film` and `filmRelationship` parameters still work, but they are **DEPRECATED**. Letterboxd points clients to the production-scoped members endpoint. See films.md for the current path.

```bash
# Deprecated form. Use the production-scoped endpoint in new code.
curl -s -G "$API/members" -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "film=b8wK" --data-urlencode "filmRelationship=Liked" --data "sort=Date"

# The members who like a list, and the members who like a review.
curl -s -G "$API/members" -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "list=1a2B3c" --data-urlencode "listRelationship=Liked"
curl -s -G "$API/members" -H "Authorization: Bearer $TOKEN" --data-urlencode "review=4d5E6f"
```

- Do this: send `memberRelationship` together with `member`, and `listRelationship` together with `list`.
- Do not do this: send `memberRelationship` alone. The API answers `400`.

Responses: `200` with a `MembersResponse`, `400` for a bad request, `403` if the request is not allowed, `404` if the list of members does not exist.

## GET /member/{id}/activity – the activity feed

`GET /member/{id}/activity` is a cursored feed of `AbstractActivity` items. The website timeline and the app timeline use this feed. No parameter of this endpoint is First Party. The `include` and `exclude` parameters need a paying member.

| Parameter | Type | Notes |
|---|---|---|
| `id` (path) | string | The member LID. |
| `cursor`, `perPage` | string, int32 | The pagination cursor. `perPage` defaults to `20`, maximum `100`. |
| `include` | `ActivityFilter[]` | Paying members only. Repeat the parameter for each value. |
| `exclude` | `ActivityFilter[]` | **DEPRECATED** Paying members only. Use `include`. |
| `where` | enum, repeatable | Reduces the feed. See below. |
| `adult` | boolean | Default `false`. Set to `true` to include adult content. |
| `combine` | boolean | Default `false`. Set to `true` to group related items. |
| `parentActivity` | string | Returns the child items of one combined item. Default `null`. |
| `excludeMemberFilmRelationships` | boolean | Set to `true` to drop the member and film relationship data. This makes the response smaller. |

### The `where` parameter

`OwnActivity` keeps only the actions of the member. `NotOwnActivity` drops them. `IncomingActivity` keeps only the actions of other members on the content of the member. `NotIncomingActivity` drops those.

Repeat `where` to combine terms. The API applies AND between the terms. `where=OwnActivity&where=NotIncomingActivity` returns the actions of the member, but drops the comments of the member on their own lists and reviews.

The reference text also names a `NetworkActivity` value – activity by the member or by the followers of the member – and gives `where=NetworkActivity&where=NotOwnActivity` as the way to see only follower activity. The `where` enum in the same reference does not list `NetworkActivity`. Test this value against the live API before you depend on it.

If you send none of `NetworkActivity`, `OwnActivity` or `NotIncomingActivity`, you get activity on the content of the member from members outside the network of the member.

### Default activity types

The defaults apply when you send neither `include` nor `exclude`. With `where=OwnActivity`, the feed excludes `FilmLikeActivity` and `FilmWatchActivity`. In every other request, the feed also excludes `FilmRatingActivity` and `FollowActivity`. These defaults copy the website. Keep them unless the member asks for more detail.

### ActivityFilter – values for `include` and `exclude`

| Value | Covers | In the default feed |
|---|---|---|
| `ReviewActivity`, `ReviewCommentActivity`, `ReviewLikeActivity`, `ReviewResponseActivity` | A member published a review, commented on one, liked one, or replied to one | Yes |
| `ListActivity`, `ListCommentActivity`, `ListLikeActivity` | A member published or updated a list, commented on one, or liked one | Yes |
| `StoryActivity`, `StoryCommentActivity`, `StoryLikeActivity` | A member published a story, commented on one, or liked one | Yes |
| `DiaryEntryActivity` | A member added a diary entry | Yes |
| `FilmRatingActivity` | A member rated a film | Own activity only |
| `FilmWatchActivity` | A member marked a film as watched | No |
| `FilmLikeActivity` | A member liked a film | No |
| `WatchlistActivity` | A member added a film to a watchlist | Yes |
| `FollowActivity` | A member followed another member | Own activity only |
| `CombinedPersonActivity` | Grouped items from one member | Yes, with `combine=true` |
| `CombinedIncomingActivity` | Grouped incoming items on the content of the member | Yes, with `combine=true` |
| `ProductionLikeActivity`, `ProductionWatchActivity`, `ProductionRatingActivity`, `ProductionWatchlistActivity` | The same four actions on a show, season or episode | Yes |

### ActivityType – the discriminator in the response

`ActivityType` holds the same 22 values as `ActivityFilter`. `ActivityFilter` is the request side. `ActivityType` is the response side: the API returns it in the `type` field of each item.

| `type` value | The item is about |
|---|---|
| `Review*` (four values), `List*` (three values), `Story*` (three values) | A review, list or story, or a comment on one |
| `DiaryEntryActivity` | A diary entry – a log entry with a diary date |
| `FilmWatchActivity`, `FilmRatingActivity`, `FilmLikeActivity`, `WatchlistActivity` | A film |
| `ProductionWatchActivity`, `ProductionRatingActivity`, `ProductionLikeActivity`, `ProductionWatchlistActivity` | A show, season or episode |
| `FollowActivity` | Another member |
| `CombinedPersonActivity`, `CombinedIncomingActivity` | A group of child items |

### The polymorphic response

`ActivityResponse` holds `next`, `items` and `itemCount`. Each item is an `AbstractActivity`.

`AbstractActivity` defines three things only.

| Field | Type | Meaning |
|---|---|---|
| `member` | `MemberSummary` | The member who did the action. |
| `whenCreated` | date-time | ISO 8601 with UTC timezone, `YYYY-MM-DDThh:mm:ssZ`. |
| `type` | `ActivityType` | The discriminator. It selects the concrete type. |

The concrete type adds its own payload fields, such as the review, the list or the film. The v0 reference leaves the discriminator value table empty, so it does not publish the payload field names. Read one live response for each type that you support, then map the fields.

Switch on `type` and always keep a default branch.

```ts
type Activity = { type: string; member: MemberSummary; whenCreated: string; [k: string]: unknown };

function renderActivity(a: Activity) {
  switch (a.type) {
    case "DiaryEntryActivity": case "ReviewActivity": case "ReviewResponseActivity":
      return renderLogEntry(a);
    case "ListActivity": case "ListLikeActivity": case "ListCommentActivity":
      return renderList(a);
    case "StoryActivity": case "StoryLikeActivity": case "StoryCommentActivity":
      return renderStory(a);
    case "FilmWatchActivity": case "FilmRatingActivity": case "FilmLikeActivity":
    case "WatchlistActivity": case "ProductionWatchActivity":
      return renderFilm(a);
    case "CombinedPersonActivity": case "CombinedIncomingActivity":
      return renderGroup(a);
    default:
      return null;   // Letterboxd adds new types. Skip an unknown type, do not fail.
  }
}
```

- Do this: treat an unknown `type` as a skip.
- Do not do this: throw an error on an unknown `type`. A new type breaks the whole feed.

### Combined activity

Set `combine=true` to group related items. The API then returns `CombinedPersonActivity` and `CombinedIncomingActivity` items. Send the identifier of one parent item in `parentActivity` to get the child items of that parent. The reference does not document an `id` field on `AbstractActivity`, so read the identifier field from a live combined response before you build this screen.

### Examples

```bash
# The default timeline of a member.
curl -s -G "$API/member/$MEMBER/activity" -H "Authorization: Bearer $TOKEN" --data "perPage=50"

# Only the actions of the member, without incoming comments.
curl -s -G "$API/member/$MEMBER/activity" -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "where=OwnActivity" --data-urlencode "where=NotIncomingActivity"

# Reviews and diary entries only. This needs a paying member.
curl -s -G "$API/member/$MEMBER/activity" -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "include=ReviewActivity" --data-urlencode "include=DiaryEntryActivity" \
  --data "excludeMemberFilmRelationships=true"
```

Responses: `200` with an `ActivityResponse`, or `404` if no member matches the LID, or if the member opted out of the API.

## GET /member/{id}/watchlist

`GET /member/{id}/watchlist` returns the public watchlist of a member as a `FilmsResponse`. Add or remove films with `PATCH /film/{id}/me`. See films.md.

| Parameter group | Parameters |
|---|---|
| Pagination | `cursor`, `perPage` (default `20`, maximum `100`) |
| Film selection | `filmId` (up to 100 LIDs, or `tmdb:` and `imdb:` prefixed IDs) |
| Category | `genre`, `includeGenre`, `excludeGenre` (up to 100 each), `country` (ISO 3166-1), `language` (ISO 639-1), `decade` (a year that ends in `0`), `year` |
| Availability | `service`, `availabilityType`, `exclusive`, `unavailable`, `includeOwned`, `negate` |
| State | `where` (`FilmWhereClause`, repeatable) |
| Comparison member | `member`, `memberRelationship`, `includeFriends`, `memberMinRating`, `memberMaxRating` |
| Tags | `tagCode`, `tagger`, `includeTaggerFriends`, `includeTags`, `excludeTags`, `tag` (**DEPRECATED**) |
| Output | `sort`, `excludeMemberFilmRelationships` |
| **FIRST PARTY** | `similarTo`, `theme`, `minigenre`, `nanogenre` |

`sort` defaults to `Added` – the order in which the member added the films, most recent first. The other values are `DateLatestFirst`, `DateEarliestFirst`, `Shuffle`, `FilmName`, `OwnerRatingHighToLow`, `OwnerRatingLowToHigh`, `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh`, `AuthenticatedMemberBasedOnLiked`, `AuthenticatedMemberRelatedToLiked`, `MemberRatingHighToLow`, `MemberRatingLowToHigh`, `AverageRatingHighToLow`, `AverageRatingLowToHigh`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `FilmDurationShortestFirst` and `FilmDurationLongestFirst`.

`includeFriends` takes `None` (default), `Only` or `All`. `None` uses the comparison member alone. `Only` uses the friends of that member. `All` uses both. `includeTaggerFriends` works the same way for `tagger`.

The `AuthenticatedMember*` values need a member token. The `MemberRating*` values need `member` and `includeFriends=None`. The `Rating*` values are **DEPRECATED** – use `AverageRating*`. The `FilmPopularityThisWeek`, `FilmPopularityThisMonth` and `FilmPopularityThisYear` values are **DEPRECATED** and have never worked.

The response holds the film relationships for three parties: the signed-in member, the watchlist owner, and the member in the `member` parameter. Use this to compare two members.

```bash
# The watchlist of a member, in the order that the member added the films.
curl -s -G "$API/member/$MEMBER/watchlist" -H "Authorization: Bearer $TOKEN" --data "perPage=100"

# Films on the watchlist that a second member has already watched.
curl -s -G "$API/member/$MEMBER/watchlist" -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "member=<other-member-LID>" --data-urlencode "memberRelationship=Watched"

# The 1990s films on the watchlist that are on a streaming service.
curl -s -G "$API/member/$MEMBER/watchlist" -H "Authorization: Bearer $TOKEN" \
  --data "decade=1990" --data-urlencode "service=<service-id>"
```

Responses: `200` with a `FilmsResponse`, `400` for a bad request, `403` if the watchlist is private, `404` if no member matches the LID.

### Watchlist compared to GET /films

`GET /films?member=X&memberRelationship=InWatchlist` returns the same films, but it behaves differently.

| Aspect | `/member/{id}/watchlist` | `/films` with `memberRelationship=InWatchlist` |
|---|---|---|
| Who owns the watchlist | The `id` in the path | The `member` query parameter |
| What `member` means | A second member, for comparison | The watchlist owner |
| Default sort | `Added` – the watchlist order | `FilmPopularity` |
| Watchlist-only sorts | `Added`, `Shuffle`, `OwnerRating*` | Not available |
| Other sorts | No `BestMatch`, no `*WithFriends` | `BestMatch` and `FilmPopularityWithFriends*` |
| A private watchlist | `403` | The reference documents no `403` |
| `includeFriends` | Applies to the comparison member | Pulls the watchlists of the friends of the owner |

- Do this: use `/member/{id}/watchlist` to show a watchlist screen in watchlist order.
- Do not do this: use `/films` for a watchlist screen. You lose the `Added` order and the clear `403` signal.

## GET /member/{id}/statistics

`GET /member/{id}/statistics` returns a `MemberStatistics` object. Use it for a profile header. Do not count the items of a list endpoint to get a total.

The object holds `member` (a `MemberIdentifier` with the LID only), `counts`, `ratingsHistogram`, `yearsInReview` (paying members only) and `summaryYears`.

`counts` holds `watches`, `ratings`, `reviews`, `diaryEntries`, `diaryEntriesThisYear`, `diaryEntriesLastYear`, `filmsInDiaryThisYear`, `filmsInDiaryLastYear`, `watchlist`, `lists`, `followers`, `following`, `listTags`, `filmTags`, `filmLikes`, `listLikes`, `reviewLikes` and `storyLikes`. `watches` counts each film once, even with several log entries. `unpublishedLists` and `accessedSharedLists` appear only when the authenticated member asks for their own statistics.

Each `RatingsHistogramBar` holds `rating` (`0.5` to `5.0`), `count` and `normalizedWeight` (`0.0` to `1.0`). The tallest bar always returns `1.0`. Draw the bar height from `normalizedWeight`. Show the number from `count`.

Warning: the histogram returns only the whole-star increments from `1.0` to `5.0` if the member never awards half stars. Do not assume 10 bars.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/member/$MEMBER/statistics" \
  | jq '{watches: .counts.watches, followers: .counts.followers, bars: (.ratingsHistogram | length)}'
```

## GET and PATCH /member/{id}/me – follow, unfollow, block

`GET /member/{id}/me` returns the `MemberRelationship` between the authenticated member and the member in the path. It needs the `user` scope.

| Field | Meaning |
|---|---|
| `following`, `followedBy` | You follow them. They follow you. |
| `blocking`, `blockedBy` | You block them. They block you. |
| `closeFriend`, `closeFriendedBy` | You added them to your Close Friends. They added you to theirs. |
| `privateNote` | Your private note about them – `text`, `textLbml`, `whenCreated`, `whenUpdated`. |

`PATCH /member/{id}/me` changes the relationship. It needs the `user` and `content:modify` scopes. Send only the fields that change: `following`, `blocking` and `closeFriend`. Set `true` to follow, block or add a Close Friend. Set `false` to reverse the action.

```bash
H=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")
curl -s -X PATCH "$API/member/$MEMBER/me" "${H[@]}" -d '{"following": true}'    # Follow.
curl -s -X PATCH "$API/member/$MEMBER/me" "${H[@]}" -d '{"following": false}'   # Unfollow.
curl -s -X PATCH "$API/member/$MEMBER/me" "${H[@]}" -d '{"blocking": true}'     # Block.
curl -s -X PATCH "$API/member/$MEMBER/me" "${H[@]}" -d '{"closeFriend": true}'  # Close Friend.
```

The response is a `MemberRelationshipUpdateResponse`. It holds `data` – the new `MemberRelationship` – and `messages`. Each message has a `type` of `Error` or `Success`, a `code` and a human-readable `title`.

| Message code | Cause |
|---|---|
| `FollowYourself`, `BlockYourself`, `BefriendYourself` | The target is your own account. |
| `FollowRateLimit` | You follow too many members too fast. |
| `FollowBlockedMember`, `BefriendBlockedMember` | The target blocks you. |
| `FollowMemberYouBlocked`, `BefriendMemberYouBlocked` | You block the target. |

- Do this: read `messages` after every `PATCH`, and show each `Error` message to the user.
- Do not do this: treat `200` as success. The API returns `200` with an `Error` message when it rejects the change.

If your client cannot send `PATCH`, send `POST` with the header `X-HTTP-Method-Override: PATCH`.

## Tags

Five tag endpoints exist. All five take the member LID in the path and an optional `input` prefix. The match is case-insensitive, so `pro` matches `pro`, `project` and `Professional`. An empty `input` returns all tags of the member, in order of relevance.

| Endpoint | Response | Status |
|---|---|---|
| `GET /member/{id}/list-tags-2` | `MemberTagsResponse` | Current. Use this for list tags. |
| `GET /member/{id}/log-entry-tags` | `MemberTagsResponse` | Current. Use this for diary entry and review tags. |
| `GET /member/{id}/list-tags` | `TagsResponse` | **DEPRECATED** – use `list-tags-2`. |
| `GET /member/{id}/review-tags` | `TagsResponse` | **DEPRECATED** – use `log-entry-tags`. |
| `GET /member/{id}/review-tags-2` | `MemberTagsResponse` | **DEPRECATED** – use `log-entry-tags`. |

The "-2" suffix marks the second generation of the response shape. A `TagsResponse` holds plain strings. A `MemberTagsResponse` holds `MemberTag` objects: `code`, `displayTag`, `counts` and the deprecated `tag`. `counts` holds `films`, `logEntries`, `diaryEntries`, `reviews` and `lists`.

A new client uses two endpoints only: `list-tags-2` for lists and `log-entry-tags` for diary entries and reviews. `log-entry-tags` is the modern replacement for both review-tag endpoints, so no `log-entry-tags-2` exists.

```bash
curl -s -G "$API/member/$MEMBER/log-entry-tags" \
  -H "Authorization: Bearer $TOKEN" --data-urlencode "input=hor" \
  | jq -r '.items[] | "\(.displayTag) (\(.code)): \(.counts.logEntries)"'
```

- Do this: send `code` as the `tagCode` value when you filter films, log entries or lists.
- Do not do this: send `displayTag` as a filter value. Show `displayTag` to the user only.

## GET /members/pronouns

`GET /members/pronouns` returns a `PronounsResponse` with the supported `Pronoun` options.

Each `Pronoun` holds `id` – the LID that you send when you set a pronoun – plus `label` for a picker, and the `subjectPronoun`, `objectPronoun`, `possessiveAdjective`, `possessivePronoun` and `reflexive` forms.

`Member.pronoun` and `MemberSummary.pronoun` hold the full `Pronoun` object. Use the forms to build sentences such as "added a film to *their* watchlist".

Set the pronoun with `PATCH /me` and the `pronoun` field. Send the LID, not the label. `PATCH /me` needs the `user:owner` and `profile:modify` scopes. See me.md.

```bash
# Read the options.
curl -s -H "Authorization: Bearer $TOKEN" "$API/members/pronouns" | jq -r '.items[] | "\(.id)\t\(.label)"'

# Set the pronoun of the authenticated member.
curl -s -X PATCH "$API/me" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"pronoun": "<pronoun-LID>"}'
```

A bad value returns the `InvalidPronounOption` message code. You cannot set the pronoun of another member.

## Register a member and report a member

### POST /members/register

`POST /members/register` creates an account. It sends a `RegisterRequest` and returns `201` with a `Member`, or `400` if the username is taken or invalid.

Send `username`, `password`, `emailAddress`, `captchaResponse`, `captchaType` and `acceptTermsOfUse`. A username has 2 to 15 characters, and holds letters, numbers and the underscore only. Check the username first with `GET /auth/username-check`. Set `acceptTermsOfUse` to `true` only when the person agrees to the Terms of Use and confirms an age of 16 or more.

The reference does not mark this endpoint **FIRST PARTY**, and it lists no scope. It needs a valid captcha pair. Ask Letterboxd for the captcha configuration before you build a registration screen. Most third-party clients send the member to the website instead.

### GET /member/report-reasons

`GET /member/report-reasons` returns a `ReportReasonMetadataResponse`. Each `ReportReasonMetadata` holds `reason`, `code`, `priority`, `descriptionHtml` and `messageRequired`. Sort the reasons by `priority`, lowest first. Render `descriptionHtml` as HTML. Make the message field mandatory when `messageRequired` is `true`.

### POST /member/{id}/report

`POST /member/{id}/report` reports a member. It needs the `user` and `content:modify` scopes. It returns `204` on success.

Send `reason` – one of `AbusiveAccount`, `HatefulAccount`, `ManipulativeAccount`, `OffensiveAccount`, `ParodyAccount`, `PiracyAccount`, `PlagiaristAccount`, `SolicitousAccount`, `SpamAccount` or `Other`. Send `message` too. The message is required for `PlagiaristAccount`, `SolicitousAccount` and `Other`.

```bash
curl -s -X POST "$API/member/$MEMBER/report" -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason": "SpamAccount"}'
```

Build the reason picker from `GET /member/report-reasons`. Do not hard-code the list – Letterboxd changes it.

## Pitfalls

**LID, not username.** Every `{id}` in this group is a member LID, such as `1PmMS`. A username never works. Get the LID from the `x-letterboxd-identifier` response header of the profile page, or from the `boxd.it` share URL in the Letterboxd iOS app. A `HEAD` request is the fastest method.

```bash
curl -sI https://letterboxd.com/dave/ | grep -i x-letterboxd-identifier
```

**Private profiles.** A member can set `privateAccount`. Their content then does not appear in the API, except in the `/me` endpoints. Every endpoint in this group answers `404` for such a member, with the same text as an unknown LID. Do not treat `404` as "the account does not exist". The `profile:private:view` scope lets your client see the private profile details of the authenticated member. It does not open the private profile of another member. A private watchlist answers `403`, not `404`, because the account is visible but the watchlist is not.

**The 100,000-object cap and cursors.** Cursor pagination stops after 100,000 objects. Letterboxd applies the cap to discourage a copy of the dataset. Follower lists of large accounts hit this limit, so filter the query and plan for a truncated result. No `page` or `offset` parameter exists. Pass the `next` value back as `cursor`, and stop when `next` is absent. Do not compute the number of pages from `itemCount` – the field is optional.

**Client token compared to member token.** These endpoints need a member token: `GET /member/{id}/me`, `PATCH /member/{id}/me`, `POST /member/{id}/report`, and any request with `sort=MemberPopularityWithFriends*` or `listRelationship=Accessed`. A client-credentials token returns public data only. It also returns no `relationships` data for a signed-in member, because no member signs in.

**Paid features.** `include` and `exclude` on the activity feed work for paying members only. Check `MemberAccount.capabilities` for `CanFilterActivity` before you show the filter control.

**Deprecated film filters.** `film`, `filmRelationship`, `filmMinRating` and `filmMaxRating` on `GET /members` are deprecated. Use the production-scoped members endpoint for new code.

**PATCH support.** Send `X-HTTP-Method-Override: PATCH` in a `POST` if your HTTP client cannot send `PATCH`.

## Relationships

| File | Content |
|---|---|
| overview.md | Base URL, LIDs, cursor pagination, the First Party rule |
| authentication.md | OAuth2 flows, scopes, token refresh and revocation |
| me.md | `GET /me`, `PATCH /me`, favorites, likes, ratings, watchlist writes for the authenticated member |
| films.md | `FilmSummary`, film relationships, `PATCH /film/{id}/me`, the production-scoped members endpoint |
| lists.md | List LIDs for the `list` filter, list tags, `ListMemberRelationship` |
| log-entries.md | Diary entries and reviews behind `DiaryEntryActivity` and `ReviewActivity`, log entry tags |
| schemas-enums.md | Full value lists for `MembersSort`, `MemberRelationships`, `MemberStatus`, `AccountStatus`, `ActivityFilter`, `ActivityType`, `IncludeFriends` |
