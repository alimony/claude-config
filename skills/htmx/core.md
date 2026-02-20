# htmx: Core Concepts
Based on htmx 2.0.8 documentation.

## What htmx Does

htmx extends HTML with attributes that let any element issue AJAX requests and update the DOM. The server returns **HTML fragments**, not JSON.

```html
<button hx-get="/clicked" hx-swap="outerHTML">Click Me</button>
```

---

## AJAX Requests

| Attribute | Method | Example |
|-----------|--------|---------|
| `hx-get` | GET | `hx-get="/search"` |
| `hx-post` | POST | `hx-post="/items"` |
| `hx-put` | PUT | `hx-put="/items/1"` |
| `hx-patch` | PATCH | `hx-patch="/items/1"` |
| `hx-delete` | DELETE | `hx-delete="/items/1"` |

```html
<form hx-post="/contacts" hx-target="#contact-list" hx-swap="beforeend">
  <input name="name" required>
  <button type="submit">Add Contact</button>
</form>
<ul id="contact-list"></ul>
```

---

## Triggers (hx-trigger)

**Defaults**: `input`/`textarea`/`select` trigger on `change`, `form` on `submit`, everything else on `click`.

### Modifiers

| Modifier | Effect |
|----------|--------|
| `once` | Fire only once |
| `changed` | Fire only if value changed |
| `delay:<time>` | Debounce: wait, restart timer on new event |
| `throttle:<time>` | Throttle: fire once per time window |
| `from:<selector>` | Listen on a different element |
| `target:<selector>` | Filter by event target |
| `consume` | Prevent event propagation |
| `queue:<strategy>` | Queue: `first`, `last`, `all`, `none` |

```html
<!-- Debounced search -->
<input hx-get="/search" hx-trigger="keyup changed delay:300ms" hx-target="#results">

<!-- Fire once -->
<div hx-get="/lazy" hx-trigger="click once">Load</div>

<!-- Listen on another element -->
<div hx-get="/updates" hx-trigger="newUpdate from:body">Updates</div>

<!-- Multiple triggers (comma-separated) -->
<input hx-get="/search" hx-trigger="keyup changed delay:500ms, search">
```

### Filters

JavaScript expressions in brackets. Evaluated against the triggering event, then global scope:

```html
<div hx-get="/clicked" hx-trigger="click[ctrlKey]">Ctrl+Click Me</div>
```

### Special Events

```html
<div hx-get="/init" hx-trigger="load">Fire on load</div>
<div hx-get="/lazy" hx-trigger="revealed">Fire when scrolled into view</div>
<img hx-get="/img" hx-trigger="intersect threshold:0.5">
```

### Polling

```html
<div hx-get="/messages" hx-trigger="every 2s"></div>
```

**Stop polling**: server responds with HTTP **286**.

**Load polling** (server-controlled): server returns an identical element to continue, or different markup to stop:

```html
<div hx-get="/progress" hx-trigger="load delay:1s" hx-swap="outerHTML">Checking...</div>
```

---

## Targeting (hx-target)

Controls where response HTML goes. Defaults to the triggering element.

```html
<input hx-get="/search" hx-target="#results">
<div id="results"></div>
```

**Extended selectors**: `this`, `closest <sel>`, `find <sel>`, `next <sel>`, `previous <sel>`

```html
<button hx-get="/details" hx-target="closest tr" hx-swap="outerHTML">View</button>
```

---

## Swapping (hx-swap)

| Strategy | Effect |
|----------|--------|
| `innerHTML` | Replace target's children **(default)** |
| `outerHTML` | Replace entire target element |
| `beforebegin` | Insert before target (sibling) |
| `afterbegin` | Insert as first child |
| `beforeend` | Insert as last child |
| `afterend` | Insert after target (sibling) |
| `delete` | Delete target, ignore response |
| `none` | No swap (OOB swaps still process) |

```html
<!-- Append to list -->
<form hx-post="/items" hx-target="#list" hx-swap="beforeend">
  <input name="item"><button>Add</button>
</form>

<!-- Delete on success -->
<button hx-delete="/items/5" hx-target="closest li" hx-swap="outerHTML">Remove</button>
```

### Swap Modifiers

Space-separated after the strategy:

```html
<button hx-get="/data" hx-swap="innerHTML swap:300ms settle:500ms">Load</button>
<button hx-post="/like" hx-swap="outerHTML transition:true">Like</button>
<div hx-get="/page" hx-swap="innerHTML show:top ignoreTitle:true">Load</div>
```

| Modifier | Effect |
|----------|--------|
| `swap:<time>` | Delay between removing old and inserting new content |
| `settle:<time>` | Delay before settling attributes (default 20ms) |
| `transition:true` | Use View Transitions API |
| `ignoreTitle:true` | Don't update document title from response |
| `scroll:top\|bottom` | Scroll target element |
| `show:top\|bottom` | Scroll element into viewport |
| `focus-scroll:true\|false` | Auto-scroll to focused element |

---

## Out-of-Band Swaps (hx-swap-oob)

Update multiple page regions from a single response. OOB elements are removed from the main response and swapped by matching ID:

```html
<!-- Server response -->
<div id="main-content">Goes to target normally</div>
<div id="notification" hx-swap-oob="true">New message!</div>
<div id="nav-count" hx-swap-oob="innerHTML">42</div>
```

Values: `true` (outerHTML), or any swap strategy. Use `hx-select-oob` to pick elements from response:

```html
<div hx-get="/updates" hx-select-oob="#alert:afterbegin,#count:outerHTML">Load</div>
```

**Table elements**: browsers strip `<tr>` outside `<table>`. Wrap in `<template>`:

```html
<template><tr id="row-5" hx-swap-oob="true"><td>Updated</td></tr></template>
```

**hx-preserve**: keep an element untouched across swaps:

```html
<video id="player" hx-preserve><!-- keeps playing --></video>
```

---

## Request Parameters

Form inputs include their values automatically. Non-GET requests inside a `<form>` include all form inputs.

```html
<!-- Include inputs from elsewhere -->
<button hx-post="/action" hx-include="#extra-field">Submit</button>

<!-- Static extra values -->
<button hx-post="/action" hx-vals='{"key": "value"}'>Go</button>

<!-- Dynamic values (requires allowEval) -->
<button hx-post="/action" hx-vals='js:{count: parseInt(this.dataset.count)}'>Go</button>

<!-- Filter parameters -->
<form hx-post="/save" hx-params="not password">...</form>
<!-- hx-params accepts: *, none, comma-list, or "not" comma-list -->
```

### File Uploads

```html
<form hx-post="/upload" hx-encoding="multipart/form-data">
  <input type="file" name="document"><button>Upload</button>
</form>
```

---

## Request Indicators

htmx adds `htmx-request` class to the triggering element during requests. Child elements with `htmx-indicator` class transition from `opacity:0` to `opacity:1`.

```html
<button hx-get="/data">
  Load <span class="htmx-indicator">Loading...</span>
</button>

<!-- Or point to an external indicator -->
<button hx-get="/data" hx-indicator="#spinner">Load</button>
<img id="spinner" class="htmx-indicator" src="/spinner.gif">

<!-- Disable element during request -->
<button hx-post="/save" hx-disabled-elt="this">Save</button>
```

Custom CSS override:

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
```

---

## CSS Transitions

htmx enables CSS transitions by keeping element IDs stable across swaps:

1. Old element attributes captured
2. New content inserted with old attribute values
3. After settle delay (20ms), new attributes applied -- CSS transition fires

**Transition classes**: `htmx-request` (during request), `htmx-swapping` (swap phase), `htmx-settling` (settle phase), `htmx-added` (new content).

**View Transitions API**: per-element with `hx-swap="outerHTML transition:true"` or globally with `htmx.config.globalViewTransitions = true`.

---

## Synchronization (hx-sync)

Coordinate requests to prevent race conditions:

```html
<input hx-post="/validate" hx-trigger="change" hx-sync="closest form:abort">
<button hx-post="/save" hx-sync="this:drop">Save</button>
<input hx-get="/search" hx-sync="this:replace">
<button hx-post="/action" hx-sync="this:queue last">Go</button>
```

| Strategy | Behavior |
|----------|----------|
| `drop` | Drop new request if one in-flight |
| `abort` | Abort in-flight, send new |
| `replace` | Abort in-flight, send new |
| `queue first\|last\|all` | Queue requests |

**Programmatic abort**: `htmx.trigger(element, 'htmx:abort')`

---

## Inheritance and Boosting

Most `hx-*` attributes **inherit** from parent elements:

```html
<div hx-target="#output" hx-swap="outerHTML">
  <button hx-get="/a">A</button>  <!-- inherits target and swap -->
  <button hx-get="/b">B</button>
</div>
```

Cancel with `hx-confirm="unset"`. Disable per-attribute with `hx-disinherit="hx-target"`. Disable globally: `htmx.config.disableInheritance = true`.

### Boosting (hx-boost)

Convert links and forms to AJAX. Degrades gracefully without JS:

```html
<nav hx-boost="true">
  <a href="/about">About</a>  <!-- AJAX GET, targets body -->
</nav>
```

Server checks `HX-Request` header to return fragment or full page.

---

## History Support

```html
<a hx-get="/page" hx-push-url="true">Push URL</a>
<a hx-get="/page" hx-replace-url="true">Replace URL (no history entry)</a>
```

htmx snapshots DOM before navigation, caches in localStorage. Back/forward restores from cache or re-requests with `HX-History-Restore-Request` header.

**Sensitive pages**: `hx-history="false"` prevents caching.

---

## Validation

htmx integrates with HTML5 Validation API -- invalid forms won't issue requests.

```html
<form hx-post="/save">
  <input name="email" type="email" required>
  <button type="submit">Save</button>
</form>
```

Events: `htmx:validation:validate`, `htmx:validation:failed`, `htmx:validation:halted`.

---

## Confirming Actions

```html
<button hx-delete="/account" hx-confirm="Delete your account?">Delete</button>
```

For custom dialogs (SweetAlert, etc.), listen for `htmx:confirm`, call `evt.preventDefault()`, then `evt.detail.issueRequest()` when confirmed.

---

## Request and Response Headers

### htmx Sends

`HX-Request` (always "true"), `HX-Target`, `HX-Trigger`, `HX-Trigger-Name`, `HX-Current-URL`, `HX-Boosted`, `HX-Prompt`, `HX-History-Restore-Request`.

### Server Can Set

| Header | Effect |
|--------|--------|
| `HX-Redirect` | Client-side redirect (full page) |
| `HX-Location` | AJAX redirect (no full reload) |
| `HX-Push-Url` / `HX-Replace-Url` | Manage browser history |
| `HX-Refresh` | Full page refresh |
| `HX-Retarget` | Change swap target |
| `HX-Reswap` | Override swap strategy |
| `HX-Reselect` | Pick subset of response |
| `HX-Trigger` | Trigger client-side events |
| `HX-Trigger-After-Settle` / `HX-Trigger-After-Swap` | Trigger events at phases |

**Important**: HTTP 3xx redirects are handled by the browser before htmx sees them. Use `HX-Redirect` or `HX-Location` for htmx-controlled redirects.

---

## Events and Integration

```javascript
// Modify requests globally
document.body.addEventListener('htmx:configRequest', function(evt) {
  evt.detail.parameters['auth_token'] = getToken();
  evt.detail.headers['X-Custom'] = 'value';
});

// Initialize libraries on new content (fires on load AND after swaps)
htmx.onLoad(function(target) {
  target.querySelectorAll('.datepicker').forEach(el => new Datepicker(el));
});

// Handle errors
document.body.addEventListener('htmx:responseError', function(evt) {
  showToast('Request failed: ' + evt.detail.xhr.status);
});
```

**Inline events**: `hx-on:htmx:after-request="this.reset()"` (kebab-case for attribute names).

**Process dynamic content**: call `htmx.process(element)` on HTML inserted via fetch/innerHTML.

**Debugging**: `htmx.logAll()` logs all events to console.

---

## Response Handling Configuration

Control how htmx handles status codes:

```html
<meta name="htmx-config" content='{
  "responseHandling": [
    {"code": "204", "swap": false},
    {"code": "[23]..", "swap": true},
    {"code": "422", "swap": true},
    {"code": "[45]..", "swap": false, "error": true}
  ]
}'/>
```

Common: swap on 422 to show server-rendered validation errors.

---

## Security

**Always escape untrusted content.** htmx swaps raw HTML -- unescaped user input means XSS.

**hx-disable**: prevent htmx processing in a subtree (for user-generated content):

```html
<div hx-disable><%= raw(user_content) %></div>
```

**CSRF tokens** -- set globally via inheritance or event:

```html
<body hx-headers='{"X-CSRFToken": "TOKEN_VALUE"}'>
```

```javascript
document.body.addEventListener('htmx:configRequest', function(evt) {
  evt.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});
```

**Security options**: `selfRequestsOnly` (default true), `allowScriptTags` (default true), `allowEval` (default true). Set `allowEval: false` for strict CSP.

---

## Configuration

Set via meta tag: `<meta name="htmx-config" content='{"defaultSwapStyle": "outerHTML"}'>` or JavaScript.

| Option | Default | Description |
|--------|---------|-------------|
| `defaultSwapStyle` | `innerHTML` | Default swap strategy |
| `defaultSwapDelay` | `0` | Delay before swap (ms) |
| `defaultSettleDelay` | `20` | Delay before settle (ms) |
| `historyCacheSize` | `10` | Pages cached (0 = disabled) |
| `refreshOnHistoryMiss` | `false` | Full page load on cache miss |
| `includeIndicatorStyles` | `true` | Inject default indicator CSS |
| `globalViewTransitions` | `false` | Use View Transitions API globally |
| `selfRequestsOnly` | `true` | Restrict to same-origin |
| `allowEval` | `true` | Enable eval-dependent features |
| `allowScriptTags` | `true` | Process script tags in responses |
| `getCacheBusterParam` | `false` | Add cache-buster to GET requests |
| `disableInheritance` | `false` | Disable attribute inheritance |
| `timeout` | `0` | Request timeout (ms, 0 = none) |
| `scrollBehavior` | `instant` | `smooth` or `instant` |
| `ignoreTitle` | `false` | Ignore `<title>` in responses |
| `methodsThatUseUrlParams` | `["get","delete"]` | Methods encoding params in URL |

CSS class names are configurable: `indicatorClass`, `requestClass`, `addedClass`, `settlingClass`, `swappingClass`.

---

## Best Practices

1. **Return HTML, not JSON.** htmx swaps HTML. Returning JSON means raw JSON text in the DOM.
2. **Use progressive enhancement.** Boosted links/forms work without JS. Check `HX-Request` server-side.
3. **Keep element IDs stable.** CSS transitions and OOB swaps depend on matching IDs.
4. **Set `Vary: HX-Request`** on responses that differ for htmx vs. normal requests.
5. **Escape all user content.** No auto-escaping -- your server templates must handle this.
6. **Validate server-side.** HTML5 validation is UX, not security.
7. **Use hx-sync for search inputs.** Prevents race conditions from fast typing.
8. **Scope hx-boost.** Apply to containers, not the whole body, unless intentional.

## Common Pitfalls

1. **JSON responses.** Endpoints must return HTML fragments, not JSON.
2. **Missing OOB IDs.** OOB elements need an `id` matching an existing DOM element. No match = silently dropped.
3. **3xx redirects bypass htmx.** Browser handles them internally. Use `HX-Redirect`/`HX-Location` response headers.
4. **Table elements in OOB.** Browsers strip `<tr>`/`<td>` outside `<table>`. Wrap in `<template>`.
5. **Forgetting `htmx.process()`.** Dynamic HTML with `hx-*` attributes needs processing.
6. **Cache poisoning.** Same URL returning different content for htmx vs. browser -- set `Vary: HX-Request`.
7. **History cache leaks.** htmx stores snapshots in localStorage. Use `hx-history="false"` for sensitive pages.
8. **Polling that never stops.** Use HTTP 286 to stop, or load polling for server-controlled termination.
9. **CSP conflicts.** Trigger filters, `hx-on`, `js:` prefixes need eval. `allowEval: false` silently disables them.
