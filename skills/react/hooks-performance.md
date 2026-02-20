# React: Performance Optimization
Based on React 19 documentation.

## When to Optimize

React is fast by default. Most components do not need manual optimization. Before reaching for any performance hook:

1. **Profile first.** Use React DevTools Profiler or `console.time` to find actual bottlenecks. Intuition is usually wrong.
2. **Fix the architecture.** Lift state down, accept children as JSX, keep rendering pure. These structural fixes eliminate re-renders without any memoization.
3. **Then memoize.** Only add `memo`, `useMemo`, or `useCallback` when profiling shows a measurable problem.

> The React Compiler (available in React 19) automatically memoizes values and functions. When using the compiler, manual `useMemo`/`useCallback`/`memo` calls are often unnecessary.

---

## Quick Decision Guide

| Problem | Solution |
|---------|----------|
| Expensive calculation re-runs on every render | `useMemo` |
| Child wrapped in `memo` receives new object/array each render | `useMemo` on the prop value |
| Child wrapped in `memo` receives new function each render | `useCallback` |
| Component re-renders with identical props | `memo` |
| Typing in input feels laggy because of slow sibling render | `useDeferredValue` |
| Navigation/tab switch blocks the UI | `useTransition` |
| Async action (form submit, data fetch) blocks the UI | `useTransition` |
| Slow component you cannot optimize internally | `useDeferredValue` + `memo` |

---

## API Reference and Patterns

### `memo(Component, arePropsEqual?)`

Wraps a component so it skips re-rendering when props are unchanged (shallow `Object.is` comparison by default).

```jsx
import { memo } from 'react';

const ExpensiveList = memo(function ExpensiveList({ items, onSelect }) {
  return items.map(item => (
    <li key={item.id} onClick={() => onSelect(item.id)}>{item.name}</li>
  ));
});
```

**`memo` does NOT prevent re-renders caused by:**
- Internal state changes (`useState`, `useReducer`)
- Context changes (`useContext`)

**Pass primitives instead of objects when possible:**

```jsx
// Do: primitives are stable across renders
<Profile name={name} age={age} />

// Don't: new object reference every render defeats memo
<Profile person={{ name, age }} />
```

**Derive data to reduce prop surface:**

```jsx
// Do: pass the derived boolean
<CallToAction hasGroups={person.groups !== null} />

// Don't: pass the whole object when only one fact matters
<CallToAction person={person} />
```

---

### `useMemo(calculateValue, dependencies)`

Caches the **result** of a calculation between renders.

```jsx
const visibleTodos = useMemo(
  () => filterTodos(todos, tab),
  [todos, tab]
);
```

**Three legitimate use cases:**

1. **Skip expensive recalculations** (consistently > 1ms).
2. **Stabilize a value** passed as a prop to a `memo`-wrapped child.
3. **Stabilize a dependency** of another hook (`useEffect`, `useMemo`).

**Common mistakes:**

```jsx
// Don't: forget the dependency array (recalculates every render)
const result = useMemo(() => compute(x));

// Don't: arrow function without parens returns undefined for objects
const opts = useMemo(() => { mode: 'fast', query }, [query]); // undefined!

// Do: wrap object literal in parentheses
const opts = useMemo(() => ({ mode: 'fast', query }), [query]);
```

**Prefer structural fixes over memoization:**

```jsx
// Before: memoizing options to prevent Effect re-fire
const options = useMemo(() => ({ serverUrl, roomId }), [roomId]);
useEffect(() => { connect(options); }, [options]);

// After: move the object inside the Effect — no memo needed
useEffect(() => {
  const options = { serverUrl, roomId };
  connect(options);
}, [roomId]);
```

---

### `useCallback(fn, dependencies)`

Caches the **function itself** between renders. Equivalent to `useMemo(() => fn, deps)`.

```jsx
const handleSubmit = useCallback((orderDetails) => {
  post('/product/' + productId + '/buy', { referrer, orderDetails });
}, [productId, referrer]);
```

**Only useful when the cached function is:**
- Passed to a `memo`-wrapped child, or
- Used as a dependency of another hook.

Otherwise `useCallback` adds complexity for zero benefit.

**Reduce dependencies with updater functions:**

```jsx
// Don't: todos changes often, breaking memoization
const addTodo = useCallback((text) => {
  setTodos([...todos, { id: nextId++, text }]);
}, [todos]);

// Do: updater function removes the dependency
const addTodo = useCallback((text) => {
  setTodos(prev => [...prev, { id: nextId++, text }]);
}, []);
```

**Move functions into Effects instead of wrapping in useCallback:**

```jsx
// Don't: useCallback just to stabilize an Effect dependency
const createOptions = useCallback(() => ({ serverUrl, roomId }), [roomId]);
useEffect(() => { connect(createOptions()); }, [createOptions]);

// Do: define the function inside the Effect
useEffect(() => {
  const options = { serverUrl, roomId };
  connect(options);
}, [roomId]);
```

---

### `useTransition()`

Marks a state update as non-blocking. The UI stays responsive while React renders the new state in the background.

```jsx
const [isPending, startTransition] = useTransition();

function handleTabChange(nextTab) {
  startTransition(() => {
    setTab(nextTab); // non-blocking update
  });
}
```

**`isPending`** lets you show inline loading feedback without replacing visible content:

```jsx
<button disabled={isPending} onClick={() => selectTab('posts')}>
  {isPending ? 'Loading...' : 'Posts'}
</button>
```

**Works with Suspense.** A transition avoids showing a Suspense fallback for already-revealed content. Users see the old UI (optionally dimmed) until the new UI is ready.

**Async actions inside transitions:**

```jsx
startTransition(async () => {
  await saveData(formData);
  // State updates after await need their own startTransition
  startTransition(() => {
    setStatus('saved');
  });
});
```

**Limitations:**
- Cannot wrap controlled input updates (inputs must update synchronously).
- `setTimeout` callbacks run outside the transition scope — wrap the `startTransition` inside the timeout, not the other way around.
- Transitions can be interrupted by higher-priority updates.

**Use standalone `startTransition` (not the hook) when you need transitions outside components:**

```jsx
import { startTransition } from 'react';
// e.g., in a router or library
startTransition(() => navigate('/about'));
```

---

### `useDeferredValue(value, initialValue?)`

Returns a deferred copy of a value. React first re-renders with the **old** deferred value (keeping the UI responsive), then schedules a background re-render with the **new** value.

```jsx
function SearchPage() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  return (
    <>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <Suspense fallback={<Spinner />}>
        <SearchResults query={deferredQuery} />
      </Suspense>
    </>
  );
}
```

**Show stale state visually:**

```jsx
const isStale = query !== deferredQuery;
<div style={{ opacity: isStale ? 0.5 : 1 }}>
  <SearchResults query={deferredQuery} />
</div>
```

**Requires `memo` on the slow child.** Without `memo`, the child re-renders with the old value anyway, gaining nothing:

```jsx
const SearchResults = memo(function SearchResults({ query }) {
  // expensive render
});
```

**Pass primitives, not fresh objects:**

```jsx
// Don't: new object on every render
const deferred = useDeferredValue({ query });

// Do: defer the primitive, construct the object inside the child
const deferredQuery = useDeferredValue(query);
```

**useDeferredValue vs debounce/throttle:**

| | `useDeferredValue` | Debounce/Throttle |
|-|-------------------|-------------------|
| Delay | Adaptive (device speed) | Fixed ms value |
| Interruptible | Yes | No |
| Network requests | Does not prevent them | Prevents extra requests |
| Best for | Render optimization | Network call reduction |

---

## useTransition vs useDeferredValue

Both defer low-priority work, but they differ in what you control:

| | `useTransition` | `useDeferredValue` |
|-|----------------|-------------------|
| You control | The state update (wrap `setState`) | A value (wrap the prop/variable) |
| `isPending` flag | Yes | No (compare old vs deferred) |
| Use when | You own the state setter | You receive a prop you cannot control |
| Async support | Yes (async actions) | No |

**Rule of thumb:** Use `useTransition` when you control the state update. Use `useDeferredValue` when you receive a value from a parent and cannot change how it is set.

---

## Common Pitfalls

### Over-memoizing
Wrapping everything in `memo`/`useMemo`/`useCallback` adds cognitive overhead and can mask real problems. Memoize only what profiling tells you to.

### Broken memoization
A single unstable prop defeats `memo`. Check that **all** props are stable:

```jsx
// This memo is useless — style is a new object every render
const Child = memo(function Child({ style, onClick }) { /* ... */ });

function Parent() {
  return <Child style={{ color: 'red' }} onClick={() => doThing()} />;
  // Both props are new references every render
}

// Fix: stabilize both props
function Parent() {
  const style = useMemo(() => ({ color: 'red' }), []);
  const onClick = useCallback(() => doThing(), []);
  return <Child style={style} onClick={onClick} />;
}
```

### Wrong mental model: "memo prevents all re-renders"
`memo` only skips re-renders caused by **parent re-rendering with same props**. State changes and context changes inside the component still trigger re-renders.

### Memoizing inside loops
Hooks cannot be called inside loops. Extract a child component instead:

```jsx
// Don't: hooks in a loop
items.map(item => {
  const data = useMemo(() => process(item), [item]); // invalid
});

// Do: extract a component
function Item({ item }) {
  const data = useMemo(() => process(item), [item]);
  return <Chart data={data} />;
}
items.map(item => <Item key={item.id} item={item} />);
```

### Using useTransition for controlled inputs
Transitions are non-blocking, but text inputs must update synchronously. Use `useDeferredValue` instead:

```jsx
// Don't: input will feel broken
startTransition(() => setText(e.target.value));

// Do: update input immediately, defer the expensive part
const [text, setText] = useState('');
const deferredText = useDeferredValue(text);
// Pass deferredText to the slow component
```

---

## Structural Fixes That Eliminate the Need for Memoization

Before reaching for hooks, try these patterns:

1. **Accept children as JSX.** A wrapper's state change won't re-render children passed as `props.children`.
2. **Keep state local.** State that only one component uses should live in that component.
3. **Lift content up, not state up.** Move the expensive subtree above the state that changes.
4. **Move objects/functions inside Effects.** Eliminates the need to memoize Effect dependencies.
5. **Pass primitives instead of objects.** Primitives are compared by value, not reference.
