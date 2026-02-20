# React: Effects, Refs & Custom Hooks
Based on React 19 documentation.

## Core Mental Model

Effects synchronize your component with **external systems** (network, DOM APIs, third-party libraries, timers). They are not a general-purpose "run code when something changes" mechanism.

**Ask yourself:** "Why does this code run?"
- Because the component was **displayed** --> Effect
- Because of a specific **user interaction** --> Event handler
- Because it's a **calculation** from props/state --> Compute during render

Effects have their own lifecycle, independent of components:
- **Start synchronizing** (setup function)
- **Stop synchronizing** (cleanup function)
- This cycle can repeat many times during a component's life

---

## useEffect

```js
useEffect(setup, dependencies?)
```

### Dependency Array Patterns

| Pattern | Meaning |
|---------|---------|
| `useEffect(fn, [a, b])` | Re-runs when `a` or `b` change |
| `useEffect(fn, [])` | Runs once on mount, cleanup on unmount |
| `useEffect(fn)` | Runs after every render (usually wrong) |

Dependencies are compared with `Object.is()`. All reactive values (props, state, derived values) used inside the effect must be listed.

### Cleanup Functions

Always return a cleanup function when your effect creates subscriptions, connections, or listeners:

```js
useEffect(() => {
  const connection = createConnection(serverUrl, roomId);
  connection.connect();
  return () => connection.disconnect();
}, [serverUrl, roomId]);
```

Cleanup runs:
1. Before the effect re-runs (with old values)
2. When the component unmounts

### Data Fetching with Race Condition Protection

```js
useEffect(() => {
  let ignore = false;

  fetchData(query).then(result => {
    if (!ignore) setData(result);
  });

  return () => { ignore = true; };
}, [query]);
```

### Development Double-Fire

In Strict Mode, React runs setup -> cleanup -> setup to verify your cleanup mirrors your setup. If you see bugs from this, your cleanup is incomplete.

---

## useLayoutEffect

```js
useLayoutEffect(setup, dependencies?)
```

Fires **before** the browser repaints. Use only when you need to measure DOM layout and apply changes before the user sees a flash of incorrect content.

```js
function Tooltip({ targetRect, children }) {
  const ref = useRef(null);
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    const { height } = ref.current.getBoundingClientRect();
    setHeight(height);
  }, []);

  const tooltipY = targetRect.top - height < 0
    ? targetRect.bottom
    : targetRect.top - height;

  return <div ref={ref} style={{ top: tooltipY }}>{children}</div>;
}
```

| | useEffect | useLayoutEffect |
|---|-----------|-----------------|
| Timing | After paint | Before paint |
| Blocks painting | No | Yes |
| Use case | Side effects | DOM measurement |
| SSR | Works | Does not run on server |

**Rule of thumb:** Start with `useEffect`. Switch to `useLayoutEffect` only if you see a visual flicker.

---

## useInsertionEffect

For CSS-in-JS library authors only. Fires before `useLayoutEffect`, used to inject `<style>` tags. Cannot update state or access refs.

---

## useEffectEvent

Separates reactive logic (should re-sync) from non-reactive logic (should read latest values without re-syncing):

```js
// Without useEffectEvent: reconnects when theme changes
useEffect(() => {
  const conn = createConnection(roomId);
  conn.on('connected', () => showNotification('Connected!', theme));
  conn.connect();
  return () => conn.disconnect();
}, [roomId, theme]); // theme causes unnecessary reconnection

// With useEffectEvent: reads latest theme without reconnecting
const onConnected = useEffectEvent(() => {
  showNotification('Connected!', theme);
});

useEffect(() => {
  const conn = createConnection(roomId);
  conn.on('connected', () => onConnected());
  conn.connect();
  return () => conn.disconnect();
}, [roomId]); // only roomId triggers reconnection
```

**Rules:**
- Only call Effect Events from inside effects
- Never pass them to child components or other hooks
- Never include them in the dependency array

---

## Refs (useRef)

```js
const ref = useRef(initialValue);
ref.current // read
ref.current = newValue // write (no re-render)
```

### Refs vs State

| | Ref | State |
|---|-----|-------|
| Triggers re-render | No | Yes |
| Mutable | Yes (`ref.current = x`) | No (use setter) |
| Read during render | Avoid | Safe |
| Use for | Timers, DOM, non-rendering data | Anything shown in UI |

### DOM Refs

```js
const inputRef = useRef(null);

return <input ref={inputRef} />;

// In event handler:
inputRef.current.focus();
```

### Ref Callbacks for Lists

```js
const mapRef = useRef(new Map());

{items.map(item => (
  <li
    key={item.id}
    ref={(node) => {
      mapRef.current.set(item.id, node);
      return () => mapRef.current.delete(item.id);
    }}
  />
))}
```

### Forwarding Refs to Children

```js
function MyInput({ ref }) {
  return <input ref={ref} />;
}
```

### Limiting Exposed API with useImperativeHandle

```js
function MyInput({ ref }) {
  const realRef = useRef(null);
  useImperativeHandle(ref, () => ({
    focus() { realRef.current.focus(); },
  }));
  return <input ref={realRef} />;
}
```

### flushSync for Synchronous DOM Updates

When you need to read from the DOM immediately after a state update:

```js
import { flushSync } from 'react-dom';

function handleAdd() {
  flushSync(() => {
    setTodos([...todos, newTodo]);
  });
  // DOM is now updated
  listRef.current.lastChild.scrollIntoView();
}
```

---

## You Might Not Need an Effect

This is the most common source of bugs in React applications. Most "effect" code should live elsewhere.

### Derive Values During Render

```js
// Don't
const [fullName, setFullName] = useState('');
useEffect(() => {
  setFullName(firstName + ' ' + lastName);
}, [firstName, lastName]);

// Do
const fullName = firstName + ' ' + lastName;
```

### Cache Expensive Computations with useMemo

```js
// Don't
const [filtered, setFiltered] = useState([]);
useEffect(() => {
  setFiltered(getFilteredTodos(todos, filter));
}, [todos, filter]);

// Do
const filtered = useMemo(
  () => getFilteredTodos(todos, filter),
  [todos, filter]
);
```

### Reset State with key, Not Effects

```js
// Don't
function Profile({ userId }) {
  const [comment, setComment] = useState('');
  useEffect(() => { setComment(''); }, [userId]);
}

// Do
<Profile userId={userId} key={userId} />
```

### Put Event Logic in Event Handlers

```js
// Don't: runs on mount, refresh, and navigation -- not just on buy
useEffect(() => {
  if (product.isInCart) showNotification('Added!');
}, [product]);

// Do: runs only when user clicks buy
function handleBuyClick() {
  addToCart(product);
  showNotification('Added!');
}
```

### Avoid Effect Chains

```js
// Don't: card -> goldCardCount -> round -> isGameOver (4 renders)
useEffect(() => { /* update goldCardCount */ }, [card]);
useEffect(() => { /* update round */ }, [goldCardCount]);
useEffect(() => { /* update isGameOver */ }, [round]);

// Do: calculate everything in the event handler
function handlePlaceCard(nextCard) {
  setCard(nextCard);
  if (nextCard.gold) {
    const newCount = goldCardCount + 1;
    if (newCount > 3) {
      setGoldCardCount(0);
      setRound(round + 1);
    } else {
      setGoldCardCount(newCount);
    }
  }
}
```

### Notify Parents in Event Handlers

```js
// Don't
useEffect(() => { onChange(isOn); }, [isOn, onChange]);

// Do
function handleClick() {
  const next = !isOn;
  setIsOn(next);
  onChange(next);
}
```

### Subscribe to External Stores with useSyncExternalStore

```js
// Don't: manual subscription in useEffect
useEffect(() => {
  const handler = () => setIsOnline(navigator.onLine);
  window.addEventListener('online', handler);
  window.addEventListener('offline', handler);
  return () => { /* cleanup */ };
}, []);

// Do
const isOnline = useSyncExternalStore(
  callback => {
    window.addEventListener('online', callback);
    window.addEventListener('offline', callback);
    return () => {
      window.removeEventListener('online', callback);
      window.removeEventListener('offline', callback);
    };
  },
  () => navigator.onLine,   // client
  () => true                 // server
);
```

### App Initialization

```js
// Don't: runs twice in dev, inside component lifecycle
function App() {
  useEffect(() => { checkAuth(); loadData(); }, []);
}

// Do: module-level, runs once
if (typeof window !== 'undefined') {
  checkAuth();
  loadData();
}

function App() { /* ... */ }
```

### Decision Table

| Scenario | Use Instead of Effect |
|----------|----------------------|
| Compute value from props/state | Calculate during render |
| Expensive computation | `useMemo` |
| Reset state on prop change | `key` prop |
| Handle user interaction | Event handler |
| Notify parent of state change | Event handler |
| Chain of dependent state updates | Single event handler |
| External store subscription | `useSyncExternalStore` |
| App initialization | Module-level code |

---

## Removing Effect Dependencies

When the linter complains about dependencies, fix the code -- never suppress the linter.

### Move Static Values Outside the Component

```js
const options = { serverUrl: 'https://localhost:1234', roomId: 'music' };

function ChatRoom() {
  useEffect(() => {
    const conn = createConnection(options);
    conn.connect();
    return () => conn.disconnect();
  }, []); // no dependencies needed
}
```

### Create Objects/Functions Inside the Effect

```js
// Don't: object recreated every render
const options = { serverUrl, roomId };
useEffect(() => { /* use options */ }, [options]); // re-runs every render

// Do: create inside the effect
useEffect(() => {
  const options = { serverUrl, roomId };
  const conn = createConnection(options);
  conn.connect();
  return () => conn.disconnect();
}, [serverUrl, roomId]); // depend on primitives
```

### Use State Updater Functions

```js
// Don't: messages in dependencies causes re-sync on every message
useEffect(() => {
  conn.on('message', msg => setMessages([...messages, msg]));
}, [messages]);

// Do: updater function removes the dependency
useEffect(() => {
  conn.on('message', msg => setMessages(prev => [...prev, msg]));
}, []);
```

### Extract Primitives from Object Props

```js
function ChatRoom({ options }) {
  const { roomId, serverUrl } = options;
  useEffect(() => {
    const conn = createConnection({ roomId, serverUrl });
    conn.connect();
    return () => conn.disconnect();
  }, [roomId, serverUrl]); // primitives, not the object
}
```

---

## Custom Hooks

### When to Extract

- Logic is duplicated across components
- An effect's purpose would be clearer with a descriptive name
- You want to hide synchronization details from the component

### Naming

Must start with `use` followed by a capital letter. Only use the `use` prefix if the function calls other hooks.

### Pattern

```js
function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);
  useEffect(() => {
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);
  return isOnline;
}
```

### Passing Event Handlers Safely

Wrap callbacks with `useEffectEvent` inside the custom hook so callers don't cause re-syncs:

```js
function useChatRoom({ serverUrl, roomId, onMessage }) {
  const onMsg = useEffectEvent(onMessage);

  useEffect(() => {
    const conn = createConnection({ serverUrl, roomId });
    conn.on('message', msg => onMsg(msg));
    conn.connect();
    return () => conn.disconnect();
  }, [serverUrl, roomId]); // onMessage not a dependency
}
```

### Common Custom Hooks

```js
// Data fetching
function useData(url) {
  const [data, setData] = useState(null);
  useEffect(() => {
    if (!url) return;
    let ignore = false;
    fetch(url)
      .then(res => res.json())
      .then(json => { if (!ignore) setData(json); });
    return () => { ignore = true; };
  }, [url]);
  return data;
}

// Form input
function useFormInput(initial) {
  const [value, setValue] = useState(initial);
  return { value, onChange: e => setValue(e.target.value) };
}

// Interval
function useInterval(callback, delay) {
  const onTick = useEffectEvent(callback);
  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => onTick(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
```

### Avoid Generic Lifecycle Wrappers

```js
// Don't: these hide intent
function useMount(fn) { useEffect(fn, []); }
function useEffectOnce(fn) { useEffect(fn, []); }

// Do: name after specific purpose
function useChatRoom(options) { /* ... */ }
function useMediaQuery(query) { /* ... */ }
function useIntersectionObserver(ref, options) { /* ... */ }
```

---

## Quick Reference: Which Hook to Use

| Need | Hook |
|------|------|
| Sync with external system | `useEffect` |
| Measure DOM before paint | `useLayoutEffect` |
| Inject styles (library authors) | `useInsertionEffect` |
| Non-reactive logic in effects | `useEffectEvent` |
| Store value without re-render | `useRef` |
| Access DOM node | `useRef` + JSX `ref` prop |
| Limit exposed ref API | `useImperativeHandle` |
| Subscribe to external store | `useSyncExternalStore` |
| Cache expensive computation | `useMemo` |
| Reusable effect logic | Custom Hook |
