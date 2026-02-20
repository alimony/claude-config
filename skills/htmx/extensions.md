# htmx: Extensions
Based on htmx 2.0.8 documentation.

## How Extensions Work

Extensions augment htmx's core hypermedia capabilities. htmx maintains two tiers: **core extensions** (supported by the htmx team) and **community extensions** (supported by the broader community).

### Core Extensions

| Extension | Purpose |
|-----------|---------|
| `sse` | Server-Sent Events |
| `ws` | WebSockets |
| `morph` (Idiomorph) | DOM morphing swaps |
| `preload` | Preload content on hover/focus |
| `response-targets` | Target elements by HTTP status code |
| `head-support` | Manage `<head>` updates |
| `htmx-1-compat` | Restore htmx 1.x behaviors |

### Installing Extensions

Extensions are separate packages. Install via CDN, npm, or local file.

```html
<!-- CDN: load htmx first, then extension -->
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4"></script>
```

```bash
# npm
npm install htmx-ext-sse
```

```javascript
// Bundler
import "htmx.org";
import "htmx-ext-sse";
```

### Activating with hx-ext

The `hx-ext` attribute enables extensions on an element and all its children.

```html
<!-- Single extension on body (global) -->
<body hx-ext="sse">

<!-- Multiple extensions -->
<body hx-ext="preload,morph,response-targets">

<!-- Scoped to a section -->
<div hx-ext="ws">
  <!-- ws only active here -->
</div>

<!-- Disable an inherited extension -->
<div hx-ext="sse">
  <div hx-ext="ignore:sse">
    <!-- sse disabled in this subtree -->
  </div>
</div>
```

`hx-ext` is inherited and merged -- child elements see all parent extensions.

---

## SSE (Server-Sent Events)

Uni-directional server-to-client streaming over HTTP. Lightweight alternative to WebSockets, works through proxies and firewalls.

### Setup

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4"></script>

<div hx-ext="sse" sse-connect="/events" sse-swap="message">
  <!-- Content replaced when "message" events arrive -->
</div>
```

### Attributes

| Attribute | Purpose |
|-----------|---------|
| `sse-connect="<url>"` | Connect to SSE endpoint |
| `sse-swap="<event>"` | Swap content when named event received |
| `sse-close="<event>"` | Close connection when event received |

### Named Events

Server sends named events; client listens for specific ones:

```
event: newMessage
data: <div>Hello!</div>

event: userCount
data: <span>42 online</span>
```

```html
<div hx-ext="sse" sse-connect="/stream">
  <div sse-swap="newMessage"></div>
  <div sse-swap="userCount"></div>
</div>
```

Multiple events on one element: `sse-swap="event1,event2"`.

### Triggering HTTP Requests from SSE

Use `sse:<eventName>` as an `hx-trigger` value:

```html
<div hx-ext="sse" sse-connect="/stream">
  <div hx-get="/latest-data" hx-trigger="sse:dataChanged">
    <!-- GET /latest-data fires when "dataChanged" SSE event arrives -->
  </div>
</div>
```

### Events

| Event | Detail |
|-------|--------|
| `htmx:sseOpen` | Connection established (`detail.source`) |
| `htmx:sseError` | Connection error (`detail.error`) |
| `htmx:sseBeforeMessage` | Before swap -- `preventDefault()` to cancel |
| `htmx:sseMessage` | After swap |
| `htmx:sseClose` | Closed (`detail.type`: nodeMissing, nodeReplaced, message) |

### Reconnection

Automatic reconnection with exponential backoff.

---

## WebSockets

Bi-directional communication between client and server.

### Setup

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-ws@2.0.4"></script>

<div hx-ext="ws" ws-connect="/chatroom">
  <div id="messages"></div>
  <form ws-send>
    <input name="chat_message">
    <button>Send</button>
  </form>
</div>
```

### Attributes

| Attribute | Purpose |
|-----------|---------|
| `ws-connect="<url>"` | Connect to WebSocket endpoint (ws:// or wss:// optional) |
| `ws-send` | On forms: serialize and send as JSON on submit |

### Sending Messages

Forms with `ws-send` serialize their values to JSON and include a `HEADERS` field with standard htmx request headers:

```json
{
  "chat_message": "Hello!",
  "HEADERS": { "HX-Request": "true", "HX-Trigger": "form", ... }
}
```

### Receiving Messages

The server sends HTML fragments. The extension swaps them using **Out of Band (OOB) swaps** -- matching elements by `id`:

```html
<!-- Server sends this; it replaces #messages in the DOM -->
<div id="messages" hx-swap-oob="beforeend">
  <p>New message arrived</p>
</div>
```

### Events

| Event | When |
|-------|------|
| `htmx:wsConnecting` | Connection attempt started |
| `htmx:wsOpen` | Connected |
| `htmx:wsClose` | Disconnected |
| `htmx:wsError` | Error occurred |
| `htmx:wsBeforeMessage` | Message received (pre-processing) |
| `htmx:wsAfterMessage` | Message processed |
| `htmx:wsConfigSend` | Before sending -- modify message here |
| `htmx:wsBeforeSend` | Just before transmission |
| `htmx:wsAfterSend` | After transmission |

All events provide `detail.socketWrapper` for queue manipulation and direct sending.

### Reconnection

Exponential backoff with full jitter by default. Customize:

```javascript
htmx.config.wsReconnectDelay = function(retryCount) {
  return retryCount * 1000; // linear backoff in ms
};
```

Messages queued during disconnection are sent automatically on reconnect.

### Configuration

| Option | Purpose |
|--------|---------|
| `createWebSocket` | Factory function for custom WebSocket instances |
| `wsBinaryType` | Binary type property (default: `blob`) |

---

## Idiomorph (Morph Swaps)

Idiomorph is a DOM morphing algorithm. Instead of replacing DOM nodes, it restructures the existing DOM tree to match new content, preserving nodes where possible. This produces smoother transitions and preserves state (focus, scroll position, CSS transitions).

### When to Use Morph vs Standard Swap

Use **morph** when:
- You want to preserve input focus, scroll position, or CSS animation state
- You're updating large sections and want minimal DOM churn
- You need smooth visual transitions between states

Use **standard swap** when:
- You're replacing small, isolated fragments
- You need maximum simplicity
- Content is entirely new (no state to preserve)

### Setup

```html
<script src="https://unpkg.com/idiomorph@0.7.4/dist/idiomorph-ext.min.js"></script>

<body hx-ext="morph">
  <button hx-get="/update" hx-swap="morph">
    Morph Outer HTML
  </button>

  <button hx-get="/update" hx-swap="morph:innerHTML">
    Morph Inner Only
  </button>
</body>
```

### Swap Variants

| Value | Behavior |
|-------|----------|
| `morph` or `morph:outerHTML` | Morphs the target element and its children |
| `morph:innerHTML` | Morphs only children, target element untouched |

---

## Preload

Loads HTML fragments into the browser cache before the user clicks, making pages appear near-instant (100-200ms advantage).

### Setup

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-preload@2.1.2"></script>

<body hx-ext="preload">
  <nav>
    <a href="/about" preload="mouseover">About</a>
    <a href="/contact" preload>Contact</a> <!-- default: mousedown -->
  </nav>
</body>
```

### Trigger Values

| Value | When it Fires |
|-------|--------------|
| `mousedown` (default) | Mouse button press (before click fires) |
| `mouseover` | After 100ms hover (immediate on touch devices) |
| `<custom-event>` | On custom events (e.g., `preload:init`) |
| `always` | Continuously preloads |

### What Gets Preloaded

- Standard `<a href="">` links
- Elements with `hx-get`
- Form elements with `method="get"` (radio, checkbox, select, submit)

Does NOT preload: POST/PUT/DELETE requests, JS/CSS resources within preloaded HTML.

### Additional Options

| Attribute | Purpose |
|-----------|---------|
| `preload-images="true"` | Also preload images found in preloaded HTML |

All preload requests include the header `HX-Preloaded: true`. Preloading respects `Cache-Control` headers.

**Caution:** Preloading too many resources wastes bandwidth and server capacity. Apply selectively to high-probability navigation targets.

---

## Response Targets

Route responses to different elements based on HTTP status codes. Essential for error handling.

### Setup

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-response-targets@2.0.4"></script>

<body hx-ext="response-targets">
  <form hx-post="/register"
        hx-target="#result"
        hx-target-422="#validation-errors"
        hx-target-5*="#server-error">
    <input name="email">
    <button>Register</button>
  </form>

  <div id="result"></div>
  <div id="validation-errors"></div>
  <div id="server-error"></div>
</body>
```

### Attribute Syntax

`hx-target-<CODE>` where CODE is an HTTP status code or wildcard pattern.

| Attribute | Matches |
|-----------|---------|
| `hx-target-404` | Exactly 404 |
| `hx-target-4*` | Any 4xx status |
| `hx-target-5*` | Any 5xx status |
| `hx-target-*` | Any non-200 status |
| `hx-target-error` | Any 4xx or 5xx |

Use `x` instead of `*` for strict HTML validators: `hx-target-4x`, `hx-target-5xx`.

### Wildcard Resolution Order

For a 404 response: `hx-target-404` -> `hx-target-40*` -> `hx-target-4*` -> `hx-target-*`.

### Target Selectors

Same selectors as standard `hx-target`: CSS selectors, `this`, `closest <sel>`, `find <sel>`, `next <sel>`, `previous <sel>`.

### Configuration Flags

| Flag | Effect |
|------|--------|
| `responseTargetPrefersRetargetHeader` | HX-Retarget header overrides calculated targets |
| `responseTargetPrefersExisting` | Don't overwrite previously set targets |
| `responseTargetUnsetsError` | Clear `isError` flag for error responses |
| `responseTargetSetsError` | Set `isError` flag for non-error responses |

**Note:** `hx-target-200` does not work. Standard `hx-target` handles 200 responses.

---

## Head Support

Manages `<head>` element updates during htmx swaps. htmx focuses on partial `<body>` replacement, so head tag handling requires this extension.

### Setup

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-head-support@2.0.5"></script>
<body hx-ext="head-support">
```

### Behavior

**Boosted requests** (`hx-boost="true"`): Merge algorithm --
- Elements matching current head content exactly are preserved
- New elements are appended
- Elements no longer present are removed

**Non-boosted requests**: All head content is appended to existing head.

### Control Attributes

| Attribute | Behavior |
|-----------|----------|
| `hx-head="merge"` | Force merge behavior |
| `hx-head="append"` | Force append behavior |
| `hx-head="re-eval"` | Re-add element on every request (useful for scripts) |
| `hx-preserve="true"` | Prevent element from being removed during merge |

### Events

| Event | When |
|-------|------|
| `htmx:beforeHeadMerge` | Before merge starts |
| `htmx:afterHeadMerge` | After merge (`detail.added`, `detail.kept`, `detail.removed`) |
| `htmx:removingHeadElement` | Before removing -- `preventDefault()` to keep |
| `htmx:addingHeadElement` | Before adding -- `preventDefault()` to skip |

---

## htmx 1 Compatibility

Restores htmx 1.x behaviors to ease migration. Apply it, upgrade, then incrementally remove reliance on deprecated features.

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-htmx-1-compat@2.0.4"></script>
<body hx-ext="htmx-1-compat">
```

### What It Restores

| Change | htmx 2 default | Restored 1.x behavior |
|--------|----------------|----------------------|
| SSE/WS attributes | `hx-ext="sse"` + `sse-connect` | Old `hx-sse="connect:..."` syntax |
| Event attributes | `hx-on*` | Old `hx-on` attribute |
| Scroll behavior | `"instant"` | `"smooth"` |
| DELETE body | URL parameters | Form-encoded body |
| Cross-domain | Blocked | Allowed |

**Cannot restore:** IE11 support, old extension swap API.

---

## Building Custom Extensions

### Defining an Extension

```javascript
htmx.defineExtension("my-extension", {
  init: function(api) {
    // Called once when extension initializes
    // api provides access to htmx internals
  },

  onEvent: function(name, evt) {
    // Called on every htmx event
    // Return false to prevent default behavior
  },

  transformResponse: function(text, xhr, elt) {
    // Modify server response text before processing
    return text;
  },

  isInlineSwap: function(swapStyle) {
    // Return true if this extension handles the given swap style
    return swapStyle === "my-swap";
  },

  handleSwap: function(swapStyle, target, fragment, settleInfo) {
    // Perform custom DOM swap logic
    // Return true if handled
    return false;
  },

  encodeParameters: function(xhr, parameters, elt) {
    // Custom parameter encoding
    // Return null to use default encoding
    return null;
  },

  getSelectors: function() {
    // Return custom CSS selectors for elements this extension manages
    return null;
  }
});
```

### Lifecycle Hooks Reference

| Hook | Arguments | Returns | Purpose |
|------|-----------|---------|---------|
| `init` | `api` | -- | One-time setup, access htmx internals |
| `onEvent` | `name, evt` | `boolean` | React to htmx lifecycle events |
| `transformResponse` | `text, xhr, elt` | `string` | Modify response before swap |
| `isInlineSwap` | `swapStyle` | `boolean` | Declare custom swap styles |
| `handleSwap` | `swapStyle, target, fragment, settleInfo` | `boolean` | Execute custom swap |
| `encodeParameters` | `xhr, parameters, elt` | `null` or encoded | Custom request encoding |
| `getSelectors` | -- | `string[]` or `null` | Custom element selectors |

### Example: Response Logger

```javascript
htmx.defineExtension("response-logger", {
  transformResponse: function(text, xhr, elt) {
    console.log("Response from", xhr.responseURL, "status:", xhr.status);
    console.log("Body length:", text.length);
    return text; // pass through unmodified
  }
});
```

```html
<div hx-ext="response-logger">
  <button hx-get="/api/data">Load (responses will be logged)</button>
</div>
```

### Example: Custom Swap Strategy

```javascript
htmx.defineExtension("fade-swap", {
  isInlineSwap: function(swapStyle) {
    return swapStyle === "fade";
  },

  handleSwap: function(swapStyle, target, fragment, settleInfo) {
    if (swapStyle !== "fade") return false;

    target.style.opacity = "0";
    setTimeout(function() {
      target.innerHTML = "";
      target.appendChild(fragment);
      target.style.opacity = "1";
    }, 300);
    return true;
  }
});
```

```html
<body hx-ext="fade-swap">
  <button hx-get="/content" hx-swap="fade">Fade In Content</button>
</body>
```

### Naming Convention

Extension names should be dash-separated, short, and descriptive. Implement in standalone JS files for reuse.
