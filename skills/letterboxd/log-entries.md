# Letterboxd API: Log Entries, Diary and Reviews
Based on Letterboxd API v0 documentation.

Base URL: `https://api.letterboxd.com/api/v0`. Send `Authorization: Bearer TOKEN` with every request. If your HTTP client cannot send PATCH, send POST with the header `X-HTTP-Method-Override: PATCH`. See `authentication.md` for the flows and the scopes.

**FIRST PARTY** marks an endpoint, a parameter or a field that only Letterboxd's own apps can use. This group has no First Party endpoint and no First Party parameter. See section 11.

## 1. The core concept: one object, two optional halves

Letterboxd stores a viewing, a diary entry, a rating and a review in one object. The API calls this object a **log entry** and returns it as a `FilmLogEntry`.

A log entry is valid only if it has at least one of these two blocks:

- `diaryDetails` – the entry appears in the member's diary. This block needs a date.
- `review` – the entry appears as a review. This block needs text.

An entry can have both blocks. The rating, the like, the tags and the privacy policy belong to the log entry itself. They do not belong to the diary block or to the review block.

```
FilmLogEntry
├─ id, owner, film, name, links
├─ whenCreated / whenUpdated   (UTC timestamps of the record)
├─ rating        0.5 … 5.0     ← on the entry, not in review or diaryDetails
├─ like          boolean       ← on the entry
├─ tags2[]       Tag objects   ← on the entry
├─ privacyPolicy Anyone | Friends | You | Draft
│
├─ diaryDetails?               ← present = the entry is a diary entry
│    ├─ diaryDate  "YYYY-MM-DD"  (the watch date)
│    └─ rewatch    boolean
│
└─ review?                     ← present = the entry is a review
     ├─ lbml            (source text you edit)
     ├─ text            (HTML you render)
     ├─ containsSpoilers, spoilersLocked, moderated
     └─ whenReviewed    (publish timestamp)
```

Annotated response, cut to the fields that matter:

```jsonc
{
  "id": "8UxL",                    // the log entry LID, used in every /log-entry/{id} path
  "owner": { "id": "1YHc" },
  "film":  { "id": "2bbs", "name": "Sinners", "releaseYear": 2025 },
  "rating": 4.5,                   // the member rating, or absent
  "like": true,                    // the heart
  "tags2": [ { "code": "70mm", "displayTag": "70mm" } ],
  "diaryDetails": {                // absent = the entry is not in the diary
    "diaryDate": "2026-08-14",     // date only, no time, no timezone
    "rewatch": false
  },
  "review": {                      // absent = the entry has no review
    "lbml": "A <strong>great</strong> film.",   // source text, for an update
    "text": "<p>A <strong>great</strong> film.</p>",  // HTML, for display
    "containsSpoilers": false,
    "whenReviewed": "2026-08-14T21:03:11Z"      // the publish time of the text
  },
  "privacyPolicy": "Anyone",
  "commentable": true,
  "whenCreated": "2026-08-14T21:03:11Z",  // the record, not the watch date
  "whenUpdated": "2026-08-15T07:22:04Z"
}
```

The four possible shapes:

| `diaryDetails` | `review` | The result |
|---|---|---|
| present | absent | A diary entry with no text. It can carry a rating and a like. |
| absent | present | A review with no diary date. It does not appear in the diary. |
| present | present | A diary entry and a review. This is the usual case. |
| absent | absent | Invalid. The API rejects it with `LogEntryWithNoReviewOrDiaryDetails`. |

**A rating alone is not a log entry.** To rate a film without a diary entry or a review, use `PATCH /me/rate/{id}` with the film LID. See section 7.

`LogEntrySummary` is the short form that other endpoints embed. It carries `id`, `rating`, `like`, `privacyPolicy` and the two booleans `review` and `diaryEntry`. Use those booleans to test the shape without a second request.

## 2. Endpoint quick reference

| Method and path | Operation ID | Scopes | Purpose |
|---|---|---|---|
| `GET /log-entries` | `getLogEntries` | token only | Query diary entries and reviews. |
| `GET /log-entry/{id}` | `getLogEntry` | token only | Get one log entry. |
| `GET /log-entry/{id}/statistics` | `getReviewStatistics` | token only | Comment and like counts. |
| `GET /log-entry/{id}/comments` | `getReviewComments` | token only | Comments on the review. |
| `GET /log-entry/{id}/members` | `filmMemberRelationships` | token only | Members who liked the review. |
| `GET /log-entry/{id}/me` | `myRelationshipToReview` | `user` | Your like, subscription and comment state. |
| `POST /log-entries` | `createLogEntry` | `user`, `content:modify` | Create a diary entry or a review. |
| `PATCH /log-entry/{id}` | `updateLogEntry` | `user`, `content:modify` | Update your own entry. |
| `DELETE /log-entry/{id}` | `deleteLogEntry` | `user`, `content:modify` | Delete your own entry. |
| `PATCH /log-entry/{id}/me` **DEPRECATED** | `updateMyRelationshipToReview` | `user`, `content:modify` | Like or subscribe. Use `/me/like` and `/me/subscribe`. |
| `POST /log-entry/{id}/comments` | `createReviewComment` | `user`, `content:modify` | Comment on a review. |
| `POST /log-entry/{id}/report` | `reportReview` | `user`, `content:modify` | Report a review. |

The GET endpoints need a valid token but no extra scope. `token only` in the table above means that. Every write needs `user` and `content:modify`.

## 3. GET /log-entries

A cursored window over log entries for a film or for a member. Returns `LogEntriesResponse`: `items` (a `FilmLogEntry[]`), `itemCount` and `next`. Pass `next` back as `cursor` to get the following page.

### 3.1 Parameters by group

**Pagination**: `cursor` (the `next` value from the last response) and `perPage` (default `20`, maximum `100`).

**Scope: which entries**

| Parameter | Notes |
|---|---|
| `film` | The film LID. Returns entries for that film. |
| `member` | The member LID. Required for `memberRelationship`, `filmMemberRelationship`, `includeFriends` and the `MemberRating*` sorts. |
| `memberRelationship` | `Owner` returns entries the member created. `Liked` returns reviews the member liked, and implies `where=HasReview`. `Ignore` applies no member filter. |
| `filmMemberRelationship` | Filters by the member's relationship to the film, for example `Liked` or `InWatchlist`. Use it with `member`. |
| `includeFriends` | `None` (default), `Only` or `All`. Use it with `member`. |

**Date window** (use with `where=HasDiaryDate` for a true diary window)

| Parameter | Notes |
|---|---|
| `year` | The four-digit year. |
| `month` | `1` to `12`. Needs `year`. |
| `week` | `1` to `52`. Needs `year`. |
| `day` | `1` to `31`. Needs `month` and `year`. |

**Rating and privacy**: `minRating` and `maxRating` (`0.5` to `5.0` in steps of `0.5`), and `privacyPolicy` (`Anyone`, `Friends`, `You` or `Draft`).

**Film metadata**: `filmDecade` (a year that ends in `0`), `filmYear`, `genre`, `includeGenre[]`, `excludeGenre[]` (up to 100 genre LIDs each), `country` (ISO 3166-1), `language` (ISO 639-1).

**Tags**: `tagCode` (`tag` is **DEPRECATED**), `tagger` (a member LID, needs `tagCode` or `includeTags`), `includeTaggerFriends`, `includeTags[]`, `excludeTags[]`.

**Availability**: `service`, `availabilityType[]`, `exclusive`, `unavailable`, `includeOwned`, `negate`.

**Content and payload**: `where[]`, `filter=NoDuplicateMembers`, `preferredLanguage` (BCP-47, for example `en-NZ`), `excludeMemberFilmRelationships` (set `true` to make the response smaller).

### 3.2 `where` clauses (`LogEntryWhereClause`)

Repeat the parameter to combine clauses: `where=Clean&where=NoSpoilers`. The API applies AND between them.

| Group | Values | Meaning |
|---|---|---|
| Entry shape | `HasDiaryDate`, `HasReview`, `NoDrafts`, `Rated`, `NotRated` | Filters the log entry itself. |
| Review content | `Clean`, `NoSpoilers` | `Clean` drops reviews with profane language. `NoSpoilers` drops reviews the owner flagged. |
| Film properties | `Released`, `NotReleased`, `FeatureLength`, `NotFeatureLength`, `Fiction`, `Film`, `TV` | These describe the film, not the entry. `Fiction` drops documentaries. `Film` drops TV shows. `TV` keeps only TV shows. |
| Viewer relationship | `InWatchlist`, `NotInWatchlist`, `Watched`, `NotWatched`, `Logged`, `NotLogged`, `Rewatched`, `NotRewatched`, `Reviewed`, `NotReviewed`, `Owned`, `NotOwned`, `Liked`, `NotLiked`, `Customised`, `NotCustomised`, `CustomisedBackdrop`, `NotCustomisedBackdrop`, `AddedPrivateNote`, `NotAddedPrivateNote` | These read the authenticated member's film lists. Add `member` and `filmMemberRelationship` to test another member instead. |

The endpoint documents `HasReview` for "the entry contains a review". It does not document a negation of `HasReview`. `NotReviewed` describes the member's relationship to the *film*. To find entries with no review text, request the entries and then keep the items where `review` is absent.

### 3.3 `sort` values

The default is `WhenAdded`. The default becomes `Date` when you pass `where=HasDiaryDate`.

| Group | Values | Constraints |
|---|---|---|
| Time | `WhenAdded`, `Date`, `WhenLiked` | `Date` sorts by the diary date and implies `where=HasDiaryDate`. |
| Counts | `DiaryCount`, `ReviewCount` | – |
| Entry rating | `EntryRatingHighToLow`, `EntryRatingLowToHigh` | Sorts by the rating on each entry. |
| Entry rating **DEPRECATED** | `RatingHighToLow`, `RatingLowToHigh` | Use the `EntryRating*` values. |
| Viewer rating | `AuthenticatedMemberRatingHighToLow`, `AuthenticatedMemberRatingLowToHigh` | Signed-in members only. |
| Member rating | `MemberRatingHighToLow`, `MemberRatingLowToHigh` | Needs `member` and `includeFriends=None`. |
| Film rating | `AverageRatingHighToLow`, `AverageRatingLowToHigh` | – |
| Film metadata | `FilmName`, `ReleaseDateLatestFirst`, `ReleaseDateEarliestFirst`, `FilmDurationShortestFirst`, `FilmDurationLongestFirst` | Do not combine these with `film`. |
| Review popularity | `ReviewPopularity`, and the `ThisWeek`, `ThisMonth`, `ThisYear` variants | Ranks by likes and comments. Implies `where=HasReview`. |
| Film popularity | `FilmPopularity`, and the `ThisWeek`, `ThisMonth`, `ThisYear` variants | Do not combine these with `film`. |
| With friends | `ReviewPopularityWithFriends*`, `FilmPopularityWithFriends*` | Signed-in members only. |

With a `film` value, only `WhenAdded`, `Date`, `EntryRating*` and `ReviewPopularity*` apply.

### 3.4 Worked examples

A member's diary for one month, newest watch date first:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/log-entries?member=1YHc&memberRelationship=Owner\
&where=HasDiaryDate&where=NoDrafts&year=2026&month=3&sort=Date&perPage=100"
```

All reviews of one film, most popular first, spoilers excluded:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/log-entries?film=2bbs&sort=ReviewPopularity\
&where=NoSpoilers&where=Clean&perPage=50&preferredLanguage=en-NZ"
```

`ReviewPopularity` already implies `where=HasReview`, so you do not need to add it.

A member's rated entries, highest rating first. Keep the ones with no review in your own code:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/log-entries?member=1YHc&memberRelationship=Owner\
&where=Rated&sort=EntryRatingHighToLow&perPage=100&excludeMemberFilmRelationships=true"
```

```js
// Keep the entries that carry a rating but no review text.
const ratedOnly = response.items.filter(e => e.rating != null && e.review == null);
```

One recent entry per member, for a "who watched this" strip:

```
GET /log-entries?film=2bbs&filter=NoDuplicateMembers&sort=WhenAdded&perPage=20
```

`filter=NoDuplicateMembers` has strict limits. Without `film`, it returns only entries from the past 30 days. It works only with `WhenAdded`, `Date` and `ReviewPopularity*`. Do not combine it with `filmMemberRelationship`, `filmDecade`, `filmYear`, `genre`, `tagCode` or `service`. The only permitted `where` values are `HasDiaryDate`, `HasReview`, `Clean` and `NoSpoilers`.

Responses: `200` `LogEntriesResponse`, `400` bad request, `403` no permission to view, `404` film or member not found.

## 4. GET /log-entry/{id} and the sub-resources

`GET /log-entry/{id}` returns one `FilmLogEntry`. The optional `preferredLanguage` query parameter translates the review text. A bad BCP-47 code returns `400`. An unknown LID returns `404`.

`GET /log-entry/{id}/statistics` returns `ReviewStatistics`:

```json
{ "logEntry": { "id": "8UxL" }, "counts": { "comments": 12, "likes": 340 } }
```

`GET /log-entry/{id}/comments` returns a cursored `ReviewCommentsResponse` of `ReviewComment` objects. Parameters: `cursor`, `perPage`, `sort` (`Date`, `DateLatestFirst` or `Updates`) and `includeDeletions`. Use `sort=Updates` with `includeDeletions=true` to sync a comment thread. `Updates` returns the newest content first, so you see edits and deletions.

Each comment carries `comment` (HTML) and `commentLbml` (source). The text is absent when `deleted`, `removedByAdmin`, `removedByContentOwner`, `blocked` or `blockedByOwner` is `true`. Test those flags before you render.

`GET /log-entry/{id}/members` returns `MemberFilmRelationshipsResponse`. The name is misleading. It lists the members who liked the review, and it gives each member's relationship to the **film**. Parameters: `cursor`, `perPage`, `sort` (a `MembersSort` value, default `Date`, so the newest like comes first), `member` and `memberRelationship` (`IsFollowing` by default).

`GET /log-entry/{id}/me` returns `ReviewRelationship` for the signed-in member:

```json
{
  "liked": false,
  "subscribed": false,
  "subscriptionState": "NotSubscribed",
  "commentThreadState": "CanComment"
}
```

Read `commentThreadState` before you show a comment box. Only `CanComment` permits a comment. The other values are `Banned`, `Blocked`, `BlockedThem`, `Closed`, `FriendsOnly`, `Moderated`, `NotCommentable` and `NotValidated`. `subscriptionState` is `Subscribed`, `NotSubscribed` or `Unsubscribed`. `Unsubscribed` is sticky: the member left the thread on purpose, so a new comment does not resubscribe them.

## 5. POST /log-entries – create a diary entry or a review

Scopes: `user` and `content:modify`. Body: `LogEntryCreationRequest`. Optional header `Accept-Language` gives the API a hint for the review language.

```bash
curl -X POST "https://api.letterboxd.com/api/v0/log-entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "Accept-Language: en-NZ" \
  -d '{
    "filmId": "2bbs",
    "diaryDetails": {
      "diaryDate": "2026-08-14",
      "rewatch": true
    },
    "review": {
      "text": "Better on the second pass. The <em>score</em> carries it.",
      "containsSpoilers": false
    },
    "rating": 4.5,
    "like": true,
    "tags": ["70mm", "rewatch2026"],
    "commentPolicy": "Anyone",
    "privacyPolicy": "Anyone"
  }'
```

| Field | Type | Notes |
|---|---|---|
| `filmId` **required** | string | The film LID. A wrong LID returns `404`. |
| `diaryDetails.diaryDate` **required in the block** | date | `YYYY-MM-DD`. The date the member watched the film. |
| `diaryDetails.rewatch` | boolean | `true` if the member saw the film before this date. |
| `review.text` **required in the block** | string | LBML. Maximum 100,000 characters. Permitted tags: `<br>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<a href="">`, `<blockquote>`. |
| `review.containsSpoilers` | boolean | `true` if the text spoils the plot. |
| `rating` | number | `0.5` to `5.0` in steps of `0.5`. |
| `like` | boolean | The heart. A member may not like their own review. |
| `tags` | string[] | Plain tag text. The response returns `tags2` with the generated codes. |
| `commentPolicy` | enum | `Anyone`, `Friends` or `You`. `You` means the owner only. |
| `privacyPolicy` | enum | `Anyone`, `Friends`, `You` or `Draft`. |

Send `diaryDetails`, or `review`, or both. The API rejects a body with neither. Note the wording of `like`: the request schema describes it as a like on the review, while the response describes it as the like status for this viewing. It is the one heart on the entry.

The response is `LogEntryCreationResponse`: the new `FilmLogEntry` plus an optional `videoMessage` to show the member. Keep `id` from the response, because every later call needs it.

## 6. PATCH /log-entry/{id} – partial update

Scopes: `user` and `content:modify`. Body: `LogEntryUpdateRequest`. A `403` means the entry belongs to another member.

Three rules govern this body:

1. **Omit a field to keep it.** The API does not touch a field you do not send.
2. **Send `null` to remove it.** `rating`, `tags`, `like`, `commentPolicy`, `privacyPolicy`, `diaryDetails` and `review` all accept `null`.
3. **Send a partial block to patch it.** `diaryDetails` and `review` accept their own partial objects, so `{"review": {"containsSpoilers": true}}` keeps the existing text.

Change only the rating:

```bash
curl -X PATCH "https://api.letterboxd.com/api/v0/log-entry/8UxL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -d '{ "rating": 3.5 }'
```

| Goal | Do this | Do not do this |
|---|---|---|
| Remove the rating | `{ "rating": null }` | `{ "rating": 0 }` – `0` is not a valid rating. |
| Remove the review, keep the diary entry | `{ "review": null }` | `{ "review": { "text": "" } }` – the API answers `ReviewWithNoText`. |
| Flag spoilers on an existing review | `{ "review": { "containsSpoilers": true } }` | `{ "review": { "text": "<stale copy>", "containsSpoilers": true } }` – a full block overwrites the text. |
| Take the entry out of the diary | `{ "diaryDetails": null }` | `{ "diaryDetails": { "diaryDate": null } }` – a date-only removal leaves an empty diary block. |
| Move the watch date | `{ "diaryDetails": { "diaryDate": "2026-08-12" } }` | A `DELETE` and a new `POST` – that loses the comments and the likes. |
| Add one tag | `{ "tags": ["70mm", "imax"] }`, the complete list | `{ "tags": ["imax"] }` – the array replaces the whole set. |

Remove `diaryDetails` only when the entry has a review. An entry with neither block is invalid, and the API answers with `LogEntryWithNoReviewOrDiaryDetails`. Delete the entry instead. `tags` replaces the whole set, so send the complete list every time, and send `[]` or `null` to clear it.

The response is `LogEntryUpdateResponse`: `data` (the updated `FilmLogEntry`), an optional `videoMessage` and a `messages` array. Read `messages` on every update. Each message has `type` (`Error` or `Success`), a human-readable `title` and a `code`:

`InvalidRatingValue`, `InvalidDiaryDate`, `ReviewWithNoText`, `ReviewIsTooLong`, `ModerationReviewText`, `LogEntryWithNoReviewOrDiaryDetails`.

`ModerationReviewText` means a moderator holds the text. The entry still exists. Show the message to the member.

### DELETE /log-entry/{id}

Scopes: `user` and `content:modify`. The path takes the log entry LID. No body is necessary.

```bash
curl -X DELETE "https://api.letterboxd.com/api/v0/log-entry/8UxL" \
  -H "Authorization: Bearer $TOKEN"
```

Success returns `204` with no body. A `403` means you may not delete this entry, usually because another member owns it. A `404` means the LID is unknown.

The delete removes the diary entry, the review, the rating, the tags, the comments and the likes. They are all parts of one object. You cannot undo it. Confirm with the member first. To keep the entry and drop only one part, use `PATCH` with a `null` field instead.

## 7. PATCH /log-entry/{id}/me versus PATCH /log-entry/{id}

These two paths differ by one segment. They do different things.

| Task | Endpoint | Whose content |
|---|---|---|
| Edit your own entry, review, rating or tags | `PATCH /log-entry/{id}` | Yours only. Another member's entry returns `403 Not your log entry`. |
| Like another member's review | `PATCH /me/like/{id}` | Anybody's. |
| Subscribe to the comments on a review | `PATCH /me/subscribe/{id}` | Anybody's. |
| Rate a film with no diary entry and no review | `PATCH /me/rate/{id}` with the **film** LID | Yours. It also marks the film watched. |

`PATCH /log-entry/{id}/me` is **DEPRECATED**. It still accepts `ReviewRelationshipUpdateRequest`:

```json
{ "liked": true, "subscribed": true }
```

It returns `ReviewRelationshipUpdateResponse` with `data` (the new `ReviewRelationship`) and `messages`. The message codes explain a refusal: `LikeOwnReview`, `LikeBlockedContent`, `LikeRemovedReview`, `LikeLogEntryWithoutReview`, `LikeRateLimit`, `SubscribeWhenOptedOut`, `SubscribeToContentYouBlocked`, `SubscribeToBlockedContent`.

Write new code against the replacements. Both return `204` and take a one-field body:

```bash
# Like a review. The id is the log entry LID.
curl -X PATCH "https://api.letterboxd.com/api/v0/me/like/8UxL" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "liked": true }'

# Subscribe to the comment notifications for the same review.
curl -X PATCH "https://api.letterboxd.com/api/v0/me/subscribe/8UxL" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{ "subscribed": true }'
```

A member may not like their own review. `subscribed: true` has no effect when the member disabled comment notifications in their account settings. See `me.md`.

## 8. Comments and reports

`POST /log-entry/{id}/comments` creates a comment on the review. Scopes: `user` and `content:modify`.

```bash
curl -X POST "https://api.letterboxd.com/api/v0/log-entry/8UxL/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -d '{ "comment": "The <em>score</em> is the best part. Agreed." }'
```

The `comment` field takes LBML with the same tag set as a review, up to 100,000 characters. The response is a `ReviewComment`. A `403` means the member may not comment here. Call `GET /log-entry/{id}/me` first and check `commentThreadState`. A log entry with no review is not commentable, because `commentable` depends on review text and on the owner's comment policy.

`POST /log-entry/{id}/report` reports the review. It returns `204` with no body.

```json
{ "reason": "Plagiarism", "message": "This copies a published review word for word." }
```

`reason` accepts `Abuse`, `Spoilers`, `Spam`, `Plagiarism` or `Other`. `message` is required when the reason is `Plagiarism` or `Other`. Otherwise it is optional.

## 9. The rating scale

The API uses a number between `0.5` and `5.0` in steps of `0.5`. Ten values are valid. There is no zero.

| API value | Star display | API value | Star display |
|---|---|---|---|
| `0.5` | ½ | `3.0` | ★★★ |
| `1.0` | ★ | `3.5` | ★★★½ |
| `1.5` | ★½ | `4.0` | ★★★★ |
| `2.0` | ★★ | `4.5` | ★★★★½ |
| `2.5` | ★★½ | `5.0` | ★★★★★ |

The number of full stars is `Math.floor(rating)`. A half star follows when `rating * 2` is odd. An absent `rating` field means the member gave no rating. Send `null` to remove a rating. Never send `0`, and never treat an absent rating as `0` in an average.

`minRating` and `maxRating` accept the same ten values. Use `where=Rated` and `where=NotRated` when you do not care about the value.

Do not confuse two different numbers. `logEntry.rating` is one member's rating on the half-star scale. `film.rating` is the weighted average of all members, so it holds more decimals, for example `4.23`. It appears only when the film has enough ratings. Show the average with two decimals. Do not round it to a half step.

`ProductionRelationship.derivedRating` marks a rating that Letterboxd derived rather than the member entered.

## 10. Pitfalls

**Rewatch is a flag, not a calculation.** `rewatch` lives inside `diaryDetails`. Set it to `true` when the member saw the film before this diary date. The API does not compute it from your other entries. A review with no `diaryDetails` cannot record a rewatch at all.

**The diary date and the published date are different fields.** `diaryDetails.diaryDate` is a plain date with no time and no timezone. It is the day the member watched the film. `whenCreated` and `whenUpdated` are UTC timestamps of the database record. `review.whenReviewed` is the publish time of the review text. `sort=Date` uses the diary date. `sort=WhenAdded` uses the creation time. Add `where=HasDiaryDate` to `year`, `month`, `week` and `day` queries, because an entry with no diary date has no date to filter on.

**A rating is not a diary entry, and a review is not a diary entry.** Log a viewing with `diaryDetails`. Publish text with `review`. Rate a film on its own with `PATCH /me/rate/{id}`.

**Respect the spoiler flags.** `containsSpoilers` is the owner's flag. `spoilersLocked` means a moderator locked it, so an update will not change it. Hide the text behind a control when `containsSpoilers` is `true`. Use `where=NoSpoilers` when you show reviews in a public feed.

**Render `text`, edit `lbml`.** `review.text` is HTML for display. `review.lbml` is the source you send back in an update. `moderated: true` means a moderator removed the review. `originalLbml` may hold the text from before the moderation.

**Translation changes the payload.** `preferredLanguage` returns a translation when one is possible. Check `translatedBy` (`Original` or `Google`), `originalLanguageCode`, `languageCode` and `truncated`. A long review can arrive truncated, because the translation service has a limit.

**All writes need `content:modify`.** Every `POST`, `PATCH` and `DELETE` in this group needs the `user` and `content:modify` scopes. The Client Credentials flow cannot get them, so use the Authorization Code flow for any write. See `authentication.md`.

**Pagination stops at 100,000 objects.** Every cursored window has this cap. Split a large query by `year` and `month`, or by `film`, to reach the rest. Always follow the `next` cursor. There is no offset parameter, and `perPage` cannot go above `100`.

**Drafts appear in your own results.** A draft has `privacyPolicy: "Draft"`. Add `where=NoDrafts` when you build a public view. `privacyPolicy` on the response is the effective policy. `configuredPrivacyPolicy` appears only for the owner, and holds the value the owner set on this entry.

**Use tag codes, not tag text.** The response field `tags` is **DEPRECATED**. Read `tags2`, which holds `code` and `displayTag`. The filters `tagCode`, `includeTags` and `excludeTags` take the code. Use `GET /me/check-tag` to convert display text into a code. See `me.md`.

**Read `403` in context.** On `GET /log-entries` a `403` means the signed-in member may not view those entries. On `PATCH /log-entry/{id}` a `403` means the entry belongs to somebody else.

**`DELETE /log-entry/{id}` cannot be undone.** It returns `204` with no body. Confirm with the member first.

**Watch the sort constraints.** With `film`, only `WhenAdded`, `Date`, `EntryRating*` and `ReviewPopularity*` work. Never send `film` with `FilmName`, `ReleaseDate*`, `FilmDuration*` or `FilmPopularity*`. The `MemberRating*` sorts need `member` and `includeFriends=None`. The `AuthenticatedMember*` and `*WithFriends` sorts need a signed-in member.

**Shrink the response when you can.** Each entry embeds a `FilmSummary` with a `relationships` array. Set `excludeMemberFilmRelationships=true` when you do not need it. The payload becomes much smaller.

## 11. First Party markers

This endpoint group has no First Party endpoint and no First Party query parameter. Three response fields carry the **FIRST PARTY** mark, so a third-party client must not depend on them: `posterPickerUrl` and `targeting` on the log entry, and `posterPickerUrl` on the embedded `film`. `backdrop` and `backdropFocalPoint` are not First Party, but the API returns them only for Patron members.

## 12. Relationships

- `overview.md` – the base URL, the LID concept, cursor pagination and the 100,000-object cap.
- `authentication.md` – the OAuth2 flows, the `user` and `content:modify` scopes, and token refresh.
- `films.md` – film LIDs, `FilmSummary`, genres, services and film statistics with the rating histogram.
- `me.md` – `PATCH /me/like/{id}`, `PATCH /me/subscribe/{id}`, `PATCH /me/rate/{id}`, `PATCH /me/watch/{id}` and the tag endpoints.
- `members.md` – member LIDs, `MemberSummary`, friends, and the member activity feed that reports `DiaryEntryActivity` and `ReviewActivity`.
- `stories-and-comments.md` – the shared comment model, `CommentThreadState`, comment updates and report reasons.
