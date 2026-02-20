# htmx: Common UI Patterns
Based on htmx 2.0.8 documentation.

Practical cookbook of common UI patterns. Each pattern shows HTML markup,
expected server response, and key attributes.

---

## 1. CRUD Patterns

### Click-to-Edit

Switch between read-only view and inline edit form.

```html
<div hx-target="this" hx-swap="outerHTML">
  <div><label>First Name</label>: Joe</div>
  <div><label>Email</label>: joe@blow.com</div>
  <button hx-get="/contact/1/edit" class="btn primary">Click To Edit</button>
</div>
```

Server returns an edit form on GET `/contact/1/edit`:

```html
<form hx-put="/contact/1" hx-target="this" hx-swap="outerHTML">
  <input type="text" name="firstName" value="Joe">
  <input type="email" name="email" value="joe@blow.com">
  <button type="submit">Submit</button>
  <button hx-get="/contact/1">Cancel</button>
</form>
```

On PUT submit, server returns the updated read-only view. On cancel GET, server
returns the original. Key: `hx-target="this"` + `hx-swap="outerHTML"`.

### Edit Row

Inline table row editing. `hx-include="closest tr"` gathers input values from the row.

```html
<tbody hx-target="closest tr" hx-swap="outerHTML">
  <tr>
    <td>Joe Smith</td>
    <td>joe@smith.org</td>
    <td><button hx-get="/contact/1/edit" hx-trigger="edit">Edit</button></td>
  </tr>
</tbody>
```

Server returns editable row; Save button uses `hx-put="/contact/1" hx-include="closest tr"`.
Use custom `edit`/`cancel` triggers with JS to enforce single-row editing.

### Delete Row

Delete with confirmation and fade-out.

```html
<tbody hx-confirm="Are you sure?" hx-target="closest tr" hx-swap="outerHTML swap:1s">
  <tr>
    <td>Angie MacDowell</td>
    <td>Active</td>
    <td><button class="btn danger" hx-delete="/contact/1">Delete</button></td>
  </tr>
</tbody>
```

Server responds with **empty body** and 200. The `swap:1s` delay lets CSS animate:

```css
tr.htmx-swapping td { opacity: 0; transition: opacity 1s ease-out; }
```

### Bulk Update

Form-wrapped table with checkboxes for batch operations.

```html
<form id="checked-contacts" hx-post="/users" hx-swap="innerHTML settle:3s"
      hx-target="#toast">
  <table><tbody>
    <tr>
      <td>Joe Smith</td>
      <td><input type="checkbox" name="active:joe@smith.org" checked></td>
    </tr>
  </tbody></table>
  <input type="submit" value="Bulk Update">
  <output id="toast"></output>
</form>
```

Server returns a confirmation message. `settle:3s` lets CSS fade the toast out.

---

## 2. Search & Filtering

### Active Search

Live search with debouncing.

```html
<input type="search" name="search"
       hx-post="/search"
       hx-trigger="input changed delay:500ms, keyup[key=='Enter'], load"
       hx-target="#search-results"
       hx-indicator=".htmx-indicator">
<tbody id="search-results"></tbody>
```

Server returns `<tr>` rows. Trigger modifiers: `changed` prevents duplicate requests,
`delay:500ms` debounces, `load` runs on page load.

### Value Select (Cascading Dropdowns)

```html
<select name="make" hx-get="/models" hx-target="#models">
  <option value="audi">Audi</option>
  <option value="toyota">Toyota</option>
  <option value="bmw">BMW</option>
</select>
<select id="models" name="model"></select>
```

Server returns `<option>` elements. Default trigger for `<select>` is `change`.

---

## 3. Loading Patterns

### Lazy Load

Load content when element enters the DOM.

```html
<div hx-get="/graph" hx-trigger="load">
  <img class="htmx-indicator" src="/img/bars.svg"/>
</div>
```

Server returns actual content. Use CSS transitions on `htmx-added` for fade-in.

### Click-to-Load

Manual "Load More" pagination.

```html
<tr id="replaceMe">
  <td colspan="3">
    <button hx-get="/contacts/?page=2" hx-target="#replaceMe" hx-swap="outerHTML">
      Load More...
    </button>
  </td>
</tr>
```

Server returns new rows plus a new button with `page=3`. Button replaces itself.

### Infinite Scroll

Automatic loading on scroll.

```html
<tr hx-get="/contacts/?page=2" hx-trigger="revealed" hx-swap="afterend">
  <td>Last visible row...</td>
</tr>
```

`hx-trigger="revealed"` fires when element scrolls into viewport. Last row in each
batch carries the trigger for the next page. For CSS overflow containers use
`hx-trigger="intersect once"` instead.

---

## 4. Forms & Validation

### Inline Validation

Validate individual fields by posting to the server.

```html
<div hx-target="this" hx-swap="outerHTML">
  <label>Email Address</label>
  <input name="email" hx-post="/contact/email" hx-indicator="#ind">
  <img id="ind" src="/img/bars.svg" class="htmx-indicator"/>
</div>
```

Server returns the entire wrapper with error/success state:

```html
<div hx-target="this" hx-swap="outerHTML" class="error">
  <label>Email Address</label>
  <input name="email" value="test@foo.com" hx-post="/contact/email">
  <div class="error-message">That email is already taken.</div>
</div>
```

### File Upload with Progress

```html
<form id="form" hx-encoding="multipart/form-data" hx-post="/upload">
  <input type="file" name="file">
  <button>Upload</button>
  <progress id="progress" value="0" max="100"></progress>
</form>
<script>
  htmx.on('#form', 'htmx:xhr:progress', function(evt) {
    htmx.find('#progress').setAttribute('value', evt.detail.loaded/evt.detail.total * 100);
  });
</script>
```

`hx-encoding="multipart/form-data"` is required for file uploads.

### File Input Preservation

Keep file input populated when validation fails. Two methods:

```html
<!-- Method 1: hx-preserve keeps element across swaps -->
<form id="binaryForm" hx-swap="outerHTML" hx-target="#binaryForm">
  <input hx-preserve id="fileInput" type="file" name="binaryFile">
  <button type="submit">Submit</button>
</form>

<!-- Method 2: place input outside the swap target -->
<input form="binaryForm" type="file" name="binaryFile">
<form id="binaryForm" hx-swap="outerHTML" hx-target="#binaryForm">
  <button type="submit">Submit</button>
</form>
```

### Reset Input After Submission

```html
<form hx-post="/note" hx-target="#notes" hx-swap="afterbegin"
      hx-on::after-request="if(event.detail.successful) this.reset()">
  <input type="text" name="note-text">
  <button class="btn">Add</button>
</form>
<ul id="notes"></ul>
```

`hx-on::after-request` runs JS after request. `this.reset()` clears on 2xx only.

---

## 5. Modals & Dialogs

### Native Dialogs

```html
<button hx-post="/submit" hx-prompt="Enter a string" hx-confirm="Are you sure?"
        hx-target="#response">
  Submit
</button>
```

Prompt value sent via `HX-Prompt` request header. Confirm fires first, then prompt.

### Custom Confirmation (SweetAlert2)

```javascript
document.addEventListener("htmx:confirm", function(e) {
  if (!e.detail.question) return;
  e.preventDefault();
  Swal.fire({ title: "Proceed?", text: e.detail.question })
    .then(result => { if (result.isConfirmed) e.detail.issueRequest(true); });
});
```

`e.preventDefault()` stops native dialog. `e.detail.issueRequest(true)` fires request.

### Bootstrap Modal

```html
<button hx-get="/modal" hx-target="#modals-here" hx-trigger="click"
        data-bs-toggle="modal" data-bs-target="#modals-here">Open Modal</button>
<div id="modals-here" class="modal modal-blur fade" style="display:none">
  <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
    <div class="modal-content"></div>
  </div>
</div>
```

Server returns Bootstrap modal-dialog/content/header/body/footer markup.

### Custom Modal (No Framework)

```html
<button hx-get="/modal" hx-target="body" hx-swap="beforeend">Open Modal</button>
```

Server returns full overlay + dialog HTML appended to body. Handle close with
JS event listeners on the returned content.

---

## 6. Navigation

### Tabs -- HATEOAS (Server-Driven)

Server owns all tab state. Each click fetches full tab bar + content.

```html
<div id="tabs" hx-get="/tab1" hx-trigger="load delay:100ms"
     hx-target="#tabs" hx-swap="innerHTML"></div>
```

Server returns complete interface:

```html
<div role="tablist">
  <button role="tab" hx-get="/tab1" class="selected" aria-selected="true">Tab 1</button>
  <button role="tab" hx-get="/tab2">Tab 2</button>
</div>
<div role="tabpanel">Content for Tab 1</div>
```

### Tabs -- JavaScript (Client-Driven)

Client manages selected state; server returns only content.

```html
<div id="tabs" hx-target="#tab-contents" role="tablist"
     hx-on:htmx-after-on-load="
       document.querySelector('[aria-selected=true]').setAttribute('aria-selected','false');
       this.querySelector('[hx-get]').setAttribute('aria-selected','true');
     ">
  <button role="tab" aria-selected="true" hx-get="/tab1">Tab 1</button>
  <button role="tab" hx-get="/tab2">Tab 2</button>
</div>
<div id="tab-contents" role="tabpanel" hx-get="/tab1" hx-trigger="load"></div>
```

---

## 7. Visual Feedback

### CSS Transitions

htmx adds classes during the swap lifecycle for CSS transitions.

**Fade out on removal** (`htmx-swapping`):

```css
.fade-me-out.htmx-swapping { opacity: 0; transition: opacity 1s ease-out; }
```
```html
<button class="fade-me-out" hx-delete="/item" hx-swap="outerHTML swap:1s">Delete</button>
```

**Fade in on addition** (`htmx-added`):

```css
#el.htmx-added { opacity: 0; }
#el { opacity: 1; transition: opacity 1s ease-out; }
```

**Smooth property transitions** (stable IDs): when server returns same `id` with
different `style`, htmx settles values and CSS transitions animate the change.

**View Transitions API**: use `hx-swap="innerHTML transition:true"`.

### Progress Bar (Server-Polled)

```html
<div hx-get="/job/progress" hx-trigger="every 600ms" hx-target="this" hx-swap="innerHTML">
  <div class="progress" role="progressbar" aria-valuenow="0">
    <div id="pb" class="progress-bar" style="width:0%"></div>
  </div>
</div>
```

Polls server every 600ms. Stable `id` on `#pb` enables smooth CSS width transitions.
When complete, server sends `HX-Trigger: done` header to trigger final view swap.

---

## 8. Advanced Patterns

### Updating Other Content

Four approaches when an action needs to update another part of the page:

1. **Expand target** -- wrap related elements, target the wrapper
2. **OOB swaps** -- server returns `<tbody hx-swap-oob="beforeend:#contacts-table">`
3. **Events** -- server sends `HX-Trigger: newContact`; table has
   `hx-trigger="newContact from:body"` to re-fetch
4. **Path deps extension** -- `hx-ext="path-deps" path-deps="/contacts"` auto-refreshes
   elements sharing a path when POST occurs

### Async Authentication

Gate requests behind async auth using `htmx:confirm` to delay.

```javascript
let authToken = null;
let auth = fetch("/token").then(r => r.text()).then(t => { authToken = t; });

htmx.on("htmx:confirm", (e) => {
  if (authToken == null) { e.preventDefault(); auth.then(() => e.detail.issueRequest()); }
});
htmx.on("htmx:configRequest", (e) => { e.detail.headers["AUTH"] = authToken; });
```

Key: `htmx:confirm` can delay any request. `issueRequest()` resumes after async completes.

### Keyboard Shortcuts

```html
<button hx-trigger="click, keyup[altKey&&shiftKey&&key=='D'] from:body" hx-post="/doit">
  Do It! (Alt+Shift+D)
</button>
```

`from:body` makes the listener global. Filter syntax uses JS keyboard event properties.

### Web Components

htmx ignores Shadow DOM by default. Call `htmx.process(root)` after attaching:

```javascript
customElements.define('my-component', class extends HTMLElement {
  connectedCallback() {
    const root = this.attachShadow({ mode: 'closed' });
    root.innerHTML = `<button hx-get="/clicked" hx-target="next div">Click</button><div></div>`;
    htmx.process(root);
  }
});
```

Selectors scope to same shadow root. Use `host:` or `global:` prefixes for outside targets.

### Sortable (Drag-and-Drop)

```html
<form class="sortable" hx-post="/items" hx-trigger="end">
  <div><input type="hidden" name="item" value="1"/>Item 1</div>
  <div><input type="hidden" name="item" value="2"/>Item 2</div>
</form>
```

`hx-trigger="end"` listens for Sortable.js `end` event. Initialize Sortable in
`htmx.onLoad()`. Hidden inputs carry item IDs so server receives new order as form data.

### moveBefore (Experimental)

```html
<video hx-preserve id="my-video" src="/video.mp4" autoplay></video>
```

Elements with `hx-preserve` and stable IDs maintain internal state (playback, focus)
across swaps. Requires browser `moveBefore()` API support (experimental).

---

## Quick Reference

**Swap lifecycle CSS classes:** `htmx-request` (during request), `htmx-swapping`
(during swap, for exit animations), `htmx-settling` (during settle, for property
transitions), `htmx-added` (on new elements, for enter animations).

**Key response headers:** `HX-Trigger` (fire client event), `HX-Redirect` (redirect),
`HX-Retarget` (change target), `HX-Reswap` (change swap strategy).

**Key events:** `htmx:confirm` (intercept/delay requests), `htmx:configRequest`
(modify headers/params), `htmx:afterRequest` (post-request logic), `htmx:afterSwap`
(post-swap logic), `htmx:xhr:progress` (upload progress tracking).
