# TMDB: People and Credits
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Core concepts

A **person** is one human record in TMDB. The person has a stable integer `person_id` (Tom Hanks is `31`). Use this id in every person endpoint.

A **credit** is the link between one person and one title. The credit has its own stable id, the `credit_id`. The `credit_id` is a 24-character hexadecimal string, not an integer. Keep it as a string.

TMDB splits every credit into two groups:

- **cast** – the person appears on screen. The credit carries a `character`.
- **crew** – the person works behind the camera. The credit carries a `department` and a `job`.

You can read credits from two directions:

- **From the person** – `/person/{id}/movie_credits`, `/tv_credits` and `/combined_credits` give the filmography of one person.
- **From the title** – `/movie/{id}/credits` and `/tv/{id}/aggregate_credits` give the full unit of one title. See `./movies.md` and `./tv-series.md`.

The `/credit/{credit_id}` endpoint is the third direction. It expands one credit into the media, the person and the exact scope of the work.

## Quick reference – every person endpoint

| Endpoint | Purpose | Query parameters |
| :-- | :-- | :-- |
| `GET /3/person/{person_id}` | Top level person details | `language`, `append_to_response` |
| `GET /3/person/{person_id}/movie_credits` | Movie cast and crew credits | `language` |
| `GET /3/person/{person_id}/tv_credits` | TV cast and crew credits | `language` |
| `GET /3/person/{person_id}/combined_credits` | Movie and TV credits in one list | `language` |
| `GET /3/person/{person_id}/external_ids` | IMDb, Wikidata and social ids | – |
| `GET /3/person/{person_id}/images` | Profile images of the person | – |
| `GET /3/person/{person_id}/tagged_images` | Media images that show the person | `page` |
| `GET /3/person/{person_id}/translations` | Translated name and biography | – |
| `GET /3/person/{person_id}/changes` | Recent field changes | `start_date`, `end_date`, `page` |
| `GET /3/person/latest` | Newest created person record | – |
| `GET /3/person/popular` | People ordered by popularity | `language`, `page` |
| `GET /3/credit/{credit_id}` | One credit, expanded | `language` |

To find a person by name, use `/3/search/person`. To find a person by an IMDb id, use `/3/find/{external_id}`. Both live in `./search-and-find.md`.

## Setup

Send the v4 read access token in an `Authorization: Bearer` header. See `./authentication.md` for the token types.

```bash
export TMDB_TOKEN="eyJhbGciOiJIUzI1NiJ9..."

curl -s "https://api.themoviedb.org/3/person/31?language=en-US" \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H "accept: application/json"
```

Reuse one HTTP session in Python. The session keeps the connection alive and sets the header once. Every later example uses this `get()` helper.

```python
import os
import requests

BASE = "https://api.themoviedb.org/3"
S = requests.Session()
S.headers.update({
    "Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
    "accept": "application/json",
})

def get(path, **params):
    r = S.get(f"{BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()
```

## The person details response

| Field | Type | Notes |
| :-- | :-- | :-- |
| `id` | integer | The stable TMDB person id. |
| `name` | string | The primary display name. It changes with `language` if a translation exists. |
| `also_known_as` | array of strings | Alternate names and transliterations, for example `"Том Хэнкс"`. |
| `biography` | string | Free text. It is empty when no translation exists for the requested language. |
| `birthday` | string or null | `YYYY-MM-DD`. |
| `deathday` | string or null | `YYYY-MM-DD`. A `null` value means the person is alive **or** the data is missing. |
| `gender` | integer | See the code table below. |
| `known_for_department` | string or null | For example `"Acting"`, `"Directing"`, `"Writing"`. |
| `place_of_birth` | string or null | Free text, for example `"Concord, California, USA"`. |
| `profile_path` | string or null | A path fragment, not a URL. See "Profile images". |
| `imdb_id` | string or null | For example `"nm0000158"`. Prefix it with `https://www.imdb.com/name/`. |
| `homepage` | string or null | The official site. |
| `popularity` | number | A TMDB score. It changes every day. |
| `adult` | boolean | Marks an adult-industry person. |

### Gender codes

| Value | Gender |
| :-- | :-- |
| 0 | Not set / not specified |
| 1 | Female |
| 2 | Male |
| 3 | Non-binary |

Never treat `0` as a real gender. Map it to "unknown" and hide the field in your UI: `GENDERS = {0: None, 1: "Female", 2: "Male", 3: "Non-binary"}`.

### Get the details and the extras in one request

The details endpoint supports `append_to_response`. Add up to 20 sub-endpoints from the person namespace. This saves round trips and rate limit budget. See `./append-to-response.md`.

```bash
curl -s "https://api.themoviedb.org/3/person/31?append_to_response=combined_credits,external_ids,images,translations" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

**Do this** – one request for the whole person page:

```python
p = get("/person/31", append_to_response="combined_credits,external_ids,images")
credits = p["combined_credits"]
imdb = p["external_ids"]["imdb_id"]
```

**Do not do this** – four separate calls (`/person/31`, then `/combined_credits`, then `/external_ids`, then `/images`) for the same page.

## The credits model

### Three endpoints, one shape

| Endpoint | Contains | Extra field |
| :-- | :-- | :-- |
| `/person/{id}/movie_credits` | Movies only | – |
| `/person/{id}/tv_credits` | TV series only | – |
| `/person/{id}/combined_credits` | Movies **and** TV series | `media_type` on every entry |

All three return the same top level shape: `{ "id": <person_id>, "cast": [...], "crew": [...] }`. None of the three is paginated. Each returns the complete list.

### Cast entries against crew entries

| Group | Media | Role fields | Other credit fields |
| :-- | :-- | :-- | :-- |
| `cast` | movie | `character` | `credit_id`, `order` |
| `cast` | tv | `character` | `credit_id`, `episode_count` |
| `crew` | movie | `department`, `job` | `credit_id` |
| `crew` | tv | `department`, `job` | `credit_id`, `episode_count` |

`order` is the billing position. `order: 0` is the top-billed actor. Movie cast entries have `order`. TV cast entries have `episode_count` instead.

Each entry also embeds the title itself. The field names differ by media type:

| Concept | Movie entry | TV entry |
| :-- | :-- | :-- |
| Title | `title`, `original_title` | `name`, `original_name` |
| Date | `release_date` | `first_air_date` |
| Country | – | `origin_country` |
| Video flag | `video` | – |

Both types carry `id`, `overview`, `poster_path`, `backdrop_path`, `genre_ids`, `original_language`, `popularity`, `vote_average` and `vote_count`.

### The media_type field

Only `combined_credits` adds `media_type`. The value is `"movie"` or `"tv"`. Read it first, then read the correct title and date field.

```python
def title_of(credit):
    if credit.get("media_type") == "tv":
        return credit["name"], credit.get("first_air_date") or ""
    return credit["title"], credit.get("release_date") or ""
```

**Do not do this** – `credit["title"]` raises `KeyError` on every TV entry:

```python
rows = [c["title"] for c in combined["cast"]]   # breaks on TV credits
```

### The credit_id

Every cast and crew entry carries a `credit_id`, for example `"52fe420ec3a36847f800074f"`. Use it as:

- a stable key for one role, and not the person id or the media id;
- the input to `/3/credit/{credit_id}`.

One person and one title can share several `credit_id` values. An actor who also produced the film has one cast credit and one crew credit. Deduplicate on `(media_type, id)` only when you want one row per title. Deduplicate on `credit_id` when you want one row per role.

## Credit details – `/3/credit/{credit_id}`

The list form gives you the role and the title summary. The credit details endpoint gives you four things that the list form does not:

1. **`media`** – the full title object, plus the `character` for a cast credit.
2. **`person`** – a compact person object, so you can go backwards from a credit to the person.
3. **`credit_type`, `department` and `job`** – the exact classification, even for a cast credit (`credit_type: "cast"`, `department: "Acting"`, `job: "Actor"`).
4. **The TV scope** – `media.seasons[]` and `media.episodes[]` tell you *where in the series* the person worked.

| Field | Type | Notes |
| :-- | :-- | :-- |
| `id` | string | The `credit_id` itself. |
| `credit_type` | string | `"cast"` or `"crew"`. |
| `department` | string | For example `"Acting"`, `"Directing"`. |
| `job` | string | For example `"Actor"`, `"Director"`. |
| `media_type` | string | `"movie"` or `"tv"`. |
| `media` | object | The movie or TV object. It also carries `character` for a cast credit. |
| `media.seasons` | array | TV only. Seasons that the credit covers (series regular). |
| `media.episodes` | array | TV only. Episodes that the credit covers (guest star, single episode crew). |
| `person` | object | `id`, `name`, `original_name`, `gender`, `known_for_department`, `profile_path`, `popularity`. |

A series-regular credit gives a filled `seasons` array and an empty `episodes` array. A guest credit gives a filled `episodes` array. Use this to separate "starred in season 1" from "appeared in one episode". See `./tv-seasons-and-episodes.md`.

```bash
curl -s "https://api.themoviedb.org/3/credit/6024a814c0ae36003d59cc3c" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

## Worked example 1 – a complete filmography sorted by release date

This example builds one flat, sorted filmography from `combined_credits`. It merges cast and crew, it normalises the movie and TV field names, and it puts undated projects at the end.

```python
def normalise(credit, kind):
    is_tv = credit.get("media_type") == "tv"
    if kind == "cast":
        role = credit.get("character") or "Uncredited role"
    else:
        role = credit.get("job") or credit.get("department") or "Crew"
    return {
        "credit_id": credit["credit_id"],
        "media_type": credit.get("media_type", "movie"),
        "media_id": credit["id"],
        "title": credit["name"] if is_tv else credit["title"],
        "date": (credit.get("first_air_date") if is_tv else credit.get("release_date")) or "",
        "kind": kind,
        "role": role,
        "order": credit.get("order"),
        "episode_count": credit.get("episode_count"),
        "poster_path": credit.get("poster_path"),
    }

def filmography(person_id, language="en-US", newest_first=True):
    data = get(f"/person/{person_id}/combined_credits", language=language)
    rows = [normalise(c, "cast") for c in data.get("cast", [])]
    rows += [normalise(c, "crew") for c in data.get("crew", [])]
    # An empty date must sort last, so give it a sentinel.
    rows.sort(key=lambda r: r["date"] or ("0000" if newest_first else "9999"),
              reverse=newest_first)
    return rows

for row in filmography(31)[:10]:
    year = row["date"][:4] or "TBA"
    tag = "TV" if row["media_type"] == "tv" else "  "
    print(f'{year}  {tag}  {row["title"]:<40} {row["role"]}')
```

Group the rows when you want one line per title and a merged role list:

```python
from collections import defaultdict

def grouped(person_id):
    buckets = defaultdict(list)
    for row in filmography(person_id):
        buckets[(row["media_type"], row["media_id"])].append(row)
    merged = [dict(rows[0], roles=sorted({r["role"] for r in rows})) for rows in buckets.values()]
    merged.sort(key=lambda r: r["date"] or "0000", reverse=True)
    return merged
```

The same normalisation in JavaScript:

```javascript
const res = await fetch(
  `https://api.themoviedb.org/3/person/${personId}/combined_credits?language=en-US`,
  { headers: { Authorization: `Bearer ${process.env.TMDB_TOKEN}`, accept: "application/json" } },
);
if (!res.ok) throw new Error(`TMDB ${res.status}`);
const { cast = [], crew = [] } = await res.json();

const rows = [...cast, ...crew].map((c) => {
  const isTv = c.media_type === "tv";
  return {
    creditId: c.credit_id,
    title: isTv ? c.name : c.title,
    date: (isTv ? c.first_air_date : c.release_date) || "",
    role: c.character ?? c.job ?? "Crew",
  };
});
rows.sort((a, b) => (b.date || "0000").localeCompare(a.date || "0000"));
```

## Worked example 2 – resolve a credit_id back to its media

Take a `credit_id` from any credits list, then expand it. The result tells you the title, the role and, for TV, the exact seasons or episodes.

```python
def resolve_credit(credit_id, language="en-US"):
    c = get(f"/credit/{credit_id}", language=language)
    media = c["media"]
    is_tv = c["media_type"] == "tv"

    out = {
        "credit_id": c["id"],
        "credit_type": c["credit_type"],          # "cast" or "crew"
        "department": c.get("department"),
        "job": c.get("job"),
        "person_id": c["person"]["id"],
        "person_name": c["person"]["name"],
        "media_type": c["media_type"],
        "media_id": media["id"],
        "title": media["name"] if is_tv else media["title"],
        "date": (media.get("first_air_date") if is_tv else media.get("release_date")) or "",
        "character": media.get("character"),
    }
    if is_tv:
        out["seasons"] = [s["season_number"] for s in media.get("seasons", [])]
        out["episodes"] = [
            (e.get("season_number"), e.get("episode_number")) for e in media.get("episodes", [])
        ]
        out["scope"] = "series regular" if out["seasons"] else "guest / episode credit"
    return out

info = resolve_credit("6024a814c0ae36003d59cc3c")
print(info["person_name"], "as", info["character"], "in", info["title"], info["scope"])
# Pedro Pascal as Joel Miller in The Last of Us series regular
```

Round-trip the two directions to prove the model:

```python
first = get("/person/1253360/tv_credits")["cast"][0]
full = resolve_credit(first["credit_id"])
assert full["media_id"] == first["id"] and full["person_id"] == 1253360
```

## Profile images

`profile_path` is a path fragment. Build the URL from the image base URL, a size and the path.

```python
profile_url = f"https://image.tmdb.org/t/p/w185{person['profile_path']}"
```

Read the base URL and the valid `profile_sizes` from `/3/configuration`, and cache the answer. Never hard-code the size list. See `./images-and-configuration.md`.

`/person/{id}/images` returns every profile image, not only the primary one:

```json
{ "id": 287, "profiles": [
  { "file_path": "/cckcYc2v0yh1tc9QjRelptcOBko.jpg", "aspect_ratio": 0.666,
    "width": 653, "height": 980, "iso_639_1": null, "vote_average": 5.288, "vote_count": 89 }
]}
```

The endpoint takes **no** `language` parameter. Profile photos carry no language, so `iso_639_1` is almost always `null`. TMDB returns the profiles in vote order, so `profiles[0]` is the community favourite.

## Tagged images

`/person/{id}/tagged_images` is different from `/images`. It returns **media artwork that shows the person** – posters, backdrops and stills from the films and shows in the filmography. Each result carries the image, an `image_type` (`"poster"`, `"backdrop"`, `"still"`) and the `media` object that the image belongs to.

```bash
curl -s "https://api.themoviedb.org/3/person/31/tagged_images?page=1" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```python
tagged = get("/person/31/tagged_images", page=1)
for item in tagged["results"]:
    media = item["media"]
    name = media.get("title") or media.get("name")
    print(item["image_type"], item["file_path"], "->", name, f'({item["media_type"]})')
```

This endpoint **is** paginated: it returns `page`, `total_pages` and `total_results`. Use tagged images for a gallery of the person at work. Use `/images` for a headshot.

## External IDs

`/person/{id}/external_ids` gives the social and reference ids. TMDB supports Facebook, IMDb, Instagram, TikTok, Twitter, Wikidata and YouTube for person records.

| Field | Link template |
| :-- | :-- |
| `imdb_id` | `https://www.imdb.com/name/{id}/` |
| `wikidata_id` | `https://www.wikidata.org/wiki/{id}` |
| `facebook_id` | `https://www.facebook.com/{id}` |
| `instagram_id` | `https://www.instagram.com/{id}` |
| `tiktok_id` | `https://www.tiktok.com/@{id}` |
| `twitter_id` | `https://twitter.com/{id}` |
| `youtube_id` | `https://www.youtube.com/{id}` |

The response also contains the legacy `freebase_mid`, `freebase_id` and `tvrage_id`. Do not use those. Every field can be `null`, so check before you build a link.

```python
TEMPLATES = {"imdb_id": "https://www.imdb.com/name/{}/",
             "instagram_id": "https://www.instagram.com/{}",
             "twitter_id": "https://twitter.com/{}",
             "wikidata_id": "https://www.wikidata.org/wiki/{}"}

ext = get("/person/31/external_ids")
links = {k: TEMPLATES[k].format(v) for k, v in ext.items() if v and k in TEMPLATES}
```

## Translations

`/person/{id}/translations` returns the name and the biography in every available language. Each entry has `iso_639_1`, `iso_3166_1`, `name`, `english_name` and a `data` object with `biography` and `name`.

Use it when the `language` parameter returns an empty biography and you want a fallback.

```python
def biography(person_id, wanted="en"):
    tr = get(f"/person/{person_id}/translations")
    by_lang = {t["iso_639_1"]: t["data"]["biography"] for t in tr["translations"]}
    return by_lang.get(wanted) or by_lang.get("en") or ""
```

See `./localization.md` for the language and region rules.

## Person changes

`/person/{id}/changes` lists the fields that changed. It returns the **last 24 hours** by default. Query up to **14 days** in one call with `start_date` and `end_date`.

```bash
curl -s "https://api.themoviedb.org/3/person/31/changes?start_date=2026-08-01&end_date=2026-08-14" \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

The response groups the changes by field key. Each item has an `id`, an `action` (`"added"`, `"updated"`, `"deleted"`), a `time` in UTC, the `iso_639_1` and `iso_3166_1` scope, and the new `value`.

```json
{ "changes": [
  { "key": "biography", "items": [
    { "id": "640469b113654500ba4e859a", "action": "added", "time": "2023-03-05 10:06:41 UTC",
      "iso_639_1": "ca", "iso_3166_1": "ES", "value": "..." }]}
]}
```

Do not poll this endpoint for every person in your database. Call the global `/3/person/changes` list first to learn *which* people changed, then call the per-person endpoint for those ids. See `./changes-and-exports.md`.

## Latest person and popular people

`/3/person/latest` returns the newest created person record. The record is almost empty: no biography, no images, `known_for_department` is `null`. Use it to learn the upper bound of the id space, and not as a source of content.

```bash
curl -s "https://api.themoviedb.org/3/person/latest" -H "Authorization: Bearer $TMDB_TOKEN"
```

`/3/person/popular` returns people ordered by the daily popularity score. It is paginated to 500 pages and 10,000 results. Each result carries a `known_for` array of up to three titles, and each of those titles carries its own `media_type`.

```python
page = get("/person/popular", language="en-US", page=1)
for p in page["results"][:5]:
    titles = [k.get("title") or k.get("name") for k in p.get("known_for", [])]
    print(f'{p["name"]:<25} {p["popularity"]:>8.1f}  {", ".join(titles)}')
```

`known_for` appears on the popular list and on person search results. It never appears on the person details response. See `./trending-and-popular.md` and `./search-and-find.md`.

## Best practices

- **Append instead of chaining.** Fetch `/person/{id}?append_to_response=combined_credits,external_ids,images` in one call.
- **Cache person records.** Biographies and filmographies change slowly. Cache for hours, and refresh with the changes feed.
- **Treat every optional field as null.** `deathday`, `place_of_birth`, `profile_path`, `imdb_id`, `known_for_department` and every social id can be `null`.
- **Store `credit_id` with your own rows.** It is the only stable key for one role.
- **Read `media_type` before any other field on a combined credit.**
- **Pick the endpoint that matches the question.** Use `movie_credits` for a film list. Use `combined_credits` only when you want both media types.
- **Get the image base URL from `/configuration`.** Cache it for the process lifetime.
- **Sort with the raw ISO date string.** `"1994-06-23"` sorts correctly as text, so you do not need to parse it.

## Anti-patterns

| Do not do this | Do this instead |
| :-- | :-- |
| Call `movie_credits` **and** `tv_credits` **and** `combined_credits`. | Call `combined_credits` alone, then filter on `media_type`. |
| Parse `credit_id` as an integer. | Keep it as a string. It is hexadecimal. |
| Use `person["popularity"]` as a quality score. | Use `vote_average` on the credited titles. |
| Assume `deathday: null` means the person is alive. | Show nothing when the field is missing. |
| Loop over person ids to build a full mirror. | Use the daily ID export files. See `./changes-and-exports.md`. |
| Show `gender: 0` as a gender. | Map `0` to "unknown" and hide it. |
| Concatenate `profile_path` on a hard-coded size. | Read `profile_sizes` from `/configuration`. |
| Call `/credit/{id}` for every row in a filmography. | Use the list data, and expand one credit on demand. |

## Common pitfalls

- **The title field name changes with the media type.** Movies use `title` and `release_date`. TV uses `name` and `first_air_date`. Only `combined_credits` mixes them.
- **Dates can be empty strings, not `null`.** Sort with a sentinel value, or the sort fails or puts unreleased work first.
- **The credit lists are not paginated and can be very large.** Tom Hanks returns more than 200 cast entries. Paginate in your own UI.
- **One title can appear more than once.** An actor-producer gets two entries with two different `credit_id` values.
- **TV cast entries have no `order`.** Use `episode_count` to rank TV work, and `order` to rank movie work.
- **`episode_count` counts episodes, not seasons.** Call `/credit/{credit_id}` to get the season and episode scope.
- **`/person/{id}/images` ignores `language`.** Do not send the parameter and do not expect `iso_639_1` to be set.
- **`tagged_images` shows media artwork, not headshots.** Many people have zero tagged images.
- **`biography` is empty when the language has no translation.** Fall back through `/translations`.
- **`also_known_as` mixes scripts and transliterations.** Normalise it before you index it.
- **The changes endpoint refuses ranges longer than 14 days.** Split a long backfill into 14-day windows.
- **`popularity` changes every day.** Do not use it as a stable sort key in your own database.

## Related skill files

| File | Why you need it |
| :-- | :-- |
| `./getting-started.md` | The base URL, the request format and the rate limits. |
| `./authentication.md` | The API key and the bearer token. |
| `./append-to-response.md` | The rules for the 20-item append list. |
| `./images-and-configuration.md` | The image base URL and the `profile_sizes` list. |
| `./localization.md` | The `language` parameter and the fallback behaviour. |
| `./search-and-find.md` | `/search/person` and `/find/{external_id}` to get a `person_id`. |
| `./movies.md` | `/movie/{id}/credits` – the credits from the title side. |
| `./tv-series.md` | `/tv/{id}/credits` and `/tv/{id}/aggregate_credits`. |
| `./tv-seasons-and-episodes.md` | The season and episode objects inside a TV credit. |
| `./trending-and-popular.md` | `/trending/person/{time_window}` next to `/person/popular`. |
| `./discover.md` | `with_cast` and `with_crew` filters that take a `person_id`. |
| `./changes-and-exports.md` | The global change feed and the daily person ID export. |
| `./entities.md` | The shared object shapes across the API. |
