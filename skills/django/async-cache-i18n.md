# Django: Async, Caching, i18n, and Cross-Cutting Concerns

Based on Django 6.0 documentation.

## Async Support

### Async Views

```python
async def my_view(request):
    results = await MyModel.objects.filter(active=True).acount()
    return JsonResponse({"count": results})

class MyView(View):
    async def get(self, request):
        items = [item async for item in Item.objects.filter(active=True)]
        return JsonResponse({"items": len(items)})
```

### Async ORM

All queryset methods that trigger SQL have `a`-prefixed async variants:

```python
async for author in Author.objects.filter(name__startswith="A"):
    book = await author.books.afirst()

book = await Book.objects.acreate(title="New Book")
count = await Book.objects.acount()
exists = await Book.objects.filter(pk=1).aexists()
```

### Bridging Sync and Async

```python
from asgiref.sync import sync_to_async, async_to_sync

results = await sync_to_async(sync_db_function)(pk=123)
sync_result = async_to_sync(async_function)()
```

### Async Pitfalls

- Calling sync ORM from async context without `sync_to_async` raises `SynchronousOnlyOperation`
- Transactions do NOT work in async mode -- wrap with `sync_to_async`
- Disable persistent DB connections (`CONN_MAX_AGE`) in async

---

## Background Tasks (New in Django 6.0)

```python
from django.tasks import task

@task
def send_welcome_email(user_id, template_name):
    user = User.objects.get(pk=user_id)
    send_mail(subject="Welcome", message="...", from_email=None, recipient_list=[user.email])
    return 1

result = send_welcome_email.enqueue(user_id=42, template_name="welcome")
```

### Transaction Safety

```python
from functools import partial
from django.db import transaction

# RIGHT: enqueue after commit
with transaction.atomic():
    obj = MyModel.objects.create(name="test")
    transaction.on_commit(partial(my_task.enqueue, obj_id=obj.pk))
```

### Task Backends

| Backend | Use Case | Executes? |
|---------|----------|-----------|
| `ImmediateBackend` | Development | Yes, immediately |
| `DummyBackend` | Testing | No, stores for inspection |
| Third-party | Production | Yes, via worker process |

**Critical:** Task arguments must be JSON-serializable AND survive round-trip.

---

## Caching

### Configuration

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
        "TIMEOUT": 300,
        "KEY_PREFIX": "mysite",
    }
}
```

### Low-Level Cache API

```python
from django.core.cache import cache

cache.set("key", value, timeout=300)
cache.get("key", default=None)
cache.add("key", value)           # Only if key doesn't exist
cache.get_or_set("key", callable)
cache.delete("key")

# Batch operations
cache.set_many({"a": 1, "b": 2})
cache.get_many(["a", "b"])

# Atomic increment
cache.incr("counter")
cache.incr("counter", 10)
```

### Caching Layers

**Per-view:**
```python
from django.views.decorators.cache import cache_page, never_cache

@cache_page(60 * 15)
def my_view(request): ...
```

**Template fragments:**
```django
{% load cache %}
{% cache 500 sidebar request.user.username %}
    ... expensive content ...
{% endcache %}
```

### HTTP Cache Headers

```python
from django.views.decorators.cache import cache_control

@cache_control(max_age=3600, public=True)
def public_page(request): ...

@never_cache
def login_view(request): ...
```

---

## Internationalization (i18n)

### Settings

```python
USE_I18N = True
LANGUAGE_CODE = "en-us"
LANGUAGES = [("en", _("English")), ("de", _("German"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
```

### Translation in Python

```python
from django.utils.translation import gettext as _, gettext_lazy as _lazy

output = _("Welcome to our site.")  # Immediate

class Article(models.Model):
    title = models.CharField(verbose_name=_lazy("title"))  # Lazy
```

```python
# DO: named parameters
_("%(count)d items in %(category)s") % {"count": 5, "category": name}

# DON'T: f-strings
_(f"{count} items")  # BROKEN
```

### Pluralization

```python
from django.utils.translation import ngettext

msg = ngettext(
    "%(count)d item found.",
    "%(count)d items found.",
    count,
) % {"count": count}
```

### Templates

```django
{% load i18n %}
{% translate "Welcome" %}

{% blocktranslate with name=user.name count counter=items|length %}
    {{ name }} has {{ counter }} item.
{% plural %}
    {{ name }} has {{ counter }} items.
{% endblocktranslate %}
```

### URL Internationalization

```python
from django.conf.urls.i18n import i18n_patterns
urlpatterns += i18n_patterns(
    path(_("about/"), about_view, name="about"),
)
```

### Message Files

```bash
django-admin makemessages -l de
django-admin compilemessages
```

---

## Timezone Handling

### Core Rule: Store UTC, display local.

```python
USE_TZ = True
TIME_ZONE = "UTC"
```

```python
from django.utils import timezone

now = timezone.now()  # ALWAYS use this

# NEVER use:
import datetime
now = datetime.datetime.now()  # Naive
```

### Conversion

```python
timezone.activate(zoneinfo.ZoneInfo("America/New_York"))
timezone.localtime(aware_dt)
timezone.make_aware(naive_dt)
```

### Templates

```django
{% load tz %}
{% timezone "Europe/Paris" %}
    {{ event.start }}
{% endtimezone %}
```

---

## Pagination

```python
from django.core.paginator import Paginator

def listing(request):
    paginator = Paginator(Article.objects.all(), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "list.html", {"page_obj": page_obj})
```

```python
class ArticleList(ListView):
    model = Article
    paginate_by = 25
```

```django
{% for item in page_obj %}{{ item.title }}{% endfor %}
{% if page_obj.has_previous %}
    <a href="?page={{ page_obj.previous_page_number }}">Previous</a>
{% endif %}
Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
{% if page_obj.has_next %}
    <a href="?page={{ page_obj.next_page_number }}">Next</a>
{% endif %}
```

---

## Email

```python
from django.core.mail import send_mail, EmailMultiAlternatives

send_mail("Subject", "Body", "from@example.com", ["to@example.com"])

# HTML email
msg = EmailMultiAlternatives("Subject", text, "from@x.com", ["to@x.com"])
msg.attach_alternative(html, "text/html")
msg.send()
```

---

## Validators

```python
from django.core.exceptions import ValidationError

def validate_even(value):
    if value % 2 != 0:
        raise ValidationError("%(value)s is not even", params={"value": value})

class MyModel(models.Model):
    number = models.IntegerField(validators=[validate_even])
```

Validators run on `form.is_valid()` or `model.full_clean()`. They do NOT run on `model.save()`.

---

## Key Utilities

```python
from django.utils.text import slugify
slugify("Hello World!")  # "hello-world"

from django.utils.functional import cached_property

from django.utils.html import format_html
format_html("<a href='{}'>{}</a>", url, label)

from django.utils.decorators import method_decorator
@method_decorator(login_required, name="dispatch")
class MyView(View): ...
```

---

## Performance Checklist

1. `qs.count()` over `len(qs)`
2. `select_related` / `prefetch_related` for N+1
3. `CONN_MAX_AGE` for persistent DB connections (sync only)
4. Cache strategically at multiple layers
5. `cached_property` for expensive per-instance computations
6. Conditional responses with ETags and Last-Modified
7. `ManifestStaticFilesStorage` for browser caching
