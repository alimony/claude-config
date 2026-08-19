# Letterboxd API: Authentication
Based on Letterboxd API v0 documentation.

## Read this first: pick the correct flow

The Letterboxd API supports four standard OAuth2 flows: Password, Client Credentials, Authorization Code and Refresh Token.

**The Password flow is for first-party clients only. Letterboxd's own apps use it. Your app must not use it.**

Many old tutorials, blog posts and legacy libraries still send `grant_type=password` with a member's username and password. That code is obsolete for third-party clients. Do not copy it. Do not ask a member for a Letterboxd password. Use the Authorization Code flow instead.

A third-party client has two legal choices:

| Flow | Grant type | What you get |
|---|---|---|
| Client Credentials | `client_credentials` | Public data only. No member context. |
| Authorization Code | `authorization_code` | A member's context. Private content and write operations. |

### "I want to ... " decision table

| I want to ... | Use this flow | Notes |
|---|---|---|
| Read public film data, cast and crew, public lists | Client Credentials | No member consent. No refresh token needed. |
| Search the public catalogue | Client Credentials | Same as above. |
| Read a member's public profile by LID | Client Credentials | Public fields only. |
| Call `/me` or any endpoint with the `user` scope | Authorization Code | The member must sign in and consent. |
| Read a member's watchlist, diary or private lists | Authorization Code | Add `profile:private:view`. |
| Write a diary entry, a review, a rating or a list | Authorization Code | Add `content:modify`. |
| Change a member's profile details | Authorization Code | Add `profile:modify`. |
| Change a member's password or email address | Authorization Code | Add `security:modify`. |
| Keep a session alive for days or weeks | Authorization Code | Add `oauth:refresh`. |
| Verify who the member is with an ID token | Authorization Code | Add `openid`, and `profile` or `email`. |
| Sign a member in with a username and a password | **Nothing. Stop.** | The Password flow is first-party only. |

### Endpoints

| Purpose | URL |
|---|---|
| Authorize (Authorization Code flow) | `https://api.letterboxd.com/api/v0/auth/authorize` |
| Token (all flows) | `https://api.letterboxd.com/api/v0/auth/token` |
| Refresh | `https://api.letterboxd.com/api/v0/auth/token` |
| API base | `https://api.letterboxd.com/api/v0/` |
| OIDC discovery | `https://letterboxd.com/.well-known/openid-configuration` |

## Token endpoint mechanics

Send every token request as a form POST. Set both headers.

| Header | Value |
|---|---|
| `Content-Type` | `application/x-www-form-urlencoded` |
| `Accept` | `application/json` |

Do not send JSON to `/auth/token`. The endpoint reads form fields.

URL encode every form field and every query parameter. See "URL encode all parameters" below.

### Client Credentials: the fields

| Field | Required | Value |
|---|---|---|
| `grant_type` | Yes | `client_credentials` |
| `client_id` | Yes | Your API key |
| `client_secret` | Yes | Your API secret |
| `audience` | **No** | The `audience` parameter from generic OAuth2 documentation is not required here. Do not send it. |

### Client Credentials with curl

```bash
curl -sS -X POST 'https://api.letterboxd.com/api/v0/auth/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: application/json' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode "client_id=$LETTERBOXD_CLIENT_ID" \
  --data-urlencode "client_secret=$LETTERBOXD_CLIENT_SECRET"
```

`--data-urlencode` does the URL encoding for you. Use it, and not `-d`, if a value contains a special character.

### Client Credentials with Python

```python
import time
import requests

TOKEN_URL = "https://api.letterboxd.com/api/v0/auth/token"
API_BASE = "https://api.letterboxd.com/api/v0"


FORM_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}
_cache = {"token": None, "expires_at": 0.0}


def app_token(client_id: str, client_secret: str) -> str:
    """Get an application token for public data, and hold it until it expires."""
    # Get a new token 60 seconds before the old token expires.
    if _cache["token"] and time.time() < _cache["expires_at"] - 60:
        return _cache["token"]
    response = requests.post(
        TOKEN_URL,
        # requests URL encodes the form body when you pass a dict to data=.
        # Do not send the audience parameter. This flow does not need it.
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers=FORM_HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    _cache["token"] = payload["access_token"]
    _cache["expires_at"] = time.time() + int(payload["expires_in"])
    return _cache["token"]


films = requests.get(
    f"{API_BASE}/films",
    headers={
        "Authorization": f"Bearer {app_token('YOUR_ID', 'YOUR_SECRET')}",
        "Accept": "application/json",
    },
    params={"perPage": 5},
    timeout=15,
).json()
```

### The token response

The documentation gives the `expires_in` attribute by name. It does not publish a full schema for the token response. Expect the standard OAuth2 fields:

| Field | Meaning |
|---|---|
| `access_token` | The bearer token. Put it in the `Authorization` header. |
| `token_type` | `Bearer`. |
| `expires_in` | The lifetime in seconds. Count from the moment of the response. |
| `refresh_token` | Present only when the token carries the `oauth:refresh` scope. |
| `id_token` | Present only when you request the `openid` scope. |

Read `expires_in` from the response. Do not hard-code a lifetime.

## Authorization Code flow

Use this flow for any operation that needs member authentication. Complete the four steps in order.

### Step 1: send the member to the authorize URL

Build the URL with these query parameters. URL encode each value.

| Parameter | Value |
|---|---|
| `response_type` | `code` |
| `client_id` | Your API key |
| `redirect_uri` | Your registered callback URL, URL encoded |
| `scope` | A space- or plus-delimited scope string, URL encoded |
| `state` | A random value that you keep. Check it in step 2. |

```
https://api.letterboxd.com/api/v0/auth/authorize?response_type=code&client_id=YOUR_ID&redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback&scope=content%3Amodify%20profile%3Aprivate%3Aview%20oauth%3Arefresh&state=8f1c2a
```

```python
from urllib.parse import urlencode
import secrets

state = secrets.token_urlsafe(24)
query = urlencode({
    "response_type": "code",
    "client_id": "YOUR_ID",
    "redirect_uri": "https://app.example.com/callback",
    "scope": "content:modify profile:private:view oauth:refresh",
    "state": state,
})
# urlencode escapes the colons and the slashes for you.
authorize_url = f"https://api.letterboxd.com/api/v0/auth/authorize?{query}"
```

The member signs in on the Letterboxd page. Letterboxd shows the extra scopes that you request. The member agrees or refuses.

### Step 2: receive the code at your redirect URI

Letterboxd sends the member back to your `redirect_uri` with `code` and `state` in the query string.

Compare the returned `state` with the value that you kept. Reject the request if the two values are different.

### Step 3: exchange the code for a token

```bash
curl -sS -X POST 'https://api.letterboxd.com/api/v0/auth/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: application/json' \
  --data-urlencode 'grant_type=authorization_code' \
  --data-urlencode "code=$AUTH_CODE" \
  --data-urlencode "client_id=$LETTERBOXD_CLIENT_ID" \
  --data-urlencode "client_secret=$LETTERBOXD_CLIENT_SECRET" \
  --data-urlencode 'redirect_uri=https://app.example.com/callback'
```

```python
response = requests.post(
    "https://api.letterboxd.com/api/v0/auth/token",
    data={
        "grant_type": "authorization_code",
        "code": code_from_callback,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        # Send the same redirect_uri that you sent in step 1.
        "redirect_uri": "https://app.example.com/callback",
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    },
    timeout=15,
)
response.raise_for_status()
tokens = response.json()
```

### Step 4: refresh before the token expires

```bash
curl -sS -X POST 'https://api.letterboxd.com/api/v0/auth/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: application/json' \
  --data-urlencode 'grant_type=refresh_token' \
  --data-urlencode "refresh_token=$REFRESH_TOKEN" \
  --data-urlencode "client_id=$LETTERBOXD_CLIENT_ID" \
  --data-urlencode "client_secret=$LETTERBOXD_CLIENT_SECRET"
```

### URL encode all parameters

All query and form parameters must be URL encoded. The `redirect_uri` parameter causes the most failures, because it contains `:` and `/` characters.

| Do this | Do not do this |
|---|---|
| `redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback` | `redirect_uri=https://app.example.com/callback` in a hand-built query string |
| Use `urlencode()`, `URLSearchParams` or `--data-urlencode` | Concatenate strings with `+` and hope |
| Send the identical `redirect_uri` in step 1 and step 3 | Add or remove a trailing slash between the two steps |
| Register the exact callback URL with Letterboxd first | Use `http://` locally when you registered `https://` |
| URL encode the scope string, for example `content%3Amodify` | Send raw spaces in the query string |

A tool such as `requests` or `URLSearchParams` encodes the form body for you. Do not encode a value twice. Double encoding turns `%3A` into `%253A` and the match fails.

## Use the token

Add this header to every request to an endpoint that shows *oauth2* security:

```
Authorization: Bearer [TOKEN]
```

```bash
curl -sS 'https://api.letterboxd.com/api/v0/me' \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Accept: application/json'
```

Do not put the token in a query parameter. Do not put the token in a cookie.

## Expiry, refresh and revocation

| Rule | Action |
|---|---|
| Refresh before the token expires | Read `expires_in`, calculate the expiry time, and refresh before it. |
| The token expired | Repeat the full auth flow. A refresh is no longer possible. |
| You want a refresh token | Request the `oauth:refresh` scope. Without that scope you get no refresh token. |
| The member signs out | Revoke the access token and the refresh token. |

Refresh early. A margin of 60 seconds protects you against clock drift and slow networks.

Letterboxd uses standard OAuth2 Token Revocation. Revoke the access token and the refresh token when the member signs out. The documentation does not publish the path of the revocation endpoint. Read `revocation_endpoint` from the OIDC discovery document, and send the standard revocation form fields (`token`, `token_type_hint`, `client_id`, `client_secret`).

Delete the stored tokens from your database after a revocation.

## Scopes

A scope is a security requirement. An endpoint states the scopes that it needs. The scopes attach to the access token.

The auth flow grants some scopes automatically. You do not request those. Letterboxd shows the extra scopes to the member, and grants them if the member agrees.

Request multiple scopes as a space- or plus-delimited string. Both forms are valid: `profile:modify content:modify` or `profile:modify+content:modify`. URL encode the string.

| Scope | Requestable | Meaning |
|---|---|---|
| `user:owner` | **No** | The caller must be the owner of the member account. The flow grants it. |
| `user` | **No** | The caller must be a Letterboxd member. The flow grants it. |
| `client:firstparty` | **No** | The caller must be a first-party client. Third-party apps never get it. |
| `cache:modify` | **No** | Update or clear a cache through the API, namely the hibernate cache. |
| `profile:private:view` | Yes | View profile information for the member, private information included. |
| `profile:modify` | Yes | Modify profile details for the member. |
| `security:modify` | Yes | Modify security details for the member. |
| `content:modify` | Yes | Modify content that belongs to the member. |
| `oauth:refresh` | Yes | Use refresh tokens. The token response then contains a refresh token. |
| `openid` | Yes | Create OIDC ID tokens. OIDC verifies the identity of the member. |
| `profile` | Yes | Put the profile details of the member in the ID token: username, display name, website link and bio. |
| `email` | Yes | Put the email address of the member in the ID token, with a validation indication. |

The four scopes marked **No** cannot be requested. Do not put them in a `scope` parameter. An endpoint that lists `user` or `user:owner` in its security section works after a normal Authorization Code sign-in. An endpoint that lists `client:firstparty` is closed to third-party clients.

Request the minimum set of scopes. A long consent screen makes members refuse.

## OpenID Connect

Letterboxd supports OpenID Connect (OIDC). Use OIDC to verify the identity of the member.

| Scope | Effect |
|---|---|
| `openid` | Letterboxd creates an ID token. |
| `profile` | The ID token contains username, display name, website link and bio. |
| `email` | The ID token contains the email address and a validation flag. |

Read the discovery document for the issuer, the JWKS URI, the supported claims and the endpoint paths:

```bash
curl -sS 'https://letterboxd.com/.well-known/openid-configuration' | jq .
```

Verify the signature of the ID token against the JWKS keys. Check the issuer, the audience and the expiry. Do not trust an unverified ID token.

## Do not sign requests

Letterboxd previously required a signature on all API requests. **Letterboxd removed that requirement.**

Legacy implementers must delete the old HMAC-SHA256 signing code. Delete the `apikey`, `nonce`, `timestamp` and `signature` query parameters. Delete the shared-secret digest step.

| Do this | Do not do this |
|---|---|
| Send `Authorization: Bearer [TOKEN]` | Append a `signature` query parameter |
| Keep the client secret for the token request only | Compute an HMAC over the request URL and body |
| Copy an example from the current documentation | Copy an example from a 2017 blog post |

## The /auth/* helper endpoints

| Endpoint | Method | Security | First party only | What it does |
|---|---|---|---|---|
| `/auth/username-check` | GET | oauth2, no scope | No | Check the validity and the availability of a username. |
| `/auth/forgotten-password-request` | POST | oauth2, no scope | No | Send a password reset link to an email address. |
| `/auth/get-login-token` | GET | oauth2, `user:owner` | No, but it needs a member token | Create a single-use token that signs the member into the website. |
| `/auth/get-upload-url` | GET | oauth2, `user`, `client:firstparty` | **Yes** | Create a single-use URL for a member data file upload. |

### GET /auth/username-check

Operation ID `checkUsername`. Pass the required `username` query parameter. A username must be 2 to 15 characters long. A username may contain upper or lowercase letters, numbers and the underscore (`_`) character only.

The `UsernameCheckResponse` returns a `result` field with one of these values: `Available`, `NotAvailable`, `TooShort`, `TooLong`, `Invalid`. `NotAvailable` also covers a deactivated or a reserved account. Letterboxd does not release the usernames of deactivated accounts automatically.

```bash
curl -sS 'https://api.letterboxd.com/api/v0/auth/username-check?username=dave' \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Accept: application/json'
```

### POST /auth/forgotten-password-request

Operation ID `forgottenPasswordRequest`. Send a JSON body with the `emailAddress` field.

| Status | Meaning |
|---|---|
| 204 | Success. Letterboxd sent the email if the address matched an account. |
| 400 | Bad request. See `ErrorResponse`. |
| 429 | Too many requests for this address. Tell the member to check the spam folder. |

A 204 does not prove that an account exists. Letterboxd hides that fact on purpose.

### GET /auth/get-login-token

Operation ID `getLoginTokenRequest`. Needs the `user:owner` scope, so it needs an Authorization Code token. The `LoginTokenResponse` contains a single-use `token`. Pass that token as the `urt` query parameter on a letterboxd.com URL to sign the member into the website.

Use this endpoint to move a member from your app to the website without a second sign-in. The token works one time only.

### GET /auth/get-upload-url

Operation ID `getUploadUrl`. Needs `user` **and** `client:firstparty`. **A third-party client cannot call this endpoint.** The `client:firstparty` scope cannot be requested. The `UploadUrlResponse` contains a single-use `url` for a data file upload.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| 401 on every call | No `Authorization` header, or the header has no `Bearer ` prefix | Send `Authorization: Bearer [TOKEN]`. |
| 401 after some hours | The access token expired | Refresh earlier, or repeat the flow. |
| The token response has no `refresh_token` | You did not request `oauth:refresh` | Add `oauth:refresh` to the scope string. |
| `invalid_grant` at the code exchange | The `redirect_uri` differs between step 1 and step 3 | Send the identical, URL encoded value both times. |
| `invalid_request` at the token endpoint | You sent a JSON body | Send `application/x-www-form-urlencoded`. |
| 403 on a first-party endpoint | The endpoint needs `client:firstparty` | Stop. No third-party route exists. |
| A member sees a scope error | You requested `user`, `user:owner`, `client:firstparty` or `cache:modify` | Remove those scopes from the request. |
| A 2016 library fails | The library still signs requests | Delete the signing code. Use plain OAuth2. |

## Relationships

- **overview.md** – the base URL, the LID identifier scheme, the request and response rules, the pagination limits, and the meaning of the "First Party" mark.
- **me.md** – the `/me` endpoints. Every one of them needs an Authorization Code token. `/me` needs `user`. The write endpoints add `content:modify`, `profile:modify` or `security:modify`. Some `/me` endpoints add `client:firstparty` and stay closed to third-party clients.
