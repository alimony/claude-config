# Django: Templates

Based on Django 6.0 documentation.

## Core Concepts

Django templates are text documents (usually HTML) with special syntax for dynamic content. The system has four primitives:

| Syntax | Purpose | Example |
|--------|---------|---------|
| `{{ variable }}` | Output a value | `{{ user.name }}` |
| `{% tag %}` | Logic and control flow | `{% if user.is_active %}` |
| `{{ var\|filter }}` | Transform a value | `{{ name\|lower }}` |
| `{# comment #}` | Template comment | `{# TODO: fix this #}` |

**Variable lookup order** for `{{ foo.bar }}`:
1. Dictionary lookup: `foo["bar"]`
2. Attribute/method lookup: `foo.bar`
3. List index lookup: `foo[bar]`

Callable attributes are auto-called if they take no arguments. Mark dangerous methods with `alters_data = True` to prevent template invocation.

---

## Configuration

```python
# settings.py
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Project-level template dirs
        "APP_DIRS": True,                   # Search app templates/ dirs
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
```

**Template search order**: `DIRS` directories first, then each app's `templates/` subdirectory in `INSTALLED_APPS` order.

---

## Template Inheritance

The most important pattern. Define a base skeleton; override specific blocks in children.

```django
{# base.html #}
<!DOCTYPE html>
<html>
<head><title>{% block title %}Default Title{% endblock %}</title></head>
<body>
  <nav>{% block nav %}...{% endblock %}</nav>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

```django
{# page.html #}
{% extends "base.html" %}

{% block title %}My Page{% endblock %}

{% block content %}
  <h1>Hello</h1>
  {{ block.super }}  {# Include parent block content #}
{% endblock content %}  {# Named endblock for readability #}
```

**Rules**:
- `{% extends %}` must be the first tag in the file
- Undefined blocks keep the parent's content
- Use `{{ block.super }}` to include (not replace) the parent block
- Three-level pattern is common: `base.html` -> `base_section.html` -> `page.html`

---

## Template Partials (New in Django 6.0)

Define reusable fragments within a template file.

```django
{# Define a partial #}
{% partialdef user-card %}
  <div class="card">
    <h3>{{ user.name }}</h3>
    <p>{{ user.bio }}</p>
  </div>
{% endpartialdef %}

{# Use it in the same template #}
{% for user in users %}
  {% partial user-card %}
{% endfor %}
```

**Inline partials** render at the definition site AND are reusable:
```django
{% partialdef user-card inline %}
  ...
{% endpartialdef %}
```

**Load a partial from another template** (for HTMX-style patterns):
```python
# In a view - render just the partial fragment
return render(request, "users.html#user-card", {"user": user})
```

```django
{# In a template #}
{% include "users.html#user-card" %}
```

---

## Built-in Tags -- Quick Reference

### Control Flow

```django
{% if user.is_authenticated %}
  Welcome, {{ user.username }}
{% elif user.is_anonymous %}
  Please log in
{% else %}
  Unknown state
{% endif %}

{% for item in items %}
  {{ forloop.counter }}. {{ item.name }}
{% empty %}
  No items found.
{% endfor %}
```

**forloop variables**: `counter`, `counter0`, `revcounter`, `revcounter0`, `first`, `last`, `length`, `parentloop`.

### Template Composition

```django
{% extends "base.html" %}
{% block content %}...{% endblock %}
{% include "snippet.html" %}
{% include "snippet.html" with title="Hello" only %}
```

### Common Tags

```django
{% csrf_token %}
{% url 'myapp:detail' obj.pk %}
{% url 'myapp:detail' obj.pk as detail_url %}
{% load static %}
{% static 'css/style.css' %}
{% with total=items|length %}
  {{ total }} items
{% endwith %}
{% verbatim %}{{ not interpreted }}{% endverbatim %}
{% cycle 'odd' 'even' %}
{% now "Y-m-d" %}
{% querystring page=2 color=None %}
{% spaceless %}<p> <a>link</a> </p>{% endspaceless %}
```

---

## Built-in Filters -- Quick Reference

### Text

| Filter | Example | Result |
|--------|---------|--------|
| `lower` | `{{ "HI"\|lower }}` | `hi` |
| `upper` | `{{ "hi"\|upper }}` | `HI` |
| `title` | `{{ "my post"\|title }}` | `My Post` |
| `capfirst` | `{{ "hello"\|capfirst }}` | `Hello` |
| `slugify` | `{{ "Hello World"\|slugify }}` | `hello-world` |
| `truncatechars:N` | `{{ text\|truncatechars:20 }}` | `"Hello world and ..."` |
| `truncatewords:N` | `{{ text\|truncatewords:3 }}` | `"Hello world and ..."` |
| `cut:" "` | `{{ "a b c"\|cut:" " }}` | `abc` |
| `striptags` | `{{ html\|striptags }}` | Plain text |
| `linebreaks` | `{{ text\|linebreaks }}` | `<p>` and `<br>` tags |
| `linebreaksbr` | `{{ text\|linebreaksbr }}` | `<br>` tags only |
| `wordcount` | `{{ text\|wordcount }}` | `4` |
| `pluralize` | `{{ count\|pluralize }}` | `s` or empty |

### Numbers and Dates

| Filter | Example | Result |
|--------|---------|--------|
| `add:N` | `{{ 4\|add:"2" }}` | `6` |
| `floatformat:N` | `{{ 3.14159\|floatformat:2 }}` | `3.14` |
| `filesizeformat` | `{{ bytes\|filesizeformat }}` | `117.7 MB` |
| `date:"FORMAT"` | `{{ dt\|date:"Y-m-d" }}` | `2026-02-19` |
| `time:"FORMAT"` | `{{ dt\|time:"H:i" }}` | `14:30` |
| `timesince` | `{{ past_date\|timesince }}` | `3 days, 2 hours` |
| `timeuntil` | `{{ future\|timeuntil }}` | `2 weeks` |

### Collections

| Filter | Example | Result |
|--------|---------|--------|
| `length` | `{{ list\|length }}` | `3` |
| `first` | `{{ list\|first }}` | First item |
| `last` | `{{ list\|last }}` | Last item |
| `join:", "` | `{{ list\|join:", " }}` | `a, b, c` |
| `slice:":2"` | `{{ list\|slice:":2" }}` | First 2 items |
| `dictsort:"key"` | `{{ dicts\|dictsort:"name" }}` | Sorted list |
| `random` | `{{ list\|random }}` | Random item |

### Safety and Escaping

| Filter | Purpose |
|--------|---------|
| `escape` | HTML-escape the value |
| `safe` | Mark as safe (skip auto-escaping) |
| `force_escape` | Immediate HTML escaping |
| `escapejs` | Escape for JS string literal |
| `json_script:"id"` | Output as JSON in a `<script>` tag |
| `urlencode` | URL-encode the value |

### Defaults

```django
{{ value|default:"nothing" }}
{{ value|default_if_none:"nothing" }}
{{ var1|yesno:"yes,no,maybe" }}
```

---

## Auto-Escaping

Django auto-escapes `<`, `>`, `&`, `'`, `"` in template variables by default.

```django
{# These are SAFE: #}
{{ user_input }}                    {# Auto-escaped #}

{# Disable per-variable (trusted content only): #}
{{ trusted_html|safe }}

{# Disable per-block: #}
{% autoescape off %}
  {{ trusted_content }}
{% endautoescape %}
```

**Do this**: Let auto-escaping protect you. Only use `|safe` on content you control.
**Don't do this**: `{% autoescape off %}` around user-generated content.

---

## Context Processors

Functions that inject variables into every template rendered with a `RequestContext`.

```python
# myapp/context_processors.py
def site_info(request):
    return {
        "site_name": "My Site",
        "current_year": 2026,
    }
```

Register in `TEMPLATES[0]["OPTIONS"]["context_processors"]`.

**Built-in context processors** and what they provide:

| Processor | Variables |
|-----------|-----------|
| `auth` | `user`, `perms` |
| `request` | `request` |
| `debug` | `debug`, `sql_queries` |
| `static` | `STATIC_URL` |
| `media` | `MEDIA_URL` |
| `csrf` | CSRF token (for `{% csrf_token %}`) |
| `messages` | `messages`, `DEFAULT_MESSAGE_LEVELS` |
| `i18n` | `LANGUAGES`, `LANGUAGE_CODE`, `LANGUAGE_BIDI` |
| `csp` | `csp_nonce` (new in 6.0) |

---

## Custom Filters

```python
# myapp/templatetags/myapp_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter(is_safe=True)
def add_suffix(value):
    return f"{value}px"
```

---

## Custom Tags

### simple_tag -- Most common

```python
@register.simple_tag
def setting_value(name):
    return getattr(settings, name, "")

@register.simple_tag(takes_context=True)
def user_greeting(context):
    user = context["request"].user
    return f"Hello, {user.username}"
```

### simple_block_tag -- Wraps content

```python
@register.simple_block_tag
def card(content, title=""):
    return format_html('<div class="card"><h3>{}</h3>{}</div>', title, content)
```

```django
{% card title="Info" %}
  <p>Card body with {{ variable }}</p>
{% endcard %}
```

### inclusion_tag -- Renders a sub-template

```python
@register.inclusion_tag("myapp/nav.html", takes_context=True)
def show_nav(context):
    return {"user": context["request"].user, "nav_items": NavItem.objects.all()}
```

### File layout for custom tags/filters

```
myapp/
    templatetags/
        __init__.py
        myapp_tags.py    # {% load myapp_tags %}
    templates/
        myapp/
            nav.html
```

Every tag module needs `register = template.Library()`. The app must be in `INSTALLED_APPS`. Restart the dev server after adding `templatetags/`.

---

## Common Pitfalls

1. **`{% load %}` does not inherit.** Every template that uses custom tags must `{% load %}` them.

2. **Forgetting `{% csrf_token %}`** in POST forms causes 403 errors.

3. **Calling methods with arguments.** Templates cannot pass arguments to methods. Compute in the view or write a custom filter/tag.

4. **`|safe` on user input.** Never mark user-provided content as safe.

5. **`{% include %}` performance.** Each `{% include %}` compiles and renders a separate template. In tight loops, consider partials or inclusion tags.

6. **Template resolution order surprises.** `INSTALLED_APPS` order determines which app's template wins when two apps have the same template path with `APP_DIRS=True`.

7. **`{% with %}` only scopes to its block.** The variable is not available outside `{% endwith %}`.

8. **`alters_data` on model methods.** If a model method has side effects (like `delete()`), set `method.alters_data = True` to prevent template invocation.

---

## Jinja2 Backend

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2_templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "myproject.jinja2.environment",
        },
    },
]
```

```python
# myproject/jinja2.py
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

def environment(**options):
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})
    return env
```

Key differences from DTL: Jinja2 supports function calls with arguments, has different filter syntax, and does not use context processors (use `env.globals` instead).
