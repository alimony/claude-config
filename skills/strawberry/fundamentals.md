# Strawberry GraphQL: Fundamentals
Based on Strawberry GraphQL 0.306.0 documentation.

## Core Philosophy

Strawberry is a **code-first** Python GraphQL framework built on dataclasses and type hints. Python types map directly to GraphQL schema — no separate SDL files needed.

- Requires Python 3.10+
- Snake_case automatically converts to camelCase in the schema (configurable)
- Type annotations drive schema generation

## Defining Types

### Object Types

```python
import strawberry
import typing

@strawberry.type
class Author:
    name: str
    books: typing.List["Book"]

@strawberry.type
class Book:
    title: str
    author: Author
```

### Scalar Type Mapping

| Python Type | GraphQL Type | Notes |
|-------------|-------------|-------|
| `str` | `String` | |
| `int` | `Int` | 32-bit signed |
| `float` | `Float` | Double precision |
| `bool` | `Boolean` | |
| `strawberry.ID` | `ID` | Unique identifier |
| `uuid.UUID` | `UUID` | Serialized as string |
| `datetime.date` | `Date` | ISO-8601 |
| `datetime.time` | `Time` | ISO-8601 |
| `datetime.datetime` | `DateTime` | ISO-8601 |

### Input Types

Input types are separate from object types (GraphQL spec requirement — you cannot reuse object types as inputs):

```python
@strawberry.input
class AddBookInput:
    title: str = strawberry.field(description="The title of the book")
    author: str = strawberry.field(description="The name of the author")
```

## Queries

Define queries as a class with `@strawberry.type`. All fields become queryable:

```python
@strawberry.type
class Query:
    @strawberry.field
    def name(self) -> str:
        return "Strawberry"
```

### Resolvers — Two Styles

**Decorator style** (preferred for simple resolvers):
```python
@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> list[Book]:
        return fetch_books()
```

**External resolver** (useful for separating data-fetching logic):
```python
def get_books() -> list[Book]:
    return fetch_books()

@strawberry.type
class Query:
    books: list[Book] = strawberry.field(resolver=get_books)
```

### Arguments

Arguments are defined as resolver parameters:

```python
@strawberry.type
class Query:
    @strawberry.field
    def fruit(self, startswith: str) -> str | None:
        # Filter logic
        return None
```

Add descriptions with `Annotated`:

```python
from typing import Annotated

@strawberry.type
class Query:
    @strawberry.field
    def fruit(
        self,
        startswith: Annotated[
            str, strawberry.argument(description="Prefix to filter fruits by.")
        ],
    ) -> str | None:
        pass
```

### Type Conversion

When the Python return type differs from the desired GraphQL type:

```python
@strawberry.type
class Query:
    @strawberry.field(graphql_type=UserType)
    def user(self) -> User:
        return User(id="ringo", name="Ringo")
```

## Mutations

Mutations modify server-side data. Define with `@strawberry.mutation`:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_book(self, title: str, author: str) -> Book:
        print(f"Adding {title} by {author}")
        return Book(title=title, author=author)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### Mutations Without Return Values

```python
@strawberry.mutation
def restart() -> None:
    print("Restarting the server")
```

Maps to a `Void` scalar (returns `null`). Note: returning nothing from mutations goes against GraphQL best practices — prefer returning the affected object or a result type.

### Input Mutation Extension

Automatically generates an input type from resolver arguments:

```python
from strawberry.field_extensions import InputMutationExtension

@strawberry.mutation(extensions=[InputMutationExtension()])
def update_fruit_weight(
    self,
    info: strawberry.Info,
    id: strawberry.ID,
    weight: Annotated[
        float,
        strawberry.argument(description="The fruit's new weight in grams"),
    ],
) -> Fruit:
    fruit = ...  # retrieve fruit
    fruit.weight = weight
    return fruit
```

Generates:
```graphql
input UpdateFruitWeightInput {
  id: ID!
  weight: Float!
}
type Mutation {
  updateFruitWeight(input: UpdateFruitWeightInput!): Fruit!
}
```

### Nested Mutations

Group related mutations under a namespace:

```python
@strawberry.type
class FruitMutations:
    @strawberry.mutation
    def add(self, info, input: AddFruitInput) -> Fruit: ...

    @strawberry.mutation
    def update_weight(self, info, input: UpdateFruitWeightInput) -> Fruit: ...

@strawberry.type
class Mutation:
    @strawberry.field
    def fruit(self) -> FruitMutations:
        return FruitMutations()
```

**Caveat:** Root mutation fields execute serially per the GraphQL spec, but nested mutations may resolve asynchronously. Use client-side aliases to guarantee serial execution when needed.

## Subscriptions

Subscriptions stream real-time data. Require ASGI with WebSocket support or AIOHTTP.

```python
import asyncio
from typing import AsyncGenerator
import strawberry

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)
```

### WebSocket Protocols

| Protocol | Status | Notes |
|----------|--------|-------|
| `graphql-transport-ws` | Recommended | Modern protocol |
| `graphql-ws` | Legacy | Backward compatibility |

Configure per framework:
```python
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

graphql_router = GraphQLRouter(
    schema,
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL],
)
```

### Authentication in Subscriptions

Browsers cannot set custom WebSocket headers. Pass auth via connection params:

```python
@strawberry.subscription
async def count(self, info: strawberry.Info) -> AsyncGenerator[int, None]:
    connection_params = info.context.get("connection_params")
    token = connection_params.get("authToken")
    if not authenticate_token(token):
        raise Exception("Forbidden!")
    # ... yield data
```

### Handling Client Disconnection

```python
@strawberry.subscription
async def messages(self) -> AsyncGenerator[str, None]:
    try:
        subscription_id = uuid4()
        while True:
            # yield messages...
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        # Clean up resources on disconnect
        pass
```

### Multipart Subscriptions

Alternative protocol for subscriptions over HTTP (no WebSocket needed). Automatically enabled when using `Subscription` — no additional configuration required. Supported by Django (async), ASGI, Litestar, FastAPI, AioHTTP, and Quart.

## Building the Schema

```python
schema = strawberry.Schema(query=Query)
schema = strawberry.Schema(query=Query, mutation=Mutation)
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
```

Run the development server:
```bash
strawberry server schema  # or: strawberry dev schema (with auto-reload)
```

## Common Pitfalls

- **Cannot reuse object types as inputs.** The GraphQL spec requires separate `@strawberry.type` and `@strawberry.input` definitions.
- **Circular imports.** Use `strawberry.lazy` with `Annotated` to break cycles:
  ```python
  from typing import TYPE_CHECKING, Annotated
  if TYPE_CHECKING:
      from .users import User

  @strawberry.type
  class Post:
      title: str
      author: Annotated["User", strawberry.lazy(".users")]
  ```
- **Private fields.** Use `strawberry.Private[T]` to keep fields out of the schema:
  ```python
  @strawberry.type
  class User:
      name: str
      password: strawberry.Private[str]
  ```
- **Missing return type annotations.** Strawberry requires explicit return types on resolvers — it will error with a helpful message if you forget.
- **Void mutations.** Returning `None` from mutations works but is considered a GraphQL anti-pattern. Prefer returning the modified object.

## Error Reporting

Strawberry provides rich error output with file locations, code context, and fix suggestions. Requires CLI extras:

```bash
pip install "strawberry-graphql[cli]"
```

Disable with `STRAWBERRY_DISABLE_RICH_ERRORS=1` environment variable.
