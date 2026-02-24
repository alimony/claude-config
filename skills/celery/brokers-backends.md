# Celery: Brokers & Backends
Based on Celery 5.6.2 documentation.

## Broker Comparison

| Broker | Status | Monitoring | Remote Control |
|--------|--------|------------|----------------|
| **RabbitMQ** | Stable | Yes | Yes |
| **Redis** | Stable | Yes | Yes |
| **Amazon SQS** | Stable | No | No |
| **Kafka** | Experimental | No | No |
| **GCP Pub/Sub** | Experimental | Yes | Yes |

**Recommendation:** RabbitMQ for production (feature-complete, durable). Redis for simpler setups (fast, but data loss risk on crashes).

---

## RabbitMQ

### Connection URL

```python
broker_url = 'amqp://myuser:mypassword@localhost:5672/myvhost'
```

### Setup

```bash
sudo rabbitmqctl add_user myuser mypassword
sudo rabbitmqctl add_vhost myvhost
sudo rabbitmqctl set_user_tags myuser mytag
sudo rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
```

### Docker

```bash
docker run -d -p 5672:5672 rabbitmq
```

### Quorum Queues

```python
from kombu import Queue

task_queues = [Queue('my-queue', queue_arguments={'x-queue-type': 'quorum'})]
broker_transport_options = {'confirm_publish': True}

# Or globally
task_default_queue_type = 'quorum'
```

> Quorum queues require disabling global QoS — some features (autoscaling, prefetch reduction) won't work.

---

## Redis

### Connection URL

```python
# Standard
broker_url = 'redis://:password@hostname:port/db_number'

# Unix socket
broker_url = 'redis+socket:///path/to/redis.sock?virtual_host=0'

# Sentinel
broker_url = 'sentinel://host1:26379;sentinel://host2:26379;sentinel://host3:26379'
broker_transport_options = {'master_name': 'cluster1'}
```

### As Result Backend

```python
result_backend = 'redis://localhost:6379/0'

# With Sentinel
result_backend = 'sentinel://host1:26379'
result_backend_transport_options = {'master_name': 'mymaster'}
```

### Visibility Timeout

Default: 1 hour. Tasks not acked within this window are redelivered.

```python
broker_transport_options = {'visibility_timeout': 43200}  # 12 hours
```

> **Critical:** Tasks with ETA/countdown exceeding the visibility timeout will execute repeatedly. Set this higher than your longest ETA.

### Key Eviction Prevention

Configure Redis server:
```
maxmemory-policy noeviction
```

Without this, Redis may evict Celery keys under memory pressure, causing `InconsistencyError`.

### Global Key Prefix

```python
result_backend_transport_options = {
    'global_keyprefix': 'myapp_'
}
```

---

## Amazon SQS

```python
broker_url = 'sqs://'
broker_transport_options = {
    'region': 'us-east-1',
    'visibility_timeout': 3600,
    'polling_interval': 1,
}
```

Uses AWS credentials from environment (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

**Limitations:** No monitoring or remote control, message size limit (256KB), no priority support.

---

## Result Backends

| Backend | URL Scheme | Notes |
|---------|-----------|-------|
| **Redis** | `redis://` | Fast K/V store, memory-limited |
| **RPC** | `rpc://` | Results as AMQP messages (can only be retrieved once) |
| **Database** | `db+postgresql://`, `db+mysql://` | Via SQLAlchemy |
| **Django ORM** | `django-db` | Via django-celery-results |
| **Django Cache** | `django-cache` | Uses Django cache framework |
| **Memcached** | `cache+memcached://` | Fast but volatile |
| **MongoDB** | `mongodb://` | Document store |
| **Elasticsearch** | `elasticsearch://` | Search-oriented |

### RPC Backend

```python
result_backend = 'rpc://'
```

Returns results as AMQP messages. Fast, but results can only be retrieved **once** and only by the caller.

### Django ORM Backend

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

---

## Best Practices

- **RabbitMQ** for reliability and rich routing needs
- **Redis** when simplicity and speed matter more than durability
- **Set `result_expires`** to prevent unbounded backend growth
- **Use `rpc://` backend** for temporary results (fastest, no cleanup needed)
- **Set `visibility_timeout`** higher than your longest-running task (Redis/SQS)
- **Configure `noeviction`** on Redis to prevent key loss

## Common Pitfalls

- **Redis visibility timeout too low** — tasks with long ETA/countdown re-execute repeatedly
- **Redis eviction** — without `noeviction` policy, Celery keys get deleted under memory pressure
- **RPC results consumed once** — calling `.get()` twice returns nothing the second time
- **SQS message size** — tasks with large payloads fail (256KB limit)
- **Missing result backend** — `.get()` hangs or errors without one configured
