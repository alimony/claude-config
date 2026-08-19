# Letterboxd API: Lists
Based on Letterboxd API v0 documentation.

A list is a member-curated, ordered collection of films. Every list has an LID, a version number, a share policy and a comment policy. Entries hold a film, an optional rank, and optional notes.

All paths start at `https://api.letterboxd.com/api/v0`. Send `Authorization: Bearer $TOKEN` on every request. If your client cannot send PATCH, send POST with the header `X-HTTP-Method-Override: PATCH`.

## Quick reference

| Method and path | Purpose | Scopes | Response |
|---|---|---|---|
| `GET /lists` | Query many lists | oauth2 | `ListsResponse` |
| `GET /lists/topics` | Featured topics and their lists | oauth2 | `TopicsResponse` |
| `GET /list/report-reasons` | Report reason metadata | oauth2 | `ReportReasonMetadataResponse` |
| `GET /list/{id}` | One list | oauth2 | `List` |
| `GET /list/{id}/entries` | Cursored entries with film filters | oauth2 | `ListEntriesResponse` |
| `GET /list/{id}/statistics` | Comment and like counts | oauth2 | `ListStatistics` |
| `GET /list/{id}/comments` | Cursored comments | oauth2 | `ListCommentsResponse` |
| `GET /list/{id}/me` | Your relationship with the list | `user` | `ListRelationship` |
| `POST /lists` | Create a list | `user`, `content:modify` | `ListCreateResponse` |
| `PATCH /list/{id}` | Update one list | `user`, `content:modify` | `ListUpdateResponse` |
| `PATCH /lists` | Add films to many lists | `user`, `content:modify` | `ListAdditionResponse` |
| `DELETE /list/{id}` | Destroy your list | `user`, `content:modify` | 204 |
| `POST /list/{id}/forget` | Drop a shared list from your view | `user`, `content:modify` | 204 |
| `PATCH /list/{id}/me` | Like or subscribe | `user`, `content:modify` | `ListRelationshipUpdateResponse` |
| `POST /list/{id}/comments` | Post a comment | `user`, `content:modify` | `ListComment` |
| `POST /list/{id}/report` | Report a list | `user`, `content:modify` | 204 |

Read endpoints work with a Client Credentials token. Write endpoints and `/me` need an Authorization Code token from a signed-in member.

## GET /lists

`GET /lists` is a cursored window over lists. Use the `next` cursor from the response to get the following page.

### Core parameters

| Parameter | Type | Notes |
|---|---|---|
| `cursor` | string | The pagination cursor from the previous response. |
| `perPage` | int32 | Default `20`, maximum `100`. |
| `sort` | enum | Default `Date`. See the sort table. |
| `film` | string | Film LID. Returns lists that contain the film. |
| `clonedFrom` | string | List LID. Returns lists cloned from that list. |
| `where` | enum[] | Repeatable. See the where table. |
| `filter` | enum[] | Only `NoDuplicateMembers`. Keeps the first list per member. |
| `filmsOfNote` | string[] | Film LIDs. Reports each film's rank in each returned list. |
| `excludeMemberFilmRelationships` | boolean | Set `true` to make the response smaller. |

`filter=NoDuplicateMembers` works only with `sort=Date`, `sort=WhenPublishedLatestFirst` or `sort=WhenCreatedLatestFirst`. Other sort orders return a 400.

### Member filters

| Parameter | Type | Notes |
|---|---|---|
| `member` | string | Member LID. |
| `memberRelationship` | `ListMemberRelationship` | Default `Owner`. Also `Liked` and `Accessed`. |
| `includeFriends` | `IncludeFriends` | Default `None`. Also `All` and `Only`. |

`memberRelationship=Owner` returns lists the member created. `Liked` returns lists the member hearted. `Accessed` returns shared lists the member has opened. Always send `member` with `memberRelationship` and with `includeFriends`.

### Tag filters

| Parameter | Type | Notes |
|---|---|---|
| `tagCode` | string | One tag code. Prefer this over the deprecated `tag`. |
| `includeTags` | string[] | Lists must carry all these tag codes. |
| `excludeTags` | string[] | Lists must carry none of these tag codes. |
| `tagger` | string | Member LID. Restricts the tag filter to that tagger. |
| `includeTaggerFriends` | `IncludeFriends` | Default `None`. Use with `tagger`. |

A tag code is not the tag text. Read `tags2[].code` from a `List` to get a usable code, and `tags2[].displayTag` to show the text.

### where clauses (ListWhereClause)

| Value | Effect |
|---|---|
| `Clean` | Only lists without profane language. |
| `Published` | Only the member's public lists. |
| `NotPublished` | Only the authenticated member's unpublished lists. |
| `NotPublishedOrShared` | Unpublished lists that the member has not shared. |
| `SharedAnyone` | Lists shared with anyone. |
| `SharedFriends` | Lists shared with friends. |
| `Owned` | Lists owned by the member. |
| `Customized` | Lists with custom presentation. |

Repeat the parameter to combine clauses, for example `where=Clean&where=Published`. Private lists of other members never appear. `where=NotPublished` returns a 403 if the authenticated member does not own the target. The endpoint text documents `Clean`, `Published` and `NotPublished` only; the other five values come from the enum and are not described there.

### Sort options

| Group | Values |
|---|---|
| Recency | `Date` (default), `WhenPublishedLatestFirst`, `WhenPublishedEarliestFirst`, `WhenCreatedLatestFirst`, `WhenCreatedEarliestFirst`, `WhenAccessedLatestFirst`, `WhenAccessedEarliestFirst` |
| Member action | `WhenLiked` |
| Name | `ListName` |
| Popularity | `ListPopularity`, `ListPopularityThisWeek`, `ListPopularityThisMonth`, `ListPopularityThisYear` |
| Friend popularity | `ListPopularityWithFriends`, `ListPopularityWithFriendsThisWeek`, `ListPopularityWithFriendsThisMonth`, `ListPopularityWithFriendsThisYear` |

`Date` returns the most recently created or updated lists first. The `*WithFriends` values need a signed-in member.

### Example: a member's own published lists

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/lists?member=8Ur&memberRelationship=Owner&where=Published&sort=WhenCreatedLatestFirst&perPage=100"
```

### Example: popular lists that contain a film

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/lists?film=b8wK&sort=ListPopularityThisYear&where=Clean&filter=NoDuplicateMembers&perPage=50"
```

`filter=NoDuplicateMembers` is invalid with `ListPopularityThisYear`. Drop the filter, or change the sort to `Date`.

### Example: ranked lists on a topic

`GET /lists` has no `topic` parameter. Topics come only from `GET /lists/topics`. To approximate a topic query, filter by tag code and then keep the lists whose `ranked` field is `true`.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/lists?tagCode=horror&sort=ListPopularity&perPage=100" \
  | jq '[.items[] | select(.ranked == true) | {id, name, filmCount, owner: .owner.displayName}]'
```

No server-side filter for ranked lists exists. Filter on `ranked` in your own code.

### Example: does each list contain my films?

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/lists?member=8Ur&filmsOfNote=b8wK&filmsOfNote=2b9s"
```

Each `ListSummary` then carries `entriesOfNote`, an array of `ListEntryOccurrence`. Each occurrence gives `filmId` and `rank`. A `rank` of `-1` means the list does not contain that film.

## GET /list/{id}

Returns the full `List` object. Important fields: `id`, `name`, `version`, `filmCount`, `published`, `ranked`, `hasEntriesWithNotes`, `sharePolicy`, `commentPolicy`, `tags2`, `owner`, `collaborators`, `clonedFrom`, `whenUpdated` and `statsFreelyAvailable`. `description` is HTML and `descriptionLbml` is LBML.

`previewEntries` holds the first 12 entries only, and it omits entry notes. Call `/list/{id}/entries` for more than 12 entries or for notes. `backdropPickerUrl` is **First Party**.

Keep the `version` value. You need it for a safe `PATCH /list/{id}`.

## GET /list/{id}/entries

Returns `ListEntriesResponse`: `items` (`ListEntry[]`), `next`, `itemCount`, `metadata` (`totalFilmCount` and `filteredFilmCount`) and `relationships`.

Each `ListEntry` gives `entryId`, `rank`, `production`, `whenAdded`, `notes`, `notesLbml` and `containsSpoilers`. The `film` field is deprecated; read `production` instead. `posterPickerUrl` and `backdropPickerUrl` are **First Party**.

Pagination: `cursor`, `perPage` (default `20`, maximum `100`).

The endpoint accepts the full film filter set: `genre`, `includeGenre`, `excludeGenre`, `country`, `language`, `decade`, `year`, `service`, `availabilityType`, `exclusive`, `unavailable`, `includeOwned`, `negate`, `where` (`FilmWhereClause[]`), `member`, `memberRelationship`, `includeFriends`, `memberMinRating`, `memberMaxRating`, `tagCode`, `includeTags`, `excludeTags`, `tagger`, `includeTaggerFriends`, `position` and `excludeMemberFilmRelationships`. The `filmId` and `tag` parameters are deprecated.

These filters are **First Party**: `similarTo`, `theme`, `minigenre`, `nanogenre`.

`sort` defaults to `ListRanking`, which is the owner's own order. Other values include `WhenAddedToList`, `WhenAddedToListEarliestFirst`, `Shuffle`, `FilmName`, `OwnerRatingHighToLow`, `AverageRatingHighToLow`, `ReleaseDateLatestFirst`, `FilmDurationShortestFirst` and `FilmPopularity`. The `AuthenticatedMember*` values need a signed-in member. The `MemberRating*` values need `member` and `includeFriends=None`. The `Rating*` values are deprecated in favour of `AverageRating*`. `FilmPopularityThisWeek`, `FilmPopularityThisMonth` and `FilmPopularityThisYear` are deprecated and have never worked.

The `sort` parameter changes your view only. It does not change the stored order. Use a `SORT_*` entry action to change the stored order.

```bash
# Get watched films from a list, 100 per page.
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.letterboxd.com/api/v0/list/1Ndg/entries?perPage=100&member=8Ur&memberRelationship=Watched"
```

## GET /list/{id}/statistics

Returns `ListStatistics` with `list.id` and `counts.comments` and `counts.likes`. The list `statsFreelyAvailable` field tells you if all members can see these numbers.

## GET /list/{id}/comments

A cursored window over `ListComment` objects. Parameters: `cursor`, `perPage` (maximum `100`), `sort` (`CommentsSort`: `Date`, `DateLatestFirst`, `Updates`) and `includeDeletions`.

Use `sort=Updates` with `includeDeletions=true` to sync a comment cache. `Updates` returns the newest content first, and the deletions keep your cache correct. If the list owner blocked the commenter, `blockedByOwner` is `true` and the `comment` field is absent.

## GET /list/{id}/me

Needs the `user` scope. Returns `ListRelationship`: `liked`, `subscribed`, `subscriptionState` (`CommentSubscriptionState`), `commentThreadState` (`CommentThreadState`) and `privateNote`.

Check `commentThreadState` before you show a comment box. Only `CanComment` permits a post. `Banned`, `Blocked`, `BlockedThem`, `Closed`, `FriendsOnly`, `Moderated`, `NotCommentable` and `NotValidated` all forbid it.

## POST /lists

Creates a list. Send a `ListCreationRequest`. `name`, `published` and `ranked` are required.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/lists \
  -d '{
    "name": "Neo-noir after 1990",
    "published": true,
    "ranked": true,
    "sharePolicy": "Anyone",
    "commentPolicy": "Friends",
    "description": "Rain, neon and bad decisions. <strong>Ranked</strong>, argue below.",
    "tags": ["neo-noir", "1990s"],
    "entries": [
      { "film": "b8wK", "notes": "The rain never stops.", "containsSpoilers": false },
      { "film": "2b9s", "notes": "Best third act of the decade.", "containsSpoilers": true },
      { "film": "1cVj" }
    ]
  }'
```

Rules for the body:

- `description` takes LBML with `<br>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<a href="">` and `<blockquote>`. The maximum size is 100,000 characters.
- `entries` uses `ListUpdateEntry` objects. Order in the array sets the initial order. Omit `action` on create; each entry is an add.
- `notes` also takes LBML and also caps at 100,000 characters.
- `clonedList` copies another list first, then applies your `entries`. Only paying members may clone. `clonedFrom` is deprecated.
- `tags` takes the tag text, not tag codes.

The response is `ListCreateResponse` with `data` (a `List`) and `messages`. Read `messages` even on a 200. Codes include `ListNameTooLong`, `ListNameIsBlank`, `ListNameForbidden`, `UnknownFilmCode`, `DuplicateEntry`, `DuplicateRank`, `EmptyPublicList`, `ListDescriptionIsTooLong`, `ListEntryNotesTooLong`, `CannotBePublic` and `CloneSourceNotFound`.

## PATCH /list/{id}

This endpoint edits your own list. It sends a `ListUpdateRequest`. Send only the fields you want to change.

Top-level fields: `version`, `name`, `published`, `ranked`, `description`, `tags`, `commentPolicy`, `sharePolicy` and `entries`. `filmsToRemove` is deprecated; send `DELETE` actions instead.

### The entries collection is a list of actions, not the list content

This is the most important rule on the page. `entries` is a set of edit commands. The server applies each command to the stored list. The server does not compare your array against the list. Any entry you do not mention stays exactly as it is.

Each item is a `ListUpdateEntry`:

| Field | Meaning |
|---|---|
| `action` | `ADD`, `DELETE`, `UPDATE`, `CLEAR` or a `SORT_*` value. |
| `film` | Film LID. Required for `ADD`. |
| `position` | Zero-based index of the existing entry. Required for `UPDATE` and `DELETE`. |
| `newPosition` | Zero-based target index for an added or updated entry. |
| `notes` | Entry notes in LBML, maximum 100,000 characters. |
| `containsSpoilers` | Set `true` if the notes spoil the film. |
| `rank` | **Deprecated.** One-based rank. Use `newPosition` instead. |

Action semantics:

- `ADD` inserts the film. Without `newPosition` the film goes to the end.
- `DELETE` removes the entry at `position`.
- `UPDATE` changes the entry at `position`. Without `newPosition` the entry keeps its place.
- `CLEAR` removes every entry in the list.
- `SORT_*` re-orders the whole stored list. Values: `SORT_NAME`, `SORT_DIARY_NEWEST`, `SORT_DIARY_OLDEST`, `SORT_RELEASE_NEWEST`, `SORT_RELEASE_OLDEST`, `SORT_RATING_HIGHEST`, `SORT_RATING_LOWEST`, `SORT_AVR_RATING_HIGHEST`, `SORT_AVR_RATING_LOWEST`, `SORT_LENGTH_SHORTEST`, `SORT_LENGTH_LONGEST`.
- If you omit `action`, the server updates an existing entry for that film, or adds the film if the list does not hold it.

`position` and `newPosition` count from 0. The deprecated `rank` counts from 1. Do not mix the two in one request.

### Append films to a large list

This request adds three films to the end of a 4,000 film list. It touches nothing else.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/list/1Ndg \
  -d '{
    "version": 47,
    "entries": [
      { "action": "ADD", "film": "b8wK" },
      { "action": "ADD", "film": "2b9s", "notes": "Added for the July theme." },
      { "action": "ADD", "film": "1cVj", "containsSpoilers": false }
    ]
  }'
```

The other 4,000 entries keep their positions, notes, entry IDs and `whenAdded` values. You never send them.

### Remove, move and annotate entries

Warning: the docs do not define whether later `position` values in one request count before or after the earlier actions. Keep mixed batches small, or send deletions in one request and moves in the next.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/list/1Ndg \
  -d '{
    "version": 48,
    "name": "Neo-noir after 1990 (revised)",
    "entries": [
      { "action": "DELETE", "position": 12 },
      { "action": "DELETE", "position": 5 },
      { "action": "UPDATE", "position": 0, "newPosition": 3 },
      { "action": "UPDATE", "position": 1, "notes": "Moved up after a rewatch.", "containsSpoilers": true },
      { "action": "ADD", "film": "9xQm", "newPosition": 0 }
    ]
  }'
```

Note the delete order. Position 12 goes first, then position 5. Each delete shifts every later entry up by one. Each insert shifts every later entry down by one.

### Do this / Do not do this

Do this. Send only the changed entries, and keep `version` from the last `GET /list/{id}`.

```json
{ "version": 47, "entries": [ { "action": "ADD", "film": "b8wK" } ] }
```

Do not do this. Do not send the whole desired list and expect the server to drop the films you left out.

```json
{ "entries": [ { "film": "b8wK" }, { "film": "2b9s" } ] }
```

That request is not a replace. It adds or updates those two films and leaves the other 4,000 in place. Worse, without `action` the server treats each item as an add-or-update, so a partial array silently grows the list.

Do this. Delete entries from the highest position to the lowest position.

```json
{ "entries": [ { "action": "DELETE", "position": 12 }, { "action": "DELETE", "position": 5 } ] }
```

Do not do this. Do not delete from the lowest position first, because the indices move.

```json
{ "entries": [ { "action": "DELETE", "position": 5 }, { "action": "DELETE", "position": 12 } ] }
```

Do not do this either. Do not send `CLEAR` and then re-add every film to force a sync.

```json
{ "entries": [ { "action": "CLEAR" }, { "action": "ADD", "film": "b8wK" } ] }
```

`CLEAR` destroys every entry ID, every note and every `whenAdded` timestamp. A failure in the middle leaves a truncated list. Compute a real diff instead, and send only `ADD`, `DELETE` and `UPDATE` actions.

### Version collisions

Read `version` from the list, then send it back in the update. If another client changed the list first, the response carries the message code `ListVersionMismatch`. Re-read the list, rebuild the actions, and retry. Omitting `version` disables this protection.

### Response

`ListUpdateResponse` returns `data` (the updated `List`) and `messages`. A 200 can still carry error messages. Codes include `ListVersionMismatch`, `MissingEntry`, `InvalidEntry`, `DuplicateEntry`, `DuplicateRank`, `UnknownFilmCode`, `ListModerated`, `EmptyPublicList`, `CannotSharePrivateList`, `SharingServiceNotAuthorized`, `InvalidItemForList` and `CannotBePublic`. A 403 means the list is not yours.

## PATCH /lists

`PATCH /lists` adds films to many lists at once. It sends a `ListAdditionRequest` with `lists` (list LIDs) and `films` (film LIDs). Each film goes to the end of each list.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/lists \
  -d '{ "lists": ["1Ndg", "2Fk1", "7Qaa"], "films": ["b8wK", "2b9s"] }'
```

The response is `ListAdditionResponse` with an `items` array of `ListAddition`. Each item gives `list.id`, `additions` (a count) and `itemsAdded` (the LIDs that went in). Compare `itemsAdded` against your input to find films the list already held.

Choose between the two endpoints as follows:

- Use `PATCH /lists` for a plain "add these films to these lists" action. It saves one round trip per list.
- Use `PATCH /list/{id}` when you need notes, positions, deletions, sorting, a version check, or any change to the list metadata.

`PATCH /lists` cannot set notes, cannot set a position, and cannot remove anything. It returns 403 if you do not own every list in the request, and 404 if any list is missing.

## DELETE /list/{id} and POST /list/{id}/forget

These two look similar and do very different things.

| | `DELETE /list/{id}` | `POST /list/{id}/forget` |
|---|---|---|
| Effect | Destroys the list for everybody | Removes the list from your own view |
| Who may call it | The owner only | Any member who has accessed the shared list |
| Effect on the owner | The list is gone | Nothing changes |
| Reversible | No | Yes, open the share link again |
| Errors | 403 if not yours, 404 if missing | 404 if missing |

`DELETE` is permanent. Ask the member to confirm before you call it.

`forget` clears the `Accessed` relationship. After a forget, the list stops appearing in `GET /lists?member={me}&memberRelationship=Accessed`. Use it for a "remove from my recently viewed lists" control.

Both return 204 on success. Both need `user` and `content:modify`.

## PATCH /list/{id}/me

This endpoint edits your relationship with someone else's list. It never edits the list content.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/list/1Ndg/me \
  -d '{ "liked": true, "subscribed": true }'
```

Both fields are nullable booleans. Omit a field to leave it unchanged. A member cannot like their own list. A `subscribed` value of `true` is ignored if the member turned off comment notifications in account settings.

The response is `ListRelationshipUpdateResponse` with `data` (a `ListRelationship`) and `messages`. Message codes include `LikeOwnList`, `LikeBlockedContent`, `LikeRateLimit`, `SubscribeWhenOptedOut`, `SubscribeToBlockedContent` and `SubscribeToContentYouBlocked`.

Compare the two PATCH endpoints:

- `PATCH /list/{id}` edits the list itself. Only the owner may call it.
- `PATCH /list/{id}/me` edits your like and your comment subscription. Any member may call it.

## Comments and reports

### POST /list/{id}/comments

Send a `CommentCreationRequest` with a single `comment` field in LBML, maximum 100,000 characters.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/list/1Ndg/comments \
  -d '{ "comment": "Great picks. <em>Chungking Express</em> belongs here too." }'
```

Check `commentThreadState` from `GET /list/{id}/me` first. A post into a closed thread returns 403.

### POST /list/{id}/report

Send a `ReportListRequest`. `reason` is required and takes `Abuse`, `Spoilers`, `Spam`, `Plagiarism` or `Other`. `message` is required when the reason is `Plagiarism` or `Other`.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.letterboxd.com/api/v0/list/1Ndg/report \
  -d '{ "reason": "Plagiarism", "message": "Copied entry notes from another list." }'
```

Success returns 204.

### GET /list/report-reasons

Returns `ReportReasonMetadataResponse` with an `items` array. Each `ReportReasonMetadata` gives `reason`, `code`, `priority`, `descriptionHtml` and `messageRequired`. Note the singular `/list/` in the path.

Build your report picker from this endpoint. Sort by `priority`, low values first. Use `messageRequired` to decide if the message box is mandatory. Do not hard-code the five reason values.

## GET /lists/topics

Returns `TopicsResponse` with an `items` array of `ListTopic`. Each topic gives a `name` and an `items` array of `ListSummary`. Letterboxd uses this feed for the Browse tab of its own apps.

The endpoint takes no parameters and no pagination. It is a curated feed, not a query. To go deeper on a topic, take the list LIDs from `items` and call `GET /list/{id}/entries`.

## Privacy and sharing

Three enums control access. They share value names, so read them carefully. In all three, `You` means the content owner, never the reader.

| Value | `SharePolicy` – who can open the list | `CommentPolicy` – who can post comments |
|---|---|---|
| `Anyone` | Any member or visitor can open it. | Any member can comment. |
| `Friends` | Only members the owner follows can open it. | Only members the owner follows can comment. |
| `You` | Only the owner can open it. | Only the owner can comment, so the thread is closed. |

`SharePolicy` is required on a `List` and optional on create and update. `CommentPolicy` is optional in both places, and it is nullable on update.

`PrivacyPolicy` adds a fourth value, `Draft`, which hides the content from everybody. Lists do not use `PrivacyPolicy`; they use the separate `published` boolean for the draft state.

Do not read `commentPolicy` to decide if the current member can comment. Read `commentThreadState` from `GET /list/{id}/me` instead. The policy describes the owner's setting; the thread state accounts for blocks, bans and moderation as well.

`published` and `sharePolicy` interact. A public list needs at least one entry, or the API returns `EmptyPublicList`. A private list cannot be shared to an external service, which returns `CannotSharePrivateList`.

## Pitfalls

**Ranked and unranked lists.** `rank` appears on a `ListEntry` only when the list has `ranked: true`. An unranked list still has a stored order; read it with the default `sort=ListRanking`. Two entries with the same rank return `DuplicateRank`. Switch a list to ranked by sending `{"ranked": true}` in a `PATCH /list/{id}`.

**Duplicate entries.** The API rejects the same film twice in one list with `DuplicateEntry`. Treat the film LID as unique inside a list. `ListEntryOccurrence` therefore returns one `rank` per film, and `-1` when the film is absent. Request the data with `filmsOfNote`, but read it back from the `entriesOfNote` field; the names differ.

**Address entries by position, not by film.** Use `entryId` from `GET /list/{id}/entries` to track an entry across reads. Use `position` in an update, because that is the only addressing the write API accepts. Re-read the positions after any write that changes the length.

**The 100,000 object pagination cap.** Cursor pagination stops after 100,000 objects. A very large query cannot be walked to the end. Narrow the query with filters instead of paging further.

**Paginating large list entries.** Set `perPage=100` and follow `next` until the field is absent. Do not compute an offset; the API is cursor-based only. Read `metadata.totalFilmCount` and `metadata.filteredFilmCount` to show progress. Send `excludeMemberFilmRelationships=true` when you do not need the per-member film data; the response gets much smaller.

**Scopes.** Every write needs `user` and `content:modify`. `GET /list/{id}/me` needs `user`. Request `content:modify` in the Authorization Code flow, because `user` and `user:owner` cannot be requested directly. A Client Credentials token can read public lists but can write nothing.

**200 responses that contain errors.** `ListCreateResponse`, `ListUpdateResponse` and `ListRelationshipUpdateResponse` all carry a `messages` array. Check `messages[].type == "Error"` on every success response, and show `messages[].title` to the member.

**Deprecated fields.** Prefer `tags2` over `tags` on responses, `production` over `film` on entries, `tagCode` over `tag`, `newPosition` over `rank`, `clonedList` over `clonedFrom`, `DELETE` actions over `filmsToRemove`, and `index` over `filmId` on the entries endpoint.

**First Party items.** The `similarTo`, `theme`, `minigenre` and `nanogenre` filters on `/list/{id}/entries` are First Party. So are the `backdropPickerUrl` field on `List` and the `posterPickerUrl` and `backdropPickerUrl` fields on `ListEntry`. Third-party clients cannot use them.

## Relationships

- `overview.md` – base URL, LID format, cursor pagination and the 100,000 object cap.
- `authentication.md` – OAuth2 flows, the `content:modify` scope, and token refresh.
- `films.md` – film LIDs, `FilmSummary`, `ProductionSummary` and the shared film filter parameters used by `/list/{id}/entries`.
- `members.md` – member LIDs, `MemberSummary`, and the `member` plus `includeFriends` filters.
- `me.md` – the authenticated member, and member-level relationship endpoints.
- `stories-and-comments.md` – `AbstractComment`, `CommentsSort`, `CommentThreadState` and comment moderation.
