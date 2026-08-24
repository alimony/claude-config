# TMDB: append_to_response and Efficient Requests
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Core concepts

`append_to_response` adds sub-requests to a detail request. The API runs them in the same namespace and returns one JSON document. You send one HTTP request and you get the parent object plus each sub-request as a new key.

This is the largest efficiency gain in the TMDB API. A movie page that needs details, credits, images, videos, external IDs, release dates and watch providers costs 7 requests without it. It costs 1 request with it. TMDB limits bulk traffic near 40 requests per second, so each saved request also protects you from a `429`.

Three rules define the feature:

- Only detail methods support it: movie, TV series, TV season, TV episode and person.
- A sub-request must live in the same namespace as the parent. You can append `/movie/{id}/credits` to `/movie/{id}`. You cannot append a TV method to a movie.
- The maximum is 20 sub-requests per call.

The sub-request name is the path segment after the parent. `/movie/{id}/release_dates` becomes `release_dates`. The response key uses the same name.

## Basic syntax

Add one sub-request:

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/11?append_to_response=videos' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

Add many sub-requests with commas. Do not put a space after a comma.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/11?append_to_response=videos,images,credits' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

```python
import requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": "application/json"}

r = requests.get(f"{BASE}/movie/11", headers=HEADERS,
                 params={"append_to_response": "videos,images,credits", "language": "en-US"})
r.raise_for_status()
movie = r.json()
print(movie["title"], len(movie["credits"]["cast"]), movie["videos"]["results"][0]["key"])
```

```js
const url = new URL("https://api.themoviedb.org/3/movie/11");
url.searchParams.set("append_to_response", "videos,images,credits");
url.searchParams.set("language", "en-US");
const movie = await (await fetch(url, {
  headers: { Authorization: `Bearer ${ACCESS_TOKEN}`, accept: "application/json" },
})).json();
```

## Valid sub-request names per parent

### Movie – `/3/movie/{movie_id}`

| Sub-request | Own query parameters | Note |
| :--- | :--- | :--- |
| `account_states` | `session_id`, `guest_session_id` | Needs a user or guest session |
| `alternative_titles` | `country` | |
| `changes` | `start_date`, `end_date`, `page` | |
| `credits` | `language` | Cast and crew |
| `external_ids` | – | IMDb, Wikidata, social IDs |
| `images` | `include_image_language`, `language` | |
| `keywords` | – | |
| `lists` | `language`, `page` | Paginated |
| `recommendations` | `language`, `page` | Paginated |
| `release_dates` | – | Holds certifications |
| `reviews` | `language`, `page` | Paginated |
| `similar` | `language`, `page` | Paginated |
| `translations` | – | |
| `videos` | `language` | |
| `watch/providers` | – | The name holds a slash |

The movie namespace has 15 sub-requests, so all of them fit inside the 20 limit.

### TV series – `/3/tv/{series_id}`

| Sub-request | Own query parameters | Note |
| :--- | :--- | :--- |
| `account_states` | `session_id`, `guest_session_id` | |
| `aggregate_credits` | `language` | Credits across all seasons |
| `alternative_titles` | – | |
| `changes` | `start_date`, `end_date`, `page` | |
| `content_ratings` | – | The TV equivalent of `release_dates` |
| `credits` | `language` | |
| `episode_groups` | – | |
| `external_ids` | – | |
| `images` | `include_image_language`, `language` | |
| `keywords` | – | |
| `lists` | `language`, `page` | Paginated |
| `recommendations` | `language`, `page` | Paginated |
| `reviews` | `language`, `page` | Paginated |
| `screened_theatrically` | – | |
| `similar` | `language`, `page` | Paginated |
| `translations` | – | |
| `videos` | `include_video_language`, `language` | |
| `watch/providers` | – | |
| `season/{n}` | – | Shorthand, see below |
| `season/{n}/episode/{m}` | – | Shorthand, see below |

The TV series namespace has 18 named sub-requests. Add season shorthands with care, because the total limit stays at 20.

### TV season and TV episode

Parents: `/3/tv/{series_id}/season/{season_number}` and `.../episode/{episode_number}`.

| Sub-request | Season | Episode | Own query parameters |
| :--- | :---: | :---: | :--- |
| `account_states` | yes | yes | `session_id`, `guest_session_id` |
| `aggregate_credits` | yes | – | `language` |
| `credits` | yes | yes | `language` |
| `external_ids` | yes | yes | – |
| `images` | yes | yes | `include_image_language`, `language` |
| `translations` | yes | yes | – |
| `videos` | yes | yes | `include_video_language`, `language` |
| `watch/providers` | yes | – | `language` |

### Person – `/3/person/{person_id}`

| Sub-request | Own query parameters | Note |
| :--- | :--- | :--- |
| `changes` | `start_date`, `end_date`, `page` | |
| `combined_credits` | `language` | Movie and TV credits together |
| `external_ids` | – | |
| `images` | – | Profile images |
| `movie_credits` | `language` | |
| `tagged_images` | `page` | Paginated |
| `translations` | – | Biography translations |
| `tv_credits` | `language` | |

### Not supported

Collection details (`/3/collection/{collection_id}`) does **not** accept `append_to_response`. Its OpenAPI definition lists only `collection_id` and `language`. Call `/3/collection/{id}/images` and `/3/collection/{id}/translations` separately. Search, discover, trending and list methods also reject it. Only the five detail methods above accept it.

## Query parameters and the dot syntax

A sub-request keeps its own query parameters. Two forms exist.

**Shared form (documented and always safe).** Put the parameter at the top level. Every sub-request that supports that parameter reads it.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?append_to_response=images&language=en-US&include_image_language=en,null' \
     --header 'Authorization: Bearer <access_token>'
```

`language=en-US` filters the images. `include_image_language=en,null` adds back the English images and the images with no language tag. Use ISO 639-1 codes plus the literal `null`. Images do not support regional variants such as `en-US` in `include_image_language`.

**Scoped form (dot syntax).** Prefix the parameter with the sub-request name and a dot. The parameter then applies to that one sub-request.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?append_to_response=images,videos&language=de-DE&images.include_image_language=de,en,null' \
     --header 'Authorization: Bearer <access_token>'
```

Use the scoped form when two sub-requests need different values. Verify the result in your own response, because the official page documents only the shared form. If the scoped form does not change the output, fall back to the shared form.

```python
# Do this – the fallback keeps the posters.
params = {"append_to_response": "images", "language": "en-US", "include_image_language": "en,null"}

# Don't do this – a narrow language filter often returns empty image arrays.
params = {"append_to_response": "images", "language": "sv-SE"}
```

## Season and episode shorthand

TV series details accepts a path fragment as a sub-request name. This pulls a full season or a full episode into the series response.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/tv/1399?append_to_response=season/1,season/1/episode/2' \
     --header 'Authorization: Bearer <access_token>'
```

The response keys carry the same names:

```json
{
  "id": 1399,
  "name": "Game of Thrones",
  "number_of_seasons": 8,
  "seasons": [ { "season_number": 1, "episode_count": 10 } ],
  "season/1": { "id": 3624, "name": "Season 1", "episodes": [ ... ] },
  "season/1/episode/2": { "id": 63057, "name": "The Kingsroad", "episode_number": 2 }
}
```

Read the keys with bracket access, because the names hold slashes:

```python
season_one = series["season/1"]
episode_two = series["season/1/episode/2"]
```

**Do this** – `GET /3/tv/1399?append_to_response=season/1`. Load one season when the user opens it.

**Don't do this** – `GET /3/tv/1399?append_to_response=season/1,season/2,...,season/8`. The payload grows large and you approach the 20 limit.

The parent `seasons` array already holds the season list, the poster and the episode count. Use it for the season selector.

## What append_to_response cannot do

| Limit | Result | Correct action |
| :--- | :--- | :--- |
| More than 20 sub-requests | `400` with error code 27: "Too many append to response objects: The maximum number of remote calls is 20." | Split the call in two |
| Pagination of a sub-request | An appended paginated sub-request gives you page 1 | Call the sub-endpoint directly for page 2 and higher |
| A different page per sub-request | A shared `page` parameter hits every paginated sub-request | Drop `page` from the append call, then page separately |
| A cross-namespace request | The key does not appear, or the API returns an error | Make a second request |
| A search, discover or list method | Not appendable | Make a second request |
| A `POST` or `DELETE` method, such as `rating` | Not appendable | Use the write endpoint directly |

```python
# One call gives page 1 of reviews and similar.
movie = requests.get(f"{BASE}/movie/550", headers=HEADERS,
                     params={"append_to_response": "reviews,similar"}).json()

# Call the sub-endpoint only when the user asks for more.
more = requests.get(f"{BASE}/movie/550/reviews", headers=HEADERS, params={"page": 2}).json()
```

## Full worked example

One request returns the whole movie page.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?append_to_response=credits,images,videos,external_ids,release_dates,watch/providers&language=en-US&include_image_language=en,null' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

```python
import requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "accept": "application/json"}

def movie_page(movie_id: int, language: str = "en-US") -> dict:
    """Fetch everything a movie detail page needs in one HTTP request."""
    params = {
        "append_to_response": "credits,images,videos,external_ids,release_dates,watch/providers",
        "language": language,
        "include_image_language": f"{language.split('-')[0]},null",
    }
    r = requests.get(f"{BASE}/movie/{movie_id}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

m = movie_page(550)

director = next(c["name"] for c in m["credits"]["crew"] if c["job"] == "Director")
trailer = next((v for v in m["videos"]["results"]
                if v["type"] == "Trailer" and v["site"] == "YouTube"), None)
us_certs = next((c for c in m["release_dates"]["results"] if c["iso_3166_1"] == "US"), None)
us_stream = m["watch/providers"]["results"].get("US", {}).get("flatrate", [])

print(m["title"], m["release_date"], director)
print("IMDb:", m["external_ids"]["imdb_id"])
print("Posters:", len(m["images"]["posters"]))
print("Streams on:", [p["provider_name"] for p in us_stream])
```

### Response shape

```json
{
  "id": 550,
  "title": "Fight Club",
  "overview": "A ticking-time-bomb insomniac ...",
  "release_date": "1999-10-15",
  "runtime": 139,
  "genres": [ { "id": 18, "name": "Drama" } ],
  "vote_average": 8.4,
  "credits": {
    "cast": [ { "id": 819, "name": "Edward Norton", "character": "The Narrator",
                "order": 0, "profile_path": "/eIkFHNlfretLS1spAcIoihKUS62.jpg" } ],
    "crew": [ { "id": 7467, "name": "David Fincher", "job": "Director",
                "department": "Directing" } ]
  },
  "images": {
    "backdrops": [ { "file_path": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg", "iso_639_1": null,
                     "width": 3840, "height": 2160, "aspect_ratio": 1.778,
                     "vote_average": 5.39, "vote_count": 4 } ],
    "logos":     [ { "file_path": "/mmd1HnuvAzFc4iuVJcnBrhDNEKr.png", "iso_639_1": "en" } ],
    "posters":   [ { "file_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", "iso_639_1": "en" } ]
  },
  "videos": {
    "results": [ { "key": "O-b2VfmmbyA", "name": "Trailer", "site": "YouTube",
                   "type": "Trailer", "size": 1080, "official": true,
                   "iso_639_1": "en", "iso_3166_1": "US",
                   "published_at": "2016-03-05T02:03:14.000Z" } ]
  },
  "external_ids": { "imdb_id": "tt0137523", "wikidata_id": "Q190050",
                    "facebook_id": "FightClub", "instagram_id": null, "twitter_id": null },
  "release_dates": {
    "results": [ { "iso_3166_1": "US",
                   "release_dates": [ { "certification": "R", "type": 3, "iso_639_1": "",
                                        "release_date": "1999-10-15T00:00:00.000Z" } ] } ]
  },
  "watch/providers": {
    "results": {
      "US": { "link": "https://www.themoviedb.org/movie/550/watch?locale=US",
              "flatrate": [ { "provider_id": 1899, "provider_name": "Max" } ],
              "rent":     [ { "provider_id": 2, "provider_name": "Apple TV" } ] }
    }
  }
}
```

Notes on the shape:

- Each appended key holds the same body that the standalone endpoint returns.
- `credits`, `images` and `videos` keep their own container fields (`cast`/`crew`, `posters`/`backdrops`/`logos`, `results`).
- Do not depend on a nested `id` field inside an appended object. Read the id from the top level.
- `watch/providers` holds a slash. Use `m["watch/providers"]` in Python and `m["watch/providers"]` in JavaScript, never dot access.

## Search, then fetch the details in one call

TMDB recommends this two-step workflow. Search returns a light list object. Details returns the full record.

Step 1 – search with `GET /3/search/movie?query=Jack+Reacher`. Step 2 – take the `id` from the first result and fetch everything in one detail request.

```python
def find_and_load(title: str) -> dict | None:
    hits = requests.get(f"{BASE}/search/movie", headers=HEADERS,
                        params={"query": title}).json()["results"]
    if not hits:
        return None
    return movie_page(hits[0]["id"])   # 1 detail request, not 7

movie = find_and_load("Jack Reacher")
```

Total cost: 2 HTTP requests for a complete movie page.

**Don't do this** – a fan-out that costs 8 requests and can trigger a `429`:

```python
mid = search(...)["results"][0]["id"]
details = get(f"/movie/{mid}")
for sub in ("credits", "images", "videos", "external_ids", "release_dates", "watch/providers"):
    parts[sub] = get(f"/movie/{mid}/{sub}")
```

## Best practices

- Append only the data that the current view shows. A large append payload costs bandwidth and parse time on the client.
- Keep one append profile per view. Define it once in a constant, then reuse it. This keeps your cache keys stable.
- Set `language` once at the top level. It flows to `credits`, `videos`, `images`, `recommendations` and the other language-aware sub-requests.
- Add `include_image_language` whenever you append `images`. A bare `language` filter often returns empty image arrays.
- Cache the combined response under one key, for example `movie:550:en-US:v3`. One request produces one cache entry.
- Count your sub-requests before you build the string. Stop at 20.
- Handle a missing key. A sub-request that needs authentication, such as `account_states`, returns nothing useful without a `session_id`.

## Anti-patterns

| Anti-pattern | Why it fails | Do this instead |
| :--- | :--- | :--- |
| A loop of one request per sub-resource | 7 round trips, higher `429` risk | Use one `append_to_response` call |
| `append_to_response` on a search or discover call | The parameter is ignored | Search, then fetch the detail with append |
| `append_to_response=all` | No such value exists | Name each sub-request |
| A space after each comma | The name does not match | Use `a,b,c` with no spaces |
| `movie.credits` as a name | The name is the path segment | Use `credits` |
| A `page` parameter added to a big append call | Every paginated sub-request moves together | Page the sub-endpoint separately |
| An append call with `season/1` … `season/20` | Over the limit and a huge payload | Load one season on demand |

## Common pitfalls

- **Error 27.** A `400` with "Too many append to response objects: The maximum number of remote calls is 20" means you passed more than 20 names. Split the call.
- **A silent empty key.** An unknown or misspelled sub-request name does not raise an error. The key is simply absent. Guard your reads with `.get()`.
- **The slash in `watch/providers`.** The name and the response key both hold a slash. Do not URL-encode the slash inside the `append_to_response` value, and do not use dot access on the key.
- **Empty image arrays.** A narrow `language` value filters out all images. Add `include_image_language=<lang>,null`.
- **Region-specific keys.** `release_dates` and `watch/providers` return every country. Select your country from `results` yourself.
- **`account_states` without a session.** The sub-request needs `session_id` or `guest_session_id` as a shared query parameter.
- **Collections.** Collection details rejects the parameter. Make separate calls for collection images and translations.
- **Payload growth.** `credits` on a large TV series and `images` on a popular movie both return long arrays. Measure the response size before you append both in a mobile client.

## Related skill files

- `./getting-started.md` – base URL, request format and the general request flow.
- `./authentication.md` – the bearer token and the `session_id` that `account_states` needs.
- `./images-and-configuration.md` – `include_image_language`, image sizes and full image URLs.
- `./localization.md` – how `language` and `region` change the parent and every sub-request.
- `./movies.md`, `./tv-series.md`, `./tv-seasons-and-episodes.md`, `./people-and-credits.md` – the full response of each sub-endpoint in these four namespaces.
- `./search-and-find.md`, `./discover.md`, `./trending-and-popular.md` – the methods that give you the IDs to fetch with append.
- `./watch-providers.md` – how to read the `watch/providers` result object.
- `./user-account-and-ratings.md` – `account_states` and the session it needs.
- `./entities.md` – collections, companies, networks and keywords, which do not support append.
- `./lists.md` – the `lists` sub-request.
- `./changes-and-exports.md` – the `changes` sub-request and its date window.
