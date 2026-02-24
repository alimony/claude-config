# Strawberry GraphQL: Operations & Tooling
Based on Strawberry GraphQL 0.306.0 documentation.

## Testing

### Synchronous tests

```python
def test_query():
    result = schema.execute_sync(
        """
        query TestQuery($title: String!) {
            books(title: $title) {
                title
                author
            }
        }
        """,
        variable_values={"title": "The Great Gatsby"},
    )
    assert result.errors is None
    assert result.data["books"] == [
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"}
    ]
```

### Async tests

```python
import pytest

@pytest.mark.asyncio
async def test_query_async():
    result = await schema.execute(
        "query { hello }",
        variable_values={"name": "World"},
    )
    assert result.errors is None
    assert result.data == {"hello": "Hello World"}
```

### Testing mutations

```python
@pytest.mark.asyncio
async def test_mutation():
    result = await schema.execute(
        """
        mutation($title: String!, $author: String!) {
            addBook(title: $title, author: $author) { title }
        }
        """,
        variable_values={"title": "The Little Prince", "author": "Saint-Exupéry"},
    )
    assert result.errors is None
    assert result.data["addBook"]["title"] == "The Little Prince"
```

### Testing subscriptions

```python
@pytest.mark.asyncio
async def test_subscription():
    sub = await schema.subscribe("subscription { count(target: 3) }")
    results = []
    async for result in sub:
        assert not result.errors
        results.append(result.data["count"])
    assert results == [0, 1, 2]
```

### Testing with context

```python
result = schema.execute_sync(
    "query { currentUser { name } }",
    context_value={"request": mock_request},
)
```

### Key patterns

- Use `variable_values` instead of string interpolation
- Check `result.errors is None` before asserting on `result.data`
- For async resolvers, use `schema.execute()` with `@pytest.mark.asyncio`
- For subscriptions, use `schema.subscribe()` and iterate async

---

## Deployment

### Production Checklist

**Disable GraphiQL** — exposes schema to unauthorized users:
```python
GraphQLView.as_view(schema=schema, graphql_ide=None)
# or
GraphQLRouter(schema, graphql_ide=None)
```

**Disable introspection** — prevents schema discovery:
```python
from strawberry.extensions import DisableIntrospection

schema = strawberry.Schema(query=Query, extensions=[DisableIntrospection()])
```

### Security extensions

```python
from strawberry.extensions import (
    QueryDepthLimiter,
    MaxAliasesLimiter,
    MaxTokensLimiter,
)

schema = strawberry.Schema(
    query=Query,
    extensions=[
        QueryDepthLimiter(max_depth=10),
        MaxAliasesLimiter(max_alias_count=15),
        MaxTokensLimiter(max_token_count=1000),
    ],
)
```

### Performance extensions

```python
from strawberry.extensions import ParserCache, ValidationCache

schema = strawberry.Schema(
    query=Query,
    extensions=[ParserCache(), ValidationCache()],
)
```

---

## Tracing

### Apollo Tracing

```python
from strawberry.extensions.tracing import ApolloTracingExtension
schema = strawberry.Schema(query=Query, extensions=[ApolloTracingExtension])
```

### Datadog

```python
from strawberry.extensions.tracing import DatadogTracingExtension
schema = strawberry.Schema(query=Query, extensions=[DatadogTracingExtension])
```

### OpenTelemetry

```bash
pip install 'strawberry-graphql[opentelemetry]'
```

```python
from strawberry.extensions.tracing import OpenTelemetryExtension
schema = strawberry.Schema(query=Query, extensions=[OpenTelemetryExtension])
```

For non-ASGI (sync), use `*Sync` variants: `ApolloTracingExtensionSync`, `DatadogTracingExtensionSync`.

---

## Schema Export (Code Generation)

Export your schema to SDL for IDE plugins and codegen tools:

```bash
# Print to stdout
strawberry export-schema myapp.schema:schema

# Save to file
strawberry export-schema myapp.schema:schema --output schema.graphql

# Or with shell redirect
strawberry export-schema myapp.schema:schema > schema.graphql
```

The argument format is `module.path:symbol` where `symbol` defaults to `schema`.

Requires: `pip install "strawberry-graphql[cli]"`

---

## CLI Commands

```bash
strawberry server myapp.schema     # Start production server
strawberry dev myapp.schema        # Start dev server with auto-reload
strawberry export-schema myapp     # Export SDL
```

## Common Pitfalls

- **Testing without context.** If resolvers use `info.context`, pass `context_value` in tests.
- **Forgetting to disable GraphiQL in production.** Set `graphql_ide=None` to prevent schema exposure.
- **Using sync tracing with ASGI.** Use the async tracing extensions (without `Sync` suffix) for ASGI frameworks.
- **Schema export needs CLI package.** Install `strawberry-graphql[cli]` for the `strawberry` command.
