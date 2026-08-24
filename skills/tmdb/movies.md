# TMDB: Movies
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Core concepts

A movie is the primary entity of TMDB. Every movie has a stable integer `movie_id` (for example `550` = Fight Club, `11` = Star Wars). All movie endpoints live in one namespace below `https://api.themoviedb.org/3/movie/{movie_id}`.

Three rules control almost all movie work:

1. **The sub-endpoints belong to one namespace.** Use `append_to_response` to get the details plus the sub-endpoints in one HTTP request. See [./append-to-response.md](./append-to-response.md).
2. **The API returns image paths, not image URLs.** Build the URL from the configuration `base_url`, a size and the `file_path`. See [./images-and-configuration.md](./images-and-configuration.md).
3. **`language` and `region` change the content of the response.** `language` translates the text. `region` filters release information. See [./localization.md](./localization.md).

Authenticate every request with the read access token in the `Authorization` header. See [./authentication.md](./authentication.md).

```bash
export TMDB_TOKEN="<your v4 read access token>"
curl -s --request GET \
  --url 'https://api.themoviedb.org/3/movie/550' \
  --header "Authorization: Bearer $TMDB_TOKEN" \
  --header 'accept: application/json'
```

## Quick reference: movie endpoints

All paths start with `https://api.themoviedb.org/3`. The "Append" column shows the value to put in `append_to_response` on the details call.

| Path | Returns | Notable parameters | Append |
| :--- | :--- | :--- | :--- |
| `GET /movie/{movie_id}` | Top level details of one movie | `language`, `append_to_response` | – |
| `GET /movie/{movie_id}/account_states` | Favourite, watchlist and rating status for the logged in user | `session_id`, `guest_session_id` | `account_states` |
| `GET /movie/{movie_id}/alternative_titles` | Titles used in other countries | `country` (ISO-3166-1) | `alternative_titles` |
| `GET /movie/{movie_id}/changes` | Field level change log | `start_date`, `end_date`, `page` | `changes` |
| `GET /movie/{movie_id}/credits` | `cast` and `crew` arrays | `language` | `credits` |
| `GET /movie/{movie_id}/external_ids` | IMDb, Wikidata, Facebook, Instagram, Twitter ids | – | `external_ids` |
| `GET /movie/{movie_id}/images` | `posters`, `backdrops`, `logos` | `language`, `include_image_language` | `images` |
| `GET /movie/{movie_id}/keywords` | Plot keyword ids and names | – | `keywords` |
| `GET /movie/latest` | The newest movie id on TMDB | – | – |
| `GET /movie/{movie_id}/lists` | Public user lists that contain the movie | `language`, `page` | `lists` |
| `GET /movie/{movie_id}/recommendations` | Movies that TMDB users also liked | `language`, `page` | `recommendations` |
| `GET /movie/{movie_id}/release_dates` | Release dates and certifications per country | – | `release_dates` |
| `GET /movie/{movie_id}/reviews` | User reviews | `language`, `page` | `reviews` |
| `GET /movie/{movie_id}/similar` | Movies with the same genres and keywords | `language`, `page` | `similar` |
| `GET /movie/{movie_id}/translations` | Translated title, tagline and overview | – | `translations` |
| `GET /movie/{movie_id}/videos` | Trailers, teasers and clips | `language` | `videos` |
| `GET /movie/{movie_id}/watch/providers` | Streaming, rent and buy availability per country | – | `watch/providers` |
| `POST /movie/{movie_id}/rating` | Adds a user rating | `session_id` or `guest_session_id`, JSON body | – |
| `DELETE /movie/{movie_id}/rating` | Removes a user rating | `session_id` or `guest_session_id` | – |
| `GET /movie/now_playing` | Movies in theatres now | `language`, `page`, `region` | – |
| `GET /movie/popular` | Movies ordered by popularity | `language`, `page`, `region` | – |
| `GET /movie/top_rated` | Movies ordered by rating | `language`, `page`, `region` | – |
| `GET /movie/upcoming` | Movies that release soon | `language`, `page`, `region` | – |

The four list endpoints belong to [./trending-and-popular.md](./trending-and-popular.md). The two rating endpoints belong to [./user-account-and-ratings.md](./user-account-and-ratings.md).

## Pattern: get everything in one request

Make one request with `append_to_response`. Do not make ten requests for one movie page.

```bash
curl -s --request GET \
  --url 'https://api.themoviedb.org/3/movie/550?language=en-US&append_to_response=credits,images,videos,external_ids,release_dates,keywords,recommendations,watch/providers&include_image_language=en,null' \
  --header "Authorization: Bearer $TMDB_TOKEN" \
  --header 'accept: application/json'
```

```python
import os
import requests

BASE = "https://api.themoviedb.org/3"
SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
    "accept": "application/json",
})

def get_movie(movie_id, language="en-US"):
    """Return the movie details plus the sub-resources of one page."""
    params = {
        "language": language,
        "append_to_response": ",".join([
            "credits", "images", "videos", "external_ids",
            "release_dates", "keywords", "recommendations", "watch/providers",
        ]),
        "include_image_language": "en,null",
    }
    response = SESSION.get(f"{BASE}/movie/{movie_id}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()

movie = get_movie(550)
print(movie["title"], movie["release_date"], movie["runtime"])
print(len(movie["credits"]["cast"]), "cast members")
print(movie["watch/providers"]["results"].get("US", {}).get("link"))
```

```javascript
const params = new URLSearchParams({
  language: "en-US",
  append_to_response: "credits,images,videos,external_ids,release_dates",
  include_image_language: "en,null",
});
const res = await fetch(`https://api.themoviedb.org/3/movie/550?${params}`, {
  headers: { Authorization: `Bearer ${process.env.TMDB_TOKEN}`, accept: "application/json" },
});
const movie = await res.json();
```

**Rules for `append_to_response`:**

- Append a maximum of 20 sub-resources. TMDB returns status code 27 above that limit.
- Append only endpoints in the movie namespace. `append_to_response=season/1` fails on a movie.
- The top level query parameters apply to every sub-request. `language=de-DE` also filters the appended images and videos.
- The appended key equals the path segment. `watch/providers` keeps the slash: read `movie["watch/providers"]`.
- Paged sub-resources return page 1 only. Call the sub-endpoint directly to get page 2.

## The movie details response

| Field | Type | Notes |
| :--- | :--- | :--- |
| `id` | integer | The TMDB movie id. Use it as your foreign key. |
| `imdb_id` | string or null | The IMDb id, for example `tt0137523`. Null for many small titles. |
| `title` / `original_title` | string | `title` follows `language`. `original_title` stays in the original language. |
| `original_language` | string | ISO-639-1 code, for example `en`. |
| `origin_country` | array of string | ISO-3166-1 codes of the production origin. |
| `overview` | string | Can be an empty string when no translation exists. |
| `tagline` | string | Often an empty string. |
| `belongs_to_collection` | object or null | `{id, name, poster_path, backdrop_path}`. Use the id with the collection endpoints in [./entities.md](./entities.md). |
| `genres` | array | `[{id, name}]`. The name follows `language`; the id does not change. |
| `runtime` | integer or null | Minutes. `0` or null for unreleased titles. |
| `status` | string | `Rumored`, `Planned`, `In Production`, `Post Production`, `Released` or `Canceled`. |
| `release_date` | string | `YYYY-MM-DD`, or an empty string for an unscheduled title. This is the primary date, not your country's date. |
| `vote_average` / `vote_count` | number / integer | `vote_average` is `0` when `vote_count` is `0`. |
| `popularity` | number | A daily lifetime score. It is not a quality score. |
| `budget` / `revenue` | integer | US dollars. `0` means "unknown", not "zero". |
| `adult` | boolean | Adult content flag. |
| `video` | boolean | True for direct-to-video style entries. |
| `poster_path` / `backdrop_path` | string or null | Image paths, not URLs. |
| `production_companies` | array | `[{id, name, logo_path, origin_country}]`. |
| `production_countries` | array | `[{iso_3166_1, name}]`. |
| `spoken_languages` | array | `[{iso_639_1, english_name, name}]`. |
| `homepage` | string | Often an empty string. |

Handle empty data defensively. TMDB uses `null`, `""` and `0` for "we do not know".

```python
def money(value):
    """Format budget or revenue. TMDB uses 0 for unknown."""
    return f"${value:,}" if value else "unknown"

def year(movie):
    return (movie.get("release_date") or "")[:4] or "TBA"

def rating(movie, min_votes=50):
    """Hide the score until enough people voted."""
    if movie.get("vote_count", 0) < min_votes:
        return None
    return round(movie["vote_average"], 1)
```

## Credits: cast and crew

`GET /movie/{movie_id}/credits` returns `id`, `cast` and `crew`. Both arrays hold person objects with `id`, `name`, `original_name`, `gender`, `known_for_department`, `profile_path`, `popularity` and `credit_id`.

- **`cast`** adds `character`, `order` and `cast_id`. `order` is the billing position. `order: 0` is the top billed actor.
- **`crew`** adds `department` (for example `Directing`, `Writing`, `Production`) and `job` (for example `Director`, `Screenplay`).
- **`credit_id`** identifies one specific credit. Use it with the credit endpoint in [./people-and-credits.md](./people-and-credits.md). Do not use it as a person id.
- One person can appear more than one time in `crew` with different jobs. Deduplicate on `id` when you show a crew list.

```python
def top_billed(credits, limit=10):
    """Return the cast in billing order."""
    cast = sorted(credits["cast"], key=lambda person: person.get("order", 999))
    return cast[:limit]

def crew_by_job(credits, *jobs):
    """Example: crew_by_job(credits, "Director") or crew_by_job(credits, "Screenplay", "Writer")."""
    return [person for person in credits["crew"] if person.get("job") in jobs]

for person in top_billed(movie["credits"]):
    print(f'{person["order"]:>2}  {person["name"]} as {person["character"]}')
```

**Do this:** sort the cast by `order`.
**Don't do this:** trust the array order, or sort the cast by `popularity`. Popularity ranks the actor's fame today, not the role in this film.

## Images: pick a poster and a backdrop

`GET /movie/{movie_id}/images` returns `posters`, `backdrops` and `logos`. Each item has `file_path`, `iso_639_1`, `width`, `height`, `aspect_ratio`, `vote_average` and `vote_count`.

`language` **filters** the images. Add `include_image_language` to get more languages back. Use `null` in that list to keep the images with no language tag – most backdrops have none.

```bash
curl -s --request GET \
  --url 'https://api.themoviedb.org/3/movie/550/images?language=en&include_image_language=en,null' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
IMAGE_BASE = "https://image.tmdb.org/t/p"

def image_url(file_path, size="w500"):
    """Build an image URL. Read the real sizes from /configuration."""
    return f"{IMAGE_BASE}/{size}{file_path}" if file_path else None

def best_poster(images, language="en"):
    """Prefer a poster in the wanted language, then the best rated one."""
    posters = images.get("posters", [])
    localized = [p for p in posters if p.get("iso_639_1") == language]
    pool = localized or posters
    if not pool:
        return None
    return max(pool, key=lambda p: (p.get("vote_average", 0), p.get("vote_count", 0)))

def best_backdrop(images):
    """Prefer a textless backdrop, so your own title text stays readable."""
    backdrops = images.get("backdrops", [])
    textless = [b for b in backdrops if b.get("iso_639_1") is None]
    pool = textless or backdrops
    if not pool:
        return None
    return max(pool, key=lambda b: (b.get("vote_average", 0), b.get("width", 0)))

print(image_url(best_poster(movie["images"])["file_path"], "w500"))
print(image_url(movie["backdrop_path"], "w1280"))
```

**Do this:** use `poster_path` from the details response for a single thumbnail. It is already the best image for your language.
**Don't do this:** call `/images` only to find a poster you already have.

Read the size list from `/configuration` one time per day and cache it. See [./images-and-configuration.md](./images-and-configuration.md).

## Videos: build a YouTube URL

`GET /movie/{movie_id}/videos` returns `results` with `key`, `site`, `type`, `name`, `size`, `official`, `published_at`, `iso_639_1` and `iso_3166_1`.

- `site` is almost always `YouTube`, sometimes `Vimeo`. Check it before you build a URL.
- `type` is `Trailer`, `Teaser`, `Clip`, `Featurette`, `Behind the Scenes`, `Bloopers` or `Opening Credits`.
- `official` marks a video from the studio channel. Fan uploads have `official: false`.
- `iso_639_1` and `iso_3166_1` give the language and country of the video.

```python
def video_url(video):
    if video["site"] == "YouTube":
        return f"https://www.youtube.com/watch?v={video['key']}"
    if video["site"] == "Vimeo":
        return f"https://vimeo.com/{video['key']}"
    return None

def main_trailer(videos, language="en", country="US"):
    """Pick the newest official trailer for one locale."""
    candidates = [v for v in videos["results"]
                  if v["site"] == "YouTube" and v["type"] in ("Trailer", "Teaser")
                  and v.get("iso_639_1") == language and v.get("iso_3166_1") == country]
    if not candidates:
        candidates = [v for v in videos["results"] if v["type"] == "Trailer"]
    if not candidates:
        return None
    candidates.sort(key=lambda v: (v.get("official", False), v.get("published_at", "")), reverse=True)
    return candidates[0]

trailer = main_trailer(movie["videos"])
print(video_url(trailer), trailer["name"])
```

The YouTube thumbnail needs no API call: `https://img.youtube.com/vi/{key}/hqdefault.jpg`.

**Gotcha:** `language=de-DE` on the details call also filters the appended videos. A movie can then return an empty `results` array. Request the videos a second time with `language=en-US` as a fallback.

## External IDs: link to other sites

`GET /movie/{movie_id}/external_ids` returns `imdb_id`, `wikidata_id`, `facebook_id`, `instagram_id` and `twitter_id`. Every field can be `null`.

| Field | URL template |
| :--- | :--- |
| `imdb_id` | `https://www.imdb.com/title/{imdb_id}/` |
| `wikidata_id` | `https://www.wikidata.org/wiki/{wikidata_id}` |
| `facebook_id` | `https://www.facebook.com/{facebook_id}` |
| `instagram_id` | `https://www.instagram.com/{instagram_id}` |
| `twitter_id` | `https://twitter.com/{twitter_id}` |

```python
LINKS = {"imdb_id": "https://www.imdb.com/title/{}/", "wikidata_id": "https://www.wikidata.org/wiki/{}",
         "facebook_id": "https://www.facebook.com/{}", "instagram_id": "https://www.instagram.com/{}",
         "twitter_id": "https://twitter.com/{}"}

def external_links(external_ids):
    return {key: tpl.format(value) for key, tpl in LINKS.items() if (value := external_ids.get(key))}
```

The details response also carries `imdb_id`, so you do not need `external_ids` for IMDb alone. To go the other way – from an IMDb id to a TMDB movie – use `/find/{external_id}`. See [./search-and-find.md](./search-and-find.md).

## Release dates and certifications

`GET /movie/{movie_id}/release_dates` returns `results`, one entry per country. Each entry holds `iso_3166_1` and a `release_dates` array with `certification`, `descriptors`, `iso_639_1`, `note`, `release_date` and `type`.

| Type | Release |
| :--- | :--- |
| 1 | Premiere |
| 2 | Theatrical (limited) |
| 3 | Theatrical |
| 4 | Digital |
| 5 | Physical |
| 6 | TV |

One country can hold several entries – for example a limited release, a wide release and a digital release. The `certification` field is often an empty string. Search for the first non-empty value in the country.

```python
def certification(release_dates, country="US"):
    """Return the age rating for one country, or None."""
    for entry in release_dates["results"]:
        if entry["iso_3166_1"] != country:
            continue
        for release in entry["release_dates"]:
            if release.get("certification"):
                return release["certification"]
    return None

def release_date_for(release_dates, country="US", types=(3, 2, 1)):
    """Return the first matching release date for a country, by type priority."""
    for entry in release_dates["results"]:
        if entry["iso_3166_1"] != country:
            continue
        by_type = {r["type"]: r["release_date"] for r in entry["release_dates"]}
        for wanted in types:
            if wanted in by_type:
                return by_type[wanted][:10]
    return None

print(certification(movie["release_dates"], "US"))   # 'R'
print(release_date_for(movie["release_dates"], "DE"))
```

**Do this:** show `release_date_for(..., country)` when you know the user's country.
**Don't do this:** show the top level `release_date` as "the release date in your country". It is the primary date, and it is often the festival premiere.

`descriptors` holds content warnings, for example `["Violence"]`. It is often empty.

## Alternative titles

`GET /movie/{movie_id}/alternative_titles` returns `titles` with `iso_3166_1`, `title` and `type`. The `type` explains the variant, for example `romanization`, `working title` or `Hispanoamérica`. It is often an empty string. Filter with `?country=DE` on the server side.

```bash
curl -s --url 'https://api.themoviedb.org/3/movie/550/alternative_titles?country=DE' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

Use alternative titles to match user input against a local title. Do not use them for display – use `title` with the correct `language`.

## Keywords

`GET /movie/{movie_id}/keywords` returns `keywords` with `id` and `name`, for example `{"id": 818, "name": "based on novel or book"}`. Keywords are not localized.

Feed the keyword `id` back into [./discover.md](./discover.md) to build a "more like this" row that you control:

```bash
curl -s --url 'https://api.themoviedb.org/3/discover/movie?with_keywords=818,4565&sort_by=vote_average.desc&vote_count.gte=200' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

## Recommendations against similar

Both endpoints return a paged movie list with the standard short movie object (`id`, `title`, `genre_ids`, `poster_path`, `vote_average`, and more).

| Endpoint | Source of the result | Use it for |
| :--- | :--- | :--- |
| `/recommendations` | The behaviour of TMDB users – what people who liked this movie also liked | The main "you may also like" row |
| `/similar` | Only the genres and the plot keywords of this movie | A fallback, or a strict genre match |

The docs warn that `/similar` results "are not always going to be 100%", because the match uses genres and keywords alone. `/recommendations` can return an empty `results` array for an obscure movie.

```python
def more_like_this(movie_id, limit=12):
    """Use recommendations first, then similar as a fallback."""
    for path in ("recommendations", "similar"):
        response = SESSION.get(f"{BASE}/movie/{movie_id}/{path}", timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[:limit]
    return []
```

## Reviews

`GET /movie/{movie_id}/reviews` returns a paged list. Each review has `author`, `content`, `created_at`, `updated_at`, `url` and `author_details` with `name`, `username`, `avatar_path` and `rating`.

- `author_details.rating` can be `null` when the author wrote a review without a score.
- `content` is Markdown. Escape it or render it – do not inject it as raw HTML.
- `avatar_path` can hold a full Gravatar URL with a leading slash, for example `/https://secure.gravatar.com/avatar/....jpg`. Strip the leading slash before you use such a value; use the TMDB image base only for a real TMDB path.

```python
def avatar_url(avatar_path, size="w45"):
    if not avatar_path:
        return None
    if avatar_path.startswith("/https://") or avatar_path.startswith("/http://"):
        return avatar_path[1:]
    return f"{IMAGE_BASE}/{size}{avatar_path}"
```

## Watch providers

`GET /movie/{movie_id}/watch/providers` returns `results` keyed by ISO-3166-1 country code. Each country holds a TMDB `link` and the arrays `flatrate`, `rent`, `buy` and sometimes `ads` or `free`.

```python
def providers_for(movie, country="US"):
    data = movie["watch/providers"]["results"].get(country)
    if not data:
        return None
    names = lambda kind: [p["provider_name"] for p in data.get(kind, [])]
    return {"link": data["link"], "stream": names("flatrate"),
            "rent": names("rent"), "buy": names("buy")}
```

Two hard rules: the response holds **no deep links** – link the user to the TMDB `link` value. And you **must attribute JustWatch** as the source of the data. TMDB revokes API access for non-compliant use. Full detail is in [./watch-providers.md](./watch-providers.md).

## Account states and rating

`GET /movie/{movie_id}/account_states` returns `favorite`, `watchlist` and `rated`. `rated` is `false` when the user has not rated the movie, and `{"value": 9.0}` when the user has. Pass `session_id` or `guest_session_id`.

```bash
curl -s --url "https://api.themoviedb.org/3/movie/550/account_states?session_id=$SESSION_ID" \
  --header "Authorization: Bearer $TMDB_TOKEN"

curl -s --request POST \
  --url "https://api.themoviedb.org/3/movie/550/rating?session_id=$SESSION_ID" \
  --header "Authorization: Bearer $TMDB_TOKEN" \
  --header 'Content-Type: application/json;charset=utf-8' \
  --data '{"value": 8.5}'
```

The rating value runs from 0.5 to 10.0 in steps of 0.5. Append `account_states` to the details call to load the whole movie page in one request. See [./user-account-and-ratings.md](./user-account-and-ratings.md).

## Lists that contain a movie

`GET /movie/{movie_id}/lists` returns the public user lists that hold this movie, with `id`, `name`, `description`, `item_count`, `favorite_count`, `iso_639_1` and `list_type`. Popular movies return thousands of lists over hundreds of pages. Show page 1 only. See [./lists.md](./lists.md).

## Latest movie id

`GET /movie/latest` returns the movie object of the newest entry on TMDB. The record is usually almost empty – no poster, no overview, `imdb_id: null`. Use it to learn the current upper bound of the id range, not as content.

**Do this:** use the daily id export files to enumerate all valid ids.
**Don't do this:** loop from 1 to `latest.id` and request every id. Many ids are deleted, and the loop wastes millions of requests. See [./changes-and-exports.md](./changes-and-exports.md).

## Changes

`GET /movie/{movie_id}/changes` returns the recent field level changes. The response holds `changes` with a `key` (the field name, for example `images`, `overview`, `release_dates`) and an `items` array with `id`, `action` (`added`, `updated`, `deleted`), `time`, `iso_639_1`, `iso_3166_1` and `value`.

The default window is the last 24 hours. `start_date` and `end_date` extend it to a maximum of 14 days – a longer range returns status code 20. To find *which* movies changed, use the `/movie/changes` list endpoint in [./changes-and-exports.md](./changes-and-exports.md), then call this endpoint per movie.

## Translations

`GET /movie/{movie_id}/translations` returns every translation with `iso_639_1`, `iso_3166_1`, `name`, `english_name` and a `data` object with `title`, `tagline`, `overview`, `homepage` and `runtime`. Empty strings mean "not translated". Read the details endpoint with `language` when you need one language. Read this endpoint when you need a language picker or a fallback chain. See [./localization.md](./localization.md).

## Best practices

- **Batch with `append_to_response`.** One request for a movie page, not ten.
- **Cache aggressively.** Movie metadata changes slowly. Cache the details for hours. Cache `/configuration` for a day.
- **Store `id`, and refresh from `id`.** Titles, posters and even the `imdb_id` change. The TMDB id does not.
- **Reuse one HTTP session.** Keep the connection alive across requests.
- **Respect `429`.** The limit sits near 40 requests per second. Back off and retry when you receive `429`.
- **Check `vote_count` before you show `vote_average`.** A single 10/10 vote is not a rating.
- **Attribute TMDB**, and attribute JustWatch for watch provider data.

## Anti-patterns

| Don't do this | Do this |
| :--- | :--- |
| Request `/movie/{id}`, then `/credits`, then `/images`, then `/videos` | Use `append_to_response=credits,images,videos` |
| Hard-code `https://image.tmdb.org/t/p/w500` forever | Read `base_url` and the size list from `/configuration` and cache them |
| Show the top level `release_date` as the local release date | Derive the date from `/release_dates` for the user's country |
| Rank by `popularity` and call it "best" | Rank by `vote_average` with a `vote_count.gte` floor, through discover |
| Scan every id from 1 to `latest` | Use the daily id exports and the changes endpoints |
| Sort the cast by `popularity` | Sort the cast by `order` |
| Assume `belongs_to_collection` and `imdb_id` exist | Test for `null` before you use them |

## Common pitfalls

- **`language` filters, it does not only translate.** On `/images` and `/videos` it removes items. Always add `include_image_language=<lang>,null` for images, and keep an English fallback for videos.
- **The `watch/providers` key contains a slash.** Read `data["watch/providers"]`, not `data["watch_providers"]`.
- **Appended lists are page 1 only.** Call `/recommendations?page=2` directly for more.
- **20 appended objects is the maximum.** Status code 27 tells you that you crossed it.
- **Pages start at 1 and stop at 500.** Status code 22 tells you that the page number is invalid.
- **`budget: 0` and `revenue: 0` mean unknown.** Do not compute a profit from them.
- **`runtime` can be `0` or `null`** for an unreleased movie.
- **An unknown movie id returns HTTP 404** with `status_code` 34 or 6 in the body. Test `response.status_code`, not only the JSON keys.
- **A movie id can move.** TMDB merges duplicate entries, so a request can redirect or 404 later. Refresh dead ids from the changes feed.
- **`credit_id` is not a person id.** Use `person.id` to link to a person.
- **Genre names follow `language`, genre ids do not.** Store the id.

## Related skill files

- **Setup:** [./getting-started.md](./getting-started.md) (base URL, keys), [./authentication.md](./authentication.md) (bearer token, sessions).
- **Request shaping:** [./append-to-response.md](./append-to-response.md) (batching), [./localization.md](./localization.md) (`language`, `region`), [./images-and-configuration.md](./images-and-configuration.md) (image URLs and sizes).
- **Find a movie id:** [./search-and-find.md](./search-and-find.md) (title or IMDb id), [./discover.md](./discover.md) (filters), [./trending-and-popular.md](./trending-and-popular.md) (`/movie/popular`, `/movie/top_rated`, `/movie/now_playing`, `/movie/upcoming`).
- **Linked entities:** [./people-and-credits.md](./people-and-credits.md) (people, `credit_id`), [./entities.md](./entities.md) (collections, genres, keywords, companies), [./watch-providers.md](./watch-providers.md).
- **Same patterns elsewhere:** [./tv-series.md](./tv-series.md), [./tv-seasons-and-episodes.md](./tv-seasons-and-episodes.md).
- **User data and sync:** [./user-account-and-ratings.md](./user-account-and-ratings.md), [./lists.md](./lists.md), [./changes-and-exports.md](./changes-and-exports.md).
