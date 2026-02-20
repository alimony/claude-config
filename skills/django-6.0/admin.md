# Django 6.0 Admin Site

The admin is Django's auto-generated interface for model CRUD. It is designed for internal/staff use, not as a public-facing frontend.

## Registration

```python
from django.contrib import admin
from myapp.models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    pass
```

## Change List Configuration

### Displaying columns

```python
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "pub_date", "word_count"]

    @admin.display(description="Words", ordering="body")
    def word_count(self, obj):
        return len(obj.body.split())
```

### Search, filtering, and editing

```python
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "pub_date"]
    list_display_links = ["title"]
    list_editable = ["status"]
    ordering = ["-pub_date"]
    list_per_page = 50
    list_select_related = ["author"]
    date_hierarchy = "pub_date"
    search_fields = ["title", "body", "author__name"]
    list_filter = [
        "status",
        "author__is_staff",
        ("author", admin.RelatedOnlyFieldListFilter),
        ("subtitle", admin.EmptyFieldListFilter),
    ]
```

## Form Configuration

```python
class ArticleAdmin(admin.ModelAdmin):
    fields = ["title", ("slug", "status"), "body"]

    fieldsets = [
        (None, {"fields": ["title", "slug", "body"]}),
        ("Publishing", {
            "classes": ["collapse"],
            "fields": ["status", "pub_date", "author"],
        }),
    ]

    exclude = ["internal_notes"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["author"]
    raw_id_fields = ["author"]
    filter_horizontal = ["tags"]
    prepopulated_fields = {"slug": ["title"]}
```

## Inlines

```python
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    min_num = 0
    max_num = 20
    fields = ["author", "body", "created_at"]
    readonly_fields = ["created_at"]

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
```

## Actions

```python
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    actions = ["make_published"]

    @admin.action(description="Publish selected articles", permissions=["change"])
    def make_published(self, request, queryset):
        count = queryset.update(status="published")
        self.message_user(request, f"{count} articles published.", messages.SUCCESS)
```

## Dynamic Configuration Methods

```python
class ArticleAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        if request.user.is_superuser:
            return ["title", "author", "status", "internal_score"]
        return ["title", "author", "status"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == "published":
            return ["title", "slug", "author"]
        return []

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(author=request.user)
        return qs
```

## Save / Delete Hooks

```python
class ArticleAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.modified_by = request.user
            instance.save()
        formset.save_m2m()

    def delete_queryset(self, request, queryset):
        queryset.update(is_deleted=True)
```

## Custom Admin Views

```python
from django.urls import path
from django.template.response import TemplateResponse

class ArticleAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("stats/", self.admin_site.admin_view(self.stats_view), name="article_stats"),
        ]
        return custom + urls  # Custom BEFORE default

    def stats_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Article Statistics",
        }
        return TemplateResponse(request, "admin/myapp/article/stats.html", context)
```

**Always** wrap custom views with `self.admin_site.admin_view()`. **Always** place custom URL patterns before `super().get_urls()`.

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Custom URL patterns not matching | Place custom patterns **before** `super().get_urls()` |
| `delete_selected` action skips model `delete()` | Override `delete_queryset()` |
| Huge dropdown for ForeignKey with millions of rows | Use `raw_id_fields` or `autocomplete_fields` |
| `list_editable` field not saving | Field must also be in `list_display` and not in `list_display_links` |
| `autocomplete_fields` returns 403 | The related ModelAdmin must define `search_fields` |
| N+1 queries on change list | Set `list_select_related` |
| Missing admin context in custom views | Include `**self.admin_site.each_context(request)` |

## Quick Reference: Key ModelAdmin Options

| Option | Purpose |
|--------|---------|
| `list_display` | Columns on change list |
| `list_filter` | Sidebar filters |
| `search_fields` | Enable search box |
| `ordering` | Default sort |
| `readonly_fields` | Non-editable display fields |
| `fieldsets` | Grouped form layout |
| `inlines` | Related object editing |
| `actions` | Bulk operations |
| `autocomplete_fields` | Select2 for FK/M2M |
| `raw_id_fields` | Raw input for FK/M2M |
| `prepopulated_fields` | Auto-fill slugs |
| `save_on_top` | Save buttons at top of form |
| `date_hierarchy` | Date-based navigation |
| `list_select_related` | Query optimization |
| `show_facets` | Filter count display |
