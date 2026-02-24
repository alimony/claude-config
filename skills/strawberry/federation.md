# Strawberry GraphQL: Federation
Based on Strawberry GraphQL 0.306.0 documentation.

## Overview

Strawberry provides built-in Apollo Federation support for creating federated GraphQL subgraphs that work with Apollo Gateway or Apollo Router.

## Defining Entities

Entities are types that can be referenced and extended across subgraphs. Define with `@strawberry.federation.type` and a `keys` parameter:

```python
import strawberry

@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str
```

Produces:
```graphql
type Book @key(fields: "id") {
  id: ID!
  title: String!
}
```

### Alternative: Using Key directive directly

```python
from strawberry.federation.schema_directives import Key

@strawberry.type(directives=[Key(fields="id")])
class Book:
    id: strawberry.ID
    title: str
```

## Resolving References

When Apollo Router queries your subgraph for an entity, it calls `resolve_reference`:

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Book":
        return Book(id=id, title=fetch_title(id))
```

**Default behavior:** If you omit `resolve_reference`, Strawberry auto-instantiates the entity using the key data. This works if resolvers on the type can compute all other fields:

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    reviews_count: int = strawberry.field(resolver=lambda: 3)
    # No resolve_reference needed — Strawberry creates Book(id=...) automatically
```

## Federation Decorators

| Decorator | Purpose |
|-----------|---------|
| `@strawberry.federation.type(keys=[...])` | Define an entity type |
| `@strawberry.federation.interface(keys=[...])` | Define an entity interface |
| `@strawberry.federation.interface_object(keys=[...])` | Extend an entity interface from another subgraph |

## Entity Interfaces

Define shared interfaces across subgraphs:

```python
@strawberry.federation.interface(keys=["id"])
class Media:
    id: strawberry.ID
```

### Extending interfaces from other subgraphs

Use `@interface_object` to add fields to an interface defined elsewhere — avoids needing to know all implementing types:

```python
@strawberry.federation.interface_object(keys=["id"])
class Media:
    id: strawberry.ID
    title: str  # Added by this subgraph

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Media":
        return Media(id=id, title=fetch_title(id))
```

## Federation Schema

Use `strawberry.federation.Schema` instead of `strawberry.Schema`:

```python
schema = strawberry.federation.Schema(query=Query)
schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    types=[Book, Author],  # Register all entity types
)
```

## Federation Field Directives

Mark fields with federation-specific directives:

```python
@strawberry.federation.type(keys=["id"])
class Product:
    id: strawberry.ID
    name: str
    # Fields provided by this subgraph
    weight: float = strawberry.federation.field(external=False)

    # Fields defined in another subgraph, referenced here
    price: float = strawberry.federation.field(external=True)

    # Computed from external fields
    @strawberry.federation.field(requires=["price", "weight"])
    def shipping_estimate(self) -> float:
        return self.price * self.weight * 0.1
```

### Field directive options

| Option | Description |
|--------|-------------|
| `external=True` | Field is defined in another subgraph |
| `requires=[...]` | Needs these external fields to resolve |
| `provides=[...]` | Provides these fields from a nested entity |
| `shareable=True` | Multiple subgraphs can resolve this field |
| `inaccessible=True` | Hidden from the supergraph |
| `override="subgraph"` | Takes ownership from another subgraph |

## Common Pitfalls

- **Must use `strawberry.federation.Schema`.** Regular `strawberry.Schema` doesn't add federation directives (`_entities`, `_service`).
- **Register all entity types.** Pass them in `types=[...]` so the schema knows about them.
- **`resolve_reference` receives only key fields.** Don't expect the full object — fetch additional data from your data source.
- **Composite keys.** Use `keys=["id organizationId"]` (space-separated in a single string) for compound keys.
