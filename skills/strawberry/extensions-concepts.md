# Strawberry GraphQL: Extensions & Concepts
Based on Strawberry GraphQL 0.306.0 documentation.

## Schema Extensions

Extensions customize the GraphQL execution flow. Pass them to `strawberry.Schema(extensions=[...])`.

### Built-in Extensions

| Category | Extension | Purpose |
|----------|-----------|---------|
| **Security** | `DisableIntrospection` | Block introspection queries |
| | `MaskErrors` | Hide error details from clients |
| | `MaxAliasesLimiter` | Limit alias count |
| | `MaxTokensLimiter` | Limit query token count |
| | `QueryDepthLimiter` | Restrict query nesting depth |
| **Tracing** | `ApolloTracingExtension` | Apollo tracing |
| | `DatadogTracingExtension` | Datadog APM |
| | `OpenTelemetryExtension` | OpenTelemetry spans |
| | `SentryTracingExtension` | Sentry error tracking |
| | `PyInstrumentExtension` | Profiling |
| **Performance** | `ParserCache` | Cache parsed queries |
| | `ValidationCache` | Cache validation results |
| | `DisableValidation` | Skip query validation |
| **Utility** | `AddValidationRules` | Custom GraphQL validation rules |
| | `InputMutationExtension` | Auto-generate input types for mutations |

### Creating Custom Schema Extensions

Extend `SchemaExtension` and implement lifecycle hooks:

```python
from strawberry.extensions import SchemaExtension

class MyExtension(SchemaExtension):
    def on_operation(self):
        print("operation start")
        yield
        print("operation end")

    def on_parse(self):
        yield  # code before/after parsing

    def on_validate(self):
        yield  # code before/after validation

    def on_execute(self):
        yield  # code before/after execution

    def resolve(self, _next, root, info, *args, **kwargs):
        # Wraps ALL resolver calls
        return _next(root, info, *args, **kwargs)

    def get_results(self):
        # Add data to the response extensions
        return {"timing": self.elapsed}

schema = strawberry.Schema(query=Query, extensions=[MyExtension])
```

### Lifecycle hook pattern

Hooks use generator syntax — code before `yield` runs at the start, after `yield` at the end:

```python
class TimingExtension(SchemaExtension):
    def on_execute(self):
        start = time.time()
        yield
        elapsed = time.time() - start
        self.execution_context.extensions_results["timing"] = elapsed
```

### Execution context

Access request data and results via `self.execution_context`:

```python
class DBSessionExtension(SchemaExtension):
    def on_operation(self):
        self.execution_context.context["db"] = get_db_session()
        yield
        self.execution_context.context["db"].close()
```

### Practical examples

**In-memory query cache:**
```python
response_cache = {}

class ExecutionCache(SchemaExtension):
    def on_execute(self):
        ctx = self.execution_context
        key = f"{ctx.query}:{json.dumps(ctx.variables)}"
        if key in response_cache:
            ctx.result = response_cache[key]
        yield
        if key not in response_cache:
            response_cache[key] = ctx.result
```

**Reject specific queries:**
```python
class RejectQueries(SchemaExtension):
    def on_execute(self):
        if self.execution_context.operation_name == "IntrospectionQuery":
            self.execution_context.result = GraphQLExecutionResult(
                data=None, errors=[GraphQLError("Not allowed")]
            )
```

---

## Field Extensions

Reusable logic that wraps individual field resolvers. Inherit from `FieldExtension`:

```python
from strawberry.extensions import FieldExtension

class UpperCaseExtension(FieldExtension):
    def resolve(self, next_, source, info, **kwargs):
        result = next_(source, info, **kwargs)
        return str(result).upper()

@strawberry.type
class Query:
    @strawberry.field(extensions=[UpperCaseExtension()])
    def greeting(self) -> str:
        return "hello"
```

### Modifying fields at schema build time

Override `apply()` to add directives or modify field metadata:

```python
class CachingExtension(FieldExtension):
    def __init__(self, ttl=100):
        self.ttl = ttl
        self.cached_result = None
        self.last_cached = 0.0

    def apply(self, field):
        field.directives.append(Cached(time=self.ttl))

    def resolve(self, next_, source, info, **kwargs):
        if time.time() < self.last_cached + self.ttl:
            return self.cached_result
        self.cached_result = next_(source, info, **kwargs)
        self.last_cached = time.time()
        return self.cached_result
```

### Chaining extensions

Multiple extensions execute in **reverse order** — last in the list runs first:

```python
@strawberry.field(extensions=[LowerCase(), UpperCase()])
# UpperCase runs first, then LowerCase
```

### Async support

Implement `resolve_async` for async resolvers:

```python
class MyExtension(FieldExtension):
    def resolve(self, next_, source, info, **kwargs):
        return next_(source, info, **kwargs)

    async def resolve_async(self, next_, source, info, **kwargs):
        return await next_(source, info, **kwargs)
```

Sync-only extensions cannot wrap async resolvers. Async extensions can wrap sync resolvers (auto-converted).

---

## Async Support

Strawberry fully supports async resolvers. Mix sync and async in the same schema:

```python
import asyncio

@strawberry.type
class Query:
    @strawberry.field
    def sync_field(self) -> str:
        return "sync"

    @strawberry.field
    async def async_field(self) -> str:
        await asyncio.sleep(0.1)
        return "async"
```

### When to use async

- **ASGI frameworks** (FastAPI, Starlette, ASGI) — use async to avoid blocking the event loop
- **DataLoaders** — require async
- **External API calls** — async avoids blocking
- **Django** — use `AsyncGraphQLView` with async resolvers, or wrap sync ORM calls with `sync_to_async`

### Standalone async resolvers

```python
async def resolve_hello(root) -> str:
    await asyncio.sleep(1)
    return "Hello world"

@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=resolve_hello)
```

---

## Tracing

### Apollo Tracing

```python
from strawberry.extensions.tracing import ApolloTracingExtension
schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])
# Sync variant: ApolloTracingExtensionSync
```

### Datadog

```python
from strawberry.extensions.tracing import DatadogTracingExtension
schema = strawberry.Schema(query=Query, extensions=[DatadogTracingExtension])
# Sync variant: DatadogTracingExtensionSync
```

### OpenTelemetry

```bash
pip install 'strawberry-graphql[opentelemetry]'
```

```python
from strawberry.extensions.tracing import OpenTelemetryExtension
schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
```

---

## Common Pitfalls

- **Extension order matters.** Extensions execute in list order for lifecycle hooks, but field extensions chain in reverse.
- **Sync extensions in async contexts.** Schema extensions work in both contexts, but sync-only field extensions fail with async resolvers.
- **`resolve` hook runs for ALL fields.** Including built-in and framework fields. Filter on `info.field_name` if needed.
- **Caching extensions bypass auth.** If you cache results, ensure permission checks still run.
