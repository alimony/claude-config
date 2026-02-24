# Celery: Configuration
Based on Celery 5.6.2 documentation.

## Configuration Methods

```python
# Direct
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.update(timezone='UTC', enable_utc=True)

# From module
app.config_from_object('proj.celeryconfig')

# From class
app.config_from_object('proj.config:ProductionConfig')

# From environment variable
app.config_from_envvar('CELERY_CONFIG_MODULE')
```

---

## Essential Settings by Category

### Broker

| Setting | Default | Description |
|---------|---------|-------------|
| `broker_url` | `'amqp://'` | Connection URL: `transport://user:pass@host:port/vhost` |
| `broker_connection_retry_on_startup` | True | Retry connection on initial startup |
| `broker_connection_retry` | True | Retry on subsequent connection loss |
| `broker_heartbeat` | 120 | Heartbeat interval in seconds (AMQP only) |
| `broker_pool_limit` | 10 | Connection pool size (0=disabled, None=unlimited) |
| `broker_use_ssl` | False | Enable SSL/TLS |

### Result Backend

| Setting | Default | Description |
|---------|---------|-------------|
| `result_backend` | None | Backend URL (e.g. `'redis://localhost/1'`, `'rpc://'`) |
| `result_expires` | 86400 (1 day) | Result TTL in seconds |
| `result_serializer` | `'json'` | Serialization format for results |
| `result_compression` | None | Compression method |
| `result_extended` | False | Store additional metadata (task name, args, etc.) |

### Task Execution

| Setting | Default | Description |
|---------|---------|-------------|
| `task_serializer` | `'json'` | Default serializer for task messages |
| `task_time_limit` | None | Hard kill after N seconds |
| `task_soft_time_limit` | None | Raise exception after N seconds |
| `task_acks_late` | False | Ack after execution (requires idempotent tasks) |
| `task_ignore_result` | False | Don't store results globally |
| `task_track_started` | False | Report STARTED state |
| `task_always_eager` | False | Run tasks synchronously (testing only!) |
| `task_eager_propagates` | False | Eager tasks propagate exceptions |
| `task_create_missing_queues` | True | Auto-create queues |

### Task Routing

| Setting | Default | Description |
|---------|---------|-------------|
| `task_default_queue` | `'celery'` | Default queue name |
| `task_default_exchange` | `'celery'` | Default exchange |
| `task_default_routing_key` | `'celery'` | Default routing key |
| `task_routes` | None | Task routing configuration |
| `task_queues` | None | Queue definitions |

### Worker

| Setting | Default | Description |
|---------|---------|-------------|
| `worker_concurrency` | CPU count | Number of concurrent processes/threads |
| `worker_prefetch_multiplier` | 4 | Messages prefetched per worker (1=fair, 0=unlimited) |
| `worker_max_tasks_per_child` | None | Recycle process after N tasks |
| `worker_max_memory_per_child` | None | Recycle process at N KB |
| `worker_disable_rate_limits` | False | Override all rate limits |
| `worker_send_task_events` | False | Enable event monitoring |
| `worker_cancel_long_running_tasks_on_connection_loss` | False | Cancel tasks on disconnect |
| `worker_soft_shutdown_timeout` | None | Soft shutdown timeout (v5.5+) |

### Beat (Scheduler)

| Setting | Default | Description |
|---------|---------|-------------|
| `beat_schedule` | {} | Periodic task definitions |
| `beat_scheduler` | `'celery.beat:PersistentScheduler'` | Scheduler class |
| `beat_schedule_filename` | `'celerybeat-schedule'` | Schedule state file |
| `timezone` | `'UTC'` | Timezone for beat schedules |
| `enable_utc` | True | Use UTC internally |

### Serialization & Security

| Setting | Default | Description |
|---------|---------|-------------|
| `accept_content` | `['json']` | Allowed content types |
| `result_accept_content` | None | Allowed types for results (defaults to accept_content) |
| `task_serializer` | `'json'` | Task message serializer |
| `result_serializer` | `'json'` | Result serializer |

### Events

| Setting | Default | Description |
|---------|---------|-------------|
| `worker_send_task_events` | False | Send task events for monitoring |
| `task_send_sent_event` | False | Send event when task is published |

---

## Common Configuration Patterns

### Development

```python
class DevConfig:
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    task_always_eager = True          # Run synchronously
    task_eager_propagates = True      # Raise exceptions immediately
    worker_concurrency = 1
```

### Production

```python
class ProdConfig:
    broker_url = 'amqp://user:pass@rabbit-host:5672/vhost'
    result_backend = 'redis://redis-host:6379/0'
    result_expires = 3600
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    worker_max_memory_per_child = 200000
    worker_send_task_events = True
    task_send_sent_event = True
    task_track_started = True
    broker_connection_retry_on_startup = True
```

### Django Integration

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# celery.py — load from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')
```

---

## Serializer Comparison

| Serializer | Speed | Security | Types |
|------------|-------|----------|-------|
| **json** | Fast | Safe | Basic types only |
| **pickle** | Fast | UNSAFE (arbitrary code execution) | All Python objects |
| **msgpack** | Fastest | Safe | Basic types |
| **yaml** | Slow | Safe | Basic types + some Python |

> **Default is json.** Only use pickle if you trust all message producers. Restrict with `accept_content = ['json']`.

---

## Best Practices

- **Always set `accept_content`** to restrict allowed serializers
- **Use `result_expires`** to prevent unbounded backend growth
- **Set `timezone` explicitly** — don't rely on system default
- **Use `task_always_eager` only for testing** — never in production
- **Enable events in production** for monitoring visibility
- **Set `worker_max_tasks_per_child`** as a safety net against memory leaks

## Common Pitfalls

- **Old setting names** — Celery 4+ uses lowercase (e.g., `broker_url` not `BROKER_URL`). With Django namespace, use `CELERY_BROKER_URL`
- **Pickle security** — never accept pickle from untrusted sources
- **`task_always_eager` in production** — silently runs everything synchronously
- **Missing `result_backend`** — `.get()` hangs or errors without one
- **`result_expires=None`** — results accumulate forever
