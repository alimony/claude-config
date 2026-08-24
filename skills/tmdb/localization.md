# TMDB: Languages, Regions and Translations
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

TMDB stores one canonical record per movie, TV series, season, episode, collection and person. Localized text lives beside that record as a set of translations. Region-specific facts – release dates, certifications, streaming availability – live in separate lists keyed by country.

Three different parameters control this. Do not mix them up.

| Parameter | Format | What it does | Typical value |
| :--- | :--- | :--- | :--- |
| `language` | ISO 639-1, or `xx-XX` | Selects the translated text (title, overview, tagline) and filters images | `pt-BR` |
| `region` | ISO 3166-1 alpha-2, uppercase | Selects which country's release dates to show or filter on | `DE` |
| `watch_region` | ISO 3166-1 alpha-2, uppercase | Selects the country for streaming provider data | `SE` |

`language` answers "in which words?". `region` answers "released where?". `watch_region` answers "streamable where?". A request can use all three at once, and they can point at different countries.

Two more country-shaped parameters exist. `country` filters movie alternative titles. `timezone` shifts the day boundary for TV air-date endpoints.

## 2. The `language` parameter

The language code system is [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Some languages have no ISO 639-1 code, so TMDB cannot represent them. The country half of the code is [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1).

Both forms are valid. Use the `xx-XX` form when the regional variant matters.

```bash
# Language only – Portuguese, no regional variant
curl -s 'https://api.themoviedb.org/3/movie/550?language=pt' \
  -H "Authorization: Bearer $TMDB_TOKEN" -H 'accept: application/json'

# Language and country – Brazilian Portuguese
curl -s 'https://api.themoviedb.org/3/movie/popular?language=pt-BR' \
  -H "Authorization: Bearer $TMDB_TOKEN" -H 'accept: application/json'
```

Most endpoints default to `language=en-US`. Two exceptions default to `language=en`: `/genre/movie/list` and `/genre/tv/list`. The `/images` endpoints have no default – an empty `language` there means "no language filter", which is a different thing.

### What `language` changes, and what it does not

`language` changes `title`, `name`, `overview`, `tagline`, `homepage`, genre names and the localized `runtime` where a translation exists.

`language` does not change these fields:

- `original_title` and `original_name` – these always hold the original-language value.
- `original_language` – this is a fact about the work, not about your request.
- Person names and character names. The docs state this gap directly: "The two main areas that are not [translated] are person names and characters."
- Release dates, certifications and provider names – `region` and `watch_region` control those.

### Fallback: what returns English and what returns empty

The rules differ per field, and this is the largest source of bugs.

| Case | Result |
| :--- | :--- |
| Title has no translation | TMDB returns the default (usually English) title, so the field looks populated |
| Overview or tagline has no translation | TMDB returns an empty string `""`, not `null` and not the English text |
| `/translations` entry has no value for a field | The field is an empty string in `data` |
| Release date missing for the `region` | TMDB falls back to the primary release date – documented behaviour |
| Poster has no image in your `language` | TMDB falls back to the original-language image, then to the highest rated image |

The collection translations response shows the empty-string case clearly:

```json
{"iso_3166_1": "AE", "iso_639_1": "ar", "name": "العربية", "english_name": "Arabic",
 "data": {"title": "", "overview": "", "homepage": ""}}
```

The Arabic entry exists, but no field is filled. Treat "the language is present in the list" and "the field has a value" as two separate tests.

> Warning: never show an empty overview to a user. Build an explicit fallback chain. Section 5 shows how.

## 3. Find the valid values

Do not hard-code a language list. Read it from the configuration endpoints and cache it.

| Endpoint | Returns |
| :--- | :--- |
| `GET /3/configuration/languages` | Every ISO 639-1 tag TMDB uses, with `english_name` and native `name` |
| `GET /3/configuration/countries` | Every ISO 3166-1 tag, with `english_name` and `native_name`; accepts `language` |
| `GET /3/configuration/primary_translations` | The officially supported `xx-XX` translations, as a flat string array |
| `GET /3/watch/providers/regions` | The countries that have watch provider data |

```python
import requests

S = requests.Session()
S.headers.update({"Authorization": f"Bearer {TOKEN}", "accept": "application/json"})
BASE = "https://api.themoviedb.org/3"

primary = S.get(f"{BASE}/configuration/primary_translations").json()
# ['af-ZA', 'ar-AE', 'ar-SA', ..., 'de-DE', 'en-GB', 'en-US', 'pt-BR', 'sv-SE', ...]

langs = {l["iso_639_1"]: l for l in S.get(f"{BASE}/configuration/languages").json()}
print(langs["sv"]["english_name"], "/", langs["sv"]["name"])
```

Prefer a code from `/configuration/primary_translations` for the user-facing language picker. These are the translations TMDB actively curates, so they have the best coverage.

**Do this**: validate the user's locale against `primary_translations` and fall back to `en-US`.
**Don't do this**: pass a browser locale such as `en_US`, `pt_BR` or `zh-Hant` straight through. The separator is a hyphen, and the country part must be a real ISO 3166-1 code.

## 4. The `region` parameter

`region` is a presentation and filter parameter for release dates. It expects an uppercase ISO 3166-1 code. Only some endpoints honour it.

| Endpoint | Honours `region`? |
| :--- | :--- |
| `/discover/movie` | Yes – filters on the country's release dates |
| `/movie/now_playing`, `/movie/upcoming` | Yes – changes which movies appear |
| `/movie/popular`, `/movie/top_rated` | Yes |
| `/search/movie`, `/search/collection` | Yes – changes the displayed release date |
| `/movie/{id}` details | No – use `/movie/{id}/release_dates` |
| `/discover/tv`, `/search/tv`, all TV lists | No – TV uses `timezone` and `content_ratings` |
| `/search/multi`, `/search/person` | No |

When TMDB has no release date for that country, it falls back to the primary release date. That is the same result as no `region` at all, so `region` never removes a movie from a details response.

```bash
# German release date, German text
curl -s 'https://api.themoviedb.org/3/search/movie?query=Whiplash&language=de-DE&region=DE' \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

### `region` plus `with_release_type` on discover

`with_release_type` accepts the type codes below. Use a comma for AND and a pipe for OR. Combine it with `region` to ask a real question: "what is in German cinemas this week?".

| Type | Release |
| :--- | :--- |
| 1 | Premiere |
| 2 | Theatrical (limited) |
| 3 | Theatrical |
| 4 | Digital |
| 5 | Physical |
| 6 | TV |

```bash
URL='https://api.themoviedb.org/3/discover/movie'
URL+='?language=de-DE&region=DE&release_date.gte=2026-08-01'
URL+='&release_date.lte=2026-08-31&with_release_type=2|3'
curl -s "$URL" -H "Authorization: Bearer $TMDB_TOKEN"
```

If you use `region` on discover without `with_release_type`, `region` only requires that the movie has at least one release date in that country.

## 5. How-to patterns

### Pattern A – get the localized details in one request

Ask for the details and the translations together with `append_to_response`. One HTTP request gives you the localized text plus every fallback candidate.

```python
def localized_movie(movie_id, language="sv-SE"):
    r = S.get(f"{BASE}/movie/{movie_id}",
              params={"language": language, "append_to_response": "translations"})
    return r.json()
```

```bash
curl -s 'https://api.themoviedb.org/3/movie/550?language=sv-SE&append_to_response=translations' \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Each appended sub-request still reads the query parameters it supports. `language` therefore applies to the appended `images` block too – see Pattern C.

### Pattern B – build an explicit fallback chain

Do not trust one field from one call. Walk a list of languages and take the first non-empty value.

```python
def pick(translations, field, chain):
    """Return the first non-empty `field` from data, following `chain`."""
    index = {}
    for t in translations:
        index[f'{t["iso_639_1"]}-{t["iso_3166_1"]}'] = t["data"]
        index.setdefault(t["iso_639_1"], t["data"])
    for code in chain:
        value = (index.get(code) or {}).get(field, "")
        if value:
            return value, code
    return "", None

data = localized_movie(550, "sv-SE")
title, used = pick(data["translations"]["translations"], "title", ["sv-SE", "sv", "en-US", "en"])
overview, _ = pick(data["translations"]["translations"], "overview", ["sv-SE", "sv", "en-US", "en"])
print(title or data["original_title"], used)
```

**Do this**: chain `xx-XX` → `xx` → `en-US` → `original_title`.
**Don't do this**: issue one request per language in the chain. One `/translations` call returns them all.

### Pattern C – localized images with a fallback

`language` filters images. A strict filter often returns an empty list. Add `include_image_language` with `null` to keep the language-neutral artwork.

```bash
curl -s 'https://api.themoviedb.org/3/movie/550/images?language=en-US&include_image_language=en,null' \
  -H "Authorization: Bearer $TMDB_TOKEN"

# The same, appended to the details request
curl -s 'https://api.themoviedb.org/3/movie/550?language=en-US&append_to_response=images&include_image_language=en-US,null' \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

Regional variants are not supported for image lookups yet. `en-US` and `en` select the same images. See `./images-and-configuration.md`.

### Pattern D – the release date and certification for one country

`region` does not appear on the movie details endpoint. Call `/movie/{id}/release_dates` and select the country yourself.

```python
TYPE_NAMES = {1: "Premiere", 2: "Theatrical (limited)", 3: "Theatrical",
              4: "Digital", 5: "Physical", 6: "TV"}

def release_info(movie_id, country="DE", want_type=3):
    results = S.get(f"{BASE}/movie/{movie_id}/release_dates").json()["results"]
    block = next((r for r in results if r["iso_3166_1"] == country), None)
    if not block:
        return None
    entries = sorted(block["release_dates"], key=lambda e: e["release_date"])
    typed = [e for e in entries if e["type"] == want_type] or entries
    first = typed[0]
    return {"date": first["release_date"][:10],
            "type": TYPE_NAMES.get(first["type"]),
            "certification": first["certification"] or None,
            "note": first["note"]}
```

One country can hold several entries. The example data for Fight Club shows two Swiss theatrical releases – one with `iso_639_1: "de"`, one with `"fr"`. Use the `iso_639_1` field on the release entry to pick the language-correct row. Also read `note` – it often holds "Premiere" or festival context. `certification` is an empty string when nobody entered one.

### Pattern E – the content rating for a TV series

TV series have no release dates. They have content ratings per country.

```python
def content_rating(series_id, country="GB"):
    results = S.get(f"{BASE}/tv/{series_id}/content_ratings").json()["results"]
    hit = next((r for r in results if r["iso_3166_1"] == country), None)
    return hit["rating"] if hit else None   # e.g. "18"
```

Each entry holds `iso_3166_1`, `rating` and a `descriptors` array. The `descriptors` array carries extra content warnings and is often empty.

To learn what a rating string means, read `/certification/movie/list` and `/certification/tv/list`. Both return a map of country code to a list of `certification`, `meaning` and `order`. Use `order` to sort ratings from mild to strong.

### Pattern F – alternative titles for one country

```bash
curl -s 'https://api.themoviedb.org/3/movie/550/alternative_titles?country=RU' \
  -H "Authorization: Bearer $TMDB_TOKEN"
```

```javascript
const res = await fetch(
  "https://api.themoviedb.org/3/tv/1399/alternative_titles",
  { headers: { Authorization: `Bearer ${token}`, accept: "application/json" } }
);
const { results } = await res.json();
const brazilian = results.filter(t => t.iso_3166_1 === "BR");
```

Note the shape difference: the movie endpoint returns the array under `titles`, the TV endpoint returns it under `results`. The `country` filter parameter exists on the movie endpoint only – filter the TV list in your own code.

### Pattern G – streaming availability in a country

`watch_region` is a separate axis. Use it with `with_watch_providers` or `with_watch_monetization_types`.

```bash
URL='https://api.themoviedb.org/3/discover/movie'
URL+='?language=fr-FR&watch_region=FR&with_watch_providers=8'
URL+='&with_watch_monetization_types=flatrate'
curl -s "$URL" -H "Authorization: Bearer $TMDB_TOKEN"
```

`with_watch_monetization_types` accepts `flatrate`, `free`, `ads`, `rent` and `buy`. See `./watch-providers.md`.

## 6. Translations endpoints

Every `/translations` endpoint returns the same envelope: `id` plus a `translations` array. Each item holds `iso_639_1`, `iso_3166_1`, `name` (the language in its own script), `english_name`, and a `data` object. Only the keys inside `data` change per entity.

| Endpoint | Fields in `data` |
| :--- | :--- |
| `GET /3/movie/{movie_id}/translations` | `title`, `overview`, `tagline`, `homepage`, `runtime` |
| `GET /3/tv/{series_id}/translations` | `name`, `overview`, `tagline`, `homepage` |
| `GET /3/tv/{series_id}/season/{season_number}/translations` | `name`, `overview` |
| `GET /3/tv/{series_id}/season/{season_number}/episode/{episode_number}/translations` | `name`, `overview` |
| `GET /3/collection/{collection_id}/translations` | `title`, `overview`, `homepage` |
| `GET /3/person/{person_id}/translations` | `name`, `biography` |

None of these endpoints accepts a `language` parameter. They always return every translation. Filter in your own code.

`/person/{person_id}/translations` is the only way to get a translated biography. The person details endpoint accepts `language`, but person names and character names stay untranslated in the main endpoints.

```python
bios = S.get(f"{BASE}/person/31/translations").json()["translations"]
fr = next(t for t in bios if t["iso_639_1"] == "fr")
print(fr["data"]["name"], "-", fr["data"]["biography"][:80])
```

Seasons and episodes have translation endpoints of their own. A season name such as "Season 1" is often untranslated and returns an empty string. See `./tv-seasons-and-episodes.md`.

## 7. Alternative titles and names

Alternative titles are not translations. A translation is the official localized text for one language. An alternative title is any other name the work is known by in a country – a romanization, a working title, a marketing title, a TV re-title.

| Endpoint | Array key | Item fields |
| :--- | :--- | :--- |
| `GET /3/movie/{movie_id}/alternative_titles?country=XX` | `titles` | `iso_3166_1`, `title`, `type` |
| `GET /3/tv/{series_id}/alternative_titles` | `results` | `iso_3166_1`, `title`, `type` |
| `GET /3/company/{company_id}/alternative_names` | `results` | `name`, `type` |
| `GET /3/network/{network_id}/alternative_names` | `results` | `name`, `type` |

Alternative titles are keyed by **country**, not by language. Two entries can share a country and differ in script, for example `CN` with `权利的游戏` and `權力的遊戲`.

The `type` field is free text and is often an empty string. Observed values include `romanization`, `working title`, `common abbreviation`, `Alternative title` and region labels such as `Hispanoamérica`. Do not build logic on an exact `type` string. Treat it as a hint for the user.

**Use `/translations` when** you want the correct localized title and overview to show in your UI.
**Use `/alternative_titles` when** you want to match user input, improve search recall, or show "also known as".

For people, the person details response carries `also_known_as`, an array of names in many scripts. That is the person equivalent of alternative titles.

## 8. `include_adult`

`include_adult` is a boolean, and it defaults to `false`. It appears on `/discover/movie`, `/discover/tv`, all `/search/*` endpoints and `/keyword/{keyword_id}/movies`.

`include_adult` is independent of `language` and `region`. It does not change with the country. It has no relation to certifications – a movie with a strong local certification is not adult content.

**Do this**: control the age gate with `certification_country` plus `certification` (or `certification.lte`) on `/discover/movie`, and read `/movie/{id}/release_dates` or `/tv/{id}/content_ratings` for the display value.
**Don't do this**: set `include_adult=true` to widen a search and hope your region filter hides the results. It does not.

```bash
# Family-safe discovery for the United States
URL='https://api.themoviedb.org/3/discover/movie'
URL+='?language=en-US&region=US&certification_country=US'
URL+='&certification.lte=PG&include_adult=false'
curl -s "$URL" -H "Authorization: Bearer $TMDB_TOKEN"
```

The docs mark `certification`, `certification.gte` and `certification.lte` as parameters to use with `region`, and `certification_country` as the companion of those filters. Send `certification_country` and `region` together with the same value to stay safe.

## 9. Pitfalls

- **The empty overview.** An empty string is the normal result for a missing translation. Test the string, not the key.
- **The lower-case region.** `region=de` is wrong. ISO 3166-1 codes are uppercase.
- **The underscore locale.** `pt_BR` is not valid. Use `pt-BR`.
- **The three-letter language code.** TMDB uses ISO 639-1, so `swe`, `ger` and `zho` all fail. Use `sv`, `de` and `zh`.
- **`region` on a details call.** `/movie/{id}` ignores `region`. Call `/movie/{id}/release_dates`.
- **`region` on TV.** No TV endpoint takes `region`. Use `/tv/{id}/content_ratings`, and `timezone` for air-date lists.
- **The disappearing images.** `language=fr-FR` on `/images` returns only French artwork. Add `include_image_language=fr,null`.
- **The `titles` and `results` mismatch.** Movie alternative titles come back under `titles`; the TV version uses `results`.
- **Genre list defaults.** `/genre/movie/list` and `/genre/tv/list` default to `language=en`, not `en-US`.
- **Cached genre names.** Genre names are localized. Cache them per language, not once for the whole application.
- **Untranslated person and character names.** These stay in the original data. Use `/person/{id}/translations` for the biography, and expect the name to stay as it is.
- **One country, several release dates.** Read the `type` and `iso_639_1` fields before you show a date.
- **Language in a cache key.** Include `language`, `region` and `watch_region` in every cache key. Otherwise you serve German text to a Japanese user.

## 10. Decision table: "I want the title in language X"

| Goal | Call | Notes |
| :--- | :--- | :--- |
| One movie's title and overview in `xx-XX` | `GET /movie/{id}?language=xx-XX` | Fast; the overview can come back empty |
| The same, with a guaranteed fallback | `GET /movie/{id}?language=xx-XX&append_to_response=translations` | One request; pick the field yourself |
| Every available translation | `GET /movie/{id}/translations` | No `language` parameter; returns all |
| A list of movies, all localized | `GET /discover/movie?language=xx-XX` | Per-item fallback is not possible; accept the API default |
| The original, untranslated title | Read `original_title` / `original_name` | Present in every details and list response |
| The title used in country YY | `GET /movie/{id}/alternative_titles?country=YY` | Country-keyed, not language-keyed |
| A TV series title | `GET /tv/{id}?language=xx-XX` or `/tv/{id}/translations` | The field is `name`, not `title` |
| A season or episode name | `GET /tv/{id}/season/{n}/translations` | Often empty for generic season names |
| A person's name or biography | `GET /person/{id}/translations` | Names are not localized in the main endpoint |
| A collection name | `GET /collection/{id}/translations` | Field is `title` |
| A company or network name | `.../alternative_names` | No language code on the items |

## 11. Related skill files

- `./getting-started.md` – base URL, response envelope, rate limits.
- `./authentication.md` – the bearer token used in every example here.
- `./images-and-configuration.md` – `include_image_language`, image sizes, the configuration endpoints.
- `./append-to-response.md` – how to combine details and `translations` in one request.
- `./movies.md` – movie details, `/release_dates`, `/alternative_titles`.
- `./tv-series.md` – series details, `/content_ratings`, `/alternative_titles`.
- `./tv-seasons-and-episodes.md` – season and episode translations.
- `./people-and-credits.md` – person details, `also_known_as`, untranslated character names.
- `./search-and-find.md` – `language`, `region` and `include_adult` on search.
- `./discover.md` – `region`, `watch_region`, `with_release_type`, `certification_country`, `with_original_language`.
- `./trending-and-popular.md` – `language` and `region` on the curated lists.
- `./watch-providers.md` – `watch_region` and `/watch/providers/regions`.
- `./entities.md` – collections, companies, networks and keywords.
- `./changes-and-exports.md` – translation edits appear in the change feed.
