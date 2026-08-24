# TMDB: Change Tracking and Daily ID Exports
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

TMDB gives you two different tools to keep a local copy of the catalogue in sync. Use both together. They do different jobs.

| Tool | Purpose | Transport | Contains |
| :--- | :--- | :--- | :--- |
| Daily ID exports | Seed and audit the full ID space | Static gzip files on `files.tmdb.org` – no API call, no auth | Every valid ID, plus a few filter fields |
| Change lists | Find which IDs changed in a period | API: `/movie/changes`, `/tv/changes`, `/person/changes` | IDs only |
| Per-item changes | See which fields changed on one item | API: `/{type}/{id}/changes` | Field-level change log |

The mental model is simple. Download the export once to learn every ID that exists. Poll the change lists each day to learn which IDs moved. Re-fetch the details of those IDs from the normal detail endpoints.

Never treat the change endpoints as a data feed. They tell you *what* changed. They do not give you a reliable full record of the new state.

---

## 2. Daily ID exports

### 2.1 The URL pattern

```
https://files.tmdb.org/p/exports/{type}_ids_MM_DD_YYYY.json.gz
```

The date uses US ordering with underscores and a zero-padded two-digit month and day, for example `10_25_2025`. The date is the publication date, not a data range.

| Export type | File name |
| :--- | :--- |
| Movies | `movie_ids_MM_DD_YYYY.json.gz` |
| TV series | `tv_series_ids_MM_DD_YYYY.json.gz` |
| People | `person_ids_MM_DD_YYYY.json.gz` |
| Collections | `collection_ids_MM_DD_YYYY.json.gz` |
| TV networks | `tv_network_ids_MM_DD_YYYY.json.gz` |
| Keywords | `keyword_ids_MM_DD_YYYY.json.gz` |
| Production companies | `production_company_ids_MM_DD_YYYY.json.gz` |

TMDB also publishes adult data sets in the same directory: `adult_movie_ids_MM_DD_YYYY.json.gz`, `adult_tv_series_ids_MM_DD_YYYY.json.gz` and `adult_person_ids_MM_DD_YYYY.json.gz`.

### 2.2 Timing, retention and access

- The export job starts at about **07:00 UTC**. All files are ready by **08:00 UTC**. Download after 08:00 UTC, or download yesterday's file.
- TMDB keeps each file for **3 months**, then deletes it automatically.
- The files need **no authentication** today. TMDB warns that this can change. Send your API credentials only to `api.themoviedb.org`, never to `files.tmdb.org`.

### 2.3 The file format

The file is gzip. The decompressed content is **JSON Lines**, not one JSON document. Each line is one complete JSON object. Read the file line by line and parse each line on its own.

```jsonc
// movie_ids_*.json.gz
{"adult":false,"id":3924,"original_title":"Blondie","popularity":1.036,"video":false}
// tv_series_ids_*.json.gz
{"id":1399,"original_name":"Game of Thrones","popularity":242.6}
// person_ids_*.json.gz
{"adult":false,"id":31,"name":"Tom Hanks","popularity":18.4}
// collection_ids_*, keyword_ids_*, tv_network_ids_*, production_company_ids_*
{"id":10,"name":"Star Wars Collection"}
```

| Field | Where it appears | Use it for |
| :--- | :--- | :--- |
| `id` | Every export | The primary key. This is the only field you must keep. |
| `original_title` | Movies | A human label for logs and debugging. |
| `original_name` | TV series | A human label for logs and debugging. |
| `name` | People, collections, keywords, networks, companies | A human label. |
| `popularity` | Movies, TV, people | Sort the seed queue. Fetch popular items first. |
| `adult` | Movies, people | Filter out adult items before you fetch them. |
| `video` | Movies | Filter out video-only records if you only want theatrical titles. |

The export is a **list of valid IDs with filter hints**. It is not a data export. It has no titles in other languages, no overviews, no images and no credits. Fetch those from the API.

### 2.4 Download and read the export

```bash
# Build yesterday's date to be safe about the 08:00 UTC publication time.
DATE=$(date -u -d "yesterday" +%m_%d_%Y 2>/dev/null || date -u -v-1d +%m_%d_%Y)
curl -fsSL "https://files.tmdb.org/p/exports/movie_ids_${DATE}.json.gz" -o movie_ids.json.gz

# Count the IDs without unpacking the file to disk.
gzip -dc movie_ids.json.gz | wc -l

# Extract only the non-adult, non-video IDs.
gzip -dc movie_ids.json.gz | jq -r 'select(.adult == false and .video == false) | .id' > movie_ids.txt
```

Stream the file in Python. Do not load it into memory.

```python
import gzip, json, datetime as dt, requests

BASE_EXPORT = "https://files.tmdb.org/p/exports"

def export_url(kind: str, day: dt.date | None = None) -> str:
    """kind: movie | tv_series | person | collection | tv_network | keyword | production_company"""
    day = day or (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1))
    return f"{BASE_EXPORT}/{kind}_ids_{day:%m_%d_%Y}.json.gz"

def iter_export(kind: str, day: dt.date | None = None):
    """Yield one dict per line. Memory stays flat for a 600 MB file."""
    url = export_url(kind, day)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with gzip.open(r.raw, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

# Seed the local table with the most popular titles first.
rows = [m for m in iter_export("movie") if not m.get("adult") and not m.get("video")]
for movie in sorted(rows, key=lambda m: m["popularity"], reverse=True):
    upsert_movie_stub(movie["id"], movie["original_title"], movie["popularity"])
```

### 2.5 Do this / Don't do this

| Do this | Don't do this |
| :--- | :--- |
| Seed your database from the daily export. | Do not walk IDs from 1 to N and call the detail endpoint for each. Most IDs do not exist. You waste days of requests and hit the rate limit. |
| Stream the gzip line by line. | Do not read the whole file into a string and call `json.loads` on it. The file is not one JSON document. |
| Download the file for yesterday, or after 08:00 UTC. | Do not download today's file at 03:00 UTC. It does not exist yet. |
| Re-download the export weekly or monthly to find deleted IDs. | Do not keep an ID forever after it disappears from the export. |
| Sort your seed queue by `popularity`. | Do not fetch 1 million detail records in random order and stop halfway. |

---

## 3. Change lists – which IDs changed

Three endpoints return changed IDs. They have identical parameters and identical response shapes.

| Endpoint | Returns |
| :--- | :--- |
| `GET /3/movie/changes` | Movie IDs changed in the window |
| `GET /3/tv/changes` | TV series IDs changed in the window |
| `GET /3/person/changes` | Person IDs changed in the window |

| Parameter | Type | Default | Notes |
| :--- | :--- | :--- | :--- |
| `start_date` | `YYYY-MM-DD` | 24 hours ago | The start of the window. |
| `end_date` | `YYYY-MM-DD` | now | The end of the window. |
| `page` | integer | `1` | 100 results per page. |

**The window has a hard maximum of 14 days.** Omit both dates to get the last 24 hours.

```bash
curl -s --request GET \
  --url 'https://api.themoviedb.org/3/movie/changes?start_date=2026-08-20&end_date=2026-08-22&page=1' \
  --header 'Authorization: Bearer YOUR_READ_ACCESS_TOKEN' \
  --header 'accept: application/json'
```

The response gives IDs only:

```json
{
  "results": [{"id": 1120293, "adult": false}, {"id": 3686, "adult": false}, {"id": 1120298, "adult": null}],
  "page": 3,
  "total_pages": 57,
  "total_results": 5700
}
```

Note two things. The `adult` flag can be `null`. There is no title, no timestamp and no field data. You must call another endpoint to learn what changed.

### 3.1 Page through the whole window

```python
import requests, time

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": "Bearer YOUR_READ_ACCESS_TOKEN", "accept": "application/json"}

def get(path: str, **params) -> dict:
    """One GET with a retry for HTTP 429."""
    for attempt in range(5):
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 1)) + 1)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"{path} failed after 5 attempts")

def changed_ids(media: str, start_date: str, end_date: str) -> set[int]:
    """media: movie | tv | person"""
    ids, page, total = set(), 1, 1
    while page <= total:
        data = get(f"/{media}/changes", start_date=start_date, end_date=end_date, page=page)
        total = data["total_pages"]
        ids.update(row["id"] for row in data["results"])
        page += 1
    return ids

print(len(changed_ids("movie", "2026-08-20", "2026-08-22")))
```

```javascript
// JavaScript: collect every page of the movie change list.
async function changedIds(media, startDate, endDate, token) {
  const ids = new Set();
  let page = 1, totalPages = 1;
  while (page <= totalPages) {
    const url = new URL(`https://api.themoviedb.org/3/${media}/changes`);
    url.search = new URLSearchParams({ start_date: startDate, end_date: endDate, page });
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    totalPages = data.total_pages;
    data.results.forEach((row) => ids.add(row.id));
    page += 1;
  }
  return ids;
}
```

### 3.2 Gotchas for the change lists

- The lists cover movies, TV series and people **only**. There is no change list for collections, keywords, networks or companies. Refresh those from the daily export.
- A TV series ID appears in `/tv/changes` when a season or an episode changes. Re-fetch the series, then look at its season and episode data.
- The list gives no reason and no timestamp. Treat every returned ID as "dirty" and re-fetch it. `total_results` can reach several thousand per day.

---

## 4. Per-item change endpoints – which fields changed

| Endpoint | Path parameter | Important |
| :--- | :--- | :--- |
| `GET /3/movie/{movie_id}/changes` | `movie_id` | |
| `GET /3/tv/{series_id}/changes` | `series_id` | Season and episode edits appear here under the `season` and `episode` keys. |
| `GET /3/tv/season/{season_id}/changes` | `season_id` | **Not** the season number. |
| `GET /3/tv/episode/{episode_id}/changes` | `episode_id` | **Not** the episode number. |
| `GET /3/person/{person_id}/changes` | `person_id` | |

All of them accept `start_date`, `end_date` and `page`, with the same 24-hour default and the same 14-day maximum. (The reference block for the episode endpoint lists only `episode_id`, but the documented behaviour is the same. Send the dates and check the result.)

### 4.1 Season and episode IDs are not ordinals

This is the most common mistake. `/tv/season/{season_id}/changes` needs the internal `season_id` (for example `3624`). It does **not** accept the season number (`1`). The same rule applies to `episode_id`.

```python
# Don't do this – 1 is a season NUMBER, not a season ID.
get("/tv/season/1/changes")            # wrong item, or 404

# Do this – read the real IDs from the series detail response first.
series = get("/tv/1399", append_to_response="season/1")
season_ids = {s["season_number"]: s["id"] for s in series["seasons"]}
get(f"/tv/season/{season_ids[1]}/changes")
```

Get `season_id` from the `seasons` array of the series detail response. Get `episode_id` from the `episodes` array of the season detail response. See `./tv-seasons-and-episodes.md` and `./append-to-response.md`.

The series-level change response also hands you the IDs directly. Items under the `season` and `episode` keys carry a `series_id` and an `episode_id` in their `value` object.

```bash
curl -s --request GET \
  --url 'https://api.themoviedb.org/3/movie/550/changes?start_date=2026-08-17' \
  --header 'Authorization: Bearer YOUR_READ_ACCESS_TOKEN'
```

### 4.2 The response shape

```json
{
  "changes": [
    {
      "key": "images",
      "items": [
        {
          "id": "640435cf021cee0084710972",
          "action": "updated",
          "time": "2023-03-05 06:25:19 UTC",
          "iso_639_1": "en",
          "iso_3166_1": "",
          "value": {"poster": {"file_path": "/ouudK6RCNnsbT1CSXrlATXQIQTG.jpg", "iso_639_1": "en"}},
          "original_value": {"poster": {"file_path": "/ouudK6RCNnsbT1CSXrlATXQIQTG.jpg", "iso_639_1": "fr"}}
        }
      ]
    },
    {"key": "plot_keywords", "items": [{"id": "6431bb5d…", "action": "added", "time": "2023-04-08 19:07:09 UTC", "value": {"name": "breaking the fourth wall", "id": 11687}}]}
  ]
}
```

| Field | Meaning |
| :--- | :--- |
| `key` | The field group that changed, for example `images`, `overview`, `title`, `air_date`, `plot_keywords`, `translations`, `season`, `episode`. |
| `items[].id` | The change record ID – a 24-character hex string, not an entity ID. Use it to de-duplicate. |
| `items[].action` | `added`, `updated`, `deleted` or `destroyed`. |
| `items[].time` | The UTC timestamp, formatted `YYYY-MM-DD HH:MM:SS UTC`. This is not ISO 8601. Parse it explicitly. |
| `items[].value` | The new value. A string, a number or an object, depending on the key. |
| `items[].original_value` | The previous value. Present on `updated` items only. |
| `items[].iso_639_1` | The language of the changed field. Empty when the change is language-neutral. |
| `items[].iso_3166_1` | The region of the changed field. Empty when the change is region-neutral. |

Season-level and episode-level responses use the same shape. Season keys include `episode`, `air_date`, `name` and `overview`. Episode keys include `name`, `overview` and `production_code`.

### 4.3 Use the per-item endpoint for triage, not for data

```python
INTERESTING = {"images", "videos", "title", "overview", "release_dates", "runtime", "cast", "crew"}

def worth_refetching(movie_id: int, start_date: str) -> bool:
    """Skip a full re-fetch when only fields you do not store changed."""
    data = get(f"/movie/{movie_id}/changes", start_date=start_date)
    keys = {block["key"] for block in data["changes"]}
    return bool(keys & INTERESTING)
```

This saves requests when you store a small subset of the fields. It costs one extra request per ID. Use it only when the filter removes most of the work. Otherwise, re-fetch the detail record directly.

---

## 5. Recommended sync architecture

Follow this procedure.

1. **Seed.** Download the daily ID export for each type you need. Insert one stub row per ID. Record the export date.
2. **Backfill.** Fetch the detail record for each stub, in `popularity` order. Use `append_to_response` to collect images, credits and videos in one request. See `./append-to-response.md`.
3. **Poll.** Run a job once per day, after 08:00 UTC. Call the three change lists for the window since the last successful run.
4. **Re-fetch.** For each changed ID, call the detail endpoint again with the same `append_to_response` set. Overwrite the stored record.
5. **Record.** Save the end date of the window only after the job succeeds. Use that date as the next `start_date`.
6. **Audit.** Re-download the export weekly. Insert IDs that are new. Mark IDs that disappeared as deleted.

### 5.1 A complete daily sync job

```python
"""Daily TMDB sync. Run once per day after 08:00 UTC."""
import datetime as dt, json, pathlib, time, requests

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": "Bearer YOUR_READ_ACCESS_TOKEN", "accept": "application/json"}
STATE = pathlib.Path("tmdb_sync_state.json")
MAX_WINDOW_DAYS = 14

APPEND = {
    "movie": "images,videos,credits,release_dates,external_ids",
    "tv": "images,videos,aggregate_credits,content_ratings,external_ids",
    "person": "images,combined_credits,external_ids",
}

session = requests.Session()
session.headers.update(HEADERS)


def get(path: str, **params) -> dict:
    for attempt in range(5):
        r = session.get(f"{BASE}{path}", params=params, timeout=30)
        if r.status_code == 429:                     # rate limited – wait and retry
            time.sleep(int(r.headers.get("Retry-After", 1)) + 1)
            continue
        if r.status_code == 404:                     # deleted or merged ID
            return {}
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"{path} failed after 5 attempts")


def changed_ids(media: str, start: dt.date, end: dt.date) -> set[int]:
    ids, page, total = set(), 1, 1
    while page <= total:
        data = get(f"/{media}/changes",
                   start_date=start.isoformat(), end_date=end.isoformat(), page=page)
        total = data.get("total_pages", 1)
        ids.update(row["id"] for row in data.get("results", []))
        page += 1
    return ids


def refetch(media: str, item_id: int) -> None:
    path = {"movie": f"/movie/{item_id}", "tv": f"/tv/{item_id}", "person": f"/person/{item_id}"}[media]
    record = get(path, append_to_response=APPEND[media], language="en-US")
    if not record:
        mark_deleted(media, item_id)                 # 404 – the ID went away
        return
    upsert(media, record)                            # overwrite the whole row


def run() -> None:
    today = dt.datetime.now(dt.timezone.utc).date()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    last = dt.date.fromisoformat(state.get("last_synced", (today - dt.timedelta(days=1)).isoformat()))

    if (today - last).days > MAX_WINDOW_DAYS:
        # The gap is larger than the change window. The change lists cannot close it.
        raise SystemExit(f"Gap of {(today - last).days} days. Re-seed from the daily ID export.")

    start = last - dt.timedelta(days=1)              # overlap one day – changes are idempotent
    for media in ("movie", "tv", "person"):
        ids = changed_ids(media, start, today)
        print(f"{media}: {len(ids)} changed IDs")
        for item_id in sorted(ids):
            refetch(media, item_id)

    STATE.write_text(json.dumps({"last_synced": today.isoformat()}))
```

Key points in the script. It overlaps the window by one day, because a re-fetch is idempotent and a missed ID is not. It writes the state file only at the end, so a crash repeats the day instead of skipping it. It stops and demands a re-seed when the gap is larger than 14 days. It treats a 404 as a deletion.

### 5.2 Do this / Don't do this

| Do this | Don't do this |
| :--- | :--- |
| Re-fetch the full detail record for each changed ID. | Do not patch your row from `value` and `original_value`. |
| Write the sync cursor after the job succeeds. | Do not write the cursor before you process the IDs. |
| Overlap the window by one day. | Do not use an exact `start_date = last_end` boundary and trust it. |
| Combine sub-resources with `append_to_response`. | Do not call `/movie/{id}`, `/movie/{id}/images` and `/movie/{id}/credits` as three requests. |
| Batch the changed IDs and process them with a small worker pool. | Do not open 200 parallel connections. |

---

## 6. Pitfalls and gotchas

**Change data is not a complete diff.** The `changes` array records the edits that TMDB logged. It can omit derived fields, and `original_value` is not always present. Re-fetch the item. Do not reconstruct the new state from the change log.

**The 14-day window is a hard wall.** A request for a longer range fails or returns a truncated result. If your job stops for more than 14 days, the change lists cannot recover the gap. Re-seed from the daily export and re-fetch everything you care about.

**Deleted and merged IDs return 404.** TMDB removes duplicates and merges records. An ID in your database can stop working. Handle `404` and `status_code: 34` ("The resource you requested could not be found"). Mark the row as deleted. Confirm the deletion with the next daily export.

**The export is a snapshot, not a diff.** Two exports on two days share almost every line. Compare the ID sets to find additions and deletions. Do not re-fetch every ID after each export.

**Time format.** Change timestamps read `2023-04-08 16:35:05 UTC`, not ISO 8601. Parse them with `datetime.strptime(value, "%Y-%m-%d %H:%M:%S UTC")` and attach the UTC timezone.

**Rate limiting during a large sync.** A first seed of the movie catalogue is hundreds of thousands of requests. Keep concurrency low, respect `Retry-After` on HTTP 429, and use one `requests.Session` so connections stay open. See `./getting-started.md` for the limits and the error codes.

**Language.** A change item with `iso_639_1: "fr"` touched the French translation only. If you store one language, ignore it. If you store many, re-fetch with `append_to_response=translations`. See `./localization.md`.

**Image paths.** A change under the `images` key gives a `file_path` only. Build the full URL from the configuration base URL. See `./images-and-configuration.md`.

**Adult content.** Both the export lines and the change list rows carry `adult`, and it can be `null`. Treat `null` as unknown, not as `false`, if your product must exclude adult titles.

---

## 7. Related skill files

| File | Why you need it here |
| :--- | :--- |
| `./getting-started.md` | Base URL, rate limits, HTTP status and TMDB error codes during a large sync. |
| `./authentication.md` | The Bearer read access token used by every change endpoint. The export files need no token. |
| `./append-to-response.md` | Collect images, credits and videos in one re-fetch request. |
| `./movies.md` | The `/movie/{id}` detail endpoint you call after a change. |
| `./tv-series.md` | The `/tv/{id}` detail endpoint, and the `seasons` array that holds each `season_id`. |
| `./tv-seasons-and-episodes.md` | The source of `season_id` and `episode_id` for the season and episode change endpoints. |
| `./people-and-credits.md` | The `/person/{id}` detail endpoint. |
| `./images-and-configuration.md` | Build full image URLs from a changed `file_path`. |
| `./localization.md` | Understand `iso_639_1` and `iso_3166_1` on each change item. |
| `./entities.md` | Collections, keywords, networks and companies – exported daily, but with no change list. |
| `./discover.md`, `./trending-and-popular.md` | Alternatives to a full mirror when you only need filtered or ranked result sets. |
