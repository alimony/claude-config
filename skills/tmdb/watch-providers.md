# TMDB: Watch Providers
Based on TMDB API v3 documentation (developer.themoviedb.org).

Watch providers tell you where a title streams, rents or sells in each country. Use this skill to build a "Where to watch" panel, or to filter Discover by a streaming service.

## Core concepts

TMDB gets this data from a partnership with **JustWatch**. TMDB does not own it.

Five facts control every design decision:

1. **The data is per country.** One title has a different provider set in each region. There is no global answer.
2. **The API gives no deep links.** Each country block has one `link` to a TMDB watch page. That page holds the real deep links.
3. **Availability changes often.** Titles enter and leave services every week.
4. **A provider is an offer type, not only a brand.** The same brand can appear under `flatrate` and under `rent` in the same country.
5. **Attribution is mandatory.** Read the next section before you write any display code.

## Warning: JustWatch attribution is required

> **Warning:** TMDB revokes API access for applications that show this data without attribution. Add the attribution before you ship the feature, not after.

The TMDB documentation states the rule on all three per-title endpoints:

> "In order to use this data you must attribute the source of the data as **JustWatch**. If we find any usage not complying with these terms we will revoke access to the API."

Follow these display rules:

1. Write the credit as **JustWatch**, with that exact spelling.
2. Put the credit on every screen or component that shows provider data.
3. Send the user to the `link` value. TMDB states you can link to the given TMDB URL to support TMDB and to give the user the real deep links.
4. Do not present the data as your own availability database.
5. Do not scrape or rebuild deep links from the provider names.

```html
<!-- Do this: attribution sits next to the provider logos -->
<section class="where-to-watch">
  <h3>Where to watch</h3>
  <ul id="providers"></ul>
  <p class="attribution">
    Streaming data by <a href="https://www.justwatch.com/">JustWatch</a>.
    <a href="https://www.themoviedb.org/movie/550/watch?locale=US">See all options on TMDB</a>
  </p>
</section>
```

```html
<!-- Don't do this: logos with no source credit and no link out -->
<ul id="providers"></ul>
```

## Quick reference: endpoints

| Purpose | Method and path | Query parameters | Returns |
| :--- | :--- | :--- | :--- |
| Supported countries | `GET /3/watch/providers/regions` | `language` | `results[]` of `iso_3166_1`, `english_name`, `native_name` |
| All movie providers | `GET /3/watch/providers/movie` | `language`, `watch_region` | `results[]` of provider objects with `display_priorities` |
| All TV providers | `GET /3/watch/providers/tv` | `language`, `watch_region` | `results[]` of provider objects with `display_priorities` |
| Providers for a movie | `GET /3/movie/{movie_id}/watch/providers` | none | `id` plus `results` keyed by country |
| Providers for a TV series | `GET /3/tv/{series_id}/watch/providers` | none | `id` plus `results` keyed by country |
| Providers for a TV season | `GET /3/tv/{series_id}/season/{season_number}/watch/providers` | `language` | `id` plus `results` keyed by country |

There is no episode-level endpoint. Season level is the smallest unit.

All calls use the standard bearer token. See `./authentication.md`.

```bash
export TMDB_TOKEN="<your v4 read access token>"

curl --request GET \
  --url 'https://api.themoviedb.org/3/movie/550/watch/providers' \
  --header "Authorization: Bearer $TMDB_TOKEN" \
  --header 'accept: application/json'
```

## The per-title response shape

The response has two top-level keys: `id` (the TMDB id you asked for) and `results`.

`results` is an **object, not an array**. Each key is an ISO 3166-1 alpha-2 country code. Each value holds one `link` plus zero or more monetization buckets.

```json
{
  "id": 550,
  "results": {
    "US": {
      "link": "https://www.themoviedb.org/movie/550-fight-club/watch?locale=US",
      "flatrate": [
        { "logo_path": "/zxrVdFjIjLqkfnwyghnfywTn3Lh.jpg", "provider_id": 15,  "provider_name": "Hulu",           "display_priority": 6 },
        { "logo_path": "/xbhHHa1YgtpwhC8lb1NQ3ACVcLd.jpg", "provider_id": 531, "provider_name": "Paramount Plus", "display_priority": 16 }
      ],
      "rent": [
        { "logo_path": "/5NyLm42TmCqCMOZFvH4fcoSNKEW.jpg", "provider_id": 10, "provider_name": "Amazon Video", "display_priority": 13 }
      ],
      "buy": [
        { "logo_path": "/peURlLlr8jggOwK53fJ5wdQl05y.jpg", "provider_id": 2, "provider_name": "Apple TV", "display_priority": 4 }
      ]
    },
    "DE": { "link": "https://www.themoviedb.org/movie/550-fight-club/watch?locale=DE", "flatrate": [] }
  }
}
```

### The `link` field

Every country block contains `link`. The value is a TMDB watch page for that title and that locale.

Send the user through this link. Three reasons apply:

1. The API gives no deep links. The TMDB page has them.
2. The link stays correct when availability changes. Your cached provider list does not.
3. TMDB asks for the link. It supports TMDB and satisfies the spirit of the attribution rule.

> **Note:** The season endpoint returns a **series** watch link, for example `https://www.themoviedb.org/tv/1399-game-of-thrones/watch?locale=AD`. Do not expect a season-specific URL.

### Monetization buckets

| Bucket | Meaning | Typical label |
| :--- | :--- | :--- |
| `flatrate` | Included in a subscription | "Stream" |
| `free` | Free and with no advertisements | "Free" |
| `ads` | Free but with advertisements | "Free with ads" |
| `rent` | Pay once for limited access | "Rent" |
| `buy` | Pay once for permanent access | "Buy" |

Each bucket is an array of provider objects. Each object has exactly four fields:

| Field | Type | Use |
| :--- | :--- | :--- |
| `provider_id` | integer | Stable identifier. Use it for Discover filters and for your own joins. |
| `provider_name` | string | Display name, for example `Netflix`. |
| `logo_path` | string | Relative path. Combine it with the image base URL. |
| `display_priority` | integer | Sort order for this country. Lower comes first. |

> **Warning:** A bucket key is absent when it is empty. Never index a bucket directly. Read it with a default of an empty list.

```python
# Do this
flatrate = country.get("flatrate", [])

# Don't do this - raises KeyError on most countries
flatrate = country["flatrate"]
```

## Pattern: get providers for one title in one region

```python
import os
import requests

BASE = "https://api.themoviedb.org/3"
SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
    "accept": "application/json",
})

BUCKETS = ("flatrate", "free", "ads", "rent", "buy")


def watch_providers(media_type: str, tmdb_id: int, region: str) -> dict | None:
    """Return the provider block for one country, or None if TMDB knows nothing."""
    path = "movie" if media_type == "movie" else "tv"
    response = SESSION.get(f"{BASE}/{path}/{tmdb_id}/watch/providers", timeout=10)
    response.raise_for_status()
    return response.json()["results"].get(region.upper())


def ordered(providers: list[dict]) -> list[dict]:
    """Sort one bucket for display. Lower display_priority comes first."""
    return sorted(providers, key=lambda p: (p["display_priority"], p["provider_name"]))


block = watch_providers("movie", 550, "US")
if block is None:
    print("No known availability in this region.")
else:
    print(block["link"])
    for bucket in BUCKETS:
        for provider in ordered(block.get(bucket, [])):
            print(f"{bucket:9} {provider['provider_name']} (id={provider['provider_id']})")
```

### The same call with `append_to_response`

Details and providers travel in one request. The appended key keeps the slash.

```bash
curl --request GET \
  --url 'https://api.themoviedb.org/3/movie/550?append_to_response=watch/providers&language=en-US' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
movie = SESSION.get(f"{BASE}/movie/550", params={"append_to_response": "watch/providers"}).json()
us = movie["watch/providers"]["results"].get("US")   # note the slash in the key
```

Prefer this form on a detail page. It removes one round trip. See `./append-to-response.md`.

## Pattern: order providers correctly

`display_priority` is JustWatch's ranking for that country. The number is not a global rank and not a quality score. A lower number goes first.

Two different `display_priority` values exist. Do not mix them.

| Where | Field | Scope |
| :--- | :--- | :--- |
| Per-title response | `display_priority` | Already the value for that country |
| Provider list endpoints | `display_priority` | A default, global fallback |
| Provider list endpoints | `display_priorities` | An object keyed by country code, for example `{"US": 4, "DE": 8}` |

```python
def list_priority(provider: dict, region: str) -> int:
    """Pick the region priority from a /watch/providers/{movie|tv} entry."""
    return provider.get("display_priorities", {}).get(region, provider["display_priority"])
```

```python
# Do this: sort inside each bucket, then show the buckets in your own fixed order
for bucket in ("flatrate", "free", "ads", "rent", "buy"):
    render(bucket, ordered(block.get(bucket, [])))

# Don't do this: merge all buckets into one list
everything = block.get("flatrate", []) + block.get("rent", []) + block.get("buy", [])
# The user cannot see which offer costs money.
```

> **Note:** The arrays usually arrive sorted by `display_priority`. The documentation does not guarantee the order. Sort the list yourself.

## Pattern: build the provider logo URL

`logo_path` is a relative path. Prefix it with the image base URL and a logo size.

Read the sizes from `GET /3/configuration`, then cache them. The current `logo_sizes` are `w45`, `w92`, `w154`, `w185`, `w300`, `w500` and `original`.

```python
LOGO_BASE = "https://image.tmdb.org/t/p/"

def logo_url(logo_path: str, size: str = "w92") -> str:
    return f"{LOGO_BASE}{size}{logo_path}"

# https://image.tmdb.org/t/p/w92/t2yyOv40HZeVlLjYsCsPHnWLk4W.jpg
```

```javascript
const logoUrl = (path, size = "w92") => `https://image.tmdb.org/t/p/${size}${path}`;
```

Use `w45` for a dense row and `w92` for a normal card. Provider logos are square, so a width size gives a predictable box. Read `./images-and-configuration.md` for the full rules and for the change policy on the base URL.

## Pattern: list the supported regions

Call this once per deploy and cache the result. Use it to fill a country selector.

```bash
curl --request GET \
  --url 'https://api.themoviedb.org/3/watch/providers/regions?language=en-US' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

```json
{ "results": [ { "iso_3166_1": "AD", "english_name": "Andorra", "native_name": "Andorra" } ] }
```

The list holds about 120 countries. Validate the user's region against it before you send `watch_region` to Discover.

## Pattern: list every provider for a media type

Use these endpoints to build a provider picker, for example "Show me only what is on my services".

```bash
# All movie providers available in Germany
curl --request GET \
  --url 'https://api.themoviedb.org/3/watch/providers/movie?language=de-DE&watch_region=DE' \
  --header "Authorization: Bearer $TMDB_TOKEN"

# All TV providers available in Germany
curl --request GET \
  --url 'https://api.themoviedb.org/3/watch/providers/tv?language=de-DE&watch_region=DE' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
def provider_picker(media_type: str, region: str) -> list[dict]:
    """media_type is 'movie' or 'tv'."""
    response = SESSION.get(
        f"{BASE}/watch/providers/{media_type}",
        params={"watch_region": region, "language": "en-US"},
        timeout=10,
    )
    response.raise_for_status()
    providers = response.json()["results"]
    return sorted(providers, key=lambda p: list_priority(p, region))
```

> **Warning:** Omit `watch_region` and you get every provider in every country, which is over 500 entries for movies. Always pass `watch_region` for a user-facing picker.

The two lists are not the same. In the documented sample the movie list holds 529 providers and the TV list holds 474. About 121 providers appear only for movies, and about 66 appear only for TV. Fetch the list that matches the media type you filter.

## Discover: filter by provider

Discover turns the provider data into a query. Read `./discover.md` for the other filters and for pagination.

| Parameter | Applies to | Notes |
| :--- | :--- | :--- |
| `watch_region` | `/discover/movie`, `/discover/tv` | ISO 3166-1 code. Required with the parameters below. |
| `with_watch_providers` | both | Comma or pipe separated `provider_id` values. |
| `without_watch_providers` | both | Excludes those providers. |
| `with_watch_monetization_types` | both | One or more of `flatrate`, `free`, `ads`, `rent`, `buy`. |

### `watch_region` is mandatory

> **Warning:** TMDB silently ignores `with_watch_providers` and `with_watch_monetization_types` when you omit `watch_region`. You get an unfiltered popular list and no error. Always send the pair.

```python
# Do this
params = {"watch_region": "SE", "with_watch_providers": "8|337", "sort_by": "popularity.desc"}

# Don't do this - the provider filter does nothing
params = {"with_watch_providers": "8|337", "sort_by": "popularity.desc"}
```

### OR and AND syntax

The separator carries the logic. It is the same rule for both parameters.

| Separator | Logic | Example | Meaning |
| :--- | :--- | :--- | :--- |
| `\|` (pipe) | OR | `with_watch_providers=8\|337` | On Netflix **or** Disney Plus |
| `,` (comma) | AND | `with_watch_providers=8,337` | On Netflix **and** Disney Plus |

Use OR almost always. A user with three subscriptions wants any of them. AND returns very few titles.

```bash
# Movies on Netflix or Disney Plus in Sweden, by subscription only
curl --get \
  --url 'https://api.themoviedb.org/3/discover/movie' \
  --data-urlencode 'watch_region=SE' \
  --data-urlencode 'with_watch_providers=8|337' \
  --data-urlencode 'with_watch_monetization_types=flatrate' \
  --data-urlencode 'sort_by=popularity.desc' \
  --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
resp = SESSION.get(f"{BASE}/discover/tv", params={
    "watch_region": "GB",
    "with_watch_providers": "9|384",              # Amazon Prime Video OR HBO Max
    "with_watch_monetization_types": "flatrate|free",
    "sort_by": "popularity.desc",
    "page": 1,
})
```

```javascript
const params = new URLSearchParams({
  watch_region: "US",
  with_watch_providers: "8|15|337",
  with_watch_monetization_types: "flatrate",
  sort_by: "popularity.desc",
});
const res = await fetch(`https://api.themoviedb.org/3/discover/movie?${params}`, {
  headers: { Authorization: `Bearer ${token}`, accept: "application/json" },
});
```

> **Note:** `URLSearchParams` and `--data-urlencode` encode the pipe as `%7C`. TMDB accepts both forms. Encode the pipe if you build the query string by hand.

### Discover result rows carry no provider data

Discover returns normal movie or TV rows. It does not tell you which provider matched. Call the per-title endpoint if you must show the logos on a result card. Batch those calls and cache them.

## Best practices

- **Resolve the region once.** Take it from the account setting, then the IP country, then a default of `US`. Pass the same value to the per-title read and to Discover.
- **Cache briefly.** Cache a per-title response for 6 to 24 hours. Cache the region list and the provider lists for days.
- **Store the whole `results` object.** One request already covers every country. Do not call the endpoint again for a second region.
- **Use `provider_id` as the key in your database.** `provider_name` changes when a service rebrands.
- **Keep the bucket order fixed.** Show `flatrate`, then `free`, then `ads`, then `rent`, then `buy`. The user reads the cheapest option first.
- **Deduplicate inside one bucket only.** The same brand in `rent` and in `buy` is two real offers.
- **Show the TMDB `link` even when a bucket is empty.** The TMDB page may list options that arrived after your cache.
- **Refresh with the change feeds.** See `./changes-and-exports.md` to find titles that changed.

## Anti-patterns

| Don't do this | Do this |
| :--- | :--- |
| Treat `results` as an array | Treat `results` as an object keyed by country code |
| Report "not available" for a missing country key | Report "no availability information" |
| Build a deep link from `provider_name` | Send the user to the `link` value |
| Cache provider data for weeks | Cache for hours, then refetch |
| Show logos with no credit | Credit JustWatch on the same screen |
| Send `with_watch_providers` alone | Send it with `watch_region` |
| Use the movie provider list to filter TV | Fetch `/watch/providers/tv` for TV |
| Sort by `provider_id` or by name | Sort by `display_priority` |
| Hard-code `https://image.tmdb.org/t/p/` forever | Read the base URL from `/3/configuration` |

## Pitfalls and gotchas

**A missing country key means "unknown", not "unavailable".** JustWatch does not cover every service in every market. Write "We have no availability information for your region" and show a search link. Never write "Not available".

**Availability changes every week.** A title leaves a subscription service with no notice. A long cache produces a wrong answer and an angry user. Keep the per-title cache short and always render the `link`.

**Provider identity is not stable across regions.** The same brand can carry a different `provider_id` in a different country. In the documented samples HBO Max is `provider_id` 384 in the US, and the Andorra block of the same series uses `provider_id` 1899. Group by brand at your own risk. Match on `provider_id` per region.

**The movie and TV provider lists differ.** A `provider_id` in the movie list may be absent from the TV list, and the reverse also happens. Fetch the list for the media type you filter, and never reuse one picker for both.

**A `provider_id` in a title response may be missing from the list endpoint.** The list endpoints lag behind. Render `provider_name` and `logo_path` from the title response instead of a lookup in your cached list.

**`display_priority` is not the same number everywhere.** The per-title value is already scoped to the country. The list endpoints give a global `display_priority` plus a `display_priorities` map. Read the map when you have a region.

**The list endpoints return an unsorted array.** The documented sample starts with priorities 2, 3, 42 and 0. Sort before you display.

**The season endpoint takes `language`, the movie and series endpoints do not.** Do not send `language` to `/movie/{id}/watch/providers`. TMDB ignores it there. `language` only changes the region names and provider names where translations exist. See `./localization.md`.

**`link` points to TMDB, not to the provider.** It is a landing page. Do not label the button with the provider name and imply direct playback.

**Empty arrays exist.** A country block can hold `link` plus an empty `flatrate` array. Test for length, not only for the key.

**Rate limits still apply.** One provider call per result row exhausts your budget fast. Use `append_to_response` on detail pages and batch elsewhere. See `./getting-started.md`.

## Related skill files

| File | Why you need it |
| :--- | :--- |
| `./discover.md` | The full Discover filter set, sorting and pagination for `with_watch_providers` |
| `./images-and-configuration.md` | The image base URL and `logo_sizes` for `logo_path` |
| `./append-to-response.md` | Fetch details and providers in one request |
| `./authentication.md` | The bearer token used by every call here |
| `./movies.md` | The `movie_id` you pass to `/movie/{id}/watch/providers` |
| `./tv-series.md` | The `series_id` for the series endpoint |
| `./tv-seasons-and-episodes.md` | The `season_number` for the season endpoint |
| `./localization.md` | The `language` parameter and ISO 3166-1 region codes |
| `./search-and-find.md` | Resolve a title to a TMDB id first |
| `./changes-and-exports.md` | Find titles that changed and refresh your cache |
| `./trending-and-popular.md` | Combine a popular list with a provider filter |
| `./getting-started.md` | Rate limits, error handling and the request basics |
