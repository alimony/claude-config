# TMDB: Discover
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

Discover is the query builder of TMDB. It returns a filtered, sorted, paginated list of movies or TV shows.

| Endpoint | Purpose |
| --- | --- |
| `GET /3/discover/movie` | Find movies with 38 filter and sort parameters. |
| `GET /3/discover/tv` | Find TV shows with 33 filter and sort parameters. |

Discover has no text query parameter. It matches on structured data only: IDs, dates, numbers, country codes, and language codes.

### Discover or Search?

| You know | Use | File |
| --- | --- | --- |
| A title, a person name, or any free text | Search | `./search-and-find.md` |
| An external ID (IMDb, TVDB) | Find | `./search-and-find.md` |
| Genre, keyword, company, person ID, date range, rating, provider | Discover | this file |
| Nothing – you want the current hits | Trending or popular | `./trending-and-popular.md` |

Do not use Discover to look up a title by name. Do not use Search to build a filtered browse page. Search ranks on text relevance and ignores almost every filter.

**Discover speaks in IDs, not names.** Convert every genre, keyword, company, network, person, and provider name to a numeric ID first. Read `./entities.md` for genre and network IDs, `./search-and-find.md` for keyword and company lookup, `./people-and-credits.md` for person IDs, and `./watch-providers.md` for provider IDs.

## 2. The base request

Authenticate with a v4 read access token in the `Authorization` header. Read `./authentication.md` for the `api_key` alternative.

```bash
curl -s -G 'https://api.themoviedb.org/3/discover/movie' \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  -H 'accept: application/json' \
  --data-urlencode 'language=en-US' \
  --data-urlencode 'sort_by=popularity.desc' \
  --data-urlencode 'with_genres=878' \
  --data-urlencode 'vote_count.gte=500' \
  --data-urlencode 'page=1'
```

Use `-G` with `--data-urlencode`. It encodes the pipe character and the comma correctly, and it stops the shell from reading `|` as a pipe operator.

```python
import os, requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {os.environ['TMDB_TOKEN']}", "accept": "application/json"}

def discover(media, params):          # media is "movie" or "tv"
    r = requests.get(f"{BASE}/discover/{media}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

data = discover("movie", {"sort_by": "popularity.desc", "with_genres": "878", "vote_count.gte": 500})
print(data["total_results"], len(data["results"]))
```

Pass a dictionary, never `**kwargs`. Many parameter names contain a dot (`vote_count.gte`), and a dot is not legal in a Python keyword argument.

```js
const qs = new URLSearchParams({ sort_by: "vote_average.desc", "vote_count.gte": "1000", with_genres: "18" });
const res = await fetch(`https://api.themoviedb.org/3/discover/movie?${qs}`, {
  headers: { Authorization: `Bearer ${process.env.TMDB_TOKEN}`, accept: "application/json" },
});
const data = await res.json();
```

### Response shape

Both endpoints return `{ "page": 1, "results": [...], "total_pages": 38020, "total_results": 760385 }`.

A movie result holds `id`, `title`, `original_title`, `overview`, `release_date`, `genre_ids`, `popularity`, `vote_average`, `vote_count`, `poster_path`, `backdrop_path`, `adult`, `video`, and `original_language`. A TV result holds `id`, `name`, `original_name`, `overview`, `first_air_date`, `genre_ids`, `origin_country`, and the same popularity, vote, image, and language fields.

Discover returns summary objects only. It gives `genre_ids`, not genre names, and it does not accept `append_to_response`. Fetch the detail endpoint for the full record – read `./movies.md`, `./tv-series.md`, and `./append-to-response.md`. Build image URLs with `./images-and-configuration.md`.

## 3. AND, OR, and NOT

| Operator | Syntax | Meaning |
| --- | --- | --- |
| AND | comma `,` | The title must match every value. |
| OR | pipe `\|` | The title must match at least one value. |
| NOT | a `without_*` parameter | The title must match no value in the list. |

```bash
with_genres=28,878     # action AND science fiction
with_genres=28|878     # action OR science fiction
without_genres=27      # not horror
```

| Parameter | AND (`,`) | OR (`\|`) | Endpoint |
| --- | --- | --- | --- |
| `with_genres` | yes | yes | movie, TV |
| `without_genres` | yes | yes | movie, TV |
| `with_keywords` | yes | yes | movie, TV |
| `without_keywords` | yes | yes | movie, TV |
| `with_companies` | yes | yes | movie, TV |
| `without_companies` | yes | yes | movie, TV |
| `with_people` | yes | yes | movie only |
| `with_cast` | yes | yes | movie only |
| `with_crew` | yes | yes | movie only |
| `with_release_type` | yes | yes | movie only |
| `with_watch_providers` | yes | yes | movie, TV |
| `without_watch_providers` | yes | yes | movie, TV |
| `with_watch_monetization_types` | yes | yes | movie, TV |
| `with_status` | yes | yes | TV only |
| `with_type` | yes | yes | TV only |
| `with_networks` | no | in practice only | TV only |
| `with_origin_country` | no | yes | movie, TV |

The API definition types `with_networks` as a single integer. A pipe-separated list works in practice, but TMDB does not document it. Send one network per request when you need a guaranteed result.

The definition marks the `without_*` parameters as plain strings. They accept the same punctuation as their `with_*` twin. Use the pipe for an exclusion list, because comma-AND only excludes titles that carry every listed value.

```bash
without_genres=27|10770    # Do this – exclude horror OR TV movies.
without_genres=27,10770    # Don't do this – it only excludes horror TV movies.
```

### The three people parameters (movie only)

| Parameter | Matches |
| --- | --- |
| `with_cast` | The person appears in the cast. Use it for an actor filmography. |
| `with_crew` | The person appears in the crew. Use it for a director or a composer. |
| `with_people` | The person appears in the cast or the crew. |

## 4. Range filters: the `.gte` and `.lte` suffixes

A range parameter takes a lower bound with `.gte` (greater than or equal) and an upper bound with `.lte` (less than or equal). Send one bound or both. Both bounds are inclusive. Write every date as `YYYY-MM-DD`.

| Base parameter | Type | Endpoint | Filters on |
| --- | --- | --- | --- |
| `primary_release_date` | date | movie only | The first worldwide release date. |
| `release_date` | date | movie only | Any release date, or the regional date when you send `region`. |
| `first_air_date` | date | TV only | The date of the first episode of the series. |
| `air_date` | date | TV only | Any episode air date in the window. |
| `vote_average` | float | movie, TV | The user rating, 0 to 10. |
| `vote_count` | float | movie, TV | The number of user votes. |
| `with_runtime` | integer | movie, TV | Runtime in minutes. |
| `certification` | string | movie only | Position in the country's certification order. |

```bash
'primary_release_date.gte=1990-01-01' 'primary_release_date.lte=1999-12-31'
'vote_average.gte=7.5' 'vote_count.gte=500' 'with_runtime.gte=90' 'with_runtime.lte=150'
```

Two shorthand year parameters exist: `primary_release_year` (movie) and `first_air_date_year` (TV). The movie `year` parameter is different – it matches a title that has any release date in that year.

## 5. Every `sort_by` value

The default is `popularity.desc` on both endpoints. Every value ends in `.asc` or `.desc`. An unknown value returns a 400 error.

| Value | Endpoint | Sorts on |
| --- | --- | --- |
| `popularity.asc` / `popularity.desc` | movie, TV | The TMDB popularity score, recalculated every day. |
| `vote_average.asc` / `vote_average.desc` | movie, TV | The user rating, 0 to 10. |
| `vote_count.asc` / `vote_count.desc` | movie, TV | The number of user votes. |
| `revenue.asc` / `revenue.desc` | movie only | Worldwide box office revenue in US dollars. |
| `primary_release_date.asc` / `.desc` | movie only | The primary release date. |
| `title.asc` / `title.desc` | movie only | The localized title, alphabetically. |
| `original_title.asc` / `original_title.desc` | movie only | The original-language title, alphabetically. |
| `first_air_date.asc` / `first_air_date.desc` | TV only | The date of the first episode. |
| `name.asc` / `name.desc` | TV only | The localized series name, alphabetically. |
| `original_name.asc` / `original_name.desc` | TV only | The original-language name, alphabetically. |

There is no `release_date` sort and no `id` sort. TV has no revenue sort at all.

## 6. Watch providers

| Parameter | Value |
| --- | --- |
| `watch_region` | An ISO 3166-1 country code, for example `US`, `SE`, `DE`. |
| `with_watch_providers` | Provider IDs, comma-AND or pipe-OR. |
| `without_watch_providers` | Provider IDs to exclude. |
| `with_watch_monetization_types` | `flatrate`, `free`, `ads`, `rent`, `buy`. |

`watch_region` is mandatory. Availability is per country, so TMDB ignores a provider filter that carries no region. It reports no error.

```bash
with_watch_providers=8|9|337&watch_region=US   # Do this – Netflix OR Prime Video OR Disney+.
with_watch_providers=8                          # Don't do this – the filter does nothing.
with_watch_providers=8,9&watch_region=US        # Don't do this – on both services at once.
```

| Monetization value | Meaning |
| --- | --- |
| `flatrate` | Included in a subscription. |
| `free` | Free, with no advertisements. |
| `ads` | Free, supported by advertisements. |
| `rent` | Available for rent. |
| `buy` | Available for purchase. |

`with_watch_monetization_types` also needs `watch_region`. Read `./watch-providers.md` for the provider ID list.

## 7. Movie-only filters

### `with_release_type`

| Code | Release type |
| --- | --- |
| 1 | Premiere |
| 2 | Theatrical (limited) |
| 3 | Theatrical |
| 4 | Digital |
| 5 | Physical |
| 6 | TV |

`with_release_type` accepts comma-AND and pipe-OR. Pair it with `region` to filter on that country's release dates.

The order of the values changes the returned date. `2|3` returns the limited theatrical date. `3|2` returns the wide theatrical date. Put the type you want to read first.

```bash
region=DE&with_release_type=4|5&release_date.gte=2026-08-01&release_date.lte=2026-08-31
```

### `certification` and `certification_country`

| Parameter | Purpose |
| --- | --- |
| `certification` | An exact certification, for example `R` or `PG-13`. |
| `certification.gte` | The lowest certification in the country's order. |
| `certification.lte` | The highest certification in the country's order. |
| `certification_country` | The country whose rating system applies. |

Always send `certification_country` with any certification filter. Rating strings differ per country, so TMDB cannot resolve `R` alone. Send `region` with the same code as well.

```bash
certification_country=US&certification.lte=PG-13&region=US
```

### `region` and `include_video`

`region` is an ISO 3166-1 country code. It switches the date filters and the returned dates to that country's release dates. The TV endpoint has no `region` parameter.

`include_video=false` is the default. It hides entries that TMDB flags as video, such as direct-to-video compilations. Keep the default for a public browse page.

## 8. TV-only filters

| Code | `with_status` | `with_type` |
| --- | --- | --- |
| 0 | Returning Series | Documentary |
| 1 | Planned | News |
| 2 | In Production | Miniseries |
| 3 | Ended | Reality |
| 4 | Cancelled | Scripted |
| 5 | Pilot | Talk Show |
| 6 | – | Video |

Both accept comma-AND and pipe-OR. Use the pipe, because one show has one status and one type.

```bash
with_status=0|2&with_type=4      # scripted shows that still run
```

- `include_null_first_air_dates` – default `false`. TMDB then drops every show with no first air date. Set it to `true` to include announced shows.
- `screened_theatrically` – set it to `true` to keep only shows with a theatrical screening record. Leave it out otherwise.
- `timezone` – takes an IANA name such as `America/New_York`. It shifts the air-date boundary. Use it only for day-accurate air-date queries.

## 9. Language, origin, and adult content

| Parameter | Effect |
| --- | --- |
| `language` | Translates the output. It does not filter. Default `en-US`. |
| `with_original_language` | Filters on the ISO 639-1 original language, for example `ja`. |
| `with_origin_country` | Filters on the ISO 3166-1 production country, for example `KR`. Pipe-OR only. |
| `include_adult` | Default `false`. Set it to `true` to include adult titles. |

```bash
language=en-US&with_original_language=ja   # Do this – Japanese films, English text.
language=ja-JP                             # Don't do this – it only translates the overview.
```

Read `./localization.md` for language codes and translation fallbacks.

## 10. Pagination and the result cap

Results per page are fixed at 20. Pages start at 1 and stop at 500, so you can reach 10 000 results at most. `total_results` often reports far more. A request for page 501 returns an error.

```python
def discover_all(media, params, max_pages=500):
    seen, page = {}, 1
    while page <= max_pages:
        data = discover(media, {**params, "page": page})
        for item in data["results"]:
            seen[item["id"]] = item                       # de-duplicate on id
        if page >= min(data["total_pages"], 500):
            break
        page += 1
    return list(seen.values())
```

Narrow the query when you need more than 10 000 titles. Split one broad query into one query per year, then merge the results.

Do not deep-page on `popularity.desc`. TMDB recalculates popularity every day, so the order moves under you and pages repeat or skip titles. Sort on a stable field such as `primary_release_date.desc` for a long crawl, and de-duplicate on `id`.

## 11. Complete parameter reference – `/discover/movie`

38 parameters. The "On TV" column says whether `/discover/tv` has the same parameter.

| Parameter | Type | On TV | Description |
| --- | --- | --- | --- |
| `certification` | string | no | Exact certification value; needs `certification_country`. |
| `certification.gte` | string | no | Lowest certification in the country's order. |
| `certification.lte` | string | no | Highest certification in the country's order. |
| `certification_country` | string | no | Country whose rating system the certification filters use. |
| `include_adult` | boolean | yes | Include adult titles. Default `false`. |
| `include_video` | boolean | no | Include entries flagged as video. Default `false`. |
| `language` | string | yes | Output language, `xx-XX`. Default `en-US`. Does not filter. |
| `page` | integer | yes | Page number, 1 to 500. Default `1`. |
| `primary_release_year` | integer | no | Year of the primary release date. |
| `primary_release_date.gte` | date | no | Primary release on or after this date. |
| `primary_release_date.lte` | date | no | Primary release on or before this date. |
| `region` | string | no | ISO 3166-1 country; switches date filters to regional dates. |
| `release_date.gte` | date | no | Any release on or after this date. |
| `release_date.lte` | date | no | Any release on or before this date. |
| `sort_by` | enum | yes (other values) | Sort order. Default `popularity.desc`. |
| `vote_average.gte` | float | yes | Minimum user rating. |
| `vote_average.lte` | float | yes | Maximum user rating. |
| `vote_count.gte` | float | yes | Minimum number of votes. |
| `vote_count.lte` | float | yes | Maximum number of votes. |
| `watch_region` | string | yes | ISO 3166-1 country for every watch-provider filter. |
| `with_cast` | string | no | Person IDs in the cast. Comma-AND or pipe-OR. |
| `with_companies` | string | yes | Production company IDs. Comma-AND or pipe-OR. |
| `with_crew` | string | no | Person IDs in the crew. Comma-AND or pipe-OR. |
| `with_genres` | string | yes | Genre IDs. Comma-AND or pipe-OR. |
| `with_keywords` | string | yes | Keyword IDs. Comma-AND or pipe-OR. |
| `with_origin_country` | string | yes | ISO 3166-1 production country. |
| `with_original_language` | string | yes | ISO 639-1 original language. |
| `with_people` | string | no | Person IDs in the cast or the crew. Comma-AND or pipe-OR. |
| `with_release_type` | integer | no | Release codes 1 to 6. Comma-AND or pipe-OR; use with `region`. |
| `with_runtime.gte` | integer | yes | Minimum runtime in minutes. |
| `with_runtime.lte` | integer | yes | Maximum runtime in minutes. |
| `with_watch_monetization_types` | string | yes | `flatrate`, `free`, `ads`, `rent`, `buy`; needs `watch_region`. |
| `with_watch_providers` | string | yes | Provider IDs; needs `watch_region`. Comma-AND or pipe-OR. |
| `without_companies` | string | yes | Company IDs to exclude. |
| `without_genres` | string | yes | Genre IDs to exclude. |
| `without_keywords` | string | yes | Keyword IDs to exclude. |
| `without_watch_providers` | string | yes | Provider IDs to exclude; needs `watch_region`. |
| `year` | integer | no | Any release date in this year. |

## 12. Complete parameter reference – `/discover/tv`

33 parameters. The "On movie" column says whether `/discover/movie` has the same parameter.

| Parameter | Type | On movie | Description |
| --- | --- | --- | --- |
| `air_date.gte` | date | no | An episode airs on or after this date. |
| `air_date.lte` | date | no | An episode airs on or before this date. |
| `first_air_date_year` | integer | no | Year of the first episode. |
| `first_air_date.gte` | date | no | First episode on or after this date. |
| `first_air_date.lte` | date | no | First episode on or before this date. |
| `include_adult` | boolean | yes | Include adult titles. Default `false`. |
| `include_null_first_air_dates` | boolean | no | Include shows with no first air date. Default `false`. |
| `language` | string | yes | Output language, `xx-XX`. Default `en-US`. Does not filter. |
| `page` | integer | yes | Page number, 1 to 500. Default `1`. |
| `screened_theatrically` | boolean | no | Keep only shows with a theatrical screening. |
| `sort_by` | enum | yes (other values) | Sort order. Default `popularity.desc`. |
| `timezone` | string | no | IANA timezone that shifts the air-date boundary. |
| `vote_average.gte` | float | yes | Minimum user rating. |
| `vote_average.lte` | float | yes | Maximum user rating. |
| `vote_count.gte` | float | yes | Minimum number of votes. |
| `vote_count.lte` | float | yes | Maximum number of votes. |
| `watch_region` | string | yes | ISO 3166-1 country for every watch-provider filter. |
| `with_companies` | string | yes | Production company IDs. Comma-AND or pipe-OR. |
| `with_genres` | string | yes | Genre IDs. Comma-AND or pipe-OR. |
| `with_keywords` | string | yes | Keyword IDs. Comma-AND or pipe-OR. |
| `with_networks` | integer | no | Network ID. The definition allows one value. |
| `with_origin_country` | string | yes | ISO 3166-1 production country. |
| `with_original_language` | string | yes | ISO 639-1 original language. |
| `with_runtime.gte` | integer | yes | Minimum episode runtime in minutes. |
| `with_runtime.lte` | integer | yes | Maximum episode runtime in minutes. |
| `with_status` | string | no | Status codes 0 to 5. Comma-AND or pipe-OR. |
| `with_type` | string | no | Show type codes 0 to 6. Comma-AND or pipe-OR. |
| `with_watch_monetization_types` | string | yes | `flatrate`, `free`, `ads`, `rent`, `buy`; needs `watch_region`. |
| `with_watch_providers` | string | yes | Provider IDs; needs `watch_region`. Comma-AND or pipe-OR. |
| `without_companies` | string | yes | Company IDs to exclude. |
| `without_genres` | string | yes | Genre IDs to exclude. |
| `without_keywords` | string | yes | Keyword IDs to exclude. |
| `without_watch_providers` | string | yes | Provider IDs to exclude; needs `watch_region`. |

The TV endpoint has no `region`, no `certification`, no `with_cast`, no `with_crew`, no `with_people`, and no `with_release_type`.

## 13. Worked recipes

### Highly rated science fiction from the 1990s

```bash
curl -s -G 'https://api.themoviedb.org/3/discover/movie' \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  --data-urlencode 'with_genres=878' \
  --data-urlencode 'primary_release_date.gte=1990-01-01' \
  --data-urlencode 'primary_release_date.lte=1999-12-31' \
  --data-urlencode 'vote_count.gte=500' \
  --data-urlencode 'sort_by=vote_average.desc'
```

The vote floor removes obscure titles with three perfect votes.

### Movies streaming on one provider in one country

```python
discover("movie", {
    "with_watch_providers": "8",              # Netflix – see ./watch-providers.md
    "watch_region": "SE",
    "with_watch_monetization_types": "flatrate",
    "sort_by": "popularity.desc",
    "vote_count.gte": 50,
})
```

### TV shows from one network that still run

```bash
curl -s -G 'https://api.themoviedb.org/3/discover/tv' \
  -H "Authorization: Bearer $TMDB_TOKEN" \
  --data-urlencode 'with_networks=213' \
  --data-urlencode 'with_status=0|2' \
  --data-urlencode 'sort_by=first_air_date.desc'
```

Network 213 is Netflix. Status `0|2` means Returning Series or In Production.

### Everything an actor appeared in, sorted by revenue

```python
data = discover("movie", {
    "with_cast": "6193",                      # person ID – see ./people-and-credits.md
    "sort_by": "revenue.desc",
    "include_adult": False,
    "include_video": False,
})
for m in data["results"]:
    print(m["release_date"], m["title"])
```

Use `with_crew` for a director. Use `/person/{id}/movie_credits` when you also want the credited role.

### Short one-liners

```bash
# Action AND comedy, no horror, 90 to 120 minutes.
with_genres=28,35&without_genres=27&with_runtime.gte=90&with_runtime.lte=120&vote_count.gte=100

# Family-safe US releases.
certification_country=US&certification.lte=PG&region=US&sort_by=popularity.desc

# Korean-language dramas from 2024 (/discover/tv).
with_original_language=ko&with_genres=18&first_air_date_year=2024&sort_by=popularity.desc

# One studio and one keyword, best rated first.
with_companies=420&with_keywords=9715&vote_count.gte=1000&sort_by=vote_average.desc
```

## 14. Best practices

- Convert names to IDs once, then cache the mapping. Genre lists change rarely.
- Always add `vote_count.gte` when you sort on `vote_average`.
- Use the pipe for "any of these" and the comma for "all of these". Read the query aloud to check it.
- Send `watch_region` with every watch-provider parameter.
- Send `certification_country` with every certification parameter.
- Keep `include_adult=false` and `include_video=false` for a public browse page.
- Cache the response. Discover results change slowly, except on popularity sorts.
- Request only the pages the user views. Do not crawl 500 pages to show 20 rows.
- Use `language` for display text and `with_original_language` for filtering.
- Treat an empty `results` array as a normal answer, not as an error.

## 15. Anti-patterns

| Don't do this | Do this |
| --- | --- |
| `sort_by=vote_average.desc` alone | Add `vote_count.gte=300`. |
| `with_genres=Action` | `with_genres=28`. |
| `with_watch_providers=8` alone | Add `watch_region=US`. |
| `certification=R` alone | Add `certification_country=US`. |
| `with_watch_providers=8,9` | `with_watch_providers=8\|9`. |
| `without_genres=27,10770` | `without_genres=27\|10770`. |
| `language=ja-JP` to find Japanese films | `with_original_language=ja`. |
| Crawl every page on `popularity.desc` | Sort on a stable field and de-duplicate on `id`. |
| Use Discover to find "Blade Runner" | Use `/search/movie` – see `./search-and-find.md`. |
| Request page 600 | Narrow the filters; the cap is page 500. |

## 16. Pitfalls and gotchas

- **A rating sort without a vote floor.** A title with two 10-star votes beats every classic. Always pair `vote_average.desc` with `vote_count.gte`.
- **A forgotten `watch_region`.** The provider filter has no effect and TMDB reports no error. You get an unfiltered popular list and you may not notice.
- **`region` and `watch_region` are different.** `region` changes which release dates the movie endpoint filters on and returns. `watch_region` chooses the country for streaming availability. Both take an ISO 3166-1 code, so the mistake is easy. Send both for a "streaming now in country X" page, and check that you did not send one in place of the other. The TV endpoint has `watch_region` but no `region`.
- **Genre IDs are not genre names.** The movie list also differs from the TV list. Movie genre 10402 is Music; TV has no such genre. Fetch the correct list per media type – read `./entities.md`.
- **Date filters drop titles with no date.** A movie with an empty `release_date` never matches a date range, and the movie endpoint has no include-null flag. A TV show with no `first_air_date` disappears unless you set `include_null_first_air_dates=true`.
- **`year` and `primary_release_year` differ.** `year` matches any release in that year, including a late festival or physical release. `primary_release_year` matches the first worldwide release only.
- **Comma-AND on providers returns almost nothing.** A title is rarely on two services in the same country at the same time.
- **`with_networks` takes one value in the definition.** Loop over networks and merge the results when you need several.
- **The release type order changes the returned date.** `2|3` returns the limited theatrical date; `3|2` returns the wide theatrical date.
- **`total_results` lies about reach.** It counts the full match set. You can still read only 10 000 of them.
- **Popularity is recalculated daily.** Two requests hours apart can return different orders and duplicate titles across pages.
- **Discover ignores `append_to_response`.** Fetch the detail endpoint per ID when you need credits, videos, or images.
- **An unknown `sort_by` value fails with a 400.** `release_date.desc` does not exist; use `primary_release_date.desc`. `revenue.desc` is movie-only.
- **Encode the pipe in a raw URL string.** Write `%7C` when you build the query string by hand, and quote the argument in a shell.

## 17. Related skill files

- `./getting-started.md` – base URL, rate limits, error codes.
- `./authentication.md` – bearer token and `api_key` setup.
- `./search-and-find.md` – text search; keyword, company, and person ID lookup.
- `./entities.md` – genre lists, network IDs, company records, certification lists.
- `./watch-providers.md` – provider IDs and per-region availability.
- `./movies.md` – movie detail records for each discovered ID.
- `./tv-series.md` – TV detail records; status and type values in context.
- `./tv-seasons-and-episodes.md` – episode data behind the `air_date` filters.
- `./people-and-credits.md` – person IDs for `with_cast`, `with_crew`, and `with_people`.
- `./localization.md` – language and country codes.
- `./images-and-configuration.md` – build poster and backdrop URLs from `poster_path`.
- `./append-to-response.md` – combine detail calls after Discover returns IDs.
- `./trending-and-popular.md` – ready-made popular lists; simpler than a Discover query.
- `./lists.md` – save discovered titles to a user list.
- `./user-account-and-ratings.md` – rated and watchlist items for a signed-in user.
- `./changes-and-exports.md` – bulk ID exports when the 10 000-result cap blocks you.
