# htmx: Scripting & Integration
Based on htmx 2.0.8 documentation.

## Scripting Philosophy

htmx follows a **hypermedia-friendly scripting** approach. HTML remains the engine of
application state (HATEOAS). JavaScript enhances hypermedia -- it does not replace it.

### Five Principles

1. **Respect HATEOAS.** Avoid `fetch()` or `XMLHttpRequest` calls returning JSON. Server
   exchanges should return HTML. State lives in the DOM, not in JS objects.
2. **Client-side-only state is fine.** Visibility toggles, UI animations, ephemeral
   presentation state that never syncs with the server -- all acceptable in plain JS.
3. **Use events for communication.** Third-party libraries emit DOM events; htmx listens
   and triggers hypermedia exchanges. This turns any JS component into a hypermedia control.
4. **Use islands for non-hypermedia components.** Complex widgets (rich-text editors,
   calendars) can live as isolated islands. They communicate outward through events or
   hidden inputs, not JS APIs.
5. **Consider inline scripting.** `hx-on:*`, Alpine.js, or hyperscript keep behavior
   co-located with the element (Locality of Behavior).

---

## hx-on Attribute

`hx-on:*` extends HTML's native `on*` event handling to **any** event, including
htmx-specific events.

### Syntax

```html
<button hx-on:click="alert('clicked')">Click Me</button>
```

For htmx events, use the kebab-case name (HTML attributes are case-insensitive):

```html
<button hx-post="/example"
        hx-on:htmx:config-request="event.detail.parameters.example = 'Hello'">
    Post Me!
</button>
```

### Accessing Event Details

The `event` variable is available in the handler. `event.detail` carries htmx-specific
data (parameters, headers, xhr, etc.):

```html
<!-- Add a parameter before the request fires -->
<form hx-post="/submit"
      hx-on:htmx:config-request="event.detail.parameters.token = getToken()">
    ...
</form>

<!-- Reset a form after a successful swap -->
<form hx-post="/items" hx-swap="outerHTML"
      hx-on:htmx:after-request="if(event.detail.successful) this.reset()">
    ...
</form>

<!-- Prevent a request conditionally -->
<button hx-get="/data"
        hx-on:htmx:config-request="if(!confirm('Sure?')) event.preventDefault()">
    Load
</button>
```

### When to Use hx-on vs. External JS

Use `hx-on:*` for short, one-liner behaviors tied to a specific element. For anything
longer than ~2 lines, move the logic to a named function or event listener.

---

## Using JavaScript with htmx

### Listening to htmx Events

htmx fires events on elements throughout the request lifecycle. Listen with standard
`addEventListener`:

```javascript
document.body.addEventListener('htmx:configRequest', function(event) {
    // Add a header to every request
    event.detail.headers['X-Custom-Header'] = 'value';
});

document.body.addEventListener('htmx:beforeSwap', function(event) {
    // Handle 404 responses with a custom swap
    if (event.detail.xhr.status === 404) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
    }
});

document.body.addEventListener('htmx:afterSettle', function(event) {
    // Run after new content is settled in the DOM
    console.log('Settled:', event.detail.elt);
});
```

### Key htmx Events (Lifecycle Order)

| Event | When |
|---|---|
| `htmx:configRequest` | Before request. Modify params, headers. |
| `htmx:beforeRequest` | After config, before send. Cancel here. |
| `htmx:beforeSwap` | Response received, before DOM swap. Modify swap behavior. |
| `htmx:afterSwap` | After content is swapped into DOM. |
| `htmx:afterSettle` | After new content is settled (animations done). |
| `htmx:load` | Fires on new content loaded into DOM. Best for initializing JS on new elements. |

### htmx.ajax() -- Triggering Requests from JS

Issue an htmx-style request from JavaScript:

```javascript
// Simple GET, swap into #result
htmx.ajax('GET', '/api/data', '#result');

// With full options
htmx.ajax('GET', '/api/data', {
    target: '#result',
    swap: 'innerHTML',
    values: { page: 2 },
    headers: { 'X-Custom': 'value' }
});

// POST with a source element (for hx-include, hx-params resolution)
htmx.ajax('POST', '/submit', {
    source: document.getElementById('my-form'),
    target: '#result'
});
```

### htmx.process() -- Activating Dynamic Content

When JavaScript (not htmx) inserts HTML containing `hx-*` attributes, tell htmx to
process it:

```javascript
const div = document.getElementById('container');
div.innerHTML = '<button hx-get="/endpoint">Load</button>';
htmx.process(div);  // Now the button is live
```

### htmx.onLoad() -- Initialize on Every Swap

Runs a callback every time htmx loads new content. Works on initial page load too:

```javascript
htmx.onLoad(function(target) {
    // target is the newly loaded element
    const charts = target.querySelectorAll('.chart');
    charts.forEach(el => new Chart(el, getChartConfig(el)));
});
```

---

## Integrating Third-Party Libraries

### Pattern: Initialize After Swap with htmx.onLoad

The standard pattern for any JS library that needs to initialize DOM elements:

```javascript
htmx.onLoad(function(content) {
    // SortableJS
    content.querySelectorAll('.sortable').forEach(function(el) {
        new Sortable(el, { animation: 150, ghostClass: 'blue-background-class' });
    });

    // Flatpickr date pickers
    content.querySelectorAll('.datepicker').forEach(function(el) {
        flatpickr(el);
    });

    // Tippy.js tooltips
    content.querySelectorAll('[data-tippy-content]').forEach(function(el) {
        tippy(el);
    });
});
```

### Pattern: Bridge Library Events to htmx

When a library fires DOM events, use `hx-trigger` to convert them into requests:

```html
<!-- SortableJS fires "end" event after drag completes -->
<form class="sortable" hx-post="/items" hx-trigger="end">
    <div class="htmx-indicator">Updating...</div>
    <div><input type="hidden" name="item" value="1"/>Item 1</div>
    <div><input type="hidden" name="item" value="2"/>Item 2</div>
    <div><input type="hidden" name="item" value="3"/>Item 3</div>
</form>
```

### Pattern: Alpine.js + htmx

Alpine handles client-side state; htmx handles server communication:

```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">
        <button hx-get="/load-details" hx-target="#details">Load from Server</button>
        <div id="details"></div>
    </div>
</div>
```

When Alpine renders template content containing htmx attributes, process it:

```html
<div x-data="{ show: false }"
     x-init="$watch('show', val => {
         if (val) htmx.process(document.querySelector('#dynamic'))
     })">
    <button @click="show = !show">Toggle</button>
    <template x-if="show">
        <div id="dynamic">
            <a hx-get="/content" href="#">Load Content</a>
        </div>
    </template>
</div>
```

---

## Web Components

htmx works naturally with web components because both operate on DOM-based lifecycles.
htmx swaps HTML into the DOM via `.innerHTML`, which triggers custom element
`connectedCallback` automatically.

### Light DOM Web Component

```javascript
class EditCell extends HTMLElement {
    connectedCallback() {
        const value = this.getAttribute('value');
        const name = this.getAttribute('name');
        this.innerHTML = `
            <select name="${name}">
                <option ${value === 'Yes' ? 'selected' : ''}>Yes</option>
                <option ${value === 'No' ? 'selected' : ''}>No</option>
                <option ${value === 'Maybe' ? 'selected' : ''}>Maybe</option>
            </select>
        `;
    }
}
customElements.define('edit-cell', EditCell);
```

```html
<form hx-put="/update">
    <table>
        <tr>
            <td>Alex</td>
            <td><edit-cell name="alex-carousel" value="Yes"></edit-cell></td>
            <td><edit-cell name="alex-roller" value="No"></edit-cell></td>
        </tr>
    </table>
    <button>Save</button>
</form>
```

### Shadow DOM Web Component

When using Shadow DOM, htmx cannot automatically see the internal elements.
Call `htmx.process(root)` on the shadow root:

```javascript
customElements.define('my-component', class extends HTMLElement {
    connectedCallback() {
        const root = this.attachShadow({ mode: 'closed' });
        root.innerHTML = `
            <button hx-get="/clicked" hx-target="next div">Click me!</button>
            <div></div>
        `;
        htmx.process(root);  // Required for shadow DOM
    }
});
```

### Shadow DOM Selector Scoping

Inside shadow DOM, `hx-target` and other selectors are scoped to the shadow root.
Special prefixes escape the boundary:

- **`host`** -- targets the host element of the shadow DOM
- **`global`** -- targets elements in the main document

```html
<!-- Inside shadow DOM: target an element in the light DOM -->
<button hx-get="/data" hx-target="global #main-content">Load</button>
```

### When Web Components Work Best with htmx

- Encapsulating reusable UI widgets (dropdowns, editors, date pickers)
- Reducing repetitive HTML markup on the server
- Creating self-contained interactive elements that participate in forms
- Light DOM components work with zero extra effort; shadow DOM needs `htmx.process()`

---

## Caching

htmx works with standard HTTP caching. No special client-side cache layer -- the
browser's native cache applies to htmx requests.

### Last-Modified / If-Modified-Since

When the server sends `Last-Modified`, the browser automatically sends
`If-Modified-Since` on subsequent requests. The server can return `304 Not Modified`
to skip re-rendering.

### Vary Header (Critical for Partial Responses)

If your server returns different HTML based on the `HX-Request` header (full page vs.
partial), you **must** set:

```
Vary: HX-Request
```

Without this, the browser may serve a cached partial response for a full-page navigation
or vice versa.

### Cache Busting

If you cannot set `Vary` headers (e.g., CDN limitations), enable cache busting:

```javascript
htmx.config.getCacheBusterParam = true;
```

htmx appends a cache-busting parameter to GET requests, preventing stale cache hits.

### ETag Support

ETags work normally. When the server returns different content for `HX-Request` vs.
non-`HX-Request`, generate different ETags for each variant.

### History Cache

htmx caches pages in `localStorage` for back-button navigation:

```javascript
// Reduce cache size (default: 10)
htmx.config.historyCacheSize = 5;

// Disable entirely (useful for sensitive data)
htmx.config.historyCacheSize = 0;
```

**Important:** Keep `htmx.config.historyRestoreAsHxRequest` disabled (the default) to
prevent caching mismatches between full-page and partial responses.

---

## Common Integration Patterns

### Initialize JS Components After Swap

Use `htmx:load` (preferred) or `htmx:afterSettle`:

```javascript
// htmx:load fires on every new element loaded into the DOM
document.body.addEventListener('htmx:load', function(event) {
    const el = event.detail.elt;
    // Initialize any JS widgets inside the new content
    el.querySelectorAll('.rich-editor').forEach(initEditor);
    el.querySelectorAll('[data-chart]').forEach(initChart);
});
```

`htmx.onLoad()` is a convenience wrapper:

```javascript
htmx.onLoad(function(el) {
    el.querySelectorAll('.rich-editor').forEach(initEditor);
});
```

### Clean Up JS Components Before Swap

Prevent memory leaks by destroying widgets before htmx removes their elements:

```javascript
document.body.addEventListener('htmx:beforeSwap', function(event) {
    const target = event.detail.target;
    // Destroy chart instances, event listeners, timers, etc.
    target.querySelectorAll('.rich-editor').forEach(function(el) {
        if (el._editorInstance) {
            el._editorInstance.destroy();
        }
    });
});
```

### Trigger htmx Requests from JavaScript

Three approaches:

```javascript
// 1. htmx.ajax() -- direct API
htmx.ajax('GET', '/notifications', '#notification-area');

// 2. Trigger a custom event on an htmx-equipped element
const el = document.getElementById('my-element');
el.dispatchEvent(new Event('my-custom-event'));
// Works when the element has: hx-trigger="my-custom-event"

// 3. htmx.trigger() helper
htmx.trigger('#my-element', 'my-custom-event');
```

### Modify Requests from JavaScript

Add headers, parameters, or change the URL:

```javascript
document.body.addEventListener('htmx:configRequest', function(event) {
    // Add auth token
    event.detail.headers['Authorization'] = 'Bearer ' + getToken();

    // Add parameters
    event.detail.parameters['timezone'] = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Change target URL
    // event.detail.path = '/alternative/endpoint';
});
```

### Modify Responses from JavaScript

Intercept and transform responses before swap:

```javascript
document.body.addEventListener('htmx:beforeSwap', function(event) {
    // Custom handling for different status codes
    if (event.detail.xhr.status === 422) {
        // Validation error -- swap the error HTML anyway
        event.detail.shouldSwap = true;
        event.detail.isError = false;
        event.detail.target = document.getElementById('errors');
    }

    if (event.detail.xhr.status === 204) {
        // No content -- skip swap, show a toast instead
        event.detail.shouldSwap = false;
        showToast('Saved successfully');
    }
});
```

### Confirm Before Request

```html
<!-- Using hx-confirm (built-in) -->
<button hx-delete="/item/1" hx-confirm="Delete this item?">Delete</button>

<!-- Using hx-on for custom confirmation (e.g., SweetAlert) -->
<button hx-delete="/item/1"
        hx-on:htmx:confirm="event.preventDefault();
            Swal.fire({title: 'Confirm?', showCancelButton: true}).then(function(result) {
                if (result.isConfirmed) event.detail.issueRequest();
            })">
    Delete
</button>
```
