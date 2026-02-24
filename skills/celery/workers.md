# Celery: Workers
Based on Celery 5.6.2 documentation.

## Starting Workers

```bash
# Basic
celery -A proj worker --loglevel=INFO

# With concurrency, specific queues, and node name
celery -A proj worker -l INFO -c 10 -Q default,priority -n worker1@%h
```

**Node name variables:** `%h` (full hostname), `%n` (hostname only), `%d` (domain only)

---

## Concurrency Pools

| Pool | Flag | Best For |
|------|------|----------|
| **prefork** | (default) | CPU-bound tasks, general purpose |
| **eventlet** | `-P eventlet` | I/O-bound tasks (HTTP calls, etc.) |
| **gevent** | `-P gevent` | I/O-bound tasks |
| **threads** | `-P threads` | I/O-bound, GIL-compatible |
| **solo** | `-P solo` | Single task at a time, debugging |

Default concurrency = number of CPUs. Override with `-c N`.

```bash
# 100 green threads for I/O-heavy work
celery -A proj worker -P eventlet -c 100

# 4 processes for CPU work
celery -A proj worker -P prefork -c 4
```

---

## Worker Lifecycle

### Shutdown Types

| Signal | Type | Behavior |
|--------|------|----------|
| `TERM` | Warm | Finishes current tasks, then exits |
| `QUIT` | Cold | Terminates immediately |
| `INT` (Ctrl+C) | Warm (first), Hard (repeated) | First: warm shutdown; second: immediate |

**Soft shutdown** (v5.5+): Time-limited warm shutdown via `worker_soft_shutdown_timeout`.

### Restart

```bash
celery multi restart w1 -A proj --pidfile=/var/run/celery/%n.pid
```

---

## celery multi — Multiple Workers

```bash
# Start 3 workers
celery multi start w1 w2 w3 -A proj -l INFO \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log

# Start 10 workers with queue routing
celery multi start 10 -A proj -l INFO \
    -Q:1-3 images,video -Q:4,5 data -Q default

# Graceful stop
celery multi stopwait w1 w2 w3 --pidfile=/var/run/celery/%n.pid
```

**Log/pid file variables:** `%n` (node name), `%i` (pool process index), `%I` (index with separator)

---

## Remote Control

Requires RabbitMQ or Redis broker.

### Inspect (read-only)

```python
i = app.control.inspect()

i.active()           # Currently executing tasks
i.reserved()         # Prefetched, waiting to execute
i.scheduled()        # ETA/countdown tasks
i.registered()       # All registered task names
i.stats()            # Worker statistics

# Target specific workers
i = app.control.inspect(['worker1@host', 'worker2@host'])
```

```bash
celery -A proj inspect active
celery -A proj inspect registered
celery -A proj inspect stats
celery -A proj status          # List online workers
```

### Control (modify state)

```python
# Ping
app.control.ping(timeout=0.5)

# Rate limits
app.control.rate_limit('tasks.api_call', '200/m')
app.control.rate_limit('tasks.api_call', '200/m',
                       destination=['worker1@host'])

# Time limits
app.control.time_limit('tasks.crawl', soft=60, hard=120, reply=True)

# Shutdown
app.control.broadcast('shutdown')

# Enable/disable events
app.control.enable_events()
app.control.disable_events()
```

---

## Revoking Tasks

```python
# By result
result.revoke()

# By ID
app.control.revoke('task-uuid-here')

# With termination (kills running task)
app.control.revoke('task-uuid-here', terminate=True)
app.control.revoke('task-uuid-here', terminate=True, signal='SIGKILL')

# Multiple tasks
app.control.revoke(['uuid1', 'uuid2', 'uuid3'])

# By stamped headers
app.control.revoke_by_stamped_headers({'header': 'value'})
```

**Persistent revokes** (survive restarts):
```bash
celery -A proj worker --statedb=/var/run/celery/worker.state
```

---

## Queue Management

### At Startup

```bash
celery -A proj worker -Q foo,bar,baz
```

### At Runtime

```python
# Add queue
app.control.add_consumer('new_queue', reply=True)

# Add with routing
app.control.add_consumer(
    queue='media',
    exchange='media_exchange',
    exchange_type='topic',
    routing_key='media.*',
    reply=True,
    destination=['worker1@host']
)

# Remove queue
app.control.cancel_consumer('old_queue', reply=True)

# List active queues
# celery -A proj inspect active_queues
```

---

## Time Limits

```python
from celery.exceptions import SoftTimeLimitExceeded

@app.task(soft_time_limit=60, time_limit=120)
def crawl(url):
    try:
        return fetch(url)
    except SoftTimeLimitExceeded:
        cleanup()
        return partial_result
```

```bash
# Via command line
celery -A proj worker --time-limit=300 --soft-time-limit=240
```

```python
# Runtime change
app.control.time_limit('tasks.crawl', soft=60, hard=120, reply=True)
```

---

## Prefork Pool Tuning

### max_tasks_per_child — Prevent Memory Leaks

Replace worker process after N tasks:
```bash
celery -A proj worker --max-tasks-per-child=1000
```

### max_memory_per_child — Memory Limit

Recycle process at memory threshold (KB):
```bash
celery -A proj worker --max-memory-per-child=200000  # ~200MB
```

---

## Autoscaling

```bash
# Min 3, max 10 processes
celery -A proj worker --autoscale=10,3
```

Scales up under load, scales down when idle.

---

## Daemonization

### systemd

```ini
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=celery
Group=celery
EnvironmentFile=/etc/conf.d/celery
WorkingDirectory=/opt/celery
ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} multi start ${CELERYD_NODES} \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
    --pidfile=${CELERYD_PID_FILE} --loglevel=${CELERYD_LOG_LEVEL}'
ExecReload=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} multi restart ${CELERYD_NODES} \
    --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
Restart=always

[Install]
WantedBy=multi-user.target
```

### Beat systemd service

```ini
# /etc/systemd/system/celerybeat.service
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=celery
Group=celery
ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} beat \
    --schedule=${CELERYBEAT_SCHEDULE_FILE} \
    --loglevel=${CELERYD_LOG_LEVEL}'
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Connection Resilience

- **Auto-reconnect on startup:** `broker_connection_retry_on_startup = True` (default in 5.3+)
- **Cancel tasks on disconnect:** `worker_cancel_long_running_tasks_on_connection_loss = True`
- **Prefetch auto-reduction:** Worker reduces prefetch count after connection loss, gradually restores

---

## Custom Remote Control Commands

```python
from celery.worker.control import control_command, inspect_command

@control_command(args=[('n', int)], signature='[N=1]')
def increase_prefetch(state, n=1):
    state.consumer.qos.increment_eventually(n)
    return {'ok': 'done'}

@inspect_command()
def current_prefetch(state):
    return {'prefetch_count': state.consumer.qos.value}
```

```bash
celery -A proj control increase_prefetch 3
celery -A proj inspect current_prefetch
```

---

## Best Practices

- **Use prefork** for CPU-bound, **eventlet/gevent** for I/O-bound work
- **Set `max_tasks_per_child`** for tasks with C extensions that leak memory
- **Use `--autoscale`** in production to handle load spikes
- **Run only one beat instance** — multiple beats cause duplicate executions
- **Use `--statedb`** to persist revoked task IDs across restarts
- **Monitor with `inspect stats`** to track pool utilization

## Common Pitfalls

- **Too many prefork workers** — more workers than CPUs causes context-switching overhead
- **eventlet/gevent with CPU work** — green threads don't parallelize CPU tasks
- **Forgetting `-Q`** — worker only consumes from `celery` queue by default
- **`SIGKILL` on prefork children** — data corruption risk; prefer `SIGTERM`
- **Worker not picking up code changes** — must restart workers after deployment
