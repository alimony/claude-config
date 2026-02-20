# React: State Management Hooks
Based on React 19 documentation.

## Core Concepts

State is React's mechanism for component memory. Regular variables reset on every render; state persists across renders and triggers re-renders when updated. State is private to each component instance and tied to position in the render tree.

Key rules:
- Hooks must be called at the **top level** of components or custom hooks -- never inside loops, conditions, or nested functions
- React tracks state by **call order**, so the hook sequence must be identical on every render
- State updates are **asynchronous** -- the new value is available on the next render, not immediately
- React **batches** multiple state updates from the same event handler into one re-render
- State equality is checked with `Object.is` -- same reference means no re-render

---

## useState

```jsx
const [value, setValue] = useState(initialValue);
```

### Lazy initialization

```jsx
// BAD: createExpensiveData() runs every render
const [data, setData] = useState(createExpensiveData());

// GOOD: function reference, runs only on first render
const [data, setData] = useState(createExpensiveData);
```

### Functional updates (when new state depends on previous state)

```jsx
// BAD: uses stale snapshot, only increments once
function handleTripleClick() {
  setCount(count + 1);
  setCount(count + 1);
  setCount(count + 1);
}

// GOOD: each updater receives latest pending state
function handleTripleClick() {
  setCount(c => c + 1);
  setCount(c => c + 1);
  setCount(c => c + 1);
}
```

### Storing functions in state

```jsx
// BAD: React calls this as an initializer
const [fn, setFn] = useState(myFunction);

// GOOD: wrap in arrow function
const [fn, setFn] = useState(() => myFunction);
setFn(() => someOtherFunction);
```

---

## Updating Objects in State

State objects are **immutable** -- never mutate, always replace.

```jsx
// BAD: mutation, no re-render
person.name = 'Taylor';
setPerson(person);

// GOOD: new object via spread
setPerson({ ...person, name: 'Taylor' });
```

### Nested objects -- copy at every level

```jsx
setPerson({
  ...person,
  artwork: {
    ...person.artwork,
    city: 'New Delhi',
  },
});
```

Local mutation is fine for freshly created objects before passing them to the setter.

---

## Updating Arrays in State

| Operation | Mutates (avoid) | Immutable (use) |
|-----------|----------------|-----------------|
| Add | `push`, `unshift` | `[...arr, item]`, `concat` |
| Remove | `pop`, `shift`, `splice` | `filter`, `slice` |
| Replace | `splice`, `arr[i] = x` | `map` |
| Sort | `sort`, `reverse` | Copy first: `[...arr].sort()` |

```jsx
setItems([...items, newItem]);                                          // add
setItems(items.filter(i => i.id !== targetId));                         // remove
setItems(items.map(i => i.id === targetId ? { ...i, done: true } : i)); // replace
setItems([...items.slice(0, idx), newItem, ...items.slice(idx)]);       // insert
setItems([...items].sort((a, b) => a.name.localeCompare(b.name)));      // sort
```

Shallow copy of an array still shares object references. Use `map` + spread to update objects inside arrays (see replace pattern above).

### Immer for complex updates

```jsx
import { useImmer } from 'use-immer';

const [items, updateItems] = useImmer(initialItems);

updateItems(draft => {
  const item = draft.find(i => i.id === targetId);
  item.done = true; // looks like mutation, produces immutable update
});
```

---

## useReducer

Use when state logic is complex, involves multiple sub-values, or when actions describe "what happened" rather than "how to update."

```jsx
const [state, dispatch] = useReducer(reducer, initialState);
const [state, dispatch] = useReducer(reducer, initialArg, initFn); // lazy init
```

### Writing a reducer

```jsx
function tasksReducer(tasks, action) {
  switch (action.type) {
    case 'added':
      return [...tasks, { id: action.id, text: action.text, done: false }];
    case 'toggled':
      return tasks.map(t => t.id === action.id ? { ...t, done: !t.done } : t);
    case 'deleted':
      return tasks.filter(t => t.id !== action.id);
    default:
      throw new Error('Unknown action: ' + action.type);
  }
}
```

### Reducer best practices

- **Pure functions** -- no side effects, no API calls, no timeouts
- **One action per user interaction** -- dispatch `'reset_form'`, not three separate field clears
- **Actions describe what happened**, not how to update -- `'changed_selection'` not `'setSelectedId'`
- **Throw on unknown actions** to catch bugs early
- **Wrap each case in braces** to avoid variable scoping issues
- Use `useImmerReducer` from `use-immer` to simplify nested updates

### useState vs useReducer

| Factor | useState | useReducer |
|--------|----------|------------|
| Simple values | Preferred | Overkill |
| Complex / related state | Gets messy | Clean separation |
| Debugging | Hard to trace | Log every action |
| Testing | Needs component | Pure function, test in isolation |
| Code size | Less boilerplate | More upfront, scales better |

---

## useContext

Reads context provided by an ancestor. Avoids prop drilling.

```jsx
// 1. Create
const ThemeContext = createContext('light');

// 2. Provide (in a parent)
<ThemeContext value={theme}>
  <App />
</ThemeContext>

// 3. Consume (in any descendant)
const theme = useContext(ThemeContext);
```

### Key behaviors

- Returns the value from the **nearest** provider above in the tree
- If no provider exists, returns the `createContext` default value
- Re-renders all consumers when the provider value changes (regardless of `memo`)
- Providers can be nested to override values for subtrees

### Avoiding unnecessary re-renders

```jsx
// BAD: new object every render, all consumers re-render
<AuthContext value={{ user, login }}>

// GOOD: memoize the context value
const contextValue = useMemo(() => ({ user, login }), [user, login]);
<AuthContext value={contextValue}>
```

### Common mistake -- provider in the same component

```jsx
// BAD: useContext in the same component that provides won't see its own provider
function App() {
  const theme = useContext(ThemeContext); // reads from ABOVE, not below
  return <ThemeContext value="dark">...</ThemeContext>;
}
```

---

## Reducer + Context Pattern

The standard pattern for scaled state management without external libraries.

```jsx
// TasksContext.js
import { createContext, useContext, useReducer } from 'react';

const TasksContext = createContext(null);
const TasksDispatchContext = createContext(null);

export function TasksProvider({ children }) {
  const [tasks, dispatch] = useReducer(tasksReducer, initialTasks);
  return (
    <TasksContext value={tasks}>
      <TasksDispatchContext value={dispatch}>
        {children}
      </TasksDispatchContext>
    </TasksContext>
  );
}

// Custom hooks for clean consumption
export function useTasks() {
  return useContext(TasksContext);
}
export function useTasksDispatch() {
  return useContext(TasksDispatchContext);
}
```

```jsx
// Usage -- any descendant, no prop drilling
function TaskList() {
  const tasks = useTasks();
  const dispatch = useTasksDispatch();
  // ...
}
```

Separate contexts for state and dispatch so components that only dispatch do not re-render when state changes.

---

## useActionState

For async actions with built-in pending state. React 19+.

```jsx
const [state, dispatchAction, isPending] = useActionState(action, initialState);
```

### With forms

```jsx
async function submitForm(prevState, formData) {
  const error = await saveToServer(formData);
  if (error) return { error };
  return { success: true };
}

function MyForm() {
  const [state, formAction, isPending] = useActionState(submitForm, { error: null });

  return (
    <form action={formAction}>
      <input name="title" />
      <button disabled={isPending}>{isPending ? 'Saving...' : 'Save'}</button>
      {state.error && <p>{state.error}</p>}
    </form>
  );
}
```

Without forms, wrap calls in `startTransition(() => { dispatchAction(payload); })`.

### Key differences from useReducer

- Action function **can be async** and **can have side effects**
- Returns `isPending` for loading states
- Actions are **queued sequentially** (each receives previous result)
- First argument to action is `previousState`, second is the payload
- Handle expected errors by returning error state, not throwing

---

## useOptimistic

Shows an optimistic value while an async action is pending. Automatically reverts when the action finishes.

```jsx
const [optimisticValue, setOptimistic] = useOptimistic(actualValue);
```

### Basic pattern

```jsx
const [todos, setTodos] = useState(serverTodos);
const [optimisticTodos, addOptimistic] = useOptimistic(
  todos,
  (current, newTodo) => [...current, { ...newTodo, pending: true }]
);

function handleAdd(text) {
  startTransition(async () => {
    addOptimistic({ text });           // instant UI update
    const saved = await saveTodo(text); // server call
    setTodos(prev => [...prev, saved]); // real update, optimistic reverts
  });
}
```

If the async action fails, the optimistic value automatically reverts (the actual state never changed). Catch errors to show user feedback. Must be called inside `startTransition` or a form action.

---

## State Structure Best Practices

### 1. Group related state

```jsx
// BAD: always updated together
const [x, setX] = useState(0);
const [y, setY] = useState(0);

// GOOD: single object
const [position, setPosition] = useState({ x: 0, y: 0 });
```

### 2. Avoid contradictory state

```jsx
// BAD: isSending and isSent can both be true
const [isSending, setIsSending] = useState(false);
const [isSent, setIsSent] = useState(false);

// GOOD: single status enum
const [status, setStatus] = useState('idle'); // 'idle' | 'sending' | 'sent'
```

### 3. Avoid redundant state -- derive instead

```jsx
// BAD: fullName must be kept in sync manually
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [fullName, setFullName] = useState('');

// GOOD: computed on render
const fullName = firstName + ' ' + lastName;
```

### 4. Avoid duplicating data -- store IDs, derive objects

```jsx
// BAD: selectedItem duplicates data from items
const [items, setItems] = useState(list);
const [selectedItem, setSelectedItem] = useState(list[0]);

// GOOD: store only the ID
const [selectedId, setSelectedId] = useState(list[0].id);
const selectedItem = items.find(i => i.id === selectedId);
```

### 5. Flatten nested state

Normalize deeply nested trees into flat maps keyed by ID (like a database). Store `childIds: [1, 2]` instead of nesting child objects. This makes updates to any node a simple property copy instead of rebuilding the entire tree.

### 6. Do not mirror props into state

```jsx
// BAD: state won't update when prop changes
function Message({ messageColor }) {
  const [color, setColor] = useState(messageColor);
}

// GOOD: use prop directly, or name with "initial" prefix if intentional
function Message({ initialColor }) {
  const [color, setColor] = useState(initialColor); // intentionally ignores updates
}
```

---

## Preserving and Resetting State

React preserves state based on **position in the render tree**, not variable names or JSX placement.

### Same component at same position = state preserved

```jsx
// Toggling isFancy does NOT reset Counter state
{isFancy ? <Counter isFancy={true} /> : <Counter isFancy={false} />}
```

### Different component at same position = state reset

```jsx
// Switching between Counter and p destroys Counter's state
{isPaused ? <p>Paused</p> : <Counter />}
```

### Force reset with key

```jsx
// Key change tells React these are different instances
<Chat key={recipientId} contact={recipient} />
```

### Never nest component definitions

```jsx
// BAD: MyInput is recreated every render, state lost
function Form() {
  function MyInput() { /* ... */ }
  return <MyInput />;
}

// GOOD: define at module level
function MyInput() { /* ... */ }
function Form() {
  return <MyInput />;
}
```

---

## Lifting State Up

When sibling components need to share state, move it to their closest common parent.

```jsx
function Accordion() {
  const [activeIndex, setActiveIndex] = useState(0);
  return (
    <>
      <Panel isActive={activeIndex === 0} onShow={() => setActiveIndex(0)}>...</Panel>
      <Panel isActive={activeIndex === 1} onShow={() => setActiveIndex(1)}>...</Panel>
    </>
  );
}

function Panel({ isActive, onShow, children }) {
  return isActive ? <p>{children}</p> : <button onClick={onShow}>Show</button>;
}
```

**Controlled** component = driven by props (parent owns state).
**Uncontrolled** component = driven by local state (component owns state).
Each piece of state should have exactly one owner -- single source of truth.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Reading state right after setting it | Stale value logged | Save to variable: `const next = count + 1; setCount(next);` |
| Mutating objects/arrays | UI does not update | Always create new references with spread or `map`/`filter` |
| Passing initializer with parens | Expensive function runs every render | `useState(fn)` not `useState(fn())` |
| Calling handler during render | "Too many re-renders" | `onClick={handleClick}` not `onClick={handleClick()}` |
| Index as list key | State follows wrong items after reorder | Use stable unique IDs as keys |
| Nesting component definitions | State resets on every parent render | Define components at module scope |
| Missing `value` on context provider | Consumers get `undefined` | `<MyContext value={val}>` -- `value` prop is required |
| Object identity in context value | All consumers re-render on every parent render | Memoize with `useMemo` |
| Contradictory boolean flags | Impossible states | Replace with a single status string/enum |
| Duplicated data in state | Values fall out of sync | Store IDs, derive objects |

---

## Hook Selection Guide

| Situation | Hook |
|-----------|------|
| Simple value (string, number, boolean) | `useState` |
| Object or array that changes shape | `useState` + spread / `useImmer` |
| Complex logic, multiple action types | `useReducer` |
| State needed by distant descendants | `useContext` + `useReducer` |
| Async action with loading indicator | `useActionState` |
| Instant UI feedback during async work | `useOptimistic` |
