# Letterboxd API: Overview and Conventions
Based on Letterboxd API v0 documentation.

The Letterboxd API gives access to the data of the Letterboxd.com service. This file holds the core conventions. Read it before you write any client code.

## Base URL and endpoint shape

Every endpoint uses HTTPS. An endpoint URL has this form:

```
https://api.letterboxd.com/api/v0/ENDPOINT_PATH
```

| Item | Value |
|---|---|
| Base URL | `https://api.letterboxd.com/api/v0` |
| Transport | HTTPS only |
| Methods | `GET`, `POST`, `PATCH`, `DELETE` |
| Response body | Always a JSON object |
| Auth header | `Authorization: Bearer ACCESS_TOKEN` |
| Write body type | `application/json` |
| Token endpoint body type | `application/x-www-form-urlencoded` |

Each endpoint accepts one method only. The documentation of the endpoint names that method. Do not send a different method.

### The PATCH fallback

Some HTTP clients and some proxies do not support the `PATCH` method. Send a `POST` request with a header instead:

```
X-HTTP-Method-Override: PATCH
```

The API then treats the `POST` request as a `PATCH` request. Use this fallback only if your client cannot send `PATCH`.

## Where the parameters go

| Method | Parameter location | Note |
|---|---|---|
| `GET` | The query string | The path parameter stays in the path. |
| `POST` | A JSON request body | Include all required parameters. |
| `PATCH` | A JSON request body | Include only the fields that change. |
| `DELETE` | A JSON request body | Include all required parameters. |

URL-encode every query parameter and every form parameter.

An array parameter uses the exploded form style. Repeat the key one time for each value:

```
GET /api/v0/films?filmId=b8wK&filmId=imdb:tt1396484&perPage=100
```

### PATCH sends only the changed fields

A `PATCH` request is a partial update. Send the fields that change. The API keeps the other fields at their present values.

Do this – change the name of a list only:

```bash
curl -X PATCH "https://api.letterboxd.com/api/v0/list/1a2b3c" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Best of 1982"}'
```

Do not do this – the full object with unchanged fields. The extra fields add risk. A stale value can overwrite a newer value:

```bash
-d '{"name": "Best of 1982", "published": true, "entries": [ ... ], "tags": []}'
```

## LIDs (Letterboxd IDs)

A LID is a Letterboxd ID. It is a short alphanumeric string. The API identifies each entity by its LID: a member, a film, a list, a review, a story and more. The API returns the LID in the `id` property of the entity.

You cannot construct a LID. You must obtain it. There are four documented sources.

| Source | Works for | How |
|---|---|---|
| The `x-letterboxd-identifier` response header | Member, film, review, list | Request the page on `letterboxd.com`. Read the header. |
| The `boxd.it` share URL | Film, review, list | The path part of the URL is the LID. |
| The `boxd.it` share URL in the iOS app | Member | Share the profile of the member. Read the path part. |
| The API response | All entities | Read the `id` property, or the `boxd` entry in `links`. |

### Resolve a URL to a LID with a HEAD request

A HEAD request to the website is the fastest way to get the LID for a known URL. The response header holds the LID. The body does not download.

```bash
curl -sI "https://letterboxd.com/film/the-thing/" | grep -i '^x-letterboxd-identifier:'
# x-letterboxd-identifier: 2b9r
```

The same request works for a member page, a list page and a review page:

```bash
curl -sI "https://letterboxd.com/dave/" | grep -i '^x-letterboxd-identifier:'
```

A small helper in Python:

```python
import requests

def lid_from_url(url: str) -> str | None:
    """Return the LID for a letterboxd.com page URL, or None."""
    response = requests.head(url, allow_redirects=True, timeout=10)
    response.raise_for_status()
    return response.headers.get("x-letterboxd-identifier")

print(lid_from_url("https://letterboxd.com/film/the-thing/"))
```

Do this – cache each LID after you resolve it. A LID is stable.
Do not do this – parse the HTML of the page. Do not guess a LID from the slug of the film.

### An external ID can replace a film LID

The `/films` endpoint accepts external IDs in the `filmId` parameter. Prefix a TMDB ID with `tmdb:`. Prefix an IMDB ID with `imdb:`. Use this if you hold external IDs and no LIDs. The limit is 100 IDs for each request.

```
GET /api/v0/films?filmId=tmdb:1091&filmId=imdb:tt0084787
```

## Pagination

Cursored endpoints use two query parameters and return the cursor for the next page.

| Item | Type | Meaning |
|---|---|---|
| `cursor` | string (query) | The pagination cursor. Omit it for the first page. |
| `perPage` | int32 (query) | The items for each page. The default is `20`. The maximum is `100`. |
| `next` | string (response) | The cursor for the next page. |
| `items` | array (response) | The objects on this page. |
| `itemCount` | int32 (response) | The count of items, if the endpoint supplies it. |

The loop is simple. Omit `cursor` on the first request. Read `next` from the response. Send that value as `cursor` on the next request. Stop when the response has no `next` value.

The cursor is an opaque string. Do not parse it. Do not build a cursor from an offset or a page number.

### The 100,000 object cap

The API stops paginated data at 100,000 objects. Letterboxd enforces this limit to stop a full copy of the dataset. Your loop reaches the end of the data before that point, or it reaches the cap.

Design for the cap. Narrow the result set with filters and with a sort order. Do not plan a feature that reads a complete dataset.

### A correct cursor loop (Python)

```python
import requests

BASE = "https://api.letterboxd.com/api/v0"
HARD_CAP = 100_000  # The API stops paginated data at this count.

def paginate(path, token, params=None):
    """Yield each item from a cursored endpoint."""
    params = dict(params or {})
    params.pop("cursor", None)   # The first request has no cursor.
    params["perPage"] = 100      # The maximum page size. It cuts the request count.
    headers = {"Authorization": f"Bearer {token}"}
    seen = 0

    while True:
        response = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        page = response.json()

        for item in page.get("items", []):
            yield item
            seen += 1

        cursor = page.get("next")
        if not cursor:
            return               # No next cursor. This page is the last page.
        if seen >= HARD_CAP:
            return               # The API gives no more data after the cap.
        params["cursor"] = cursor

for film in paginate("/films", TOKEN, {"sort": "FilmPopularity"}):
    print(film["id"], film["name"])
```

Do this – set `perPage=100` for a bulk read. Fewer requests give a faster result.
Do not do this – increase `perPage` above 100. The API rejects a larger value.

## Error handling

An error response is an `ErrorResponse` object.

| Property | Type | Required | Meaning |
|---|---|---|---|
| `error` | boolean | Yes | Always `true` on an error. |
| `message` | string | Yes | The text of the error. |
| `code` | string | No | A machine-readable code, if the API supplies one. |

The HTTP status code carries the primary meaning.

| Status | Meaning | Your action |
|---|---|---|
| `200` | Success. The body is the response schema of the endpoint. | Parse the body. |
| `400` | Bad request. A parameter is absent, or a value is invalid. | Correct the request. A retry of the same request fails again. |
| `403` | The request was not allowed. | See the causes below. |
| `404` | No entity matches the LID. A member can also opt out of the API. | Do not retry. Treat the entity as absent. |
| `429` | Too many requests of this type. | Wait. Then retry. |

A `403` status has several causes. Read the `message` property to separate them:

- The signed-in member has no permission for the private content.
- The endpoint or the parameter is First Party. See the section below.
- The content belongs to a different member.
- The time window for the action closed, for example the window to delete a comment.
- The member gave an incorrect password or an incorrect two-factor code.

A `404` on a member endpoint has two causes. The member does not exist, or the member opted out of the API. The API does not separate the two. Show a neutral message to your user.

The v0 endpoint documentation lists `400`, `403`, `404` and `429`. Treat a `401` status as an expired or invalid access token. Refresh the token. Then retry the request one time. See `authentication.md`.

```python
import requests

def call(method, url, token, **kwargs):
    response = requests.request(
        method, url, headers={"Authorization": f"Bearer {token}"}, timeout=30, **kwargs
    )
    if response.ok:
        return response.json()

    # An error body is an ErrorResponse. A 429 body can be empty.
    try:
        body = response.json()
    except ValueError:
        body = {}
    message = body.get("message", response.reason)
    raise RuntimeError(f"{response.status_code} {message} (code={body.get('code')})")
```

## Images

An image comes as an `Image` object. The object holds one array only.

| Schema | Property | Type | Meaning |
|---|---|---|---|
| `Image` | `sizes` | `ImageSize[]` | The available sizes of the image. |
| `ImageSize` | `width` | int32 | The width in pixels. |
| `ImageSize` | `height` | int32 | The height in pixels. |
| `ImageSize` | `url` | url (string) | The URL of the image file. |

Select a size from the `sizes` array. Compare the `width` value against the width of your layout. Take the smallest size that is equal to or larger than your target. Fall back to the largest size.

```python
def pick_size(image, target_width):
    """Return the URL of the smallest size that fits the target width."""
    sizes = sorted(image.get("sizes", []), key=lambda size: size["width"])
    if not sizes:
        return None
    for size in sizes:
        if size["width"] >= target_width:
            return size["url"]
    return sizes[-1]["url"]   # The target is larger than each available size.
```

Do this – read the URL from the `sizes` array for each request.
Do not do this – store an image URL for a long time. Do not edit the URL to change the size. Do not build a URL from a pattern. Letterboxd can change the host, the path and the set of sizes.

Poster and avatar notes:

- `poster` on a film has a 2:3 aspect ratio. It holds one obfuscated image only if the `adult` flag is `true`.
- `adultPoster` holds the unobfuscated image. The API populates it only if the `adult` flag is `true`. It can contain adult content.
- `contextualPoster` holds the poster for the present context. An example is the poster that a member chose for a review. Prefer it in a list view or a review view.
- An avatar has no enforced aspect ratio. Center-crop the avatar to a square if it is not 1:1.

## First Party restrictions

Letterboxd marks some endpoints, some parameters and some schema properties as **First Party**. These items are available to the apps of Letterboxd only. Licensing agreements for the film data cause this restriction.

A third-party client cannot use them. A call to a First Party endpoint returns a permission error (`403`). A First Party property does not appear in the response body of a third-party client. The value is absent, not empty.

Check for the First Party marker before you design a feature around an endpoint, a parameter or a field. A feature that needs a First Party field cannot ship in a third-party client.

Examples of First Party properties on film schemas:

| Property | Content |
|---|---|
| `originalName` | The original non-English title. |
| `alternativeNames` | The other names of the film. |
| `countries` | The production countries. |
| `productionLanguage`, `languages` | The language data. |
| `releases` | The release information. |
| `themes`, `minigenres`, `nanogenres` | The fine-grained classifications. |
| `posterPickerUrl`, `backdropPickerUrl` | The custom image picker URLs. |

The OAuth2 Password flow is also first-party only. A third-party client uses the Client Credentials flow or the Authorization Code flow. See `authentication.md`.

## Identifier schemas

Several responses return a small wrapper object that holds one LID. Use it to find the affected entity after a write operation.

| Schema | Property | The LID refers to |
|---|---|---|
| `FilmIdentifier` | `id` (string, required) | A film. |
| `MemberIdentifier` | `id` (string, required) | A member. |
| `ListIdentifier` | `id` (string, required) | A list. |
| `ReviewIdentifier` | `id` (string, required) | A log entry. The review LID is the LID of its log entry. |
| `StoryIdentifier` | `id` (string, required) | A story. |

Read the `ReviewIdentifier` row again. A review is part of a log entry. Send that LID to the log entry endpoints. See `log-entries.md`.

## Links

Many entities include a `links` array of `Link` objects.

| Property | Type | Meaning |
|---|---|---|
| `type` | enum | One of `letterboxd`, `boxd`, `tmdb`, `imdb`, `justwatch`, `facebook`, `instagram`, `twitter`, `youtube`, `tickets`, `tiktok`, `bluesky`, `threads`. |
| `id` | string | The object ID on the destination site. |
| `url` | url (string) | The full URL on the destination site. |
| `label` | string | An optional label. It can be absent or empty. |
| `checkUrl` | string | An optional check URL. |

Use the `letterboxd` link for the web page of the entity. Use the `boxd` link for a short share URL. Use the `tmdb` link or the `imdb` link to join Letterboxd data to an external dataset. Do not build these URLs yourself.

## Relationships

| File | Read it when you |
|---|---|
| `authentication.md` | Choose an OAuth2 flow, request scopes or refresh a token. |
| `films.md` | Fetch films, film details, genres, statistics or availability. |
| `log-entries.md` | Read or write diary entries, ratings and reviews. |
| `lists.md` | Read, create or update lists and list entries. |
| `members.md` | Read member profiles, activity, watchlists and relationships. |
| `me.md` | Act for the authenticated member. |
| `search.md` | Search across films, members, lists and other types. |
| `stories-and-comments.md` | Read or write stories and comment threads. |
| `schemas-entities.md` | Check the exact properties of a response object. |
| `schemas-enums.md` | Check the allowed values of an enum parameter. |
