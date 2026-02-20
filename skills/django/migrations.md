# Django 6.0 Migrations

## Core Concepts

Migrations are Django's version control for database schemas. They translate model changes into database operations, tracked as Python files in each app's `migrations/` directory.

**Key ideas:**
- Migrations are **declarative** -- they describe desired state, Django computes the diff
- Each migration has **dependencies** forming a directed acyclic graph (not a linear chain)
- Migrations produce **historical models** -- in-memory snapshots of models at each migration point
- Schema changes and data changes should live in **separate migrations**

## Essential Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `makemigrations` | Generate migration files from model changes | `manage.py makemigrations --name add_uuid_to_user myapp` |
| `migrate` | Apply (or unapply) migrations | `manage.py migrate myapp 0003` |
| `showmigrations` | List migrations and their applied status | `manage.py showmigrations` |
| `sqlmigrate` | Show SQL a migration will execute | `manage.py sqlmigrate myapp 0002` |
| `squashmigrations` | Collapse multiple migrations into one | `manage.py squashmigrations myapp 0001 0009` |
| `migrate --prune` | Remove stale entries from django_migrations table | `manage.py migrate --prune` |

### Reversing Migrations

```bash
# Roll back to migration 0002 (unapplies 0003+)
manage.py migrate myapp 0002

# Roll back ALL migrations for an app
manage.py migrate myapp zero
```

A migration is only reversible if every operation in it is reversible (e.g., `RunPython` needs `reverse_code`).

## Migration File Anatomy

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    # Required: which migrations must run first
    dependencies = [
        ("myapp", "0001_initial"),
        ("other_app", "0004_some_change"),
    ]

    # Optional: force this to run before another migration
    run_before = [
        ("third_party_app", "0001_initial"),
    ]

    # The operations to perform
    operations = [
        migrations.AddField(
            model_name="book",
            name="isbn",
            field=models.CharField(max_length=13, unique=True, null=True),
        ),
    ]

    # Set False to disable wrapping in a transaction (default: True)
    atomic = True

    # Mark as initial migration (affects --fake-initial behavior)
    initial = False
```

## Schema Operations Quick Reference

### Model Operations

```python
migrations.CreateModel(
    name="Book",
    fields=[
        ("id", models.BigAutoField(primary_key=True)),
        ("title", models.CharField(max_length=200)),
    ],
    options={"ordering": ["title"]},
)

migrations.DeleteModel("Book")

migrations.RenameModel(old_name="Book", new_name="Publication")

migrations.AlterModelTable(name="Book", table="library_books")
```

### Field Operations

```python
migrations.AddField(
    model_name="book",
    name="isbn",
    field=models.CharField(max_length=13, null=True),
)

migrations.RemoveField(model_name="book", name="isbn")

migrations.AlterField(
    model_name="book",
    name="isbn",
    field=models.CharField(max_length=13, unique=True),
)

migrations.RenameField(
    model_name="book",
    old_name="isbn",
    new_name="isbn_13",
)
```

### Index and Constraint Operations

```python
migrations.AddIndex(
    model_name="book",
    index=models.Index(fields=["title", "pub_date"], name="idx_title_pubdate"),
)
migrations.RemoveIndex(model_name="book", name="idx_title_pubdate")
migrations.RenameIndex(model_name="book", old_name="idx_old", new_name="idx_new")

migrations.AddConstraint(
    model_name="book",
    constraint=models.CheckConstraint(check=models.Q(price__gte=0), name="price_positive"),
)
migrations.RemoveConstraint(model_name="book", name="price_positive")
```

## Data Migrations with RunPython

```bash
# Generate an empty migration to write data operations in
manage.py makemigrations --empty myapp --name populate_slugs
```

```python
from django.db import migrations
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    Article = apps.get_model("myapp", "Article")  # historical model
    for article in Article.objects.all():
        article.slug = slugify(article.title)
        article.save(update_fields=["slug"])

def clear_slugs(apps, schema_editor):
    Article = apps.get_model("myapp", "Article")
    Article.objects.update(slug="")

class Migration(migrations.Migration):
    dependencies = [("myapp", "0003_article_slug")]
    operations = [
        migrations.RunPython(populate_slugs, clear_slugs),
    ]
```

### Critical: Always Use Historical Models

```python
# DO: get models from the apps registry
def forwards(apps, schema_editor):
    MyModel = apps.get_model("myapp", "MyModel")
    for obj in MyModel.objects.all():
        obj.save()

# DON'T: import models directly -- breaks when model changes later
from myapp.models import MyModel  # WRONG
```

Historical models have limitations:
- No custom `save()`, instance methods, or properties
- No custom managers unless `use_in_migrations = True`
- Only versioned `Meta` options available

### Use RunPython.noop for One-Way Data Migrations

```python
migrations.RunPython(forwards_func, migrations.RunPython.noop)
```

## Raw SQL with RunSQL

```python
migrations.RunSQL(
    sql="CREATE INDEX CONCURRENTLY idx_name ON myapp_book (title);",
    reverse_sql="DROP INDEX idx_name;",
)

# Parameterized SQL
migrations.RunSQL(
    sql=[("INSERT INTO myapp_config (key, value) VALUES (%s, %s);", ["site_name", "My Site"])],
    reverse_sql=[("DELETE FROM myapp_config WHERE key = %s;", ["site_name"])],
)

# RunSQL that also updates Django's internal state
migrations.RunSQL(
    sql="ALTER TABLE myapp_book ADD COLUMN rating int NOT NULL DEFAULT 0;",
    reverse_sql="ALTER TABLE myapp_book DROP COLUMN rating;",
    state_operations=[
        migrations.AddField("book", "rating", models.IntegerField(default=0)),
    ],
)
```

## Common Patterns

### Adding a Non-Nullable Unique Field to Existing Rows

This requires three migrations:

```python
# Migration 1: Add as nullable
migrations.AddField(
    model_name="mymodel",
    name="uuid",
    field=models.UUIDField(null=True),
)
```

```python
# Migration 2: Populate values
import uuid

def gen_uuid(apps, schema_editor):
    MyModel = apps.get_model("myapp", "MyModel")
    for row in MyModel.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=["uuid"])

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(gen_uuid, migrations.RunPython.noop),
    ]
```

```python
# Migration 3: Set NOT NULL + UNIQUE
migrations.AlterField(
    model_name="mymodel",
    name="uuid",
    field=models.UUIDField(default=uuid.uuid4, unique=True),
)
```

### Large Table Data Migration (Non-Atomic, Batched)

```python
import uuid
from django.db import migrations, transaction

def gen_uuid_batched(apps, schema_editor):
    MyModel = apps.get_model("myapp", "MyModel")
    while MyModel.objects.filter(uuid__isnull=True).exists():
        with transaction.atomic():
            for row in MyModel.objects.filter(uuid__isnull=True)[:1000]:
                row.uuid = uuid.uuid4()
                row.save(update_fields=["uuid"])

class Migration(migrations.Migration):
    atomic = False  # required for batched approach
    operations = [
        migrations.RunPython(gen_uuid_batched),
    ]
```

### Converting ManyToManyField to a Through Model

Use `SeparateDatabaseAndState` to rename the existing join table without losing data:

```python
migrations.SeparateDatabaseAndState(
    database_operations=[
        migrations.RunSQL(
            sql="ALTER TABLE myapp_book_authors RENAME TO myapp_authorbook",
            reverse_sql="ALTER TABLE myapp_authorbook RENAME TO myapp_book_authors",
        ),
    ],
    state_operations=[
        migrations.CreateModel(
            name="AuthorBook",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("author", models.ForeignKey(on_delete=models.DO_NOTHING, to="myapp.Author")),
                ("book", models.ForeignKey(on_delete=models.DO_NOTHING, to="myapp.Book")),
            ],
        ),
        migrations.AlterField(
            model_name="book",
            name="authors",
            field=models.ManyToManyField(to="myapp.Author", through="myapp.AuthorBook"),
        ),
    ],
)
```

## SeparateDatabaseAndState

Decouples what happens in the database from what Django thinks happened. Powerful but dangerous.

```python
migrations.SeparateDatabaseAndState(
    database_operations=[...],  # actual SQL/schema changes
    state_operations=[...],     # what Django records in its internal state
)
```

**When to use:** converting M2M to through model, renaming tables while preserving data, changing unmanaged to managed models.

**Verify correctness with:**
- `sqlmigrate` -- confirm the database operations produce correct SQL
- `makemigrations --dry-run` -- confirm state operations leave Django in sync

## Best Practices

- **Separate schema and data migrations.** Never mix `AddField`/`AlterField` with `RunPython` in the same migration.
- **Always provide `reverse_code`.** Use `RunPython.noop` if truly irreversible.
- **Name your migrations.** `makemigrations --name add_isbn_to_book` beats `0005_auto_20260219_1423`.
- **Commit migrations with the model changes** in the same commit.
- **Keep migrations small and focused.** One logical change per migration.
- **Test migrations on a copy of production data** before deploying.
- **Use `--fake-initial`** when adding migrations to an existing database.

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Importing models directly in `RunPython` | Always use `apps.get_model("app", "Model")` |
| Adding non-nullable field without default | Use the 3-step pattern: add nullable, populate, alter to non-null |
| Editing auto-generated migration files carelessly | Use `sqlmigrate` to verify changes before applying |
| Assuming DDL transactions work on MySQL | MySQL has no DDL transactions; failed migrations need manual cleanup |
| Running `RunPython` + schema ops in same migration | Use separate migrations |
| Calling custom model methods in `RunPython` | Historical models lack custom methods. Write logic inline. |
| Squashing without keeping old files during transition | Keep old files until all environments run the squashed version |
| Concurrent `makemigrations` on same app | Use `makemigrations --merge` |
| `SeparateDatabaseAndState` with wrong state ops | Always verify with `makemigrations --dry-run` |

## Database Backend Differences

| Feature | PostgreSQL | MySQL | SQLite |
|---------|-----------|-------|--------|
| DDL transactions | Yes | No | Yes |
| Schema alteration support | Full | Limited | Emulated (copy-table) |
| `CONCURRENTLY` index creation | Yes | No | No |
| Failed migration rollback | Automatic | Manual cleanup needed | Automatic |

## Custom Serialization

For custom field defaults or validators referenced in migrations:

```python
from django.utils.deconstruct import deconstructible

@deconstructible
class RangeValidator:
    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val

    def __call__(self, value):
        if not (self.min_val <= value <= self.max_val):
            raise ValidationError(f"Value must be between {self.min_val} and {self.max_val}")

    def __eq__(self, other):
        return (
            isinstance(other, RangeValidator)
            and self.min_val == other.min_val
            and self.max_val == other.max_val
        )
```

The class must be importable at module level and must implement `__eq__` so Django can detect when defaults change.

## Manager Serialization

```python
class PublishedManager(models.Manager):
    use_in_migrations = True  # required

class Article(models.Model):
    objects = models.Manager()
    published = PublishedManager()
```

Without `use_in_migrations = True`, the manager won't be available in historical models.
