# TMDB: Getting Started
Based on TMDB API v3 documentation (developer.themoviedb.org).

The entry point for every other TMDB skill file. Read this first, then go to the topic file you need.

## 1. Core concepts

| Fact | Value |
| :--- | :--- |
| Base URL | `https://api.themoviedb.org` |
| Path prefix | `/3` – every v3 endpoint starts with it |
| Full example | `https://api.themoviedb.org/3/movie/550` |
| Response format | JSON only. No XML. |
| Authorization | `Authorization: Bearer <access_token>` header, or `?api_key=<key>` |
| Transport | HTTPS API wide, for endpoints and for the image CDN. Use it always. |
| Read methods | `GET` |
| Write methods | `POST` and `DELETE`, plus a session id |
| Page size | 20 results per page, fixed |
| Page cap | 500. Pages start at 1. |
| Rate limit | Approximately 40 requests per second. Respect a `429`. |
| Cost | Free for non-commercial use with attribution. Commercial use needs a licence. |

Three ideas explain most of the API:

1. **Every record has an integer id per entity type.** A movie id, a TV series id and a person id are separate number spaces. The id `550` is Fight Club as a movie, and something different as a person.
2. **The API returns data, not URLs for images.** A response gives you a file path such as `/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg`. You build the full image URL yourself. See `./images-and-configuration.md`.
3. **Most responses are localized.** The `language` parameter changes the text, and `region` changes release data. See `./localization.md`.

Register a key on your TMDB account settings page. The registration pages are not optimized for mobile devices, so use a desktop browser. You must agree to the terms of use before TMDB issues a key.

## 2. The shape of a request

```
GET https://api.themoviedb.org/3/search/movie?query=Batman&language=en-US&page=1
     ^                        ^  ^                ^
     always HTTPS             |  endpoint path    query parameters
                              API version
Headers:
  Authorization: Bearer <access_token>
  accept: application/json
```

Rules for the request:

* Send `accept: application/json` on every request.
* Send `Content-Type: application/json;charset=utf-8` on every `POST`.
* URL-encode each query value. A search for `Amélie` or `Léon: The Professional` fails without it.
* Do not add a file extension to the path. TMDB removed the old `.json` suffix style.

## 3. Authorization in one minute

TMDB v3 accepts two application level methods. Both give the same access.

```bash
# Preferred: the API Read Access Token as a Bearer token.
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'

# Legacy but still supported: the api_key query parameter.
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?api_key=<api_key>' \
     --header 'accept: application/json'
```

Use the Bearer token. One token works for both the v3 and the v4 methods, and the token stays out of your URLs, your logs and your analytics.

Test a credential with the validate endpoint:

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/authentication' \
     --header 'Authorization: Bearer <access_token>'
# 200 -> {"success":true,"status_code":1,"status_message":"Success."}
# 401 -> {"status_code":7,"status_message":"Invalid API key: You must be granted a valid key.","success":false}
```

User specific actions – ratings, watchlists, favorites and private lists – need a session id in addition to the application credential. Read `./authentication.md` for request tokens, sessions and guest sessions.

## 4. Your first requests

```bash
# curl
curl -s --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?language=en-US' \
     --header "Authorization: Bearer $TMDB_TOKEN" \
     --header 'accept: application/json'
```

```python
# Python, with requests
import os, requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": f"Bearer {os.environ['TMDB_TOKEN']}",
    "accept": "application/json",
}

r = requests.get(f"{BASE}/movie/550", headers=HEADERS, params={"language": "en-US"}, timeout=10)
r.raise_for_status()
movie = r.json()
print(movie["title"], movie["release_date"])
```

```javascript
// JavaScript, server side only. Never ship the token to a browser.
const res = await fetch("https://api.themoviedb.org/3/movie/550?language=en-US", {
  headers: {
    Authorization: `Bearer ${process.env.TMDB_TOKEN}`,
    accept: "application/json",
  },
});
if (!res.ok) throw new Error(`TMDB ${res.status}: ${(await res.json()).status_message}`);
const movie = await res.json();
```

## 5. Build one client, then reuse it

Create a single client with the credential, the timeout and the retry policy in one place. Do not repeat the header block in each function.

```python
import os, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TMDB:
    BASE = "https://api.themoviedb.org/3"

    def __init__(self, token=None, language="en-US"):
        self.language = language
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token or os.environ['TMDB_TOKEN']}",
            "accept": "application/json",
        })
        retry = Retry(
            total=5,
            backoff_factor=0.5,                       # 0.5s, 1s, 2s, 4s, 8s
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),                 # never auto-retry a POST rating
            respect_retry_after_header=True,
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=20))

    def get(self, path, params=None):
        params = dict(params or {})            # a dict, so dotted keys like "vote_count.gte" work
        params.setdefault("language", self.language)
        r = self.s.get(f"{self.BASE}{path}", params=params, timeout=10)
        if not r.ok:
            body = r.json() if "application/json" in r.headers.get("content-type", "") else {}
            raise TMDBError(r.status_code, body.get("status_code"), body.get("status_message", r.text))
        return r.json()

class TMDBError(Exception):
    def __init__(self, http_status, status_code, message):
        super().__init__(f"HTTP {http_status} (status_code {status_code}): {message}")
        self.http_status, self.status_code = http_status, status_code

tmdb = TMDB()
print(tmdb.get("/movie/550")["title"])
```

Do this / Don't do this:

```python
# Do: one session, connection reuse, one place for the credential.
tmdb.get("/movie/550")

# Don't: a new connection and a hand-built URL for each call.
requests.get(f"https://api.themoviedb.org/3/movie/550?api_key={KEY}&query={title}")  # no encoding, no timeout
```

## 6. The response envelope

TMDB uses three response shapes.

**A. A single record.** The object itself, with no wrapper.

```json
{ "id": 550, "title": "Fight Club", "release_date": "1999-10-15", "vote_average": 8.433 }
```

**B. A paginated list.** Always these four keys.

```json
{ "page": 1, "results": [ /* up to 20 objects */ ], "total_pages": 38020, "total_results": 760385 }
```

**C. A status envelope.** Write endpoints and errors return it.

```json
{ "success": true, "status_code": 1, "status_message": "Success." }
```

Note the two different codes. `status_code` is a TMDB code from the table in section 8. It is not the HTTP status. Log both.

Absent data is `null`, not a missing key. Check for `None` before you use `poster_path`, `belongs_to_collection`, `imdb_id` or `runtime`.

## 7. Pagination and the 500-page cap

| Rule | Detail |
| :--- | :--- |
| `page` | Integer, starts at 1, default 1, maximum 500 |
| Page size | 20, and you cannot change it |
| Hard ceiling | 10,000 results (500 pages × 20) |
| Over the cap | HTTP 400, `status_code` 22, "Invalid page: Pages start at 1 and max at 500." |

`total_pages` often reports a much larger number than 500. A discover query can report 38,020 pages. You still cannot read past page 500. Clamp the loop yourself.

```python
def paginate(tmdb, path, params=None, max_items=None):
    """Yield results across pages, and respect the 500 page cap."""
    params = dict(params or {})
    page, yielded = 1, 0
    while page <= 500:
        data = tmdb.get(path, {**params, "page": page})
        for item in data["results"]:
            yield item
            yielded += 1
            if max_items and yielded >= max_items:
                return
        if page >= min(data["total_pages"], 500):
            return
        page += 1

for movie in paginate(tmdb, "/discover/movie", {"sort_by": "popularity.desc"}, max_items=100):
    print(movie["id"], movie["title"])
```

To read a set larger than 10,000 records, split the query into windows that each stay below the cap. Use `primary_release_date.gte` and `primary_release_date.lte` on `/discover/movie`, one month or one year per window. See `./discover.md`. For a full catalogue, do not page at all – download the daily id export files. See `./changes-and-exports.md`.

```python
# Do: partition by date, then page inside each window. Each window stays below 10,000 results.
def all_movies(tmdb, first_year=1900, last_year=2026):
    for year in range(first_year, last_year + 1):
        window = {
            "primary_release_date.gte": f"{year}-01-01",
            "primary_release_date.lte": f"{year}-12-31",
            "sort_by": "primary_release_date.asc",
        }
        yield from paginate(tmdb, "/discover/movie", window)

# Don't: trust total_pages and walk 38,020 pages. Page 501 returns HTTP 400, status_code 22.
```

## 8. Errors

Handle the HTTP status first, then read `status_code` for the reason.

```json
{ "success": false, "status_code": 7, "status_message": "Invalid API key: You must be granted a valid key." }
```

### HTTP status, and what to do

| HTTP | Meaning | Action |
| :--- | :--- | :--- |
| 200 | Success. Also used for "nothing to update" and "entry not found" on edits. | Read `status_code` on write calls. |
| 201 | The record was created or updated. | Treat as success. |
| 400 | Bad input: invalid page, invalid date, missing confirm, too many `append_to_response` objects. | Fix the request. Never retry. |
| 401 | Authentication failed, invalid or suspended key, invalid token or session. | Fix the credential. Never retry. |
| 403 | Duplicate entry, or a suspended user. | Do not retry. |
| 404 | Invalid id, or the resource does not exist. | Treat as "no data". Cache the negative result. |
| 405 | The method is not supported for this resource. | Fix the verb. |
| 406 | Invalid accept header. | Send `accept: application/json`. |
| 422 | Invalid parameters, an unapproved request token, or a date range longer than 14 days. | Fix the request. |
| 429 | Over the rate limit. | Back off, then retry. See section 9. |
| 500 | Internal error. | Retry with backoff. Report a repeat to TMDB. |
| 501 | The service does not exist. | Fix the path. |
| 502 / 504 | The backend did not answer in time. | Retry with backoff. |
| 503 | Service offline or in maintenance. | Retry later with a long backoff. |

### The TMDB `status_code` values you will meet most

| `status_code` | HTTP | Message and cause |
| :--- | :--- | :--- |
| 1 | 200 | Success. |
| 3 | 401 | Authentication failed. You lack permission for the service. |
| 6 | 404 | Invalid id. The pre-requisite id is invalid or not found. |
| 7 | 401 | Invalid API key. |
| 10 | 401 | Suspended API key. Contact TMDB. |
| 12 / 13 | 201 / 200 | The record was updated / deleted. |
| 22 | 400 | Invalid page. Pages start at 1 and max at 500. |
| 23 | 400 | Invalid date. The format is `YYYY-MM-DD`. |
| 25 | 429 | The request count is over the allowed limit. |
| 27 | 400 | Too many `append_to_response` objects. The maximum is 20. |
| 33 | 401 | Invalid request token. It expired, or it is wrong. |
| 34 | 404 | The resource could not be found. |
| 36 | 401 | The token has no write permission from the user. |
| 39 | 401 | This resource is private. |
| 41 | 422 | The user has not approved this request token. |
| 46 | 503 | The API is in maintenance. Try again later. |

```python
# Do: separate the permanent failure from the temporary one.
try:
    movie = tmdb.get(f"/movie/{movie_id}")
except TMDBError as e:
    if e.http_status == 404:
        movie = None                      # a real answer: no such movie
    elif e.http_status in (429, 500, 502, 503, 504):
        raise                             # the retry policy handles it
    else:
        log.error("permanent TMDB failure: %s", e)   # 400 and 401 need a code fix
        raise

# Don't: retry every failure in a tight loop. A 401 never becomes a 200.
```

Do not treat HTTP 200 as success on a write. Codes 21 ("Entry not found") and 40 ("Nothing to update") arrive with HTTP 200. Read `status_code`.

## 9. Rate limiting

TMDB disabled the legacy limit of 40 requests per 10 seconds on 16 December 2019. An upper limit still exists to stop bulk scraping. It sits in the range of about 40 requests per second, and TMDB can change it at any time.

What happens in practice:

* A normal application never meets the limit.
* A parallel crawler meets it quickly.
* The server answers with HTTP 429 and `status_code` 25.

```python
import time, random, requests

def get_with_backoff(session, url, params=None, max_tries=6):
    for attempt in range(max_tries):
        r = session.get(url, params=params, timeout=10)
        if r.status_code != 429:
            return r
        wait = float(r.headers.get("Retry-After", 0)) or (2 ** attempt) + random.random()
        time.sleep(wait)                  # honour Retry-After when the server sends one
    raise RuntimeError("still rate limited after retries")
```

Guidance:

* Keep concurrency low. Use 4 to 8 workers, not 100.
* Add jitter to the backoff. Synchronized retries create a second burst.
* Cache aggressively. Movie details change slowly, and configuration data changes very rarely.
* Use `append_to_response` to merge up to 20 sub-requests into one HTTP call. See `./append-to-response.md`.
* Use the daily id exports and the change endpoints for bulk work, not a page crawl. See `./changes-and-exports.md`.
* Respect a 429 even when your own counter says you are below the limit.

## 10. JSON and JSONP

JSON is the only response format. For a browser client on another domain, add the `callback` parameter. TMDB then wraps the JSON in a JavaScript function call.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/search/movie?query=Batman&callback=test' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
# -> test({"page":1,"results":[...]})
```

JSONP solves a cross-origin problem, but it does not solve the credential problem. A browser request carries your credential to the user's machine.

```
Do:    browser -> your server (session cookie) -> TMDB (your token) -> browser
Don't: browser -> TMDB with the token or api_key inside the front-end bundle
```

Build a thin proxy on your own server. Add caching there, and keep the token secret.

## 11. Attribution, terms and commercial use

TMDB requires attribution from every application.

* Place this notice prominently in your application: **"This product uses the TMDB API but is not endorsed or certified by TMDB."**
* Put the attribution in the "About" or "Credits" section.
* Use the TMDB logo to identify your use of the API. Use one of the approved logos from the logos and attribution page.
* Keep the TMDB logo less prominent than your own logo or mark.
* Do not change the logo colour, aspect ratio, or rotation, and do not flip it.
* Call the service "TMDB" or "The Movie Database". No other name is acceptable.
* Link back to `https://www.themoviedb.org`.
* Ask TMDB first before you put the name or logo on merchandise or on product packaging.

Licence and service facts that affect a business decision:

| Question | Answer |
| :--- | :--- |
| Cost | Free for non-commercial use, with attribution. |
| Commercial use | A project is commercial when its primary purpose is revenue for the owner. Contact `sales@themoviedb.org`, and name your country. |
| SLA | None. TMDB publishes a status page at `https://status.themoviedb.org`. |
| SSL | Available API wide, for endpoints and for the CDN. TMDB strongly recommends it. |
| Ownership | TMDB does not claim ownership of the images or the data, and it follows the DMCA. |
| Content rules | Do not use the data or the images with libelous, obscene or abusive content. |
| Source | The API is closed source. You cannot change it. |

## 12. Wrapper libraries

TMDB lists community libraries. There is no official first-party SDK. Pick one for the boilerplate, but keep the endpoint reference open – a wrapper often lags behind the API.

| Language | Libraries |
| :--- | :--- |
| Python | `tmdbsimple` (celiao), `tmdb3`, `pytmdb3` |
| JavaScript | `moviedb-promise` (grantholle), `themoviedb-javascript-library`, `tmdb-js`, `node-tmdb` |
| TypeScript | `tmdb-ts` (blakejoy), `tmdb` (lorenzopant), `tmdb` (leandrowkz) |
| C# | `TMDbLib` (LordMike), `TheMovieDbWrapper`, `TmdbEasy` |
| Java | `api-themoviedb` (Omertron), `themoviedbapi` (c-eg) |
| PHP | `php-tmdb-api` (wtfzdotnet), `WtfzTmdbBundle` for Symfony |
| Go | `golang-tmdb` (cyruzin), `go-tmdb` (ryanbradynd05) |
| Ruby | `themoviedb-api` (18Months), `themoviedb` (ahmetabdi) |
| Swift / iOS | `TMDb` (adamayoung), `TheMovieDatabaseSwiftWrapper`, `TMDBSwifty` |
| Dart | `tmdb_api` (Ratakondala Arun), `tmdb` (Josep Sayol) |
| Rust | `tmdb-client-rs` (bcourtine) |
| Other | C, C++, Clojure, ColdFusion, Delphi, Haskell, Julia, mSL, Perl, and an MCP server (`mcp-tmdb`) |

Check three things before you adopt a wrapper: recent commits, Bearer token support, and `append_to_response` support. A raw `requests` or `fetch` client of 50 lines is often the better choice.

## 13. Roadmap and FAQ items that change how you build

* **The API changes over time.** TMDB posts updates in the documentation and tracks work on a public Trello board. Do not fail a parse when a new field appears. Read the fields you need, and ignore the rest.
* **There is no SLA.** Add a timeout, a retry, and a cache to every call. Degrade the page instead of an error when TMDB is offline.
* **Vote for features on the Trello board.** Report a bug or a missing feature on the API support forum.
* **The API is closed source.** Do not plan around a change you cannot make. Build a fallback instead.
* **Configuration is not static forever.** Fetch `/3/configuration` at start up and cache it for a few days. Do not hardcode the image base URL. See `./images-and-configuration.md`.

## 14. Global parameters you will use everywhere

| Parameter | Type | Default | Notes |
| :--- | :--- | :--- | :--- |
| `language` | string | `en-US` | ISO 639-1, plus an optional region: `pt-BR`. See `./localization.md`. |
| `region` | string | – | ISO 3166-1, uppercase. Changes release dates and providers. |
| `page` | integer | 1 | Maximum 500. |
| `append_to_response` | string | – | Comma separated sub-requests, maximum 20. See `./append-to-response.md`. |
| `include_adult` | boolean | `false` | Adult titles stay out unless you opt in. |
| `include_image_language` | string | – | Image language fallback, for example `en,null`. |
| `callback` | string | – | JSONP wrapper function name. |
| `session_id` | string | – | User session, for account actions. |
| `guest_session_id` | string | – | Guest session, for ratings without a login. |

## 15. First endpoints to know

| Endpoint | Purpose | Skill file |
| :--- | :--- | :--- |
| `GET /3/authentication` | Validate your credential | `./authentication.md` |
| `GET /3/configuration` | Image base URL and sizes, static lists | `./images-and-configuration.md` |
| `GET /3/search/multi?query=` | Find a movie, a series or a person by name | `./search-and-find.md` |
| `GET /3/find/{external_id}?external_source=imdb_id` | Map an IMDb or a TVDB id to a TMDB id | `./search-and-find.md` |
| `GET /3/movie/{movie_id}` | Movie details | `./movies.md` |
| `GET /3/tv/{series_id}` | TV series details | `./tv-series.md` |
| `GET /3/tv/{series_id}/season/{season_number}` | Season and episode data | `./tv-seasons-and-episodes.md` |
| `GET /3/person/{person_id}` | Person details and credits | `./people-and-credits.md` |
| `GET /3/discover/movie` | Filtered and sorted browse | `./discover.md` |
| `GET /3/trending/all/day` | Trending across types | `./trending-and-popular.md` |
| `GET /3/movie/{movie_id}/watch/providers` | Streaming availability | `./watch-providers.md` |
| `GET /3/account/{account_id}` | The signed-in user | `./user-account-and-ratings.md` |
| `GET /3/list/{list_id}` | A user list | `./lists.md` |
| `GET /3/movie/changes` | Recently changed ids | `./changes-and-exports.md` |

## 16. Where to go next

* Credentials, sessions, guest sessions and v4 tokens: `./authentication.md`
* Build image URLs and cache the configuration: `./images-and-configuration.md`
* Languages, regions, translations and fallbacks: `./localization.md`
* Merge up to 20 sub-requests into one call: `./append-to-response.md`
* Movie data, credits, videos and release dates: `./movies.md`
* Series data: `./tv-series.md` and `./tv-seasons-and-episodes.md`
* Cast, crew and filmographies: `./people-and-credits.md`
* Name lookup and external id lookup: `./search-and-find.md`
* Filtered browse and catalogue partition: `./discover.md`
* Trending, popular and the popularity metric: `./trending-and-popular.md`
* Collections, companies, networks, keywords, genres, reviews and certifications: `./entities.md`
* Ratings, favorites and watchlists: `./user-account-and-ratings.md`
* Create and edit lists: `./lists.md`
* Streaming availability by region: `./watch-providers.md`
* Daily id exports and change tracking for a local copy: `./changes-and-exports.md`

## 17. Checklist before you ship

1. Move the token to an environment variable. Keep it off the client.
2. Send `accept: application/json`, and set a timeout on every call.
3. Clamp `page` to 500, and never trust `total_pages`.
4. Handle 401, 404 and 429 as three different outcomes.
5. Add exponential backoff with jitter for 429 and 5xx.
6. Cache configuration, genres and detail records.
7. Add the attribution notice and an approved TMDB logo.
8. Check `null` on every optional field before you render it.
