# Next.js: Data Fetching & Caching
Based on Next.js documentation (App Router).

## Data Fetching in Server Components

Server Components are async — fetch data directly with `await`.

### With `fetch`

```tsx
// app/blog/page.tsx
export default async function Page() {
  const data = await fetch('https://api.vercel.app/blog')
  const posts = await data.json()
  return (
    <ul>
      {posts.map((post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

`fetch` responses are **not cached by default**. Routes are still pre-rendered (static) unless a Dynamic API is used. To force dynamic rendering, use `{ cache: 'no-store' }` or the `connection()` API.

### With ORM / Database

```tsx
import { db, posts } from '@/lib/db'

export default async function Page() {
  const allPosts = await db.select().from(posts)
  return <ul>{allPosts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}
```

### Client Components

Two approaches:

1. **Stream with `use` hook** — fetch in Server Component, pass promise to Client Component:

```tsx
// Server Component (page.tsx)
export default function Page() {
  const posts = getPosts() // don't await
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Posts posts={posts} />
    </Suspense>
  )
}

// Client Component (posts.tsx)
'use client'
import { use } from 'react'
export default function Posts({ posts }: { posts: Promise<Post[]> }) {
  const allPosts = use(posts)
  return <ul>{allPosts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}
```

2. **SWR / React Query** — standard client-side fetching libraries.

## Parallel vs Sequential Fetching

### Sequential (waterfall — avoid when possible)

```tsx
// BAD: getAlbums waits for getArtist to finish
const artist = await getArtist(username)
const albums = await getAlbums(username)
```

### Parallel (preferred)

```tsx
// GOOD: both requests start immediately
const artistData = getArtist(username)  // no await
const albumsData = getAlbums(username)  // no await
const [artist, albums] = await Promise.all([artistData, albumsData])
```

Use `Promise.allSettled` if one failure shouldn't block the other.

### Preloading Pattern

```tsx
const preload = (id: string) => { void getItem(id) }

export default async function Page({ params }) {
  const { id } = await params
  preload(id)                           // start fetching early
  const isAvailable = await checkIsAvailable()
  return isAvailable ? <Item id={id} /> : null
}
```

## Request Deduplication (Memoization)

`fetch` GET/HEAD requests with the same URL and options are automatically memoized within a single render pass. Call the same fetch in Layout, Page, and components — it executes once.

For non-fetch data (ORM, database), use React `cache`:

```tsx
import { cache } from 'react'
export const getPost = cache(async (id: string) => {
  return db.query.posts.findFirst({ where: eq(posts.id, parseInt(id)) })
})
```

Memoization lasts only for the current request's render pass and is not shared across requests.

## Streaming

Break rendering into chunks to avoid blocking on slow data.

### Page-level: `loading.js`

Place `loading.tsx` next to `page.tsx` to stream the whole page:

```tsx
// app/blog/loading.tsx
export default function Loading() {
  return <div>Loading...</div>
}
```

### Component-level: `<Suspense>`

```tsx
import { Suspense } from 'react'
export default function BlogPage() {
  return (
    <div>
      <header><h1>Blog</h1></header>
      <Suspense fallback={<BlogListSkeleton />}>
        <BlogList />  {/* async Server Component — streams in */}
      </Suspense>
    </div>
  )
}
```

## Server Actions (Mutations)

### Defining

Add `'use server'` at function level (inline in Server Component) or file level:

```tsx
// app/lib/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const title = formData.get('title')
  await db.post.create({ data: { title } })
  revalidatePath('/posts')
  redirect('/posts')
}
```

### Using in Forms

```tsx
import { createPost } from '@/app/lib/actions'
export function Form() {
  return (
    <form action={createPost}>
      <input type="text" name="title" />
      <button type="submit">Create</button>
    </form>
  )
}
```

Forms support progressive enhancement — they work before JS loads.

### Passing Extra Arguments with `bind`

```tsx
'use client'
import { updateUser } from './actions'
export function UserProfile({ userId }: { userId: string }) {
  const updateUserWithId = updateUser.bind(null, userId)
  return <form action={updateUserWithId}>...</form>
}

// actions.ts
'use server'
export async function updateUser(userId: string, formData: FormData) { ... }
```

### Event Handlers (Client Components)

```tsx
'use client'
import { incrementLike } from './actions'
export default function LikeButton({ initialLikes }) {
  const [likes, setLikes] = useState(initialLikes)
  return (
    <button onClick={async () => {
      const updated = await incrementLike()
      setLikes(updated)
    }}>
      Like ({likes})
    </button>
  )
}
```

### Validation with Zod

```tsx
'use server'
import { z } from 'zod'
const schema = z.object({ email: z.string().email() })

export async function createUser(prevState: any, formData: FormData) {
  const result = schema.safeParse({ email: formData.get('email') })
  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors }
  }
  // mutate data...
}
```

### Pending State with `useActionState`

```tsx
'use client'
import { useActionState } from 'react'
import { createUser } from '@/app/actions'

export function Signup() {
  const [state, formAction, pending] = useActionState(createUser, { message: '' })
  return (
    <form action={formAction}>
      <input type="email" name="email" required />
      <p aria-live="polite">{state?.message}</p>
      <button disabled={pending}>Sign up</button>
    </form>
  )
}
```

### Optimistic Updates with `useOptimistic`

```tsx
'use client'
import { useOptimistic } from 'react'
import { send } from './actions'

export function Thread({ messages }) {
  const [optimistic, addOptimistic] = useOptimistic(
    messages, (state, msg) => [...state, { message: msg }]
  )
  const formAction = async (formData) => {
    const message = formData.get('message')
    addOptimistic(message)
    await send(message)
  }
  return (
    <div>
      {optimistic.map((m, i) => <div key={i}>{m.message}</div>)}
      <form action={formAction}>
        <input name="message" />
        <button type="submit">Send</button>
      </form>
    </div>
  )
}
```

## Caching Architecture

### Four Cache Layers

| Layer | What | Where | Duration | Scope |
|---|---|---|---|---|
| **Request Memoization** | `fetch` return values | Server | Per-request | React component tree |
| **Data Cache** | Fetched data | Server | Persistent (revalidatable) | Across requests & deploys |
| **Full Route Cache** | HTML + RSC payload | Server | Persistent (revalidatable) | Across requests & deploys |
| **Router Cache** | RSC payload | Client | Session-based | Per browser tab |

### Static vs Dynamic Rendering

**Static** (default): rendered at build time, fully cached.
**Dynamic**: rendered per-request. Triggered by using any Dynamic API:
- `cookies()`, `headers()`, `connection()`
- `searchParams` prop
- `fetch` with `{ cache: 'no-store' }`
- `unstable_noStore()` (deprecated, use `connection()`)

### Key Cache Interactions

- Revalidating Data Cache invalidates Full Route Cache (render depends on data).
- Invalidating Full Route Cache does NOT affect Data Cache.
- `revalidatePath` / `revalidateTag` in Server Actions also clear Router Cache.
- `revalidatePath` / `revalidateTag` in Route Handlers do NOT clear Router Cache immediately.
- `router.refresh()` clears Router Cache but not Data or Full Route Cache.

## fetch Options

```ts
// Default: no cache in dynamic routes, cached in static routes
fetch('https://...')

// Force cache (persists across requests)
fetch('https://...', { cache: 'force-cache' })

// Never cache
fetch('https://...', { cache: 'no-store' })

// Time-based revalidation (seconds)
fetch('https://...', { next: { revalidate: 3600 } })

// Tag for on-demand revalidation
fetch('https://...', { next: { tags: ['posts'] } })
```

- `revalidate: false` — cache indefinitely
- `revalidate: 0` — never cache
- Tags: max 256 chars per tag, max 128 tags per request
- Conflicting options (`{ revalidate: 3600, cache: 'no-store' }`) are both ignored

## Revalidation

### `revalidatePath(path, type?)`

Invalidates cached data for a specific path. Use in Server Actions or Route Handlers.

```ts
import { revalidatePath } from 'next/cache'

revalidatePath('/blog/post-1')           // specific URL
revalidatePath('/blog/[slug]', 'page')   // all matching pages
revalidatePath('/blog/[slug]', 'layout') // layout + all pages beneath
revalidatePath('/', 'layout')            // entire site
```

- `type` is required when path contains dynamic segments
- In Server Actions: updates UI immediately
- In Route Handlers: revalidation happens on next visit

### `revalidateTag(tag, profile?)`

Invalidates cached data by tag. Works in Server Actions and Route Handlers.

```ts
import { revalidateTag } from 'next/cache'

// Recommended: stale-while-revalidate semantics
revalidateTag('posts', 'max')

// Custom profile
revalidateTag('posts', { expire: 0 }) // immediate expiry (for webhooks)
```

- With `profile="max"` (recommended): serves stale while fetching fresh in background
- Without profile (deprecated): immediate expiry — migrate to `updateTag` instead
- Single-argument form is deprecated

### `updateTag(tag)`

Immediately expires cached data. **Server Actions only.** Use for read-your-own-writes.

```ts
'use server'
import { updateTag } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPost(formData: FormData) {
  const post = await db.post.create({ ... })
  updateTag('posts')           // list pages see fresh data
  updateTag(`post-${post.id}`) // detail page sees fresh data
  redirect(`/posts/${post.id}`)
}
```

### Choosing Between Them

| | `updateTag` | `revalidateTag` | `revalidatePath` |
|---|---|---|---|
| **Context** | Server Actions only | Server Actions + Route Handlers | Server Actions + Route Handlers |
| **Behavior** | Immediate expiry | Stale-while-revalidate (with `"max"`) | Revalidates path + data |
| **Use case** | Read-your-own-writes | Background refresh | Broad path invalidation |

Combine them for comprehensive consistency:

```ts
'use server'
import { revalidatePath, updateTag } from 'next/cache'

export async function updatePost() {
  await updatePostInDatabase()
  revalidatePath('/blog')  // refresh the specific page
  updateTag('posts')       // refresh all pages using this tag
}
```

## ISR (Incremental Static Regeneration)

### Time-Based

```tsx
// app/blog/[id]/page.tsx
export const revalidate = 60 // seconds

export async function generateStaticParams() {
  const posts = await fetch('https://api.vercel.app/blog').then(r => r.json())
  return posts.map((post) => ({ id: String(post.id) }))
}

export default async function Page({ params }) {
  const { id } = await params
  const post = await fetch(`https://api.vercel.app/blog/${id}`).then(r => r.json())
  return <main><h1>{post.title}</h1><p>{post.content}</p></main>
}
```

How it works:
1. Build generates known pages
2. Requests serve cached pages instantly
3. After `revalidate` seconds, next request still serves stale page
4. Background regeneration starts
5. On success, cache updates; subsequent requests get fresh page
6. Unknown paths generate on-demand (controlled by `dynamicParams`)

### On-Demand ISR

Use `revalidatePath` or `revalidateTag` in Server Actions:

```ts
'use server'
import { revalidatePath } from 'next/cache'
export async function createPost() {
  revalidatePath('/posts')
}
```

### ISR Caveats

- Only supported with Node.js runtime (not Edge)
- Not supported with Static Export
- Multiple fetches with different `revalidate` values: lowest wins for route
- Any fetch with `revalidate: 0` or `no-store` makes the route dynamic
- Debug with `NEXT_PRIVATE_DEBUG_CACHE=1` env var

## Cache Components (`use cache` directive)

The newer caching model (requires `cacheComponents: true` in `next.config`). Replaces `unstable_cache`.

### `cacheTag` — Tag Cached Functions/Components

```tsx
import { cacheTag } from 'next/cache'

export async function getProducts() {
  'use cache'
  cacheTag('products')
  return await db.query('SELECT * FROM products')
}
```

- Works with any server-side computation, not just `fetch`
- Multiple tags: `cacheTag('tag-one', 'tag-two')`
- Tags can be derived from data: `cacheTag('post', data.id)`
- Max 256 chars per tag, max 128 tags

### `cacheLife` — Control Cache Lifetime

```tsx
'use cache'
import { cacheLife } from 'next/cache'

export default async function BlogPage() {
  cacheLife('days')
  const posts = await getBlogPosts()
  return <div>{/* render */}</div>
}
```

#### Preset Profiles

| Profile | Use Case | `stale` | `revalidate` | `expire` |
|---|---|---|---|---|
| `default` | Standard content | 5 min | 15 min | never |
| `seconds` | Real-time data | 30 sec | 1 sec | 1 min |
| `minutes` | Frequently updated | 5 min | 1 min | 1 hour |
| `hours` | Multiple daily updates | 5 min | 1 hour | 1 day |
| `days` | Daily updates | 5 min | 1 day | 1 week |
| `weeks` | Weekly updates | 5 min | 1 week | 30 days |
| `max` | Rarely changes | 5 min | 30 days | 1 year |

#### Custom Profiles

```ts
// next.config.ts
const nextConfig = {
  cacheComponents: true,
  cacheLife: {
    editorial: { stale: 600, revalidate: 3600, expire: 86400 },
  },
}
```

#### Inline Profile

```tsx
'use cache'
import { cacheLife } from 'next/cache'
export default async function Page() {
  cacheLife({ stale: 3600, revalidate: 900, expire: 86400 })
  return <div>Page</div>
}
```

#### Conditional Lifetimes

```tsx
async function getPostContent(slug: string) {
  'use cache'
  const post = await fetchPost(slug)
  cacheTag(`post-${slug}`)
  if (!post) {
    cacheLife('minutes')  // missing content — recheck soon
    return null
  }
  cacheLife('days')       // published content — cache longer
  return post.data
}
```

## `connection()` — Opt Into Dynamic Rendering

Replaces deprecated `unstable_noStore`. Use when you want dynamic rendering without using cookies/headers/searchParams.

```tsx
import { connection } from 'next/server'

export default async function Page() {
  await connection()
  const rand = Math.random() // always fresh
  return <span>{rand}</span>
}
```

## Legacy: `unstable_cache`

Replaced by `use cache` + `cacheTag` + `cacheLife` in Next.js 16. Still works for backward compatibility.

```tsx
import { unstable_cache } from 'next/cache'

const getCachedUser = unstable_cache(
  async (id) => getUserById(id),
  ['user-cache-key'],        // keyParts (optional)
  { tags: ['users'], revalidate: 60 }  // options
)
const user = await getCachedUser(userId)
```

- Cannot use Dynamic APIs (`headers`, `cookies`) inside the cached function
- `keyParts` array further identifies the cache entry beyond function arguments

## Best Practices

### Do

- **Fetch in Server Components** — avoid client-side fetching when possible
- **Use parallel fetching** with `Promise.all` for independent requests
- **Tag data granularly** — `cacheTag('post', post.id)` enables precise invalidation
- **Use `updateTag` in Server Actions** for mutations where user must see their change
- **Use `revalidateTag` with `'max'`** for background refresh in Route Handlers / webhooks
- **Combine `revalidatePath` + `updateTag`** for comprehensive invalidation
- **Use Suspense boundaries** to stream slow data without blocking the page
- **Set explicit `cacheLife`** on `use cache` functions — don't rely on defaults
- **Debug caching** with `logging: { fetches: { fullUrl: true } }` in dev, `NEXT_PRIVATE_DEBUG_CACHE=1` in production

### Don't

- **Don't `await` independent fetches sequentially** — creates waterfalls
- **Don't use `revalidateTag` without a profile** — the single-argument form is deprecated
- **Don't use `updateTag` in Route Handlers** — it only works in Server Actions
- **Don't mix conflicting fetch options** — `{ revalidate: 3600, cache: 'no-store' }` are both ignored
- **Don't cache sensitive data** — the Data Cache persists across requests and deployments
- **Don't assume Route Handler revalidation clears Router Cache** — it does not; only Server Actions do
- **Don't use `unstable_cache` in new code** — migrate to `use cache` directive
- **Don't use `unstable_noStore` in new code** — use `connection()` instead

## Quick Reference: API Summary

| Function | Import | Purpose |
|---|---|---|
| `fetch` | global | Data fetching with cache/revalidate options |
| `revalidatePath` | `next/cache` | Invalidate cache for a path |
| `revalidateTag` | `next/cache` | Invalidate cache by tag (stale-while-revalidate) |
| `updateTag` | `next/cache` | Expire cache by tag immediately (Server Actions only) |
| `cacheTag` | `next/cache` | Tag a `use cache` function for invalidation |
| `cacheLife` | `next/cache` | Set lifetime of a `use cache` function |
| `connection` | `next/server` | Opt into dynamic rendering |
| `unstable_cache` | `next/cache` | Legacy: cache non-fetch data |
| `unstable_noStore` | `next/cache` | Legacy: opt out of static rendering |
| `React.cache` | `react` | Memoize function within a single request |
