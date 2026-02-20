# Django: Authentication

Based on Django 6.0 documentation.

## Core Concepts

Django auth handles **authentication** (who are you?) and **authorization** (what can you do?). The system provides: Users, Permissions, Groups, a pluggable password hashing system, built-in views/forms, and swappable authentication backends.

---

## User Management

```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.create_user("john", "john@example.com", "securepassword")
User.objects.create_superuser("admin", "admin@example.com", "adminpass")
```

**Never set `user.password` directly.** Use `set_password()`.

### Referencing the User Model

```python
# In models (ForeignKey/M2M) -- use settings string
from django.conf import settings
class Article(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

# In runtime code -- use get_user_model()
User = get_user_model()
```

**Do not** `from django.contrib.auth.models import User` -- this breaks with custom user models.

---

## Authentication & Sessions

```python
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    user = authenticate(request, username=request.POST["username"],
                        password=request.POST["password"])
    if user is not None:
        login(request, user)
        return redirect("home")

def logout_view(request):
    logout(request)
    return redirect("login")
```

### Session Invalidation on Password Change

```python
from django.contrib.auth import update_session_auth_hash

def change_password_view(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)  # Prevents logout
```

---

## Access Control

| Need | Function-Based View | Class-Based View |
|------|-------------------|-----------------|
| Must be logged in | `@login_required` | `LoginRequiredMixin` |
| Custom condition | `@user_passes_test(func)` | `UserPassesTestMixin` |
| Specific permission | `@permission_required("app.perm")` | `PermissionRequiredMixin` |

```python
from django.contrib.auth.decorators import login_required, permission_required

@login_required
def dashboard(request): ...

@permission_required("blog.add_post", raise_exception=True)
def create_post(request): ...
```

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class DashboardView(LoginRequiredMixin, View):
    login_url = "/login/"

class CreatePostView(PermissionRequiredMixin, CreateView):
    permission_required = "blog.add_post"
```

### Stacking Decorators -- Avoid Redirect Loops

```python
# WRONG
@login_required
@permission_required("polls.add_choice")
def my_view(request): ...

# RIGHT
@login_required
@permission_required("polls.add_choice", raise_exception=True)
def my_view(request): ...
```

---

## Permissions

Django auto-creates four permissions per model: `app.add_model`, `app.change_model`, `app.delete_model`, `app.view_model`.

```python
user.has_perm("app.close_task")
user.has_perms(["app.close_task", "app.reassign_task"])
```

### Permission Caching Gotcha

```python
user.has_perm("app.new_perm")     # False (caches)
user.user_permissions.add(perm)
user.has_perm("app.new_perm")     # Still False (cached!)

# Fix: re-fetch user from database
user = User.objects.get(pk=user.pk)
```

### Permissions in Templates

```django
{% if perms.blog.add_post %}
    <a href="{% url 'post_create' %}">New Post</a>
{% endif %}
```

---

## Password Management

### Hasher Priority

```python
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",    # Used for new passwords
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",    # Can verify existing
]
```

**Argon2 is recommended** for new projects (`pip install django[argon2]`).

### Password Validation

```python
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
```

---

## Built-in Views

```python
urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
]
# Provides: login, logout, password_change, password_change_done,
#           password_reset, password_reset_done, password_reset_confirm,
#           password_reset_complete
```

---

## Custom User Model

### AbstractUser (Simplest Custom Model)

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    bio = models.TextField(blank=True)

# settings.py
AUTH_USER_MODEL = "myapp.User"
```

**Do this before your first migration.**

### AbstractBaseUser (Full Control)

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    @property
    def is_staff(self):
        return self.is_admin
```

---

## Custom Authentication Backends

```python
from django.contrib.auth.backends import BaseBackend

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

```python
AUTHENTICATION_BACKENDS = [
    "myapp.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `user.password = "new"` | Use `user.set_password("new")` |
| `from django.contrib.auth.models import User` | Use `get_user_model()` or `settings.AUTH_USER_MODEL` |
| Permission check stale after `.add()` | Re-fetch user: `User.objects.get(pk=user.pk)` |
| Stacking `@login_required` + `@permission_required` | Add `raise_exception=True` to `@permission_required` |
| Multiple `UserPassesTestMixin` in MRO | Combine logic in one `test_func()` |
| Setting `AUTH_USER_MODEL` after first migration | Set it **before** first `migrate` |
| Forgetting `update_session_auth_hash` | User gets logged out after changing their own password |
