# Next.js: Routing
Based on Next.js documentation (App Router).

## Core Concepts

Next.js uses **file-system routing** where folders define routes and special files define UI. Each folder in the `app` directory maps to a URL segment. Only files exported from `page.js` are publicly accessible.

### How Navigation Works

1. **Server Rendering** -- layouts and pages are React Server Components by default
2. **Prefetching** -- routes linked with `<Link>` are prefetched when they enter the viewport
3. **Streaming** -- the server sends parts of a dynamic route as they become ready
4. **Client-side transitions** -- `<Link>` updates content without full page reloads, preserving shared layouts and state

---

## File Conventions Quick Reference

| File | Purpose | Re-renders on nav? | Must be Client Component? |
|------|---------|-------------------|--------------------------:|
| `page.js` | Unique UI for a route (leaf node) | Yes | No (Server by default) |
| `layout.js` | Shared UI wrapping children, persists across navigations | **No** | No |
| `template.js` | Like layout but remounts on every navigation | Yes (new instance) | No |
| `loading.js` | Instant loading UI via Suspense boundary | N/A (fallback) | No |
| `error.js` | Error boundary fallback | N/A (fallback) | **Yes** |
| `not-found.js` | UI when `notFound()` is called | N/A | No |
| `default.js` | Fallback for parallel route slots after hard navigation | N/A | No |
| `route.js` | API endpoint (Route Handler) | N/A | N/A |
| `global-error.js` | Root-level error boundary (replaces root layout) | N/A | **Yes** |

### Nesting Order

Files in a route segment render in this order:

```
layout.js
  template.js
    error.js (boundary)
      loading.js (Suspense boundary)
        not-found.js (boundary)
          page.js
```

---

## page.js

Makes a route segment publicly accessible. Always the leaf of the route subtree.

```tsx
// app/blog/[slug]/page.tsx
export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const { slug } = await params
  const { page = '1' } = await searchParams
  return <h1>Post: {slug}</h1>
}
```

Key points:
- `params` and `searchParams` are **promises** (since Next.js 15). Use `await` or React's `use()`.
- `searchParams` opts the page into **dynamic rendering** (values unknown at build time).
- In Client Components, use `use(params)` and `use(searchParams)` instead of `await`.
- Type helper: `PageProps<'/blog/[slug]'>` provides strongly typed props.

---

## layout.js

Wraps child routes. **Does not re-render on navigation** -- state is preserved.

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <section>{children}</section>
}
```

### Root Layout Requirements

The root `app/layout.js` **must** define `<html>` and `<body>` tags. Use the Metadata API instead of manual `<head>` tags.

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

### Layout Caveats

- **No `searchParams`**: Layouts don't re-render, so search params would go stale. Read them in a Client Component with `useSearchParams()`.
- **No `pathname`**: Use `usePathname()` in a Client Component.
- **No data passing to children**: Fetch the same data in both layout and page; Next.js deduplicates `fetch` requests automatically.
- **Child segment access**: Use `useSelectedLayoutSegment()` in a Client Component.
- Type helper: `LayoutProps<'/dashboard'>` provides typed props including parallel route slots.

---

## template.js

Like a layout, but creates a **new instance on every navigation**. Use when you need:
- `useEffect` to re-run on navigation
- Child Client Component state to reset
- Suspense fallbacks to show on every navigation (not just first load)

```tsx
// app/template.tsx
export default function Template({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}
```

Rendered as: `<Layout> <Template key={routeParam}>{children}</Template> </Layout>`

The template remounts when its own segment (including dynamic params) changes. Navigations within deeper segments do not remount higher-level templates.

---

## loading.js

Creates an instant loading state by wrapping `page.js` in a `<Suspense>` boundary.

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <LoadingSkeleton />
}
```

Key behaviors:
- Navigation is **immediate** -- the loading fallback shows instantly
- Navigation is **interruptible** -- users can navigate away before content loads
- Shared layouts remain interactive while loading
- The fallback is **prefetched** for static routes
- For dynamic routes, `loading.js` enables **partial prefetching** (the loading skeleton is fetched ahead of time)

Always add `loading.js` to dynamic routes to avoid the appearance of an unresponsive app.

---

## error.js

Creates a React Error Boundary. **Must be a Client Component.**

```tsx
'use client'
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

- `error.message`: Original message for client errors; generic message for server errors (to prevent leaking sensitive info).
- `error.digest`: Hash to match server-side logs.
- `reset()`: Re-renders the error boundary contents.
- `global-error.js`: Catches errors in the root layout. Must define its own `<html>` and `<body>`.

---

## not-found.js

Renders when `notFound()` is called within a route segment.

```tsx
import Link from 'next/link'
export default function NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <Link href="/">Return Home</Link>
    </div>
  )
}
```

- Root `app/not-found.js` catches all unmatched URLs.
- Can be async (Server Component) to fetch data.
- `global-not-found.js` (experimental, v15.4+): Bypasses layout rendering entirely; must include `<html>` and `<body>`. Useful with multiple root layouts or top-level dynamic segments.

---

## Dynamic Routes

| Convention | Example | Matches | `params` |
|-----------|---------|---------|----------|
| `[slug]` | `app/blog/[slug]/page.js` | `/blog/hello` | `{ slug: 'hello' }` |
| `[...slug]` | `app/shop/[...slug]/page.js` | `/shop/a/b/c` | `{ slug: ['a','b','c'] }` |
| `[[...slug]]` | `app/shop/[[...slug]]/page.js` | `/shop` or `/shop/a/b` | `{ slug: undefined }` or `{ slug: ['a','b'] }` |

### Static Generation with generateStaticParams

```tsx
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json())
  return posts.map((post) => ({ slug: post.slug }))
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  // ...
}
```

Without `generateStaticParams`, dynamic segments fall back to dynamic rendering at request time. Add it to prerender known paths at build time.

---

## Route Groups

Wrap a folder name in parentheses: `(folderName)`. Organizes routes **without affecting the URL**.

```
app/
  (marketing)/
    about/page.js      -> /about
    blog/page.js       -> /blog
  (shop)/
    cart/page.js       -> /cart
    products/page.js   -> /products
```

Use cases:
- Organize by team or feature
- Apply different layouts to route subsets
- Create multiple root layouts

Caveats:
- Navigating between different root layouts triggers a **full page reload**.
- Routes in different groups must not resolve to the same URL (e.g., `(a)/about` and `(b)/about` both map to `/about` -- this errors).
- Without a top-level `layout.js`, the home route `/` must be inside one of the groups.

---

## Parallel Routes

Render multiple pages simultaneously in the same layout using named **slots** (`@folder`).

```
app/
  @analytics/page.js
  @team/page.js
  layout.js
  page.js
```

```tsx
// app/layout.tsx
export default function Layout({
  children,
  analytics,
  team,
}: {
  children: React.ReactNode
  analytics: React.ReactNode
  team: React.ReactNode
}) {
  return (
    <>
      {children}
      {team}
      {analytics}
    </>
  )
}
```

Key points:
- Slots are **not** URL segments (`@analytics/views` maps to `/views`).
- `children` is an implicit slot (equivalent to `@children`).
- Each slot can have its own `loading.js` and `error.js`.
- Use `useSelectedLayoutSegment('slotName')` to read the active segment of a slot.

### Conditional Rendering

```tsx
export default function Layout({ user, admin }) {
  const role = checkUserRole()
  return role === 'admin' ? admin : user
}
```

### default.js (Critical for Parallel Routes)

On **soft navigation** (client-side), Next.js tracks each slot's active state. On **hard navigation** (full page load/refresh), it cannot recover state for slots that don't match the current URL. It renders `default.js` as fallback, or 404 if missing.

**Always define `default.js` for every parallel route slot**, including the implicit `children` slot. Common patterns:

```tsx
// Return null when slot should be hidden
export default function Default() { return null }

// Or trigger not-found
import { notFound } from 'next/navigation'
export default function Default() { notFound() }
```

---

## Intercepting Routes

Load a route from another part of the app within the current layout, masking the browser URL. Used for modals that show on client navigation but render as full pages on direct access/refresh.

| Convention | Matches |
|-----------|---------|
| `(.)` | Same level |
| `(..)` | One level above |
| `(..)(..)` | Two levels above |
| `(...)` | Root `app` directory |

The convention is based on **route segments**, not the file system. `@slot` folders are not counted.

### Modal Pattern (Intercepting + Parallel Routes)

```
app/
  @modal/
    default.js              -> returns null
    (.)photo/[id]/page.js   -> intercepted route (shows modal)
  photo/[id]/page.js        -> full page (direct access)
  layout.js
  page.js
```

```tsx
// app/layout.tsx
export default function Layout({ children, modal }) {
  return (
    <>
      {children}
      {modal}
    </>
  )
}
```

Close the modal with `router.back()`. Use a catch-all `@modal/[...catchAll]/page.js` returning `null` to dismiss the modal when navigating to other routes.

---

## Linking and Navigation

### Link Component

```tsx
import Link from 'next/link'

<Link href="/dashboard">Dashboard</Link>
<Link href="/blog/hello-world">Blog Post</Link>
<Link href="/about" prefetch={false}>About</Link>  // disable prefetching
```

### Programmatic Navigation (Client Components)

```tsx
'use client'
import { useRouter } from 'next/navigation'

export default function Page() {
  const router = useRouter()
  return <button onClick={() => router.push('/dashboard')}>Go</button>
}
```

`useRouter` methods: `push(url)`, `replace(url)`, `refresh()`, `back()`, `forward()`, `prefetch(url)`.

### Native History API

`window.history.pushState` and `replaceState` integrate with the Next.js router and sync with `usePathname` / `useSearchParams`.

```tsx
'use client'
import { useSearchParams } from 'next/navigation'

export default function SortProducts() {
  const searchParams = useSearchParams()
  function updateSorting(order: string) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('sort', order)
    window.history.pushState(null, '', `?${params.toString()}`)
  }
  return <button onClick={() => updateSorting('asc')}>Sort</button>
}
```

---

## Redirecting

| Method | Where | Status Code |
|--------|-------|-------------|
| `redirect(url)` | Server Components, Server Actions, Route Handlers | 307 (or 303 from Server Action) |
| `permanentRedirect(url)` | Same as above | 308 |
| `useRouter().push(url)` | Client Component event handlers | N/A (client-side) |
| `next.config.js` `redirects` | Build config | 307 or 308 |
| `NextResponse.redirect()` | Middleware/Proxy | Any |

```tsx
// Server Action
'use server'
import { redirect } from 'next/navigation'

export async function createPost(id: string) {
  // ... create post
  redirect(`/post/${id}`) // call OUTSIDE try/catch -- it throws
}
```

```ts
// next.config.ts
export default {
  async redirects() {
    return [
      { source: '/old-blog/:slug', destination: '/blog/:slug', permanent: true },
    ]
  },
}
```

`redirect` throws an error internally -- always call it **outside** `try/catch` blocks.

---

## Prefetching

### Static vs Dynamic

| | Static route | Dynamic route |
|---|---|---|
| Prefetched? | Yes, full route | Only if `loading.js` exists (partial) |
| Client cache TTL | 5 min default | Off by default |
| Server roundtrip on click | No | Yes (streamed) |

### Controlling Prefetch Behavior

```tsx
// Default: prefetch on viewport entry
<Link href="/about">About</Link>

// Disable prefetching
<Link href="/about" prefetch={false}>About</Link>

// Manual prefetch
const router = useRouter()
router.prefetch('/dashboard')
```

### Hover-Only Prefetch Pattern

For large link lists (infinite scroll, tables), defer prefetching to hover:

```tsx
'use client'
import Link from 'next/link'
import { useState } from 'react'

export function HoverPrefetchLink({ href, children }) {
  const [active, setActive] = useState(false)
  return (
    <Link href={href} prefetch={active ? null : false} onMouseEnter={() => setActive(true)}>
      {children}
    </Link>
  )
}
```

### Prefetch Pitfall: Side Effects

Side effects in layouts/pages (e.g., analytics tracking) run during prefetch, not on visit. Move them to `useEffect` in a Client Component.

---

## Common Pitfalls

1. **Missing `loading.js` on dynamic routes**: Navigation feels frozen while waiting for server response. Always add a loading state.

2. **Missing `default.js` for parallel routes**: Hard navigation (refresh) returns 404 for slots without `default.js`. Define it for every slot, including `children`.

3. **Layout expecting fresh `searchParams`**: Layouts don't re-render on navigation. Use `useSearchParams()` in a Client Component instead.

4. **`redirect()` inside `try/catch`**: `redirect` works by throwing -- placing it inside `try` catches the redirect. Call it outside.

5. **Intercepting route segment counting**: The `(..)` convention counts route segments, not filesystem directories. `@slot` folders are skipped in the count.

6. **Multiple root layouts**: Navigating between routes with different root layouts causes a **full page reload**, not a client-side transition.

7. **Side effects in Server Components**: Code in layouts/pages runs during prefetching. Analytics, logging, and mutations belong in `useEffect` or Server Actions.

8. **Parallel route slot visibility**: On client-side navigation to a route that no longer matches a slot, the slot's previous content stays visible. Use catch-all routes returning `null` to clear it.
