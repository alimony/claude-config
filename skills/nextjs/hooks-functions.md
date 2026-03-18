# Next.js: Hooks & Functions
Based on Next.js documentation (App Router).

## Client Hooks

All client hooks require `'use client'` and are imported from `next/navigation` (unless noted otherwise).

### useRouter

Programmatic client-side navigation. Prefer `<Link>` for declarative navigation.

```tsx
'use client'
import { useRouter } from 'next/navigation'

const router = useRouter()
```

**Methods:**
- `router.push(href, { scroll? })` -- navigate, adds history entry
- `router.replace(href, { scroll? })` -- navigate, replaces current history entry
- `router.refresh()` -- re-fetch Server Components without losing client state or scroll position
- `router.prefetch(href, { onInvalidate? })` -- prefetch a route; `onInvalidate` fires when prefetched data goes stale
- `router.back()` / `router.forward()` -- history navigation

**Security:** Never pass untrusted URLs to `push`/`replace` (XSS risk via `javascript:` URLs).

**Scroll:** Pass `{ scroll: false }` to prevent scrolling to top on navigation.

### usePathname

Returns the current URL pathname as a string. Does not include query string or hash.

```tsx
'use client'
import { usePathname } from 'next/navigation'

const pathname = usePathname()  // e.g. '/dashboard'
```

| URL                  | Return value          |
|----------------------|-----------------------|
| `/`                  | `'/'`                 |
| `/dashboard?v=2`     | `'/dashboard'`        |
| `/blog/hello-world`  | `'/blog/hello-world'` |

**Note:** Cannot read pathname in Server Components (by design -- layouts preserve state across navigations). If your app uses rewrites or a Proxy, reading pathname on the client may differ from the server, causing hydration mismatches. Mitigate by reading it in a `useEffect` and rendering a stable fallback initially.

### useSearchParams

Returns a **read-only** `URLSearchParams` object for the current URL query string.

```tsx
'use client'
import { useSearchParams } from 'next/navigation'

const searchParams = useSearchParams()
const q = searchParams.get('q')       // string | null
const all = searchParams.getAll('tag') // string[]
searchParams.has('page')               // boolean
searchParams.toString()                // 'q=foo&tag=bar'
```

**Suspense requirement:** On statically rendered routes, `useSearchParams` causes client-side rendering up to the nearest `<Suspense>` boundary. Wrap the consuming component in `<Suspense>` to avoid blocking static rendering of sibling components.

```tsx
import { Suspense } from 'react'
import SearchBar from './search-bar'

export default function Page() {
  return (
    <Suspense fallback={<p>Loading...</p>}>
      <SearchBar />
    </Suspense>
  )
}
```

**Server Components:** Use the `searchParams` page prop instead. Layouts do NOT receive `searchParams` (they are not re-rendered on navigation).

**Updating search params pattern:**

```tsx
'use client'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import { useCallback } from 'react'

function Filters() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const setParam = useCallback((key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set(key, value)
    router.push(`${pathname}?${params.toString()}`)
  }, [searchParams, pathname, router])

  return <button onClick={() => setParam('sort', 'asc')}>Sort ASC</button>
}
```

### useParams

Returns an object of the current route's dynamic parameters.

```tsx
'use client'
import { useParams } from 'next/navigation'

const params = useParams<{ slug: string }>()
```

| Route                            | URL          | Return value                |
|----------------------------------|--------------|-----------------------------|
| `app/shop/page.js`               | `/shop`      | `{}`                        |
| `app/shop/[slug]/page.js`        | `/shop/1`    | `{ slug: '1' }`            |
| `app/shop/[tag]/[item]/page.js`  | `/shop/1/2`  | `{ tag: '1', item: '2' }`  |
| `app/shop/[...slug]/page.js`     | `/shop/1/2`  | `{ slug: ['1', '2'] }`     |

### useSelectedLayoutSegment / useSelectedLayoutSegments

Read active route segments from within a layout. Useful for navigation tabs and breadcrumbs.

```tsx
'use client'
import { useSelectedLayoutSegment, useSelectedLayoutSegments } from 'next/navigation'

const segment = useSelectedLayoutSegment()    // string | null (one level below)
const segments = useSelectedLayoutSegments()  // string[] (all levels below)
```

Both accept an optional `parallelRoutesKey` parameter for parallel routes. Since layouts are Server Components, use these hooks in a Client Component imported into the layout.

| Layout                     | URL                        | `useSelectedLayoutSegment` | `useSelectedLayoutSegments` |
|----------------------------|----------------------------|----------------------------|-----------------------------|
| `app/layout.js`            | `/dashboard`               | `'dashboard'`              | `['dashboard']`             |
| `app/dashboard/layout.js`  | `/dashboard/settings`      | `'settings'`               | `['settings']`              |
| `app/dashboard/layout.js`  | `/dashboard/analytics/mon` | `'analytics'`              | `['analytics', 'mon']`      |

**Note:** Route groups (parenthesized folders) may appear in `useSelectedLayoutSegments` results -- filter them out with `.filter(s => !s.startsWith('('))`.

### useLinkStatus

Track the pending state of navigation triggered by a parent `<Link>`. Must be used inside a descendant of `<Link>`. Import from `next/link`.

```tsx
'use client'
import Link from 'next/link'
import { useLinkStatus } from 'next/link'

function Spinner() {
  const { pending } = useLinkStatus()  // boolean
  return pending ? <span className="spinner" /> : null
}

export default function Nav() {
  return (
    <Link href="/dashboard" prefetch={false}>
      Dashboard <Spinner />
    </Link>
  )
}
```

Most useful when `prefetch={false}` and the destination has no `loading.js`. If the route is prefetched, the pending phase is skipped. Add an animation delay (~100ms) to avoid flashing on fast navigations.

### useReportWebVitals

Report Core Web Vitals (TTFB, FCP, LCP, FID, CLS, INP). Import from `next/web-vitals`. Requires `'use client'`.

```tsx
'use client'
import { useReportWebVitals } from 'next/web-vitals'

// Keep a stable reference to avoid duplicate reports
const reportVital = (metric) => {
  console.log(metric.name, metric.value, metric.rating) // 'LCP', 2500, 'good'
}

export function WebVitals() {
  useReportWebVitals(reportVital)
  return null
}
```

**Metric properties:** `id`, `name`, `delta`, `value`, `rating` (`'good'` | `'needs-improvement'` | `'poor'`), `entries`, `navigationType`.

Place in a dedicated Client Component imported into root layout to limit the client boundary.

## Server Functions

These run on the server. They cannot be called from client-side event handlers.

### cookies()

**Import:** `import { cookies } from 'next/headers'`

Async function. Returns a cookie store for reading in Server Components or reading/writing in Server Actions and Route Handlers.

```tsx
// Reading (Server Component, Server Action, Route Handler)
const cookieStore = await cookies()
cookieStore.get('theme')          // { name, value } | undefined
cookieStore.getAll()              // [{ name, value }, ...]
cookieStore.has('session')        // boolean

// Writing (Server Action or Route Handler only)
cookieStore.set('name', 'value', { httpOnly: true, secure: true, maxAge: 3600 })
cookieStore.delete('name')
```

**Cookie options:** `name`, `value`, `expires` (Date), `maxAge` (seconds), `domain`, `path` (default `'/'`), `secure`, `httpOnly`, `sameSite` (`'lax'` | `'strict'` | `'none'`), `priority`, `partitioned`.

**Key rules:**
- `cookies()` is a Dynamic API -- using it opts the route into dynamic rendering.
- Cannot set/delete cookies during Server Component rendering (response headers already sent). Use a Server Action or Route Handler.
- Delete a cookie by calling `.delete('name')`, setting value to `''`, or setting `maxAge: 0`.

### headers()

**Import:** `import { headers } from 'next/headers'`

Async function. Returns a **read-only** Web `Headers` object from the incoming request.

```tsx
const headersList = await headers()
headersList.get('authorization')
headersList.get('user-agent')
headersList.has('x-custom')
```

Read-only -- cannot set or delete headers. Opts route into dynamic rendering.

### redirect(path, type?)

**Import:** `import { redirect } from 'next/navigation'`

Throws a `NEXT_REDIRECT` error to terminate rendering and redirect the user.

```tsx
redirect('/login')                           // 307 temporary
redirect('/login', RedirectType.replace)     // replaces history entry
```

| Context         | Status code |
|-----------------|-------------|
| Server Component | 307         |
| Server Action    | 303         |
| Streaming        | meta tag    |

- Uses `307` (not `302`) to preserve the HTTP method (e.g. POST stays POST).
- Call **outside** `try/catch` blocks -- it throws an error internally.
- TypeScript return type is `never` -- no need to `return redirect(...)`.
- Can be used in Client Components during render (not in event handlers -- use `useRouter` instead).

### permanentRedirect(path, type?)

**Import:** `import { permanentRedirect } from 'next/navigation'`

Same API as `redirect()` but issues a **308** (permanent) instead of 307.

```tsx
permanentRedirect('/new-path')
```

### notFound()

**Import:** `import { notFound } from 'next/navigation'`

Throws a `NEXT_HTTP_ERROR_FALLBACK;404` error, terminates rendering, and renders the nearest `not-found.js` file. Injects `<meta name="robots" content="noindex" />`.

```tsx
import { notFound } from 'next/navigation'

export default async function Page({ params }) {
  const { id } = await params
  const item = await getItem(id)
  if (!item) notFound()
  return <div>{item.title}</div>
}
```

### forbidden() (experimental)

**Import:** `import { forbidden } from 'next/navigation'`

Renders a 403 page using `forbidden.js`. Requires `experimental.authInterrupts: true` in `next.config.js`.

```tsx
import { forbidden } from 'next/navigation'

export default async function AdminPage() {
  const session = await verifySession()
  if (session.role !== 'admin') forbidden()
  return <div>Admin content</div>
}
```

Cannot be called in the root layout.

### unauthorized() (experimental)

**Import:** `import { unauthorized } from 'next/navigation'`

Renders a 401 page using `unauthorized.js`. Requires `experimental.authInterrupts: true` in `next.config.js`.

```tsx
import { unauthorized } from 'next/navigation'

export default async function DashboardPage() {
  const session = await verifySession()
  if (!session) unauthorized()
  return <div>Welcome {session.user.name}</div>
}
```

Cannot be called in the root layout.

### after(callback)

**Import:** `import { after } from 'next/server'`

Schedule work to run after the response is sent. Useful for logging, analytics, and other side effects that should not block the response.

```tsx
import { after } from 'next/server'

export default async function Page() {
  const ua = (await headers()).get('user-agent') || 'unknown'
  after(() => {
    logPageView({ ua })  // runs after response is sent
  })
  return <h1>My Page</h1>
}
```

**Key rules:**
- In Server Components: read `cookies()`/`headers()` **before** `after()` and pass values via closure. Calling dynamic APIs inside the `after` callback from a Server Component throws a runtime error.
- In Route Handlers and Server Actions: `cookies()`/`headers()` can be called directly inside the `after` callback.
- `after` is NOT a Dynamic API -- using it alone does not opt into dynamic rendering.
- Runs even if the response errors, or if `notFound()`/`redirect()` is called.
- Can be nested.

### draftMode()

**Import:** `import { draftMode } from 'next/headers'`

Async function for enabling/disabling Draft Mode (CMS preview).

```tsx
const draft = await draftMode()
draft.isEnabled  // boolean
draft.enable()   // sets __prerender_bypass cookie (Route Handler only)
draft.disable()  // removes the cookie (Route Handler only)
```

Check in Server Components:
```tsx
const { isEnabled } = await draftMode()
```

Enable via Route Handler:
```tsx
export async function GET() {
  const draft = await draftMode()
  draft.enable()
  return new Response('Draft mode enabled')
}
```

### refresh()

**Import:** `import { refresh } from 'next/cache'`

Refreshes the client router from within a Server Action only. Cannot be used in Route Handlers, Client Components, or other contexts.

```tsx
'use server'
import { refresh } from 'next/cache'

export async function createPost(formData: FormData) {
  await db.post.create({ data: { title: formData.get('title') } })
  refresh()
}
```

### userAgent(request)

**Import:** `import { userAgent } from 'next/server'`

Parses the user agent from a request object. Typically used in Middleware/Proxy.

```tsx
import { NextRequest, NextResponse, userAgent } from 'next/server'

export function middleware(request: NextRequest) {
  const { device, isBot, browser, os } = userAgent(request)
  // device.type: 'mobile' | 'tablet' | 'console' | 'smarttv' | 'wearable' | 'embedded' | undefined
}
```

**Properties:** `isBot` (boolean), `browser` (`{ name, version }`), `device` (`{ model, type, vendor }`), `engine` (`{ name, version }`), `os` (`{ name, version }`), `cpu` (`{ architecture }`).

## Generation Functions

### generateStaticParams

Exported from `page.tsx`, `layout.tsx`, or `route.ts` to statically generate routes with dynamic segments at build time.

```tsx
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json())
  return posts.map(post => ({ slug: post.slug }))
}
```

**Return types by route pattern:**

| Route                              | Return type                               |
|------------------------------------|-------------------------------------------|
| `/product/[id]`                    | `{ id: string }[]`                        |
| `/products/[category]/[product]`   | `{ category: string, product: string }[]` |
| `/products/[...slug]`              | `{ slug: string[] }[]`                    |

**Cascading params (top-down generation):** Child `generateStaticParams` receives parent params:

```tsx
// app/products/[category]/[product]/page.tsx
export async function generateStaticParams({ params: { category } }) {
  const products = await fetch(`/api/products?cat=${category}`).then(r => r.json())
  return products.map(p => ({ product: p.id }))
}
```

**Control unmatched paths:** Set `export const dynamicParams = false` to 404 for paths not returned by `generateStaticParams`. Default is `true` (render on demand at runtime).

**Timing:** Runs at `next build`. During `next dev`, called on navigation. Not called again during ISR revalidation.

## Components

### Link

**Import:** `import Link from 'next/link'`

Extends `<a>` with prefetching and client-side navigation. Primary way to navigate.

```tsx
<Link href="/dashboard">Dashboard</Link>
<Link href={{ pathname: '/about', query: { name: 'test' } }}>About</Link>
```

**Props:**

| Prop          | Type                    | Default   | Description                                             |
|---------------|-------------------------|-----------|---------------------------------------------------------|
| `href`        | `string \| UrlObject`   | required  | Path or URL to navigate to                              |
| `replace`     | `boolean`               | `false`   | Replace history entry instead of push                   |
| `scroll`      | `boolean`               | `true`    | Scroll to top on navigation (maintains position if page visible) |
| `prefetch`    | `boolean \| null`       | `'auto'`  | `true` = full prefetch; `false` = no prefetch; `null`/`'auto'` = static full, dynamic partial |
| `onNavigate`  | `(e) => void`           | --        | Called on client-side navigation; call `e.preventDefault()` to cancel |

Standard `<a>` attributes (`className`, `target`, `id`, etc.) are passed through to the underlying element.

**Active link pattern:**
```tsx
'use client'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

export function NavLink({ href, children }) {
  const pathname = usePathname()
  return <Link href={href} className={pathname === href ? 'active' : ''}>{children}</Link>
}
```

**Hash links:** `<Link href="/page#section">` scrolls to the element with that id.

**Sticky header offset:** Set `html { scroll-padding-top: 64px; }` to account for sticky headers when scrolling to anchors.

### Form

**Import:** `import Form from 'next/form'`

Extends `<form>` with prefetching, client-side navigation on submit, and progressive enhancement.

**String action (GET navigation):**
```tsx
import Form from 'next/form'

<Form action="/search">
  <input name="query" />
  <button type="submit">Search</button>
</Form>
// Submits as /search?query=value with client-side navigation
```

Prefetches the target route when the form enters the viewport. Shows `loading.js` instantly during navigation.

**Props for string action:** `action` (string, required), `replace` (boolean), `scroll` (boolean), `prefetch` (boolean, default `true`).

**Function action (Server Action / mutation):**
```tsx
import Form from 'next/form'
import { createPost } from './actions'

<Form action={createPost}>
  <input name="title" />
  <button type="submit">Create</button>
</Form>
```

When `action` is a function, `replace` and `scroll` props are ignored.

**Caveats:**
- `method`, `encType`, `target` are not supported (they override `<Form>` behavior). Use native `<form>` if you need them.
- `<input type="file">` with string action submits filename only (browser behavior).
- Use `useFormStatus()` from `react-dom` to show pending states.

## Server vs Client Context Quick Reference

| API                         | Server Component | Server Action | Route Handler | Client Component | Middleware/Proxy |
|-----------------------------|:---:|:---:|:---:|:---:|:---:|
| `useRouter`                 |     |     |     | yes |     |
| `usePathname`               |     |     |     | yes |     |
| `useSearchParams`           |     |     |     | yes |     |
| `useParams`                 |     |     |     | yes |     |
| `useSelectedLayoutSegment`  |     |     |     | yes |     |
| `useLinkStatus`             |     |     |     | yes |     |
| `cookies()` (read)          | yes | yes | yes |     |     |
| `cookies()` (write)         |     | yes | yes |     |     |
| `headers()`                 | yes | yes | yes |     |     |
| `redirect()`                | yes | yes | yes | yes* |    |
| `notFound()`                | yes | yes | yes |     |     |
| `forbidden()`               | yes | yes | yes |     |     |
| `unauthorized()`            | yes | yes | yes |     |     |
| `after()`                   | yes | yes | yes |     |     |
| `draftMode()`               | yes | yes | yes |     |     |
| `refresh()`                 |     | yes |     |     |     |
| `userAgent()`               |     |     |     |     | yes |
| `generateStaticParams`      | yes |     | yes |     |     |

*`redirect()` in Client Components works during render only, not in event handlers.

## Common Pitfalls

1. **Using `useSearchParams` without `<Suspense>`** causes the entire component tree up to the nearest Suspense boundary to render client-side. Always wrap it.

2. **Calling `cookies()`/`headers()` inside `after()` from Server Components** throws a runtime error. Read the values before calling `after()` and pass them via closure.

3. **`redirect()` inside `try/catch`** will be caught as an error. Call it outside the try block.

4. **Importing `useRouter` from `next/router`** instead of `next/navigation` when using the App Router. The Pages Router hook is a different API.

5. **Reading `searchParams` in layouts** is not supported. Layouts are shared across navigations and do not re-render. Use `useSearchParams` in a Client Component or read from the page's `searchParams` prop.

6. **Setting cookies during Server Component render** is not possible. The response has already started streaming. Use a Server Action or Route Handler.

7. **`forbidden()` and `unauthorized()` without config** require `experimental.authInterrupts: true` in `next.config.js`. They cannot be called from the root layout.

8. **`refresh()` outside Server Actions** throws an error. It is only available in Server Actions (not Route Handlers or Client Components). For client-side refresh, use `router.refresh()` from `useRouter`.

9. **Passing unsanitized user input to `router.push()`** opens XSS vulnerabilities, especially `javascript:` URLs.

10. **`useReportWebVitals` callback reference changes** cause duplicate metric reports. Define the callback outside the component or use `useCallback`.
