# React: Utility Hooks
Based on React 19 documentation.

## useRef

Holds a mutable value that persists across renders **without triggering re-renders**. Returns an object with a single `.current` property.

```jsx
const ref = useRef(initialValue);
ref.current = newValue; // mutate freely — no re-render
```

### useRef vs useState

- **useState**: value is rendered in JSX; setting it triggers re-render.
- **useRef**: value is NOT rendered (timer IDs, DOM nodes, previous values); mutating `.current` does not re-render.

### DOM Access

```jsx
function Form() {
  const inputRef = useRef(null);
  return (
    <>
      <input ref={inputRef} />
      <button onClick={() => inputRef.current.focus()}>Focus</button>
    </>
  );
}
```

### Storing Non-Render Values (Timers, IDs)

```jsx
function Stopwatch() {
  const intervalRef = useRef(null);

  function handleStart() {
    intervalRef.current = setInterval(() => { /* ... */ }, 10);
  }
  function handleStop() {
    clearInterval(intervalRef.current);
  }
}
```

### Lazy Initialization (Avoid Expensive Re-creation)

```jsx
// BAD: new VideoPlayer() runs every render, result is thrown away
const playerRef = useRef(new VideoPlayer());

// GOOD: only creates once
const playerRef = useRef(null);
if (playerRef.current === null) {
  playerRef.current = new VideoPlayer();
}
```

### Passing Refs to Child Components (React 19)

In React 19, `ref` is a regular prop -- no `forwardRef` needed.

```jsx
function MyInput({ ref }) {
  return <input ref={ref} />;
}
function Parent() {
  const inputRef = useRef(null);
  return <MyInput ref={inputRef} />;
}
```

### Pitfall: Never Read or Write Refs During Render

Refs during render break component purity. Only access `.current` in event handlers or effects.

```jsx
// BAD: reading/writing ref during render
return <h1>{myRef.current}</h1>;

// GOOD: in event handlers or effects
useEffect(() => { myRef.current = 123; }, []);
function handleClick() { console.log(myRef.current); }
```

---

## useImperativeHandle

Customizes what a parent sees when it accesses a ref to your component. Limits the exposed API instead of handing over the raw DOM node.

```jsx
useImperativeHandle(ref, createHandle, dependencies?)
```

### Exposing Selected Methods

```jsx
function MyInput({ ref }) {
  const inputRef = useRef(null);
  useImperativeHandle(ref, () => ({
    focus() { inputRef.current.focus(); },
    scrollIntoView() { inputRef.current.scrollIntoView(); },
  }), []);
  return <input ref={inputRef} />;
}
// Parent can call ref.current.focus() but NOT ref.current.style = ...
```

### Composing Multiple Child Refs

```jsx
function Post({ ref }) {
  const commentsRef = useRef(null);
  const addCommentRef = useRef(null);
  useImperativeHandle(ref, () => ({
    scrollAndFocusAddComment() {
      commentsRef.current.scrollToBottom();
      addCommentRef.current.focus();
    },
  }), []);
}
```

### When to Use (and When Not To)

Use for imperative actions that can't be expressed as props: focusing, scrolling, selecting text, triggering animations.

Don't use when props work:

```jsx
// BAD: imperative open/close methods via ref
useImperativeHandle(ref, () => ({ open() {}, close() {} }));

// GOOD: declarative prop
<Modal isOpen={isOpen} />
```

---

## useId

Generates unique, stable IDs for accessibility attributes. Works correctly with server-side rendering and hydration.

```jsx
const id = useId();
```

### Linking Labels and Inputs

```jsx
function PasswordField() {
  const hintId = useId();
  return (
    <>
      <label>Password: <input type="password" aria-describedby={hintId} /></label>
      <p id={hintId}>Must contain at least 18 characters</p>
    </>
  );
}
```

### Multiple Related Elements from One ID

Call `useId` once, derive related IDs with suffixes:

```jsx
function Form() {
  const id = useId();
  return (
    <>
      <label htmlFor={id + '-first'}>First Name:</label>
      <input id={id + '-first'} />
      <label htmlFor={id + '-last'}>Last Name:</label>
      <input id={id + '-last'} />
    </>
  );
}
```

### Multiple React Roots on One Page

Use `identifierPrefix` to prevent collisions. Pass the same prefix on server and client:

```jsx
createRoot(document.getElementById('root1'), { identifierPrefix: 'app1-' });
createRoot(document.getElementById('root2'), { identifierPrefix: 'app2-' });
// SSR: same prefix on both sides
renderToPipeableStream(<App />, { identifierPrefix: 'app1-' });
hydrateRoot(container, <App />, { identifierPrefix: 'app1-' });
```

### Pitfalls

- **Not for list keys.** Keys come from your data, not `useId`.
- **Not for CSS selectors.** The generated format (`:r1:`) is an implementation detail.
- **Top level only.** Don't call inside loops or conditions; extract a component instead.
- **SSR tree must match.** Mismatched server/client trees cause hydration ID mismatches.

---

## useDebugValue

Adds a label to a custom hook visible in React DevTools. Only useful inside custom hooks, not in regular components.

```jsx
useDebugValue(value, format?)
```

### Basic Usage

```jsx
function useOnlineStatus() {
  const isOnline = /* ... */;
  useDebugValue(isOnline ? 'Online' : 'Offline');
  return isOnline;
}
// DevTools shows: OnlineStatus: "Online"
```

### Deferred Formatting

The optional second argument only runs when inspected in DevTools, not on every render:

```jsx
useDebugValue(date, date => date.toDateString());
```

### When to Use

- **Shared library hooks** where internal state is non-obvious.
- Skip for simple or app-specific hooks. Not every custom hook needs one.

---

## useSyncExternalStore

Subscribes a component to an external (non-React) data source. Ensures tearing-free reads during concurrent rendering.

```jsx
const snapshot = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?)
```

### Parameters

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `subscribe(callback)` | Yes | Subscribe to the store; return an unsubscribe function |
| `getSnapshot()` | Yes | Return current store value (must be immutable or cached) |
| `getServerSnapshot()` | No | Return initial value for SSR/hydration |

### Subscribing to a Browser API (Custom Hook Pattern)

Wrap in a custom hook. Define `subscribe` and `getSnapshot` outside the component for referential stability.

```jsx
function subscribe(callback) {
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}
function getSnapshot() { return navigator.onLine; }

export function useOnlineStatus() {
  return useSyncExternalStore(subscribe, getSnapshot, () => true); // SSR default
}

function StatusBar() {
  const isOnline = useOnlineStatus();
  return <span>{isOnline ? 'Online' : 'Offline'}</span>;
}
```

### External Store Pattern

```jsx
let todos = [{ id: 0, text: 'Initial' }];
let listeners = [];
export const todosStore = {
  addTodo(text) {
    todos = [...todos, { id: todos.length, text }]; // immutable update
    listeners.forEach(l => l());
  },
  subscribe(listener) {
    listeners = [...listeners, listener];
    return () => { listeners = listeners.filter(l => l !== listener); };
  },
  getSnapshot() { return todos; },
};
```

### Pitfall: getSnapshot Must Return Immutable/Cached Data

Returning a new object every call causes an infinite re-render loop. Return the same reference when data hasn't changed.

```jsx
// BAD: new object every call
function getSnapshot() { return { todos: store.todos }; }

// GOOD: return the immutable reference directly
function getSnapshot() { return store.todos; }

// GOOD: cache when wrapping is necessary
let cached = null, lastVersion = 0;
function getSnapshot() {
  if (store.version !== lastVersion) {
    cached = { todos: store.todos };
    lastVersion = store.version;
  }
  return cached;
}
```

### Pitfall: subscribe Must Be Stable

A new function reference each render causes resubscription every render. Define outside the component, or use `useCallback` when it depends on props.

```jsx
// BAD: inline arrow = new function each render
useSyncExternalStore((cb) => store.subscribe(cb), store.getSnapshot);

// GOOD: stable reference defined outside
function subscribe(cb) { return store.subscribe(cb); }
function Component() {
  useSyncExternalStore(subscribe, store.getSnapshot);
}

// GOOD: useCallback when subscribe depends on props
function Component({ channel }) {
  const sub = useCallback((cb) => store.subscribe(channel, cb), [channel]);
  useSyncExternalStore(sub, store.getSnapshot);
}
```

### When to Use

- Third-party state libraries (Redux, Zustand, MobX)
- Browser APIs (`navigator.onLine`, `matchMedia`, `ResizeObserver`)
- Any non-React data source that changes over time

Prefer `useState`/`useReducer` for state that lives entirely within React.

---

## Quick Reference

| Hook | Purpose | Triggers Re-render? |
|------|---------|-------------------|
| `useRef` | Mutable value that persists across renders | No |
| `useImperativeHandle` | Customize ref handle exposed to parent | No (configures ref) |
| `useId` | Generate stable unique IDs for accessibility | No (returns string) |
| `useDebugValue` | Label custom hooks in DevTools | No (DevTools only) |
| `useSyncExternalStore` | Subscribe to external data source | Yes (on store change) |
