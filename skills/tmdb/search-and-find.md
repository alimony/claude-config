# TMDB: Search and Find
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

TMDB gives three ways to locate an item. Pick the correct one first. This is the most important decision in the whole API.

| What you hold | Use | Endpoints | Skill file |
| :--- | :--- | :--- | :--- |
| Free text that a person typed ("fight club", "tom hanks") | **Search** | `/search/movie`, `/search/tv`, `/search/person`, `/search/multi`, `/search/collection`, `/search/company`, `/search/keyword` | this file |
| Attribute filters (genre, date range, rating, cast, provider, sort order) | **Discover** | `/discover/movie`, `/discover/tv` | `./discover.md` |
| An external ID (IMDb, TVDB, Wikidata, a social handle) | **Find** | `/find/{external_id}` | this file |
| A TMDB numeric ID | **Details** | `/movie/{id}`, `/tv/{id}`, `/person/{id}` | `./movies.md`, `./tv-series.md`, `./people-and-credits.md` |

Three rules follow from that table:

* Use search **only** for free text. Search has no genre filter, no rating filter, no date range and no `sort_by` parameter.
* Use discover for **every** attribute filter. Discover has approximately 30 filter parameters and a sort order. Do not try to imitate discover with a search query string.
* Use find when you already hold an external ID. Find is an exact lookup. It is faster and safer than a text search.

Search matches more than the display title. Movie search matches original, translated and alternative titles. TV search matches original, translated and "also known as" names. Person search matches the name and the "also known as" names.

### The shared response envelope

Every search endpoint returns the same paginated envelope. Find does **not**.

```json
{ "page": 1, "results": [ ... ], "total_pages": 2, "total_results": 39 }
```

Each page holds up to 20 items. See section 5 for the page cap.

### Request setup

All examples below send the v4 read access token as a bearer header (`export TMDB_TOKEN='<read access token>'`). Read `./authentication.md` for the token types and the older `api_key` parameter. Read `./getting-started.md` for the base URL and the error format.

## 2. Quick reference – every search endpoint

| Endpoint | Matches | `query` | `page` | `include_adult` | `language` | `region` | Date parameters |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `GET /3/search/movie` | original, translated and alternative titles | required | yes | yes | yes | yes | `year`, `primary_release_year` |
| `GET /3/search/tv` | original, translated and also-known-as names | required | yes | yes | yes | – | `year`, `first_air_date_year` |
| `GET /3/search/person` | name and also-known-as names | required | yes | yes | yes | – | – |
| `GET /3/search/multi` | movies, TV shows and people together | required | yes | yes | yes | – | – |
| `GET /3/search/collection` | original, translated and alternative names | required | yes | yes | yes | yes | – |
| `GET /3/search/company` | original and alternative names | required | yes | – | – | – | – |
| `GET /3/search/keyword` | keyword name | required | yes | – | – | – | – |

Defaults: `page=1`, `include_adult=false`, `language=en-US`.

Key fields in each result:

| Endpoint | Fields |
| :--- | :--- |
| `search/movie` | `id`, `title`, `original_title`, `release_date`, `overview`, `genre_ids`, `poster_path`, `backdrop_path`, `popularity`, `vote_average`, `vote_count`, `adult`, `video`, `original_language` |
| `search/tv` | `id`, `name`, `original_name`, `first_air_date`, `origin_country`, `overview`, `genre_ids`, `poster_path`, `backdrop_path`, `popularity`, `vote_average`, `vote_count` |
| `search/person` | `id`, `name`, `original_name`, `gender`, `known_for_department`, `profile_path`, `popularity`, `known_for[]` (up to 3 movie or TV objects with `media_type`) |
| `search/multi` | the movie or TV or person fields above, plus `media_type` |
| `search/collection` | `id`, `name`, `original_name`, `overview`, `poster_path`, `backdrop_path`, `original_language` |
| `search/company` | `id`, `name`, `logo_path`, `origin_country` |
| `search/keyword` | `id`, `name` |

`poster_path`, `backdrop_path`, `profile_path` and `logo_path` are partial paths. Build the full URL with the configuration base URL – read `./images-and-configuration.md`.

## 3. How to send a query correctly

### URL-encode the query

The `query` parameter carries spaces, accents, apostrophes, ampersands and colons. Let your HTTP client encode it. Never paste raw user text into a URL string.

```bash
# Do this – curl encodes each value for you
curl --request GET --get \
     --url 'https://api.themoviedb.org/3/search/movie' \
     --data-urlencode 'query=Amélie & Co' \
     --data-urlencode 'primary_release_year=2001' \
     --data-urlencode 'include_adult=false' \
     --header "Authorization: Bearer $TMDB_TOKEN" \
     --header 'accept: application/json'
```

```bash
# Don't do this – the space and the ampersand break the request
curl --url "https://api.themoviedb.org/3/search/movie?query=Amélie & Co"
```

```python
# Do this – requests encodes the params dict
import requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "accept": "application/json"}

def search(path, **params):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

data = search("/search/movie", query="Amélie & Co", primary_release_year=2001, include_adult=False)
```

```python
# Don't do this – an f-string in the URL corrupts the query
requests.get(f"{BASE}/search/movie?query={user_text}", headers=HEADERS)
```

```js
// Do this – URLSearchParams encodes the value
const url = new URL("https://api.themoviedb.org/3/search/movie");
url.searchParams.set("query", "Amélie & Co");
url.searchParams.set("include_adult", "false");
const res = await fetch(url, { headers: { Authorization: `Bearer ${token}`, accept: "application/json" } });
const data = await res.json();
```

Trim the text before you send it. Return early when the trimmed text is empty. An empty `query` gives a 400 error, because `query` is required.

### `include_adult`

`include_adult` defaults to `false`. Adult titles and adult performers stay out of the results. Set it to `true` only when your product permits adult content, and only when the user asked for it. The flag applies to `search/movie`, `search/tv`, `search/person`, `search/multi` and `search/collection`. `search/company` and `search/keyword` ignore it.

### `language`

`language` uses the `ISO 639-1` code, usually joined to an `ISO 3166-1` country code – for example `de-DE` or `pt-BR`. The parameter controls the **output** text (`title`, `overview`, `name`). It does not limit which titles the search matches. A user can type an English title and get the German translation back.

```bash
curl --request GET --get \
     --url 'https://api.themoviedb.org/3/search/movie' \
     --data-urlencode 'query=Whiplash' \
     --data-urlencode 'language=de-DE' \
     --data-urlencode 'region=DE' \
     --header "Authorization: Bearer $TMDB_TOKEN"
```

TMDB falls back to the English text when no translation exists. Read `./localization.md` for the fallback rules and the language list.

### `region`

`region` takes an `ISO 3166-1` code. On `search/movie` it acts as a presentation filter for release date information. TMDB shows the release date of that country. TMDB falls back to the primary release date when that country has no entry. `region` is **not** a filter that removes movies from the result set on search. Use discover with `region` plus `with_release_type` when you want a real regional filter.

### `year` compared with `primary_release_year`

| Endpoint | Parameter | Meaning | Use it when |
| :--- | :--- | :--- | :--- |
| `search/movie` | `primary_release_year` | The year of the primary release date | You know the premiere year. This is the precise filter. |
| `search/movie` | `year` | Any release year that the movie holds, including regional releases | A festival year or a regional year makes the primary year wrong |
| `search/tv` | `first_air_date_year` | The year of the first air date | You know the premiere year of the show |
| `search/tv` | `year` | Any air year that the show holds | The show ran for several years and the user gave one of them |

Use the precise parameter first. Retry without it when the result set is empty.

```python
def movie_candidates(title, year=None):
    tries = [{"primary_release_year": year}, {"year": year}, {}] if year else [{}]
    for extra in tries:
        hits = search("/search/movie", query=title, include_adult=False, **extra)["results"]
        if hits:
            return hits
    return []
```

Do not pass both `year` and `primary_release_year` in one request. The two filters fight each other and can empty the result set.

## 4. How results are ranked

TMDB does not publish the ranking rules. In practice the order mixes text relevance with popularity. A popular unrelated title can outrank the exact match. TMDB offers no `sort_by` on search.

**Do not treat `results[0]` as the answer.** Re-rank the first page yourself with the signals that you hold – the exact title, the year and the popularity.

```python
import unicodedata

def norm(text):
    text = unicodedata.normalize("NFKD", (text or "").casefold())
    kept = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
    return " ".join(kept.split())

def pick_best(results, title, year=None):
    """Return the most probable match, or None."""
    want = norm(title)

    def score(item):
        names = {norm(item.get("title") or item.get("name")),
                 norm(item.get("original_title") or item.get("original_name"))}
        points = 100 if want in names else 40 * any(want and want in n for n in names)
        date = item.get("release_date") or item.get("first_air_date") or ""
        if year and date[:4] == str(year):
            points += 50
        return points + min(item.get("popularity") or 0.0, 100) / 10

    return max(results, key=score) if results else None
```

Show the top 5 candidates when the score gap is small. An ambiguous title – for example "The Office" – needs a human choice, not a guess.

## 5. Pagination and the page cap

* `page` starts at 1. Each page holds up to 20 results.
* **The maximum page is 500.** A higher value returns HTTP 400 with TMDB status code 22: "Invalid page: Pages start at 1 and max at 500."
* `total_pages` can report a number above 500. Cap your loop.

```python
def iter_search(path, query, max_pages=5, **params):
    """Yield results page by page. Respect the 500 page cap."""
    page = 1
    while page <= max_pages:
        data = search(path, query=query, page=page, **params)
        yield from data["results"]
        last = min(data["total_pages"], 500)
        if page >= last:
            return
        page += 1
```

Do not page through hundreds of pages to build a catalogue. Use discover with a sort order for browsing, and use the daily ID export files for bulk work – see `./discover.md` and `./changes-and-exports.md`. TMDB removed the legacy rate limit, but an upper limit near 40 requests per second remains. Respect a `429` response.

## 6. Multi search and the `media_type` discriminator

`GET /3/search/multi` searches movies, TV shows and people in one request. Every result carries a `media_type` field. Branch on it, because the field names differ per type.

| `media_type` | Title field | Date field | Extra fields |
| :--- | :--- | :--- | :--- |
| `movie` | `title`, `original_title` | `release_date` | `video`, `genre_ids`, `adult` |
| `tv` | `name`, `original_name` | `first_air_date` | `origin_country`, `genre_ids` |
| `person` | `name`, `original_name` | – | `profile_path`, `known_for_department`, `known_for[]` |

```python
def label(item):
    kind = item["media_type"]
    if kind == "person":
        known = ", ".join(k.get("title") or k.get("name") for k in item.get("known_for", []))
        return f"[person] {item['name']} – {known}"
    title = item.get("title") or item.get("name")                       # movie vs tv
    year = (item.get("release_date") or item.get("first_air_date") or "????")[:4]
    return f"[{kind}] {title} ({year})"

for item in search("/search/multi", query="star wars")["results"]:
    print(label(item))
```

### Prefer multi when

* You build one search box that covers everything, for example a global header search.
* You want a single request and a single spinner.

### Prefer three typed searches when

* You need the year filters. Multi has no `year`, no `primary_release_year` and no `first_air_date_year`.
* You need `region`. Multi has no `region`.
* You must show separate result groups with their own counts and their own "more results" links.
* You must control the mix. Multi ranks all three types in one list, so a popular movie can push the correct person off the first page.
* You need collections, companies or keywords. Multi never returns them.

```python
import concurrent.futures as cf

def typed_search(query):
    kinds = ("movie", "tv", "person")
    with cf.ThreadPoolExecutor(3) as pool:
        jobs = {k: pool.submit(search, f"/search/{k}", query=query, include_adult=False)
                for k in kinds}
    return {k: job.result()["results"] for k, job in jobs.items()}
```

## 7. Find by external ID

`GET /3/find/{external_id}` converts an ID from another service into TMDB objects. Pass the source in the **required** `external_source` parameter.

| `external_source` | Example ID | Movies | TV shows | TV seasons | TV episodes | People |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `imdb_id` | `tt0137523`, `nm0000158` | yes | yes | – | yes | yes |
| `tvdb_id` | `81189` | – | yes | yes | yes | – |
| `wikidata_id` | `Q190050` | yes | yes | yes | yes | yes |
| `facebook_id` | `FightClub` | yes | yes | – | – | yes |
| `instagram_id` | `tomhanks` | yes | yes | – | – | yes |
| `twitter_id` | `tomhanks` | yes | yes | – | – | yes |
| `tiktok_id` | `tomhanks` | yes | yes | – | – | yes |
| `youtube_id` | `dQw4w9WgXcQ` | yes | yes | – | – | yes |

`language` is the only other parameter. Find has no `page` and no `query`.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/find/tt0137523?external_source=imdb_id&language=en-US' \
     --header "Authorization: Bearer $TMDB_TOKEN" \
     --header 'accept: application/json'
```

### The multi-bucket response

Find returns five arrays, not one `results` array. Empty arrays are normal. One ID usually fills exactly one bucket.

```json
{
  "movie_results": [ { "id": 934433, "title": "Scream VI", "media_type": "movie", "...": "..." } ],
  "person_results": [],
  "tv_results": [],
  "tv_episode_results": [],
  "tv_season_results": []
}
```

```python
BUCKETS = ("movie_results", "tv_results", "person_results",
           "tv_season_results", "tv_episode_results")

KIND = {"movie_results": "movie", "tv_results": "tv", "person_results": "person",
        "tv_season_results": "tv_season", "tv_episode_results": "tv_episode"}

def find_external(external_id, external_source="imdb_id", language="en-US"):
    """Return (kind, item) for the first non-empty bucket, or (None, None)."""
    data = search(f"/find/{external_id}",
                  external_source=external_source, language=language)
    for bucket in BUCKETS:
        items = data.get(bucket) or []
        if items:
            return KIND[bucket], items[0]
    return None, None

kind, item = find_external("tt0903747")     # -> ("tv", {... "name": "Breaking Bad" ...})
```

```js
const buckets = ["movie_results", "tv_results", "person_results",
                 "tv_season_results", "tv_episode_results"];
const hit = buckets.map((b) => [b, (data[b] ?? [])[0]]).find(([, item]) => item);
```

### Find gotchas

* `external_source` is required. A request without it fails.
* Send the ID in its native form. IMDb title IDs start with `tt`. IMDb person IDs start with `nm`. Do not strip the prefix.
* Send the bare handle for a social source. Send `tomhanks`, not the profile URL.
* Find is exact. An unknown ID returns HTTP 200 with five empty arrays, not a 404. Check the arrays.
* A TVDB episode ID fills `tv_episode_results`, which contains the episode object with its `show_id`, `season_number` and `episode_number`. Read `./tv-seasons-and-episodes.md`.
* Find gives list objects, not full details. Take the `id` and fetch the details endpoint next. For the reverse direction, read `/movie/{id}/external_ids` and its TV and person equivalents – see `./entities.md`.

## 8. The canonical two-step workflow

The documented flow is: **search for the ID, then query for the details.** Search results are list objects. They are deliberately small.

```bash
# Step 1 – search
curl --request GET --get --url 'https://api.themoviedb.org/3/search/movie' \
     --data-urlencode 'query=Jack Reacher' \
     --header "Authorization: Bearer $TMDB_TOKEN"
# -> results[0].id == 343611

# Step 2 – details, plus sub-requests in the same call
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/343611?append_to_response=credits,videos,external_ids' \
     --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
def resolve_movie(title, year=None, extras="credits,videos,images,external_ids,watch/providers"):
    """Search by title, then return the full movie details."""
    hits = movie_candidates(title, year)
    best = pick_best(hits, title, year)
    if best is None:
        return None
    return search(f"/movie/{best['id']}", append_to_response=extras)

movie = resolve_movie("Fight Club", 1999)
print(movie["runtime"], movie["imdb_id"], movie["credits"]["cast"][0]["name"])
```

`append_to_response` turns the second step into one HTTP call instead of five. Read `./append-to-response.md`.

### What search does not return

Never treat a search field as complete. These fields exist **only** on the details endpoint.

| Type | Search gives you | Search omits |
| :--- | :--- | :--- |
| Movie | `genre_ids` (numbers), `overview`, `release_date`, `vote_average` | `runtime`, `genres` (names), `budget`, `revenue`, `status`, `tagline`, `imdb_id`, `homepage`, `production_companies`, `spoken_languages`, `belongs_to_collection`, `credits`, `videos`, `images` |
| TV | `genre_ids`, `first_air_date`, `origin_country` | `number_of_seasons`, `number_of_episodes`, `seasons`, `episode_run_time`, `networks`, `created_by`, `status`, `last_episode_to_air`, `credits` |
| Person | `known_for`, `known_for_department`, `popularity` | `biography`, `birthday`, `deathday`, `place_of_birth`, `also_known_as`, `imdb_id`, `combined_credits` |
| Collection | `name`, `overview`, `poster_path` | `parts` (the member movies) |

Other traps in the list objects:

* `genre_ids` holds numbers. Map them with `/genre/movie/list` or `/genre/tv/list`, or read the `genres` array from the details response.
* `poster_path` and `backdrop_path` can be `null`.
* `release_date` and `first_air_date` can be an empty string for an unreleased item. Guard the slice `date[:4]`.
* `popularity` changes every day. Do not cache a ranking that you built from it. Read `./trending-and-popular.md`.

## 9. Bridge patterns – search into another endpoint

### Company or keyword: search for the ID, then discover

Search finds the ID. Discover does the real work.

```python
# "All A24 movies, newest first"
company = search("/search/company", query="A24")["results"][0]
films = search("/discover/movie",
               with_companies=company["id"],
               sort_by="primary_release_date.desc")

# "Movies with the keyword 'time travel', best rated"
keyword = search("/search/keyword", query="time travel")["results"][0]
films = search("/discover/movie",
               with_keywords=keyword["id"],
               sort_by="vote_average.desc",
               **{"vote_count.gte": 500})
```

Read `./discover.md` for the full filter list and `./entities.md` for the company, keyword and collection detail endpoints.

### Person or collection: search, then read the details

```python
person = pick_best(search("/search/person", query="Greta Gerwig")["results"], "Greta Gerwig")
detail = search(f"/person/{person['id']}", append_to_response="combined_credits,external_ids")

collection = search("/search/collection", query="The Avengers Collection")["results"][0]
parts = search(f"/collection/{collection['id']}")["parts"]        # the member movies
```

Use `known_for` in a person result to separate two people with the same name. Read `./people-and-credits.md`.

### Type-ahead search box

```js
// Debounce, cancel the stale request, and query only page 1.
let controller;
async function suggest(text) {
  const q = text.trim();
  if (q.length < 2) return [];        // do not query on one character
  controller?.abort();                 // cancel the stale request
  controller = new AbortController();
  const url = new URL("https://api.themoviedb.org/3/search/multi");
  url.searchParams.set("query", q);
  url.searchParams.set("include_adult", "false");
  const res = await fetch(url, { signal: controller.signal,
    headers: { Authorization: `Bearer ${token}`, accept: "application/json" } });
  return (await res.json()).results.slice(0, 8);
}
// Call suggest() from a 250 ms debounce, never from every keystroke.
// Cache the response per query string. Users retype the same prefixes often.
```

## 10. Best practices and anti-patterns

| Do this | Don't do this |
| :--- | :--- |
| Use discover for genre, rating, date range or sort order | Do not append filter words to the search `query` string |
| Use find when you hold an IMDb or TVDB ID | Do not text-search a title that you already hold an ID for |
| Let the HTTP client encode `query` | Do not build the URL with string concatenation |
| Re-rank the first page and confirm with the user | Do not assume `results[0]` is correct |
| Fetch the details endpoint for the full record | Do not render `runtime` or `genres` from a search result – they are absent |
| Send `primary_release_year` or `first_air_date_year` when you know the year | Do not send `year` and `primary_release_year` together |
| Combine the second step with `append_to_response` | Do not fire five separate sub-requests per item |
| Debounce and cancel type-ahead requests | Do not send a request on every keystroke |
| Cap the page loop at 500 | Do not trust `total_pages` above 500 |
| Store the TMDB `id` in your database | Do not store the title and search for it again later |
| Use the daily ID exports for bulk matching | Do not page through search to mirror the catalogue |

## 11. Common pitfalls

1. **`query` is required.** An empty or whitespace query returns a 400 error. Guard the input.
2. **Search has no sort parameter.** If you need "highest rated" or "newest", you need discover.
3. **Multi search field names differ per type.** Read `title` for a movie and `name` for a TV show or a person. Always branch on `media_type`.
4. **Multi search has no year filter.** Switch to `search/movie` or `search/tv` when the user gives a year.
5. **`region` on search is a presentation filter.** It changes which release date TMDB shows. It does not remove movies from the result set.
6. **`language` does not restrict matching.** A German query can return an English title, and the reverse.
7. **Page 501 fails.** TMDB status code 22 reports the cap.
8. **Find returns 200 with empty buckets** for an unknown ID. Check every bucket before you report a match.
9. **`search/company` and `search/keyword` accept only `query` and `page`.** Do not send `language` or `include_adult` and expect an effect.
10. **`include_adult=false` also hides adult performers** in person and multi search.
11. **A TV show and a movie can share a title.** Use `search/multi` and show the `media_type` badge, or ask the user which one they mean.

## 12. Error codes that hit search and find

| HTTP | TMDB code | Meaning | Fix |
| :--- | :--- | :--- | :--- |
| 400 | 22 | Invalid page. Pages start at 1 and max at 500. | Cap the loop at 500 |
| 401 | 7 | Invalid API key | Check the bearer token – see `./authentication.md` |
| 404 | 34 | The resource could not be found | Check the path and the ID |
| 429 | – | Too many requests | Back off, then retry |

## 13. Related skill files

| File | Why you open it |
| :--- | :--- |
| `./discover.md` | Every attribute filter and sort order. Read it before you extend a search query. |
| `./getting-started.md`, `./authentication.md` | Base URL, error format, rate limits, bearer token compared with `api_key`. |
| `./append-to-response.md` | Merge the sub-requests of step two into one call. |
| `./movies.md`, `./tv-series.md`, `./tv-seasons-and-episodes.md`, `./people-and-credits.md` | The detail endpoints that step two calls. |
| `./entities.md` | Collection, company, keyword and network details, plus the `external_ids` endpoints – the reverse of find. |
| `./images-and-configuration.md` | Build a full image URL from `poster_path` or `profile_path`. |
| `./localization.md` | `language`, `region` and the translation fallback. |
| `./trending-and-popular.md` | Ranked lists that need no query. |
| `./watch-providers.md` | Provider filters. They belong to discover, not to search. |
| `./changes-and-exports.md` | Daily ID exports for bulk matching. |
| `./lists.md`, `./user-account-and-ratings.md` | Store the IDs that search returns. |
