# Celery: Routing
Based on Celery 5.6.2 documentation.

## Automatic Routing (Simple)

By default, `task_create_missing_queues=True` — Celery auto-creates queues as needed.

```python
# Route specific tasks to specific queues
app.conf.task_routes = {
    'feed.tasks.import_feed': {'queue': 'feeds'},
}

# Pattern matching
app.conf.task_routes = {
    'feed.tasks.*': {'queue': 'feeds'},
    'web.tasks.*': {'queue': 'web'},
}

# Change default queue name (default is 'celery')
app.conf.task_default_queue = 'default'
```

```bash
# Start worker for specific queues
celery -A proj worker -Q feeds
celery -A proj worker -Q feeds,celery  # Multiple queues
```

### Ordered Pattern Matching

```python
import re

app.conf.task_routes = ([
    ('feed.tasks.*', {'queue': 'feeds'}),
    ('web.tasks.*', {'queue': 'web'}),
    (re.compile(r'(video|image)\.tasks\..*'), {'queue': 'media'}),
],)
```

Patterns are evaluated in order; first match wins.

---

## Routing at Call Time

```python
# Override routing per-call
task.apply_async(args, queue='priority')
task.apply_async(args, queue='feeds', routing_key='feed.import')
task.apply_async(args, priority=9)
```

---

## Queue Configuration (AMQP)

```python
from kombu import Exchange, Queue

default_exchange = Exchange('default', type='direct')
media_exchange = Exchange('media', type='direct')

app.conf.task_queues = (
    Queue('default', default_exchange, routing_key='default'),
    Queue('videos', media_exchange, routing_key='media.video'),
    Queue('images', media_exchange, routing_key='media.image'),
)
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'
```

### Multiple Bindings

```python
from kombu import binding

media_exchange = Exchange('media', type='direct')
app.conf.task_queues = (
    Queue('media', [
        binding(media_exchange, routing_key='media.video'),
        binding(media_exchange, routing_key='media.image'),
    ]),
)
```

---

## AMQP Exchange Types

| Type | Routing Behavior |
|------|------------------|
| **direct** | Exact routing key match |
| **topic** | Pattern match with `*` (one word) and `#` (zero+ words) |
| **fanout** | Broadcast to all bound queues |

**Topic example:** routing key `usa.news` matches patterns `usa.*`, `usa.#`, `#.news`, `#`

---

## Custom Routers

```python
def route_task(name, args, kwargs, options, task=None, **kw):
    if name == 'myapp.tasks.compress_video':
        return {
            'exchange': 'video',
            'exchange_type': 'topic',
            'routing_key': 'video.compress',
        }
    return None  # Fall through to next router

app.conf.task_routes = (route_task,)

# Or by import path
app.conf.task_routes = ('myapp.routers.route_task',)

# Mixed routers and dicts
app.conf.task_routes = [
    route_task,
    {'myapp.tasks.compress_video': {'queue': 'video'}},
]
```

---

## Priority Queues

### RabbitMQ

```python
from kombu import Exchange, Queue

app.conf.task_queues = [
    Queue('tasks', Exchange('tasks'), routing_key='tasks',
          queue_arguments={'x-max-priority': 10}),
]
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5
```

### Redis (simulated)

```python
app.conf.broker_transport_options = {
    'queue_order_strategy': 'priority',
    'priority_steps': list(range(10)),
    'sep': ':',
}
```

> **Note:** Reduce `worker_prefetch_multiplier` to 1 for better priority responsiveness.

---

## Broadcast Routing

Send a task to ALL workers:

```python
from kombu.common import Broadcast

app.conf.task_queues = (Broadcast('broadcast_tasks'),)
app.conf.task_routes = {
    'tasks.reload_cache': {
        'queue': 'broadcast_tasks',
        'exchange': 'broadcast_tasks',
    },
}
```

> Set `ignore_result=True` on broadcast tasks.

### Transient Queues

For non-critical tasks, skip disk persistence:

```python
app.conf.task_queues = (
    Queue('transient', Exchange('transient', delivery_mode=1),
          routing_key='transient', durable=False),
)
```

---

## Routing Resolution Order

1. Arguments to `apply_async()` (queue, exchange, routing_key)
2. Task class attributes
3. Entries in `task_routes` (routers evaluated in sequence)

---

## Best Practices

- **Start simple** — use `task_routes` with queue names, skip AMQP details until needed
- **Separate by workload type** — CPU-heavy tasks on different queues/workers than I/O tasks
- **Use `-Q`** to dedicate workers to specific queues
- **Name queues descriptively** — `emails`, `reports`, `image-processing`

## Common Pitfalls

- **Worker not consuming queue** — forgot to add `-Q queue_name` at startup
- **Missing queues** — disable `task_create_missing_queues` and queues must be pre-declared
- **Priority with prefetch** — high-prefetch negates priority ordering
- **Broadcast + results** — don't store results for broadcast tasks
