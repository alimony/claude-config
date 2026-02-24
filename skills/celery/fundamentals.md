# Celery: Fundamentals
Based on Celery 5.6.2 documentation.

## What is Celery?

A distributed task queue that processes work asynchronously across workers and machines. Clients submit tasks as messages to a broker, workers consume and execute them.

| Component | Role |
|-----------|------|
| **Broker** | Message transport (RabbitMQ, Redis, SQS, Kafka) |
| **Worker** | Process that executes tasks |
| **Result Backend** | Stores task return values (Redis, RPC, database, etc.) |
| **Beat** | Scheduler for periodic tasks |

---

## Creating the App

```python
from celery import Celery

app = Celery('proj',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/1',
             include=['proj.tasks'])

app.conf.update(
    result_expires=3600,
)
```

**Arguments:**
- First arg = main module name (used to auto-generate task names)
- `broker` = message transport URL
- `backend` = result storage URL
- `include` = modules to import on worker startup

### Project Layout

```
src/
    proj/
        __init__.py
        celery.py      # App definition
        tasks.py       # Task definitions
```

### Configuration Methods

```python
# Direct
app.conf.timezone = 'Europe/London'
app.conf.update(enable_utc=True, timezone='Europe/London')

# From module (resets prior config)
app.config_from_object('celeryconfig')

# From class
class Config:
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True

app.config_from_object(Config)
# Or: app.config_from_object('proj.config:Config')

# From environment variable
import os
os.environ.setdefault('CELERY_CONFIG_MODULE', 'celeryconfig')
app.config_from_envvar('CELERY_CONFIG_MODULE')
```

---

## Defining Tasks

```python
from .celery import app

@app.task
def add(x, y):
    return x + y

@app.task
def mul(x, y):
    return x * y
```

### shared_task (for reusable apps)

```python
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
```

Use `@shared_task` when you don't have a reference to the app instance (e.g., in Django reusable apps). Use `@app.task` when you have the app.

---

## Running the Worker

```bash
# Basic
celery -A proj worker --loglevel=INFO

# With concurrency and queue
celery -A proj worker -l INFO -c 4 -Q default,priority
```

### Background / Multi-worker

```bash
# Start
celery multi start w1 -A proj -l INFO \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log

# Restart
celery multi restart w1 -A proj -l INFO

# Graceful stop (waits for current tasks)
celery multi stopwait w1 -A proj -l INFO

# Multiple workers with queue routing
celery multi start 10 -A proj -l INFO \
    -Q:1-3 images,video -Q:4,5 data -Q default
```

---

## Calling Tasks

### Three Ways to Call

```python
# 1. delay() — shortcut, most common
result = add.delay(4, 4)

# 2. apply_async() — full control over execution options
result = add.apply_async((4, 4), countdown=10, queue='lopri')

# 3. Direct call — runs synchronously in current process (no worker)
result = add(4, 4)  # Returns 8 immediately
```

### Working with Results

```python
result = add.delay(4, 4)

result.id              # Task UUID
result.ready()         # True if finished
result.successful()    # True if succeeded
result.failed()        # True if failed
result.state           # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY'

result.get(timeout=10)              # Block until result (raises on error)
result.get(propagate=False)         # Returns exception instead of raising
result.traceback                    # Traceback string on failure
```

**State progression:**
```
PENDING → STARTED → SUCCESS
PENDING → STARTED → RETRY → STARTED → SUCCESS
PENDING → STARTED → FAILURE
```

> **Note:** `PENDING` means "unknown" — the task may not exist at all. Celery doesn't store state until the task starts.

---

## Signatures & Partials

Signatures wrap a task call (name + args + options) into an object that can be passed around, serialized, or combined into workflows.

```python
# Full signature
sig = add.s(2, 2)
sig.delay()           # Executes add(2, 2)

# Partial signature (incomplete args)
sig = add.s(2)        # Missing one arg
sig.delay(8)          # Executes add(8, 2)

# With options
sig = add.signature((2, 2), countdown=10)
```

---

## Canvas: Workflow Primitives

### chain — Sequential execution

```python
from celery import chain

# (4 + 4) * 8 = 64
chain(add.s(4, 4) | mul.s(8))().get()

# Pipe syntax (equivalent)
(add.s(4, 4) | mul.s(8))().get()
```

### group — Parallel execution

```python
from celery import group

# Run 10 tasks in parallel
result = group(add.s(i, i) for i in range(10))()
result.get()  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

### chord — Group then callback

```python
from celery import chord

# Run group, then sum results
chord((add.s(i, i) for i in range(10)), xsum.s())().get()  # 90

# Equivalent pipe syntax
(group(add.s(i, i) for i in range(10)) | xsum.s())().get()
```

---

## Custom Base Task Classes

```python
from celery import Task

class DebugTask(Task):
    def __call__(self, *args, **kwargs):
        print(f'TASK STARTING: {self.name}[{self.request.id}]')
        return self.run(*args, **kwargs)

@app.task(base=DebugTask)
def add(x, y):
    return x + y

# Or set app-wide default
app.Task = DebugTask
```

> **Important:** Override `__call__`, call `self.run()` — never `super().__call__()`.

---

## Remote Control

```bash
# Inspect (read-only)
celery -A proj inspect active              # Current tasks
celery -A proj inspect reserved            # Prefetched tasks
celery -A proj inspect scheduled           # ETA/countdown tasks
celery -A proj status                      # Online workers

# Control (modify state)
celery -A proj control enable_events       # Enable monitoring
celery -A proj events --dump               # View event stream
celery -A proj events                      # Curses monitor
```

---

## Best Practices

- **Always specify the app name** to avoid `__main__` in task names
- **Use `config_from_object`** with a dedicated config module rather than inline config
- **Set `result_expires`** to avoid unbounded result backend growth
- **Use `shared_task`** for reusable/library code, `@app.task` for project-specific tasks
- **Don't import the app in task modules** — use relative imports from your celery.py
- **Avoid `current_app`** — pass the app explicitly (dependency injection)

## Common Pitfalls

- **Forgetting the result backend:** Without one, you can't call `.get()` on results
- **Task name conflicts:** If main module name isn't set, tasks may be named `__main__.add`
- **Stale workers:** Old workers running different code. Always restart after code changes
- **Blocking `.get()` in a task:** Never call `result.get()` inside a task — it can deadlock the worker pool. Use canvas primitives (chains, chords) instead
- **`PENDING` doesn't mean queued:** It means Celery has no information about the task. The task ID may not exist
