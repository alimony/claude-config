# Celery: Signals, Testing & Security
Based on Celery 5.6.2 documentation.

## Signals

### Connecting to Signals

```python
from celery.signals import task_failure

@task_failure.connect
def handle_failure(sender=None, task_id=None, exception=None, **kwargs):
    print(f'Task {task_id} failed: {exception}')

# Filter by sender (specific task)
@task_failure.connect(sender='proj.tasks.send_email')
def handle_email_failure(sender=None, **kwargs):
    alert_admin()
```

> Always include `**kwargs` in signal handlers for forward compatibility.

### Task Signals

| Signal | When | Key Arguments |
|--------|------|---------------|
| `before_task_publish` | Before publishing (in sender) | `body`, `exchange`, `routing_key`, `headers` |
| `after_task_publish` | After sent to broker | `headers`, `body`, `exchange`, `routing_key` |
| `task_prerun` | Before execution (in worker) | `task_id`, `task`, `args`, `kwargs` |
| `task_postrun` | After execution | `task_id`, `task`, `args`, `kwargs`, `retval`, `state` |
| `task_retry` | When retrying | `request`, `reason`, `einfo` |
| `task_success` | On success | `result` |
| `task_failure` | On failure | `task_id`, `exception`, `args`, `kwargs`, `traceback`, `einfo` |
| `task_received` | Received from broker | `request` |
| `task_revoked` | Revoked/terminated | `request`, `terminated`, `signum`, `expired` |
| `task_unknown` | Unregistered task received | `name`, `id`, `message`, `exc` |
| `task_rejected` | Unknown message type | `message`, `exc` |

### Worker Signals

| Signal | When | Key Arguments |
|--------|------|---------------|
| `celeryd_init` | First startup signal | `sender` (hostname), `instance`, `conf`, `options` |
| `celeryd_after_setup` | After setup, before run | `sender` (nodename), `instance`, `conf` |
| `worker_init` | Before worker starts | — |
| `worker_ready` | Ready to accept work | — |
| `worker_process_init` | Pool child process starts | — (must complete in <4s) |
| `worker_shutdown` | About to shut down | — |

### Beat Signals

| Signal | When |
|--------|------|
| `beat_init` | Beat starts (standalone or embedded) |
| `beat_embedded_init` | Beat starts as embedded process |

### Example: Per-Worker Configuration

```python
from celery.signals import celeryd_init

@celeryd_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    if sender == 'worker1@example.com':
        conf.task_default_rate_limit = '10/m'
```

### Example: Database Connection in Workers

```python
from celery.signals import worker_process_init

@worker_process_init.connect
def init_worker(**kwargs):
    # Initialize per-process database connections
    db.connect()
```

---

## Testing

### Approach: Mock, Don't Eager

Avoid `task_always_eager` — it emulates worker behavior with many discrepancies from production. Test by mocking instead.

### Task Design for Testability

```python
# Extract business logic from task
def _process_order(order_id, amount):
    order = Order.objects.get(id=order_id)
    order.charge(amount)
    return order.status

@app.task(bind=True)
def process_order(self, order_id, amount):
    try:
        return _process_order(order_id, amount)
    except PaymentError as exc:
        raise self.retry(exc=exc)
```

Test the logic directly, test the task's retry behavior separately.

### Unit Testing with Mocks

```python
from unittest.mock import patch
from celery.exceptions import Retry

class TestSendOrder:
    @patch('proj.tasks.Product.order')
    def test_success(self, mock_order):
        product = Product.objects.create(name='Foo')
        send_order(product.pk, 3, Decimal('30.3'))
        mock_order.assert_called_with(3, Decimal('30.3'))

    @patch('proj.tasks.Product.order')
    @patch('proj.tasks.send_order.retry')
    def test_retry_on_failure(self, mock_retry, mock_order):
        mock_retry.side_effect = Retry()
        mock_order.side_effect = OperationalError()
        product = Product.objects.create(name='Foo')
        with pytest.raises(Retry):
            send_order(product.pk, 3, Decimal('30.6'))
```

### Pytest Plugin Setup

```python
# conftest.py
pytest_plugins = ("celery.contrib.pytest",)
```

Or: `pip install celery[pytest]`

### Key Fixtures

```python
# celery_app — test Celery app instance
# celery_worker — embedded worker in separate thread

def test_task(celery_app, celery_worker):
    @celery_app.task
    def mul(x, y):
        return x * y

    celery_worker.reload()
    assert mul.delay(4, 4).get(timeout=10) == 16
```

### Configuration Fixtures

```python
@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
    }

@pytest.fixture(scope='session')
def celery_includes():
    return ['proj.tasks']

@pytest.fixture(scope='session')
def celery_worker_parameters():
    return {
        'queues': ('high-prio', 'low-prio'),
        'shutdown_timeout': 10,
    }
```

### Per-Test Config Override

```python
@pytest.mark.celery(result_backend='redis://')
def test_with_redis():
    ...
```

### Session-Scoped Worker

```python
def test_add(celery_session_worker):
    assert add.delay(2, 2).get(timeout=10) == 4
```

> Don't mix session and ephemeral workers in the same test suite.

---

## Security

### Serializer Security

```python
# Restrict to safe serializers (default since Celery 4.0)
accept_content = ['json']
```

> **Never accept `pickle`** from untrusted sources — it allows arbitrary code execution.

### Message Signing

```python
app.conf.update(
    security_key='/etc/ssl/private/worker.key',
    security_certificate='/etc/ssl/certs/worker.pem',
    security_cert_store='/etc/ssl/certs/*.pem',
    security_digest='sha256',
    task_serializer='auth',
    event_serializer='auth',
    accept_content=['auth'],
)
app.setup_security()
```

- Uses public-key cryptography to sign (not encrypt) messages
- Prevents unauthorized task submission
- Implement separate encryption if message content is sensitive

### Broker Security

- **Firewall** broker access to whitelisted machines only
- **Use SSL/TLS:** `broker_use_ssl = True`
- **Enable fine-grained ACLs** on RabbitMQ (per-vhost permissions)

### Best Practices

- Always set `accept_content = ['json']` in production
- Use message signing (`auth` serializer) in untrusted networks
- Run workers with least-privilege OS user
- Isolate workers via chroot/containers/VMs for untrusted task code
- Enable SSL for broker connections in production
