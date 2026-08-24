# TMDB: Collections, Companies, Networks, Keywords, Genres and Certifications
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Core concepts

TMDB has two kinds of object. Primary objects are movies, TV series and people. Supporting entities are collections, companies, networks, keywords, genres, certifications and reviews.

Supporting entities do three jobs:

1. **They supply Discover filter values.** `with_genres`, `with_keywords`, `with_companies`, `with_networks` and `certification` take IDs or codes, never names.
2. **They supply navigation targets.** A movie page links to its franchise, its studio and its keyword tags.
3. **They supply display labels.** Search and Discover return `genre_ids`, not genre names. You map the IDs yourself.

Two rules apply to all of them. **A name is not an ID** – resolve the name first, with the [ID-lookup pattern](#the-id-lookup-pattern-name--id). **Cache the small lists** – genres and certifications change a few times per year.

## Setup for the examples

The examples send a v4 read access token in the `Authorization` header, from the shell variable `TMDB_TOKEN`. Read [./authentication.md](./authentication.md) for the `api_key` alternative.

```python
import os, requests

TMDB = "https://api.themoviedb.org/3"
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
                        "accept": "application/json"})

def get(path, **params):
    r = session.get(f"{TMDB}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
```

Every Python example below uses this `get()` helper.

## Endpoint quick reference

| Endpoint | Purpose | Query parameters |
| --- | --- | --- |
| `GET /3/collection/{collection_id}` | Details plus the `parts` film list | `language` (default `en-US`) |
| `GET /3/collection/{collection_id}/images` | Posters and backdrops | `language`, `include_image_language` |
| `GET /3/collection/{collection_id}/translations` | Translated name and overview | none |
| `GET /3/company/{company_id}` | Company details | none |
| `GET /3/company/{company_id}/images` | Company logos | none |
| `GET /3/company/{company_id}/alternative_names` | Other trade names | none |
| `GET /3/network/{network_id}` | Network details | none |
| `GET /3/network/{network_id}/images` and `/alternative_names` | Network logos and names | none |
| `GET /3/keyword/{keyword_id}` | Keyword `id` and `name` | none |
| `GET /3/keyword/{keyword_id}/movies` | Deprecated. Use Discover | `language`, `page`, `include_adult` |
| `GET /3/genre/movie/list` | Official movie genres | `language` (default `en`) |
| `GET /3/genre/tv/list` | Official TV genres | `language` (default `en`) |
| `GET /3/certification/movie/list` | Movie ratings per country | none |
| `GET /3/certification/tv/list` | TV ratings per country | none |
| `GET /3/review/{review_id}` | One review | none |

## Collections

A collection is a movie franchise, for example the Star Wars films. Collections apply to movies only. TV series have no collections.

### Find a collection ID

Movie details return `belongs_to_collection`. The value is `null` for a standalone film. You can also call `/3/search/collection?query=...`, described in [./search-and-find.md](./search-and-find.md).

```python
movie = get("/movie/11")                      # Star Wars (1977)
stub = movie.get("belongs_to_collection")
# {"id": 10, "name": "Star Wars Collection", "poster_path": ..., "backdrop_path": ...}
if stub:
    collection = get(f"/collection/{stub['id']}", language="en-US")
```

### Details and the parts array

The stub gives a name and two image paths, but no film list. Call the details endpoint for that. The response has `id`, `name`, `original_name`, `original_language`, `overview`, `poster_path`, `backdrop_path` and `parts`. Each item in `parts` is a movie summary with `id`, `overview`, `poster_path`, `backdrop_path`, `media_type`, `genre_ids`, `popularity`, `release_date`, `adult`, `video`, `vote_average` and `vote_count`.

```python
def franchise_timeline(collection_id):
    parts = get(f"/collection/{collection_id}", language="en-US")["parts"]
    parts.sort(key=lambda p: p.get("release_date") or "9999-99-99")
    for p in parts:
        print(p.get("release_date") or "unreleased", p.get("title") or p.get("name"))

franchise_timeline(10)   # prints the Star Wars films in release order
```

- **The title field varies.** The documented collection schema uses `name` and `original_name`. Movie objects elsewhere use `title` and `original_title`. Read both keys with a fallback.
- **The API does not sort `parts`.** Sort by `release_date` yourself.
- **Announced films appear.** They carry an empty `release_date` and a `vote_count` of 0. Filter them out of a "watch in order" list.
- **Discover has no `with_collections` parameter.** The `parts` array is the only way to list a franchise.

### Images and translations

```bash
curl -s "https://api.themoviedb.org/3/collection/10/images?include_image_language=en,null" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

The response holds `backdrops` and `posters`. Each image has `file_path`, `width`, `height`, `aspect_ratio`, `iso_639_1`, `vote_average` and `vote_count`. `language` filters the result, and `include_image_language` adds more languages. Use the literal string `null` for images without text. Build the full URL from the configuration base URL – read [./images-and-configuration.md](./images-and-configuration.md).

```python
tr = get("/collection/10/translations")       # no parameters, returns every language
for t in tr["translations"]:
    if t["iso_639_1"] == "de":
        print(t["data"]["title"], "|", t["data"]["overview"][:60])
```

Each entry has `iso_3166_1`, `iso_639_1`, `name`, `english_name` and a `data` object with `title`, `overview` and `homepage`. Many `data` fields are empty strings. Treat an empty string as missing. Read [./localization.md](./localization.md).

## Companies

A company is a production company or a distributor, for example Lucasfilm Ltd. Movies list `production_companies`, and TV series list them too, so a company filter works for both media types.

```json
{ "id": 1, "name": "Lucasfilm Ltd.", "description": "",
  "headquarters": "San Francisco, California", "homepage": "https://www.lucasfilm.com",
  "logo_path": "/o86DbpburjxrqAzEDhXZcyE8pDb.png", "origin_country": "US",
  "parent_company": null }
```

`description` is empty for most companies. `parent_company` is `null`, or an object with `id`, `name` and `logo_path`.

### Walk the parent_company chain

```python
def company_chain(company_id, max_depth=10):
    """Return the ownership chain from a company up to its top parent."""
    chain, seen, current = [], set(), company_id
    while current and current not in seen and len(chain) < max_depth:
        seen.add(current)
        company = get(f"/company/{current}")
        chain.append(company)
        parent = company.get("parent_company")
        current = parent["id"] if parent else None
    return chain
```

Always guard the loop with a `seen` set and a depth limit. The data is user-contributed and a cycle is possible. The chain goes up only. No endpoint lists the children of a parent. Collect subsidiary IDs from search or from the daily ID export – read [./changes-and-exports.md](./changes-and-exports.md).

### Logos and alternative names

Each logo in `/3/company/{id}/images` has `file_path`, `file_type`, `width`, `height`, `aspect_ratio`, `id`, `vote_average` and `vote_count`.

**Gotcha – SVG logos.** `file_path` always ends with `.png`, but `file_type` can be `.svg`. Request the `original` size to get the true SVG. Request a width size such as `w300` to get a rasterized PNG. The `width` and `height` fields describe the uploaded asset only. Do not treat them as a maximum for an SVG.

```python
base = get("/configuration")["images"]["secure_base_url"]
best = max(get("/company/1/images")["logos"], key=lambda l: l["vote_average"])
svg_url = f"{base}original{best['file_path']}"    # SVG when file_type is .svg
png_url = f"{base}w300{best['file_path']}"        # always a PNG
```

`/3/company/{id}/alternative_names` returns `{"id": 1, "results": [{"name": "Lucasfilm", "type": ""}, ...]}`. The `type` field is almost always empty. Use the names to match a studio name that a user typed.

### Filter Discover by company

```bash
# Movies from Lucasfilm (1) OR Pixar (3)
curl -s "https://api.themoviedb.org/3/discover/movie?with_companies=1%7C3&sort_by=primary_release_date.desc" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Use `|` (encoded `%7C`) for OR. Use `,` for AND, which forces a film to list every company. Use `without_companies` to exclude.

**Gotcha – a parent ID does not match its children.** `with_companies=2` (Walt Disney Pictures) returns no Marvel Studios film. TMDB matches only the companies credited on the film. Join the whole family with `|`.

```python
ids = [c["id"] for c in company_chain(420)]     # 420 = Marvel Studios
results = get("/discover/movie", with_companies="|".join(map(str, ids)))
```

Read [./discover.md](./discover.md) for the full filter list.

## Networks

A network is a TV broadcaster or a streaming service, for example HBO (49) or Netflix (213). **Networks apply to TV only. Companies apply to movies and to TV.** Never send a network ID to a movie endpoint.

```json
{ "id": 49, "name": "HBO", "headquarters": "New York City, New York",
  "homepage": "https://www.hbo.com", "logo_path": "/tuomPhY2UtuPTqqFnKMVHvSb724.png",
  "origin_country": "US" }
```

A network has no `description` and no `parent_company`. `/3/network/{id}/images` and `/3/network/{id}/alternative_names` behave exactly like the company versions, including the SVG rule.

### Find a network ID

**There is no `/search/network` endpoint.** Use one of three routes. Read the `networks` array of a known series from `/3/tv/{series_id}`. Search a series first, then read the networks from its details. Or download the daily `tv_network_ids` export and search it offline.

```python
hit = get("/search/tv", query="The Sopranos")["results"][0]
for n in get(f"/tv/{hit['id']}")["networks"]:
    print(n["id"], n["name"], n["origin_country"])   # a series can have several networks
```

### Filter Discover by network

```bash
curl -s "https://api.themoviedb.org/3/discover/tv?with_networks=213&sort_by=popularity.desc" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Pass one network ID for a reliable result. A pipe-separated OR list works in practice, but check the result count before you depend on it.

**Do not confuse a network with a watch provider.** `with_networks=213` finds series that Netflix produced or first aired. It does not find every series that streams on Netflix in your country. Use `with_watch_providers` and `watch_region` for that – read [./watch-providers.md](./watch-providers.md).

## Keywords

A keyword is a free-text tag on a movie or a series, for example `hero` (1701). Keywords describe a subject, a setting or a trope. They are the strongest tool for a "find titles like this" feature.

`GET /3/keyword/{keyword_id}` returns two fields only: `{"id":1701,"name":"hero"}`. There is no description and no image.

`GET /3/keyword/{keyword_id}/movies` is **deprecated**. It pages through movies, but it offers no sort and no filter.

```bash
# Do NOT do this (deprecated, no sort, no filter):
curl -s "https://api.themoviedb.org/3/keyword/1701/movies?page=1" -H "..."

# Do this instead:
curl -s "https://api.themoviedb.org/3/discover/movie?with_keywords=1701&sort_by=vote_average.desc&vote_count.gte=200" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

### Find a keyword ID

`/3/search/keyword?query=...` returns `{page, results: [{id, name}], total_pages, total_results}`. Note the shape difference on the title endpoints: `/movie/{id}/keywords` returns a `keywords` array, and `/tv/{id}/keywords` returns a `results` array.

```python
def keyword_ids(term):
    return [(k["id"], k["name"]) for k in get("/search/keyword", query=term)["results"]]

print(keyword_ids("dystopia"))
# [(4458, 'dystopia'), (285157, 'dystopian future'), ...]

kw = get("/movie/603/keywords")["keywords"]        # The Matrix
similar = get("/discover/movie", sort_by="popularity.desc",
              with_keywords="|".join(str(k["id"]) for k in kw[:5]))
```

| Parameter | Effect |
| --- | --- |
| `with_keywords=A,B` | The title must have keyword A **and** keyword B |
| `with_keywords=A\|B` | The title must have keyword A **or** keyword B |
| `without_keywords=A,B` | Exclude every title with A or B |

### Keywords are user-contributed and inconsistent

- **Near-duplicates are normal.** `dystopia`, `dystopian future` and `post-apocalyptic future` are separate IDs. Resolve a term to several IDs and join them with `|`.
- **Coverage is uneven.** A popular recent film carries 20 or more keywords. An obscure 1950s film often carries none.
- **An absent keyword proves nothing.** Never treat a missing keyword as evidence that a theme is absent.
- **Spelling and case vary.** Match the search results. Do not guess the string.
- **Keywords are not genres.** Build a navigation menu from genres, never from keywords.

## Genres

Genres are a small, official, curated list. TMDB controls them, so the IDs are stable. Both endpoints return `{"genres": [{"id": 28, "name": "Action"}, ...]}`. The `language` parameter translates the **names**, never the IDs. Its default is `en`, not `en-US`.

```bash
curl -s "https://api.themoviedb.org/3/genre/movie/list?language=en" -H "Authorization: Bearer $TMDB_TOKEN"
curl -s "https://api.themoviedb.org/3/genre/tv/list?language=de"    -H "Authorization: Bearer $TMDB_TOKEN"
```

### The movie set and the TV set overlap but differ

| Shared (same ID in both) | Movie only | TV only |
| --- | --- | --- |
| 16 Animation, 35 Comedy, 80 Crime, 99 Documentary, 18 Drama, 10751 Family, 9648 Mystery, 37 Western | 28 Action, 12 Adventure, 14 Fantasy, 36 History, 27 Horror, 10402 Music, 10749 Romance, 878 Science Fiction, 10770 TV Movie, 53 Thriller, 10752 War | 10759 Action & Adventure, 10762 Kids, 10763 News, 10764 Reality, 10765 Sci-Fi & Fantasy, 10766 Soap, 10767 Talk, 10768 War & Politics |

**Gotcha – do not mix the sets.** TV merges Action with Adventure (10759), and Science Fiction with Fantasy (10765). `with_genres=28` on `/discover/tv` matches nothing useful. `with_genres=10759` on `/discover/movie` matches nothing useful. Load the list for the correct media type.

### Map genre_ids to names

Search, Discover, trending and collection `parts` all return `genre_ids`. Details endpoints return a `genres` array of objects instead. Build one cached map and use it everywhere.

```python
import time
_cache = {}     # (media_type, language) -> (fetched_at, {id: name})

def genre_map(media_type="movie", language="en", ttl=86400):
    key, hit = (media_type, language), _cache.get((media_type, language))
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    mapping = {g["id"]: g["name"] for g in get(f"/genre/{media_type}/list", language=language)["genres"]}
    _cache[key] = (time.time(), mapping)
    return mapping

names = genre_map("movie")
for m in get("/discover/movie", sort_by="popularity.desc")["results"][:5]:
    print(m["title"], "-", ", ".join(names.get(i, "Unknown") for i in m["genre_ids"]))
```

```javascript
// Same idea in the browser: fetch once, reuse the promise for the whole session.
let genrePromise;
const genreMap = (mediaType = "movie", language = "en") =>
  (genrePromise ??= fetch(`https://api.themoviedb.org/3/genre/${mediaType}/list?language=${language}`,
    { headers: { Authorization: `Bearer ${TMDB_TOKEN}`, accept: "application/json" } })
    .then((r) => r.json())
    .then((d) => new Map(d.genres.map((g) => [g.id, g.name]))));
```

**Do this:** fetch each list once per day per language and cache it. Always use a default such as `names.get(id, "Unknown")`, because TMDB can add a genre before you refresh. **Do not do this:** call `/genre/movie/list` inside a result loop, and do not hard-code English names for a user who reads another language.

## Certifications

A certification is an age rating, for example `PG-13` in the US. TMDB keeps one list per country, and separate lists for movies and for TV. The response maps a country code to an array.

```bash
curl -s "https://api.themoviedb.org/3/certification/movie/list" -H "Authorization: Bearer $TMDB_TOKEN"
curl -s "https://api.themoviedb.org/3/certification/tv/list"    -H "Authorization: Bearer $TMDB_TOKEN"
```

```json
{ "certifications": {
    "US": [
      { "certification": "NR",    "meaning": "No rating information.", "order": 0 },
      { "certification": "PG-13", "meaning": "Some material may be inappropriate...", "order": 3 },
      { "certification": "R",     "meaning": "Under 17 requires an accompanying parent...", "order": 4 }
    ] } }
```

| Field | Use |
| --- | --- |
| `certification` | The exact string to send to Discover |
| `meaning` | The human explanation. Show it in a tooltip |
| `order` | The sort key, from the most permissive to the most restrictive |

The movie list covers 45 countries and the TV list covers 40. US movie ratings run `NR, G, PG, PG-13, R, NC-17` in `order` 0 to 5. US TV ratings run `NR, TV-Y, TV-Y7, TV-G, TV-PG, TV-14, TV-MA` in `order` 0 to 6.

```python
def rating_options(media_type, country):
    data = get(f"/certification/{media_type}/list")
    return sorted(data["certifications"].get(country, []), key=lambda c: c["order"])

print([c["certification"] for c in rating_options("movie", "US")])
```

- **The array is not sorted.** Sort by `order` before you build a dropdown or a slider.
- **Not every key is an ISO country code.** The movie list holds `CA-QC` (Quebec) next to `CA`.
- **The codes differ per country.** Germany uses `0, 6, 12, 16, 18`. Sweden uses `Btl, 7, 11, 15`. France uses `TP, 12, 16, 18`. Never map one country's code onto another. Re-fetch the list when the user changes country.

### Pair certification with certification_country in Discover

`certification` **only works with** `certification_country`. Send both or send neither.

```bash
# Family films rated G or PG in the US.
curl -s "https://api.themoviedb.org/3/discover/movie?certification_country=US&certification.lte=PG&sort_by=popularity.desc" \
  -H "Authorization: Bearer $TMDB_TOKEN"

# Exactly R-rated US films.
curl -s "https://api.themoviedb.org/3/discover/movie?certification_country=US&certification=R" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

| Parameter | Effect |
| --- | --- |
| `certification_country` | Required with any other certification parameter |
| `certification` | Exact match |
| `certification.gte` | This rating or a more restrictive one |
| `certification.lte` | This rating or a more permissive one |

The `.gte` and `.lte` comparisons follow the `order` field of that country's list.

**Gotcha – certification filters work on `/discover/movie` only.** `/discover/tv` has no certification parameter. Read the ratings from `/3/tv/{series_id}/content_ratings` and filter in your own code – read [./tv-series.md](./tv-series.md).

**Gotcha – the filter drops unrated titles.** A film with no US rating disappears from a `certification_country=US` query, even a popular foreign film. Warn the user that the filter narrows the catalogue.

## Reviews

A review is a user-written text review of a movie or a series.

```json
{ "id": "640b2aeecaaca20079decdcc", "author": "Ricardo Oliveira",
  "author_details": { "name": "Ricardo Oliveira", "username": "RSOliveira",
                      "avatar_path": "/23Cl7rhsknc7IIAcZZAGKzovjTu.jpg", "rating": 9.0 },
  "content": "\"The Last of Us\" is a post-apocalyptic TV series ...",
  "created_at": "2023-03-10T13:04:46.674Z", "updated_at": "2023-03-10T13:04:46.734Z",
  "iso_639_1": "en", "media_id": 100088, "media_title": "The Last of Us",
  "media_type": "tv", "url": "https://www.themoviedb.org/review/640b2aeecaaca20079decdcc" }
```

### Where review IDs come from

**A review ID is a 24-character hex string, not an integer.** There is no review search and no review list endpoint. IDs arrive from `GET /3/movie/{movie_id}/reviews`, from `GET /3/tv/{series_id}/reviews`, or from `append_to_response=reviews` on a details call.

```python
detail = get("/tv/100088", append_to_response="reviews")
for r in detail["reviews"]["results"]:
    stars = r["author_details"].get("rating")
    print(r["id"], r["author"], stars if stars is not None else "no rating")
```

The list endpoints already embed the full review object. Call `/3/review/{id}` only when a user opens a deep link and holds the ID alone. That endpoint adds `media_id`, `media_title` and `media_type`, which the embedded version lacks. Use them to build a back-link from a review to its title.

### The author_details object

| Field | Notes |
| --- | --- |
| `name` | Often an empty string. Fall back to `username` |
| `username` | Always present |
| `avatar_path` | Nullable. See the gotcha below |
| `rating` | A number from 0.5 to 10.0, **or `null`**. A review needs no score |

**Gotcha – the Gravatar avatar path.** `avatar_path` is normally a TMDB path such as `/23Cl7rhsknc7IIAcZZAGKzovjTu.jpg`. It is sometimes a full Gravatar URL with an extra leading slash, such as `/https://secure.gravatar.com/avatar/abc123`. Strip that leading slash.

```python
def avatar_url(path, base, size="w185"):
    if not path: return None
    return path[1:] if path.startswith("/http") else f"{base}{size}{path}"
```

`content` is plain text with Markdown-style markup and `\r\n` line breaks. Escape it before you render HTML, and truncate it in a list view. `iso_639_1` gives the review language. A `language` parameter does not apply to the review endpoints.

## The ID-lookup pattern (name → ID)

Users type names. Discover takes IDs. This table shows every route.

| Entity | Resolve a name | Other source | Discover parameter |
| --- | --- | --- | --- |
| Collection | `GET /3/search/collection?query=` | `movie.belongs_to_collection` | none. Use `/collection/{id}` |
| Company | `GET /3/search/company?query=` | `movie.production_companies` | `with_companies`, `without_companies` |
| Network | **no search endpoint** | `tv.networks`, daily ID export | `with_networks` (TV only) |
| Keyword | `GET /3/search/keyword?query=` | `movie/{id}/keywords`, `tv/{id}/keywords` | `with_keywords`, `without_keywords` |
| Genre | `GET /3/genre/{movie\|tv}/list` | `genres` on any details call | `with_genres`, `without_genres` |
| Certification | `GET /3/certification/{movie\|tv}/list` | `release_dates`, `content_ratings` | `certification` + `certification_country` |
| Person | `GET /3/search/person?query=` | credits | `with_cast`, `with_crew`, `with_people` |
| Review | **no search endpoint** | `movie/{id}/reviews`, `tv/{id}/reviews` | none |

```python
def resolve(kind, name, media_type="movie"):
    """Turn a name into a list of (id, label) candidates."""
    if kind == "genre":
        return [(g["id"], g["name"]) for g in get(f"/genre/{media_type}/list")["genres"]
                if name.lower() in g["name"].lower()]
    if kind == "network":                      # no network search endpoint
        out = []
        for s in get("/search/tv", query=name)["results"][:3]:
            out += [(n["id"], n["name"]) for n in get(f"/tv/{s['id']}")["networks"]
                    if name.lower() in n["name"].lower()]
        return sorted(set(out))
    endpoint = {"collection": "/search/collection", "company": "/search/company",
                "keyword": "/search/keyword"}[kind]
    return [(r["id"], r["name"]) for r in get(endpoint, query=name)["results"]]

print(resolve("keyword", "time travel"), resolve("company", "A24"))
```

**Confirm an ambiguous match with the user.** A search for `Universal` returns many companies, and `dystopia` returns many keywords. Show the top matches, or join every plausible ID with `|`. **Cache the resolved IDs** in your own database. These IDs never change.

## Best practices

- **Cache the two static lists.** Fetch the genre list and the certification list once per day.
- **Store IDs, not names.** Save `with_keywords=1701` in a saved filter, never `"hero"`.
- **Use `|` to widen a filter and `,` to narrow it.** Start wide, then add AND terms.
- **Use `append_to_response`** to fetch keywords, images and reviews in the details call – read [./append-to-response.md](./append-to-response.md).
- **Sort what the API leaves unsorted:** collection `parts` by `release_date`, certifications by `order`.
- **Guard every nullable field:** `belongs_to_collection`, `parent_company`, `avatar_path`, `author_details.rating`.
- **Match the entity to the media type.** Networks and TV genre IDs belong to TV. Certification filters belong to movies.

## Anti-patterns

| Do not do this | Do this |
| --- | --- |
| `?with_genres=Action` | Resolve the name to `28`, then send `?with_genres=28` |
| Call `/genre/movie/list` in every request | Cache the map for 24 hours |
| Use movie genre IDs on `/discover/tv` | Load `/genre/tv/list` for TV |
| Use `/keyword/{id}/movies` | Use `/discover/movie?with_keywords={id}` |
| Send one keyword ID for a broad theme | Join the near-duplicate IDs with `\|` |
| Send `certification=R` alone | Send `certification_country=US&certification=R` |
| Use `with_networks` to find streamable series | Use `with_watch_providers` and `watch_region` |
| Expect a parent company ID to include subsidiaries | Join the family IDs with `\|` |
| Show collection `parts` in the returned order | Sort them by `release_date` |

## Common pitfalls

1. **A collection stub is not a collection.** `belongs_to_collection` has no `parts`. Call `/collection/{id}`.
2. **Four lookups have no endpoint:** network search, review search, "list all keywords" and "list all companies". Use search, a details call, or the daily ID exports.
3. **The `language` parameter changes labels, never IDs.** A German genre list still returns `28` for Action.
4. **`CA-QC` breaks a strict ISO 3166-1 parser** in the movie certification list.
5. **A certification filter silently removes unrated titles.**
6. **`author_details.rating` can be `null`.** Do not render `null` as `0`.
7. **A review ID is a hex string.** Do not cast it to an integer.
8. **Empty strings mean missing data** in `company.description`, in translation `data` fields, and in the alternative-name `type` field.

## Related skill files

| File | Why you need it |
| --- | --- |
| [./discover.md](./discover.md) | The consumer of every ID on this page. Full filter list and AND/OR syntax |
| [./search-and-find.md](./search-and-find.md) | `/search/collection`, `/search/company`, `/search/keyword` |
| [./movies.md](./movies.md) | `belongs_to_collection`, `production_companies`, `keywords`, `release_dates`, `reviews` |
| [./tv-series.md](./tv-series.md), [./tv-seasons-and-episodes.md](./tv-seasons-and-episodes.md) | `networks`, `content_ratings`, `keywords`, `reviews` |
| [./images-and-configuration.md](./images-and-configuration.md) | Base URL and size keys for posters, backdrops and logos |
| [./localization.md](./localization.md), [./append-to-response.md](./append-to-response.md) | Translation fallbacks. Fetch keywords, images and reviews in one call |
| [./watch-providers.md](./watch-providers.md) | Streaming services, which differ from networks |
| [./changes-and-exports.md](./changes-and-exports.md) | Daily ID exports for collections, companies, networks and keywords |
| [./getting-started.md](./getting-started.md), [./authentication.md](./authentication.md) | Base URL, request shape, rate limits, tokens |
| [./trending-and-popular.md](./trending-and-popular.md), [./people-and-credits.md](./people-and-credits.md) | Ranked lists return raw `genre_ids`. People power the `with_cast` filters |
| [./lists.md](./lists.md), [./user-account-and-ratings.md](./user-account-and-ratings.md) | User lists differ from collections. User ratings differ from review scores |
