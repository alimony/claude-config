# Django: Models & Fields

Based on Django 6.0 documentation.

## Core Concepts

Every Django model is a Python class subclassing `django.db.models.Model`. Each attribute is a database field. Each model maps to one database table. Django auto-adds a `BigAutoField` primary key unless you define one.

```python
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

---

## Field Types Quick Reference

### Strings

| Field | DB Type | Required Params | Notes |
|-------|---------|-----------------|-------|
| `CharField` | VARCHAR | `max_length` | For short strings. MySQL: max 255 with `unique=True`. |
| `TextField` | TEXT | — | Large text. Cannot index on MySQL/Oracle. |
| `SlugField` | VARCHAR | — | `max_length=50` default. Implies `db_index=True`. |
| `EmailField` | VARCHAR(254) | — | Validates email format. |
| `URLField` | VARCHAR(200) | — | Validates URL format. |

### Numbers

| Field | Range | Notes |
|-------|-------|-------|
| `IntegerField` | -2.1B to 2.1B | Standard integer. |
| `BigIntegerField` | -9.2E18 to 9.2E18 | 64-bit. |
| `SmallIntegerField` | -32,768 to 32,767 | |
| `PositiveIntegerField` | 0 to 2.1B | |
| `DecimalField` | Arbitrary precision | Requires `max_digits`, `decimal_places`. |
| `FloatField` | Python float | Not for money — use `DecimalField`. |

### Date/Time

| Field | Python Type | Key Options |
|-------|-------------|-------------|
| `DateField` | `datetime.date` | `auto_now`, `auto_now_add` |
| `DateTimeField` | `datetime.datetime` | `auto_now`, `auto_now_add` |
| `TimeField` | `datetime.time` | `auto_now`, `auto_now_add` |
| `DurationField` | `timedelta` | Stored as microseconds (except PostgreSQL). |

### Other

| Field | Notes |
|-------|-------|
| `BooleanField` | Default is `None` unless you set `default`. |
| `UUIDField` | Use `default=uuid.uuid4` (no parens). Native on PostgreSQL. |
| `JSONField` | Supported on all backends. SQLite requires JSON1 (default on 3.38+). |
| `FileField` | Requires `upload_to`. Needs `MEDIA_ROOT`/`MEDIA_URL` settings. |
| `ImageField` | Inherits `FileField`. Requires `pillow`. |
| `GeneratedField` | DB-computed column. Params: `expression`, `output_field`, `db_persist`. |
| `BinaryField` | Raw bytes. Not editable by default. |

---

## Common Field Options

```python
# The options you'll use most often
title = models.CharField(
    max_length=200,
    null=False,          # DB allows NULL? Default: False
    blank=False,         # Forms allow empty? Default: False
    default="Untitled",  # Python-side default (can be callable)
    db_default=Value("Untitled"),  # DB-side default (new)
    unique=True,         # Enforce uniqueness
    db_index=True,       # Create index (prefer Meta.indexes)
    choices=STATUS_CHOICES,
    help_text="The article title",
    verbose_name="headline",
    validators=[validate_no_profanity],
    editable=True,       # Show in forms? Default: True
    db_column="headline", # Custom DB column name
    db_comment="Article headline",
)
```

### null vs blank

| Scenario | `null` | `blank` | Notes |
|----------|--------|---------|-------|
| Required string field | `False` | `False` | Default. Empty = `""` not `NULL`. |
| Optional string field | `False` | `True` | Store `""` for empty, not `NULL`. |
| Optional non-string field | `True` | `True` | Dates, numbers, FKs need `NULL`. |
| Required non-string field | `False` | `False` | Default. |

**Do this:** `blank=True` for optional string fields.
**Don't do this:** `null=True` on `CharField`/`TextField` — you'll have two empty states (`""` and `NULL`).

### Choices with Enumerations (preferred pattern)

```python
class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"
        ARCHIVED = "AR", "Archived"

    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT,
    )

# Usage
article.status                      # "DF"
article.get_status_display()        # "Draft"
article.status == Article.Status.DRAFT  # True
```

Use `IntegerChoices` for integer fields. Use `Choices` subclass for other types.

---

## Relationships

### ForeignKey (Many-to-One)

```python
class Comment(models.Model):
    article = models.ForeignKey(
        Article,               # or "app.Article" for lazy reference
        on_delete=models.CASCADE,
        related_name="comments",  # article.comments.all()
    )
```

**`on_delete` options:**

| Option | Behavior |
|--------|----------|
| `CASCADE` | Delete child when parent deleted |
| `PROTECT` | Prevent parent deletion |
| `RESTRICT` | Like PROTECT but allows cascading through other paths |
| `SET_NULL` | Set to NULL (requires `null=True`) |
| `SET_DEFAULT` | Set to `default` value |
| `SET(callable)` | Set to return value of callable |
| `DO_NOTHING` | No action (risks `IntegrityError`) |

**Naming:** ForeignKey field name is singular (`article`, not `articles`).

### ManyToManyField

```python
class Article(models.Model):
    tags = models.ManyToManyField("Tag", related_name="articles")
```

**Naming:** ManyToManyField name is plural (`tags`, not `tag`).

**With extra fields on the relationship:**

```python
class Membership(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date_joined = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["person", "group"], name="unique_membership"),
        ]

class Group(models.Model):
    members = models.ManyToManyField(Person, through="Membership")
```

### OneToOneField

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
```

Same as `ForeignKey(unique=True)` but reverse side returns a single object, not a queryset.

---

## Model Meta Options

```python
class Article(models.Model):
    class Meta:
        # Table configuration
        db_table = "blog_articles"
        db_table_comment = "Published articles"

        # Ordering
        ordering = ["-pub_date", "title"]  # prefix "-" for descending

        # Display names
        verbose_name = "article"
        verbose_name_plural = "articles"

        # Indexes and constraints
        indexes = [
            models.Index(fields=["pub_date"], name="pub_date_idx"),
            models.Index(fields=["title", "-pub_date"], name="title_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(word_count__gte=0),
                name="positive_word_count",
            ),
            models.UniqueConstraint(
                fields=["slug", "pub_date"],
                name="unique_slug_per_date",
            ),
        ]

        # Permissions
        permissions = [("can_publish", "Can publish articles")]

        # Other
        get_latest_by = "-pub_date"
        default_related_name = "%(model_name)ss"  # supports placeholders
        managed = True   # False for existing tables/views
        abstract = False  # True for base classes
```

**`unique_together` is deprecated.** Use `UniqueConstraint` in `constraints` instead.

---

## Indexes

```python
from django.db.models import Index
from django.db.models.functions import Lower

class Meta:
    indexes = [
        # Basic index
        Index(fields=["last_name", "first_name"]),

        # Descending index
        Index(fields=["-pub_date"], name="recent_first_idx"),

        # Functional index
        Index(Lower("email"), name="lower_email_idx"),

        # Partial index (PostgreSQL, SQLite)
        Index(
            fields=["status"],
            condition=Q(status="active"),
            name="active_status_idx",
        ),

        # Covering index (PostgreSQL only)
        Index(
            fields=["slug"],
            include=["title", "pub_date"],
            name="slug_covering_idx",
        ),
    ]
```

**Gotcha:** `condition` and `include` are ignored on MySQL/MariaDB. Partial indexes not supported on Oracle.

Use `%(app_label)s_%(class)s_` prefix in `name` on abstract base classes to avoid collisions.

---

## Constraints

```python
from django.db.models import Q, UniqueConstraint, CheckConstraint

class Meta:
    constraints = [
        # Check constraint
        CheckConstraint(
            condition=Q(age__gte=18),
            name="age_gte_18",
        ),

        # Unique constraint (replaces unique_together)
        UniqueConstraint(
            fields=["room", "date"],
            name="unique_booking",
        ),

        # Conditional unique constraint
        UniqueConstraint(
            fields=["user"],
            condition=Q(status="draft"),
            name="one_draft_per_user",
        ),

        # Functional unique constraint
        UniqueConstraint(
            Lower("email"),
            name="unique_lower_email",
        ),
    ]
```

**Oracle gotcha:** Check constraints on nullable fields must include a NULL check:
```python
CheckConstraint(condition=Q(age__gte=18) | Q(age__isnull=True), name="age_gte_18")
```

---

## Model Inheritance

### Abstract Base Classes (recommended for shared fields)

```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # No table created

class Article(TimestampedModel):
    title = models.CharField(max_length=200)
    # Gets created_at and updated_at in its own table
```

Use `%(app_label)s_%(class)s_related` in `related_name` for abstract ForeignKey fields.

### Multi-Table Inheritance (each model gets its own table)

```python
class Place(models.Model):
    name = models.CharField(max_length=50)

class Restaurant(Place):
    serves_pizza = models.BooleanField(default=False)
    # Implicit OneToOneField to Place. Extra JOIN on every query.
```

**Gotcha:** Each query on `Restaurant` joins with `Place`. Prefer abstract base classes unless you need to query the parent independently.

### Proxy Models (same table, different behavior)

```python
class OrderedArticle(Article):
    class Meta:
        proxy = True
        ordering = ["-pub_date"]

    def is_recent(self):
        return self.pub_date >= timezone.now() - timedelta(days=7)
```

No new table. Adds methods or changes default ordering/manager.

---

## Composite Primary Keys (Django 5.2+)

```python
class OrderLineItem(models.Model):
    pk = models.CompositePrimaryKey("product_id", "order_id")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    quantity = models.IntegerField()
```

```python
item.pk  # (1, "A755H") — tuple
OrderLineItem.objects.filter(pk=(1, "A755H"))
```

**Limitations:**
- `ForeignKey` to composite PK models not supported — use `ForeignObject` (internal API).
- Cannot register in Django admin.
- `primary_key` attribute is `False` on individual fields — use `_meta.pk_fields`.
- No auto-migration to/from composite PKs after table creation.

---

## Essential Model Methods

```python
class Article(models.Model):
    def __str__(self):
        """Always define this. Used in admin, shell, debugging."""
        return self.title

    def get_absolute_url(self):
        """Used by admin 'View on site' and other conventions."""
        return f"/articles/{self.slug}/"

    def save(self, **kwargs):
        """Override with caution. Always call super()."""
        self.slug = slugify(self.title)
        super().save(**kwargs)

    def clean(self):
        """Model-level validation. Called by full_clean()."""
        if self.pub_date and self.pub_date > timezone.now():
            raise ValidationError("Publication date cannot be in the future.")
```

**Gotcha:** Overridden `save()` and `delete()` are NOT called by bulk operations (`QuerySet.update()`, `QuerySet.delete()`, `bulk_create()`). Use signals (`pre_save`, `post_save`, `pre_delete`, `post_delete`) if you need hooks on bulk operations.

**Gotcha:** Always use `**kwargs` in overridden `save()`/`delete()` signatures for forward compatibility.

---

## Model Exceptions

```python
try:
    article = Article.objects.get(pk=999)
except Article.DoesNotExist:
    pass  # Model-specific exception

try:
    article = Article.objects.get(status="draft")
except Article.MultipleObjectsReturned:
    pass  # More than one match
```

`NotUpdated` (new in Django 6.0): raised when a forced update affects zero rows.

---

## The _meta API

```python
# Get a field by name
Article._meta.get_field("title")       # <CharField: title>

# Get all fields
Article._meta.get_fields()             # Tuple of all fields + relations

# Primary key fields (useful for composite PKs)
Article._meta.pk_fields                # [<BigAutoField: id>]

# Model identity
Article._meta.label                    # "blog.Article"
Article._meta.db_table                 # "blog_article"
```

---

## Custom Model Fields

Override these methods when building a custom field:

| Method | Purpose |
|--------|---------|
| `db_type(connection)` | Return DB column type string |
| `from_db_value(value, expression, connection)` | DB value -> Python object |
| `to_python(value)` | Any value -> Python object (validation + deserialization) |
| `get_prep_value(value)` | Python object -> DB query value |
| `deconstruct()` | Serialize for migrations |

```python
class ColorField(models.Field):
    def db_type(self, connection):
        return "char(7)"

    def from_db_value(self, value, expression, connection):
        return value  # Already a string like "#ff0000"

    def to_python(self, value):
        if not value:
            return value
        if not value.startswith("#") or len(value) != 7:
            raise ValidationError("Invalid color format")
        return value

    def get_prep_value(self, value):
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
```

---

## Database-Specific Gotchas

| Issue | Database | Impact |
|-------|----------|--------|
| `CharField(unique=True)` max 255 chars | MySQL/MariaDB | Use `TextField` or shorten |
| `TextField` cannot be indexed | MySQL, Oracle | Cannot use `unique=True` or `db_index=True` |
| `DecimalField` stored as float | SQLite | No precise decimal arithmetic |
| Empty string stored as `NULL` | Oracle | Django converts back silently |
| `JSONField` needs JSON1 extension | SQLite < 3.38 | Must enable manually |
| `contains` lookup is case-insensitive | SQLite | `filter(name__contains="aa")` matches `"Aabb"` |
| Auto-increment sequences not updated on manual PK insert | PostgreSQL | Run `sqlsequencereset` |
| `LIKE` lookups case-insensitive by default | MySQL | Configure collation for case-sensitivity |

---

## Common Anti-Patterns

**Don't do this:**
```python
# Mutable default
data = models.JSONField(default={})    # Shared across instances!

# null on string field
name = models.CharField(null=True)     # Two empty states: "" and NULL

# Missing on_delete
author = models.ForeignKey(User)       # Won't work — on_delete required

# Overriding save without **kwargs
def save(self):                        # Breaks when Django adds params
    super().save()
```

**Do this instead:**
```python
data = models.JSONField(default=dict)  # Callable — new dict per instance

name = models.CharField(blank=True)    # Single empty state: ""

author = models.ForeignKey(User, on_delete=models.CASCADE)

def save(self, **kwargs):
    super().save(**kwargs)
```
