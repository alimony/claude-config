# Next.js: Rendering & Components
Based on Next.js documentation (App Router).

## Server Components vs Client Components

Components in Next.js are **Server Components by default** (layouts and pages). They render on the server, optionally cache, and stream to the client. Client Components opt in to interactivity with `'use client'`.

### When to use each

| Use Server Components when you need | Use Client Components when you need |
|--------------------------------------|--------------------------------------|
| Fetch data close to the source (DB, APIs) | State (`useState`, `useReducer`) |
| Keep secrets server-side (API keys, tokens) | Event handlers (`onClick`, `onChange`) |
| Reduce client JS bundle | Lifecycle effects (`useEffect`) |
| Improve FCP, stream content progressively | Browser APIs (`localStorage`, `window`, geolocation) |
| | Custom hooks |

### Rendering lifecycle

**First load (server):**
1. Server Components render into the RSC Payload (compact binary format).
2. Client Components + RSC Payload produce pre-rendered HTML.
3. Browser shows non-interactive HTML immediately.
4. RSC Payload reconciles the component tree.
5. JavaScript hydrates Client Components, adding interactivity.

**Subsequent navigations:**
- RSC Payload is prefetched and cached for instant transitions.
- Client Components render entirely on the client.

## Directives

### `'use client'`

Declares a **client-server boundary**. Place at the top of a file, before imports. All exports from that file (and their imports/children) become part of the client bundle.

```tsx
'use client'

import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

**Key rules:**
- Props passed from Server to Client Components must be **serializable** (no functions, class instances, Symbols).
- You do NOT need `'use client'` on every client file -- only on entry points imported by Server Components.
- Add it as narrowly as possible to minimize the client bundle.

### `'use server'`

Marks functions as **Server Actions** -- callable from Client Components over the network. Use at the top of a file (all exports become server functions) or inline within a function body.

```tsx
// File-level: all exports are server functions
'use server'

export async function createPost(formData: FormData) {
  await db.post.create({ data: Object.fromEntries(formData) })
}
```

```tsx
// Inline: single function within a Server Component
export default async function Page({ params }) {
  async function updatePost(formData: FormData) {
    'use server'
    await savePost(params.id, formData)
    revalidatePath(`/posts/${params.id}`)
  }
  return <EditForm action={updatePost} />
}
```

**Security:** Always authenticate and authorize inside Server Actions. They are public HTTP endpoints.

### `'use cache'`

Caches the return value of an async function or component. Requires `cacheComponents: true` in `next.config.ts`.

```ts
// next.config.ts
const nextConfig: NextConfig = { cacheComponents: true }
```

Three levels of placement:

```tsx
// File level -- all exports cached
'use cache'
export default async function Page() { /* ... */ }

// Component level
export async function MyComponent() {
  'use cache'
  return <div>...</div>
}

// Function level
export async function getData() {
  'use cache'
  return fetch('/api/data')
}
```

**Cache keys** are generated from: build ID, function ID, serializable arguments, and any closed-over variables from parent scopes. Different inputs produce separate cache entries.

**Default profile:**
- `stale`: 5 min (client-side)
- `revalidate`: 15 min (server-side)
- `expire`: never

Customize with `cacheLife`:

```tsx
import { cacheLife } from 'next/cache'

async function getData() {
  'use cache'
  cacheLife('hours')           // Built-in profile
  // or custom:
  // cacheLife({ stale: 3600, revalidate: 7200, expire: 86400 })
  return fetch('/api/data')
}
```

**Cannot access** `cookies()`, `headers()`, or `searchParams` directly inside `use cache`. Read them outside and pass values as arguments.

### `'use cache: private'` (experimental)

Allows `cookies()`, `headers()`, and `searchParams` inside a cached scope. Results are cached **only in the browser memory** (never stored server-side). Use when refactoring runtime access out of the cached scope is impractical, or compliance prevents server-side storage.

```tsx
async function getRecommendations(productId: string) {
  'use cache: private'
  cacheLife({ stale: 60 })
  const sessionId = (await cookies()).get('session-id')?.value || 'guest'
  return getPersonalizedRecommendations(productId, sessionId)
}
```

### `'use cache: remote'`

Stores cached output in a **remote cache handler** (e.g., Redis, KV store) instead of in-memory. Shared across all server instances. Useful in serverless environments where in-memory caches are ephemeral.

```tsx
async function getProductPrice(productId: string, currency: string) {
  'use cache: remote'
  cacheTag(`product-price-${productId}`)
  cacheLife({ expire: 3600 })
  return db.products.getPrice(productId, currency)
}
```

**When to use remote:** rate-limited APIs, protecting slow backends, expensive computations, flaky external services. **When to avoid:** operations already fast (<50ms), highly unique cache keys, rapidly changing data.

### Cache directive comparison

| Feature | `use cache` | `use cache: remote` | `use cache: private` |
|---------|-------------|---------------------|----------------------|
| Server storage | In-memory | Remote handler | None |
| Scope | Shared (all users) | Shared (all users) | Per-client (browser) |
| Access cookies/headers | No | No | Yes |
| Additional costs | None | Infrastructure | None |

### Nesting rules for cache directives

- `use cache: remote` inside `use cache` or `use cache: remote` -- **valid**
- `use cache: remote` inside `use cache: private` -- **invalid**
- `use cache: private` inside `use cache: remote` -- **invalid**

## Composition Patterns

### Pass Server Components as children to Client Components

Use `children` (or any prop) to create a "slot" so Server Components render inside Client Component wrappers.

```tsx
// modal.tsx -- Client Component
'use client'
export default function Modal({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return open ? <div className="modal">{children}</div> : null
}

// page.tsx -- Server Component
import Modal from './modal'
import Cart from './cart'  // Server Component

export default function Page() {
  return (
    <Modal>
      <Cart />  {/* Rendered on the server, passed through */}
    </Modal>
  )
}
```

Server Components passed as props are rendered on the server ahead of time. The RSC Payload contains references for where Client Components slot in.

### Context providers

React context is not supported in Server Components. Create a Client Component provider and wrap children in a Server Component layout:

```tsx
// theme-provider.tsx
'use client'
import { createContext } from 'react'
export const ThemeContext = createContext({})
export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  return <ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>
}

// layout.tsx (Server Component)
import ThemeProvider from './theme-provider'
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html><body>
      <ThemeProvider>{children}</ThemeProvider>
    </body></html>
  )
}
```

Render providers as deep in the tree as possible to maximize the static portion.

### Sharing data across Server and Client Components

Combine `React.cache` with context providers. Create a cached fetch, pass the **promise** (not awaited) to a client context, and resolve it with `use()` in Client Components:

```tsx
// lib/user.ts
import { cache } from 'react'
export const getUser = cache(async () => {
  const res = await fetch('https://api.example.com/user')
  return res.json()
})

// layout.tsx -- pass promise, don't await
import UserProvider from './user-provider'
import { getUser } from './lib/user'
export default function Layout({ children }) {
  const userPromise = getUser() // no await
  return <UserProvider userPromise={userPromise}>{children}</UserProvider>
}

// Client Component -- resolve with use()
'use client'
import { use, useContext } from 'react'
export function Profile() {
  const userPromise = useContext(UserContext)
  const user = use(userPromise)
  return <p>Welcome, {user.name}</p>
}
```

`React.cache` is scoped to the current request only -- no sharing between requests.

### Third-party components without `'use client'`

Wrap them in a thin Client Component:

```tsx
// carousel.tsx
'use client'
import { Carousel } from 'acme-carousel'
export default Carousel

// page.tsx (Server Component) -- now works
import Carousel from './carousel'
export default function Page() {
  return <Carousel />
}
```

## Cache Components & Partial Prerendering

Enable with `cacheComponents: true` in `next.config.ts`. This activates Partial Prerendering (PPR): routes are prerendered into a **static HTML shell**, with dynamic content streaming in at request time.

### Three types of content

1. **Automatically prerendered** -- synchronous I/O, module imports, pure computations. Included in static shell with no extra work.
2. **Cached (`use cache`)** -- async/dynamic data wrapped in `use cache`. Included in static shell, revalidated per `cacheLife`.
3. **Deferred to request time** -- wrapped in `<Suspense>`. Fallback is in the static shell; content streams when ready.

### Handling dynamic data

If a component accesses network, DB, or async operations and is NOT wrapped in `<Suspense>` or marked `use cache`, you get a build error: `Uncached data was accessed outside of <Suspense>`.

```tsx
// Correct: defer with Suspense
export default function Page() {
  return (
    <>
      <h1>Static content</h1>
      <Suspense fallback={<p>Loading...</p>}>
        <DynamicContent />
      </Suspense>
    </>
  )
}
```

### Runtime data (cookies, headers, searchParams)

Always requires `<Suspense>` -- cannot be cached with `use cache` (except `use cache: private`). Extract values and pass them to cached functions if needed:

```tsx
async function ProfileContent() {
  const session = (await cookies()).get('session')?.value
  return <CachedContent sessionId={session} />
}

async function CachedContent({ sessionId }: { sessionId: string }) {
  'use cache'
  const data = await fetchUserData(sessionId)
  return <div>{data}</div>
}
```

### Tagging and revalidation

Tag cached data with `cacheTag`, then invalidate with `updateTag` (immediate) or `revalidateTag` (stale-while-revalidate):

```tsx
import { cacheTag, updateTag } from 'next/cache'

async function getCart() {
  'use cache'
  cacheTag('cart')
  return fetch('/api/cart')
}

async function updateCart(itemId: string) {
  'use server'
  await db.cart.update(itemId)
  updateTag('cart')  // Immediate invalidation
}
```

## Common Pitfalls

### Serialization across the boundary

Props from Server to Client Components must be serializable. No functions, class instances, Symbols, WeakMaps, or WeakSets.

```tsx
// BAD: passing a function prop across the boundary
<ClientComponent onClick={handleClick} />  // Error

// GOOD: define the handler inside the Client Component
// or pass a Server Action (marked 'use server')
```

### Importing server code into client modules

Use `server-only` package to get build-time errors if server-only code is accidentally imported client-side:

```ts
import 'server-only'
export async function getData() {
  return fetch('...', { headers: { authorization: process.env.API_KEY } })
}
```

The corresponding `client-only` package guards client-only modules.

### `React.cache` isolation in `use cache`

`React.cache` operates in an **isolated scope** inside `use cache` boundaries. Values stored via `React.cache` outside are NOT visible inside a `use cache` function. Pass data through function arguments instead.

### Build hangs with `use cache`

Passing Promises that resolve to runtime data into a `use cache` scope causes timeouts during build (50s). The cached function waits for data that cannot resolve at build time.

```tsx
// BAD: passing a cookies() promise into use cache
async function Cached({ promise }) {
  'use cache'
  const data = await promise  // Hangs at build time
}

// GOOD: await outside, pass the value
async function Dynamic() {
  const value = (await cookies()).get('key')?.value
  return <Cached value={value} />
}
```

### `use cache` pass-through pattern

Non-serializable values (like `children` or Server Actions) can be passed through a cached component as long as you do NOT read or call them inside the cache body:

```tsx
async function CachedWrapper({ children }: { children: ReactNode }) {
  'use cache'
  const data = await fetch('/api/data')
  return (
    <div>
      <CachedPart data={data} />
      {children}  {/* Passed through, not inspected */}
    </div>
  )
}
```

### Environment poisoning

Non-prefixed env vars (`process.env.API_KEY`) are replaced with empty strings on the client. Rely on `NEXT_PUBLIC_` prefix for client-safe values, and `server-only` to guard secrets.

## Best Practices

1. **Default to Server Components.** Only add `'use client'` where you need interactivity, state, or browser APIs.
2. **Push `'use client'` to the leaves.** Keep the boundary as narrow as possible to minimize client JS.
3. **Use `children` for composition.** Pass Server Components as children/props to Client Components instead of importing server code in client files.
4. **Cache close to the data.** Apply `use cache` at the function or component level nearest to the data fetch, not at the page level.
5. **Use `<Suspense>` for dynamic sections.** Place boundaries close to dynamic components to maximize the static shell.
6. **Tag caches for on-demand revalidation.** Use `cacheTag` + `updateTag`/`revalidateTag` rather than short expiry times.
7. **Avoid unique cache keys.** Cache on dimensions with few unique values (category, language) rather than per-user or per-search-query.
8. **Guard server-only code.** Use `import 'server-only'` in modules with secrets or server-only logic.
