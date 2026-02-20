# Django 6.0 Class-Based Views

## Core Concepts

Class-based views (CBVs) replace conditional branching on `request.method` with separate methods (`get()`, `post()`, etc.) and enable code reuse through mixins and inheritance. Every CBV is deployed via `as_view()`, which returns a callable that creates a fresh instance per request (thread-safe by design).

**View lifecycle:** `as_view()` -> `setup()` -> `dispatch()` -> method handler (`get()`, `post()`, etc.)

### The View Hierarchy

| Layer | Classes | Purpose |
|-------|---------|---------|
| Base | `View`, `TemplateView`, `RedirectView` | Foundation: dispatch, template rendering, redirects |
| Display | `DetailView`, `ListView` | Single object and list display with pagination |
| Editing | `FormView`, `CreateView`, `UpdateView`, `DeleteView` | Form processing and model CRUD |
| Date-based | `ArchiveIndexView`, `YearArchiveView`, `MonthArchiveView`, `WeekArchiveView`, `DayArchiveView`, `TodayArchiveView`, `DateDetailView` | Date-filtered archives |
| Mixins | `ContextMixin`, `FormMixin`, `SingleObjectMixin`, `MultipleObjectMixin`, etc. | Composable building blocks |

---

## How-To Patterns

### Basic View with HTTP Method Dispatch

```python
from django.http import HttpResponse
from django.views import View

class MyView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Hello")

    def post(self, request, *args, **kwargs):
        return HttpResponse("Posted")
```

### Rendering a Template with Context

```python
from django.views.generic import TemplateView

class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_articles"] = Article.objects.all()[:5]
        return context
```

### Displaying a Single Object (DetailView)

```python
from django.views.generic import DetailView

class BookDetailView(DetailView):
    model = Book
    context_object_name = "book"
    template_name = "books/book_detail.html"

# urls.py
path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail")
path("books/<slug:slug>/", BookDetailView.as_view(), name="book-detail-slug")
```

### Displaying a List with Pagination (ListView)

```python
from django.views.generic import ListView

class BookListView(ListView):
    model = Book
    paginate_by = 25
    ordering = ["-publication_date"]
    context_object_name = "books"
```

Template context includes: `object_list`, `is_paginated`, `paginator`, `page_obj`.

### Dynamic Queryset Filtering

```python
class PublisherBookListView(ListView):
    template_name = "books/books_by_publisher.html"
    context_object_name = "books"

    def get_queryset(self):
        self.publisher = get_object_or_404(Publisher, slug=self.kwargs["slug"])
        return Book.objects.filter(publisher=self.publisher)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["publisher"] = self.publisher
        return context
```

### Creating and Updating Objects

```python
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

class AuthorCreateView(CreateView):
    model = Author
    fields = ["name", "email"]
    # success_url defaults to model.get_absolute_url()

class AuthorUpdateView(UpdateView):
    model = Author
    fields = ["name", "email"]
    template_name_suffix = "_update_form"

class AuthorDeleteView(DeleteView):
    model = Author
    success_url = reverse_lazy("author-list")
```

### Non-Model Form Handling (FormView)

```python
from django.views.generic.edit import FormView

class ContactFormView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = "/thanks/"

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)
```

### Setting the Current User on Create

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ["title", "body"]

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
```

### Redirects

```python
from django.views.generic.base import RedirectView

# Static redirect
path("old-page/", RedirectView.as_view(url="/new-page/"))

# Named URL redirect with side effects
class CounterRedirectView(RedirectView):
    permanent = False
    pattern_name = "article-detail"

    def get_redirect_url(self, *args, **kwargs):
        article = get_object_or_404(Article, pk=kwargs["pk"])
        article.update_counter()
        return super().get_redirect_url(*args, **kwargs)
```

---

## Decorating Class-Based Views

### In URLconf (per-instance)

```python
from django.contrib.auth.decorators import login_required
path("secret/", login_required(SecretView.as_view()))
```

### On the class (all instances)

```python
from django.utils.decorators import method_decorator

@method_decorator(login_required, name="dispatch")
class SecretView(TemplateView):
    template_name = "secret.html"

# Multiple decorators
@method_decorator([never_cache, login_required], name="dispatch")
class SecretView(TemplateView):
    template_name = "secret.html"
```

Prefer `LoginRequiredMixin` over decorator when possible:

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class SecretView(LoginRequiredMixin, TemplateView):
    template_name = "secret.html"
```

---

## Key Attributes Quick Reference

| Attribute | Used By | Purpose |
|-----------|---------|---------|
| `model` | All generic views | Model class to query |
| `queryset` | All generic views | Custom QuerySet (overrides `model`) |
| `template_name` | All template views | Explicit template path |
| `template_name_suffix` | All generic views | Suffix for auto-generated template name |
| `context_object_name` | Detail/List views | Template variable name for the object(s) |
| `paginate_by` | ListView | Items per page (enables pagination) |
| `ordering` | ListView | Sort order |
| `fields` | Create/UpdateView | Model fields to include in auto-generated form |
| `form_class` | FormView, Create/UpdateView | Explicit form class (cannot combine with `fields`) |
| `success_url` | Editing views | Redirect target after success |
| `pk_url_kwarg` | SingleObjectMixin | URL kwarg for primary key lookup (default: `"pk"`) |
| `slug_field` | SingleObjectMixin | Model field for slug lookup (default: `"slug"`) |
| `slug_url_kwarg` | SingleObjectMixin | URL kwarg for slug lookup (default: `"slug"`) |
| `allow_empty` | ListView, date views | Show page when no objects exist |
| `date_field` | Date-based views | Model field for date filtering |
| `allow_future` | Date-based views | Include future-dated objects |

## Key Methods Quick Reference

| Method | Purpose | Always Call Super? |
|--------|---------|-------------------|
| `get_queryset()` | Return the queryset to use | Yes, or return your own |
| `get_object()` | Return a single object | Yes, unless fully replacing |
| `get_context_data(**kwargs)` | Build template context | **Yes, always** |
| `get_form_class()` | Return the form class | Depends |
| `get_form_kwargs()` | Build form constructor kwargs | Yes |
| `form_valid(form)` | Handle valid form submission | Yes (it does redirect/save) |
| `form_invalid(form)` | Handle invalid form submission | Yes (it re-renders) |
| `get_success_url()` | Return redirect URL after success | Depends |
| `dispatch(request, ...)` | Route to method handler | Yes (for decoration) |

---

## Default Template Names

| View | Default Template | Suffix |
|------|-----------------|--------|
| `DetailView` | `<app>/<model>_detail.html` | `_detail` |
| `ListView` | `<app>/<model>_list.html` | `_list` |
| `CreateView` | `<app>/<model>_form.html` | `_form` |
| `UpdateView` | `<app>/<model>_form.html` | `_form` |
| `DeleteView` | `<app>/<model>_confirm_delete.html` | `_confirm_delete` |
| `ArchiveIndexView` | `<app>/<model>_archive.html` | `_archive` |

---

## Best Practices

1. **Use `reverse_lazy()` for `success_url` at class level.** `reverse()` runs at import time when URLs are not yet loaded.

2. **Define `get_absolute_url()` on models.** `CreateView` and `UpdateView` use it as the default success URL.

3. **Override `get_queryset()`, not `queryset` directly.** The `queryset` attribute is evaluated once at import time.

4. **Prefer `LoginRequiredMixin` over `@login_required` decorator** for cleaner CBV authentication.

5. **Keep mixins to one `View` ancestor.** Only one parent class should inherit from `View`. All other parents should be pure mixins.

6. **Don't mix detail, list, and editing generics carelessly.** Combining `SingleObjectMixin` with `MultipleObjectMixin` is error-prone due to MRO conflicts.

---

## Common Pitfalls

### Using `reverse()` instead of `reverse_lazy()` at class level

```python
# WRONG -- raises error at import time
class MyView(DeleteView):
    success_url = reverse("author-list")

# RIGHT
class MyView(DeleteView):
    success_url = reverse_lazy("author-list")
```

### Specifying both `fields` and `form_class`

```python
# WRONG -- raises ImproperlyConfigured
class AuthorCreateView(CreateView):
    model = Author
    fields = ["name"]
    form_class = AuthorForm

# RIGHT -- use one or the other
class AuthorCreateView(CreateView):
    model = Author
    fields = ["name"]
```

### Forgetting `super()` in `get_context_data()`

```python
# WRONG -- loses all parent context
def get_context_data(self, **kwargs):
    return {"my_data": 42}

# RIGHT
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["my_data"] = 42
    return context
```

### Mutating the class-level `queryset` attribute

```python
# WRONG -- queryset is shared across all requests
class MyView(ListView):
    queryset = Book.objects.all()

    def get_queryset(self):
        return self.queryset.filter(published=True)

# RIGHT -- return a new queryset
class MyView(ListView):
    model = Book

    def get_queryset(self):
        return super().get_queryset().filter(published=True)
```

### Mixing async and sync handlers

```python
# WRONG -- raises ImproperlyConfigured
class MyView(View):
    def get(self, request):
        return HttpResponse("sync")

    async def post(self, request):
        return HttpResponse("async")
```

---

## Date-Based Views Quick Reference

All date-based views require `model` (or `queryset`) and `date_field`. Future objects are excluded by default (`allow_future=False`).

```python
from django.views.generic.dates import ArchiveIndexView, MonthArchiveView

class ArticleArchiveView(ArchiveIndexView):
    model = Article
    date_field = "pub_date"

class ArticleMonthView(MonthArchiveView):
    queryset = Article.objects.all()
    date_field = "pub_date"
    month_format = "%m"
    allow_future = True
```
