# Django: Forms

Based on Django 6.0 documentation.

## Core Concepts

**Bound vs Unbound:** A form with data (`Form(request.POST)`) is bound; without data (`Form()`) is unbound. Only bound forms can be validated. Even an empty dict `Form({})` creates a bound form.

**Fields vs Widgets:** Fields handle validation and data conversion. Widgets handle HTML rendering. They are separate concerns -- a `CharField` can render as `TextInput` or `Textarea` depending on the widget.

**Validation Order:** Per field (in declaration order): `to_python()` -> `validate()` -> `run_validators()` -> `clean_<fieldname>()`. Then `Form.clean()` runs last for cross-field validation.

**cleaned_data:** After `is_valid()` returns `True`, access validated/converted data through `form.cleaned_data` (a dict). Never read raw values from `request.POST` after validation.

---

## Standard View Pattern

```python
from django.http import HttpResponseRedirect
from django.shortcuts import render

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            send_email(form.cleaned_data["email"])
            return HttpResponseRedirect("/success/")
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})
```

**Template:**
```django
<form method="post" {% if form.is_multipart %}enctype="multipart/form-data"{% endif %}>
    {% csrf_token %}
    {{ form.as_div }}
    <button type="submit">Send</button>
</form>
```

---

## Defining Forms

### Plain Form

```python
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
    priority = forms.ChoiceField(choices=[("low", "Low"), ("high", "High")])
    send_copy = forms.BooleanField(required=False)
```

### ModelForm

```python
from django.forms import ModelForm

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ["title", "body", "category"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 20}),
        }
        labels = {"title": "Article Title"}
        help_texts = {"category": "Select the primary category."}
        error_messages = {
            "title": {"required": "Every article needs a title."},
        }
```

| Do | Don't |
|----|-------|
| Use explicit `fields` list | Use `fields = "__all__"` on models with sensitive fields |
| Specify `widgets` in Meta for overrides | Manually recreate model fields on the form |
| Use `exclude` only when most fields are needed | Forget that new model fields auto-appear with `__all__` |

### ModelForm Save

```python
# Create
form = ArticleForm(request.POST)
if form.is_valid():
    article = form.save()

# Update
article = Article.objects.get(pk=1)
form = ArticleForm(request.POST, instance=article)
if form.is_valid():
    form.save()

# Deferred save (e.g., to set fields not on the form)
form = ArticleForm(request.POST)
if form.is_valid():
    article = form.save(commit=False)
    article.author = request.user
    article.save()
    form.save_m2m()  # required when commit=False with M2M fields
```

---

## Validation

### Field-Level: `clean_<fieldname>()`

```python
class SignupForm(forms.Form):
    username = forms.CharField(max_length=30)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username  # always return the value
```

### Cross-Field: `clean()`

```python
class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")
        if pw and confirm and pw != confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data
```

### Assigning Errors to Specific Fields from `clean()`

```python
def clean(self):
    cleaned_data = super().clean()
    if cleaned_data.get("start") and cleaned_data.get("end"):
        if cleaned_data["start"] > cleaned_data["end"]:
            self.add_error("end", "End date must be after start date.")
    return cleaned_data
```

### Raising ValidationError Properly

```python
from django.utils.translation import gettext_lazy as _

raise ValidationError(
    _("Invalid value: %(value)s"),
    code="invalid",
    params={"value": value},
)

# Multiple errors at once
raise ValidationError([
    ValidationError(_("Error one"), code="e1"),
    ValidationError(_("Error two"), code="e2"),
])

# Bad: string interpolation without params
raise ValidationError(f"Invalid: {value}")  # not translatable, no code
```

---

## Field Types Quick Reference

| Field | Normalizes To | Default Widget | Key Args |
|-------|--------------|----------------|----------|
| `CharField` | `str` | `TextInput` | `max_length`, `min_length`, `strip` |
| `EmailField` | `str` | `EmailInput` | `max_length` |
| `IntegerField` | `int` | `NumberInput` | `max_value`, `min_value`, `step_size` |
| `FloatField` | `float` | `NumberInput` | `max_value`, `min_value` |
| `DecimalField` | `Decimal` | `NumberInput` | `max_digits`, `decimal_places` |
| `BooleanField` | `bool` | `CheckboxInput` | -- |
| `DateField` | `date` | `DateInput` | `input_formats` |
| `DateTimeField` | `datetime` | `DateTimeInput` | `input_formats` |
| `ChoiceField` | `str` | `Select` | `choices` |
| `MultipleChoiceField` | `list[str]` | `SelectMultiple` | `choices` |
| `FileField` | `UploadedFile` | `ClearableFileInput` | `max_length`, `allow_empty_file` |
| `ImageField` | `UploadedFile` | `ClearableFileInput` | (requires Pillow) |
| `JSONField` | Python object | `Textarea` | `encoder`, `decoder` |
| `UUIDField` | `uuid.UUID` | `TextInput` | -- |
| `ModelChoiceField` | model instance | `Select` | `queryset`, `empty_label` |
| `ModelMultipleChoiceField` | `QuerySet` | `SelectMultiple` | `queryset` |

---

## Widgets

### Overriding Widgets

```python
class MyForm(forms.Form):
    bio = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "cols": 60}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bio"].widget.attrs.update({"class": "rich-editor"})
```

---

## Formsets

### Basic Formset

```python
from django.forms import formset_factory

ArticleFormSet = formset_factory(ArticleForm, extra=2, max_num=5)

if request.method == "POST":
    formset = ArticleFormSet(request.POST)
    if formset.is_valid():
        for form in formset:
            process(form.cleaned_data)
else:
    formset = ArticleFormSet()
```

**Template must include the management form:**
```django
<form method="post">
    {% csrf_token %}
    {{ formset.management_form }}
    {% for form in formset %}
        {{ form.as_div }}
    {% endfor %}
    <button type="submit">Save</button>
</form>
```

### Inline Formsets (Parent-Child)

```python
ChapterFormSet = inlineformset_factory(
    Book, Chapter,
    fields=["title", "number"],
    extra=1,
    can_delete=True,
)

book = Book.objects.get(pk=1)
if request.method == "POST":
    formset = ChapterFormSet(request.POST, instance=book)
    if formset.is_valid():
        formset.save()
else:
    formset = ChapterFormSet(instance=book)
```

---

## Template Rendering

### Rendering Methods

| Method | Output |
|--------|--------|
| `form.as_div()` | Fields in `<div>` elements (recommended) |
| `form.as_p()` | Fields in `<p>` elements |
| `form.as_ul()` | Fields as `<li>` elements |
| `form.as_table()` | Fields as `<tr>` elements |

### Manual Field Rendering

```django
{{ form.non_field_errors }}
{% for field in form %}
<div class="field {% if field.errors %}has-error{% endif %}">
    {{ field.label_tag }}
    {{ field }}
    {{ field.errors }}
    {% if field.help_text %}<p class="help">{{ field.help_text|safe }}</p>{% endif %}
</div>
{% endfor %}
```

### Form Prefixes (Multiple Forms on One Page)

```python
billing = AddressForm(request.POST, prefix="billing")
shipping = AddressForm(request.POST, prefix="shipping")
```

---

## Common Pitfalls

1. **Forgetting `return` in `clean_<fieldname>()`** -- must return the value or the field becomes `None`.
2. **Using `cleaned_data` before `is_valid()`** -- only safe after validation runs.
3. **Missing `form.save_m2m()`** -- required after `save(commit=False)` when M2M fields exist.
4. **Missing management form in formsets** -- `{{ formset.management_form }}` is mandatory.
5. **`BooleanField(required=True)`** means the value must be `True`, not just present.
6. **Empty dict creates a bound form** -- `Form({})` is bound and will validate (likely with errors).
7. **`fields = "__all__"` on ModelForm** -- new model fields auto-appear on the form. Prefer explicit field lists.
8. **File uploads need `request.FILES`** -- `Form(request.POST, request.FILES)` and `enctype="multipart/form-data"`.
9. **`add_error()` removes the field from `cleaned_data`** -- don't access it afterward.
