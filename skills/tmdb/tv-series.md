# TMDB: TV Series
Based on TMDB API v3 documentation (developer.themoviedb.org).

The TV series namespace covers everything at the show level: details, credits, images, ratings, providers and changes. Anything below the show level – a season, an episode – lives in `./tv-seasons-and-episodes.md`.

## Core concepts

- **Base URL**: `https://api.themoviedb.org/3`. Send `Authorization: Bearer <access_token>` and `accept: application/json`. Read `./authentication.md` for the token types.
- **The series id** is the integer TMDB id, for example `1399` for Game of Thrones. Get it from `./search-and-find.md` or `./discover.md`.
- **A namespace** groups the sub-requests of one entity. Every `/3/tv/{series_id}/...` path belongs to the TV series namespace. Only endpoints in the same namespace work with `append_to_response`.
- **`language`** takes an IETF tag such as `en-US` or `pt-BR`. It changes the text fields and it filters images. Read `./localization.md`.
- **Image fields are paths, not URLs.** Build the URL with the configuration base URL. Read `./images-and-configuration.md`.
- **A TV show is a tree**: series → seasons → episodes. The series response lists the seasons but not the episodes.

## Quick reference: every TV series endpoint

| Endpoint | Method | Extra parameters | Returns |
| --- | --- | --- | --- |
| `/tv/{series_id}` | GET | `language`, `append_to_response` | Full series object |
| `/tv/{series_id}/account_states` | GET | `session_id`, `guest_session_id` | `favorite`, `rated`, `watchlist` |
| `/tv/{series_id}/aggregate_credits` | GET | `language` | Whole-series cast and crew with `roles`/`jobs` |
| `/tv/{series_id}/alternative_titles` | GET | – | Titles per country with a `type` label |
| `/tv/{series_id}/changes` | GET | `start_date`, `end_date`, `page` | Change entries, last 24 hours by default |
| `/tv/{series_id}/content_ratings` | GET | – | One rating string per country |
| `/tv/{series_id}/credits` | GET | `language` | Latest season cast and crew, flat |
| `/tv/{series_id}/episode_groups` | GET | – | Alternate orderings (aired, DVD, absolute …) |
| `/tv/{series_id}/external_ids` | GET | – | IMDb, TVDB, Wikidata, social ids |
| `/tv/{series_id}/images` | GET | `language`, `include_image_language` | `backdrops`, `posters`, `logos` |
| `/tv/{series_id}/keywords` | GET | – | Keyword ids and names |
| `/tv/{series_id}/lists` | GET | `language`, `page` | Public lists that contain this show |
| `/tv/{series_id}/recommendations` | GET | `language`, `page` | Personalised "you may also like" |
| `/tv/{series_id}/reviews` | GET | `language`, `page` | User reviews with `author_details` |
| `/tv/{series_id}/screened_theatrically` | GET | – | Episodes that ran in cinemas |
| `/tv/{series_id}/similar` | GET | `language`, `page` | Keyword and genre matches |
| `/tv/{series_id}/translations` | GET | – | Translated name, overview, tagline |
| `/tv/{series_id}/videos` | GET | `language`, `include_video_language` | Trailers, clips, opening credits |
| `/tv/{series_id}/watch/providers` | GET | – | Streaming availability per country |
| `/tv/{series_id}/rating` | POST | `session_id` or `guest_session_id` | Saves a rating, body `{"value": 8.5}` |
| `/tv/{series_id}/rating` | DELETE | `session_id` or `guest_session_id` | Removes your rating |
| `/tv/latest` | GET | – | The newest TV show object |
| `/tv/airing_today` | GET | `language`, `page`, `timezone` | Shows that air today |
| `/tv/on_the_air` | GET | `language`, `page`, `timezone` | Shows that air in the next 7 days |
| `/tv/popular` | GET | `language`, `page` | Shows by popularity |
| `/tv/top_rated` | GET | `language`, `page` | Shows by rating |
| `/tv/episode_group/{id}` | GET | – | The episodes inside one episode group |

`series_id` is always a required path parameter. The four list endpoints are paginated with 20 results per page.

## Fetch the details

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/tv/1399?language=en-US' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

```python
import os, requests

BASE = "https://api.themoviedb.org/3"
TMDB = requests.Session()
TMDB.headers.update({"Authorization": f"Bearer {os.environ['TMDB_ACCESS_TOKEN']}",
                     "accept": "application/json"})

def get(path, **params):                      # every example below reuses this helper
    r = TMDB.get(f"{BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

show = get("/tv/1399", language="en-US")
print(show["name"], show["number_of_seasons"], show["status"])
```

## The series details response

| Field | Type | What to know |
| --- | --- | --- |
| `id` | int | The TMDB series id. Use it for every sub-request. |
| `name` | string | The title in the requested `language`. |
| `original_name` | string | The title in `original_language`. It never changes with `language`. |
| `original_language` | string | ISO 639-1 code of the production language. |
| `origin_country` | array | ISO 3166-1 codes, for example `["US"]`. |
| `overview`, `tagline` | string | Localised text. Both can be an empty string. |
| `first_air_date` | string | `YYYY-MM-DD`. It can be `""` for an unaired show. |
| `last_air_date` | string | The air date of the most recent episode. |
| `in_production` | bool | `true` while TMDB expects more episodes. |
| `status` | string | `Returning Series`, `Ended`, `Canceled`, `In Production`, `Planned`, `Pilot`. |
| `type` | string | `Scripted`, `Documentary`, `Reality`, `Miniseries`, `News`, `Talk Show`, `Video`. |
| `episode_run_time` | array of int | Minutes. It is often empty or has several values. |
| `number_of_seasons` | int | It excludes season 0 (Specials). |
| `number_of_episodes` | int | The total over all seasons. |
| `seasons` | array | One stub per season, including season 0. |
| `networks` | array | Broadcaster: `id`, `name`, `logo_path`, `origin_country`. |
| `production_companies` | array | The studios, not the broadcaster. |
| `created_by` | array | Creators with `id`, `credit_id`, `name`, `profile_path`. |
| `genres` | array | Objects with `id` and `name`. TV genres differ from movie genres. |
| `last_episode_to_air` | object or null | The most recent episode, with `season_number` and `episode_number`. |
| `next_episode_to_air` | object or null | `null` when nothing is scheduled. |
| `vote_average`, `vote_count`, `popularity` | number | TMDB community numbers. |
| `homepage`, `poster_path`, `backdrop_path` | string or null | `null` is common on new shows. |

Each item in `seasons` has `air_date`, `episode_count`, `id`, `name`, `overview`, `poster_path`, `season_number` and `vote_average`. It does **not** have the episodes. Call the season endpoint for those.

### Season 0 is Specials

`seasons` contains a season with `season_number: 0` on most shows. `number_of_seasons` does not count it. Filter it out before you show a season list.

```python
regular = [s for s in show["seasons"] if s["season_number"] > 0]
specials = next((s for s in show["seasons"] if s["season_number"] == 0), None)
```

### Show the next episode

Do not derive "is it running?" from `status` alone. Combine `in_production`, `status` and `next_episode_to_air`.

```python
nxt = show.get("next_episode_to_air")
if nxt:
    print(f"S{nxt['season_number']:02d}E{nxt['episode_number']:02d} on {nxt['air_date']}")
elif show["in_production"]:
    print("In production, no date announced")
else:
    print(f"Finished: {show['status']}")
```

## append_to_response – one request instead of ten

`append_to_response` accepts a comma separated list of endpoints in the same namespace, 20 items maximum. Read `./append-to-response.md` for the general rules.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/tv/1399?language=en-US&append_to_response=aggregate_credits,content_ratings,external_ids,images,videos,keywords,watch%2Fproviders,recommendations' \
     --header 'Authorization: Bearer <access_token>'
```

```python
show = get(
    "/tv/1399",
    language="en-US",
    append_to_response="aggregate_credits,content_ratings,external_ids,images,videos,keywords,watch/providers",
    include_image_language="en,null",
)
providers = show["watch/providers"]["results"]   # note the key keeps the slash
logos = show["images"]["logos"]
```

Three rules trip people up:

1. **The appended key repeats the path.** `watch/providers` appends under the literal key `"watch/providers"`, not `"watch_providers"`.
2. **Query parameters apply to every appended part.** `language=de-DE` also filters `images`. Add `include_image_language=de,null` to keep the language-free artwork.
3. **`account_states` needs a `session_id`.** Append it only on an authenticated request.

### The `season/N` shorthand

The TV namespace accepts `season/{number}` inside `append_to_response`. It pulls whole season objects, with their episode arrays, into the series response.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/tv/1399?append_to_response=season%2F1,season%2F2' \
     --header 'Authorization: Bearer <access_token>'
```

```python
show = get("/tv/1399", append_to_response="season/1,season/2")
for ep in show["season/1"]["episodes"]:
    print(ep["episode_number"], ep["name"], ep["air_date"])
```

Use it to build a full episode guide in one round trip. Keep the total under the 20 item limit, so fetch at most about 18 seasons per call. This shorthand is not on the reference page, so verify it against your own key before you depend on it in production. Read `./tv-seasons-and-episodes.md` for the plain season and episode endpoints.

```python
# Do this – one call for the whole show page.
get("/tv/1399", append_to_response="aggregate_credits,content_ratings,videos,images,season/1")

# Don't do this – five calls for the same page.
get("/tv/1399"); get("/tv/1399/aggregate_credits"); get("/tv/1399/content_ratings")
get("/tv/1399/videos"); get("/tv/1399/images")
```

## credits vs aggregate_credits – the big one

These two endpoints answer different questions. Choose deliberately.

| | `/credits` | `/aggregate_credits` |
| --- | --- | --- |
| Scope | The **latest season only** | **All episodes of the show** |
| Cast item | One flat object with `character` and `credit_id` | `roles` array plus `total_episode_count` |
| Crew item | One flat object with `job` and `department` | `jobs` array plus `total_episode_count` |
| A person appears | Once per credit | Once, with every role merged |
| Matches the TMDB website | No | Yes |

`/credits` cast item:

```json
{ "id": 22970, "name": "Peter Dinklage", "character": "Tyrion Lannister",
  "credit_id": "5256c8b219c2956ff6047cd8", "order": 0 }
```

`/aggregate_credits` cast item:

```json
{ "id": 221978, "name": "Iwan Rheon", "order": 31, "total_episode_count": 38,
  "roles": [
    { "credit_id": "570162b19251416070000450", "character": "Ramsay Bolton", "episode_count": 20 },
    { "credit_id": "5347ff6c0e0a265c6c001636", "character": "Ramsay Snow",  "episode_count": 18 } ] }
```

`/aggregate_credits` crew item uses `jobs` in the same shape, plus a top level `department`:

```json
{ "id": 1406918, "name": "Brendan Rankin", "department": "Art", "total_episode_count": 15,
  "jobs": [ { "job": "Assistant Art Director", "episode_count": 5 },
            { "job": "Art Direction", "episode_count": 10 } ] }
```

Render an aggregate cast list correctly:

```python
credits = get("/tv/1399/aggregate_credits", language="en-US")

for person in sorted(credits["cast"], key=lambda c: c["order"])[:15]:
    characters = " / ".join(r["character"] for r in person["roles"])
    print(f'{person["name"]:<25} {characters:<40} {person["total_episode_count"]} eps')
```

```javascript
const res = await fetch("https://api.themoviedb.org/3/tv/1399/aggregate_credits", {
  headers: { Authorization: `Bearer ${token}`, accept: "application/json" },
});
const { cast } = await res.json();

cast.map((p) => p.character);                        // Don't – always undefined here
cast.map((p) => p.roles.map((r) => r.character));    // Do – read the roles array
```

Use `total_episode_count` for the per-person total. Never add up the `roles` counts. A person can hold two credits in the same episode, so the sum can exceed the real total.

Guidance:
- Use `/aggregate_credits` for a cast page, a "main cast" filter or an actor-to-show link.
- Use `/credits` when you want the current season line-up only, for example on a "now airing" card.
- Use the season and episode credit endpoints for finer scope. Read `./tv-seasons-and-episodes.md`.
- Read `./people-and-credits.md` for the reverse direction, from a person to their shows.

## episode_groups – alternate orderings

An episode group is an alternative way to order the episodes of a show. Fans use them for DVD order, absolute (anime) order, story arcs and streaming collections.

```bash
curl 'https://api.themoviedb.org/3/tv/1399/episode_groups' \
     --header 'Authorization: Bearer <access_token>'
```

```json
{ "id": 1399, "results": [
  { "id": "5e9077d2e640d600151f32bd", "name": "Aired Order", "description": "",
    "episode_count": 102, "group_count": 9, "type": 1,
    "network": { "id": 49, "name": "HBO", "logo_path": "/tuom….png", "origin_country": "US" } } ] }
```

The list endpoint returns only the group headers. Fetch the episodes with the group id:

```python
groups = get("/tv/1399/episode_groups")["results"]
dvd = next((g for g in groups if g["type"] == 3), None)
if dvd:
    detail = get(f"/tv/episode_group/{dvd['id']}")
    for grp in sorted(detail["groups"], key=lambda g: g["order"]):
        print(grp["name"], len(grp["episodes"]))
```

`type` is an integer. The reference page does not publish a legend, so treat this observed mapping as a hint and always show `name` to the user.

| `type` | Meaning |
| --- | --- |
| 1 | Original air date |
| 2 | Absolute |
| 3 | DVD |
| 4 | Digital |
| 5 | Story arc |
| 6 | Production |
| 7 | TV |

Gotchas:
- The group id is a **string** (a Mongo-style hex id), not an integer.
- `groups[].episodes[]` carries the **canonical** `season_number` and `episode_number` plus a group-local `order`. Map the group order to the canonical numbers before you call the episode endpoints.
- Most shows have no episode groups. Handle an empty `results` array.
- `/tv/episode_group/{id}` belongs to the season and episode docs. Read `./tv-seasons-and-episodes.md`.

## content_ratings – a TV rating per country

```json
{ "id": 1399, "results": [
  { "iso_3166_1": "US", "rating": "TV-MA", "descriptors": [] },
  { "iso_3166_1": "DE", "rating": "16",    "descriptors": [] } ] }
```

Derive the rating for one country and fall back cleanly:

```python
def tv_rating(series_id, country="US", fallback=("US",)):
    rows = get(f"/tv/{series_id}/content_ratings")["results"]
    by_country = {r["iso_3166_1"]: r for r in rows}
    for code in (country, *fallback):
        if code in by_country and by_country[code]["rating"]:
            return by_country[code]["rating"], by_country[code].get("descriptors", [])
    return None, []

print(tv_rating(1399, "DE"))     # ('16', [])
```

Rules:
- **Never compare ratings across countries.** `16` in Germany and `TV-MA` in the US are different scales.
- Do not assume a country exists in the results. Many shows only carry a few.
- `rating` can be an empty string. Treat that as "unrated".
- `descriptors` is usually empty. Use it only as an extra hint.
- Movies use `release_dates`, not `content_ratings`. Read `./movies.md`.

## external_ids – leave TMDB

```json
{ "id": 1399, "imdb_id": "tt0944947", "tvdb_id": 121361, "wikidata_id": "Q23572",
  "facebook_id": "GameOfThrones", "instagram_id": "gameofthrones", "twitter_id": "GameOfThrones",
  "freebase_mid": "/m/0524b41", "freebase_id": "/en/game_of_thrones", "tvrage_id": 24493 }
```

Supported sources: Facebook, IMDb, Instagram, TheTVDB, Twitter, Wikidata. Every field can be `null`. `freebase_*` and `tvrage_id` are dead services – ignore them.

Go the other way with `/find/{external_id}`. Read `./search-and-find.md`.

## images, videos, translations, alternative_titles, keywords

**Images** return `backdrops`, `posters` and `logos`. Each item has `file_path`, `iso_639_1`, `width`, `height`, `aspect_ratio`, `vote_average` and `vote_count`. `language` filters the images and `include_image_language` adds languages back. Always add `null` to keep the text-free artwork. Sort by `vote_average` to pick the best poster. Read `./images-and-configuration.md`.

**Videos** return YouTube keys, not embed URLs. `type` values include `Trailer`, `Teaser`, `Clip`, `Behind the Scenes`, `Opening Credits` and `Featurette`. Use `include_video_language=en,null` to widen a narrow language filter.

**Translations** list every localised `name`, `overview`, `homepage` and `tagline` under `data`. Use them to fill a gap when `language` returns an empty overview.

```python
videos = get("/tv/1399/videos", language="en-US")["results"]
trailer = next((v for v in videos
                if v["type"] == "Trailer" and v["site"] == "YouTube" and v["official"]), None)
print(f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else "no trailer")

tr = get("/tv/1399/translations")["translations"]
de = next((t for t in tr if t["iso_639_1"] == "de"), None)
overview = show["overview"] or (de["data"]["overview"] if de else "")
```

**Alternative titles** give `iso_3166_1`, `title` and `type`. `type` is free text: `working title`, `common abbreviation`, `romanization` or `""`. Use them to widen a search index, not to display a title.

**Keywords** return `{"id": 818, "name": "based on novel or book"}`. Feed the ids straight into `/discover/tv?with_keywords=`. Read `./discover.md`.

## recommendations vs similar

| | `/recommendations` | `/similar` |
| --- | --- | --- |
| Source | TMDB user behaviour | Keyword and genre overlap |
| Quality | Better for a "you may also like" row | Noisy, sometimes irrelevant |
| Results | Can be empty on an obscure show | Almost always full |
| Extra field | Items carry `media_type: "tv"` | No `media_type` |

Both are paginated and return the standard TV list item: `id`, `name`, `original_name`, `overview`, `poster_path`, `backdrop_path`, `genre_ids`, `first_air_date`, `origin_country`, `vote_average`, `vote_count` and `popularity`. Prefer `/recommendations` and fall back to `/similar` when it is empty.

```python
recs = get("/tv/1399/recommendations", page=1)["results"] \
    or get("/tv/1399/similar", page=1)["results"]
```

## reviews, screened_theatrically, lists

**Reviews** are paginated. Each item has `author`, `content`, `url`, `created_at`, `updated_at` and `author_details` with `name`, `username`, `avatar_path` and `rating`. `rating` can be `null`. `content` is Markdown, so escape it before you render it as HTML.

**Screened theatrically** lists the episodes that ran in cinemas: `{"id": 63103, "season_number": 4, "episode_number": 10}`. It is empty for nearly every show.

**Lists** returns the public user lists that contain this show, with `id`, `name`, `description`, `item_count`, `favorite_count`, `iso_639_1` and `iso_3166_1`. Read `./lists.md`.

## Watch providers

```python
data = get("/tv/1399/watch/providers")["results"]
se = data.get("SE", {})
print(se.get("link"))
for p in se.get("flatrate", []):
    print(p["provider_name"], p["provider_id"], p["logo_path"])
```

Response shape: `{"id": 1399, "results": {"US": {"link": …, "flatrate": [...], "buy": [...], "rent": [...]}}}`.

- **You must attribute JustWatch as the data source.** TMDB revokes API access for non-compliant use. This is a hard requirement in the docs.
- The `link` is a TMDB watch page, not a deep link into the provider. Link to it – it gives your users the real deep links and it supports TMDB.
- The keys under `results` are ISO 3166-1 country codes. A country key is missing when the show is unavailable there. There is no `language` parameter, so pick the country yourself.
- The buckets are optional: `flatrate`, `free`, `ads`, `rent`, `buy`. Test for each key, and sort each list by `display_priority`.
- Seasons have their own provider endpoint. Read `./tv-seasons-and-episodes.md` and `./watch-providers.md`.

## account_states and rating

All three need a user session. Read `./authentication.md` and `./user-account-and-ratings.md`.

```bash
S='session_id=<session_id>'; A='Authorization: Bearer <access_token>'
C='Content-Type: application/json;charset=utf-8'

curl "https://api.themoviedb.org/3/tv/1399/account_states?$S" -H "$A"
curl -X POST   "https://api.themoviedb.org/3/tv/1399/rating?$S" -H "$A" -H "$C" -d '{"value": 8.5}'
curl -X DELETE "https://api.themoviedb.org/3/tv/1399/rating?$S" -H "$A" -H "$C"
```

```python
state = get("/tv/1399/account_states", session_id=SESSION_ID)
rated = state["rated"]["value"] if state["rated"] else None

r = TMDB.post(f"{BASE}/tv/1399/rating",
              params={"session_id": SESSION_ID},
              headers={"Content-Type": "application/json;charset=utf-8"},
              json={"value": 8.5})
print(r.json())    # {"status_code": 1, "status_message": "Success."}
```

Notes:
- `rated` is an object `{"value": 9.0}` when you rated the show. It is `false` when you did not. Test the truthiness, do not index it blindly.
- Send `value` between 0.5 and 10.0. Set the `Content-Type` header on both POST and DELETE, or TMDB rejects the call. The DELETE response is `{"status_code": 13, ...}`.
- Pass `guest_session_id` instead of `session_id` for a guest. A guest can rate but has no favourites or watchlist.
- A successful rating **removes the show from your watchlist** by default. The user controls that in their TMDB sharing settings.
- The reference example for `account_states` shows `"id": 550`, which is a movie id. Ignore that – the endpoint returns the series id.

## latest id and changes

`/tv/latest` is a live response and it changes constantly. Use it to learn the current id ceiling. Do not use it to enumerate the catalogue – use the daily ID exports in `./changes-and-exports.md`.

```python
newest = get("/tv/latest")["id"]     # a full series object, but mostly empty fields

recent = get("/tv/1399/changes", start_date="2024-01-01", end_date="2024-01-14", page=1)
for group in recent["changes"]:
    print(group["key"], len(group["items"]))
```

- The default window is the **last 24 hours**. The maximum window is **14 days** per query.
- Each entry has `key` (`images`, `name`, `overview`, `season`, `episode` …) and an `items` array with `id`, `action`, `time`, `value` and `original_value`.
- Season and episode edits raise a **series-level** entry under the `season` and `episode` keys. Those items carry ids. Look them up with the season changes and episode changes endpoints in `./tv-seasons-and-episodes.md`.
- Poll `/tv/changes` (the global list) first to learn which shows changed, then call this per-series endpoint. Read `./changes-and-exports.md`.

## Series lists

`/tv/popular`, `/tv/top_rated`, `/tv/on_the_air` and `/tv/airing_today` are convenience wrappers. The docs state that each one is a `/discover/tv` call behind the scenes.

| List | Equivalent discover call |
| --- | --- |
| `popular` | `sort_by=popularity.desc` |
| `top_rated` | `sort_by=vote_average.desc&vote_count.gte=200` |
| `on_the_air` | `sort_by=popularity.desc&air_date.gte={today}&air_date.lte={+7d}` |
| `airing_today` | `sort_by=popularity.desc&air_date.gte={today}&air_date.lte={today}` |

Use the wrapper for the default view. Switch to `/discover/tv` as soon as you want a filter – a genre, a network, a country or a different vote threshold. Read `./discover.md` and `./trending-and-popular.md`.

`on_the_air` and `airing_today` accept a `timezone` parameter, for example `America/New_York`. Set it, or the window follows the TMDB default and your "today" is wrong for your users.

## Best practices and anti-patterns

| Do this | Don't do this |
| --- | --- |
| Batch sub-requests with `append_to_response` | Fire one HTTP request per section of a page |
| Read `roles[]` from `aggregate_credits` | Read `character` from `aggregate_credits` |
| Use `total_episode_count` for a person | Sum the `episode_count` values in `roles` |
| Filter out `season_number == 0` for a season list | Trust `number_of_seasons` to match `len(seasons)` |
| Keep `include_image_language=<lang>,null` | Send `language` alone and lose all artwork |
| Cache details and credits for hours | Re-fetch a static show on every page view |
| Attribute JustWatch on provider data | Show provider logos with no attribution |
| Track updates with `/changes` | Re-crawl every id every day |
| Build image URLs from `/configuration` | Hard-code `image.tmdb.org` sizes |
| Test every `*_path` for `null` | Concatenate a `null` path into a URL |

## Common pitfalls

1. **`name` vs `original_name`.** `name` follows `language`. `original_name` never moves. Show both when they differ.
2. **`episode_run_time` is an array and it is often empty.** Fall back to `last_episode_to_air.runtime`, or show nothing.
3. **`number_of_episodes` counts every season, including Specials.** Your own sum over `seasons[].episode_count` can differ.
4. **`next_episode_to_air` is `null` more often than you expect**, even on a returning series. A date field can also be `""` instead of `null`. Parse defensively.
5. **The appended provider key keeps its slash**: `response["watch/providers"]`.
6. **Episode group ids are strings.** Do not cast them to `int`. `/similar` also declares `series_id` as a string – send the integer as text.
7. **Content ratings are country-specific strings.** Never sort or compare them numerically.
8. **`/tv/latest` returns a nearly empty object.** A brand new show has no images, no networks and no genres.
9. **Sub-requests do not paginate inside `append_to_response`.** You get page 1 only. Call `/reviews` or `/recommendations` directly for page 2.
10. **TV genre ids differ from movie genre ids** (`10765` Sci-Fi & Fantasy, `10759` Action & Adventure). Read `./entities.md`.

## Related skill files

| File | Go there for |
| --- | --- |
| `./tv-seasons-and-episodes.md` | Everything below the series: season details, episode details, episode group detail, per-episode credits, images, videos and ratings |
| `./append-to-response.md` | The general batching rules and the parameter interactions |
| `./movies.md` | The movie namespace – similar shapes, different names (`title`, `release_date`, `release_dates`) |
| `./people-and-credits.md` | A person's TV credits and `credit_id` lookups |
| `./search-and-find.md` | `/search/tv` and `/find/{external_id}` to get a series id |
| `./discover.md` | Filtered TV queries: network, genre, country, air date, keyword |
| `./trending-and-popular.md` | `/trending/tv/{window}` and the popularity lists |
| `./images-and-configuration.md` | Image base URLs, size buckets and selection |
| `./localization.md` | `language`, `region` and translation fallbacks |
| `./watch-providers.md` | Provider and region catalogues, plus the JustWatch terms |
| `./user-account-and-ratings.md` | Rated shows, favourites and the watchlist |
| `./lists.md` | Reading and building user lists |
| `./changes-and-exports.md` | The global change feed and the daily ID exports |
| `./authentication.md`, `./getting-started.md` | Tokens, sessions and rate limits |
| `./entities.md` | Genre, network and keyword reference data |
