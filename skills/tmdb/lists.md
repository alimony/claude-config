# TMDB: Lists
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Read this first: v3 lists or v4 lists?

TMDB has two list APIs. The v3 list methods still work, but TMDB puts every new list feature in v4 only. Decide this before you write any code, because the two APIs use different auth and different data models.

| Capability | v3 lists | v4 lists |
| --- | --- | --- |
| Movies on a list | Yes | Yes |
| TV series on a list (mixed media) | No | Yes |
| Private lists | No | Yes |
| Comments per item | No | Yes |
| Sort options | No | Yes, several |
| Bulk add or remove in one request | No, one `media_id` per request | Yes, "unlimited" items per request |
| Paginated list details with `total_pages` | No envelope, see the gotcha below | Yes |
| Speed | Slower | Faster |
| Auth | v3 `session_id` | v4 user access token |

**Use v4 lists for new work.** Only three reasons justify v3 lists:

1. The app already holds a v3 `session_id` and you do not want a second auth flow.
2. The list holds movies only, forever.
3. You must read a legacy v3 list that other TMDB users already follow.

Read `./authentication.md` for both flows. A v3 `session_id` does not work on v4 endpoints, and a v4 access token does not create a v3 session.

**v3 lists hold movies only.** The write methods are `Add Movie` and `Remove Movie`. Every list that v3 creates gets `list_type: "movie"`. You cannot put a TV series on a v3 list. If your product needs TV series on a list, stop here and use v4.

## Core concepts

* A **list** is a public, user-owned collection of movies. Each list has a numeric `list_id`.
* The **owner** creates, edits and deletes the list. TMDB checks ownership through the `session_id`.
* **Reads are public.** List details, item status, and the "which lists hold this movie" endpoints need only your read access token.
* **Writes need a `session_id`.** Create, add, remove, clear and delete all fail without one.
* Every v3 write returns a small **status envelope**, not the changed object. See "Response envelope and status codes".
* A list holds an `iso_639_1` language and a `poster_path`. TMDB builds the poster from the first items. Read `./images-and-configuration.md` to make a poster URL.

## Quick reference: every v3 list endpoint

| Method | Path | Purpose | Needs `session_id` |
| --- | --- | --- | --- |
| POST | `/3/list` | Create a list | Yes |
| GET | `/3/list/{list_id}` | Get list details and its items | No |
| POST | `/3/list/{list_id}/add_item` | Add one movie | Yes |
| POST | `/3/list/{list_id}/remove_item` | Remove one movie | Yes |
| GET | `/3/list/{list_id}/item_status` | Check if a movie is on the list | No |
| POST | `/3/list/{list_id}/clear` | Remove every item | Yes, plus `confirm=true` |
| DELETE | `/3/list/{list_id}` | Delete the list | Yes |
| GET | `/3/account/{account_id}/lists` | Get the lists a user owns | Yes |
| GET | `/3/movie/{movie_id}/lists` | Get the lists that hold a movie | No |
| GET | `/3/tv/{series_id}/lists` | Get the lists that hold a TV series | No |

### Parameters

| Parameter | Where | Applies to | Notes |
| --- | --- | --- | --- |
| `list_id` | path | all `/3/list/...` methods | integer |
| `session_id` | query | create, add, remove, clear, delete, account lists | required for every write |
| `confirm` | query | clear | boolean, default `false`, you must send `true` |
| `page` | query | details, account lists, movie lists, TV lists | integer, default `1` |
| `language` | query | details, item status, movie lists, TV lists | default `en-US` |
| `movie_id` | query | item status | integer |
| `media_id` | JSON body | add item, remove item | integer, the movie id |
| `name`, `description`, `language` | JSON body | create | `language` here is a short code such as `en` |

## Setup

Set two environment variables. Get the read access token and the session id from `./authentication.md`.

```bash
export TMDB_TOKEN="<v3 read access token>"
export TMDB_SESSION_ID="<v3 session id>"
```

Every example below uses this Python helper:

```python
import os
import requests

BASE = "https://api.themoviedb.org/3"
SESSION = os.environ["TMDB_SESSION_ID"]
HEADERS = {
    "Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
    "Content-Type": "application/json;charset=utf-8",
    "Accept": "application/json",
}

def get(path, **params):
    r = requests.get(f"{BASE}{path}", params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def post(path, body=None, **params):
    params["session_id"] = SESSION
    r = requests.post(f"{BASE}{path}", params=params, json=body or {},
                      headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()
```

## The full v3 lifecycle

### 1. Create a list

Send the body as raw JSON. The `language` field takes a short code, for example `en`.

```bash
curl -s -X POST "https://api.themoviedb.org/3/list?session_id=$TMDB_SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H "Content-Type: application/json;charset=utf-8" \
  -d '{"name":"My awesome test list","description":"Just an awesome list.","language":"en"}'
```

```json
{
  "status_message": "The item/record was created successfully.",
  "success": true,
  "status_code": 1,
  "list_id": 5861
}
```

```python
created = post("/list", {
    "name": "My awesome test list",
    "description": "Just an awesome list.",
    "language": "en",
})
list_id = created["list_id"]      # keep this id, you need it for every other call
```

Store `list_id` in your own database. The create response is the only place TMDB gives it to you directly.

### 2. Read the list details, with pagination

The details endpoint is public. It returns the list metadata and an `items` array of full movie objects.

```bash
curl -s "https://api.themoviedb.org/3/list/1?language=en-US&page=1" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Response shape:

```json
{
  "created_by": "travisbell",
  "description": "The idea behind this list is to collect the live action comic book movies...",
  "favorite_count": 0,
  "id": "1",
  "item_count": 59,
  "iso_639_1": "en",
  "name": "The Marvel Universe",
  "poster_path": "/coJVIUEOToAEGViuhclM7pXC75R.jpg",
  "items": [ { "id": 634649, "media_type": "movie", "title": "Spider-Man: No Way Home", "...": "..." } ]
}
```

The response holds **no** `page`, `total_pages` or `total_results` field, although the endpoint accepts `page`. Use `item_count` as the total and count what you receive:

```python
def iter_list_items(list_id, language="en-US"):
    """Yield every movie on a v3 list. Works whether or not the API pages the items."""
    page, seen = 1, 0
    while True:
        data = get(f"/list/{list_id}", language=language, page=page)
        items = data.get("items") or []
        if not items:
            return
        for item in items:
            yield item
        seen += len(items)
        if seen >= data["item_count"]:
            return
        page += 1

for movie in iter_list_items(1):
    print(movie["id"], movie["title"])
```

The loop stops on an empty page and on a full count. It therefore stays correct if TMDB changes the page size. Read `./localization.md` for what `language` does to `title` and `overview`.

### 3. Add a movie

The body key is `media_id`, not `movie_id`.

```bash
curl -s -X POST "https://api.themoviedb.org/3/list/5861/add_item?session_id=$TMDB_SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H "Content-Type: application/json;charset=utf-8" \
  -d '{"media_id":18}'
```

```json
{ "status_code": 12, "status_message": "The item/record was updated successfully." }
```

```python
post(f"/list/{list_id}/add_item", {"media_id": 550})
```

JavaScript:

```js
const url = new URL(`https://api.themoviedb.org/3/list/${listId}/add_item`);
url.searchParams.set("session_id", sessionId);

const res = await fetch(url, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json;charset=utf-8",
  },
  body: JSON.stringify({ media_id: 550 }),
});
const data = await res.json();   // { status_code: 12, status_message: "..." }
```

v3 adds one movie per request. To add 40 movies you send 40 requests. Add a small delay between them, or move to v4, which imports many items in one request.

### 4. Check if a movie is on the list

This read is public. It costs one cheap request and it prevents duplicate work.

```bash
curl -s "https://api.themoviedb.org/3/list/1/item_status?movie_id=550" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{ "id": 1, "item_present": true }
```

```python
def is_on_list(list_id, movie_id):
    return get(f"/list/{list_id}/item_status", movie_id=movie_id)["item_present"]

if not is_on_list(list_id, 550):
    post(f"/list/{list_id}/add_item", {"media_id": 550})
```

Note the inconsistent name. The query parameter here is `movie_id`. The body key for add and remove is `media_id`.

### 5. Remove a movie

```bash
curl -s -X POST "https://api.themoviedb.org/3/list/5861/remove_item?session_id=$TMDB_SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H "Content-Type: application/json;charset=utf-8" \
  -d '{"media_id":18}'
```

```json
{ "status_code": 13, "status_message": "The item/record was deleted successfully." }
```

Remove uses `POST`, not `DELETE`. Only the whole-list delete uses the `DELETE` method.

### 6. Clear the list

**Warning: `clear` removes every item at once. TMDB gives you no undo and no backup. Save the item ids first if you may need them.**

Send `confirm=true` in the query string. The default is `false`, and the call fails without it.

```python
# Save a copy first.
backup = [item["id"] for item in iter_list_items(list_id)]

post(f"/list/{list_id}/clear", confirm="true")
```

```bash
curl -s -X POST "https://api.themoviedb.org/3/list/5861/clear?session_id=$TMDB_SESSION_ID&confirm=true" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{ "status_code": 12, "status_message": "The item/record was updated successfully." }
```

Clear reports status code 12, "updated", not 13. The list survives. Only the items go.

### 7. Delete the list

**Warning: `delete` destroys the list and its `list_id` permanently. Other TMDB users lose the link. Ask the user to confirm in your own UI before you send this request.**

```bash
curl -s -X DELETE "https://api.themoviedb.org/3/list/5861?session_id=$TMDB_SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{ "status_code": 12, "status_message": "The item/record was updated successfully." }
```

```python
r = requests.delete(f"{BASE}/list/{list_id}", params={"session_id": SESSION},
                    headers=HEADERS, timeout=10)
r.raise_for_status()
```

Delete also returns status code 12, not 13. Do not test for 13 here.

## Read the lists a user owns

Use the account endpoint. You need the `account_id` and a `session_id` from `./authentication.md`.

```bash
curl -s "https://api.themoviedb.org/3/account/548/lists?page=1&session_id=$TMDB_SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{
  "page": 1,
  "results": [
    { "id": 1, "name": "The Marvel Universe", "description": "...", "item_count": 59,
      "favorite_count": 0, "iso_639_1": "en", "list_type": "movie",
      "poster_path": "/coJVIUEOToAEGViuhclM7pXC75R.jpg" }
  ],
  "total_pages": 3,
  "total_results": 42
}
```

This endpoint uses the normal paginated envelope, so the page loop is simple:

```python
def all_account_lists(account_id):
    page = 1
    while True:
        data = get(f"/account/{account_id}/lists", page=page, session_id=SESSION)
        yield from data["results"]
        if page >= data["total_pages"]:
            return
        page += 1
```

`results` holds list summaries only. Each summary gives `item_count`, but not the items. Call the details endpoint for the items. Read `./user-account-and-ratings.md` for the other account collections, such as favorites and the watchlist.

## Read the lists that hold a movie or a TV series

Both endpoints are public reads and both use the paginated envelope.

```bash
# Lists that hold Fight Club (movie 550)
curl -s "https://api.themoviedb.org/3/movie/550/lists?page=1" \
  -H "Authorization: Bearer $TMDB_TOKEN"

# Lists that hold Game of Thrones (series 1399)
curl -s "https://api.themoviedb.org/3/tv/1399/lists?page=1" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```python
movie_lists = get("/movie/550/lists", page=1)
tv_lists = get("/tv/1399/lists", page=1)
print(movie_lists["total_results"], tv_lists["total_results"])
```

Both responses add the subject id at the top level, next to `page`, `results`, `total_pages` and `total_results`. Two small differences exist between them:

| Field | `/3/movie/{movie_id}/lists` | `/3/tv/{series_id}/lists` |
| --- | --- | --- |
| `list_type` | present, `"movie"` | absent |
| `iso_3166_1` | absent | present, for example `"US"` |

A TV series can only sit on a v4 list, because v3 lists hold movies only. The TV endpoint therefore returns lists that your v3 write methods cannot edit. Read them, and edit them with the v4 API. You can also request these lists with `append_to_response=lists` on the movie or series detail call – see `./append-to-response.md`, `./movies.md` and `./tv-series.md`.

## Response envelope and status codes

Every v3 write returns the same small object. It never returns the changed list.

```json
{ "status_code": 12, "status_message": "The item/record was updated successfully." }
```

| `status_code` | `status_message` | You see it on |
| --- | --- | --- |
| 1 | The item/record was created successfully. | `POST /3/list` (this response also adds `success` and `list_id`) |
| 12 | The item/record was updated successfully. | `add_item`, `clear`, `DELETE /3/list/{list_id}` |
| 13 | The item/record was deleted successfully. | `remove_item` |

Read the HTTP status too. A `200` with a status code above means success. A `401` means a bad or expired `session_id`, or a bad token. A `404` means a wrong `list_id`. Read `./getting-started.md` for the shared error format and the rate limit rules.

Check both layers:

```python
def assert_ok(payload, expected):
    if payload.get("status_code") != expected:
        raise RuntimeError(payload.get("status_message", "unknown TMDB error"))

assert_ok(post(f"/list/{list_id}/add_item", {"media_id": 550}), 12)
```

## Best practices and anti-patterns

**Do this: send the body as raw JSON.**

```python
requests.post(url, json={"media_id": 550}, headers=HEADERS)
```

**Don't do this: copy the `RAW_BODY` wrapper out of the OpenAPI definition.** The TMDB reference shows a `RAW_BODY` property because of the way its documentation tool models a raw JSON body. `RAW_BODY` is not a real field. A body such as `{"RAW_BODY": "{\"media_id\": 550}"}` fails.

| Do this | Don't do this |
| --- | --- |
| Check `item_status` before you add a movie. The check is a public read and it keeps the list clean. | Add the same movie twice and hope TMDB removes the duplicate. |
| Keep the `list_id` from the create response in your database. | Search the account lists by name to find your list again. Names are not unique. |
| Cache the list details. A list changes rarely and the response is large. | Call the details endpoint inside a render loop. |
| Ask the user to confirm in your own UI before `clear` or `delete`. | Treat `confirm=true` as the user confirmation. That flag protects the API, not your user. |
| Move to v4 when you need TV series, private lists or bulk import. | Build a "mixed" list in v3 and keep the TV ids somewhere else. The list then breaks on the TMDB website. |

## Common pitfalls

* **The body key is `media_id`, the query key is `movie_id`.** Add and remove use `media_id` in the JSON body. Item status uses `movie_id` in the query string.
* **`clear` needs `confirm=true`.** The default is `false`. The call does nothing useful without the flag.
* **`clear` and `delete` both return status code 12.** Do not test for 13 after a delete. Only `remove_item` returns 13.
* **`remove_item` uses POST.** Only the whole-list delete uses the HTTP `DELETE` method.
* **List details returns no pagination envelope.** There is no `total_pages`. Use `item_count`, and stop on an empty `items` array.
* **The `id` type changes between endpoints.** List details returns `"id": "1"`, a string. Account lists and movie lists return `"id": 1`, an integer. Cast the value before you compare it.
* **`language` means two things.** In the create body it is a short code such as `en`. In the query string of a read it is a full code such as `en-US`.
* **v3 has no update method.** You cannot rename a v3 list or change its description through the API. Use v4, or delete and create again, which changes the `list_id`.
* **Writes need a user session, not just an API key.** A read access token alone gets a 401 on create, add, remove, clear and delete.
* **v3 lists are always public.** Never put private data in a list name or description.
* **One request per item is slow.** Respect the rate limits in `./getting-started.md` when you import many movies.

## Related skill files

| File | Why you need it |
| --- | --- |
| `./authentication.md` | Get the read access token, the `session_id` and the v4 user access token |
| `./getting-started.md` | Base URL, error format, rate limits |
| `./user-account-and-ratings.md` | Account id, favorites, watchlist, rated items |
| `./movies.md` | Movie ids and movie details, plus `append_to_response=lists` |
| `./tv-series.md` | Series ids and series details, plus `append_to_response=lists` |
| `./search-and-find.md` | Find the `media_id` values that you add to a list |
| `./discover.md` | Build a candidate set of movies for a new list |
| `./images-and-configuration.md` | Build a full URL from the list `poster_path` |
| `./localization.md` | Choose the right `language` value for reads |
| `./append-to-response.md` | Fetch a movie and its lists in one request |
| `./trending-and-popular.md` | Seed a list from trending or popular movies |
