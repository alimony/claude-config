# htmx: Attributes Reference
Based on htmx 2.0.8 documentation.

## Quick Reference

| Attribute | Purpose | Inherited |
|-----------|---------|-----------|
| `hx-get` | Issues GET request | No |
| `hx-post` | Issues POST request | No |
| `hx-put` | Issues PUT request | No |
| `hx-patch` | Issues PATCH request | No |
| `hx-delete` | Issues DELETE request | No |
| `hx-trigger` | Specifies triggering event | No |
| `hx-target` | Specifies swap target element | Yes |
| `hx-swap` | Controls how response is swapped in | Yes |
| `hx-swap-oob` | Out-of-band swap (update multiple elements) | No |
| `hx-sync` | Synchronizes concurrent requests | Yes |
| `hx-select` | Filters response content via CSS selector | Yes |
| `hx-select-oob` | Out-of-band selection from response | Yes |
| `hx-include` | Includes additional input values | Yes |
| `hx-params` | Filters submitted parameters | Yes |
| `hx-vals` | Adds static/dynamic values to request | Yes |
| `hx-vars` | Adds dynamic values (deprecated, use hx-vals) | Yes |
| `hx-headers` | Adds custom request headers | Yes |
| `hx-encoding` | Changes request encoding | Yes |
| `hx-request` | Configures request options | Yes (merge) |
| `hx-indicator` | Shows loading indicator | Yes |
| `hx-disabled-elt` | Disables elements during request | Yes |
| `hx-confirm` | Shows confirmation dialog | Yes |
| `hx-prompt` | Shows prompt dialog | Yes |
| `hx-boost` | Converts links/forms to AJAX | Yes |
| `hx-push-url` | Pushes URL to browser history | Yes |
| `hx-replace-url` | Replaces current URL in history | Yes |
| `hx-history` | Controls history cache behavior | No |
| `hx-history-elt` | Designates element for history snapshots | No |
| `hx-inherit` | Explicitly enables attribute inheritance | -- |
| `hx-disinherit` | Disables attribute inheritance | -- |
| `hx-disable` | Disables all htmx processing | Yes |
| `hx-preserve` | Keeps element unchanged during swaps | No |
| `hx-ext` | Enables htmx extensions | Yes |
| `hx-on` | Inline event handler | No |
| `hx-validate` | Enables HTML5 validation | No |

---

## 1. AJAX Request Attributes

These attributes issue HTTP requests when triggered. The value is the target URL. An empty value requests the current page URL.

### hx-get

Issues a GET request to the specified URL.

```html
<button hx-get="/api/items">Load Items</button>
```

### hx-post

Issues a POST request. Commonly used with forms and actions that create resources.

```html
<button hx-post="/account/enable" hx-target="body">
  Enable Your Account
</button>
```

### hx-put

Issues a PUT request for full resource replacement.

```html
<button hx-put="/account" hx-target="body">
  Update Account
</button>
```

### hx-patch

Issues a PATCH request for partial resource updates.

```html
<button hx-patch="/account" hx-target="body">
  Patch Your Account
</button>
```

### hx-delete

Issues a DELETE request. Return 200 with an empty body to remove the element. A 204 response prevents any swap.

```html
<button hx-delete="/account" hx-target="body">
  Delete Your Account
</button>
```

**Common behavior for all request attributes:**
- Not inherited -- must be placed directly on the element.
- Default trigger: `click` for most elements, `submit` for forms, `change` for inputs/selects.
- Default swap: `innerHTML` of the element itself.
- Use `hx-target`, `hx-swap`, and `hx-trigger` to customize behavior.

---

## 2. Trigger and Timing

### hx-trigger

Specifies what event initiates the AJAX request. Accepts event names, polling definitions, or comma-separated combinations.

**Syntax:** `hx-trigger="event [filter] [modifier...]"`

**Standard events:**
```html
<div hx-get="/clicked" hx-trigger="click">Click Me</div>
```

**Event filters** -- boolean expressions in square brackets:
```html
<div hx-get="/clicked" hx-trigger="click[ctrlKey]">Control Click Only</div>
```

**Polling:**
```html
<div hx-get="/updates" hx-trigger="every 2s">Live Updates</div>
```

**Multiple triggers:**
```html
<div hx-get="/news" hx-trigger="load, click delay:1s"></div>
```

#### Trigger Modifiers

| Modifier | Description |
|----------|-------------|
| `once` | Fires only on the first occurrence |
| `changed` | Fires only when the element value changes |
| `delay:<time>` | Waits before firing; resets if event recurs (debounce) |
| `throttle:<time>` | Ignores repeat events within the time window |
| `from:<selector>` | Listens on a different element (`document`, `window`, `closest <sel>`, `find <sel>`) |
| `target:<selector>` | Filters events by their originating target |
| `consume` | Prevents event from triggering parent htmx requests |
| `queue:<mode>` | Queuing: `first`, `last`, `all`, `none` |

#### Special Triggers

| Trigger | Description |
|---------|-------------|
| `load` | Fires when element loads |
| `revealed` | Fires when element is scrolled into viewport |
| `intersect` | Fires on viewport intersection; supports `root:<sel>` and `threshold:<float>` |

**Gotchas:**
- Not inherited.
- CSS selectors with whitespace in `from:` require parentheses: `from:(form input)`.
- `reset` events may fire before form values update -- add `delay:0.01s` as a workaround.

### hx-sync

Synchronizes AJAX requests between elements to prevent race conditions. Uses a CSS selector to identify a coordination element and a strategy.

**Syntax:** `hx-sync="<selector>:<strategy>"`

| Strategy | Behavior |
|----------|----------|
| `drop` | Ignore this request if one is already in flight (default) |
| `abort` | Drop if in flight; abort this request if another starts |
| `replace` | Abort the current in-flight request and replace with this one |
| `queue first` | Queue the first request only |
| `queue last` | Queue only the most recent request |
| `queue all` | Queue all requests |

```html
<!-- Prevent double-submit on a form -->
<form hx-post="/submit" hx-sync="this:drop">
  <button type="submit">Submit</button>
</form>

<!-- Replace stale search requests while typing -->
<input type="search" hx-get="/search" hx-trigger="keyup changed delay:300ms"
       hx-sync="this:replace">
```

**Inherited.** Can be placed on a parent element.

---

## 3. Targeting and Swapping

### hx-target

Specifies a different element to receive the swapped content. Without this, the issuing element is the target.

**Syntax:** CSS selector or extended selector.

| Value | Description |
|-------|-------------|
| CSS selector | e.g. `#results`, `.container` |
| `this` | The element itself |
| `closest <selector>` | Nearest ancestor matching selector |
| `find <selector>` | First descendant matching selector |
| `next` | Next sibling element |
| `next <selector>` | Next sibling matching selector |
| `previous` | Previous sibling element |
| `previous <selector>` | Previous sibling matching selector |

```html
<button hx-post="/register" hx-target="#response-div" hx-swap="beforeend">
  Register!
</button>
<div id="response-div"></div>
```

**Inherited.** Useful on parent elements when children share a target.

### hx-swap

Controls how the response HTML is inserted into the target element. Default is `innerHTML`.

#### Swap Strategies

| Value | Effect |
|-------|--------|
| `innerHTML` | Replace inner content of target (default) |
| `outerHTML` | Replace the entire target element |
| `textContent` | Replace text content only, no HTML parsing |
| `beforebegin` | Insert before the target element |
| `afterbegin` | Insert before target's first child |
| `beforeend` | Insert after target's last child (append) |
| `afterend` | Insert after the target element |
| `delete` | Remove the target element, ignoring response |
| `none` | Do not swap (out-of-band swaps still process) |

#### Swap Modifiers

Appended after the strategy, space-separated.

| Modifier | Example | Effect |
|----------|---------|--------|
| `swap:<time>` | `swap:500ms` | Delay before inserting content |
| `settle:<time>` | `settle:500ms` | Delay before settle step (default 20ms) |
| `transition:true` | | Use View Transitions API |
| `ignoreTitle:true` | | Do not update page title from response |
| `scroll:<target>` | `scroll:top`, `scroll:#el:bottom` | Scroll after swap |
| `show:<target>` | `show:top`, `show:#el:top` | Ensure element visibility |
| `focus-scroll:true` | | Auto-scroll to focused inputs |

```html
<!-- Append items to a list with smooth scroll -->
<button hx-get="/items" hx-target="#list" hx-swap="beforeend scroll:bottom">
  Load More
</button>

<!-- Swap with view transition -->
<div hx-get="/page" hx-swap="innerHTML transition:true">Navigate</div>
```

**Gotchas:**
- Inherited.
- `outerHTML` on `<body>` is automatically converted to `innerHTML`.
- Default swap delay is 0ms; default settle delay is 20ms.

### hx-swap-oob

Enables out-of-band swaps -- updating multiple elements from a single response. Placed on elements **in the server response**, not in the page HTML.

**Syntax:**

| Value | Behavior |
|-------|----------|
| `true` | Swap by matching the element's `id` (uses `outerHTML`) |
| `<strategy>` | Use a specific swap strategy |
| `<strategy>:<selector>` | Swap into the element matching the selector |

```html
<!-- Server response with OOB swap -->
<div id="main-content">Primary response content</div>

<div id="alerts" hx-swap-oob="true">
  Saved successfully!
</div>

<!-- Append a row to a table -->
<template>
  <tr hx-swap-oob="beforeend:#table-body">
    <td>New row</td>
  </tr>
</template>
```

**Gotchas:**
- Not inherited.
- Table rows, list items, and similar elements that cannot exist independently in HTML require wrapping in `<template>` tags.
- SVG elements need both `<template>` and `<svg>` wrappers for proper namespacing.
- Nested OOB elements process by default even within main content. Set `htmx.config.allowNestedOobSwaps = false` to limit this.

### hx-select

Filters the server response, extracting only matching elements before swapping.

```html
<button hx-get="/page" hx-select="#content" hx-swap="outerHTML">
  Load Content
</button>
```

The value is a CSS selector applied to the response. **Inherited.**

### hx-select-oob

Selects elements from the response for out-of-band swapping at other locations.

**Syntax:** comma-separated selectors, optionally with swap strategy: `selector:strategy`

```html
<button hx-get="/info"
        hx-select="#info-details"
        hx-swap="outerHTML"
        hx-select-oob="#alert, #sidebar:afterbegin">
  Get Info!
</button>
```

Default swap strategy is `outerHTML`. **Inherited.**

---

## 4. Request Data

### hx-include

Includes additional element values in the request beyond those automatically submitted.

**Syntax:** CSS selector or extended selector (`this`, `closest <sel>`, `find <sel>`, `next <sel>`, `previous <sel>`).

```html
<button hx-post="/register" hx-include="[name='email']">
  Register!
</button>
<input name="email" type="email"/>
```

**Gotchas:**
- Inherited, but evaluated from the triggering element.
- Non-input elements automatically include all enclosed inputs.
- Disabled inputs are filtered out.

### hx-params

Filters which parameters are submitted with the request.

| Value | Effect |
|-------|--------|
| `*` | Include all parameters (default) |
| `none` | Exclude all parameters |
| `not <comma-list>` | Include all except listed |
| `<comma-list>` | Include only listed parameters |

```html
<form hx-post="/submit" hx-params="not password_confirm">
  <input name="username">
  <input name="password" type="password">
  <input name="password_confirm" type="password">
  <button>Submit</button>
</form>
```

**Inherited.**

### hx-vals

Adds extra values to the request parameters. Accepts JSON by default; prefix with `js:` for dynamic evaluation.

**Static JSON:**
```html
<div hx-get="/example" hx-vals='{"myVal": "My Value"}'>Click</div>
```

**Dynamic JavaScript:**
```html
<div hx-get="/example" hx-vals='js:{myVal: calculateValue()}'>Click</div>
```

**Accessing the event object:**
```html
<div hx-get="/example" hx-trigger="keyup" hx-vals='js:{lastKey: event.key}'>
  <input type="text" />
</div>
```

**Gotchas:**
- Inherited; child declarations override parent values.
- Values override input fields with the same name.
- `js:` prefix creates XSS risk with untrusted input. Use static JSON for user-generated content.

### hx-vars (Deprecated)

Deprecated in favor of `hx-vals`. Evaluates JavaScript expressions by default, creating XSS risk.

```html
<div hx-get="/example" hx-vars="myVar:computeMyVar()">Click</div>
```

**Use `hx-vals` with `js:` prefix instead.**

### hx-headers

Adds custom HTTP headers to the request. Accepts JSON; prefix with `js:` for dynamic evaluation.

```html
<div hx-get="/api/data" hx-headers='{"X-Custom-Header": "value"}'>
  Fetch Data
</div>

<div hx-get="/api/data" hx-headers='js:{"X-Token": getToken()}'>
  Fetch with Dynamic Header
</div>
```

**Gotchas:**
- Inherited; child values override parent values.
- `js:` prefix introduces XSS risk with untrusted content.

### hx-encoding

Changes request encoding from the default `application/x-www-form-urlencoded` to `multipart/form-data`. Required for file uploads.

```html
<form hx-post="/upload" hx-encoding="multipart/form-data">
  <input type="file" name="document">
  <button>Upload</button>
</form>
```

**Inherited.** Can be placed on a parent element.

---

## 5. UI Feedback

### hx-indicator

Specifies which element receives the `htmx-request` CSS class during a request, enabling loading indicators.

```html
<button hx-post="/submit" hx-indicator="#spinner">
  Submit
</button>
<img id="spinner" class="htmx-indicator" src="/img/spinner.svg"/>
```

**Built-in indicator** (child of the triggering element):
```html
<button hx-post="/submit">
  Submit
  <img class="htmx-indicator" src="/img/spinner.svg"/>
</button>
```

**Default CSS behavior:**
```css
.htmx-indicator { opacity: 0; }
.htmx-request .htmx-indicator {
  opacity: 1;
  transition: opacity 200ms ease-in;
}
```

**Gotchas:**
- Inherited.
- Without an explicit indicator, `htmx-request` is added to the triggering element itself.
- Accepts extended selectors: `closest <sel>`.
- Use `inherit` keyword to combine parent indicators: `hx-indicator="inherit, #extra-spinner"`.

### hx-disabled-elt

Adds the HTML `disabled` attribute to elements during an active request.

**Syntax:** CSS selector or extended selector (`this`, `closest`, `find`, `next`, `previous`). Comma-separated for multiple targets.

```html
<button hx-post="/submit" hx-disabled-elt="this">
  Submit (disables itself)
</button>

<form hx-post="/submit" hx-disabled-elt="find input, find button">
  <input name="data">
  <button type="submit">Send</button>
</form>
```

**Inherited.** Use `inherit` keyword to extend parent rules.

### hx-confirm

Shows a browser confirmation dialog before issuing the request. The request proceeds only if the user confirms.

```html
<button hx-delete="/account" hx-confirm="Are you sure you want to delete your account?">
  Delete My Account
</button>
```

**Gotchas:**
- Inherited.
- Uses `window.confirm()` by default but can be customized via the `htmx:confirm` event.
- The event provides `issueRequest(skipConfirmation)` callback for custom confirmation flows.

### hx-prompt

Shows a browser prompt dialog before the request. The user's input is sent in the `HX-Prompt` request header.

```html
<button hx-delete="/account" hx-prompt="Enter your account name to confirm deletion">
  Delete My Account
</button>
```

**Inherited.** The prompt value is accessible server-side via the `HX-Prompt` header.

---

## 6. Navigation

### hx-boost

Converts standard anchors and forms to use AJAX. Links and forms work normally without JavaScript (progressive enhancement).

```html
<div hx-boost="true">
  <a href="/page1">Page 1</a>
  <a href="/page2">Page 2</a>

  <form action="/submit" method="post">
    <input name="email" type="email">
    <button>Submit</button>
  </form>
</div>
```

**Boosted link behavior:** GET to href, targets `<body>`, `innerHTML` swap, pushes URL to history.

**Boosted form behavior:** GET or POST per method attribute, targets `<body>`, `innerHTML` swap, does NOT push URL by default.

**Gotchas:**
- Inherited. Use `hx-boost="false"` on children to opt out.
- Only boosts same-domain links; local anchors are excluded.
- Server can detect boosted requests via the `HX-Boosted` header.
- Use `hx-push-url` on forms if URL history entries are needed.

### hx-push-url

Pushes a URL into browser history after a successful request, creating a new history entry for back/forward navigation.

| Value | Effect |
|-------|--------|
| `true` | Push the fetched URL |
| `false` | Disable pushing (overrides inheritance) |
| URL string | Push this specific URL |

```html
<div hx-get="/account" hx-push-url="true">Go to Account</div>
<div hx-get="/account" hx-push-url="/account/home">Go to Account</div>
```

**Gotchas:**
- Inherited.
- The `HX-Push-Url` response header can override this attribute.

### hx-replace-url

Replaces the current URL in browser history (no new entry) after a successful request.

| Value | Effect |
|-------|--------|
| `true` | Replace with the fetched URL |
| `false` | Disable replacement (overrides inheritance) |
| URL string | Replace with this specific URL |

```html
<div hx-get="/account" hx-replace-url="true">Go to Account</div>
```

**Gotchas:**
- Inherited.
- The `HX-Replace-Url` response header can override this attribute.
- Use `hx-push-url` instead when you want a new history entry.

### hx-history

Controls whether the current page state is saved to the localStorage history cache. Set to `false` to prevent caching sensitive data.

```html
<body>
  <div hx-history="false">
    <!-- Sensitive content not cached -->
  </div>
</body>
```

History navigation still works, but restoration requires a fresh server request. Can be placed anywhere in the document.

### hx-history-elt

Designates which element is used for history snapshots. Default is `<body>`.

```html
<div id="content" hx-history-elt>
  <!-- Only this element is snapshot for history -->
</div>
```

**Gotchas:**
- Not inherited.
- In most cases, narrowing the history snapshot is not recommended.
- The targeted element must remain visible at all times for proper history restoration.

---

## 7. Inheritance and Control

### hx-inherit

Explicitly enables inheritance of specific attributes from a parent element. Most useful when `htmx.config.disableInheritance` is set to `true`.

**Syntax:** `*` (all attributes) or space-separated attribute names.

```html
<div hx-target="#tab-container" hx-inherit="hx-target">
  <a hx-boost="true" href="/tab1">Tab 1</a>
  <a hx-boost="true" href="/tab2">Tab 2</a>
</div>
```

### hx-disinherit

Disables inheritance of attributes from a parent element.

**Syntax:** `*` (all attributes) or space-separated attribute names.

```html
<!-- Disable all inheritance -->
<div hx-boost="true" hx-disinherit="*">
  <a href="/page1">Not boosted</a>
</div>

<!-- Disable specific attribute inheritance -->
<div hx-boost="true" hx-target="#content" hx-disinherit="hx-target">
  <button hx-get="/test">Uses own target, not #content</button>
</div>
```

### hx-disable

Disables all htmx processing on an element and all its descendants. Useful as a security measure for user-generated content.

```html
<div hx-disable>
  <!-- No htmx attributes processed here, even if present -->
  <div hx-get="/malicious">This request will not fire</div>
</div>
```

**Gotchas:**
- Inherited and cannot be reversed by any content beneath it.
- Use alongside HTML escaping for defense-in-depth against untrusted content.

### hx-preserve

Keeps an element unchanged during HTML replacement. The element must have an `id` attribute.

```html
<div id="video-player" hx-preserve>
  <!-- Video continues playing through page updates -->
</div>
```

**Gotchas:**
- Not inherited.
- Elements must have a stable `id`.
- Text inputs, iframes, and videos may lose focus or caret position -- consider the `morphdom` extension for more reliable DOM reconciliation.
- Do not combine with `hx-swap="none"` to avoid element loss.

---

## 8. Integration

### hx-ext

Enables htmx extensions for an element and all its children.

```html
<!-- Enable extensions on body for site-wide use -->
<body hx-ext="preload,morph">
  ...
  <!-- Disable a specific extension for a subtree -->
  <div hx-ext="ignore:preload">
    ...
  </div>
</body>
```

**Syntax:**
- Single: `hx-ext="extension-name"`
- Multiple: `hx-ext="ext1,ext2"`
- Disable inherited: `hx-ext="ignore:extension-name"`

**Inherited.** Extensions cascade to all descendants.

### hx-on

Inline event handler for any DOM or htmx event. Supports "Locality of Behaviour" -- keeping behavior next to the markup it affects.

**Standard DOM events:**
```html
<button hx-on:click="alert('Clicked!')">Click Me</button>
```

**htmx events (use double colon):**
```html
<button hx-get="/info" hx-on::before-request="alert('Requesting...')">
  Get Info
</button>
```

**Dash-based alternative** (for template engines that dislike colons):
```html
<button hx-get="/info" hx-on--before-request="alert('Requesting...')">
  Get Info
</button>
```

**Available in handler scope:** `this` (the element), `event` (the triggering event).

**Gotchas:**
- Not inherited, but events bubble so parent handlers still fire.
- DOM attributes are case-insensitive -- use kebab-case for event names, not camelCase.

### hx-request

Configures request behavior using JSON-like syntax.

| Option | Type | Effect |
|--------|------|--------|
| `timeout` | ms | Request timeout duration |
| `credentials` | boolean | Include credentials in request |
| `noHeaders` | boolean | Strip all headers from request |

```html
<div hx-request='{"timeout": 3000}'>
  <button hx-get="/slow-endpoint">Fetch</button>
</div>

<!-- Dynamic values with js: prefix -->
<div hx-request='js: timeout:getTimeout()'>...</div>
```

**Merge-inherited.** Settings cascade and merge with child declarations.

### hx-validate

Forces HTML5 form validation on non-form elements before issuing a request. Forms validate by default; this extends validation to individual inputs, textareas, and selects.

```html
<input type="email" name="email"
       hx-post="/validate-email"
       hx-trigger="change"
       hx-validate="true">
```

**Not inherited.** Must be placed on each element individually. Uses the HTML5 Validation API.
