# Celery: Tasks
Based on Celery 5.6.2 documentation.

## Defining Tasks

```python
@app.task
def add(x, y):
    return x + y

# For reusable apps (no app reference needed)
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
```

**Decorator order:** `@app.task` must be outermost:
```python
@app.task
@other_decorator
def my_task():
    pass
```

---

## Task Options Quick Reference

| Option | Default | Purpose |
|--------|---------|---------|
| `bind` | False | Pass task instance as `self` |
| `name` | auto | Custom task name |
| `max_retries` | 3 | Max retry count (None=infinite) |
| `default_retry_delay` | 180 | Seconds between retries |
| `rate_limit` | None | e.g. `'10/m'`, `'1/s'` |
| `time_limit` | None | Hard kill after N seconds |
| `soft_time_limit` | None | Raise `SoftTimeLimitExceeded` after N seconds |
| `acks_late` | False | Ack after execution (requires idempotent tasks) |
| `reject_on_worker_lost` | False | Requeue if worker dies (with `acks_late`) |
| `ignore_result` | False | Don't store result (better performance) |
| `store_errors_even_if_ignored` | False | Store errors even with `ignore_result` |
| `track_started` | False | Report STARTED state |
| `serializer` | None | Override task serializer |
| `throws` | () | Expected exceptions (logged as INFO) |
| `pydantic` | False | Use Pydantic for arg validation |

### Autoretry Options

| Option | Default | Purpose |
|--------|---------|---------|
| `autoretry_for` | () | Exception classes to auto-retry |
| `dont_autoretry_for` | () | Exceptions to exclude |
| `retry_backoff` | False | Exponential backoff (True or numeric factor) |
| `retry_backoff_max` | 600 | Max backoff in seconds |
| `retry_jitter` | True | Randomize backoff |
| `retry_kwargs` | {} | Extra args for retry() |

---

## Bound Tasks

Use `bind=True` to access the task instance (`self`):

```python
@app.task(bind=True)
def send_email(self, recipient):
    print(f'Task ID: {self.request.id}')
    print(f'Retries: {self.request.retries}')
    try:
        send(recipient)
    except SMTPError as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Task Request Attributes

| Attribute | Description |
|-----------|-------------|
| `self.request.id` | Task UUID |
| `self.request.args` | Positional arguments |
| `self.request.kwargs` | Keyword arguments |
| `self.request.retries` | Current retry count |
| `self.request.hostname` | Worker hostname |
| `self.request.delivery_info` | Queue/routing info |
| `self.request.root_id` | Workflow root task ID |
| `self.request.parent_id` | Parent task ID |
| `self.request.is_eager` | True if running locally |
| `self.request.eta` | Original ETA |
| `self.request.expires` | Expiration time |
| `self.request.timelimit` | (soft, hard) tuple |

---

## Retries

### Manual Retry

```python
@app.task(bind=True, max_retries=5, default_retry_delay=300)
def process_payment(self, order_id):
    try:
        charge(order_id)
    except PaymentGatewayError as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Automatic Retry with Backoff

```python
@app.task(
    autoretry_for=(RequestException, ConnectionError),
    dont_autoretry_for=(ValidationError,),
    retry_backoff=True,        # 1s, 2s, 4s, 8s...
    retry_backoff_max=600,     # Cap at 10 minutes
    retry_jitter=True,         # Randomize to prevent thundering herd
    max_retries=5,
)
def fetch_api(url):
    return requests.get(url, timeout=10).json()
```

---

## Task States

| State | Description |
|-------|-------------|
| `PENDING` | Unknown — task may not exist |
| `STARTED` | Executing (requires `track_started=True`) |
| `SUCCESS` | Completed successfully |
| `FAILURE` | Raised an exception |
| `RETRY` | Being retried |
| `REVOKED` | Cancelled |

### Custom States

```python
@app.task(bind=True)
def long_task(self, items):
    for i, item in enumerate(items):
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': len(items)})
        process(item)
    return {'status': 'complete'}
```

---

## Task Lifecycle Handlers

```python
class MyTask(Task):
    def before_start(self, task_id, args, kwargs):
        """Called before task starts."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful completion."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on exception."""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called on retry."""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Called after task returns (success or failure)."""

@app.task(base=MyTask)
def risky_operation(x):
    return do_something(x)
```

---

## Custom Task Classes

```python
class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = Database.connect()
        return self._db

@app.task(base=DatabaseTask)
def query(sql):
    return query.db.execute(sql)
```

Set as default for all tasks:
```python
app.Task = DatabaseTask
```

---

## Pydantic Validation

```python
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    email: str

@app.task(pydantic=True)
def create_user(user: UserInput):
    # user is auto-deserialized from dict to UserInput
    save(user.name, user.email)

# Call with dict — Pydantic validates and converts
create_user.delay({'name': 'Alice', 'email': 'alice@example.com'})
```

---

## Logging

```python
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@app.task
def process(data):
    logger.info('Processing %s', data)
```

## Hiding Sensitive Arguments

```python
result = charge_card.apply_async(
    ('account123', '4111111111111111'),
    argsrepr='(<account>, <card>)',
    kwargsrepr='{}'
)
```

---

## Best Practices

### 1. Make tasks idempotent (especially with acks_late)

```python
# BAD
@app.task
def increment(user_id):
    User.objects.filter(id=user_id).update(points=F('points') + 10)

# GOOD — check if already processed
@app.task
def increment(user_id, operation_id):
    if Operation.objects.filter(id=operation_id).exists():
        return  # Already done
    User.objects.filter(id=user_id).update(points=F('points') + 10)
    Operation.objects.create(id=operation_id)
```

### 2. Pass IDs, not objects

```python
# BAD — serialized object may be stale
@app.task
def process(article):
    article.publish()

# GOOD — fetch fresh data
@app.task
def process(article_id):
    article = Article.objects.get(id=article_id)
    article.publish()
```

### 3. Never block on subtasks

```python
# BAD — deadlocks worker pool
@app.task
def bad_workflow(data):
    result = subtask.delay(data).get()  # BLOCKS!

# GOOD — use chains
(subtask.s(data) | next_step.s()).delay()
```

### 4. Django transaction safety

```python
# Use delay_on_commit (Celery 5.4+)
def create_view(request):
    obj = MyModel.objects.create(...)
    process.delay_on_commit(obj.pk)

# Or manually with on_commit
from django.db import transaction
transaction.on_commit(lambda: process.delay(obj.pk))
```

### 5. Ignore results when not needed

```python
@app.task(ignore_result=True)
def fire_and_forget(data):
    log_event(data)
```

## Common Pitfalls

- **`PENDING` doesn't mean queued** — it means Celery has no info about the task
- **Forgetting `bind=True`** when using `self.retry()` or `self.request`
- **Mutable default args** — same as regular Python, avoid mutable defaults
- **Import errors silently swallowed** — check `celery inspect registered` to verify tasks loaded
- **Rate limits are per-worker** — `'10/m'` means 10/min per worker, not globally
- **`time_limit` kills the process** — use `soft_time_limit` for graceful handling
