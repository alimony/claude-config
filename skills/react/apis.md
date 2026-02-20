# React: Core APIs
Based on React 19 documentation.

## Overview

React 19 provides these top-level APIs:

| API | Purpose |
|-----|---------|
| `createContext` | Share values through the component tree without prop drilling |
| `lazy` | Defer loading a component's code until first render |
| `memo` | Skip re-renders when props haven't changed |
| `startTransition` | Mark state updates as non-urgent |
| `act` | Flush pending updates in tests before assertions |
| `use` | Read a Promise or Context value (can be called conditionally) |
| `cache` | Memoize function results across components (Server Components only) |

---

## `createContext` -- Context for Shared State

### Create and Provide

```jsx
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext('light'); // default is a static fallback

function App() {
  const [theme, setTheme] = useState('dark');

  // React 19: use the context object directly as provider
  return (
    <ThemeContext value={theme}>
      <Page />
    </ThemeContext>
  );
}
```

### Consume with `useContext`

```jsx
function Button() {
  const theme = useContext(ThemeContext);
  return <button className={theme}>Click</button>;
}
```

### Best Practices

- Declare contexts at module level, not inside components.
- Export from a dedicated file so multiple components can import.
- The default value is a static fallback for when no provider exists above -- it never changes.
- `SomeContext.Provider` still works but `<SomeContext value={...}>` is the React 19 way.
- `SomeContext.Consumer` is legacy. Use `useContext` or `use` instead.

---

## `lazy` -- Code Splitting

### Basic Pattern

```jsx
import { lazy, Suspense } from 'react';

// Declare at module top level, never inside a component
const MarkdownPreview = lazy(() => import('./MarkdownPreview.js'));

function Editor() {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <MarkdownPreview />
    </Suspense>
  );
}
```

### Key Rules

- The imported module must have a **default export** that is a valid React component.
- The `load` function is called only once; both the Promise and result are cached.
- Always wrap lazy components in `<Suspense>` with a `fallback`.
- If the import rejects, the rejection propagates to the nearest Error Boundary.

### Do / Don't

```jsx
// DON'T: declaring inside a component resets state on every render
function Editor() {
  const Preview = lazy(() => import('./Preview.js')); // BAD
}

// DO: declare at module scope
const Preview = lazy(() => import('./Preview.js')); // GOOD
function Editor() { /* use <Preview /> */ }
```

---

## `memo` -- Skip Unnecessary Re-renders

### Signature

```jsx
const MemoizedComponent = memo(Component, arePropsEqual?);
```

### When It Re-renders

A memoized component **skips** re-render when the parent re-renders but props are the same (shallow `Object.is` comparison). It **still re-renders** when:

- Its own state changes.
- A context it reads changes.
- Props actually differ.

### Patterns

```jsx
// Basic
const Greeting = memo(function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
});

// Stabilize object props with useMemo
function Page() {
  const [name, setName] = useState('Taylor');
  const [age, setAge] = useState(42);
  const person = useMemo(() => ({ name, age }), [name, age]);
  return <Profile person={person} />;
}

// Stabilize function props with useCallback
function Parent() {
  const handleClick = useCallback(() => { /* ... */ }, []);
  return <MemoizedChild onClick={handleClick} />;
}
```

### When NOT to Use `memo`

- Props are always different (new objects/functions every render and you haven't stabilized them).
- The component rarely re-renders or re-rendering is cheap.
- Prefer structural fixes first: keep state local, accept children as JSX, remove unnecessary Effects.
- The React Compiler (when available) applies equivalent memoization automatically.

### Custom Comparison Pitfalls

```jsx
// WRONG: forgetting to compare function props causes stale closures
memo(Chart, (old, new_) => old.data === new_.data); // forgot onClick!

// WRONG: deep equality is a performance killer
memo(Chart, (old, new_) => JSON.stringify(old) === JSON.stringify(new_));

// RIGHT: compare every prop
memo(Chart, (old, new_) =>
  old.data === new_.data && old.onClick === new_.onClick
);
```

---

## `startTransition` -- Non-Urgent Updates

### Signature

```jsx
import { startTransition } from 'react';

startTransition(() => {
  setTab(nextTab); // marked as a Transition
});
```

### Key Behavior

- The callback runs **synchronously and immediately**; all `set` calls inside are batched as low-priority.
- The UI stays responsive -- higher-priority updates (e.g., typing) interrupt transitions.
- Does **not** provide a pending indicator. Use the `useTransition` hook if you need `isPending`.

### `startTransition` vs `useTransition`

| | `startTransition` | `useTransition` |
|-|-------------------|-----------------|
| Pending indicator | No | Yes (`isPending`) |
| Usable outside components | Yes | No (hook) |

### Async Transitions

After an `await`, you must re-wrap state updates:

```jsx
startTransition(async () => {
  const data = await fetchData();
  startTransition(() => {
    setData(data); // must re-wrap after await
  });
});
```

### Don't Use For

- Controlled text inputs (typing must be synchronous).
- State updates inside `setTimeout` or other async callbacks (they won't be marked as transitions).

---

## `use` -- Read Promises and Context

### Signature

```jsx
const value = use(resource); // resource is a Promise or Context
```

### Unique Property

Unlike all other hooks, `use` **can be called inside conditionals and loops**. It must still be inside a component or custom hook.

### Reading Context Conditionally

```jsx
function HorizontalRule({ show }) {
  if (show) {
    const theme = use(ThemeContext); // legal!
    return <hr className={theme} />;
  }
  return false;
}
```

### Streaming Data from Server to Client

```jsx
// Server Component
export default function App() {
  const messagePromise = fetchMessage();
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <Message messagePromise={messagePromise} />
    </Suspense>
  );
}

// Client Component
'use client';
import { use } from 'react';

function Message({ messagePromise }) {
  const content = use(messagePromise); // suspends until resolved
  return <p>{content}</p>;
}
```

### Error Handling

`use` does **not** work inside try-catch. Handle errors with:

```jsx
// Option 1: Error Boundary
<ErrorBoundary fallback={<p>Something went wrong</p>}>
  <Suspense fallback={<p>Loading...</p>}>
    <Message messagePromise={messagePromise} />
  </Suspense>
</ErrorBoundary>

// Option 2: catch before passing
const messagePromise = fetchMessage().catch(() => 'Fallback message');
```

### Best Practices

- In Server Components, prefer `async/await` over `use`.
- Create Promises in Server Components, pass to Client Components (avoids recreating on each render).
- Resolved values must be serializable when crossing the server/client boundary.

---

## `cache` -- Server-Side Memoization

**Server Components only.**

### Signature

```jsx
import { cache } from 'react';
const cachedFn = cache(fn);
```

Cache uses `Object.is` for argument comparison. The cache lives for the duration of a single server request.

### Deduplicate Data Fetches

```jsx
// getUser.js -- shared module
import { cache } from 'react';

export const getUser = cache(async (id) => {
  return await db.user.query(id);
});

// Profile.jsx and Sidebar.jsx both call getUser(id)
// Only one query runs; the second call returns the cached result.
```

### Preload Data

```jsx
function Page({ id }) {
  getUser(id); // fire-and-forget: starts fetch early
  return <Profile id={id} />;
}

async function Profile({ id }) {
  const user = await getUser(id); // hits cache, fast
}
```

### Do / Don't

```jsx
// DON'T: calling cache() inside a component creates a new cache per render
function Temperature({ city }) {
  const getReport = cache(calcReport); // BAD -- new cache each render
}

// DO: call cache() at module scope
const getReport = cache(calcReport); // GOOD
```

### Gotchas

- **Object arguments** don't share cache across components (different object references). Pass primitives or the same reference.
- **Errors are cached too.** If `fn` throws for given args, subsequent calls with the same args rethrow the cached error.
- Must be called **within a component render** (not at the module top-level for side effects).

### `cache` vs `useMemo` vs `memo`

| API | Where | Scope | Invalidation |
|-----|-------|-------|-------------|
| `cache` | Server Components | Across components, one request | End of server request |
| `useMemo` | Client Components | Single component instance | Dependency array changes |
| `memo` | Client Components | Single component | Prop changes |

---

## `act` -- Test Helper

### Signature

```jsx
await act(async () => {
  // render or interact
});
// now safe to assert
```

### Usage

```jsx
// Setup
global.IS_REACT_ACT_ENVIRONMENT = true; // React Testing Library does this for you

// Render
await act(async () => {
  ReactDOMClient.createRoot(container).render(<Counter />);
});

// Interact
await act(async () => {
  button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
});

// Assert after act completes
expect(container.textContent).toBe('1');
```

### Key Rules

- Always `await` the result.
- Make assertions **after** `act()`, not inside.
- React Testing Library wraps its helpers with `act` automatically -- you rarely need it directly.

---

## Experimental & Canary APIs

### `addTransitionType` (Canary)

Associates a label with a transition for animation customization with View Transitions.

```jsx
import { startTransition, addTransitionType } from 'react';

startTransition(() => {
  addTransitionType('navigation-forward');
  navigate(nextUrl);
});
```

Must be called **inside** a `startTransition` scope. Types reset after each commit.

### `cacheSignal` (Experimental, Server Components only)

Returns an `AbortSignal` that aborts when the cache lifetime ends (render completes, aborts, or fails).

```jsx
import { cache, cacheSignal } from 'react';
const dedupedFetch = cache(fetch);

async function Component() {
  await dedupedFetch(url, { signal: cacheSignal() });
}
```

Returns `null` outside rendering or in Client Components.

### `captureOwnerStack` (Development only)

Returns the Owner Stack as a string for debugging and custom error overlays.

```jsx
import * as React from 'react';

// Use namespace import (named import may be tree-shaken in production bundles)
if (process.env.NODE_ENV !== 'production') {
  const stack = React.captureOwnerStack();
}
```

Returns `null` in production. Only available inside React-controlled contexts (render, effects, React event handlers).

### `experimental_taintObjectReference` (Experimental, Server Components only)

Prevents an object from being passed to Client Components.

```jsx
import { experimental_taintObjectReference } from 'react';

export async function getUser(id) {
  const user = await db.query(id);
  experimental_taintObjectReference(
    'Do not pass the entire user object to the client. Pick specific properties.',
    user
  );
  return user;
}
```

Taint does NOT propagate to copies (`{...user}`) or extracted properties. It is one security layer, not a complete solution.

### `experimental_taintUniqueValue` (Experimental, Server Components only)

Prevents a specific value (token, key, password) from being passed to Client Components.

```jsx
import { experimental_taintUniqueValue } from 'react';

experimental_taintUniqueValue(
  'Do not pass the API token to the client.',
  process,            // lifetime: taint lasts as long as this object lives
  process.env.SECRET  // the value to protect
);
```

Only works for high-entropy values (crypto tokens, keys, hashes). Derived values (`.toUpperCase()`, concatenation, substrings) are NOT automatically tainted.

---

## Quick Reference

### Common Patterns

| I want to... | Use |
|--------------|-----|
| Share state without prop drilling | `createContext` + `useContext` |
| Code-split a component | `lazy` + `Suspense` |
| Skip re-renders for unchanged props | `memo` (+ `useMemo`/`useCallback` for prop stability) |
| Keep UI responsive during slow updates | `startTransition` or `useTransition` |
| Read a promise or context conditionally | `use` |
| Deduplicate server-side data fetches | `cache` |
| Test that updates are flushed | `act` |
| Animate between transition states | `addTransitionType` (canary) |
| Prevent sensitive data leaking to client | `taintObjectReference` / `taintUniqueValue` (experimental) |

### Anti-Patterns to Avoid

1. **Creating `lazy`, `cache`, or `memo` inside components** -- creates new instances every render.
2. **Wrapping everything in `memo`** -- fix the structure first (local state, children-as-JSX).
3. **Using `use` inside try-catch** -- throws a Suspense exception, not a real error.
4. **Forgetting to re-wrap `startTransition` after `await`** -- the state update won't be a transition.
5. **Passing new object literals as props to memoized components** -- defeats memoization.
6. **Using `cache` in Client Components** -- it only works in Server Components.
7. **Assuming `taint` is a complete security solution** -- it's one layer; copies bypass it.
