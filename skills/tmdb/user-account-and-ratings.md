# TMDB: User Account, Favorites, Watchlist and Ratings
Based on TMDB API v3 documentation (developer.themoviedb.org).

**Every endpoint on this page needs a user credential.** Send a `session_id` (a logged-in TMDB account) or a `guest_session_id` (a limited anonymous session). Your API key or read access token alone is not enough – it identifies your application, not the user. Read `./authentication.md` first and get a session. This page shows you what to do with that session.

## 1. Core concepts

**Two credentials travel together.** Send the application credential in the `Authorization: Bearer <access_token>` header (or as `api_key` in the query string). Send the user credential as the `session_id` or `guest_session_id` query parameter. TMDB rejects the request with status code 3 or 17 if the user credential is missing or dead.

**Two session types.**

| Session type | Query parameter | Can rate | Can favorite / watchlist | Can read account details or lists | Expiry |
| --- | --- | --- | --- | --- | --- |
| Account session | `session_id` | Yes | Yes | Yes | Until you delete it |
| Guest session | `guest_session_id` | Yes (movie, TV, episode) | No | No | 60 minutes after the last use |

**The account_id.** Every `/3/account/...` path needs the integer account id of the user. Fetch it once from the account details endpoint and cache it with the session. Do not hard-code it.

**Three per-item user states.** TMDB stores `favorite`, `watchlist` and `rated` for each item. Read all three with one `account_states` call. Write them with three different endpoints.

**One endpoint adds and removes.** The favorite and watchlist endpoints are toggles that you control with a boolean. There is no DELETE. Ratings are the exception: they use POST to write and DELETE to remove.

**Rating scale.** Values run from 0.5 to 10.0 in steps of 0.5. TMDB rejects any other value.

**Write response envelope.** Every write returns the same small object:

```json
{ "success": true, "status_code": 1, "status_message": "Success." }
```

Check `status_code` first – it is the stable machine-readable field. The OpenAPI examples on these pages show only `status_code` and `status_message`, so treat `success` as a hint and never as the only test.

## 2. Quick reference: every endpoint

`ACC` = `session_id` required. `EITHER` = `session_id` or `guest_session_id`. `LPS` = `language`, `page`, `sort_by`.

| Group | Method | Path | Auth | Other parameters |
| --- | --- | --- | --- | --- |
| account | GET | `/3/account/{account_id}` | ACC | – |
| account | GET | `/3/account/{account_id}/lists` | ACC | `page` – see `./lists.md` |
| favorites | POST | `/3/account/{account_id}/favorite` | ACC | body: `media_type`, `media_id`, `favorite` |
| favorites | GET | `/3/account/{account_id}/favorite/movies` | ACC | LPS |
| favorites | GET | `/3/account/{account_id}/favorite/tv` | ACC | LPS |
| watchlist | POST | `/3/account/{account_id}/watchlist` | ACC | body: `media_type`, `media_id`, `watchlist` |
| watchlist | GET | `/3/account/{account_id}/watchlist/movies` | ACC | LPS |
| watchlist | GET | `/3/account/{account_id}/watchlist/tv` | ACC | LPS |
| ratings | POST | `/3/movie/{movie_id}/rating` | EITHER | body: `{"value": 8.5}` |
| ratings | DELETE | `/3/movie/{movie_id}/rating` | EITHER | no body |
| ratings | POST | `/3/tv/{series_id}/rating` | EITHER | body: `{"value": 8.5}` |
| ratings | DELETE | `/3/tv/{series_id}/rating` | EITHER | no body |
| ratings | POST | `/3/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating` | EITHER | body: `{"value": 8.5}` |
| ratings | DELETE | `/3/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating` | EITHER | no body |
| ratings | GET | `/3/account/{account_id}/rated/movies` | ACC | LPS |
| ratings | GET | `/3/account/{account_id}/rated/tv` | ACC | LPS |
| ratings | GET | `/3/account/{account_id}/rated/tv/episodes` | ACC | LPS |
| account-states | GET | `/3/movie/{movie_id}/account_states` | EITHER | returns `id`, `favorite`, `rated`, `watchlist` |
| account-states | GET | `/3/tv/{series_id}/account_states` | EITHER | same four fields |
| account-states | GET | `/3/tv/{series_id}/season/{season_number}/account_states` | EITHER | returns `results`: one `rated` per episode |
| account-states | GET | `/3/tv/{series_id}/season/{season_number}/episode/{episode_number}/account_states` | EITHER | same four fields |
| guest-session | GET | `/3/authentication/guest_session/new` | none | see `./authentication.md` |
| guest-session | GET | `/3/guest_session/{guest_session_id}/rated/movies` | id in path | LPS |
| guest-session | GET | `/3/guest_session/{guest_session_id}/rated/tv` | id in path | LPS |
| guest-session | GET | `/3/guest_session/{guest_session_id}/rated/tv/episodes` | id in path | LPS |

No endpoint rates a season. Rate the episodes instead. The guest rated paths take the id in the **path**, not in the query string.

### Shared query parameters

| Parameter | Values | Default | Notes |
| --- | --- | --- | --- |
| `language` | `en-US`, `de-DE`, … | `en-US` | Translates titles and overviews – see `./localization.md` |
| `page` | 1 to 500 | `1` | 20 results per page |
| `sort_by` | `created_at.asc`, `created_at.desc` | `created_at.asc` | These two values only |
| `session_id` | session string | – | Required on all `/3/account/...` paths |
| `guest_session_id` | guest session string | – | Ratings and account states only |

## 3. Set up a client

```python
import os, requests

BASE = "https://api.themoviedb.org/3"
TOKEN = os.environ["TMDB_ACCESS_TOKEN"]      # v4 read access token
SESSION_ID = os.environ["TMDB_SESSION_ID"]   # from ./authentication.md

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {TOKEN}",
                        "Content-Type": "application/json;charset=utf-8"})

def get(path, **params):
    r = session.get(f"{BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def post(path, body, **params):
    r = session.post(f"{BASE}{path}", params=params, json=body, timeout=10)
    return r.status_code, r.json()

def delete(path, **params):
    r = session.delete(f"{BASE}{path}", params=params, timeout=10)
    return r.status_code, r.json()
```

Set `Content-Type: application/json;charset=utf-8` on every write. The rating endpoints list this header as required.

## 4. How-to patterns

### 4.1 Get the account details and the account_id

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/account/548?session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```json
{
  "id": 548, "username": "travisbell", "name": "Travis Bell",
  "iso_639_1": "en", "iso_3166_1": "CA", "include_adult": false,
  "avatar": { "gravatar": { "hash": "c9e9fc152ee7..." },
              "tmdb": { "avatar_path": "/xy44UvpbTgzs9kWmp4C3fEaCl5h.png" } }
}
```

Use `iso_639_1` and `iso_3166_1` as the default `language` and `region` of the user. Build the avatar URL from `avatar.tmdb.avatar_path` with the image base URL – see `./images-and-configuration.md`. Fall back to Gravatar with `avatar.gravatar.hash` when `avatar_path` is null.

**Bootstrap problem:** the path needs the id, but a new session does not tell you the id. TMDB answers the legacy path `GET /3/account?session_id=...` and returns the account that owns the session. The OpenAPI definition does not list this path, so call it once, cache the `id` next to the session, and use the documented path afterwards.

```python
ACCOUNT_ID = get("/account", session_id=SESSION_ID)["id"]   # cache this with the session
```

### 4.2 Add or remove a favorite

The body has three fields. `media_type` is `movie` or `tv`. `media_id` is the integer TMDB id. `favorite` is the boolean that adds or removes.

```bash
# Add. To remove, send the same request with "favorite":false.
curl --request POST \
     --url 'https://api.themoviedb.org/3/account/548/favorite?session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
     --header 'Content-Type: application/json;charset=utf-8' \
     --data '{"media_type":"movie","media_id":550,"favorite":true}'
```

```python
def set_favorite(media_type, media_id, favorite):
    return post(f"/account/{ACCOUNT_ID}/favorite",
                {"media_type": media_type, "media_id": media_id, "favorite": favorite},
                session_id=SESSION_ID)

set_favorite("movie", 550, True)    # (201, {'success': True, 'status_code': 1, ...})
set_favorite("movie", 550, False)   # (200, {'success': True, 'status_code': 13, ...})
```

### 4.3 Add or remove a watchlist item

The shape is identical, but the flag is named `watchlist`.

```javascript
async function setWatchlist(mediaType, mediaId, watchlist) {
  const url = `https://api.themoviedb.org/3/account/${ACCOUNT_ID}/watchlist?session_id=${SESSION_ID}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}`,
               "Content-Type": "application/json;charset=utf-8" },
    body: JSON.stringify({ media_type: mediaType, media_id: mediaId, watchlist }),
  });
  return res.json();   // { success, status_code, status_message }
}
```

Only `movie` and `tv` are valid media types. You cannot favorite a person, a season or an episode.

### 4.4 Read the favorite and watchlist collections

Four separate endpoints exist because TMDB splits movies from TV.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/account/548/favorite/movies?language=en-US&page=1&sort_by=created_at.desc&session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```python
favorites = get(f"/account/{ACCOUNT_ID}/favorite/movies", session_id=SESSION_ID,
                sort_by="created_at.desc", page=1, language="en-US")
watchlist = get(f"/account/{ACCOUNT_ID}/watchlist/tv", session_id=SESSION_ID,
                sort_by="created_at.desc")
print(favorites["total_results"], favorites["total_pages"])   # 80 4

def all_pages(path, **params):            # read the full collection
    page = 1
    while True:
        data = get(path, page=page, **params)
        yield from data["results"]
        if page >= data["total_pages"] or page >= 500:
            return
        page += 1

for movie in all_pages(f"/account/{ACCOUNT_ID}/watchlist/movies",
                       session_id=SESSION_ID, sort_by="created_at.desc"):
    print(movie["id"], movie["title"], movie["release_date"])
```

Movie results carry `title`, `original_title` and `release_date`. TV results carry `name`, `original_name`, `first_air_date` and `origin_country`. The result objects contain no `media_type` field – you know the type from the endpoint you called.

Sort with `created_at.desc` to show the newest item first. That order matches what the user expects after a write. Stop at `total_pages`. Page 501 fails with status code 22. Add a short pause between pages on large accounts – see the rate-limit notes in `./getting-started.md`.

### 4.5 Post a rating

Send `{"value": <number>}`. Use 0.5 to 10.0 in steps of 0.5.

```bash
AUTH=(--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
      --header 'Content-Type: application/json;charset=utf-8')
S='session_id=YOUR_SESSION_ID'
curl -X POST "${AUTH[@]}" -d '{"value":8.5}'  "https://api.themoviedb.org/3/movie/550/rating?$S"
curl -X POST "${AUTH[@]}" -d '{"value":9.0}'  "https://api.themoviedb.org/3/tv/1396/rating?$S"
curl -X POST "${AUTH[@]}" -d '{"value":10.0}' "https://api.themoviedb.org/3/tv/1396/season/1/episode/1/rating?$S"
```

```python
def valid_rating(value):
    return 0.5 <= value <= 10.0 and (value * 2) % 1 == 0   # 0.5 steps

def rate(path, value, **auth):
    if not valid_rating(value):
        raise ValueError("Use 0.5 to 10.0 in steps of 0.5")
    return post(path, {"value": value}, **auth)

rate("/movie/550/rating", 8.5, session_id=SESSION_ID)
rate("/tv/1396/rating", 9.0, session_id=SESSION_ID)
rate("/tv/1396/season/1/episode/1/rating", 10.0, session_id=SESSION_ID)
```

Validate the value in your client before you send it. That saves a round trip and gives the user a better message. A bad value returns HTTP 400 with status code 18.

**A rating removes the item from the watchlist.** TMDB documents this behavior on the add-rating pages. It keeps the "watched" list and the "want to watch" list in sync. The user can change the behavior in the TMDB sharing settings. Refresh your local watchlist state after a rating write.

### 4.6 Delete a rating

Send DELETE to the same path. Send no body.

```bash
curl --request DELETE \
     --url 'https://api.themoviedb.org/3/movie/550/rating?session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
     --header 'Content-Type: application/json;charset=utf-8'
```

```python
delete("/movie/550/rating", session_id=SESSION_ID)
# (200, {'success': True, 'status_code': 13, 'status_message': 'The item/record was deleted successfully.'})
delete("/tv/1396/rating", session_id=SESSION_ID)
delete("/tv/1396/season/1/episode/1/rating", session_id=SESSION_ID)
```

A delete on an item with no rating returns status code 34 (HTTP 404). Treat that result as success in an idempotent "clear my rating" action.

### 4.7 Read the rated collections

```python
rated_movies   = get(f"/account/{ACCOUNT_ID}/rated/movies", session_id=SESSION_ID,
                     sort_by="created_at.desc")
rated_series   = get(f"/account/{ACCOUNT_ID}/rated/tv", session_id=SESSION_ID)
rated_episodes = get(f"/account/{ACCOUNT_ID}/rated/tv/episodes", session_id=SESSION_ID)

for item in rated_movies["results"]:
    print(item["title"], "-> you rated", item["rating"], "| average", item["vote_average"])
```

Each result adds one field to the normal object: `rating`, the value of the user. Do not confuse it with `vote_average`, which is the public average. Read `rating` as a float – TMDB returns 8 and 8.5 in the same collection.

Episode results carry `show_id`, `season_number`, `episode_number`, `air_date`, `still_path` and `runtime`. Use `show_id` to link back to the series.

### 4.8 Read the account states of one item

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550/account_states?session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```json
{ "id": 550, "favorite": true, "rated": { "value": 9.0 }, "watchlist": false }
```

The `rated` field has two shapes. It is `false` when the user did not rate the item. It is an object `{"value": 9.0}` when the user did rate it. Handle both shapes:

```python
def read_state(payload):
    rated = payload.get("rated")
    return {
        "favorite": bool(payload.get("favorite")),
        "watchlist": bool(payload.get("watchlist")),
        "user_rating": rated["value"] if isinstance(rated, dict) else None,
    }

state = read_state(get("/movie/550/account_states", session_id=SESSION_ID))
# {'favorite': True, 'watchlist': False, 'user_rating': 9.0}
```

Drive the UI from this object. Fill the heart icon when `favorite` is true. Show "You rated this 9.0" when `user_rating` is not None. Show the empty star row when it is None.

### 4.9 Read the account states of a whole season

The season endpoint has a different shape. It returns one entry per episode and no favorite or watchlist fields.

```python
season = get("/tv/1396/season/1/account_states", session_id=SESSION_ID)
ratings = {
    ep["episode_number"]: (ep["rated"]["value"] if isinstance(ep["rated"], dict) else None)
    for ep in season["results"]
}
# {1: 9.0, 2: None, 3: None, ...}
```

Call this endpoint once for a season page. Do not call the episode endpoint in a loop.

### 4.10 Get account states with append_to_response

This is the pattern that keeps a detail page fast. Append `account_states` to the detail request and pass the `session_id` in the same query string. The sub-request inherits the query parameters, so the session reaches it.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?append_to_response=account_states,credits,videos&session_id=YOUR_SESSION_ID' \
     --header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

```python
movie = get("/movie/550", append_to_response="account_states,credits,videos",
            session_id=SESSION_ID)
print(movie["title"], read_state(movie["account_states"]))

# The same pattern works on TV series, seasons and episodes.
series  = get("/tv/1396", append_to_response="account_states", session_id=SESSION_ID)
season  = get("/tv/1396/season/1", append_to_response="account_states", session_id=SESSION_ID)
episode = get("/tv/1396/season/1/episode/1", append_to_response="account_states",
              session_id=SESSION_ID)
```

Omit the `session_id` and the `account_states` key disappears from the response, or it comes back empty. Do not read it without a guard. See `./append-to-response.md` for the 20-object limit and the other rules.

### 4.11 Use a guest session

A guest session lets an anonymous user rate items. It cannot favorite, cannot use a watchlist, and cannot read account details or lists.

```python
guest = requests.get(f"{BASE}/authentication/guest_session/new",
                     headers={"Authorization": f"Bearer {TOKEN}"}).json()
# {'success': True, 'guest_session_id': '1ce82ec...', 'expires_at': '2016-08-27 16:26:40 UTC'}
gsid = guest["guest_session_id"]

# Rate as the guest – the parameter name changes, the body does not
post("/movie/550/rating", {"value": 7.5}, guest_session_id=gsid)
post("/tv/1399/rating", {"value": 8.5}, guest_session_id=gsid)
post("/tv/1399/season/1/episode/1/rating", {"value": 8.5}, guest_session_id=gsid)

# Read the guest rated lists – the id goes in the PATH
get(f"/guest_session/{gsid}/rated/movies", sort_by="created_at.desc")
get(f"/guest_session/{gsid}/rated/tv")
get(f"/guest_session/{gsid}/rated/tv/episodes")

# Read the state of one item as the guest
get("/movie/550/account_states", guest_session_id=gsid)
# favorite and watchlist stay false; only `rated` is meaningful
```

**Expiry:** TMDB deletes a guest session if no request uses it for 60 minutes. Store `expires_at`, watch for status code 3 or 7, and create a new guest session when the old one dies. Warn the user that the guest ratings do not move to a real account. Keep the guest session id private, the same way you keep an account session id private.

## 5. Worked example: authenticate, rate, read back

```python
"""Rate a movie with a real account session, then confirm the state."""
import os, requests

BASE, MOVIE_ID = "https://api.themoviedb.org/3", 550
http = requests.Session()
http.headers.update({"Authorization": f"Bearer {os.environ['TMDB_ACCESS_TOKEN']}",
                     "Content-Type": "application/json;charset=utf-8"})

# 1. Create a request token, validate it with the login, and trade it for a session.
#    See ./authentication.md - prefer the redirect flow in a real product.
token = http.get(f"{BASE}/authentication/token/new").json()["request_token"]
http.post(f"{BASE}/authentication/token/validate_with_login",
          json={"username": os.environ["TMDB_USERNAME"],
                "password": os.environ["TMDB_PASSWORD"], "request_token": token})
session_id = http.post(f"{BASE}/authentication/session/new",
                       json={"request_token": token}).json()["session_id"]

# 2. Get the account id once and cache it.
account_id = http.get(f"{BASE}/account", params={"session_id": session_id}).json()["id"]

# 3. Post the rating.
resp = http.post(f"{BASE}/movie/{MOVIE_ID}/rating",
                 params={"session_id": session_id}, json={"value": 8.5})
print(resp.status_code, resp.json()["status_code"], resp.json()["status_message"])
# 201 1 Success.                                       <- first rating
# 201 12 The item/record was updated successfully.     <- later change

# 4. Read the state back. This is the authoritative confirmation.
state = http.get(f"{BASE}/movie/{MOVIE_ID}/account_states",
                 params={"session_id": session_id}).json()
rated = state["rated"]
print(state["favorite"], state["watchlist"],
      rated["value"] if isinstance(rated, dict) else None)
# False False 8.5

# 5. The rated collection shows the same value with the item metadata.
page = http.get(f"{BASE}/account/{account_id}/rated/movies",
                params={"session_id": session_id, "sort_by": "created_at.desc"}).json()
print(page["total_results"], page["results"][0]["title"], page["results"][0]["rating"])

# 6. Delete the rating when the user clears it.
http.delete(f"{BASE}/movie/{MOVIE_ID}/rating", params={"session_id": session_id})
```

## 6. Status codes you will meet

| Code | HTTP | Message | What to do |
| --- | --- | --- | --- |
| 1 | 200 / 201 | Success. | The write created the record. |
| 12 | 201 | The item/record was updated successfully. | The write changed an existing record. Treat as success. |
| 13 | 200 | The item/record was deleted successfully. | The delete or the "remove" toggle worked. |
| 3 | 401 | Authentication failed: you do not have permissions. | The session is dead or wrong. Re-authenticate. |
| 7 | 401 | Invalid API key. | Fix the application credential. |
| 8 | 403 | Duplicate entry. | The record already exists. Treat as success in a toggle. |
| 17 | 401 | Session denied. | The session cannot act on this resource. |
| 18 | 400 | Validation failed. | The rating value or the body is wrong. |
| 22 | 400 | Invalid page. | Pages start at 1 and stop at 500. |
| 25 | 429 | Request count over the allowed limit. | Back off and retry. |
| 34 | 404 | The resource could not be found. | Bad id, or no rating to delete. |
| 37 | 404 | The requested session could not be found. | The guest session expired. Create a new one. |
| 40 | 200 | Nothing to update. | The value did not change. Treat as success. |

```python
OK_CODES = {1, 12, 13, 40}          # treat every one of these as a successful write
```

## 7. Best practices and anti-patterns

```python
# Do this: confirm a write with account_states.
post("/movie/550/rating", {"value": 8.5}, session_id=SESSION_ID)
state = get("/movie/550/account_states", session_id=SESSION_ID)
# Don't do this: the collection can serve a cached page and can span 40 pages.
pages = get(f"/account/{ACCOUNT_ID}/rated/movies", session_id=SESSION_ID)

# Do this: get the detail and the state in one request.
movie = get("/movie/550", append_to_response="account_states", session_id=SESSION_ID)
# Don't do this: two requests for one screen.
movie = get("/movie/550"); state = get("/movie/550/account_states", session_id=SESSION_ID)

# Do this: toggle with the boolean flag.
set_favorite("movie", 550, not current_state["favorite"])
# Don't do this: the favorite endpoint has no DELETE method.
delete(f"/account/{ACCOUNT_ID}/favorite", session_id=SESSION_ID)   # fails
```

**Reuse one session.** Create the session once, store it, and use it for every request of that user. Do not create a session per request – you burn the rate limit and you annoy the user with a new approval.

**Cache the account_id.** Store it next to the session. Do not call the account details endpoint before every write.

**Keep the session out of logs.** The `session_id` gives full write access to the account. Do not print it. Do not put it in a URL that you share. Do not send it to a browser client. Proxy the writes through your server.

**Update the UI after the response, not before it.** Optimistic UI is fine, but roll back when `status_code` is not in the success set.

## 8. Pitfalls and gotchas

1. **`rated` is `false` or an object, never a plain number.** `state["rated"]["value"]` crashes on unrated items. Test the type first.
2. **A rating deletes the watchlist entry.** This is the documented default. Refresh the watchlist flag after a rating write.
3. **`sort_by` takes two values only.** `created_at.asc` and `created_at.desc` work. `popularity.desc` and `rating.desc` do not. Sort other orders in your own code, or use `./discover.md` for public sorting.
4. **`vote_average` is not the user rating.** In the rated collections, `rating` belongs to the user and `vote_average` belongs to everyone.
5. **The favorite and watchlist results have no `media_type`.** Add the type yourself when you merge the movie list and the TV list.
6. **The guest rated paths put the id in the path.** `/3/guest_session/{id}/rated/movies` – a `guest_session_id` query parameter does nothing there.
7. **A guest cannot favorite or use the watchlist.** Hide those controls for a guest, or ask the user to log in.
8. **The v4 account object id is not the v3 `account_id`.** The v3 paths need the integer `id` from `/3/account`. A v4 string id fails.
9. **The Bearer token alone does not authenticate the user.** Without `session_id` you get status code 3, or an empty `account_states` object under `append_to_response`.
10. **Set the Content-Type header.** The rating endpoints list `application/json;charset=utf-8` as required. Some clients send `text/plain` by default and the write fails.
11. **Ratings are per episode, not per season.** No season rating endpoint exists.
12. **Rate limits still apply.** Do not write a whole watchlist in a tight loop. Batch the work and add a pause.
13. **Pages stop at 500.** A very large collection needs `sort_by` plus a client-side filter, not page 501.

## 9. Related skill files

| File | Why you need it |
| --- | --- |
| `./authentication.md` | Create the `session_id` and the `guest_session_id`, and delete a session. Read this first. |
| `./getting-started.md` | Base URL, headers, rate limits and the error model. |
| `./append-to-response.md` | Merge `account_states` into a detail request and stay under the 20-object limit. |
| `./movies.md` | Movie detail fields that pair with `/movie/{id}/account_states`. |
| `./tv-series.md` | Series detail fields and the series rating endpoints. |
| `./tv-seasons-and-episodes.md` | Season and episode ids for the episode rating and state calls. |
| `./lists.md` | Custom lists – `/3/account/{account_id}/lists` and the list write endpoints. |
| `./images-and-configuration.md` | Build the avatar URL and the poster URLs of the collections. |
| `./localization.md` | Choose the `language` value, and use `iso_639_1` and `iso_3166_1` from the account. |
| `./search-and-find.md` | Find the `media_id` that you write to a favorite, a watchlist or a rating. |
| `./discover.md` | Public sorting and filtering that `sort_by` on these endpoints cannot do. |
| `./trending-and-popular.md` | Public popularity, in contrast with the private state on this page. |
