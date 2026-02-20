# React: Fundamentals
Based on React 19 documentation.

## Components

A React component is a JavaScript function that returns JSX. Component names **must start with a capital letter** -- React uses this to distinguish custom components from HTML tags.

```jsx
function Greeting({ name }) {
  return <h1>Hello, {name}</h1>;
}

export default function App() {
  return (
    <section>
      <Greeting name="Alice" />
      <Greeting name="Bob" />
    </section>
  );
}
```

### Exports

| Pattern | Export | Import |
|---------|--------|--------|
| Default (one per file) | `export default function Button() {}` | `import Button from './Button'` |
| Named (multiple per file) | `export function Button() {}` | `import { Button } from './Button'` |

Default imports can use any name; named imports must match exactly. Pick one style per file to avoid confusion.

### Never Nest Component Definitions

```jsx
// BAD: Profile is redefined every render, destroying state
function Gallery() {
  function Profile() { return <img src="..." />; }
  return <Profile />;
}

// GOOD: define at the top level
function Profile() { return <img src="..." />; }
function Gallery() { return <Profile />; }
```

---

## JSX Rules

### 1. Single Root Element

A component must return one root element. Use a Fragment (`<>...</>`) to avoid extra DOM nodes.

```jsx
// BAD: multiple roots
return (
  <h1>Title</h1>
  <p>Body</p>
);

// GOOD: fragment wrapper
return (
  <>
    <h1>Title</h1>
    <p>Body</p>
  </>
);
```

### 2. Close All Tags

Self-closing tags require a slash: `<img />`, `<br />`, `<input />`.

### 3. camelCase Attributes

HTML `class` becomes `className`. Dashed attributes become camelCase (`stroke-width` becomes `strokeWidth`). Exceptions: `aria-*` and `data-*` keep dashes.

### Expressions in JSX

Curly braces open a JavaScript window inside JSX. They work as **text content** and as **attribute values**.

```jsx
const url = '/avatar.png';
const name = 'Alice';
return <img src={url} alt={`Photo of ${name}`} />;
```

Double braces are just an object inside curly braces -- common for inline styles:

```jsx
<div style={{ backgroundColor: 'black', color: 'pink' }}>
  {formatDate(today)}
</div>
```

### Multi-line Return

Wrap multi-line JSX in parentheses. Without them, JavaScript's automatic semicolon insertion silently breaks the return.

```jsx
return (
  <div>
    <h1>Title</h1>
  </div>
);
```

---

## Props

Props are the arguments to a component function. Any JavaScript value works -- objects, arrays, functions, JSX.

### Destructuring and Defaults

```jsx
function Avatar({ src, size = 100, alt = '' }) {
  return <img src={src} width={size} height={size} alt={alt} />;
}
```

Defaults apply when a prop is `undefined` or missing. They do **not** apply for `null` or `0`.

### Spreading Props

Forward all props to a child when a component is a thin wrapper:

```jsx
function Card(props) {
  return <div className="card"><Avatar {...props} /></div>;
}
```

Use sparingly. Overuse signals the component should be split or children passed as JSX.

### Children

Nest JSX inside a component to pass it as the `children` prop:

```jsx
function Card({ children }) {
  return <div className="card">{children}</div>;
}

<Card>
  <Avatar src="/alice.png" />
  <p>Alice is a developer.</p>
</Card>
```

### Props Are Read-Only

A component never modifies its own props. When data needs to change, the parent passes new props and React re-renders the child.

---

## Conditional Rendering

### if/else -- Different Return Paths

```jsx
function Item({ name, isPacked }) {
  if (isPacked) {
    return <li className="item">{name} (packed)</li>;
  }
  return <li className="item">{name}</li>;
}
```

### Ternary -- Inline Choice

```jsx
<li>{isPacked ? <del>{name}</del> : name}</li>
```

### Logical AND -- Render or Nothing

```jsx
<li>{name} {isPacked && '(packed)'}</li>
```

**Pitfall: falsy numbers render as text.**

```jsx
// BAD: renders "0" when count is 0
{count && <span>New messages</span>}

// GOOD: renders nothing when count is 0
{count > 0 && <span>New messages</span>}
```

### Variable Assignment -- Complex Logic

```jsx
let content = name;
if (isPacked) {
  content = <del>{name}</del>;
}
return <li>{content}</li>;
```

---

## Rendering Lists

Use `map()` to transform arrays into JSX. Use `filter()` to select items first.

```jsx
function TodoList({ todos }) {
  return (
    <ul>
      {todos
        .filter(todo => !todo.done)
        .map(todo => (
          <li key={todo.id}>{todo.text}</li>
        ))}
    </ul>
  );
}
```

### Multiple DOM Nodes Per Item

Use `<Fragment>` with an explicit `key` (the `<>` shorthand does not accept keys):

```jsx
import { Fragment } from 'react';

{items.map(item => (
  <Fragment key={item.id}>
    <dt>{item.term}</dt>
    <dd>{item.definition}</dd>
  </Fragment>
))}
```

### Arrow Function Bodies

```jsx
// BAD: block body without return -- renders nothing
items.map(item => { <li>{item.name}</li> });

// GOOD: explicit return
items.map(item => { return <li>{item.name}</li>; });

// GOOD: implicit return (parentheses, no braces)
items.map(item => (
  <li>{item.name}</li>
));
```

---

## Keys

Keys tell React which array item corresponds to which component across re-renders. Without stable keys, React falls back to position, which breaks when items are reordered, inserted, or deleted.

### Rules

1. **Unique among siblings.** Keys can repeat across different arrays.
2. **Stable.** Never generate during render (`Math.random()`, `crypto.randomUUID()` at render time).
3. **From the data.** Use database IDs, slugs, or other data-derived identifiers.

### Don't Use Array Index

```jsx
// BAD: indices shift when items are reordered or deleted
{items.map((item, index) => <li key={index}>{item.name}</li>)}

// GOOD: stable, data-derived key
{items.map(item => <li key={item.id}>{item.name}</li>)}
```

Index-as-key causes: lost input state, wrong animations, stale component data after reorder.

### Keys Are Not Props

React consumes `key` internally. If a child component needs the ID, pass it as a separate prop:

```jsx
<Profile key={user.id} userId={user.id} />
```

---

## Event Handling

Define a handler function inside the component and **pass it** (don't call it) to the event prop.

```jsx
function SubmitButton() {
  function handleClick() {
    alert('Submitted!');
  }
  return <button onClick={handleClick}>Submit</button>;
}
```

### Naming Convention

- Handler functions: `handle` + event name (`handleClick`, `handleSubmit`)
- Handler props on custom components: `on` + event name (`onClick`, `onSubmit`)

### Inline Handlers

```jsx
<button onClick={() => alert('Clicked!')}>Click</button>
```

### Passing Handlers to Children

```jsx
function Toolbar({ onPlay, onUpload }) {
  return (
    <div>
      <Button onClick={onPlay}>Play</Button>
      <Button onClick={onUpload}>Upload</Button>
    </div>
  );
}
```

### Common Mistake: Calling vs Passing

```jsx
// BAD: calls handleClick immediately during render
<button onClick={handleClick()}>Click</button>

// GOOD: passes a reference, called on click
<button onClick={handleClick}>Click</button>

// GOOD: arrow wrapper when you need arguments
<button onClick={() => handleClick(id)}>Click</button>
```

### Event Propagation

Events bubble up from child to parent. Use `e.stopPropagation()` to stop bubbling. Use `e.preventDefault()` to prevent browser defaults (form submission, link navigation).

```jsx
function handleSubmit(e) {
  e.preventDefault(); // stop page reload
  // process form data
}

<form onSubmit={handleSubmit}>
  <button onClick={(e) => {
    e.stopPropagation(); // don't trigger parent's onClick
    doSomething();
  }}>
    Submit
  </button>
</form>
```

`onScroll` is the only React event that does not bubble.

### Capture Phase

Use `onClickCapture` (instead of `onClick`) to handle events during the capture phase, before bubbling. Useful for analytics or routing logic that must run even if children stop propagation.

---

## Rendering Model

React updates the UI in three steps:

### 1. Trigger

- **Initial render:** `createRoot(el).render(<App />)`
- **Re-render:** a component's state changes via a setter function

### 2. Render

React calls your component function to compute what the UI should look like. This is recursive -- if a component returns other components, React renders those too.

**Rendering must be pure:**
- Same props and state produce the same JSX.
- No side effects (no DOM manipulation, no network requests, no mutations of external variables).

### 3. Commit

React applies the **minimal necessary DOM changes**. On initial render, all nodes are created. On re-renders, only nodes whose output actually changed are updated. Unchanged elements keep their state (input values, focus, scroll position).

After commit, the browser repaints.

### Batching

React processes all state updates from a single event handler as a batch, then re-renders once. This means state values are **snapshots** -- within an event handler, the state variable holds the value from before any setter calls in that handler.

```jsx
function handleClick() {
  setCount(count + 1); // count is still 0
  setCount(count + 1); // count is still 0
  // result: count becomes 1, not 2
}
```

Use **updater functions** to queue multiple updates based on previous state:

```jsx
function handleClick() {
  setCount(c => c + 1); // 0 -> 1
  setCount(c => c + 1); // 1 -> 2
  // result: count becomes 2
}
```

---

## Component Purity

React requires that components behave as pure functions during rendering. A pure component:

1. **Minds its own business** -- does not mutate variables or objects that existed before the call.
2. **Same inputs, same output** -- given the same props and state, always returns the same JSX.

### Local Mutation Is Fine

Creating and modifying variables **within** a render is not a side effect:

```jsx
function TodoList() {
  const items = []; // created this render
  for (let i = 0; i < 5; i++) {
    items.push(<li key={i}>Item {i}</li>);
  }
  return <ul>{items}</ul>;
}
```

### Shared Mutation Is Not

```jsx
// BAD: mutates variable outside the component
let guest = 0;
function Cup() {
  guest = guest + 1;
  return <h2>Cup for guest #{guest}</h2>;
}
```

Fix: pass data as props instead.

### Where Side Effects Go

| Location | Side Effects Allowed? |
|----------|----------------------|
| During render (component body) | No |
| Event handlers (`handleClick`, etc.) | Yes |
| `useEffect` (last resort) | Yes |

### StrictMode

In development, React calls components twice to surface impure code. If a component is pure, double-invocation produces identical results and the extra call is invisible.

---

## Thinking in React

The five-step process for building a React UI:

### 1. Break UI into a Component Hierarchy

Each component should have one responsibility. If it grows too large, decompose it. Well-structured data naturally maps to component structure.

### 2. Build a Static Version First

Render the UI from data using only **props** -- no state, no interactivity. Build top-down for simple UIs, bottom-up for complex ones. This separates the structural work from the interactive work.

### 3. Find the Minimal State

For each piece of data, ask:
- Does it stay the same over time? --> not state
- Is it passed from a parent via props? --> not state
- Can you compute it from existing state or props? --> not state

Everything else is state. Keep it minimal -- derive the rest.

### 4. Decide Where State Lives

Find every component that renders based on a piece of state. Place that state in their **closest common parent**. Data flows down via props; there is no upward data flow through props.

### 5. Add Inverse Data Flow

Pass setter functions (callbacks) down as props so child components can update parent state:

```jsx
function SearchBar({ filterText, onFilterTextChange }) {
  return (
    <input
      value={filterText}
      onChange={e => onFilterTextChange(e.target.value)}
    />
  );
}

function App() {
  const [filterText, setFilterText] = useState('');
  return <SearchBar filterText={filterText} onFilterTextChange={setFilterText} />;
}
```

---

## UI as a Tree

### Render Tree

The component hierarchy forms a tree. The root component is at the top, leaf components (those rendering only HTML) are at the bottom. Understanding this tree helps with:

- **Data flow**: props flow downward, callbacks flow upward.
- **Performance**: top-level re-renders cascade to all descendants. Leaf components re-render most often.
- **Conditional rendering**: the tree shape can change across renders.

### Module Dependency Tree

Import statements form a separate tree of file dependencies. Bundlers use this tree to determine what code to ship. Large dependency trees mean larger bundles and slower load times.

---

## Declarative UI Model

React is declarative: you describe **what** the UI should look like for each state, not **how** to manipulate the DOM step by step.

1. **Identify visual states** (empty, loading, success, error).
2. **Determine triggers** (user input, network response).
3. **Model with state** -- use a single status variable over multiple booleans to avoid impossible combinations.
4. **Derive what you can** -- compute values from state rather than storing redundant data.
5. **Connect event handlers** to transition between states.

```jsx
// BAD: multiple booleans can conflict
const [isLoading, setIsLoading] = useState(false);
const [isError, setIsError] = useState(false);
const [isSuccess, setIsSuccess] = useState(false);

// GOOD: single status prevents impossible states
const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
```

---

## Common Pitfalls Summary

| Pitfall | Fix |
|---------|-----|
| Lowercase component name (`<myButton>`) | Capitalize: `<MyButton>` |
| Nesting component definitions | Define all components at the top level |
| `class` attribute in JSX | Use `className` |
| Unclosed self-closing tags (`<img>`) | Add slash: `<img />` |
| Multi-line return without parentheses | Wrap in `( )` |
| `{count && <X />}` renders `0` | Use `{count > 0 && <X />}` |
| Array index as key | Use stable, data-derived keys |
| `onClick={handleClick()}` calls immediately | Pass reference: `onClick={handleClick}` |
| Mutating props or external variables in render | Use state; keep render pure |
| Multiple boolean state variables for one status | Use a single string/enum status |
| `key` used as a prop inside the component | Pass the value as a separate prop too |
| `map()` with block body and no `return` | Add explicit `return` or use parentheses |
