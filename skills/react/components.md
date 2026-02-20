# React: Built-in Components
Based on React 19 documentation.

## Fragment

Groups elements without adding a DOM wrapper node.

```jsx
// Shorthand (default choice)
<>
  <Child1 />
  <Child2 />
</>

// Explicit (required for key or ref)
import { Fragment } from 'react';

<Fragment key={item.id}>
  <Child1 />
  <Child2 />
</Fragment>
```

- **Lists**: Rendering fragments in `.map()` requires `<Fragment key={...}>`.
- **Refs** (canary): `<Fragment ref={...}>` provides a `FragmentInstance` for event handling, focus management, and intersection observing without a wrapper DOM node.
- **Pitfall**: React does not reset state when alternating between `<><Child /></>` and `<Child />` at the same position (one level deep only).

---

## Suspense

Displays a fallback while children are loading.

```jsx
<Suspense fallback={<Spinner />}>
  <SlowComponent />
</Suspense>
```

**What triggers Suspense**: `lazy()`, `use()`, Suspense-enabled frameworks (Next.js, Relay).
**Does NOT work with**: data fetched inside Effects or event handlers.

### Pattern: Reveal content together

All children under one boundary load as a unit:

```jsx
<Suspense fallback={<Loading />}>
  <Biography />
  <Albums />
</Suspense>
// Both appear at the same time, or neither does
```

### Pattern: Progressive loading with nested boundaries

```jsx
<Suspense fallback={<PageSkeleton />}>
  <Header />
  <Suspense fallback={<ContentSkeleton />}>
    <MainContent />
  </Suspense>
</Suspense>
```

Header appears first. MainContent shows its own skeleton while loading.

### Pattern: Stale content with deferred values

```jsx
function Search() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <Suspense fallback={<Loading />}>
        <div style={{ opacity: isStale ? 0.5 : 1 }}>
          <SearchResults query={deferredQuery} />
        </div>
      </Suspense>
    </>
  );
}
```

Shows dimmed old results instead of a loading spinner while new results load.

### Pattern: Prevent visible content from hiding

Wrap state updates in `startTransition` so React waits for new content before swapping:

```jsx
function navigate(url) {
  startTransition(() => setPage(url));
}
```

Without `startTransition`, the fallback replaces already-visible content.

### Pattern: Show transition progress with `useTransition`

```jsx
const [isPending, startTransition] = useTransition();
// Use isPending to dim current UI: style={{ opacity: isPending ? 0.7 : 1 }}
```

### Pattern: Reset boundary on navigation

Use `key` to tell React this is different content: `<ProfilePage key={userId} />`

### Caveats

- State is **not preserved** for components that suspended before first mount. React retries from scratch.
- Fallback re-shows when visible content suspends again, **unless** the update used `startTransition` or `useDeferredValue`.
- Layout Effects clean up when content hides and re-fire when it reappears.

---

## StrictMode

Development-only checks that help find bugs early. No effect in production.

```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode><App /></StrictMode>
);
```

| Check | Catches |
|-------|---------|
| Double-invokes render functions | Impure rendering (mutations during render) |
| Double-invokes Effects (setup + cleanup + setup) | Missing cleanup functions |
| Double-invokes ref callbacks | Missing ref cleanup |
| Deprecation warnings | Unsafe lifecycle methods |

### Do/Don't: Impure rendering

```jsx
// BAD: mutates prop array
function StoryTray({ stories }) {
  const items = stories;
  items.push({ id: 'create', label: 'Create Story' });
  return <ul>{items.map(s => <li key={s.id}>{s.label}</li>)}</ul>;
}

// GOOD: copies first
function StoryTray({ stories }) {
  const items = [...stories];
  items.push({ id: 'create', label: 'Create Story' });
  return <ul>{items.map(s => <li key={s.id}>{s.label}</li>)}</ul>;
}
```

### Do/Don't: Effect cleanup

```jsx
// BAD: missing cleanup
useEffect(() => {
  const conn = createConnection(serverUrl, roomId);
  conn.connect();
}, [roomId]);

// GOOD: cleanup included
useEffect(() => {
  const conn = createConnection(serverUrl, roomId);
  conn.connect();
  return () => conn.disconnect();
}, [roomId]);
```

### Partial application

Can wrap subtrees instead of the whole app. Checks only apply to the wrapped portion and descendants.

### Caveats

- Cannot opt out for children inside a `<StrictMode>` tree.
- When wrapping only part of the app (not root), Effects won't double-fire on initial mount.
- React DevTools dims console logs from the second render call.

---

## Profiler

Measures rendering performance of a component tree. Disabled in production by default.

```jsx
<Profiler id="Sidebar" onRender={onRender}>
  <Sidebar />
</Profiler>
```

### onRender callback

```jsx
function onRender(id, phase, actualDuration, baseDuration, startTime, commitTime) {
  // phase: "mount" | "update" | "nested-update"
  // actualDuration: ms spent rendering (reflects memoization gains)
  // baseDuration: ms for full re-render without memoization (worst case)
}
```

Compare `actualDuration` vs `baseDuration` to verify `memo`/`useMemo` optimizations work. Can be nested for granular measurement. Adds overhead -- use only where needed.

---

## Activity

Hides and shows children without unmounting. Preserves component state and DOM state. Effects clean up when hidden, re-fire when visible.

```jsx
<Activity mode={isVisible ? 'visible' : 'hidden'}>
  <Sidebar />
</Activity>
```

### How it differs from conditional rendering

```jsx
// Conditional: destroys state on hide
{showSidebar && <Sidebar />}

// Activity: preserves state on hide
<Activity mode={showSidebar ? 'visible' : 'hidden'}>
  <Sidebar />
</Activity>
```

**Preserved**: component state (useState), DOM state (input values, scroll position).
**Not preserved**: Effects clean up when hidden and re-fire when visible.

### Pattern: Pre-rendering hidden content

```jsx
<Suspense fallback={<Loading />}>
  <Activity mode={tab === 'home' ? 'visible' : 'hidden'}>
    <Home />
  </Activity>
  <Activity mode={tab === 'posts' ? 'visible' : 'hidden'}>
    <Posts />  {/* Pre-fetches data at low priority while hidden */}
  </Activity>
</Suspense>
```

Hidden children render at low priority. Suspense-enabled data sources fetch ahead of time. Content appears instantly on tab switch.

### Pattern: Improving hydration

Wrap sections in `<Activity>` to enable selective hydration, even for always-visible content:

```jsx
<Activity>
  <Comments />  {/* Hydrates independently from rest of page */}
</Activity>
```

### Pitfalls

- **Side effects in hidden components**: DOM-based side effects (video/audio) persist when hidden. Use `useLayoutEffect` cleanup (not `useEffect`) so it runs synchronously: `return () => video.pause();`
- **Text-only children**: Hidden Activities with text-only children render nothing. Wrap in a DOM element like `<div>`.

---

## ViewTransition

Animates UI changes using the browser View Transition API. Canary/experimental.

```jsx
<ViewTransition>
  <div>Animated content</div>
</ViewTransition>
```

### Requirements

1. **Must wrap a DOM node** (not be wrapped by one):
   ```jsx
   // GOOD
   <ViewTransition><div>Content</div></ViewTransition>
   // BAD
   <div><ViewTransition>Content</ViewTransition></div>
   ```

2. **State changes must use `startTransition`** to trigger animations:
   ```jsx
   startTransition(() => setShow(true)); // animates
   setShow(true);                        // no animation
   ```

### Animation triggers and props

| Trigger | When | Prop |
|---------|------|------|
| `enter` | ViewTransition inserted | `enter="class-name"` |
| `exit` | ViewTransition removed | `exit="class-name"` |
| `update` | DOM/layout changes inside | `update="class-name"` |
| `share` | Named VT in old tree matches new tree | `share="class-name"` |

Also: `default="class-name"` (fallback), `name="unique-id"` (for shared transitions).

Props accept strings or objects mapping transition types to class names:

```jsx
<ViewTransition default={{
  'navigation-back': 'slide-right',
  'navigation-forward': 'slide-left',
}}>
  <Page />
</ViewTransition>
```

### Styling

```css
::view-transition-old(.slide-in) { animation: slideOut 300ms ease-out; }
::view-transition-new(.slide-in) { animation: slideIn 300ms ease-out; }
```

### Pattern: Shared element transition

Same `name` in both old and new trees animates between them:

```jsx
// Thumbnail view
<ViewTransition name="hero-image">
  <img className="thumbnail" src={src} />
</ViewTransition>

// Detail view (swapped in via startTransition)
<ViewTransition name="hero-image">
  <img className="full-size" src={src} />
</ViewTransition>
```

### Pattern: List reordering

Wrap each item, not the container:

```jsx
// GOOD: each item animates independently
{items.map(item => (
  <ViewTransition key={item.id}>
    <ListItem item={item} />
  </ViewTransition>
))}
```

### Pattern: Suspense integration

```jsx
// Cross-fade fallback to content
<ViewTransition>
  <Suspense fallback={<Skeleton />}><Content /></Suspense>
</ViewTransition>

// Separate enter/exit animations
<Suspense fallback={<ViewTransition><Skeleton /></ViewTransition>}>
  <ViewTransition><Content /></ViewTransition>
</Suspense>
```

### Pattern: Opt out children

```jsx
<ViewTransition>
  <div className={theme}>
    <ViewTransition update="none">
      {children}  {/* Won't animate on theme change */}
    </ViewTransition>
  </div>
</ViewTransition>
```

### Pitfalls

- **Unique names**: Only one mounted ViewTransition per `name`. In lists, use `name={\`item-${id}\`}`.
- **Reduced motion**: React does not auto-disable. Always add:
  ```css
  @media (prefers-reduced-motion: reduce) {
    ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; }
  }
  ```
- `flushSync` during a transition skips the animation.
- Browser back button (popstate) cannot animate; requires Navigation API.
- DOM-only (no React Native support yet).
