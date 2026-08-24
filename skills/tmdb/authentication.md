# TMDB: Authentication
Based on TMDB API v3 documentation (developer.themoviedb.org).

## Core concepts

TMDB v3 has three authentication modes. Each mode answers a different question – who is the application, and who is the person.

| Mode | Credential | Access | Use it for |
| --- | --- | --- | --- |
| Application | API key or API Read Access Token | Read access to the public catalogue | Movies, TV, people, search, discover, images, configuration |
| User session | `session_id` plus the application credential | Read and write access to one TMDB account | Ratings, favourites, watchlist, custom lists, account details |
| Guest session | `guest_session_id` plus the application credential | A temporary anonymous rating scope | Ratings from a person who has no TMDB account |

Three rules make the model clear:

- Send the application credential on every request. A user credential never replaces it.
- Add `session_id` only when the endpoint reads or writes private account data.
- Use a guest session only when the person does not want to log in.

Get both application credentials from one page: log in to TMDB, then open `https://www.themoviedb.org/settings/api`. The page shows a v3 **API Key** and an **API Read Access Token** (a v4 JWT). Both give the same level of access to v3.

## Application authentication: header token or query key

The API accepts two forms of the application credential.

**Prefer the Bearer token.** The documentation calls it "the default method to authenticate". One token works across both the v3 and the v4 API, so you keep one secret instead of two.

```bash
# Preferred: API Read Access Token in a header
curl --request GET \
     --url 'https://api.themoviedb.org/3/movie/11' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'accept: application/json'
```

```bash
# Legacy alternative: the v3 API key as a query parameter
curl --request GET \
     --url "https://api.themoviedb.org/3/movie/11?api_key=$TMDB_API_KEY"
```

Use the query parameter only when the client cannot set headers – for example an `<img>` tag or a fixed third-party widget. The value then appears in server logs, proxy logs, browser history and referrer headers.

Set the header once in a client object and reuse it.

```python
import os
import requests

BASE = "https://api.themoviedb.org/3"

tmdb = requests.Session()
tmdb.headers.update({
    "Authorization": f"Bearer {os.environ['TMDB_READ_ACCESS_TOKEN']}",
    "accept": "application/json",
})

movie = tmdb.get(f"{BASE}/movie/11", timeout=10).json()
print(movie["title"])
```

```javascript
// Server-side only. Never run this in a browser bundle.
const TMDB = "https://api.themoviedb.org/3";
const headers = {
  Authorization: `Bearer ${process.env.TMDB_READ_ACCESS_TOKEN}`,
  accept: "application/json",
};

const res = await fetch(`${TMDB}/movie/11`, { headers });
const movie = await res.json();
```

## Endpoint quick reference

Base URL: `https://api.themoviedb.org`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/3/authentication` | Validate the application credential |
| GET | `/3/authentication/token/new` | Create a request token (login step 1) |
| POST | `/3/authentication/session/new` | Exchange an approved request token for a `session_id` (login step 3) |
| POST | `/3/authentication/token/validate_with_login` | Approve a request token with a username and a password |
| POST | `/3/authentication/session/convert/4` | Convert a user-approved v4 access token into a v3 `session_id` |
| DELETE | `/3/authentication/session` | Delete a session (log out) |
| GET | `/3/authentication/guest_session/new` | Create a guest session |

| Field | Where | Notes |
| --- | --- | --- |
| `api_key` | Query parameter | v3 key. Optional if you send the Bearer header. |
| `Authorization: Bearer <token>` | Header | API Read Access Token. Preferred. |
| `session_id` | Query parameter | Identifies the logged-in user on account endpoints. |
| `guest_session_id` | Query parameter | Identifies a guest on rating endpoints. |
| `request_token` | JSON body | Temporary token for the login flow. Expires after 60 minutes. |
| `redirect_to` | Query parameter on the approval URL | Sends the user back to your application after approval. |

## Validate the key

Call `GET /3/authentication` to test a credential. Use it in a start-up check or a health check, not before every request.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/authentication' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN"
```

```json
{ "success": true, "status_code": 1, "status_message": "Success." }
```

A bad credential returns HTTP 401:

```json
{ "status_code": 7, "status_message": "Invalid API key: You must be granted a valid key.", "success": false }
```

```python
def validate_credentials():
    r = tmdb.get(f"{BASE}/authentication", timeout=10)
    if r.status_code == 401:
        raise SystemExit(f"TMDB rejected the credential: {r.json()['status_message']}")
    r.raise_for_status()
    return True
```

## The user login flow

The documented flow has three steps. Step 2 happens in the browser of the user, not in your code.

1. Create a request token with `GET /3/authentication/token/new`.
2. Send the user to `https://www.themoviedb.org/authenticate/{REQUEST_TOKEN}` to approve the token.
3. Exchange the approved token for a `session_id` with `POST /3/authentication/session/new`.

### Step 1 – create a request token

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/authentication/token/new' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN"
```

```json
{
  "success": true,
  "expires_at": "2016-08-26 17:04:39 UTC",
  "request_token": "ff5c7eeb5a8870efe3cd7fc5c282cffd26800ecd"
}
```

The request token expires 60 minutes after you create it, if nobody uses it. Store it server-side against the local session of the user.

### Step 2 – the user approves the token

Send the user to the approval page:

```text
https://www.themoviedb.org/authenticate/{REQUEST_TOKEN}
```

Add a `redirect_to` parameter to bring the user back to your application:

```text
https://www.themoviedb.org/authenticate/{REQUEST_TOKEN}?redirect_to=https://www.yourapp.com/approved
```

URL-encode the callback value. If you give no `redirect_to`, TMDB shows the `/authenticate/allow` page. That page also returns an `Authentication-Callback` header. The header holds the ready-made API call for step 3. You can use that call or build the request yourself.

The user can also deny the request. Treat a missing or unapproved token as a failed login and start again.

### Step 3 – exchange the token for a session ID

```bash
curl --request POST \
     --url 'https://api.themoviedb.org/3/authentication/session/new' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'content-type: application/json' \
     --data '{"request_token": "ff5c7eeb5a8870efe3cd7fc5c282cffd26800ecd"}'
```

```json
{ "success": true, "session_id": "79191836ddaa0da3df76a5ffef6f07ad6ab0c641" }
```

Treat the `session_id` like a password. Keep it secret and store it encrypted. The documentation gives no expiry for a session ID, so it stays valid until you delete it.

### Use the session ID

Pass the session ID as a query parameter on account endpoints.

```bash
curl --request GET \
     --url "https://api.themoviedb.org/3/account?session_id=$TMDB_SESSION_ID" \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN"
```

## Full worked example: the interactive session flow

This script runs the complete flow from a terminal. It opens the browser, waits for the approval, and prints the session ID.

```python
"""TMDB v3 interactive login. Run: python tmdb_login.py"""
import os
import webbrowser
from urllib.parse import quote

import requests

BASE = "https://api.themoviedb.org/3"
AUTH_PAGE = "https://www.themoviedb.org/authenticate"

tmdb = requests.Session()
tmdb.headers.update({
    "Authorization": f"Bearer {os.environ['TMDB_READ_ACCESS_TOKEN']}",
    "accept": "application/json",
    "content-type": "application/json",
})


def create_request_token() -> dict:
    """Step 1. The token expires after 60 minutes."""
    r = tmdb.get(f"{BASE}/authentication/token/new", timeout=10)
    r.raise_for_status()
    return r.json()


def approval_url(request_token: str, redirect_to: str | None = None) -> str:
    """Step 2. Send the user to this page."""
    url = f"{AUTH_PAGE}/{request_token}"
    if redirect_to:
        url += f"?redirect_to={quote(redirect_to, safe='')}"
    return url


def create_session(request_token: str) -> str:
    """Step 3. Exchange the approved token for a session ID."""
    r = tmdb.post(
        f"{BASE}/authentication/session/new",
        json={"request_token": request_token},
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError(f"TMDB refused the token: {r.status_code} {r.text}")
    return r.json()["session_id"]


def delete_session(session_id: str) -> bool:
    """Log the user out."""
    r = tmdb.delete(
        f"{BASE}/authentication/session",
        json={"session_id": session_id},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("success", False)


if __name__ == "__main__":
    token = create_request_token()
    print(f"Request token expires at {token['expires_at']}.")

    url = approval_url(token["request_token"])
    print(f"Approve the login here:\n{url}")
    webbrowser.open(url)
    input("Press Enter after you approve the request. ")

    session_id = create_session(token["request_token"])
    print(f"session_id = {session_id}")

    account = tmdb.get(
        f"{BASE}/account", params={"session_id": session_id}, timeout=10
    ).json()
    print(f"Logged in as {account['username']} (account id {account['id']}).")
```

### The same flow in a web application

Use two routes. The first route starts the login. The second route completes it.

```python
# Flask sketch. Keep the request token in the server-side session.
@app.get("/login")
def login():
    token = create_request_token()
    session["tmdb_request_token"] = token["request_token"]
    callback = url_for("approved", _external=True)
    return redirect(approval_url(token["request_token"], callback))


@app.get("/approved")
def approved():
    request_token = session.pop("tmdb_request_token", None)
    if not request_token:
        abort(400, "No pending TMDB login.")
    session["tmdb_session_id"] = create_session(request_token)
    return redirect(url_for("home"))
```

Read the request token from your own server-side session, not from the callback URL. The user controls the query string, and a token that you did not issue must not create a session in your application.

## Login with a username and password

`POST /3/authentication/token/validate_with_login` approves a request token with the TMDB credentials of the user. It replaces step 2, not step 3.

```bash
curl --request POST \
     --url 'https://api.themoviedb.org/3/authentication/token/validate_with_login' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'content-type: application/json' \
     --data '{
       "username": "johnny_appleseed",
       "password": "test123",
       "request_token": "1531f1a558c8357ce8990cf887ff196e8f5402ec"
     }'
```

```json
{
  "success": true,
  "expires_at": "2018-07-24 04:10:26 UTC",
  "request_token": "1531f1a558c8357ce8990cf887ff196e8f5402ec"
}
```

The response returns the request token again – not a session ID. Call `POST /3/authentication/session/new` with that token to finish the login.

**The documentation discourages this method.** The preferred method sends the user to the TMDB website. Use the login method only when your application has no web view, for example a television application or a command-line tool. Always use HTTPS. Your code sees the password of the user, so this method breaks two-factor protection and makes you responsible for a credential that belongs to TMDB.

| Do | Do not |
| --- | --- |
| Send the user to `themoviedb.org/authenticate/{token}` | Build a login form that copies the TMDB brand |
| Use `validate_with_login` only with no web view | Store, log or cache the password |
| Discard the password from memory after the call | Reuse the password for a later "silent" re-login |

## Create a session from a v4 access token

If your application already runs the v4 OAuth flow, convert the result to a v3 session.

```bash
curl --request POST \
     --url 'https://api.themoviedb.org/3/authentication/session/convert/4' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'content-type: application/json' \
     --data '{"access_token": "<v4 access token approved by the user>"}'
```

```json
{ "success": true, "session_id": "2629f70fb498edc263a0adb99118ac41f0053e8c" }
```

The access token must be a **user-approved v4 access token**. The standard API Read Access Token does not work here. Use this endpoint when you want one login flow for both API versions.

## Delete a session (log out)

```bash
curl --request DELETE \
     --url 'https://api.themoviedb.org/3/authentication/session' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'content-type: application/json' \
     --data '{"session_id": "2629f70fb498edc263a0adb99118ac41f0053e8c"}'
```

```json
{ "success": true }
```

The session ID travels in the JSON body, not in the query string. Some HTTP clients drop the body of a DELETE request. Check that your client sends it – `requests` and `fetch` both support it.

```javascript
await fetch("https://api.themoviedb.org/3/authentication/session", {
  method: "DELETE",
  headers: {
    Authorization: `Bearer ${process.env.TMDB_READ_ACCESS_TOKEN}`,
    "content-type": "application/json",
  },
  body: JSON.stringify({ session_id: sessionId }),
});
```

Delete the stored session ID in your own database in the same step. A session that you forget stays valid.

## Guest sessions

A guest session lets a person rate content without a TMDB account. Create one with a single call.

```bash
curl --request GET \
     --url 'https://api.themoviedb.org/3/authentication/guest_session/new' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN"
```

```json
{
  "success": true,
  "guest_session_id": "1ce82ec1223641636ad4a60b07de3581",
  "expires_at": "2016-08-27 16:26:40 UTC"
}
```

Pass the value as the `guest_session_id` query parameter on rating endpoints.

```bash
curl --request POST \
     --url 'https://api.themoviedb.org/3/movie/550/rating?guest_session_id=1ce82ec1223641636ad4a60b07de3581' \
     --header "Authorization: Bearer $TMDB_READ_ACCESS_TOKEN" \
     --header 'content-type: application/json' \
     --data '{"value": 8.5}'
```

What a guest session can do:

- Rate a movie, a TV series and a TV episode.
- Keep the rated list of that guest. Read it with `GET /3/guest_session/{guest_session_id}/rated/movies`.

What a guest session cannot do:

- Read or write a real TMDB account.
- Create or edit a custom list.
- Give access to `/3/account` endpoints.

The two documentation pages differ a little. The reference page also names a watchlist and a favourite list for a guest session. The guide page limits a guest session to ratings. Plan for ratings only, and test any other call before you depend on it.

**Expiry:** TMDB deletes a guest session if nobody uses it within 60 minutes. Read `expires_at` from the response, store it, and create a new guest session when the old one expires. Keep the guest session ID private, exactly like a user session ID.

## Secret handling

**Never ship the API key or the read access token in client-side code.** A key in a browser bundle, a mobile application binary or a public repository is a public key. Anybody can read it and spend your rate limit.

| Do | Do not |
| --- | --- |
| Keep the token in an environment variable or a secret manager | Commit `TMDB_READ_ACCESS_TOKEN` to git |
| Proxy TMDB calls through your own backend | Call `api.themoviedb.org` from browser JavaScript with your key |
| Send the credential in the `Authorization` header | Put `api_key=` in a URL that a log or a referrer can capture |
| Store `session_id` encrypted, server-side | Put `session_id` in a cookie that JavaScript can read, or in a URL |
| Rotate the key on the TMDB settings page after a leak | Reuse one session ID for more than one user |

A backend proxy also gives you one place for caching, rate-limit control and error handling.

## Common pitfalls

- **You send only the user credential.** A `session_id` alone fails. Send the application credential on every request as well.
- **The request token expires.** The token is valid for 60 minutes. Create a new one instead of retrying an old one.
- **You reuse a request token.** One token creates one session. Create a new token for each login.
- **You expect `validate_with_login` to return a session.** It returns the request token. You must still call `/3/authentication/session/new`.
- **You send the read access token to `/session/convert/4`.** That endpoint needs a v4 access token that the user approved.
- **You put the session ID in the JSON body of an account call.** Account endpoints read `session_id` from the query string.
- **You drop the body of the DELETE request.** `DELETE /3/authentication/session` needs the JSON body.
- **You trust `success` only.** Check the HTTP status code too. A 401 carries `status_code: 7` for an invalid key.
- **You forget to URL-encode `redirect_to`.** An unencoded callback with its own query string breaks the approval URL.
- **You read the request token from the callback URL.** Read it from your own server-side session instead.
- **You call `/3/authentication` before every request.** Validate once at start-up.
- **You cache one session ID for all users.** Each user needs a separate session ID.

## How this connects to other TMDB topics

| Topic | Link | Relation |
| --- | --- | --- |
| Getting started | [./getting-started.md](./getting-started.md) | Where to request a key, the base URL, rate limits and status codes |
| User account and ratings | [./user-account-and-ratings.md](./user-account-and-ratings.md) | The main consumer of `session_id` and `guest_session_id` |
| Lists | [./lists.md](./lists.md) | Creating and editing a custom list needs a user session |
| Movies | [./movies.md](./movies.md) | `account_states` needs a session; the rest is application level |
| TV series | [./tv-series.md](./tv-series.md) | Same pattern as movies for ratings and account states |
| TV seasons and episodes | [./tv-seasons-and-episodes.md](./tv-seasons-and-episodes.md) | Episode ratings accept a guest session |
| Append to response | [./append-to-response.md](./append-to-response.md) | Combine `account_states` with a detail call in one request |
| Images and configuration | [./images-and-configuration.md](./images-and-configuration.md) | Image URLs need no credential – keep the key out of `<img>` tags |
| Localization | [./localization.md](./localization.md) | `language` and `region` are separate from authentication |
| Search and find | [./search-and-find.md](./search-and-find.md) | Application level only |
| Discover | [./discover.md](./discover.md) | Application level only |
| Trending and popular | [./trending-and-popular.md](./trending-and-popular.md) | Application level only |
| People and credits | [./people-and-credits.md](./people-and-credits.md) | Application level only |
| Entities | [./entities.md](./entities.md) | Shared object shapes in the responses |
| Watch providers | [./watch-providers.md](./watch-providers.md) | Application level only |
| Changes and exports | [./changes-and-exports.md](./changes-and-exports.md) | Application level only |
