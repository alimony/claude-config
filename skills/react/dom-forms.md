# React: DOM & Form Components
Based on React 19 documentation.

## Controlled vs Uncontrolled Inputs

Use **controlled** when you need real-time validation, conditional UI, or programmatic value changes. Use **uncontrolled** for simple forms where you only read values on submit.

| Feature | Uncontrolled | Controlled |
|---------|-------------|------------|
| Set initial value | `defaultValue` / `defaultChecked` | `value` + `useState` |
| Who owns the value | The DOM | React state |
| Read value | On submit via `FormData` | Anytime from state |
| Use case | Simple forms, progressive enhancement | Validation, formatting, dependent fields |
| Required handler | None | `onChange` (mandatory) |

### Controlled pattern

```jsx
function NameInput() {
  const [name, setName] = useState('');
  return (
    <input value={name} onChange={e => setName(e.target.value)} />
  );
}
```

### Uncontrolled pattern

```jsx
function NameInput() {
  return <input name="name" defaultValue="Jane" />;
}
```

**Rule**: An input cannot switch between controlled and uncontrolled during its lifetime. Pick one.

---

## Form Actions (React 19)

React 19 lets you pass a function to `<form action>`. The function receives `FormData` directly. It runs inside a Transition, enabling pending states, optimistic updates, and error handling.

### Basic client action

```jsx
function SearchForm() {
  function search(formData) {
    const query = formData.get('query');
    alert(`Searched for: ${query}`);
  }
  return (
    <form action={search}>
      <input name="query" />
      <button type="submit">Search</button>
    </form>
  );
}
```

### Server action with progressive enhancement

```jsx
function AddToCart({ productId }) {
  async function addToCart(formData) {
    'use server';
    await updateCart(formData.get('productId'));
  }
  return (
    <form action={addToCart}>
      <input type="hidden" name="productId" value={productId} />
      <button type="submit">Add to Cart</button>
    </form>
  );
}
```

Server Functions work without JS enabled -- the form falls back to native POST.

### Passing extra arguments with `.bind()`

```jsx
const boundAction = addToCart.bind(null, productId);
// addToCart receives (productId, formData) instead of just (formData)
<form action={boundAction}><button type="submit">Add</button></form>
```

### Multiple submit actions with `formAction`

```jsx
<form action={publish}>
  <textarea name="content" rows={4} cols={40} />
  <button type="submit">Publish</button>
  <button formAction={saveDraft}>Save Draft</button>
</form>
```

**Caveat**: When `action` is a function, the HTTP method is always POST regardless of the `method` prop.

---

## useActionState

Manages form action state including return values and pending status. The action receives `(previousState, formData)` and its return value becomes the new state.

```jsx
import { useActionState } from 'react';

export default function Signup() {
  async function signup(prevState, formData) {
    'use server';
    try {
      await signUpNewUser(formData.get('email'));
      return null;
    } catch (err) {
      return err.toString();
    }
  }
  const [errorMessage, signupAction] = useActionState(signup, null);
  return (
    <form action={signupAction}>
      <input name="email" type="email" required />
      <button type="submit">Sign Up</button>
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </form>
  );
}
```

---

## useFormStatus

Shows pending state during form submission. **Must be called from a child component** rendered inside the `<form>`, not the component that renders the form itself.

```jsx
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting...' : 'Submit'}
    </button>
  );
}

// Usage: SubmitButton must be INSIDE a <form>
function MyForm() {
  return (
    <form action={submitAction}>
      <input name="email" type="email" />
      <SubmitButton />
    </form>
  );
}
```

**Returns** an object with:

| Property | Type | Description |
|----------|------|-------------|
| `pending` | `boolean` | `true` while the parent form is submitting |
| `data` | `FormData \| null` | The form data being submitted |
| `method` | `string` | `'get'` or `'post'` |
| `action` | `function \| null` | Reference to the action function |

**Common mistake** -- calling `useFormStatus` in the same component that renders the `<form>`. It only reads status from a *parent* form. Extract the button into its own component.

---

## Optimistic Updates with useOptimistic

Show expected results immediately while the server action is in flight.

```jsx
function Chat({ messages, sendMessage }) {
  const formRef = useRef();
  const [optimistic, addOptimistic] = useOptimistic(messages,
    (state, newMsg) => [...state, { text: newMsg, sending: true }]);

  async function handleAction(formData) {
    addOptimistic(formData.get('message'));
    formRef.current.reset();
    await sendMessage(formData);
  }
  return (
    <form action={handleAction} ref={formRef}>
      {optimistic.map((msg, i) => (
        <p key={i}>{msg.text}{msg.sending && <em> (sending...)</em>}</p>
      ))}
      <input name="message" /><button type="submit">Send</button>
    </form>
  );
}
```

---

## Error Handling

### With useActionState (preferred for progressive enhancement)

Return error state from the action function (see useActionState section above).

### With Error Boundaries

```jsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary fallback={<p>Something went wrong.</p>}>
  <form action={riskyAction}>
    <button type="submit">Go</button>
  </form>
</ErrorBoundary>
```

---

## Form Element Quick Reference

### `<input>` key props

| Prop | Controlled | Uncontrolled | Notes |
|------|-----------|-------------|-------|
| `value` | Yes | -- | For text types. Always pass a string, never `null`/`undefined`. |
| `checked` | Yes | -- | For checkbox/radio. |
| `defaultValue` | -- | Yes | Initial text value. |
| `defaultChecked` | -- | Yes | Initial checked state. |
| `onChange` | Required | Optional | Read `e.target.value` (text) or `e.target.checked` (checkbox). |
| `name` | Always include | Always include | Key for FormData on submit. |
| `type` | -- | -- | `text`, `email`, `number`, `password`, `checkbox`, `radio`, `file`, etc. |
| `required` | -- | -- | Native validation. |
| `disabled` | -- | -- | Prevents interaction. |
| `placeholder` | -- | -- | Hint text shown when empty. |

### `<select>` key props

```jsx
// Uncontrolled
<select name="color" defaultValue="blue">
  <option value="red">Red</option>
  <option value="blue">Blue</option>
</select>

// Controlled
<select value={color} onChange={e => setColor(e.target.value)}>
  <option value="red">Red</option>
  <option value="blue">Blue</option>
</select>

// Multiple
<select multiple defaultValue={['red', 'blue']}>
  <option value="red">Red</option>
  <option value="blue">Blue</option>
  <option value="green">Green</option>
</select>
```

**Do not** use the `selected` attribute on `<option>`. Use `defaultValue`/`value` on the parent `<select>`.

### `<textarea>` key props

```jsx
// Uncontrolled
<textarea name="bio" defaultValue="Hello" rows={4} />

// Controlled
<textarea value={bio} onChange={e => setBio(e.target.value)} />
```

**Do not** pass children to `<textarea>`. Use `defaultValue` instead.

### `<progress>`

```jsx
<progress value={0.7} />              {/* 70% complete */}
<progress value={75} max={100} />     {/* 75% complete */}
<progress value={null} />             {/* Indeterminate / loading */}
```

---

## Accessibility Essentials

### Labels

```jsx
// Wrapping (simplest)
<label>Email: <input name="email" type="email" /></label>

// With htmlFor + useId (for separate elements)
const id = useId();
<label htmlFor={id}>Email:</label>
<input id={id} name="email" type="email" />
```

### ARIA and focus

```jsx
<input aria-label="Search" aria-describedby="help-text" />
<button aria-pressed={isActive} role="switch">Toggle</button>
```

- `tabIndex={0}` -- include in natural tab order
- `tabIndex={-1}` -- programmatically focusable only
- `autoFocus` -- focus on mount (use sparingly)

---

## Common Event Handlers

| Event | Fires when | Typical use |
|-------|-----------|-------------|
| `onChange` | Value changes (React fires on every keystroke) | Controlled input state updates |
| `onSubmit` | Form is submitted | Form handling with `e.preventDefault()` |
| `onFocus` / `onBlur` | Element gains/loses focus | Validation, show/hide helpers |
| `onKeyDown` / `onKeyUp` | Key pressed/released | Keyboard shortcuts, Enter-to-submit |
| `onInvalid` | Native validation fails | Custom validation messages |

Note: In React, `onFocus` and `onBlur` **bubble** (unlike native DOM).

---

## Reading Form Data on Submit (Without Controlled State)

```jsx
function handleSubmit(e) {
  e.preventDefault();
  const data = new FormData(e.target);
  const values = Object.fromEntries(data.entries());
  // { name: "...", email: "..." }
}
<form onSubmit={handleSubmit}>
  <input name="name" /><input name="email" type="email" />
  <button type="submit">Send</button>
</form>
```

For `<select multiple>`, use `[...data.entries()]` instead of `Object.fromEntries` (which drops duplicate keys).

---

## Common Pitfalls

### 1. Controlled input value is `undefined` or `null`

```jsx
// DON'T -- switches from uncontrolled to controlled
const [val, setVal] = useState(undefined);
<input value={val} onChange={e => setVal(e.target.value)} />

// DO -- always initialize with a string
const [val, setVal] = useState('');
<input value={val} onChange={e => setVal(e.target.value)} />
```

### 2. Async state updates cause cursor jumping

```jsx
// DON'T -- async update moves cursor to start
onChange={e => setTimeout(() => setText(e.target.value), 100)}

// DO -- update synchronously
onChange={e => setText(e.target.value)}
```

### 3. Using `value` for checkboxes instead of `checked`

```jsx
// DON'T
<input type="checkbox" value={isOn} />

// DO
<input type="checkbox" checked={isOn} onChange={e => setIsOn(e.target.checked)} />
```

### 4. Forgetting `onChange` on controlled inputs

Passing `value` without `onChange` makes the input read-only. React warns about this. Either add `onChange`, use `defaultValue`, or explicitly pass `readOnly`.

### 5. Non-submit buttons inside forms

```jsx
// DON'T -- this button submits the form
<form><button onClick={doSomething}>Click</button></form>

// DO -- explicitly set type="button"
<form><button type="button" onClick={doSomething}>Click</button></form>
```

### 6. Performance: controlled inputs re-render the parent

Isolate controlled inputs in their own component to avoid re-rendering large trees on every keystroke. Use `useDeferredValue` if the value drives expensive rendering.

---

## Refs and Style

Access DOM nodes with `useRef`:

```jsx
const inputRef = useRef(null);
<input ref={inputRef} />
// Later: inputRef.current.focus();
```

React 19 ref callbacks support cleanup functions:

```jsx
<input ref={(node) => { node?.focus(); return () => { /* cleanup */ }; }} />
```

Pass CSS as a camelCase object. Numbers auto-append `px` for dimensional properties. Prefer `className` for static styles; reserve `style` for dynamic values.

```jsx
<input style={{ fontSize: 16, padding: 8, border: '1px solid #ccc' }} />
```
