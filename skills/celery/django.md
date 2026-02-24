# Celery: Django Integration
Based on Celery 5.6.2 documentation.

## Project Structure

```
myproject/
    manage.py
    myproject/
        __init__.py
        settings.py
        urls.py
        celery.py       # Celery app definition
    myapp/
        tasks.py         # Auto-discovered by Celery
        models.py
```

---

## Setup

### 1. Create celery.py

```python
# myproject/myproject/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**What each line does:**
- `os.environ.setdefault(...)` — ensures Django settings available for `celery` CLI
- `Celery('myproject')` — creates the app instance
- `config_from_object(..., namespace='CELERY')` — reads settings prefixed with `CELERY_`
- `autodiscover_tasks()` — finds `tasks.py` in all `INSTALLED_APPS`

### 2. Import in __init__.py

```python
# myproject/myproject/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

This ensures the app loads when Django starts, enabling `@shared_task`.

### 3. Configure in settings.py

```python
# myproject/settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
```

**Naming convention:** lowercase Celery setting → uppercase with `CELERY_` prefix.
`task_serializer` → `CELERY_TASK_SERIALIZER`

---

## Defining Tasks

### @shared_task (recommended for Django apps)

```python
# myapp/tasks.py
from celery import shared_task

@shared_task
def add(x, y):
    return x + y

@shared_task
def send_welcome_email(user_id):
    user = User.objects.get(id=user_id)
    user.email_user('Welcome!', 'Thanks for signing up.')
```

Use `@shared_task` instead of `@app.task` — it works without importing the app instance, making apps reusable.

### @app.task (when you have the app)

```python
from myproject.celery import app

@app.task
def admin_task():
    ...
```

---

## Transaction Safety

### Problem

Task may execute before the database transaction commits:

```python
def create_user(request):
    user = User.objects.create(...)
    send_welcome_email.delay(user.pk)  # Worker might not find user yet!
```

### Solution: delay_on_commit (Celery 5.4+)

```python
def create_user(request):
    user = User.objects.create(...)
    send_welcome_email.delay_on_commit(user.pk)  # Sent after commit
```

### Pre-5.4 Alternative

```python
from django.db import transaction

def create_user(request):
    user = User.objects.create(...)
    transaction.on_commit(lambda: send_welcome_email.delay(user.pk))
```

---

## Result Backends

### Django ORM (django-celery-results)

```bash
pip install django-celery-results
```

```python
# settings.py
INSTALLED_APPS = [..., 'django_celery_results']
CELERY_RESULT_BACKEND = 'django-db'
```

```bash
python manage.py migrate django_celery_results
```

### Django Cache

```python
CELERY_RESULT_BACKEND = 'django-cache'
CELERY_CACHE_BACKEND = 'default'
```

---

## Database Scheduler (django-celery-beat)

```bash
pip install django-celery-beat
```

```python
# settings.py
INSTALLED_APPS = [..., 'django_celery_beat']
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

```bash
python manage.py migrate django_celery_beat
```

Manage periodic tasks via Django admin.

```bash
celery -A myproject beat -l INFO
```

---

## Running

```bash
# Worker
celery -A myproject worker -l INFO

# Beat (separate process)
celery -A myproject beat -l INFO

# Flower
celery -A myproject flower
```

---

## Common Patterns

### Calling from Views

```python
from django.http import JsonResponse
from .tasks import process_upload

def upload_view(request):
    file = request.FILES['file']
    saved = save_file(file)
    result = process_upload.delay_on_commit(saved.pk)
    return JsonResponse({'task_id': result.id})
```

### Checking Task Status

```python
from celery.result import AsyncResult

def task_status(request, task_id):
    result = AsyncResult(task_id)
    return JsonResponse({
        'state': result.state,
        'info': result.info,
    })
```

---

## Best Practices

- **Use `@shared_task`** for reusable app tasks, `@app.task` only in project-specific code
- **Use `delay_on_commit`** instead of `delay` to avoid race conditions with DB transactions
- **Pass model PKs, not objects** — re-fetch in the task for fresh data
- **Use `django-celery-results`** if you need to query task results from Django
- **Use `django-celery-beat`** for admin-managed periodic tasks

## Common Pitfalls

- **Circular imports** — don't import models at module level in celery.py; `autodiscover_tasks` handles it
- **Missing `__init__.py` import** — `@shared_task` won't work without the celery_app import in `__init__.py`
- **`DJANGO_SETTINGS_MODULE` not set** — worker can't find settings; ensure it's in celery.py
- **Task sent before transaction commits** — use `delay_on_commit` or `transaction.on_commit`
- **Settings namespace** — all Celery settings need `CELERY_` prefix when using `namespace='CELERY'`
