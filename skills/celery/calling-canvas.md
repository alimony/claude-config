# Celery: Calling Tasks & Canvas Workflows
Based on Celery 5.6.2 documentation.

## Calling Tasks

### Three Ways to Call

```python
# 1. delay() — shortcut, most common
add.delay(4, 4)

# 2. apply_async() — full control
add.apply_async((4, 4), countdown=10, queue='priority')

# 3. Direct call — synchronous, no worker involved
add(4, 4)
```

### apply_async Options

| Option | Type | Purpose |
|--------|------|---------|
| `countdown` | int | Delay execution by N seconds |
| `eta` | datetime | Execute at specific time (UTC) |
| `expires` | int/datetime | Invalidate task after N seconds or at datetime |
| `retry` | bool | Retry on connection failure (default: True) |
| `retry_policy` | dict | Connection retry config |
| `queue` | str | Target queue name |
| `exchange` | str | AMQP exchange |
| `routing_key` | str | AMQP routing key |
| `priority` | int (0-255) | Message priority (255=highest) |
| `serializer` | str | Message format (json, pickle, msgpack) |
| `compression` | str | Compression (zlib, bzip2, gzip, zstd, brotli, lzma) |
| `link` | signature | Success callback |
| `link_error` | signature | Error callback |
| `ignore_result` | bool | Skip result storage |

### Timing Control

```python
from datetime import datetime, timedelta, timezone

# Countdown — execute after N seconds
add.apply_async((2, 2), countdown=60)

# ETA — execute at specific time
tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
add.apply_async((2, 2), eta=tomorrow)

# Expiration — discard if not executed in time
add.apply_async((10, 10), expires=300)  # 5 minutes
```

> **Warning:** ETA/countdown tasks reside in worker memory. Don't schedule far-future tasks this way — use Celery Beat instead. RabbitMQ may timeout with countdown >15 minutes.

### Connection Retry Policy

```python
add.apply_async((2, 2), retry=True, retry_policy={
    'max_retries': 3,
    'interval_start': 0,       # First retry immediately
    'interval_step': 0.2,      # Add 0.2s each retry
    'interval_max': 0.2,       # Cap at 0.2s
    'retry_errors': (TimeoutError,),
})
```

### Handling Connection Errors

```python
try:
    add.delay(2, 2)
except add.OperationalError as exc:
    logger.exception('Sending task raised: %r', exc)
```

---

## Task Linking (Callbacks & Errbacks)

```python
# Success callback — result of add(2,2) becomes first arg to mul
add.apply_async((2, 2), link=mul.s(16))
# add(2,2)=4 → mul(4, 16)=64

# Error callback
@app.task
def error_handler(request, exc, traceback):
    print(f'Task {request.id} raised: {exc!r}')

add.apply_async((2, 2), link_error=error_handler.s())

# Multiple callbacks
add.apply_async((2, 2), link=[mul.s(16), log_result.s()])
```

### Accessing Linked Results

```python
res = add.apply_async((2, 2), link=mul.s(16))
res.children            # [<AsyncResult: ...>]
res.children[0].get()   # 64
list(res.collect())     # [(<AsyncResult>, 4), (<AsyncResult>, 64)]
```

---

## Progress Monitoring

```python
@app.task(bind=True)
def long_task(self, data):
    total = len(data)
    for i, item in enumerate(data):
        process(item)
        self.update_state(state='PROGRESS', meta={'current': i, 'total': total})
    return {'status': 'complete'}

# Monitor progress
result = long_task.delay(data)
result.state  # 'PROGRESS'
result.info   # {'current': 42, 'total': 100}
```

---

## Signatures

Signatures wrap a task invocation (name + args + options) into a serializable object.

```python
from celery import signature

# Three ways to create
sig = signature('tasks.add', args=(2, 2), countdown=10)
sig = add.signature((2, 2), countdown=10)
sig = add.s(2, 2)  # Shortcut

# Inspect
sig.args       # (2, 2)
sig.kwargs     # {}
sig.options    # {'countdown': 10}

# Execute
sig.delay()
sig.apply_async()
sig()  # Synchronous
```

### Partials

```python
# Incomplete signature — missing one arg
partial = add.s(2)
partial.delay(8)          # add(8, 2) — args prepended
partial.apply_async((8,)) # Same

# kwargs merge (new values win)
s = add.s(2, 2)
s.delay(debug=True)       # add(2, 2, debug=True)

# Options merge (new values win)
s = add.signature((2, 2), countdown=10)
s.apply_async(countdown=1)  # countdown=1

# Clone with modifications
s = add.s(2)
s.clone(args=(4,), kwargs={'debug': True})  # add(4, 2, debug=True)
```

### Immutable Signatures (.si)

Prevent parent result from being passed as argument. Use for callbacks that don't need the parent's return value.

```python
# Mutable — receives parent result as first arg
add.apply_async((2, 2), link=mul.s(16))     # mul(4, 16)

# Immutable — ignores parent result
add.apply_async((2, 2), link=reset_buffers.si())  # reset_buffers()

# Creating immutable signatures
add.si(2, 2)
add.signature((2, 2), immutable=True)
```

---

## Canvas Primitives

### chain — Sequential Execution

Each task's return value becomes the first argument of the next task.

```python
from celery import chain

# Explicit
res = chain(add.s(4, 4), mul.s(8), mul.s(10))()
res.get()  # (4+4) * 8 * 10 = 640

# Pipe syntax (preferred)
res = (add.s(4, 4) | mul.s(8) | mul.s(10))()
res.get()  # 640

# Partial chain
c = add.s(4) | mul.s(8)
res = c(16)            # (16+4) * 8 = 160

# Traversing results
res = (add.s(4, 4) | mul.s(8) | mul.s(10))()
res.get()              # 640
res.parent.get()       # 64
res.parent.parent.get()  # 8
```

### group — Parallel Execution

```python
from celery import group

# Execute tasks in parallel
res = group(add.s(i, i) for i in range(10))()
res.get()  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# GroupResult API
res.ready()             # All done?
res.successful()        # All succeeded?
res.failed()            # Any failed?
res.completed_count()   # Number completed
res.revoke()            # Cancel all
```

### chord — Group + Callback (Fan-out/Fan-in)

```python
from celery import chord

# Parallel tasks, then aggregate
res = chord(add.s(i, i) for i in range(10))(tsum.s())
res.get()  # 90

# Equivalent pipe syntax
res = (group(add.s(i, i) for i in range(10)) | tsum.s())()
res.get()  # 90

# Immutable callback (doesn't receive group results)
chord(
    (import_contact.s(c) for c in contacts),
    notify_complete.si(import_id)
).apply_async()
```

**Chord error handling:**

```python
@app.task
def on_chord_error(request, exc, traceback):
    print(f'Task {request.id!r} raised: {exc!r}')

c = (group(add.s(i, i) for i in range(10)) |
     tsum.s().on_error(on_chord_error.s()))
c.delay()
```

> **Important:** Chords require a result backend. Tasks in a chord must NOT have `ignore_result=True`.

### chunks — Batch Processing

Divides work into batches to reduce messaging overhead.

```python
# Split 100 items into batches of 10
res = add.chunks(zip(range(100), range(100)), 10)()
res.get()  # [[0, 2, 4, ...], [20, 22, ...], ...]

# Convert to group for parallel execution
add.chunks(zip(range(100), range(100)), 10).group()
```

### map & starmap — Sequential Iteration

Single task message, sequential execution (unlike group which sends separate messages).

```python
# map — single argument per call
~tsum.map([list(range(10)), list(range(100))])  # [45, 4950]

# starmap — unpacks arguments
~add.starmap(zip(range(10), range(10)))  # [0, 2, 4, ..., 18]
```

---

## Complex Workflow Patterns

### Chain into Group (fan-out)

```python
new_user_workflow = (
    create_user.s() |
    group(import_contacts.s(), send_welcome_email.s())
)
new_user_workflow.delay(username='art', email='art@example.com')
```

### Preventing Result Forwarding

```python
# Use .si() to prevent parent result being passed
res = (add.s(4, 4) | group(add.si(i, i) for i in range(10)))()
res.get()         # [0, 2, 4, ..., 18] — each runs independently
res.parent.get()  # 8 — result of add(4,4)
```

### Connection Pooling for Bulk Sends

```python
# Efficient bulk sending
with add.app.pool.acquire(block=True) as connection:
    with add.get_publisher(connection) as publisher:
        for args in work_items:
            add.apply_async(args, publisher=publisher)

# Better: use group
from celery import group
group(add.s(*args) for args in work_items).apply_async()
```

---

## Best Practices

- **Prefer pipe syntax** for chains: `add.s(2, 2) | mul.s(8)` over `chain(add.s(2, 2), mul.s(8))`
- **Use `.si()` for callbacks** that don't need the parent result
- **Avoid overly complex workflows** — deeply nested canvas primitives are hard to debug
- **Use groups over manual loops** for parallel work
- **Always configure a result backend** when using chords
- **Use JSON serializer** for simple workflows, **pickle for complex** ones (JSON inflates message size with recursive references)

## Common Pitfalls

- **Chord without result backend:** Chords require results — they'll silently fail without a backend
- **`ignore_result=True` in chords:** Tasks in a chord must store results
- **Calling `.get()` inside a task:** Deadlocks the worker pool. Use chains/chords instead
- **Single-item groups unroll:** `chain(a, group(b), c)` becomes `a | b | c` — the group disappears
- **Far-future ETA/countdown:** Uses worker memory; use Beat for scheduled tasks
- **Synchronous waiting in workflows:** Never block — let canvas handle orchestration
