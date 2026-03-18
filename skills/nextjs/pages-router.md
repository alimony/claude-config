# Next.js: Pages Router
Based on Next.js documentation (Pages Router).

## Routing

### File-System Routing

The `pages/` directory maps files to routes automatically.

```
pages/index.js        -> /
pages/about.js        -> /about
pages/blog/index.js   -> /blog
pages/blog/first.js   -> /blog/first
pages/dashboard/settings/username.js -> /dashboard/settings/username
```

A **page** is a React component exported as default from a `.js`, `.jsx`, `.ts`, or `.tsx` file in `pages/`.

```jsx
// pages/about.js
export default function About() {
  return <div>About</div>
}
```

### Dynamic Routes

Wrap file or folder names in square brackets for dynamic segments.

| Pattern | Example URL | `params` |
|---------|------------|----------|
| `[slug].js` | `/blog/hello` | `{ slug: 'hello' }` |
| `[...slug].js` | `/shop/a/b` | `{ slug: ['a', 'b'] }` |
| `[[...slug]].js` | `/shop` or `/shop/a/b` | `{ slug: undefined }` or `{ slug: ['a', 'b'] }` |

- **`[param]`** -- single dynamic segment
- **`[...param]`** -- catch-all (must have at least one segment)
- **`[[...param]]`** -- optional catch-all (also matches the bare path)

Route priority: predefined routes > dynamic `[param]` > catch-all `[...param]`.

Access params via `useRouter().query` or through data-fetching context objects.

### Special Files

#### `_app.js` -- Custom App

Controls page initialization. Use it to add global CSS, shared layouts, or inject data into all pages.

```jsx
// pages/_app.js
import '../styles/globals.css'

export default function MyApp({ Component, pageProps }) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  )
}
```

- `Component` is the active page -- changes on navigation.
- `pageProps` are preloaded props from data-fetching methods.
- Does NOT support `getStaticProps` or `getServerSideProps`.
- Using `getInitialProps` here disables Automatic Static Optimization for all pages without `getStaticProps`.

#### `_document.js` -- Custom Document

Customizes the `<html>` and `<body>` tags. Rendered on the server only.

```jsx
// pages/_document.js
import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
```

- All four components (`Html`, `Head`, `Main`, `NextScript`) are required.
- The `<Head>` here is for tags common to ALL pages (fonts, etc). For per-page `<title>`, use `next/head`.
- Components outside `<Main />` are not initialized by the browser -- no app logic here.
- Does NOT support `getStaticProps` or `getServerSideProps`.

#### `404.js` and `500.js` -- Error Pages

```jsx
// pages/404.js -- statically generated at build time
export default function Custom404() {
  return <h1>404 - Page Not Found</h1>
}
```

```jsx
// pages/500.js -- statically generated at build time
export default function Custom500() {
  return <h1>500 - Server Error</h1>
}
```

Both support `getStaticProps` for build-time data. For advanced error handling, use `pages/_error.js`:

```jsx
// pages/_error.js
function Error({ statusCode }) {
  return <p>{statusCode ? `${statusCode} error on server` : 'Client error'}</p>
}
Error.getInitialProps = ({ res, err }) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404
  return { statusCode }
}
export default Error
```

### Linking and Navigation

```jsx
import Link from 'next/link'

// Static path
<Link href="/about">About</Link>

// Dynamic path with interpolation
<Link href={`/blog/${post.slug}`}>{post.title}</Link>

// Dynamic path with URL object
<Link href={{ pathname: '/blog/[slug]', query: { slug: post.slug } }}>
  {post.title}
</Link>
```

`<Link>` prefetches statically generated pages in the viewport. SSR pages are fetched only on click.

#### Imperative Navigation with `useRouter`

```jsx
import { useRouter } from 'next/router'

export default function Page() {
  const router = useRouter()

  // Navigate
  router.push('/about')
  router.replace('/login')        // no history entry
  router.back()                    // browser back
  router.reload()                  // full reload

  // URL object
  router.push({ pathname: '/post/[pid]', query: { pid: post.id } })
}
```

#### Router Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `pathname` | `string` | Route path after `/pages` (excludes basePath, locale) |
| `query` | `object` | Parsed query string + dynamic route params |
| `asPath` | `string` | Path shown in browser including search params |
| `isFallback` | `boolean` | Whether in fallback mode |
| `isReady` | `boolean` | Router fields updated client-side and ready |
| `basePath` | `string` | Active basePath |
| `locale` | `string` | Active locale |

#### Router Events

```jsx
// pages/_app.js
import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function MyApp({ Component, pageProps }) {
  const router = useRouter()

  useEffect(() => {
    const handleStart = (url) => console.log('Navigating to', url)
    const handleComplete = (url) => console.log('Navigated to', url)

    router.events.on('routeChangeStart', handleStart)
    router.events.on('routeChangeComplete', handleComplete)

    return () => {
      router.events.off('routeChangeStart', handleStart)
      router.events.off('routeChangeComplete', handleComplete)
    }
  }, [router])

  return <Component {...pageProps} />
}
```

Events: `routeChangeStart`, `routeChangeComplete`, `routeChangeError`, `beforeHistoryChange`, `hashChangeStart`, `hashChangeComplete`. All receive `(url, { shallow })`.

#### Shallow Routing

Update the URL without re-running data-fetching methods:

```jsx
router.push('/?counter=10', undefined, { shallow: true })
```

Only works for URL changes within the **same page**. Navigating to a different page ignores `shallow`.

## Data Fetching

### `getStaticProps` -- Static Generation

Runs at build time (and during ISR revalidation). Returns props to pre-render the page as static HTML + JSON.

```jsx
export async function getStaticProps(context) {
  const res = await fetch('https://api.example.com/posts')
  const posts = await res.json()

  return {
    props: { posts },     // passed to page component
    revalidate: 60,       // ISR: regenerate at most every 60s
    // notFound: true,    // return 404
    // redirect: { destination: '/', permanent: false },
  }
}
```

**Context object:**

| Key | Description |
|-----|-------------|
| `params` | Dynamic route parameters |
| `draftMode` | `true` if in draft mode |
| `locale` / `locales` / `defaultLocale` | i18n info (if enabled) |
| `revalidateReason` | `"build"`, `"stale"`, or `"on-demand"` |

**Return values:**

| Key | Description |
|-----|-------------|
| `props` | Serializable object passed to the page |
| `revalidate` | Seconds until next regeneration (ISR). `false` = never |
| `notFound` | `true` to return 404 |
| `redirect` | `{ destination, permanent }` to redirect |

- Only exported from **page** files (not `_app`, `_document`, components).
- Server-side only -- write direct DB queries, read files with `process.cwd()`.
- Generates both HTML and JSON; client-side navigation uses the JSON.

### `getStaticPaths` -- Dynamic Static Routes

Required when a dynamic route page uses `getStaticProps`. Defines which paths to pre-render.

```jsx
export async function getStaticPaths() {
  const res = await fetch('https://api.example.com/posts')
  const posts = await res.json()

  return {
    paths: posts.map((post) => ({ params: { id: String(post.id) } })),
    fallback: false, // or true or 'blocking'
  }
}
```

**`fallback` modes:**

| Value | Unbuilt paths behavior |
|-------|----------------------|
| `false` | 404 page |
| `true` | Serve fallback page, then generate in background. Check `router.isFallback`. |
| `'blocking'` | SSR on first request, then cache. No fallback UI -- user waits. |

For large sites, return empty `paths` with `fallback: 'blocking'` to generate all pages on-demand.

Param values must be **strings**. For catch-all routes, params is an array:
```js
// pages/[...slug].js
{ params: { slug: ['a', 'b'] } }  // matches /a/b
```

### `getServerSideProps` -- Server-Side Rendering

Runs on every request. The page cannot be cached by a CDN.

```jsx
export async function getServerSideProps(context) {
  const { params, req, res, query, resolvedUrl } = context

  res.setHeader('Cache-Control', 'public, s-maxage=10, stale-while-revalidate=59')

  const data = await fetch(`https://api.example.com/data`)
  return { props: { data: await data.json() } }
}
```

**Context object** (superset of `getStaticProps` context):

| Key | Description |
|-----|-------------|
| `params` | Dynamic route params |
| `req` | HTTP IncomingMessage + `cookies` |
| `res` | HTTP ServerResponse (can set headers) |
| `query` | Full query string object |
| `resolvedUrl` | Normalized URL without `_next/data` prefix |
| `draftMode` | Draft mode flag |
| `locale` / `locales` / `defaultLocale` | i18n info |

**Returns:** `{ props }`, `{ notFound: true }`, or `{ redirect: { destination, permanent } }`.

Errors thrown inside show `pages/500.js` in production.

### `getInitialProps` -- Legacy

Runs on server for initial load, then on client for navigation. **Prefer `getStaticProps` or `getServerSideProps` instead.**

```jsx
Page.getInitialProps = async (ctx) => {
  // ctx: { pathname, query, asPath, req (server only), res (server only), err }
  const res = await fetch('https://api.example.com/data')
  return { data: await res.json() }
}
```

Using `getInitialProps` in `_app` disables Automatic Static Optimization for pages without `getStaticProps`.

### Client-Side Fetching

For data that doesn't need SEO or pre-rendering. Use SWR (recommended) or `useEffect`.

```jsx
import useSWR from 'swr'

const fetcher = (...args) => fetch(...args).then((res) => res.json())

function Profile() {
  const { data, error, isLoading } = useSWR('/api/profile', fetcher)
  if (error) return <div>Failed to load</div>
  if (isLoading) return <div>Loading...</div>
  return <h1>{data.name}</h1>
}
```

## Rendering Modes

### Automatic Static Optimization

Pages without `getServerSideProps` or `getInitialProps` are automatically pre-rendered as static HTML.

- Build output: `.html` for static pages, `.js` for SSR pages.
- The router's `query` object is empty during prerender, then populated after hydration.
- Use `router.isReady` before relying on `query` or `asPath`.
- Adding `getInitialProps` to `_app` disables this for pages without `getStaticProps`.

### Static Site Generation (SSG)

Page HTML generated at build time. Use `getStaticProps` (+ `getStaticPaths` for dynamic routes). Best for content that doesn't change per-request.

### Incremental Static Regeneration (ISR)

Add `revalidate` to `getStaticProps` return. After the revalidation period, the next request triggers background regeneration while serving the stale page.

```jsx
return { props: { posts }, revalidate: 60 }
```

On-demand revalidation via API route:
```jsx
// pages/api/revalidate.js
export default async function handler(req, res) {
  await res.revalidate('/blog/post-1')
  return res.json({ revalidated: true })
}
```

ISR cache status header `x-nextjs-cache`: `MISS` | `STALE` | `HIT`.

### Server-Side Rendering (SSR)

Page HTML generated on each request. Use `getServerSideProps`. Page cannot be CDN-cached (without manual `Cache-Control` headers).

### Client-Side Rendering (CSR)

Fetch data in the browser with `useEffect` or SWR. Page shell is pre-rendered; data loads after JS executes. Impacts SEO for the dynamic content.

## API Routes

Files in `pages/api/` are server-side endpoints mapped to `/api/*`. They are NOT included in the client bundle.

```ts
// pages/api/hello.ts
import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    // handle POST
  }
  res.status(200).json({ message: 'Hello' })
}
```

### Request Helpers

- `req.cookies` -- parsed cookies object
- `req.query` -- parsed query string (includes dynamic params)
- `req.body` -- parsed body (based on content-type), or `null`

### Response Helpers

- `res.status(code)` -- set HTTP status
- `res.json(body)` -- send JSON response
- `res.send(body)` -- send string, object, or Buffer
- `res.redirect([status,] path)` -- redirect (default 307)
- `res.revalidate(urlPath)` -- trigger on-demand ISR

### Config

```js
export const config = {
  api: {
    bodyParser: { sizeLimit: '1mb' },  // or `false` to disable (e.g., webhooks)
    externalResolver: true,             // suppress unresolved-request warnings
    responseLimit: '8mb',               // or false to disable
  },
  maxDuration: 5,  // max execution time in seconds
}
```

### Dynamic API Routes

Same bracket syntax as pages: `pages/api/post/[pid].js`, `pages/api/post/[...slug].js`, `pages/api/post/[[...slug]].js`.

### Streaming

```js
export default async function handler(req, res) {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-store',
  })
  for (let i = 0; i < 10; i++) {
    res.write(`data: ${i}\n\n`)
    await new Promise((r) => setTimeout(r, 1000))
  }
  res.end()
}
```

## Layout Patterns

### Single Shared Layout

```jsx
// pages/_app.js
import Layout from '../components/layout'

export default function MyApp({ Component, pageProps }) {
  return <Layout><Component {...pageProps} /></Layout>
}
```

### Per-Page Layouts

Attach a `getLayout` function to each page:

```jsx
// pages/dashboard.js
import DashboardLayout from '../components/dashboard-layout'

export default function Dashboard() { return <p>Dashboard</p> }

Dashboard.getLayout = (page) => <DashboardLayout>{page}</DashboardLayout>
```

```jsx
// pages/_app.js
export default function MyApp({ Component, pageProps }) {
  const getLayout = Component.getLayout ?? ((page) => page)
  return getLayout(<Component {...pageProps} />)
}
```

This preserves component state across navigations (React reconciliation keeps the tree stable).

### TypeScript Per-Page Layout

```tsx
// pages/_app.tsx
import type { ReactElement, ReactNode } from 'react'
import type { NextPage } from 'next'
import type { AppProps } from 'next/app'

export type NextPageWithLayout<P = {}, IP = P> = NextPage<P, IP> & {
  getLayout?: (page: ReactElement) => ReactNode
}

type AppPropsWithLayout = AppProps & { Component: NextPageWithLayout }

export default function MyApp({ Component, pageProps }: AppPropsWithLayout) {
  const getLayout = Component.getLayout ?? ((page) => page)
  return getLayout(<Component {...pageProps} />)
}
```

### Data Fetching in Layouts

Layouts are not pages, so they cannot use `getStaticProps` or `getServerSideProps`. Fetch data client-side with SWR or `useEffect`.

## Migration to App Router

### Key Differences

| Pages Router | App Router |
|-------------|------------|
| `pages/` directory | `app/` directory |
| `pages/index.js` | `app/page.js` |
| `pages/about.js` | `app/about/page.js` |
| `pages/blog/[slug].js` | `app/blog/[slug]/page.js` |
| `pages/_app.js` + `pages/_document.js` | `app/layout.js` (root layout) |
| `pages/_error.js` | `app/error.js` |
| `pages/404.js` | `app/not-found.js` |
| `pages/api/*.js` | `app/api/route.js` (Route Handlers) |
| `getStaticProps` | `fetch()` with `cache: 'force-cache'` (default) |
| `getServerSideProps` | `fetch()` with `cache: 'no-store'` |
| `getStaticPaths` | `generateStaticParams()` |
| `getStaticProps` + `revalidate` | `fetch()` with `next: { revalidate: N }` |
| `useRouter` from `next/router` | `useRouter` from `next/navigation` + `usePathname` + `useSearchParams` |
| `next/head` | `export const metadata` or `generateMetadata()` |

### Migration Path

1. Create `app/` directory alongside `pages/`.
2. Create `app/layout.js` as root layout (replaces `_app` + `_document`).
3. Migrate pages incrementally -- both routers work simultaneously.
4. Move data fetching into async Server Components (replace `getStaticProps`/`getServerSideProps` with `fetch()` calls).
5. Replace `useRouter` from `next/router` with hooks from `next/navigation`.
6. For shared components during migration, use `next/compat/router` which works in both routers.

Navigation between `pages/` and `app/` routes causes a hard navigation (no client-side transition).

### Data Fetching Equivalents in App Router

```jsx
// app/page.js -- Server Component

// Equivalent to getStaticProps
const staticData = await fetch('https://...', { cache: 'force-cache' })

// Equivalent to getServerSideProps
const dynamicData = await fetch('https://...', { cache: 'no-store' })

// Equivalent to getStaticProps with revalidate
const revalidatedData = await fetch('https://...', { next: { revalidate: 60 } })
```

### Routing Hooks in App Router

```jsx
'use client'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'

// useRouter: push(), replace(), refresh(), back(), forward(), prefetch()
// usePathname(): current pathname string
// useSearchParams(): URLSearchParams object
```

Removed from App Router `useRouter`: `query`, `asPath`, `isFallback`, `isReady`, `locale`, `basePath`, `events`.
