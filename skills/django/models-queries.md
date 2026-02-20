# Django: Models & Queries

Based on Django 6.0 documentation.

## Core Concepts

- **QuerySets are lazy.** No database hit until evaluated (iteration, slicing, `list()`, `bool()`, `len()`).
- **QuerySets are chainable.** Each `filter()`/`exclude()` returns a new QuerySet.
- **QuerySets cache results.** After first evaluation, subsequent access uses the cache (except slicing/indexing).
- **`get()` returns an object; `filter()` returns a QuerySet.** `get()` raises `DoesNotExist` or `MultipleObjectsReturned`.

---

## Quick Reference: Field Lookups

| Lookup | SQL Equivalent | Example |
|--------|---------------|---------|
| `exact` / `iexact` | `= / ILIKE` | `name__exact="Bob"` |
| `contains` / `icontains` | `LIKE '%x%'` | `title__icontains="django"` |
| `startswith` / `istartswith` | `LIKE 'x%'` | `name__startswith="A"` |
| `endswith` / `iendswith` | `LIKE '%x'` | `name__endswith="son"` |
| `in` | `IN (...)` | `id__in=[1, 2, 3]` |
| `gt` / `gte` / `lt` / `lte` | `> / >= / < / <=` | `price__gte=10` |
| `range` | `BETWEEN` | `date__range=(start, end)` |
| `isnull` | `IS NULL` | `author__isnull=True` |
| `regex` / `iregex` | `~ / ~*` | `name__regex=r"^(An|The)"` |
| `date` / `year` / `month` / `day` | Extract component | `created__year=2024` |

---

## CRUD Operations

### Create
```python
# Option 1: instantiate + save
obj = MyModel(field="value")
obj.save()

# Option 2: one-step create
obj = MyModel.objects.create(field="value")

# Bulk create (single query)
MyModel.objects.bulk_create([MyModel(field="a"), MyModel(field="b")])
```

### Read
```python
obj = MyModel.objects.get(pk=1)             # Single object
qs = MyModel.objects.filter(active=True)     # QuerySet
qs = MyModel.objects.exclude(status="draft") # Exclude
qs = MyModel.objects.all()[:10]              # LIMIT 10
```

### Update
```python
# Single object
obj.name = "New"
obj.save()

# Partial update (only touches specified columns)
obj.save(update_fields=["name"])

# Bulk update (SQL UPDATE, no save() or signals)
MyModel.objects.filter(old=True).update(old=False)

# Bulk update on instances
MyModel.objects.bulk_update(objects, ["field1", "field2"])
```

### Delete
```python
obj.delete()                                      # Single
MyModel.objects.filter(expired=True).delete()     # Bulk (cascades by default)
```

### Upsert Patterns
```python
obj, created = MyModel.objects.get_or_create(
    slug="unique-slug",
    defaults={"title": "New Entry"},
)

obj, created = MyModel.objects.update_or_create(
    slug="unique-slug",
    defaults={"title": "Updated Entry"},
)
```

---

## Filtering Patterns

### Q Objects — OR, NOT, XOR
```python
from django.db.models import Q

# OR
MyModel.objects.filter(Q(status="draft") | Q(status="review"))

# NOT
MyModel.objects.filter(~Q(status="archived"))

# Combined (Q objects must precede keyword args)
MyModel.objects.filter(Q(pub_date__year=2024) | Q(featured=True), active=True)
```

### F Expressions — Field-to-Field Comparison
```python
from django.db.models import F

# Compare fields
Entry.objects.filter(comments__gt=F("pingbacks"))

# Arithmetic
Entry.objects.filter(comments__gt=F("pingbacks") * 2)

# Date arithmetic
from datetime import timedelta
Entry.objects.filter(modified__gt=F("created") + timedelta(days=3))

# Atomic update (no race condition)
Entry.objects.update(views=F("views") + 1)
```

### Spanning Relationships
```python
# Forward (ForeignKey)
Entry.objects.filter(blog__name="Tech")

# Reverse
Blog.objects.filter(entry__headline__contains="Django")

# Multi-level
Blog.objects.filter(entry__authors__name="Alice")

# Use _id to avoid a join
entry.blog_id  # Already loaded, no extra query
```

### Multi-Valued Relationship Gotcha
```python
# Single filter() — conditions on SAME related object
Blog.objects.filter(entry__headline__contains="Lennon", entry__pub_date__year=2008)

# Chained filter() — conditions on ANY related object (potentially different)
Blog.objects.filter(entry__headline__contains="Lennon").filter(entry__pub_date__year=2008)
```

---

## Aggregation & Annotation

### aggregate() vs annotate()

| | `aggregate()` | `annotate()` |
|---|---|---|
| Returns | `dict` | QuerySet with extra attributes |
| Scope | Whole queryset | Per object |
| Terminal | Yes | No (chainable) |

```python
from django.db.models import Count, Sum, Avg, Max, Min

# Aggregate: single summary value
Book.objects.aggregate(avg_price=Avg("price"), total=Count("id"))
# {'avg_price': Decimal('34.35'), 'total': 2452}

# Annotate: per-object computed field
books = Book.objects.annotate(num_authors=Count("authors"))
books[0].num_authors  # 3
```

### Combining Multiple Aggregations — Use distinct=True
```python
# BUG: cross-join inflates counts
Book.objects.annotate(Count("authors"), Count("stores"))  # WRONG

# FIX:
Book.objects.annotate(Count("authors", distinct=True), Count("stores", distinct=True))
```

### Order Matters: filter() vs annotate()
```python
# filter THEN annotate — annotation only sees filtered rows
Publisher.objects.filter(book__rating__gt=3).annotate(num_books=Count("book"))

# annotate THEN filter — annotation sees ALL rows, filter constrains output
Publisher.objects.annotate(num_books=Count("book")).filter(num_books__gt=5)
```

### Conditional Aggregation
```python
from django.db.models import Count, Q

Client.objects.aggregate(
    gold=Count("pk", filter=Q(tier="gold")),
    silver=Count("pk", filter=Q(tier="silver")),
)
```

### Empty QuerySet Defaults
```python
Book.objects.aggregate(total=Sum("price", default=0))  # 0 instead of None
```

---

## Expressions & Conditional Logic

### Subquery and Exists
```python
from django.db.models import Subquery, OuterRef, Exists

# Subquery: correlated scalar subquery
newest = Comment.objects.filter(post=OuterRef("pk")).order_by("-created")
Post.objects.annotate(latest_comment=Subquery(newest.values("text")[:1]))

# Exists: boolean subquery (more efficient than count)
recent = Comment.objects.filter(post=OuterRef("pk"), created__gte=cutoff)
Post.objects.annotate(has_recent=Exists(recent))
Post.objects.filter(Exists(recent))       # as filter
Post.objects.filter(~Exists(recent))      # NOT EXISTS
```

### Case/When — Conditional Updates and Annotations
```python
from django.db.models import Case, When, Value, CharField

Client.objects.annotate(
    discount=Case(
        When(tier="gold", then=Value("10%")),
        When(tier="silver", then=Value("5%")),
        default=Value("0%"),
        output_field=CharField(),
    )
)

# Conditional bulk update
Client.objects.update(
    tier=Case(
        When(joined__lte=a_year_ago, then=Value("gold")),
        When(joined__lte=a_month_ago, then=Value("silver")),
        default=Value("bronze"),
    )
)
```

### ExpressionWrapper — Explicit Output Type
```python
from django.db.models import ExpressionWrapper, F, DateTimeField

Ticket.objects.annotate(
    expires=ExpressionWrapper(F("active_at") + F("duration"), output_field=DateTimeField())
)
```

### Window Functions
```python
from django.db.models import Window, F, Avg
from django.db.models.functions import RowNumber, Rank

Movie.objects.annotate(
    row=Window(expression=RowNumber(), order_by=F("title").asc()),
    avg_by_genre=Window(expression=Avg("rating"), partition_by=[F("genre")]),
)
```

---

## Key Database Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `Coalesce` | First non-null | `Coalesce("nickname", "name")` |
| `Greatest` / `Least` | Max/min of values | `Greatest("modified", "created")` |
| `Concat` | Join strings | `Concat("first", Value(" "), "last")` |
| `Upper` / `Lower` | Case conversion | `Upper("name")` |
| `Length` | String length | `Length("name")` |
| `Substr` | Substring | `Substr("name", 1, 3)` |
| `Replace` | String replace | `Replace("name", Value("old"), Value("new"))` |
| `Trim` | Strip whitespace | `Trim("name")` |
| `Now` | Current DB time | `filter(published__lte=Now())` |
| `Extract*` | Date parts | `ExtractYear("created")` |
| `Trunc*` | Truncate dates | `TruncMonth("created")` |
| `Cast` | Type conversion | `Cast("age", FloatField())` |

---

## Full-Text Search

### Basic Search
```python
# Simple containment (uses LIKE — not indexed)
Entry.objects.filter(body__icontains="cheese")

# PostgreSQL full-text search
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

Entry.objects.annotate(
    search=SearchVector("title", "body"),
).filter(search=SearchQuery("cheese"))
```

### Ranked Search (PostgreSQL)
```python
vector = SearchVector("title", weight="A") + SearchVector("body", weight="B")
query = SearchQuery("cheese")
Entry.objects.annotate(
    rank=SearchRank(vector, query)
).filter(rank__gte=0.3).order_by("-rank")
```

### Trigram Similarity (PostgreSQL)
```python
from django.contrib.postgres.search import TrigramSimilarity

Author.objects.annotate(
    similarity=TrigramSimilarity("name", "Hemmingway"),
).filter(similarity__gt=0.3).order_by("-similarity")
```

---

## Performance Optimization

### Avoid N+1 Queries
```python
# select_related: FK and OneToOne (SQL JOIN)
Entry.objects.select_related("blog", "blog__owner")

# prefetch_related: ManyToMany and reverse FK (separate queries)
Blog.objects.prefetch_related("entry_set", "entry_set__authors")

# Prefetch with custom queryset
from django.db.models import Prefetch
Blog.objects.prefetch_related(
    Prefetch("entry_set", queryset=Entry.objects.filter(active=True), to_attr="active_entries")
)
```

### Reduce Data Transfer
```python
Entry.objects.values("id", "headline")        # Dicts
Entry.objects.values_list("id", flat=True)     # Flat list
Entry.objects.only("id", "headline")           # Deferred other fields
Entry.objects.defer("body")                    # Defer heavy fields
```

### Use Efficient Checks
```python
# Do this:
if qs.exists(): ...           # SELECT 1 ... LIMIT 1
count = qs.count()            # SELECT COUNT(*)

# Not this:
if len(qs): ...               # Loads all objects
if qs: ...                    # Loads all objects
```

### Bulk Operations
```python
MyModel.objects.bulk_create(items, batch_size=1000)
MyModel.objects.bulk_update(items, ["field"], batch_size=1000)
Entry.objects.filter(...).update(status="published")  # Single SQL UPDATE
```

### Other Tips
```python
# Use iterator() for large result sets (avoids caching entire queryset)
for obj in MyModel.objects.iterator(chunk_size=2000):
    process(obj)

# Access FK id without join
entry.blog_id  # not entry.blog.id

# Clear unnecessary ordering
MyModel.objects.order_by()  # Removes default Meta.ordering

# Use explain() to inspect query plan
print(MyModel.objects.filter(...).explain())
```

---

## Related Object Managers

### Reverse FK and M2M Methods
```python
blog.entry_set.all()                    # All related
blog.entry_set.filter(active=True)      # Filtered
blog.entry_set.count()                  # Count

blog.entry_set.add(e1, e2)             # Associate
blog.entry_set.remove(e1)              # Disassociate (FK must be nullable)
blog.entry_set.clear()                 # Remove all
blog.entry_set.set([e1, e2])           # Replace all
blog.entry_set.create(title="New")     # Create and associate
```

### Custom related_name
```python
class Entry(models.Model):
    blog = models.ForeignKey(Blog, related_name="entries")

blog.entries.all()  # Instead of blog.entry_set.all()
```

---

## Custom Managers

### Preferred Pattern: QuerySet.as_manager()
```python
class EntryQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status="published")

    def by_author(self, user):
        return self.filter(author=user)

class Entry(models.Model):
    objects = EntryQuerySet.as_manager()

# Chainable: Entry.objects.published().by_author(user)
```

### Manager with Modified Base QuerySet
```python
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status="published")

class Entry(models.Model):
    objects = models.Manager()          # Default (all objects)
    published = PublishedManager()      # Filtered
```

**Warning:** Do not filter in base managers used for related-object access. Django needs unfiltered access for reverse relations.

---

## Transactions

### atomic() — Context Manager or Decorator
```python
from django.db import transaction

# As context manager
with transaction.atomic():
    obj.save()
    related.save()

# As decorator
@transaction.atomic
def transfer_funds(from_acc, to_acc, amount):
    from_acc.balance = F("balance") - amount
    from_acc.save()
    to_acc.balance = F("balance") + amount
    to_acc.save()
```

### Nested atomic() Creates Savepoints
```python
with transaction.atomic():          # Transaction
    operation_a()
    try:
        with transaction.atomic():  # Savepoint
            risky_operation()
    except IntegrityError:
        pass                        # Savepoint rolled back, transaction continues
    operation_b()                   # Still runs
```

**Critical:** Catch exceptions OUTSIDE the inner `atomic()` block.

### on_commit() — Post-Commit Side Effects
```python
from django.db import transaction

def send_notification(user_id):
    ...

with transaction.atomic():
    user = User.objects.create(...)
    transaction.on_commit(lambda: send_notification(user.id))
# Notification sent only after successful commit
```

---

## Raw SQL

### Manager.raw() — Returns Model Instances
```python
people = Person.objects.raw("SELECT * FROM app_person WHERE age > %s", [18])
for p in people:
    print(p.name)  # Full model instance
```

### cursor.execute() — Arbitrary SQL
```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM app_entry WHERE status = %s", ["published"])
    row = cursor.fetchone()
```

### SQL Injection Prevention
```python
# ALWAYS use parameterized queries
Person.objects.raw("SELECT * FROM t WHERE name = %s", [user_input])  # SAFE

# NEVER use string formatting
Person.objects.raw("SELECT * FROM t WHERE name = '%s'" % user_input)  # VULNERABLE
```

---

## Custom Lookups

```python
from django.db.models import Lookup

class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} <> {rhs}", [*lhs_params, *rhs_params]

from django.db.models import Field
Field.register_lookup(NotEqual)

# Usage: MyModel.objects.filter(status__ne="archived")
```

---

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Negative indexing | `qs[-1]` raises error | Use `qs.order_by("-pk").first()` |
| `update()` skips signals | No `save()` or `post_save` | Use loop + `save()` if signals needed |
| `delete()` cascades | Related objects deleted by default | Check `on_delete` on FK fields |
| Multiple aggregations | Cross-join inflates counts | Add `distinct=True` |
| filter/annotate order | Different results depending on order | Put `filter()` before `annotate()` to constrain |
| QuerySet re-evaluation | Slicing/indexing bypasses cache | Store in variable, iterate once |
| `get()` without index | Full table scan | Use `pk`, `unique`, or `db_index` fields |
| M2M filter semantics | Single vs chained `filter()` differ | Single = same object, chained = any object |
| F() after save() | Object field holds F expression, not value | Call `refresh_from_db()` |
| Deferred field access | Triggers extra query per field | Use `only()` / `defer()` deliberately |

---

## Model Instance Patterns

### Copying Instances
```python
obj.pk = None
obj._state.adding = True
obj.save()  # Creates new row; M2M relations must be re-set manually
```

### Refreshing from Database
```python
obj.refresh_from_db()                  # Reload all fields
obj.refresh_from_db(fields=["status"]) # Reload specific fields
```

### Display Choices
```python
obj.get_status_display()  # Auto-generated for fields with choices
```

---

## Multi-Database

```python
# Query specific database
MyModel.objects.using("replica").all()

# Save to specific database
obj.save(using="analytics_db")

# Database router (in settings: DATABASE_ROUTERS)
class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return "replica"
    def db_for_write(self, model, **hints):
        return "default"
```

**Limitation:** Foreign keys and M2M relations cannot span databases.

---

## Database Instrumentation

```python
from django.db import connection

class QueryLogger:
    def __init__(self):
        self.queries = []
    def __call__(self, execute, sql, params, many, context):
        start = time.monotonic()
        result = execute(sql, params, many, context)
        self.queries.append({"sql": sql, "duration": time.monotonic() - start})
        return result

logger = QueryLogger()
with connection.execute_wrapper(logger):
    do_queries()
print(logger.queries)
```
