# Letterboxd API: Stories, Comments and Reporting
Based on Letterboxd API v0 documentation.

Stories are long-form posts by a member. Comments attach to three different parent types. Reports send content to the Letterboxd moderators. Read `overview.md` first for the base URL, the LID scheme and the cursor rules.

## First Party marks

The API marks some endpoints and some parameters as "First Party". Only the apps of Letterboxd can call them. The licence terms of Letterboxd cause this restriction. **No endpoint and no parameter in this file carries the First Party mark.** Every endpoint here is open to a third-party client with the correct scopes. The related `client:firstparty` scope cannot be requested, so a third-party client never gains it.

## Endpoint map

| Endpoint | Method | Extra scopes | Returns |
|---|---|---|---|
| `/stories` | GET | none | `StoriesResponse` |
| `/story/{id}` | GET | none | `Story` |
| `/story/{id}/statistics` | GET | none | `StoryStatistics` |
| `/story/{id}/comments` | GET | none | `StoryCommentsResponse` |
| `/story/{id}/me` | GET | `user` | `StoryRelationship` |
| `/story/{id}` | PATCH | `user`, `content:modify` | `StoryUpdateResponse` |
| `/story/{id}/me` | PATCH **DEPRECATED** | `user`, `content:modify` | `StoryRelationshipUpdateResponse` |
| `/story/{id}/comments` | POST | `user`, `content:modify` | `StoryComment` |
| `/list/{id}/comments` | GET, POST | POST adds `user`, `content:modify` | `ListCommentsResponse`, `ListComment` |
| `/log-entry/{id}/comments` | GET, POST | POST adds `user`, `content:modify` | `ReviewCommentsResponse`, `ReviewComment` |
| `/comment/{id}` | PATCH, DELETE | `user`, `content:modify` | `CommentUpdateResponse`, 204 |
| `/comment/{id}/report` | POST | `user`, `content:modify` | 204, no body |
| `/comment/report-reasons` | GET | none | `ReportReasonMetadataResponse` |

Every endpoint uses the `oauth2` scheme. Send `Authorization: Bearer ACCESS_TOKEN`. An endpoint with the `user` scope needs a token from the Authorization Code flow. See `authentication.md`.

# Part 1: Stories

## GET /stories

Operation ID `stories`. The endpoint returns a cursored window over stories.

| Parameter | Type | Default | Note |
|---|---|---|---|
| `cursor` | string | – | The pagination cursor. Copy it from the `next` field of the previous page. |
| `perPage` | int32 | `20` | The maximum is `100`. |
| `sort` | enum | `WhenUpdatedLatestFirst` | See the table below. |
| `member` | string | – | The LID of a member. |
| `memberRelationship` | `StoryMemberRelationship` | `Owner` | `Owner` returns the stories of the member. `Liked` returns the stories that the member liked. Use it only together with `member`. |
| `where` | array of enum | – | `Published` or `NotPublished`. The style is exploded form, so repeat the key: `?where=Published&where=NotPublished`. |

| `sort` value | Order |
|---|---|
| `WhenUpdatedLatestFirst`, `WhenUpdatedEarliestFirst` | By the time of the last update. The first value is the default. |
| `WhenPublishedLatestFirst`, `WhenPublishedEarliestFirst` | By the time of publication. |
| `WhenCreatedLatestFirst`, `WhenCreatedEarliestFirst` | By the time of creation. |
| `StoryTitle` | Alphabetical by title. |
| `PinnedFirst` | The stories that the author pinned come first. |
| `WhenLiked` | The most recent like first. Use it with `memberRelationship=Liked`. |

### Worked examples

```bash
API=https://api.letterboxd.com/api/v0
AUTH="Authorization: Bearer $TOKEN"

# The 50 most recently updated stories on the service.
curl "$API/stories?perPage=50" -H "$AUTH"

# The published stories of one member, newest publication first.
curl "$API/stories?member=1AbC&memberRelationship=Owner&where=Published&sort=WhenPublishedLatestFirst" -H "$AUTH"

# The stories that a member liked, in the order of the likes.
curl "$API/stories?member=1AbC&memberRelationship=Liked&sort=WhenLiked" -H "$AUTH"

# Your own drafts. The token must belong to the member in the member parameter.
curl "$API/stories?member=$MY_LID&where=NotPublished" -H "$AUTH"
```

The later examples in this file reuse the `$API` variable and the `$AUTH` variable from the block above.

**The API never returns the unpublished stories of another member.** A `where=NotPublished` filter on another member gives an empty item list, not an error.

`StoriesResponse` holds `next` (string), `items` (`StorySummary[]`) and `itemCount` (int32). Pass `next` back as `cursor`. A missing `next` means the end of the data.

## GET /story/{id}

Operation ID `getStory`. The path parameter `id` is the LID of the story. The response is a `Story`.

Both `Story` and `StorySummary` hold `id`, `name`, `author` (a `MemberSummary`), `url`, `source`, `videoUrl`, `bodyHtml`, `bodyLbml`, `whenCreated`, `whenUpdated`, `image` and `pinned`. Three points differ.

| Property | `Story` | `StorySummary` | Meaning |
|---|---|---|---|
| `commentPolicy` | **yes** | no | The `CommentPolicy` of the story. |
| `bodyTruncated` | no | **yes** | `true` if the API cut a long body. |
| `pinned` | required | optional | `true` if the author pinned the story. |

The body of a story is always a preview extract, and the API can truncate it. Use the `letterboxd` link of the story for the full text.

## GET /story/{id}/statistics

Operation ID `getStoryStatistics`. The `StoryStatistics` response holds `story` (a `StoryIdentifier`) and `counts`, with an integer `comments` field and an integer `likes` field. Use this endpoint for the counts. Do not count the items of a comment page.

## GET /story/{id}/me

Operation ID `myRelationshipToStory`. It needs the `user` scope. The response is `StoryRelationship`.

| Property | Type | Meaning |
|---|---|---|
| `liked` | boolean | `true` if the member likes the story. A member cannot like their own story. |
| `subscribed` | boolean | `true` if the member gets comment notifications. |
| `subscriptionState` | `CommentSubscriptionState` | `Subscribed`, `NotSubscribed` or `Unsubscribed`. |
| `commentThreadState` | `CommentThreadState` | The permission of the member to post a comment. |

**Call this endpoint before you show a comment box.** The `commentThreadState` value tells you if the member can post.

## GET and POST /story/{id}/comments

Operation IDs `getStoryComments` and `createStoryComment`. The POST needs `user` and `content:modify`, takes a `CommentCreationRequest` and returns a `StoryComment`. The parameters and the model match the list threads and the review threads. See Part 2.

## PATCH /story/{id} against PATCH /story/{id}/me

These two paths look similar. They do different work. Read this table before you write the code.

| Question | `PATCH /story/{id}` | `PATCH /story/{id}/me` |
|---|---|---|
| Operation ID | `updateStory` | `updateMyRelationshipToStory` |
| Status | Current | **DEPRECATED** |
| Who calls it | The author of the story only | Any member other than the author |
| What it changes | The story object | Your relationship to the story |
| Request schema | `StoryUpdateRequest` | `StoryRelationshipUpdateRequest` |
| Body fields | `commentPolicy` | `liked`, `subscribed` (boolean or null) |
| Response | `StoryUpdateResponse` | `StoryRelationshipUpdateResponse` |
| 403 text | "Not your story" | "The request was not allowed" |

**`StoryUpdateRequest` holds one field only: `commentPolicy`.** The API gives no way to change the title, the body or the image of a story. It also gives no create route and no delete route. Members write stories on the website.

```bash
# Close the comment thread of your own story.
curl -X PATCH "$API/story/1AbC" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"commentPolicy": "You"}'

# Like the story of another member. This is the current route. It returns 204 and no body.
curl -X PATCH "$API/me/like/1AbC" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"liked": true}'

# The deprecated route. It returns the new relationship and a message list.
curl -X PATCH "$API/story/1AbC/me" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"liked": true, "subscribed": true}'
```

### Read the messages array

`StoryUpdateResponse` and `StoryRelationshipUpdateResponse` both hold `data` and `messages`. **The API can return HTTP 200 and an error in `messages`.** Test each item for `type == "Error"`.

| Schema | Error codes |
|---|---|
| `StoryUpdateMessage` | `StoryNameTooLong`, `StoryNameIsBlank`, `StoryWithNoText`, `StoryIsTooLong`, `StoryWithNoImage` |
| `StoryRelationshipUpdateMessage` | `LikeBlockedContent`, `LikeOwnStory`, `LikeRateLimit`, `SubscribeWhenOptedOut`, `SubscribeToContentYouBlocked`, `SubscribeToBlockedContent` |

# Part 2: Comments

Comments are not one endpoint group. A comment attaches to a list, to a log entry (a review) or to a story. The three parents share one request schema, one base entity and one edit path.

## The mapping table

| Comment on | Create | Read | Item type |
|---|---|---|---|
| A list | `POST /list/{id}/comments` | `GET /list/{id}/comments` | `ListComment` |
| A log entry (review) | `POST /log-entry/{id}/comments` | `GET /log-entry/{id}/comments` | `ReviewComment` |
| A story | `POST /story/{id}/comments` | `GET /story/{id}/comments` | `StoryComment` |
| **Edit** any of them | `PATCH /comment/{id}` | – | `CommentUpdateResponse` |
| **Delete** any of them | `DELETE /comment/{id}` | – | 204, no body |
| **Report** any of them | `POST /comment/{id}/report` | – | 204, no body |

**The edit path, the delete path and the report path are generic.** They take the LID of the comment. They do not know and do not need the parent type. Store the comment LID after each create operation. You cannot derive it from the parent LID.

## Read a thread

The three GET endpoints share four query parameters.

| Parameter | Type | Default | Note |
|---|---|---|---|
| `cursor` | string | – | The pagination cursor. |
| `perPage` | int32 | `20` | The maximum is `100`. |
| `sort` | `CommentsSort` | `Date` | `Date`, `DateLatestFirst` or `Updates`. |
| `includeDeletions` | boolean | not documented | Set it to `true` to see the deleted comments. |

Poll a thread with the `Updates` order. It returns the newest content first. Add `includeDeletions=true` with it, because a deleted comment then stays in the sequence and your local copy stays consistent.

```bash
curl "$API/story/1AbC/comments?sort=Updates&includeDeletions=true&perPage=100" -H "$AUTH"
```

## Create a comment

`CommentCreationRequest` holds one required field: `comment`, a string in LBML, with a maximum size of 100,000 characters. LBML accepts these HTML tags only: `<br>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<a href="">`, `<blockquote>`.

```bash
curl -X POST "$API/log-entry/2DeF/comments" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"comment": "A <strong>great</strong> read. Thank you."}'
```

The create endpoints return the comment entity directly, without a wrapper. A 403 means that the member cannot post to this thread.

## Edit and delete

`PATCH /comment/{id}` takes a `CommentUpdateRequest`. That schema matches `CommentCreationRequest`: one required `comment` field in LBML.

```bash
curl -X PATCH "$API/comment/9XyZ" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"comment": "A great read. I corrected a typo."}'
```

The response is a `CommentUpdateResponse`: `data` (an `AbstractComment`) and `messages` (a `CommentUpdateMessage[]`). Test the messages again.

| `CommentUpdateMessage` code | Cause |
|---|---|
| `MissingComment` | The body has no `comment` field. |
| `CommentOnContentYouBlocked` | You blocked the owner of the content. |
| `CommentOnBlockedContent` | The owner of the content blocked you. |
| `CommentBan` | The community managers stopped your comments. |
| `CommentEditWindowExpired` | The edit window closed. |
| `CommentTooLong` | The text is longer than 100,000 characters. |

`DELETE /comment/{id}` sends no body. **The owner of the comment can delete it. The owner of the thread can also delete it.** A 403 means that the delete window expired.

The edit window appears in two fields of `AbstractComment`. `editableWindowExpiresIn` is **deprecated**; it gives the remaining seconds. `whenEditingWindowExpires` is current; it gives the end time in ISO 8601 with the UTC timezone. Both fields appear only for the comments of the authenticated member. An absent field means that you cannot edit the comment.

## AbstractComment is polymorphic

`AbstractComment` is the base entity. The discriminator is the `type` property. Its value comes from the `CommentType` enum. Each subtype adds one parent identifier, and that identifier holds a single `id` string.

| `type` value | Concrete schema | Extra property |
|---|---|---|
| `ListComment` | `ListComment` | `list` – a `ListIdentifier` |
| `ReviewComment` | `ReviewComment` | `review` – a `ReviewIdentifier` |
| `StoryComment` | `StoryComment` | `story` – a `StoryIdentifier` |

### The shared base properties

| Property | Type | Note |
|---|---|---|
| `id` (required) | string | The LID of the comment. Send it to `/comment/{id}`. |
| `member` (required) | `MemberSummary` | The author of the comment. |
| `whenCreated`, `whenUpdated` (required) | date-time | ISO 8601 with the UTC timezone. |
| `comment` | string | The message as HTML. Render this field. |
| `commentLbml` | string | The message as LBML. Send this field back in an edit. |
| `removedByAdmin` (required) | boolean | A moderator removed the comment. |
| `removedByContentOwner` (required) | boolean | The owner of the thread removed the comment. |
| `deleted` (required) | boolean | The author of the comment removed it. |
| `blocked` (required) | boolean | You blocked the author of the comment. |
| `blockedByOwner` (required) | boolean | The owner of the thread blocked the author. |

**Five flags hide the body.** If `removedByAdmin`, `removedByContentOwner`, `deleted`, `blocked` or `blockedByOwner` is `true`, the API omits `comment` and `commentLbml`. Test the five flags before you render the body. Never assume that `comment` exists.

### Handle the discriminator

Switch on `type`. Do not test for the presence of the `list`, the `review` or the `story` field.

```js
// Return the parent of any comment. The type field selects the branch.
function parentOf(comment) {
  switch (comment.type) {
    case "ListComment":   return { kind: "list",     id: comment.list.id };
    case "ReviewComment": return { kind: "logEntry", id: comment.review.id };
    case "StoryComment":  return { kind: "story",    id: comment.story.id };
    // A new type can appear later. Keep the comment. Hide the parent link.
    default: return { kind: "unknown", id: null };
  }
}
```

A `ReviewIdentifier` holds the LID of the **log entry**, not a separate review LID. Send that LID to the `/log-entry/` endpoints.

Each GET endpoint returns one concrete type, so `type` is predictable inside a single thread. The `PATCH /comment/{id}` response returns the base type, so the discriminator matters there. Write one handler and use it in both places.

## Comment state reference

### CommentThreadState

This enum answers one question: can the authenticated member post a comment now? Read it from the `commentThreadState` property of `StoryRelationship`, `ListRelationship` or `ReviewRelationship`.

| Value | Can post? | Cause |
|---|---|---|
| `CanComment` | **Yes** | The member is authorized. |
| `Banned` | No | The community managers stopped the comments of the member. |
| `Blocked` | No | The owner blocked the member. |
| `BlockedThem` | No | The member blocked the owner. |
| `Closed` | No | The owner closed the thread to all other members. |
| `FriendsOnly` | No | The owner accepts comments from followed members only. |
| `Moderated` | No | The community managers removed the content. This applies to reviews only. |
| `NotCommentable` | No | The thread accepts no comments. |
| `NotValidated` | No | The owner did not validate their email address. |

**`CanComment` is the only value that permits a post.** Treat every other value as a block. Do not test for a list of bad values, because Letterboxd can add a value later.

### CommentPolicy

| Value | Who can comment |
|---|---|
| `Anyone` | Every member. |
| `Friends` | The members that the owner follows. |
| `You` | The owner only. This closes the thread. |

`CommentPolicy` is the setting of the owner. `CommentThreadState` is the result for you. The policy appears on the `Story` entity and in `StoryUpdateRequest`. **Use `commentThreadState` for the user interface, not `commentPolicy`.** A policy of `Anyone` still gives you `Banned` or `Blocked` in some cases.

### CommentsSort and CommentType

| Enum | Values |
|---|---|
| `CommentsSort` | `Date` (the oldest first, and the default), `DateLatestFirst` (the newest first), `Updates` (the newest change first) |
| `CommentType` | `ListComment`, `ReviewComment`, `StoryComment` |

### CommentSubscriptionState

| Value | Meaning |
|---|---|
| `Subscribed` | The member gets comment notifications. |
| `NotSubscribed` | The member never made a choice. A comment by the member starts a subscription. |
| `Unsubscribed` | The member made an explicit choice to stop. A later comment does not start a subscription again. |

The two negative states differ for one reason. `NotSubscribed` changes to `Subscribed` when the member posts a comment. `Unsubscribed` does not change. Show the difference in your user interface.

### What stops a post

Check these four items in this order before you send a `POST`:

1. The token has the `content:modify` scope. If not, the API returns a 403.
2. The `commentThreadState` of the parent is `CanComment`. Any other value gives a 403.
3. The `comment` field is present and is not empty. An empty field gives a `MissingComment` message.
4. The text is 100,000 characters or shorter. A longer text gives a `CommentTooLong` message.

## Subscriptions

A subscription controls the comment notifications for one thread. `PATCH /me/subscribe/{id}` is the current route. The `{id}` is the LID of any commentable object: a list, a log entry or a story. It needs `user` and `content:modify`. The body is a `SubscribeUpdateRequest` with one required field, `subscribed` (boolean or null). Success gives 204 and no body. A 403 means that the request was not allowed. A 404 means that no commentable object matches the LID.

```bash
# Subscribe to the comment thread of a story, a list or a log entry.
curl -X PATCH "$API/me/subscribe/1AbC" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"subscribed": true}'
```

The endpoint returns no state. Read the current state from the relationship endpoint of the parent: `GET /story/{id}/me`, `GET /list/{id}/me` or `GET /log-entry/{id}/me`.

**A value of `true` fails silently when the member disabled comment notifications in their account settings.** The API ignores the value. Read the state back if the result matters.

The API can also change the subscription without your request. A member who posts a comment becomes `Subscribed`, unless the member previously chose `Unsubscribed`. Refresh the relationship after each successful post. See `me.md` for the other `/me/*` write endpoints.

# Part 3: Reports

A report sends content to the Letterboxd moderators. Five object types accept a report. Three of them publish their reasons through an endpoint.

## Use two steps. Never hardcode a reason.

1. Call the `report-reasons` endpoint for the object type. It returns a `ReportReasonMetadataResponse` with an `items` array.
2. Sort the items by `priority`, the low value first. Render the `descriptionHtml` of each item for the member.
3. Post the report. Copy the `reason` string of the chosen item into the request body.

| `ReportReasonMetadata` field | Type | Use |
|---|---|---|
| `reason` (required) | string | Send this exact value as the `reason` of the report. |
| `code` | string | The internal code. Use it for your own analytics only. |
| `priority` (required) | integer | The sort order. A low value comes first. |
| `descriptionHtml` (required) | string | The label for the member. Render it as HTML. |
| `messageRequired` (required) | boolean | `true` means that the report needs a `message`. |

**Read `messageRequired` from the response.** Do not build your own rule for the message. The reason set can change without a change of the API version.

```bash
# Step 1: get the current reasons.
curl "$API/comment/report-reasons" -H "$AUTH"

# Step 2: post the report with a reason from step 1. Success gives 204.
curl -X POST "$API/comment/9XyZ/report" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"reason": "Plagiarism", "message": "This text comes from another review."}'
```

## The report endpoints

| Object | Report endpoint | Reasons endpoint | Request schema |
|---|---|---|---|
| Comment | `POST /comment/{id}/report` | `GET /comment/report-reasons` | `ReportCommentRequest` |
| List | `POST /list/{id}/report` | `GET /list/report-reasons` | `ReportListRequest` |
| Log entry (review) | `POST /log-entry/{id}/report` | **none** | `ReportReviewRequest` |
| Member | `POST /member/{id}/report` | `GET /member/report-reasons` | `ReportMemberRequest` |
| Film | `POST /film/{id}/report` **DEPRECATED** | **none** | `ReportProductionRequest` |

Every report endpoint needs `user` and `content:modify`, and every one returns 204 on success. Each request schema holds two fields: `reason` (required) and `message` (an optional string). The log entry and the film have no reasons endpoint, so use the enum of the request schema for those two. The film route is deprecated, and the documentation points to a `/production/{id}/report` route that the endpoint reference does not describe.

## The documented reason enums

Use these values as a fallback only. Prefer the `report-reasons` endpoint whenever one exists.

| Schema | Reason values | A message is required for |
|---|---|---|
| `ReportCommentRequest` | `Abuse`, `Spoilers`, `Spam`, `Plagiarism`, `Other` | `Plagiarism`, `Other` |
| `ReportListRequest` | `Abuse`, `Spoilers`, `Spam`, `Plagiarism`, `Other` | `Plagiarism`, `Other` |
| `ReportReviewRequest` | `Abuse`, `Spoilers`, `Spam`, `Plagiarism`, `Other` | `Plagiarism`, `Other` |
| `ReportMemberRequest` | `AbusiveAccount`, `HatefulAccount`, `ManipulativeAccount`, `OffensiveAccount`, `ParodyAccount`, `PiracyAccount`, `PlagiaristAccount`, `SolicitousAccount`, `SpamAccount`, `Other` | `PlagiaristAccount`, `SolicitousAccount`, `Other` |
| `ReportProductionRequest` | `Duplicate`, `NotAFilm`, `Image`, `Other` | All four values |

# Pitfalls

| Pitfall | Effect | Fix |
|---|---|---|
| A Client Credentials token on a write endpoint | 403 on every `POST`, `PATCH` and `DELETE` | Use the Authorization Code flow. Request `content:modify`. |
| You test the HTTP status only | You miss the errors in the `messages` array | Test each message for `type == "Error"` after a `PATCH`. |
| You render `comment` without a check | An empty comment box for the removed items | Check the five removal flags first. |
| You send HTML in `comment` | The API rejects or strips the tags | Send LBML with the seven permitted tags only. |
| You send `comment` (HTML) back in an edit | The text loses its format | Send `commentLbml` back, not `comment`. |
| You cache `commentPolicy` for the button state | The blocked members see an active comment box | Read `commentThreadState` from the `/me` relationship. |
| You expect `PATCH /story/{id}` to change the title | No change | Only `commentPolicy` is editable. No create route and no delete route exist. |
| You call `PATCH /story/{id}/me` in new code | The route is deprecated | Use `PATCH /me/like/{id}` and `PATCH /me/subscribe/{id}`. |
| You hardcode a report reason | The report fails after a change at Letterboxd | Fetch the reasons. Read `messageRequired`. |
| You page past 100,000 objects | The cursor stops | The API caps the paginated data at 100,000 objects. Add filters. |
| You fetch every page to count the comments | Slow, and it hits the cap | Call `GET /story/{id}/statistics`. |
| You expect `Moderated` on a story | The state never appears | `Moderated` applies to reviews only. |
| You generate a client from the specification | Three operations share the ID `reportReasons` | Rename them, for example `commentReportReasons`. |
| You trust the 404 text of the story endpoints | Confusing logs | The official text has copy-paste errors. `GET /story/{id}/comments` says "No log entry matches". `POST /story/{id}/comments` says "No film matches". Both mean "No story matches". |

# Relationships

| File | Read it when you |
|---|---|
| `overview.md` | Need the base URL, the LID scheme, the cursor rules or the meaning of the First Party mark. |
| `authentication.md` | Choose an OAuth2 flow or request the `content:modify` scope. |
| `lists.md` | Work with the list comment endpoints, `ListRelationship` or `GET /list/report-reasons`. |
| `log-entries.md` | Work with the log entry comment endpoints, `ReviewRelationship` or `POST /log-entry/{id}/report`. |
| `me.md` | Use `PATCH /me/like/{id}` or `PATCH /me/subscribe/{id}`, the current routes for a like and a subscription. |
| `members.md` | Need `MemberSummary`, `GET /member/report-reasons` or `POST /member/{id}/report`. |
