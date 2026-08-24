# TMDB: TV Seasons and Episodes
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

### The URL hierarchy

Every season and episode endpoint hangs off the parent series. The path grows from left to right:

```
/3/tv/{series_id}                                                  series
/3/tv/{series_id}/season/{season_number}                           season
/3/tv/{series_id}/season/{season_number}/episode/{episode_number}  episode
```

Append a sub-resource to any of those three levels, for example `/credits`, `/images`, `/videos`.

### season_number and episode_number are ordinals, not IDs

This is the single most common mistake. `series_id` is a TMDB database ID. `season_number` and `episode_number` are **positions inside the show**.

| Segment | Kind | Example | Where you get it |
| :-- | :-- | :-- | :-- |
| `series_id` | database ID | `1399` | search, discover, `/tv/{id}` |
| `season_number` | ordinal | `1` | the `seasons[]` array of the series |
| `episode_number` | ordinal | `1` | the `episodes[]` array of the season |

Season 0 always holds the specials. Use `/season/0` to read pilots, recaps, webisodes and Christmas specials. Not every show has a season 0, and season 0 can have gaps in its episode numbers.

Do this:

```bash
curl "https://api.themoviedb.org/3/tv/1399/season/1/episode/1"
```

Do not do this – `63056` is the episode database ID, not the ordinal:

```bash
curl "https://api.themoviedb.org/3/tv/1399/season/1/episode/63056"   # 404
```

The season database ID and the episode database ID do exist in the responses. You need them only for the change endpoints. See section 9.

### One call returns a whole season

The season details response embeds the complete `episodes[]` array, and each episode carries its own `crew[]` and `guest_stars[]`. Do not loop over episode endpoints to build a season page.

### Setup for the examples

All examples use a v4 read access token in the `Authorization` header. Read `./authentication.md` for the alternative `api_key` query parameter.

```python
import requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": "Bearer <TMDB_READ_ACCESS_TOKEN>",
    "accept": "application/json",
}

def get(path, **params):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
```

## 2. Quick reference – season endpoints

Base path: `/3/tv/{series_id}/season/{season_number}`

| Endpoint | Suffix | Key query parameters | Returns |
| :-- | :-- | :-- | :-- |
| Details | *(none)* | `language`, `append_to_response` | season plus full `episodes[]` |
| Aggregate Credits | `/aggregate_credits` | `language` | `cast[]` with `roles[]`, `crew[]` with `jobs[]` |
| Credits | `/credits` | `language` | flat `cast[]`, `crew[]` |
| Account States | `/account_states` | `session_id` or `guest_session_id` | per-episode `rated` list |
| External IDs | `/external_ids` | – | `tvdb_id`, `wikidata_id`, `freebase_*` |
| Images | `/images` | `language`, `include_image_language` | `posters[]` only |
| Translations | `/translations` | – | `translations[]` with `data.name`, `data.overview` |
| Videos | `/videos` | `language`, `include_video_language` | `results[]` |
| Watch Providers | `/watch/providers` | `language` | `results` keyed by country |
| Changes | `/3/tv/season/{season_id}/changes` | `start_date`, `end_date`, `page` | uses the **season ID**, not the ordinal |

## 3. Quick reference – episode endpoints

Base path: `/3/tv/{series_id}/season/{season_number}/episode/{episode_number}`

| Endpoint | Method and suffix | Key query parameters | Returns |
| :-- | :-- | :-- | :-- |
| Details | GET *(none)* | `language`, `append_to_response` | episode plus `crew[]`, `guest_stars[]` |
| Credits | GET `/credits` | `language` | `cast[]`, `crew[]`, `guest_stars[]` |
| Account States | GET `/account_states` | `session_id` or `guest_session_id` | `rated`, `favorite`, `watchlist` |
| External IDs | GET `/external_ids` | – | `imdb_id`, `tvdb_id`, `wikidata_id` |
| Images | GET `/images` | `language`, `include_image_language` | `stills[]` only |
| Translations | GET `/translations` | – | `translations[]` |
| Videos | GET `/videos` | `language`, `include_video_language` | `results[]` |
| Add Rating | POST `/rating` | `session_id` or `guest_session_id` | status envelope |
| Delete Rating | DELETE `/rating` | `session_id` or `guest_session_id` | status envelope |
| Changes | GET `/3/tv/episode/{episode_id}/changes` | – | uses the **episode ID**, not the ordinal |

## 4. Quick reference – episode group endpoints

| Endpoint | Path | Notes |
| :-- | :-- | :-- |
| List groups of a series | `/3/tv/{series_id}/episode_groups` | documented in `./tv-series.md` |
| Group details | `/3/tv/episode_group/{tv_episode_group_id}` | the ID is a 24-character **string** |

## 5. The season details response

```bash
curl "https://api.themoviedb.org/3/tv/1399/season/1?language=en-US" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Top level fields:

| Field | Notes |
| :-- | :-- |
| `id` | the **season database ID**. Pass it to `/tv/season/{season_id}/changes`. |
| `_id` | a legacy 24-character string. Ignore it. |
| `season_number` | the ordinal you sent |
| `name`, `overview`, `air_date`, `poster_path`, `vote_average` | display fields |
| `networks[]` | `id`, `name`, `logo_path`, `origin_country` |
| `episodes[]` | the full episode list |

Each object in `episodes[]` holds `id`, `episode_number`, `season_number`, `show_id`, `name`, `overview`, `air_date`, `runtime`, `still_path`, `production_code`, `episode_type`, `vote_average`, `vote_count`, plus `crew[]` and `guest_stars[]`.

`episode_type` labels the position of the episode in the season. The documented sample shows `standard` and `finale`.

Render a season list with one request:

```python
season = get("/tv/1399/season/1")
print(season["name"], season["air_date"], len(season["episodes"]))
for ep in season["episodes"]:
    guests = ", ".join(g["name"] for g in ep["guest_stars"][:3])
    print(f'S{ep["season_number"]:02d}E{ep["episode_number"]:02d}  {ep["name"]}  '
          f'({ep["runtime"]} min)  guests: {guests}')
```

## 6. The efficient pattern – append_to_response

`append_to_response` takes a comma separated list of sub-endpoints from the same namespace, 20 items maximum. TMDB counts the whole call as one request. Read `./append-to-response.md` for the general rules.

Do this – one request builds a complete season page:

```bash
curl "https://api.themoviedb.org/3/tv/1399/season/1?language=en-US\
&append_to_response=credits,aggregate_credits,images,videos,external_ids,translations,watch/providers\
&include_image_language=en,null" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```python
season = get(
    "/tv/1399/season/1",
    language="en-US",
    append_to_response="credits,images,videos,external_ids,watch/providers",
    include_image_language="en,null",
)
posters = season["images"]["posters"]
trailers = [v for v in season["videos"]["results"] if v["type"] == "Trailer"]
providers_us = season["watch/providers"]["results"].get("US", {})
```

Do not do this – 11 requests for the same season page:

```python
season = get("/tv/1399/season/1")
for ep in season["episodes"]:                       # one request per episode
    detail = get(f'/tv/1399/season/1/episode/{ep["episode_number"]}')
```

Rules to remember:

- The appended key in the JSON is the endpoint name, so `watch/providers` stays `watch/providers` with the slash.
- Query parameters are shared. `language` and `include_image_language` apply to the appended blocks too.
- `append_to_response` works at the episode level as well, with the episode sub-endpoints.

## 7. Episode details, credits and guest stars

```python
ep = get(
    "/tv/1399/season/1/episode/1",
    append_to_response="credits,images,videos,external_ids,translations",
    include_image_language="en,null",
)
print(ep["name"], ep["air_date"], ep["runtime"], ep["still_path"], ep["vote_average"])
```

Three people arrays exist, and they have different meanings:

| Array | Content | Where it lives |
| :-- | :-- | :-- |
| `cast[]` | the regular series cast for this episode | `/episode/{n}/credits` |
| `guest_stars[]` | the one-off actors of this episode | episode details **and** `/credits` |
| `crew[]` | the director, the writer and the rest, with `department` and `job` | episode details **and** `/credits` |

Episode details already contains `crew[]` and `guest_stars[]`. Call `/credits` only when you also need the recurring `cast[]`.

Find the director of an episode:

```python
directors = [c["name"] for c in ep["crew"] if c["job"] == "Director"]
writers = [c["name"] for c in ep["crew"] if c["department"] == "Writing"]
```

Guest star objects carry `character`, `credit_id`, `order`, `id`, `name`, `profile_path` and `popularity`. Sort by `order` before you display them. Use `credit_id` with the credit endpoint in `./people-and-credits.md`.

## 8. Images, stills and videos

Season images and episode images return different keys. Nothing else changes.

| Level | Response key | Image kind | Typical size keys |
| :-- | :-- | :-- | :-- |
| Season | `posters[]` | poster, 2:3 | `w154`, `w342`, `w500`, `original` |
| Episode | `stills[]` | still frame, 16:9 | `w92`, `w185`, `w300`, `original` |

The episode object also has a single `still_path` string. Use `stills[]` only when you want a choice of frames.

```python
conf = get("/configuration")
base = conf["images"]["secure_base_url"]
url = f'{base}w300{ep["still_path"]}'
```

Build the URL with the size list from `/configuration`. Read `./images-and-configuration.md`.

Warning: `language` acts as a **filter** on images. Most stills have `iso_639_1: null`, so a plain `language=en` request can return an empty list. Always add the languageless items:

```bash
curl "https://api.themoviedb.org/3/tv/1399/season/1/episode/1/images?include_image_language=en,null"
```

Videos behave the same way. Use `include_video_language=en,null` when you widen the search. Each video result has `key`, `site`, `type`, `official` and `published_at`. Build the player URL yourself, for example `https://www.youtube.com/watch?v={key}` when `site == "YouTube"`.

## 9. credits versus aggregate_credits at season level

| Call | Shape | Use it for |
| :-- | :-- | :-- |
| `/credits` | flat `cast[]` with one `character` and one `credit_id` per person | a simple cast list |
| `/aggregate_credits` | `cast[]` with `roles[]` and `total_episode_count`; `crew[]` with `jobs[]` and `total_episode_count` | "appeared in 8 of 10 episodes", multi-role actors |

`aggregate_credits` merges every episode of the season. One actor appears once, even with several characters.

```python
agg = get("/tv/1399/season/1/aggregate_credits")
for person in agg["cast"][:10]:
    roles = ", ".join(f'{r["character"]} ({r["episode_count"]} eps)' for r in person["roles"])
    print(person["name"], "-", roles, "- total:", person["total_episode_count"])
```

Do not use `aggregate_credits` for a "top billed" strip on an episode page. Use the episode `credits` there.

## 10. External IDs, translations and watch providers

External IDs let you join TMDB to other databases:

```python
get("/tv/1399/season/1/external_ids")
# {"id": 3624, "tvdb_id": 364731, "wikidata_id": "Q1658029", "tvrage_id": null, ...}
get("/tv/1399/season/1/episode/1/external_ids")
# {"id": 63056, "imdb_id": "tt1480055", "tvdb_id": 3254641, "wikidata_id": "Q2614622", ...}
```

Seasons support TheTVDB and Wikidata. Episodes also support IMDb. Seasons have no `imdb_id`, so do not expect one.

Translations return `iso_639_1`, `iso_3166_1`, `name`, `english_name` and a `data` object with the translated `name` and `overview`. Read `./localization.md` for the language and region rules.

Season watch providers come from JustWatch:

```python
wp = get("/tv/1399/season/1/watch/providers")
us = wp["results"]["US"]
print(us["link"])                                    # send the user here
for p in us.get("flatrate", []):
    print(p["provider_name"], p["provider_id"], p["logo_path"], p["display_priority"])
```

- `results` is a map keyed by ISO 3166-1 country code. The sample response covers 98 countries.
- Offer buckets in the season sample are `flatrate`, `buy` and `rent`. Read every bucket you find, and do not assume that all three exist.
- TMDB **requires** attribution to JustWatch. TMDB can revoke your access without it.
- The API returns no deep links. Send the user to the `link` URL. Do not build your own provider URL.

Read `./watch-providers.md` for the provider list and the region list.

## 11. Account states and ratings

TMDB has **no** season rating endpoint. Rate episodes.

Season account states return one row per episode:

```python
states = get("/tv/1399/season/1/account_states", session_id=SESSION_ID)
# {"id": 3624, "results": [{"id": 63056, "episode_number": 1, "rated": {"value": 9}},
#                          {"id": 63057, "episode_number": 2, "rated": false}, ...]}
rated = {r["episode_number"]: r["rated"]["value"] for r in states["results"] if r["rated"]}
```

`rated` is `false` when the user has not rated the episode. `rated` is an object with a `value` key when the user has rated it. Test `rated` first. Never read `rated["value"]` directly.

Episode account states return a single object with `rated`, `favorite` and `watchlist`. Use `rated`. TMDB has no favourite list and no watchlist for episodes.

Add a rating:

```bash
curl -X POST "https://api.themoviedb.org/3/tv/1399/season/1/episode/1/rating?session_id=$SESSION_ID" \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H "Content-Type: application/json;charset=utf-8" \
  -d '{"value": 8.5}'
```

```python
requests.post(
    f"{BASE}/tv/1399/season/1/episode/1/rating",
    headers={**HEADERS, "Content-Type": "application/json;charset=utf-8"},
    params={"session_id": SESSION_ID},
    json={"value": 8.5},
)
```

Delete a rating with the same path and the DELETE method. Send `value` between 0.5 and 10.0 in steps of 0.5. Send the `Content-Type` header, because TMDB rejects the body without it. Pass `guest_session_id` instead of `session_id` for a guest session. Read `./user-account-and-ratings.md`.

## 12. Episode groups

### What an episode group is

An episode group is an alternate ordering of the episodes of a show. TMDB users curate the groups. Use a group when the broadcast order does not match the order that your users expect, for example a DVD order, an absolute anime order or a streaming collection.

A group holds sub-groups. Each sub-group holds an ordered slice of episodes. The example "Netflix Collections" for *Comedians in Cars Getting Coffee* has 6 sub-groups and 83 episodes.

### Group types

| `type` | Name |
| :-- | :-- |
| 1 | Original air date |
| 2 | Absolute |
| 3 | DVD |
| 4 | Digital |
| 5 | Story arc |
| 6 | Production |
| 7 | TV |

### Step 1 – find the groups of a series

```bash
curl "https://api.themoviedb.org/3/tv/1399/episode_groups" -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{"id": 1399, "results": [{"id": "5e9077d2e640d600151f32bd", "name": "Aired Order",
  "type": 1, "group_count": 9, "episode_count": 102, "description": "",
  "network": {"id": 49, "name": "HBO", "logo_path": "/tuo...png", "origin_country": "US"}}]}
```

### Step 2 – read the group

```bash
curl "https://api.themoviedb.org/3/tv/episode_group/5acf93e60e0a26346d0000ce" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

The response has `id`, `name`, `description`, `type`, `network`, `group_count`, `episode_count` and `groups[]`. Each entry in `groups[]` has `id`, `name`, `order`, `locked` and `episodes[]`.

### Step 3 – render the alternate ordering

```python
def render_group(group_id):
    g = get(f"/tv/episode_group/{group_id}")
    print(f'{g["name"]} (type {g["type"]}) - {g["group_count"]} groups, {g["episode_count"]} episodes')
    for sub in sorted(g["groups"], key=lambda s: s["order"]):
        print(f'\n== {sub["order"]}. {sub["name"]}')
        for ep in sorted(sub["episodes"], key=lambda e: e["order"]):
            # keep the canonical coordinates so you can link back to the real episode
            canonical = f'S{ep["season_number"]:02d}E{ep["episode_number"]:02d}'
            print(f'  {ep["order"]:>3}. {ep["name"]}  [{canonical}]  {ep["air_date"]}')

render_group("5acf93e60e0a26346d0000ce")
```

```javascript
const res = await fetch(
  "https://api.themoviedb.org/3/tv/episode_group/5acf93e60e0a26346d0000ce",
  { headers: { Authorization: `Bearer ${token}`, accept: "application/json" } }
);
const group = await res.json();
const flat = group.groups
  .sort((a, b) => a.order - b.order)
  .flatMap((sub) => [...sub.episodes].sort((a, b) => a.order - b.order));
```

### Episode group gotchas

- The group ID is a **string** such as `5acf93e60e0a26346d0000ce`. Do not cast it to an integer.
- `order` inside a sub-group starts at **0**. `order` on the sub-group itself starts at **1** in the sample.
- The episodes inside a group keep their real `season_number` and `episode_number`. Use those two values to build the canonical episode URL for details, images or ratings.
- The episode payload inside a group is a subset. It has no `crew[]`, no `guest_stars[]` and no `episode_type`. `runtime` can be `null`.
- The group details endpoint accepts **no** `language` parameter. The text comes back in the default language.
- `locked: true` means that TMDB has locked the sub-group against edits. It is metadata, not an access control.

## 13. Changes use IDs, not ordinals

Both change endpoints break the hierarchy pattern. They take a database ID:

```
/3/tv/season/{season_id}/changes      season_id  = season details "id"
/3/tv/episode/{episode_id}/changes    episode_id = episodes[].id
```

Do this:

```python
season = get("/tv/1399/season/1")
season_changes = get(f'/tv/season/{season["id"]}/changes')          # id = 3624
ep_changes = get(f'/tv/episode/{season["episodes"][0]["id"]}/changes')  # id = 63056
```

Do not do this:

```python
get("/tv/1399/season/1/changes")     # wrong shape, this endpoint does not exist
```

Notes:

- Both endpoints return the last 24 hours by default. Query up to 14 days with `start_date` and `end_date` on the season endpoint.
- The season change feed contains an `episode` key. Each item there holds `value.episode_id` and `value.episode_number`. Follow the `episode_id` into the episode change endpoint for the field level detail.
- The episode change feed groups items by field, for example `production_code` or `overview`. Translated fields carry `iso_639_1`.
- The published OpenAPI for the episode change endpoint lists only `episode_id`. The prose also describes `start_date` and `end_date`. Test them before you depend on them.
- Read `./changes-and-exports.md` for the daily change feed pattern.

## 14. Pitfalls checklist

| Pitfall | Fix |
| :-- | :-- |
| You pass an episode database ID as `episode_number` | Pass the ordinal. Keep the ID only for changes. |
| You miss the specials | Read `/season/0`. Check the `seasons[]` array of the series for season 0. |
| You loop over every episode | Read the season once. It embeds `episodes[]` with crew and guest stars. |
| `images` returns an empty array | Add `include_image_language=en,null`. |
| You expect `images` on an episode | The episode key is `stills`, the season key is `posters`. |
| You try to rate a season | Rate the episodes. No season rating endpoint exists. |
| You test `rated` as a boolean only | `rated` is `false` or an object with `value`. |
| You build a provider deep link | Use the `link` field. Attribute JustWatch. |
| Unaired episodes look broken | `air_date`, `runtime`, `overview` and `still_path` can be `null` or empty. |
| Season `id` and `_id` confusion | Use `id`. `_id` is a legacy string. |
| Episode numbers have gaps | Never assume `range(1, n+1)`. Iterate the returned array. |
| `append_to_response` block is missing | The key uses the endpoint name, including the slash in `watch/providers`. |

## 15. Related skill files

| File | Why you need it |
| :-- | :-- |
| `./tv-series.md` | series details, the `seasons[]` array, `/tv/{id}/episode_groups`, series level credits |
| `./append-to-response.md` | the full rules for combined requests |
| `./images-and-configuration.md` | `/configuration`, base URLs and the still and poster size lists |
| `./localization.md` | `language`, `include_image_language`, `include_video_language`, translation fallbacks |
| `./authentication.md` | bearer token, `api_key`, `session_id`, guest sessions |
| `./user-account-and-ratings.md` | rated episode lists, session management |
| `./people-and-credits.md` | `credit_id` lookups for guest stars and crew |
| `./watch-providers.md` | provider IDs, regions, JustWatch attribution |
| `./changes-and-exports.md` | daily change feeds and bulk ID exports |
| `./search-and-find.md` | resolve an external ID (IMDb, TVDB) to a TMDB episode |
| `./getting-started.md` | rate limits, error envelope, base URL |
