# Letterboxd API: The Authenticated Member (/me)
Based on Letterboxd API v0 documentation.

The `/me` group reads and writes the data of the signed-in member. Every endpoint here needs a member access token. Get that token with the **Authorization Code** flow. The Client Credentials flow gives you no member, so all `/me` calls fail with it.

Base URL: `https://api.letterboxd.com/api/v0`. Send the token in an `Authorization: Bearer TOKEN` header. If your HTTP client cannot send PATCH, send POST with the header `X-HTTP-Method-Override: PATCH`.

**FIRST PARTY** marks an endpoint, a parameter or a field that only Letterboxd's own apps can use. Licensing rules block third-party clients from these. The scope `client:firstparty` cannot be requested.

## Quick reference

| Method and path | Operation ID | Request body | Success | Scopes |
|---|---|---|---|---|
| `GET /me` | `whoAmI` | – | 200 `MemberAccount` | `user` |
| `PATCH /me` | `update` | `MemberSettingsUpdateRequest` | 200 `MemberSettingsUpdateResponse` | `user:owner`, `profile:modify` |
| `PATCH /me/watch/{id}` | `watch` | `WatchUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/rate/{id}` | `rate` | `RateUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/like/{id}` | `like` | `LikeUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/watchlist/{id}` | `watchlist` | `WatchlistUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/subscribe/{id}` | `subscribe` | `SubscribeUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/favorite-films` | `favoriteFilms` | `FavoriteFilmsUpdateRequest` | 204 | `user`, `content:modify` |
| `PATCH /me/favorite-productions` **FIRST PARTY** | `updateFavoriteProductions` | `FavoriteProductionsUpdateRequest` | 204 | `user`, `client:firstparty`, `content:modify` |
| `GET /me/check-tag` | `checkTag` | `TagCheckRequest` | 200 `TagCheckResponse` | `user` |
| `PATCH /me/update-tag` | `updateTag` | `TagUpdateRequest` | 200 (empty) | `user`, `content:modify` |
| `DELETE /me/delete-tag` | `deleteTag` | `TagDeleteRequest` | 204 | `user`, `content:modify` |
| `POST /me/register-push-notifications` **FIRST PARTY** | `registerPushNotifications` | `RegisterPushNotificationsRequest` | 204 | `user`, `client:firstparty` |
| `POST /me/deregister-push-notifications` **FIRST PARTY** | `deregisterPushNotifications` | `DeregisterPushNotificationsRequest` | 204 | `client:firstparty` |
| `POST /me/collect-item` | `collect` | `CollectRequest` | 200 (empty) | `user`, `content:modify` |
| `POST /me/validation-request` **FIRST PARTY** | `validationEmailRequest` | – | 204 | `user:owner`, `client:firstparty` |
| `POST /me/disable` **DESTRUCTIVE** | `disable` | `DisableAccountRequest` | 204 | `user:owner`, `security:modify` |

## GET /me

`GET /me` returns a `MemberAccount`. This is not the public `Member` schema. The public schema sits inside it, in the required `member` property. Read `member` for the username, the display name, the avatar, the bio, the links and the favorite productions.

The scope is `user`. The Authorization Code flow grants `user` automatically. You cannot request it.

`MemberAccount` adds the private state that `Member` never exposes:

| Group | Fields |
|---|---|
| Identity and email | `emailAddress`, `emailAddressValidated` |
| Security | `twoFactorAuthenticationEnabled`, `suspended`, `accountStatus` (`Active` or `Memorialized`) |
| Privacy | `privateAccount`, `includeInPeopleSection`, `privacyPolicy`, `commentPolicy`, `adultContentPolicy`, `posterMode`, `posterModeOptions` |
| Subscription | `hasActiveSubscription`, `subscriptionType` (`apple`, `google` or `paddle`), `membershipDaysRemaining`, `membershipWillAutoRenewViaIAP` |
| Permissions | `capabilities` (an array of enum values) |
| Notifications | all `email*` flags, all `pushNotificationsFor*` flags, `devicesRegisteredForPushNotifications` |
| Ads and other | `hideAds`, `showCustomPostersAds`, `hasVideoStoreSetup`, `campaigns`, `campaignCode`, `genreCategorisation` |

`privateAccount` has an important effect. If it is `true`, the member's content disappears from every API endpoint except `/me`. Do not report an empty profile as a bug before you check this flag.

Read permissions from `capabilities`. The old boolean fields `canComment`, `canCloneLists`, `canChangeAppIcon`, `canFilterActivity`, `canViewListStats`, `canHaveCustomPosters`, `canHaveCustomBackdrops`, `canSeeStoryLikesComments`, `canSeePrivateViewings`, `canAccessVideoStore` and `canSeeShows` are all **deprecated**.

The `capabilities` values are: `CanSeeReviewTranslations`, `CanSeePrivateNotes`, `CanPublishStories`, `CanSeeShows`, `CanAccessVideoStore`, `CanSeePrivateViewings`, `CanSeeStoryLikesComments`, `CanHaveCustomBackdrops`, `CanHaveCustomPosters`, `CanSeeListStats`, `CanFilterActivity`, `CanChangeAppIcon`, `CanCloneLists`, `CanComment`.

```bash
curl -s "https://api.letterboxd.com/api/v0/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

```json
{
  "emailAddress": "member@example.com",
  "emailAddressValidated": true,
  "twoFactorAuthenticationEnabled": false,
  "privateAccount": false,
  "accountStatus": "Active",
  "capabilities": ["CanComment", "CanCloneLists"],
  "member": {
    "id": "4Fd8",
    "username": "example",
    "displayName": "Example Member",
    "memberStatus": "Patron",
    "links": [{ "type": "letterboxd", "id": "4Fd8", "url": "https://letterboxd.com/example/" }]
  }
}
```

- **Do this:** cache the `member.id` from `/me` and reuse it for `/member/{id}/...` calls.
- **Do not do this:** do not cache the whole `MemberAccount`. It holds security state that changes.

## PATCH /me

`PATCH /me` updates the profile and the account settings. The body is a `MemberSettingsUpdateRequest`. Send only the fields that change. The API leaves every omitted field unchanged.

The documented scopes are `user:owner` and `profile:modify`. `user:owner` is automatic and cannot be requested. Request `profile:modify` in the authorization URL. Also request `security:modify` if your app changes the password or the email address, because these are security fields. `security:modify` is the documented scope for `POST /me/disable`.

Profile fields: `givenName`, `familyName`, `pronoun` (the LID from `GET /members/pronouns`), `location`, `website`, `bio` (LBML, max 100,000 characters), `favoriteProductions`, `favoriteFilms` (**deprecated**).

Privacy fields: `privateAccount` and `includeInPeopleSection`.

Policy fields: `privacyPolicy` (`Anyone`, `Friends`, `You`, `Draft`), `commentPolicy` (`Anyone`, `Friends`, `You`), `adultContentPolicy` (`Always` or `Default`), `posterMode` (`All`, `Theirs`, `Yours`, `None`). `Default` means never show adult content.

Security fields: `emailAddress`, `password`, `currentPassword`, `authenticationCode`.

Notification fields: 15 `email*` flags and 14 `pushNotificationsFor*` flags. The names match the `MemberAccount` fields exactly.

Two rules control a password change. Send `currentPassword` with the new `password`. Send `authenticationCode` also, if the member enabled two-factor authentication.

```bash
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "givenName": "Example",
    "location": "Wellington",
    "bio": "I watch <strong>many</strong> films.",
    "privacyPolicy": "Friends",
    "adultContentPolicy": "Default",
    "emailRushes": false,
    "pushNotificationsForComments": true
  }'
```

The 200 response is a `MemberSettingsUpdateResponse`. It has two parts: `data`, the full updated `MemberAccount`, and `messages`, an array your client must show to the user. Each message has a `type` (`Error` or `Success`), a `code` and a human-readable `title`.

The message codes are: `IncorrectCurrentPassword`, `BlankPassword`, `InvalidPassword`, `InvalidEmailAddress`, `EmailAddressInUse`, `InvalidFavoriteFilm`, `InvalidFavoriteProduction`, `BioTooLong`, `InvalidPronounOption`, `InvalidGivenName`, `InvalidFamilyName`.

- **Do this:** read `messages` on every 200 response, and look for `type: "Error"`.
- **Do not do this:** do not treat a 200 status as full success. The API ignores an invalid field and reports it only in `messages`.

## The generic relationship PATCH endpoints

Five endpoints write the member's relationship to one object. They share one shape, so learn them together:

```
PATCH /me/{verb}/{id}
```

Each one takes the LID of a target object in the path. Each one takes a small JSON body with a single field. Each one needs the scopes `user` and `content:modify`. Each one returns **204 No Content** on success, with no body. Each one returns 404 if no object of the correct kind matches the LID.

### Action table

| Action | Endpoint | What `{id}` is | Request body |
|---|---|---|---|
| Mark watched | `PATCH /me/watch/{id}` | A watchable LID: a film, show, season or episode | `{"watched": true}` |
| Mark not watched | `PATCH /me/watch/{id}` | The same | `{"watched": false}` |
| Set a rating | `PATCH /me/rate/{id}` | A rateable LID: a film, show, season or episode | `{"rating": 4.5}` |
| Clear a rating | `PATCH /me/rate/{id}` | The same | `{"rating": null}` |
| Like | `PATCH /me/like/{id}` | A likeable LID: a film, a log entry (review), a list or a story | `{"liked": true}` |
| Unlike | `PATCH /me/like/{id}` | The same | `{"liked": false}` |
| Add to watchlist | `PATCH /me/watchlist/{id}` | A watchlistable LID: a film or other production | `{"inWatchlist": true}` |
| Remove from watchlist | `PATCH /me/watchlist/{id}` | The same | `{"inWatchlist": false}` |
| Subscribe to comments | `PATCH /me/subscribe/{id}` | A commentable LID: a log entry (review), a list or a story | `{"subscribed": true}` |
| Unsubscribe | `PATCH /me/subscribe/{id}` | The same | `{"subscribed": false}` |

### How to clear a value

Only `rating` accepts `null`. Send `{"rating": null}` to remove the rating. For the four other endpoints, send the boolean `false`. `subscribed` also accepts `null`, but `false` is the clear and correct way to unsubscribe.

- **Do this:** `{"rating": null}` to delete a rating.
- **Do not do this:** do not send `{"rating": 0}`. Zero is outside the valid range, and the API answers 403.

### The rating scale

A rating is a number from `0.5` to `5.0`, in steps of `0.5`. This gives ten valid values: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0. These map to the half-star to five-star display on the website. Any other number causes a **403** with the message "Rating must be a number between 0.5 and 5.0, with increments of 0.5."

### Side effects you must expect

A rating implies a watch. If you set a rating, the API also marks the object as watched.

A watch clears the watchlist entry. If you set `watched: true` and the object sits in the watchlist, the API removes it from the watchlist in the same action.

An unwatch can fail. You cannot set `watched: false` while activity exists on the object – a rating, a review or a diary entry. The API answers **409 Conflict**. Delete the activity first, then unwatch.

`{"subscribed": true}` is ignored if the member turned off comment notifications in the account settings. Read `emailComments` and `pushNotificationsForComments` from `GET /me` to explain this to the user.

```bash
# Rate a film 4.5 stars. This also marks the film as watched.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/rate/2bbs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 4.5}'

# Like a review. The id is the log entry LID, not the film LID.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/like/1a2B3c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"liked": true}'

# Add a film to the watchlist.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/watchlist/2bbs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inWatchlist": true}'
```

### The older per-entity endpoints

`PATCH /film/{id}/me` and `PATCH /log-entry/{id}/me` do the same work in one call, but both are **deprecated**. `PATCH /film/{id}/me` takes a `FilmRelationshipUpdateRequest` with `watched`, `liked`, `rating` and `inWatchlist` together. It returns 200 with a `messages` array instead of 204.

Prefer the generic endpoints for new code. `PATCH /list/{id}/me` is not deprecated, because a list relationship also carries subscription and access state.

- **Do this:** send four separate PATCH calls to set watched, rating, like and watchlist.
- **Do not do this:** do not use the deprecated `PATCH /film/{id}/me` for new work.

## Favorites

Two endpoints set the member's favorites, up to a maximum of four items, in display order.

`PATCH /me/favorite-films` takes `{"favoriteFilms": ["LID", ...]}`. The scopes are `user` and `content:modify`.

`PATCH /me/favorite-productions` takes `{"favoriteProductions": ["LID", ...]}`. This endpoint is **FIRST PARTY**. The scopes are `user`, `client:firstparty` and `content:modify`.

Both return 204. Both return 400 for a bad request and 403 if the request is not allowed.

Third-party clients cannot call `PATCH /me/favorite-productions`. They can still set `favoriteProductions` through `PATCH /me`, because that endpoint carries no first-party scope. `PATCH /me` reports a bad LID as an `InvalidFavoriteProduction` message.

### The read-modify-write hazard

**Warning: these two endpoints replace the whole collection.** They do not append. If you send one LID, the member keeps one favorite and loses the other three.

Follow this sequence to add or remove one favorite:

1. Call `GET /me`.
2. Read the current list from `member.favoriteProductions` (each item holds a `production` object with an `id`).
3. Build the new array of up to four LIDs, in the order you want.
4. Send the complete array.

```bash
# Wrong. This deletes the other three favorites.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/favorite-films" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"favoriteFilms": ["2bbs"]}'

# Right. Send the full collection after you read it from GET /me.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/favorite-films" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"favoriteFilms": ["2bbs", "aBcD", "eFgH", "iJkL"]}'
```

Send `{"favoriteFilms": []}` to remove all favorites. The array order is the display order on the profile page.

`Member.favoriteFilms` is **deprecated**. Read `Member.favoriteProductions` instead. A `FavoriteProduction` also carries `posterPickerUrl` and `backdropPickerUrl`, and both are **FIRST PARTY**.

## Tags

A tagging joins a tag to a diary entry, a review or a list. Three endpoints edit tags across the whole account at once. All three answer **403** if the member has no permission to mass-edit tags. Handle that 403 as a normal state, not as a crash.

Every request needs a `type`. The value is `viewings` (diary entries and reviews) or `lists`.

Three different tag strings exist. Do not mix them. `tagCode` is the normalized code the API matches on. `rawTag` is the raw value the member typed. `displayTag` is the text the API shows in a `Tag` object.

| Endpoint | Body | Returns |
|---|---|---|
| `GET /me/check-tag` | `{"type", "tagCode"}` | 200 `TagCheckResponse` with `count`, `type` and `tagCode` |
| `PATCH /me/update-tag` | `{"type", "tagCode", "rawTag", "newTagCode"}` | 200, empty body |
| `DELETE /me/delete-tag` | `{"type", "tagCode", "rawTag"}` | 204 |

`GET /me/check-tag` sends a JSON body on a GET request. This is unusual. Confirm that your HTTP client supports a body on GET, or the call fails silently.

`count` in the `TagCheckResponse` is the number of existing taggings that match the **new** tag code. A count above zero means the rename merges two tags. Show a merge warning to the user before you continue.

### Rename a tag everywhere

1. Get the current tags with `GET /member/{id}/log-entry-tags` (for `viewings`) or `GET /member/{id}/list-tags-2` (for `lists`). Each `Tag` gives you `code` and `displayTag`.
2. Ask the user for the new tag text.
3. Check for a merge with `GET /me/check-tag`, using the **new** code.
4. Warn the user if `count` is above zero, because the rename joins the two tags.
5. Apply the rename with `PATCH /me/update-tag`.

```bash
# Step 3. Does the target code already exist?
curl -s -X GET "https://api.letterboxd.com/api/v0/me/check-tag" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type": "viewings", "tagCode": "noir"}'
# -> {"count": 12, "type": "viewings", "tagCode": "noir"}
# 12 diary entries already carry "noir". The rename merges them.

# Step 5. Rename "film-noir" to "noir" on every viewing.
curl -s -X PATCH "https://api.letterboxd.com/api/v0/me/update-tag" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "type": "viewings",
    "tagCode": "film-noir",
    "rawTag": "film noir",
    "newTagCode": "noir"
  }'

# Delete a tag from every viewing.
curl -s -X DELETE "https://api.letterboxd.com/api/v0/me/delete-tag" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type": "viewings", "tagCode": "to-rewatch", "rawTag": "to rewatch"}'
```

- **Do this:** call `GET /me/check-tag` before every rename, and show the merge count.
- **Do not do this:** do not rename a tag without a confirmation step. The change touches every tagging and you cannot undo it.

## Push notifications **FIRST PARTY**

Both push endpoints need `client:firstparty`. Third-party clients cannot register a device.

`POST /me/register-push-notifications` needs the scopes `user` and `client:firstparty`. The body is `{"deviceId", "deviceName", "token"}`. `deviceId` and `token` are required, and `deviceName` is optional. Letterboxd sends notifications through Firebase, so `token` must come from Firebase.

`POST /me/deregister-push-notifications` needs the scope `client:firstparty` only. The body is `{"deviceId"}`. Call it when the user signs out.

Both return 204 with no body.

```bash
curl -s -X POST "https://api.letterboxd.com/api/v0/me/register-push-notifications" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"deviceId": "9F1C-...", "deviceName": "iPhone 15", "token": "FIREBASE_TOKEN"}'
```

Read `devicesRegisteredForPushNotifications` from `GET /me` to list the registered device IDs. Control the notification types with the `pushNotificationsFor*` fields on `PATCH /me`.

## Collect, validate and disable

### POST /me/collect-item

This endpoint collects a treasure hunt item. The scopes are `user` and `content:modify`. The body is `{"nonce", "token", "itemId"}`.

Do not build these three values yourself. Read them from a `TreasureHuntItem`, which endpoints such as `GET /contributor/{id}/hunt-items` return. The same object carries `found`, `name`, `locationHint` and `actionUrl`. Skip an item whose `found` is already `true`.

A 200 means success. A 404 means the API did not find the hunt item.

### POST /me/validation-request **FIRST PARTY**

This endpoint sends a new email validation link. The scopes are `user:owner` and `client:firstparty`. It takes no body.

Call it when `emailAddressValidated` is `false` and the first link expired. A 204 means the API dispatched the email. A 403 means the address is already valid. A 429 means too many requests – tell the user to look in the spam folder.

### POST /me/disable **DESTRUCTIVE**

**Warning: this endpoint deactivates or deletes the member account. The `Delete` mode destroys the account and its content.**

The scopes are `user:owner` and `security:modify`. The body is a `DisableAccountRequest`:

| Field | Required | Notes |
|---|---|---|
| `currentPassword` | Yes | The member's current password |
| `authenticationCode` | No | Required only if the member enabled two-factor authentication |
| `mode` | No | `Disable` or `Delete`. Defaults to `Disable` |

A 204 means success. A 403 means a wrong password or a wrong two-factor code.

Build a confirmation step into any client. Follow these rules:

1. Show the user the exact effect of the chosen `mode`.
2. Ask the user to type the password in a fresh field. Never reuse a stored password.
3. Ask for a second, explicit confirmation before you send the request.
4. Revoke the access token and the refresh token after the 204, then sign the user out.

- **Do this:** show a plain warning that `Delete` is permanent, then ask twice.
- **Do not do this:** never call `POST /me/disable` from a script or an agent without direct human confirmation in that same step.

## Scopes cheat sheet

| Operation | `user` | `user:owner` | `profile:modify` | `content:modify` | `security:modify` | `client:firstparty` |
|---|---|---|---|---|---|---|
| `GET /me` | Yes | – | – | – | – | – |
| `PATCH /me` | – | Yes | Yes | – | – | – |
| `PATCH /me/watch/{id}` | Yes | – | – | Yes | – | – |
| `PATCH /me/rate/{id}` | Yes | – | – | Yes | – | – |
| `PATCH /me/like/{id}` | Yes | – | – | Yes | – | – |
| `PATCH /me/watchlist/{id}` | Yes | – | – | Yes | – | – |
| `PATCH /me/subscribe/{id}` | Yes | – | – | Yes | – | – |
| `PATCH /me/favorite-films` | Yes | – | – | Yes | – | – |
| `PATCH /me/favorite-productions` | Yes | – | – | Yes | – | **Yes** |
| `GET /me/check-tag` | Yes | – | – | – | – | – |
| `PATCH /me/update-tag` | Yes | – | – | Yes | – | – |
| `DELETE /me/delete-tag` | Yes | – | – | Yes | – | – |
| `POST /me/register-push-notifications` | Yes | – | – | – | – | **Yes** |
| `POST /me/deregister-push-notifications` | – | – | – | – | – | **Yes** |
| `POST /me/collect-item` | Yes | – | – | Yes | – | – |
| `POST /me/validation-request` | – | Yes | – | – | – | **Yes** |
| `POST /me/disable` | – | Yes | – | – | Yes | – |

`user`, `user:owner` and `client:firstparty` cannot be requested. The API grants `user` and `user:owner` automatically when a member signs in through the Authorization Code flow. Request the other scopes in the authorization URL, in a space-delimited or plus-delimited string:

```
profile:modify content:modify
profile:modify+content:modify
```

A third-party app that reads and writes member data usually needs `content:modify profile:modify oauth:refresh`. Add `security:modify` only if the app changes the password, the email address or the account state.

## Pitfalls

**PATCH is partial, but the favorites endpoints are not.** This is the largest trap in the group. `PATCH /me` and the five relationship endpoints leave every omitted field unchanged. `PATCH /me/favorite-films` and `PATCH /me/favorite-productions` replace the whole array with the array you send. The two behaviours look the same, but they are not. Read the current favorites first, then write the complete list back.

**Use the Authorization Code flow, never Client Credentials.** Client Credentials returns public data with no member attached. Every `/me` endpoint then fails. The Password flow also works, but it is first-party only.

**A 200 can still carry an error.** `PATCH /me` returns 200 with a `messages` array. Check each message for `type: "Error"`. The API ignores an invalid field instead of rejecting the request.

**The like target is the log entry, not the film.** A review lives inside a `LogEntry`. Pass the log entry LID to `PATCH /me/like/{id}`.

**An unwatch can conflict.** `{"watched": false}` returns 409 when a rating, a review or a diary entry exists. Remove that activity first.

**A rating must fall on a half-star step.** Values outside 0.5 to 5.0, or off the 0.5 grid, return 403.

**`privateAccount` hides the member everywhere except `/me`.** Check this flag before you report missing data.

**Refresh the token before it expires.** Watch the `expires_in` value on the token. Request `oauth:refresh` to get a refresh token. Revoke both tokens at sign-out.

**Find LIDs from the website.** Send a HEAD request to a Letterboxd page and read the `x-letterboxd-identifier` response header. Film, review and list LIDs also appear in the `boxd.it` short URL path.

**Read `capabilities`, not the old booleans.** All the `can*` fields on `MemberAccount` are deprecated.

## Relationships

- **overview.md** – base URL, LIDs, the `X-HTTP-Method-Override` header, pagination limits and the First Party rule.
- **authentication.md** – the OAuth2 flows, the scope list, token refresh and revocation.
- **films.md** – film LIDs, `GET /film/{id}/me` for the current relationship, and the deprecated `PATCH /film/{id}/me`.
- **log-entries.md** – log entry and review LIDs for `/me/like` and `/me/subscribe`, plus tag fields on a diary entry.
- **lists.md** – list LIDs for `/me/like` and `/me/subscribe`, and `PATCH /list/{id}/me`.
- **members.md** – the public `Member` schema, `GET /member/{id}/log-entry-tags` and `GET /member/{id}/list-tags-2` for tag codes, `GET /members/pronouns` for pronoun LIDs, and `GET /member/{id}/statistics`.
