# React: DOM APIs & Resource Loading
Based on React 19 documentation.

## Client APIs

### createRoot

Creates a React root for client-side rendering. Called once at app startup.

```jsx
import { createRoot } from 'react-dom/client';

const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

**Signature:** `createRoot(domNode, options?)` returns `{ render, unmount }`

**Options:**

| Option | Purpose |
|--------|---------|
| `onCaughtError(error, errorInfo)` | Error caught by an Error Boundary |
| `onUncaughtError(error, errorInfo)` | Error not caught by any Error Boundary |
| `onRecoverableError(error, errorInfo)` | Error React auto-recovers from |
| `identifierPrefix` | Prefix for `useId()` — avoids conflicts with multiple roots |

**Error reporting in production:**

```jsx
const root = createRoot(document.getElementById('root'), {
  onCaughtError: (error, errorInfo) => {
    reportToService('caught', error, errorInfo.componentStack);
  },
  onUncaughtError: (error, errorInfo) => {
    reportToService('uncaught', error, errorInfo.componentStack);
  },
});
```

**Multiple roots** for partially-React pages:

```jsx
createRoot(document.getElementById('navigation')).render(<Navigation />);
createRoot(document.getElementById('main')).render(<MainContent />);
```

**Cleanup:** `root.unmount()` removes the tree and cleans up. Cannot call `root.render()` after — create a new root instead.

### hydrateRoot

Hydrates server-rendered HTML. Must produce identical output on client and server.

```jsx
import { hydrateRoot } from 'react-dom/client';

const root = hydrateRoot(document.getElementById('root'), <App />);
```

**Signature:** `hydrateRoot(domNode, reactNode, options?)` — same options as `createRoot`.

**Handling hydration mismatches:**

```jsx
// Suppress warning for unavoidable differences (timestamps, etc.)
<h1 suppressHydrationWarning={true}>
  {new Date().toLocaleDateString()}
</h1>

// Two-pass rendering for intentionally different client content
function ClientOnly({ children, fallback }) {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => setIsClient(true), []);
  return isClient ? children : fallback;
}
```

**Do this / Don't do this:**

```jsx
// Do: use hydrateRoot for server-rendered HTML
hydrateRoot(document.getElementById('root'), <App />);

// Don't: use createRoot on server-rendered HTML — destroys existing DOM
createRoot(document.getElementById('root')).render(<App />);

// Don't: pass options to root.render() — they go on hydrateRoot
const root = hydrateRoot(container, <App />, { onUncaughtError });
```

---

## Portals

### createPortal

Renders children into a different DOM node while keeping them in the React tree.

```jsx
import { createPortal } from 'react-dom';

function Modal({ children, onClose }) {
  return createPortal(
    <div className="modal-overlay">
      <div className="modal">{children}</div>
    </div>,
    document.body
  );
}
```

**Signature:** `createPortal(children, domNode, key?)`

**Use cases:**
- Modals and dialogs that escape `overflow: hidden` containers
- Tooltips and popovers that render above the page flow
- Rendering React into non-React DOM (third-party widgets, server-rendered sections)

**Event bubbling follows the React tree, not the DOM tree.** A parent `onClick` catches clicks from portaled children even though they live elsewhere in the DOM. Stop propagation inside the portal if needed:

```jsx
// Parent onClick fires on portal child clicks — often surprising
<div onClick={handleClick}>
  {showModal && createPortal(<Modal />, document.body)}
</div>

// Fix: stop propagation inside the portal
<div onClick={e => e.stopPropagation()}>{portalContent}</div>
```

**Use portals, not separate roots** for overlays. Separate `createRoot` calls lose shared context and state.

**Accessibility:** Portaled modals must follow WAI-ARIA dialog patterns — manage focus, keyboard navigation, and ARIA attributes.

---

## Document Metadata Components (React 19)

React 19 automatically hoists `<title>`, `<meta>`, `<link>`, `<style>`, and `<script>` to the document `<head>`. Render them from any component.

### title

```jsx
function BlogPost({ post }) {
  return (
    <>
      <title>{`My Blog: ${post.title}`}</title>
      <article>{post.content}</article>
    </>
  );
}
```

**Gotcha — use template literals for dynamic titles:**

```jsx
// Don't: creates an array of children
<title>Results page {pageNumber}</title>

// Do: single string child
<title>{`Results page ${pageNumber}`}</title>
```

Only render one `<title>` at a time. Multiple `<title>` tags cause undefined browser behavior.

### meta

```jsx
function ProductPage({ product }) {
  return (
    <>
      <meta name="description" content={product.summary} />
      <meta name="keywords" content={product.tags.join(', ')} />
      <h1>{product.name}</h1>
    </>
  );
}
```

Exception: `<meta itemProp="...">` renders inline (not hoisted) for structured data.

### link

**Stylesheets** get special treatment when `precedence` is provided:

```jsx
function Dashboard() {
  return (
    <>
      <link rel="stylesheet" href="dashboard.css" precedence="medium" />
      <div className="dashboard">...</div>
    </>
  );
}
```

With `precedence`, React:
- Deduplicates stylesheets with the same `href`
- Suspends the component while the stylesheet loads
- Controls insertion order based on precedence values

**Precedence controls cascade order.** Values are arbitrary strings — React treats first-discovered values as lower priority:

```jsx
<link rel="stylesheet" href="base.css" precedence="low" />
<link rel="stylesheet" href="theme.css" precedence="medium" />
<link rel="stylesheet" href="page.css" precedence="high" />
```

**Special behavior is disabled** when `precedence` is omitted, or `onLoad`/`onError`/`disabled` props are set.

**Non-stylesheet links** work normally:

```jsx
<link rel="icon" href="favicon.ico" />
<link rel="canonical" href="https://example.com/page" />
```

### style

Inline stylesheets with deduplication and precedence:

```jsx
function PieChart({ data, colors }) {
  const id = useId();
  const css = colors.map((color, i) =>
    `#${id} .slice-${i} { fill: ${color}; }`
  ).join('\n');

  return (
    <>
      <style href={`PieChart-${JSON.stringify(colors)}`} precedence="medium">
        {css}
      </style>
      <svg id={id}>...</svg>
    </>
  );
}
```

`href` enables deduplication. `precedence` controls ordering (same system as `<link>`).

### script

**External scripts** with `async={true}` get deduplication and head placement:

```jsx
function MapWidget({ lat, lng }) {
  return (
    <>
      <script async={true} src="map-sdk.js" onLoad={() => initMap()} />
      <div id="map" data-lat={lat} data-lng={lng} />
    </>
  );
}
```

**Inline scripts** are not deduplicated or moved to `<head>`:

```jsx
<script>{'ga("send", "pageview");'}</script>
```

**Avoid `defer`** — incompatible with streaming SSR. Use `async` instead.

---

## Resource Loading APIs

Hint to the browser to start loading resources before they are needed. These are imperative functions, not components.

### Quick Reference

| Function | What it does | When to use |
|----------|-------------|-------------|
| `prefetchDNS(url)` | DNS lookup only | Many speculative domains |
| `preconnect(url)` | DNS + TCP + TLS | Know the server, not the resources |
| `preload(url, opts)` | Download resource | Know specific resource needed soon |
| `preloadModule(url, opts)` | Download ESM module | Know specific module needed soon |
| `preinit(url, opts)` | Download and execute/insert | Script or stylesheet needed immediately |
| `preinitModule(url, opts)` | Download and execute ESM | Module needed immediately |

All functions are imported from `'react-dom'` and return `void`. Duplicate calls are no-ops.

### preload — download without executing

```jsx
import { preload } from 'react-dom';

function App() {
  preload('/fonts/brand.woff2', { as: 'font', type: 'font/woff2' });
  preload('/hero.jpg', { as: 'image' });
  return <main>...</main>;
}
```

Supported `as` values: `audio`, `document`, `embed`, `fetch`, `font`, `image`, `object`, `script`, `style`, `track`, `video`, `worker`. For responsive images, pass `imageSrcSet` and `imageSizes` with `as: 'image'`.

### preinit — download and execute immediately

```jsx
import { preinit } from 'react-dom';

function App() {
  preinit('https://cdn.example.com/analytics.js', { as: 'script' });
  preinit('/styles/theme.css', { as: 'style', precedence: 'medium' });
  return <main>...</main>;
}
```

`precedence` is required for stylesheets, same ordering system as `<link>`.

### Preloading in event handlers

```jsx
function StartButton() {
  function handleClick() {
    preconnect('https://api.example.com');
    preload('/wizard/styles.css', { as: 'style' });
    preinit('/wizard/logic.js', { as: 'script' });
    navigateToWizard();
  }
  return <button onClick={handleClick}>Start</button>;
}
```

### prefetchDNS vs preconnect

- `prefetchDNS(url)` — DNS lookup only, lightweight, good for speculative domains
- `preconnect(url)` — full connection (DNS + TCP + TLS), use when you will load resources
- Don't preconnect to your own origin (already connected)
- Don't prefetchDNS when you know the exact resource (use `preload`)

---

## flushSync

Forces React to synchronously flush state updates and update the DOM. **Use sparingly.**

```jsx
import { flushSync } from 'react-dom';

function handleClick() {
  flushSync(() => {
    setCount(c => c + 1);
  });
  // DOM is updated here — can read it immediately
  console.log(inputRef.current.value);
}
```

**Legitimate use case — browser APIs needing synchronous DOM:**

```jsx
useEffect(() => {
  function handleBeforePrint() {
    flushSync(() => setIsPrinting(true));
    // DOM reflects printing state when print dialog opens
  }
  window.addEventListener('beforeprint', handleBeforePrint);
  return () => window.removeEventListener('beforeprint', handleBeforePrint);
}, []);
```

**Do this / Don't do this:**

```jsx
// Don't: call inside useEffect — warns and no-ops
useEffect(() => {
  flushSync(() => setSomething(value));
}, []);

// Don't: call during render — throws error
function Component() {
  flushSync(() => setSomething(value));
  return <div />;
}

// Do: call in event handlers
function handleSubmit() {
  flushSync(() => setSubmitted(true));
  formRef.current.scrollIntoView();
}

// Last resort: wrap in microtask if you must use in an effect
useEffect(() => {
  queueMicrotask(() => flushSync(() => setSomething(value)));
}, []);
```

**Performance cost:** flushSync defeats React's batching optimization. It can also force Suspense boundaries to show fallback states. Treat it as an escape hatch.

---

## Common Pitfalls

1. **createRoot on server-rendered HTML.** Use `hydrateRoot` instead. `createRoot` destroys existing DOM content on first render.

2. **Multiple roots instead of portals.** Separate `createRoot` calls lose shared context and state. Use `createPortal` for modals and overlays.

3. **Portal event bubbling.** Events from portaled children bubble through the React tree, not the DOM tree. This surprises people when a parent `onClick` catches portal clicks.

4. **Hydration mismatches.** Server and client must produce identical initial HTML. Common causes: `Date.now()`, `window` checks, browser-only APIs. Use `suppressHydrationWarning` or two-pass rendering.

5. **Missing `precedence` on `<link rel="stylesheet">`.** Without it, React skips deduplication, Suspense integration, and ordering. The stylesheet renders as a plain HTML link.

6. **Dynamic `<title>` with JSX expressions.** `<title>Page {num}</title>` creates an array of children. Use template literals: `<title>{\`Page ${num}\`}</title>`.

7. **`flushSync` in effects.** Calling it inside `useEffect` or lifecycle methods warns and does nothing. Move to an event handler or wrap in `queueMicrotask`.

8. **`defer` on `<script>`.** Incompatible with streaming SSR. Use `async={true}` for external scripts.

9. **Prop changes on metadata components.** React ignores prop changes to `<link>`, `<style>`, and `<script>` after initial render. Treat them as static declarations.

10. **Calling `root.render()` after `root.unmount()`.** Throws an error. Create a new root instead.
