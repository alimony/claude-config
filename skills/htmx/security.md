# htmx: Security & Configuration
Based on htmx 2.0.8 documentation.

## Security Model

htmx swaps HTML from server responses directly into the DOM. This means the server's response is **trusted markup** -- it executes scripts, applies attributes, and modifies the page. Security depends on:

1. Only requesting routes you control
2. Never injecting unsanitized user content into responses
3. Treating server-rendered HTML with the same care as any other executable code

Unlike JSON APIs where the client decides what to render, htmx gives the server full control over the DOM. This simplifies architecture but means a compromised or untrusted endpoint can inject arbitrary HTML and scripts.

**Four rules for htmx security:**

1. Only call routes you control -- htmx inserts responses directly into the page
2. Always use auto-escaping template engines (Django, Jinja2, etc.)
3. Only serve user-generated content inside HTML element bodies -- never in script tags, style blocks, attribute names, or tag names
4. Secure authentication cookies with `Secure`, `HttpOnly`, and `SameSite=Lax`

---

## CSRF Protection

### Using hx-headers on a Parent Element

Apply CSRF headers globally via the `<body>` or `<html>` tag. All htmx requests from child elements inherit these headers.

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    <!-- all htmx requests include the CSRF header -->
</body>
```

### Using a Meta Tag (Django Example)

```html
<meta name="csrf-token" content="{{ csrf_token }}">
```

```javascript
document.body.addEventListener("htmx:configRequest", function (evt) {
    evt.detail.headers["X-CSRFToken"] = document.querySelector(
        'meta[name="csrf-token"]'
    ).content;
});
```

### Django-Specific Pattern

Django's CSRF middleware checks `X-CSRFToken` header for AJAX. With htmx:

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

Or read from the cookie (when `CSRF_COOKIE_HTTPONLY = False`):

```javascript
document.body.addEventListener("htmx:configRequest", function (evt) {
    if (evt.detail.verb !== "get") {
        evt.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
    }
});
```

### hx-boost and CSRF Tokens

`hx-boost` does **not** update `<html>` or `<body>` attributes on navigation. If you place `hx-headers` on these elements, the CSRF token will go stale after Django rotates it (e.g., on login). Solutions:

- Place the token in a `<meta>` tag and read it via `htmx:configRequest`
- Use Django's `{% csrf_token %}` hidden input inside each form
- Place `hx-headers` on elements that get swapped/refreshed

### SameSite Cookies

`SameSite=Lax` on authentication cookies prevents most CSRF attacks by blocking cross-site cookie transmission on non-GET requests. This is sufficient for most applications but only works at the domain level -- subdomains like `yoursite.github.io` are not protected.

---

## Content Security Policy (CSP)

### The Challenge

htmx uses `eval()` internally for several features. A strict CSP that blocks `unsafe-eval` will break:

- `hx-on:*` inline event handlers
- Event filter expressions (e.g., `hx-trigger="click[ctrlKey]"`)
- `hx-vals='js:{...}'` dynamic values
- `hx-headers='js:{...}'` dynamic headers

### Nonce-Based Approach

Configure htmx to add nonces to inline scripts and styles it generates:

```html
<meta name="htmx-config" content='{"inlineScriptNonce": "{{ csp_nonce }}"}'>
```

This adds the nonce to any `<script>` tags htmx processes from swapped content.

```html
<!-- CSP header or meta tag -->
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self' 'nonce-{{ csp_nonce }}';">
```

### Disabling eval Entirely

For strict CSP compliance, disable eval:

```html
<meta name="htmx-config" content='{"allowEval": false}'>
```

When `allowEval` is `false`, these features stop working:
- `hx-on:*` attributes (use `addEventListener` in JS instead)
- Event filter expressions in `hx-trigger`
- `js:` prefix in `hx-vals` and `hx-headers`

Replacement pattern for `hx-on`:

```html
<!-- Instead of this: -->
<button hx-on:click="alert('clicked')">Click</button>

<!-- Use standard JS: -->
<button id="my-btn" hx-get="/endpoint">Click</button>
<script nonce="{{ csp_nonce }}">
    document.getElementById("my-btn").addEventListener("click", function () {
        alert("clicked");
    });
</script>
```

### Style Nonce

If your CSP restricts inline styles:

```html
<meta name="htmx-config" content='{"inlineStyleNonce": "{{ csp_nonce }}"}'>
```

---

## XSS Prevention

### The Core Risk

htmx swaps raw HTML into the DOM. If that HTML contains unsanitized user input, you have XSS. This is the **same risk** as any server-rendered application -- htmx does not make it worse or better, but you must be aware that partial responses are just as dangerous as full-page renders.

### Auto-Escaping is Mandatory

Always use your template engine's auto-escaping:

```html
<!-- SAFE: auto-escaped -->
<td>{{ user.name }}</td>

<!-- DANGEROUS: bypasses escaping -->
<td>{{ user.name|safe }}</td>
<td>{% autoescape off %}{{ user.name }}{% endautoescape %}</td>
```

### Dangerous Contexts

Even with escaping, these contexts require extra care:

```html
<!-- DANGEROUS: user data in attribute without quotes -->
<div class={{ user_input }}>  <!-- XSS vector -->
<div class="{{ user_input }}">  <!-- safer, but still risky in href/src -->

<!-- DANGEROUS: user data in script blocks -->
<script>var name = "{{ user_input }}";</script>  <!-- escaping may not help -->

<!-- DANGEROUS: user data in CSS -->
<style>.thing { background: {{ user_input }}; }</style>

<!-- DANGEROUS: user data in URLs -->
<a hx-get="{{ user_url }}">  <!-- can hit attacker-controlled endpoints -->
```

### What to Escape

Replace these characters with HTML entities in user content: `&`, `<`, `>`, `"`, `'`, `/`, `` ` ``, `=`.

---

## hx-disable

Prevents htmx from processing any element within a subtree. Use this to safely render user-generated HTML content.

```html
<div hx-disable>
    {{ raw_user_content }}
</div>
```

**How it works:** htmx checks the entire parent hierarchy when initializing elements. Even if an attacker injects `hx-get` or other htmx attributes, they will not be processed inside an `hx-disable` subtree. The check cannot be bypassed by injected content.

**Custom disable selector:** Change which selector disables processing:

```html
<meta name="htmx-config" content='{"disableSelector": "[hx-disable], [data-hx-disable], .no-htmx"}'>
```

---

## Configuration Reference

Set configuration via a meta tag:

```html
<meta name="htmx-config" content='{"selfRequestsOnly": true, "allowScriptTags": false}'>
```

Or in JavaScript:

```javascript
htmx.config.selfRequestsOnly = true;
htmx.config.allowScriptTags = false;
```

### Security-Critical Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `selfRequestsOnly` | `true` | Only allows AJAX requests to the same domain as the page. **Keep this `true` unless you have a specific reason.** |
| `allowScriptTags` | `true` | Processes `<script>` tags found in swapped content. Set to `false` if you serve any untrusted HTML. |
| `allowEval` | `true` | Enables features that use `eval()`: event filters, `hx-on:*`, `js:` prefix. Set to `false` for strict CSP. |
| `inlineScriptNonce` | `''` | Nonce added to inline `<script>` tags htmx processes. Required for CSP with script nonces. |
| `inlineStyleNonce` | `''` | Nonce added to inline `<style>` elements htmx generates. Required for CSP with style nonces. |
| `historyCacheSize` | `10` | Pages cached in localStorage. Set to `0` to disable caching entirely (avoids storing sensitive data). |
| `withCredentials` | `false` | Sends cookies/auth on cross-origin requests. Only enable if you understand CORS implications. |
| `disableSelector` | `[hx-disable], [data-hx-disable]` | CSS selector for subtrees where htmx is disabled. Extend to cover more areas. |

### URL Validation Event

For fine-grained control over which URLs htmx can request:

```javascript
document.body.addEventListener("htmx:validateUrl", function (evt) {
    // Allow same-host and one trusted API
    if (!evt.detail.sameHost && evt.detail.url.hostname !== "api.example.com") {
        evt.preventDefault();
    }
});
```

### All Configuration Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `historyEnabled` | `true` | Enable history push/pop support |
| `historyCacheSize` | `10` | Number of pages stored in history cache (0 to disable) |
| `refreshOnHistoryMiss` | `false` | Full page refresh instead of AJAX on history cache miss |
| `defaultSwapStyle` | `innerHTML` | Default swap strategy |
| `defaultSwapDelay` | `0` | Delay in ms before swap |
| `defaultSettleDelay` | `20` | Delay in ms before settling |
| `includeIndicatorStyles` | `true` | Include default indicator CSS |
| `indicatorClass` | `htmx-indicator` | Class for request indicators |
| `requestClass` | `htmx-request` | Class added during requests |
| `addedClass` | `htmx-added` | Class for newly added content |
| `settlingClass` | `htmx-settling` | Class during settling phase |
| `swappingClass` | `htmx-swapping` | Class during swapping phase |
| `allowEval` | `true` | Allow eval-based features |
| `allowScriptTags` | `true` | Process script tags in responses |
| `inlineScriptNonce` | `''` | Nonce for inline scripts |
| `inlineStyleNonce` | `''` | Nonce for inline styles |
| `attributesToSettle` | `["class", "style", "width", "height"]` | Attributes merged during settle |
| `useTemplateFragments` | `false` | Use `<template>` for HTML parsing |
| `wsReconnectDelay` | `full-jitter` | WebSocket reconnection strategy |
| `wsBinaryType` | `blob` | WebSocket binary type |
| `disableSelector` | `[hx-disable], [data-hx-disable]` | Selector to disable htmx processing |
| `withCredentials` | `false` | Send credentials on cross-origin requests |
| `timeout` | `0` | Request timeout in ms (0 = no timeout) |
| `scrollBehavior` | `instant` | Scroll behavior (`instant` or `smooth`) |
| `defaultFocusScroll` | `false` | Auto-scroll to focused element |
| `getCacheBusterParam` | `false` | Add cache-buster to GET requests |
| `globalViewTransitions` | `false` | Use View Transitions API globally |
| `methodsThatUseUrlParams` | `["get", "delete"]` | Methods that encode params in URL |
| `selfRequestsOnly` | `true` | Restrict to same-domain requests |
| `ignoreTitle` | `false` | Ignore `<title>` in responses |
| `disableInheritance` | `false` | Disable attribute inheritance |
| `scrollIntoViewOnBoost` | `true` | Scroll on boosted navigation |
| `triggerSpecsCache` | `null` | Cache for trigger specifications |
| `allowNestedOobSwaps` | `true` | Process OOB swaps in nested elements |
| `responseHandling` | (see below) | Custom response code handling |

### Response Handling Configuration

Override how htmx handles HTTP status codes:

```javascript
htmx.config.responseHandling = [
    { code: "204", swap: false },
    { code: "[23]..", swap: true },
    { code: "422", swap: true, error: true },  // swap validation errors
    { code: "[45]..", swap: false, error: true },
];
```

Or handle per-request via the `htmx:beforeSwap` event:

```javascript
document.body.addEventListener("htmx:beforeSwap", function (evt) {
    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }
});
```

---

## Browser Quirks

### Attribute Inheritance

htmx attributes on parent elements are inherited by children. This can cause unexpected behavior when a parent has `hx-target` or `hx-swap` that children inherit unintentionally. Disable globally with `htmx.config.disableInheritance = true`, then use `hx-inherit` to opt in where needed.

### Body Element Always Uses innerHTML

Targeting `<body>` always performs an `innerHTML` swap regardless of `hx-swap`. You cannot modify body attributes via htmx responses.

### Error Responses Don't Swap

Status codes 400+ and 500+ are **not swapped** by default. To display server-rendered validation errors (e.g., 422), configure `responseHandling` or use the `htmx:beforeSwap` event (see above).

### GET Requests Exclude Form Values

GET requests do **not** include values from an enclosing `<form>`. Use `hx-include="closest form"` to include them:

```html
<form>
    <input name="q" type="text">
    <button hx-get="/search" hx-include="closest form">Search</button>
</form>
```

### hx-boost Limitations

`hx-boost` converts links and forms to AJAX but:

- Does not update `<html>` or `<body>` attributes (CSRF tokens placed there go stale)
- Discards new page `<link>` and `<script>` tags outside the swapped area
- Does not refresh global JavaScript state

### History Cache Security

`historyCacheSize` stores page HTML in `localStorage`. This can expose sensitive data if the browser is shared. Set to `0` on pages with private content, or use `hx-history="false"` on individual pages:

```html
<body hx-history="false">
    <!-- this page will not be cached in localStorage -->
</body>
```

### Load htmx Synchronously

htmx must be loaded with a standard blocking `<script>` tag. Async loading, deferred loading, or ES module imports may cause initialization failures:

```html
<!-- CORRECT -->
<script src="/static/htmx.min.js"></script>

<!-- MAY FAIL -->
<script src="/static/htmx.min.js" defer></script>
<script type="module">import "htmx.org";</script>
```

---

## Server-Side Considerations

### Validate the HX-Request Header

htmx sends `HX-Request: true` on every request. Use this to distinguish htmx requests from full-page navigations -- but **never use it as a security boundary**. Headers are trivially spoofable.

```python
# Django example
def my_view(request):
    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/content.html", context)
    return render(request, "full_page.html", context)
```

### Protect Partial Endpoints

Endpoints that return HTML fragments need the **same authentication and authorization** as full-page views. A partial endpoint is not "internal" -- it is a regular HTTP endpoint anyone can call.

```python
# Every htmx endpoint needs auth checks
@login_required
def user_list_partial(request):
    users = User.objects.filter(organization=request.user.organization)
    return render(request, "partials/user_list.html", {"users": users})
```

### Don't Over-Expose Data

HTML responses naturally limit exposure to rendered fields. Unlike JSON APIs that may serialize entire model objects, templates explicitly choose what to display. This is a security advantage -- maintain it by not adding hidden fields or data attributes with sensitive values.

### Response Headers for htmx

Useful response headers htmx recognizes:

| Header | Purpose |
|--------|---------|
| `HX-Redirect` | Client-side redirect to URL |
| `HX-Refresh` | Full page refresh when `true` |
| `HX-Retarget` | Override the target element |
| `HX-Reswap` | Override the swap strategy |
| `HX-Trigger` | Trigger client-side events |
| `HX-Push-Url` | Push URL into browser history |
| `HX-Replace-Url` | Replace current URL without history entry |

---

## Recommended Secure Defaults

A conservative starting configuration for production:

```html
<meta name="htmx-config" content='{
    "selfRequestsOnly": true,
    "allowScriptTags": false,
    "historyCacheSize": 0,
    "allowEval": false,
    "inlineScriptNonce": "{{ csp_nonce }}"
}'>
```

This disables script processing, eval, and history caching. Re-enable features as needed -- each one you enable is a security surface to reason about.

**If you need `allowScriptTags`** (e.g., for inline scripts in responses), ensure every response comes from your own server and all user data is escaped.

**If you need `allowEval`** (e.g., for `hx-on:*` or event filters), you cannot use a strict CSP without `unsafe-eval`. Consider whether `addEventListener` in a separate script block is acceptable instead.
