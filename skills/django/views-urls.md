# Django 6.0: Views & URL Configuration

## Core Concepts

Django maps URLs to view functions via **URLconfs** -- Python modules containing a `urlpatterns` list. The request lifecycle: root URLconf is loaded, patterns are matched top-to-bottom, the first match calls the view, the view returns an `HttpResponse`.

---

## URL Configuration

### path() vs re_path()

Prefer `path()` for readability. Use `re_path()` only when you need regex.

```python
from django.urls import path, re_path
from . import views

urlpatterns = [
    # path() -- clean, typed captures
    path("articles/<int:year>/", views.year_archive, name="year-archive"),
    path("articles/<slug:title>/", views.article_detail, name="article-detail"),

    # re_path() -- when you need regex
    re_path(r"^articles/(?P<year>[0-9]{4})/$", views.year_archive),
]
```

### Built-in Path Converters

| Converter | Matches | Python type |
|-----------|---------|-------------|
| `str`     | Non-empty string, excluding `/` (default) | `str` |
| `int`     | Zero or positive integer | `int` |
| `slug`    | ASCII letters/numbers/hyphens/underscores | `str` |
| `uuid`    | Formatted UUID | `uuid.UUID` |
| `path`    | Non-empty string, including `/` | `str` |

### Custom Path Converters

```python
class FourDigitYearConverter:
    regex = r"[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%04d" % value

from django.urls import register_converter
register_converter(FourDigitYearConverter, "yyyy")

# Usage: path("articles/<yyyy:year>/", views.year_archive)
```

### Including Other URLconfs

```python
from django.urls import include, path

urlpatterns = [
    path("blog/", include("blog.urls")),
    path("api/", include([
        path("users/", views.user_list),
        path("users/<int:pk>/", views.user_detail),
    ])),
]
```

### URL Namespaces

Set `app_name` in the app's `urls.py` and use namespaced names everywhere:

```python
# polls/urls.py
app_name = "polls"
urlpatterns = [
    path("", views.index, name="index"),
    path("<int:pk>/", views.detail, name="detail"),
]

# Root urls.py
path("polls/", include("polls.urls"))

# Reverse: "polls:detail"
```

### Reversing URLs

```python
from django.urls import reverse, reverse_lazy

# In views
reverse("polls:detail", args=[42])
reverse("polls:detail", kwargs={"pk": 42})

# With query string and fragment (Django 5.2+)
reverse("search", query={"q": "django"}, fragment="results")

# For class attributes / decorators (evaluated before URLconf loads)
class MyView(RedirectView):
    url = reverse_lazy("home")
```

In templates:

```django
<a href="{% url 'polls:detail' poll.pk %}">View poll</a>
```

### Default View Arguments

```python
urlpatterns = [
    path("blog/", views.page),            # num defaults to 1
    path("blog/page<int:num>/", views.page),
]

def page(request, num=1):
    ...
```

### Error Handlers (root URLconf only)

```python
handler400 = "myapp.views.bad_request"
handler403 = "myapp.views.permission_denied"
handler404 = "myapp.views.page_not_found"
handler500 = "myapp.views.server_error"
```

---

## Views

### Function-Based Views

```python
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, "articles/detail.html", {"article": article})
```

### Async Views

```python
async def dashboard(request):
    data = await fetch_dashboard_data()
    return render(request, "dashboard.html", {"data": data})
```

---

## Shortcut Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `render(request, template, context)` | Render template | `HttpResponse` |
| `redirect(to, permanent=False)` | Redirect to URL/view/model | `HttpResponseRedirect` |
| `get_object_or_404(klass, **kwargs)` | Fetch or 404 | Model instance |
| `get_list_or_404(klass, **kwargs)` | Filter or 404 if empty | `list` |

### render()

```python
return render(request, "app/template.html", {
    "items": items,
}, status=200, content_type="text/html")
```

### redirect()

```python
# By view name
return redirect("article-detail", pk=article.pk)

# By model (calls get_absolute_url())
return redirect(article)

# By URL string
return redirect("/articles/")

# Permanent (301)
return redirect("home", permanent=True)

# Preserve HTTP method (307/308) -- Django 5.2+
return redirect("process", preserve_request=True)
```

### get_object_or_404()

```python
# With model class
article = get_object_or_404(Article, pk=pk)

# With queryset
article = get_object_or_404(Article.objects.filter(published=True), pk=pk)

# Async version
article = await aget_object_or_404(Article, pk=pk)
```

---

## HttpRequest Key Attributes

| Attribute | Description |
|-----------|-------------|
| `request.method` | `"GET"`, `"POST"`, etc. |
| `request.GET` | QueryDict of URL parameters |
| `request.POST` | QueryDict of form data |
| `request.FILES` | Uploaded files (requires `multipart/form-data`) |
| `request.body` | Raw request body as bytes |
| `request.headers` | Case-insensitive header dict |
| `request.META` | Server variables and HTTP headers |
| `request.user` | Current user (requires `AuthenticationMiddleware`) |
| `request.session` | Session dict (requires `SessionMiddleware`) |
| `request.path` | Path without query string |
| `request.content_type` | MIME type from `Content-Type` header |

Key methods:

```python
request.get_host()                    # "example.com:8000"
request.get_full_path()               # "/path/?key=value"
request.build_absolute_uri("/other/") # "https://example.com/other/"
request.is_secure()                   # True if HTTPS
request.accepts("application/json")   # Content negotiation
```

### QueryDict

Handles multiple values per key:

```python
q = QueryDict("color=red&color=blue")
q["color"]           # "blue" (last value)
q.getlist("color")   # ["red", "blue"]
```

---

## HttpResponse

```python
from django.http import HttpResponse, JsonResponse

# Basic
response = HttpResponse("Hello", content_type="text/plain", status=200)

# JSON
response = JsonResponse({"status": "ok"})
response = JsonResponse([1, 2, 3], safe=False)  # Non-dict requires safe=False

# Headers
response["X-Custom"] = "value"
response.set_cookie("key", "value", max_age=3600, httponly=True, secure=True)
```

### Response Subclasses

| Class | Status | Use case |
|-------|--------|----------|
| `HttpResponseRedirect` | 302 | Temporary redirect |
| `HttpResponsePermanentRedirect` | 301 | Permanent redirect |
| `HttpResponseNotFound` | 404 | Not found |
| `HttpResponseForbidden` | 403 | Forbidden |
| `HttpResponseBadRequest` | 400 | Bad request |
| `HttpResponseNotAllowed` | 405 | Method not allowed |
| `HttpResponseServerError` | 500 | Server error |
| `JsonResponse` | 200 | JSON data |

### Streaming & File Responses

```python
from django.http import StreamingHttpResponse, FileResponse

# Stream large data
def generate_csv():
    yield "Name,Email\n"
    for user in User.objects.iterator():
        yield f"{user.name},{user.email}\n"

response = StreamingHttpResponse(generate_csv(), content_type="text/csv")

# Serve files (sets Content-Length, Content-Type automatically)
response = FileResponse(open("report.pdf", "rb"), as_attachment=True, filename="report.pdf")
```

---

## View Decorators

```python
from django.views.decorators.http import require_http_methods, require_GET, require_POST, require_safe
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from django.views.decorators.common import no_append_slash

@require_http_methods(["GET", "POST"])
def my_view(request):
    ...

@require_safe          # GET and HEAD only (prefer over require_GET)
def read_only(request):
    ...

@never_cache
def dynamic_view(request):
    ...

@cache_control(max_age=3600, public=True)
def cached_view(request):
    ...

@no_append_slash       # Exclude from APPEND_SLASH behavior
def webhook(request):
    ...
```

---

## Middleware

### Writing Custom Middleware

```python
# Function-based
def timing_middleware(get_response):
    def middleware(request):
        import time
        start = time.monotonic()
        response = get_response(request)
        duration = time.monotonic() - start
        response["X-Request-Duration"] = f"{duration:.3f}s"
        return response
    return middleware

# Class-based
class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time
        start = time.monotonic()
        response = self.get_response(request)
        response["X-Request-Duration"] = f"{time.monotonic() - start:.3f}s"
        return response
```

### Middleware Hooks

```python
class FullMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Before view
        response = self.get_response(request)
        # After view
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Called before the view. Return None to continue or HttpResponse to short-circuit."""
        return None

    def process_exception(self, request, exception):
        """Called when view raises an exception. Return None or HttpResponse."""
        return None

    def process_template_response(self, request, response):
        """Called if response has a render() method (TemplateResponse)."""
        return response
```

### Recommended Middleware Order

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",        # 1. Security first
    "django.contrib.sessions.middleware.SessionMiddleware", # 2. Sessions
    "django.middleware.common.CommonMiddleware",            # 3. URL normalization
    "django.middleware.csrf.CsrfViewMiddleware",           # 4. CSRF before auth
    "django.contrib.auth.middleware.AuthenticationMiddleware", # 5. Auth (needs sessions)
    "django.contrib.messages.middleware.MessageMiddleware", # 6. Messages (needs sessions)
    "django.middleware.clickjacking.XFrameOptionsMiddleware", # 7. Clickjacking
]
```

### Sessions

```python
# Read/write like a dict
request.session["cart"] = [1, 2, 3]
cart = request.session.get("cart", [])
del request.session["cart"]
"cart" in request.session  # membership test

# Expiration
request.session.set_expiry(300)   # 5 minutes
request.session.set_expiry(0)     # Browser close

# Security
request.session.flush()           # Delete data + regenerate key
request.session.cycle_key()       # New key, keep data (prevents fixation)
```

### Gotcha: Nested Mutations Are Not Detected

```python
# WRONG -- Django does not detect this change
request.session["cart"]["items"].append(new_item)

# RIGHT -- signal the modification
request.session["cart"]["items"].append(new_item)
request.session.modified = True
```

---

## File Uploads

```python
def upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_upload(request.FILES["file"])
            return redirect("success")
    else:
        form = UploadForm()
    return render(request, "upload.html", {"form": form})

def handle_upload(f):
    with open(f"uploads/{f.name}", "wb+") as dest:
        for chunk in f.chunks():   # Don't use read() -- memory risk
            dest.write(chunk)
```

---

## Common Pitfalls

**URL matching is order-dependent.** The first matching pattern wins. Put specific patterns before general ones.

**Trailing slashes matter.** `path("articles/", ...)` does not match `/articles`. Use `APPEND_SLASH = True` (default) or be consistent.

**URLconf only matches the path.** Domain, query string, and HTTP method are not considered during URL resolution.

**Extra kwargs override captures.** If `path("blog/<int:id>/", view, {"id": 3})`, the extra kwarg `id=3` always wins.

**`require_safe` over `require_GET`.** `require_safe` also allows HEAD requests, which web crawlers and link checkers use.

**Session integer keys become strings.** The JSON serializer converts `request.session[0] = "x"` to `request.session["0"]` after save/load.

**Streaming responses have no `content` attribute.** Check `response.streaming` before accessing `response.content` in middleware.

---

## resolve() for URL Introspection

```python
from django.urls import resolve

match = resolve("/polls/42/")
match.url_name      # "detail"
match.namespace     # "polls"
match.view_name     # "polls:detail"
match.kwargs        # {"pk": 42}
match.func          # <function detail>
```
