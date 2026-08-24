# TMDB: Images and Configuration
Based on TMDB API v3 documentation (developer.themoviedb.org).

## 1. Core concepts

TMDB never returns a full image URL. It returns a **file path**, for example `/1E5baAaEse26fej7uHcjOgEE2t2.jpg`. You must build the URL from three parts.

| Part | Where it comes from | Example |
| --- | --- | --- |
| Base URL | `GET /configuration` → `images.secure_base_url` | `https://image.tmdb.org/t/p/` |
| Size | `GET /configuration` → one of the `images.*_sizes` arrays | `w500` |
| File path | The media object field: `poster_path`, `backdrop_path`, `logo_path`, `profile_path`, `still_path`, or `file_path` in an `/images` response | `/1E5baAaEse26fej7uHcjOgEE2t2.jpg` |

Join the three parts in that order:

```text
https://image.tmdb.org/t/p/  +  w500  +  /1E5baAaEse26fej7uHcjOgEE2t2.jpg
= https://image.tmdb.org/t/p/w500/1E5baAaEse26fej7uHcjOgEE2t2.jpg
```

The base URL ends with a slash. The file path starts with a slash. Concatenate them directly – do not add a third slash.

**Why you must not hardcode the base URL or the sizes.** TMDB publishes the host and the size buckets through `/configuration` so it can change them. A hardcoded `https://image.tmdb.org/t/p/w500` breaks on the day TMDB moves the CDN or removes a bucket. Read both values from `/configuration`, cache them, and refresh them on a timer. See section 4.

**The image host is a plain CDN.** It needs no API key. Do not send your read access token to `image.tmdb.org`. Send it only to `api.themoviedb.org` – see [./authentication.md](./authentication.md).

## 2. The `/configuration` response

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/configuration' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

```json
{
  "images": {
    "base_url": "http://image.tmdb.org/t/p/",
    "secure_base_url": "https://image.tmdb.org/t/p/",
    "backdrop_sizes": ["w300", "w780", "w1280", "original"],
    "logo_sizes": ["w45", "w92", "w154", "w185", "w300", "w500", "original"],
    "poster_sizes": ["w92", "w154", "w185", "w342", "w500", "w780", "original"],
    "profile_sizes": ["w45", "w185", "h632", "original"],
    "still_sizes": ["w92", "w185", "w300", "original"]
  },
  "change_keys": ["adult", "air_date", "..."]
}
```

**Always use `secure_base_url`.** `base_url` is `http://`. An HTTP image on an HTTPS page causes a mixed-content block in every modern browser. Treat `base_url` as legacy.

`change_keys` lists every field name that the changes API can report. See [./changes-and-exports.md](./changes-and-exports.md).

### Size buckets

A `wNNN` bucket sets the width in pixels. A `hNNN` bucket sets the height. `original` returns the file as the contributor uploaded it.

| Image type | Field | Sizes | Typical choice |
| --- | --- | --- | --- |
| Poster | `poster_path` | w92, w154, w185, w342, w500, w780, original | `w185` in a grid, `w500` on a detail page |
| Backdrop | `backdrop_path` | w300, w780, w1280, original | `w780` on mobile, `w1280` for a hero banner |
| Logo | `logo_path` | w45, w92, w154, w185, w300, w500, original | `w185` for a company row, `original` for SVG |
| Profile | `profile_path` | w45, w185, h632, original | `w45` for an avatar, `h632` for a portrait |
| Still | `still_path` | w92, w185, w300, original | `w300` for an episode card |

Pick the smallest bucket that is at least as wide as the rendered element. Multiply by 2 for a high-density display. Do not download `original` for a thumbnail grid – original files can be several megabytes each.

## 3. How to build one URL

```bash
# Get the config once, then build the URL.
curl -s 'https://api.themoviedb.org/3/configuration' \
     -H 'Authorization: Bearer <access_token>' | jq -r '.images.secure_base_url'
# https://image.tmdb.org/t/p/

curl -sI 'https://image.tmdb.org/t/p/w500/1E5baAaEse26fej7uHcjOgEE2t2.jpg' | head -1
# HTTP/2 200
```

```python
base = "https://image.tmdb.org/t/p/"   # from /configuration, never hardcoded in real code
url = f"{base}w500{movie['poster_path']}"
```

```javascript
const url = `${secureBaseUrl}w500${movie.poster_path}`;
```

## 4. Complete helper: cached configuration plus URL builder

Cache `/configuration` in memory or in your data store. The values change very seldom. Refresh them once a day, or every few days – a shorter interval only wastes requests. Never call `/configuration` before each image URL.

```python
import time
import requests

API = "https://api.themoviedb.org/3"

# Last-resort values. Use them only when /configuration is unreachable.
FALLBACK = {
    "secure_base_url": "https://image.tmdb.org/t/p/",
    "backdrop_sizes": ["w300", "w780", "w1280", "original"],
    "logo_sizes": ["w45", "w92", "w154", "w185", "w300", "w500", "original"],
    "poster_sizes": ["w92", "w154", "w185", "w342", "w500", "w780", "original"],
    "profile_sizes": ["w45", "w185", "h632", "original"],
    "still_sizes": ["w92", "w185", "w300", "original"],
}


class TmdbImages:
    """Build TMDB image URLs from a cached /configuration response."""

    def __init__(self, token, ttl_seconds=24 * 3600):
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "accept": "application/json"}
        )
        self.ttl = ttl_seconds
        self._images = None
        self._fetched_at = 0.0

    def config(self):
        """Return the images block. Refresh it when the cache expires."""
        now = time.time()
        if self._images is None or now - self._fetched_at > self.ttl:
            try:
                response = self.session.get(f"{API}/configuration", timeout=10)
                response.raise_for_status()
                self._images = response.json()["images"]
                self._fetched_at = now
            except (requests.RequestException, KeyError, ValueError):
                if self._images is None:
                    self._images = FALLBACK          # cold start failed
                # A warm cache stays in use until the next refresh succeeds.
        return self._images

    def sizes(self, kind):
        """kind is one of: backdrop, logo, poster, profile, still."""
        return self.config().get(f"{kind}_sizes", ["original"])

    def best_size(self, kind, min_width):
        """Return the smallest width bucket that is at least min_width."""
        buckets = []
        for name in self.sizes(kind):
            if name.startswith("w") and name[1:].isdigit():
                buckets.append((int(name[1:]), name))
        for width, name in sorted(buckets):
            if width >= min_width:
                return name
        return "original"

    def url(self, file_path, kind="poster", size=None, min_width=None):
        """Turn a poster_path into a full URL. Return None when there is no image."""
        if not file_path:
            return None                              # poster_path is often null
        images = self.config()
        if size is None:
            size = self.best_size(kind, min_width or 500)
        if size not in self.sizes(kind):
            size = "original"                        # never send an unknown bucket
        base = images.get("secure_base_url") or FALLBACK["secure_base_url"]
        return f"{base}{size}{file_path}"            # base ends with /, path starts with /


# Usage
tmdb = TmdbImages(token="<access_token>")
movie = requests.get(
    f"{API}/movie/550",
    headers={"Authorization": "Bearer <access_token>"},
    timeout=10,
).json()

print(tmdb.url(movie["poster_path"], "poster", min_width=342))
# https://image.tmdb.org/t/p/w342/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg
print(tmdb.url(movie["backdrop_path"], "backdrop", size="w1280"))
print(tmdb.url(None, "poster"))   # None – render your placeholder
```

The same pattern in JavaScript:

```javascript
let cache = null;
let fetchedAt = 0;
const TTL = 24 * 60 * 60 * 1000;

async function imageConfig(token) {
  if (cache && Date.now() - fetchedAt < TTL) return cache;
  const res = await fetch("https://api.themoviedb.org/3/configuration", {
    headers: { Authorization: `Bearer ${token}`, accept: "application/json" },
  });
  cache = (await res.json()).images;
  fetchedAt = Date.now();
  return cache;
}

export async function imageUrl(token, filePath, size = "w500") {
  if (!filePath) return null;
  const { secure_base_url } = await imageConfig(token);
  return `${secure_base_url}${size}${filePath}`;
}
```

## 5. Image languages

Two different things return images. Know which one you use.

1. **The `*_path` field on a detail object** (`movie.poster_path`). TMDB already selected one image for you.
2. **The `/images` methods** (`/movie/550/images`). You get every image and you select one.

### How TMDB selects the `*_path` field

| Field | Selection rule |
| --- | --- |
| `poster_path` | TMDB queries your `language` first. If no poster exists, TMDB falls back to the highest rated poster in the media's original language. If that is absent, TMDB returns the highest rated poster overall. |
| `backdrop_path` | Almost no backdrop has text, so TMDB queries the highest rated backdrop with **no** language. If none exists, TMDB returns the highest rated backdrop overall. |
| `still_path` | Episode images carry no language, so TMDB returns the highest rated still. |

Regional variants do not work for images. TMDB tags images with an ISO 639-1 code only (`en`, `de`, `ja`), not with an IETF tag (`en-US`). This is a known limit and TMDB plans to change it.

### `language` filters, `include_image_language` adds

On an `/images` method the `language` parameter **removes** every image that does not match. The `include_image_language` parameter **adds** more languages back. Use the literal word `null` for images with no language tag – those are the textless images.

```bash
# English images plus every textless image.
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550/images?language=en&include_image_language=en,null' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

Get the same data in one request with `append_to_response` – see [./append-to-response.md](./append-to-response.md):

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/550?append_to_response=images&language=en-US&include_image_language=en,null' \
     --header 'Authorization: Bearer <access_token>' \
     --header 'accept: application/json'
```

```python
params = {"language": "en", "include_image_language": "en,null"}
images = requests.get(f"{API}/movie/550/images", headers=headers, params=params).json()
print(len(images["posters"]), len(images["backdrops"]), len(images["logos"]))
```

**Do this**

```python
# Ask for the text language you want, and for textless art as a fallback.
{"include_image_language": "en,null"}
# Backdrops: prefer textless art, and accept English logos on top of it.
{"include_image_language": "null,en"}
```

**Do not do this**

```python
{"language": "en-US"}                      # regional tag – images are ISO 639-1, result is often empty
{"include_image_language": "en-US,null"}   # same problem
{"include_image_language": "en, null"}     # the space becomes part of the value
{"include_image_language": ""}             # sends nothing useful
```

## 6. Select the best image yourself

Each image object in an `/images` response has these fields.

| Field | Meaning |
| --- | --- |
| `file_path` | The path you feed to the URL builder |
| `iso_639_1` | The language tag of the text in the image – `null` means textless |
| `vote_average` | The community rating. Higher is better. |
| `vote_count` | The number of votes behind `vote_average` |
| `width`, `height`, `aspect_ratio` | The pixel size of the original file |
| `file_type` | Company logos only – `.svg` or `.png`, the format of the upload |

Do not depend on the array order. Sort the array yourself.

```python
def pick_image(images, language="en", prefer_textless=False):
    """Return the best image object, or None."""
    def rank(image):
        lang = image.get("iso_639_1")
        if prefer_textless:
            tier = 0 if lang is None else (1 if lang == language else 2)
        else:
            tier = 0 if lang == language else (1 if lang is None else 2)
        # A high rating with few votes is not reliable, so use vote_count as a tie break.
        return (tier, -image.get("vote_average", 0.0), -image.get("vote_count", 0))

    return sorted(images, key=rank)[0] if images else None


data = requests.get(f"{API}/movie/550/images",
                    headers=headers,
                    params={"include_image_language": "en,null"}).json()

poster = pick_image(data["posters"], "en")                       # text is fine
backdrop = pick_image(data["backdrops"], "en", prefer_textless=True)
logo = pick_image(data["logos"], "en")

print(tmdb.url(poster["file_path"], "poster", "w500"))
print(tmdb.url(backdrop["file_path"], "backdrop", "w1280"))
```

Use `prefer_textless=True` for a backdrop that carries your own title overlay. Use the language tier first for a poster, because a poster in the reader's language is more useful than a slightly higher rated foreign poster.

## 7. The `/images` endpoints

| Endpoint | Arrays in the response | Accepts `language` and `include_image_language` |
| --- | --- | --- |
| `GET /movie/{movie_id}/images` | `backdrops`, `logos`, `posters` | Yes |
| `GET /tv/{series_id}/images` | `backdrops`, `logos`, `posters` | Yes |
| `GET /tv/{series_id}/season/{season_number}/images` | `posters` | Yes |
| `GET /tv/{series_id}/season/{season_number}/episode/{episode_number}/images` | `stills` | Yes |
| `GET /collection/{collection_id}/images` | `backdrops`, `posters` | Yes |
| `GET /person/{person_id}/images` | `profiles` | **No** |
| `GET /company/{company_id}/images` | `logos` (with `file_type`) | **No** |
| `GET /person/{person_id}/tagged_images` | `results` (paged, each with a `media` object) | No – `page` only |

Do not send `include_image_language` to `/person/{id}/images` or `/company/{id}/images`. Those methods ignore it.

## 8. Company and network logos: SVG or PNG

Every `logo_path` field returns a `.png` name. TMDB kept that behaviour for backward compatibility after it added SVG support. The `/company/{id}/images` method exposes the real upload format in `file_type`.

```bash
# Netflix logo, uploaded as SVG (wwemzKWzjKYJFfCeiB57q3r4Bcm.svg)
https://image.tmdb.org/t/p/original/wwemzKWzjKYJFfCeiB57q3r4Bcm.svg   # vector, not resized
https://image.tmdb.org/t/p/original/wwemzKWzjKYJFfCeiB57q3r4Bcm.png   # raster fallback
https://image.tmdb.org/t/p/w500/wwemzKWzjKYJFfCeiB57q3r4Bcm.png       # any bucket works for PNG
```

Rules:

- Request the `original` size for an SVG. TMDB does not resize vector files, so a `wNNN` bucket has no meaning for `.svg`.
- Request any bucket for a PNG.
- Swap the extension yourself when you want the SVG: replace `.png` with `.svg` only when `file_type` says `.svg`.

```python
def logo_url(tmdb, logo, size="w300"):
    """Prefer the SVG when the upload was a vector file."""
    path = logo["file_path"]
    if logo.get("file_type") == ".svg":
        return tmdb.url(path.rsplit(".", 1)[0] + ".svg", "logo", size="original")
    return tmdb.url(path, "logo", size=size)
```

## 9. The other configuration endpoints

All of them are static reference data. Cache each one for at least a day. None of them needs a page parameter.

| Endpoint | Parameters | Returns | Use it for |
| --- | --- | --- | --- |
| `GET /configuration` | none | `images` block, `change_keys` | Image URLs, and the field names used by the changes API |
| `GET /configuration/countries` | `language` (default `en-US`) | `iso_3166_1`, `english_name`, `native_name` | Country pickers, `region` and `watch_region` values, release-date regions |
| `GET /configuration/languages` | none | `iso_639_1`, `english_name`, `name` | Language pickers, and a name for the `iso_639_1` tag on an image or on `spoken_languages` |
| `GET /configuration/jobs` | none | `department`, `jobs[]` | Crew filters, and grouping of a credits list by department |
| `GET /configuration/primary_translations` | none | IETF tags, for example `en-US`, `pt-BR`, `zh-TW` | The valid values for the `language` parameter across the API |
| `GET /configuration/timezones` | none | `iso_3166_1`, `zones[]` | Map a country to its time zones for TV air dates |

```bash
curl -s 'https://api.themoviedb.org/3/configuration/countries?language=de-DE' \
     -H 'Authorization: Bearer <access_token>' | jq '.[0]'
# { "iso_3166_1": "AD", "english_name": "Andorra", "native_name": "Andorra" }
```

```python
# Build a lookup that turns an image iso_639_1 tag into a display name.
langs = requests.get(f"{API}/configuration/languages", headers=headers).json()
NAMES = {l["iso_639_1"]: (l["name"] or l["english_name"]) for l in langs}
NAMES["en"], NAMES["cs"], NAMES.get(None, "No language")
# ('English', 'Český', 'No language')
```

The `name` field holds the native name and it is **an empty string for many languages**. Fall back to `english_name`, as the example above does.

`primary_translations` lists the translations that TMDB also supports on its website. Any language can hold content, but only these are "primary". Use this list to populate a language selector. Remember the exception: image languages stay ISO 639-1 only. See [./localization.md](./localization.md).

```python
# Validate a user language choice before you send it to the API.
primary = set(requests.get(f"{API}/configuration/primary_translations", headers=headers).json())
lang = user_choice if user_choice in primary else "en-US"
```

## 10. Best practices and anti-patterns

| Do this | Do not do this |
| --- | --- |
| Read `secure_base_url` and the size arrays from `/configuration` | Hardcode `https://image.tmdb.org/t/p/w500` in your templates |
| Cache the configuration and refresh it once a day | Call `/configuration` before every image URL |
| Keep a small hardcoded fallback for a cold start failure | Crash the page when `/configuration` times out |
| Use `secure_base_url` | Use `base_url`, which is `http://` |
| Pick the smallest bucket that covers the rendered size | Load `original` into a 92 px thumbnail |
| Guard for a null `poster_path` and show a placeholder | Concatenate `None` into a URL string |
| Pass `include_image_language=en,null` | Pass `language=en-US` alone and get an empty list |
| Sort images by `iso_639_1`, then `vote_average` | Take `posters[0]` and trust the order |
| Link directly to `image.tmdb.org` | Proxy every image through your own server |
| Send the token only to `api.themoviedb.org` | Send an `Authorization` header to the image CDN |

## 11. Pitfalls

- **A double slash.** `secure_base_url` ends with `/` and `file_path` starts with `/`. `f"{base}/{size}/{path}"` produces `//`. Use `f"{base}{size}{path}"`.
- **A null path.** `poster_path`, `backdrop_path`, `profile_path` and `logo_path` are frequently `null`. Check before you build the URL.
- **A size from the wrong list.** `w342` is a poster bucket, not a backdrop bucket. Always read the array that matches the image type.
- **A regional image language.** Images accept `en`, not `en-US`. The `language` parameter on the parent object still accepts `en-US`.
- **`null` as a real null.** In `include_image_language` the value `null` is the four-letter string. Do not send an empty parameter and do not send a JSON null.
- **`language` on `/images` is a filter.** It does not act as a preference. Add `include_image_language` whenever you set it.
- **Person and company images ignore the language parameters.** Filter the result in your own code.
- **An empty native `name`.** `/configuration/languages` returns `""` for many entries. Fall back to `english_name`.
- **`vote_average` of 0.** A new image has no votes. Use `vote_count` as a tie break so an unrated image does not win over a well rated one.
- **SVG logos.** A `wNNN` size does nothing for `.svg`. Request `original`.
- **Aspect ratio.** Posters are near 0.667, backdrops and stills near 1.778. Read `aspect_ratio` before you place an image in a fixed frame.

## 12. Related skill files

- [./getting-started.md](./getting-started.md) – the base API URL, the request format, and rate limits.
- [./authentication.md](./authentication.md) – the bearer read access token that `/configuration` needs.
- [./localization.md](./localization.md) – the `language`, `region` and `watch_region` parameters, and how they differ from image languages.
- [./append-to-response.md](./append-to-response.md) – get `images` together with the detail object in one request.
- [./movies.md](./movies.md), [./tv-series.md](./tv-series.md), [./tv-seasons-and-episodes.md](./tv-seasons-and-episodes.md) – the `/images` methods for each media type.
- [./people-and-credits.md](./people-and-credits.md) – `profile_path`, `/person/{id}/images`, `tagged_images`, and the departments from `/configuration/jobs`.
- [./entities.md](./entities.md) – company, network and collection logos and images.
- [./search-and-find.md](./search-and-find.md), [./discover.md](./discover.md), [./trending-and-popular.md](./trending-and-popular.md) – list results that carry `poster_path` and `backdrop_path` for the URL builder.
- [./watch-providers.md](./watch-providers.md) – provider `logo_path` values use the same builder and the logo sizes.
- [./changes-and-exports.md](./changes-and-exports.md) – the `change_keys` array from `/configuration`.
