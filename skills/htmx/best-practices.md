# htmx: Best Practices & Architecture
Based on htmx 2.0.8 documentation.

## 1. Hypermedia-Driven Application (HDA) Architecture

An HDA merges the simplicity of traditional multi-page applications with SPA-level interactivity. Two defining constraints:

1. **Declarative HTML syntax** -- interactions are expressed in HTML attributes, not imperative scripts.
2. **Hypermedia communication** -- the server returns HTML, not JSON. The browser renders it directly.

| Aspect | HDA (htmx) | SPA (React, Vue, etc.) |
|--------|-----------|----------------------|
| Server response format | HTML fragments | JSON data |
| State management | Server-driven (HATEOAS) | Client-side stores |
| Routing | Server-side, real URLs | Client-side router |
| REST alignment | Naturally REST-ful | REST is incidental |
| JavaScript role | Enhancement, not foundation | Core application layer |
| Offline capability | Limited | Achievable with service workers |

**Core example -- an active search field:**

```html
<input type="search"
       hx-post="/search"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#search-results">
<div id="search-results"></div>
```

The behavior is declared in HTML. The server returns an HTML fragment. No client-side state, no JSON parsing, no template rendering in the browser.

---

## 2. When to Use htmx

### Good Fits

- **Text and image-heavy UIs.** Content sites, dashboards, admin panels. The web's native medium.
- **CRUD applications.** Showing forms, saving data, displaying results. Rails-style apps are ideal.
- **Block-based updates.** UI changes happen within well-defined regions (a contact card, a table, a sidebar) rather than scattered across the page.
- **Deep linking and initial load performance.** Browsers are very good at rendering HTML given a URL. SSR is the default, not a bolt-on optimization.
- **SEO-sensitive applications.** HTML responses are indexable out of the box.

### Poor Fits

- **Highly interactive, real-time UIs.** Collaborative editors (Google Docs), spreadsheets (Google Sheets), or map applications (Google Maps) need client-side state and fine-grained reactivity.
- **Offline-first applications.** htmx depends on the server for rendering. No server, no UI.
- **Frequent, scattered state updates.** When a single action must update many unrelated parts of the page simultaneously, a client-side state store may be simpler.
- **Mouse-position or frame-rate-sensitive interactions.** Games, drawing tools, drag-heavy interfaces.

### The Decision Heuristic

If your application is primarily about **displaying and manipulating records** through **forms and links** with **page-section-level updates**, htmx is likely the simpler choice. If your application is primarily about **real-time collaboration**, **complex client-side state**, or **offline usage**, an SPA framework is likely better.

---

## 3. Top Tips for SSR/HDA Apps

### Tip 1: Maximize Server-Side Strengths

Use mature server framework features: caching, ORM optimization, middleware. Target sub-100ms response times for HTML partials.

### Tip 2: Factor on the Server, Not the Client

Organize code with server-side patterns (MVC, service layers). Break templates using template inclusion and fragments -- not component-based client-side architectures.

### Tip 3: Specialize Your Endpoints

htmx endpoints serve your UI, not arbitrary clients. Return exactly the HTML your UI needs. Do not build generic REST resources -- build purpose-specific hypermedia responses.

### Tip 4: Refactor Endpoints Aggressively

Because the server controls both the HTML and the endpoint, you can reshape your API freely. No versioning, no client coordination. HATEOAS means the response *is* the interface contract.

### Tip 5: Use Direct Data Store Access

Server-side rendering means you can use joins, aggregation, and advanced SQL directly. Target three or fewer database queries per request.

### Tip 6: Avoid Modals

Modals create problematic client-side state and fight the web's navigation model. Prefer inline editing, expanding sections, or navigating to a dedicated page.

### Tip 7: Accept "Good Enough" UX

A uniform interface trades peak efficiency for simplicity. A slightly less interactive solution that eliminates a client-side state management layer is usually the right trade-off.

### Tip 8: Create Islands of Interactivity

When a specific interaction truly needs client-side logic (drag-and-drop reordering, a rich text editor), use a focused library for just that widget. Integrate it with htmx via events. Keep the island small and isolated.

```html
<!-- Island: SortableJS handles drag-and-drop, htmx persists the new order -->
<div id="sortable-list" hx-post="/reorder" hx-trigger="end">
  <div class="item" data-id="1">Item 1</div>
  <div class="item" data-id="2">Item 2</div>
</div>
```

### Tip 9: Script When Needed

Scripting is part of the web architecture. Use it for progressive enhancement -- but keep hypermedia exchanges as the primary state-change mechanism. Alpine.js and hyperscript are natural companions for small inline behaviors.

### Tip 10: Be Pragmatic

htmx is a tool, not a religion. If a particular feature genuinely needs SPA-level interactivity, build it that way. The goal is to use the simplest approach that works for each part of the application.

---

## 4. Locality of Behaviour (LoB)

**Principle:** "The behaviour of a unit of code should be as obvious as possible by looking only at that unit of code."

### htmx Embodies LoB

```html
<button hx-get="/clicked" hx-target="#result">Click Me</button>
```

Reading this single element tells you: clicking this button makes a GET to `/clicked` and puts the response in `#result`. No hunting through JS files.

### The jQuery Anti-Pattern

```javascript
// behavior.js -- somewhere else entirely
$("#d1").on("click", function() {
  $.ajax({ url: "/clicked", success: function(data) { $("#result").html(data); } });
});
```

```html
<button id="d1">Click Me</button>
```

The button's behavior is invisible from the HTML. This is "spooky action at a distance."

### LoB vs Separation of Concerns

LoB intentionally trades strict SoC for readability. When behavior is declared inline in HTML, you sacrifice the "all behavior in JS files" separation -- but you gain the ability to understand any element by reading it. For htmx applications, this trade-off strongly favors LoB.

**Guideline:** Prefer declaring behavior in HTML attributes. Extract to JS only when the logic is too complex for an attribute or is reused across many elements.

---

## 5. Template Fragments

### The Problem

htmx frequently needs partial HTML responses -- just the updated table row, just the new form state. Without fragment support, you split templates into many tiny files, losing context and locality.

### The Solution: Render Fragments from a Single Template

Define named sections within a full-page template. Render either the whole page (initial load) or just a fragment (htmx request).

**Django 6.0 partials example:**

```django
{# contacts/detail.html #}
{% extends "base.html" %}

{% block content %}
<h1>{{ contact.name }}</h1>

{% partialdef archive-ui inline %}
  {% if contact.archived %}
    <button hx-patch="{% url 'contacts:unarchive' contact.id %}"
            hx-target="closest div">Unarchive</button>
  {% else %}
    <button hx-delete="{% url 'contacts:archive' contact.id %}"
            hx-target="closest div">Archive</button>
  {% endif %}
{% endpartialdef %}
{% endblock %}
```

**View returns the fragment for htmx, full page otherwise:**

```python
def archive_contact(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id)
    contact.archived = True
    contact.save()
    # Return just the fragment for htmx requests
    return render(request, "contacts/detail.html#archive-ui", {"contact": contact})
```

### Why This Matters

- **One file, one feature.** The full page and the htmx partial live together.
- **LoB preserved.** The button, its htmx attributes, and the server template are co-located.
- **Fewer files.** You do not need `_archive_button.html` as a separate partial.

If your template engine lacks fragment support, extract to a separate partial file and `{% include %}` it in the full-page template. The fragment approach is preferred when available.

---

## 6. API Design: Hypermedia vs Data APIs

### The Two-API Architecture

Most applications benefit from separating two distinct API types:

```
Data API (JSON)  -->  External clients, mobile apps, third-party integrations
                      Stable, versioned, documented, generic

Hypermedia API (HTML)  -->  Your web application's frontend only
                            Specialized, freely refactorable, undocumented
```

### Why They Must Be Separate

| Concern | Data API (JSON) | Hypermedia API (HTML) |
|---------|----------------|----------------------|
| Consumers | Many unknown clients | Your frontend only |
| Stability | Must be versioned | Changes freely with the UI |
| Shape | Generic, resource-oriented | UI-optimized, endpoint-per-interaction |
| Self-describing | Needs documentation | HTML *is* the documentation |
| Security | Expressive queries = attack surface | Server controls all query logic |

### Practical Implications

**Do not reuse JSON API endpoints for htmx.** htmx endpoints return HTML shaped for a specific UI interaction. They are not resources in the REST-API sense. They are "a half of your app."

**Do not version htmx endpoints.** When you change the HTML a hypermedia endpoint returns, the new interface is automatically reflected in the browser. No client code to update.

**Do not document htmx endpoints externally.** They are internal implementation details of your web application, not a public contract.

```python
# Data API -- stable, generic, documented
@api_view(["GET"])
def contacts_api(request):
    contacts = Contact.objects.all()
    return JsonResponse({"contacts": serialize(contacts)})

# Hypermedia API -- specialized, UI-optimized, undocumented
def contacts_table_fragment(request):
    contacts = Contact.objects.select_related("company").all()
    return render(request, "contacts/table.html#rows", {"contacts": contacts})
```

---

## 7. Updating Multiple Parts of the Page

When a single htmx request needs to update more than one DOM element, there are four strategies. Choose based on complexity and coupling.

### Strategy 1: Expand the Target (Simplest)

Wrap related elements in a shared container and target that container.

```html
<div id="contact-section">
  <table id="contacts-table">...</table>
  <form hx-post="/contacts" hx-target="#contact-section">...</form>
</div>
```

The server response replaces the entire section, including both the table and the form. Simple, predictable, but may re-render more DOM than necessary.

### Strategy 2: Out-of-Band Swaps (hx-swap-oob)

The primary response updates the target normally. Additional elements in the response with `hx-swap-oob` update other parts of the page.

```html
<!-- Primary response (goes to the normal target) -->
<form id="contact-form">...</form>

<!-- Out-of-band: also update the table body -->
<tbody id="contacts-table" hx-swap-oob="beforeend">
  <tr><td>New Contact</td><td>new@example.com</td></tr>
</tbody>
```

Powerful but creates coupling between the response and specific DOM IDs. Use when the server knows exactly what else needs updating.

### Strategy 3: Server-Triggered Events

The server response includes an `HX-Trigger` response header. Other elements listen for that event and independently refresh themselves.

```html
<!-- This element refreshes itself when it hears "contactsChanged" -->
<table id="contacts-table"
       hx-get="/contacts/table"
       hx-trigger="contactsChanged from:body">
  ...
</table>

<!-- This form triggers the event via the server's HX-Trigger header -->
<form hx-post="/contacts" hx-target="#contact-form">...</form>
```

Server response:
```
HTTP/1.1 200 OK
HX-Trigger: contactsChanged
Content-Type: text/html

<form id="contact-form">...</form>
```

**This is the most decoupled approach.** The form does not know about the table. The table does not know about the form. They communicate through events.

### Strategy 4: Path Dependencies (Extension)

The `path-deps` extension auto-refreshes elements based on REST-ful path relationships.

```html
<table hx-get="/contacts/table"
       hx-trigger="path-deps"
       hx-ext="path-deps"
       path-deps="/contacts">
  ...
</table>
```

Any htmx request that mutates `/contacts` (or a sub-path) automatically triggers a refresh of this table.

### Recommendation

Start with **expanding the target**. Move to **server-triggered events** when you need decoupled updates. Use **OOB swaps** for targeted, server-controlled multi-updates. Use **path-deps** when your URLs follow consistent REST patterns.

---

## 8. View Transitions

The View Transition API provides smooth animated transitions between DOM states. htmx integrates with it natively.

### Enabling Transitions

Add `transition:true` to `hx-swap`:

```html
<button hx-get="/new-content"
        hx-swap="innerHTML transition:true"
        hx-target="#content">
  Load Content
</button>
```

### CSS Setup

```css
/* Define animations */
@keyframes fade-in {
  from { opacity: 0; }
}
@keyframes fade-out {
  to { opacity: 0; }
}
@keyframes slide-from-right {
  from { transform: translateX(30px); }
}

/* Apply to view transitions */
::view-transition-old(slide-it) {
  animation: 180ms cubic-bezier(0.4, 0, 0.2, 1) both fade-out;
}
::view-transition-new(slide-it) {
  animation: 180ms cubic-bezier(0.4, 0, 0.2, 1) both slide-from-right;
}

/* Bind to elements */
.transition-slide {
  view-transition-name: slide-it;
}
```

```html
<div class="transition-slide" id="content">
  <!-- Content swapped by htmx will animate -->
</div>
```

### Browser Support

Chrome 111+. Other browsers gracefully degrade -- the swap happens instantly without animation. No polyfill needed, no breakage.

---

## 9. No Build Step

htmx is distributed as a single JavaScript file (~3,500 lines unminified). There is no build step, no transpilation, no bundler.

### The Philosophy

- **Longevity.** Plain JavaScript runs unmodified for as long as browsers exist. ECMA guarantees backward compatibility. Build tools do not.
- **Direct debugging.** Browser errors link directly to source code. No source maps needed.
- **Minimal maintenance.** No TypeScript version upgrades, no bundler config drift, no dependency chain to audit.
- **Simplicity pressure.** A single file creates natural discipline against unnecessary complexity.

### What This Means for Your Project

htmx does not require you to adopt a build step either. You can include it with a `<script>` tag and write your application without a bundler, transpiler, or package manager. This is not a limitation -- it is a deliberate architectural choice aligned with progressive enhancement.

If your project already uses a build step for other reasons, htmx works fine within it. But it does not require one.

---

## 10. Dependency Management: Vendoring

### What Vendoring Means

Copy the htmx source file directly into your project's static files. Check it into version control.

### How to Vendor htmx

```bash
# Download htmx into your project
curl -o static/vendor/htmx-2.0.8.min.js \
  https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js
```

```html
<!-- Reference from your templates -->
<script src="/static/vendor/htmx-2.0.8.min.js"></script>
```

### Why Vendor Instead of CDN

| Approach | Pros | Cons |
|----------|------|------|
| **Vendored (local)** | Self-contained, no external dependency at build or runtime, auditable, works offline | Must manually update |
| **CDN** | Auto-updated (sometimes), no disk space | External runtime dependency, cache-busting issues, CDN outage = broken site |
| **npm** | Version management | Requires package manager, node_modules, often a build step |

### The Recommendation

**Vendor htmx.** It has zero runtime dependencies, making it ideal for vendoring. Download the file, put it in your static directory, reference it in a `<script>` tag, and check it into version control. Update by downloading the new version when you choose to upgrade.

This approach eliminates external dependencies from your build and deployment pipeline. Your application is fully self-contained.

---

## Summary: The htmx Mental Model

1. **The server is your application.** It owns the state, the logic, and the HTML rendering. The browser displays what the server sends.
2. **HTML is the API.** Endpoints return rendered HTML fragments, not JSON. The response *is* the interface.
3. **Behavior lives in the markup.** `hx-*` attributes declare what happens, keeping behavior local and visible.
4. **Specialize, don't generalize.** htmx endpoints serve your UI. Build each one for its specific purpose.
5. **Simplicity is the feature.** No client-side state management, no build step, no framework boilerplate. The cost is accepting the constraints of hypermedia.
6. **Be pragmatic.** Use islands of interactivity for what hypermedia cannot do. Use a full SPA framework if the whole application needs it. Match the tool to the problem.
