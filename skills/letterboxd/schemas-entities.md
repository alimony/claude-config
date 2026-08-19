# Letterboxd API: Object Schemas
Based on Letterboxd API v0 documentation.

The API defines 190 object schemas. It also defines 30 enums, which `schemas-enums.md` covers. Do not memorise the 190 schemas. Learn the naming conventions in section 1 first. The name of a schema tells you its shape.

| Mark | Meaning |
|---|---|
| **FP** | FIRST PARTY. The API returns this field only to a first-party client (a client with the `client:firstparty` scope). A third-party client never receives it. Do not build a feature on it. |
| **DEP** | Deprecated. The API still returns the field, but a replacement exists. Do not write new code against it. |
| Req | Required. The API always returns the field, or your request body must contain it. |

## 1. The naming conventions

Each schema name ends with a suffix that tells you the role of the object. This table gives one example of each convention.

| Convention | What it is | Example | Where you meet it |
|---|---|---|---|
| `X` | The full entity. An endpoint returns it for one object. | `Film` | `GET /film/{id}` |
| `XSummary` | The trimmed entity. The API embeds it in other objects and in lists. | `FilmSummary` | `FilmsResponse.items` |
| `XIdentifier` | A wrapper around one LID. It has a single `id` field. | `ListIdentifier` | `ListComment.list` |
| `XCreationRequest` | The POST body that creates an object. | `ListCreationRequest` | `POST /lists` |
| `XUpdateRequest` | The PATCH body that changes an object. | `LogEntryUpdateRequest` | `PATCH /log-entry/{id}` |
| `XCreateResponse` / `XUpdateResponse` | An envelope. It holds `data` and `messages`. | `ListUpdateResponse` | `PATCH /list/{id}` |
| `XCreateMessage` / `XUpdateMessage` | One validation message. It holds `type`, `code` and `title`. | `ListUpdateMessage` | inside the envelope |
| `XResponse` | A cursored page. It holds `next`, `items` and `itemCount`. | `FilmsResponse` | `GET /films` |
| `XRelationship` | The relationship of a member to an entity. | `ListRelationship` | `GET /list/{id}/me` |
| `XRelationshipUpdateRequest` | The PATCH body for a relationship. | `ListRelationshipUpdateRequest` | `PATCH /list/{id}/me` |
| `XStatistics` | Aggregate counts for one entity, plus the identifier of that entity. | `FilmStatistics` | `GET /film/{id}/statistics` |
| `XStatisticsCounts` | The counts object inside `XStatistics`. | `FilmStatisticsCounts` | nested |
| `AbstractX` | A polymorphic base. A `type` field selects the concrete schema. | `AbstractComment` | `ListCommentsResponse.items` |
| `MemberXRelationship` | The relationship of another member to an entity, plus that member. | `MemberFilmRelationship` | `FilmSummary.relationships` |
| `XsMetadata` / `XsRelationship` | Filter counts and aggregate counts for a set of films. | `FilmsMetadata` | `ListEntriesResponse.metadata` |

### 1.1 `X` versus `XSummary`

The rule is simple. An endpoint that returns one entity returns the full `X`. Every other place returns the `XSummary`.

| Full | The endpoint that returns it | The summary | Where the summary appears |
|---|---|---|---|
| `Film` | `GET /film/{id}` | `FilmSummary` | `FilmsResponse.items`, `FilmCollection.films`, `ListEntrySummary.film`, `FilmContribution.film`, `FilmLogEntry.film` |
| `Member` | `GET /member/{id}`, `POST /members/register`, `MemberAccount.member` | `MemberSummary` | every `owner`, `author` and `member` field, `MembersResponse.items`, `List.collaborators` |
| `List` | `GET /list/{id}`, `ListCreateResponse.data`, `ListUpdateResponse.data` | `ListSummary` | `ListsResponse.items`, `Member.pinnedFilmLists`, `Member.featuredList`, `ListTopic.items` |
| `Story` | `GET /story/{id}`, `StoryUpdateResponse.data`, `Production.recentStories` | `StorySummary` | `StoriesResponse.items` |
| `Contributor` | `GET /contributor/{id}` | `ContributorSummary` | `FilmSummary.directors`, `Contributions.contributors` |
| `Production` | polymorphic base of `Film` | `ProductionSummary` | `ListEntry.production`, `ProductionLogEntry.production`, `FavoriteProduction.production` |
| `ProductionLogEntry` | `GET /log-entry/{id}` (as `FilmLogEntry`) | `LogEntrySummary` | `MemberFilmViewingRelationship.logEntry` |

**Warning: the summary is not a subset of the full object. Read the next paragraph before you write a shared type.**

`FilmSummary` carries three fields that `Film` does not carry: `directors`, `relationships` and `contextualPoster`. `Film` carries about 20 fields that `FilmSummary` does not carry, such as `description`, `tagline`, `trailer`, `backdrop`, `releases`, `countries`, `languages` and `themes`. The same asymmetry applies to `ListSummary`, which adds `descriptionTruncated` and `entriesOfNote`.

Three consequences for your client:

1. Model the pair as two types. Do not model one type with optional fields.
2. Do not merge a summary into a cached full object. The merge overwrites nothing and hides the missing fields.
3. Plan the round trip. A search result or a page item gives you a `FilmSummary`. To show a synopsis you must call `GET /film/{id}` again. The full `Film` has no `directors` field, so the cast needs a third call. The deprecation note on `Film.contributions` names `GET /production/{id}/contributions` for that call, but the endpoint reference does not document the path.

### 1.2 `XIdentifier`

An identifier holds one required `id` field, which is the LID of the entity. The API uses it where a full object would waste bandwidth.

| Schema | Points at | Appears in |
|---|---|---|
| `FilmIdentifier` | a film | `FilmStatistics.film` |
| `ListIdentifier` | a list | `ListComment.list`, `ListStatistics.list`, `List.clonedFrom`, `ListAddition.list` |
| `MemberIdentifier` | a member | `MemberStatistics.member` |
| `ReviewIdentifier` | a log entry that has a review | `ReviewComment.review`, `ReviewStatistics.logEntry` |
| `StoryIdentifier` | a story | `StoryComment.story`, `StoryStatistics.story` |

### 1.3 `XRequest`, `XResponse` and `XUpdateMessage`

A write endpoint takes an `XCreationRequest` or an `XUpdateRequest`. It answers with an envelope that holds two fields.

| Field | Type | Note |
|---|---|---|
| `data` | the created or updated object | `ListUpdateResponse.data` is a `List`. `LogEntryUpdateResponse.data` is a `FilmLogEntry`. |
| `messages` Req | `XUpdateMessage[]` | The messages you must show to the member. The array is often empty. |

**Warning: a 200 status does not mean success. Read `messages` before you show a result.**

Each message has three fields: `type` (`Error` or `Success`), `code` (a machine-readable enum) and `title` (the text for the member). The API ignores a field that breaks a business rule, and reports the reason in a message.

```js
// Apply a PATCH and act on the validation messages.
const res = await fetch(url, { method: "PATCH", headers, body });
const envelope = await res.json();
const errors = envelope.messages.filter((m) => m.type === "Error");
if (errors.length > 0) {
  // Show every title to the member. Log every code for yourself.
  throw new WriteRejected(errors.map((m) => m.code));
}
return envelope.data;
```

The message schemas and their `code` values:

| Message schema | `code` values |
|---|---|
| `FilmRelationshipUpdateMessage` | `InvalidRatingValue`, `UnableToRemoveWatch` |
| `LogEntryUpdateMessage` | `InvalidRatingValue`, `InvalidDiaryDate`, `ReviewWithNoText`, `ReviewIsTooLong`, `ModerationReviewText`, `LogEntryWithNoReviewOrDiaryDetails` |
| `ListCreateMessage` | `ListNameTooLong`, `ListNameIsBlank`, `UnknownFilmCode`, `InvalidRatingValue`, `DuplicateEntry`, `DuplicateRank`, `EmptyPublicList`, `CloneSourceNotFound`, `MemberCannotCloneLists`, `SharingServiceNotAuthorized`, `CannotSharePrivateList`, `ListDescriptionIsTooLong`, `ListEntryNotesTooLong`, `ListNameForbidden`, `InvalidItemForList`, `CannotBePublic` |
| `ListUpdateMessage` | the `ListCreateMessage` set, less `CloneSourceNotFound` and `MemberCannotCloneLists`, plus `ListModerated`, `ListVersionMismatch`, `MissingEntry`, `InvalidEntry` |
| `ListRelationshipUpdateMessage` | `LikeBlockedContent`, `LikeOwnList`, `LikeRateLimit`, `SubscribeWhenOptedOut`, `SubscribeToContentYouBlocked`, `SubscribeToBlockedContent` |
| `ReviewRelationshipUpdateMessage` | the list set, plus `LikeOwnReview`, `LikeRemovedReview`, `LikeLogEntryWithoutReview` |
| `StoryRelationshipUpdateMessage` | the list set, with `LikeOwnStory` in place of `LikeOwnList` |
| `MemberRelationshipUpdateMessage` | `BlockYourself`, `FollowYourself`, `FollowRateLimit`, `FollowBlockedMember`, `FollowMemberYouBlocked`, `BefriendYourself`, `BefriendBlockedMember`, `BefriendMemberYouBlocked` |
| `MemberSettingsUpdateMessage` | `IncorrectCurrentPassword`, `BlankPassword`, `InvalidPassword`, `InvalidEmailAddress`, `EmailAddressInUse`, `InvalidFavoriteFilm`, `InvalidFavoriteProduction`, `BioTooLong`, `InvalidPronounOption`, `InvalidGivenName`, `InvalidFamilyName` |
| `CommentUpdateMessage` | `MissingComment`, `CommentOnContentYouBlocked`, `CommentOnBlockedContent`, `CommentBan`, `CommentEditWindowExpired`, `CommentTooLong` |
| `StoryUpdateMessage` | `StoryNameTooLong`, `StoryNameIsBlank`, `StoryWithNoText`, `StoryIsTooLong`, `StoryWithNoImage` |

An `XResponse` schema is a cursored page. It always has the same three fields: `next`, `items` and `itemCount`. The `next` cursor is absent on the last page. Some pages add a `metadata` or a `relationships` field.

### 1.4 `XRelationship`

A relationship object answers the question "what has this member done with this entity?". The API never puts the relationship inside the entity itself. You read it from a separate endpoint, or from a `relationships` array.

| Relationship | Read it from | Write it with | The fields it holds |
|---|---|---|---|
| `ProductionRelationship` | `GET /film/{id}/me` | `PATCH /film/{id}/me` with `FilmRelationshipUpdateRequest` | `watched`, `liked`, `favorited`, `owned`, `inWatchlist`, `rating`, `rewatched`, `drafts`, `reviews`, `diaryEntries`, `privateNote`, `customPoster` and the `when*` timestamps |
| `MemberFilmRelationship` **DEP** | `GET /film/{id}/member/{member}`, `FilmSummary.relationships` | – | `member` plus `relationship`. Use the identical `MemberProductionRelationship`. |
| `ListRelationship` | `GET /list/{id}/me` | `PATCH /list/{id}/me` | `liked`, `subscribed`, `subscriptionState`, `commentThreadState`, `privateNote` |
| `ReviewRelationship` | `GET /log-entry/{id}/me` | `PATCH /log-entry/{id}/me` | `liked`, `subscribed`, `subscriptionState`, `commentThreadState` |
| `StoryRelationship` | `GET /story/{id}/me` | `PATCH /story/{id}/me` | `liked`, `subscribed`, `subscriptionState`, `commentThreadState` |
| `MemberRelationship` | `GET /member/{id}/me` | `PATCH /member/{id}/me` | `following`, `followedBy`, `blocking`, `blockedBy`, `closeFriend`, `closeFriendedBy`, `privateNote` |
| `ContributorRelationship` | `GET /contributor/{id}/me` | – | `customPoster` only |
| `FilmsRelationship` | `FilmsMemberRelationship.relationship` | – | `counts.watches` and `counts.likes` for a set of films |

Two enums control the comment behaviour of a relationship. `commentThreadState` says whether the member may post a comment now. `subscriptionState` says whether the member receives comment notifications. `schemas-enums.md` lists the values.

### 1.5 `XStatistics` and `XStatisticsCounts`

A statistics object holds an identifier and a `counts` object. The counts object is a flat set of integers.

| Statistics | Identifier field | Counts schema | The counts |
|---|---|---|---|
| `FilmStatistics` | `film` | `FilmStatisticsCounts` | `watches`, `likes`, `ratings`, `fans`, `lists`, `reviews`. It adds `rating` and `ratingsHistogram`. |
| `MemberStatistics` | `member` | `MemberStatisticsCounts` | 20 counts, such as `watches`, `ratings`, `reviews`, `diaryEntries`, `watchlist`, `followers`, `following`. It adds `ratingsHistogram`, `yearsInReview` and `summaryYears`. |
| `ListStatistics` | `list` | `ListStatisticsCounts` | `comments`, `likes` |
| `ReviewStatistics` | `logEntry` | `ReviewStatisticsCounts` | `comments`, `likes` |
| `StoryStatistics` | `story` | `StoryStatisticsCounts` | `comments`, `likes` |
| `ContributorStatistics` | – | `ContributionStatistics[]` | one `filmCount` for each `ContributionType` |
| `MemberTagCounts` | – | – | `films`, `logEntries`, `diaryEntries`, `reviews`, `lists` |

### 1.6 `AbstractX`

Three schemas are polymorphic. Section 3 gives the discriminator values and a dispatch example.

### 1.7 Four more patterns

| Pattern | The rule |
|---|---|
| LBML and HTML pairs | A text field comes twice. `descriptionLbml` and `description`, `commentLbml` and `comment`, `bodyLbml` and `bodyHtml`, `lbml` and `text`, `notesLbml` and `notes`. Read the HTML field to display the text. Send the LBML field back when you write. LBML permits `<br> <strong> <em> <b> <i> <a href=""> <blockquote>` and has a limit of 100,000 characters. |
| Timestamps | Every `when*` field is a string in ISO 8601 format with the UTC timezone, `YYYY-MM-DDThh:mm:ssZ`. A `diaryDate` and a `releaseDate` are date-only, `YYYY-MM-DD`. |
| `tags` and `tags2` | `tags` is a **DEP** array of strings. `tags2` is an array of `Tag` objects. Read `tags2`. Write plain strings, because the request bodies still take `string[]`. |
| Film to production drift | Letterboxd migrates the film schemas to production schemas. `Production` is the new base, `Film` extends it. `ListEntry.production` replaces `ListEntry.film`. `MemberProductionRelationship` replaces `MemberFilmRelationship`. `favoriteProductions` replaces `favoriteFilms`. Prefer the production name in new code, but keep the film field, because most endpoints still return it. |

## 2. The core entities in full

### 2.1 `Production` – the base of `Film`

`Film` is `Production` plus the film-only fields in 2.2. A client that handles productions handles both.

| Field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the production. |
| `name` Req | string | The title. |
| `fullDisplayName` Req | string | The title with the air dates. |
| `link` Req | url | The page on letterboxd.com. |
| `sortingName` Req | string | The title, normalised for sorting. |
| `alternativeNames` | string[] | **FP** Other titles and translations. |
| `releaseYear` | int32 | The year of the first release. |
| `releaseDate` | date | `YYYY-MM-DD`. |
| `runTime` | int32 | The duration in minutes. |
| `rating` | number | The weighted average, `0.5` to `5.0`. It is absent until the film has enough ratings. |
| `poster` | `Image` | 2:3 ratio, many sizes. It holds one obfuscated image if `adult` is `true`. |
| `adultPoster` | `Image` | The unobfuscated poster. It is present only if `adult` is `true`. |
| `adult` Req | boolean | The film is in the TMDB adult category. |
| `reviewsHidden` Req | boolean | **DEP** Use `reviewsHiddenReason`. |
| `reviewsHiddenReason` | enum | `Sensitive`, `Embargoed`, `Unreleased` or `NoReleaseDate`. It is absent when reviews are visible. |
| `posterCustomisable` Req | boolean | Any member may change the poster. |
| `posterPickerUrl` | url | **FP** The poster picker. |
| `backdropCustomisable` Req | boolean | Any member may change the backdrop. |
| `backdropPickerUrl` | url | **FP** The backdrop picker. |
| `description` | string | The synopsis. |
| `trailer` | `FilmTrailer` | The YouTube ID and URL. |
| `backdrop` | `Image` | 16:9 ratio, many sizes. |
| `backdropFocalPoint` | number | `0.0` to `1.0` from the top. Use it when you crop the backdrop. |
| `targeting` | string[] | **FP** The ad targeting values. |
| `recentStories` | `Story[]` | The related recent stories. |
| `similarProductions` | string[] | **FP** The LIDs of similar productions. |
| `inVideoStore` Req | boolean | At least one Video Store product exists somewhere. |
| `type` Req | string | The discriminator. The only published value is `Film`. |

### 2.2 `Film` – the fields it adds to `Production`

Returned by `GET /film/{id}` only.

| Field | Type | Note |
|---|---|---|
| `originalName` | string | **FP** The original non-English title. |
| `top250Position` | int32 | **DEP** Use `topFilmsPosition`. |
| `topFilmsPosition` | int32 | The position in the official top films list, or `null`. |
| `filmCollectionId` | string | The LID of the collection that holds the film. |
| `links` Req | `Link[]` | **DEP** The URLs on Letterboxd and on other sites. |
| `genres` | `Genre[]` | The genres. |
| `tagline` | string | The tagline. |
| `countries` | `Country[]` | **FP** The production countries. |
| `originalLanguage` | `Language` | **DEP** Use `productionLanguage`. |
| `productionLanguage` | `Language` | **FP** The original production language. |
| `primaryLanguage` | `Language` | The primary spoken language. |
| `languages` | `Language[]` | **FP** All spoken languages. |
| `releases` | `Release[]` | **FP** The release list by country and type. |
| `contributions` | `Contributions[]` | **DEP** Use `GET /production/{id}/contributions`. |
| `news` | `NewsItem[]` | **DEP** The related news items. |
| `similarTo` | `FilmSummary[]` | **DEP** **FP** Use `similarProductions`. |
| `themes` | `Theme[]` | **FP** The themes. |
| `minigenres` | `Minigenre[]` | **FP** The minigenres. |
| `nanogenres` | `Nanogenre[]` | **FP** The nanogenres. |

### 2.3 `FilmSummary`

| Field | Type | Note |
|---|---|---|
| `type` | string | **DEP** Always `FilmSummary`. Old apps need it. |
| `id` Req | string | The LID of the film. |
| `name` Req | string | The title. |
| `fullDisplayName` Req | string | The title with the air dates. |
| `link` Req | url | The page on letterboxd.com. |
| `sortingName` Req | string | The title, normalised for sorting. |
| `alternativeNames` | string[] | **FP** |
| `releaseYear` | int32 | |
| `runTime` | int32 | The duration in minutes. |
| `rating` | number | The weighted average, `0.5` to `5.0`. |
| `poster` | `Image` | 2:3 ratio. |
| `adultPoster` | `Image` | Present only if `adult` is `true`. |
| `adult` Req | boolean | |
| `reviewsHidden` Req | boolean | **DEP** |
| `reviewsHiddenReason` | enum | See 2.1. |
| `posterCustomisable` Req | boolean | |
| `posterPickerUrl` | url | **FP** |
| `backdropCustomisable` Req | boolean | |
| `backdropPickerUrl` | url | **FP** |
| `contextualPoster` | `Image` | The poster that the current context chose, such as the poster of a review or of a list entry. |
| `originalName` | string | **FP** |
| `top250Position` | int32 | **DEP** |
| `topFilmsPosition` | int32 | |
| `filmCollectionId` | string | |
| `directors` Req | `ContributorSummary[]` | The directors. `Film` has no such field. |
| `genres` Req | `Genre[]` | |
| `links` Req | `Link[]` | **DEP** |
| `relationships` | `MemberFilmRelationship[]` | The relationship of the authenticated member, and of other members when the request asks for them. |

### 2.4 `Member`

Returned by `GET /member/{id}` and by `POST /members/register`.

| Field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the member. |
| `username` Req | string | 2 to 15 characters. Letters, digits and `_` only. |
| `givenName` | string | |
| `familyName` | string | |
| `displayName` Req | string | The given name and the family name, or the username. It is never empty. |
| `shortName` Req | string | The given name, or the username. It is never empty. |
| `pronoun` | `Pronoun` | Use `GET /members/pronouns` for the full set. |
| `avatar` | `Image` | The ratio is not fixed. Crop it to a square from the centre. |
| `memberStatus` Req | `MemberStatus` | `Crew`, `Alum`, `Hq`, `Patron`, `Pro` or `Member`. |
| `hideAdsInContent` Req | boolean | Show no ads on the content of this member. |
| `canPublishStories` Req | boolean | |
| `accountStatus` Req | `AccountStatus` | `Active` or `Memorialized`. |
| `commentPolicy` | `CommentPolicy` | **DEP** |
| `hideAds` Req | boolean | **DEP** |
| `twitterUsername` | string | Present after the member authenticates the account. |
| `bioLbml` | string | The bio in LBML. |
| `bio` | string | The bio as HTML. |
| `location` | string | |
| `website` | string | The API does not validate the URL. Sanitise it. |
| `backdrop` | `Image` | Patron members only. |
| `backdropFocalPoint` | number | `0.0` to `1.0` from the top. |
| `backdropPickerUrl` | url | **FP** |
| `favoriteFilms` | `FilmSummary[]` | **DEP** Use `favoriteProductions`. Maximum four. |
| `favoriteProductions` | `FavoriteProduction[]` | Maximum four. |
| `pinnedFilmLists` | `ListSummary[]` | Paying members only. Maximum two. |
| `pinnedReviews` | `ProductionLogEntry[]` | Paying members only. Maximum two. |
| `links` Req | `Link[]` | The profile page. |
| `privateWatchlist` | boolean | The member hides the watchlist from other members. |
| `featuredList` | `ListSummary` | HQ members only. |
| `teamMembers` | `MemberSummary[]` | HQ members only. |
| `orgType` | enum | HQ members only. `Society`, `Educator`, `Exhibitor`, `Festival`, `Single_Film`, `Genre`, `Association`, `Media_Publisher`, `Product_Platform`, `Podcast`, `Streamer` or `Studio`. |

### 2.5 `MemberSummary`

`MemberSummary` holds the first 14 fields of `Member`. The order and the types are the same. The fields are `id`, `username`, `givenName`, `familyName`, `displayName`, `shortName`, `pronoun`, `avatar`, `memberStatus`, `hideAdsInContent`, `canPublishStories`, `accountStatus`, `commentPolicy` (**DEP**) and `hideAds` (**DEP**). It holds no bio, no location, no favorites and no links.

### 2.6 `MemberAccount`

Returned by `GET /me` and by `MemberSettingsUpdateResponse.data`. It needs an Authorization Code token. The profile itself sits in the nested `member` field.

| Field | Type | Note |
|---|---|---|
| `member` Req | `Member` | The standard member details. |
| `emailAddress` | string | |
| `emailAddressValidated` | boolean | |
| `twoFactorAuthenticationEnabled` | boolean | |
| `privateAccount` | boolean | The content of the member appears only in `/me`. |
| `includeInPeopleSection` | boolean | |
| `privateWatchlist` | boolean | **DEP** Found in `member`. |
| `suspended` | boolean | The member breached the community policy and cannot comment. |
| `capabilities` | enum[] | `CanSeeReviewTranslations`, `CanSeePrivateNotes`, `CanPublishStories`, `CanSeeShows`, `CanAccessVideoStore`, `CanSeePrivateViewings`, `CanSeeStoryLikesComments`, `CanHaveCustomBackdrops`, `CanHaveCustomPosters`, `CanSeeListStats`, `CanFilterActivity`, `CanChangeAppIcon`, `CanCloneLists`, `CanComment`. |
| `canComment`, `canCloneLists`, `canChangeAppIcon`, `canFilterActivity`, `canViewListStats`, `canHaveCustomPosters`, `canHaveCustomBackdrops`, `canSeeStoryLikesComments`, `canSeePrivateViewings`, `canAccessVideoStore`, `canSeeShows` | boolean | **DEP** Read `capabilities` instead. |
| `membershipDaysRemaining` | int64 | Paying members only. |
| `membershipWillAutoRenewViaIAP` | boolean | IAP subscribers only. |
| `hasActiveSubscription` | boolean | It is `false` when the member stopped the renewal, even before the period ends. |
| `subscriptionType` | string | `apple`, `google` or `paddle`. |
| `commentPolicy` | `CommentPolicy` | The default policy for new content. |
| `privacyPolicy` | `PrivacyPolicy` | The default policy for new content. |
| `adultContentPolicy` | enum | `Always` or `Default`. `Default` hides adult content. |
| `posterMode` | `PosterMode` | `All`, `Yours` or `None`. |
| `posterModeOptions` | `PosterMode[]` | The values this account may use. |
| `accountStatus` | `AccountStatus` | |
| `hideAds` | boolean | |
| `showCustomPostersAds` | boolean | |
| `hasVideoStoreSetup` | boolean | |
| `devicesRegisteredForPushNotifications` | string[] | The device IDs. |
| `campaigns` | string[] | |
| `campaignCode` | string | |
| `genreCategorisation` | string | The genre categorisation of the watched films. |

The notification flags are all booleans. Each one defaults to `true` for a new account.

| Family | Fields |
|---|---|
| Email, activity | `emailWhenFollowed`, `emailComments`, `emailFromFollowedOnly`, `emailAccountSecurityWarning` |
| Email, availability | `emailAvailability`, `emailBuyAvailability`, `emailRentAvailability`, `emailVideoStoreAvailability`, `emailVideoStoreRentalExpiry` |
| Email, editorial | `emailNews`, `emailCallSheet`, `emailShelfLife`, `emailBestInShow`, `emailRushes`, `emailPartnerMessages` |
| Push, activity | `pushNotificationsForComments`, `pushNotificationsForListLikes`, `pushNotificationsForReviewLikes`, `pushNotificationsForStoryLikes`, `pushNotificationsForNewFollowers`, `pushNotificationsFromFollowedOnly` |
| Push, availability | `pushNotificationsForAvailability`, `pushNotificationsForBuyAvailability`, `pushNotificationsForRentAvailability`, `pushNotificationsForVideoStoreAvailability`, `pushNotificationsForVideoStoreRentalExpiry` |
| Push, editorial | `pushNotificationsForGeneralAnnouncements`, `pushNotificationsForPartnerMessages`, `pushNotificationsForEditorialContent` |

### 2.7 `List`

| Field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the list. |
| `name` Req | string | |
| `version` | int64 | Send it back in a `ListUpdateRequest`. It prevents an edit collision. |
| `filmCount` Req | int32 | |
| `published` Req | boolean | Other members can see the list. |
| `ranked` Req | boolean | |
| `hasEntriesWithNotes` Req | boolean | |
| `descriptionLbml` | string | The description in LBML. |
| `description` | string | The description as HTML. |
| `tags` | string[] | **DEP** Use `tags2`. |
| `tags2` Req | `Tag[]` | |
| `whenCreated` Req | date-time | |
| `whenPublished` | date-time | |
| `whenUpdated` Req | date-time | |
| `commentPolicy` | `CommentPolicy` | The policy of the owner. To learn whether the viewer may comment, read `ListRelationship.commentThreadState`. |
| `sharePolicy` Req | `SharePolicy` | `Anyone`, `Friends` or `You`. |
| `owner` Req | `MemberSummary` | |
| `collaborators` | `MemberSummary[]` | |
| `clonedFrom` | `ListIdentifier` | |
| `previewEntries` Req | `ListEntrySummary[]` | The first 12 entries only. Call `GET /list/{id}/entries` for the rest and for the notes. |
| `links` Req | `Link[]` | |
| `backdrop` | `Image` | Patron members only. |
| `backdropFocalPoint` | number | |
| `backdropPickerUrl` | url | **FP** |
| `statsFreelyAvailable` Req | boolean | |

### 2.8 `ListSummary`

These fields keep the meaning that 2.7 gives them: `id`, `name`, `version`, `filmCount`, `published`, `ranked`, `descriptionLbml`, `description`, `sharePolicy`, `owner`, `collaborators`, `clonedFrom`, `previewEntries`, `whenCreated`, `whenPublished` and `whenUpdated`. `ListSummary` drops `hasEntriesWithNotes`, `tags2`, `commentPolicy`, `links`, `backdrop` and `statsFreelyAvailable`. It adds two fields.

| Field | Type | Note |
|---|---|---|
| `descriptionTruncated` | boolean | The description is a preview extract. It is cut when the text is long. |
| `entriesOfNote` | `ListEntryOccurrence[]` | Present when the request sets `filmsOfNote`. Each item gives the `rank` of a film of note, or `-1`. |

### 2.9 `ListEntry` and `ListEntrySummary`

`ListEntry` comes from `GET /list/{id}/entries`. `ListEntrySummary` comes from `List.previewEntries`.

| Field | Type | Note |
|---|---|---|
| `entryId` Req | string | The unique ID of the entry in the list. |
| `rank` | int32 | The rank in a ranked list. It counts from 1. |
| `film` Req | `FilmSummary` | **DEP** Use `production`. |
| `production` Req | `ProductionSummary` | The production of the entry. |
| `notesLbml` | string | The notes in LBML. |
| `notes` | string | The notes as HTML. |
| `containsSpoilers` | boolean | |
| `whenAdded` Req | date-time | |
| `posterPickerUrl` | url | **FP** |
| `backdropPickerUrl` | url | **FP** |

`ListEntrySummary` holds `entryId`, `rank` and `film` only. It carries no notes. `ListEntryOccurrence` holds `rank` and `filmId` only.

### 2.10 `ProductionLogEntry`, `FilmLogEntry` and `LogEntrySummary`

There is no schema named `LogEntry`. The log entry object is `ProductionLogEntry`. `FilmLogEntry` extends it and adds two fields. `GET /log-entry/{id}` returns a `FilmLogEntry`.

| Field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the log entry. |
| `production` Req | `ProductionSummary` | The production that the member logged. |
| `name` Req | string | A descriptive title for the entry. |
| `owner` Req | `MemberSummary` | |
| `diaryDetails` | `DiaryDetails` | `diaryDate` and `rewatch`. It is absent when the entry is not a diary entry. |
| `review` | `Review` | It is absent when the entry has no review. |
| `tags` | string[] | **DEP** Use `tags2`. |
| `tags2` Req | `Tag[]` | |
| `whenCreated` Req | date-time | |
| `whenUpdated` Req | date-time | |
| `rating` | number | `0.5` to `5.0`, in steps of `0.5`. |
| `like` Req | boolean | |
| `commentable` Req | boolean | It depends on the review text and on the comment policy of the owner. |
| `commentPolicy` | `CommentPolicy` | |
| `links` Req | `Link[]` | |
| `posterPickerUrl` | url | **FP** |
| `backdrop` | `Image` | Patron members only. |
| `backdropFocalPoint` | number | |
| `backdropPickerUrl` | url | |
| `targeting` | string[] | **FP** |
| `privacyPolicy` Req | `PrivacyPolicy` | The effective policy. It falls back to the default policy of the owner. |
| `configuredPrivacyPolicy` | `PrivacyPolicy` | The policy on the entry itself. The API returns it to the owner only. |

`FilmLogEntry` adds `film` (`FilmSummary`, with a `MemberFilmRelationship` for the owner) and `type` (**DEP**, always `FilmLogEntry`).

`LogEntrySummary` is a different and much smaller object: `id`, `review` (boolean), `diaryEntry` (boolean), `rating`, `like` and `privacyPolicy`. The two boolean fields say whether a review or a diary entry exists. They are not objects.

### 2.11 `Review`

`Review` is not a top-level entity. It sits inside `ProductionLogEntry.review`. The review endpoints are the `/log-entry/{id}` endpoints.

| Field | Type | Note |
|---|---|---|
| `lbml` Req | string | The review in LBML. |
| `text` Req | string | The review as HTML. |
| `originalLbml` | string | The text before the moderation, for a moderated review. |
| `containsSpoilers` Req | boolean | |
| `spoilersLocked` Req | boolean | A moderator locked the spoiler flag. |
| `moderated` Req | boolean | A moderator removed the review. |
| `whenReviewed` | date-time | The first publication of the review. |
| `originalLanguageCode` | string | BCP-47. |
| `languageCode` | string | BCP-47. The language of the returned text. |
| `translatedBy` Req | enum | `Original` or `Google`. |
| `translatable` Req | boolean | |
| `truncated` Req | boolean | It is `true` when the text is too long to translate in full. |

### 2.12 `Story` and `StorySummary`

| Field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the story. |
| `name` Req | string | |
| `author` Req | `MemberSummary` | |
| `url` | string | The external URL, if the story links to one. |
| `source` | string | The publication name. |
| `videoUrl` | string | |
| `bodyHtml` | string | A preview extract. It is cut when the text is long. |
| `bodyLbml` | string | The same text in LBML. |
| `whenCreated` Req | date-time | |
| `whenUpdated` | date-time | |
| `image` | `Image` | The hero image. |
| `pinned` Req | boolean | The author pinned the story. |
| `commentPolicy` | `CommentPolicy` | `Story` only. `StorySummary` has no such field. |

`StorySummary` adds `bodyTruncated` (boolean) and drops `commentPolicy`. `GET /stories` returns summaries. `GET /story/{id}` returns the full story.

### 2.13 `Contributor` and `ContributorSummary`

| Field | Type | In `Contributor` | In `ContributorSummary` |
|---|---|---|---|
| `id` Req | string | yes | yes |
| `name` Req | string | yes | yes |
| `tmdbid` | string | yes | yes |
| `poster` | `Image` | yes | yes |
| `customPoster` | `Image` | **DEP** | **DEP** |
| `bio` | string | yes | no |
| `statistics` Req | `ContributorStatistics` | yes | no |
| `links` Req | `Link[]` | yes | no |
| `contributorPosterPickerUrl` | url | **FP** | no |
| `characterName` | string | no | yes, and only when the contribution type is `Actor` |

### 2.14 The small shared objects

| Schema | Fields |
|---|---|
| `Image` | `sizes` Req (`ImageSize[]`). Nothing else. Pick a size yourself. |
| `ImageSize` | `width` Req (int32), `height` Req (int32), `url` Req. |
| `Link` | `type` Req (`letterboxd`, `boxd`, `tmdb`, `imdb`, `justwatch`, `facebook`, `instagram`, `twitter`, `youtube`, `tickets`, `tiktok`, `bluesky`, `threads`), `id` Req, `url` Req, `label`, `checkUrl`. |
| `Tag` | `tag` (**DEP**), `code` Req (the tag code), `displayTag` Req (the text of the tagger). |
| `MemberTag` | `tag` (**DEP**), `code` Req, `displayTag` Req, `counts` Req (`MemberTagCounts`). |
| `ErrorResponse` | `error` Req (boolean), `message` Req (string), `code` (string). Every 4xx and 5xx body uses it. |

## 3. The polymorphic types

Three schemas are abstract. Each one declares a `type` discriminator. Your client must switch on `type`. This is the place where most clients break, so read the three tables with care.

### 3.1 `AbstractComment`

The base holds every field that a comment needs. The concrete schema adds one field: the identifier of the parent object.

| Base field | Type | Note |
|---|---|---|
| `id` Req | string | The LID of the comment or of the reply. |
| `member` Req | `MemberSummary` | The author of the comment. |
| `whenCreated` Req | date-time | |
| `whenUpdated` Req | date-time | |
| `commentLbml` | string | The comment in LBML. |
| `comment` | string | The comment as HTML. |
| `removedByAdmin` Req | boolean | A moderator removed the comment. `comment` is then absent. |
| `removedByContentOwner` Req | boolean | The content owner removed the comment. `comment` is then absent. |
| `deleted` Req | boolean | The author removed the comment. `comment` is then absent. |
| `blocked` Req | boolean | The authenticated member blocked the author. `comment` is then absent. |
| `blockedByOwner` Req | boolean | The content owner blocked the author. `comment` is then absent. |
| `editableWindowExpiresIn` | int64 | **DEP** The seconds that remain in the edit window. |
| `whenEditingWindowExpires` | date-time | The end of the edit window, for a comment of the authenticated member. |

Five boolean flags can hide the text. Always test them before you render `comment`.

| `type` value | Concrete schema | The field it adds |
|---|---|---|
| `ListComment` | `ListComment` | `list` (`ListIdentifier`) |
| `ReviewComment` | `ReviewComment` | `review` (`ReviewIdentifier`) |
| `StoryComment` | `StoryComment` | `story` (`StoryIdentifier`) |

### 3.2 `AbstractActivity`

The base holds `member` (`MemberSummary`) and `whenCreated` (date-time). `ActivityResponse.items` returns the array. `GET /member/{id}/activity` returns it.

The discriminator is `type`, of the enum `ActivityType`. It has 22 values. **The API reference publishes no concrete schema for any of them.** Treat every field beyond `member` and `whenCreated` as unknown until you see it in a live response.

| Group | `type` values |
|---|---|
| Film and production | `FilmWatchActivity`, `FilmLikeActivity`, `FilmRatingActivity`, `WatchlistActivity`, `ProductionWatchActivity`, `ProductionLikeActivity`, `ProductionRatingActivity`, `ProductionWatchlistActivity` |
| Diary and review | `DiaryEntryActivity`, `ReviewActivity`, `ReviewCommentActivity`, `ReviewLikeActivity`, `ReviewResponseActivity` |
| List | `ListActivity`, `ListCommentActivity`, `ListLikeActivity` |
| Story | `StoryActivity`, `StoryCommentActivity`, `StoryLikeActivity` |
| Member | `FollowActivity` |
| Combined | `CombinedPersonActivity`, `CombinedIncomingActivity` |

The `ActivityFilter` enum holds the same 22 values. Pass it in the `include` parameter to limit the types that arrive. The production values duplicate the film values, so handle both names for the same event.

### 3.3 `AbstractSearchItem`

The base holds one field: `score` (number), the relevancy value for the sort order. `SearchResponse.items` returns the array. `GET /search` returns it.

The discriminator is `type`, a string. The values come from the `SearchResultType` enum. **The API reference publishes no concrete schema for any of them.**

| `type` value | The entity it carries |
|---|---|
| `FilmSearchItem` | a film |
| `ContributorSearchItem` | a cast or crew member |
| `MemberSearchItem` | a member |
| `ListSearchItem` | a list |
| `ReviewSearchItem` | a log entry that has a review |
| `StorySearchItem` | a story |
| `TagSearchItem` | a tag |
| `ArticleSearchItem` | an article |
| `PodcastSearchItem` | a podcast |
| `ShowSearchItem` | a show |

Pass `include` on `GET /search` to restrict the result types. Restrict them to the types that you can render. This is the cheapest way to keep the dispatch safe.

### 3.4 Two more discriminated schemas

| Schema | Discriminator | Values |
|---|---|---|
| `Production` | `type` (string) | `Film` selects `Film`. The docs publish no other value. |
| `FeaturedContentItem` | `type` (`FeaturedContentType`) | `FeaturedTrailer` and `FeaturedLink`. The docs publish no concrete schema for either value. |

### 3.5 The dispatch pattern

```js
// One switch for each abstract type. Never assume a shape from the array name.
function renderComment(c) {
  switch (c.type) {
    case "ListComment":   return renderListComment(c, c.list.id);
    case "ReviewComment": return renderReviewComment(c, c.review.id);
    case "StoryComment":  return renderStoryComment(c, c.story.id);
    default:              return null; // A new type arrived. Skip it.
  }
}

// The text of a comment can be absent. Test the five flags first.
function commentText(c) {
  const hidden = c.deleted || c.removedByAdmin || c.removedByContentOwner ||
                 c.blocked || c.blockedByOwner;
  return hidden ? null : c.comment;
}

// Activity and search items carry no published schema. Guard every access.
function activityKey(a) {
  if (typeof a.type !== "string") return null;
  if (!KNOWN_ACTIVITY_TYPES.has(a.type)) return null; // Skip the unknown type.
  return `${a.type}:${a.member.id}:${a.whenCreated}`;
}
```

Three rules for a safe dispatch:

1. Return `null` for an unknown `type`. Do not throw an error. Letterboxd adds values.
2. Read the parent identifier from the concrete field, not from the request context.
3. Log each unknown `type` value once. It tells you when the API grows.

## 4. The request bodies

Every write endpoint takes JSON. A PATCH body may hold all of the current values, or only the values that you change. The API ignores a field that breaks a business rule, and it reports the reason in `messages`.

### 4.1 `LogEntryCreationRequest` – `POST /log-entries`

| Field | Required | Type | Note |
|---|---|---|---|
| `filmId` | **yes** | string | The LID of the film. |
| `diaryDetails` | no | `LogEntryCreationRequestDiaryDetails` | It makes the entry a diary entry. |
| `review` | no | `LogEntryCreationRequestReview` | It attaches a review. |
| `rating` | no | number | `0.5` to `5.0`, in steps of `0.5`. |
| `like` | no | boolean | |
| `tags` | no | string[] | |
| `commentPolicy` | no | `CommentPolicy` | |
| `privacyPolicy` | no | `PrivacyPolicy` | `Anyone`, `Friends`, `You` or `Draft`. |

| Nested schema | Fields |
|---|---|
| `LogEntryCreationRequestDiaryDetails` | `diaryDate` **required** (`YYYY-MM-DD`), `rewatch` optional. |
| `LogEntryCreationRequestReview` | `text` **required** (LBML, maximum 100,000 characters), `containsSpoilers` optional. |

Send at least a review or diary details. An entry with neither one returns the code `LogEntryWithNoReviewOrDiaryDetails`.

### 4.2 `LogEntryUpdateRequest` – `PATCH /log-entry/{id}`

Every field is optional. Every field accepts `null`. A `null` removes the part.

| Field | Type | `null` does this |
|---|---|---|
| `diaryDetails` | `LogEntryUpdateRequestDiaryDetails` | It removes the entry from the diary. |
| `review` | `LogEntryUpdateRequestReview` | It removes the review from the entry. |
| `rating` | number | It removes the rating. |
| `like` | boolean | – |
| `tags` | string[] | – |
| `commentPolicy` | `CommentPolicy` | It restores the default of the member. |
| `privacyPolicy` | `PrivacyPolicy` | It restores the default of the member. |

The two nested update schemas hold the same fields as the creation schemas, but nothing is required and each field accepts `null`.

### 4.3 `ListCreationRequest` – `POST /lists`

| Field | Required | Type | Note |
|---|---|---|---|
| `name` | **yes** | string | |
| `published` | **yes** | boolean | |
| `ranked` | **yes** | boolean | |
| `description` | no | string | LBML, maximum 100,000 characters. |
| `tags` | no | string[] | |
| `commentPolicy` | no | `CommentPolicy` | |
| `sharePolicy` | no | `SharePolicy` | |
| `clonedList` | no | string | The LID of the list to clone. Paying members only. |
| `clonedFrom` | no | string | **DEP** Use `clonedList`. |
| `entries` | no | `ListUpdateEntry[]` | The API adds the cloned entries first, then applies these updates. |

### 4.4 `ListUpdateRequest` – `PATCH /list/{id}`

Every field is optional.

| Field | Type | Note |
|---|---|---|
| `version` | int64 | Send the `version` that you read. It prevents a collision. A stale value returns `ListVersionMismatch`. |
| `name`, `published`, `ranked`, `description`, `tags`, `commentPolicy`, `sharePolicy` | as in 4.3 | `commentPolicy` also accepts `null`. |
| `entries` | `ListUpdateEntry[]` | The API inserts an absent entry and updates a present entry. |
| `filmsToRemove` | string[] | **DEP** Send a `DELETE` action entry instead. |

`ListUpdateEntry` drives every list edit:

| Field | Type | Note |
|---|---|---|
| `action` | enum | `ADD`, `DELETE`, `UPDATE`, `CLEAR` or one of the 10 `SORT_*` values. Without an action the API updates a present film and adds an absent film. |
| `film` | string | The LID. It is required for `ADD`. |
| `position` | int32 | It counts from 0. It is required for `UPDATE` and for `DELETE`. |
| `newPosition` | int32 | It counts from 0. It sets the new place of the entry. |
| `rank` | int32 | **DEP** It counts from 1. Use `newPosition`. |
| `notes` | string | LBML, maximum 100,000 characters. |
| `containsSpoilers` | boolean | |

The `SORT_*` values are `SORT_NAME`, `SORT_DIARY_NEWEST`, `SORT_DIARY_OLDEST`, `SORT_RELEASE_NEWEST`, `SORT_RELEASE_OLDEST`, `SORT_RATING_HIGHEST`, `SORT_RATING_LOWEST`, `SORT_AVR_RATING_HIGHEST`, `SORT_AVR_RATING_LOWEST`, `SORT_LENGTH_SHORTEST` and `SORT_LENGTH_LONGEST`.

### 4.5 `MemberSettingsUpdateRequest` – `PATCH /me`

Every field is optional. The body holds the writable half of `MemberAccount`.

| Group | Fields | Note |
|---|---|---|
| Credentials | `emailAddress`, `password`, `currentPassword`, `authenticationCode` | Send `currentPassword` when you change the password. Send `authenticationCode` as well when the member uses two-factor authentication. This group needs the `security:modify` scope. |
| Profile | `givenName`, `familyName`, `pronoun` (the LID), `location`, `website`, `bio` (LBML) | |
| Favorites | `favoriteProductions` (LIDs, maximum four), `favoriteFilms` (**DEP**) | |
| Policies | `commentPolicy`, `privacyPolicy`, `adultContentPolicy`, `posterMode` | Each one is a string, not an enum reference. |
| Privacy | `privateAccount`, `includeInPeopleSection` | |
| Notifications | the `email*` and `pushNotifications*` booleans of 2.6 | The same names as in `MemberAccount`. |

### 4.6 `FilmRelationshipUpdateRequest` – `PATCH /film/{id}/me`

| Field | Type | Note |
|---|---|---|
| `watched` | boolean | `true` also removes the film from the watchlist. `false` fails while a rating, a review or a diary entry exists. Read `messages` for `UnableToRemoveWatch`. |
| `liked` | boolean | |
| `rating` | number or `null` | `0.5` to `5.0`, in steps of `0.5`. A value also sets `watched` to `true`. `null` removes the rating. |
| `inWatchlist` | boolean | |

### 4.7 The small relationship bodies

These bodies take one field. The `/me` endpoints accept the LID of any object of the right kind, so one call covers a film, a list, a review or a story.

| Schema | Endpoint | Field | Note |
|---|---|---|---|
| `RateUpdateRequest` | `PATCH /me/rate/{id}` | `rating` Req, number or `null` | A value also marks the object as watched. |
| `WatchUpdateRequest` | `PATCH /me/watch/{id}` | `watched` Req, boolean | `true` also removes the object from the watchlist. A 409 says that activity blocks the change. |
| `LikeUpdateRequest` | `PATCH /me/like/{id}` | `liked` Req, boolean | A member may not like their own content. |
| `WatchlistUpdateRequest` | `PATCH /me/watchlist/{id}` | `inWatchlist` Req, boolean | |
| `SubscribeUpdateRequest` | `PATCH /me/subscribe/{id}` | `subscribed` Req, boolean or `null` | The API ignores `true` when the member disabled comment notifications. |

Each one of these five endpoints answers 204 with no body. The equivalent per-entity endpoints answer with a full envelope instead.

| Schema | Endpoint | Fields |
|---|---|---|
| `ListRelationshipUpdateRequest` | `PATCH /list/{id}/me` | `liked`, `subscribed`. Both accept `null`. |
| `ReviewRelationshipUpdateRequest` | `PATCH /log-entry/{id}/me` | `liked`, `subscribed`. Both accept `null`. |
| `StoryRelationshipUpdateRequest` | `PATCH /story/{id}/me` | `liked`, `subscribed`. Both accept `null`. |
| `MemberRelationshipUpdateRequest` | `PATCH /member/{id}/me` | `following`, `blocking`, `closeFriend`. A member may not target their own account. |
| `CommentCreationRequest` | `POST /list/{id}/comments`, `POST /log-entry/{id}/comments`, `POST /story/{id}/comments` | `comment` Req. LBML, maximum 100,000 characters. |
| `CommentUpdateRequest` | `PATCH /comment/{id}` | `comment` Req. The edit window must still be open. |
| `ListAdditionRequest` | `PATCH /lists` | `lists` (the target LIDs) and `films` (the LIDs to add to each target). |
| `StoryUpdateRequest` | `PATCH /story/{id}` | `commentPolicy` only. |

## 5. The index of the remaining schemas

These 134 schemas need no field table. Each row gives the purpose and the place of use. "nested" means that no endpoint returns the schema on its own.

| Schema | Purpose | Used by |
|---|---|---|
| `ActivityResponse` | A cursored page of `AbstractActivity`. | members.md, `GET /member/{id}/activity` |
| `AvailabilityType` | The key and the label of an availability type. | films.md |
| `AvailabilityTypesResponse` | The list of availability types. | films.md, `GET /films/availability-types` |
| `CollectRequest` | The `nonce`, `token` and `itemId` of a treasure hunt collect. | me.md, `POST /me/collect-item` |
| `CommentUpdateMessage` | One validation message for a comment write. | comments.md |
| `CommentUpdateResponse` | An envelope. `data` is an `AbstractComment`. | comments.md, `PATCH /comment/{id}` |
| `Contributions` | One contribution type plus its contributors. | nested in `Film.contributions` (**DEP**) |
| `ContributionStatistics` | The film count for one contribution type. | nested in `ContributorStatistics` |
| `ContributorRelationship` | The custom poster of the viewer for a contributor. | contributors.md, `GET /contributor/{id}/me` |
| `ContributorStatistics` | The array of contribution counts. | nested in `Contributor` |
| `CountriesResponse` | The country list. | films.md, `GET /films/countries` |
| `Country` | An ISO 3166-1 code, a name and a flag URL. | nested in `Release` and `Film.countries` |
| `DeregisterPushNotificationsRequest` | One `deviceId`. | me.md |
| `DiaryDetails` | The `diaryDate` and the `rewatch` flag of a log entry. | nested in `ProductionLogEntry` |
| `DisableAccountRequest` | The password, the 2FA code and the mode `Disable` or `Delete`. | me.md, `POST /me/disable` |
| `FavoriteFilmsUpdateRequest` | Up to four film LIDs. **DEP** | me.md |
| `FavoriteProduction` | A favourite production plus the picker URLs. | nested in `Member` |
| `FavoriteProductionsUpdateRequest` | Up to four production LIDs. | me.md |
| `FeaturedContentResponse` | The featured content items. | featured.md |
| `FilmCollection` | A collection: `id`, `name`, `filmCount`, `films`, `links`. | film-collections.md |
| `FilmCollectionsResponse` | A cursored page of collections. | film-collections.md |
| `FilmContribution` | One credit: `type`, `film`, `characterName`, `containsSpoilers`. | nested in `FilmContributionsResponse` |
| `FilmContributionsResponse` | The credits of a contributor, plus metadata and relationships. | contributors.md |
| `FilmContributorMemberRelationship` | A member plus their relationships per contribution type. | nested |
| `FilmContributorMetadata` | The film counts for one contribution type. | nested |
| `FilmContributorRelationship` | A contribution type plus a `FilmsRelationship`. | nested |
| `FilmIdentifier` | A LID wrapper. | nested in `FilmStatistics` |
| `FilmRelationshipUpdateMessage` | One validation message for a film relationship write. | films.md |
| `FilmRelationshipUpdateResponse` | An envelope. `data` is a `ProductionRelationship`. | films.md |
| `FilmsAutocompleteResponse` | Films for an autocomplete field. It has no cursor. | films.md |
| `FilmServicesResponse` | The streaming services. | films.md |
| `FilmsMemberRelationship` | A member plus a `FilmsRelationship`. | nested in `ListEntriesResponse` |
| `FilmsMetadata` | `totalFilmCount` and `filteredFilmCount`. | nested |
| `FilmsRelationship` | A wrapper around `FilmsRelationshipCounts`. | nested |
| `FilmsRelationshipCounts` | The `watches` and `likes` counts for a set of films. | nested |
| `FilmsResponse` | A cursored page of `FilmSummary`. | films.md, members.md |
| `FilmStatistics` | The counts, the rating and the histogram of a film. | films.md |
| `FilmStatisticsCounts` | The six counts of a film. | nested |
| `FilmTrailer` | The YouTube type, ID and URL. | nested in `Production` |
| `ForgottenPasswordRequest` | One `emailAddress`. | authentication.md |
| `FriendFilmRelationshipsResponse` | The relationships of friends. `watchCount` and `watchListCount` return `-1` when the count is too costly. | films.md |
| `Genre` | A LID and a name. | nested |
| `GenresResponse` | The genre list. | films.md |
| `HuntItems` | The treasure hunt items of a production. **FP** | contributors.md |
| `Language` | An ISO 639-1 code and a name. | nested |
| `LanguagesResponse` | The language list. | films.md |
| `ListAddition` | One list, the number of additions and the added LIDs. | nested in `ListAdditionResponse` |
| `ListAdditionResponse` | The result of a batch add. | lists.md, `PATCH /lists` |
| `ListCommentsResponse` | A cursored page of `ListComment`. | lists.md |
| `ListCreateMessage` | One validation message for a list creation. | lists.md |
| `ListCreateResponse` | An envelope. `data` is a `List`. | lists.md, `POST /lists` |
| `ListEntriesResponse` | A cursored page of `ListEntry`, plus metadata and relationships. | lists.md |
| `ListEntryOccurrence` | The `rank` and the `filmId` of a film of note. | nested in `ListSummary` |
| `ListIdentifier` | A LID wrapper. | nested |
| `ListRelationship` | The relationship of the viewer to a list. | lists.md |
| `ListRelationshipUpdateMessage` | One validation message. | lists.md |
| `ListRelationshipUpdateResponse` | An envelope. `data` is a `ListRelationship`. | lists.md |
| `ListsResponse` | A cursored page of `ListSummary`. | lists.md |
| `ListStatistics` | The comment and like counts of a list. | lists.md |
| `ListStatisticsCounts` | The two counts. | nested |
| `ListTopic` | A named group of featured lists. | nested in `TopicsResponse` |
| `ListUpdateMessage` | One validation message for a list update. | lists.md |
| `ListUpdateResponse` | An envelope. `data` is a `List`. | lists.md |
| `LogEntriesResponse` | A cursored page of `FilmLogEntry`. | log-entries.md |
| `LogEntryCreationResponse` | A `FilmLogEntry` plus an optional `videoMessage`. | log-entries.md, `POST /log-entries` |
| `LogEntryUpdateMessage` | One validation message for a log entry write. | log-entries.md |
| `LogEntryUpdateResponse` | `data`, `videoMessage` and `messages`. | log-entries.md |
| `LoginTokenResponse` | A single-use token for the website. | authentication.md |
| `MemberFilmRelationship` | **DEP** The identical `MemberProductionRelationship` replaces it. | films.md, nested in `FilmSummary` |
| `MemberFilmRelationshipsResponse` | A cursored page of member and film relationships. | films.md, log-entries.md |
| `MemberFilmViewingRelationship` | A member, a `ProductionRelationship` and a `LogEntrySummary`. | nested in `FriendFilmRelationshipsResponse` |
| `MemberIdentifier` | A LID wrapper. | nested in `MemberStatistics` |
| `MemberProductionRelationship` | A member plus a `ProductionRelationship`. | nested |
| `MemberRelationship` | The relationship between two members. | members.md |
| `MemberRelationshipUpdateMessage` | One validation message. | members.md |
| `MemberRelationshipUpdateResponse` | An envelope. `data` is a `MemberRelationship`. | members.md |
| `MemberSettingsUpdateMessage` | One validation message for a settings write. | me.md |
| `MemberSettingsUpdateResponse` | An envelope. `data` is a `MemberAccount`. | me.md |
| `MembersResponse` | A cursored page of `MemberSummary`. | members.md |
| `MemberStatistics` | The counts, the histogram and the review years of a member. | members.md |
| `MemberStatisticsCounts` | The 20 counts of a member. | nested |
| `MemberTagCounts` | The five counts of one tag. | nested in `MemberTag` |
| `MemberTagsResponse` | The tags of a member, most used first. | members.md |
| `Minigenre` | A code and a name. **FP** on `Film`. | nested |
| `Nanogenre` | A code and a name. **FP** on `Film`. | nested |
| `NewsItem` | A title, an image, a URL, two descriptions, a season and an episode. | nested in `NewsResponse` |
| `NewsResponse` | A cursored page of news items. | news.md |
| `PrivateNote` | `text`, `textLbml`, `whenCreated` and `whenUpdated`. | nested in the relationship objects |
| `ProductionAvailability` | One store: name, icons, country, URL, types and classification. | nested |
| `ProductionAvailabilityResponse` | Where to watch a production, in order of preference. | films.md |
| `ProductionRelationship` | The relationship of a member to a production. | films.md |
| `Pronoun` | A LID, a label and the five word forms. | nested in `Member` |
| `PronounsResponse` | The pronoun list. | members.md |
| `RatingsHistogramBar` | `rating`, `normalizedWeight` and `count`. | nested in the statistics objects |
| `RegisterPushNotificationsRequest` | A device ID, a device name and a Firebase token. | me.md |
| `RegisterRequest` | The fields of a new account, and the captcha. | members.md, `POST /members/register` |
| `Release` | A release: type, country, language, certification and date. | nested in `Film.releases` (**FP**) |
| `ReportCommentRequest` | A reason and a message. | comments.md |
| `ReportListRequest` | A reason and a message. | lists.md |
| `ReportMemberRequest` | A reason and a message. | members.md |
| `ReportProductionRequest` | A reason and a message. | films.md |
| `ReportReasonMetadata` | One reason: code, priority, HTML text and `messageRequired`. | nested |
| `ReportReasonMetadataResponse` | The reasons for a report form. | comments.md, lists.md, members.md |
| `ReportReviewRequest` | A reason and a message. | log-entries.md |
| `ReviewCommentsResponse` | A cursored page of `ReviewComment`. | log-entries.md |
| `ReviewIdentifier` | A LID wrapper. The LID is the LID of the log entry. | nested |
| `ReviewRelationship` | The relationship of the viewer to a review. | log-entries.md |
| `ReviewRelationshipUpdateMessage` | One validation message. | log-entries.md |
| `ReviewRelationshipUpdateResponse` | An envelope. `data` is a `ReviewRelationship`. | log-entries.md |
| `ReviewStatistics` | The comment and like counts of a review. | log-entries.md |
| `ReviewStatisticsCounts` | The two counts. | nested |
| `SearchResponse` | A cursored page of `AbstractSearchItem`. | search.md |
| `Service` | A LID, a name and two icons. | nested in `FilmServicesResponse` |
| `StoriesResponse` | A cursored page of `StorySummary`. | stories.md |
| `StoryCommentsResponse` | A cursored page of `StoryComment`. | stories.md |
| `StoryIdentifier` | A LID wrapper. | nested |
| `StoryRelationship` | The relationship of the viewer to a story. | stories.md |
| `StoryRelationshipUpdateMessage` | One validation message. | stories.md |
| `StoryRelationshipUpdateResponse` | An envelope. `data` is a `StoryRelationship`. | stories.md |
| `StoryStatistics` | The comment and like counts of a story. | stories.md |
| `StoryStatisticsCounts` | The two counts. | nested |
| `StoryUpdateMessage` | One validation message for a story write. | stories.md |
| `StoryUpdateResponse` | An envelope. `data` is a `Story`. | stories.md |
| `TagCheckRequest` | A tag type and a tag code. | me.md, `GET /me/check-tag` |
| `TagCheckResponse` | The number of taggings that match the new name. | me.md |
| `TagDeleteRequest` | A tag type, a tag code and the raw tag. | me.md, `DELETE /me/delete-tag` |
| `TagsResponse` | Plain string tags, most used first. | members.md |
| `TagUpdateRequest` | A rename. A duplicate code merges the two tags. | me.md, `PATCH /me/update-tag` |
| `Theme` | A code and a name. **FP** on `Film`. | nested |
| `TopicsResponse` | The list topics. | lists.md, `GET /lists/topics` |
| `TreasureHuntItem` | A hint, a name, an image, a found flag and a collect token. **FP** | nested in `HuntItems` |
| `UploadUrlResponse` | A single-use upload URL. | authentication.md |
| `UsernameCheckResponse` | `Available`, `NotAvailable`, `TooShort`, `TooLong` or `Invalid`. | authentication.md |
| `VideoMessage` | A `videoUrl` to play after a log write. | nested in the log entry responses |

## 6. Relationships

| File | What it gives you |
|---|---|
| **schemas-enums.md** | The 30 enums. Read it for `ActivityType`, `CommentThreadState`, `CommentSubscriptionState`, `ContributionType`, `MemberStatus`, `PrivacyPolicy`, `SharePolicy`, `PosterMode`, `ProductionType`, `SearchResultType` and the `*WhereClause` filters. |
| **overview.md** | The base URL, the LID scheme, the request rules, the pagination limits and the meaning of the **FP** mark. |
| **authentication.md** | The OAuth2 flows and the scopes. `client:firstparty` controls every **FP** field. |
| **films.md** | `Film`, `FilmSummary`, `ProductionRelationship`, `FilmStatistics` and the film relationship write. |
| **members.md** | `Member`, `MemberSummary`, `MemberRelationship`, `MemberStatistics` and the activity feed. |
| **me.md** | `MemberAccount`, `MemberSettingsUpdateRequest` and the five small `/me` write bodies. |
| **lists.md** | `List`, `ListSummary`, `ListEntry`, `ListUpdateEntry` and the list write envelopes. |
| **log-entries.md** | `ProductionLogEntry`, `FilmLogEntry`, `Review` and the log entry write bodies. |
| **stories.md** | `Story`, `StorySummary` and `StoryRelationship`. |
| **comments.md** | `AbstractComment` and the comment write bodies. |
| **contributors.md** | `Contributor`, `ContributorSummary` and `FilmContribution`. |
| **film-collections.md** | `FilmCollection`. |
| **search.md** | `AbstractSearchItem` and the `include` parameter. |
| **news.md**, **featured.md** | `NewsItem` and `FeaturedContentItem`. |
