# TMDB: Trending and Popular Lists
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

TMDB gives you three different ideas that people often confuse. Keep them separate.

| Idea | Endpoint family | What it measures | Time scale |
|---|---|---|---|
| **Popularity** | `/movie/popular`, `/tv/popular`, `/person/popular`, `sort_by=popularity.desc` in Discover | A lifetime attention score that carries over day to day | Slow – it decays and accumulates |
| **Trending** | `/trending/{type}/{time_window}` | A short-burst attention score | Fast – `day` or `week` |
| **Rating** | `/movie/top_rated`, `/tv/top_rated`, `vote_average` | The average user vote | Very slow |

Three more facts drive every decision in this file:

1. **Popularity is attention, not quality.** A bad film with a big marketing campaign beats a great film with no campaign.
2. **Every curated list is a fixed Discover query.** The docs say so on each list page. You can reproduce it and change it.
3. **The lists re-rank under you.** The same page number returns different items tomorrow, and sometimes an hour later.

All endpoints in this file need a read access token. See `./authentication.md`.

```bash
export TMDB_TOKEN="eyJhbGciOi..."   # v4 read access token
curl -s --url 'https://api.themoviedb.org/3/trending/movie/day?language=en-US' \
     --header "Authorization: Bearer $TMDB_TOKEN" \
     --header 'accept: application/json'
```

## 2. The popularity model

TMDB calculates one popularity number per item. Each media type uses a different mix of signals.

| Signal | Movies | TV shows | People |
|---|---|---|---|
| Number of votes for the day | yes | yes | – |
| Number of views for the day | yes | yes | yes |
| Number of users who marked it a favourite for the day | yes | yes | – |
| Number of users who added it to a watchlist for the day | yes | yes | – |
| Release date | yes | – | – |
| Next or last episode to air date | – | yes | – |
| Number of total votes | yes | yes | – |
| Previous day score | yes | yes | yes |

**How often it recalculates.** The signals are all daily counts, and each new value builds on the previous day score. So the score updates once a day. It behaves like a decayed running total: a spike of attention lifts the score, and the score then falls slowly when the attention stops. TMDB calls it a "lifetime" popularity score for this reason.

**Person popularity is thin.** It uses only page views and the previous day score. It does not use votes or ratings. A person can chart high because of one news story.

**Why popularity is not quality.** Read the signal list again. Every input measures attention: votes cast, pages viewed, watchlist adds. None of them measures whether the votes were good votes. A film with 50,000 one-star votes scores higher than a film with 500 ten-star votes. Use `vote_average` with a vote floor when you want quality. See section 8.

**Historical popularity.** No API gives you the popularity history. The daily ID export files carry the popularity value for each day, back to 28 April 2017. Use those files to build a time series. See `./changes-and-exports.md`.

## 3. Trending, and what `day` and `week` mean

Trending is a second score with a much shorter memory. It exists to surface new content that popularity is too slow to show.

| `time_window` | Meaning | Behaviour |
|---|---|---|
| `day` | Trend over the last day | Volatile. New trailers, news, and releases enter and leave fast. |
| `week` | Trend over the last week | Steadier. A title must hold attention for several days to stay high. |

`time_window` is a **path** segment, not a query parameter. It is required. The enum is `day` or `week`.

```bash
# Correct
curl -s 'https://api.themoviedb.org/3/trending/movie/week' -H "Authorization: Bearer $TMDB_TOKEN"

# Wrong – 404, the path segment is missing
curl -s 'https://api.themoviedb.org/3/trending/movie?time_window=week' -H "Authorization: Bearer $TMDB_TOKEN"
```

**Trending against popular.** Ask which question you want to answer.

- "What is hot right now?" – use `/trending/...`.
- "What is big overall?" – use `/movie/popular` or `sort_by=popularity.desc`.

A 40-year-old classic can sit in `/movie/popular` forever. It reaches `/trending/movie/day` only when something happens to it.

## 4. Quick reference – every list endpoint

| Endpoint | Returns | `language` | `page` | `region` | `timezone` | Extra |
|---|---|---|---|---|---|---|
| `GET /3/trending/all/{time_window}` | Movies, TV and people mixed | yes | no | no | no | Items carry `media_type` |
| `GET /3/trending/movie/{time_window}` | Movies | yes | no | no | no | – |
| `GET /3/trending/tv/{time_window}` | TV shows | yes | no | no | no | – |
| `GET /3/trending/person/{time_window}` | People | yes | no | no | no | Items carry `known_for` |
| `GET /3/movie/popular` | Movies by popularity | yes | yes | **yes** | no | – |
| `GET /3/movie/top_rated` | Movies by rating | yes | yes | **yes** | no | – |
| `GET /3/movie/now_playing` | Movies in theatres now | yes | yes | **yes** | no | Returns `dates` |
| `GET /3/movie/upcoming` | Movies released soon | yes | yes | **yes** | no | Returns `dates` |
| `GET /3/tv/popular` | TV by popularity | yes | yes | no | no | – |
| `GET /3/tv/top_rated` | TV by rating | yes | yes | no | no | – |
| `GET /3/tv/airing_today` | TV with an episode today | yes | yes | no | **yes** | – |
| `GET /3/tv/on_the_air` | TV with an episode in 7 days | yes | yes | no | **yes** | – |
| `GET /3/person/popular` | People by popularity | yes | yes | no | no | Items carry `known_for` |

Every endpoint returns `page`, `results`, `total_pages` and `total_results`. The two movie date endpoints add a `dates` object.

**The trending endpoints accept no `page` parameter.** They return one page. Do not build a paginator for them.

## 5. What each curated list really means

### Movies

| List | Criteria | Sort |
|---|---|---|
| `popular` | No filter at all, except adult and video exclusion | `popularity.desc` |
| `top_rated` | `vote_count.gte=200`, and it excludes genres `99,10755` | `vote_average.desc` |
| `now_playing` | Theatrical release types (`2` limited, `3` theatrical) inside a **past** date window | `popularity.desc` |
| `upcoming` | The same release types inside a **future** date window | `popularity.desc` |

**`now_playing` against `upcoming`.** Both use the same Discover filter. Only the date window differs, and the two windows do not overlap.

- `now_playing` looks backward from today. In the reference example the window is `2023-03-16` to `2023-05-03` – about seven weeks back.
- `upcoming` starts the day after the `now_playing` window ends. In the reference example it is `2023-05-04` to `2023-05-23` – about three weeks ahead.

So a title moves out of `upcoming` and into `now_playing` on its release day. A title never sits in both lists.

**Read the `dates` object.** Both endpoints tell you the window they used. Show it to the user, and never guess it.

```json
{
  "dates": { "minimum": "2023-03-16", "maximum": "2023-05-03" },
  "page": 1,
  "results": [ ... ],
  "total_pages": 76,
  "total_results": 1509
}
```

The window is not fixed. It moves each day, and its width can change. Read `dates` from every response instead of hard-coding a range.

### TV

| List | Criteria | Sort |
|---|---|---|
| `airing_today` | An episode airs **today** in the given `timezone` | `popularity.desc` |
| `on_the_air` | An episode airs in the **next 7 days** | `popularity.desc` |
| `popular` | No filter except adult exclusion | `popularity.desc` |
| `top_rated` | `vote_count.gte=200` | `vote_average.desc` |

**`airing_today` against `on_the_air`.** Both build an `air_date.gte` / `air_date.lte` Discover window. `airing_today` uses a one-day window. `on_the_air` uses a seven-day window that starts today. So `on_the_air` normally contains everything in `airing_today`, plus the rest of the week. Neither returns a `dates` object – you must compute the window yourself if you need it.

**Pass `timezone` for these two.** "Today" depends on the viewer. A show that airs at 21:00 in `America/New_York` is a different calendar day in `Asia/Tokyo`.

```bash
curl -s --url 'https://api.themoviedb.org/3/tv/airing_today?language=en-US&page=1&timezone=America/New_York' \
     --header "Authorization: Bearer $TMDB_TOKEN"
```

### People

`person/popular` has no filter and no Discover equivalent. Discover covers movies and TV only. Each result carries a `known_for` array of up to three movie or TV objects, and each of those carries its own `media_type`.

## 6. `region` and `language`

**`region`** is an ISO-3166-1 country code, uppercase, such as `US`, `SE`, `BR`. Only the four movie list endpoints accept it. It changes which release dates count, so it is essential for `now_playing` and `upcoming`.

```bash
# Swedish theatrical schedule, Swedish text
curl -s --url 'https://api.themoviedb.org/3/movie/now_playing?language=sv-SE&region=SE&page=1' \
     --header "Authorization: Bearer $TMDB_TOKEN"
```

**Do this:** always send `region` with `now_playing` and `upcoming`. **Don't do this:** never show a US theatre schedule to a user in Sweden. The release dates differ by many weeks.

**`language`** is an `ISO-639-1`-`ISO-3166-1` pair such as `en-US` or `pt-BR`. The default is `en-US`. It changes only the translated text: `title`, `name`, `overview`, and the poster and backdrop that TMDB picks. It does **not** re-rank the list, and it does **not** filter by the original language of the title. See `./localization.md`.

```python
# Wrong idea: this does NOT return Japanese films.
requests.get(url, params={"language": "ja-JP"})

# Right idea: filter by original language in Discover.
requests.get("https://api.themoviedb.org/3/discover/movie",
             params={"with_original_language": "ja", "sort_by": "popularity.desc"},
             headers=H)
```

**No region for TV.** `tv/popular`, `tv/top_rated`, `airing_today` and `on_the_air` ignore region. Use Discover with `watch_region` or `with_origin_country` when you need a country view of TV.

## 7. How-to patterns

### Fetch trending and handle the mixed types

`/trending/all/...` mixes three shapes in one array. Movies carry `title` and `release_date`. TV shows carry `name` and `first_air_date`. People carry `name` and `known_for`. Branch on `media_type` – never assume `title` exists.

```python
import os, requests

BASE = "https://api.themoviedb.org/3"
H = {"Authorization": f"Bearer {os.environ['TMDB_TOKEN']}", "accept": "application/json"}

def trending(media_type="all", window="day", language="en-US"):
    r = requests.get(f"{BASE}/trending/{media_type}/{window}",
                     params={"language": language}, headers=H, timeout=10)
    r.raise_for_status()
    return r.json()["results"]

def label(item):
    mt = item.get("media_type")
    if mt == "movie":
        return f"[movie] {item['title']} ({item.get('release_date', '')[:4]})"
    if mt == "tv":
        return f"[tv]    {item['name']} ({item.get('first_air_date', '')[:4]})"
    if mt == "person":
        known = ", ".join(k.get("title") or k.get("name") for k in item.get("known_for", []))
        return f"[person] {item['name']} – known for: {known}"
    return f"[?] {item.get('id')}"

for item in trending("all", "week"):
    print(label(item))
```

The single-type endpoints also set `media_type` on each result, so the same `label()` works for all four.

### Read `now_playing` together with its window

```python
def now_playing(region="US", language="en-US", page=1):
    r = requests.get(f"{BASE}/movie/now_playing",
                     params={"region": region, "language": language, "page": page},
                     headers=H, timeout=10)
    r.raise_for_status()
    return r.json()

data = now_playing(region="SE", language="sv-SE")
win = data["dates"]
print(f"In theatres, releases {win['minimum']} to {win['maximum']}")
for m in data["results"][:10]:
    print(f"{m['release_date']}  {m['title']}  (pop {m['popularity']:.0f})")
```

### Page through a curated list safely

```python
def paged(path, params, max_pages=5):
    """Collect several pages and drop duplicates that re-ranking creates."""
    seen, out = set(), []
    for page in range(1, max_pages + 1):
        r = requests.get(f"{BASE}{path}", params={**params, "page": page}, headers=H, timeout=10)
        r.raise_for_status()
        body = r.json()
        for item in body["results"]:
            if item["id"] not in seen:
                seen.add(item["id"])
                out.append(item)
        if page >= body["total_pages"]:
            break
    return out

top = paged("/movie/top_rated", {"language": "en-US", "region": "US"}, max_pages=3)
```

The de-duplication is not optional. The list re-ranks between your requests, so page 2 can repeat an item from page 1 and skip another one.

### JavaScript fetch

```javascript
const H = { Authorization: `Bearer ${process.env.TMDB_TOKEN}`, accept: "application/json" };

async function trending(mediaType = "all", window = "day", language = "en-US") {
  const url = `https://api.themoviedb.org/3/trending/${mediaType}/${window}?language=${language}`;
  const res = await fetch(url, { headers: H });
  if (!res.ok) throw new Error(`TMDB ${res.status}`);
  const { results } = await res.json();
  return results.map(r => ({
    id: r.id,
    mediaType: r.media_type,
    label: r.title ?? r.name,
    date: r.release_date ?? r.first_air_date ?? null,
  }));
}
```

## 8. The judgement call – curated list or Discover?

Each curated list is a **fixed** Discover query. TMDB says this in a note on every list reference page. The list gives you no control over the filter. Discover gives you the same data and full control.

| Curated list | Equivalent Discover call |
|---|---|
| `/movie/popular` | `/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc` |
| `/movie/top_rated` | `/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=vote_average.desc&without_genres=99,10755&vote_count.gte=200` |
| `/movie/now_playing` | `/discover/movie?...&sort_by=popularity.desc&with_release_type=2\|3&release_date.gte={min}&release_date.lte={max}` |
| `/movie/upcoming` | The same call, with a future `{min}`/`{max}` window |
| `/tv/popular` | `/discover/tv?include_adult=false&language=en-US&page=1&sort_by=popularity.desc` |
| `/tv/top_rated` | `/discover/tv?include_adult=false&language=en-US&page=1&sort_by=vote_average.desc&vote_count.gte=200` |
| `/tv/airing_today` | `/discover/tv?...&sort_by=popularity.desc&air_date.gte={today}&air_date.lte={today}` |
| `/tv/on_the_air` | `/discover/tv?...&sort_by=popularity.desc&air_date.gte={today}&air_date.lte={today+7}` |

Genre `99` is Documentary. Genre `10755` does not appear in the public movie genre list; TMDB uses it to hide a category from the top-rated chart.

**Rule of thumb.** Use the curated list when you want exactly what TMDB shows on its own site. Switch to Discover the moment you want one extra filter – a genre, a year, a country, a streaming provider, or a stricter vote floor.

### Build your own "top rated" with a proper vote floor

The TMDB `top_rated` floor of 200 votes is low. A niche title with 210 votes and a 9.0 average outranks a classic with 20,000 votes and an 8.6 average. Raise the floor to match your audience.

```bash
# Top rated movies, strict: 2000+ votes, no documentaries, English text
curl -s --get 'https://api.themoviedb.org/3/discover/movie' \
     --data-urlencode 'sort_by=vote_average.desc' \
     --data-urlencode 'vote_count.gte=2000' \
     --data-urlencode 'without_genres=99,10755' \
     --data-urlencode 'include_adult=false' \
     --data-urlencode 'include_video=false' \
     --data-urlencode 'language=en-US' \
     --data-urlencode 'page=1' \
     --header "Authorization: Bearer $TMDB_TOKEN"
```

```python
def top_rated_movies(min_votes=2000, page=1, language="en-US", **extra):
    params = {
        "sort_by": "vote_average.desc",
        "vote_count.gte": min_votes,
        "without_genres": "99,10755",
        "include_adult": False,
        "include_video": False,
        "language": language,
        "page": page,
        **extra,          # e.g. with_genres="878", primary_release_year=1999
    }
    r = requests.get(f"{BASE}/discover/movie", params=params, headers=H, timeout=10)
    r.raise_for_status()
    return r.json()["results"]
```

For an even fairer order, apply a Bayesian weighted rating on the client. This is your own logic, not a TMDB feature.

```python
def weighted(item, prior_votes=2000, prior_mean=6.8):
    v, R = item["vote_count"], item["vote_average"]
    return (v / (v + prior_votes)) * R + (prior_votes / (v + prior_votes)) * prior_mean
```

Read `./discover.md` for the full parameter set.

## 9. Best practices and anti-patterns

| Do this | Don't do this |
|---|---|
| Use `vote_average` with a `vote_count` floor for quality | Sort by `popularity` and call the result "best" |
| Send `region` with `now_playing` and `upcoming` | Show one country's theatre schedule to every user |
| Read the `dates` object from the response | Hard-code a release window in your code |
| Branch on `media_type` in `/trending/all` | Read `item["title"]` and crash on a TV show |
| Cache `top_rated` for a day | Cache `trending/day` for a day |
| Switch to Discover for one extra filter | Fetch 20 curated pages and filter in your app |
| Store TMDB IDs and refresh the details later | Store the whole list response as your source of truth |
| Send `timezone` to `airing_today` and `on_the_air` | Assume the server timezone matches the user |

**The biggest anti-pattern: popularity as a quality proxy.** When a user asks for "the best sci-fi films", `sort_by=popularity.desc` gives you the loudest films, not the best. Use `vote_average.desc` with a vote floor. When a user asks "what is everyone watching", popularity is the correct answer.

**Second anti-pattern: over-fetch and filter locally.** Do not pull ten pages of `/movie/popular` to keep the action films. Send `with_genres=28` to Discover. One request replaces ten.

## 10. Pitfalls and gotchas

**Cache policy.** The docs do not state TTL values. These come from how the scores update. Use them as a starting point.

| Data | Suggested TTL | Reason |
|---|---|---|
| `/trending/*/day` | 15–60 minutes | The whole value is freshness. A stale trending list is worse than no list. |
| `/trending/*/week` | 1–6 hours | It moves slower, but it is still a "now" list. |
| `movie/tv popular` | 3–12 hours | Popularity recalculates once a day. |
| `now_playing`, `airing_today`, `on_the_air` | 1–6 hours, and expire at local midnight | The date window moves each day. |
| `upcoming` | 6–24 hours | Slow, but new titles appear. |
| `top_rated` | 12–24 hours | It barely moves. |

Never cache a trending list for a day and label it "trending today". You then show yesterday.

**Re-rank breaks pagination.** Items shift between pages while you page. Expect duplicates and gaps. De-duplicate by `id`, as shown in section 7.

**`total_pages` is not a fetch budget.** TMDB caps paged endpoints at page 500, even when `total_pages` reports more. Cap your loop yourself. See `./discover.md`.

**Trending has no `page`.** Only `time_window` and `language`. If you need more items, use Discover.

**`vote_average` can be `0.0`.** Unreleased titles in `/movie/upcoming` and hot titles in trending often have `vote_count: 0`. Never render a zero-vote average as a rating – hide it or show "not rated yet".

**`popularity` values are not comparable across media types.** A movie score of 3000 and a person score of 40 mean nothing next to each other. Do not merge and re-sort the `/trending/all` results by `popularity`.

**Path fields are partial.** `poster_path` and `profile_path` are path fragments, not URLs. Build the URL with the configuration base URL and a size. See `./images-and-configuration.md`.

**A null `poster_path` is common.** Trending catches new titles before the artwork arrives. Always ship a placeholder.

**`/movie/popular` includes adult and video exclusion already.** It sets `include_adult=false` and `include_video=false`. If you build the Discover version yourself, keep both, or your list changes shape.

**`known_for` is a summary, not a filmography.** It holds up to three items and TMDB picks them. Call the person credits endpoints for the real list. See `./people-and-credits.md`.

**The list objects are thin.** They carry `genre_ids`, not genre objects, and no runtime, no cast, no videos. Fetch the detail endpoint for a full record, and use `append_to_response` to keep it to one request. See `./append-to-response.md`.

## 11. Related skill files

| File | Use it for |
|---|---|
| `./discover.md` | The full filter set behind every curated list. Read this next. |
| `./getting-started.md` | Base URL, request format, rate limits, error codes |
| `./authentication.md` | The bearer token these calls need |
| `./localization.md` | `language`, `region` and translation fallback rules |
| `./images-and-configuration.md` | Turn `poster_path` into a real image URL |
| `./movies.md` | Full details for a movie ID from a list |
| `./tv-series.md` | Full details for a TV ID, and next or last episode to air |
| `./tv-seasons-and-episodes.md` | Episode air dates behind `airing_today` and `on_the_air` |
| `./people-and-credits.md` | Real credits behind `known_for` |
| `./append-to-response.md` | Fetch details plus credits, videos and images in one call |
| `./search-and-find.md` | Find one known title instead of a chart |
| `./watch-providers.md` | Combine a popular list with "where to stream" |
| `./changes-and-exports.md` | Daily ID exports that carry historical popularity from 28 April 2017 |
| `./user-account-and-ratings.md` | Your own votes, which feed the popularity signals |
| `./lists.md` | Save a chart into a user list |
