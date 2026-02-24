# Strawberry GraphQL: Integrations
Based on Strawberry GraphQL 0.306.0 documentation.

## Overview

Strawberry provides integrations for multiple Python web frameworks. Each integration provides a view/router that handles GraphQL HTTP requests, GraphiQL IDE, and optionally WebSocket subscriptions.

### Common View Options

All integrations accept:

| Option | Default | Description |
|--------|---------|-------------|
| `schema` | Required | `strawberry.Schema` instance |
| `graphql_ide` | `"graphiql"` | `"graphiql"`, `"apollo-sandbox"`, `"pathfinder"`, or `None` |
| `allow_queries_via_get` | `True` | Allow GET requests for queries |
| `multipart_uploads_enabled` | `False` | Enable file uploads (security implications) |

### Common Customization Methods

All views support overriding:
- `get_context()` — custom context for resolvers
- `get_root_value()` — custom root value
- `process_result()` — transform result before sending
- `encode_json()` / `decode_json()` — custom JSON serialization

---

## Django

```python
from strawberry.django.views import GraphQLView
from django.urls import path

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

Add `strawberry_django` to `INSTALLED_APPS` for GraphiQL template.

### Async Django

```python
from strawberry.django.views import AsyncGraphQLView

urlpatterns = [
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
```

**Handling `SynchronousOnlyOperation`** when using the ORM:

```python
# Option 1: Use async ORM methods (Django 4.1+)
user = await User.objects.aget(id=id)

# Option 2: Wrap sync code
from asgiref.sync import sync_to_async
users = await sync_to_async(list)(User.objects.all())

# Option 3: Use strawberry_django (handles this automatically)
```

### Custom context

```python
class MyGraphQLView(GraphQLView):
    def get_context(self, request, response):
        return {"request": request, "user": request.user}
```

Subscriptions require Django Channels.

---

## FastAPI

```bash
pip install 'strawberry-graphql[fastapi]'
```

```python
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

### Context with FastAPI dependencies

```python
from fastapi import Depends

def get_db():
    return Database()

async def get_context(db=Depends(get_db)):
    return {"db": db}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
```

### Class-based context

```python
from strawberry.fastapi import BaseContext

class Context(BaseContext):
    @cached_property
    def user(self) -> User | None:
        auth = self.request.headers.get("Authorization")
        return authorize(auth)
```

### Background tasks

```python
@strawberry.mutation
def create_item(self, info: strawberry.Info) -> bool:
    info.context["background_tasks"].add_task(notify, "created")
    return True
```

**Important:** Sync resolvers block the event loop. Use async resolvers for concurrent handling.

---

## Flask

```python
from strawberry.flask.views import GraphQLView
from flask import Flask

app = Flask(__name__)
app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema),
)
```

For async (DataLoaders), use `AsyncGraphQLView`.

---

## Django Channels (WebSocket Subscriptions)

```bash
pip install 'strawberry-graphql[channels]'
```

### ASGI setup

```python
from strawberry.channels import GraphQLProtocolTypeRouter
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()
from mysite.graphql import schema

application = GraphQLProtocolTypeRouter(
    schema,
    django_application=django_asgi_app,
)
```

### Consumers

- `GraphQLHTTPConsumer` — HTTP requests
- `GraphQLWSConsumer` — WebSocket subscriptions

### WebSocket authentication

```python
from strawberry.channels import GraphQLWSConsumer
from strawberry.exceptions import ConnectionRejectionError

class MyWSConsumer(GraphQLWSConsumer):
    async def on_ws_connect(self, context):
        params = context["connection_params"]
        if params.get("password") != "secret":
            raise ConnectionRejectionError({"reason": "Invalid"})
```

### Channel layers for real-time messaging

```python
ws = info.context["ws"]
channel_layer = ws.channel_layer
await channel_layer.group_add(room, ws.channel_name)

# Listen to messages
async with ws.listen_to_channel("chat.message", groups=room_ids) as cm:
    async for message in cm:
        yield ChatMessage(text=message["text"])
```

---

## Pydantic Integration (Experimental)

Create GraphQL types from Pydantic models:

```python
@strawberry.experimental.pydantic.type(model=UserModel)
class UserType:
    id: strawberry.auto
    name: strawberry.auto
```

### All fields shortcut

```python
@strawberry.experimental.pydantic.type(model=UserModel, all_fields=True)
class UserType:
    pass
```

### Input types from Pydantic

```python
@strawberry.experimental.pydantic.input(model=UserModel)
class UserInput:
    id: strawberry.auto
    name: strawberry.auto
```

### Converting between types

```python
# Pydantic → Strawberry
user_type = UserType.from_pydantic(user_model, extra={"age": 10})

# Strawberry → Pydantic (triggers validation)
user_model = user_input.to_pydantic()
```

### Error types for validation

```python
@strawberry.experimental.pydantic.error_type(model=UserModel)
class UserError:
    id: strawberry.auto  # Each field becomes [String!] of error messages
    name: strawberry.auto
```

### Key considerations

- Generated types skip Pydantic validation by default
- Use `to_pydantic()` to trigger validation explicitly
- Be careful with `all_fields=True` — may expose unintended fields
- `strawberry.auto` inherits the type from the Pydantic model field

---

## Other Integrations

All follow the same pattern as Flask with framework-specific view classes:

| Framework | View Class | Notes |
|-----------|-----------|-------|
| ASGI | `strawberry.asgi.GraphQL` | Raw ASGI app |
| Starlette | `strawberry.asgi.GraphQL` | Same as ASGI |
| Litestar | `strawberry.litestar.MakeGraphQLController` | Litestar-native |
| Sanic | `strawberry.sanic.views.GraphQLView` | |
| AIOHTTP | `strawberry.aiohttp.views.GraphQLView` | |
| Quart | `strawberry.quart.views.GraphQLView` | Async Flask |
| Chalice | `strawberry.chalice.views.GraphQLView` | AWS Lambda |

## Common Pitfalls

- **CSRF protection.** Django wraps views with `csrf_exempt` for GraphQL. If enabling file uploads, ensure CSRF middleware is properly configured.
- **Sync resolvers in async frameworks.** Using sync resolvers with FastAPI/ASGI blocks the event loop. Use async resolvers or `sync_to_async`.
- **Pydantic `all_fields=True` leaks.** May expose sensitive fields. Explicitly list fields when security matters.
- **Channel layers required for subscriptions.** Django Channels subscriptions need a channel layer (Redis, in-memory) configured in `CHANNEL_LAYERS`.
