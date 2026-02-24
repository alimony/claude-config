# Strawberry GraphQL: Schema & Configuration
Based on Strawberry GraphQL 0.306.0 documentation.

## Creating a Schema

```python
import strawberry

schema = strawberry.Schema(query=Query)
schema = strawberry.Schema(query=Query, mutation=Mutation)
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
```

### Schema Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | Type | Yes | Root query type |
| `mutation` | Type | No | Root mutation type |
| `subscription` | Type | No | Root subscription type |
| `config` | StrawberryConfig | No | Schema configuration |
| `types` | list[Type] | No | Extra types to register (needed for interface implementations) |
| `extensions` | list[SchemaExtension] | No | Schema extensions |
| `scalar_overrides` | dict | No | Override built-in scalar implementations |

### Registering Extra Types

When using interfaces or unions, register all implementing types explicitly:

```python
@strawberry.interface
class Customer:
    name: str

@strawberry.type
class Individual(Customer):
    date_of_birth: date

@strawberry.type
class Company(Customer):
    founded: date

# Must register concrete types so the schema knows about them
schema = strawberry.Schema(Query, types=[Individual, Company])
```

## StrawberryConfig

```python
from strawberry.schema.config import StrawberryConfig

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        auto_camel_case=True,           # Default: snake_case → camelCase
        default_resolver=getattr,        # Default resolver function
        relay_max_results=100,           # Default max for Relay connections
        disable_field_suggestions=False, # Disable field name suggestions in errors
    ),
)
```

### auto_camel_case

Enabled by default. Converts `example_field` → `exampleField` in the schema. Disable to preserve snake_case:

```python
config = StrawberryConfig(auto_camel_case=False)
```

### default_resolver

Default is `getattr`. Override for dict-based data sources:

```python
def custom_resolver(obj, field):
    try:
        return obj[field]
    except (KeyError, TypeError):
        return getattr(obj, field)

config = StrawberryConfig(default_resolver=custom_resolver)
```

### Experimental Incremental Execution

Enable `@defer` and `@stream` support (requires graphql-core>=3.3.0a9):

```python
config = StrawberryConfig(enable_experimental_incremental_execution=True)
```

## Query Batching

Disabled by default. Enable to allow clients to send multiple operations in a single HTTP request:

```python
config = StrawberryConfig(batching_config={"max_operations": 10})
```

Client sends an array of operations:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '[{"query": "{ hello }"}, {"query": "{ world }"}]' \
  http://localhost:8000/graphql
```

Returns an array of results. Multipart subscriptions are not supported in batch requests.

## Executing Queries Programmatically

### Synchronous

```python
result = schema.execute_sync(
    "query { hello }",
    variable_values={"name": "World"},
    context_value={"request": request},
)
# result.data, result.errors
```

### Asynchronous

```python
result = await schema.execute(
    "query { hello }",
    variable_values={"name": "World"},
    context_value={"request": request},
)
```

## Custom Error Processing

Override `process_errors` to customize error logging:

```python
from graphql import GraphQLError
from strawberry.types import ExecutionContext

class CustomSchema(strawberry.Schema):
    def process_errors(
        self,
        errors: list[GraphQLError],
        execution_context: ExecutionContext | None = None,
    ) -> None:
        for error in errors:
            logger.error(error.message, exc_info=error.original_error)
```

## Field Filtering

Subclass Schema to conditionally expose fields:

```python
@strawberry.type
class User:
    name: str
    email: str = strawberry.field(metadata={"tags": ["internal"]})

class PublicSchema(strawberry.Schema):
    def get_fields(self, type_definition):
        return [f for f in type_definition.fields if "internal" not in f.metadata.get("tags", [])]
```

## Schema Directives

Add metadata to schema types without changing behavior:

```python
from strawberry.schema_directive import Location

@strawberry.schema_directive(locations=[Location.OBJECT])
class CacheControl:
    max_age: int

@strawberry.type(directives=[CacheControl(max_age=300)])
class User:
    name: str
```

Produces: `type User @cacheControl(maxAge: 300) { name: String! }`

### Supported Directive Locations

SCHEMA, SCALAR, OBJECT, FIELD_DEFINITION, ARGUMENT_DEFINITION, INTERFACE, UNION, ENUM, ENUM_VALUE, INPUT_OBJECT, INPUT_FIELD_DEFINITION.

## Operation Directives

Built-in: `@skip(if: Boolean!)` and `@include(if: Boolean!)`.

### Custom Operation Directives

```python
from strawberry.directive import DirectiveLocation

@strawberry.directive(locations=[DirectiveLocation.FIELD])
def uppercase(value: str):
    return value.upper()

@strawberry.directive(locations=[DirectiveLocation.FIELD])
def replace(value: str, old: str, new: str):
    return value.replace(old, new)
```

Usage in queries:
```graphql
query {
  person { name @uppercase }
  other: person { name @replace(old: "Jess", new: "Jessica") }
}
```

## Schema Export

Export to SDL format for IDE plugins and code generation:

```bash
strawberry export-schema package.module:schema > schema.graphql
# or
strawberry export-schema package.module:schema --output schema.graphql
```

Requires `pip install "strawberry-graphql[cli]"`.

## Common Pitfalls

- **Forgetting to register interface implementations.** If a field returns an interface type, all implementing types must be in `types=[...]` or Strawberry can't resolve `__typename`.
- **Blocking the event loop.** Using sync resolvers with ASGI blocks the entire worker. Use async resolvers or `sync_to_async` wrappers.
- **Schema export requires CLI extras.** `strawberry export-schema` needs `strawberry-graphql[cli]`.
