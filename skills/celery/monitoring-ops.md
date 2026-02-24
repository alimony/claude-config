# Celery: Monitoring & Operations
Based on Celery 5.6.2 documentation.

## Flower — Web Monitor

```bash
pip install flower
celery -A proj flower --port=5555
```

Access at `http://localhost:5555`. Features: real-time task monitoring, worker management, queue inspection, rate limit control, HTTP API.

---

## CLI Commands

### Status

```bash
celery -A proj status                    # List online workers
celery -A proj inspect active            # Currently executing tasks
celery -A proj inspect reserved          # Prefetched tasks
celery -A proj inspect scheduled         # ETA/countdown tasks
celery -A proj inspect registered        # All registered task names
celery -A proj inspect stats             # Worker statistics
celery -A proj inspect active_queues     # Queues being consumed
celery -A proj inspect query_task <uuid> # Task details by ID

# Target specific workers
celery -A proj inspect active -d worker1@host,worker2@host
celery -A proj inspect --timeout=10 active
```

### Control

```bash
celery -A proj control enable_events     # Enable event monitoring
celery -A proj control disable_events
celery -A proj events                    # Curses monitor
celery -A proj events --dump             # Dump events to stdout
celery -A proj purge                     # DANGER: Delete all queued messages
celery -A proj purge -Q celery,foo       # Purge specific queues
celery -A proj result <uuid>             # Get task result
celery -A proj migrate redis://src amqp://dst  # Move messages between brokers
```

### Programmatic Inspection

```python
i = app.control.inspect()
i = app.control.inspect(['worker1@host'])  # Specific workers

i.active()          # Running tasks
i.reserved()        # Prefetched
i.scheduled()       # ETA tasks
i.registered()      # Task names
i.stats()           # Statistics
```

### Programmatic Control

```python
app.control.ping(timeout=0.5)
app.control.rate_limit('tasks.api_call', '200/m')
app.control.time_limit('tasks.crawl', soft=60, hard=120, reply=True)
app.control.broadcast('shutdown')
app.control.enable_events()
app.control.add_consumer('new_queue', reply=True)
app.control.cancel_consumer('old_queue', reply=True)
```

---

## Real-time Event Processing

```python
def my_monitor(app):
    state = app.events.State()

    def on_task_failed(event):
        state.event(event)
        task = state.tasks.get(event['uuid'])
        print(f'FAILED: {task.name}[{task.uuid}] {task.info()}')

    with app.connection() as connection:
        recv = app.events.Receiver(connection, handlers={
            'task-failed': on_task_failed,
            '*': state.event,  # Catch-all to maintain state
        })
        recv.capture(limit=None, timeout=None, wakeup=True)
```

### Event Types

| Event | When |
|-------|------|
| `task-sent` | Published (requires `task_send_sent_event=True`) |
| `task-received` | Worker receives task |
| `task-started` | Execution begins |
| `task-succeeded` | Completed successfully |
| `task-failed` | Exception raised |
| `task-retried` | Retry scheduled |
| `task-revoked` | Task cancelled |
| `worker-online` | Worker connected |
| `worker-heartbeat` | Every ~60s (offline after 2 missed) |
| `worker-offline` | Worker disconnected |

---

## Queue Inspection

```bash
# RabbitMQ
rabbitmqctl list_queues name messages messages_ready messages_unacknowledged

# Redis
redis-cli llen celery
```

---

## Optimization

### Prefetch Multiplier

Controls how many messages each worker prefetches.

```python
# Long tasks — fairest distribution
worker_prefetch_multiplier = 1

# Short tasks — best throughput (default is 4)
worker_prefetch_multiplier = 50

# Disable prefetching entirely (Redis only)
worker_disable_prefetch = True
```

### Late Acknowledgment

Ack after execution to prevent task loss on worker crash:

```python
task_acks_late = True
worker_prefetch_multiplier = 1  # Recommended with acks_late
```

### Memory Management

```python
worker_max_tasks_per_child = 1000    # Recycle after N tasks
worker_max_memory_per_child = 200000  # Recycle at ~200MB
```

### Connection Pooling

```python
broker_pool_limit = 10  # Connection pool size (default: 10, 0=disabled)
```

### Transient Queues

For non-critical tasks, skip disk persistence:

```python
from kombu import Exchange, Queue

task_queues = (
    Queue('transient', Exchange('transient', delivery_mode=1),
          routing_key='transient', durable=False),
)
```

---

## Debugging

### Remote Debugger (rdb)

```python
from celery.contrib import rdb

@app.task
def debug_task():
    rdb.set_trace()  # Opens telnet debugger
```

```bash
# Connect to debugger
telnet localhost 6899
```

### Dump Worker State

```bash
kill -USR1 <worker-pid>  # Dump thread tracebacks to logs
```

---

## Best Practices

- **Enable Flower in production** for visibility into task execution
- **Monitor queue lengths** — growing queues indicate capacity issues
- **Set `worker_send_task_events=True`** for monitoring (slight overhead)
- **Route long and short tasks to separate workers** to prevent blocking
- **Use `worker_prefetch_multiplier=1`** for long-running tasks
- **Set `worker_max_tasks_per_child`** for tasks with potential memory leaks
- **Capacity plan:** if tasks take 10min avg and 10 arrive/min, you need 100 workers

## Common Pitfalls

- **High prefetch with long tasks** — one worker grabs many tasks, others idle
- **No result backend** — can't query task state without one
- **`task_always_eager` in production** — disables async, defeats the purpose of Celery
- **Unmonitored queues** — messages pile up silently until OOM
- **Forgetting `wakeup=True`** on event receiver — may miss initial heartbeats
