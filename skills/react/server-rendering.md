# React: Server Rendering & Server Components
Based on React 19 documentation.

## Server Components (RSC)

Server Components render ahead of time -- at build time or per request -- in a server environment separate from the client. The rendered output is sent to the browser; the component source code is not.

### What Server Components Can Do

- Use `async/await` directly in the render function
- Access databases, filesystems, and backend APIs directly
- Keep secrets server-side (API keys, tokens)
- Use heavy libraries without adding to client bundle size
- Pass JSX and serializable data as props to Client Components

### What Server Components Cannot Do

- Use `useState`, `useEffect`, `useContext`, or other client hooks
- Attach event handlers (`onClick`, `onChange`, etc.)
- Access browser APIs (localStorage, geolocation, DOM)

### The Key Insight

Server Components are the **default**. There is no `"use server"` directive for components. A component is a Server Component unless it is in a file marked `"use client"` or transitively imported by one.

```jsx
// This is a Server Component (default)
async function NotePage({ id }) {
  const note = await db.notes.get(id);
  return <div>{note.content}</div>;
}
```

### Async Data with Suspense

Await critical data on the server. Start non-critical fetches and hand the promise to Client Components via the `use` hook.

```jsx
// Server Component
async function Page({ id }) {
  const note = await db.notes.get(id);              // blocks render
  const commentsPromise = db.comments.get(note.id); // starts fetch, doesn't block

  return (
    <div>
      <NoteContent note={note} />
      <Suspense fallback={<p>Loading comments...</p>}>
        <Comments commentsPromise={commentsPromise} />
      </Suspense>
    </div>
  );
}

// Client Component
'use client';
import { use } from 'react';

function Comments({ commentsPromise }) {
  const comments = use(commentsPromise); // suspends until resolved
  return comments.map(c => <p key={c.id}>{c.text}</p>);
}
```

### Composing Server and Client Components

Client Components can render Server Components passed as children or JSX props.

```jsx
// Server Component
import Expandable from './Expandable'; // Client Component

async function Notes() {
  const notes = await db.notes.getAll();
  return notes.map(note => (
    <Expandable key={note.id}>
      <p>{note.content}</p>  {/* This JSX is server-rendered */}
    </Expandable>
  ));
}

// Client Component
'use client';
import { useState } from 'react';

export default function Expandable({ children }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div>
      <button onClick={() => setExpanded(!expanded)}>Toggle</button>
      {expanded && children}
    </div>
  );
}
```

---

## Directives

### `'use client'`

Marks a file (and all its transitive imports) as client code. Place it at the very top of the file, before any imports.

```jsx
'use client';

import { useState } from 'react';

export default function Counter({ initialValue = 0 }) {
  const [count, setCount] = useState(initialValue);
  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;
}
```

**Use it when you need:** event handlers, React state/effect hooks, browser APIs, or third-party libraries that use them.

**Don't use it when:** the component is non-interactive and just renders data.

**How the boundary works:** `'use client'` operates on the module dependency tree, not the render tree. Every module transitively imported from a `'use client'` file becomes client code. The same component file can behave as a Server Component or Client Component depending on who imports it.

### `'use server'`

Marks async functions as Server Functions callable from the client. Two placements:

```jsx
// Function-level: inside a Server Component
function EmptyNote() {
  async function createNote() {
    'use server';
    await db.notes.create();
  }
  return <Button onClick={createNote} />;
}

// Module-level: all exports become Server Functions
'use server';

export async function createNote() {
  await db.notes.create();
}

export async function deleteNote(id) {
  await db.notes.delete(id);
}
```

**Rules:**
- Must be on `async` functions only
- Must use single or double quotes (not backticks)
- Function-level: first statement in the function body
- Module-level: first statement in the file

**Common mistake:** `'use server'` does NOT make a component a Server Component. It creates Server Functions (callable endpoints). Server Components are the default and need no directive.

---

## Server Functions

Server Functions are async functions on the server that the client calls via a network request. Arguments and return values are serialized automatically.

### Calling from Forms (preferred for mutations)

```jsx
// actions.js
'use server';

export async function updateName(prevState, formData) {
  const name = formData.get('name');
  if (!name) return { error: 'Name is required' };
  await db.users.update({ name });
  return { error: null };
}

// Client Component
'use client';
import { useActionState } from 'react';
import { updateName } from './actions';

function NameForm() {
  const [state, action, isPending] = useActionState(updateName, { error: null });
  return (
    <form action={action}>
      <input type="text" name="name" disabled={isPending} />
      <button type="submit">Save</button>
      {state.error && <p>{state.error}</p>}
    </form>
  );
}
```

### Calling Outside Forms

Wrap in `useTransition` for proper pending/error states.

```jsx
'use client';
import { useTransition } from 'react';
import { incrementLike } from './actions';

function LikeButton() {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      disabled={isPending}
      onClick={() => {
        startTransition(async () => {
          await incrementLike();
        });
      }}
    >
      Like
    </button>
  );
}
```

### Security

Treat every Server Function argument as untrusted user input. Always:
- Validate and sanitize arguments
- Verify the user is authorized to perform the action
- Never return sensitive data in the response

### Server Functions Are for Mutations

Server Functions are designed for writes and actions, not data fetching. Use Server Components for reads; use Server Functions for mutations.

---

## Serialization Boundary

Data crossing the server/client boundary must be serializable.

### Can Cross the Boundary

| Type | Notes |
|------|-------|
| `string`, `number`, `bigint`, `boolean`, `undefined`, `null` | Primitives |
| `Array`, `Map`, `Set`, `Date` | Built-in collections |
| `TypedArray`, `ArrayBuffer` | Binary data |
| Plain objects | Only with serializable property values |
| `FormData` | For Server Function arguments |
| `Promise` | Streamable from server to client |
| JSX elements | Server-rendered before crossing |
| Server Functions | Reference, not the function body |
| Symbols via `Symbol.for()` | Globally registered only |

### Cannot Cross the Boundary

| Type | Why |
|------|-----|
| Regular functions / closures | Not serializable |
| Class instances | Prototype chain lost |
| Local Symbols (`Symbol('x')`) | Not globally registered |
| DOM nodes, event objects | Browser-only |
| Objects with null prototype | `Object.create(null)` |

Passing a non-serializable value throws at runtime.

---

## Streaming SSR

### `renderToPipeableStream` (Node.js)

The primary streaming API for Node.js servers. Streams HTML as Suspense boundaries resolve.

```jsx
import { renderToPipeableStream } from 'react-dom/server';

app.use('/', (req, res) => {
  let didError = false;

  const { pipe, abort } = renderToPipeableStream(<App />, {
    bootstrapScripts: ['/main.js'],
    onShellReady() {
      res.statusCode = didError ? 500 : 200;
      res.setHeader('content-type', 'text/html');
      pipe(res);
    },
    onShellError(error) {
      res.statusCode = 500;
      res.send('<h1>Something went wrong</h1>');
    },
    onError(error) {
      didError = true;
      console.error(error);
    },
  });

  setTimeout(() => abort(), 10000); // timeout safety net
});
```

**Key concepts:**
- **Shell** = everything outside `<Suspense>` boundaries. Rendered first.
- **`onShellReady`**: shell is done, start piping. Set status code here.
- **`onShellError`**: shell failed, send fallback HTML.
- **`onError`**: any error (recoverable or not). Use for logging.
- **`onAllReady`**: everything done, including suspended content. Use for crawlers/bots.
- **`abort()`**: stop waiting, flush fallbacks, let client render the rest.

### `renderToReadableStream` (Web Streams / Edge / Deno)

Same mental model, different stream type. Returns a Promise.

```jsx
import { renderToReadableStream } from 'react-dom/server';

async function handler(request) {
  let didError = false;

  try {
    const stream = await renderToReadableStream(<App />, {
      bootstrapScripts: ['/main.js'],
      onError(error) {
        didError = true;
        console.error(error);
      },
    });

    return new Response(stream, {
      status: didError ? 500 : 200,
      headers: { 'content-type': 'text/html' },
    });
  } catch (error) {
    // Shell error
    return new Response('<h1>Something went wrong</h1>', { status: 500 });
  }
}
```

For crawlers, await `stream.allReady` before responding. For timeouts, pass an `AbortSignal` via the `signal` option.

### Suspense Boundaries Control Streaming

Wrap slow content in `<Suspense>`. The shell streams immediately; suspended content streams when ready.

```jsx
function ProfilePage() {
  return (
    <ProfileLayout>         {/* shell */}
      <ProfileCover />      {/* shell */}
      <Suspense fallback={<PostsGlimmer />}>
        <Posts />            {/* streams when ready */}
      </Suspense>
    </ProfileLayout>
  );
}
```

---

## Static Prerendering

For static site generation (SSG). Unlike streaming APIs, prerender waits for **all** Suspense boundaries to resolve before producing output.

### `prerender` (Web Streams)

```jsx
import { prerender } from 'react-dom/static';

async function handler(request) {
  const { prelude } = await prerender(<App />, {
    bootstrapScripts: ['/main.js'],
  });
  return new Response(prelude, {
    headers: { 'content-type': 'text/html' },
  });
}
```

### `prerenderToNodeStream` (Node.js)

```jsx
import { prerenderToNodeStream } from 'react-dom/static';

app.use('/', async (req, res) => {
  const { prelude } = await prerenderToNodeStream(<App />, {
    bootstrapScripts: ['/main.js'],
  });
  res.setHeader('content-type', 'text/html');
  prelude.pipe(res);
});
```

### Streaming vs Prerendering

| | Streaming (`renderToPipeableStream`) | Prerendering (`prerenderToNodeStream`) |
|-|--------------------------------------|----------------------------------------|
| Sends HTML as soon as shell is ready | Yes | No -- waits for all data |
| Suspense fallbacks visible to user | Yes, briefly | No -- resolved before send |
| Best for | Dynamic, per-request SSR | Static pages, build-time generation |
| Crawler-friendly by default | Only with `onAllReady` | Yes |

---

## Resume APIs (Server-to-Server Handoff)

Resume APIs enable partial prerendering: render what you can at build time, then finish per-request on a different server. The `postponed` state is a JSON-serializable opaque object stored between phases.

### Two-Phase Pattern

```jsx
// Phase 1: Prerender at build time (abort what takes too long)
import { prerenderToNodeStream } from 'react-dom/static';

const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);

const { prelude, postponed } = await prerenderToNodeStream(<App />, {
  bootstrapScripts: ['/main.js'],
  signal: controller.signal,
});
// Store `postponed` (e.g., to Redis or filesystem)
// Serve `prelude` as the initial HTML

// Phase 2: Resume per-request on an SSR server
import { resumeToPipeableStream } from 'react-dom/server';

const postponed = await loadPostponedState();
const { pipe } = resumeToPipeableStream(<App />, postponed, {
  onShellReady() {
    pipe(response);
  },
});
```

### API Matrix

| Environment | Streaming Resume | Static Resume |
|-------------|-----------------|---------------|
| Web Streams | `resume` | `resumeAndPrerender` |
| Node.js | `resumeToPipeableStream` | `resumeAndPrerenderToNodeStream` |

Resume APIs do NOT accept `bootstrapScripts` or `identifierPrefix` -- those must be set in the original prerender call.

---

## Legacy APIs

### `renderToString`

Not recommended. Does not support streaming or waiting for Suspense data. Immediately resolves Suspense to its fallback.

```jsx
// Avoid in new code
import { renderToString } from 'react-dom/server';
const html = renderToString(<App />);
```

**Use instead:** `renderToPipeableStream` (Node.js) or `renderToReadableStream` (Web Streams) for SSR. `prerenderToNodeStream` or `prerender` for SSG.

### `renderToStaticMarkup`

Renders non-interactive HTML that **cannot be hydrated**. Use only for static content like emails or PDF generation.

```jsx
import { renderToStaticMarkup } from 'react-dom/server';
const html = renderToStaticMarkup(<EmailTemplate user={user} />);
```

---

## Best Practices

1. **Default to Server Components.** Only add `'use client'` when you need interactivity, state, or browser APIs.
2. **Push `'use client'` to the leaves.** Keep the boundary as low as possible in the component tree to maximize server rendering.
3. **Keep the shell fast.** Place `<Suspense>` boundaries around slow data. The shell should render a meaningful skeleton instantly.
4. **Always set status codes before streaming.** Use `onShellReady` / `onShellError` in `renderToPipeableStream`, or `try/catch` around `renderToReadableStream`.
5. **Always implement `onError`.** Log errors in every server render call. Silent failures are invisible.
6. **Set a timeout with `abort()`.** Never let a render hang indefinitely. Abort and let the client finish.
7. **Match `identifierPrefix` between server and client.** Mismatches cause hydration errors.
8. **Use `useActionState` for form mutations.** It handles pending state, error state, and progressive enhancement.
9. **Validate Server Function inputs.** They are public endpoints. Treat arguments like you would any API request body.
10. **Use `prerenderToNodeStream` / `prerender` for SSG, not `renderToString`.** The prerender APIs properly await Suspense data.

## Common Pitfalls

- **Passing non-serializable props across the boundary.** Functions, class instances, and local Symbols cannot cross from Server to Client Components. You will get a runtime error.
- **Using `'use server'` on a component.** It does not make a Server Component. It creates a callable Server Function. Components are Server Components by default.
- **Importing a Server-only module from a `'use client'` file.** All transitive imports of a client file become client code. Filesystem access, database calls, or secrets will break or leak.
- **Fetching data in Server Functions.** Server Functions are for mutations. Fetch data in Server Components or use route loaders.
- **Using `renderToString` with Suspense.** It resolves immediately to the fallback. Use streaming or prerender APIs instead.
- **Forgetting `bootstrapScripts`.** Without it, the rendered HTML is static -- no hydration, no interactivity.
- **Setting status codes after streaming starts.** HTTP headers (including status) must be sent before the body. Set them in `onShellReady`, not later.
