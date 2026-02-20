# React: Rules & Linting
Based on React 19 documentation.

## The Three Rules of React

React has three fundamental rules that enable it to optimize rendering, maintain predictable behavior, and support features like concurrent rendering.

### 1. Components and Hooks Must Be Pure

Pure means: given the same inputs, always return the same output with no observable side effects during render.

**What counts as impure during render:**
- Reading or writing global/module-level variables
- Mutating props, state, or hook return values
- Calling `Math.random()`, `Date.now()`, `crypto.randomUUID()`
- Making network requests, setting timers, or modifying the DOM
- Reading `ref.current`

**What is allowed during render:**
- Mutating values created locally within the render (local mutation)
- Reading props, state, and context
- Returning JSX
- Creating new objects and arrays

```js
// Local mutation is fine
function FriendList({ friends }) {
  const items = [];  // created locally
  for (const friend of friends) {
    items.push(<Friend key={friend.id} friend={friend} />);
  }
  return <section>{items}</section>;
}
```

**Side effects belong in:**
- Event handlers (`onClick`, `onSubmit`, etc.)
- `useEffect` (runs after render)
- `useState` initializer (runs once)

### 2. React Calls Components and Hooks

React controls when and how components render. You describe what to render; React decides the rest.

- **Never call components as functions.** Use JSX: `<Article />`, not `Article()`.
- **Never pass hooks as values.** Don't pass hooks as props or return them from non-hook functions.
- **Don't wrap hooks in higher-order functions.** Create a new custom hook instead.

```js
// Wrong
function BlogPost() {
  return <Layout>{Article()}</Layout>;
}

// Right
function BlogPost() {
  return <Layout><Article /></Layout>;
}
```

### 3. Rules of Hooks

Hooks rely on call order. React tracks hooks by the order they are called, so that order must be identical on every render.

**Only call hooks:**
- At the top level of a function component or custom hook
- Before any early returns

**Never call hooks:**
- Inside conditions, loops, or nested functions
- In event handlers or callbacks
- In class components
- Inside `try`/`catch`/`finally`
- Inside functions passed to `useMemo`, `useReducer`, or `useEffect`

```js
// Wrong: conditional hook
function Bad({ cond }) {
  if (cond) {
    const [val, setVal] = useState(0);  // breaks hook order
  }
}

// Wrong: hook after early return
function Bad({ data }) {
  if (!data) return null;
  const [val, setVal] = useState(data);  // may not run
}

// Right: always call, conditionally use
function Good({ cond, data }) {
  const [val, setVal] = useState(data ?? null);
  if (!cond) return null;
  return <div>{val}</div>;
}
```

**Exception:** The `use` hook can be called conditionally and in loops, but not in `try`/`catch`.

**Naming convention:** Functions starting with `use` are treated as hooks by React and the linter.

---

## Props and State Are Immutable

Never mutate props or state directly. Always create new values.

```js
// Wrong: mutating props
function Post({ item }) {
  item.url = new URL(item.url, base);
  return <Link url={item.url}>{item.title}</Link>;
}

// Right: derive a new value
function Post({ item }) {
  const url = new URL(item.url, base);
  return <Link url={url}>{item.title}</Link>;
}

// Wrong: mutating state in place
items.push(newItem);
setItems(items);  // same reference, no re-render

// Right: new array
setItems([...items, newItem]);

// Right: new object
setUser({ ...user, name: 'Bob' });

// Right: nested update
setUser({
  ...user,
  settings: { ...user.settings, theme: 'dark' },
});
```

Don't mutate values after passing them to JSX either -- React may have already read them.

---

## ESLint Plugin Setup

### Installation

`eslint-plugin-react-hooks` ships two core rules (`rules-of-hooks`, `exhaustive-deps`) and, with React Compiler, a full suite of additional lint rules.

### Configuration

```json
{
  "extends": ["plugin:react-hooks/recommended"]
}
```

The `recommended` preset enables all rules at their recommended severity. No extra configuration is needed for most projects.

### Custom Effect Hooks

If you have custom hooks that behave like `useEffect` (take a dependency array), tell the linter:

```json
{
  "settings": {
    "react-hooks": {
      "additionalEffectHooks": "(useMyEffect|useCustomEffect)"
    }
  }
}
```

Or at the rule level (takes precedence over shared settings):

```json
{
  "rules": {
    "react-hooks/exhaustive-deps": ["warn", {
      "additionalHooks": "(useMyCustomHook|useAnotherHook)"
    }]
  }
}
```

---

## Exhaustive Dependencies (Most Important Rule)

The `exhaustive-deps` rule ensures dependency arrays in `useEffect`, `useMemo`, and `useCallback` list every reactive value used inside the callback. Missing dependencies cause stale closures -- your code reads outdated values.

### The Rule

Every variable from the component scope that the effect/memo reads must appear in the dependency array.

```js
// Wrong: missing userId
useEffect(() => {
  fetchUser(userId);
}, []);

// Right
useEffect(() => {
  fetchUser(userId);
}, [userId]);
```

### Common Fix Patterns

**Function causes infinite loop as dependency:**

```js
// Problem: new function reference every render
const logItems = () => console.log(items);
useEffect(() => { logItems(); }, [logItems]);  // infinite loop

// Fix 1: move logic into the effect
useEffect(() => { console.log(items); }, [items]);

// Fix 2: stabilize with useCallback
const logItems = useCallback(() => console.log(items), [items]);
useEffect(() => { logItems(); }, [logItems]);
```

**Want to run only on mount but linter complains:**

```js
// Wrong: suppressing the warning
useEffect(() => { sendAnalytics(userId); }, []);  // lint warning

// Right: include dep (usually the correct answer)
useEffect(() => { sendAnalytics(userId); }, [userId]);

// Right: ref guard for true fire-once behavior
const sent = useRef(false);
useEffect(() => {
  if (sent.current) return;
  sent.current = true;
  sendAnalytics(userId);
}, [userId]);
```

**Object/array dependency changes every render:**

```js
// Problem: new object every render
const options = { method: 'GET', headers };
useEffect(() => { fetch(url, options); }, [options]);  // runs every render

// Fix: useMemo to stabilize, or spread the primitives
useEffect(() => { fetch(url, { method: 'GET', headers }); }, [url, headers]);
```

**Do not suppress the warning with `// eslint-disable`.** It almost always means there is a real bug. If the linter is wrong, restructure the code so the linter can understand it.

---

## Lint Rules Quick Reference

### Core Rules (always active)

| Rule | What it catches |
|------|----------------|
| `rules-of-hooks` | Hooks called conditionally, in loops, after early returns, in callbacks, or in class components |
| `exhaustive-deps` | Missing or extra dependencies in `useEffect`, `useMemo`, `useCallback` |

### React Compiler Rules

These rules are added when using React Compiler. The compiler skips components that violate them (they still work, just aren't optimized).

| Rule | What it catches |
|------|----------------|
| `purity` | Impure calls during render (`Math.random()`, `Date.now()`, `new Date()`) |
| `immutability` | Direct mutation of props, state, or hook return values |
| `globals` | Assignment or mutation of global/module-level variables during render |
| `refs` | Reading or writing `ref.current` during render |
| `set-state-in-render` | Unconditional `setState` during render (infinite loop) |
| `set-state-in-effect` | Synchronous `setState` in effects (unnecessary re-render) |
| `static-components` | Components defined inside other components (recreated every render) |
| `component-hook-factories` | Factory functions that create components or hooks |
| `error-boundaries` | `try`/`catch` around JSX instead of Error Boundaries |
| `preserve-manual-memoization` | Incomplete deps in `useMemo`/`useCallback` that block compiler optimization |
| `incompatible-library` | APIs with interior mutability that break memoization (e.g., `react-hook-form` `watch`) |
| `use-memo` | `useMemo` callback that doesn't return a value |
| `unsupported-syntax` | `eval` or `with` statements that prevent static analysis |
| `config` | Invalid React Compiler configuration options |
| `gating` | Invalid gating mode configuration for gradual compiler adoption |

---

## Common Violations and Fixes

### Impure render: `Math.random()` or `Date.now()`

```js
// Wrong
function Component() {
  const id = Math.random();
  return <div key={id}>Content</div>;
}

// Right: stable via useState initializer
function Component() {
  const [id] = useState(() => crypto.randomUUID());
  return <div key={id}>Content</div>;
}
```

### Mutating globals during render

```js
// Wrong
let count = 0;
function Component() {
  count++;  // mutates global
  return <div>{count}</div>;
}

// Right
function Component() {
  const [count, setCount] = useState(0);
  return <div>{count}</div>;
}
```

### Reading refs during render

```js
// Wrong
function Component() {
  const ref = useRef(null);
  const width = ref.current?.offsetWidth;  // ref may be stale
  return <div ref={ref}>{width}</div>;
}

// Right: read in effect or event handler
function Component() {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    if (ref.current) setWidth(ref.current.offsetWidth);
  }, []);
  return <div ref={ref}>{width}</div>;
}
```

### Unconditional setState in render

```js
// Wrong: infinite loop
function Component({ value }) {
  const [count, setCount] = useState(0);
  setCount(value);  // runs every render
  return <div>{count}</div>;
}

// Right: derive the value
function Component({ value }) {
  return <div>{value}</div>;
}

// Right: conditional update (rare, for adjusting state on prop change)
function Component({ items }) {
  const [prevItems, setPrevItems] = useState(items);
  if (items !== prevItems) {
    setPrevItems(items);
  }
}
```

### setState in effects (unnecessary re-render)

```js
// Wrong: transforming data in effect
useEffect(() => {
  setProcessed(rawData.map(transform));
}, [rawData]);

// Right: compute during render
const processed = rawData.map(transform);
```

### Components defined inside components

```js
// Wrong: Child is a new component type every render
function Parent() {
  function Child() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
  }
  return <Child />;  // state lost every render
}

// Right: define at module level, pass data as props
function Child({ theme }) {
  const [count, setCount] = useState(0);
  return <button className={theme} onClick={() => setCount(c => c + 1)}>{count}</button>;
}

function Parent() {
  const [theme] = useState('light');
  return <Child theme={theme} />;
}
```

### Factory functions for components or hooks

```js
// Wrong
function makeButton(color) {
  return function Button({ children }) {
    return <button style={{ backgroundColor: color }}>{children}</button>;
  };
}

// Right: use props
function Button({ color, children }) {
  return <button style={{ backgroundColor: color }}>{children}</button>;
}
```

### Error handling: try/catch vs Error Boundaries

```js
// Wrong: try/catch can't catch render errors
function Parent() {
  try {
    return <Child />;
  } catch (e) {
    return <div>Error</div>;  // never reached
  }
}

// Right: use Error Boundary
function Parent() {
  return (
    <ErrorBoundary fallback={<div>Error</div>}>
      <Child />
    </ErrorBoundary>
  );
}
```

### useMemo without a return value

```js
// Wrong: useMemo used for side effects (returns undefined)
const processed = useMemo(() => {
  data.forEach(item => console.log(item));
}, [data]);

// Right: return the computed value
const processed = useMemo(() => {
  return data.map(item => item * 2);
}, [data]);

// Right: use useEffect for side effects
useEffect(() => {
  data.forEach(item => console.log(item));
}, [data]);
```

### Incompatible libraries

Some libraries use interior mutability that breaks memoization. The `incompatible-library` rule flags known cases.

```js
// Flagged: react-hook-form watch() uses interior mutability
const { watch } = useForm();
const value = watch('field');

// Fix: use useWatch instead
const value = useWatch({ control, name: 'field' });
```

---

## React Compiler and Linting

React Compiler automatically memoizes components and hooks. The compiler lint rules help it work correctly:

- **Components that violate rules are skipped**, not broken. The compiler optimizes what it can and leaves the rest alone.
- **Gradual adoption.** You don't need to fix every violation before enabling the compiler. Fix them over time.
- **Manual memoization becomes optional.** With the compiler, you can remove `useMemo`, `useCallback`, and `React.memo` -- the compiler handles it. The `preserve-manual-memoization` rule ensures existing manual memoization has correct deps until you remove it.
- **`unsupported-syntax`** flags `eval` and `with` -- these prevent static analysis entirely.
- **`config` and `gating`** validate compiler configuration, not application code.
