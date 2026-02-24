# Celery: Periodic Tasks
Based on Celery 5.6.2 documentation.

## Overview

**Celery Beat** is a scheduler that sends tasks at regular intervals. Workers then execute them. Only run **one beat instance** — multiples cause duplicate task execution.

---

## Defining Periodic Tasks

### Via beat_schedule (recommended)

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-every-night': {
        'task': 'myapp.tasks.cleanup',
        'schedule': crontab(hour=0, minute=0),
        'args': (),
    },
    'check-every-30-seconds': {
        'task': 'myapp.tasks.health_check',
        'schedule': 30.0,
        'args': ('https://example.com',),
    },
    'send-report-monday': {
        'task': 'myapp.tasks.send_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),
        'kwargs': {'report_type': 'weekly'},
        'options': {'queue': 'reports', 'expires': 3600},
    },
}
app.conf.timezone = 'UTC'
```

### Entry Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `task` | str | Yes | Registered task name |
| `schedule` | number/timedelta/crontab/solar | Yes | Execution frequency |
| `args` | tuple | No | Positional arguments |
| `kwargs` | dict | No | Keyword arguments |
| `options` | dict | No | apply_async options (queue, expires, etc.) |
| `relative` | bool | No | Round interval to nearest second/minute/hour |

### Via on_after_configure (dynamic)

```python
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, check.s('hello'), name='check every 10s')
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        report.s('Monday report'),
    )
```

> Use `on_after_finalize` if the task is defined in a different module than the app.

---

## Schedule Types

### Interval (seconds or timedelta)

```python
from datetime import timedelta

app.conf.beat_schedule = {
    'every-30-seconds': {
        'task': 'tasks.ping',
        'schedule': 30.0,
    },
    'every-5-minutes': {
        'task': 'tasks.sync',
        'schedule': timedelta(minutes=5),
    },
}
```

### Crontab

```python
from celery.schedules import crontab
```

| Pattern | Crontab |
|---------|---------|
| Every minute | `crontab()` |
| Daily at midnight | `crontab(minute=0, hour=0)` |
| Every 15 minutes | `crontab(minute='*/15')` |
| Every 3 hours | `crontab(minute=0, hour='*/3')` |
| Every Sunday | `crontab(day_of_week='sunday')` |
| Mon-Fri at 9am | `crontab(minute=0, hour=9, day_of_week='mon-fri')` |
| 1st of each month | `crontab(0, 0, day_of_month='1')` |
| Every quarter | `crontab(0, 0, day_of_month='1', month_of_year='1,4,7,10')` |
| Every even day | `crontab(0, 0, day_of_month='2-30/2')` |
| Thu/Fri 3am, 5pm, 10pm every 10 min | `crontab(minute='*/10', hour='3,17,22', day_of_week='thu,fri')` |

**Parameters:** `minute`, `hour`, `day_of_week` (0=Mon or name), `day_of_month`, `month_of_year`

### Solar

Execute at sunrise/sunset/dawn/dusk based on coordinates:

```python
from celery.schedules import solar

app.conf.beat_schedule = {
    'sunset-task': {
        'task': 'tasks.lights_on',
        'schedule': solar('sunset', -37.81, 144.96),  # Melbourne
    },
}
```

**Events:** `dawn_astronomical`, `dawn_nautical`, `dawn_civil`, `sunrise`, `solar_noon`, `sunset`, `dusk_civil`, `dusk_nautical`, `dusk_astronomical`

**Coordinates:** latitude (+N/-S), longitude (+E/-W)

---

## Running Beat

```bash
# Standalone (recommended for production)
celery -A proj beat -l INFO

# Embedded in worker (development only)
celery -A proj worker -B -l INFO

# Custom schedule file
celery -A proj beat -s /var/run/celery/beat-schedule

# With database scheduler
celery -A proj beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Database Scheduler (Django)

```bash
pip install django-celery-beat
```

```python
# settings.py
INSTALLED_APPS = [..., 'django_celery_beat']
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

```bash
python manage.py migrate
```

Manage schedules via Django admin or programmatically.

---

## Timezone

```python
app.conf.timezone = 'Europe/London'
```

Default is UTC. All internal times use UTC; beat converts when needed. With Django, uses `TIME_ZONE` unless explicitly overridden.

---

## Best Practices

- **One beat instance only** — use a process supervisor (systemd, supervisord) to ensure exactly one
- **Make periodic tasks idempotent** — missed runs may cause catch-up bursts
- **Set `expires`** on periodic tasks to prevent queue buildup if workers are down
- **Use `relative=True`** for intervals to align to clock boundaries
- **Use database scheduler** for dynamic schedules (add/remove via admin without restarts)

## Common Pitfalls

- **Multiple beat instances** — causes duplicate task execution. No built-in leader election
- **Task overlap** — if a task takes longer than its interval, the next run starts anyway. Use locking if serial execution is needed
- **Timezone confusion** — always set `timezone` explicitly; don't rely on system timezone
- **`on_after_configure` timing** — tasks defined in other modules may not be registered yet; use `on_after_finalize` instead
- **Trailing comma in args** — single-arg tuple needs `(16,)` not `(16)`
