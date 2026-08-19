# Letterboxd API: Search, News and Featured Content
Based on Letterboxd API v0 documentation.

The base URL is `https://api.letterboxd.com/api/v0`. Send `Authorization: Bearer [TOKEN]` on every request. Read authentication.md for the token flow. An application token is sufficient for these four endpoints. Add a member token when you want member relationship data in the film results.

## At a glance

| Endpoint | Method | Operation ID | Response schema | First Party only |
|---|---|---|---|---|
| `/search` | GET | `search` | `SearchResponse` | No |
| `/films/autocomplete` | GET | `autocompleteFilms` | `FilmsAutocompleteResponse` | No, but **DEPRECATED** |
| `/news` | GET | `recentNews` | `NewsResponse` | No |
| `/featured-content` | GET | `featuredContent` | `FeaturedContentResponse` | No |

No parameter of these four endpoints carries a First Party mark. The restriction applies to some fields inside the returned entities. Read "First Party fields" below.

## GET /search

One endpoint searches films, members, lists, reviews, tags, contributors, stories, articles, podcasts and shows.

| Parameter | Type | Required | Default | What it does |
|---|---|---|---|---|
| `input` | string | **Yes** | – | The word, the partial word or the phrase to search for. URL-encode it. |
| `searchMethod` | enum | No | `FullText` | Selects the match mode. Values: `FullText`, `Autocomplete`, `NamesAndKeywords`. |
| `include` | `SearchResultType[]` | No | all types | Limits the result types. Exploded form style: repeat the key for each value. |
| `contributionType` | `ContributionType` | No | – | Filters contributors by role. It implies `include=ContributorSearchItem`. |
| `adult` | boolean | No | `false` | Set to `true` to include adult content. |
| `excludeMemberFilmRelationships` | boolean | No | `false` | Set to `true` to drop the member/film relationship blocks. It makes the response smaller. |
| `cursor` | string | No | – | The pagination cursor. Copy it from the `next` field of the last page. |
| `perPage` | int32 | No | `20` | The number of items per page. The maximum is `100`. |

Status 200 returns a `SearchResponse`. Status 400 returns an `ErrorResponse` when the search fails.

```bash
curl -sS -G 'https://api.letterboxd.com/api/v0/search' \
  -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' \
  --data-urlencode 'input=parasite' --data-urlencode 'searchMethod=Autocomplete' \
  --data-urlencode 'include=FilmSearchItem' --data-urlencode 'perPage=5'
```

`ContributionType` accepts these values: `Director`, `CoDirector`, `Actor`, `Producer`, `Writer`, `OriginalWriter`, `Story`, `Casting`, `Editor`, `Cinematography`, `AssistantDirector`, `AdditionalDirecting`, `ExecutiveProducer`, `Lighting`, `CameraOperator`, `AdditionalPhotography`, `ProductionDesign`, `ArtDirection`, `SetDecoration`, `SpecialEffects`, `VisualEffects`, `TitleDesign`, `Stunts`, `Choreography`, `Composer`, `Songs`, `Sound`, `Costumes`, `Creator`, `MakeUp`, `Hairstyling`, `Studio`.

## The polymorphic response

`SearchResponse` holds three fields.

| Field | Type | Notes |
|---|---|---|
| `items` | `AbstractSearchItem[]` | **Required.** The list of results. Every item has a different shape. |
| `next` | string | The cursor to the next page. The field is absent on the last page. |
| `itemCount` | int32 | The number of items. |

`AbstractSearchItem` is an abstract type. It gives two fields to every result.

| Field | Type | Notes |
|---|---|---|
| `score` | number | **Required.** A relevancy value. Use it to order results. It is not a percentage. |
| `type` | string | **The discriminator.** It names the concrete result type. |

Read `type` first. Then read the payload field that belongs to that type. Never assume that a result is a film.

| `type` (SearchResultType) | Payload key | Payload schema | Read more |
|---|---|---|---|
| `FilmSearchItem` | `film` | `FilmSummary` | films.md |
| `MemberSearchItem` | `member` | `MemberSummary` | members.md |
| `ListSearchItem` | `list` | `ListSummary` | lists.md |
| `ReviewSearchItem` | `review` | log entry entity | log-entries.md |
| `TagSearchItem` | `tag` | `Tag` | lists.md, log-entries.md |
| `ContributorSearchItem` | `contributor` | `ContributorSummary` | films.md |
| `StorySearchItem` | `story` | `StorySummary` | schemas-entities.md |
| `ArticleSearchItem` | `article` | `NewsItem` | this file |
| `PodcastSearchItem` | `podcast` | `NewsItem` | this file |
| `ShowSearchItem` | `show` | show summary | films.md |

**Warning.** The reference lists the ten `type` values, but it leaves the subtype property tables empty. The payload keys in the table above follow the API convention. Confirm each key against a live response before you ship. This command prints the real keys for each type:

```bash
curl -sS -G 'https://api.letterboxd.com/api/v0/search' -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'input=kurosawa' --data-urlencode 'perPage=100' \
  | jq -r '.items[] | "\(.type): \(keys - ["type","score"] | join(", "))"' | sort -u
```

### Handle every type in Python

```python
HANDLERS = {
    "FilmSearchItem": lambda i: f"Film: {i['film']['name']} ({i['film'].get('releaseYear', '?')}) lid={i['film']['id']}",
    "MemberSearchItem": lambda i: f"Member: @{i['member']['username']} lid={i['member']['id']}",
    "ListSearchItem": lambda i: f"List: {i['list']['name']} ({i['list']['filmCount']} films)",
    "ReviewSearchItem": lambda i: f"Review: lid={i['review']['id']}",
    "TagSearchItem": lambda i: f"Tag: {i['tag']['displayTag']} code={i['tag']['code']}",
    "ContributorSearchItem": lambda i: f"Person: {i['contributor']['name']} lid={i['contributor']['id']}",
    "StorySearchItem": lambda i: f"Story: {i['story']['name']} by @{i['story']['author']['username']}",
    "ArticleSearchItem": lambda i: f"Article: {i['article']['title']} {i['article']['url']}",
    "PodcastSearchItem": lambda i: f"Podcast: {i['podcast']['title']} {i['podcast']['url']}",
    "ShowSearchItem": lambda i: f"Show: {i['show']['name']} lid={i['show']['id']}",
}

def summarise(item):
    """Make a short label for one search result."""
    handler = HANDLERS.get(item["type"])
    # Letterboxd adds new result types. Do not raise an error on an unknown type.
    if handler is None:
        return f"[skipped unknown type {item['type']}]"
    return handler(item)

for result in sorted(page["items"], key=lambda i: -i["score"]):
    print(summarise(result))
```

## Search method options

| `searchMethod` | What it matches | Documented |
|---|---|---|
| `FullText` (default) | Text in all fields. It reads review bodies, list descriptions and bios. | Yes |
| `Autocomplete` | Primary fields only. It matches names and titles, and it matches a partial word. | Yes |
| `NamesAndKeywords` | Names plus keyword fields. | The reference gives no description. Test it before you depend on it. |

`FullText` gives recall. `Autocomplete` gives speed and precision. Pick `Autocomplete` for every box that runs while the member types.

| I want to | Use this |
|---|---|
| Turn a typed title into a film LID | `searchMethod=Autocomplete&include=FilmSearchItem` |
| Fill a type-ahead box | `searchMethod=Autocomplete`, `perPage=8`, `excludeMemberFilmRelationships=true` |
| Find a member by username | `searchMethod=Autocomplete&include=MemberSearchItem` |
| Find a director by name | `contributionType=Director` (it implies `include=ContributorSearchItem`) |
| Find reviews that mention a phrase | `searchMethod=FullText&include=ReviewSearchItem` |
| Find lists about a subject | `searchMethod=FullText&include=ListSearchItem` |
| Match a tag | `include=TagSearchItem` |

## /search vs /films/autocomplete

`/films/autocomplete` is **DEPRECATED**. The reference tells you to call `/search?input={input}&searchMethod=Autocomplete&include=FilmSearchItem` instead.

| | `/search` | `/films/autocomplete` |
|---|---|---|
| Status | Current | **DEPRECATED** |
| Result types | All ten types | Films only |
| Item shape | `AbstractSearchItem` with a `type` discriminator | Flat `FilmSummary` objects |
| Pagination | `cursor` plus `next` | None. It returns up to 100 films. |
| `perPage` | Default 20, maximum 100 | Default 20, maximum 100 |
| Match modes | Three (`FullText`, `Autocomplete`, `NamesAndKeywords`) | Prefix match only |

Use `/search` for new code. The flat response of `/films/autocomplete` is easier to parse, and that is its only advantage. Keep the old endpoint only in a client that already ships it, and migrate that client at the next release. `/films/autocomplete` cannot paginate, cannot search members, lists, reviews, tags or people, cannot do a full-text search, and cannot filter by contribution type.

## Practical patterns

A small helper carries the token and the encoding for every example below.

```python
import time, requests
API_BASE = "https://api.letterboxd.com/api/v0"

def api_get(token, path, params):
    """Call one GET endpoint. The requests library URL encodes the params."""
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=15,
                     headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    r.raise_for_status()
    return r.json()
```

Pass a list for `include`, such as `{"include": ["FilmSearchItem", "ContributorSearchItem"]}`. The library then repeats the key, which is the exploded form the API needs.

### Pattern 1: resolve a typed title into a film LID

```python
def film_lid(token, title):
    """Return the LID of the best film match, or None."""
    page = api_get(token, "/search", {
        "input": title, "searchMethod": "Autocomplete", "include": "FilmSearchItem",
        # Send the string "true". Python True becomes "True", which the API rejects.
        "perPage": 5, "excludeMemberFilmRelationships": "true"})
    for item in page["items"]:
        if item["type"] == "FilmSearchItem":
            return item["film"]["id"]
    return None
```

Show the top three matches to the member when the year or the director is ambiguous. Do not guess for the member.

### Pattern 2: build a type-ahead box

```javascript
const API = "https://api.letterboxd.com/api/v0";
let controller = null, timer = null;

function onInput(event) {
  const text = event.target.value.trim();
  clearTimeout(timer);
  if (controller) controller.abort();   // Cancel the request that is now stale.
  if (text.length < 2) return;          // Do not search for one character.
  timer = setTimeout(() => runSearch(text), 250);   // Wait for a pause of 250 ms.
}

async function runSearch(text) {
  controller = new AbortController();
  const params = new URLSearchParams({   // URLSearchParams encodes the text.
    input: text, searchMethod: "Autocomplete", perPage: "8",
    excludeMemberFilmRelationships: "true",
  });
  params.append("include", "FilmSearchItem");        // Repeat the key per type.
  params.append("include", "ContributorSearchItem");
  const response = await fetch(`${API}/search?${params}`, {
    headers: { Authorization: `Bearer ${TOKEN}`, Accept: "application/json" },
    signal: controller.signal,
  });
  if (!response.ok) return;             // A failed search returns 400.
  // Write labelFor as a switch on item.type, with a default branch that returns null.
  render((await response.json()).items.map(labelFor).filter(Boolean));
}
```

Three rules make a type-ahead box polite: debounce the keystrokes, abort the stale request, and cache the last results per prefix.

### Pattern 3: paginate the results

```python
def search_all(token, text, max_items=1000, **extra):
    """Yield search results page by page until the cursor ends."""
    cursor, count = None, 0
    while True:
        params = {"input": text, "perPage": 100, **extra}
        if cursor:
            params["cursor"] = cursor
        page = api_get(token, "/search", params)
        for item in page["items"]:
            yield item
            count += 1
            if count >= max_items:
                return
        cursor = page.get("next")   # The last page has no next cursor.
        if not cursor:
            return
        time.sleep(0.2)             # Stay polite. Do not flood the API.
```

Call it with a filter, such as `search_all(TOKEN, "film noir", max_items=200, include="ListSearchItem")`. Always set a `max_items` limit. The cursor stops at 100,000 objects, and a full sweep helps nobody.

## GET /news

`GET /news` returns recent news from the Letterboxd editors.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `cursor` | string | – | The pagination cursor. |
| `perPage` | int32 | `20` | The maximum is `100`. |
| `sort` | enum | `Date` | `Date` is the only value. |

`NewsResponse` holds `items` (**required**), `next` and `itemCount`. Each item is a `NewsItem`.

| Field | Type | Notes |
|---|---|---|
| `title` | string | **Required.** The title of the news item. |
| `url` | url string | **Required.** The link to the news item. |
| `image` | `Image` | The image, in several sizes. Read `sizes[].url`. |
| `shortDescription` | string | A short description in LBML. |
| `longDescription` | string | A long description in LBML. |
| `episode` | int32 | The podcast episode number. It is present only for a podcast. |
| `season` | int32 | The podcast season number. It is present only for a podcast. |

LBML can contain `<br>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<a href="">` and `<blockquote>`. Render those tags, or strip them. Never inject the text as raw HTML without a sanitizer. Use `/news` for a news feed, a "what is new" panel or a podcast list. Read `episode` to separate the podcast items from the articles.

```bash
curl -sS -G 'https://api.letterboxd.com/api/v0/news' -H "Authorization: Bearer $TOKEN" \
  --data-urlencode 'perPage=10' | jq '.items[] | {title, url, episode, season}'
```

## GET /featured-content

`GET /featured-content` returns featured content from the Letterboxd editors. Use it for a promotional carousel, a trailer strip or a home-screen banner.

The endpoint takes one parameter: `include` (`FeaturedContentType[]`). It selects the subset to return. Repeat the key, because the parameter uses the exploded form style.

`FeaturedContentType` has two values: `FeaturedTrailer` (a featured film trailer) and `FeaturedLink` (a featured link).

`FeaturedContentResponse` holds one field: `items` (**required**), a list of `FeaturedContentItem`. The endpoint gives no cursor and no `perPage`.

| Field | Type | Notes |
|---|---|---|
| `type` | `FeaturedContentType` | **Required. The discriminator.** Read it before you read the rest. |
| `title` | string | **Required.** |
| `thumbnail` | `Image` | **Required.** |
| `poster` | `Image` | **Required.** |
| `subtitle` | string | The subtitle for the item. |
| `captionLBML` | string | A caption in LBML. |
| `posterUrl` | url string | The target of the default action on the poster. |
| `trackingUrl` | url string | Call it when the member sees or taps the item. |
| `secondaryTrackingUrl` | url string | The second tracking URL. |

The reference marks no First Party restriction on `/featured-content`, and it leaves the subtype tables of the discriminator empty, exactly like `AbstractSearchItem`. The Letterboxd editors control the content, so handle an empty `items` array as a normal result.

## First Party fields

A third-party client does not receive the **First Party** fields of `FilmSummary` inside a `FilmSearchItem`: `alternativeNames`, `originalName`, `posterPickerUrl` and `backdropPickerUrl`. Do not build a feature on them. `MemberSummary`, `ListSummary`, `ContributorSummary`, `NewsItem` and `FeaturedContentItem` carry no First Party field.

## Pitfalls

1. **URL-encode `input`.** A space, an ampersand, a plus sign or a non-ASCII letter breaks a raw URL. Use `--data-urlencode` in curl, `params=` in requests, or `URLSearchParams` in the browser.
2. **Repeat the `include` key.** `include` is an exploded form-style array. Send `include=FilmSearchItem&include=ListSearchItem`. A comma-joined list fails.
3. **Read `type` before the payload.** The response mixes ten shapes in one array. A client that reads `item.film` on every item crashes on the first member result.
4. **Handle an unknown `type`.** Letterboxd adds result types. Add a default branch that skips the item.
5. **Send booleans as `"true"` or `"false"`.** Python `True` renders as `True` in the query string, and the API rejects it.
6. **Respect the limits.** Cursor pagination stops at 100,000 objects, and Letterboxd sets that cap to stop a copy of the dataset. `perPage` stops at 100, and a larger value gives no more items.
7. **Do not scrape the website.** `/search` exists. A scraper breaks on the next markup change, and it violates the terms.
8. **Be polite with the rate.** Debounce a type-ahead box by 250 ms. Cache the repeat queries. Sleep between the pages of a sweep. Back off after an error.
9. **Handle 400.** `/search` answers 400 with an `ErrorResponse` when the search fails. Show a clean message.
10. **Order by `score`.** `score` is a relevancy value, not a percentage and not a rating. Set `excludeMemberFilmRelationships=true` when you do not show watch state, because the response then gets much smaller.
11. **Sanitize LBML.** News descriptions and featured captions hold markup. Never inject them raw.

## Relationships

| File | What it covers |
|---|---|
| overview.md | The base URL, the LID concept, the 100,000 object cap, the First Party rule. |
| authentication.md | The bearer token, the client credentials flow, the member sign-in flow. |
| films.md | `FilmSummary`, `Film`, contributors, and `/films/autocomplete` in full. |
| members.md | `MemberSummary`, and the member endpoints you call after a `MemberSearchItem`. |
| lists.md | `ListSummary` and the list endpoints you call after a `ListSearchItem`. |
| log-entries.md | The review and diary entities behind a `ReviewSearchItem`. |
| schemas-entities.md | `SearchResponse`, `AbstractSearchItem`, `NewsItem`, `FeaturedContentItem` and every summary entity. |
