# htmx: Events, Headers & JavaScript API
Based on htmx 2.0.8 documentation.

## Event Lifecycle

Events fire in this order during a standard htmx AJAX request:

```
htmx:confirm          →  Can cancel/delay the request
htmx:validateUrl      →  Validates the request URL
htmx:beforeRequest    →  Before AJAX request is issued
htmx:configRequest    →  Customize parameters, headers (last chance to modify)
htmx:beforeSend       →  Right before send (non-cancellable)
htmx:xhr:loadstart    →  XHR request starts
htmx:xhr:progress     →  Periodic progress updates
htmx:xhr:loadend      →  XHR request finishes
htmx:beforeOnLoad     →  Before response processing (cancellable)
htmx:afterOnLoad      →  After response processing, before swap
htmx:beforeSwap       →  Before DOM swap (configure swap behavior)
htmx:beforeTransition →  Before View Transition API swap (if used)
htmx:afterSwap        →  After content swapped into DOM
htmx:afterSettle      →  After DOM has settled (attributes processed)
htmx:load             →  New content added to DOM (init point)
htmx:afterRequest     →  After request completes (success or error)
```

Error events (`htmx:sendError`, `htmx:responseError`, `htmx:timeout`, `htmx:swapError`) interrupt the normal flow.

### Listening for Events

**addEventListener (recommended for global handlers):**
```javascript
document.body.addEventListener("htmx:configRequest", function(evt) {
    evt.detail.headers["X-Custom"] = "value";
});
```

**hx-on attribute (inline, scoped to element):**
```html
<button hx-get="/api" hx-on:htmx:config-request="event.detail.headers['X-Custom'] = 'value'">
    Click
</button>
```

Note: In `hx-on` attributes, event names use kebab-case (`htmx:config-request`) not camelCase.

**htmx.on() helper:**
```javascript
htmx.on("htmx:afterSwap", function(evt) {
    console.log("Swapped into", evt.detail.target);
});
```

### Cancelling Events

Most pre-action events are cancellable with `preventDefault()`:
```javascript
document.body.addEventListener("htmx:beforeRequest", function(evt) {
    if (!shouldProceed()) {
        evt.preventDefault(); // cancels the request
    }
});
```

---

## Key Events in Detail

### htmx:configRequest — Modify Outgoing Requests

Fires after parameters are collected. Last chance to modify headers, parameters, or URL.

```javascript
document.body.addEventListener("htmx:configRequest", function(evt) {
    // Add custom headers
    evt.detail.headers["Authorization"] = "Bearer " + getToken();

    // Add/modify parameters
    evt.detail.parameters["timezone"] = Intl.DateTimeFormat().resolvedOptions().timeZone;

    // Change target URL
    // evt.detail.path = "/alternative-endpoint";
});
```

**detail properties:** `parameters`, `unfilteredParameters`, `headers`, `elt`, `target`, `verb`

### htmx:beforeSwap — Control Swap Behavior

Modify how (or whether) the response is swapped into the DOM. Essential for handling error responses.

```javascript
document.body.addEventListener("htmx:beforeSwap", function(evt) {
    // Swap on 404 (normally htmx only swaps 2xx responses)
    if (evt.detail.xhr.status === 404) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }

    // Change swap strategy for this response
    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.swapOverride = "innerHTML";
        evt.detail.target = htmx.find("#errors");
    }

    // Prevent swap entirely
    if (evt.detail.xhr.status === 204) {
        evt.detail.shouldSwap = false;
    }
});
```

**detail properties:** `elt`, `xhr`, `shouldSwap`, `isError`, `target`, `swapOverride`, `selectOverride`

### htmx:afterSwap / htmx:afterSettle — Post-Swap Actions

`afterSwap` fires immediately after content insertion. `afterSettle` fires after htmx processes attributes on new content.

```javascript
// Re-initialize third-party libraries after swap
document.body.addEventListener("htmx:afterSettle", function(evt) {
    // evt.detail.target is the element that received new content
    initTooltips(evt.detail.target);
    initDropdowns(evt.detail.target);
});
```

### htmx:responseError — Error Handling

Fires when the server returns a non-2xx/3xx status.

```javascript
document.body.addEventListener("htmx:responseError", function(evt) {
    const status = evt.detail.xhr.status;
    if (status === 401) {
        window.location.href = "/login";
    } else if (status === 500) {
        showToast("Server error. Please try again.");
    }
});

// Network-level errors (no response at all)
document.body.addEventListener("htmx:sendError", function(evt) {
    showToast("Network error. Check your connection.");
});

// Timeout
document.body.addEventListener("htmx:timeout", function(evt) {
    showToast("Request timed out.");
});
```

### htmx:confirm — Custom Confirmation Dialogs

Intercept and replace the default browser `confirm()` with a custom dialog.

```html
<button hx-delete="/items/42" hx-confirm="Are you sure?">Delete</button>
```

```javascript
document.body.addEventListener("htmx:confirm", function(evt) {
    evt.preventDefault(); // pause the request

    showCustomDialog(evt.detail.question).then(function(confirmed) {
        if (confirmed) {
            evt.detail.issueRequest(); // proceed with the request
        }
    });
});
```

**detail properties:** `elt`, `target`, `path`, `verb`, `question`, `issueRequest()`

### htmx:load — Initialize New Content

Fires when new content is added to the DOM. The preferred way to initialize JS on htmx-loaded content.

```javascript
htmx.onLoad(function(elt) {
    // elt is the newly added element
    var charts = elt.querySelectorAll(".chart");
    charts.forEach(function(chart) {
        new Chart(chart, getChartConfig(chart));
    });
});
```

### htmx:validateUrl — Security Gate

Prevents requests to untrusted URLs. Cancel to block the request.

```javascript
document.body.addEventListener("htmx:validateUrl", function(evt) {
    if (!evt.detail.sameHost) {
        evt.preventDefault(); // block cross-origin requests
    }
});
```

### Other Notable Events

| Event | Use Case |
|-------|----------|
| `htmx:beforeRequest` | Show loading indicators |
| `htmx:afterRequest` | Hide loading indicators (fires on success AND error) |
| `htmx:beforeCleanupElement` | Teardown before element removal |
| `htmx:beforeHistorySave` | Modify content before history caching |
| `htmx:oobBeforeSwap` | Configure out-of-band swap behavior |
| `htmx:abort` | Send to element to cancel in-flight request |
| `htmx:validation:validate` | Custom validation before request |
| `htmx:pushedIntoHistory` | After URL pushed to history |

**Aborting a request from outside:**
```javascript
htmx.trigger(document.getElementById("my-request"), "htmx:abort");
```

---

## HTTP Request Headers

Headers htmx sends with every AJAX request:

| Header | Value | Description |
|--------|-------|-------------|
| `HX-Request` | `true` | Always present. Use server-side to detect htmx requests |
| `HX-Trigger` | Element ID | The `id` of the element that triggered the request |
| `HX-Trigger-Name` | Element name | The `name` of the element that triggered the request |
| `HX-Target` | Element ID | The `id` of the target element (if it exists) |
| `HX-Current-URL` | Full URL | The current browser URL |
| `HX-Boosted` | `true` | Present only if request is via `hx-boost` |
| `HX-Prompt` | User input | The user's response to `hx-prompt` (if used) |
| `HX-History-Restore-Request` | `true` | Present when restoring from history cache miss |

### Server-Side Detection Examples

**Django:**
```python
def my_view(request):
    if request.headers.get("HX-Request"):
        return render(request, "partial.html", context)
    return render(request, "full_page.html", context)
```

**Python/Flask:**
```python
@app.route("/endpoint")
def endpoint():
    if request.headers.get("HX-Request"):
        return render_template("partial.html")
    return render_template("full.html")
```

---

## HTTP Response Headers

Headers the server sends back to control htmx behavior.

**Important:** Response headers are NOT processed on 3xx status codes.

### Navigation Headers

| Header | Description |
|--------|-------------|
| `HX-Location` | Client-side redirect via AJAX (no full reload). Creates history entry |
| `HX-Redirect` | Client-side redirect with full page reload |
| `HX-Push-Url` | Push URL into browser history (or `false` to prevent) |
| `HX-Replace-Url` | Replace current URL in history (no new entry) (or `false` to prevent) |
| `HX-Refresh` | Set to `true` to trigger full page refresh |

### Content Control Headers

| Header | Description |
|--------|-------------|
| `HX-Reswap` | Override the swap strategy (e.g., `innerHTML`, `outerHTML`, `beforeend`) |
| `HX-Retarget` | CSS selector to redirect the swap to a different element |
| `HX-Reselect` | CSS selector to pick which part of the response to swap |

### Event Trigger Headers

| Header | When Events Fire |
|--------|-----------------|
| `HX-Trigger` | Immediately when response is received |
| `HX-Trigger-After-Swap` | After the swap step |
| `HX-Trigger-After-Settle` | After the settle step |

### HX-Location — AJAX Redirect

Performs a client-side redirect using AJAX (like a boosted link). Creates a history entry.

**Simple redirect:**
```
HX-Location: /new-page
```

**With options (JSON):**
```
HX-Location: {"path":"/new-page", "target":"#content", "swap":"innerHTML", "select":"#main"}
```

JSON properties: `path` (required), `target`, `source`, `event`, `handler`, `swap`, `values`, `headers`, `select`, `push` (`false` or path string), `replace` (path string)

### HX-Push-Url / HX-Replace-Url — History Management

```
HX-Push-Url: /new-url          # adds history entry
HX-Push-Url: false             # prevents history push

HX-Replace-Url: /new-url       # replaces current entry (no back button)
HX-Replace-Url: false          # prevents URL replacement
```

Both override their corresponding `hx-push-url` / `hx-replace-url` attributes.

### HX-Redirect — Full Page Redirect

```
HX-Redirect: /login
```

Triggers a full browser navigation (not AJAX). Use `HX-Location` for AJAX-based redirect instead.

### HX-Trigger — Server-Triggered Client Events

**Single event:**
```
HX-Trigger: myEvent
```

**Multiple events:**
```
HX-Trigger: event1, event2
```

**Event with simple data:**
```json
HX-Trigger: {"showMessage":"Here Is A Message"}
```
Access: `evt.detail.value`

**Event with structured data:**
```json
HX-Trigger: {"showMessage":{"level":"info","message":"Saved successfully"}}
```
Access: `evt.detail.level`, `evt.detail.message`

**Multiple events with data:**
```json
HX-Trigger: {"showToast":"Item saved","refreshList":"true"}
```

**Target a specific element:**
```json
HX-Trigger: {"showMessage":{"target":"#notifications","level":"info","message":"Done"}}
```

**Listening for server-triggered events:**
```javascript
document.body.addEventListener("showMessage", function(evt) {
    showToast(evt.detail.level, evt.detail.value || evt.detail.message);
});
```

```html
<!-- Declarative: trigger another htmx request when event fires -->
<div hx-get="/notifications" hx-trigger="refreshNotifications from:body"></div>
```

### HX-Reswap / HX-Retarget / HX-Reselect — Override Swap Behavior

```
HX-Reswap: outerHTML           # change swap strategy
HX-Retarget: #error-container  # change target element
HX-Reselect: #main-content     # select part of the response
```

Useful for error responses where you want to swap into a different element with a different strategy:

```python
# Django example: validation error targets the form
response = render(request, "form_errors.html", {"errors": errors})
response["HX-Retarget"] = "#my-form"
response["HX-Reswap"] = "innerHTML"
response.status_code = 422
return response
```

---

## JavaScript API

### Programmatic AJAX Requests — htmx.ajax()

```javascript
// Simple: GET, swap innerHTML of target
htmx.ajax("GET", "/api/items", "#results");

// With context object for full control
htmx.ajax("GET", "/api/items", {
    target: "#results",
    swap: "innerHTML",
    values: { page: 2, search: "query" },
    headers: { "X-Custom": "value" },
    source: "#search-form",
    select: "#items-list"
});

// Returns a Promise
htmx.ajax("POST", "/api/items", {
    target: "#results",
    values: { name: "New Item" }
}).then(function() {
    console.log("Request complete and content swapped");
});
```

### Processing New Content — htmx.process()

Call after manually inserting HTML that contains htmx attributes:

```javascript
var container = document.getElementById("dynamic");
container.innerHTML = '<button hx-get="/api/data" hx-target="#output">Load</button>';
htmx.process(container); // activates htmx on new content
```

### DOM Content Swap — htmx.swap()

```javascript
htmx.swap("#output", "<div>New content</div>", { swapStyle: "innerHTML" });
```

### Event Methods

```javascript
// Listen for events
htmx.on("htmx:afterSwap", function(evt) { /* ... */ });
htmx.on("#my-element", "click", function(evt) { /* ... */ });

// Stop listening
htmx.off("htmx:afterSwap", myHandler);
htmx.off("#my-element", "click", myHandler);

// Trigger events programmatically
htmx.trigger("#my-element", "myEvent", { answer: 42 });

// Register load handler (fires for initial and swapped content)
htmx.onLoad(function(elt) {
    // Initialize components in elt
    elt.querySelectorAll("[data-tooltip]").forEach(initTooltip);
});
```

### DOM Query Helpers

```javascript
htmx.find("#my-element");              // returns single element
htmx.find(parentEl, ".child");         // scoped search
htmx.findAll(".items");                // returns NodeList
htmx.findAll(parentEl, ".items");      // scoped search
htmx.closest(element, "form");         // traverse up the DOM
```

### CSS Class Manipulation

All accept optional delay in milliseconds:

```javascript
htmx.addClass(elt, "active");           // immediate
htmx.addClass(elt, "fade-in", 100);     // after 100ms delay
htmx.removeClass(elt, "active");
htmx.removeClass(elt, "active", 2000);  // remove after 2s
htmx.toggleClass(elt, "open");
htmx.takeClass(elt, "selected");        // removes "selected" from all siblings, adds to elt
```

### DOM Manipulation

```javascript
htmx.remove(elt);          // remove element immediately
htmx.remove(elt, 2000);    // remove after 2 second delay
```

### Utilities

```javascript
// Get form values as htmx would resolve them
htmx.values(htmx.find("#myForm"));
// Returns: { field1: "value1", field2: "value2" }

// Parse timing strings
htmx.parseInterval("3s");    // 3000
htmx.parseInterval("500ms"); // 500
htmx.parseInterval("2m");    // 120000
```

### Debugging

```javascript
htmx.logAll();   // log every htmx event to console (verbose)
htmx.logNone();  // disable logging

// Custom logger
htmx.logger = function(elt, event, data) {
    if (event === "htmx:configRequest") {
        console.log("Request config:", data);
    }
};
```

### Extensions

```javascript
htmx.defineExtension("my-ext", {
    onEvent: function(name, evt) {
        if (name === "htmx:beforeRequest") {
            console.log("Request starting");
        }
    },
    transformResponse: function(text, xhr, elt) {
        return text; // modify response HTML
    },
    handleSwap: function(swapStyle, target, fragment, settleInfo) {
        // custom swap handling
        return false; // return false to use default swap
    }
});

htmx.removeExtension("my-ext");
```

### Configuration — htmx.config

```javascript
// Override default configuration
htmx.config.defaultSwapStyle = "outerHTML";     // default: "innerHTML"
htmx.config.timeout = 10000;                     // request timeout in ms (default: 0 = none)
htmx.config.historyCacheSize = 20;                // default: 10
htmx.config.withCredentials = true;               // include cookies in CORS
htmx.config.selfRequestsOnly = true;              // only allow same-origin requests (default: true)
htmx.config.allowEval = true;                     // allow inline event handlers (default: true)
htmx.config.getCacheBusterParam = false;           // add cache-buster to GET (default: false)
htmx.config.globalViewTransitions = false;         // enable View Transition API (default: false)
htmx.config.defaultSettleDelay = 20;               // ms before settling (default: 20)
htmx.config.defaultSwapDelay = 0;                  // ms before swapping (default: 0)
htmx.config.scrollBehavior = "instant";            // or "smooth" (default: "instant")
htmx.config.scrollIntoViewOnBoost = true;          // scroll to top on boost (default: true)
htmx.config.includeIndicatorStyles = true;         // inject .htmx-indicator CSS (default: true)
htmx.config.allowNestedOobSwaps = true;            // process OOB in nested elements (default: true)
htmx.config.responseHandling = [                   // customize response code handling
    { code: "204", swap: false },
    { code: "[23]..", swap: true },
    { code: "[45]..", swap: false, error: true },
];
```

---

## Common Patterns

### Loading Indicators with Events

```javascript
document.body.addEventListener("htmx:beforeRequest", function(evt) {
    evt.detail.elt.classList.add("loading");
});

document.body.addEventListener("htmx:afterRequest", function(evt) {
    evt.detail.elt.classList.remove("loading");
});
```

### Global Error Handler

```javascript
document.body.addEventListener("htmx:beforeSwap", function(evt) {
    var status = evt.detail.xhr.status;
    if (status === 401) {
        window.location.href = "/login";
        evt.detail.shouldSwap = false;
    } else if (status === 403) {
        evt.detail.shouldSwap = true;
        evt.detail.target = htmx.find("#error-display");
    } else if (status === 422) {
        // Validation errors — swap into the form
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    } else if (status >= 500) {
        evt.detail.shouldSwap = false;
        showToast("Server error. Please try again.");
    }
});
```

### CSRF Token Injection (Django)

```javascript
document.body.addEventListener("htmx:configRequest", function(evt) {
    var csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value
        || document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    if (csrfToken) {
        evt.detail.headers["X-CSRFToken"] = csrfToken;
    }
});
```

### Server-Triggered Toast Notifications

Server sends: `HX-Trigger: {"showToast":{"message":"Saved","level":"success"}}`

```javascript
document.body.addEventListener("showToast", function(evt) {
    var detail = evt.detail;
    var message = detail.message || detail.value;
    var level = detail.level || "info";
    // render toast notification
    renderToast(message, level);
});
```

### Cascading Updates via Server Events

```html
<!-- These elements re-fetch when server triggers their events -->
<div hx-get="/cart/count" hx-trigger="cartUpdated from:body">#cart-count</div>
<div hx-get="/notifications" hx-trigger="notificationsChanged from:body">#notifications</div>
```

Server response header after adding to cart:
```
HX-Trigger: cartUpdated, notificationsChanged
```

### Programmatic Request After User Action

```javascript
document.getElementById("save-btn").addEventListener("click", function() {
    var data = collectFormData();
    htmx.ajax("POST", "/api/save", {
        target: "#result",
        swap: "innerHTML",
        values: data
    });
});
```
