# Celery: Extensions & Bootsteps
Based on Celery 5.6.2 documentation.

## Bootsteps Overview

Bootsteps add custom functionality to worker startup/shutdown. Workers have two **blueprints**:

1. **Worker** — initializes event loop, pool, timer
2. **Consumer** — establishes broker connection, consumes messages

Each blueprint contains ordered steps with dependency management.

---

## Creating Bootsteps

### Basic Worker Bootstep

```python
from celery import bootsteps

class MyWorkerStep(bootsteps.StartStopStep):
    requires = {'celery.worker.components:Pool'}

    def __init__(self, worker, **kwargs):
        print('Worker initializing')

    def start(self, worker):
        print('Worker started')

    def stop(self, worker):
        print('Worker stopping')
```

### Timer-Based Bootstep

```python
class DeadlockDetection(bootsteps.StartStopStep):
    requires = {'celery.worker.components:Timer'}

    def __init__(self, worker, deadlock_timeout=3600):
        self.timeout = deadlock_timeout
        self.tref = None

    def start(self, worker):
        self.tref = worker.timer.call_repeatedly(
            30.0, self.detect, (worker,), priority=10)

    def stop(self, worker):
        if self.tref:
            self.tref.cancel()

    def detect(self, worker):
        from time import time
        for req in worker.active_requests:
            if req.time_start and time() - req.time_start > self.timeout:
                raise SystemExit()
```

### Custom Message Consumer

```python
from kombu import Consumer, Exchange, Queue

my_queue = Queue('custom', Exchange('custom'), 'routing_key')

class MyConsumerStep(bootsteps.ConsumerStep):
    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[my_queue],
                         callbacks=[self.handle_message],
                         accept=['json'])]

    def handle_message(self, body, message):
        print(f'Received: {body!r}')
        message.ack()
```

### Gossip Callbacks (Cluster Events)

```python
class ClusterAwareStep(bootsteps.StartStopStep):
    requires = {'celery.worker.consumer.gossip:Gossip'}

    def start(self, c):
        self.c = c
        c.gossip.on.node_join.add(self.on_change)
        c.gossip.on.node_leave.add(self.on_change)
        c.gossip.on.node_lost.add(self.on_lost)

    def on_change(self, worker):
        cluster_size = len(list(self.c.gossip.state.alive_workers()))
        print(f'Cluster size: {cluster_size}')

    def on_lost(self, worker):
        self.c.timer.call_after(10.0, self.on_change)
```

---

## Installing Bootsteps

```python
app = Celery()
app.steps['worker'].add(MyWorkerStep)
app.steps['consumer'].add(MyConsumerStep)
```

---

## Dependencies

Common worker components:

| Component | Requirement String |
|-----------|-------------------|
| Event loop | `celery.worker.components:Hub` |
| Pool | `celery.worker.components:Pool` |
| Timer | `celery.worker.components:Timer` |
| State DB | `celery.worker.components:Statedb` |

Common consumer components:

| Component | Requirement String |
|-----------|-------------------|
| Connection | `celery.worker.consumer.connection:Connection` |
| Events | `celery.worker.consumer.events:Events` |
| Gossip | `celery.worker.consumer.gossip:Gossip` |
| Heartbeat | `celery.worker.consumer.heart:Heart` |
| Tasks | `celery.worker.consumer.tasks:Tasks` |

---

## Lifecycle Methods

| Method | When Called |
|--------|-----------|
| `__init__(parent)` | During initialization |
| `create(parent)` | Delegate to another object |
| `start(parent)` | Component starts |
| `stop(parent)` | Shutdown or connection loss |
| `terminate(parent)` | Hard termination |

> `stop` and `terminate` run in signal handlers — must be reentrant, cannot use Python logging.

---

## Adding CLI Options

```python
from click import Option

app.user_options['worker'].add(
    Option(('--my-option',), is_flag=True, help='Enable feature'))

class MyStep(bootsteps.Step):
    def __init__(self, parent, my_option=False, **options):
        if my_option:
            activate_feature()

app.steps['worker'].add(MyStep)
```

---

## Timer API

```python
# After delay
worker.timer.call_after(secs, callback, args=(), priority=0)

# Repeating
worker.timer.call_repeatedly(secs, callback, args=(), priority=0)

# At specific time
worker.timer.call_at(eta, callback, args=(), priority=0)
```

---

## Notable Third-Party Extensions

| Extension | Purpose |
|-----------|---------|
| **django-celery-results** | Django ORM result backend |
| **django-celery-beat** | Database-backed periodic task scheduler |
| **flower** | Real-time web monitoring |
| **celery-redbeat** | Redis-backed beat scheduler with locking |
| **pytest-celery** | Docker-based integration testing |

---

## Best Practices

- **Use bootsteps sparingly** — most needs are met by signals and configuration
- **Prefer signals** over bootsteps for simple hooks (e.g., `worker_ready`, `task_failure`)
- **Use `requires`** to declare dependencies — don't assume component ordering
- **Keep `stop`/`terminate` fast** — they run in signal handlers
- **Debug with `--loglevel=debug`** to see boot order and dependency resolution

## Common Pitfalls

- **Blocking in `start()`** — can delay worker startup or hang
- **Logging in `stop()`/`terminate()`** — signal handlers can't safely use Python logging
- **Missing `requires`** — accessing `worker.pool` without requiring `Pool` may fail
- **`worker_process_init` signal timeout** — handlers must complete in <4 seconds
