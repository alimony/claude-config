# Strawberry GraphQL: Guides & Patterns
Based on Strawberry GraphQL 0.306.0 documentation.

## Accessing Parent Data

### Method resolvers — use `self`

```python
@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

### Function resolvers — use `strawberry.Parent`

```python
def get_full_name(parent: strawberry.Parent[User]) -> str:
    return f"{parent.first_name} {parent.last_name}"

@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=get_full_name)
```

### Static method resolvers (explicit, type-checker friendly)

```python
@strawberry.type
class User:
    @strawberry.field
    @staticmethod
    def full_name(parent: strawberry.Parent[User]) -> str:
        return f"{parent.first_name} {parent.last_name}"
```

---

## Authentication

Authentication is handled by your web framework. Strawberry handles **authorization** via permissions.

### Login mutation with union result types

```python
@strawberry.type
class LoginSuccess:
    user: User

@strawberry.type
class LoginError:
    message: str

LoginResult = Annotated[Union[LoginSuccess, LoginError], strawberry.union("LoginResult")]

@strawberry.type
class Mutation:
    @strawberry.field
    def login(self, username: str, password: str) -> LoginResult:
        user = auth_service.login(username, password)
        if user is None:
            return LoginError(message="Invalid credentials")
        return LoginSuccess(user=User(username=username))
```

### Accessing the authenticated user via custom context

```python
from functools import cached_property
from strawberry.fastapi import BaseContext

class Context(BaseContext):
    @cached_property
    def user(self) -> User | None:
        if not self.request:
            return None
        auth = self.request.headers.get("Authorization")
        return auth_service.authorize(auth)

@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: strawberry.Info[Context]) -> User | None:
        return info.context.user
```

---

## Permissions

Permission classes control field access. Extend `BasePermission`:

```python
from strawberry.permission import BasePermission

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source, info: strawberry.Info, **kwargs) -> bool:
        request = info.context["request"]
        return "Authorization" in request.headers

@strawberry.type
class Query:
    user: str = strawberry.field(permission_classes=[IsAuthenticated])
```

### Custom error extensions

```python
class IsAuthenticated(BasePermission):
    message = "User is not authenticated"
    error_extensions = {"code": "UNAUTHORIZED"}
```

### Silent failure (return None instead of error)

```python
from strawberry.permission import PermissionExtension

@strawberry.type
class Query:
    @strawberry.field(
        extensions=[PermissionExtension(permissions=[IsAuthenticated()], fail_silently=True)]
    )
    def name(self) -> str | None:
        return "secret"
```

Only works with nullable or list return types.

---

## DataLoaders

Reduce N+1 queries by batching and caching. Require async context.

### Define a batch loader

```python
from strawberry.dataloader import DataLoader

async def load_users(keys: list[int]) -> list[User]:
    return [User(id=key) for key in keys]

loader = DataLoader(load_fn=load_users)
```

### Use in resolvers

```python
user = await loader.load(1)
users = await loader.load_many([1, 2, 3])
```

### Per-request DataLoader (recommended for servers)

```python
class MyGraphQL(GraphQL):
    async def get_context(self, request, response):
        return {"user_loader": DataLoader(load_fn=load_users)}

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info: strawberry.Info, id: strawberry.ID) -> User:
        return await info.context["user_loader"].load(id)
```

### Error handling in batch loaders

Return exceptions at positions corresponding to failed keys:

```python
async def load_users(keys: list[int]) -> list[User | ValueError]:
    return [users_db.get(k) or ValueError("not found") for k in keys]
```

### Cache control

```python
loader.clear(id)              # Remove specific key
loader.clear_many([id1, id2]) # Remove multiple keys
loader.clear_all()            # Empty cache
loader.prime_many({...})      # Pre-populate cache
```

---

## Error Handling Patterns

### Return None for missing data

```python
@strawberry.field
def user(self, id: str) -> User | None:
    try:
        return get_user(id)
    except UserDoesNotExist:
        return None
```

### Union result types (recommended for expected errors)

```python
@strawberry.type
class RegisterSuccess:
    user: User

@strawberry.type
class UsernameAlreadyExists:
    username: str
    alternative: str

RegisterResult = Annotated[
    Union[RegisterSuccess, UsernameAlreadyExists],
    strawberry.union("RegisterResult"),
]

@strawberry.mutation
def register(self, username: str, password: str) -> RegisterResult:
    if username_exists(username):
        return UsernameAlreadyExists(username=username, alternative=suggest(username))
    return RegisterSuccess(user=create_user(username, password))
```

Clients use `__typename` to distinguish results.

### When to use which approach

| Scenario | Approach |
|----------|----------|
| Optional data (may not exist) | Return `None` |
| Expected business errors | Union result types |
| Unexpected server errors | Let them propagate to `errors` |

---

## Relay Support

Strawberry implements the Relay specification for pagination and node identification.

### Define a Relay Node

```python
from strawberry import relay

@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[int]
    name: str

    @classmethod
    def resolve_nodes(cls, *, info, node_ids, required=False):
        return [fruits_db.get(int(nid)) for nid in node_ids]
```

### Connection query

```python
@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(relay.ListConnection[Fruit])
    def fruits(self) -> Iterable[Fruit]:
        return fruits_db.values()
```

### GlobalID for mutations

```python
@strawberry.mutation
async def update_fruit(self, info, id: relay.GlobalID, weight: float) -> Fruit:
    fruit = await id.resolve_node(info, ensure_type=Fruit)
    fruit.weight = weight
    return fruit
```

---

## File Uploads

Multipart uploads disabled by default. Enable with `multipart_uploads_enabled=True`.

```python
from strawberry.file_uploads import Upload

@strawberry.mutation
async def upload(self, file: Upload) -> str:
    content = await file.read()
    return content.decode("utf-8")
```

The `Upload` runtime type varies by integration (FastAPI → `fastapi.UploadFile`, Django → `UploadedFile`, etc.).

---

## Pagination

Three approaches: offset-based, cursor-based, and Relay connections.

- **Offset-based**: Simple, supports jumping to any page, but unreliable with frequently changing data
- **Cursor-based**: Efficient for large datasets, uses opaque cursors
- **Relay**: Full spec implementation with `Connection`, `Edge`, `PageInfo` — use `relay.ListConnection`

---

## Converting to Dictionary

```python
user_dict = strawberry.asdict(User(name="Alice", age=30))
# {"name": "Alice", "age": 30}
```

## Common Pitfalls

- **DataLoaders must be per-request.** Sharing a DataLoader across requests causes stale cache data. Create them in `get_context`.
- **File uploads are disabled by default.** Explicitly enable `multipart_uploads_enabled=True` and implement CSRF protection.
- **Permission `fail_silently` requires nullable return type.** If the return type is non-null, the permission error propagates anyway.
- **`info` parameter must be named `info`.** Strawberry injects it by name; any other name becomes a GraphQL argument.
