# Django 6.0 -- Settings & Management

## Settings Fundamentals

```python
# Access settings in code
from django.conf import settings
if settings.DEBUG: ...

# Don't do this:
from django.conf.settings import DEBUG  # settings is an object, not a module
settings.DEBUG = True                   # never mutate at runtime
```

### Critical Settings

| Setting | Default | Notes |
|---------|---------|-------|
| `SECRET_KEY` | `''` | Required. Keep it secret. |
| `DEBUG` | `False` | Never `True` in production. |
| `ALLOWED_HOSTS` | `[]` | Required when `DEBUG=False`. |

```python
# Production
DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = ["www.example.com"]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

Run `python manage.py check --deploy` to audit security settings.

---

## Application Configuration (AppConfig)

```python
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "myapp"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # import signal handlers here
```

### App Loading Order

1. **Import app packages** -- `AppConfig` classes loaded. Do NOT import models yet.
2. **Import models** -- ORM APIs become usable.
3. **Call `ready()`** -- Safe for signal registration and initialization.

---

## Logging

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "INFO"},
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "mail_admins"], "level": "INFO"},
        "myapp": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
```

```python
import logging
logger = logging.getLogger(__name__)

logger.info("User %s logged in", user.pk)  # Do: lazy formatting
logger.info(f"User {user.pk} logged in")   # Don't: eager formatting
```

### Key Django Loggers

| Logger | What it captures |
|--------|-----------------|
| `django.request` | 5XX as ERROR, 4XX as WARNING |
| `django.db.backends` | SQL queries (only when `DEBUG=True`) |
| `django.security.*` | CSRF failures, `SuspiciousOperation` |

---

## Signals

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    def ready(self):
        from django.db.models.signals import post_save
        from . import handlers
        post_save.connect(handlers.on_user_save, sender="auth.User")
```

```python
# myapp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender="auth.User")
def on_user_save(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
```

Prevent duplicate connections:
```python
post_save.connect(my_handler, dispatch_uid="unique_string_id")
```

---

## System Check Framework

```bash
python manage.py check
python manage.py check --deploy
python manage.py check --tag security
```

### Writing a Custom Check

```python
from django.core.checks import Warning, register, Tags

@register(Tags.security, deploy=True)
def check_api_key_configured(app_configs, **kwargs):
    from django.conf import settings
    errors = []
    if not getattr(settings, "MY_API_KEY", None):
        errors.append(Warning("MY_API_KEY is not set.", id="myapp.W001"))
    return errors
```

---

## Custom Management Commands

```
myapp/management/commands/mycommand.py
```

```python
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Description of what this command does"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        name = options["name"]
        if options["dry_run"]:
            self.stdout.write(f"Would process {name}")
            return
        self.stdout.write(self.style.SUCCESS(f"Processed {name}"))
```

```python
from django.core.management import call_command
call_command("migrate", verbosity=0)
```

---

## Error Reporting

```python
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters

@sensitive_variables("password", "credit_card")
def process_payment(user, password, credit_card): ...

@sensitive_post_parameters("password", "ssn")
def register(request): ...
```

Django auto-hides settings containing: `API`, `KEY`, `PASS`, `SECRET`, `SIGNATURE`, `TOKEN`.

---

## Environment-Based Settings Pattern

```python
# settings/base.py -- shared settings
# settings/development.py
from .base import *
DEBUG = True

# settings/production.py
from .base import *
DEBUG = False
SECURE_HSTS_SECONDS = 31536000
```

Set via: `DJANGO_SETTINGS_MODULE=mysite.settings.production`
