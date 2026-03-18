# Next.js: Fundamentals
Based on Next.js documentation (App Router).

## Core Concepts

Next.js is a full-stack React framework using **file-system based routing**. The App Router (v13+) is built on React Server Components and supports layouts, nested routing, streaming, and server-side data fetching.

**Three directives** control where code runs:

| Directive | Purpose |
|-----------|---------|
| `'use client'` | Marks a file as a Client Component boundary |
| `'use server'` | Marks a function as a Server Function callable from client code |
| `'use cache'` | Marks a component or function as cacheable |

**Rendering model:** Components are Server Components by default. They render on the server, produce an RSC Payload (compact binary format), and stream HTML to the client. Client Components are pre-rendered on the server for HTML, then hydrated on the client.

---

## Project Structure

### Special Files (in order of rendering hierarchy)

| File | Purpose |
|------|---------|
| `layout.js` | Shared UI wrapper, persists across navigations, does NOT re-render |
| `template.js` | Like layout but re-renders on every navigation |
| `error.js` | Error boundary (must be `'use client'`) |
| `loading.js` | Suspense fallback shown while segment loads |
| `not-found.js` | 404 UI, triggered by `notFound()` |
| `page.js` | The route's unique UI, makes a route publicly accessible |
| `route.js` | API endpoint (GET, POST, etc.), mutually exclusive with `page.js` |
| `global-error.js` | Root-level error boundary, must include `<html>` and `<body>` |
| `default.js` | Fallback for parallel route slots |

### Top-Level Folders

| Folder | Purpose |
|--------|---------|
| `app/` | App Router routes and layouts |
| `public/` | Static assets served from `/` |
| `src/` | Optional — separates app code from config files |

### Key Config Files

| File | Purpose |
|------|---------|
| `next.config.js` | Framework configuration |
| `instrumentation.ts` | OpenTelemetry setup |
| `proxy.ts` | Request proxy (formerly middleware) |
| `.env.local` | Local environment variables (gitignored) |

---

## Routing

### Folders define routes, files define UI

A folder becomes a public route only when it contains a `page.js` or `route.js`. Other files colocated in the folder are safe and not routable.

```
app/
  page.tsx          -> /
  blog/
    page.tsx        -> /blog
    [slug]/
      page.tsx      -> /blog/:slug
    _components/    -> not routable (private folder)
      Post.tsx
```

### Dynamic Segments

| Pattern | Example Path | Matches |
|---------|-------------|---------|
| `[slug]` | `app/blog/[slug]/page.tsx` | `/blog/hello` (single segment) |
| `[...slug]` | `app/docs/[...slug]/page.tsx` | `/docs/a`, `/docs/a/b/c` (catch-all) |
| `[[...slug]]` | `app/docs/[[...slug]]/page.tsx` | `/docs` + all above (optional catch-all) |

Access dynamic params in page/layout:

```tsx
// app/blog/[slug]/page.tsx
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  // ...
}
```

**Note:** `params` is a Promise in the App Router. Always `await` it.

### Route Groups — `(folderName)`

Organize routes without affecting URLs. Useful for sharing layouts among a subset of routes.

```
app/
  (marketing)/
    layout.tsx      -> shared marketing layout
    page.tsx        -> /
    about/page.tsx  -> /about
  (shop)/
    layout.tsx      -> shared shop layout
    cart/page.tsx   -> /cart
```

Multiple root layouts: remove the top-level `layout.js` and add one in each route group. Each must include `<html>` and `<body>`.

### Private Folders — `_folderName`

Prefix with underscore to exclude from routing entirely. Useful for colocating utilities, components, or helpers.

---

## Layouts and Pages

### Root Layout (required)

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

- Must contain `<html>` and `<body>` tags
- Wraps all routes in the app
- If omitted, Next.js auto-creates one in dev

### Nested Layouts

```tsx
// app/blog/layout.tsx
export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return <section>{children}</section>
}
```

Layouts preserve state and do not re-render on navigation. The root layout wraps the blog layout, which wraps the page.

### Pages

```tsx
// app/blog/page.tsx
export default async function Page() {
  const posts = await getPosts()
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
}
```

### Search Params

```tsx
// Server Component — opts page into dynamic rendering
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const filters = (await searchParams).filters
}
```

- `searchParams` prop: use when search params drive data fetching
- `useSearchParams()` hook: use in Client Components for client-only filtering
- `new URLSearchParams(window.location.search)`: use in event handlers to avoid re-renders

### Type Helpers

```tsx
// PageProps and LayoutProps are globally available (generated by next dev/build)
export default async function Page(props: PageProps<'/blog/[slug]'>) {
  const { slug } = await props.params
}
```

---

## Navigation

### Link Component

```tsx
import Link from 'next/link'

<Link href="/blog/hello">Read post</Link>
<Link href={`/blog/${post.slug}`}>{post.title}</Link>
```

- Prefetches routes when links enter the viewport
- Client-side navigation (no full page reload)
- Primary navigation method

### Programmatic Navigation

```tsx
'use client'
import { useRouter } from 'next/navigation'

export function NavigateButton() {
  const router = useRouter()
  return <button onClick={() => router.push('/dashboard')}>Go</button>
}
```

---

## Server and Client Components

### When to Use Each

| Need | Use |
|------|-----|
| Fetch data, access secrets, reduce JS bundle | Server Component (default) |
| State (`useState`), effects (`useEffect`), event handlers, browser APIs | Client Component (`'use client'`) |

### Do: Push `'use client'` to the leaves

```tsx
// app/layout.tsx — Server Component (default)
import Search from './search'  // Client Component
import Logo from './logo'      // Server Component

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav><Logo /><Search /></nav>
      <main>{children}</main>
    </>
  )
}
```

```tsx
// app/search.tsx
'use client'
export default function Search() {
  // Interactive — needs client
}
```

### Don't: Mark entire layouts or pages as `'use client'`

This sends unnecessary JavaScript to the browser and defeats Server Components.

### Passing Data: Server to Client

Props must be serializable by React:

```tsx
// Server Component
import LikeButton from './like-button'
export default async function Page() {
  const post = await getPost()
  return <LikeButton likes={post.likes} />
}

// Client Component
'use client'
export default function LikeButton({ likes }: { likes: number }) {
  // ...
}
```

### Interleaving: Server Components Inside Client Components

Use the `children` pattern to nest Server Components within Client boundaries:

```tsx
// Client Component
'use client'
export default function Modal({ children }: { children: React.ReactNode }) {
  return <div className="modal">{children}</div>
}

// Server Component (parent)
import Modal from './modal'
import Cart from './cart'  // Server Component

export default function Page() {
  return <Modal><Cart /></Modal>
}
```

### Context Providers

React context requires `'use client'`. Wrap the provider in a Client Component, import it in the root layout:

```tsx
// app/theme-provider.tsx
'use client'
import { createContext } from 'react'
export const ThemeContext = createContext({})
export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  return <ThemeContext.Provider value="dark">{children}</ThemeContext.Provider>
}

// app/layout.tsx
import ThemeProvider from './theme-provider'
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html><body><ThemeProvider>{children}</ThemeProvider></body></html>
  )
}
```

Render providers as deep as possible so Next.js can optimize static parts above them.

### Third-Party Components Without `'use client'`

Wrap them in a thin Client Component re-export:

```tsx
// app/carousel.tsx
'use client'
import { Carousel } from 'acme-carousel'
export default Carousel
```

### Preventing Environment Leaks

- Only `NEXT_PUBLIC_*` env vars are exposed to the client
- Use `import 'server-only'` in modules with secrets to get a build error if imported client-side
- Use `import 'client-only'` for browser-only modules

---

## CSS and Styling

### Recommended Approach

| Method | Use Case |
|--------|----------|
| **Tailwind CSS** | Primary styling for most components |
| **CSS Modules** | Scoped custom CSS when Tailwind is insufficient |
| **Global CSS** | Truly global styles (base resets, Tailwind `@import`) |

### Tailwind CSS Setup

```js
// postcss.config.mjs
export default { plugins: { '@tailwindcss/postcss': {} } }
```

```css
/* app/globals.css */
@import 'tailwindcss';
```

```tsx
// app/layout.tsx
import './globals.css'
```

### CSS Modules

```css
/* app/blog/blog.module.css */
.blog { padding: 24px; }
```

```tsx
import styles from './blog.module.css'
export default function Page() {
  return <main className={styles.blog}>...</main>
}
```

### CSS Ordering Pitfall

Import order determines CSS order in production. To keep it predictable:
- Contain CSS imports to a single entry file when possible
- Import global styles in the root layout
- Do not use auto-sorting linters on CSS imports
- Check production build (`next build`) to verify final order

---

## Error Handling

### Two Categories

1. **Expected errors** — validation failures, failed requests. Return as values, not exceptions.
2. **Uncaught exceptions** — bugs. Let error boundaries catch them.

### Expected Errors: Server Functions

```tsx
// app/actions.ts
'use server'
export async function createPost(prevState: any, formData: FormData) {
  const res = await fetch('https://api.example.com/posts', {
    method: 'POST',
    body: JSON.stringify({ title: formData.get('title') }),
  })
  if (!res.ok) return { message: 'Failed to create post' }
}

// app/ui/form.tsx
'use client'
import { useActionState } from 'react'
import { createPost } from '@/app/actions'

export function Form() {
  const [state, formAction, pending] = useActionState(createPost, { message: '' })
  return (
    <form action={formAction}>
      <input name="title" required />
      {state?.message && <p aria-live="polite">{state.message}</p>}
      <button disabled={pending}>Create</button>
    </form>
  )
}
```

### Not Found

```tsx
import { notFound } from 'next/navigation'

export default async function Page({ params }) {
  const post = await getPost((await params).slug)
  if (!post) notFound()
  return <div>{post.title}</div>
}
```

Pair with `not-found.tsx` in the same segment for custom 404 UI.

### Uncaught Exceptions: `error.tsx`

```tsx
// app/dashboard/error.tsx
'use client'
export default function ErrorPage({
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

- Must be `'use client'`
- Errors bubble up to the nearest parent `error.tsx`
- Place at different route levels for granular handling
- Does NOT catch errors in the layout of the same segment (use parent's error boundary)

### Global Error Boundary

```tsx
// app/global-error.tsx — catches root layout errors
'use client'
export default function GlobalError({ error, reset }) {
  return (
    <html><body>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </body></html>
  )
}
```

Must include `<html>` and `<body>` since it replaces the root layout.

---

## Deployment

| Option | Features | When to Use |
|--------|----------|-------------|
| **Node.js server** | All features | Standard deployment |
| **Docker** | All features | Containerized environments |
| **Static export** | Limited (no server features) | Static hosting (S3, GitHub Pages) |
| **Adapters** | Platform-specific | Cloudflare, Netlify, Vercel, AWS Amplify, etc. |

### Production Build

```json
{
  "scripts": {
    "build": "next build",
    "start": "next start"
  }
}
```

### Static Export

```js
// next.config.js
module.exports = { output: 'export' }
```

Does NOT support: Server Components that fetch at request time, API routes, cookies/headers, revalidation, proxy/middleware.

### Docker (Standalone)

```js
// next.config.js
module.exports = { output: 'standalone' }
```

Produces a minimal `.next/standalone` folder with only required runtime files.

---

## Key Terminology

| Term | Meaning |
|------|---------|
| **RSC Payload** | Binary representation of rendered Server Component tree, sent to client for DOM reconciliation |
| **Hydration** | React attaching event handlers to server-rendered HTML to make it interactive |
| **Prerendering** | Rendering at build time or during revalidation; the default for components without request-time APIs |
| **Request-time rendering** | Rendering at request time; triggered by `cookies()`, `headers()`, `searchParams`, or `draftMode()` |
| **Streaming** | Server sends parts of the page as they become ready, enabled by `loading.js` or `<Suspense>` |
| **ISR (Revalidation)** | Updating static content without full rebuild; time-based (`cacheLife()`) or on-demand (`updateTag()`) |
| **Version skew** | Mismatch between client assets and server after deployment; handled via `deploymentId` config |
| **Turbopack** | Rust-based bundler, default for `next dev`, available for `next build` |
| **Route segment** | A folder in the `app` directory mapping to a URL segment |
| **Module graph** | Import/export dependency graph; determines client/server bundle splitting |

---

## Common Pitfalls

1. **Forgetting `await` on `params` and `searchParams`.** In the App Router, these are Promises.
2. **Putting `'use client'` too high in the tree.** Everything imported below becomes client code. Push it to leaf components.
3. **Using React context in Server Components.** Context requires `'use client'`. Wrap providers in a Client Component.
4. **Expecting `error.tsx` to catch layout errors.** It catches errors in `page.tsx` and children, not the sibling `layout.tsx`. Use the parent segment's error boundary.
5. **Non-serializable props to Client Components.** Functions, class instances, and Dates cannot be passed from Server to Client Components. Only JSON-serializable values work.
6. **CSS import order surprises in production.** Dev and production CSS ordering can differ. Always verify with `next build`.
7. **Using `NEXT_PUBLIC_` for secrets.** Variables prefixed with `NEXT_PUBLIC_` are inlined into the client bundle. Never use this prefix for API keys or tokens.
8. **Importing server-only code in Client Components.** Use `import 'server-only'` to get a build-time error instead of a runtime leak.
