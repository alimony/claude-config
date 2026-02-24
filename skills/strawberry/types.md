# Strawberry GraphQL: Types
Based on Strawberry GraphQL 0.306.0 documentation.

## Core Concepts

Strawberry uses Python type annotations and dataclass-style decorators to define a GraphQL schema.
Every GraphQL type maps to a Python class. Strawberry auto-converts Python names (`snake_case`) to
GraphQL names (`camelCase`).

| GraphQL concept | Strawberry decorator / API |
|-----------------|---------------------------|
| Object type | `@strawberry.type` |
| Input type | `@strawberry.input` |
| Interface | `@strawberry.interface` |
| Enum | `@strawberry.enum` |
| Scalar | `@strawberry.scalar` / `strawberry.scalar()` |
| Union | `strawberry.union()` / `Annotated[..., strawberry.union()]` |
| Generic type | `@strawberry.type` on a class extending `Generic[T]` |

---

## Object Types

Define with `@strawberry.type`. All class fields become GraphQL fields automatically.

```python
import strawberry

@strawberry.type
class User:
    name: str
    age: int
```

Produces:

```graphql
type User {
  name: String!
  age: Int!
}
```

### Field options with `strawberry.field()`

```python
@strawberry.type
class User:
    # Custom GraphQL name
    full_name: str = strawberry.field(name="fullName")

    # Description and deprecation
    age: int = strawberry.field(description="Age in years", deprecation_reason="Use birthDate")

    # Default value
    active: bool = strawberry.field(default=True)

    # Resolver (computed field)
    @strawberry.field(description="Greeting message")
    def greeting(self) -> str:
        return f"Hello, {self.name}"
```

### Custom type name and description

```python
@strawberry.type(name="UserProfile", description="A user profile")
class User:
    name: str
```

### Optional / nullable fields

```python
from typing import Optional

@strawberry.type
class User:
    name: str                   # String!  (required / non-null)
    nickname: Optional[str]     # String   (nullable)
    bio: str | None = None      # String   (nullable, Python 3.10+)
```

---

## Resolvers

Resolvers compute field values. Two styles:

### 1. Method resolver (preferred for type fields)

```python
@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

`self` is the instance of the parent type. Strawberry passes the parent object automatically.

### 2. Standalone function resolver

```python
def get_users() -> list[User]:
    return [User(first_name="Ada", last_name="Lovelace")]

@strawberry.type
class Query:
    users: list[User] = strawberry.field(resolver=get_users)
```

When using a standalone resolver, the field on the class is purely declarative — its value
comes entirely from the resolver function.

### Resolver arguments

Arguments to a resolver become GraphQL arguments automatically:

```python
@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID) -> User:
        return get_user_by_id(id)
```

```graphql
type Query {
  user(id: ID!): User!
}
```

### The `info` parameter

Access request context, selected fields, and more via `strawberry.types.Info`:

```python
from strawberry.types import Info

@strawberry.type
class Query:
    @strawberry.field
    def current_user(self, info: Info) -> User:
        return info.context.request.user
```

`info` is injected by name — it is never exposed as a GraphQL argument.

### Resolver with default values

```python
@strawberry.type
class Query:
    @strawberry.field
    def users(self, limit: int = 10, offset: int = 0) -> list[User]:
        return fetch_users(limit=limit, offset=offset)
```

Default values make the argument optional in the schema.

---

## Input Types

Used for mutation arguments. Defined with `@strawberry.input`.

```python
@strawberry.input
class CreateUserInput:
    name: str
    age: int
    email: Optional[str] = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User:
        return User(name=input.name, age=input.age)
```

Produces:

```graphql
input CreateUserInput {
  name: String!
  age: Int!
  email: String
}
```

### OneOf input types

Exactly-one-field-set inputs (useful for search-by-id-or-email patterns):

```python
@strawberry.input(one_of=True)
class UserSearchInput:
    id: Optional[strawberry.ID] = strawberry.UNSET
    email: Optional[str] = strawberry.UNSET
```

### Do / Don't

| Do | Don't |
|----|-------|
| Use `@strawberry.input` for mutation arguments | Reuse `@strawberry.type` objects as inputs |
| Keep inputs flat when possible | Nest deeply without reason |
| Use `Optional` with `= None` for optional fields | Forget the default — it's required for nullable inputs |

---

## Enums

```python
@strawberry.enum
class Color:
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
```

Produces:

```graphql
enum Color {
  RED
  GREEN
  BLUE
}
```

### Descriptions and deprecation on values

```python
@strawberry.enum(description="Available colors")
class Color:
    RED = strawberry.enum_value("red", description="The color red")
    GREEN = strawberry.enum_value("green")
    BLUE = strawberry.enum_value("blue", deprecation_reason="Use GREEN instead")
```

### Using Python's `enum.Enum`

Strawberry enums *are* Python enums. You can also decorate an existing `Enum`:

```python
import enum

@strawberry.enum
class Status(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
```

---

## Scalars

### Built-in scalar mapping

| Python type | GraphQL scalar |
|-------------|---------------|
| `str` | `String` |
| `int` | `Int` |
| `float` | `Float` |
| `bool` | `Boolean` |
| `strawberry.ID` | `ID` |
| `datetime.datetime` | `DateTime` |
| `datetime.date` | `Date` |
| `datetime.time` | `Time` |
| `decimal.Decimal` | `Decimal` |
| `uuid.UUID` | `UUID` |
| `bytes` | `Base64` (base64-encoded string) |

### Custom scalars

#### Class-based (decorator)

```python
import strawberry
from datetime import datetime

@strawberry.scalar(
    name="UnixTimestamp",
    description="Datetime as Unix timestamp (seconds)",
)
class UnixTimestamp:
    @staticmethod
    def serialize(value: datetime) -> int:
        return int(value.timestamp())

    @staticmethod
    def parse_value(value: int) -> datetime:
        return datetime.fromtimestamp(value)
```

#### Function-based (wrapping an existing type)

```python
import strawberry
from typing import NewType

JSON = strawberry.scalar(
    NewType("JSON", object),
    serialize=lambda v: v,
    parse_value=lambda v: v,
    description="Arbitrary JSON value",
)
```

Use the scalar as a type annotation:

```python
@strawberry.type
class Query:
    @strawberry.field
    def config(self) -> JSON:
        return {"key": "value"}
```

### Overriding built-in scalars

Pass `scalar_overrides` when creating the schema:

```python
schema = strawberry.Schema(
    query=Query,
    scalar_overrides={datetime: UnixTimestamp},
)
```

---

## Interfaces

Define shared fields across types. Use `@strawberry.interface`.

```python
@strawberry.interface
class Node:
    id: strawberry.ID

@strawberry.type
class User(Node):
    name: str

@strawberry.type
class Post(Node):
    title: str
```

Produces:

```graphql
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
}

type Post implements Node {
  id: ID!
  title: String!
}
```

### Resolving interface types

When a field returns an interface, Strawberry resolves the concrete type from the Python class.
Return actual instances of implementing types, not the interface class:

```python
@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: strawberry.ID) -> Node:
        # Return a concrete type, not Node()
        return User(id=id, name="Ada")
```

### Interfaces with resolvers

```python
@strawberry.interface
class Timestamped:
    @strawberry.field
    def created_at(self) -> datetime:
        return self._created_at
```

---

## Union Types

Represent "one of several types." Every member must be an object type (not scalars, not inputs).

### Annotated syntax (preferred)

```python
from typing import Annotated, Union

@strawberry.type
class Success:
    message: str

@strawberry.type
class NotFound:
    id: strawberry.ID

Result = Annotated[Union[Success, NotFound], strawberry.union(name="Result")]

@strawberry.type
class Query:
    @strawberry.field
    def result(self) -> Result:
        return Success(message="Found it")
```

### Legacy syntax

```python
Result = strawberry.union("Result", types=[Success, NotFound])
```

### Union as error handling pattern

Return errors as union members instead of raising exceptions:

```python
@strawberry.type
class UserNotFoundError:
    message: str = "User not found"

@strawberry.type
class PermissionError:
    message: str = "Permission denied"

CreateUserResult = Annotated[
    Union[User, UserNotFoundError, PermissionError],
    strawberry.union(name="CreateUserResult"),
]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> CreateUserResult:
        if not has_permission():
            return PermissionError()
        return User(name=input.name, age=input.age)
```

Query with inline fragments:

```graphql
mutation {
  createUser(input: { name: "Ada", age: 36 }) {
    ... on User { name }
    ... on UserNotFoundError { message }
    ... on PermissionError { message }
  }
}
```

---

## Generics

Create reusable type templates using Python generics.

```python
from typing import Generic, TypeVar

T = TypeVar("T")

@strawberry.type
class Connection(Generic[T]):
    nodes: list[T]
    total_count: int

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> Connection[User]:
        return Connection(nodes=[User(name="Ada", age=36)], total_count=1)
```

Strawberry generates a concrete type name: `UserConnection`.

### Generic inputs

```python
T = TypeVar("T")

@strawberry.input
class Pagination(Generic[T]):
    cursor: Optional[str] = None
    limit: int = 10
```

### Multiple type variables

```python
T = TypeVar("T")
E = TypeVar("E")

@strawberry.type
class ResultType(Generic[T, E]):
    value: Optional[T] = None
    error: Optional[E] = None
```

### Naming

Strawberry auto-generates names by prepending the concrete type: `Connection[User]` becomes
`UserConnection`. Override with `name` parameter if needed.

---

## Lazy Types

Solve circular import issues between types in different modules.

### Problem

```python
# user.py
from .post import Post  # Circular!

@strawberry.type
class User:
    posts: list[Post]
```

### Solution: `strawberry.lazy()`

```python
# user.py
from typing import Annotated, TYPE_CHECKING
import strawberry

if TYPE_CHECKING:
    from .post import Post

@strawberry.type
class User:
    @strawberry.field
    def posts(self) -> list[Annotated["Post", strawberry.lazy(".post")]]:
        return get_posts_for_user(self.id)
```

The string argument to `strawberry.lazy()` is a **module path** (relative or absolute), not a
class name. Strawberry resolves the type at schema-build time.

### Key rules

- The `Annotated` type hint must use a **string** forward reference for the type name (`"Post"`)
- The `strawberry.lazy()` argument is the **module** that contains the type (e.g., `".post"`)
- Use `TYPE_CHECKING` guard for IDE support without runtime circular imports

---

## Private Fields

Fields that exist on the Python class but are **not** exposed in the GraphQL schema.
Use `strawberry.Private`.

```python
import strawberry

@strawberry.type
class User:
    name: str
    age: int
    # This field is NOT in the GraphQL schema
    password_hash: strawberry.Private[str]
```

`password_hash` is accessible in Python (e.g., in resolvers) but invisible to GraphQL clients.

### When to use Private

- Internal state needed by resolvers (database IDs, cached values)
- Sensitive data that should never be queried
- Helper data passed between parent and child resolvers

```python
@strawberry.type
class User:
    name: str
    _db_row: strawberry.Private[dict]  # raw DB data, not exposed

    @strawberry.field
    def email(self) -> str:
        return self._db_row["email"]
```

---

## Handling Errors as Types (Expected Errors)

Rather than relying on GraphQL's top-level `errors` array, model expected errors as union
members. This gives clients typed, predictable error handling.

### Pattern: union-based result types

```python
@strawberry.type
class CreateUserSuccess:
    user: User

@strawberry.type
class UsernameAlreadyTaken:
    message: str = "Username is already taken"
    suggested: list[str] = strawberry.field(default_factory=list)

@strawberry.type
class InvalidInput:
    field: str
    message: str

CreateUserResult = Annotated[
    Union[CreateUserSuccess, UsernameAlreadyTaken, InvalidInput],
    strawberry.union(name="CreateUserResult"),
]
```

### When to use which error style

| Scenario | Approach |
|----------|----------|
| Expected business errors (validation, not found, permission) | Union-based result types |
| Unexpected errors (server crash, DB down) | Let them become top-level `errors` |
| Authentication failures | Top-level errors or middleware |

---

## @defer and @stream

Incremental delivery directives for large responses. **Experimental / spec draft.**

### @defer

Delays delivery of a fragment. The server sends the rest of the response first, then streams
the deferred fragment:

```graphql
query {
  user(id: "1") {
    name
    ... @defer {
      expensiveField
    }
  }
}
```

No special Python code needed — Strawberry supports `@defer` if the integration layer
(ASGI, etc.) supports streaming responses.

### @stream

Streams list items incrementally instead of waiting for the entire list:

```graphql
query {
  users @stream(initialCount: 2) {
    name
  }
}
```

Returns the first 2 items immediately, then streams the rest.

### Requirements

- Must use an async integration that supports streaming (e.g., ASGI with `StreamingResponse`)
- Schema must be built with `schema = strawberry.Schema(query=Query)` (no special config)
- Client must support incremental delivery (multipart responses)

---

## Quick Reference: Type Decorators

| Decorator | Creates | Key differences |
|-----------|---------|----------------|
| `@strawberry.type` | Object type | Can have resolvers, used for output |
| `@strawberry.input` | Input type | For mutation arguments, no resolvers |
| `@strawberry.interface` | Interface | Abstract, must be subclassed |
| `@strawberry.enum` | Enum | Values are enum members |
| `@strawberry.scalar` | Custom scalar | Serialize/parse between Python and GraphQL |

## Quick Reference: Field Configuration

```python
strawberry.field(
    name="graphqlName",              # Override auto camelCase name
    description="Field docs",        # Shows in schema introspection
    deprecation_reason="Use X",      # Marks field as deprecated
    default=value,                   # Default value
    default_factory=list,            # Default factory (like dataclass)
    resolver=some_function,          # External resolver function
    permission_classes=[IsAuth],     # Permission checks
)
```

## Common Pitfalls

1. **Forgetting `Optional` for nullable fields.** All fields are non-null (`!`) by default.
   Use `Optional[str]` or `str | None` to make them nullable.

2. **Reusing object types as inputs.** GraphQL requires separate `type` and `input` definitions.
   Create a dedicated `@strawberry.input` class even if the fields are identical.

3. **Circular imports.** Use `strawberry.lazy()` with `Annotated` and `TYPE_CHECKING` to break
   cycles. Do not try to hack around it with late imports in resolvers.

4. **Union members must be object types.** You cannot put scalars (`str`, `int`) or input types
   in a union. Wrap them: `@strawberry.type class StringResult: value: str`.

5. **Standalone resolvers lose `self`.** When using `strawberry.field(resolver=fn)`, the function
   does NOT receive `self` (the parent instance). If you need parent data, use a method resolver.

6. **Enum values in Python vs GraphQL.** Strawberry enum values are accessed as Python enum
   members (`Color.RED`), but in GraphQL queries they appear as plain names (`RED`).

7. **Generic type naming collisions.** `Connection[User]` and `Connection[Post]` auto-generate
   `UserConnection` and `PostConnection`. If you use the same generic with the same concrete
   type in different contexts, you may get name collisions. Use `name` parameter to disambiguate.

8. **Private fields need a value at construction.** Since `strawberry.Private[T]` fields exist
   on the Python object, you must provide them when instantiating, even though they are not
   in the schema.

9. **`strawberry.lazy()` takes a module path, not a class name.** The argument is like an
   import path: `".post"` not `"Post"`.

10. **`info` parameter naming.** The resolver parameter must be named exactly `info` for
    Strawberry to inject it. Any other name and it becomes a GraphQL argument.
